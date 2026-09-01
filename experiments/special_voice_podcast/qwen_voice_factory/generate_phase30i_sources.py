#!/usr/bin/env python3
"""Manual Phase 30I Qwen VoiceDesign source generator; CPU-only and offline."""
from __future__ import annotations

import gc
import json
import os
import resource
import sys
import time
from pathlib import Path

os.environ.setdefault("HF_HUB_OFFLINE", "1")
os.environ.setdefault("TRANSFORMERS_OFFLINE", "1")

import numpy as np
import psutil
import soundfile as sf
import torch
from qwen_tts import Qwen3TTSModel

ROOT = Path(__file__).resolve().parent
MODEL = ROOT / "models" / "Qwen3-TTS-12Hz-1.7B-VoiceDesign"
OUT = ROOT / "reference_audio"
MEASUREMENTS = ROOT / "measurements" / "source_generation.json"
PROMPTS = json.loads((ROOT / "prompts.json").read_text(encoding="utf-8"))


def say(message: str) -> None:
    print(message, flush=True)


def memory() -> dict:
    vm, sw = psutil.virtual_memory(), psutil.swap_memory()
    return {"ram_total_bytes": vm.total, "ram_available_bytes": vm.available, "ram_used_bytes": vm.used, "swap_used_bytes": sw.used}


def peak_rss_mb() -> float:
    return round(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1024, 2)


def analyze(path: Path) -> dict:
    data, rate = sf.read(path, always_2d=True)
    mono = data.mean(axis=1)
    peak = float(np.max(np.abs(mono))) if mono.size else 0.0
    rms = float(np.sqrt(np.mean(np.square(mono)))) if mono.size else 0.0
    clipped = int(np.count_nonzero(np.abs(mono) >= 0.999))
    active = np.flatnonzero(np.abs(mono) > 0.001)
    return {"duration_seconds": round(float(mono.size / rate), 3), "sample_rate": int(rate), "channels": int(data.shape[1]), "peak": round(peak, 6), "rms": round(rms, 6), "clipped_samples": clipped, "clipping_ratio": round(clipped / max(1, mono.size), 8), "leading_silence_seconds": round(float(active[0] / rate), 3) if active.size else round(float(mono.size / rate), 3), "trailing_silence_seconds": round(float((mono.size - 1 - active[-1]) / rate), 3) if active.size else round(float(mono.size / rate), 3)}


def valid(metrics: dict) -> bool:
    return metrics["duration_seconds"] > 0 and metrics["clipping_ratio"] <= 0.01


def render(model: Qwen3TTSModel, identity: str, target: Path) -> dict:
    for attempt in (1, 2):
        say(f"[{identity}] Generation attempt {attempt}/2...")
        started = time.perf_counter()
        try:
            with torch.inference_mode():
                wavs, rate = model.generate_voice_design(text=PROMPTS["english_reference_text"], language="English", instruct=PROMPTS["candidates"][identity])
            sf.write(target, wavs[0], rate)
            metrics = analyze(target)
            record = {"identity": identity, "attempt": attempt, "generation_seconds": round(time.perf_counter() - started, 3), "peak_process_rss_mb": peak_rss_mb(), "audio": metrics}
            if valid(metrics):
                return record
            say(f"[{identity}] Technical validation failed: {metrics}." )
        except Exception as exc:
            record = {"identity": identity, "attempt": attempt, "generation_seconds": round(time.perf_counter() - started, 3), "error": repr(exc), "peak_process_rss_mb": peak_rss_mb()}
            say(f"[{identity}] Generation exception: {exc!r}")
        if attempt == 2:
            raise RuntimeError(f"Candidate {identity} failed after one technical retry: {record}")
    raise AssertionError("unreachable")


def main() -> int:
    if not MODEL.is_dir() or not (MODEL / "model.safetensors").is_file() or not (MODEL / "speech_tokenizer" / "model.safetensors").is_file():
        raise SystemExit("LOCAL_MODEL_REQUIRED: official local VoiceDesign checkpoint is incomplete")
    before = memory()
    say("[Phase30I] Offline mode enabled. CPU-only Qwen VoiceDesign runner.")
    say(f"[Phase30I] MemAvailable: {before['ram_available_bytes'] / 2**30:.2f} GiB; swap used: {before['swap_used_bytes'] / 2**30:.2f} GiB.")
    if before["ram_available_bytes"] < 7 * 2**30:
        raise SystemExit("QWEN_RAM_BLOCKED: MemAvailable is below 7 GiB; close applications manually and retry.")
    if before["ram_available_bytes"] < 8 * 2**30:
        say("[Phase30I] WARNING: MemAvailable is below preferred 8 GiB; continuing under the documented RAM-risk allowance.")
    OUT.mkdir(parents=True, exist_ok=True); MEASUREMENTS.parent.mkdir(parents=True, exist_ok=True)
    say("[Phase30I] Loading Qwen model...")
    started = time.perf_counter()
    model = Qwen3TTSModel.from_pretrained(str(MODEL), device_map="cpu", dtype=torch.bfloat16, attn_implementation="eager")
    after_load = memory()
    say(f"[Phase30I] Model loaded in {time.perf_counter() - started:.2f}s.")
    records = []
    try:
        for number, identity in enumerate(("A", "B", "C"), start=1):
            target = OUT / f"qwen_candidate_{identity}.wav"
            if target.is_file():
                existing = analyze(target)
                if valid(existing):
                    say(f"[{number}/3] Candidate {identity} already exists and is technically valid; preserving it.")
                    records.append({"identity": identity, "preserved_existing": True, "audio": existing})
                    continue
            say(f"[{number}/3] Generating Candidate {identity}...")
            record = render(model, identity, target)
            records.append(record)
            say(f"[{number}/3] Candidate {identity} saved. Duration: {record['audio']['duration_seconds']:.2f}s; generation time: {record['generation_seconds']:.2f}s.")
    finally:
        del model
        gc.collect()
    result = {"model": "Qwen/Qwen3-TTS-12Hz-1.7B-VoiceDesign", "offline": True, "device": "cpu", "dtype": "torch.bfloat16", "memory_before_load": before, "memory_after_load": after_load, "memory_after_unload": memory(), "records": records}
    MEASUREMENTS.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    say("[Phase30I] All source voices generated.")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        say(f"[Phase30I] FAILED: {exc!r}")
        raise
