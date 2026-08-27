"""Phase 23 regression coverage: reference DSP and metadata-only history."""

import io
import json
import asyncio

import numpy as np
import pytest
import soundfile as sf
from backend.app import voice_lab
from backend.main import analyze_voice_lab_reference
from backend.app.tts.reference_quality import analyze_clip, quality_score


def wav_bytes(data, sample_rate=16000):
    buffer = io.BytesIO()
    sf.write(buffer, data, sample_rate, format="WAV", subtype="FLOAT")
    return buffer.getvalue()


def tone(seconds=6.0, sample_rate=16000, amplitude=0.2):
    t = np.arange(int(seconds * sample_rate), dtype=np.float32) / sample_rate
    return amplitude * np.sin(2 * np.pi * 220 * t)


def test_score_is_bounded_and_quality_score_matches_analysis():
    analysis = analyze_clip(wav_bytes(tone()))
    assert 0 <= analysis.score <= 100
    assert quality_score(analysis) == analysis.score


def test_mono_and_stereo_metrics_are_reported():
    mono = analyze_clip(wav_bytes(tone()))
    stereo = analyze_clip(wav_bytes(np.column_stack((tone(), tone()))))
    assert mono.metrics["channels"] == 1
    assert mono.metrics["mono"] is True
    assert stereo.metrics["channels"] == 2
    assert stereo.metrics["mono"] is False


def test_noise_clipping_silence_and_duration_are_detected():
    clean = analyze_clip(wav_bytes(tone(seconds=6)))
    noisy = analyze_clip(wav_bytes(tone(seconds=6) + np.random.default_rng(4).normal(0, 0.04, 96000).astype(np.float32)))
    clipped = analyze_clip(wav_bytes(np.full(96000, 1.0, dtype=np.float32)))
    quiet = analyze_clip(wav_bytes(np.concatenate((np.zeros(16000, dtype=np.float32), tone(seconds=4), np.zeros(16000, dtype=np.float32)))))
    short = analyze_clip(wav_bytes(tone(seconds=2)))
    assert noisy.metrics["noise_estimate"] > clean.metrics["noise_estimate"]
    assert clipped.metrics["clipping"]["ratio"] > 0.99
    assert quiet.metrics["leading_silence"] >= 0.99
    assert quiet.metrics["ending_silence"] >= 0.99
    assert short.metrics["duration_seconds"] == pytest.approx(2.0, abs=0.01)


def test_history_is_metadata_only_and_preferred_is_explicit(tmp_path):
    target = tmp_path / "reference_history.json"
    report = {"quality_score": 92, "bars": {"noise": 0.9}}
    entry = voice_lab.ReferenceHistoryEntry(
        id="reference_b",
        filename="speaker.wav",
        duration=6.0,
        score=92,
        sample_rate=16000,
        quality_report=report,
    )
    voice_lab.save_reference_analysis(entry, path=target)
    saved = voice_lab.set_reference_preferred("reference_b", path=target)
    history = voice_lab.load_reference_history(path=target)
    raw = target.read_text(encoding="utf-8")
    assert saved["preferred"] is True
    assert history[0]["filename"] == "speaker.wav"
    assert history[0]["quality_report"] == report
    assert "audio" not in json.dumps(history).lower()
    assert "speaker.wav" in raw


def test_analyze_api_returns_contract_and_only_metadata_history(tmp_path, monkeypatch):
    monkeypatch.setenv("VOICE_LAB_DIR", str(tmp_path))
    class InMemoryUpload:
        filename = "speaker.wav"

        async def read(self, _limit):
            return wav_bytes(tone())

    payload = asyncio.run(analyze_voice_lab_reference(InMemoryUpload(), "reference_a"))
    assert {"duration", "sample_rate", "channels", "peak", "rms", "noise", "silence_ratio", "leading_silence", "ending_silence", "quality_score", "strengths", "weaknesses", "tips", "recommended"} <= set(payload)
    assert not list(tmp_path.glob("*.wav"))
    assert voice_lab.load_reference_history()[0]["filename"] == "speaker.wav"
