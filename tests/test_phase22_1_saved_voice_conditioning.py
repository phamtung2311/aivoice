"""Phase 22.1 — saved-voice conditioning investigation tests.

Covers: profile serialization round-trip (dtype/shape/values, no biometric
values printed), Vieneu use_ref_codes plumbing through our engine, /api/tts
conditioning_mode diagnostics (saved-voice only), experiment persistence for
the conditioning round without identity arrays, production-call invariance,
and the frontend conditioning UI contract.
"""

from pathlib import Path

import numpy as np
import pytest
from fastapi import HTTPException

from backend.app.tts import voice_store
from backend.app.tts.engine import TTSEngine
from backend.app.voice_lab import (
    ExperimentCreate,
    ExperimentEvaluation,
    ListeningScores,
    create_experiment,
    evaluate_experiment,
    load_experiments,
)
from backend.main import TTSRequest, tts

APP = (Path("frontend") / "app.js").read_text(encoding="utf-8")
HTML = (Path("frontend") / "index.html").read_text(encoding="utf-8")


# ── §4/§17: saved profile serialization round-trip ───────────────────────────

def test_saved_profile_roundtrip_preserves_values_dtype_and_shape(tmp_path):
    fresh = {
        "description": "mô tả kiểm thử",
        "gender": "",
        "style": "tu_nhien",
        # Fresh encode may hand back a 2-D embedding; persisted shape is flat,
        # matching vieneu's own save_voices() and the preset assets.
        "speaker_emb": np.linspace(-1.0, 1.0, 16, dtype=np.float32).reshape(2, 8),
        "codes": np.array([11, 22, 33, 44], dtype=np.int64),
    }
    serialized = voice_store.serialize_profile(fresh)
    assert serialized["speaker_emb"] is not None and len(serialized["speaker_emb"]) == 16
    assert serialized["codes"] == [11, 22, 33, 44]

    voice_store.save_user_voices({"tester": serialized}, path=tmp_path / "voices.json")
    loaded = voice_store.load_user_voices(path=tmp_path / "voices.json")["tester"]
    rebuilt = voice_store.deserialize_profile(loaded)
    fresh_flat = fresh["speaker_emb"].reshape(-1)

    assert rebuilt["speaker_emb"].dtype == np.float32
    assert rebuilt["speaker_emb"].shape == (16,)
    # speaker_emb is quantized to 6 decimals by design (mirrors vieneu
    # save_voices()), so the round-trip is NOT bit-exact — but the deviation is
    # bounded far below anything that could alter conditioning behavior.
    max_err = float(np.max(np.abs(rebuilt["speaker_emb"] - fresh_flat)))
    assert np.allclose(rebuilt["speaker_emb"], fresh_flat, rtol=0, atol=5e-7)
    assert max_err <= 1e-6
    # codes are integers: the round-trip must be bit-exact.
    assert rebuilt["codes"].dtype == np.int64
    assert rebuilt["codes"].shape == (4,)
    assert np.array_equal(rebuilt["codes"], fresh["codes"])
    assert rebuilt["description"] == "mô tả kiểm thử"
    assert rebuilt["style"] == "tu_nhien"


def test_saved_profile_roundtrip_tolerates_missing_arrays():
    rebuilt = voice_store.deserialize_profile({"description": "x"})
    assert rebuilt["speaker_emb"] is None and rebuilt["codes"] is None


# ── §5/§8: conditioning round experiment schema ──────────────────────────────

def _conditioning_payload(**overrides):
    payload = {
        "reference": {
            "id": "saved_voice",
            "label": "Giọng đã lưu",
            "filename": "giogclone",
            "format": "wav",
            "size_bytes": 1,
            "duration_seconds": None,
        },
        "saved_voice_id": "giogclone",
        "conditioning_mode": "full",
        "evaluation_text_id": "quality_short_normal",
        "round": "conditioning",
        "run_number": 1,
    }
    payload.update(overrides)
    return payload


def test_conditioning_round_requires_saved_voice_mode_and_baseline():
    with pytest.raises(Exception):
        ExperimentCreate.model_validate(_conditioning_payload(saved_voice_id=None))
    with pytest.raises(Exception):
        ExperimentCreate.model_validate(_conditioning_payload(conditioning_mode="bogus"))
    with pytest.raises(Exception):
        ExperimentCreate.model_validate(_conditioning_payload(
            parameters={"speed": 1.0, "temperature": 0.9, "top_k": 25, "top_p": 0.95, "repetition_penalty": 1.2},
        ))
    created = ExperimentCreate.model_validate(_conditioning_payload(conditioning_mode="identity_only"))
    assert created.conditioning_mode == "identity_only"


def test_conditioning_evaluation_requires_pronunciation_result_and_stores_no_identity(tmp_path, monkeypatch):
    from backend.app import voice_lab

    store = tmp_path / "experiments.json"
    monkeypatch.setattr(voice_lab, "experiments_path", lambda: store)
    record = create_experiment(ExperimentCreate.model_validate(_conditioning_payload()), runtime={"engine": "test"})
    scores = {name: 4 for name in ListeningScores.model_fields}
    with pytest.raises(ValueError):
        evaluate_experiment(record["id"], ExperimentEvaluation(
            scores=scores, notes="", pronunciation_ok=None,
        ))
    for verdict in (True, False):
        result = evaluate_experiment(record["id"], ExperimentEvaluation(scores=scores, notes="", pronunciation_ok=verdict))
        assert result["pronunciation_ok"] is verdict
    raw = store.read_text(encoding="utf-8")
    assert "speaker_emb" not in raw and '"codes"' not in raw
    saved = {item["id"]: item for item in load_experiments()}[record["id"]]
    assert saved["conditioning_mode"] == "full" and saved["saved_voice_id"] == "giogclone"


