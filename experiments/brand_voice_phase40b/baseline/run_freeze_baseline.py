#!/usr/bin/env python3
"""Phase 40B Task 1: freeze the canonical Candidate B baseline package.

Reproduces the exact Phase 40A Candidate B speaker embedding formula and the
fixed reference-code anchor:

    speaker_emb_B = 0.75 x Pham Tuyen + 0.25 x Thanh Binh   (float32, convex)
    reference codes = Thanh Binh  (North / storytelling), shape (42, 16)

The resulting .npy files are the CANONICAL Candidate B. The rounded copy stored
in data/voices/voices.json (for the voice library) is deliberately NOT used as a
source for cross-text validation.
"""
from __future__ import annotations

import hashlib
import json
import platform
import subprocess
import sys
from datetime import datetime, timezone
from importlib.metadata import version
from pathlib import Path

import numpy as np
import vieneu

ROOT = Path(__file__).resolve().parent
PACKAGE = ROOT / "PODCAST_CANDIDATE_B_BASELINE"
MANIFEST = PACKAGE / "manifest.json"
FREEZE_RECORD = PACKAGE / "freeze_record.json"
VOICE_ASSET = Path(vieneu.__file__).resolve().parent / "assets" / "voices_v3_turbo.json"
EXPECTED_VOICE_ASSET_SHA256 = "574e6acf03823c4cafdc43f106731ce5fce6de30228fe383831b8b9064ee0bd8"
EXPECTED_EMB_SHA256 = "0c0cbc23228c89cfc27b0d109603b42b3fa0ca071cf728801455ec2cae752b53"
EXPECTED_CODES_SHA256 = "38964457925e5cf4362c90026e4bf552ddf1cf6acc35bc9555cd06c12603efb8"
EXPECTED_EMB_NORM = 10.962793350219727
FORMULA = {"Phạm Tuyên": 0.75, "Thanh Bình": 0.25}
REFERENCE_CODE_ANCHOR = "Thanh Bình"


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def sha256_array(array: np.ndarray) -> str:
    return sha256_bytes(np.ascontiguousarray(array).tobytes())


