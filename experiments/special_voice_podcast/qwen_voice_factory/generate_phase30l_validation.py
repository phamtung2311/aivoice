#!/usr/bin/env python3
"""Phase 30L controlled long-form validation using only preserved conditioning."""
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
sys.path.insert(0, str(PROJECT))
from backend.app.tts.audio import edge_silence_samples, join_audios, save_wav
from backend.app.tts.text import chunk_sentences, preprocess_text, split_into_sentences
PHASE = ROOT.parent / "phase30l"
KEEPERS = ROOT.parent / "keepers"
TEXTS = PHASE / "test_texts"
MEASUREMENTS = PHASE / "measurements" / "generation.json"
AUDITION = PHASE / "audition"
TESTS = (("test_01", "test_01_conversational.txt"), ("test_02", "test_02_reflective.txt"), ("test_03", "test_03_informational.txt"), ("test_04_longform", "test_04_longform.txt"))
FINALISTS = {"CONTROL": {"keeper": "g2_06", "directory": "control"}, "K-A": {"keeper": "phase30k_04", "directory": "k_a"}}


def say(message: str) -> None:
    print(message, flush=True)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def validate_keepers() -> None:
    manifest = json.loads((KEEPERS / "KEEPERS_MANIFEST.json").read_text(encoding="utf-8"))
    for keeper in manifest["keepers"]:
        for artifact in keeper["files"].values():
            path = Path(artifact["path"])
            if not path.is_file() or path.stat().st_size != artifact["size_bytes"] or sha256(path) != artifact["sha256"]:
                raise SystemExit(f"KEEPER_INTEGRITY_FAILED: {path}")


def metrics(path: Path) -> dict:
    data, rate = sf.read(path, always_2d=True)
    mono = data.mean(axis=1)
    peak = float(np.max(np.abs(mono))) if mono.size else 0.0
    rms = float(np.sqrt(np.mean(np.square(mono)))) if mono.size else 0.0
    clipped = int(np.count_nonzero(np.abs(mono) >= 0.999))
    return {"duration_seconds": round(float(mono.size / rate), 3), "sample_rate": int(rate), "channels": int(data.shape[1]), "peak": round(peak, 6), "rms": round(rms, 6), "clipped_samples": clipped, "clipping_ratio": round(clipped / max(1, mono.size), 8)}


def valid(audio: dict) -> bool:
    return audio["duration_seconds"] > 0 and audio["clipping_ratio"] <= 0.01


def peak_rss_mb() -> float:
    return round(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1024, 2)


def generate(engine, identity: str, test_id: str, text: str, voice: dict, target: Path) -> dict:
    if target.is_file() and valid(metrics(target)):
        return {"identity": identity, "test": test_id, "preserved_existing": True, "audio": metrics(target), "technical_status": "valid"}
    started = time.perf_counter()
    clean = preprocess_text(text)
    chunks = chunk_sentences(split_into_sentences(clean), max_chars=240)
    checkpoint = target.parent / ".chunks" / test_id
    checkpoint.mkdir(parents=True, exist_ok=True)
    audios, chunk_info = [], []
    np.random.seed(30109)
    for index, chunk in enumerate(chunks):
        chunk_path = checkpoint / f"chunk_{index:03d}.wav"
        if not chunk_path.is_file() or not valid(metrics(chunk_path)):
            raw = np.asarray(engine._model.infer(chunk, voice=voice, denoise=False, use_ref_codes=True))
            audio = raw.astype(np.float32) / np.iinfo(raw.dtype).max if np.issubdtype(raw.dtype, np.integer) else raw.astype(np.float32)
            if audio.size == 0:
                raise RuntimeError(f"empty chunk {index}")
            save_wav(str(chunk_path), audio, engine._model.sample_rate)
        data, rate = sf.read(chunk_path, always_2d=True)
        audio = data[:, 0].astype(np.float32)
        leading, trailing = edge_silence_samples(audio)
        audios.append(audio)
        chunk_info.append({"chars": len(chunk), "duration_seconds": round(float(audio.size / rate), 4), "leading_silence_ms": round(leading * 1000 / rate, 2), "trailing_silence_ms": round(trailing * 1000 / rate, 2)})
    sr = engine._model.sample_rate
    targets = [130 if chunk.rstrip()[-1:] in ".!?…" else 75 if chunk.rstrip()[-1:] in ",;:" else 45 for chunk in chunks[:-1]]
    gaps = [max(0, int((target - chunk_info[i]["trailing_silence_ms"] - chunk_info[i + 1]["leading_silence_ms"]) * sr / 1000)) for i, target in enumerate(targets)]
    temporary = target.with_name(f".{target.stem}.tmp.wav")
    save_wav(str(temporary), join_audios(audios, sr, gap_samples=gaps), sr)
    audio = metrics(temporary)
    if not valid(audio):
        raise RuntimeError(f"technical generation failure: {audio}")
    temporary.replace(target)
    return {"identity": identity, "test": test_id, "attempt": 1, "generation_seconds": round(time.perf_counter() - started, 3), "peak_process_rss_mb": peak_rss_mb(), "audio": audio, "technical_status": "valid", "chunk_count": len(chunks), "chunk_character_lengths": [item["chars"] for item in chunk_info], "chunk_durations_seconds": [item["duration_seconds"] for item in chunk_info], "all_expected_chunks_synthesized": True}


