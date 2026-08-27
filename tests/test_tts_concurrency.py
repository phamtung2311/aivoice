import time
import threading
from concurrent.futures import ThreadPoolExecutor
import numpy as np
import soundfile as sf
from fastapi.testclient import TestClient

from backend import main as main_mod


class DummyEngineBlocking:
    def __init__(self, sleep_s=0.2):
        self.model_name = "dummy-model"
        self.device = "cpu"
        self.sleep_s = sleep_s

    def get_voices(self):
        return ["default"]

    def generate(self, text, voice=None, speed=1.0, out_path=None, **kwargs):
        # increment active counter stored on the class
        cls = DummyEngineBlocking
        if not hasattr(cls, "active_generations"):
            cls.active_generations = 0
            cls.max_active_generations = 0

        cls.active_generations += 1
        try:
            if cls.active_generations > cls.max_active_generations:
                cls.max_active_generations = cls.active_generations
            # simulate blocking work
            time.sleep(self.sleep_s)
            # write a small wav so handler returns file
            sr = 22050
            t = np.linspace(0, 0.01, int(sr * 0.01), False)
            data = 0.01 * np.sin(2 * np.pi * 440 * t).astype(np.float32)
            sf.write(out_path, data, sr)
            return out_path
        finally:
            cls.active_generations -= 1


def setup_module(module):
    # override engine dependency with blocking dummy engine
    main_mod.app.dependency_overrides[main_mod.get_engine] = lambda: DummyEngineBlocking(sleep_s=0.2)


def teardown_module(module):
    main_mod.app.dependency_overrides.clear()


def test_semaphore_limits_concurrency():
    client = TestClient(main_mod.app)

    payload = {"text": "Xin chào", "voice": "default", "speed": 1.0}

    # run two requests concurrently
    def post_request():
        r = client.post("/api/tts", json=payload)
        return r.status_code

    DummyEngineBlocking.active_generations = 0
    DummyEngineBlocking.max_active_generations = 0

    with ThreadPoolExecutor(max_workers=2) as ex:
        futs = [ex.submit(post_request) for _ in range(2)]
        results = [f.result() for f in futs]

    # both requests should succeed
    assert all(r == 200 for r in results)
    # ensure that at most one generate ran concurrently
    assert DummyEngineBlocking.max_active_generations == 1
