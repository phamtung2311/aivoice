from pathlib import Path


ROOT = Path(__file__).resolve().parents[1] / "experiments" / "special_voice_podcast"


def test_phase30d_audition_text_is_new_normal_prose():
    text = (ROOT / "phase30d_audition.txt").read_text(encoding="utf-8").strip()
    assert 300 <= len(text) <= 700
    assert text.count(".") == 4
    assert "[" not in text and "..." not in text and "!!!" not in text


def test_phase30d_filter_relies_on_explicit_packaged_metadata_only():
    source = (ROOT / "phase30d_runner.py").read_text(encoding="utf-8")
    assert 'for label in ("Bắc", "Nam", "Trung")' in source
    assert "never speaker names" in source
    assert "speed=1.0" not in source
    assert "phase30d_mapping.json" in source


def test_phase30d_report_and_phase30c_preservation_exist():
    repo = Path(__file__).resolve().parents[1]
    assert (repo / "docs" / "reports" / "PHASE_30D_REPORT.md").is_file()
    phase30c = ROOT / "outputs" / "phase30c"
    assert (phase30c / "phase30c_mapping.json").is_file()
    assert (phase30c / "phase30c_listening.csv").is_file()
