#!/usr/bin/env python3
"""Phase 30I: exactly three Qwen VoiceDesign source references, CPU only."""
from __future__ import annotations

import gc
import json
import resource
import time
from pathlib import Path

import numpy as np
import psutil
import soundfile as sf
import torch
from qwen_tts import Qwen3TTSModel

ROOT = Path(__file__).resolve().parent
MODEL = ROOT / "models" / "Qwen3-TTS-12Hz-1.7B-VoiceDesign"
OUT = ROOT / "reference_audio"
PROMPTS = json.loads((ROOT / "prompts.json").read_text(encoding="utf-8"))


def memory() -> dict:
    vm, sw = psutil.virtual_memory(), psutil.swap_memory()
    return {"ram_available_bytes": vm.available, "ram_used_bytes": vm.used, "swap_used_bytes": sw.used}


def rss_mb() -> float:
    return resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1024


def audio_metrics(path: Path) -> dict:
    samples, sample_rate = sf.read(path, always_2d=True)
    mono = samples.mean(axis=1)
    peak = float(np.max(np.abs(mono))) if mono.size else 0.0
    rms = float(np.sqrt(np.mean(np.square(mono)))) if mono.size else 0.0
    clipped = int(np.count_nonzero(np.abs(mono) >= 0.999))
    threshold = 0.001
    active = np.flatnonzero(np.abs(mono) > threshold)
    leading = float(active[0] / sample_rate) if active.size else float(mono.size / sample_rate)
    trailing = float((mono.size - 1 - active[-1]) / sample_rate) if active.size else float(mono.size / sample_rate)
    return {"duration_seconds": round(float(mono.size / sample_rate), 3), "sample_rate": int(sample_rate), "channels": int(samples.shape[1]), "peak": round(peak, 6), "rms": round(rms, 6), "clipped_samples": clipped, "leading_silence_seconds": round(leading, 3), "trailing_silence_seconds": round(trailing, 3)}


def main() -> int:
    if not MODEL.is_dir() or not (MODEL / "model.safetensors").is_file():
        raise SystemExit("local VoiceDesign checkpoint missing")
    OUT.mkdir(parents=True, exist_ok=True)
    existing = list(OUT.glob("qwen_candidate_*.wav"))
    if existing:
        raise SystemExit("refusing to overwrite existing Qwen candidates")
    before = memory()
    load_started = time.perf_counter()
    model = Qwen3TTSModel.from_pretrained(str(MODEL), device_map="cpu", dtype=torch.bfloat16, attn_implementation="eager")
    load_seconds = time.perf_counter() - load_started
    after_load = memory()
    records = []
    for identity in ("A", "B", "C"):
        started = time.perf_counter()
        wavs, sample_rate = model.generate_voice_design(text=PROMPTS["english_reference_text"], language="English", instruct=PROMPTS["candidates"][identity])
        path = OUT / f"qwen_candidate_{identity}.wav"
        sf.write(path, wavs[0], sample_rate)
        record = {"identity": identity, "generation_seconds": round(time.perf_counter() - started, 3), "peak_process_rss_mb": round(rss_mb(), 2), "audio": audio_metrics(path)}
        if record["audio"]["duration_seconds"] <= 0 or record["audio"]["clipped_samples"] > 0:
            raise SystemExit(f"technical Qwen output failure for {identity}: {record}")
        records.append(record)
    del model
    gc.collect()
    payload = {"device": "cpu", "dtype": "torch.bfloat16", "memory_before_load": before, "load_seconds": round(load_seconds, 3), "memory_after_load": after_load, "peak_process_rss_mb": round(rss_mb(), 2), "records": records, "memory_after_unload": memory()}
    (ROOT / "measurements" / "qwen_generation.json").parent.mkdir(parents=True, exist_ok=True)
    (ROOT / "measurements" / "qwen_generation.json").write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
