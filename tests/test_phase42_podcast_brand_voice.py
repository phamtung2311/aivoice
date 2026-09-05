"""Phase 42 production profile tests. No real TTS inference is performed."""
from __future__ import annotations

import hashlib
import inspect
import json
from pathlib import Path
import shutil
import threading
import time

import numpy as np

from backend import main as main_mod
from backend.app.tts.audio import save_wav
from backend.app.tts.engine import TTSEngine
from backend.app.tts.long_audio import LongAudioJob, LongAudioJobs
from backend.app.tts.podcast_brand import (
    PODCAST_BRAND_SOURCE_VOICE_ID,
    PODCAST_BRAND_VOICE_ID,
    PODCAST_ENGINE_CONFIG,
    PODCAST_FINAL_TEMPO,
    PODCAST_HARD_MAX_CHARS,
    PODCAST_INFERENCE_CONFIG,
    PODCAST_PAUSES_SECONDS,
    PODCAST_SEMANTIC_PLANNER_VERSION,
    canonical_lexical_text,
    load_canonical_candidate_03,
    plan_podcast_text,
    semantic_chunk_to_tts_text,
)
from backend.app.tts.special_voices import SPECIAL_VOICES

ROOT = Path(__file__).resolve().parents[1]
CANDIDATE_03 = ROOT / "experiments/brand_voice_phase41b/baseline/PODCAST_SYNTHETIC_CANDIDATE_03"
CANDIDATE_B = ROOT / "experiments/brand_voice_phase40b/baseline/PODCAST_CANDIDATE_B_BASELINE"


class VoiceListEngine:
    def get_voices(self): return ["default", PODCAST_BRAND_SOURCE_VOICE_ID]
    def get_preset_names(self): return ["default"]
    def get_user_voice_names(self): return []
    def get_special_voice_names(self): return [PODCAST_BRAND_SOURCE_VOICE_ID]
    def get_voice_metadata(self, name): return SPECIAL_VOICES.get(name, {})


class FakeDiskEngine:
    def __init__(self): self.calls = []
    def generate(self, text, *, voice, speed, out_path, **kwargs):
        self.calls.append({"text": text, "voice": voice, "speed": speed, "kwargs": kwargs})
        save_wav(out_path, np.zeros(4800, dtype=np.float32), 48000)
        return out_path


class FailOnceEngine(FakeDiskEngine):
    def __init__(self):
        super().__init__()
        self.failed = False

    def generate(self, text, **kwargs):
        if len(self.calls) == 1 and not self.failed:
            self.failed = True
            raise RuntimeError("simulated final-chunk failure")
        return super().generate(text, **kwargs)


class RecordingModel:
    sample_rate = 48000
    def __init__(self): self.calls = []
    def infer(self, text, voice=None, **kwargs):
        self.calls.append((text, voice, kwargs))
        return np.zeros(4800, dtype=np.float32)


def wait_terminal(job, timeout=5):
    deadline = time.monotonic() + timeout
    while job.state not in {"COMPLETED", "FAILED", "CANCELLED"} and time.monotonic() < deadline:
        time.sleep(0.01)
    assert job.state == "COMPLETED", job.error


def test_profile_is_visible_and_resolves_to_candidate_03():
    profile = SPECIAL_VOICES[PODCAST_BRAND_VOICE_ID]
    assert profile["display_name"] == "🎙️ Podcast Brand Voice"
    assert profile["source_voice_id"] == PODCAST_BRAND_SOURCE_VOICE_ID
    assert profile["speaker"] == "Synthetic Candidate 03"
    assert profile["status"] == "candidate"
    assert profile["is_final_brand_voice"] is False
    item = next(v for v in main_mod.voices(engine=VoiceListEngine())["voices"] if v["id"] == PODCAST_BRAND_VOICE_ID)
    assert item["name"] == "🎙️ Podcast Brand Voice"
    assert item["pipeline_version"] == "podcast_brand_voice_v1"


