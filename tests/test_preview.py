"""Phase 13 — voice preview contract tests (server side, mock engine).

The preview feature is frontend-driven: it reuses POST /api/tts with a fixed
sample text and speed 1.0. These tests pin the server-side contract that the
preview relies on: correct text/voice/speed forwarding, saved-voice support,
and graceful failure for unknown voices.
"""
import io

import numpy as np
import soundfile as sf
from fastapi.testclient import TestClient

from backend import main as main_mod

# Must match VOICE_PREVIEW_TEXT in frontend/app.js
VOICE_PREVIEW_TEXT = 'Xin chào, đây là giọng đọc mẫu của aivoice.'


class RecordingEngine:
    def __init__(self):
        self.model_name = "dummy-model"
        self.device = "cpu"
        self._user = {}
        self._preset = ["default", "Kim Thanh"]
        self.last_text = None
        self.last_voice = None
        self.last_speed = None

    def get_voices(self):
        return sorted(set(self._preset) | set(self._user))

    def get_preset_names(self):
        return list(self._preset)

    def get_user_voice_names(self):
        return sorted(self._user)

    def add_saved_voice(self, name, ref_audio):
        if name in self._preset or name in self._user:
            raise ValueError("exists")
        self._user[name] = {}
        return name

    def delete_saved_voice(self, name):
        if name in self._preset:
            return False
        self._user.pop(name, None)
        return True

    def generate(self, text, voice=None, speed=1.0, out_path=None, **kwargs):
        self.last_text = text
        self.last_voice = voice
        self.last_speed = speed
        sr = 22050
        t = np.linspace(0, 0.05, int(sr * 0.05), False)
        data = 0.05 * np.sin(2 * np.pi * 440 * t).astype(np.float32)
        sf.write(out_path, data, sr)
        return out_path


def _wav_bytes(duration_s=0.5, sr=22050):
    t = np.linspace(0, duration_s, int(sr * duration_s), False)
    data = 0.05 * np.sin(2 * np.pi * 440 * t).astype(np.float32)
    bio = io.BytesIO()
    sf.write(bio, data, sr, format="WAV")
    bio.seek(0)
    return bio.read()


def setup_module(module):
    module._rec = RecordingEngine()
    main_mod.app.dependency_overrides[main_mod.get_engine] = lambda: module._rec


def teardown_module(module):
    main_mod.app.dependency_overrides.clear()


client = TestClient(main_mod.app)


def test_preview_request_uses_fixed_text_and_voice():
    r = client.post("/api/tts", json={"text": VOICE_PREVIEW_TEXT, "voice": "Kim Thanh", "speed": 1.0})
    assert r.status_code == 200
    assert r.headers.get("content-type", "").startswith("audio/")
    assert _rec.last_text == VOICE_PREVIEW_TEXT
    assert _rec.last_voice == "Kim Thanh"
    assert _rec.last_speed == 1.0


def test_preview_with_saved_voice_uses_saved_profile():
    files = {"ref_audio": ("ref.wav", _wav_bytes(), "audio/wav")}
    r = client.post("/api/voices/save", data={"name": "PrevVoice"}, files=files)
    assert r.status_code == 200
    r2 = client.post("/api/tts", json={"text": VOICE_PREVIEW_TEXT, "voice": "PrevVoice", "speed": 1.0})
    assert r2.status_code == 200
    assert _rec.last_voice == "PrevVoice"
    assert _rec.last_text == VOICE_PREVIEW_TEXT


def test_preview_unknown_voice_returns_400_not_crash():
    r = client.post("/api/tts", json={"text": VOICE_PREVIEW_TEXT, "voice": "no_such_voice", "speed": 1.0})
    assert r.status_code == 400


def test_preview_response_is_wav_audio():
    r = client.post("/api/tts", json={"text": VOICE_PREVIEW_TEXT, "voice": "default", "speed": 1.0})
    assert r.status_code == 200
    assert r.content[:4] == b"RIFF"