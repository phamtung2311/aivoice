#!/usr/bin/env python3
"""Phase 36G: one combined duration + comma-removal probe; no retry/no overwrite."""
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
REFERENCE_WAV = (HERE.parent / "brand_speaker_phase33c/baseline_anchor/BRAND_CANDIDATE_03_BASELINE/qwen_source.wav").resolve()
MODEL_CACHE = HERE / "model_cache"
OUTPUT_DIR = HERE / "output"
BASELINE_WAV = OUTPUT_DIR / "vietvoice_candidate03_raw.wav"
PHASE36F_METRICS = OUTPUT_DIR / "vietvoice_candidate03_phase36f_duration_probe_metrics.json"
OUTPUT_WAV = OUTPUT_DIR / "vietvoice_candidate03_phase36g_combined_continuity.wav"
METRICS_JSON = OUTPUT_DIR / "vietvoice_candidate03_phase36g_combined_continuity_metrics.json"

REFERENCE_TEXT = "A quiet evening settles over the city. I speak clearly, naturally, and without rushing."
TARGET_TEXT = "Một câu chuyện rõ ràng cần được kể liền mạch có điểm nhấn đúng chỗ."
SPEED = 1.2933333333333332


def audio_metrics(path: Path) -> dict[str, float | int]:
    audio, sample_rate = sf.read(path, always_2d=True)
    mono = audio.mean(axis=1, dtype=np.float64)
    peak = float(np.max(np.abs(mono))) if len(mono) else 0.0
    rms = float(np.sqrt(np.mean(np.square(mono)))) if len(mono) else 0.0
    return {"duration_seconds": round(len(mono) / sample_rate, 6), "sample_rate": int(sample_rate), "channels": int(audio.shape[1]), "peak": round(peak, 8), "rms": round(rms, 8), "clipped_samples": int(np.count_nonzero(np.abs(mono) >= 0.999))}


def low_energy_analysis(path: Path, threshold_dbfs: float = -40.0) -> dict:
    """Same Phase 36F method: 20ms RMS, 10ms hop, 80ms minimum region."""
    audio, sample_rate = sf.read(path, always_2d=True)
    mono = audio.mean(axis=1, dtype=np.float64)
    frame, hop = int(.020 * sample_rate), int(.010 * sample_rate)
    starts = np.arange(0, len(mono) - frame + 1, hop)
    rms = np.array([np.sqrt(np.mean(mono[i:i + frame] ** 2)) for i in starts])
    silent = 20 * np.log10(np.maximum(rms, 1e-12)) <= threshold_dbfs
    regions, i = [], 0
    while i < len(silent):
        if not silent[i]:
            i += 1
            continue
        j = i + 1
        while j < len(silent) and silent[j]:
            j += 1
        start, end = starts[i] / sample_rate, (starts[j - 1] + frame) / sample_rate
        if end - start >= .080:
            regions.append({"start": round(float(start), 3), "end": round(float(end), 3), "duration": round(float(end - start), 3)})
        i = j
    duration = len(mono) / sample_rate
    internal = [r for r in regions if r["start"] > .001 and r["end"] < duration - .020]
    return {
        "method": "20ms_RMS_10ms_hop_threshold_-40dBFS_min_region_80ms",
        "regions": regions,
        "leading_silence_seconds": regions[0]["duration"] if regions and regions[0]["start"] <= .001 else 0.0,
        "trailing_silence_seconds": regions[-1]["duration"] if regions and regions[-1]["end"] >= duration - .020 else 0.0,
        "internal_low_energy_total_seconds": round(sum(r["duration"] for r in internal), 3),
        "longest_internal_gap_seconds": max((r["duration"] for r in internal), default=0.0),
        "major_internal_gap_count": sum(1 for r in internal if r["duration"] >= .250),
    }


def main() -> None:
    if OUTPUT_WAV.exists():
        raise SystemExit(f"REFUSING_TO_OVERWRITE_EXISTING_OUTPUT: {OUTPUT_WAV}")
    for required in (REFERENCE_WAV, BASELINE_WAV, PHASE36F_METRICS, MODEL_CACHE / "model-bin.pt"):
        if not required.is_file():
            raise SystemExit(f"MISSING_REQUIRED_ARTIFACT: {required}")
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    config = ModelConfig(model_cache_dir=str(MODEL_CACHE), speed=SPEED)
    load_started = time.perf_counter()
    api = TTSApi(config)
    _ = api.engine
    model_load_seconds = time.perf_counter() - load_started
    total_started = time.perf_counter()
    synthesis_seconds = api.synthesize_to_file(TARGET_TEXT, str(OUTPUT_WAV), reference_audio=str(REFERENCE_WAV), reference_text=REFERENCE_TEXT)
    total_seconds = time.perf_counter() - total_started
    phase36f = json.loads(PHASE36F_METRICS.read_text(encoding="utf-8"))
    silence = low_energy_analysis(OUTPUT_WAV)
    metrics = audio_metrics(OUTPUT_WAV)
    metrics.update({
        "phase": "36G", "renderer": "VietVoice-TTS", "experiment": "combined_duration_correction_and_comma_removed",
        "reference_wav": str(REFERENCE_WAV), "reference_text": REFERENCE_TEXT, "target_text_passed": TARGET_TEXT,
        "speed": SPEED, "expected_target_duration_seconds": 5.938144, "device": "CPUExecutionProvider",
        "onnx_available_providers": onnxruntime.get_available_providers(), "configuration": config.to_dict(),
        "model_load_seconds": round(model_load_seconds, 6), "synthesis_seconds": round(synthesis_seconds, 6), "total_seconds": round(total_seconds, 6),
        "rtf": round(synthesis_seconds / metrics["duration_seconds"], 6), "peak_rss_mib": round(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1024, 3),
        "low_energy_analysis": silence,
        "comparison": {
            "phase36d": {"internal_low_energy_total_seconds": 3.23, "longest_internal_gap_seconds": .93, "major_internal_gap_count": 5},
            "phase36f": phase36f["low_energy_analysis"],
            "phase36g": {key: silence[key] for key in ("internal_low_energy_total_seconds", "longest_internal_gap_seconds", "major_internal_gap_count")},
        },
        "pid": os.getpid(),
    })
    METRICS_JSON.write_text(json.dumps(metrics, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(metrics, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
