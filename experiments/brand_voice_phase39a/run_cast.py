#!/usr/bin/env python3
"""Phase 39A: exactly four sequential, CPU-only Qwen VoiceDesign identities."""

from __future__ import annotations

import gc
import hashlib
import json
import os
import platform
import random
import resource
import subprocess
import sys
import time
from datetime import datetime, timezone
from importlib.metadata import version
from pathlib import Path

os.environ.setdefault("HF_HUB_OFFLINE", "1")
os.environ.setdefault("TRANSFORMERS_OFFLINE", "1")

import numpy as np
import psutil
import soundfile as sf
import torch
from qwen_tts import Qwen3TTSModel


ROOT = Path(__file__).resolve().parent
PROJECT = ROOT.parents[1]
MODEL = PROJECT / "experiments/special_voice_podcast/qwen_voice_factory/models/Qwen3-TTS-12Hz-1.7B-VoiceDesign"
AUDIO = ROOT / "audio"
TEXT_FILE = ROOT / "shared_audition_text.txt"
MANIFEST = ROOT / "manifest.json"
PROVENANCE = ROOT / "provenance.json"

TEXT = "When the noise fades, we begin to see what truly matters: not the answer we inherited, but the principle we choose to live by."
MODEL_ID = "Qwen/Qwen3-TTS-12Hz-1.7B-VoiceDesign"
SEEDS = {"A": 39001, "B": 39002, "C": 39003, "D": 39004}
GENERATION = {
    "do_sample": True,
    "temperature": 0.9,
    "top_k": 50,
    "top_p": 1.0,
    "repetition_penalty": 1.05,
    "subtalker_dosample": True,
    "subtalker_temperature": 0.9,
    "subtalker_top_k": 50,
    "subtalker_top_p": 1.0,
    "max_new_tokens": 8192,
}

PROMPTS = {
    "A": (
        "Design a fictional mature male podcast narrator with a medium-low register and a dark-neutral, "
        "slightly back-set resonance. Give the voice a close, intimate presence, restrained dry grain, "
        "moderate vocal weight, and firm clean consonants. Pitch movement is economical, with occasional "
        "subtle downward sentence endings; energy stays controlled, alert, and deliberately thoughtful. "
        "The acoustic signature should be compact dark resonance plus fine dry texture, recognizable without "
        "being gimmicky. Use neutral English pronunciation. Avoid sleepiness, excessive bass, theatricality, "
        "news or radio delivery, advertising polish, whispering, forced rasp, and regional accent."
    ),
    "B": (
        "Design a fictional mature male podcast narrator in a lower-mid register with warm chest resonance "
        "and a lightly weathered surface. Use restrained natural roughness, slightly irregular organic texture, "
        "substantial but human vocal weight, and confident articulation that never becomes an announcer voice. "
        "His cadence should feel lived-in and reflective, with clear emphasis on the central idea and natural "
        "variation between phrases. The acoustic signature is warm chest body plus subtle weathering. Use neutral "
        "English pronunciation. Avoid forced rasp, trailer drama, commercial polish, radio or television news, "
        "heroic acting, whispering, sleepiness, exaggerated emotion, and regional accent."
    ),
    "C": (
        "Design a fictional male podcast narrator with a medium-low register, a dry matte timbre, narrower "
        "forward-focused resonance, and precise consonant edges. Keep vocal weight moderate, emotion restrained, "
        "and diction exact, while introducing slight natural asymmetry in pitch movement so the voice remains "
        "human and attentive. Use a close-mic intellectual presence and selectively weighted phrase endings. "
        "The acoustic signature is matte dryness plus precise forward focus. Use neutral English pronunciation. "
        "Avoid sterility, robotic rhythm, academic lecturing, corporate narration, advertising, newsreading, "
        "theatricality, whispering, exaggerated rasp, young-influencer energy, and regional accent."
    ),
    "D": (
        "Design a fictional mature male nighttime podcast narrator with a deep but natural register, warm-dark "
        "lower resonance, rounded vocal body, and smooth restrained richness. Let phrase onsets begin slightly "
        "soft, then gather into firm, focused words; maintain calm confidence, alert thoughtfulness, and intimate "
        "headphone presence. The acoustic signature is a soft-entry contrast against a solid warm-dark core, "
        "memorable but never cinematic. Use neutral English pronunciation. Avoid artificial bass, meditation or "
        "ASMR pacing, sleepiness, whispering, trailer narration, commercial or broadcast delivery, theatrical "
        "acting, over-polish, and regional accent."
    ),
}


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def audio_metrics(path: Path) -> dict:
    info = sf.info(path)
    data, sample_rate = sf.read(path, always_2d=True, dtype="float32")
    mono = data.mean(axis=1, dtype=np.float64)
    finite = bool(np.isfinite(data).all())
    peak = float(np.max(np.abs(data))) if data.size else 0.0
    rms = float(np.sqrt(np.mean(np.square(mono)))) if mono.size else 0.0
    clipped = int(np.count_nonzero(np.abs(data) >= 0.999))
    return {
        "duration_seconds": float(len(data) / sample_rate),
        "sample_rate_hz": int(sample_rate),
        "channels": int(data.shape[1]),
        "format": info.format,
        "subtype": info.subtype,
        "frames_header": int(info.frames),
        "frames_read": int(len(data)),
        "all_samples_finite": finite,
        "peak_abs": peak,
        "rms": rms,
        "clipped_samples_abs_ge_0_999": clipped,
        "size_bytes": path.stat().st_size,
        "sha256": sha256(path),
    }


