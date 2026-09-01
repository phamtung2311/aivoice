#!/usr/bin/env python3
"""Freeze selected Phase 30J G2 artifacts without altering audio or conditioning."""
from __future__ import annotations

import hashlib
import json
import shutil
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent
GENERATION = ROOT / "generation_2"
KEEPERS = ROOT.parent / "keepers"
MAPPING = json.loads((GENERATION / "private_mapping.json").read_text(encoding="utf-8"))
PROMPTS = json.loads((GENERATION / "prompts.json").read_text(encoding="utf-8"))
SOURCE_MEASUREMENTS = json.loads((GENERATION / "measurements" / "source_generation.json").read_text(encoding="utf-8"))
VIENEU_MEASUREMENTS = json.loads((GENERATION / "measurements" / "vieneu_generation.json").read_text(encoding="utf-8"))
SELECTED = ("01", "05", "06")


def digest(path: Path) -> str:
    value = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            value.update(block)
    return value.hexdigest()


def validate_manifest(manifest: dict) -> None:
    for keeper in manifest["keepers"]:
        for artifact in keeper["files"].values():
            path = Path(artifact["path"])
            if not path.is_file() or path.stat().st_size != artifact["size_bytes"] or digest(path) != artifact["sha256"]:
                raise RuntimeError(f"KEEPER_INTEGRITY_FAILED: {path}")


def copy_once(source: Path, target: Path) -> None:
    if target.exists():
        if not target.is_file() or digest(source) != digest(target):
            raise RuntimeError(f"refusing to overwrite keeper artifact: {target}")
        return
    shutil.copy2(source, target)


def write_once(target: Path, value: object) -> None:
    content = json.dumps(value, ensure_ascii=False, indent=2) + "\n"
    if target.exists():
        if target.read_text(encoding="utf-8") != content:
            raise RuntimeError(f"refusing to overwrite keeper artifact: {target}")
        return
    target.write_text(content, encoding="utf-8")


def record(records: list[dict], identity: str) -> dict:
    return next(item for item in records if item["identity"] == identity)


def files_manifest(directory: Path) -> dict:
    return {path.name: {"path": str(path), "size_bytes": path.stat().st_size, "sha256": digest(path)} for path in sorted(directory.iterdir()) if path.is_file()}


def main() -> int:
    manifest_path = KEEPERS / "KEEPERS_MANIFEST.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    validate_manifest(manifest)
    if any(item["keeper_id"] in {f"g2_{number}" for number in SELECTED} for item in manifest["keepers"]):
        raise RuntimeError("selected G2 keeper already exists; refusing manifest overwrite")
    timestamp = datetime.now(timezone.utc).isoformat()
    new_entries = []
    for number in SELECTED:
        identity = MAPPING[number]
        suffix = identity[-1]
        directory = KEEPERS / f"g2_{number}"
        directory.mkdir(exist_ok=False)
        source = GENERATION / "reference_audio" / f"g2_{suffix}.wav"
        vietnamese = GENERATION / "vietnamese_outputs" / f"vietnamese_G2_{suffix}.wav"
        emb = GENERATION / "conditioning" / f"speaker_emb_{suffix}.npy"
        codes = GENERATION / "conditioning" / f"reference_codes_{suffix}.npy"
        for source_path, target_name in ((source, "qwen_source.wav"), (vietnamese, "vietnamese_sample.wav"), (emb, "speaker_emb.npy"), (codes, "reference_codes.npy")):
            if not source_path.is_file():
                raise RuntimeError(f"missing required G2 artifact: {source_path}")
            copy_once(source_path, directory / target_name)
        write_once(directory / "source_measurements.json", record(SOURCE_MEASUREMENTS["records"], identity))
        write_once(directory / "vieneu_measurements.json", record(VIENEU_MEASUREMENTS["records"], identity))
        metadata = {"keeper_id": f"g2_{number}", "phase": "30J", "blind_audition_number": number, "original_identity": identity, "user_verdict": {"01": "fairly good; slightly too slow", "05": "fairly good", "06": "highest potential of the six; primary candidate"}[number], "preserved_at_utc": timestamp, "english_generation_text": PROMPTS["english_reference_text"], "voicedesign_prompt": PROMPTS["candidates"][identity], "original_paths": {"qwen_source": str(source), "vietnamese_output": str(vietnamese), "speaker_embedding": str(emb), "reference_codes": str(codes)}, "audio_modified": False, "conditioning_reencoded": False}
        write_once(directory / "metadata.json", metadata)
        new_entries.append({"keeper_id": f"g2_{number}", "phase30j_blind_number": number, "original_identity": identity, "verdict": metadata["user_verdict"], "voicedesign_prompt": PROMPTS["candidates"][identity], "qwen_source_path": str(directory / "qwen_source.wav"), "vietnamese_sample_path": str(directory / "vietnamese_sample.wav"), "speaker_embedding_path": str(directory / "speaker_emb.npy"), "reference_codes_path": str(directory / "reference_codes.npy"), "preserved_at_utc": timestamp, "files": files_manifest(directory)})
    manifest["updated_at_utc"] = timestamp
    manifest["keepers"].extend(new_entries)
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    validate_manifest(manifest)
    print("[Phase30K] Frozen 3 G2 keepers; all keeper hashes valid.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
