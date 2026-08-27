"""Phase 22 — Vietnamese pronunciation & text normalization audit tests.

Covers: NFC composition, NFD input, invisible-separator hygiene, accent
preservation, chunker word integrity with combining sequences, frontend UTF-8
contract, the controlled pronunciation corpus, and (when importable) the
sea_g2p NFD/NFC phonemizer equivalence measured in the Phase 22 probe.
"""

import json
import unicodedata
from pathlib import Path

import pytest

from backend.app.tts.normalize_vi import (
    audit_invisible_characters,
    normalize_vi_input,
)
from backend.app.tts.text import (
    chunk_sentences,
    preprocess_text,
    split_into_sentences,
)

APP = (Path("frontend") / "app.js").read_text(encoding="utf-8")
HTML = (Path("frontend") / "index.html").read_text(encoding="utf-8")

NGUOI = "người"
NGUOI_NFD = unicodedata.normalize("NFD", NGUOI)


def test_preprocess_keeps_nfc_word_visually_identical():
    assert preprocess_text(NGUOI) == NGUOI
    # Idempotent: running twice changes nothing.
    assert preprocess_text(preprocess_text(NGUOI)) == NGUOI


def test_nfd_input_composes_to_nfc_before_proceeding():
    assert unicodedata.is_normalized("NFD", NGUOI_NFD)
    cleaned = preprocess_text(NGUOI_NFD)
    assert unicodedata.is_normalized("NFC", cleaned)
    assert cleaned == NGUOI
    # normalize_vi_input alone already composes.
    assert normalize_vi_input(NGUOI_NFD) == NGUOI


def test_vietnamese_accents_are_never_folded():
    samples = ["người", "cười", "tươi", "lười", "rượu", "mượn", "nguyễn", "nghiêng", "khuỷu", "thuở"]
    for sample in samples:
        assert preprocess_text(sample) == sample
        assert unicodedata.normalize("NFD", "nguoi") not in sample  # guard sanity


def test_zero_width_characters_inside_word_are_removed_not_spaced():
    # Phase 22 probe evidence: ZWSP inside a word became a real space inside
    # sea_g2p normalization and split the syllable ("ng" + "ười").
    for intruder in ("\u200B", "\u200C", "\u200D", "\u2060", "\uFEFF", "\u00AD"):
        assert preprocess_text(f"ng{intruder}ười") == NGUOI
        assert audit_invisible_characters(f"ng{intruder}ười") == [f"U+{ord(intruder):04X}"]


def test_nbsp_and_narrow_nbsp_become_plain_spaces_between_words():
    assert preprocess_text("mọi\u00A0người") == "mọi người"
    assert preprocess_text("mọi\u202Fngười") == "mọi người"
    # A zero-width space never hides between words either.
    assert preprocess_text("mọi \u200B người") == "mọi người"


def test_chunker_never_splits_words_with_combining_sequences():
    sentence = " ".join(["mọi người"] * 30) + "."
    chunks = chunk_sentences(split_into_sentences(sentence), max_chars=12)
    assert len(chunks) > 1
    reassembled = " ".join(chunks)
    assert reassembled == sentence
    # Every token, including every accented "người", survives intact.
    assert set(reassembled.split()) == set(sentence.split())


def test_split_into_sentences_preserves_accented_sentence():
    sentence = "Người Việt Nam luôn yêu tiếng Việt."
    parts = split_into_sentences(preprocess_text(sentence))
    assert parts == [sentence]


def test_pronunciation_corpus_loads_and_covers_focus_word():
    corpus_path = Path("data") / "voice_lab" / "pronunciation_corpus.json"
    corpus = json.loads(corpus_path.read_text(encoding="utf-8"))
    assert corpus["focus_word"] == NGUOI
    for word in corpus["words"]:
        assert NGUOI in word or word, word
    assert NGUOI in corpus["words"]
    settings = corpus["probe_settings"]
    assert settings == {
        "speed": 1.0,
        "temperature": 0.8,
        "top_k": 25,
        "top_p": 0.95,
        "repetition_penalty": 1.2,
    }
    # Full-sentence diagnostics use only the controlled corpus inputs.
    assert "Mọi người đang ở đây." in corpus["manual_listening"]["sentences"]


def test_frontend_utf8_contract_for_vietnamese_payloads():
    assert 'charset="utf-8"' in HTML.lower() or "charset=utf-8" in HTML.lower()
    # Main TTS payload is JSON.stringify'd UTF-8; text is never URI-encoded.
    assert "encodeURIComponent(text" not in APP
    assert "body: JSON.stringify(payload)" in APP


def test_sea_g2p_nfd_equals_nfc_for_focus_word_when_importable():
    pytest.importorskip("sea_g2p")
    from sea_g2p import SEAPipeline

    pipe = SEAPipeline(lang="vi")
    nfc_phones = pipe.run(NGUOI, punc_norm=True)
    nfd_phones = pipe.run(NGUOI_NFD, punc_norm=True)
    assert nfc_phones == nfd_phones
    # Measured Phase 22 probe representation: ŋ + ʲyə glide + tone 2, not split.
    assert nfc_phones.startswith("ŋ")
    assert "ɛndʒ" not in nfc_phones  # orphan 'ng' must not read as English G


def test_sea_g2p_audit_hides_zero_width_split_case_therefore_app_layer_fixes_it():
    pytest.importorskip("sea_g2p")
    from sea_g2p import SEAPipeline

    pipe = SEAPipeline(lang="vi")
    poisoned = f"ng\u200Bười"
    # sea_g2p normalizes the ZWSP into a real space and the audit reports nothing.
    assert pipe.normalizer.normalize(poisoned) == "ng ười"
    assert list(pipe.normalizer.audit(poisoned)) == []
    # Our Phase 22 layer removes the poison BEFORE the library can split it.
    assert pipe.run(normalize_vi_input(poisoned), punc_norm=True) == pipe.run(NGUOI, punc_norm=True)
