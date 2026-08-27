"""Phase 12.1 — native emotion cue pass-through tests (mock engine)."""
import io

import numpy as np
import soundfile as sf
from fastapi.testclient import TestClient

from backend import main as main_mod


class RecordingEngine:
    def __init__(self):
        self.model_name = "dummy-model"
        self.device = "cpu"
        self.last_text = None
        self._user = {}
        self._preset = ["default"]

    def get_voices(self):
        return sorted(set(self._preset) | set(self._user))

    def get_preset_names(self):
        return list(self._preset)

    def get_user_voice_names(self):
        return sorted(self._user)

    def add_saved_voice(self, name, ref_audio):
        self._user[name] = {}
        return name

    def delete_saved_voice(self, name):
        if name in self._preset:
            return False
        self._user.pop(name, None)
        return True

    def generate(self, text, voice=None, speed=1.0, out_path=None, **kwargs):
        self.last_text = text
        sr = 22050
        t = np.linspace(0, 0.05, int(sr * 0.05), False)
        data = 0.05 * np.sin(2 * np.pi * 440 * t).astype(np.float32)
        sf.write(out_path, data, sr)
        return out_path


def setup_module(module):
    module._rec = RecordingEngine()
    main_mod.app.dependency_overrides[main_mod.get_engine] = lambda: module._rec


def teardown_module(module):
    main_mod.app.dependency_overrides.clear()


client = TestClient(main_mod.app)


def test_emotion_cue_accepted_in_text():
    text = "[cười]\nHôm nay chúng ta cùng bắt đầu."
    r = client.post("/api/tts", json={"text": text, "voice": "default", "speed": 1.0})
    assert r.status_code == 200
    # the native inline cue passes through untouched to the model text path
    assert _rec.last_text is not None
    assert "[cười]" in _rec.last_text


def test_all_supported_cues_accepted():
    text = "[cười] Vui quá. [thở dài] Mệt thật. [hắng giọng] Được rồi."
    r = client.post("/api/tts", json={"text": text, "voice": "default", "speed": 1.0})
    assert r.status_code == 200
    for cue in ("[cười]", "[thở dài]", "[hắng giọng]"):
        assert cue in _rec.last_text


def test_inline_cue_with_saved_voice():
    # save a voice first
    wav = io.BytesIO()
    t = np.linspace(0, 0.5, int(22050 * 0.5), False)
    data = 0.05 * np.sin(2 * np.pi * 440 * t).astype(np.float32)
    sf.write(wav, data, 22050, format="WAV")
    wav.seek(0)
    files = {"ref_audio": ("ref.wav", wav.read(), "audio/wav")}
    r = client.post("/api/voices/save", data={"name": "Emo Voice"}, files=files)
    assert r.status_code == 200
    # emotion + saved voice works together (separate channels)
    r2 = client.post("/api/tts", json={"text": "[thở dài]\nGiờ thì kể chuyện thôi.", "voice": "Emo Voice", "speed": 1.0})
    assert r2.status_code == 200
    assert "[thở dài]" in _rec.last_text


def test_unknown_emotion_does_not_crash():
    # Unknown bracketed tags are preserved as plain text by vieneu (graceful).
    r = client.post("/api/tts", json={"text": "[không tồn tại]\nChào bạn.", "voice": "default", "speed": 1.0})
    assert r.status_code == 200
    assert r.headers.get("content-type", "").startswith("audio/")
    assert _rec.last_text is not None