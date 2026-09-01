#!/usr/bin/env python3
"""Render the finite, blind Phase 30B short test with native VieNeu defaults."""
from __future__ import annotations

import argparse
import csv
import json
import random
import resource
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent
PROJECT_ROOT = ROOT.parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

REFERENCE = ROOT / "reference_audio" / "podcast_reference.wav"
OUTPUT = ROOT / "outputs" / "phase30b_short"
SHORT_IDS = ("reflective", "serious_observation", "long_complex")


def rss_mb() -> float:
    return resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1024.0


def validate_reference(path: Path) -> dict:
    """Return lightweight DSP evidence and reject clearly unsuitable input."""
    if not path.is_file():
        raise SystemExit(f"REFERENCE_REQUIRED: place a permissioned WAV at {path}")
    try:
        from backend.app.tts.reference_quality import analyze_wav

        report = analyze_wav(path).to_dict()
    except Exception as exc:
        raise SystemExit(f"REFERENCE_INVALID: cannot decode {path}: {exc}") from exc
    metrics = report["metrics"]
    failures = []
    if not 6.0 <= metrics["duration_seconds"] <= 8.0:
        failures.append("duration must be 6–8 seconds")
    if metrics["clipping"]["ratio"] > 0.002:
        failures.append("clipping is too high")
    if metrics["leading_silence"] > 0.8 or metrics["ending_silence"] > 1.0:
        failures.append("leading or trailing silence is too long")
    if metrics["rms"] < 0.01:
        failures.append("signal level is too low")
    report["validation"] = {"status": "valid" if not failures else "unsuitable", "reasons": failures}
    if failures:
        raise SystemExit("REFERENCE_UNSUITABLE: " + "; ".join(failures) + "\n" + json.dumps(report, ensure_ascii=False, indent=2))
    return report


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--reference", type=Path, default=REFERENCE, help="User-supplied, permissioned candidate WAV.")
    parser.add_argument("--control-voice", help="Existing normal VieNeu preset/profile for the blind control.")
    parser.add_argument("--validate-only", action="store_true", help="Validate reference only; do not load the TTS engine.")
    args = parser.parse_args()
    if args.validate_only and args.control_voice:
        parser.error("--validate-only cannot be combined with --control-voice")
    if not args.validate_only and not args.control_voice:
        parser.error("--control-voice is required to generate the short test")

    report = validate_reference(args.reference)
    print(json.dumps(report, ensure_ascii=False, indent=2))
    if args.validate_only:
        return 0
    if OUTPUT.exists() and any(OUTPUT.rglob("*.wav")):
        raise SystemExit(f"Refusing to overwrite blind artifacts: {OUTPUT}")

    corpus = json.loads((ROOT / "test_sentences.json").read_text(encoding="utf-8"))
    sentences = [item for item in corpus["sentences"] if item["id"] in SHORT_IDS]
    if tuple(item["id"] for item in sentences) != SHORT_IDS:
        raise SystemExit("Required short-test sentences are missing or reordered.")
    import numpy as np

    from backend.app.tts.engine import TTSEngine

    engine = TTSEngine(backend="onnx")
    if args.control_voice not in set(engine.get_voices() or []):
        raise SystemExit("Control voice is unavailable in the current local engine.")
    speaker_emb, codes = engine._model.encode_reference(str(args.reference), denoise=True, use_ref_codes=True)
    candidate = {"speaker_emb": speaker_emb, "codes": codes}
    mapping, rows, records = {}, [], []
    rng = random.Random(30002)
    for index, item in enumerate(sentences, start=1):
        group = f"group_{index:02d}"
        folder = OUTPUT / group
        folder.mkdir(parents=True)
        variants = [("control", args.control_voice), ("podcast_candidate", candidate)]
        rng.shuffle(variants)
        mapping[group] = {"sentence_id": item["id"], "samples": {}}
        for sample_number, (kind, voice) in enumerate(variants, start=1):
            sample_id = f"sample_{sample_number:02d}"
            path = folder / f"{sample_id}.wav"
            np.random.seed(30002 + index)
            started = time.perf_counter()
            engine.generate(item["text"], voice=voice, speed=1.0, out_path=str(path), denoise=True, use_ref_codes=True, quality_diagnostics=True)
            wall = time.perf_counter() - started
            duration = engine.last_generation_diagnostics["final_duration_seconds"]
            mapping[group]["samples"][sample_id] = kind
            rows.append({"group": group, "sample_id": sample_id})
            records.append({"group": group, "sample_id": sample_id, "wall_generation_seconds": round(wall, 3), "audio_duration_seconds": duration, "RTF": round(wall / duration, 4), "peak_RSS_MB": round(rss_mb(), 2)})
    (OUTPUT / "phase30b_mapping.json").write_text(json.dumps(mapping, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    (OUTPUT / "phase30b_metrics.json").write_text(json.dumps({"reference_quality": report, "reference_encoded_once": True, "records": records}, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    fields = next(csv.reader((ROOT / "evaluation.csv").open(encoding="utf-8")))
    with (OUTPUT / "phase30b_listening.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader(); writer.writerows(rows)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
