#!/usr/bin/env python3
"""Render a blind audition of distinct local VieNeu preset identities only."""
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

OUTPUT = ROOT / "outputs" / "phase30c"
AUDITION_TEXT = (ROOT / "phase30c_audition.txt").read_text(encoding="utf-8").strip()
SEED = 30003
MAX_CANDIDATES = 10


def rss_mb() -> float:
    return resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1024.0


def select_candidates(model) -> list[dict]:
    """Choose packaged, independent identities; never synthesize variations."""
    profiles = getattr(model._v, "_preset_voices", {})
    preset_names = set(model.get_preset_names())
    candidates = []
    for name in preset_names:
        profile = profiles.get(name, {})
        if not isinstance(profile, dict):
            continue
        if profile.get("speaker_emb") is None or profile.get("codes") is None:
            continue
        candidates.append({
            "source": name,
            "gender": profile.get("gender", ""),
            "style": profile.get("style", ""),
            "source_type": "packaged_preset_profile",
        })
    # Male-oriented where available, followed only by narration-friendly natural
    # or story presets. These are separate profile embeddings/codes, not settings.
    male = sorted((item for item in candidates if item["gender"] == "male"), key=lambda item: item["source"])
    other = sorted((item for item in candidates if item["gender"] != "male" and item["style"] in {"tu_nhien", "doc_truyen"}), key=lambda item: item["source"])
    return (male + other)[:MAX_CANDIDATES]


def main() -> int:
    parser = argparse.ArgumentParser(description="Render blind, distinct VieNeu preset candidates.")
    parser.add_argument("--dry-run", action="store_true", help="Audit sources without inference or output writes.")
    parser.add_argument("--candidate-index", type=int, choices=range(1, MAX_CANDIDATES + 1), help="Render exactly one blind candidate; safe for constrained local shells.")
    args = parser.parse_args()

    from backend.app.tts.engine import TTSEngine

    engine = TTSEngine(backend="onnx")
    candidates = select_candidates(engine._model)
    if not candidates:
        raise SystemExit("EXTERNAL_REFERENCE_CANDIDATES_REQUIRED: no independent local preset identities found.")
    if args.dry_run:
        print(json.dumps({"candidate_count": len(candidates), "sources": candidates}, ensure_ascii=False, indent=2))
        return 0

    shuffled = list(candidates)
    random.Random(SEED).shuffle(shuffled)
    OUTPUT.mkdir(parents=True, exist_ok=True)
    mapping_path = OUTPUT / "phase30c_mapping.json"
    metrics_path = OUTPUT / "phase30c_metrics.json"
    existing_mapping = json.loads(mapping_path.read_text(encoding="utf-8")) if mapping_path.exists() else {"seed": SEED, "mapping": {}}
    existing_records = json.loads(metrics_path.read_text(encoding="utf-8")).get("records", []) if metrics_path.exists() else []
    selected = [(index, candidate) for index, candidate in enumerate(shuffled, start=1) if args.candidate_index in (None, index)]
    for index, candidate in selected:
        blind_id = f"podcast_candidate_{index:02d}"
        path = OUTPUT / f"{blind_id}.wav"
        if path.exists():
            raise SystemExit(f"Refusing to overwrite existing blind artifact: {path}")
        started = time.perf_counter()
        engine.generate(AUDITION_TEXT, voice=candidate["source"], speed=1.0, out_path=str(path), quality_diagnostics=True)
        wall = time.perf_counter() - started
        duration = engine.last_generation_diagnostics["final_duration_seconds"]
        existing_mapping["mapping"][blind_id] = candidate
        existing_records = [item for item in existing_records if item.get("candidate") != blind_id]
        existing_records.append({
            "candidate": blind_id,
            "wall_generation_seconds": round(wall, 3),
            "audio_duration_seconds": duration,
            "RTF": round(wall / duration, 4),
            "peak_RSS_MB": round(rss_mb(), 2),
        })
        mapping_path.write_text(json.dumps(existing_mapping, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        metrics_path.write_text(json.dumps({"audition_text_chars": len(AUDITION_TEXT), "records": existing_records}, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        print(f"DONE {blind_id}: {wall:.3f}s, RTF={wall / duration:.4f}")
    fields = next(csv.reader((ROOT / "phase30c_listening.csv").open(encoding="utf-8")))
    with (OUTPUT / "phase30c_listening.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader(); writer.writerows({"candidate": blind_id} for blind_id in sorted(existing_mapping["mapping"]))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