def test_web_selector_has_clean_production_hint_without_phase_labels():
    html = (ROOT / "frontend/index.html").read_text(encoding="utf-8")
    app = (ROOT / "frontend/app.js").read_text(encoding="utf-8")
    assert 'id="voiceProfileHint"' in html
    assert "podcast_brand_voice_v1" in app
    assert "Giọng podcast dài — nhịp tự nhiên, nhấn trọng tâm, tối ưu nghe lâu." in app
    assert "control.disabled = isPodcastBrand" in app
    assert "ttsScriptArea.disabled = isPodcastBrand" in app
    assert "Phase 41E" not in app and "Phase 41F" not in app and "Phase 41H" not in app
    studio = (ROOT / "frontend/audio-studio.js").read_text(encoding="utf-8")
    assert "Đang dùng thiết lập tối ưu của Podcast Brand Voice." in studio
    assert "speed.disabled=isPodcastBrand" in studio
    assert "script.disabled=isPodcastBrand" in studio


def test_canonical_assets_are_exact_and_candidate_b_is_preserved():
    expected = {
        CANDIDATE_03 / "speaker_emb.npy": "c763159d8ed6ed4b0f1916f8b0762d1902743d293fcd7874541966d7f9ee10a1",
        CANDIDATE_03 / "reference_codes.npy": "fe8f8e3e1766a7954595fa3a355e46aca8c3e27be4aba4bb1db8d9b60a960aa5",
        CANDIDATE_B / "speaker_emb.npy": "09ce43e1facce2878df2e4bc78581213804d1beca638e6861f8794ba3f63986e",
        CANDIDATE_B / "reference_codes.npy": "fe8f8e3e1766a7954595fa3a355e46aca8c3e27be4aba4bb1db8d9b60a960aa5",
    }
    for path, digest in expected.items():
        assert hashlib.sha256(path.read_bytes()).hexdigest() == digest
    embedding = np.load(CANDIDATE_03 / "speaker_emb.npy", allow_pickle=False)
    assert hashlib.sha256(np.ascontiguousarray(embedding).tobytes()).hexdigest() == "980d5856f58a8619b6abf0c3935de74ddfb5c333b9b8fae2fd5c3b6ef7067771"
    profile, evidence = load_canonical_candidate_03()
    assert np.array_equal(profile["speaker_emb"], embedding)
    assert evidence["speaker_array_sha256"] == "980d5856f58a8619b6abf0c3935de74ddfb5c333b9b8fae2fd5c3b6ef7067771"


def test_missing_canonical_candidate_fails_without_named_voice_fallback(monkeypatch, tmp_path):
    import backend.app.tts.podcast_brand as module
    monkeypatch.setattr(module, "PODCAST_CANDIDATE_03_ROOT", tmp_path / "missing")
    with np.testing.assert_raises_regex(RuntimeError, "cannot be resolved"):
        module.load_canonical_candidate_03()


def test_v2_pause_and_engine_policy_are_frozen():
    assert PODCAST_PAUSES_SECONDS["semantic_thought_boundary"] == 0.10
    assert PODCAST_PAUSES_SECONDS["setup_resolution_boundary"] == 0.06
    assert PODCAST_PAUSES_SECONDS["paragraph_transition"] == 0.32
    assert PODCAST_FINAL_TEMPO == 0.98
    assert PODCAST_INFERENCE_CONFIG == {
        "mode": "v3turbo", "backend": "onnx",
        "temperature": 0.8, "top_k": 25, "top_p": 0.95,
        "repetition_penalty": 1.2, "repetition_window": 64,
        "denoise": True, "use_ref_codes": True, "silence_p": 0.15,
        "crossfade_p": 0.0, "apply_watermark": True, "sample_rate": 48000,
        "max_new_frames": 600, "max_chars": 800, "batch_size": 1,
    }
    assert PODCAST_ENGINE_CONFIG["model_max_chars"] == 800
    assert PODCAST_ENGINE_CONFIG["expected_sample_rate"] == 48000
    assert PODCAST_ENGINE_CONFIG["preplanned_text"] is True


