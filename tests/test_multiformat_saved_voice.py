"""Phase 19.3 multi-format saved-voice enrollment tests (no real model)."""

import io
import asyncio
import inspect
import os
import shutil
import subprocess
import tempfile

import numpy as np
import pytest
import soundfile as sf
from fastapi import HTTPException, UploadFile

from backend import main as main_mod
from backend.app.tts import voice_store
from backend.app.tts.engine import TTSEngine


def wav_bytes(duration_s=0.5, sample_rate=22050):
    timeline = np.linspace(0, duration_s, int(sample_rate * duration_s), False)
    audio = 0.05 * np.sin(2 * np.pi * 440 * timeline).astype(np.float32)
    output = io.BytesIO()
    sf.write(output, audio, sample_rate, format="WAV")
    return output.getvalue()


def mp3_bytes(duration_s=0.5, sample_rate=22050):
    timeline = np.linspace(0, duration_s, int(sample_rate * duration_s), False)
    audio = 0.05 * np.sin(2 * np.pi * 440 * timeline).astype(np.float32)
    output = io.BytesIO()
    sf.write(output, audio, sample_rate, format="MP3")
    return output.getvalue()


def m4a_bytes(duration_s=0.5):
    if not shutil.which("ffmpeg"):
        pytest.skip("FFmpeg not available")
    wav_fd, wav_path = tempfile.mkstemp(suffix=".wav")
    os.close(wav_fd)
    m4a_fd, m4a_path = tempfile.mkstemp(suffix=".m4a")
    os.close(m4a_fd)
    try:
        sf.write(wav_path, np.zeros(int(22050 * duration_s), dtype=np.float32), 22050)
        result = subprocess.run(
            ["ffmpeg", "-y", "-i", wav_path, "-c:a", "aac", m4a_path],
            capture_output=True,
            text=True,
            timeout=30,
        )
        if result.returncode != 0:
            pytest.skip("FFmpeg could not create M4A fixture")
        with open(m4a_path, "rb") as source:
            return source.read()
    finally:
        for path in (wav_path, m4a_path):
            try:
                os.remove(path)
            except OSError:
                pass


class RecordingSavedVoiceEngine:
    model_name = "dummy"
    device = "cpu"

    def __init__(self):
        self.saved = set()
        self.enrollments = []

    def get_voices(self):
        return ["Adam", *sorted(self.saved)]

    def add_saved_voice(self, name, ref_audio, description=""):
        info = sf.info(ref_audio)
        assert ref_audio.endswith(".wav")
        assert info.frames > 0
        self.enrollments.append({
            "name": name,
            "was_wav": True,
            "existed_during_enrollment": os.path.exists(ref_audio),
            "description": description,
        })
        self.saved.add(name)
        return name


def temp_reference_files():
    names = os.listdir(tempfile.gettempdir())
    return {name for name in names if name.startswith(("save_voice_ref_", "clone_conv_"))}


@pytest.fixture
def saved_voice_engine():
    engine = RecordingSavedVoiceEngine()
    yield engine


def save_voice(engine, name, filename, payload, description=""):
    upload_file = tempfile.SpooledTemporaryFile(max_size=main_mod.REF_MAX_BYTES + 1024)
    upload_file.write(payload)
    upload_file.seek(0)
    upload = UploadFile(file=upload_file, filename=filename)
    async def invoke_without_environment_executor_hang():
        loop = asyncio.get_running_loop()
        original = loop.run_in_executor

        def immediate(_executor, function, *args):
            future = loop.create_future()
            try:
                future.set_result(function(*args))
            except Exception as error:
                future.set_exception(error)
            return future

        loop.run_in_executor = immediate
        try:
            return await main_mod.save_voice(
                name=name,
                description=description,
                ref_audio=upload,
                engine=engine,
            )
        finally:
            loop.run_in_executor = original

    return asyncio.run(invoke_without_environment_executor_hang())


