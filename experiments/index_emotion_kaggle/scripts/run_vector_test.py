#!/usr/bin/env python3
"""Optional two-file vector experiment. Never called by run_matrix.py."""
from __future__ import annotations

from common import CONFIG_PATH, load_json, set_best_effort_seed
from engine_adapter import load_low_vram_engine
from run_helpers import run_sample


def main() -> int:
    config = load_json(CONFIG_PATH)
    vector_test = config["secondary_vector_test"]
    if vector_test.get("enabled") is not True:
        print("VECTOR TEST BLOCKED: set secondary_vector_test.enabled=true only after shared-audio evaluation succeeds.")
        return 2
    if config.get("smoke_test_approved") is not True:
        print("VECTOR TEST BLOCKED: smoke_test_approved must be true.")
        return 2
    set_best_effort_seed(config["seed"])
    engine = load_low_vram_engine()
    for speaker in ("speaker_A", "speaker_B"):
        run_sample(engine, sample_id=f"vector_{speaker}_{vector_test['emotion']}", speaker=speaker, emotion=vector_test["emotion"], mode="vector", text=config["text"], generation=config["generation"], vector=vector_test["vector"])
    print("VECTOR TEST COMPLETE. Listen before any further experiment.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
