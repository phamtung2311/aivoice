#!/usr/bin/env python3
"""Provision Podcast Brand (Beta) from verified canonical M-A native artifacts.

This is a local, no-inference operation. It reuses the M-A speaker embedding
and reference codes that VieNeu encoded during Phase 30M; it does not load
Qwen, VieNeu, or any remote model.
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

VOICE_ID = "podcast_brand_beta"
KEEPER_ID = "phase30m_04"


def _manifest_records() -> dict:
    manifest = json.loads((ROOT / "experiments/special_voice_podcast/keepers/KEEPERS_MANIFEST.json").read_text(encoding="utf-8"))
    keeper = next((item for item in manifest["keepers"] if item["keeper_id"] == KEEPER_ID), None)
    if keeper is None or keeper.get("original_identity") != "M-A":
        raise RuntimeError("Canonical M-A keeper is not unambiguous")
    return keeper["files"]


def _verify(path: Path, record: dict) -> None:
    if not path.is_file() or path.stat().st_size != record["size_bytes"]:
        raise RuntimeError(f"Keeper size/path validation failed: {path}")
    if hashlib.sha256(path.read_bytes()).hexdigest() != record["sha256"]:
        raise RuntimeError(f"Keeper hash validation failed: {path}")


def main() -> int:
    definition = SPECIAL_VOICES[VOICE_ID]
    records = _manifest_records()
    emb_path = ROOT / definition["speaker_embedding_path"]
    codes_path = ROOT / definition["reference_codes_path"]
    _verify(emb_path, records["speaker_emb.npy"])
    _verify(codes_path, records["reference_codes.npy"])
    voices = voice_store.load_user_voices()
    existing = voices.get(VOICE_ID)
    if existing:
        if existing.get("is_special") is True and existing.get("special_type") == "podcast":
            print("Podcast Brand (Beta) profile is already provisioned locally.")
            return 0
        raise RuntimeError("podcast_brand_beta conflicts with an existing non-special profile")
    profile = {
        "description": definition["description"], "gender": "", "style": None,
        "speaker_emb": np.load(emb_path, allow_pickle=False),
        "codes": np.load(codes_path, allow_pickle=False),
        **{key: definition[key] for key in ("category", "is_special", "special_type", "recommended_use", "display_name")},
    }
    voices[VOICE_ID] = voice_store.serialize_profile(profile)
    voice_store.save_user_voices(voices)
    print("Podcast Brand (Beta) profile provisioned from verified Phase30M M-A artifacts.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
