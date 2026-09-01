#!/usr/bin/env python3
"""Generate the finite, blinded Phase 29B smoke listening set locally.

This is research-only orchestration.  It deliberately reuses the existing model
adapter and TTSEngine text/audio helpers, but keeps one encoded reference profile
in memory so every candidate receives precisely the same speaker embedding/codes.
It neither calls an API nor saves a production voice.
"""
from __future__ import annotations

import csv
import json
import random
import resource
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parent
PROJECT_ROOT = ROOT.parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from backend.app.tts.audio import edge_silence_samples, join_audios, save_wav
from backend.app.tts.engine import TTSEngine
from backend.app.tts.reference_quality import analyze_clip
from backend.app.tts.text import chunk_sentences, preprocess_text, split_into_sentences


REFERENCE = ROOT / "reference_audio" / "review_film.wav"
OUTPUT = ROOT / "outputs" / "phase29b"
CONFIG = ROOT / "experiment_config.json"
CORPUS = ROOT / "test_sentences.json"
SELECTED_IDS = ("intro", "suspense", "reflective")
CANDIDATES = ("baseline", "review_candidate_a", "review_candidate_b", "review_candidate_c")


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def rss_mb() -> float:
    return resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1024.0


def as_float_audio(audio: object) -> np.ndarray:
    raw = np.asarray(audio)
    if np.issubdtype(raw.dtype, np.integer):
        raw = raw.astype(np.float32) / np.iinfo(raw.dtype).max
    else:
        raw = raw.astype(np.float32)
    if raw.size == 0 or raw.ndim not in (1, 2):
        raise RuntimeError("Model returned no valid waveform")
    return raw


def render(engine: TTSEngine, reference_voice: dict, text: str, sampling: dict) -> tuple[np.ndarray, dict]:
    """Mirror existing TTSEngine generation, except profile encoding is external."""
    model = engine._model
    sr = model.sample_rate
    clean = preprocess_text(text)
    chunks = chunk_sentences(split_into_sentences(clean), max_chars=240)
    audios, chunk_metrics = [], []
    for index, chunk in enumerate(chunks):
        call_kwargs = {"denoise": True, "use_ref_codes": True, **sampling}
        audio = as_float_audio(model.infer(chunk, voice=reference_voice, **call_kwargs))
        leading, trailing = edge_silence_samples(audio)
        chunk_metrics.append({
            "index": index,
            "chars": len(chunk),
            "leading_silence_ms": round(leading * 1000 / sr, 2),
            "trailing_silence_ms": round(trailing * 1000 / sr, 2),
        })
        audios.append(audio)
    gaps = []
    for index, chunk in enumerate(chunks[:-1]):
        ending = chunk.rstrip()[-1:] if chunk.strip() else ""
        target_ms = 130 if ending in ".!?…" else 75 if ending in ",;:" else 45
        existing_ms = chunk_metrics[index]["trailing_silence_ms"] + chunk_metrics[index + 1]["leading_silence_ms"]
        gaps.append(max(0, int((target_ms - existing_ms) * sr / 1000)))
    joined = join_audios(audios, sr, gap_samples=gaps)
    return joined, {
        "input_chars": len(clean), "outer_chunk_count": len(chunks),
        "inserted_gap_ms": [round(gap * 1000 / sr, 2) for gap in gaps],
    }


