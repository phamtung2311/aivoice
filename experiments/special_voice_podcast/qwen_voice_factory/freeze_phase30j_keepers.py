#!/usr/bin/env python3
"""Freeze the user-selected Phase 30I keepers without altering their audio."""
from __future__ import annotations

import hashlib
import json
import os
import shutil
import sys
from datetime import datetime, timezone
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parent
PROJECT = ROOT.parents[2]
KEEPERS = ROOT.parent / "keepers"
PROMPTS = json.loads((ROOT / "prompts.json").read_text(encoding="utf-8"))
MAPPING = json.loads((ROOT / "private_mapping.json").read_text(encoding="utf-8"))
SOURCE_MEASUREMENTS = json.loads((ROOT / "measurements" / "source_generation.json").read_text(encoding="utf-8"))
VIENEU_MEASUREMENTS = json.loads((ROOT / "measurements" / "vieneu_generation.json").read_text(encoding="utf-8"))
SELECTED = {
    "01": "good; human-like; fairly acceptable",
    "02": "good; human-like; fairly acceptable",
}


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def copy_once(source: Path, target: Path) -> None:
    if target.exists():
        if not target.is_file() or sha256(source) != sha256(target):
            raise RuntimeError(f"refusing to overwrite keeper artifact: {target}")
        return
    shutil.copy2(source, target)


def write_once_json(target: Path, value: object) -> None:
    text = json.dumps(value, ensure_ascii=False, indent=2) + "\n"
    if target.exists():
        if target.read_text(encoding="utf-8") != text:
            raise RuntimeError(f"refusing to overwrite keeper artifact: {target}")
        return
    target.write_text(text, encoding="utf-8")


def record_for(records: list[dict], identity: str) -> dict:
    return next(record for record in records if record["identity"] == identity)


def main() -> int:
    sys.path.insert(0, str(PROJECT))
    from backend.app.tts.engine import TTSEngine

    if set(MAPPING) != {"01", "02", "03"}:
        raise RuntimeError("unexpected Phase 30I blind mapping")
    timestamp = datetime.now(timezone.utc).isoformat()
    keepers_manifest: list[dict] = []
    KEEPERS.mkdir(parents=True, exist_ok=True)
    engine = None

    for blind_number, verdict in SELECTED.items():
        identity = MAPPING[blind_number]
        keeper_id = f"phase30i_{blind_number}"
        directory = KEEPERS / keeper_id
        directory.mkdir(exist_ok=True)
        source = ROOT / "reference_audio" / f"qwen_candidate_{identity}.wav"
        vietnamese = ROOT / "audition" / f"vietnamese_{blind_number}.wav"
        if not source.is_file() or not vietnamese.is_file():
            raise RuntimeError(f"missing required Phase 30I artifact for {keeper_id}")

        copy_once(source, directory / "qwen_source.wav")
        copy_once(vietnamese, directory / "vietnamese_sample.wav")
        write_once_json(directory / "source_measurements.json", record_for(SOURCE_MEASUREMENTS["records"], identity))
        write_once_json(directory / "vieneu_measurements.json", record_for(VIENEU_MEASUREMENTS["records"], identity))

        emb_path, codes_path = directory / "speaker_emb.npy", directory / "reference_codes.npy"
        if emb_path.exists() != codes_path.exists():
            raise RuntimeError(f"incomplete conditioning preservation for {keeper_id}")
        if not emb_path.exists():
            if engine is None:
                engine = TTSEngine(backend="onnx")
                runtime_home = ROOT / ".vieneu_runtime_home"
                (runtime_home / ".cache" / "vieneu" / "tmp").mkdir(parents=True, exist_ok=True)
                os.environ["HOME"] = str(runtime_home)
            speaker_emb, codes = engine._model.encode_reference(str(source), denoise=False, use_ref_codes=True)
            np.save(emb_path, np.asarray(speaker_emb))
            np.save(codes_path, np.asarray(codes))

        metadata = {
            "keeper_id": keeper_id,
            "phase": "30I",
            "blind_audition_number": blind_number,
            "original_identity": identity,
            "user_verdict": verdict,
            "preserved_at_utc": timestamp,
            "english_generation_text": PROMPTS["english_reference_text"],
            "voicedesign_prompt": PROMPTS["candidates"][identity],
            "original_paths": {
                "qwen_source": str(source),
                "vietnamese_audition": str(vietnamese),
                "source_measurements": str(ROOT / "measurements" / "source_generation.json"),
                "vieneu_measurements": str(ROOT / "measurements" / "vieneu_generation.json"),
            },
            "conditioning": {
                "encoder": "existing VieNeu ONNX reference encoder",
                "denoise": False,
                "use_ref_codes": True,
                "speaker_embedding_shape": list(np.load(emb_path, allow_pickle=False).shape),
                "reference_codes_shape": list(np.load(codes_path, allow_pickle=False).shape),
            },
            "audio_modified": False,
        }
        write_once_json(directory / "metadata.json", metadata)
        files = {}
        for artifact in sorted(directory.iterdir()):
            if artifact.is_file():
                files[artifact.name] = {"path": str(artifact), "size_bytes": artifact.stat().st_size, "sha256": sha256(artifact)}
        keepers_manifest.append({
            "keeper_id": keeper_id,
            "phase30i_blind_number": blind_number,
            "original_identity": identity,
            "verdict": verdict,
            "voicedesign_prompt": PROMPTS["candidates"][identity],
            "qwen_source_path": str(directory / "qwen_source.wav"),
            "vietnamese_sample_path": str(directory / "vietnamese_sample.wav"),
            "speaker_embedding_path": str(emb_path),
            "reference_codes_path": str(codes_path),
            "preserved_at_utc": timestamp,
            "files": files,
        })

    manifest = {
        "phase": "30J",
        "created_at_utc": timestamp,
        "integrity_algorithm": "sha256",
        "keepers": keepers_manifest,
    }
    manifest_path = KEEPERS / "KEEPERS_MANIFEST.json"
    if manifest_path.exists():
        raise RuntimeError(f"refusing to overwrite protected manifest: {manifest_path}")
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"[Phase30J] Frozen {len(keepers_manifest)} protected keeper baselines.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
