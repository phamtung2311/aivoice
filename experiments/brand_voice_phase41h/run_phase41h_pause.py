#!/usr/bin/env python3
"""Assemble Phase 41H from frozen Phase 41G chunks. This script has no TTS path."""

from __future__ import annotations

import argparse
import array
import hashlib
import json
import math
import secrets
import shutil
import statistics
import subprocess
import sys
import wave
from pathlib import Path

PHASE_DIR = Path(__file__).resolve().parent
REPO_ROOT = PHASE_DIR.parents[1]
CONFIG_PATH = PHASE_DIR / "config.json"
PLAN_PATH = PHASE_DIR / "pause_plan.json"


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def read_json(path: Path) -> dict:
    with path.open("r", encoding="utf-8") as stream:
        return json.load(stream)


def repo_path(relative: str) -> Path:
    return REPO_ROOT / relative


def wav_info(path: Path) -> dict:
    with wave.open(str(path), "rb") as wav:
        params = wav.getparams()
        frames = wav.readframes(params.nframes)
    samples = array.array("h")
    samples.frombytes(frames)
    peak = max((abs(value) for value in samples), default=0)
    clipped = sum(1 for value in samples if value in (-32768, 32767))
    return {
        "channels": params.nchannels,
        "sample_width_bytes": params.sampwidth,
        "sample_rate": params.framerate,
        "frames": params.nframes,
        "duration_seconds": params.nframes / params.framerate,
        "peak_pcm16": peak,
        "peak_dbfs": 20 * math.log10(peak / 32768) if peak else None,
        "clipped_samples": clipped,
        "sha256": sha256(path),
    }


def preflight(config: dict) -> tuple[list[Path], dict]:
    source = config["source"]
    manifest_path = repo_path(source["manifest"])
    semantic_path = repo_path(source["semantic_plan"])
    if sha256(manifest_path) != source["manifest_sha256"]:
        raise RuntimeError("Phase41G manifest hash mismatch")
    if sha256(semantic_path) != source["semantic_plan_sha256"]:
        raise RuntimeError("Phase41G semantic-plan hash mismatch")
    manifest = read_json(manifest_path)
    if manifest["chunk_count"] != 55:
        raise RuntimeError("Expected exactly 55 Phase41G chunks")
    chunks = []
    for index in range(55):
        path = repo_path(source["chunk_directory"]) / f"chunk_{index:03d}.wav"
        expected = manifest["chunks"][str(index)]["wav_sha256"]
        actual = sha256(path)
        if actual != expected:
            raise RuntimeError(f"Chunk {index:03d} hash mismatch: {actual} != {expected}")
        info = wav_info(path)
        expected_format = (source["channels"], source["sample_width_bytes"], source["sample_rate"])
        actual_format = (info["channels"], info["sample_width_bytes"], info["sample_rate"])
        if actual_format != expected_format:
            raise RuntimeError(f"Chunk {index:03d} WAV format mismatch")
        chunks.append(path)
    return chunks, manifest


def assemble(chunks: list[Path], additions: dict[str, float], output: Path, config: dict) -> None:
    source = config["source"]
    output.parent.mkdir(parents=True, exist_ok=True)
    with wave.open(str(output), "wb") as dst:
        dst.setnchannels(source["channels"])
        dst.setsampwidth(source["sample_width_bytes"])
        dst.setframerate(source["sample_rate"])
        for index, path in enumerate(chunks):
            with wave.open(str(path), "rb") as src:
                dst.writeframes(src.readframes(src.getnframes()))
            seconds = float(additions.get(str(index), 0.0))
            silence_frames = round(seconds * source["sample_rate"])
            if silence_frames:
                dst.writeframes(b"\x00" * silence_frames * source["sample_width_bytes"] * source["channels"])


def boundary_additions(plan: dict, variant: dict) -> dict[str, float]:
    """Map each left chunk to its direct explicit assembly pause."""
    schema = plan["schema"]["boundary_record"]
    additions = {}
    for row in plan["boundaries"]:
        record = dict(zip(schema, row))
        seconds = float(variant["explicit_additions_seconds"][record["policy_boundary_type"]])
        if seconds > 0:
            additions[str(record["left_chunk"])] = seconds
    return additions


def run_atempo(source: Path, output: Path) -> None:
    command = [
        "ffmpeg", "-hide_banner", "-loglevel", "error", "-y",
        "-i", str(source), "-map_metadata", "-1", "-af", "atempo=0.98",
        "-c:a", "pcm_s16le", "-ar", "48000", "-ac", "1", str(output),
    ]
    subprocess.run(command, check=True)


