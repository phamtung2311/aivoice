import json
from pathlib import Path

import pytest
from pydantic import ValidationError

from backend.app.runtime_metadata import get_runtime_metadata
from backend.app import voice_lab


class FakeRuntime:
    __module__ = "vieneu.v3turbo"
    backend = "onnx"


class FakeLoader:
    def __init__(self):
        self._v = FakeRuntime()
        self.model_name = "legacy-label"
        self.device = None


class FakeEngine:
    def __init__(self):
        self._model = FakeLoader()
        self.backend = None
        self.device = None


def sample_create():
    return voice_lab.ExperimentCreate(
        reference={
            "id": "reference_a",
            "label": "Reference A",
            "filename": "speaker-a.wav",
            "format": "wav",
            "size_bytes": 1024,
            "duration_seconds": 6.2,
        },
        evaluation_text_id="brand_introduction",
        parameters=voice_lab.BASELINE_PARAMETERS,
        round="reference_selection",
        run_number=1,
    )


def test_runtime_metadata_uses_loaded_runtime():
    metadata = get_runtime_metadata(FakeEngine())
    assert metadata["engine_library"] == "vieneu"
    assert metadata["engine_version"] != ""
    assert metadata["runtime_family"] == "v3turbo"
    assert metadata["runtime_class"] == "FakeRuntime"
    assert metadata["runtime_backend"] == "onnx"
    assert metadata["device"] == "cpu"


def test_fixed_evaluation_corpus():
    corpus = voice_lab.load_corpus()
    assert len(corpus["sentences"]) == 6
    assert len(corpus["rubric"]) == 6
    categories = {item["category"] for item in corpus["sentences"]}
    assert categories == {
        "brand_introduction", "call_to_action", "numbers_and_date",
        "punctuation", "narrative", "emotion_cue",
    }
    emotion = next(item for item in corpus["sentences"] if item["category"] == "emotion_cue")
    assert emotion["cue"] in voice_lab.VERIFIED_CUES


def test_experiment_pending_and_persistent(tmp_path, monkeypatch):
    monkeypatch.setenv("VOICE_LAB_DIR", str(tmp_path))
    record = voice_lab.create_experiment(sample_create(), get_runtime_metadata(FakeEngine()))
    assert record["status"] == "pending_evaluation"
    assert record["parameters"] == voice_lab.BASELINE_PARAMETERS
    assert record["runtime"]["runtime_family"] == "v3turbo"
    assert "speaker_emb" not in json.dumps(record)
    assert "codes" not in json.dumps(record)
    assert voice_lab.load_experiments()[0]["id"] == record["id"]


def test_invalid_score_rejected():
    with pytest.raises(ValidationError):
        voice_lab.ListeningScores(
            identity=6,
            naturalness=4,
            pronunciation=4,
            prosody=4,
            audio_cleanliness=4,
            consistency=4,
        )


def test_evaluation_scores_and_notes_persist(tmp_path, monkeypatch):
    monkeypatch.setenv("VOICE_LAB_DIR", str(tmp_path))
    record = voice_lab.create_experiment(sample_create(), get_runtime_metadata(FakeEngine()))
    evaluation = voice_lab.ExperimentEvaluation(
        scores={
            "identity": 5,
            "naturalness": 4,
            "pronunciation": 4,
            "prosody": 3,
            "audio_cleanliness": 5,
            "consistency": 4,
        },
        notes="Giữ identity ổn định.",
    )
    updated = voice_lab.evaluate_experiment(record["id"], evaluation)
    assert updated["status"] == "evaluated"
    assert updated["average_score"] == pytest.approx(4.17)
    assert updated["notes"] == "Giữ identity ổn định."
    assert voice_lab.load_experiments()[0]["scores"]["identity"] == 5


def test_experiment_audio_status_persists_without_audio_payload(tmp_path, monkeypatch):
    monkeypatch.setenv("VOICE_LAB_DIR", str(tmp_path))
    record = voice_lab.create_experiment(sample_create(), get_runtime_metadata(FakeEngine()))
    assert record["has_audio"] is False
    updated = voice_lab.set_experiment_audio_status(record["id"], True)
    assert updated["has_audio"] is True
    assert voice_lab.load_experiments()[0]["has_audio"] is True
    cleaned = voice_lab.set_experiment_audio_status(record["id"], False)
    assert cleaned["has_audio"] is False


def test_identity_experiment_rejects_speed_change():
    with pytest.raises(ValidationError):
        voice_lab.ExperimentParameters(speed=1.1)


def test_initial_experiment_rejects_top_k_sweep():
    with pytest.raises(ValidationError):
        voice_lab.ExperimentParameters(top_k=30)


def test_reference_round_requires_baseline():
    payload = sample_create().model_dump()
    payload["parameters"]["temperature"] = 0.9
    with pytest.raises(ValidationError):
        voice_lab.ExperimentCreate.model_validate(payload)


def test_frontend_voice_lab_contracts_are_wired():
    app_source = (Path("frontend") / "app.js").read_text(encoding="utf-8")
    html = (Path("frontend") / "index.html").read_text(encoding="utf-8")
    assert "fetch(API + '/api/tts/clone'" in app_source
    assert "fetch(API + '/api/voice-lab/experiments'" in app_source
    assert "persistVoiceLabAudio(record.id, blob)" in app_source
    assert "idbGetVoiceLabAudio(item.id)" in app_source
    assert "round:voiceLabRound.value" in app_source
    assert "quality-corpus" in app_source
    assert "missing_words" in app_source
    assert "function playHistoryItem(item)" in app_source
    assert "fetch(API + '/api/tts'" not in app_source[app_source.index("async function playHistoryItem(item)"):app_source.index("function regenerateFromHistory(item)")]
    assert "method:'PATCH'" in app_source
    assert 'id="voiceLabAudio"' in html
    assert 'id="voiceLabSaveVoiceBtn"' in html
    assert 'id="voiceLabRubric"' in html
    assert 'value="1.0" readonly' in html


def test_manifest_requires_user_confirmation(tmp_path):
    path = tmp_path / "branded_voice.json"
    manifest = voice_lab.BrandedVoiceManifest(
        name="AIVoice Brand",
        saved_voice_id="brand-voice",
        runtime=get_runtime_metadata(FakeEngine()),
        reference_id="reference_a",
        parameters=voice_lab.ExperimentParameters(),
        evaluation_summary={"average": 4.5},
    )
    with pytest.raises(ValueError):
        voice_lab.save_branded_manifest(manifest, path=path)
    assert not path.exists()
    voice_lab.save_branded_manifest(manifest, user_confirmed=True, path=path)
    assert voice_lab.load_branded_manifest(path)["saved_voice_id"] == "brand-voice"
