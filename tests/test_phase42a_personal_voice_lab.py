import hashlib
import io
import shutil
import subprocess

import numpy as np
import soundfile as sf

from backend import main as main_mod
from backend.app.personal_voice_lab import PersonalVoiceStore


def _wav_bytes(duration=35.0, sample_rate=16_000):
    t = np.arange(int(duration * sample_rate), dtype=np.float32) / sample_rate
    # Natural gaps give the segmentation heuristic boundaries to prefer.
    wave = 0.08 * np.sin(2 * np.pi * 180 * t)
    wave[(t % 5.0) > 4.6] = 0
    buffer = io.BytesIO()
    sf.write(buffer, wave, sample_rate, format="WAV", subtype="PCM_16")
    return buffer.getvalue()


def _encoded_phone_bytes(tmp_path, extension):
    if not shutil.which("ffmpeg"):
        import pytest
        pytest.skip("FFmpeg unavailable")
    source = tmp_path / "source.wav"
    source.write_bytes(_wav_bytes())
    destination = tmp_path / f"phone{extension}"
    proc = subprocess.run(
        ["ffmpeg", "-hide_banner", "-loglevel", "error", "-y", "-i", source, "-c:a", "aac", destination],
        capture_output=True,
    )
    assert proc.returncode == 0
    return destination.read_bytes()


class DummyCloneEngine:
    model_name = "dummy"
    device = "cpu"

    def get_voices(self):
        return ["default"]

    def generate(self, text, voice=None, speed=1.0, out_path=None, **kwargs):
        sf.write(out_path, np.zeros(4800, dtype=np.float32), 48_000)
        return out_path


def test_source_is_preserved_and_segment_is_engine_safe(tmp_path):
    payload = _wav_bytes()
    store = PersonalVoiceStore(tmp_path)
    source = store.save_source("phone take.wav", payload)

    assert source["original_sha256"] == hashlib.sha256(payload).hexdigest()
    assert source["normalized"]["sample_rate"] == 48_000
    assert source["normalized"]["channels"] == 1
    assert source["processing"]["normalization"] is False
    assert source["segment_suggestions"]

    suggestion = source["segment_suggestions"][0]
    segment = store.create_segment(
        source["id"], suggestion["start_seconds"], suggestion["end_seconds"], "Reference A"
    )
    assert 3 <= segment["duration_seconds"] <= 8
    assert segment["engine_compatibility"]["vieneu_3_3_0"] is True


def test_phone_m4a_is_preserved_and_decoded_locally(tmp_path):
    payload = _encoded_phone_bytes(tmp_path, ".m4a")
    store = PersonalVoiceStore(tmp_path / "store")
    source = store.save_source("personal_voice_take_01.m4a", payload)
    assert source["source"]["codec"] == "aac"
    assert source["original_sha256"] == hashlib.sha256(payload).hexdigest()
    assert source["normalized"]["sample_rate"] == 48_000


def test_api_upload_extract_and_controlled_candidate(tmp_path, monkeypatch):
    monkeypatch.setattr(main_mod, "_PERSONAL_VOICE_ROOT", tmp_path)
    monkeypatch.setattr(main_mod, "_PERSONAL_VOICE_STORE", PersonalVoiceStore(tmp_path))
    # The API loads the immutable controlled corpus from the experiment folder.
    test_set = (
        main_mod.Path("experiments/personal_voice_phase42a/test_set.json")
        .read_text(encoding="utf-8")
    )
    (tmp_path / "test_set.json").write_text(test_set, encoding="utf-8")
    source = main_mod._PERSONAL_VOICE_STORE.save_source("personal_take.wav", _wav_bytes())
    suggestion = source["segment_suggestions"][0]
    segment = main_mod.create_personal_voice_segment(
        source["id"],
        main_mod.PersonalVoiceSegmentRequest(
            start_seconds=suggestion["start_seconds"],
            end_seconds=suggestion["end_seconds"],
            label="Reference A",
        ),
    )
    candidate = main_mod.create_personal_voice_candidate(
        main_mod.PersonalVoiceCandidateRequest(
            source_id=source["id"], segment_id=segment["id"],
            engine_id="vieneu_3_3_0", test_id="test1_short",
        ),
        engine=DummyCloneEngine(),
    )
    assert (tmp_path / "outputs" / f"{candidate['id']}.wav").exists()


def test_api_exposes_only_installed_engine_as_available(tmp_path, monkeypatch):
    monkeypatch.setattr(main_mod, "_PERSONAL_VOICE_ROOT", tmp_path)
    (tmp_path / "test_set.json").write_text(
        main_mod.Path("experiments/personal_voice_phase42a/test_set.json").read_text(encoding="utf-8"),
        encoding="utf-8",
    )
    engines = main_mod.personal_voice_config()["engines"]
    assert [item["id"] for item in engines if item["available"]] == ["vieneu_3_3_0"]
    assert next(item for item in engines if item["id"] == "v_tts")["research_only"] is True


def test_personal_voice_ui_removed_while_voice_lab_remains():
    html = main_mod.Path("frontend/index.html").read_text(encoding="utf-8")
    js = main_mod.Path("frontend/app.js").read_text(encoding="utf-8")
    assert 'id="personalVoice' not in html
    assert "/api/personal-voice/" not in js
    assert "loadPersonalVoiceConfig" not in js
    assert 'id="voiceLab"' in html
    assert "loadVoiceLab()" in js
