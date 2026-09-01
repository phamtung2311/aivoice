"""Phase 30Q.1: Audio Studio uses the shared, marked long-audio pipeline."""
import threading
import time

import numpy as np

from backend.app.tts.audio import save_wav
from backend.app.tts.long_audio import LongAudioJobs


class FakeEngine:
    def __init__(self):
        self.calls = []

    def generate(self, text, *, out_path, **_kwargs):
        self.calls.append(text)
        save_wav(out_path, np.zeros(480, dtype=np.float32), 24000)


def wait_terminal(manager, job, timeout=3):
    deadline = time.monotonic() + timeout
    while job.state not in {"COMPLETED", "FAILED", "CANCELLED"} and time.monotonic() < deadline:
        time.sleep(0.01)
    assert job.state == "COMPLETED", job.error


def test_markers_are_parsed_before_safe_chunking_and_never_reach_engine(tmp_path):
    engine = FakeEngine()
    manager = LongAudioJobs(engine, threading.BoundedSemaphore(1), root=str(tmp_path))
    job = manager.create(text="Câu đầu. || Câu sau.", voice="podcast_brand_beta", speed=1,
                         prosody_markup=True, options={})
    wait_terminal(manager, job)
    assert engine.calls == ["Câu đầu.", "Câu sau."]
    assert all("|" not in call for call in engine.calls)
    assert job.total_chunks == job.completed_chunks == 2
    assert job.output_path and job.output_path.exists()


def test_cancel_is_cooperative_and_public_state_is_diagnostic(tmp_path):
    manager = LongAudioJobs(FakeEngine(), threading.BoundedSemaphore(1), root=str(tmp_path))
    job = manager.create(text="Câu đầu. Câu sau.", voice="default", speed=1,
                         prosody_markup=False, options={})
    manager.cancel(job.id)
    deadline = time.monotonic() + 3
    while job.state not in {"CANCELLED", "COMPLETED"} and time.monotonic() < deadline:
        time.sleep(0.01)
    assert manager.public(job)["cancel_requested"] is True
    assert job.state == "CANCELLED"
