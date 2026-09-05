#!/usr/bin/env python3
"""Phase 36J: one Vietnamese-reference VietVoice Candidate 03 PoC.

This script deliberately refuses to overwrite its sole output.  It performs
one synthesis only; all metrics and silence analysis are measurement-only.
"""
from __future__ import annotations

import json
import os
import re
import resource
import time
from pathlib import Path

import numpy as np
import onnxruntime
import soundfile as sf
from vietvoicetts import ModelConfig, TTSApi

HERE = Path(__file__).resolve().parent
WORKSPACE = HERE.parents[1]
REFERENCE_WAV = HERE / "bridge_reference" / "candidate03_vietnamese_bridge_vieneu.wav"
MODEL_CACHE = WORKSPACE / "experiments" / "brand_voice_phase36d" / "model_cache"
OUTPUT_DIR = HERE / "output"
OUTPUT_WAV = OUTPUT_DIR / "vietvoice_candidate03_vietnamese_bridge_speed1.wav"
METRICS_JSON = OUTPUT_DIR / "vietvoice_candidate03_vietnamese_bridge_speed1_metrics.json"

# Frozen Phase 36I Vietnamese bridge. Do not edit, trim, or post-process it.
REFERENCE_TEXT = "Hôm nay chúng ta cùng đi qua một câu chuyện ngắn với giọng kể rõ ràng và tự nhiên."
TARGET_TEXT = "Một câu chuyện rõ ràng cần được kể liền mạch, có điểm nhấn đúng chỗ."
SPEED = 1.0


def weighted_utf8_length(text: str, pause_punctuation: str) -> int:
    # Mirrors the installed VietVoice TextProcessor implementation exactly.
    return len(text.encode("utf-8")) + 3 * len(re.findall(pause_punctuation, text))


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


def low_energy(path: Path, threshold_dbfs: float = -40.0) -> dict:
    """Identical Phase 36F/36G/36H analysis; never changes the waveform."""
    audio, sample_rate = sf.read(path, always_2d=True)
    mono = audio.mean(axis=1, dtype=np.float64)
    frame, hop = int(0.020 * sample_rate), int(0.010 * sample_rate)
    starts = np.arange(0, len(mono) - frame + 1, hop)
    rms = np.array([np.sqrt(np.mean(mono[i:i + frame] ** 2)) for i in starts])
    silent = 20 * np.log10(np.maximum(rms, 1e-12)) <= threshold_dbfs
    regions, index = [], 0
    while index < len(silent):
        if not silent[index]:
            index += 1
            continue
        end_index = index + 1
        while end_index < len(silent) and silent[end_index]:
            end_index += 1
        start = starts[index] / sample_rate
        end = (starts[end_index - 1] + frame) / sample_rate
        if end - start >= 0.080:
            regions.append({"start": round(float(start), 3), "end": round(float(end), 3), "duration": round(float(end - start), 3)})
        index = end_index
    duration = len(mono) / sample_rate
    internal = [region for region in regions if region["start"] > 0.001 and region["end"] < duration - 0.020]
    return {
        "method": "20ms_RMS_10ms_hop_threshold_-40dBFS_min_region_80ms",
        "regions": regions,
        "leading_silence_seconds": regions[0]["duration"] if regions and regions[0]["start"] <= 0.001 else 0.0,
        "trailing_silence_seconds": regions[-1]["duration"] if regions and regions[-1]["end"] >= duration - 0.020 else 0.0,
        "internal_low_energy_total_seconds": round(sum(region["duration"] for region in internal), 3),
        "longest_internal_gap_seconds": max((region["duration"] for region in internal), default=0.0),
        "major_internal_gap_count": sum(1 for region in internal if region["duration"] >= 0.250),
    }


def main() -> None:
    if OUTPUT_WAV.exists() or METRICS_JSON.exists():
        raise SystemExit(f"REFUSING_TO_OVERWRITE_PHASE36J_ARTIFACT: {OUTPUT_WAV}")
    for required in (REFERENCE_WAV, MODEL_CACHE / "model-bin.pt"):
        if not required.is_file():
            raise SystemExit(f"MISSING_REQUIRED_ARTIFACT: {required}")

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    config = ModelConfig(model_cache_dir=str(MODEL_CACHE), speed=SPEED)
    reference_audio = audio_metrics(REFERENCE_WAV)
    reference_length = weighted_utf8_length(REFERENCE_TEXT, config.pause_punctuation)
    target_length = weighted_utf8_length(TARGET_TEXT, config.pause_punctuation)
    speaking_rate = reference_length / reference_audio["duration_seconds"]
    estimated_target_duration = target_length / speaking_rate / SPEED

    load_started = time.perf_counter()
    api = TTSApi(config)
    _ = api.engine
    model_load_seconds = time.perf_counter() - load_started
    total_started = time.perf_counter()
    synthesis_seconds = api.synthesize_to_file(
        TARGET_TEXT,
        str(OUTPUT_WAV),
        reference_audio=str(REFERENCE_WAV),
        reference_text=REFERENCE_TEXT,
    )
    total_seconds = time.perf_counter() - total_started

    output_audio = audio_metrics(OUTPUT_WAV)
    silence = low_energy(OUTPUT_WAV)
    metrics = {
        "phase": "36J",
        "renderer": "VietVoice-TTS",
        "experiment": "vietnamese_to_vietnamese_reference_bridge",
        "reference_wav": str(REFERENCE_WAV),
        "reference_text": REFERENCE_TEXT,
        "reference_audio": reference_audio,
        "target_text_passed": TARGET_TEXT,
        "duration_formula": {
            "pause_punctuation": config.pause_punctuation,
            "reference_weighted_utf8_length": reference_length,
            "target_weighted_utf8_length": target_length,
            "speaking_rate_weighted_bytes_per_second": round(speaking_rate, 9),
            "estimated_target_duration_seconds": round(estimated_target_duration, 9),
        },
        "configuration": config.to_dict(),
        "device": "CPUExecutionProvider",
        "onnx_available_providers": onnxruntime.get_available_providers(),
        "model_load_seconds": round(model_load_seconds, 6),
        "synthesis_seconds": round(synthesis_seconds, 6),
        "total_seconds": round(total_seconds, 6),
        "rtf": round(synthesis_seconds / output_audio["duration_seconds"], 6),
        "peak_rss_mib": round(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1024, 3),
        "audio": output_audio,
        "low_energy_analysis": silence,
        "comparison": {
            "phase36d": {"internal_low_energy_total_seconds": 3.23, "longest_internal_gap_seconds": 0.93, "major_internal_gap_count": 5},
            "phase36g": {"internal_low_energy_total_seconds": 0.83, "longest_internal_gap_seconds": 0.45, "major_internal_gap_count": 2},
            "phase36h": {"internal_low_energy_total_seconds": 2.07, "longest_internal_gap_seconds": 0.88, "major_internal_gap_count": 3},
            "phase36j": {key: silence[key] for key in ("internal_low_energy_total_seconds", "longest_internal_gap_seconds", "major_internal_gap_count")},
        },
        "pid": os.getpid(),
    }
    METRICS_JSON.write_text(json.dumps(metrics, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(metrics, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
