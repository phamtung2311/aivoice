import os
import numpy as np
import soundfile as sf
from backend import main as main_mod
from backend.app.tts.engine import TTSEngine
from backend.app.tts.prosody import PAUSE_PRESETS_MS, parse_prosody_script, transform_prosody_script


def test_parser_preserves_punctuation_and_maps_markers():
    parsed = parse_prosody_script("Xin chào. || Tiếp theo | là ví dụ.")
    assert [(item.text, item.pause_after_ms) for item in parsed] == [
        ("Xin chào.", PAUSE_PRESETS_MS["medium"]),
        ("Tiếp theo", PAUSE_PRESETS_MS["light"]),
        ("là ví dụ.", None),
    ]


def test_parser_covers_all_presets_unicode_spaces_and_newlines():
    parsed = parse_prosody_script("Cà phê |\nđủ chậm || để nghe. ||| Rồi tiếp tục")
    assert [item.pause_after_ms for item in parsed] == [70, 140, 260, None]
    assert [item.text for item in parsed] == ["Cà phê", "đủ chậm", "để nghe.", "Rồi tiếp tục"]


def test_parser_without_markers_is_a_single_clean_segment():
    parsed = parse_prosody_script("Không có marker.")
    assert len(parsed) == 1
    assert (parsed[0].text, parsed[0].pause_after_ms) == ("Không có marker.", None)


def test_clean_segment_transform_preserves_marker_boundaries():
    transformed = transform_prosody_script("Ngày 10/05 | lúc 20:45", lambda item: f"[{item}]")
    assert transformed == "[Ngày 10/05] | [lúc 20:45]"


def test_parser_rejects_ambiguous_marker_sequences():
    for script in ("| Xin chào", "Xin chào || | tiếp", "Xin chào |||| tiếp"):
        try:
            parse_prosody_script(script)
        except ValueError:
            pass
        else:
            raise AssertionError(script)


class _RecordingModel:
    sample_rate = 1000

    def __init__(self):
        self.inputs = []

    def infer(self, text, voice=None, **kwargs):
        self.inputs.append(text)
        return np.full(10, 0.25, dtype=np.float32)


def test_explicit_pause_replaces_punctuation_join_and_markers_are_stripped(tmp_path):
    engine = TTSEngine(cache_model=False)
    model = _RecordingModel()
    engine._model = model
    path = tmp_path / "prosody.wav"
    engine.generate_prosody("Một. || Hai.", out_path=str(path))
    audio, sr = sf.read(path, dtype="float32")
    assert sr == 1000
    assert model.inputs == ["Một.", "Hai."]
    # 10 samples speech + exact 140 ms explicit deficit + 10 samples speech.
    # A period's ordinary 130 ms target is not stacked at this marked boundary.
    assert len(audio) == 10 + 140 + 10


class _ApiEngine:
    def __init__(self):
        self.calls = []

    def get_voices(self):
        return ["default"]

    def generate(self, text, out_path=None, **kwargs):
        self.calls.append(("normal", text))
        sf.write(out_path, np.full(16, 0.1, dtype=np.float32), 1000)

    def generate_prosody(self, text, out_path=None, **kwargs):
        self.calls.append(("prosody", text))
        sf.write(out_path, np.full(16, 0.1, dtype=np.float32), 1000)


def test_api_is_backward_compatible_and_only_uses_markup_path_when_requested():
    engine = _ApiEngine()
    ordinary = main_mod.tts(main_mod.TTSRequest(text="Xin chào", voice="default"), engine)
    marked = main_mod.tts(main_mod.TTSRequest(text="Xin chào", tts_script="Xin || chào", prosody_markup=True, voice="default"), engine)
    editable = main_mod.tts(main_mod.TTSRequest(text="Bản gốc", tts_script="Bản đã sửa", voice="default"), engine)
    assert ordinary.media_type == marked.media_type == editable.media_type == "audio/wav"
    assert engine.calls == [("normal", "Xin chào"), ("prosody", "Xin || chào"), ("normal", "Bản đã sửa")]
    for response in (ordinary, marked, editable):
        os.remove(response.path)


def test_final_marker_preserved_by_normalization_and_rendered_as_silence(tmp_path):
    for marker, milliseconds in (("|", 70), ("||", 140), ("|||", 260)):
        script = f"Xin chào. {marker}  "
        parsed = parse_prosody_script(script)
        assert [(part.text, part.pause_after_ms) for part in parsed] == [("Xin chào.", milliseconds)]
        assert transform_prosody_script(script, str.upper) == f"XIN CHÀO. {marker}"
        engine = TTSEngine(cache_model=False)
        model = _RecordingModel()
        engine._model = model
        path = tmp_path / f"trailing_{milliseconds}.wav"
        engine.generate_prosody(script, out_path=str(path))
        audio, sr = sf.read(path, dtype="float32")
        assert model.inputs == ["Xin chào."]
        assert sr == 1000
        assert len(audio) == 10 + milliseconds
        assert np.all(audio[-milliseconds:] == 0)


def test_trailing_pause_keeps_existing_silence_and_stereo_shape():
    from backend.app.tts.audio import fill_trailing_pause
    audio = np.concatenate((np.full((10, 2), .2), np.zeros((100, 2))))
    padded = fill_trailing_pause(audio, 1000, 140)
    assert padded.shape == (150, 2)
    np.testing.assert_array_equal(padded[:110], audio)
    assert fill_trailing_pause(audio, 1000, 70) is audio
