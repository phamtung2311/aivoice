"""Phase 14 — multi-format reference audio tests for /api/tts/clone.

WAV/MP3 are created with soundfile (libsndfile has native MP3 support).
M4A samples require FFmpeg; those tests are skipped when FFmpeg is absent
(the runtime machine has it installed at /usr/bin/ffmpeg).
"""
import io
import os
import shutil
import tempfile

import numpy as np
import pytest
import soundfile as sf
from fastapi.testclient import TestClient

from backend import main as main_mod


class DummyCloneEngine:
    def __init__(self):
        self.model_name = "dummy-model"
        self.device = "cpu"

    def get_voices(self):
        return ["default"]

    def generate(self, text, voice=None, speed=1.0, out_path=None, **kwargs):
        sr = 22050
        t = np.linspace(0, 0.05, int(sr * 0.05), False)
        data = 0.05 * np.sin(2 * np.pi * 440 * t).astype(np.float32)
        sf.write(out_path, data, sr)
        return out_path


def _wav_bytes(duration_s=1.0, sr=22050):
    t = np.linspace(0, duration_s, int(sr * duration_s), False)
    data = 0.05 * np.sin(2 * np.pi * 440 * t).astype(np.float32)
    bio = io.BytesIO()
    sf.write(bio, data, sr, format="WAV")
    bio.seek(0)
    return bio.read()


def _mp3_bytes(duration_s=1.0, sr=22050):
    t = np.linspace(0, duration_s, int(sr * duration_s), False)
    data = 0.05 * np.sin(2 * np.pi * 440 * t).astype(np.float32)
    bio = io.BytesIO()
    sf.write(bio, data, sr, format="MP3")
    bio.seek(0)
    return bio.read()


def _m4a_bytes(duration_s=1.0):
    """Encode a tiny M4A via the system FFmpeg binary."""
    if not shutil.which("ffmpeg"):
        pytest.skip("FFmpeg not available")
    fd, wav_path = tempfile.mkstemp(suffix=".wav")
    os.close(fd)
    t = np.linspace(0, duration_s, int(22050 * duration_s), False)
    data = 0.05 * np.sin(2 * np.pi * 440 * t).astype(np.float32)
    sf.write(wav_path, data, 22050)
    fd2, m4a_path = tempfile.mkstemp(suffix=".m4a")
    os.close(fd2)
    import subprocess
    proc = subprocess.run(
        ["ffmpeg", "-y", "-i", wav_path, "-c:a", "aac", m4a_path],
        capture_output=True, text=True,
    )
    try:
        os.remove(wav_path)
    except Exception:
        pass
    if proc.returncode != 0:
        pytest.skip("FFmpeg failed to encode test M4A")
    with open(m4a_path, "rb") as f:
        payload = f.read()
    try:
        os.remove(m4a_path)
    except Exception:
        pass
    return payload


def setup_module(module):
    main_mod.app.dependency_overrides[main_mod.get_engine] = lambda: DummyCloneEngine()


def teardown_module(module):
    main_mod.app.dependency_overrides.clear()


client = TestClient(main_mod.app)


def test_clone_accepts_wav():
    files = {"ref_audio": ("ref.wav", _wav_bytes(), "audio/wav")}
    r = client.post("/api/tts/clone", data={"text": "Xin chào"}, files=files)
    assert r.status_code == 200
    assert r.headers.get("content-type", "").startswith("audio/")


def test_clone_accepts_mp3():
    files = {"ref_audio": ("ref.mp3", _mp3_bytes(), "audio/mpeg")}
    r = client.post("/api/tts/clone", data={"text": "Xin chào"}, files=files)
    assert r.status_code == 200
    assert r.headers.get("content-type", "").startswith("audio/")


def test_clone_accepts_m4a():
    files = {"ref_audio": ("ref.m4a", _m4a_bytes(), "audio/mp4")}
    r = client.post("/api/tts/clone", data={"text": "Xin chào"}, files=files)
    assert r.status_code == 200
    assert r.headers.get("content-type", "").startswith("audio/")


def test_clone_rejects_unsupported_extension():
    files = {"ref_audio": ("ref.ogg", b"OggS-not-really", "application/ogg")}
    r = client.post("/api/tts/clone", data={"text": "Xin chào"}, files=files)
    assert r.status_code == 400
    assert "WAV" in r.json()["detail"] or "MP3" in r.json()["detail"] or "M4A" in r.json()["detail"]


def test_clone_rejects_corrupt_mp3():
    files = {"ref_audio": ("broken.mp3", b"\x00\x01\x02not-an-audio-stream\xff\xff", "audio/mpeg")}
    r = client.post("/api/tts/clone", data={"text": "Xin chào"}, files=files)
    assert r.status_code in (400, 500)


def test_clone_fake_extension_does_not_crash():
    # Real WAV bytes disguised as .mp3: libsndfile sniffs by content when
    # reading, so this may succeed OR fail cleanly — the contract is that the
    # server never crashes and always returns a controlled status.
    files = {"ref_audio": ("fake.mp3", _wav_bytes(), "audio/mpeg")}
    r = client.post("/api/tts/clone", data={"text": "Xin chào"}, files=files)
    assert r.status_code in (200, 400, 500)


def test_clone_rejects_corrupt_m4a():
    files = {"ref_audio": ("broken.m4a", b"\x00\x00\x00\x20ftypgarbage-not-audio", "audio/mp4")}
    r = client.post("/api/tts/clone", data={"text": "Xin chào"}, files=files)
    assert r.status_code in (400, 500)


def test_clone_rejects_too_long_mp3():
    files = {"ref_audio": ("long.mp3", _mp3_bytes(duration_s=11.0), "audio/mpeg")}
    r = client.post("/api/tts/clone", data={"text": "Xin chào"}, files=files)
    assert r.status_code == 413


def test_clone_temp_files_cleaned_up_after_success():
    tmpdir = tempfile.gettempdir()
    def conv_count():
        return len([p for p in os.listdir(tmpdir) if p.startswith("clone_conv_")])
    before = conv_count()
    files = {"ref_audio": ("ref.mp3", _mp3_bytes(), "audio/mpeg")}
    r = client.post("/api/tts/clone", data={"text": "Xin chào"}, files=files)
    assert r.status_code == 200
    assert conv_count() <= before


def test_clone_temp_files_cleaned_up_after_conversion_failure():
    tmpdir = tempfile.gettempdir()
    def conv_count():
        return len([p for p in os.listdir(tmpdir) if p.startswith("clone_conv_")])
    before = conv_count()
    files = {"ref_audio": ("broken.m4a", b"garbage-m4a-payload", "audio/mp4")}
    r = client.post("/api/tts/clone", data={"text": "Xin chào"}, files=files)
    assert r.status_code in (400, 500)
    assert conv_count() <= before