import io
import os
import tempfile
import time
import soundfile as sf
from fastapi.testclient import TestClient

from backend import main as main_mod


class DummyEngineFail:
    def __init__(self):
        self.model_name = "dummy-model"
        self.device = "cpu"

    def get_voices(self):
        return ["default"]

    def generate(self, text, voice=None, speed=1.0, out_path=None, **kwargs):
        # simulate failure during generation
        raise RuntimeError("simulated generation error")


class DummyEngineOK:
    def __init__(self):
        self.model_name = "dummy-model"
        self.device = "cpu"

    def get_voices(self):
        return ["default"]

    def generate(self, text, voice=None, speed=1.0, out_path=None, **kwargs):
        sr = 22050
        t = [0.0]
        data = [0.0]
        sf.write(out_path, [0.0], sr)
        return out_path


client = TestClient(main_mod.app)


def _wav_temp_files():
    d = tempfile.gettempdir()
    return [p for p in os.listdir(d) if p.lower().endswith('.wav')]


def make_wav_bytes(duration_s=0.5, sr=22050):
    import numpy as np
    t = np.linspace(0, duration_s, int(sr * duration_s), False)
    data = 0.05 * np.sin(2 * np.pi * 440 * t).astype(np.float32)
    bio = io.BytesIO()
    sf.write(bio, data, sr, format='WAV')
    bio.seek(0)
    return bio.read()


def test_clone_tempfile_cleanup_on_exception():
    # override engine to failing one
    main_mod.app.dependency_overrides[main_mod.get_engine] = lambda: DummyEngineFail()
    before = set(_wav_temp_files())
    wav = make_wav_bytes(duration_s=0.5)
    files = {'ref_audio': ('ref.wav', wav, 'audio/wav')}
    params = {'text': 'Hello clone', 'voice': 'default', 'speed': '1.0'}
    r = client.post('/api/tts/clone', params=params, files=files)
    assert r.status_code == 500
    # wait briefly for any cleanup tasks
    time.sleep(0.1)
    after = set(_wav_temp_files())
    # ensure no new wav files remain in temp dir
    assert after.issubset(before)
    main_mod.app.dependency_overrides.clear()


def test_clone_tempfile_cleanup_on_success():
    main_mod.app.dependency_overrides[main_mod.get_engine] = lambda: DummyEngineOK()
    before = set(_wav_temp_files())
    wav = make_wav_bytes(duration_s=0.5)
    files = {'ref_audio': ('ref.wav', wav, 'audio/wav')}
    params = {'text': 'Hello clone', 'voice': 'default', 'speed': '1.0'}
    r = client.post('/api/tts/clone', data=params, files=files)
    assert r.status_code == 200
    time.sleep(0.1)
    after = set(_wav_temp_files())
    assert after.issubset(before)
    main_mod.app.dependency_overrides.clear()
