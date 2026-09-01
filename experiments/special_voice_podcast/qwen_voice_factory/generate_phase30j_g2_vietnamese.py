#!/usr/bin/env python3
"""Phase 30J G2: independent VieNeu bridge and a private blind audition."""
from __future__ import annotations

import gc
import hashlib
import json
import os
import random
import resource
import shutil
import sys
import time
from pathlib import Path

import numpy as np
import soundfile as sf

ROOT = Path(__file__).resolve().parent
PROJECT = ROOT.parents[2]
GENERATION = ROOT / "generation_2"
SOURCES = GENERATION / "reference_audio"
OUTPUTS = GENERATION / "vietnamese_outputs"
CONDITIONING = GENERATION / "conditioning"
AUDITION = GENERATION / "audition"
MEASUREMENTS = GENERATION / "measurements" / "vieneu_generation.json"
SOURCE_MEASUREMENTS = json.loads((GENERATION / "measurements" / "source_generation.json").read_text(encoding="utf-8"))
PROMPTS = json.loads((GENERATION / "prompts.json").read_text(encoding="utf-8"))
IDENTITIES = ("G2-A", "G2-B", "G2-C", "G2-D", "G2-E", "G2-F")
VIETNAMESE_TEXT = "Có những câu chuyện không cần phải kể thật nhanh. Chỉ cần một giọng nói đủ gần gũi, một khoảng dừng đúng lúc, và đôi khi chính những điều rất bình thường lại khiến chúng ta muốn ngồi lại, lắng nghe lâu hơn một chút."


def say(message: str) -> None:
    print(message, flush=True)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def validate_keepers() -> None:
    manifest_path = ROOT.parent / "keepers" / "KEEPERS_MANIFEST.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    for keeper in manifest["keepers"]:
        for artifact in keeper["files"].values():
            path = Path(artifact["path"])
            if not path.is_file() or path.stat().st_size != artifact["size_bytes"] or sha256(path) != artifact["sha256"]:
                raise SystemExit(f"KEEPER_INTEGRITY_FAILED: {path}")


def audio_metrics(path: Path) -> dict:
    samples, sample_rate = sf.read(path, always_2d=True)
    mono = samples.mean(axis=1)
    peak = float(np.max(np.abs(mono))) if mono.size else 0.0
    rms = float(np.sqrt(np.mean(np.square(mono)))) if mono.size else 0.0
    clipped = int(np.count_nonzero(np.abs(mono) >= 0.999))
    return {"duration_seconds": round(float(mono.size / sample_rate), 3), "sample_rate": int(sample_rate), "channels": int(samples.shape[1]), "peak": round(peak, 6), "rms": round(rms, 6), "clipped_samples": clipped, "clipping_ratio": round(clipped / max(1, mono.size), 8)}


def valid(metrics: dict) -> bool:
    return metrics["duration_seconds"] > 0 and metrics["clipping_ratio"] <= 0.01


def peak_rss_mb() -> float:
    return round(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1024, 2)


def require_matching_source_measurement(identity: str, metrics: dict) -> None:
    record = next((item for item in SOURCE_MEASUREMENTS["records"] if item["identity"] == identity), None)
    if record is None or record.get("audio") != metrics:
        raise SystemExit(f"G2_SOURCE_VERIFICATION_FAILED: {identity}")