def gap_metrics(plan: dict, variant: dict) -> dict:
    schema = plan["schema"]["boundary_record"]
    records = [dict(zip(schema, row)) for row in plan["boundaries"]]
    additions = boundary_additions(plan, variant)
    groups = {"semantic": [], "thought_transition": [], "paragraph": []}
    for record in records:
        effective = record["existing_gap_seconds"] + float(additions.get(str(record["left_chunk"]), 0.0))
        if record["source_boundary_type"] == "semantic_thought_boundary":
            groups["semantic"].append(effective)
        if record["source_boundary_type"] == "thought_transition":
            groups["thought_transition"].append(effective)
        if record["policy_boundary_type"] == "paragraph_transition":
            groups["paragraph"].append(effective)
    return {
        key: {
            "mean_seconds": statistics.mean(values) if values else None,
            "median_seconds": statistics.median(values) if values else None,
        }
        for key, values in groups.items()
    }


def make_blind(outputs: dict[str, Path]) -> dict:
    blind_dir = PHASE_DIR / "blind"
    blind_dir.mkdir(parents=True, exist_ok=True)
    mapping_path = PHASE_DIR / "blind_mapping.json"
    names = list(outputs)
    if mapping_path.exists():
        mapping = read_json(mapping_path)
        if sorted(mapping.values()) != sorted(names):
            raise RuntimeError("Existing blind mapping is incompatible; refusing to rerandomize")
    else:
        shuffled = names[:]
        secrets.SystemRandom().shuffle(shuffled)
        mapping = {f"{index:02d}.wav": name for index, name in enumerate(shuffled, 1)}
        with mapping_path.open("x", encoding="utf-8") as stream:
            json.dump(mapping, stream, ensure_ascii=False, indent=2, sort_keys=True)
            stream.write("\n")
    for blind_name, variant in mapping.items():
        shutil.copyfile(outputs[variant], blind_dir / blind_name)
    shutil.copyfile(PHASE_DIR / "HUMAN_REVIEW.md", blind_dir / "HUMAN_REVIEW.md")
    return mapping


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--execute", action="store_true", help="assemble and run FFmpeg after static preflight")
    args = parser.parse_args()
    config = read_json(CONFIG_PATH)
    plan = read_json(PLAN_PATH)
    chunks, source_manifest = preflight(config)
    if not args.execute:
        print("Static integrity preflight PASS. No audio written. Re-run with --execute externally.")
        return 0
    if not shutil.which("ffmpeg"):
        raise RuntimeError("ffmpeg is not available")

    audio_dir = PHASE_DIR / "audio"
    pretempo_dir = audio_dir / "pretempo"
    outputs = {}
    results = {}
    filenames = {
        "v0_current": "v0_current.wav",
        "v1_light": "v1_light.wav",
        "v2_natural": "v2_natural.wav",
        "v3_spacious": "v3_spacious.wav",
    }
    for variant_name, filename in filenames.items():
        variant = plan["variants"][variant_name]
        additions = boundary_additions(plan, variant)
        calculated_total = round(sum(additions.values()), 9)
        if not math.isclose(calculated_total, variant["total_added_seconds"], abs_tol=1e-9):
            raise RuntimeError(f"{variant_name} explicit-pause total does not match pause plan")
        pretempo = pretempo_dir / filename
        final = audio_dir / filename
        assemble(chunks, additions, pretempo, config)
        if variant_name == "v0_current" and sha256(pretempo) != config["source"]["original_wav_sha256"]:
            raise RuntimeError("V0 pre-tempo assembly does not reproduce Phase41G original")
        run_atempo(pretempo, final)
        outputs[variant_name] = final
        results[variant_name] = {
            "path": str(final.relative_to(REPO_ROOT)),
            "pretempo": wav_info(pretempo),
            "final": wav_info(final),
            "total_added_seconds": variant["total_added_seconds"],
            "average_added_per_boundary_seconds": variant["average_added_per_boundary_seconds"],
            "added_by_class_seconds": variant["added_by_class_seconds"],
            "boundaries_receiving_pause": variant["boundaries_receiving_pause"],
            "effective_gap_metrics": gap_metrics(plan, variant),
        }

    mapping = make_blind(outputs)
    manifest = {
        "phase": "41H",
        "status": "pending_blind_human_qa",
        "no_tts": True,
        "source_chunk_count": 55,
        "source_chunk_integrity": "PASS",
        "source_chunk_hashes": {str(i): source_manifest["chunks"][str(i)]["wav_sha256"] for i in range(55)},
        "tempo_filter": "atempo=0.98 once after complete assembly",
        "variants": results,
        "blind_package_created": True,
        "blind_mapping_path": str((PHASE_DIR / "blind_mapping.json").relative_to(REPO_ROOT)),
        "blind_mapping_sha256": sha256(PHASE_DIR / "blind_mapping.json"),
        "mapping_not_embedded_in_listener_files": True,
    }
    with (PHASE_DIR / "manifest.json").open("w", encoding="utf-8") as stream:
        json.dump(manifest, stream, ensure_ascii=False, indent=2, sort_keys=True)
        stream.write("\n")
    print("Phase41H assembly complete; blind mapping saved but not printed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
