"""Compare both API paths with deterministic inference, without loading a model."""
import threading
import time
from pathlib import Path

import numpy as np
import pytest

from backend import main
from backend.app.tts.engine import TTSEngine
from backend.app.tts.long_audio import LongAudioJobs
from backend.app.tts.podcast_voices import PODCAST_VOICES


class DeterministicModel:
    sample_rate = 24000

    def __init__(self):
        self.calls = []

    def infer(self, text, voice=None, **kwargs):
        self.calls.append((text, voice, kwargs))
        return (np.sin(np.arange(960) * .07) * .2).astype(np.float32)


def make_engine():
    engine = TTSEngine.__new__(TTSEngine)
    engine._model = DeterministicModel()
    return engine


@pytest.mark.parametrize('voice', PODCAST_VOICES)
@pytest.mark.parametrize('markup,speed', [(False, 1.0), (False, 1.3), (True, .8)])
def test_studio_matches_tts_text_voice_options_and_wav(tmp_path, monkeypatch, voice, markup, speed):
    direct, studio = make_engine(), make_engine()
    monkeypatch.setattr(main, '_valid_voice_ids', lambda engine: set(PODCAST_VOICES))
    manager = LongAudioJobs(studio, threading.BoundedSemaphore(1), root=str(tmp_path))
    monkeypatch.setattr(main, '_LONG_AUDIO_JOBS', manager)
    text = ('Quán cà phê nhỏ ở góc phố vắng khách, chỉ có tiếng nhạc. '*8)
    if markup:
        text += ' || Hôm nay trời rất đẹp. |||'
    payload = dict(text=text, voice=voice, speed=speed,
                   tts_script='Nội dung script cũ phải bị bỏ qua. || Câu khác.',
                   prosody_markup=markup, smart_text_processing=True,
                   temperature=.8, top_k=25, top_p=.95, repetition_penalty=1.2)
    response = main.tts(main.TTSRequest(**payload), engine=direct)
    try:
        result = main.create_long_audio_job(main.LongAudioRequest(**payload), engine=studio)
        job = manager.get(result['job_id'])
        deadline = time.monotonic() + 5
        while job.state not in {'COMPLETED', 'FAILED', 'CANCELLED'} and time.monotonic() < deadline:
            time.sleep(.01)
        assert job.state == 'COMPLETED', job.error
        assert Path(response.path).read_bytes() == job.output_path.read_bytes()
        assert len(direct._model.calls) == len(studio._model.calls)
        for left, right in zip(direct._model.calls, studio._model.calls):
            assert left[0] == right[0]
            assert left[2] == right[2]
            for key in ('speaker_emb', 'codes'):
                np.testing.assert_array_equal(left[1][key], right[1][key])
    finally:
        Path(response.path).unlink(missing_ok=True)
