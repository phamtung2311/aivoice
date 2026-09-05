#!/usr/bin/env python3
"""Freeze the Phase 33B blind Candidate 03 identity anchor without altering it."""
from __future__ import annotations

import hashlib
import json
import shutil
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
SOURCE = ROOT / "experiments/brand_speaker_phase33b"
ANCHOR = HERE / "baseline_anchor" / "BRAND_CANDIDATE_03_BASELINE"


def digest(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def main() -> int:
    mapping = json.loads((SOURCE / "private_mapping.json").read_text(encoding="utf-8"))
    if mapping.get("Candidate 03.wav") != "D":
        raise SystemExit("CANDIDATE_03_MAPPING_INTEGRITY_FAILED")
    files = {
        "qwen_source.wav": SOURCE / "sources/source_D.wav",
        "speaker_emb.npy": SOURCE / "conditioning/speaker_emb_D.npy",
        "reference_codes.npy": SOURCE / "conditioning/reference_codes_D.npy",
        "phase33b_vietnamese_raw.wav": SOURCE / "raw_vietnamese/vietnamese_D.wav",
    }
    if ANCHOR.exists() and any(ANCHOR.iterdir()):
        manifest = ANCHOR / "manifest.json"
        if not manifest.is_file():
            raise SystemExit("ANCHOR_EXISTS_WITHOUT_MANIFEST")
        recorded = json.loads(manifest.read_text(encoding="utf-8"))
        if all((ANCHOR / name).is_file() and digest(ANCHOR / name) == item["sha256"] for name, item in recorded["files"].items()):
            print("BASELINE_ALREADY_FROZEN")
            return 0
        raise SystemExit("ANCHOR_IMMUTABILITY_FAILED")
    ANCHOR.mkdir(parents=True, exist_ok=False)
    for name, source in files.items():
        if not source.is_file():
            raise SystemExit(f"MISSING_SOURCE_ARTIFACT: {source}")
        shutil.copy2(source, ANCHOR / name)
    instruction = (
        "A mature adult male voice with a medium-low register, dark-neutral back resonance, "
        "a controlled matte texture with restrained natural grain, and a firm broad vocal body. "
        "It must be clearly unlike a smooth bass narrator: neutral delivery, no forced rasp, no accent, no acting."
    )
    config = {
        "phase33b_identity": "D",
        "blind_label": "Candidate 03.wav",
        "concept": "Dark / Textured",
        "qwen_voice_design_instruction": instruction,
        "qwen_source_text": "A quiet evening settles over the city. I speak clearly, naturally, and without rushing.",
        "vieneu_generation": {"temperature": 0.8, "top_k": 25, "top_p": 0.95, "repetition_penalty": 1.2, "speed": 1.0, "max_chunk_chars": 240, "denoise": False, "use_ref_codes": True, "seed": 33117},
    }
    (ANCHOR / "generation_config.json").write_text(json.dumps(config, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    manifest = {"name": "BRAND_CANDIDATE_03_BASELINE", "immutable": True, "files": {name: {"sha256": digest(ANCHOR / name), "size_bytes": (ANCHOR / name).stat().st_size} for name in files}}
    (ANCHOR / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    print("BRAND_CANDIDATE_03_BASELINE_FROZEN")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
