#!/usr/bin/env python3
"""Phase 31B: perceptually distinct Podcast behavior, R&D only.

All candidates use the installed ``podcast_brand_beta`` profile. The experiment
varies phrase segmentation and measured insertion-only pauses; it never changes
the production registry, identity embeddings, or playback speed.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import random
import re
import sys
import time
from pathlib import Path

import numpy as np
import soundfile as sf

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from backend.app.tts.audio import edge_silence_samples, join_audios, save_wav
from backend.app.tts.engine import TTSEngine
from backend.app.tts.nlp import normalize_text
from backend.app.tts.text import chunk_sentences, split_into_sentences

VOICE = "podcast_brand_beta"
SAMPLING = {"temperature": 0.8, "top_k": 25, "top_p": 0.95, "repetition_penalty": 1.2}
TEXT = """Có lúc, giữa một ngày quá nhiều việc, tôi tự hỏi: mình đang vội vì điều gì? Có thể là vì sợ chậm hơn người khác. Cũng có thể vì đã quen lấp đầy mọi khoảng trống bằng một việc mới.

Nhưng rồi, khi ngồi xuống và nghe lại tiếng mưa ngoài cửa sổ, tôi nhận ra có những câu trả lời không cần tìm ngay. Chúng chỉ xuất hiện khi ta cho mình một nhịp thở, một khoảng lặng, và sự kiên nhẫn để nhìn kỹ hơn.

Chúng ta không cần biến mọi ngày thành một câu chuyện thật lớn. Đôi khi, chỉ cần đi chậm qua một đoạn đường quen, gọi cho một người bạn, hoặc tắt màn hình sớm hơn vài phút. Những điều nhỏ ấy không làm cuộc sống dừng lại; chúng giúp ta trở về với nó.

