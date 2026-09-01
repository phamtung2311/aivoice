#!/usr/bin/env python3
"""Standalone CPU load measurement for the locally acquired Phase 30I model."""
from __future__ import annotations

import gc
import json
import resource
import time
from pathlib import Path

import psutil
import torch
from qwen_tts import Qwen3TTSModel

ROOT = Path(__file__).resolve().parent
MODEL = ROOT / "models" / "Qwen3-TTS-12Hz-1.7B-VoiceDesign"


def memory() -> dict:
    vm, sw = psutil.virtual_memory(), psutil.swap_memory()
    return {"ram_available_bytes": vm.available, "ram_used_bytes": vm.used, "swap_used_bytes": sw.used}


def main() -> int:
    before = memory(); started = time.perf_counter()
    model = Qwen3TTSModel.from_pretrained(str(MODEL), device_map="cpu", dtype=torch.bfloat16, attn_implementation="eager")
    after = memory()
    result = {"device": "cpu", "dtype": "torch.bfloat16", "memory_before_load": before, "load_seconds": round(time.perf_counter() - started, 3), "memory_after_load": after, "peak_process_rss_mb": round(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1024, 2)}
    (ROOT / "measurements").mkdir(exist_ok=True)
    (ROOT / "measurements" / "qwen_load_test.json").write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2))
    del model; gc.collect()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
