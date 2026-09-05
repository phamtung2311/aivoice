#!/usr/bin/env python3
"""Generate the single frozen VieNeu preset source for Phase 38C."""

from __future__ import annotations

import hashlib
import json
import platform
import resource
import sys
import time
from datetime import datetime, timezone
from importlib.metadata import version
from pathlib import Path

import numpy as np
import soundfile as sf
from vieneu import Vieneu


ROOT = Path(__file__).resolve().parent
TEXT_PATH = ROOT / "source_text.txt"
OUTPUT = ROOT / "audio" / "source_vietnamese.wav"
METRICS = ROOT / "metrics" / "source_metrics.json"
EXPECTED_TEXT = "Khi mọi thứ trở nên ồn ào, điều quan trọng nhất là giữ một nhịp suy nghĩ thật rõ ràng."
PRESET_ID = "Minh Đức"


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def audio_metrics(path: Path) -> dict[str, float | int | str]:
    data, sample_rate = sf.read(path, always_2d=True, dtype="float32")
    mono = data.mean(axis=1, dtype=np.float64)
    return {
        "path": str(path.relative_to(ROOT)),
        "sha256": sha256(path),
        "size_bytes": path.stat().st_size,
        "duration_seconds": float(len(data) / sample_rate),
        "sample_rate_hz": int(sample_rate),
        "channels": int(data.shape[1]),
        "peak_abs": float(np.max(np.abs(data))),
        "rms": float(np.sqrt(np.mean(np.square(mono)))),
        "clipped_samples_abs_ge_0_999": int(np.count_nonzero(np.abs(data) >= 0.999)),
    }


def main() -> None:
    if OUTPUT.exists() or METRICS.exists():
        raise FileExistsError("Phase 38C source output/metrics already exists; no overwrite allowed")

    text = TEXT_PATH.read_text(encoding="utf-8").strip()
    if text != EXPECTED_TEXT:
        raise RuntimeError("Frozen source text changed; refusing generation")

    started_utc = datetime.now(timezone.utc).isoformat()
    load_started = time.perf_counter()
    tts = Vieneu(backend="onnx")
    load_seconds = time.perf_counter() - load_started

    presets = dict((voice_id, label) for label, voice_id in tts.list_preset_voices())
    if PRESET_ID not in presets:
        raise RuntimeError(f"Installed preset {PRESET_ID!r} is unavailable")

    generation_started = time.perf_counter()
    # Exactly the documented defaults: only text and the verified preset ID.
    audio = tts.infer(text, voice=PRESET_ID)
    generation_seconds = time.perf_counter() - generation_started
    if not isinstance(audio, np.ndarray) or audio.size == 0:
        raise RuntimeError("VieNeu returned empty audio")

    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    METRICS.parent.mkdir(parents=True, exist_ok=True)
    tts.save(audio, OUTPUT)

    result = {
        "phase": "38C",
        "role": "source_vietnamese",
        "created_utc": started_utc,
        "text": text,
        "preset_id": PRESET_ID,
        "preset_label": presets[PRESET_ID],
        "vieneu_version": version("vieneu"),
        "backend": "onnx",
        "device": "cpu",
        "call": "tts.infer(text, voice='Minh Đức')",
        "documented_defaults": {
            "denoise": True,
            "use_ref_codes": True,
            "temperature": 0.8,
            "top_k": 25,
            "top_p": 0.95,
            "max_new_frames": 300,
            "repetition_penalty": 1.2,
            "repetition_window": 64,
            "max_chars": 256,
            "silence_p": 0.15,
            "crossfade_p": 0.0,
            "apply_watermark": True,
            "batch_size": None,
        },
        "model_load_seconds": load_seconds,
        "generation_seconds": generation_seconds,
        "peak_rss_mib": resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1024.0,
        "python": sys.version,
        "platform": platform.platform(),
        "audio": audio_metrics(OUTPUT),
        "human_source_gate": "PENDING",
    }
    METRICS.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()

