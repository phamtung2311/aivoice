#!/usr/bin/env python3
"""Phase 36D: one CPU-only VietVoice-TTS Candidate 03 probe.

This script intentionally has no retry path and refuses to overwrite output.
"""
from __future__ import annotations

import json
import os
import resource
import time
from pathlib import Path

import numpy as np
import onnxruntime
import soundfile as sf
from vietvoicetts import ModelConfig, TTSApi


HERE = Path(__file__).resolve().parent
REFERENCE_WAV = (
    HERE.parent
    / "brand_speaker_phase33c/baseline_anchor/BRAND_CANDIDATE_03_BASELINE/qwen_source.wav"
).resolve()
OUTPUT_DIR = HERE / "output"
OUTPUT_WAV = OUTPUT_DIR / "vietvoice_candidate03_raw.wav"
METRICS_JSON = OUTPUT_DIR / "vietvoice_candidate03_raw_metrics.json"
MODEL_CACHE = HERE / "model_cache"

REFERENCE_TEXT = "A quiet evening settles over the city. I speak clearly, naturally, and without rushing."
# Short enough to remain one inference unit with the 6.96-second reference and
# VietVoice's documented/default 15-second maximum chunk duration.
TARGET_TEXT = "Một câu chuyện rõ ràng cần được kể liền mạch, có điểm nhấn đúng chỗ."


def audio_metrics(path: Path) -> dict[str, float | int]:
    audio, sample_rate = sf.read(path, always_2d=True)
    mono = audio.mean(axis=1, dtype=np.float64)
    peak = float(np.max(np.abs(mono))) if len(mono) else 0.0
    rms = float(np.sqrt(np.mean(np.square(mono)))) if len(mono) else 0.0
    return {
        "duration_seconds": round(len(mono) / sample_rate, 6),
        "sample_rate": int(sample_rate),
        "channels": int(audio.shape[1]),
        "peak": round(peak, 8),
        "rms": round(rms, 8),
        "clipped_samples": int(np.count_nonzero(np.abs(mono) >= 0.999)),
    }


def main() -> None:
    if OUTPUT_WAV.exists():
        raise SystemExit(f"REFUSING_TO_OVERWRITE_EXISTING_OUTPUT: {OUTPUT_WAV}")
    if not REFERENCE_WAV.is_file():
        raise SystemExit(f"MISSING_CANONICAL_REFERENCE: {REFERENCE_WAV}")

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    config = ModelConfig(
        model_cache_dir=str(MODEL_CACHE),
        # All remaining values are the installed documented defaults.
    )
    config_payload = config.to_dict()

    load_started = time.perf_counter()
    api = TTSApi(config)
    model_load_seconds = time.perf_counter() - load_started

    generation_started = time.perf_counter()
    api.synthesize_to_file(
        TARGET_TEXT,
        str(OUTPUT_WAV),
        reference_audio=str(REFERENCE_WAV),
        reference_text=REFERENCE_TEXT,
    )
    generation_seconds = time.perf_counter() - generation_started

    metrics = audio_metrics(OUTPUT_WAV)
    metrics.update(
        {
            "phase": "36D",
            "renderer": "VietVoice-TTS",
            "reference_wav": str(REFERENCE_WAV),
            "reference_text": REFERENCE_TEXT,
            "target_text_passed": TARGET_TEXT,
            "device": "CPUExecutionProvider",
            "onnx_available_providers": onnxruntime.get_available_providers(),
            "configuration": config_payload,
            "model_load_seconds": round(model_load_seconds, 6),
            "generation_seconds": round(generation_seconds, 6),
            "rtf": round(generation_seconds / metrics["duration_seconds"], 6),
            "peak_rss_mib": round(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1024, 3),
            "pid": os.getpid(),
        }
    )
    METRICS_JSON.write_text(json.dumps(metrics, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(metrics, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
