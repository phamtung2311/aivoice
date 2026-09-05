#!/usr/bin/env python3
"""Run the one allowed Phase 38C OpenVoice conversion after source approval."""

from __future__ import annotations

import hashlib
import json
import platform
import resource
import subprocess
import sys
import time
from datetime import datetime, timezone
from importlib.metadata import version
from pathlib import Path

import librosa
import numpy as np
import soundfile as sf
import torch
from openvoice.api import ToneColorConverter


ROOT = Path(__file__).resolve().parent
REPO_ROOT = ROOT.parents[1]
OPENVOICE_REPO = ROOT / "src" / "OpenVoice"
CONFIG = ROOT / "checkpoints" / "openvoice_v2" / "converter" / "config.json"
CHECKPOINT = ROOT / "checkpoints" / "openvoice_v2" / "converter" / "checkpoint.pth"
SOURCE = ROOT / "audio" / "source_vietnamese.wav"
SOURCE_APPROVAL = ROOT / "provenance" / "SOURCE_APPROVED"
TARGET = REPO_ROOT / "experiments" / "brand_speaker_phase33c" / "baseline_anchor" / "BRAND_CANDIDATE_03_BASELINE" / "qwen_source.wav"
OUTPUT = ROOT / "audio" / "candidate03_openvoice.wav"
METRICS = ROOT / "metrics" / "metrics.json"
PROVENANCE = ROOT / "provenance" / "provenance.json"

EXPECTED_REPO_COMMIT = "74a1d147b17a8c3092dd5430504bd83ef6c7eb23"
EXPECTED_TARGET_SHA256 = "3f3f5c6771ed437297ffdd89c5ea2aebd2d34dd531235ad5dd12e93bf18b5f06"
EXPECTED_CHECKPOINT_SHA256 = "9652c27e92b6b2a91632590ac9962ef7ae2b712e5c5b7f4c34ec55ee2b37ab9e"
EXPECTED_CONFIG_SHA256 = "9dfff60350b8c63f2c664efd92a61b2516efb22671466960f0e5dfebd881fa47"
CHECKPOINT_REVISION = "f36e7edfe1684461a8343844af60babc2efbb727"


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def audio_metrics(path: Path) -> dict[str, float | int | str]:
    data, sample_rate = sf.read(path, always_2d=True, dtype="float32")
    mono = data.mean(axis=1, dtype=np.float64)
    return {
        "path": str(path.relative_to(ROOT)),
        "sha256": sha256(path),
        "size_bytes": path.stat().st_size,
        "duration_seconds": float(len(data) / sample_rate),
        "sample_rate_hz": int(sample_rate),
        "channels": int(data.shape[1]),
        "peak_abs": float(np.max(np.abs(data))),
        "rms": float(np.sqrt(np.mean(np.square(mono)))),
        "clipped_samples_abs_ge_0_999": int(np.count_nonzero(np.abs(data) >= 0.999)),
    }


def main() -> None:
    if OUTPUT.exists() or METRICS.exists() or PROVENANCE.exists():
        raise FileExistsError("Phase 38C conversion artifacts already exist; no overwrite allowed")
    if not SOURCE.is_file():
        raise FileNotFoundError("Approved source WAV is missing")
    if not SOURCE_APPROVAL.is_file() or SOURCE_APPROVAL.read_text(encoding="utf-8").strip() != "PASS":
        raise RuntimeError("Human source gate has not been recorded as PASS")

    repo_commit = subprocess.check_output(
        ["git", "-C", str(OPENVOICE_REPO), "rev-parse", "HEAD"], text=True
    ).strip()
    checks = {
        "repo_commit": (repo_commit, EXPECTED_REPO_COMMIT),
        "target_sha256": (sha256(TARGET), EXPECTED_TARGET_SHA256),
        "checkpoint_sha256": (sha256(CHECKPOINT), EXPECTED_CHECKPOINT_SHA256),
        "config_sha256": (sha256(CONFIG), EXPECTED_CONFIG_SHA256),
    }
    for name, (actual, expected) in checks.items():
        if actual != expected:
            raise RuntimeError(f"{name} mismatch: {actual} != {expected}")

    source_before = audio_metrics(SOURCE)
    started_utc = datetime.now(timezone.utc).isoformat()
    load_started = time.perf_counter()
    # Keep the pinned OpenVoice V2 constructor default, including watermarking.
    # There is no watermark on/off comparison in this experiment.
    converter = ToneColorConverter(str(CONFIG), device="cpu")
    converter.load_ckpt(str(CHECKPOINT))
    load_seconds = time.perf_counter() - load_started

    embedding_started = time.perf_counter()
    source_se = converter.extract_se(str(SOURCE))
    source_embedding_seconds = time.perf_counter() - embedding_started
    embedding_started = time.perf_counter()
    target_se = converter.extract_se(str(TARGET))
    target_embedding_seconds = time.perf_counter() - embedding_started

    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    conversion_started = time.perf_counter()
    converter.convert(
        audio_src_path=str(SOURCE),
        src_se=source_se,
        tgt_se=target_se,
        output_path=str(OUTPUT),
        tau=0.3,
        message="default",
    )
    conversion_seconds = time.perf_counter() - conversion_started
    converted = audio_metrics(OUTPUT)

    METRICS.parent.mkdir(parents=True, exist_ok=True)
    PROVENANCE.parent.mkdir(parents=True, exist_ok=True)
    metrics = {
        "phase": "38C",
        "created_utc": started_utc,
        "source": source_before,
        "converted": converted,
        "openvoice_model_load_seconds": load_seconds,
        "source_embedding_seconds": source_embedding_seconds,
        "target_embedding_seconds": target_embedding_seconds,
        "conversion_seconds": conversion_seconds,
        "conversion_rtf": conversion_seconds / converted["duration_seconds"],
        "peak_rss_mib": resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1024.0,
    }
    provenance = {
        "phase": "38C",
        "research_assets_only": True,
        "downstream_corpus_rights": "UNRESOLVED",
        "source_text": (ROOT / "source_text.txt").read_text(encoding="utf-8").strip(),
        "source_preset_id": "Minh Đức",
        "vieneu_version": "3.3.0",
        "candidate03_path": str(TARGET.relative_to(REPO_ROOT)),
        "candidate03_sha256": EXPECTED_TARGET_SHA256,
        "candidate03_transcript": "A quiet evening settles over the city. I speak clearly, naturally, and without rushing.",
        "openvoice_repo_commit": repo_commit,
        "openvoice_checkpoint_revision": CHECKPOINT_REVISION,
        "openvoice_checkpoint_sha256": EXPECTED_CHECKPOINT_SHA256,
        "openvoice_config_sha256": EXPECTED_CONFIG_SHA256,
        "device": "cpu",
        "torch_version": torch.__version__,
        "torch_cuda_version": torch.version.cuda,
        "torch_cuda_available": torch.cuda.is_available(),
        "python": sys.version,
        "platform": platform.platform(),
        "conversion_settings": {
            "tau": 0.3,
            "message": "default",
            "enable_watermark": True,
            "vad": False,
            "denoiser": False,
            "post_processing": False,
        },
        "output_sha256": converted["sha256"],
    }
    METRICS.write_text(json.dumps(metrics, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    PROVENANCE.write_text(json.dumps(provenance, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"metrics": metrics, "provenance": provenance}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