def valid(metrics: dict) -> bool:
    return (
        metrics["duration_seconds"] > 0
        and metrics["channels"] == 1
        and metrics["all_samples_finite"]
        and metrics["frames_header"] == metrics["frames_read"]
        and metrics["clipped_samples_abs_ge_0_999"] / max(1, metrics["frames_read"]) <= 0.01
    )


def directory_size(path: Path) -> int:
    return sum(item.stat().st_size for item in path.rglob("*") if item.is_file())


def set_seed(seed: int) -> None:
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)


def main() -> None:
    if ROOT.exists() and (MANIFEST.exists() or PROVENANCE.exists() or AUDIO.exists()):
        existing = list(AUDIO.glob("*.wav")) if AUDIO.exists() else []
        if existing or MANIFEST.exists() or PROVENANCE.exists():
            raise FileExistsError("Phase 39A artifacts already exist; no overwrite or reroll allowed")
    if TEXT_FILE.read_text(encoding="utf-8").strip() != TEXT:
        raise RuntimeError("Shared audition text differs from the frozen text")
    required = [MODEL / "model.safetensors", MODEL / "speech_tokenizer/model.safetensors", MODEL / "generation_config.json"]
    if not all(path.is_file() and path.stat().st_size > 0 for path in required):
        raise FileNotFoundError("Existing local VoiceDesign checkpoint is missing or incomplete")
    available_before = psutil.virtual_memory().available
    if available_before < 7 * 2**30:
        raise RuntimeError(f"Insufficient available RAM before load: {available_before} bytes")

    AUDIO.mkdir(parents=True, exist_ok=False)
    started_utc = datetime.now(timezone.utc).isoformat()
    total_started = time.perf_counter()
    print(f"[Phase39A] Loading local Qwen VoiceDesign on CPU; available RAM {available_before / 2**30:.2f} GiB.", flush=True)
    load_started = time.perf_counter()
    model = Qwen3TTSModel.from_pretrained(
        str(MODEL), device_map="cpu", dtype=torch.bfloat16, attn_implementation="eager"
    )
    load_seconds = time.perf_counter() - load_started
    records = []
    try:
        for index, key in enumerate(("A", "B", "C", "D"), start=1):
            output = AUDIO / f"candidate_{key}.wav"
            seed = SEEDS[key]
            failures = []
            for attempt in (1, 2):
                temporary = AUDIO / f".candidate_{key}.attempt{attempt}.tmp.wav"
                set_seed(seed)
                generation_started = time.perf_counter()
                print(f"[Phase39A {index}/4] Candidate {key}, seed {seed}, attempt {attempt}.", flush=True)
                try:
                    with torch.inference_mode():
                        wavs, sample_rate = model.generate_voice_design(
                            text=TEXT,
                            language="English",
                            instruct=PROMPTS[key],
                            **GENERATION,
                        )
                    sf.write(temporary, wavs[0], sample_rate, subtype="PCM_16")
                    metrics = audio_metrics(temporary)
                    if not valid(metrics):
                        raise RuntimeError(f"invalid WAV: {metrics}")
                    temporary.replace(output)
                    records.append(
                        {
                            "candidate": key,
                            "seed": seed,
                            "attempt": attempt,
                            "technical_failures_before_success": failures,
                            "generation_seconds": time.perf_counter() - generation_started,
                            "peak_process_rss_mib": resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1024.0,
                            "audio": audio_metrics(output),
                        }
                    )
                    print(f"[Phase39A {index}/4] Candidate {key} saved ({metrics['duration_seconds']:.3f} s).", flush=True)
                    break
                except Exception as exc:
                    failures.append({"attempt": attempt, "error": repr(exc)})
                    if temporary.exists():
                        temporary.unlink()
                    if attempt == 2:
                        raise
                    print(f"[Phase39A {index}/4] Technical failure; one identical retry allowed: {exc!r}", flush=True)
    finally:
        del model
        gc.collect()

    if len(records) != 4 or sorted(path.name for path in AUDIO.glob("*.wav")) != [f"candidate_{key}.wav" for key in "ABCD"]:
        raise RuntimeError("Phase 39A did not produce exactly the four intended candidates")

    completed_utc = datetime.now(timezone.utc).isoformat()
    total_seconds = time.perf_counter() - total_started
    repository_commit = subprocess.check_output(["git", "-C", str(PROJECT), "rev-parse", "HEAD"], text=True).strip()
    manifest = {
        "phase": "39A",
        "execution_status": "PASS",
        "human_gate": "PENDING HUMAN QA",
        "shared_audition_text": TEXT,
        "language": "English",
        "candidates": records,
    }
    provenance = {
        "phase": "39A",
        "purpose": "private synthetic podcast brand-identity casting",
        "candidate03_status": "RETIRED AS ACTIVE BRAND TARGET",
        "candidate03_historical_assets_modified": False,
        "production_modified": False,
        "downstream_synthetic_corpus_rights": "UNRESOLVED",
        "started_utc": started_utc,
        "completed_utc": completed_utc,
        "repository_commit_before_phase39a": repository_commit,
        "repository_worktree_before_phase39a": "DIRTY; existing user changes preserved",
        "model_id": MODEL_ID,
        "model_path": str(MODEL.relative_to(PROJECT)),
        "model_downloaded_in_phase39a": False,
        "model_size_bytes": directory_size(MODEL),
        "environment": "experiments/special_voice_podcast/qwen_voice_factory/.venv",
        "python": sys.version,
        "platform": platform.platform(),
        "device": "cpu",
        "dtype": "torch.bfloat16",
        "torch_version": torch.__version__,
        "torch_cuda_version": torch.version.cuda,
        "torch_cuda_available": torch.cuda.is_available(),
        "qwen_tts_version": version("qwen-tts"),
        "transformers_version": version("transformers"),
        "generation_settings": GENERATION,
        "language": "English",
        "non_streaming_mode": True,
        "seeds": SEEDS,
        "prompts": PROMPTS,
        "shared_audition_text": TEXT,
        "model_load_seconds": load_seconds,
        "total_wall_seconds": total_seconds,
        "peak_process_rss_mib": resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1024.0,
        "memory_available_before_bytes": available_before,
        "experiment_disk_bytes": directory_size(ROOT),
    }
    MANIFEST.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    PROVENANCE.write_text(json.dumps(provenance, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print("PHASE39A_CAST_READY", flush=True)


if __name__ == "__main__":
    main()
