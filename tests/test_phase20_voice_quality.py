import numpy as np
import soundfile as sf

from backend.app import voice_lab
from backend.app.tts.audio import join_audios
from backend.app.tts.engine import QUALITY_OUTER_CHUNK_CHARS, TTSEngine
from backend.app.tts.text import chunk_sentences, split_into_sentences


class QualityRecordingModel:
    sample_rate = 24000

    def __init__(self):
        self.calls = []
        self.profile = (np.array([0.1, 0.2], dtype=np.float32), np.array([[3, 4]], dtype=np.int64))

    def encode_reference(self, *_args, **_kwargs):
        return self.profile

    def infer(self, text, voice=None, **kwargs):
        self.calls.append((text, voice, kwargs))
        # Nonzero edges make fade/trimming regressions observable.
        return np.linspace(0.25, -0.25, 240, dtype=np.float32)


def test_long_text_chunking_preserves_tokens_and_punctuation():
    long_sentence = " ".join(["tháng-5/2026"] * 35) + "."
    chunks = chunk_sentences(split_into_sentences(long_sentence), max_chars=80)
    assert chunks
    assert all("tháng-5/2026" in chunk or chunk == "." for chunk in chunks)
    assert " ".join(chunks) == long_sentence
    assert chunks[-1].endswith(".")


def test_long_sentence_prefers_comma_boundary_before_plain_whitespace():
    sentence = "một hai ba bốn, năm sáu bảy tám chín mười"
    chunks = chunk_sentences([sentence], max_chars=18)
    assert chunks[0].endswith(",")
    assert " ".join(chunks) == sentence


def test_join_keeps_first_last_samples_and_inserts_only_requested_gap():
    first = np.array([0.4, 0.3], dtype=np.float32)
    second = np.array([-0.2, -0.4], dtype=np.float32)
    joined = join_audios([first, second], 1000, gap_samples=[3])
    assert np.array_equal(joined[:2], first)
    assert np.array_equal(joined[-2:], second)
    assert np.array_equal(joined[2:5], np.zeros(3, dtype=np.float32))


def test_engine_limits_outer_chunks_reuses_saved_profile_and_keeps_final_chunk(tmp_path):
    model = QualityRecordingModel()
    engine = TTSEngine(cache_model=False)
    engine._model = model
    text = " ".join(["từ"] * 150) + "."
    path = engine.generate(text, ref_audio="reference.wav", out_path=tmp_path / "quality.wav", quality_diagnostics=True)
    waveform, sr = sf.read(path, dtype="float32")
    assert sr == model.sample_rate
    assert len(model.calls) > 1
    assert all(len(call[0]) <= QUALITY_OUTER_CHUNK_CHARS for call in model.calls)
    assert model.calls[-1][0].endswith(".")
    assert all(np.array_equal(call[1]["speaker_emb"], model.profile[0]) for call in model.calls)
    assert all(np.array_equal(call[1]["codes"], model.profile[1]) for call in model.calls)
    assert waveform[-1] != 0.0
    assert engine.last_generation_diagnostics["outer_chunk_count"] == len(model.calls)
    assert engine.last_generation_diagnostics["chunks"][-1]["ending"] == "."


def test_quality_corpus_and_missing_word_evaluation_persist(tmp_path, monkeypatch):
    monkeypatch.setenv("VOICE_LAB_DIR", str(tmp_path / "experiments"))
    quality = voice_lab.load_quality_corpus()
    assert len(quality["sentences"]) >= 5
    payload = voice_lab.ExperimentCreate(
        reference={"id":"reference_a", "label":"Reference A", "filename":"a.wav", "format":"wav", "size_bytes":100, "duration_seconds":6},
        evaluation_text_id="quality_repeated_word",
        parameters=voice_lab.BASELINE_PARAMETERS,
        round="reference_selection",
    )
    record = voice_lab.create_experiment(payload, {"runtime_family":"test"})
    evaluated = voice_lab.evaluate_experiment(record["id"], voice_lab.ExperimentEvaluation(
        scores={"identity":3, "naturalness":3, "pronunciation":3, "prosody":3, "audio_cleanliness":3, "consistency":3},
        missing_words=True,
        missing_word_note="từ năm",
    ))
    assert evaluated["missing_words"] is True
    assert evaluated["missing_word_note"] == "từ năm"