def test_semantic_planner_preserves_lexical_text_focus_and_hard_limit():
    text = (
        "Ta thường nghĩ rằng nhanh hơn là tốt hơn, nhưng điều quan trọng là hiểu mình đang đi đâu. "
        "Không phải mọi khoảng dừng đều là trì hoãn, mà là cơ hội để nhìn rõ hơn.\n\n"
        "Khi một ý kết thúc, người nghe cần một nhịp để tiếp nhận. Sau đó câu chuyện mới tiếp tục tự nhiên."
    )
    chunks = plan_podcast_text(text)
    assert canonical_lexical_text(" ".join(c.text for c in chunks)) == canonical_lexical_text(text)
    assert all(len(c.text) <= PODCAST_HARD_MAX_CHARS for c in chunks)
    assert all(c.primary_focus_phrase is None or c.text.count(c.primary_focus_phrase) >= 1 for c in chunks)
    assert sum(c.text.count(c.primary_focus_phrase) for c in chunks if c.primary_focus_phrase) <= len(chunks)
    assert chunks[-1].boundary_after == "final"
    assert any(c.boundary_after == "paragraph_transition" for c in chunks)


def test_tts_text_policy_and_phase41g_planner_regression_are_exact():
    assert semantic_chunk_to_tts_text("Một ý, vẫn giữ dấu phẩy. Ý tiếp theo!") == "Một ý, vẫn giữ dấu phẩy Ý tiếp theo"
    source = (ROOT / "experiments/brand_voice_phase41g/podcast_text.txt").read_text(encoding="utf-8").strip()
    validated = json.loads((ROOT / "experiments/brand_voice_phase41g/semantic_plan.json").read_text(encoding="utf-8"))
    produced = plan_podcast_text(source)
    assert len(produced) == len(validated["chunks"]) == 55
    assert [item.text for item in produced] == [item["text"] for item in validated["chunks"]]
    expected_boundaries = [
        "paragraph_transition" if item["boundary_after"] == "thought_transition"
        else "final" if item["boundary_after"] == "paragraph_end"
        else item["boundary_after"]
        for item in validated["chunks"]
    ]
    assert [item.boundary_after for item in produced] == expected_boundaries
    assert [item.index for item in produced if item.boundary_after == "setup_resolution_boundary"] == [7, 21, 27, 30, 37, 39, 43]
    assert len({item.paragraph_index for item in produced}) == 17
    assert canonical_lexical_text(" ".join(item.text for item in produced)) == canonical_lexical_text(source)
    assert produced[-1].pause_after_seconds == 0
    assert sum(item.pause_after_seconds for item in produced) == 8.64


def test_planner_contains_general_rules_not_fixture_sentence_hacks():
    import backend.app.tts.podcast_brand as module
    implementation = inspect.getsource(module)
    validated = json.loads((ROOT / "experiments/brand_voice_phase41g/semantic_plan.json").read_text(encoding="utf-8"))
    assert "S000" not in implementation and "chunk_index" not in implementation
    assert all(item["text"] not in implementation for item in validated["chunks"])


def test_preplanned_engine_text_is_not_rechunked_and_exact_kwargs_reach_model(tmp_path):
    engine = TTSEngine(cache_model=False)
    model = RecordingModel()
    engine._model = model
    voice, _evidence = load_canonical_candidate_03()
    tts_text = "Một câu đã được lập kế hoạch không còn dấu kết thúc"
    engine.generate(tts_text, voice=voice, speed=1.0, out_path=str(tmp_path / "one.wav"),
                    **PODCAST_ENGINE_CONFIG)
    assert len(model.calls) == 1
    actual_text, actual_voice, kwargs = model.calls[0]
    assert actual_text == tts_text
    assert actual_voice is voice
    assert kwargs == {
        "denoise": True, "use_ref_codes": True, "temperature": 0.8,
        "top_k": 25, "top_p": 0.95, "repetition_penalty": 1.2,
        "repetition_window": 64, "apply_watermark": True,
        "max_new_frames": 600, "batch_size": 1, "silence_p": 0.15,
        "crossfade_p": 0.0, "max_chars": 800,
    }


