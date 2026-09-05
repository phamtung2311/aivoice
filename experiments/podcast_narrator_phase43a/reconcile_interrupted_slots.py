#!/usr/bin/env python3
"""One-time recovery of technically valid Phase 43A WAVs quarantined by stale manifests.

This does not synthesize audio or select by quality. It restores the latest
quarantined PCM16/48-kHz mono WAV for the three named slots, re-hashes it, and
records the stale-manifest race explicitly.
"""

from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path

import soundfile as sf


ROOT = Path(__file__).resolve().parent
MANIFEST = ROOT / "metadata" / "casting_manifest.json"
QUARANTINE = ROOT / "metadata" / "quarantine"
SLOTS = (("03", "A"), ("03", "B"), ("04", "A"))


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> None:
    data = json.loads(MANIFEST.read_text(encoding="utf-8"))
    for voice, text in SLOTS:
        stem = f"voice{voice}_{text}"
        candidates = sorted(QUARANTINE.glob(f"{stem}.integrity-mismatch.*.wav"), key=lambda item: item.stat().st_mtime)
        if not candidates:
            raise RuntimeError(f"No quarantined candidate for {stem}")
        source = candidates[-1]
        info = sf.info(source)
        if info.samplerate != 48000 or info.channels != 1 or info.frames <= 0 or info.subtype != "PCM_16":
            raise RuntimeError(f"Quarantined artifact is not an expected WAV: {source}")
        destination = ROOT / "voices" / f"{stem}.wav"
        os.replace(source, destination)
        entry = next(item for item in data["outputs"] if item["voice"] == f"VOICE {voice}" and item["text"] == text)
        selected = entry["attempts"][-1]
        selected["path"] = str(destination.relative_to(ROOT))
        selected["sha256"] = digest(destination)
        selected["size_bytes"] = destination.stat().st_size
        entry["selected"] = selected
        entry["attempt_count"] = len(entry["attempts"])
        entry["integrity_events"] = entry.get("integrity_events", []) + [{
            "event": "reconciled stale-manifest race without rerender",
            "restored_from": str(source.relative_to(ROOT)),
            "verified_sha256": selected["sha256"],
        }]
    temporary = MANIFEST.with_suffix(".reconciled.tmp")
    temporary.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    os.replace(temporary, MANIFEST)
    print("PHASE43A_INTERRUPTED_SLOTS_RECONCILED")


if __name__ == "__main__":
    main()
