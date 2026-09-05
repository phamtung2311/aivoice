#!/usr/bin/env python3
"""Prepared only for a future Phase 36I bridge render; never overwrites output."""
from __future__ import annotations

import hashlib
import json
import resource
import sys
import time
from pathlib import Path

import numpy as np
import soundfile as sf

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(ROOT))
ANCHOR = ROOT / "experiments/brand_speaker_phase33c/baseline_anchor/BRAND_CANDIDATE_03_BASELINE"
OUTPUT = HERE / "bridge_reference/candidate03_vietnamese_bridge_vieneu.wav"
METRICS = HERE / "bridge_reference/candidate03_vietnamese_bridge_vieneu_metrics.json"

REFERENCE_TEXT = "Hôm nay chúng ta cùng đi qua một câu chuyện ngắn với giọng kể rõ ràng và tự nhiên."
CONFIG = {"temperature": 0.82, "top_k": 25, "top_p": 0.97, "repetition_penalty": 1.15, "speed": 1.0, "max_chunk_chars": 240, "denoise": False, "use_ref_codes": True, "seed": 34001}


def audio_metrics(path: Path) -> dict:
    data, sr = sf.read(path, always_2d=True)
    mono = data.mean(axis=1)
    return {"duration_seconds": round(len(mono) / sr, 6), "sample_rate": int(sr), "channels": int(data.shape[1]), "peak": round(float(np.max(np.abs(mono))), 8), "rms": round(float(np.sqrt(np.mean(mono * mono))), 8), "clipped_samples": int(np.count_nonzero(np.abs(mono) >= .999)), "sha256": hashlib.sha256(path.read_bytes()).hexdigest()}


def main() -> None:
    if OUTPUT.exists(): raise SystemExit(f"REFUSING_TO_OVERWRITE_EXISTING_OUTPUT: {OUTPUT}")
    emb_path, codes_path = ANCHOR / "speaker_emb.npy", ANCHOR / "reference_codes.npy"
    if not emb_path.is_file() or not codes_path.is_file(): raise SystemExit("MISSING_FROZEN_CANDIDATE03_CONDITIONING")
    embedding, codes = np.load(emb_path, allow_pickle=False), np.load(codes_path, allow_pickle=False)
    if embedding.shape != (192,) or codes.shape != (87, 16): raise SystemExit("FROZEN_CONDITIONING_SHAPE_INVALID")
    from backend.app.tts.engine import TTSEngine
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    temp = OUTPUT.with_name(f".{OUTPUT.stem}.tmp.wav")
    started = time.perf_counter(); np.random.seed(CONFIG["seed"])
    engine = TTSEngine(backend="onnx")
    try:
        engine.generate(REFERENCE_TEXT, voice={"speaker_emb": embedding, "codes": codes}, speed=CONFIG["speed"], out_path=str(temp), max_chunk_chars=CONFIG["max_chunk_chars"], denoise=CONFIG["denoise"], use_ref_codes=CONFIG["use_ref_codes"], quality_diagnostics=True, temperature=CONFIG["temperature"], top_k=CONFIG["top_k"], top_p=CONFIG["top_p"], repetition_penalty=CONFIG["repetition_penalty"])
        temp.replace(OUTPUT)
    finally:
        del engine
    result = {"phase": "36I", "purpose": "synthetic_vietnamese_bridge_reference", "canonical_anchor": str(ANCHOR), "reference_text": REFERENCE_TEXT, "configuration": CONFIG, "generation_seconds": round(time.perf_counter() - started, 6), "peak_rss_mib": round(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1024, 3), "audio": audio_metrics(OUTPUT)}
    METRICS.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__": main()
