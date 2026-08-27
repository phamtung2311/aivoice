import io
import os
import numpy as np
import soundfile as sf
from fastapi.testclient import TestClient

from backend import main as main_mod


class DummyEngine:
    def __init__(self):
        self.model_name = "dummy-model"
        self.device = "cpu"

    def get_voices(self):
        return ["default"]

    def generate(self, text, voice=None, speed=1.0, out_path=None, **kwargs):
        # create a short 0.1s sine wave wav
        sr = 22050
        t = np.linspace(0, 0.1, int(sr * 0.1), False)
        data = 0.1 * np.sin(2 * np.pi * 440 * t).astype(np.float32)
        # write to out_path
        sf.write(out_path, data, sr)
        return out_path


def setup_module(module):
    # override engine dependency
    main_mod.app.dependency_overrides[main_mod.get_engine] = lambda: DummyEngine()


def teardown_module(module):
    main_mod.app.dependency_overrides.clear()


client = TestClient(main_mod.app)


def test_health():
    r = client.get("/api/health")
    assert r.status_code == 200
    j = r.json()
    assert j["status"] == "ok"
    assert j["engine"] == "local"


def test_voices():
    r = client.get("/api/voices")
    assert r.status_code == 200
    j = r.json()
    assert "voices" in j
    assert any(v["id"] == "default" for v in j["voices"])


def test_tts_success():
    payload = {"text": "Xin chào", "voice": "default", "speed": 1.0}
    r = client.post("/api/tts", json=payload)
    assert r.status_code == 200
    assert r.headers.get("content-type", "").startswith("audio/")
    data = r.content
    assert len(data) > 100


def test_tts_invalid():
    payload = {"text": "   ", "voice": "default", "speed": 1.0}
    r = client.post("/api/tts", json=payload)
    assert r.status_code == 400


def test_tts_upload():
    files = {"file": ("test.txt", b"Xin chao tu file", "text/plain")}
    r = client.post("/api/tts/upload", files=files)
    assert r.status_code == 200
    assert r.headers.get("content-type", "").startswith("audio/")
