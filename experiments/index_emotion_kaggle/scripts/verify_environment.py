#!/usr/bin/env python3
"""Hard-stop before any model download."""
from __future__ import annotations

import platform
import sys

from common import CONFIG_PATH, ROOT, cuda_snapshot, free_disk_gb, load_json


def main() -> int:
    config = load_json(CONFIG_PATH)
    snapshot = cuda_snapshot()
    print(f"Python: {sys.version.split()[0]}")
    print(f"Platform: {platform.platform()}")
    try:
        import torch
        print(f"PyTorch: {torch.__version__}")
        print(f"CUDA runtime: {torch.version.cuda}")
    except ImportError:
        print("PyTorch: unavailable")

    print(f"System RAM: unavailable without psutil (Kaggle UI reports it)")
    print(f"Free disk: {free_disk_gb(ROOT):.2f} GiB")
    print(f"GPU snapshot: {snapshot}")

    failures = []
    if not snapshot.get("available"):
        failures.append("CUDA GPU is unavailable.")
    elif snapshot["total_vram_bytes"] / (1024 ** 3) < config["safe_minimum_vram_gb"]:
        failures.append(f"GPU VRAM is below safe threshold ({config['safe_minimum_vram_gb']} GiB).")
    if free_disk_gb(ROOT) < config["minimum_free_disk_gb"]:
        failures.append(f"Free disk is below minimum ({config['minimum_free_disk_gb']} GiB).")

    if failures:
        print("ENVIRONMENT CHECK: FAIL")
        for failure in failures:
            print(f"- {failure}")
        return 1
    print("ENVIRONMENT CHECK: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
