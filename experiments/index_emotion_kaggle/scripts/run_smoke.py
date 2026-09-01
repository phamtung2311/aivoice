#!/usr/bin/env python3
"""Generate exactly three smoke files, then stop for human listening."""
from __future__ import annotations

from pathlib import Path

from common import CONFIG_PATH, environment_text, load_json, load_run_manifest, save_run_manifest, set_best_effort_seed
from engine_adapter import load_low_vram_engine
from run_helpers import run_sample


def main() -> int:
    config = load_json(CONFIG_PATH)
    if config["smoke_test_approved"]:
        print("Smoke approval is already true. Do not regenerate: use run_matrix.py for the gated matrix.")
        return 2
    set_best_effort_seed(config["seed"])
    manifest = load_run_manifest()
    manifest["environment"]["text"] = environment_text()
    manifest["checkpoint_revisions"] = load_json(Path(CONFIG_PATH).parents[0] / "assets_manifest.json").get("actual_download_record")
    save_run_manifest(manifest)
    engine = load_low_vram_engine()
    generation = config["generation"]
    text = config["text"]
    run_sample(engine, sample_id="smoke_A_neutral", speaker="speaker_A", emotion="neutral", mode="shared_audio", text=text, generation=generation)
    run_sample(engine, sample_id="smoke_A_sad", speaker="speaker_A", emotion="sad", mode="shared_audio", text=text, generation=generation)
    run_sample(engine, sample_id="smoke_B_sad", speaker="speaker_B", emotion="sad", mode="shared_audio", text=text, generation=generation)
    print("SMOKE TEST COMPLETE. Listen to all three WAVs. Keep smoke_test_approved=false unless pronunciation, identity, emotion, naturalness, and donor leakage are acceptable.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
