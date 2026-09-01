import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1] / "experiments" / "special_voice_podcast"


def test_phase30b_scaffold_has_complete_original_corpus():
    corpus = json.loads((ROOT / "test_sentences.json").read_text(encoding="utf-8"))
    assert len(corpus["sentences"]) == 12
    assert set(corpus["initial_short_test_ids"]) == {"reflective", "serious_observation", "long_complex"}
    required = {"reflective_statement", "personal_storytelling", "serious_observation", "question", "gentle_emotional", "slightly_dramatic", "calm_explanatory", "numbers_date", "vietnamese_english", "long_complex_sentence", "short_impactful", "soft_closing"}
    assert {item["category"] for item in corpus["sentences"]} == required
    assert all(item["text"].strip() for item in corpus["sentences"])


def test_phase30b_runner_is_reference_driven_and_blind():
    source = (ROOT / "runner.py").read_text(encoding="utf-8")
    assert "REFERENCE_REQUIRED" in source
    assert "--validate-only" in source
    assert "speed=1.0" in source
    assert "temperature=" not in source
    assert "phase30b_mapping.json" in source


def test_phase30b_sensitive_audio_and_outputs_are_ignored():
    gitignore = (Path(__file__).resolve().parents[1] / ".gitignore").read_text(encoding="utf-8")
    assert "experiments/special_voice_podcast/outputs/" in gitignore
    assert "experiments/special_voice_podcast/reference_audio/" in gitignore


def test_review_film_definition_remains_present_without_production_changes():
    special_voices = (Path(__file__).resolve().parents[1] / "backend" / "app" / "tts" / "special_voices.py").read_text(encoding="utf-8")
    assert '"review_film"' in special_voices
    assert "🎬 Review Film" in special_voices
