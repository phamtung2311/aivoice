"""Phase 12.1 — voice profile API tests (mock engine only, no real model inference)."""
import io

import numpy as np
import soundfile as sf
from fastapi.testclient import TestClient

from backend import main as main_mod


class DummyVoiceEngine:
    """Simulates the ModelLoader voice-profile contract for API tests."""

    def __init__(self):
        self.model_name = "dummy-model"
        self.device = "cpu"
        self._preset = ["thu_minh", "huong", "default"]
        self._user = {}  # name -> {}
        self.last_text = None

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
        sr = 22050
        t = np.linspace(0, 0.1, int(sr * 0.1), False)
        data = 0.1 * np.sin(2 * np.pi * 440 * t).astype(np.float32)
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
    module._engine = DummyVoiceEngine()
    main_mod.app.dependency_overrides[main_mod.get_engine] = lambda: module._engine


def teardown_module(module):
    main_mod.app.dependency_overrides.clear()


client = TestClient(main_mod.app)


def test_list_preset_voices():
    r = client.get("/api/voices")
    assert r.status_code == 200
    j = r.json()
    voices = j["voices"]
    preset_ids = [v["id"] for v in voices if v.get("type") == "preset"]
    assert "thu_minh" in preset_ids
    assert "default" in preset_ids


def test_save_valid_voice_listed_as_saved():
    files = {"ref_audio": ("ref.wav", _wav_bytes(), "audio/wav")}
    r = client.post("/api/voices/save", data={"name": "My Voice"}, files=files)
    assert r.status_code == 200, r.text
    assert r.json()["voice"]["type"] == "saved"
    r2 = client.get("/api/voices")
    saved_ids = [v["id"] for v in r2.json()["voices"] if v.get("type") == "saved"]
    assert "My Voice" in saved_ids


def test_list_saved_voices():
    r = client.get("/api/voices")
    assert r.status_code == 200
    assert any(v.get("type") == "saved" for v in r.json()["voices"])


def test_reject_invalid_voice_name():
    files = {"ref_audio": ("ref.wav", _wav_bytes(), "audio/wav")}
    for bad in ("", "a/b", "a\\b", "  "):
        r = client.post("/api/voices/save", data={"name": bad}, files=files)
        assert r.status_code == 400, (bad, r.text)


def test_reject_duplicate_voice():
    files = {"ref_audio": ("ref.wav", _wav_bytes(), "audio/wav")}
    r = client.post("/api/voices/save", data={"name": "My Voice"}, files=files)
    assert r.status_code == 409, r.text


def test_delete_saved_voice():
    files = {"ref_audio": ("ref.wav", _wav_bytes(), "audio/wav")}
    r = client.post("/api/voices/save", data={"name": "Temp Voice"}, files=files)
    assert r.status_code == 200
    r2 = client.delete("/api/voices/Temp Voice")
    assert r2.status_code == 200
    r3 = client.get("/api/voices")
    saved_ids = [v["id"] for v in r3.json()["voices"] if v.get("type") == "saved"]
def test_saved_voice_can_be_selected_for_tts():
    files = {"ref_audio": ("ref.wav", _wav_bytes(), "audio/wav")}
    r = client.post("/api/voices/save", data={"name": "Story Voice"}, files=files)
    assert r.status_code == 200
    r2 = client.post("/api/tts", json={"text": "Xin chào", "voice": "Story Voice", "speed": 1.0})
    assert r2.status_code == 200
    assert r2.headers.get("content-type", "").startswith("audio/")


def test_failed_save_does_not_leave_corrupt_profile():
    class FailingEngine(DummyVoiceEngine):
        def add_saved_voice(self, name, ref_audio):
            raise RuntimeError("boom")

    main_mod.app.dependency_overrides[main_mod.get_engine] = lambda: FailingEngine()
    try:
        files = {"ref_audio": ("ref.wav", _wav_bytes(), "audio/wav")}
        r = client.post("/api/voices/save", data={"name": "Broken"}, files=files)
        assert r.status_code == 500
    finally:
        main_mod.app.dependency_overrides[main_mod.get_engine] = lambda: _engine


def test_voice_store_persistence_roundtrip(tmp_path):
    from backend.app.tts import voice_store

    profiles = {"P1": {"description": "", "speaker_emb": [0.1, 0.2], "codes": [[1, 2], [3, 4]]}}
    path = tmp_path / "sub" / "voices.json"
    voice_store.save_user_voices(profiles, path)
    loaded = voice_store.load_user_voices(path)
    assert loaded["P1"]["speaker_emb"] == [0.1, 0.2]
    # corrupt file -> graceful empty
    path.write_text("{not json")
    assert voice_store.load_user_voices(path) == {}


def test_voice_name_validation_utility():
    from backend.app.tts import voice_store

    assert voice_store.validate_voice_name("  My Voice  ") == "My Voice"
    for bad in ("", "   ", "a/b", "a\\b", "a" * 65, "a\x00b"):
        try:
            voice_store.validate_voice_name(bad)
            assert False, bad
        except ValueError:
            pass



def test_cannot_delete_preset_voice():
    r = client.delete("/api/voices/thu_minh")
    assert r.status_code == 403
    r2 = client.get("/api/voices")
    preset_ids = [v["id"] for v in r2.json()["voices"] if v.get("type") == "preset"]
    assert "thu_minh" in preset_ids