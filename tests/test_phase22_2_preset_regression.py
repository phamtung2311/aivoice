"""Phase 22.2 — preset pronunciation regression guards.

Adds the §16 regression contract: preset ordinary TTS never receives the
experimental conditioning mode; absent conditioning_mode preserves the legacy
inference call; the fixed diagnostic sentence survives preprocessing
byte-identically to the pre-Phase-22 implementation; the Voice-Lab-only A/B
stays isolated; Phase 20 chunking, history and Save Voice remain untouched.
"""

from pathlib import Path

import pytest
from fastapi import HTTPException

from backend.app.tts.text import preprocess_text
from backend.main import TTSRequest, tts

APP = (Path("frontend") / "app.js").read_text(encoding="utf-8")
SENTENCE = "Mọi người đang ở đây."


class FakeEngine:
    def __init__(self):
        self.generate_calls = []

    def get_voices(self):
        return ["preset_one", "myclone"]

    def get_user_voice_names(self):
        return ["myclone"]

    def generate(self, text, voice=None, speed=1.0, out_path=None, **kwargs):
        Path(out_path).write_bytes(b"RIFF")
        self.generate_calls.append({"voice": voice, "kwargs": kwargs})
        return str(out_path)


def test_preset_ordinary_tts_never_receives_identity_only():
    engine = FakeEngine()
    tts(TTSRequest(text=SENTENCE, voice="preset_one"), engine=engine)
    call = engine.generate_calls[-1]
    assert call["voice"] == "preset_one"
    assert "use_ref_codes" not in call["kwargs"]
    assert "conditioning_mode" not in call["kwargs"]
    with pytest.raises(HTTPException) as exc:
        tts(TTSRequest(text=SENTENCE, voice="preset_one", conditioning_mode="identity_only"), engine=engine)
    assert exc.value.status_code == 400  # experimental mode is saved-voice-only


def test_absent_conditioning_mode_preserves_legacy_inference_call():
    engine = FakeEngine()
    tts(TTSRequest(text=SENTENCE, voice="preset_one", speed=1.0), engine=engine)
    kwargs = engine.generate_calls[-1]["kwargs"]
    # Legacy /api/tts forwarded only the four sampling params (or omitted the
    # unset ones) — nothing new may appear for a plain preset request.
    assert set(kwargs) <= {"temperature", "top_k", "top_p", "repetition_penalty", "use_ref_codes"}
    assert kwargs.get("use_ref_codes") is not False


def test_frontend_main_tts_payload_never_sends_conditioning_mode():
    start = APP.index("async function synthesize")
    end = APP.index("function isSupportedTextFile")
    synthesize_source = APP[start:end]
    assert "conditioning_mode" not in synthesize_source
    assert "payload = {text, voice, speed}" in synthesize_source
    # The only producers of conditioning_mode are the two Voice Lab sample/
    # evaluation handlers; ordinary main TTS (synthesize) must never send it.
    assert APP.count("conditioning_mode:") == 1          # generateVoiceLabSample experiment body
    assert APP.count("payload.conditioning_mode") == 1   # identity_only branch
    first = APP.index("async function generateVoiceLabSample")
    assert APP.index("payload.conditioning_mode") > first


def test_diagnostic_sentence_survives_preprocessing_byte_identical_to_legacy():
    def legacy_preprocess(text):  # verbatim pre-Phase-22 implementation
        if text is None:
            return ""
        import re
        text = re.sub(r"[\t\r]+", " ", text)
        text = re.sub(r" +", " ", text)
        lines = [ln.strip() for ln in text.splitlines()]
        cleaned, prev_blank = [], False
        for ln in lines:
            if ln == "":
                if not prev_blank:
                    cleaned.append("")
                prev_blank = True
            else:
                cleaned.append(ln)
                prev_blank = False
        return "\n".join(cleaned).strip()

    samples = [SENTENCE, "Người Việt Nam luôn yêu tiếng Việt.",
               "Mười người đang đứng ngoài cửa.", "Tôi cười với mọi người.",
               "Xin chào. Đây là câu hai!", "Đã 4.200,5 điểm... thử"]
    for sample in samples:
        assert preprocess_text(sample) == legacy_preprocess(sample)
        assert preprocess_text(sample) == sample  # clean input is a pure no-op
        assert preprocess_text(sample).encode("utf-8") == sample.encode("utf-8")


def test_phase22_invisible_character_cleanup_still_works():
    assert preprocess_text("Mọi ng\u200Bười đang ở đây.") == SENTENCE
    assert preprocess_text("Mọi ng\u00ADười đang ở đây.") == SENTENCE
    assert preprocess_text("mọi\u00A0người") == "mọi người"


def test_phase20_chunking_remains_intact():
    from backend.app.tts.text import chunk_sentences, split_into_sentences

    sentence = " ".join(["mọi người"] * 30) + "."
    chunks = chunk_sentences(split_into_sentences(sentence), max_chars=12)
    assert " ".join(chunks) == sentence
    assert set(" ".join(chunks).split()) == set(sentence.split())


def test_history_and_save_voice_surfaces_untouched():
    assert "'/api/voices/save'" in APP
    assert APP.count("fetch(API + '/api/voices/save'") == 1  # Voice Lab only
    assert "function playHistoryItem(item)" in APP
    start = APP.index("async function playHistoryItem")
    end = APP.index("function markHistoryAudioUnavailable")
    replay = APP[start:end]
    assert "fetch(" not in replay  # history replay stays blob-only