def test_brand_api_ignores_ui_overrides_but_normal_voice_keeps_them(monkeypatch):
    calls = []
    class Manager:
        def create(self, **kwargs):
            calls.append(kwargs)
            return LongAudioJob("stub", kwargs["text"], kwargs["voice"], kwargs["speed"],
                                kwargs["prosody_markup"], kwargs["options"], Path("/tmp/stub"))
        def public(self, job): return {"job_id": job.id}
        def get(self, _job_id): return None
    monkeypatch.setattr(main_mod, "_LONG_AUDIO_JOBS", Manager())
    brand = main_mod.LongAudioRequest(
        text="Một câu.", voice=PODCAST_BRAND_VOICE_ID, speed=1.7,
        temperature=0.2, top_k=5, top_p=0.6, repetition_penalty=1.8,
    )
    main_mod.create_long_audio_job(brand, engine=VoiceListEngine())
    assert calls[-1]["speed"] == 0.98
    assert calls[-1]["options"] == {}
    normal = main_mod.LongAudioRequest(
        text="Một câu.", voice="default", speed=1.3,
        temperature=0.2, top_k=5, top_p=0.6, repetition_penalty=1.8,
    )
    main_mod.create_long_audio_job(normal, engine=VoiceListEngine())
    assert calls[-1]["speed"] == 1.3
    assert calls[-1]["options"] == {
        "temperature": 0.2, "top_k": 5, "top_p": 0.6, "repetition_penalty": 1.8,
    }


def test_only_podcast_profile_invokes_semantic_planner(monkeypatch, tmp_path):
    import backend.app.tts.long_audio as module
    calls = []
    original = module.plan_podcast_text
    monkeypatch.setattr(module, "plan_podcast_text", lambda text: (calls.append(text) or original(text)))
    manager = LongAudioJobs(FakeDiskEngine(), threading.BoundedSemaphore(1), root=str(tmp_path))
    podcast = LongAudioJob("p", "Một ý.\n\nÝ tiếp theo.", PODCAST_BRAND_VOICE_ID, 1, False, {}, tmp_path / "p")
    normal = LongAudioJob("n", "Một ý. Ý tiếp theo.", "default", 1, False, {}, tmp_path / "n")
    manager._segments(podcast)
    manager._segments(normal)
    assert calls == [podcast.text]


