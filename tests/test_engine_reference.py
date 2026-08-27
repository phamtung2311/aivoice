import numpy as np

from backend.app.tts.engine import TTSEngine


class RecordingModel:
    sample_rate = 24000

    def __init__(self):
        self.calls = []
        self.speaker_emb = np.array([0.25, -0.5], dtype=np.float32)
        self.codes = np.array([[1, 2], [3, 4]], dtype=np.int64)

    def encode_reference(self, path, **kwargs):
        return self.speaker_emb, self.codes

    def infer(self, text, voice=None, **kwargs):
        self.calls.append((text, voice, kwargs))
        return np.zeros(240, dtype=np.float32)


def test_reference_identity_uses_native_voice_profile(tmp_path):
    model = RecordingModel()
    engine = TTSEngine(cache_model=False)
    engine._model = model

    engine.generate(
        "Xin chao",
        voice="Adam",
        ref_audio=str(tmp_path / "reference.wav"),
        out_path=str(tmp_path / "result.wav"),
    )

    _, voice, kwargs = model.calls[0]
    assert np.array_equal(voice["speaker_emb"], model.speaker_emb)
    assert np.array_equal(voice["codes"], model.codes)
    assert "ref_codes" not in kwargs
