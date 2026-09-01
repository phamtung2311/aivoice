#!/usr/bin/env python3
"""Phase 30K: controlled VieNeu bridge for preserved G2-06 and K refinements."""
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
GENERATION = ROOT / "generation_3"
KEEPERS = ROOT.parent / "keepers"
OUTPUTS = GENERATION / "vietnamese_outputs"
CONDITIONING = GENERATION / "conditioning"
AUDITION = GENERATION / "audition"
MEASUREMENTS = GENERATION / "measurements" / "vieneu_generation.json"
SOURCE_MEASUREMENTS = json.loads((GENERATION / "measurements" / "source_generation.json").read_text(encoding="utf-8"))
IDENTITIES = ("CONTROL", "K-A", "K-B", "K-C")
VIETNAMESE_TEXT = "Có những câu chuyện không cần phải kể thật nhanh. Chỉ cần một giọng nói đủ gần gũi, một khoảng dừng đúng lúc, và đôi khi chính những điều rất bình thường lại khiến chúng ta muốn ngồi lại, lắng nghe lâu hơn một chút."


def say(message: str) -> None:
    print(message, flush=True)


def sha256(path: Path) -> str:
    value = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            value.update(block)
    return value.hexdigest()


def validate_keepers() -> None:
    manifest = json.loads((KEEPERS / "KEEPERS_MANIFEST.json").read_text(encoding="utf-8"))
    required = {"phase30i_01", "phase30i_02", "g2_01", "g2_05", "g2_06"}
    if {item["keeper_id"] for item in manifest["keepers"]} != required:
        raise SystemExit("KEEPER_INTEGRITY_FAILED: unexpected keeper collection")
    for keeper in manifest["keepers"]:
        for artifact in keeper["files"].values():
            path = Path(artifact["path"])
            if not path.is_file() or path.stat().st_size != artifact["size_bytes"] or sha256(path) != artifact["sha256"]:
                raise SystemExit(f"KEEPER_INTEGRITY_FAILED: {path}")


def audio_metrics(path: Path) -> dict:
    data, rate = sf.read(path, always_2d=True)
    mono = data.mean(axis=1)
    peak = float(np.max(np.abs(mono))) if mono.size else 0.0
    rms = float(np.sqrt(np.mean(np.square(mono)))) if mono.size else 0.0
    clipped = int(np.count_nonzero(np.abs(mono) >= 0.999))
    return {"duration_seconds": round(float(mono.size / rate), 3), "sample_rate": int(rate), "channels": int(data.shape[1]), "peak": round(peak, 6), "rms": round(rms, 6), "clipped_samples": clipped, "clipping_ratio": round(clipped / max(1, mono.size), 8)}


def valid(metrics: dict) -> bool:
    return metrics["duration_seconds"] > 0 and metrics["clipping_ratio"] <= 0.01


def peak_rss_mb() -> float:
    return round(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1024, 2)


def source_check(identity: str, path: Path) -> dict:
    metrics = audio_metrics(path)
    if not path.is_file() or path.stat().st_size == 0 or not valid(metrics):
        raise SystemExit(f"K_SOURCE_VERIFICATION_FAILED: {identity}")
    expected = next((record["audio"] for record in SOURCE_MEASUREMENTS["records"] if record["identity"] == identity), None)
    if expected is not None and expected != metrics:
        raise SystemExit(f"K_SOURCE_VERIFICATION_FAILED: measurement mismatch for {identity}")
    return metrics


def generate(engine, identity: str, source_metrics: dict, speaker_emb, codes, target: Path, encode_seconds: float | None) -> dict:
    if target.is_file() and valid(audio_metrics(target)):
        return {"identity": identity, "source_audio": source_metrics, "preserved_existing": True, "speaker_emb_shape": list(np.asarray(speaker_emb).shape), "reference_codes_shape": list(np.asarray(codes).shape), "audio": audio_metrics(target), "technical_status": "valid"}
    for attempt in (1, 2):
        temporary = target.with_name(f".{target.stem}.attempt{attempt}.tmp.wav")
        started = time.perf_counter()
        try:
            np.random.seed(30109)
            engine.generate(VIETNAMESE_TEXT, voice={"speaker_emb": speaker_emb, "codes": codes}, speed=1.0, out_path=str(temporary), denoise=False, use_ref_codes=True, quality_diagnostics=True)
            audio = audio_metrics(temporary)
            record = {"identity": identity, "source_audio": source_metrics, "encode_seconds": encode_seconds, "generation_seconds": round(time.perf_counter() - started, 3), "attempt": attempt, "speaker_emb_shape": list(np.asarray(speaker_emb).shape), "reference_codes_shape": list(np.asarray(codes).shape), "audio": audio, "peak_process_rss_mb": peak_rss_mb(), "technical_status": "valid" if valid(audio) else "invalid"}
            if valid(audio):
                temporary.replace(target)
                return record
        except Exception as exc:
            record = {"identity": identity, "source_audio": source_metrics, "encode_seconds": encode_seconds, "generation_seconds": round(time.perf_counter() - started, 3), "attempt": attempt, "speaker_emb_shape": list(np.asarray(speaker_emb).shape), "reference_codes_shape": list(np.asarray(codes).shape), "error": repr(exc), "peak_process_rss_mb": peak_rss_mb(), "technical_status": "exception"}
        if attempt == 2:
            raise RuntimeError(f"technical bridge failure after one retry: {record}")
    raise AssertionError("unreachable")


