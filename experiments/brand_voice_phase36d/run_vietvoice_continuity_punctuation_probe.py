#!/usr/bin/env python3
"""Phase 36E: one punctuation-only continuity probe, no retry/no overwrite."""
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
MODEL_CACHE = HERE / "model_cache"
OUTPUT_DIR = HERE / "output"
OUTPUT_WAV = OUTPUT_DIR / "vietvoice_candidate03_phase36e_comma_removed.wav"
METRICS_JSON = OUTPUT_DIR / "vietvoice_candidate03_phase36e_comma_removed_metrics.json"

REFERENCE_TEXT = "A quiet evening settles over the city. I speak clearly, naturally, and without rushing."
BASELINE_TEXT = "Một câu chuyện rõ ràng cần được kể liền mạch, có điểm nhấn đúng chỗ."
# Single experimental variable: comma removed. No other text, identity, or setting changes.
TARGET_TEXT = "Một câu chuyện rõ ràng cần được kể liền mạch có điểm nhấn đúng chỗ."


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
    if not (MODEL_CACHE / "model-bin.pt").is_file():
        raise SystemExit("MISSING_PHASE36D_MODEL_ARCHIVE")

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    config = ModelConfig(model_cache_dir=str(MODEL_CACHE))
    config_payload = config.to_dict()

    load_started = time.perf_counter()
    api = TTSApi(config)
    _ = api.engine  # Load ONNX sessions before timing the one synthesis call.
    model_load_seconds = time.perf_counter() - load_started

    total_started = time.perf_counter()
    synthesis_seconds = api.synthesize_to_file(
        TARGET_TEXT,
        str(OUTPUT_WAV),
        reference_audio=str(REFERENCE_WAV),
        reference_text=REFERENCE_TEXT,
    )
    total_seconds = time.perf_counter() - total_started

    metrics = audio_metrics(OUTPUT_WAV)
    metrics.update(
        {
            "phase": "36E",
            "renderer": "VietVoice-TTS",
            "experiment": "punctuation_only_comma_removed",
            "baseline_text": BASELINE_TEXT,
            "target_text_passed": TARGET_TEXT,
            "reference_wav": str(REFERENCE_WAV),
            "reference_text": REFERENCE_TEXT,
            "device": "CPUExecutionProvider",
            "onnx_available_providers": onnxruntime.get_available_providers(),
            "configuration": config_payload,
            "model_load_seconds": round(model_load_seconds, 6),
            "synthesis_seconds": round(synthesis_seconds, 6),
            "total_seconds": round(total_seconds, 6),
            "rtf": round(synthesis_seconds / metrics["duration_seconds"], 6),
            "peak_rss_mib": round(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1024, 3),
            "pid": os.getpid(),
        }
    )
    METRICS_JSON.write_text(json.dumps(metrics, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(metrics, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
