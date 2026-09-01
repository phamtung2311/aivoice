#!/usr/bin/env python3
"""Manual Phase 30K Qwen VoiceDesign refinement generator; CPU-only/offline."""
from __future__ import annotations

import gc
import json
import os
import resource
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
GENERATION = ROOT / "generation_3"
OUT = GENERATION / "reference_audio"
MEASUREMENTS = GENERATION / "measurements" / "source_generation.json"
PROMPTS = json.loads((GENERATION / "prompts.json").read_text(encoding="utf-8"))
IDENTITIES = ("K-A", "K-B", "K-C")


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
    return {"duration_seconds": round(float(mono.size / rate), 3), "sample_rate": int(rate), "channels": int(data.shape[1]), "peak": round(peak, 6), "rms": round(rms, 6), "clipped_samples": clipped, "clipping_ratio": round(clipped / max(1, mono.size), 8)}


def valid(metrics: dict) -> bool:
    return metrics["duration_seconds"] > 0 and metrics["clipping_ratio"] <= 0.01


def render(model: Qwen3TTSModel, identity: str, target: Path) -> dict:
    for attempt in (1, 2):
        temporary = target.with_name(f".{target.stem}.attempt{attempt}.tmp.wav")
        say(f"[{identity}] Generation attempt {attempt}/2...")
        started = time.perf_counter()
        try:
            with torch.inference_mode():
                wavs, rate = model.generate_voice_design(text=PROMPTS["english_reference_text"], language="English", instruct=PROMPTS["candidates"][identity])
            sf.write(temporary, wavs[0], rate)
            audio = analyze(temporary)
            record = {"identity": identity, "attempt": attempt, "generation_seconds": round(time.perf_counter() - started, 3), "peak_process_rss_mb": peak_rss_mb(), "prompt": PROMPTS["candidates"][identity], "audio": audio}
            if valid(audio):
                temporary.replace(target)
                return record
            say(f"[{identity}] Technical validation failed: {audio}.")
        except Exception as exc:
            record = {"identity": identity, "attempt": attempt, "generation_seconds": round(time.perf_counter() - started, 3), "error": repr(exc), "peak_process_rss_mb": peak_rss_mb(), "prompt": PROMPTS["candidates"][identity]}
            say(f"[{identity}] Generation exception: {exc!r}")
        if attempt == 2:
            raise RuntimeError(f"Candidate {identity} failed after one technical retry: {record}")
    raise AssertionError("unreachable")


def main() -> int:
    if not MODEL.is_dir() or not (MODEL / "model.safetensors").is_file() or not (MODEL / "speech_tokenizer" / "model.safetensors").is_file():
        raise SystemExit("LOCAL_MODEL_REQUIRED: official local VoiceDesign checkpoint is incomplete")
    if set(PROMPTS.get("candidates", {})) != set(IDENTITIES):
        raise SystemExit("exactly three K prompts are required")
    before = memory()
    say("[Phase30K] Offline mode enabled. CPU-only Qwen VoiceDesign runner.")
    say(f"[Phase30K] MemAvailable: {before['ram_available_bytes'] / 2**30:.2f} GiB; swap used: {before['swap_used_bytes'] / 2**30:.2f} GiB.")
    if before["ram_available_bytes"] < 7 * 2**30:
        raise SystemExit("QWEN_RAM_BLOCKED: MemAvailable is below 7 GiB; close applications manually and retry.")
    if before["ram_available_bytes"] < 8 * 2**30:
        say("[Phase30K] WARNING: MemAvailable is below preferred 8 GiB; continuing under the documented RAM-risk allowance.")
    OUT.mkdir(parents=True, exist_ok=True)
    MEASUREMENTS.parent.mkdir(parents=True, exist_ok=True)
    say("[Phase30K] Loading Qwen model...")
    loaded = time.perf_counter()
    model = Qwen3TTSModel.from_pretrained(str(MODEL), device_map="cpu", dtype=torch.bfloat16, attn_implementation="eager")
    after_load = memory()
    say(f"[Phase30K] Model loaded in {time.perf_counter() - loaded:.2f}s.")
    records = []
    try:
        for number, identity in enumerate(IDENTITIES, start=1):
            target = OUT / f"k_{identity[-1]}.wav"
            if target.is_file() and valid(analyze(target)):
                records.append({"identity": identity, "preserved_existing": True, "prompt": PROMPTS["candidates"][identity], "audio": analyze(target)})
                say(f"[{number}/3] {identity} already exists and is technically valid; preserving it.")
                continue
            say(f"[{number}/3] {identity} ...")
            record = render(model, identity, target)
            records.append(record)
            say(f"[{number}/3] {identity} saved. Duration: {record['audio']['duration_seconds']:.2f}s; generation time: {record['generation_seconds']:.2f}s.")
    finally:
        del model
        gc.collect()
    result = {"model": "Qwen/Qwen3-TTS-12Hz-1.7B-VoiceDesign", "offline": True, "device": "cpu", "dtype": "torch.bfloat16", "memory_before_load": before, "memory_after_load": after_load, "memory_after_unload": memory(), "records": records}
    MEASUREMENTS.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    say("[Phase30K] All three refinement source voices finished.")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        say(f"[Phase30K] FAILED: {exc!r}")
        raise
