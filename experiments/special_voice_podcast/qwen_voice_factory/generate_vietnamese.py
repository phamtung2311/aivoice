#!/usr/bin/env python3
"""Phase 30I: pass all three Qwen references through the existing VieNeu path."""
from __future__ import annotations

import gc
import json
import os
import random
import resource
import shutil
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent
PROJECT = ROOT.parents[2]
sys.path.insert(0, str(PROJECT))
PROMPTS = json.loads((ROOT / "prompts.json").read_text(encoding="utf-8"))


def rss_mb() -> float:
    return resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1024


def audio_metrics(path: Path) -> dict:
    import numpy as np
    import soundfile as sf
    samples, sample_rate = sf.read(path, always_2d=True)
    mono = samples.mean(axis=1)
    peak = float(np.max(np.abs(mono))) if mono.size else 0.0
    rms = float(np.sqrt(np.mean(np.square(mono)))) if mono.size else 0.0
    clipped = int(np.count_nonzero(np.abs(mono) >= 0.999))
    return {"duration_seconds": round(float(mono.size / sample_rate), 3), "sample_rate": int(sample_rate), "channels": int(samples.shape[1]), "peak": round(peak, 6), "rms": round(rms, 6), "clipped_samples": clipped, "clipping_ratio": round(clipped / max(1, mono.size), 8)}


def technically_valid(metrics: dict) -> bool:
    return metrics["duration_seconds"] > 0 and metrics["clipping_ratio"] <= 0.01


def main() -> int:
    import numpy as np
    from backend.app.tts.engine import TTSEngine
    refs = {identity: ROOT / "reference_audio" / f"qwen_candidate_{identity}.wav" for identity in ("A", "B", "C")}
    if not all(path.is_file() for path in refs.values()):
        raise SystemExit("all three Qwen references are required")
    out = ROOT / "vietnamese_outputs"; audition = ROOT / "audition"
    if any(audition.glob("*.wav")):
        raise SystemExit("refusing to overwrite audition artifacts")
    out.mkdir(parents=True, exist_ok=True); audition.mkdir(parents=True, exist_ok=True)
    engine = TTSEngine(backend="onnx")
    # VieNeu's existing reference path writes only a transient pre-clean WAV under
    # Path.home()/.cache/vieneu/tmp. Keep that per-process scratch file isolated
    # and writable without changing the installed production package or its cache.
    runtime_home = ROOT / ".vieneu_runtime_home"
    (runtime_home / ".cache" / "vieneu" / "tmp").mkdir(parents=True, exist_ok=True)
    os.environ["HOME"] = str(runtime_home)
    records = []
    for identity, ref in refs.items():
        source_metrics = audio_metrics(ref)
        if not technically_valid(source_metrics):
            raise SystemExit(f"invalid Qwen source for {identity}: {source_metrics}")
        target = out / f"vietnamese_candidate_{identity}.wav"
        if target.is_file():
            existing = audio_metrics(target)
            if technically_valid(existing):
                records.append({"identity": identity, "source_audio": source_metrics, "preserved_existing": True, "audio": existing})
                continue
        enc_started = time.perf_counter()
        speaker_emb, codes = engine._model.encode_reference(str(ref), denoise=False, use_ref_codes=True)
        encode_seconds = time.perf_counter() - enc_started
        voice = {"speaker_emb": speaker_emb, "codes": codes}
        generated = None
        for attempt in (1, 2):
            np.random.seed(30109)
            started = time.perf_counter()
            engine.generate(PROMPTS["vietnamese_test_text"], voice=voice, speed=1.0, out_path=str(target), denoise=False, use_ref_codes=True, quality_diagnostics=True)
            generated = audio_metrics(target)
            generation_seconds = round(time.perf_counter() - started, 3)
            if technically_valid(generated):
                break
            if attempt == 2:
                raise SystemExit(f"technical VieNeu output failure for {identity}: {generated}")
        records.append({"identity": identity, "source_audio": source_metrics, "encode_seconds": round(encode_seconds, 3), "generation_seconds": generation_seconds, "audio": generated, "peak_process_rss_mb": round(rss_mb(), 2), "speaker_emb_shape": list(getattr(speaker_emb, "shape", [])), "codes_shape": list(getattr(codes, "shape", []))})
    mapping = list(("A", "B", "C")); random.Random(30109).shuffle(mapping)
    private = {}
    for number, identity in enumerate(mapping, start=1):
        shutil.copy2(refs[identity], audition / f"source_{number:02d}.wav")
        shutil.copy2(out / f"vietnamese_candidate_{identity}.wav", audition / f"vietnamese_{number:02d}.wav")
        private[f"{number:02d}"] = identity
    (ROOT / "private_mapping.json").write_text(json.dumps(private, indent=2) + "\n", encoding="utf-8")
    (ROOT / "measurements" / "vieneu_generation.json").write_text(json.dumps({"records": records}, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    del engine; gc.collect()
    print(json.dumps({"records": records, "audition_files": 6}, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
