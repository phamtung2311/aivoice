#!/usr/bin/env python3
"""Preserve the two Phase 30K finalists without new audio generation."""
from __future__ import annotations

import hashlib
import json
import shutil
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent
GENERATION = ROOT / "generation_3"
KEEPERS = ROOT.parent / "keepers"
MAPPING = json.loads((GENERATION / "private_mapping.json").read_text(encoding="utf-8"))
PROMPTS = json.loads((GENERATION / "prompts.json").read_text(encoding="utf-8"))
SOURCE_MEASUREMENTS = json.loads((GENERATION / "measurements" / "source_generation.json").read_text(encoding="utf-8"))
VIENEU_MEASUREMENTS = json.loads((GENERATION / "measurements" / "vieneu_generation.json").read_text(encoding="utf-8"))


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def validate(manifest: dict) -> None:
    for keeper in manifest["keepers"]:
        for artifact in keeper["files"].values():
            path = Path(artifact["path"])
            if not path.is_file() or path.stat().st_size != artifact["size_bytes"] or sha256(path) != artifact["sha256"]:
                raise RuntimeError(f"KEEPER_INTEGRITY_FAILED: {path}")


def copy_once(source: Path, target: Path) -> None:
    if target.exists():
        if not target.is_file() or sha256(source) != sha256(target):
            raise RuntimeError(f"refusing to overwrite keeper artifact: {target}")
        return
    shutil.copy2(source, target)


def write_once(path: Path, value: object) -> None:
    text = json.dumps(value, ensure_ascii=False, indent=2) + "\n"
    if path.exists():
        if path.read_text(encoding="utf-8") != text:
            raise RuntimeError(f"refusing to overwrite keeper artifact: {path}")
        return
    path.write_text(text, encoding="utf-8")


def files(directory: Path) -> dict:
    return {item.name: {"path": str(item), "size_bytes": item.stat().st_size, "sha256": sha256(item)} for item in sorted(directory.iterdir()) if item.is_file()}


def record(records: list[dict], identity: str) -> dict:
    return next(item for item in records if item["identity"] == identity)


def main() -> int:
    manifest_path = KEEPERS / "KEEPERS_MANIFEST.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    validate(manifest)
    if MAPPING != {"01": "CONTROL", "02": "K-C", "03": "K-B", "04": "K-A"}:
        raise RuntimeError("unexpected completed Phase 30K mapping")
    if any(item["keeper_id"] in {"phase30k_01", "phase30k_04"} for item in manifest["keepers"]):
        raise RuntimeError("finalist keeper already exists; refusing overwrite")
    timestamp = datetime.now(timezone.utc).isoformat()
    new_entries = []

    control = KEEPERS / "g2_06"
    control_dir = KEEPERS / "phase30k_01"
    control_dir.mkdir(exist_ok=False)
    control_link = {"keeper_id": "phase30k_01", "phase": "30K", "blind_audition_number": "01", "identity": "CONTROL", "selected": True, "selection_verdict": "okay / selected", "preserved_at_utc": timestamp, "canonical_keeper": "g2_06", "canonical_paths": {"qwen_source": str(control / "qwen_source.wav"), "vietnamese_sample": str(control / "vietnamese_sample.wav"), "speaker_embedding": str(control / "speaker_emb.npy"), "reference_codes": str(control / "reference_codes.npy")}, "reason_for_link": "CONTROL is already the byte-identical preserved G2-06 keeper; no duplicate audio or conditioning was created.", "audio_modified": False, "conditioning_reencoded": False}
    write_once(control_dir / "finalist_link.json", control_link)
    new_entries.append({"keeper_id": "phase30k_01", "phase30k_blind_number": "01", "original_identity": "CONTROL", "verdict": "okay / selected", "canonical_keeper_link": "g2_06", "preserved_at_utc": timestamp, "files": files(control_dir)})

    identity = "K-A"
    finalist_dir = KEEPERS / "phase30k_04"
    finalist_dir.mkdir(exist_ok=False)
    suffix = identity[-1]
    artifacts = ((GENERATION / "reference_audio" / f"k_{suffix}.wav", "qwen_source.wav"), (GENERATION / "vietnamese_outputs" / f"vietnamese_{identity}.wav", "vietnamese_sample.wav"), (GENERATION / "conditioning" / f"speaker_emb_{suffix}.npy", "speaker_emb.npy"), (GENERATION / "conditioning" / f"reference_codes_{suffix}.npy", "reference_codes.npy"))
    for source, name in artifacts:
        if not source.is_file():
            raise RuntimeError(f"missing finalist artifact: {source}")
        copy_once(source, finalist_dir / name)
    write_once(finalist_dir / "source_measurements.json", record(SOURCE_MEASUREMENTS["records"], identity))
    write_once(finalist_dir / "vieneu_measurements.json", record(VIENEU_MEASUREMENTS["records"], identity))
    metadata = {"keeper_id": "phase30k_04", "phase": "30K", "blind_audition_number": "04", "identity": identity, "selected": True, "selection_verdict": "okay / selected", "preserved_at_utc": timestamp, "english_generation_text": PROMPTS["english_reference_text"], "voicedesign_prompt": PROMPTS["candidates"][identity], "original_paths": {"qwen_source": str(GENERATION / "reference_audio" / f"k_{suffix}.wav"), "vietnamese_output": str(GENERATION / "vietnamese_outputs" / f"vietnamese_{identity}.wav")}, "audio_modified": False, "conditioning_reencoded": False}
    write_once(finalist_dir / "metadata.json", metadata)
    new_entries.append({"keeper_id": "phase30k_04", "phase30k_blind_number": "04", "original_identity": identity, "verdict": "okay / selected", "voicedesign_prompt": PROMPTS["candidates"][identity], "qwen_source_path": str(finalist_dir / "qwen_source.wav"), "vietnamese_sample_path": str(finalist_dir / "vietnamese_sample.wav"), "speaker_embedding_path": str(finalist_dir / "speaker_emb.npy"), "reference_codes_path": str(finalist_dir / "reference_codes.npy"), "preserved_at_utc": timestamp, "files": files(finalist_dir)})
    manifest["updated_at_utc"] = timestamp
    manifest["keepers"].extend(new_entries)
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    validate(manifest)
    print("[Phase30K] Preserved 01 as canonical G2-06 link and 04 as K-A keeper; all hashes valid.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