def test_disk_job_uses_candidate_source_and_never_overwrites_canonical(monkeypatch, tmp_path):
    before = {path: hashlib.sha256(path.read_bytes()).hexdigest() for path in CANDIDATE_03.glob("*.npy")}
    engine = FakeDiskEngine()
    manager = LongAudioJobs(engine, threading.BoundedSemaphore(1), root=str(tmp_path / "jobs"))
    monkeypatch.setattr(manager, "_apply_podcast_tempo", lambda source, destination: shutil.copyfile(source, destination))
    job = manager.create(text="Ý đầu tiên.\n\nÝ thứ hai.", voice=PODCAST_BRAND_VOICE_ID,
                         speed=1.7, prosody_markup=True, options={"temperature": 0.1})
    wait_terminal(job)
    expected_embedding = np.load(CANDIDATE_03 / "speaker_emb.npy", allow_pickle=False)
    expected_codes = np.load(CANDIDATE_03 / "reference_codes.npy", allow_pickle=False)
    assert all(isinstance(call["voice"], dict) for call in engine.calls)
    assert all(np.array_equal(call["voice"]["speaker_emb"], expected_embedding) for call in engine.calls)
    assert all(np.array_equal(call["voice"]["codes"], expected_codes) for call in engine.calls)
    assert all(call["speed"] == 1.0 for call in engine.calls)
    assert all(call["kwargs"]["temperature"] == 0.8 for call in engine.calls)
    assert all(call["kwargs"] == PODCAST_ENGINE_CONFIG for call in engine.calls)
    assert job.output_path and job.output_path.is_file()
    assert not list(job.directory.glob("chunk_*.wav"))
    metadata = json.loads((job.directory / "metadata.json").read_text(encoding="utf-8"))
    assert metadata["pipeline_version"] == "podcast_brand_voice_v1"
    assert metadata["completed_chunks"] == metadata["total_chunks"]
    assert len(metadata["completed_chunk_metadata"]) == metadata["total_chunks"]
    manifest = json.loads((job.directory / "podcast_pipeline_manifest.json").read_text(encoding="utf-8"))
    assert manifest["semantic_planner_version"] == PODCAST_SEMANTIC_PLANNER_VERSION
    assert manifest["generic_ui_parameters"] == "ignored"
    assert manifest["effective_inference_config"] == PODCAST_INFERENCE_CONFIG
    assert manifest["candidate_03"]["speaker_array_sha256"] == "980d5856f58a8619b6abf0c3935de74ddfb5c333b9b8fae2fd5c3b6ef7067771"
    assert manifest["chunks"][-1]["explicit_pause_after_seconds"] == 0
    after = {path: hashlib.sha256(path.read_bytes()).hexdigest() for path in CANDIDATE_03.glob("*.npy")}
    assert after == before


def test_normal_voice_keeps_adjustable_sampling(tmp_path):
    engine = FakeDiskEngine()
    manager = LongAudioJobs(engine, threading.BoundedSemaphore(1), root=str(tmp_path / "jobs"))
    job = manager.create(text="Một câu bình thường.", voice="default", speed=1.0,
                         prosody_markup=False, options={"temperature": 0.35, "top_k": 12})
    wait_terminal(job)
    assert engine.calls[0]["voice"] == "default"
    assert engine.calls[0]["kwargs"] == {"temperature": 0.35, "top_k": 12}


def test_pause_is_after_current_chunk_and_tempo_runs_once(monkeypatch, tmp_path):
    engine = FakeDiskEngine()
    manager = LongAudioJobs(engine, threading.BoundedSemaphore(1), root=str(tmp_path / "jobs"))
    calls = []
    def copy_once(source, destination):
        calls.append((source, destination))
        shutil.copyfile(source, destination)
    monkeypatch.setattr(manager, "_apply_podcast_tempo", copy_once)
    job = manager.create(text="Ý đầu tiên.\n\nÝ thứ hai.", voice=PODCAST_BRAND_VOICE_ID,
                         speed=1.7, prosody_markup=True, options={"temperature": 0.1})
    wait_terminal(job)
    assert len(calls) == 1
    with __import__("wave").open(str(job.output_path), "rb") as wav:
        assert wav.getnframes() == 4800 * 2 + round(0.32 * 48000)


def test_failed_long_job_resumes_without_regenerating_verified_chunk(monkeypatch, tmp_path):
    engine = FailOnceEngine()
    manager = LongAudioJobs(engine, threading.BoundedSemaphore(1), root=str(tmp_path / "jobs"))
    monkeypatch.setattr(manager, "_apply_podcast_tempo", lambda source, destination: shutil.copyfile(source, destination))
    job = manager.create(text="Ý đầu tiên.\n\nÝ thứ hai.", voice=PODCAST_BRAND_VOICE_ID,
                         speed=1.0, prosody_markup=False, options={})
    deadline = time.monotonic() + 5
    while job.state not in {"FAILED", "COMPLETED"} and time.monotonic() < deadline:
        time.sleep(0.01)
    assert job.state == "FAILED"
    first_hash = job.chunk_records[0]["wav_sha256"]
    manager.resume(job.id)
    wait_terminal(job)
    assert len(engine.calls) == 2  # successful first + successful retry of second only
    assert job.chunk_records[0]["wav_sha256"] == first_hash