def write_listening_files(rows: list[dict]) -> None:
    fields = ["sentence_id", "sample_id", "naturalness_1_5", "review_suitability_1_5", "clarity_1_5", "voice_consistency_1_5", "robotic_rhythm_1_5", "preferred", "notes"]
    with (OUTPUT / "phase29b_listening_sheet.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows({field: row.get(field, "") for field in fields} for row in rows)
    (OUTPUT / "PHASE29B_LISTENING.md").write_text(
        "# Phase 29B — Nghe mù\\n\\n"
        "Mỗi nhóm câu có bốn mẫu ẩn danh. Hãy nghe cả bốn trước khi chấm; ưu tiên tai nghe. "
        "Không mở `phase29b_mapping.json` cho tới khi hoàn tất phiếu.\\n\\n"
        "1. Chấm Naturalness, độ phù hợp Review, Clarity và độ nhất quán giọng từ 1–5.\\n"
        "2. Chấm Robotic rhythm: 1 = tự nhiên, 5 = rất máy móc.\\n"
        "3. Ghi một sample ưu tiên cho mỗi câu và ghi chú ngắn.\\n"
        "4. Điền vào `phase29b_listening_sheet.csv`.\\n",
        encoding="utf-8",
    )


def main() -> int:
    if not REFERENCE.is_file():
        raise SystemExit(f"REFERENCE_REQUIRED: {REFERENCE}")
    reference_report = analyze_clip(REFERENCE.read_bytes()).to_dict()
    duration = reference_report["metrics"]["duration_seconds"]
    if not 5.0 <= duration <= 8.5:
        raise SystemExit(f"Reference duration {duration}s is outside the approved 6–8 second useful range.")
    if OUTPUT.exists() and any(OUTPUT.rglob("*.wav")):
        raise SystemExit(f"Refusing to overwrite existing Phase 29B WAV files: {OUTPUT}")
    OUTPUT.mkdir(parents=True, exist_ok=True)
    config, corpus = load_json(CONFIG), load_json(CORPUS)
    selected = [item for item in corpus["sentences"] if item["id"] in SELECTED_IDS]
    if [item["id"] for item in selected] != list(SELECTED_IDS):
        raise SystemExit("The Phase 29B selected smoke corpus is incomplete.")

    print("Loading current local ONNX engine; no production voice profile will be written.", flush=True)
    engine = TTSEngine(backend="onnx")
    print("Encoding the supplied reference once for the whole controlled run.", flush=True)
    speaker_emb, codes = engine._model.encode_reference(str(REFERENCE), denoise=True, use_ref_codes=True)
    reference_voice = {"speaker_emb": speaker_emb, "codes": codes}
    evidence = {
        "encoded_once": True,
        "same_reference_for_all_samples": True,
        "speaker_emb": {"present": speaker_emb is not None, "shape": list(np.asarray(speaker_emb).shape)},
        "codes": {"present": codes is not None, "shape": list(np.asarray(codes).shape) if codes is not None else None},
        "denoise": True, "use_ref_codes": True,
    }
    mapping, records, listening_rows = {}, [], []
    mapping_rng = random.Random(29029)
    for sentence_index, item in enumerate(selected, start=1):
        sentence_dir = OUTPUT / f"sentence_{sentence_index:02d}_{item['id']}"
        sentence_dir.mkdir()
        shuffled = list(CANDIDATES)
        mapping_rng.shuffle(shuffled)
        mapping[item["id"]] = {f"sample_{i:02d}": candidate for i, candidate in enumerate(shuffled, start=1)}
        for sample_index, candidate in enumerate(shuffled, start=1):
            sample_id = f"sample_{sample_index:02d}"
            output = sentence_dir / f"{sample_id}.wav"
            # Same NumPy seed for the four candidate settings of a sentence: controlled comparison.
            seed = 29000 + sentence_index
            np.random.seed(seed)
            start_wall, start_cpu = time.perf_counter(), time.process_time()
            audio, diagnostics = render(engine, reference_voice, item["text"], config["candidates"][candidate]["sampling"])
            wall, cpu = time.perf_counter() - start_wall, time.process_time() - start_cpu
            save_wav(str(output), audio, engine._model.sample_rate)
            audio_duration = float(audio.shape[0]) / engine._model.sample_rate
            record = {
                "timestamp": datetime.now(timezone.utc).isoformat(), "sentence_id": item["id"],
                "category": item["category"], "sample_id": sample_id,
                "output": str(output.relative_to(ROOT)), "numpy_seed": seed,
                "wall_generation_seconds": round(wall, 3), "process_cpu_seconds": round(cpu, 3),
                "audio_duration_seconds": round(audio_duration, 4), "RTF": round(wall / audio_duration, 4),
                "peak_RSS_MB": round(rss_mb(), 2), "diagnostics": diagnostics, "status": "success",
            }
            records.append(record)
            listening_rows.append({"sentence_id": item["id"], "sample_id": sample_id})
            print(f"DONE {item['id']}/{sample_id}: {record['wall_generation_seconds']}s; RTF={record['RTF']}", flush=True)
    (OUTPUT / "phase29b_mapping.json").write_text(json.dumps(mapping, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    (OUTPUT / "phase29b_measurements.json").write_text(json.dumps({"reference_quality": reference_report, "reference_encoding": evidence, "records": records}, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    write_listening_files(listening_rows)
    print("Generated exactly 12 anonymized WAV files. Stop here for human listening.", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
