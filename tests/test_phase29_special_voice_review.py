import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1] / "experiments" / "special_voice_review"


def test_review_experiment_configuration_is_controlled():
    config = json.loads((ROOT / "experiment_config.json").read_text(encoding="utf-8"))
    candidates = config["candidates"]
    assert set(candidates) == {"baseline", "review_candidate_a", "review_candidate_b", "review_candidate_c"}
    assert candidates["baseline"]["sampling"] == {}
    assert config["common"]["speed"] == 1.0
    assert config["common"]["use_ref_codes"] is True
    assert config["common"]["quality_diagnostics"] is True


def test_review_corpus_is_original_and_covers_required_cases():
    corpus = json.loads((ROOT / "test_sentences.json").read_text(encoding="utf-8"))
    categories = {item["category"] for item in corpus["sentences"]}
    assert 8 <= len(corpus["sentences"]) <= 12
    assert {"intro", "narrative", "suspense", "reveal", "action", "quiet_reflective", "names_numbers", "long_chunking"} <= categories
    assert all(item["text"].strip() for item in corpus["sentences"])


def test_review_outputs_and_reference_audio_are_ignored():
    gitignore = (Path(__file__).resolve().parents[1] / ".gitignore").read_text(encoding="utf-8")
    assert "experiments/special_voice_review/outputs/" in gitignore
    assert "experiments/special_voice_review/reference_audio/" in gitignore
