#!/usr/bin/env python3
"""Render one controlled VieNeu baseline for the Phase 42B listening set.

This is deliberately a standalone experiment script: it reads project code but
does not edit its configuration, saved voices, or production artifacts.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path

import numpy as np
import soundfile as sf

# Running a script by path makes its directory, rather than the repository
# root, the first import location.
REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
if str(REPOSITORY_ROOT) not in sys.path:
    sys.path.insert(0, str(REPOSITORY_ROOT))

from backend.app.tts.engine import TTSEngine


ROOT = Path(__file__).resolve().parent
TEST_SET = ROOT.parent / "personal_voice_phase42a" / "test_set.json"


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--reference", required=True, type=Path)
    parser.add_argument("--reference-id", required=True)
    parser.add_argument("--test-id", required=True)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    args.reference = args.reference.resolve()
    args.output = args.output.resolve()
    if args.output.exists():
        raise FileExistsError(f"refusing to overwrite {args.output}")

    tests = {item["id"]: item for item in json.loads(TEST_SET.read_text(encoding="utf-8"))["tests"]}
    test = tests.get(args.test_id)
    if test is None:
        raise KeyError(args.test_id)
    ref_info = sf.info(args.reference)
    ref_duration = ref_info.frames / ref_info.samplerate

    args.output.parent.mkdir(parents=True, exist_ok=True)
    engine = TTSEngine(cache_model=True)
    engine.generate(
        test["text"],
        ref_audio=str(args.reference),
        out_path=str(args.output),
        speed=1.0,
        max_chunk_chars=240,
        # Diagnostics make the baseline's normal engine joins inspectable;
        # no Phase 41 prosody planner, tempo adjustment, or mastering is used.
        quality_diagnostics=True,
    )
    info = sf.info(args.output)
    audio, _ = sf.read(args.output, dtype="float32")
    manifest = {
        "phase": "42B",
        "engine": "VieNeu 3.3.0 v3 Turbo",
        "mode": "current_production_baseline_no_config_change",
        "research_only_comparison": True,
        "reference_id": args.reference_id,
        "reference_path": str(args.reference),
        "reference_sha256": sha256(args.reference),
        "reference_duration_seconds": ref_duration,
        "test_id": args.test_id,
        "text": test["text"],
        "text_sha256": hashlib.sha256(test["text"].encode()).hexdigest(),
        "output_path": str(args.output),
        "output_sha256": sha256(args.output),
        "sample_rate": info.samplerate,
        "duration_seconds": info.frames / info.samplerate,
        "peak": float(np.max(np.abs(audio))) if audio.size else 0.0,
        "clipped": bool(np.max(np.abs(audio)) >= 0.999) if audio.size else False,
        "diagnostics": engine.last_generation_diagnostics,
        "postprocessing": "none; normal TTSEngine generation only",
        "production_engine_changed": False,
    }
    metadata = ROOT / "metadata" / f"{args.output.stem}.json"
    metadata.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(manifest, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