@pytest.mark.parametrize(
    ("filename", "content_type", "payload"),
    [
        ("reference.wav", "audio/wav", wav_bytes),
        ("reference.mp3", "audio/mpeg", mp3_bytes),
        ("reference.m4a", "audio/mp4", m4a_bytes),
    ],
)
def test_save_voice_accepts_wav_mp3_m4a_and_cleans_temps(saved_voice_engine, filename, content_type, payload):
    engine = saved_voice_engine
    before = temp_reference_files()
    name = f"Saved {filename}"
    response = save_voice(engine, name, filename, payload(), "local profile")
    assert response["voice"]["id"] == name
    assert engine.enrollments[-1]["was_wav"] is True
    assert engine.enrollments[-1]["existed_during_enrollment"] is True
    assert engine.enrollments[-1]["description"] == "local profile"
    assert temp_reference_files() <= before


def test_save_voice_rejects_invalid_format_before_enrollment(saved_voice_engine):
    engine = saved_voice_engine
    with pytest.raises(HTTPException) as exc:
        save_voice(engine, "Invalid", "reference.txt", b"not audio")
    assert exc.value.status_code == 400
    assert not engine.enrollments


def test_save_voice_rejects_oversize_and_long_audio_with_cleanup(saved_voice_engine):
    engine = saved_voice_engine
    before = temp_reference_files()
    with pytest.raises(HTTPException) as oversize:
        save_voice(engine, "Too Large", "large.wav", b"0" * (main_mod.REF_MAX_BYTES + 1))
    assert oversize.value.status_code == 413
    with pytest.raises(HTTPException) as too_long:
        save_voice(engine, "Too Long", "long.wav", wav_bytes(duration_s=8.1))
    assert too_long.value.status_code == 413
    assert temp_reference_files() <= before


def test_duplicate_rejected_before_decode_and_without_temp_files(saved_voice_engine):
    engine = saved_voice_engine
    engine.saved.add("Duplicate")
    before = temp_reference_files()
    with pytest.raises(HTTPException) as duplicate:
        save_voice(engine, "Duplicate", "broken.m4a", b"not an m4a")
    assert duplicate.value.status_code == 409
    assert not engine.enrollments
    assert temp_reference_files() <= before


def test_decode_and_engine_failures_clean_all_temp_files(saved_voice_engine):
    engine = saved_voice_engine
    before = temp_reference_files()
    with pytest.raises(HTTPException) as decode_error:
        save_voice(engine, "Decode Failure", "broken.m4a", b"not an m4a")
    assert decode_error.value.status_code == 400

    class FailingEngine(RecordingSavedVoiceEngine):
        def add_saved_voice(self, name, ref_audio, description=""):
            assert os.path.exists(ref_audio)
            raise RuntimeError("enrollment failed")

    with pytest.raises(HTTPException) as engine_error:
        save_voice(FailingEngine(), "Engine Failure", "reference.mp3", mp3_bytes())
    assert engine_error.value.status_code == 500
    assert temp_reference_files() <= before


def test_multiformat_enrollment_profile_survives_store_reload(tmp_path, monkeypatch):
    store_path = tmp_path / "voices.json"
    monkeypatch.setenv("VOICE_STORE_PATH", str(store_path))

    class PersistentEngine(RecordingSavedVoiceEngine):
        def add_saved_voice(self, name, ref_audio, description=""):
            super().add_saved_voice(name, ref_audio, description)
            voice_store.save_user_voices(
                {name: {"description": description, "speaker_emb": [0.1, 0.2], "codes": [[1, 2]]}}
            )
            return name

    engine = PersistentEngine()
    response = save_voice(engine, "Restart Voice", "reference.m4a", m4a_bytes())
    assert response["voice"]["id"] == "Restart Voice"
    restored = voice_store.load_user_voices()
    assert "Restart Voice" in restored
    assert restored["Restart Voice"]["speaker_emb"]
    assert restored["Restart Voice"]["codes"]


def test_engine_forwards_saved_voice_description():
    class RecordingModel:
        def add_saved_voice(self, name, ref_audio, description=""):
            self.call = (name, ref_audio, description)
            return name

    model = RecordingModel()
    engine = TTSEngine(cache_model=False)
    engine._model = model
    assert engine.add_saved_voice("Named", "reference.wav", description="Brand voice") == "Named"
    assert model.call == ("Named", "reference.wav", "Brand voice")


def test_clone_and_save_share_reference_conversion_helper():
    clone_source = inspect.getsource(main_mod.tts_clone)
    save_source = inspect.getsource(main_mod.save_voice)
    assert "_prepare_reference_wav" in clone_source
    assert "_prepare_reference_wav" in save_source
