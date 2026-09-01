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
import json
import threading
import time
import uuid

import numpy as np
import soundfile as sf

from .audio import edge_silence_samples, join_audios, resample_audio, save_wav
from .prosody import PODCAST_PROSODY_VERSION, ProsodySegment, parse_prosody_script, transform_prosody_script
from .text import chunk_sentences, split_into_sentences


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

    def public(self, job):
        return {
            "job_id": job.id, "state": job.state, "total_chunks": job.total_chunks,
            "completed_chunks": job.completed_chunks, "active_chunk": job.active_chunk,
            "failed_chunk": job.failed_chunk, "error": job.error,
            "cancel_requested": job.cancel_requested, "created_at": job.created_at,
            "updated_at": job.updated_at, "prosody_version": PODCAST_PROSODY_VERSION if job.prosody_markup else None,
        }

    def _write_metadata(self, job):
        job.updated_at = time.time()
        job.directory.mkdir(parents=True, exist_ok=True)
        (job.directory / "metadata.json").write_text(json.dumps(self.public(job), ensure_ascii=False, indent=2), encoding="utf-8")

    def _segments(self, job):
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
                result.append((chunk, segment.pause_after_ms if index == len(chunks) - 1 else None))
        return result

    def _run(self, job):
        try:
            chunks = self._segments(job)
            if not chunks:
                raise ValueError("Text contains no speakable content")
            job.total_chunks, job.state = len(chunks), "RUNNING"
            self._write_metadata(job)
            paths = []
            for index, (chunk, pause_after) in enumerate(chunks):
                if job.cancel_requested:
                    job.state, job.active_chunk = "CANCELLED", None
                    self._write_metadata(job)
                    return
                job.active_chunk = index + 1
                self._write_metadata(job)
                path = job.directory / f"chunk_{index:04d}.wav"
                # The shared semaphore covers normal TTS, previews, Voice Lab,
                # and these jobs.  Cancellation is checked again after waiting.
                self.semaphore.acquire()
                try:
                    if job.cancel_requested:
                        job.state, job.active_chunk = "CANCELLED", None
                        self._write_metadata(job)
                        return
                    kwargs = {key: value for key, value in job.options.items() if key in {"temperature", "top_k", "top_p", "repetition_penalty"} and value is not None}
                    self.engine.generate(chunk, voice=job.voice, speed=1.0, out_path=str(path), **kwargs)
                finally:
                    self.semaphore.release()
                paths.append((path, pause_after, chunk))
                job.completed_chunks = index + 1
                self._write_metadata(job)
            if job.cancel_requested:
                job.state, job.active_chunk = "CANCELLED", None
                self._write_metadata(job)
                return
            job.state, job.active_chunk = "ASSEMBLING", None
            self._write_metadata(job)
            audios, pauses, sr = [], [], None
            for index, (path, pause_after, chunk) in enumerate(paths):
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
            if job.speed != 1.0:
                final = resample_audio(final, sr, job.speed)
            job.output_path = job.directory / "result.wav"
            save_wav(str(job.output_path), final, sr)
            job.state = "COMPLETED"
            self._write_metadata(job)
        except Exception as exc:
            job.state, job.error, job.failed_chunk, job.active_chunk = "FAILED", str(exc), job.active_chunk, None
            self._write_metadata(job)
