#!/usr/bin/env python3
"""Phase 38A: fixed, sequential Candidate 03 short-source corpus pilot.

This experiment uses the existing local CPU/ONNX Candidate 03 path. It never
modifies production or the canonical anchor. No sampling, continuity, speed or
chunking parameter is varied. A technical failure receives one same-config retry;
subjectively poor but technically valid audio is preserved as evidence.
"""
from __future__ import annotations

import csv
import hashlib
import json
import os
import platform
import resource
import shutil
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import soundfile as sf

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
ANCHOR = ROOT / "experiments/brand_speaker_phase33c/baseline_anchor/BRAND_CANDIDATE_03_BASELINE"
OUT = HERE / "audio"
ATTEMPTS = HERE / "technical_attempts"
MANIFEST = HERE / "manifest.json"
MANIFEST_CSV = HERE / "manifest.csv"
PROVENANCE = HERE / "provenance.json"
REVIEW = HERE / "HUMAN_REVIEW.md"
TEXTS = HERE / "texts.json"

# Exact established Candidate 03 decoding used in Phase 34 / 36I. The seed is
# deliberately reset before each unique text: fixed configuration, reproducible
# stochastic sequence, no per-clip tuning.
CONFIG = {
    "backend": "onnx",
    "temperature": 0.82,
    "top_k": 25,
    "top_p": 0.97,
    "repetition_penalty": 1.15,
    "speed": 1.0,
    "max_chunk_chars": 240,
    "denoise": False,
    "use_ref_codes": True,
    "numpy_seed": 34001,
}


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for block in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def audio_metrics(path: Path) -> dict:
    audio, sample_rate = sf.read(path, always_2d=True, dtype="float32")
    mono = audio.mean(axis=1)
    if not mono.size or not np.isfinite(mono).all():
        raise RuntimeError(f"Invalid waveform: {path}")
    # Same simple edge threshold for every evidence clip; it is not an acceptance
    # decision and never changes the waveform.
    active = np.flatnonzero(np.abs(mono) > 1e-4)
    leading = int(active[0]) if active.size else len(mono)
    trailing = int(len(mono) - active[-1] - 1) if active.size else len(mono)
    return {
        "sample_rate": int(sample_rate),
        "channels": int(audio.shape[1]),
        "duration_seconds": round(float(len(mono) / sample_rate), 6),
        "peak": round(float(np.max(np.abs(mono))), 8),
        "rms": round(float(np.sqrt(np.mean(np.square(mono)))), 8),
        "clipped_samples_abs_ge_0_999": int(np.count_nonzero(np.abs(mono) >= 0.999)),
        "leading_silence_seconds": round(float(leading / sample_rate), 6),
        "trailing_silence_seconds": round(float(trailing / sample_rate), 6),
        "sha256": sha256(path),
        "bytes": path.stat().st_size,
    }


def git_state() -> dict:
    commit = subprocess.run(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True,
                            capture_output=True, check=False).stdout.strip()
    status = subprocess.run(["git", "status", "--short"], cwd=ROOT, text=True,
                            capture_output=True, check=False).stdout.splitlines()
    return {"commit": commit or None, "working_tree_status_at_start": status}


def write_outputs(manifest: dict) -> None:
    MANIFEST.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    rows = manifest["clips"]
    fields = [
        "clip_id", "category", "original_text", "normalized_text", "output_file",
        "generation_status", "technical_retry_count", "qa_status", "qa_notes",
        "duration_seconds", "generation_wall_seconds", "realtime_factor",
        "sample_rate", "channels", "peak", "rms", "clipped_samples_abs_ge_0_999",
        "peak_rss_mib", "sha256",
    ]
    with MANIFEST_CSV.open("w", newline="", encoding="utf-8") as output:
        writer = csv.DictWriter(output, fieldnames=fields)
        writer.writeheader()
        for row in rows:
            writer.writerow({key: row.get(key) for key in fields})

    review_lines = ["# Phase 38A — Human review", "", "Listen in this order. Mark PASS only if the exact clip is suitable to teach the future permanent Brand Voice. Do not regenerate during this review.", ""]
    for row in rows:
        review_lines.extend([
            f"## {row['clip_id']} — {row['category']}",
            f"Text: {row['normalized_text']}",
            f"Duration: {row.get('duration_seconds', 'N/A')} s",
            f"File: `{row.get('output_file', 'NO SUCCESSFUL WAV')}`",
            "Human result: PENDING",
            "Notes: PENDING",
            "",
        ])
    REVIEW.write_text("\n".join(review_lines) + "\n", encoding="utf-8")


