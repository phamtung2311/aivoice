#!/usr/bin/env python3
"""Provision Synthetic Podcast Candidate 03 as an experimental voice in the local library.

Follows the same safe checks used by `install_podcast_candidate_b.py`: verifies
manifest file and array-level identity where available, then writes a rounded
UI/library profile into `data/voices/voices.json` using `voice_store.serialize_profile`.

This script does NOT modify canonical .npy artifacts; it only writes the UI copy.
"""
from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from backend.app.tts import voice_store
from backend.app.tts.special_voices import SPECIAL_VOICES

VOICE_ID = "podcast_synthetic_candidate_03"

# We don't have a previously-known array hash to compare against; this script
# verifies manifest presence and file-level integrity only.


def _verify_baseline(definition: dict) -> dict:
    manifest_path = ROOT / definition["baseline_manifest_path"]
    if not manifest_path.is_file():
        raise RuntimeError(f"Baseline manifest missing: {manifest_path}")
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    loaded = {}
    # Verify file-level presence and hashes if manifest lists them
    for key, field in (("speaker_emb.npy", "speaker_embedding_path"), ("reference_codes.npy", "reference_codes_path")):
        path = ROOT / definition[field]
        if not path.is_file():
            raise RuntimeError(f"Baseline asset missing: {path}")
        # If manifest contains file info, validate size and sha256
        files = manifest.get("files", {})
        if key in files:
            rec = files[key]
            if path.stat().st_size != rec.get("size_bytes", path.stat().st_size):
                raise RuntimeError(f"Baseline {key} size mismatch: {path}")
            if hashlib.sha256(path.read_bytes()).hexdigest() != rec.get("sha256", hashlib.sha256(path.read_bytes()).hexdigest()):
                raise RuntimeError(f"Baseline {key} file hash mismatch: {path}")
        arr = np.load(path, allow_pickle=False)
        loaded[key] = arr
    return loaded


def main() -> int:
    definition = SPECIAL_VOICES.get(VOICE_ID)
    if not definition:
        raise RuntimeError(f"Special voice definition {VOICE_ID} not found in SPECIAL_VOICES")

    if definition.get("category") != "Podcast / Experimental":
        raise RuntimeError("Voice category mismatch")
    if definition.get("status") != "candidate" or definition.get("is_final_brand_voice") is not False:
        raise RuntimeError("Metadata must stay candidate / non-final")

    loaded = _verify_baseline(definition)
    voices = voice_store.load_user_voices()
    existing = voices.get(VOICE_ID)
    if existing:
        if existing.get("is_special") is True and existing.get("special_type") == "synthetic_podcast_candidate":
            print("podcast_synthetic_candidate_03 profile is already provisioned locally.")
            return 0
        raise RuntimeError("podcast_synthetic_candidate_03 conflicts with an existing non-special profile")

    profile = {
        "description": definition.get("description", ""),
        "gender": "",
        "style": None,
        "speaker_emb": loaded["speaker_emb.npy"],
        "codes": loaded["reference_codes.npy"],
        **{
            key: definition[key]
            for key in ("category", "is_special", "special_type", "recommended_use", "display_name", "status", "is_final_brand_voice")
            if key in definition
        },
    }
    voices[VOICE_ID] = voice_store.serialize_profile(profile)
    out = voice_store.save_user_voices(voices)
    print(f"Provisioned {VOICE_ID} into local voice store: {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
