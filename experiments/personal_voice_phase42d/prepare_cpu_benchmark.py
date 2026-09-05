#!/usr/bin/env python3
"""Prepare, but do not interpret, a reproducible tiny CPU RVC training run.

This selects only slices for which all four Phase 42D extraction products exist.
It writes the RVC runtime configuration beneath the cloned upstream source so that
the upstream trainer's fixed ``./logs/<experiment>`` convention is respected.
"""

from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parent
FEATURES = ROOT / "features" / "rvc_prep"
RVC = ROOT / "rvc_source"
EXPERIMENT = RVC / "logs" / "phase42d_cpu_benchmark"
LIMIT = 16


def feature_stems(directory: Path) -> set[str]:
    return {item.stem for item in directory.glob("*.npy")}


def f0_stems(directory: Path) -> set[str]:
    """RVC's F0 extractor preserves the input's ``.wav`` in its .npy name."""
    suffix = ".wav.npy"
    return {
        item.name[: -len(suffix)]
        for item in directory.glob("*.wav.npy")
        if item.name.endswith(suffix)
    }


def main() -> None:
    wav_dir = FEATURES / "0_gt_wavs"
    feature_dir = FEATURES / "3_feature768"
    f0_dir = FEATURES / "2a_f0"
    f0nsf_dir = FEATURES / "2b-f0nsf"
    valid = sorted(
        {item.stem for item in wav_dir.glob("*.wav")}
        & feature_stems(feature_dir)
        & f0_stems(f0_dir)
        & f0_stems(f0nsf_dir)
    )
    if len(valid) < LIMIT:
        raise RuntimeError(f"Need {LIMIT} fully extracted slices; found {len(valid)}")

    EXPERIMENT.mkdir(parents=True, exist_ok=True)
    config = json.loads((RVC / "configs" / "v1" / "40k.json").read_text())
    config["train"]["epochs"] = 1
    config["train"]["batch_size"] = 1
    config["train"]["log_interval"] = 1
    (EXPERIMENT / "config.json").write_text(json.dumps(config, indent=2) + "\n")

    lines = [
        "|".join(
            [
                str(wav_dir / f"{stem}.wav"),
                str(feature_dir / f"{stem}.npy"),
                str(f0_dir / f"{stem}.wav.npy"),
                str(f0nsf_dir / f"{stem}.wav.npy"),
                "0",
            ]
        )
        for stem in valid[:LIMIT]
    ]
    (EXPERIMENT / "filelist.txt").write_text("\n".join(lines) + "\n")
    (EXPERIMENT / "benchmark_manifest.json").write_text(
        json.dumps(
            {
                "purpose": "CPU feasibility measurement only; not a quality render",
                "upstream_rvc_commit": "81eed5e8f68b6bed1789f682fe78cdd324495afc",
                "all_valid_slices": len(valid),
                "benchmark_slices": len(lines),
                "sample_rate": 40000,
                "version": "v2",
                "f0": "pm (existing Phase 42D artifacts)",
                "pretrained_models": "none; initialization benchmark only",
            },
            indent=2,
        )
        + "\n"
    )
    print(f"all_valid_slices={len(valid)}")
    print(f"benchmark_slices={len(lines)}")
    print(EXPERIMENT / "filelist.txt")


if __name__ == "__main__":
    main()
