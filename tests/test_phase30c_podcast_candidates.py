from pathlib import Path


ROOT = Path(__file__).resolve().parents[1] / "experiments" / "special_voice_podcast"


def test_phase30c_audition_uses_one_original_normal_prose_script():
    text = (ROOT / "phase30c_audition.txt").read_text(encoding="utf-8").strip()
    assert 400 <= len(text) <= 700
    assert text.count(".") >= 4
    assert "[" not in text and "..." not in text and "!!!" not in text


def test_phase30c_runner_keeps_candidates_identity_based_and_blind():
    source = (ROOT / "phase30c_runner.py").read_text(encoding="utf-8")
    assert "packaged_preset_profile" in source
    assert "speaker_emb" in source and "codes" in source
    assert "random.Random(SEED).shuffle" in source
    assert "--candidate-index" in source
    assert "speed=1.0" in source
    assert "temperature=" not in source
    assert "phase30c_mapping.json" in source


def test_phase30c_listening_guidance_allows_rank_only_feedback():
    instructions = (ROOT / "phase30c_listening_instructions.md").read_text(encoding="utf-8")
    assert "Top 1:" in instructions
    assert "Top 2:" in instructions
    assert "Top 3:" in instructions


def test_phase30c_persistent_report_exists():
    report = Path(__file__).resolve().parents[1] / "docs" / "reports" / "PHASE_30C_REPORT.md"
    assert report.is_file()