def main() -> int:
    if not VOICE_ASSET.exists():
        raise RuntimeError(f"VieNeu voice asset not found: {VOICE_ASSET}")
    asset_sha = sha256_file(VOICE_ASSET)
    if asset_sha != EXPECTED_VOICE_ASSET_SHA256:
        raise RuntimeError("Installed VieNeu voice asset hash changed; refusing to freeze")

    print("Installed VieNeu version:", version("vieneu"))
    print("Voice asset hash:", asset_sha)

    asset = json.loads(VOICE_ASSET.read_text(encoding="utf-8"))
    presets = asset["presets"]
    pham_tuyen = np.asarray(presets["Phạm Tuyên"]["speaker_emb"], dtype=np.float32)
    thanh_binh_emb = np.asarray(presets["Thanh Bình"]["speaker_emb"], dtype=np.float32)
    thanh_binh_codes = np.asarray(presets["Thanh Bình"]["codes"], dtype=np.int64)

    # Exact Phase 40A Candidate B computation (see phase40a/run_latent_cast.py).
    blend = (np.float32(0.75) * pham_tuyen + np.float32(0.25) * thanh_binh_emb).astype(np.float32)
    blend_sha = sha256_array(blend)
    blend_norm = float(np.linalg.norm(blend))
    codes_sha = sha256_array(thanh_binh_codes)

    print("Blend shape:", blend.shape)
    print("Blend norm:", blend_norm)
    print("Blend sha256:", blend_sha)
    print("Codes shape:", thanh_binh_codes.shape)
    print("Codes sha256:", codes_sha)

    if blend.shape != (192,):
        raise RuntimeError("Blend shape mismatch")
    if not np.isfinite(blend).all():
        raise RuntimeError("Blend has non-finite values")
    if blend_sha != EXPECTED_EMB_SHA256:
        raise RuntimeError(f"Blend hash mismatch: expected {EXPECTED_EMB_SHA256}, got {blend_sha}")
    if not abs(blend_norm - EXPECTED_EMB_NORM) < 1e-4:
        raise RuntimeError(f"Blend norm mismatch: {blend_norm}")
    if codes_sha != EXPECTED_CODES_SHA256:
        raise RuntimeError(f"Codes hash mismatch: expected {EXPECTED_CODES_SHA256}, got {codes_sha}")

    PACKAGE.mkdir(parents=True, exist_ok=True)
    emb_path = PACKAGE / "speaker_emb.npy"
    codes_path = PACKAGE / "reference_codes.npy"
    np.save(emb_path, blend, allow_pickle=False)
    np.save(codes_path, thanh_binh_codes, allow_pickle=False)

    files = {
        "speaker_emb.npy": {
            "sha256": sha256_file(emb_path),
            "size_bytes": emb_path.stat().st_size,
            "array_sha256": blend_sha,
        },
        "reference_codes.npy": {
            "sha256": sha256_file(codes_path),
            "size_bytes": codes_path.stat().st_size,
            "array_sha256": codes_sha,
        },
    }
    manifest = {
        "name": "PODCAST_CANDIDATE_B_BASELINE",
        "immutable": True,
        "category_label": "Podcast / Experimental",
        "status": "candidate",
        "is_final_brand_voice": False,
        "formula": FORMULA,
        "reference_code_anchor": REFERENCE_CODE_ANCHOR,
        "files": files,
    }

    started_utc = datetime.now(timezone.utc).isoformat()
    try:
        repo_commit = subprocess.check_output(
            ["git", "-C", str(PROJECT), "rev-parse", "HEAD"], text=True
        ).strip()
    except Exception:
        repo_commit = "UNKNOWN"
    freeze_record = {
        "package": "PODCAST_CANDIDATE_B_BASELINE",
        "phase": "40B",
        "task": "freeze_baseline",
        "formula": FORMULA,
        "formula_expr": "0.75 x Phạm Tuyên + 0.25 x Thanh Bình",
        "blend_normalization_applied": False,
        "reference_codes_preset": REFERENCE_CODE_ANCHOR,
        "reference_codes_style": "Bắc - kể chuyện",
        "speaker_emb": {
            "file": "speaker_emb.npy",
            "shape": [192],
            "dtype": "float32",
            "norm": blend_norm,
            "finite": True,
            "sha256": blend_sha,
        },
        "reference_codes": {
            "file": "reference_codes.npy",
            "shape": [42, 16],
            "dtype": "int64",
            "sha256": codes_sha,
        },
        "vieneu_version": version("vieneu"),
        "backend": "onnx",
        "device": "cpu",
        "sample_rate_hz": 48000,
        "voice_asset_path": str(VOICE_ASSET),
        "voice_asset_sha256": asset_sha,
        "generation_parameters": {
            "denoise": True,
            "use_ref_codes": True,
            "temperature": 0.8,
            "top_k": 25,
            "top_p": 0.95,
            "max_new_frames": 300,
            "repetition_penalty": 1.2,
            "repetition_window": 64,
            "max_chars": 256,
            "silence_p": 0.15,
            "crossfade_p": 0.0,
            "apply_watermark": True,
        },
        "phase40a_provenance": {
            "phase": "40A",
            "candidate": "B",
            "human_qa": "INTERESTING",
            "reference_dir": "experiments/brand_voice_phase40a",
            "embedding_geometry": "experiments/brand_voice_phase40a/embedding_geometry.json",
            "audition_wav": "experiments/brand_voice_phase40a/audio/candidate_B.wav",
            "audition_sha256": "7a280b94c8802b99e29dc4f5b57e2e481c9fb0928973d3d9e6d72fe40b55e066",
        },
        "canonical_source": "This package (.npy files) is the only canonical source for Phase 40B cross-text validation. The rounded data/voices/voices.json copy is UI/library-only.",
        "started_utc": started_utc,
        "repository_commit": repo_commit,
        "python": sys.version,
        "platform": platform.platform(),
    }

    MANIFEST.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    FREEZE_RECORD.write_text(
        json.dumps(freeze_record, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )

    print("FROZEN_CANDIDATE_B_BASELINE_READY", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
