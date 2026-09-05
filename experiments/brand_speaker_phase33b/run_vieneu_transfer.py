#!/usr/bin/env python3
"""Stage 2 of Phase 33B, run in the existing local VieNeu environment only."""
from __future__ import annotations

import gc
import hashlib
import json
import random
import resource
import sys
import time
from pathlib import Path

import numpy as np
import soundfile as sf

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(ROOT))

SOURCES = HERE / "sources"
CONDITIONING = HERE / "conditioning"
RAW = HERE / "raw_vietnamese"
AUDITION = HERE / "audition"
TMP = HERE / "tmp_vieneu"
METRICS = HERE / "metrics" / "metrics.json"
PRIVATE_MAPPING = HERE / "private_mapping.json"
IDENTITIES = ("A", "B", "C", "D")
TEXT = (
    "Có những ngày chúng ta không cần phải nói thật nhiều. Chỉ cần một giọng nói rõ ràng, "
    "một nhịp kể vừa phải, và vài phút bình yên để nghe lại điều mình đang nghĩ. "
    "Câu chuyện này bắt đầu rất đơn giản, rồi từ từ mở ra theo cách tự nhiên nhất."
)
SAMPLING = {"temperature": 0.80, "top_k": 25, "top_p": 0.95, "repetition_penalty": 1.20}
SEED, TARGET_RMS, PEAK_CEILING = 33117, 0.09, 0.95


def say(message: str) -> None:
    print(message, flush=True)


def metrics(path: Path) -> dict:
    data, rate = sf.read(path, always_2d=True)
    mono = data.mean(axis=1)
    peak = float(np.max(np.abs(mono))) if mono.size else 0.0
    rms = float(np.sqrt(np.mean(np.square(mono)))) if mono.size else 0.0
    clipped = int(np.count_nonzero(np.abs(mono) >= 0.999))
    return {
        "duration_seconds": round(float(mono.size / rate), 3), "sample_rate": int(rate),
        "channels": int(data.shape[1]), "peak": round(peak, 6), "rms": round(rms, 6),
        "clipped_samples": clipped, "clipping_ratio": round(clipped / max(1, mono.size), 8),
        "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
    }


def valid(item: dict, rate: int | None = None) -> bool:
    return item["duration_seconds"] > 0 and item["channels"] == 1 and item["clipping_ratio"] <= .01 and (rate is None or item["sample_rate"] == rate)


def normalized(data: np.ndarray) -> tuple[np.ndarray, float]:
    data = np.asarray(data, dtype=np.float32)
    rms, peak = float(np.sqrt(np.mean(data * data))), float(np.max(np.abs(data)))
    gain = TARGET_RMS / rms if rms > 1e-9 else 1.0
    if peak > 1e-9:
        gain = min(gain, PEAK_CEILING / peak)
    return (data * gain).astype(np.float32), round(gain, 6)


