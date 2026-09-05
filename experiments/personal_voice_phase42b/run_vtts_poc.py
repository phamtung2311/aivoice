#!/usr/bin/env python3
"""Sequential, raw CPU V-TTS Phase42B renderer. Never touches production TTS."""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import resource
import subprocess
import time

import numpy as np
import soundfile as sf


ROOT = Path(__file__).resolve().parent
CHECKPOINT_ROOT = ROOT / "checkpoints"
TEST_SET = ROOT.parent / "personal_voice_phase42a" / "test_set.json"
SOURCE_COMMIT = "e22eef3267869375e40a096b376cde94aa41e610"
SPACE_COMMIT = "83deb9f5ab591ca79840c9042dbef37dd2e5780e"


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def mem_available_bytes() -> int:
    for line in Path("/proc/meminfo").read_text().splitlines():
        if line.startswith("MemAvailable:"):
            return int(line.split()[1]) * 1024
    return 0


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--reference", required=True, type=Path)
    parser.add_argument("--reference-id", required=True)
    parser.add_argument("--test-id", required=True)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--threads", type=int, default=4)
    args = parser.parse_args()
    # V-TTS internally requires a cwd switch to find H/ASP; never let that
    # change the caller's reference/output resolution.
    args.reference = args.reference.resolve()
    args.output = args.output.resolve()

    available = mem_available_bytes()
    if available < 5 * 1024**3:
        raise RuntimeError(f"RAM guard: only {available / 1024**3:.2f} GiB MemAvailable; need >=5 GiB")
    ref_info = sf.info(args.reference)
    ref_duration = ref_info.frames / ref_info.samplerate
    if not 3.0 <= ref_duration <= 10.0:
        raise ValueError(f"reference must be 3–10 s, got {ref_duration:.3f}s")
    tests = {item["id"]: item for item in json.loads(TEST_SET.read_text(encoding="utf-8"))["tests"]}
    test = tests.get(args.test_id)
    if test is None:
        raise KeyError(args.test_id)
    if args.output.exists():
        raise FileExistsError(f"refusing to overwrite {args.output}")
    args.output.parent.mkdir(parents=True, exist_ok=True)

    # V-TTS SpeakerEncoder resolves H/ASP from cwd/pretrained/hasp.
    os.chdir(CHECKPOINT_ROOT)
    os.environ.setdefault("OMP_NUM_THREADS", str(args.threads))
    os.environ.setdefault("MKL_NUM_THREADS", str(args.threads))
    import torch
    torch.set_num_threads(args.threads)
    try:
        torch.set_num_interop_threads(1)
    except RuntimeError:
        pass
    from v_tts import ZeroShotTTS

    started = time.monotonic()
    engine = ZeroShotTTS(
        checkpoint_path=str(CHECKPOINT_ROOT / "pretrained/zeroshot/G_175000.pth"),
        config_path=str(CHECKPOINT_ROOT / "pretrained/zeroshot/config.json"),
        device="cpu",
    )
    loaded_seconds = time.monotonic() - started
    generated_start = time.monotonic()
    engine.clone_voice(test["text"], str(args.reference), str(args.output))
    generated_seconds = time.monotonic() - generated_start
    info = sf.info(args.output)
    duration = info.frames / info.samplerate
    wav, _ = sf.read(args.output, dtype="float32")
    peak = float(np.max(np.abs(wav))) if len(wav) else 0.0
    manifest = {
        "phase": "42B", "engine": "V-TTS", "mode": "raw_cpu_only",
        "research_only": True, "production_engine_changed": False,
        "source_commit": SOURCE_COMMIT, "space_commit": SPACE_COMMIT,
        "reference_id": args.reference_id, "reference_path": str(args.reference),
        "reference_sha256": sha256(args.reference), "reference_duration_seconds": ref_duration,
        "test_id": args.test_id, "text": test["text"],
        "text_sha256": hashlib.sha256(test["text"].encode()).hexdigest(),
        "output_path": str(args.output), "output_sha256": sha256(args.output),
        "sample_rate": info.samplerate, "duration_seconds": duration,
        "peak": peak, "clipped": peak >= 0.999,
        "load_seconds": loaded_seconds, "generation_seconds": generated_seconds,
        "rtf": generated_seconds / duration if duration else None,
        "peak_rss_mib": resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1024,
        "mem_available_before_gib": available / 1024**3,
        "threads": args.threads, "cuda_available": torch.cuda.is_available(),
        "checkpoint_sha256": sha256(CHECKPOINT_ROOT / "pretrained/zeroshot/G_175000.pth"),
        "speaker_encoder_sha256": sha256(CHECKPOINT_ROOT / "pretrained/hasp/pytorch_model.bin"),
    }
    metadata_path = ROOT / "metadata" / f"{args.output.stem}.json"
    metadata_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(manifest, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
