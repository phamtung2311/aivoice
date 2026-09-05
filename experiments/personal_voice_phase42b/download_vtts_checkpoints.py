#!/usr/bin/env python3
"""Download the exact Phase 42B research checkpoint and verify every byte.

This intentionally does not call V-TTS's unpinned auto-download routine.
"""
from __future__ import annotations

import hashlib
from pathlib import Path

from huggingface_hub import hf_hub_download


REPO_ID = "letrggghieu/v-zeroshot-voice-cloning"
REPO_TYPE = "space"
REVISION = "83deb9f5ab591ca79840c9042dbef37dd2e5780e"
FILES = {
    "pretrained/zeroshot/G_175000.pth": {
        "size": 803_111_837,
        "sha256": "9d1c82cf10b667340e02e1a5b666c4ef020b9fce2491e3b4be3c9183fdc9bb0c",
    },
    "pretrained/hasp/pytorch_model.bin": {
        "size": 44_610_930,
        "sha256": "8f96efb20cbeeefd81fd8336d7f0155bf8902f82f9474e58ccb19d9e12345172",
    },
    "pretrained/zeroshot/config.json": {
        "size": 29_259,
        "sha256": None,
    },
}
ROOT = Path(__file__).resolve().parent / "checkpoints"


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def verify(path: Path, expected: dict) -> None:
    size = path.stat().st_size
    if size != expected["size"]:
        raise RuntimeError(f"size mismatch for {path}: {size} != {expected['size']}")
    if expected["sha256"]:
        actual = sha256(path)
        if actual != expected["sha256"]:
            raise RuntimeError(f"SHA256 mismatch for {path}: {actual}")


def main() -> None:
    for filename, expected in FILES.items():
        target = ROOT / filename
        if target.exists():
            verify(target, expected)
            print(f"verified existing {filename}")
            continue
        result = hf_hub_download(
            repo_id=REPO_ID,
            repo_type=REPO_TYPE,
            revision=REVISION,
            filename=filename,
            local_dir=ROOT,
        )
        verify(Path(result), expected)
        print(f"downloaded and verified {filename}")


if __name__ == "__main__":
    main()