def main() -> int:
    from backend.app.tts.engine import TTSEngine
    for directory in (CONDITIONING, RAW, AUDITION, TMP, METRICS.parent):
        directory.mkdir(parents=True, exist_ok=True)
    source_rows = []
    for identity in IDENTITIES:
        source = SOURCES / f"source_{identity}.wav"
        if not source.is_file() or not valid(metrics(source)):
            raise SystemExit(f"SOURCE_MISSING_OR_INVALID: {identity}")
        source_rows.append({"identity": identity, "audio": metrics(source)})
    engine = TTSEngine(backend="onnx")
    transfer_rows = []
    try:
        for number, identity in enumerate(IDENTITIES, 1):
            source = SOURCES / f"source_{identity}.wav"
            emb_file, code_file = CONDITIONING / f"speaker_emb_{identity}.npy", CONDITIONING / f"reference_codes_{identity}.npy"
            if emb_file.exists() != code_file.exists():
                raise SystemExit(f"INCOMPLETE_CONDITIONING: {identity}")
            if emb_file.exists():
                emb, codes, encode_seconds = np.load(emb_file, allow_pickle=False), np.load(code_file, allow_pickle=False), None
            else:
                started = time.perf_counter()
                # VieNeu v3.3.0 otherwise defaults its private cleaned-reference
                # temp file to ~/.cache, which is read-only in this isolated
                # runner. Route only that ephemeral file into this experiment;
                # no HOME override and no production cache is touched.
                native = engine._model._v
                original_preclean = native._preclean_reference_audio
                clean_path = TMP / f"preclean_{identity}.wav"
                native._preclean_reference_audio = lambda ref_audio, **_kwargs: original_preclean(ref_audio, out_path=clean_path)
                try:
                    emb, codes = engine._model.encode_reference(str(source), denoise=False, use_ref_codes=True)
                finally:
                    native._preclean_reference_audio = original_preclean
                encode_seconds = round(time.perf_counter() - started, 3)
                np.save(emb_file, np.asarray(emb)); np.save(code_file, np.asarray(codes))
            if np.asarray(emb).shape != (192,) or np.asarray(codes).ndim != 2:
                raise RuntimeError(f"CONDITIONING_SHAPE_INVALID: {identity}")
            target = RAW / f"vietnamese_{identity}.wav"
            if target.is_file() and valid(metrics(target), 48000):
                transfer_rows.append({"identity": identity, "preserved_existing": True, "audio": metrics(target)})
                continue
            temporary = target.with_name(f".{target.stem}.tmp.wav")
            started = time.perf_counter()
            np.random.seed(SEED)
            say(f"[VieNeu {number}/4] Generating transferred Vietnamese probe.")
            engine.generate(TEXT, voice={"speaker_emb": emb, "codes": codes}, speed=1.0, out_path=str(temporary), max_chunk_chars=240, denoise=False, use_ref_codes=True, quality_diagnostics=True, **SAMPLING)
            item = metrics(temporary)
            if not valid(item, 48000):
                raise RuntimeError(f"VIENEU_OUTPUT_INVALID {identity}: {item}")
            temporary.replace(target)
            transfer_rows.append({"identity": identity, "encode_seconds": encode_seconds, "generation_seconds": round(time.perf_counter() - started, 3), "speaker_emb_shape": list(np.asarray(emb).shape), "reference_codes_shape": list(np.asarray(codes).shape), "peak_process_rss_mb": round(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1024, 2), "audio": metrics(target), "generation_diagnostics": engine.last_generation_diagnostics})
    finally:
        del engine; gc.collect()
    if PRIVATE_MAPPING.exists():
        mapping = json.loads(PRIVATE_MAPPING.read_text(encoding="utf-8"))
        if set(mapping) != {f"Candidate {i:02d}.wav" for i in range(1, 5)} or set(mapping.values()) != set(IDENTITIES):
            raise SystemExit("PRIVATE_MAPPING_INVALID")
    else:
        shuffled = list(IDENTITIES); random.Random(SEED).shuffle(shuffled)
        mapping = {f"Candidate {i:02d}.wav": identity for i, identity in enumerate(shuffled, 1)}
    presentation = {}
    for public_name, identity in mapping.items():
        data, rate = sf.read(RAW / f"vietnamese_{identity}.wav", dtype="float32", always_2d=False)
        copy, gain = normalized(data)
        target = AUDITION / public_name
        sf.write(target, copy, rate, subtype="PCM_16")
        item = metrics(target)
        if item["clipped_samples"]:
            raise RuntimeError(f"AUDITION_CLIPPED: {public_name}")
        presentation[public_name] = {"gain": gain, "audio": item}
    PRIVATE_MAPPING.write_text(json.dumps(mapping, indent=2) + "\n", encoding="utf-8")
    result = {"phase": "33B", "device": "cpu", "source_text_language": "English", "vietnamese_text": TEXT, "settings": {"sampling": SAMPLING, "speed": 1.0, "max_chunk_chars": 240, "denoise": False, "use_ref_codes": True, "seed": SEED}, "sources": source_rows, "transfers": transfer_rows, "audition_presentation": presentation}
    METRICS.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    say("PHASE33B_WIDE_CAST_AUDITION_READY")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