def main() -> int:
    validate_keepers()
    if AUDITION.exists() and any(AUDITION.iterdir()):
        raise SystemExit("refusing to overwrite existing Phase 30L audition")
    mapping_path = PHASE / "private_mapping.json"
    if mapping_path.exists():
        raise SystemExit("refusing to overwrite existing Phase 30L mapping")
    texts = {test_id: (TEXTS / filename).read_text(encoding="utf-8").strip() for test_id, filename in TESTS}
    if any(not text for text in texts.values()):
        raise SystemExit("all test texts are required")
    voices = {}
    for identity, details in FINALISTS.items():
        directory = KEEPERS / details["keeper"]
        emb, codes = directory / "speaker_emb.npy", directory / "reference_codes.npy"
        if not emb.is_file() or not codes.is_file():
            raise SystemExit(f"KEEPER_INTEGRITY_FAILED: missing conditioning for {identity}")
        voices[identity] = {"speaker_emb": np.load(emb, allow_pickle=False), "codes": np.load(codes, allow_pickle=False)}
    sys.path.insert(0, str(PROJECT))
    from backend.app.tts.engine import TTSEngine
    runtime_home = ROOT / ".vieneu_runtime_home"
    (runtime_home / ".cache" / "vieneu" / "tmp").mkdir(parents=True, exist_ok=True)
    engine = TTSEngine(backend="onnx")
    os.environ["HOME"] = str(runtime_home)
    records = []
    try:
        for identity, details in FINALISTS.items():
            output_dir = PHASE / "internal" / details["directory"]
            output_dir.mkdir(parents=True, exist_ok=True)
            for test_id, _ in TESTS:
                say(f"[{identity}] {test_id}...")
                records.append(generate(engine, identity, test_id, texts[test_id], voices[identity], output_dir / f"{test_id}.wav"))
    finally:
        del engine
        gc.collect()
    if len(records) != 8 or not all(record.get("technical_status") == "valid" for record in records):
        raise RuntimeError("FINALIST_AUDITION_PARTIAL")
    AUDITION.mkdir(parents=True)
    blind = list(FINALISTS)
    random.Random(30109).shuffle(blind)
    mapping = {"A": blind[0], "B": blind[1]}
    for test_id, _ in TESTS:
        audition_dir = AUDITION / test_id
        audition_dir.mkdir()
        for label, identity in mapping.items():
            source = PHASE / "internal" / FINALISTS[identity]["directory"] / f"{test_id}.wav"
            shutil.copy2(source, audition_dir / f"voice_{label}.wav")
    mapping_path.write_text(json.dumps(mapping, indent=2) + "\n", encoding="utf-8")
    result = {"settings": {"speed": 1.0, "denoise": False, "use_ref_codes": True, "numpy_seed_before_each_generation": 30109, "normal_production_chunking": True}, "tests": {test_id: {"text_path": str(TEXTS / filename), "sha256": sha256(TEXTS / filename), "characters": len(texts[test_id])} for test_id, filename in TESTS}, "records": records}
    MEASUREMENTS.parent.mkdir(parents=True, exist_ok=True)
    MEASUREMENTS.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    say("[Phase30L] FINALIST_AUDITION_READY")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        say(f"[Phase30L] FAILED: {exc!r}")
        raise
