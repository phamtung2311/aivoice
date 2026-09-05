#!/usr/bin/env python3
"""Run the single, raw Phase 37C Candidate 04 VoxCPM2 audition.

This program is prepared only.  It must be run once on an approved temporary
CUDA machine after the exact source and checkpoint revisions in ../provenance.json
have been obtained.  It intentionally has no retry or warm-up generation.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import platform
import resource
import sys
import time
from pathlib import Path

import numpy as np
import soundfile as sf
import torch
from voxcpm import VoxCPM


PACKAGE_DIR = Path(__file__).resolve().parents[1]


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as file_obj:
        for block in iter(lambda: file_obj.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def load_json(name: str) -> dict:
    return json.loads((PACKAGE_DIR / name).read_text(encoding="utf-8"))


def validate_model(model_dir: Path, provenance: dict) -> None:
    required = provenance["official_model"]["required_files"]
    for filename, expected in required.items():
        actual_path = model_dir / filename
        if not actual_path.is_file():
            raise FileNotFoundError(f"Missing pinned model asset: {actual_path}")
        actual_size = actual_path.stat().st_size
        if actual_size != expected["bytes"]:
            raise RuntimeError(
                f"Size mismatch for {filename}: {actual_size} != {expected['bytes']}"
            )
        expected_hash = expected.get("sha256")
        if expected_hash and sha256_file(actual_path) != expected_hash:
            raise RuntimeError(f"SHA-256 mismatch for {filename}")


def audio_metrics(waveform: np.ndarray, sample_rate: int) -> dict:
    mono = np.asarray(waveform, dtype=np.float64).reshape(-1)
    peak = float(np.max(np.abs(mono))) if mono.size else 0.0
    rms = float(np.sqrt(np.mean(np.square(mono)))) if mono.size else 0.0
    return {
        "sample_rate_hz": int(sample_rate),
        "channels": 1,
        "duration_seconds": float(mono.size / sample_rate),
        "peak": peak,
        "rms": rms,
        "clipped_sample_count_abs_ge_1": int(np.count_nonzero(np.abs(mono) >= 1.0)),
        "dtype_from_model": str(np.asarray(waveform).dtype),
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--model-dir", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()

    config = load_json("config.json")
    provenance = load_json("provenance.json")
    target = (PACKAGE_DIR / config["target_file"]).read_text(encoding="utf-8").strip()
    voice_design = (PACKAGE_DIR / config["voice_design_file"]).read_text(encoding="utf-8").strip()
    if not target or not voice_design:
        raise RuntimeError("Target text or Voice Design instruction is empty")
    if not torch.cuda.is_available():
        raise RuntimeError("CUDA is required for this approved temporary-GPU audition")
    if torch.cuda.device_count() < 1:
        raise RuntimeError("Unable to resolve cuda:0")

    model_dir = args.model_dir.resolve()
    validate_model(model_dir, provenance)
    args.output_dir.mkdir(parents=True, exist_ok=True)
    output_wav = args.output_dir / config["output_filename"]
    metrics_path = args.output_dir / config["metrics_filename"]
    if output_wav.exists() or metrics_path.exists():
        raise FileExistsError(
            "Refusing to overwrite a prior Phase 37C result; this package permits one run."
        )

    design_text = f"({voice_design}){target}"
    torch.cuda.reset_peak_memory_stats(0)
    load_start = time.perf_counter()
    model = VoxCPM.from_pretrained(
        str(model_dir),
        local_files_only=True,
        load_denoiser=False,
        optimize=False,
        device=config["device"],
    )
    load_seconds = time.perf_counter() - load_start

    generate_start = time.perf_counter()
    waveform = model.generate(
        text=design_text,
        cfg_value=config["cfg_value"],
        inference_timesteps=config["inference_timesteps"],
        normalize=config["normalize"],
        denoise=config["denoise"],
        retry_badcase=config["retry_badcase"],
        retry_badcase_max_times=config["retry_badcase_max_times"],
        seed=config["seed"],
    )
    generation_seconds = time.perf_counter() - generate_start
    sample_rate = int(model.tts_model.sample_rate)
    sf.write(output_wav, waveform, sample_rate, subtype=config["output_subtype"])

    metrics = {
        "phase": config["phase"],
        "source_commit": config["source_commit"],
        "checkpoint_repository": config["checkpoint_repository"],
        "checkpoint_revision": config["checkpoint_revision"],
        "validated_model_assets": provenance["official_model"]["required_files"],
        "target_text": target,
        "voice_design_instruction": voice_design,
        "exact_model_text": design_text,
        "generation_config": config,
        "runtime": {
            "device": config["device"],
            "gpu_name": torch.cuda.get_device_name(0),
            "gpu_total_vram_bytes": int(torch.cuda.get_device_properties(0).total_memory),
            "python": sys.version,
            "platform": platform.platform(),
            "torch": torch.__version__,
            "torch_cuda": torch.version.cuda,
            "model_load_seconds": load_seconds,
            "generation_seconds": generation_seconds,
            "peak_gpu_allocated_bytes": int(torch.cuda.max_memory_allocated(0)),
            "peak_gpu_reserved_bytes": int(torch.cuda.max_memory_reserved(0)),
            "peak_process_rss_kib": int(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss),
        },
        "audio": audio_metrics(waveform, sample_rate),
        "output": {
            "path": str(output_wav),
            "sha256": sha256_file(output_wav),
            "bytes": output_wav.stat().st_size,
        },
    }
    metrics["runtime"]["rtf"] = (
        generation_seconds / metrics["audio"]["duration_seconds"]
        if metrics["audio"]["duration_seconds"] > 0
        else None
    )
    metrics_path.write_text(json.dumps(metrics, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(output_wav)
    print(metrics_path)


if __name__ == "__main__":
    main()