# ── §5/§7/§25: /api/tts conditioning diagnostics, production invariance ─────

class FakeEngine:
    def __init__(self):
        self.generate_calls = []

    def get_voices(self):
        return ["myclone", "preset_one"]

    def get_user_voice_names(self):
        return ["myclone"]

    def generate(self, text, voice=None, speed=1.0, out_path=None, **kwargs):
        Path(out_path).write_bytes(b"RIFF")
        self.generate_calls.append({"voice": voice, "kwargs": kwargs})
        return str(out_path)


def test_identity_only_mode_via_api_tts_for_saved_voice():
    engine = FakeEngine()
    response = tts(TTSRequest(
        text="Mọi người đang ở đây.", voice="myclone", conditioning_mode="identity_only",
    ), engine=engine)
    assert response is not None
    assert engine.generate_calls[-1]["kwargs"]["use_ref_codes"] is False


def test_identity_only_mode_rejects_preset_and_unknown_mode():
    engine = FakeEngine()
    with pytest.raises(HTTPException) as preset_error:
        tts(TTSRequest(text="Mọi người đang ở đây.", voice="preset_one", conditioning_mode="identity_only"), engine=engine)
    assert preset_error.value.status_code == 400
    with pytest.raises(HTTPException) as mode_error:
        tts(TTSRequest(text="Mọi người đang ở đây.", voice="myclone", conditioning_mode="codes_off"), engine=engine)
    assert mode_error.value.status_code == 422


def test_main_tts_production_call_unchanged_without_conditioning_mode():
    engine = FakeEngine()
    tts(TTSRequest(text="Mọi người đang ở đây.", voice="myclone"), engine=engine)
    assert "use_ref_codes" not in engine.generate_calls[-1]["kwargs"]
    # Schema default stays None → the diagnostics branch never activates.
    assert TTSRequest(text="x").conditioning_mode is None


# ── §2/§16: engine plumbing for use_ref_codes + per-chunk profile reuse ─────

class FakeModel:
    sample_rate = 24000

    def __init__(self):
        self.infer_calls = []
        self.encode_calls = 0
        self._profile = (np.zeros(4, dtype=np.float32), np.array([5, 6], dtype=np.int64))

    def encode_reference(self, ref_audio, denoise=True, use_ref_codes=True):
        self.encode_calls += 1
        return self._profile

    def infer(self, text, voice=None, **kwargs):
        self.infer_calls.append({"voice": voice, "kwargs": kwargs})
        return np.zeros(4800, dtype=np.float32)


def _engine_with_fake_model():
    engine = TTSEngine(cache_model=False)
    engine._model = FakeModel()
    return engine


def test_engine_default_keeps_use_ref_codes_true_and_single_voice_for_every_chunk(tmp_path):
    engine = _engine_with_fake_model()
    long_text = "Câu một cho chunk. " * 30 + "Mọi người đang ở đây."
    engine.generate(long_text, voice="myclone", out_path=str(tmp_path / "default.wav"))
    assert engine._model.infer_calls, "expected chunked generation"
    assert all(call["kwargs"].get("use_ref_codes") is True for call in engine._model.infer_calls)
    assert len({str(call["voice"]) for call in engine._model.infer_calls}) == 1


def test_engine_identity_only_passthrough_drops_reference_codes(tmp_path):
    engine = _engine_with_fake_model()
    engine.generate("Mọi người đang ở đây.", voice="myclone",
                    out_path=str(tmp_path / "identity.wav"), use_ref_codes=False)
    assert engine._model.infer_calls[-1]["kwargs"]["use_ref_codes"] is False


def test_engine_reuses_one_encoded_profile_across_chunks(tmp_path):
    engine = _engine_with_fake_model()
    long_text = "Câu một cho chunk. " * 30
    engine.generate(long_text, voice="myclone", out_path=str(tmp_path / "clone.wav"), ref_audio="fake_ref.wav")
    assert engine._model.encode_calls == 1
    voices = [call["voice"] for call in engine._model.infer_calls]
    assert len(voices) >= 2
    assert voices[0] is voices[1]  # same profile object for every chunk (Phase 17 fix)


# ── §23: frontend conditioning UI contract ───────────────────────────────────

def test_frontend_conditioning_ui_uses_human_readable_labels_only():
    assert 'id="voiceLabConditioningMode"' in HTML
    assert 'id="voiceLabPronunciationOk"' in HTML
    assert 'value="conditioning"' in HTML
    assert "Đầy đủ tham chiếu" in HTML
    assert "Chỉ giữ đặc trưng giọng" in HTML
    assert "Đọc “người” đúng" in HTML
    # Technical identifiers must never surface in the UI layer.
    assert "use_ref_codes" not in APP and "speaker_emb" not in APP and "speaker_emb" not in HTML
    assert "voiceLabRound.value === 'conditioning'" in APP
    assert "conditioning_mode" in APP


def test_phase22_unicode_hygiene_still_applies_before_conditioning_paths():
    from backend.app.tts.text import preprocess_text

    assert preprocess_text("ng\u200Bười") == "người"


