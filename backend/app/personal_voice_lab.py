"""Local, non-destructive storage and segmentation for personal voice recordings.

Source recordings are deliberately separate from TTS references: a 30–180 second
phone recording is preserved byte-for-byte, while engines receive only explicitly
selected short PCM WAV segments.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any
import hashlib
import json
import os
import secrets
import shutil
import subprocess

import numpy as np
import soundfile as sf


ACCEPTED_EXTENSIONS = {".m4a", ".wav", ".mp3", ".aac"}
SOURCE_MIN_SECONDS = 30.0
SOURCE_MAX_SECONDS = 180.0
SOURCE_MAX_BYTES = 64 * 1024 * 1024
NORMALIZED_SAMPLE_RATE = 48_000
VIENEU_REFERENCE_MIN_SECONDS = 3.0
VIENEU_REFERENCE_MAX_SECONDS = 8.0


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _atomic_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_suffix(path.suffix + ".tmp")
    temp.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    os.replace(temp, path)


def _ffprobe(path: Path) -> dict[str, Any]:
    if not shutil.which("ffprobe"):
        raise RuntimeError("FFprobe chưa được cài trên máy.")
    proc = subprocess.run(
        [
            "ffprobe", "-v", "error", "-select_streams", "a:0",
            "-show_entries", "stream=codec_name,sample_rate,channels:format=duration",
            "-of", "json", str(path),
        ],
        capture_output=True,
        text=True,
        timeout=30,
    )
    if proc.returncode != 0:
        raise ValueError("Không thể đọc bản thu âm.")
    try:
        data = json.loads(proc.stdout)
        stream = data["streams"][0]
        return {
            "codec": str(stream.get("codec_name") or "unknown"),
            "sample_rate": int(stream.get("sample_rate") or 0),
            "channels": int(stream.get("channels") or 0),
            "duration_seconds": float(data.get("format", {}).get("duration") or 0),
        }
    except (KeyError, IndexError, TypeError, ValueError) as exc:
        raise ValueError("Bản thu không có audio stream hợp lệ.") from exc


def _decode_preserving_dynamics(source: Path, destination: Path) -> None:
    if not shutil.which("ffmpeg"):
        raise RuntimeError("FFmpeg chưa được cài; không thể giải mã bản thu.")
    proc = subprocess.run(
        [
            "ffmpeg", "-hide_banner", "-loglevel", "error", "-y", "-i", str(source),
            "-map", "0:a:0", "-vn", "-ac", "1", "-ar", str(NORMALIZED_SAMPLE_RATE),
            "-c:a", "pcm_s16le", str(destination),
        ],
        capture_output=True,
        text=True,
        timeout=120,
    )
    if proc.returncode != 0 or not destination.exists() or destination.stat().st_size <= 44:
        destination.unlink(missing_ok=True)
        raise ValueError("Không thể giải mã bản thu sang PCM WAV.")


def _audio_metrics(path: Path) -> dict[str, Any]:
    wav, sr = sf.read(path, dtype="float32", always_2d=False)
    if getattr(wav, "ndim", 1) > 1:
        wav = wav.mean(axis=1)
    wav = np.asarray(wav, dtype=np.float32)
    if wav.size == 0:
        raise ValueError("Bản thu rỗng.")
    abs_wav = np.abs(wav)
    frame = max(1, int(sr * 0.02))
    usable = len(wav) - (len(wav) % frame)
    if usable:
        rms_frames = np.sqrt(np.mean(np.square(wav[:usable].reshape(-1, frame)), axis=1) + 1e-12)
        silence_ratio = float(np.mean(rms_frames < 10 ** (-45 / 20)))
    else:
        silence_ratio = float(np.mean(abs_wav < 10 ** (-45 / 20)))
    return {
        "duration_seconds": round(len(wav) / float(sr), 6),
        "sample_rate": int(sr),
        "channels": 1,
        "peak": round(float(abs_wav.max()), 6),
        "rms": round(float(np.sqrt(np.mean(np.square(wav)) + 1e-12)), 6),
        "clipped_samples": int(np.count_nonzero(abs_wav >= 0.999)),
        "silence_ratio": round(silence_ratio, 6),
    }


def propose_segments(path: Path, *, maximum: int = 8) -> list[dict[str, Any]]:
    """Suggest 3–8 s windows with endpoints near low-energy frames.

    This is intentionally an assistive heuristic, not transcription. The user
    must listen and can replace each range manually before cloning.
    """
    wav, sr = sf.read(path, dtype="float32", always_2d=False)
    if getattr(wav, "ndim", 1) > 1:
        wav = wav.mean(axis=1)
    wav = np.asarray(wav, dtype=np.float32)
    frame_seconds = 0.02
    frame = max(1, int(sr * frame_seconds))
    usable = len(wav) - (len(wav) % frame)
    if usable <= 0:
        return []
    rms = np.sqrt(np.mean(np.square(wav[:usable].reshape(-1, frame)), axis=1) + 1e-12)
    db = 20 * np.log10(rms + 1e-9)
    # A fixed conservative floor remains usable for recordings with little
    # silence; a percentile-derived floor can incorrectly classify every frame
    # as noise when speech occupies most of the take.
    active = db > -45.0
    indices = np.flatnonzero(active)
    if not indices.size:
        return []
    speech_start = indices[0] * frame_seconds
    speech_end = min(len(wav) / sr, (indices[-1] + 1) * frame_seconds)
    suggestions: list[dict[str, Any]] = []
    cursor = speech_start
    while cursor + VIENEU_REFERENCE_MIN_SECONDS <= speech_end and len(suggestions) < maximum:
        target = min(cursor + 7.0, speech_end)
        lo = int(max(cursor + 3.0, target - 1.0) / frame_seconds)
        hi = int(min(cursor + 8.0, speech_end) / frame_seconds)
        if hi > lo:
            end_frame = lo + int(np.argmin(rms[lo:hi]))
            end = max(cursor + 3.0, min(cursor + 8.0, end_frame * frame_seconds))
        else:
            end = target
        suggestions.append({
            "start_seconds": round(cursor, 3),
            "end_seconds": round(end, 3),
            "duration_seconds": round(end - cursor, 3),
            "kind": "automatic_suggestion",
            "transcript": "",
        })
        cursor = end + 0.18
    return suggestions


@dataclass
class PersonalVoiceStore:
    root: Path

    def __post_init__(self) -> None:
        self.root = Path(self.root)
        for name in ("source", "normalized", "references", "outputs", "metadata"):
            (self.root / name).mkdir(parents=True, exist_ok=True)

    def source_metadata(self, source_id: str) -> dict[str, Any]:
        if not source_id.startswith("src_") or not source_id.replace("_", "").isalnum():
            raise KeyError(source_id)
        path = self.root / "metadata" / f"{source_id}.json"
        if not path.exists():
            raise KeyError(source_id)
        return json.loads(path.read_text(encoding="utf-8"))

    def save_source(self, filename: str, payload: bytes) -> dict[str, Any]:
        safe_name = Path(filename or "recording").name
        extension = Path(safe_name).suffix.lower()
        if extension not in ACCEPTED_EXTENSIONS:
            raise ValueError("Chỉ nhận M4A, WAV, MP3 hoặc AAC.")
        if not payload or len(payload) > SOURCE_MAX_BYTES:
            raise ValueError("Bản thu phải có dữ liệu và không vượt quá 64 MiB.")
        source_id = "src_" + secrets.token_hex(8)
        original = self.root / "source" / f"{source_id}{extension}"
        normalized = self.root / "normalized" / f"{source_id}.wav"
        original.write_bytes(payload)
        try:
            source_probe = _ffprobe(original)
            if source_probe["duration_seconds"] < SOURCE_MIN_SECONDS - 0.05 or source_probe["duration_seconds"] > SOURCE_MAX_SECONDS + 0.05:
                raise ValueError("Bản thu nguồn phải dài từ 30 giây đến 3 phút.")
            _decode_preserving_dynamics(original, normalized)
            normalized_metrics = _audio_metrics(normalized)
        except Exception:
            original.unlink(missing_ok=True)
            normalized.unlink(missing_ok=True)
            raise
        warnings = []
        if normalized_metrics["clipped_samples"]:
            warnings.append("Phát hiện mẫu chạm ngưỡng clipping.")
        if normalized_metrics["silence_ratio"] > 0.45:
            warnings.append("Bản thu có tỷ lệ im lặng cao.")
        metadata = {
            "schema_version": 1,
            "id": source_id,
            "original_filename": safe_name,
            "original_path": str(original),
            "original_sha256": _sha256(original),
            "original_bytes": len(payload),
            "source": source_probe,
            "normalized_path": str(normalized),
            "normalized_sha256": _sha256(normalized),
            "normalized": normalized_metrics,
            "processing": {
                "local_only": True,
                "decode": "ffmpeg",
                "channels": 1,
                "sample_rate": NORMALIZED_SAMPLE_RATE,
                "sample_format": "PCM_S16LE",
                "denoise": False,
                "compression": False,
                "normalization": False,
                "pitch_or_formant_change": False,
            },
            "warnings": warnings,
            "segment_suggestions": propose_segments(normalized),
            "segments": [],
        }
        _atomic_json(self.root / "metadata" / f"{source_id}.json", metadata)
        return metadata

    def create_segment(
        self, source_id: str, start_seconds: float, end_seconds: float,
        label: str = "", transcript: str = "",
    ) -> dict[str, Any]:
        metadata = self.source_metadata(source_id)
        start = float(start_seconds)
        end = float(end_seconds)
        duration = end - start
        if start < 0 or end > metadata["normalized"]["duration_seconds"] + 0.001 or duration <= 0:
            raise ValueError("Khoảng segment nằm ngoài bản thu.")
        if duration < VIENEU_REFERENCE_MIN_SECONDS or duration > VIENEU_REFERENCE_MAX_SECONDS:
            raise ValueError("Reference VieNeu phải dài từ 3 đến 8 giây.")
        segment_id = "ref_" + secrets.token_hex(6)
        destination = self.root / "references" / f"{source_id}_{segment_id}.wav"
        proc = subprocess.run(
            [
                "ffmpeg", "-hide_banner", "-loglevel", "error", "-y",
                "-ss", f"{start:.6f}", "-i", metadata["normalized_path"],
                "-t", f"{duration:.6f}", "-c:a", "pcm_s16le", str(destination),
            ], capture_output=True, text=True, timeout=30,
        )
        if proc.returncode != 0:
            destination.unlink(missing_ok=True)
            raise ValueError("Không thể trích reference segment.")
        metrics = _audio_metrics(destination)
        segment = {
            "id": segment_id,
            "label": (label or segment_id).strip()[:100],
            "start_seconds": round(start, 6),
            "end_seconds": round(end, 6),
            "duration_seconds": metrics["duration_seconds"],
            "transcript": transcript.strip(),
            "path": str(destination),
            "sha256": _sha256(destination),
            "metrics": metrics,
            "engine_compatibility": {"vieneu_3_3_0": True},
        }
        metadata["segments"].append(segment)
        _atomic_json(self.root / "metadata" / f"{source_id}.json", metadata)
        return segment

    def audio_path(self, source_id: str, kind: str, segment_id: str | None = None) -> Path:
        metadata = self.source_metadata(source_id)
        if kind == "original":
            return Path(metadata["original_path"])
        if kind == "normalized":
            return Path(metadata["normalized_path"])
        if kind == "segment" and segment_id:
            for segment in metadata["segments"]:
                if segment["id"] == segment_id:
                    return Path(segment["path"])
        raise KeyError((source_id, kind, segment_id))


def engine_catalog() -> list[dict[str, Any]]:
    return [
        {
            "id": "vieneu_3_3_0", "name": "VieNeu v3 Turbo 3.3.0", "available": True,
            "production_eligible": True, "research_only": False,
            "reference_seconds": "3–8", "transcript_required": False,
        },
        {
            "id": "v_tts", "name": "V-TTS", "available": False,
            "production_eligible": False, "research_only": True,
            "reason": "Chưa cài; CC BY-NC 4.0 không phù hợp production có monetization.",
            "reference_seconds": "3–10", "transcript_required": False,
        },
        {
            "id": "gwen_tts_0_6b", "name": "Gwen-TTS 0.6B", "available": False,
            "production_eligible": False, "research_only": True,
            "reason": "Chưa cài; upstream ưu tiên CUDA/BF16 và chưa có CPU backend được xác nhận.",
            "reference_seconds": "few-shot", "transcript_required": True,
        },
    ]
