#!/usr/bin/env python3
"""Audit VieNeu packaged presets for Phase 30D; never alter profiles or audio."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
PROJECT_ROOT = ROOT.parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

OUTPUT = ROOT / "outputs" / "phase30d"


def classify_profile(profile: dict) -> tuple[str, str]:
    """Classify only explicit packaged regional metadata, never speaker names."""
    description = str(profile.get("description", ""))
    for label in ("Bắc", "Nam", "Trung"):
        if f"· {label} ·" in description:
            return "REGIONAL", f"packaged metadata explicitly identifies {label} regional delivery"
    return "UNCERTAIN", "no explicit regional descriptor in packaged metadata"


def audit(model, phase30c_mapping: dict) -> list[dict]:
    profiles = getattr(model._v, "_preset_voices", {})
    previously_tested = {item["source"] for item in phase30c_mapping.get("mapping", {}).values()}
    records = []
    for name in sorted(model.get_preset_names()):
        profile = profiles.get(name, {})
        if not isinstance(profile, dict):
            continue
        classification, reason = classify_profile(profile)
        records.append({
            "source": name,
            "gender": profile.get("gender", ""),
            "style": profile.get("style", ""),
            "description": profile.get("description", ""),
            "classification": classification,
            "reason": reason,
            "previously_tested": name in previously_tested,
        })
    return records


def main() -> int:
    parser = argparse.ArgumentParser(description="Audit the local VieNeu preset pool for neutral Podcast candidates.")
    parser.add_argument("--audit-only", action="store_true", help="Required: Phase 30D does not synthesize regional profiles.")
    args = parser.parse_args()
    if not args.audit_only:
        parser.error("Use --audit-only; no neutral packaged profile has passed the Phase 30D filter.")

    from backend.app.tts.engine import TTSEngine

    phase30c_path = ROOT / "outputs" / "phase30c" / "phase30c_mapping.json"
    phase30c_mapping = json.loads(phase30c_path.read_text(encoding="utf-8"))
    engine = TTSEngine(backend="onnx")
    records = audit(engine._model, phase30c_mapping)
    eligible = [item for item in records if item["classification"] == "NEUTRAL_OR_BROAD"]
    OUTPUT.mkdir(parents=True, exist_ok=True)
    (OUTPUT / "phase30d_mapping.json").write_text(json.dumps({"mapping": {}, "audit": records, "eligible_count": len(eligible)}, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"total_presets": len(records), "regional": sum(item["classification"] == "REGIONAL" for item in records), "uncertain": sum(item["classification"] == "UNCERTAIN" for item in records), "neutral_or_broad": len(eligible), "status": "NATIVE_PRESET_POOL_INSUFFICIENT" if not eligible else "AUDITION_ELIGIBLE"}, ensure_ascii=False))
    return 0 if not eligible else 2


if __name__ == "__main__":
    raise SystemExit(main())
