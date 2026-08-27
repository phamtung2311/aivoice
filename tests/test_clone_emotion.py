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
        # create a short 0.05s sine wave wav to emulate generation
        sr = 22050
        t = np.linspace(0, 0.05, int(sr * 0.05), False)
        data = 0.05 * np.sin(2 * np.pi * 440 * t).astype(np.float32)
        sf.write(out_path, data, sr)
        return out_path


def make_wav_bytes(duration_s=0.5, sr=22050):
    t = np.linspace(0, duration_s, int(sr * duration_s), False)
    data = 0.05 * np.sin(2 * np.pi * 440 * t).astype(np.float32)
    bio = io.BytesIO()
    sf.write(bio, data, sr, format='WAV')
    bio.seek(0)
    return bio.read()


def setup_module(module):
    main_mod.app.dependency_overrides[main_mod.get_engine] = lambda: DummyEngine()


def teardown_module(module):
    main_mod.app.dependency_overrides.clear()


client = TestClient(main_mod.app)


def test_clone_success():
    wav = make_wav_bytes(duration_s=0.5)
    files = {
        'ref_audio': ('ref.wav', wav, 'audio/wav')
    }
    params = {'text': 'Hello clone', 'voice': 'default', 'speed': '1.0'}
    r = client.post('/api/tts/clone', data=params, files=files)
    assert r.status_code == 200
    assert r.headers.get('content-type', '').startswith('audio/')
    assert len(r.content) > 100


def test_clone_missing_file():
    params = {'text': 'Hello clone', 'voice': 'default'}
    r = client.post('/api/tts/clone', data=params)
    assert r.status_code == 400


def test_clone_invalid_extension():
    # send non-wav file
    files = {'ref_audio': ('ref.mp3', b'notawav', 'audio/mpeg')}
    params = {'text': 'Hello clone'}
    r = client.post('/api/tts/clone', data=params, files=files)
    assert r.status_code == 400


def test_clone_too_long_duration():
    # create a >10s wav (11s)
    wav = make_wav_bytes(duration_s=11.0)
    files = {'ref_audio': ('long.wav', wav, 'audio/wav')}
    params = {'text': 'Hello clone'}
    r = client.post('/api/tts/clone', data=params, files=files)
    assert r.status_code == 413


def test_clone_emotion_unknown():
    wav = make_wav_bytes(duration_s=0.3)
    files = {'ref_audio': ('ref.wav', wav, 'audio/wav')}
    params = {'text': 'Hello clone', 'emotion': 'angry'}
    r = client.post('/api/tts/clone', data=params, files=files)
    assert r.status_code == 422


def test_clone_emotion_known():
    wav = make_wav_bytes(duration_s=0.3)
    files = {'ref_audio': ('ref.wav', wav, 'audio/wav')}
    params = {'text': 'Hello clone', 'emotion': 'natural'}
    r = client.post('/api/tts/clone', data=params, files=files)
    assert r.status_code == 200
    assert r.headers.get('content-type', '').startswith('audio/')
