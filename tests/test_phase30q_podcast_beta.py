"""Phase 30Q registry/profile tests; no model inference."""
from __future__ import annotations

import numpy as np
import soundfile as sf

from backend import main as main_mod
from backend.app.tts.special_voices import SPECIAL_VOICES


class PodcastSpecialEngine:
    model_name = "mock-vieneu"
    device = "cpu"

    def get_voices(self): return ["default", "review_film", "podcast_brand_beta"]
    def get_preset_names(self): return ["default"]
    def get_user_voice_names(self): return []
    def get_special_voice_names(self): return ["review_film", "podcast_brand_beta"]
    def get_voice_metadata(self, name): return SPECIAL_VOICES[name] if name in SPECIAL_VOICES else {}
    def generate(self, text, out_path=None, **kwargs):
        sf.write(out_path, np.zeros(100, dtype=np.float32), 24000)
        return out_path
    def generate_prosody(self, text, out_path=None, **kwargs):
        assert "|" in text
        sf.write(out_path, np.zeros(100, dtype=np.float32), 24000)
        return out_path


def test_podcast_beta_special_profile_points_to_canonical_ma_keeper():
    profile = SPECIAL_VOICES["podcast_brand_beta"]
    assert profile["display_name"] == "🎙️ Podcast Brand (Beta)"
    assert profile["is_special"] is True
    assert profile["special_type"] == "podcast"
    assert str(profile["reference_path"]).endswith("keepers/phase30m_04/qwen_source.wav")
    assert str(profile["speaker_embedding_path"]).endswith("keepers/phase30m_04/speaker_emb.npy")
    assert str(profile["reference_codes_path"]).endswith("keepers/phase30m_04/reference_codes.npy")


def test_review_film_and_podcast_beta_are_listed_and_use_normal_tts_paths():
    engine = PodcastSpecialEngine()
    voices = main_mod.voices(engine=engine)["voices"]
    special = {item["id"]: item for item in voices if item["type"] == "special"}
    assert set(special) == {"review_film", "podcast_brand_beta"}
    assert special["podcast_brand_beta"]["name"] == "🎙️ Podcast Brand (Beta)"
    normal = main_mod.tts(main_mod.TTSRequest(text="Đoạn kiểm tra.", voice="podcast_brand_beta"), engine)
    marked = main_mod.tts(main_mod.TTSRequest(text="Đoạn kiểm tra.", tts_script="Đoạn | kiểm tra.", prosody_markup=True, voice="podcast_brand_beta"), engine)
    assert normal.media_type == marked.media_type == "audio/wav"
