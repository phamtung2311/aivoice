#!/usr/bin/env python3
"""Generate the exact shared-audio 3 × 4 matrix after human approval only."""
from __future__ import annotations

from common import CONFIG_PATH, load_json, set_best_effort_seed
from engine_adapter import load_low_vram_engine
from run_helpers import run_sample


def main() -> int:
    config = load_json(CONFIG_PATH)
    if config.get("smoke_test_approved") is not True:
        print("MATRIX BLOCKED: manually listen to smoke outputs, then set smoke_test_approved=true in poc_config.json.")
        return 2
    set_best_effort_seed(config["seed"])
    engine = load_low_vram_engine()
    for speaker in config["speakers"]:
        for emotion in config["emotions"]:
            run_sample(engine, sample_id=f"matrix_{speaker}_{emotion}", speaker=speaker, emotion=emotion, mode="shared_audio", text=config["text"], generation=config["generation"])
    print("MATRIX COMPLETE. Human listening evaluation remains required.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