def main() -> int:
    validate_keepers()
    control_dir = KEEPERS / "g2_06"
    refs = {"CONTROL": control_dir / "qwen_source.wav", **{identity: GENERATION / "reference_audio" / f"k_{identity[-1]}.wav" for identity in ("K-A", "K-B", "K-C")}}
    source_metrics = {identity: source_check(identity, path) for identity, path in refs.items()}
    if AUDITION.exists() and any(AUDITION.iterdir()):
        raise SystemExit("refusing to overwrite existing refinement audition")
    if (GENERATION / "private_mapping.json").exists():
        raise SystemExit("refusing to overwrite existing refinement mapping")
    OUTPUTS.mkdir(parents=True, exist_ok=True)
    CONDITIONING.mkdir(parents=True, exist_ok=True)
    MEASUREMENTS.parent.mkdir(parents=True, exist_ok=True)
    sys.path.insert(0, str(PROJECT))
    from backend.app.tts.engine import TTSEngine
    runtime_home = ROOT / ".vieneu_runtime_home"
    (runtime_home / ".cache" / "vieneu" / "tmp").mkdir(parents=True, exist_ok=True)
    engine = TTSEngine(backend="onnx")
    os.environ["HOME"] = str(runtime_home)
    records = []
    try:
        control_emb = control_dir / "speaker_emb.npy"
        control_codes = control_dir / "reference_codes.npy"
        speaker_emb, codes = np.load(control_emb, allow_pickle=False), np.load(control_codes, allow_pickle=False)
        control_target = OUTPUTS / "vietnamese_CONTROL_regenerated.wav"
        control_record = generate(engine, "CONTROL", source_metrics["CONTROL"], speaker_emb, codes, control_target, None)
        original_control = control_dir / "vietnamese_sample.wav"
        original_metrics = audio_metrics(original_control)
        regenerated_metrics = audio_metrics(control_target)
        control_record["reproducibility"] = {"status": "CONTROL_REPRODUCIBILITY_EXACT" if sha256(original_control) == sha256(control_target) else "CONTROL_REPRODUCIBILITY_NONEXACT", "preserved_original_audio": original_metrics, "regenerated_audio": regenerated_metrics, "preserved_original_sha256": sha256(original_control), "regenerated_sha256": sha256(control_target)}
        records.append(control_record)
        say("[1/4] CONTROL: reproducibility sample generated; preserved original remains audition control.")
        for number, identity in enumerate(("K-A", "K-B", "K-C"), start=2):
            suffix = identity[-1]
            emb_path, codes_path = CONDITIONING / f"speaker_emb_{suffix}.npy", CONDITIONING / f"reference_codes_{suffix}.npy"
            if emb_path.exists() != codes_path.exists():
                raise RuntimeError(f"incomplete saved conditioning for {identity}")
            if emb_path.exists():
                speaker_emb, codes, encode_seconds = np.load(emb_path, allow_pickle=False), np.load(codes_path, allow_pickle=False), None
            else:
                started = time.perf_counter()
                speaker_emb, codes = engine._model.encode_reference(str(refs[identity]), denoise=False, use_ref_codes=True)
                encode_seconds = round(time.perf_counter() - started, 3)
                np.save(emb_path, np.asarray(speaker_emb))
                np.save(codes_path, np.asarray(codes))
            records.append(generate(engine, identity, source_metrics[identity], speaker_emb, codes, OUTPUTS / f"vietnamese_{identity}.wav", encode_seconds))
            say(f"[{number}/4] {identity}: Vietnamese output saved.")
    finally:
        del engine
        gc.collect()
    AUDITION.mkdir(parents=True)
    candidates = list(IDENTITIES)
    random.Random(30109).shuffle(candidates)
    mapping = {}
    for number, identity in enumerate(candidates, start=1):
        source = refs[identity]
        vietnamese = control_dir / "vietnamese_sample.wav" if identity == "CONTROL" else OUTPUTS / f"vietnamese_{identity}.wav"
        shutil.copy2(source, AUDITION / f"source_{number:02d}.wav")
        shutil.copy2(vietnamese, AUDITION / f"vietnamese_{number:02d}.wav")
        mapping[f"{number:02d}"] = identity
    (GENERATION / "private_mapping.json").write_text(json.dumps(mapping, indent=2) + "\n", encoding="utf-8")
    result = {"vietnamese_test_text": VIETNAMESE_TEXT, "settings": {"speed": 1.0, "denoise": False, "use_ref_codes": True, "numpy_seed": 30109}, "records": records, "blind_control_audio": "preserved G2-06 Vietnamese keeper WAV"}
    MEASUREMENTS.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    say("[Phase30K] K_REFINEMENT_AUDITION_GENERATED")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        say(f"[Phase30K] K_VIENEU_BRIDGE_FAILED: {exc!r}")
        raise
