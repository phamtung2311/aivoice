#!/usr/bin/env python3
"""Verify the approved local core and Hugging Face cache without loading TTS."""
from __future__ import annotations

from common import ASSETS_PATH, HF_CACHE, MODEL_DIR, ROOT, free_disk_gb, load_json, sha256


def locate_cached_file(source: str, filename: str):
    """Locate a file only under its declared Hugging Face repository cache."""
    repo_cache = HF_CACHE / f"models--{source.replace('/', '--')}" / "snapshots"
    matches = list(repo_cache.rglob(Path(filename).name))
    return next((path for path in matches if path.is_file() and str(path).endswith(filename)), None)


from pathlib import Path


def main() -> int:
    manifest = load_json(ASSETS_PATH)
    failures = []
    hashes = {}
    for asset in manifest["core_required_assets"]:
        for filename in asset["files"]:
            path = MODEL_DIR / filename if asset["destination"] == "model" else locate_cached_file(asset["source"], filename)
            if path is None or not path.is_file():
                failures.append(f"Missing {asset['source']} :: {filename}")
                continue
            if path.stat().st_size <= 0:
                failures.append(f"Empty {path}")
                continue
            expected = asset.get("expected_bytes", {}).get(filename)
            if expected is not None and path.stat().st_size != expected:
                failures.append(f"Unexpected size for {path}: {path.stat().st_size} != {expected}")
                continue
            hashes[str(path.relative_to(ROOT))] = sha256(path)

    qwen_files = list(ROOT.rglob("qwen0.6bemo4-merge"))
    if qwen_files:
        failures.append("Qwen emotion classifier was downloaded despite SKIPPED_FOR_INITIAL_POC.")
    if free_disk_gb(ROOT) < 2:
        failures.append("Less than 2 GiB free disk remains after assets.")

    manifest["verification"] = {"hashes": hashes, "free_disk_gb": free_disk_gb(ROOT)}
    from common import atomic_json
    atomic_json(ASSETS_PATH, manifest)
    if failures:
        print("ASSET CHECK: FAIL")
        print("\n".join(f"- {failure}" for failure in failures))
        return 1
    print("ASSET CHECK: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