def main() -> None:
    sys.path.insert(0, str(ROOT))
    # Offline guard is intentionally inherited by huggingface_hub. If the local
    # cache were incomplete, load must fail instead of downloading an asset.
    os.environ.setdefault("HF_HUB_OFFLINE", "1")
    os.environ.setdefault("TRANSFORMERS_OFFLINE", "1")

    canonical_wav = ANCHOR / "qwen_source.wav"
    embedding_path, codes_path = ANCHOR / "speaker_emb.npy", ANCHOR / "reference_codes.npy"
    if not canonical_wav.is_file() or not embedding_path.is_file() or not codes_path.is_file():
        raise SystemExit("MISSING_FROZEN_CANDIDATE03_ASSET")
    embedding = np.load(embedding_path, allow_pickle=False)
    codes = np.load(codes_path, allow_pickle=False)
    if embedding.shape != (192,) or codes.shape != (87, 16):
        raise SystemExit("FROZEN_CANDIDATE03_CONDITIONING_SHAPE_INVALID")

    entries = json.loads(TEXTS.read_text(encoding="utf-8"))
    if len(entries) != 12 or {entry["clip_id"] for entry in entries} != {f"{i:02d}" for i in range(1, 13)}:
        raise SystemExit("PILOT_MUST_CONTAIN_EXACTLY_12_UNIQUE_TEXTS")
    OUT.mkdir(parents=True, exist_ok=True)
    ATTEMPTS.mkdir(parents=True, exist_ok=True)
    if MANIFEST.exists():
        manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    else:
        manifest = {"phase": "38A", "purpose": "Candidate 03 short-source corpus viability", "configuration": CONFIG, "clips": []}
    completed = {row["clip_id"]: row for row in manifest["clips"] if row.get("generation_status") == "SUCCESS"}

    import importlib.metadata
    from backend.app.tts.engine import TTSEngine
    provenance = {
        "phase": "38A",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "canonical_candidate03_directory": str(ANCHOR),
        "canonical_qwen_source": {"path": str(canonical_wav), "sha256": sha256(canonical_wav)},
        "qwen_model_identifier_from_project_evidence": "Qwen/Qwen3-TTS-12Hz-1.7B-VoiceDesign",
        "vieneu": {"version": importlib.metadata.version("vieneu"), "runtime": "CPU ONNX", "model_loader_identifier": "pnnbao-ump/VieNeu-TTS-v2"},
        "python": sys.version,
        "platform": platform.platform(),
        "fixed_parameters": CONFIG,
        "script": str(Path(__file__).resolve()),
        "offline_guard": {"HF_HUB_OFFLINE": os.environ["HF_HUB_OFFLINE"], "TRANSFORMERS_OFFLINE": os.environ["TRANSFORMERS_OFFLINE"]},
        "git": git_state(),
    }
    PROVENANCE.write_text(json.dumps(provenance, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    total_started = time.perf_counter()
    engine = TTSEngine(backend=CONFIG["backend"])
    try:
        for entry in entries:
            clip_id = entry["clip_id"]
            if clip_id in completed:
                continue
            final_path = OUT / f"{clip_id}_{entry['category']}.wav"
            if final_path.exists():
                raise RuntimeError(f"REFUSING_UNTRACKED_OVERWRITE: {final_path}")
            row = {
                **entry,
                "output_file": str(final_path.relative_to(HERE)),
                "reference_voice": "Candidate 03 frozen conditioning",
                "reference_audio_path": str(canonical_wav),
                "reference_audio_sha256": sha256(canonical_wav),
                "engine": "backend.app.tts.engine.TTSEngine",
                "engine_version": importlib.metadata.version("vieneu"),
                "model_runtime_identifier": "pnnbao-ump/VieNeu-TTS-v2 via local v3 ONNX runtime",
                "generation_parameters": CONFIG,
                "seed": CONFIG["numpy_seed"],
                "technical_retry_count": 0,
                "generation_status": "TECHNICAL_FAILURE",
                "qa_status": "PENDING_HUMAN_REVIEW",
                "qa_notes": "PENDING",
            }
            failure = None
            for attempt in (1, 2):
                attempt_path = ATTEMPTS / f"{clip_id}_{entry['category']}_attempt{attempt}.wav"
                started = time.perf_counter()
                np.random.seed(CONFIG["numpy_seed"])
                try:
                    engine.generate(
                        entry["normalized_text"],
                        voice={"speaker_emb": embedding, "codes": codes},
                        speed=CONFIG["speed"], out_path=str(attempt_path),
                        max_chunk_chars=CONFIG["max_chunk_chars"], denoise=CONFIG["denoise"],
                        use_ref_codes=CONFIG["use_ref_codes"], quality_diagnostics=True,
                        temperature=CONFIG["temperature"], top_k=CONFIG["top_k"],
                        top_p=CONFIG["top_p"], repetition_penalty=CONFIG["repetition_penalty"],
                    )
                    metrics = audio_metrics(attempt_path)
                    if metrics["duration_seconds"] <= 0 or metrics["sample_rate"] != 48000 or metrics["channels"] != 1:
                        raise RuntimeError("INVALID_SUCCESSFUL_WAV")
                    attempt_path.replace(final_path)
                    elapsed = time.perf_counter() - started
                    row.update(metrics)
                    row.update({
                        "generation_wall_seconds": round(elapsed, 6),
                        "realtime_factor": round(elapsed / metrics["duration_seconds"], 6),
                        "peak_rss_mib": round(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1024, 3),
                        "engine_diagnostics": engine.last_generation_diagnostics,
                        "technical_retry_count": attempt - 1,
                        "generation_status": "SUCCESS",
                    })
                    failure = None
                    break
                except Exception as exc:
                    failure = repr(exc)
                    row["technical_retry_count"] = attempt
                    row["technical_failure"] = failure
                    if attempt == 2:
                        break
            manifest["clips"] = [item for item in manifest["clips"] if item["clip_id"] != clip_id] + [row]
            manifest["clips"].sort(key=lambda item: item["clip_id"])
            write_outputs(manifest)
            if failure is not None:
                raise RuntimeError(f"TECHNICAL_FAILURE_AFTER_ONE_RETRY clip={clip_id}: {failure}")
    finally:
        del engine

    manifest["total_wall_seconds_this_run"] = round(time.perf_counter() - total_started, 6)
    manifest["output_disk_bytes"] = sum(path.stat().st_size for path in OUT.glob("*.wav"))
    manifest["stage_0_corpus_quality_gate"] = "PENDING_HUMAN_QA"
    write_outputs(manifest)
    print("PHASE38A_GENERATION_COMPLETE")


if __name__ == "__main__":
    main()
