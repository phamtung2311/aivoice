from pathlib import Path


ROOT = Path(__file__).resolve().parents[1] / "experiments" / "special_voice_podcast" / "custom_voice_research"


def test_phase30e_analysis_is_read_only():
    source = (ROOT / "speaker_embedding_analysis.py").read_text(encoding="utf-8")
    assert "read-only" in source
    assert "engine.generate" not in source
    assert "speaker_embedding_analysis.json" in source


def test_phase30e_report_and_decision_exist():
    repo = Path(__file__).resolve().parents[1]
    assert (repo / "docs" / "reports" / "PHASE_30E_REPORT.md").is_file()
    assert "HUMAN_REFERENCE_REQUIRED" in (ROOT / "phase30e_decision.md").read_text(encoding="utf-8")
