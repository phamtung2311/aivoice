"""Phase 40B — Podcast Candidate B registry/profile tests; no model inference.

Verifies the baseline package integrity (canonical .npy), the special-voice
metadata contract (Experimental / candidate / non-final), the additive voice
store round-trip of the new metadata fields, and the /api/voices exposure.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

import numpy as np

from backend import main as main_mod
from backend.app.tts import voice_store
from backend.app.tts.special_voices import SPECIAL_VOICES

ROOT = Path(__file__).resolve().parents[1]
EXPECTED_DIR = ROOT / "experiments/brand_voice_phase40b"
BASELINE = EXPECTED_DIR / "baseline" / "PODCAST_CANDIDATE_B_BASELINE"


class CandidateBEngine:
    model_name = "mock-vieneu"
    device = "cpu"

    def get_voices(self): return ["default", "podcast_candidate_b"]
    def get_preset_names(self): return ["default"]
    def get_user_voice_names(self): return []
    def get_special_voice_names(self): return ["podcast_candidate_b"]
    def get_voice_metadata(self, name):
        return SPECIAL_VOICES.get(name, {})
    def generate(self, text, voice=None, speed=1.0, out_path=None, **kwargs):
        import soundfile as sf
        sf.write(out_path, np.zeros(1200, dtype=np.float32), 24000)
        return out_path


def test_baseline_package_files_are_canonical_candidate_b():
    assert BASELINE.is_dir(), "canonical baseline package is missing"
    manifest = json.loads((BASELINE / "manifest.json").read_text(encoding="utf-8"))
    assert manifest["name"] == "PODCAST_CANDIDATE_B_BASELINE"
    assert manifest["immutable"] is True
    assert manifest["status"] == "candidate"
    assert manifest["is_final_brand_voice"] is False
    for key in ("speaker_emb.npy", "reference_codes.npy"):
        path = BASELINE / key
        record = manifest["files"][key]
        assert path.is_file() and path.stat().st_size == record["size_bytes"]
        assert hashlib.sha256(path.read_bytes()).hexdigest() == record["sha256"]
        arr = np.load(path, allow_pickle=False)
        assert hashlib.sha256(np.ascontiguousarray(arr).tobytes()).hexdigest() == record["array_sha256"]
    emb = np.load(BASELINE / "speaker_emb.npy", allow_pickle=False)
    codes = np.load(BASELINE / "reference_codes.npy", allow_pickle=False)
    assert emb.dtype == np.float32 and emb.shape == (192,)
    assert codes.dtype == np.int64 and codes.shape == (42, 16)
    # Candidate B identity hashes match Phase 40A manifest/geometry.
    assert hashlib.sha256(emb.tobytes()).hexdigest() == "0c0cbc23228c89cfc27b0d109603b42b3fa0ca071cf728801455ec2cae752b53"
    assert hashlib.sha256(codes.tobytes()).hexdigest() == "38964457925e5cf4362c90026e4bf552ddf1cf6acc35bc9555cd06c12603efb8"


def test_podcast_candidate_b_special_metadata_contract():
    profile = SPECIAL_VOICES["podcast_candidate_b"]
    assert profile["display_name"] == "🎙️ Podcast Candidate B (Thử nghiệm)"
    assert profile["category"] == "Podcast / Experimental"
    assert profile["status"] == "candidate"
    assert profile["is_final_brand_voice"] is False
    assert profile["is_special"] is True
    assert profile["special_type"] == "podcast_candidate"
    assert str(profile["speaker_embedding_path"]).endswith(
        "baseline/PODCAST_CANDIDATE_B_BASELINE/speaker_emb.npy"
    )
    assert str(profile["reference_codes_path"]).endswith(
        "baseline/PODCAST_CANDIDATE_B_BASELINE/reference_codes.npy"
    )


def test_new_metadata_fields_roundtrip_additively():
    raw = {
        "speaker_emb": np.linspace(-1.0, 1.0, 8, dtype=np.float32),
        "codes": np.array([[1, 2], [3, 4]], dtype=np.int64),
        "category": "Podcast / Experimental",
        "status": "candidate",
        "is_final_brand_voice": False,
        "is_special": True,
        "special_type": "podcast_candidate",
        "display_name": "x",
        "recommended_use": "y",
    }
    serialized = voice_store.serialize_profile(raw)
    restored = voice_store.deserialize_profile(serialized)
    assert restored["category"] == "Podcast / Experimental"
    assert restored["status"] == "candidate"
    assert restored["is_final_brand_voice"] is False
    assert restored["special_type"] == "podcast_candidate"


def test_podcast_candidate_b_listed_as_special_via_api():
    engine = CandidateBEngine()
    main_mod.app.dependency_overrides[main_mod.get_engine] = lambda: engine
    try:
        voices = main_mod.voices(engine=engine)["voices"]
        item = next(v for v in voices if v["id"] == "podcast_candidate_b")
        assert item["type"] == "special"
        assert item["category"] == "Podcast / Experimental"
        assert item["status"] == "candidate"
        assert item["is_final_brand_voice"] is False
        response = main_mod.tts(
            main_mod.TTSRequest(text="Đây là câu kiểm tra.", voice="podcast_candidate_b", speed=1.0),
            engine=engine,
        )
        assert response.media_type == "audio/wav"
    finally:
        main_mod.app.dependency_overrides.clear()