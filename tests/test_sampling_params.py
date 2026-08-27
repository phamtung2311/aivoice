import io
import os
import numpy as np
import soundfile as sf
from fastapi.testclient import TestClient

from backend import main as main_mod


class RecordingEngine:
    def __init__(self):
        self.model_name = "dummy-model"
        self.device = "cpu"
        self.last_generate_args = None
        self.last_generate_kwargs = None

    def get_voices(self):
        return ["default"]

    def generate(self, *args, **kwargs):
        # record call
        self.last_generate_args = args
        self.last_generate_kwargs = kwargs
        # create a short 0.05s sine wave wav to emulate generation
        sr = 22050
        t = np.linspace(0, 0.05, int(sr * 0.05), False)
        data = 0.05 * np.sin(2 * np.pi * 440 * t).astype(np.float32)
        out_path = kwargs.get('out_path') or ("out_test.wav")
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
    module._rec = RecordingEngine()
    main_mod.app.dependency_overrides[main_mod.get_engine] = lambda: module._rec


def teardown_module(module):
    main_mod.app.dependency_overrides.clear()


client = TestClient(main_mod.app)


def test_tts_no_sampling_keeps_defaults():
    payload = {"text": "Xin chào", "voice": "default", "speed": 1.0}
    r = client.post("/api/tts", json=payload)
    assert r.status_code == 200
    # engine should have been called and sampling keys may be present but None
    assert hasattr(_rec, 'last_generate_kwargs') and _rec.last_generate_kwargs is not None
    # ensure voice and speed forwarded
    assert _rec.last_generate_kwargs.get('voice') == 'default'
    assert _rec.last_generate_kwargs.get('speed') == 1.0


def test_tts_forward_temperature():
    payload = {"text": "Xin chào", "voice": "default", "speed": 1.0, "temperature": 1.2}
    r = client.post("/api/tts", json=payload)
    assert r.status_code == 200
    assert _rec.last_generate_kwargs.get('temperature') == 1.2


def test_tts_forward_top_k():
    payload = {"text": "Hello", "top_k": 50}
    r = client.post("/api/tts", json=payload)
    assert r.status_code == 200
    assert _rec.last_generate_kwargs.get('top_k') == 50


def test_tts_forward_top_p():
    payload = {"text": "Hello", "top_p": 0.8}
    r = client.post("/api/tts", json=payload)
    assert r.status_code == 200
    assert abs(_rec.last_generate_kwargs.get('top_p') - 0.8) < 1e-6


def test_tts_forward_repetition_penalty():
    payload = {"text": "Hello", "repetition_penalty": 1.5}
    r = client.post("/api/tts", json=payload)
    assert r.status_code == 200
    assert abs(_rec.last_generate_kwargs.get('repetition_penalty') - 1.5) < 1e-6


def test_tts_invalid_out_of_range():
    payload = {"text": "Hello", "temperature": 0.01}
    r = client.post("/api/tts", json=payload)
    assert r.status_code == 422


def test_clone_accepts_sampling_and_ref_audio():
    wav = make_wav_bytes(duration_s=0.5)
    files = { 'ref_audio': ('ref.wav', wav, 'audio/wav') }
    params = {'text': 'Hello clone', 'voice': 'default', 'speed': '1.0', 'temperature': '1.1', 'top_k': '30', 'top_p': '0.9', 'repetition_penalty': '1.3'}
    r = client.post('/api/tts/clone', data=params, files=files)
    assert r.status_code == 200
    # recording engine should have sampling kwargs forwarded
    assert float(_rec.last_generate_kwargs.get('temperature')) == 1.1
    assert int(_rec.last_generate_kwargs.get('top_k')) == 30
    assert abs(float(_rec.last_generate_kwargs.get('top_p')) - 0.9) < 1e-6
    assert abs(float(_rec.last_generate_kwargs.get('repetition_penalty')) - 1.3) < 1e-6


def test_clone_rejects_out_of_range_sampling():
    wav = make_wav_bytes(duration_s=0.5)
    files = {'ref_audio': ('ref.wav', wav, 'audio/wav')}
    params = {'text': 'Hello clone', 'temperature': '0.01'}
    r = client.post('/api/tts/clone', data=params, files=files)
    assert r.status_code == 422


def test_clone_accepts_legacy_query_params():
    wav = make_wav_bytes(duration_s=0.5)
    files = {'ref_audio': ('ref.wav', wav, 'audio/wav')}
    params = {
        'text': 'Legacy clone',
        'voice': 'default',
        'speed': '1.2',
        'emotion': 'natural',
        'temperature': '1.1',
        'top_k': '30',
        'top_p': '0.9',
        'repetition_penalty': '1.3',
    }
    r = client.post('/api/tts/clone', params=params, files=files)
    assert r.status_code == 200
    assert _rec.last_generate_args[0] == 'Legacy clone'
    assert _rec.last_generate_kwargs.get('speed') == 1.2
    assert _rec.last_generate_kwargs.get('emotion_tag') == '<|emotion_0|>'
    assert _rec.last_generate_kwargs.get('temperature') == 1.1
    assert _rec.last_generate_kwargs.get('top_k') == 30
    assert _rec.last_generate_kwargs.get('top_p') == 0.9
    assert _rec.last_generate_kwargs.get('repetition_penalty') == 1.3


def test_clone_rejects_out_of_range_legacy_sampling():
    wav = make_wav_bytes(duration_s=0.5)
    files = {'ref_audio': ('ref.wav', wav, 'audio/wav')}
    params = {'text': 'Legacy clone', 'temperature': '0.01'}
    r = client.post('/api/tts/clone', params=params, files=files)
    assert r.status_code == 422


def test_clone_form_values_take_precedence_over_query():
    wav = make_wav_bytes(duration_s=0.5)
    files = {'ref_audio': ('ref.wav', wav, 'audio/wav')}
    query = {'text': 'Query text', 'speed': '1.4', 'temperature': '1.1', 'top_k': '40'}
    form = {'text': 'Form text', 'speed': '0.9', 'temperature': '0.7'}
    r = client.post('/api/tts/clone', params=query, data=form, files=files)
    assert r.status_code == 200
    assert _rec.last_generate_args[0] == 'Form text'
    assert _rec.last_generate_kwargs.get('speed') == 0.9
    assert _rec.last_generate_kwargs.get('temperature') == 0.7
    assert _rec.last_generate_kwargs.get('top_k') == 40
