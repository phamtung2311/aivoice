"""Cooperative, single-process jobs used by the existing Audio Studio.

The job is deliberately local and conservative: one worker is started per job,
but every VieNeu call uses the application's shared inference semaphore.  A
cancel request cannot safely interrupt native inference; it prevents the next
chunk and preserves the completed chunks for diagnostics until the job is
cleaned up.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
import gc
import hashlib
import json
import shutil
import subprocess
import threading
import time
import uuid
import wave

import numpy as np
import soundfile as sf

from .audio import fill_trailing_pause, edge_silence_samples, join_audios, resample_audio, save_wav
from .prosody import PODCAST_PROSODY_VERSION, ProsodySegment, parse_prosody_script, transform_prosody_script
from .text import chunk_sentences, split_into_sentences
from .podcast_brand import (
    PODCAST_BRAND_VOICE_ID,
    PODCAST_ENGINE_CONFIG,
    PODCAST_FINAL_TEMPO,
    PODCAST_INFERENCE_CONFIG,
    PODCAST_PIPELINE_VERSION,
    PODCAST_SEMANTIC_PLANNER_VERSION,
    inference_config_hash,
    load_canonical_candidate_03,
    plan_podcast_text,
    profile_hash,
)
from .podcast_voices import PODCAST_VOICES, resolve_podcast_voice


@dataclass(frozen=True)
class RenderSegment:
    text: str
    pause_after_ms: int | None
    boundary_after: str | None = None
    primary_focus_phrase: str | None = None


@dataclass
class LongAudioJob:
    id: str
    text: str
    voice: str | None
    speed: float
    prosody_markup: bool
    options: dict
    directory: Path
    state: str = "QUEUED"
    total_chunks: int = 0
    completed_chunks: int = 0
    active_chunk: int | None = None
    cancel_requested: bool = False
    error: str | None = None
    failed_chunk: int | None = None
    output_path: Path | None = None
    source_text_sha256: str = ""
    profile_sha256: str | None = None
    chunk_records: list[dict] = field(default_factory=list)
    created_at: float = field(default_factory=time.time)
    updated_at: float = field(default_factory=time.time)


class LongAudioJobs:
    """Small in-memory registry with inspectable on-disk job artifacts."""
    def __init__(self, engine, semaphore, root: str = "data/jobs"):
        self.engine, self.semaphore = engine, semaphore
        self.root = Path(root)
        self.jobs: dict[str, LongAudioJob] = {}
        self.lock = threading.Lock()

    def create(self, *, text, voice, speed, prosody_markup, options):
        job_id = f"long_{uuid.uuid4().hex[:16]}"
        job = LongAudioJob(job_id, text, voice, speed, prosody_markup, options, self.root / job_id)
        job.source_text_sha256 = hashlib.sha256(text.encode("utf-8")).hexdigest()
        if voice == PODCAST_BRAND_VOICE_ID:
            job.profile_sha256 = profile_hash()
        with self.lock:
            self.jobs[job_id] = job
        threading.Thread(target=self._run, args=(job,), daemon=True, name=job_id).start()
        return job

    def get(self, job_id):
        with self.lock:
            return self.jobs.get(job_id)

    def cancel(self, job_id):
        job = self.get(job_id)
        if not job:
            return None
        with self.lock:
            if job.state in {"COMPLETED", "FAILED", "CANCELLED"}:
                return job
            job.cancel_requested = True
            job.updated_at = time.time()
        return job

    def resume(self, job_id):
        """Resume a failed/cancelled job, reusing verified completed chunk files."""
        job = self.get(job_id)
        if not job or job.state not in {"FAILED", "CANCELLED"}:
            return job
        with self.lock:
            job.state = "QUEUED"
            job.error = None
            job.failed_chunk = None
            job.cancel_requested = False
            job.active_chunk = None
        threading.Thread(target=self._run, args=(job,), daemon=True, name=f"{job.id}_resume").start()
        return job

    def public(self, job):
        return {
            "job_id": job.id, "state": job.state, "total_chunks": job.total_chunks,
            "completed_chunks": job.completed_chunks, "active_chunk": job.active_chunk,
            "failed_chunk": job.failed_chunk, "error": job.error,
            "cancel_requested": job.cancel_requested, "created_at": job.created_at,
            "updated_at": job.updated_at, "prosody_version": PODCAST_PROSODY_VERSION if job.prosody_markup else None,
            "pipeline_version": PODCAST_PIPELINE_VERSION if job.voice == PODCAST_BRAND_VOICE_ID else None,
            "source_text_sha256": job.source_text_sha256,
            "profile_sha256": job.profile_sha256,
            "completed_chunk_metadata": list(job.chunk_records),
        }

    def _write_metadata(self, job):
        job.updated_at = time.time()
        job.directory.mkdir(parents=True, exist_ok=True)
        (job.directory / "metadata.json").write_text(json.dumps(self.public(job), ensure_ascii=False, indent=2), encoding="utf-8")

    def _segments(self, job):
        if job.voice == PODCAST_BRAND_VOICE_ID:
            return [
                RenderSegment(
                    item.text,
                    round(item.pause_after_seconds * 1000),
                    item.boundary_after,
                    item.primary_focus_phrase,
                )
                for item in plan_podcast_text(job.text)
            ]
        # Production podcast voices use the exact TTS engine entry point for
        # the whole request, including normalization, chunking, pauses and speed.
        if job.voice in PODCAST_VOICES:
            return [RenderSegment(job.text, None)]
        text = job.text
        if job.prosody_markup:
            transform = job.options.get("normalize")
            if transform:
                text = transform_prosody_script(text, transform)
            semantic = parse_prosody_script(text)
        else:
            semantic = [ProsodySegment(text)]
        result = []
        for segment in semantic:
            chunks = chunk_sentences(split_into_sentences(segment.text), max_chars=240)
            for index, chunk in enumerate(chunks):
                # Explicit pause belongs only to the final safe chunk of its semantic segment.
                result.append(RenderSegment(chunk, segment.pause_after_ms if index == len(chunks) - 1 else None))
        return result

    @staticmethod
    def _assemble_podcast_to_disk(paths, destination: Path):
        """Concatenate PCM WAV chunks and explicit pauses without loading them all."""
        expected = None
        destination.parent.mkdir(parents=True, exist_ok=True)
        with wave.open(str(destination), "wb") as output:
            for index, (path, segment) in enumerate(paths):
                with wave.open(str(path), "rb") as source:
                    params = (source.getnchannels(), source.getsampwidth(), source.getframerate(), source.getcomptype())
                    if expected is None:
                        expected = params
                        output.setnchannels(params[0])
                        output.setsampwidth(params[1])
                        output.setframerate(params[2])
                        output.setcomptype(params[3], "not compressed")
                    elif params != expected:
                        raise ValueError("Generated chunks have incompatible WAV parameters")
                    while True:
                        block = source.readframes(65536)
                        if not block:
                            break
                        output.writeframesraw(block)
                if index < len(paths) - 1 and segment.pause_after_ms:
                    frames = round(segment.pause_after_ms * expected[2] / 1000)
                    output.writeframesraw(b"\x00" * frames * expected[0] * expected[1])
        if expected is None:
            raise ValueError("No podcast chunks to assemble")

    @staticmethod
    def _apply_podcast_tempo(source: Path, destination: Path):
        if not shutil.which("ffmpeg"):
            raise RuntimeError("FFmpeg is required for Podcast Brand Voice")
        subprocess.run([
            "ffmpeg", "-hide_banner", "-loglevel", "error", "-y", "-i", str(source),
            "-map_metadata", "-1", "-af", f"atempo={PODCAST_FINAL_TEMPO}",
            "-c:a", "pcm_s16le", str(destination),
        ], check=True)

    def _run(self, job):
        try:
            chunks = self._segments(job)
            if not chunks:
                raise ValueError("Text contains no speakable content")
            job.total_chunks, job.state = len(chunks), "RUNNING"
            job.completed_chunks = 0
            self._write_metadata(job)
            paths = []
            is_podcast_brand = job.voice == PODCAST_BRAND_VOICE_ID
            is_production_podcast = job.voice in PODCAST_VOICES
            podcast_voice = None
            if is_podcast_brand:
                # Resolve lossless canonical arrays before any inference. Hash or
                # load failures are fatal; there is no fallback to a named voice.
                podcast_voice, speaker_identity = load_canonical_candidate_03()
                pipeline_manifest = {
                    "pipeline_version": PODCAST_PIPELINE_VERSION,
                    "profile_id": PODCAST_BRAND_VOICE_ID,
                    "source_text_sha256": job.source_text_sha256,
                    "profile_sha256": job.profile_sha256,
                    "candidate_03": speaker_identity,
                    "effective_inference_config": PODCAST_INFERENCE_CONFIG,
                    "inference_config_sha256": inference_config_hash(),
                    "semantic_planner_version": PODCAST_SEMANTIC_PLANNER_VERSION,
                    "chunk_count": len(chunks),
                    "final_tempo": PODCAST_FINAL_TEMPO,
                    "generic_ui_parameters": "ignored",
                    "chunks": [
                        {"index": i, "tts_text_sha256": hashlib.sha256(item.text.encode("utf-8")).hexdigest(),
                         "chars": len(item.text), "boundary_after": item.boundary_after,
                         "explicit_pause_after_seconds": item.pause_after_ms / 1000,
                         "primary_focus_phrase": item.primary_focus_phrase}
                        for i, item in enumerate(chunks)
                    ],
                }
                (job.directory / "podcast_pipeline_manifest.json").write_text(
                    json.dumps(pipeline_manifest, ensure_ascii=False, indent=2), encoding="utf-8"
                )
                # Keep the Phase 42 filename as a compatibility view.
                (job.directory / "plan.json").write_text(
                    json.dumps(pipeline_manifest, ensure_ascii=False, indent=2), encoding="utf-8"
                )
            elif is_production_podcast:
                # Exact frozen Phase 45 artifacts; unknown/hash failures must
                # fail the job rather than silently falling back to a preset.
                podcast_voice = resolve_podcast_voice(job.voice)
            for index, segment in enumerate(chunks):
                chunk, pause_after = segment.text, segment.pause_after_ms
                if job.cancel_requested:
                    job.state, job.active_chunk = "CANCELLED", None
                    self._write_metadata(job)
                    return
                job.active_chunk = index + 1
                self._write_metadata(job)
                path = job.directory / f"chunk_{index:04d}.wav"
                text_hash = hashlib.sha256(chunk.encode("utf-8")).hexdigest()
                prior = next((record for record in job.chunk_records if record.get("index") == index), None)
                if prior and prior.get("text_sha256") == text_hash and path.is_file():
                    actual_hash = hashlib.sha256(path.read_bytes()).hexdigest()
                    if actual_hash == prior.get("wav_sha256"):
                        paths.append((path, segment))
                        job.completed_chunks = index + 1
                        self._write_metadata(job)
                        continue
                # The shared semaphore covers normal TTS, previews, Voice Lab,
                # and these jobs.  Cancellation is checked again after waiting.
                self.semaphore.acquire()
                try:
                    if job.cancel_requested:
                        job.state, job.active_chunk = "CANCELLED", None
                        self._write_metadata(job)
                        return
                    if is_podcast_brand:
                        kwargs = dict(PODCAST_ENGINE_CONFIG)
                        render_voice = podcast_voice
                    elif is_production_podcast:
                        kwargs = {key: value for key, value in job.options.items() if key in {"temperature", "top_k", "top_p", "repetition_penalty"} and value is not None}
                        render_voice = job.voice
                        kwargs["voice_profile"] = podcast_voice
                    else:
                        kwargs = {key: value for key, value in job.options.items() if key in {"temperature", "top_k", "top_p", "repetition_penalty"} and value is not None}
                        render_voice = job.voice
                    render = self.engine.generate_prosody if is_production_podcast and job.prosody_markup else self.engine.generate
                    render(chunk, voice=render_voice,
                           speed=job.speed if is_production_podcast else 1.0,
                           out_path=str(path), **kwargs)
                finally:
                    self.semaphore.release()
                chunk_hash = hashlib.sha256(path.read_bytes()).hexdigest()
                job.chunk_records = [record for record in job.chunk_records if record.get("index") != index]
                job.chunk_records.append({"index": index, "path": path.name, "wav_sha256": chunk_hash,
                                          "text_sha256": text_hash, "chars": len(chunk),
                                          "boundary_after": segment.boundary_after,
                                          "explicit_pause_after_ms": pause_after})
                job.chunk_records.sort(key=lambda record: record["index"])
                paths.append((path, segment))
                job.completed_chunks = index + 1
                self._write_metadata(job)
                gc.collect()
            if job.cancel_requested:
                job.state, job.active_chunk = "CANCELLED", None
                self._write_metadata(job)
                return
            job.state, job.active_chunk = "ASSEMBLING", None
            self._write_metadata(job)
            if is_podcast_brand:
                pretempo = job.directory / "assembled_original.wav"
                self._assemble_podcast_to_disk(paths, pretempo)
                job.output_path = job.directory / "result.wav"
                self._apply_podcast_tempo(pretempo, job.output_path)
                pretempo.unlink(missing_ok=True)
                for path, _segment in paths:
                    path.unlink(missing_ok=True)
                job.state = "COMPLETED"
                self._write_metadata(job)
                return
            if is_production_podcast:
                # Keep the TTS engine's WAV unchanged; do not assemble/resample twice.
                job.output_path = job.directory / "result.wav"
                shutil.copyfile(paths[0][0], job.output_path)
                job.state = "COMPLETED"
                self._write_metadata(job)
                return
            audios, pauses, sr = [], [], None
            for index, (path, segment) in enumerate(paths):
                pause_after, chunk = segment.pause_after_ms, segment.text
                audio, part_sr = sf.read(str(path), dtype="float32", always_2d=False)
                sr = int(part_sr) if sr is None else sr
                if sr != int(part_sr):
                    raise ValueError("Generated chunks have incompatible sample rates")
                audios.append(np.asarray(audio, dtype=np.float32))
                if index < len(paths) - 1:
                    pauses.append(pause_after if pause_after is not None else (130 if chunk.rstrip()[-1:] in ".!?…" else 75 if chunk.rstrip()[-1:] in ",;:" else 45))
            gaps = []
            for index, target in enumerate(pauses):
                _leading, trailing = edge_silence_samples(audios[index])
                leading, _trailing = edge_silence_samples(audios[index + 1])
                gaps.append(max(0, int((target - ((trailing + leading) * 1000 / sr)) * sr / 1000)))
            final = join_audios(audios, sr, gap_samples=gaps)
            final = fill_trailing_pause(final, sr, paths[-1][1].pause_after_ms)
            if job.speed != 1.0:
                final = resample_audio(final, sr, job.speed)
            job.output_path = job.directory / "result.wav"
            save_wav(str(job.output_path), final, sr)
            job.state = "COMPLETED"
            self._write_metadata(job)
        except Exception as exc:
            job.state, job.error, job.failed_chunk, job.active_chunk = "FAILED", str(exc), job.active_chunk, None
            self._write_metadata(job)
