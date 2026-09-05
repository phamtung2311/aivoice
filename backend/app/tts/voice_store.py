"""Persistence for user-created voice profiles.

Voice profiles are local personal data (speaker embedding + reference codes =
biometric-like). They are stored under ``data/voices/`` (gitignored) and use the
same JSON shape as vieneu's native ``save_voices()`` so a profile can be restored
into the loaded model without re-encoding the reference audio.

We deliberately do NOT write into the installed ``vieneu`` package directory.
"""
from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any, Dict, Optional

import numpy as np

DEFAULT_STORE_DIR = Path("data") / "voices"
DEFAULT_STORE_FILE = DEFAULT_STORE_DIR / "voices.json"

# Maximum length for a user-chosen voice name.
VOICE_NAME_MAX_LENGTH = 64
PROFILE_METADATA_FIELDS = (
    "category",
    "is_special",
    "special_type",
    "recommended_use",
    "display_name",
    "status",
    "is_final_brand_voice",
)


def store_path() -> Path:
    env = os.environ.get("VOICE_STORE_PATH")
    if env:
        return Path(env)
    return DEFAULT_STORE_FILE


def validate_voice_name(name: Optional[str]) -> str:
    """Normalize and validate a voice profile name. Raise ValueError on reject."""
    if name is None:
        raise ValueError("Tên giọng không được để trống.")
    n = str(name).strip()
    if not n:
        raise ValueError("Tên giọng không được để trống.")
    if len(n) > VOICE_NAME_MAX_LENGTH:
        raise ValueError(f"Tên giọng quá dài (tối đa {VOICE_NAME_MAX_LENGTH} ký tự).")
    # Reject path separators / control characters (also blocks path traversal).
    if any(c in "/\\" for c in n) or any(ord(c) < 32 for c in n):
        raise ValueError("Tên giọng không hợp lệ.")
    return n


def save_user_voices(profiles: Dict[str, Dict[str, Any]], path: Optional[Path] = None) -> str:
    """Write voice profiles to a JSON file (atomic replace)."""
    p = Path(path) if path is not None else store_path()
    p.parent.mkdir(parents=True, exist_ok=True)
    payload = {"version": 1, "voices": profiles}
    tmp = p.with_suffix(".json.tmp")
    tmp.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    os.replace(tmp, p)
    return str(p)


def load_user_voices(path: Optional[Path] = None) -> Dict[str, Dict[str, Any]]:
    """Load voice profiles from disk; missing/corrupt file yields empty dict."""
    p = Path(path) if path is not None else store_path()
    if not p.exists():
        return {}
    try:
        data = json.loads(p.read_text(encoding="utf-8"))
    except Exception:
        return {}
    voices = data.get("voices", {}) if isinstance(data, dict) else {}
    return {k: v for k, v in voices.items() if isinstance(v, dict)}


def serialize_profile(v: Dict[str, Any], default_style: Optional[str] = None) -> Dict[str, Any]:
    """Flatten a native Vieneu voice-profile dict into the persisted JSON shape.

    Mirrors vieneu's own ``save_voices()``: ``speaker_emb`` is flattened and
    rounded to 6 decimals, ``codes`` become plain ints, descriptive metadata
    passes through. Phase 22.1 extracts this so the round-trip
    (dtype/shape/precision) is testable without loading the TTS model.
    """
    emb = v.get("speaker_emb")
    codes = v.get("codes")
    profile = {
        "description": v.get("description", ""),
        "gender": v.get("gender", ""),
        "style": v.get("style", default_style),
        "speaker_emb": [round(float(x), 6) for x in np.asarray(emb).reshape(-1)] if emb is not None else None,
        "codes": np.asarray(codes, dtype=int).tolist() if codes is not None else None,
    }
    # Additive metadata: older profiles omit these keys and retain their schema.
    for key in PROFILE_METADATA_FIELDS:
        if key in v:
            profile[key] = v.get(key)
    return profile


def deserialize_profile(d: Dict[str, Any], default_style: Optional[str] = None) -> Dict[str, Any]:
    """Rebuild native arrays from the persisted JSON shape (float32 emb, int64 codes)."""
    profile = {
        "description": d.get("description", ""),
        "gender": d.get("gender", ""),
        "style": d.get("style", default_style),
        "speaker_emb": np.asarray(d.get("speaker_emb"), dtype=np.float32) if d.get("speaker_emb") is not None else None,
        "codes": np.asarray(d.get("codes"), dtype=np.int64) if d.get("codes") is not None else None,
    }
    for key in PROFILE_METADATA_FIELDS:
        if key in d:
            profile[key] = d.get(key)
    return profile
