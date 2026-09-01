#!/usr/bin/env python3
"""Generate only the finite Phase 30A blind smoke set when a reference exists."""
from __future__ import annotations

import argparse
import csv
import json
import random
import resource
import sys
import time
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parent
PROJECT_ROOT = ROOT.parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from backend.app.tts.audio import save_wav
from backend.app.tts.engine import TTSEngine
from backend.app.tts.reference_quality import analyze_clip

REFERENCE = ROOT / "reference_audio" / "meme_breath.wav"
OUTPUT = ROOT / "outputs" / "phase30a"
SMOKE_IDS = ("normal", "punchline", "question")


def rss_mb() -> float:
    return resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1024.0


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--control-voice", required=True, help="Existing permissioned VieNeu preset/profile.")
    args = parser.parse_args()
    if not REFERENCE.is_file():
        raise SystemExit(f"REFERENCE_REQUIRED: place a permissioned WAV at {REFERENCE}")
    report = analyze_clip(REFERENCE.read_bytes()).to_dict()
    duration = report["metrics"]["duration_seconds"]
    if not 5.0 <= duration <= 8.5:
        raise SystemExit(f"Reference duration {duration}s is outside the approved useful range.")
    if OUTPUT.exists() and any(OUTPUT.rglob("*.wav")):
        raise SystemExit(f"Refusing to overwrite existing blind artifacts: {OUTPUT}")
    corpus = json.loads((ROOT / "test_sentences.json").read_text(encoding="utf-8"))
    sentences = [item for item in corpus["sentences"] if item["id"] in SMOKE_IDS]
    if [item["id"] for item in sentences] != list(SMOKE_IDS):
        raise SystemExit("Required smoke sentences are missing.")
    engine = TTSEngine(backend="onnx")
    if args.control_voice not in set(engine.get_voices() or []):
        raise SystemExit("Control voice is unavailable in the current local engine.")
    speaker_emb, codes = engine._model.encode_reference(str(REFERENCE), denoise=True, use_ref_codes=True)
    reference_voice = {"speaker_emb": speaker_emb, "codes": codes}
    OUTPUT.mkdir(parents=True)
    mapping, rows, records = {}, [], []
    rng = random.Random(30001)
    for index, item in enumerate(sentences, start=1):
        folder = OUTPUT / f"sentence_{index:02d}_{item['id']}"; folder.mkdir()
        variants = [("control", args.control_voice), ("meme_breath", reference_voice)]
        rng.shuffle(variants); mapping[item["id"]] = {}
        for sample_number, (kind, voice) in enumerate(variants, start=1):
            sample_id = f"sample_{sample_number:02d}"; path = folder / f"{sample_id}.wav"
            np.random.seed(30000 + index)
            started = time.perf_counter()
            # No sampling override: both use native production defaults and speed 1.0.
            engine.generate(item["text"], voice=voice, speed=1.0, out_path=str(path), denoise=True, use_ref_codes=True, quality_diagnostics=True)
            duration_out = engine.last_generation_diagnostics["final_duration_seconds"]
            records.append({"sentence_id": item["id"], "sample_id": sample_id, "wall_generation_seconds": round(time.perf_counter()-started, 3), "audio_duration_seconds": duration_out, "RTF": round((time.perf_counter()-started)/duration_out, 4), "peak_RSS_MB": round(rss_mb(), 2)})
            mapping[item["id"]][sample_id] = kind; rows.append({"sentence_id": item["id"], "sample_id": sample_id})
    (OUTPUT / "phase30a_mapping.json").write_text(json.dumps(mapping, ensure_ascii=False, indent=2)+"\n", encoding="utf-8")
    (OUTPUT / "phase30a_metrics.json").write_text(json.dumps({"reference_quality": report, "reference_encoded_once": True, "records": records}, ensure_ascii=False, indent=2)+"\n", encoding="utf-8")
    with (OUTPUT / "phase30a_listening.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=["sentence_id", "sample_id", "naturalness_1_5", "meme_suitability_1_5", "distinctive_character_1_5", "breathy_airy_character_1_5", "clarity_1_5", "voice_consistency_1_5", "robotic_rhythm_1_5", "preferred", "notes"])
        writer.writeheader(); writer.writerows(rows)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
