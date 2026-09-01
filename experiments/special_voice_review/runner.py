#!/usr/bin/env python3
"""Controlled local VieNeu Review Film candidate renderer.

This research runner is intentionally outside production. It does not alter saved
voices or API behavior; it only calls the existing TTSEngine with an explicit
reference and writes ignored experiment output.
"""
from __future__ import annotations

import argparse
import json
import os
import resource
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent
PROJECT_ROOT = ROOT.parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from backend.app.tts.engine import TTSEngine


CONFIG_PATH = ROOT / "experiment_config.json"
CORPUS_PATH = ROOT / "test_sentences.json"
OUTPUT_DIR = ROOT / "outputs"
MEASUREMENTS_PATH = ROOT / "measurements.json"


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def rss_mb() -> float:
    # Linux ru_maxrss is KiB; Fedora is the supported local target.
    return resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1024.0


def append_measurements(records: list[dict]) -> None:
    existing = []
    if MEASUREMENTS_PATH.exists():
        try:
            existing = json.loads(MEASUREMENTS_PATH.read_text(encoding="utf-8"))
        except Exception:
            existing = []
    MEASUREMENTS_PATH.write_text(json.dumps([*existing, *records], ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def candidate_blind_id(config: dict, candidate: str) -> str:
    return config["candidates"][candidate]["label"].replace(" ", "_").lower()


def render_candidate(engine: TTSEngine, *, candidate: str, reference: Path, config: dict, corpus: dict, overwrite: bool) -> list[dict]:
    common = config["common"]
    candidate_config = config["candidates"][candidate]
    sampling = candidate_config["sampling"]
    blind_id = candidate_blind_id(config, candidate)
    records: list[dict] = []
    for item in corpus["sentences"]:
        output = OUTPUT_DIR / blind_id / f"{item['id']}.wav"
        if output.exists() and not overwrite:
            print(f"SKIP existing: {output}")
            continue
        output.parent.mkdir(parents=True, exist_ok=True)
        started_wall = time.perf_counter()
        started_cpu = time.process_time()
        try:
            engine.generate(
                item["text"],
                speed=common["speed"],
                out_path=str(output),
                max_chunk_chars=common["max_chunk_chars"],
                ref_audio=str(reference),
                denoise=common["denoise"],
                use_ref_codes=common["use_ref_codes"],
                quality_diagnostics=common["quality_diagnostics"],
                temperature=sampling.get("temperature"),
                top_k=sampling.get("top_k"),
                top_p=sampling.get("top_p"),
                repetition_penalty=sampling.get("repetition_penalty"),
            )
            diagnostics = getattr(engine, "last_generation_diagnostics", None) or {}
            audio_duration = diagnostics.get("final_duration_seconds")
            wall_seconds = time.perf_counter() - started_wall
            record = {
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "candidate": candidate,
                "blind_id": blind_id,
                "sentence_id": item["id"],
                "category": item["category"],
                "output": str(output.relative_to(ROOT)),
                "wall_seconds": round(wall_seconds, 3),
                "cpu_seconds": round(time.process_time() - started_cpu, 3),
                "peak_process_rss_mb": round(rss_mb(), 2),
                "audio_duration_seconds": audio_duration,
                "rtf": round(wall_seconds / audio_duration, 4) if audio_duration else None,
                "diagnostics": diagnostics,
                "status": "success",
            }
            print(f"DONE {blind_id}/{item['id']}: {record['wall_seconds']}s, RTF={record['rtf']}")
        except Exception as exc:
            record = {
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "candidate": candidate,
                "blind_id": blind_id,
                "sentence_id": item["id"],
                "status": "failed",
                "error": repr(exc),
                "peak_process_rss_mb": round(rss_mb(), 2),
            }
            records.append(record)
            append_measurements(records)
            raise
        records.append(record)
    return records


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate isolated Review Film voice candidates locally.")
    parser.add_argument("--reference", required=True, type=Path, help="Permissioned Review Film-style reference WAV.")
    parser.add_argument("--candidate", choices=["baseline", "review_candidate_a", "review_candidate_b", "review_candidate_c"])
    parser.add_argument("--all-candidates", action="store_true", help="Render the four controlled candidates sequentially.")
    parser.add_argument("--overwrite", action="store_true")
    args = parser.parse_args()
    if bool(args.candidate) == bool(args.all_candidates):
        parser.error("Choose exactly one of --candidate or --all-candidates.")
    if not args.reference.is_file():
        parser.error(f"Reference missing: {args.reference}. Read reference_contract.md first.")

    config = load_json(CONFIG_PATH)
    corpus = load_json(CORPUS_PATH)
    selected = list(config["candidates"]) if args.all_candidates else [args.candidate]
    print("Loading the existing local ONNX engine once. No production voice profile is saved or modified.")
    engine = TTSEngine(backend="onnx")
    all_records: list[dict] = []
    for candidate in selected:
        print(f"Rendering controlled candidate: {candidate}")
        all_records.extend(render_candidate(engine, candidate=candidate, reference=args.reference, config=config, corpus=corpus, overwrite=args.overwrite))
    append_measurements(all_records)
    print("Render complete. Blind-listen before selecting any candidate; metrics do not establish quality.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
