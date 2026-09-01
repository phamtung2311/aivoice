"""Phase 29D special voice metadata/API regression tests; no real inference."""
from __future__ import annotations

import numpy as np
import soundfile as sf

from backend import main as main_mod
from backend.app.tts import voice_store


class SpecialVoiceEngine:
    model_name = "mock-vieneu"
    device = "cpu"

    def get_voices(self): return ["default", "saved", "review_film"]
    def get_preset_names(self): return ["default"]
    def get_user_voice_names(self): return ["saved"]
    def get_special_voice_names(self): return ["review_film"]
    def get_voice_metadata(self, name):
        return {"display_name": "🎬 Review Film", "category": "Special Voice", "is_special": True,
                "special_type": "review_film", "description": "Giọng kể chuyện chuyên cho nội dung review phim và tóm tắt cốt truyện.",
                "recommended_use": "Review phim."} if name == "review_film" else {}
    def generate(self, text, voice=None, speed=1.0, out_path=None, **kwargs):
        assert voice in self.get_voices()
        sf.write(out_path, np.zeros(1200, dtype=np.float32), 24000)
        return out_path


def test_special_metadata_roundtrip_is_additive():
    raw = {"speaker_emb": np.array([0.1]), "codes": np.array([[1, 2]]), "is_special": True,
           "display_name": "🎬 Review Film", "category": "Special Voice", "special_type": "review_film",
           "recommended_use": "Review phim.", "description": "x"}
    serialized = voice_store.serialize_profile(raw)
    restored = voice_store.deserialize_profile(serialized)
    assert restored["is_special"] is True
    assert restored["special_type"] == "review_film"
    assert restored["speaker_emb"].dtype == np.float32


def test_special_voice_is_listed_and_uses_normal_tts_api():
    engine = SpecialVoiceEngine()
    main_mod.app.dependency_overrides[main_mod.get_engine] = lambda: engine
    try:
        voices = main_mod.voices(engine=engine)["voices"]
        review = next(item for item in voices if item["id"] == "review_film")
        assert review["type"] == "special"
        assert review["category"] == "Special Voice"
        response = main_mod.tts(main_mod.TTSRequest(text="Đây là câu kiểm tra.", voice="review_film", speed=1.0), engine=engine)
        assert response.media_type == "audio/wav"
    finally:
        main_mod.app.dependency_overrides.clear()