Vậy hôm nay, bạn có thể để lại cho mình một khoảng trống nhỏ không?"""

# These profiles are deliberately farther apart than Phase 31's micro-tuning.
DIRECTIONS = {
    "intimate": {"mode": "clauses", "gap": {"clause": 95, "sentence": 210, "paragraph": 360}},
    "reflective": {"mode": "sentences", "gap": {"clause": 120, "sentence": 390, "paragraph": 720}},
    "story": {"mode": "story", "gap": {"clause": 125, "sentence": 280, "question": 440, "paragraph": 520}},
    "clean": {"mode": "grouped", "gap": {"clause": 65, "sentence": 145, "paragraph": 270}},
}


def sentence_units(text: str) -> list[tuple[str, str]]:
    """Return spoken units and their boundary category without mid-phrase cuts."""
    units = []
    paragraphs = [line.strip() for line in text.splitlines() if line.strip()]
    for paragraph_index, paragraph in enumerate(paragraphs):
        sentences = split_into_sentences(paragraph)
        for sentence_index, sentence in enumerate(sentences):
            boundary = "sentence"
            if sentence.rstrip().endswith("?"):
                boundary = "question"
            if sentence_index == len(sentences) - 1 and paragraph_index < len(paragraphs) - 1:
                boundary = "paragraph"
            units.append((sentence, boundary))
    return units


def clause_units(text: str) -> list[tuple[str, str]]:
    units = []
    for sentence, boundary in sentence_units(text):
        phrases = [part.strip() for part in re.split(r"(?<=[,;:])\s+", sentence) if part.strip()]
        for index, phrase in enumerate(phrases):
            units.append((phrase, boundary if index == len(phrases) - 1 else "clause"))
    return units


def build_units(text: str, mode: str) -> list[tuple[str, str]]:
    sentences = sentence_units(text)
    if mode == "clauses":
        return clause_units(text)
    if mode == "sentences":
        return sentences
    if mode == "story":
        return clause_units(text)
    if mode == "grouped":
        grouped = chunk_sentences([sentence for sentence, _kind in sentences], max_chars=240)
        return [(chunk, "paragraph" if chunk.endswith(("?", "!")) else "sentence") for chunk in grouped]
    raise ValueError(f"Unknown segmentation mode: {mode}")


def target_gap(direction: dict, boundary: str) -> int:
    gaps = direction["gap"]
    return int(gaps.get(boundary, gaps.get("sentence", 0)))


def metrics(path: Path, started: float, units: list[tuple[str, str]], gaps: list[int]) -> dict:
    audio, sample_rate = sf.read(path, dtype="float32", always_2d=False)
    mono = audio if audio.ndim == 1 else audio.mean(axis=1)
    duration = len(mono) / sample_rate
    return {
        "duration_seconds": round(duration, 3),
        "generation_seconds": round(time.monotonic() - started, 3),
        "rtf": round((time.monotonic() - started) / duration, 3),
        "sample_rate": int(sample_rate), "channels": 1 if audio.ndim == 1 else int(audio.shape[1]),
        "peak": round(float(np.max(np.abs(mono))), 6), "rms": round(float(np.sqrt(np.mean(mono * mono))), 6),
        "clipped_samples": int(np.count_nonzero(np.abs(mono) >= .999)),
        "silence_ratio": round(float(np.mean(np.abs(mono) < .003)), 4),
        "chunk_count": len(units), "gap_count": len(gaps), "inserted_gap_ms": [round(value * 1000 / sample_rate, 1) for value in gaps],
        "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
    }


def render(engine: TTSEngine, label: str, direction: dict, output_dir: Path, log_dir: Path) -> dict:
    text = normalize_text(TEXT)
    units = build_units(text, direction["mode"])
    if not units:
        raise RuntimeError("No speakable units")
    output = output_dir / f"Podcast {label}.wav"
    started = time.monotonic()
    np.random.seed(31102)
    audio_parts, sample_rate = [], None
    for index, (unit, _boundary) in enumerate(units):
        temporary = output_dir / f".podcast_{label}_{index:02d}.wav"
        engine.generate(unit, voice=VOICE, speed=1.0, out_path=str(temporary), **SAMPLING)
        audio, current_rate = sf.read(temporary, dtype="float32", always_2d=False)
        temporary.unlink(missing_ok=True)
        sample_rate = int(current_rate) if sample_rate is None else sample_rate
        if sample_rate != int(current_rate):
            raise RuntimeError("Generated sample rates differ")
        audio_parts.append(np.asarray(audio, dtype=np.float32))
    inserted = []
    for index, (_unit, boundary) in enumerate(units[:-1]):
        _leading, trailing = edge_silence_samples(audio_parts[index])
        leading, _trailing = edge_silence_samples(audio_parts[index + 1])
        deficit = target_gap(direction, boundary) - ((leading + trailing) * 1000 / sample_rate)
        inserted.append(max(0, round(deficit * sample_rate / 1000)))
    save_wav(str(output), join_audios(audio_parts, sample_rate, gap_samples=inserted), sample_rate)
    chunk_log = [{"index": index + 1, "boundary": boundary, "text": unit} for index, (unit, boundary) in enumerate(units)]
    (log_dir / f"Podcast_{label}.json").write_text(json.dumps(chunk_log, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return metrics(output, started, units, inserted)


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate selected blind Phase 31B candidates.")
    parser.add_argument("--labels", nargs="+", choices=list("ABCD"), default=list("ABCD"))
    args = parser.parse_args()
    phase = Path(__file__).resolve().parent
    output_dir, mapping_dir, log_dir, metric_dir = (phase / "outputs", phase / "mappings", phase / "chunk_logs", phase / "metrics")
    for directory in (output_dir, mapping_dir, log_dir, metric_dir):
        directory.mkdir(parents=True, exist_ok=True)
    blind_order = list(DIRECTIONS)
    random.Random(31102).shuffle(blind_order)
    mapping = {label: direction for label, direction in zip("ABCD", blind_order)}
    metrics_path = metric_dir / "metrics.json"
    try:
        existing = {record["label"]: record for record in json.loads(metrics_path.read_text(encoding="utf-8"))}
    except (FileNotFoundError, json.JSONDecodeError):
        existing = {}
    engine = TTSEngine(backend="onnx")
    try:
        for label in args.labels:
            record = {"label": f"Podcast {label}", "metrics": render(engine, label, DIRECTIONS[mapping[label]], output_dir, log_dir)}
            existing[record["label"]] = record
            print(f"READY Podcast {label}: {record['metrics']['duration_seconds']}s / {record['metrics']['chunk_count']} chunks", flush=True)
    finally:
        del engine
    records = [existing[f"Podcast {label}"] for label in "ABCD" if f"Podcast {label}" in existing]
    hashes = {record["metrics"]["sha256"] for record in records}
    if len(records) == 4 and len(hashes) != len(records):
        raise RuntimeError("ENGINE CURRENTLY COLLAPSES THESE PROSODY VARIANTS: duplicate output")
    if len(records) == 4 and len({record["metrics"]["chunk_count"] for record in records}) < 3:
        raise RuntimeError("ENGINE CURRENTLY COLLAPSES THESE PROSODY VARIANTS: segmentation not distinct")
    if any(record["metrics"]["clipped_samples"] for record in records):
        raise RuntimeError("A candidate clipped")
    (mapping_dir / "private_mapping.json").write_text(json.dumps({"directions": DIRECTIONS, "mapping": mapping}, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    (metric_dir / "metrics.json").write_text(json.dumps(records, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print("PHASE31B_AUDITION_READY", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
