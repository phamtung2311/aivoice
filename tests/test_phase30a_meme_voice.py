from pathlib import Path
import json


ROOT = Path(__file__).resolve().parents[1] / "experiments" / "special_voice_meme"


def test_phase30a_scaffold_has_original_corpus_and_reference_contract():
    corpus = json.loads((ROOT / "test_sentences.json").read_text(encoding="utf-8"))
    assert 8 <= len(corpus["sentences"]) <= 10
    assert {"normal", "punchline", "question", "exclamation", "sarcastic", "numbers_internet", "long", "fast", "calm"} == {item["id"] for item in corpus["sentences"]}
    assert "6–8" in (ROOT / "reference_contract.md").read_text(encoding="utf-8")


def test_phase30a_runner_stays_reference_driven():
    source = (ROOT / "runner.py").read_text(encoding="utf-8")
    assert "REFERENCE_REQUIRED" in source
    assert "temperature=" not in source
    assert "speed=1.0" in source
