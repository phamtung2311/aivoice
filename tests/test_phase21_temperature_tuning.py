from pathlib import Path

import pytest
from pydantic import ValidationError

from backend.app import voice_lab


def test_temperature_round_requires_saved_voice_and_locks_other_sampling_values():
    reference = {"id":"saved_voice", "label":"Giọng ứng viên", "filename":"tung", "format":"wav", "size_bytes":1}
    payload = {
        "reference": reference,
        "evaluation_text_id": "quality_short_normal",
        "parameters": {"speed":1.0, "temperature":0.7, "top_k":25, "top_p":0.95, "repetition_penalty":1.2},
        "round": "temperature",
        "saved_voice_id": "tung",
    }
    assert voice_lab.ExperimentCreate.model_validate(payload).parameters.temperature == 0.7
    payload["saved_voice_id"] = None
    with pytest.raises(ValidationError):
        voice_lab.ExperimentCreate.model_validate(payload)
    payload["saved_voice_id"] = "tung"
    payload["parameters"]["top_p"] = 0.9
    with pytest.raises(ValidationError):
        voice_lab.ExperimentCreate.model_validate(payload)


def test_temperature_candidate_needs_explicit_user_selection_and_persists(tmp_path):
    candidate = voice_lab.TemperatureCandidateSelection(saved_voice_id="tung", temperature=0.8)
    target = tmp_path / "temperature_candidates.json"
    with pytest.raises(ValueError):
        voice_lab.save_temperature_candidate(candidate, user_confirmed=False, path=target)
    saved = voice_lab.save_temperature_candidate(candidate, user_confirmed=True, path=target)
    assert saved["temperature"] == 0.8
    assert saved["saved_voice_id"] == "tung"
    assert "speaker_emb" not in target.read_text(encoding="utf-8")
    assert voice_lab.load_temperature_candidates(target)["tung"]["speed"] == 1.0


def test_temperature_candidate_whitelist_and_identity_separation():
    with pytest.raises(ValidationError):
        voice_lab.TemperatureCandidateSelection(saved_voice_id="tung", temperature=0.6)
    with pytest.raises(ValidationError):
        voice_lab.TemperatureCandidateSelection(saved_voice_id="tung", temperature=0.7, repetition_penalty=1.3)


def test_temperature_summary_uses_only_user_evaluations(tmp_path, monkeypatch):
    monkeypatch.setenv("VOICE_LAB_DIR", str(tmp_path))
    payload = voice_lab.ExperimentCreate(
        reference={"id":"saved_voice", "label":"Giọng ứng viên", "filename":"tung", "format":"wav", "size_bytes":1},
        saved_voice_id="tung",
        evaluation_text_id="quality_short_normal",
        parameters={"speed":1.0, "temperature":0.8, "top_k":25, "top_p":0.95, "repetition_penalty":1.2},
        round="temperature",
    )
    record = voice_lab.create_experiment(payload, {"runtime_family":"test"})
    voice_lab.evaluate_experiment(record["id"], voice_lab.ExperimentEvaluation(
        scores={"identity":4, "naturalness":3, "pronunciation":5, "prosody":4, "audio_cleanliness":5, "consistency":3},
        missing_words=True,
    ))
    summary = voice_lab.temperature_summary("tung", 0.8)
    assert summary["evaluated_runs"] == 1
    assert summary["missing_word_count"] == 1
    assert summary["pronunciation_average"] == 5


def test_frontend_uses_saved_voice_candidate_and_manual_override_contract():
    source = Path("frontend/app.js").read_text(encoding="utf-8")
    assert "selectedSavedVoiceId" in source
    assert "Round Temperature chỉ dùng giọng đã lưu" in source
    assert "fetch(API + '/api/tts'" in source
    assert "preferredSamplingForVoice(voice)" in source
    assert "if(advancedOpen)" in source
    assert "user_confirmed:true" in source