def main() -> int:
    validate_keepers()
    refs = {identity: SOURCES / f"g2_{identity[-1]}.wav" for identity in IDENTITIES}
    for identity, path in refs.items():
        if not path.is_file() or path.stat().st_size == 0:
            raise SystemExit(f"G2_SOURCE_VERIFICATION_FAILED: missing or empty {path}")
        metrics = audio_metrics(path)
        if not valid(metrics):
            raise SystemExit(f"G2_SOURCE_VERIFICATION_FAILED: {identity}: {metrics}")
        require_matching_source_measurement(identity, metrics)
    if AUDITION.exists() and any(AUDITION.iterdir()):
        raise SystemExit("refusing to overwrite existing G2 audition artifacts")
    if (GENERATION / "private_mapping.json").exists():
        raise SystemExit("refusing to overwrite existing G2 private mapping")
    if PROMPTS.get("vietnamese_test_text", VIETNAMESE_TEXT) != VIETNAMESE_TEXT:
        raise SystemExit("Vietnamese test text must exactly match Phase 30I")

    sys.path.insert(0, str(PROJECT))
    from backend.app.tts.engine import TTSEngine

    OUTPUTS.mkdir(parents=True, exist_ok=True)
    CONDITIONING.mkdir(parents=True, exist_ok=True)
    MEASUREMENTS.parent.mkdir(parents=True, exist_ok=True)
    runtime_home = ROOT / ".vieneu_runtime_home"
    (runtime_home / ".cache" / "vieneu" / "tmp").mkdir(parents=True, exist_ok=True)
    engine = TTSEngine(backend="onnx")
    os.environ["HOME"] = str(runtime_home)
    records = []
    try:
        for number, identity in enumerate(IDENTITIES, start=1):
            ref = refs[identity]
            source_audio = audio_metrics(ref)
            emb_path = CONDITIONING / f"speaker_emb_{identity[-1]}.npy"
            codes_path = CONDITIONING / f"reference_codes_{identity[-1]}.npy"
            if emb_path.exists() != codes_path.exists():
                raise SystemExit(f"incomplete saved conditioning for {identity}")
            if emb_path.exists():
                speaker_emb, codes = np.load(emb_path, allow_pickle=False), np.load(codes_path, allow_pickle=False)
                encode_seconds = None
            else:
                started = time.perf_counter()
                speaker_emb, codes = engine._model.encode_reference(str(ref), denoise=False, use_ref_codes=True)
                encode_seconds = round(time.perf_counter() - started, 3)
                np.save(emb_path, np.asarray(speaker_emb))
                np.save(codes_path, np.asarray(codes))
            target = OUTPUTS / f"vietnamese_G2_{identity[-1]}.wav"
            if target.is_file() and valid(audio_metrics(target)):
                generated = audio_metrics(target)
                record = {"identity": identity, "source_audio": source_audio, "preserved_existing": True, "speaker_emb_shape": list(np.asarray(speaker_emb).shape), "reference_codes_shape": list(np.asarray(codes).shape), "audio": generated, "technical_status": "valid"}
                records.append(record)
                say(f"[{number}/6] {identity}: preserved valid Vietnamese output.")
                continue
            generated = None
            record = None
            for attempt in (1, 2):
                temporary = target.with_name(f".{target.stem}.attempt{attempt}.tmp.wav")
                started = time.perf_counter()
                try:
                    np.random.seed(30109)
                    engine.generate(VIETNAMESE_TEXT, voice={"speaker_emb": speaker_emb, "codes": codes}, speed=1.0, out_path=str(temporary), denoise=False, use_ref_codes=True, quality_diagnostics=True)
                    generated = audio_metrics(temporary)
                    record = {"identity": identity, "source_audio": source_audio, "encode_seconds": encode_seconds, "generation_seconds": round(time.perf_counter() - started, 3), "attempt": attempt, "speaker_emb_shape": list(np.asarray(speaker_emb).shape), "reference_codes_shape": list(np.asarray(codes).shape), "audio": generated, "peak_process_rss_mb": peak_rss_mb(), "technical_status": "valid" if valid(generated) else "invalid"}
                    if valid(generated):
                        temporary.replace(target)
                        break
                    say(f"[{number}/6] {identity}: technical validation failed; retrying once.")
                except Exception as exc:
                    record = {"identity": identity, "source_audio": source_audio, "encode_seconds": encode_seconds, "generation_seconds": round(time.perf_counter() - started, 3), "attempt": attempt, "speaker_emb_shape": list(np.asarray(speaker_emb).shape), "reference_codes_shape": list(np.asarray(codes).shape), "error": repr(exc), "peak_process_rss_mb": peak_rss_mb(), "technical_status": "exception"}
                    say(f"[{number}/6] {identity}: technical exception; retrying once: {exc!r}")
                if attempt == 2:
                    raise RuntimeError(f"G2 bridge failed after one technical retry: {record}")
            records.append(record)
            say(f"[{number}/6] {identity}: Vietnamese output saved.")
    finally:
        del engine
        gc.collect()

    if len(records) != len(IDENTITIES):
        raise RuntimeError("G2_BRIDGE_PARTIAL")
    AUDITION.mkdir(parents=True)
    mapping = list(IDENTITIES)
    random.Random(30109).shuffle(mapping)
    private = {}
    for number, identity in enumerate(mapping, start=1):
        shutil.copy2(refs[identity], AUDITION / f"source_{number:02d}.wav")
        shutil.copy2(OUTPUTS / f"vietnamese_G2_{identity[-1]}.wav", AUDITION / f"vietnamese_{number:02d}.wav")
        private[f"{number:02d}"] = identity
    (GENERATION / "private_mapping.json").write_text(json.dumps(private, indent=2) + "\n", encoding="utf-8")
    result = {"vietnamese_test_text": VIETNAMESE_TEXT, "settings": {"speed": 1.0, "denoise": False, "use_ref_codes": True, "numpy_seed": 30109}, "records": records}
    MEASUREMENTS.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    say("[Phase30J] G2_AUDITION_SET_GENERATED")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        say(f"[Phase30J] G2_VIENEU_BRIDGE_FAILED: {exc!r}")
        raise
