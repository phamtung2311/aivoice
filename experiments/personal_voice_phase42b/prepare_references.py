#!/usr/bin/env python3
"""Copy the three user-selected Phase42A reference regions without processing."""
from __future__ import annotations

import hashlib
import json
import shutil
from pathlib import Path

import soundfile as sf


ROOT = Path(__file__).resolve().parent
SOURCE = Path("experiments/personal_voice_phase42a/references")
REFERENCES = {
    # Roles are a small controlled spread, not claims about transcript content.
    "ref_n": {
        "source": SOURCE / "src_fb562cbea3980f3e_ref_202a40af97ff.wav",
        "role": "neutral / stable pitch contour",
        "sha256": "18563b07584d72464a9d68551e4de09f65aabff4f6db8ca0fd91d27f029e11ed",
    },
    "ref_r": {
        "source": SOURCE / "src_fb562cbea3980f3e_ref_ec062a6e0b33.wav",
        "role": "reflective / lower median pitch",
        "sha256": "e0d56087e2e94803cf938d32261a0a75a4a917a7caac308fd61267e618482876",
    },
    "ref_e": {
        "source": SOURCE / "src_fb562cbea3980f3e_ref_75c9f1c3d441.wav",
        "role": "gently emphasized / wider pitch contour",
        "sha256": "d2fa6986453f2c90f518471b0ebbde52ef2217cb2ab9bce0c5ca10c9eb207cf9",
    },
}


def digest(path: Path) -> str:
    value = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            value.update(block)
    return value.hexdigest()


def main() -> None:
    out = []
    destination_dir = ROOT / "references"
    destination_dir.mkdir(parents=True, exist_ok=True)
    for ref_id, spec in REFERENCES.items():
        source = spec["source"]
        if digest(source) != spec["sha256"]:
            raise RuntimeError(f"source hash mismatch: {source}")
        destination = destination_dir / f"{ref_id}.wav"
        if not destination.exists():
            shutil.copy2(source, destination)
        if digest(destination) != spec["sha256"]:
            raise RuntimeError(f"copy hash mismatch: {destination}")
        info = sf.info(destination)
        out.append({
            "id": ref_id, "role": spec["role"], "path": str(destination),
            "sha256": spec["sha256"], "duration_seconds": info.frames / info.samplerate,
            "sample_rate": info.samplerate, "channels": info.channels,
            "processing": "byte-identical copy; no audio processing",
        })
    metadata = ROOT / "metadata" / "references.json"
    metadata.parent.mkdir(parents=True, exist_ok=True)
    metadata.write_text(json.dumps(out, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(out, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
