#!/usr/bin/env python3
"""Provision Podcast Candidate B as an experimental voice in the local library.

Local, no-inference operation. Loads the canonical Phase 40B Candidate B
baseline .npy files (immutable package), verifies them against the baseline
manifest, then writes a rounded UI/library profile with the existing
``voice_store.serialize_profile`` contract (speaker_emb rounded to 6 decimals).

The canonical .npy files remain the ONLY source for cross-text validation; the
rounded data/voices/voices.json copy is UI/library-only.
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

VOICE_ID = "podcast_candidate_b"
BASELINE_MANIFEST_EXPECT = {
    "speaker_emb.npy": "0c0cbc23228c89cfc27b0d109603b42b3fa0ca071cf728801455ec2cae752b53",
    "reference_codes.npy": "38964457925e5cf4362c90026e4bf552ddf1cf6acc35bc9555cd06c12603efb8",
}


def _verify_baseline(definition: dict) -> dict:
    manifest_path = ROOT / definition["baseline_manifest_path"]
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    if manifest.get("name") != "PODCAST_CANDIDATE_B_BASELINE":
        raise RuntimeError("Baseline manifest name mismatch")
    loaded = {}
    for key in ("speaker_emb.npy", "reference_codes.npy"):
        path = ROOT / definition["speaker_embedding_path" if key == "speaker_emb.npy" else "reference_codes_path"]
        record = manifest["files"][key]
        # File-level integrity: hash of the literal .npy bytes on disk.
        if not path.is_file() or path.stat().st_size != record["size_bytes"]:
            raise RuntimeError(f"Baseline {key} size/path validation failed: {path}")
        if hashlib.sha256(path.read_bytes()).hexdigest() != record["sha256"]:
            raise RuntimeError(f"Baseline {key} file hash validation failed: {path}")
        arr = np.load(path, allow_pickle=False)
        # Array-level identity: hash of the raw array bytes must equal the frozen
        # Candidate B identity (matches Phase 40A manifest/geometry).
        array_sha = hashlib.sha256(np.ascontiguousarray(arr).tobytes()).hexdigest()
        if array_sha != record["array_sha256"]:
            raise RuntimeError(f"Baseline {key} array hash validation failed")
        if array_sha != BASELINE_MANIFEST_EXPECT.get(key):
            raise RuntimeError(f"Baseline {key} array hash does not match frozen Candidate B expectation")
        loaded[key] = arr
    return loaded


def main() -> int:
    definition = SPECIAL_VOICES[VOICE_ID]
    if definition.get("category") != "Podcast / Experimental":
        raise RuntimeError("Podcast Candidate B is not labelled Experimental")
    if definition.get("status") != "candidate" or definition.get("is_final_brand_voice") is not False:
        raise RuntimeError("Podcast Candidate B metadata must stay candidate / non-final")

    loaded = _verify_baseline(definition)
    voices = voice_store.load_user_voices()
    existing = voices.get(VOICE_ID)
    if existing:
        if existing.get("is_special") is True and existing.get("special_type") == "podcast_candidate":
            print("Podcast Candidate B profile is already provisioned locally.")
            return 0
        raise RuntimeError("podcast_candidate_b conflicts with an existing non-candidate profile")

    profile = {
        "description": definition["description"],
        "gender": "",
        "style": None,
        "speaker_emb": loaded["speaker_emb.npy"],
        "codes": loaded["reference_codes.npy"],
        **{
            key: definition[key]
            for key in ("category", "is_special", "special_type", "recommended_use", "display_name", "status", "is_final_brand_voice")
        },
    }
    voices[VOICE_ID] = voice_store.serialize_profile(profile)
    voice_store.save_user_voices(voices)
    print("Podcast Candidate B (Experimental) profile provisioned from canonical Phase 40B baseline.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())