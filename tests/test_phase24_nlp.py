"""Phase 24 — deterministic local Brand Voice Studio NLP coverage."""

from pathlib import Path

import pytest

from backend.app.tts.nlp import normalize_text
from backend.main import NLPPreviewRequest, TTSRequest, nlp_preview, tts


@pytest.mark.parametrize(("source", "expected"), [
    ("10/05/2026", "ngày mười tháng năm, năm hai nghìn không trăm hai mươi sáu"),
    ("01/01/2004", "ngày một tháng một, năm hai nghìn không trăm lẻ bốn"),
    ("31/12/1999", "ngày ba mươi mốt tháng mười hai, năm một nghìn chín trăm chín mươi chín"),
])
def test_ddmmyyyy_dates_include_one_year_introducer(source, expected):
    assert normalize_text(source) == expected


def test_written_numeric_date_keeps_the_year_introducer_once():
    assert normalize_text("ngày 10 tháng 5 năm 2026") == "ngày mười tháng năm, năm hai nghìn không trăm hai mươi sáu"


def test_money_percent_time_decimal_and_fraction():
    assert normalize_text("1.250.000đ") == "một triệu hai trăm năm mươi nghìn đồng"
    assert normalize_text("15%") == "mười lăm phần trăm"
    assert normalize_text("20:45") == "hai mươi giờ bốn mươi lăm phút"
    assert normalize_text("72,5") == "bảy mươi hai phẩy năm"
    assert normalize_text("3/5") == "ba phần năm"


def test_dictionary_and_custom_dictionary(tmp_path, monkeypatch):
    custom = tmp_path / "custom_dictionary.json"
    custom.write_text('{"AIVoice": "ây ai voice", "ACME": "ác mi"}', encoding="utf-8")
    monkeypatch.setenv("NLP_CUSTOM_DICTIONARY_PATH", str(custom))
    assert normalize_text("OpenAI dùng API và AIVoice của ACME") == "Ô-pần AI dùng ây pi ai và ây ai voice của ác mi"


def test_disable_pipeline_and_protected_text_are_unchanged():
    source = 'Báo giá 15% vào `10/05/2026`; xem https://example.test/10/05/2026.'
    assert normalize_text(source, enabled=False) == source
    processed = normalize_text(source)
    assert processed.startswith("Báo giá mười lăm phần trăm")
    assert "`10/05/2026`" in processed
    assert "https://example.test/10/05/2026." in processed


def test_preview_uses_the_same_optional_pipeline():
    enabled = nlp_preview(NLPPreviewRequest(text="20:45", smart_text_processing=True))
    disabled = nlp_preview(NLPPreviewRequest(text="20:45", smart_text_processing=False))
    assert enabled == {"original": "20:45", "processed": "hai mươi giờ bốn mươi lăm phút"}
    assert disabled == {"original": "20:45", "processed": "20:45"}


def test_frontend_exposes_opt_in_and_local_preview_contract():
    source = Path("frontend/app.js").read_text(encoding="utf-8")
    markup = Path("frontend/index.html").read_text(encoding="utf-8")
    assert 'id="smartTextProcessing"' in markup
    assert 'id="smartTextPreview"' in markup
    assert "'/api/nlp/preview'" in source
    assert "payload.smart_text_processing" in source


class RecordingEngine:
    def __init__(self):
        self.text = None

    def get_voices(self):
        return ["default"]

    def get_user_voice_names(self):
        return []

    def generate(self, text, **_kwargs):
        self.text = text
        Path(_kwargs["out_path"]).write_bytes(b"RIFF")


def test_tts_pipeline_can_be_disabled():
    enabled = RecordingEngine()
    disabled = RecordingEngine()
    tts(TTSRequest(text="15%", voice="default"), engine=enabled)
    tts(TTSRequest(text="15%", voice="default", smart_text_processing=False), engine=disabled)
    assert enabled.text == "mười lăm phần trăm"
    assert disabled.text == "15%"
