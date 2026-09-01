#!/usr/bin/env python3
"""Download only the audited asset subset into this isolated experiment.

Run only after verify_environment.py passes. No model is downloaded on import.
"""
from __future__ import annotations

import argparse
from pathlib import Path

from common import ASSETS_PATH, HF_CACHE, MODEL_DIR, ROOT, atomic_json, configure_hf_environment, free_disk_gb, load_json


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--confirm-download", action="store_true", help="Required explicit acknowledgement before network download.")
    args = parser.parse_args()
    if not args.confirm_download:
        print("Refusing download. Re-run with --confirm-download only after environment review.")
        return 2

    manifest = load_json(ASSETS_PATH)
    if free_disk_gb(ROOT) < 15:
        print("DOWNLOAD CHECK: FAIL — less than 15 GiB free disk.")
        return 1

    from huggingface_hub import hf_hub_download
    configure_hf_environment()
    MODEL_DIR.mkdir(parents=True, exist_ok=True)
    print("Downloading only approved assets. Qwen text-emotion files are intentionally excluded.")

    actual = []
    for asset in manifest["core_required_assets"]:
        destination = MODEL_DIR if asset["destination"] == "model" else None
        for filename in asset["files"]:
            kwargs = {"repo_id": asset["source"], "filename": filename, "revision": asset["revision"], "resume_download": True}
            if destination is not None:
                kwargs.update({"local_dir": str(destination), "local_dir_use_symlinks": False})
            else:
                kwargs.update({"cache_dir": str(HF_CACHE)})
            path = hf_hub_download(**kwargs)
            actual.append({"source": asset["source"], "revision": asset["revision"], "file": filename, "resolved_path": str(path)})
            print(f"OK {asset['source']} :: {filename}")

    manifest["actual_download_record"] = actual
    atomic_json(ASSETS_PATH, manifest)
    print("DOWNLOAD CHECK: PASS — run scripts/verify_assets.py next.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
