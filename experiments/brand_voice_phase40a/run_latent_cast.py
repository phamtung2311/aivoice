#!/usr/bin/env python3
"""Phase 40A: four native Vietnamese convex speaker-latent candidates."""

from __future__ import annotations

import hashlib
import json
import os
import platform
import resource
import subprocess
import sys
import time
from datetime import datetime, timezone
from importlib.metadata import version
from pathlib import Path

os.environ.setdefault("HF_HUB_OFFLINE", "1")
os.environ.setdefault("TRANSFORMERS_OFFLINE", "1")

import numpy as np
import soundfile as sf
import vieneu
from vieneu import Vieneu


ROOT = Path(__file__).resolve().parent
PROJECT = ROOT.parents[1]
AUDIO = ROOT / "audio"
TEXT_PATH = ROOT / "shared_vietnamese_text.txt"
MANIFEST = ROOT / "manifest.json"
PROVENANCE = ROOT / "provenance.json"
GEOMETRY = ROOT / "embedding_geometry.json"

TEXT = "Giữa những đổi thay, điều giữ chúng ta đứng vững không phải là câu trả lời có sẵn, mà là khả năng nhìn rõ điều mình tin và sống nhất quán với nó."
VOICE_ASSET = Path(vieneu.__file__).resolve().parent / "assets" / "voices_v3_turbo.json"
EXPECTED_VOICE_ASSET_SHA256 = "574e6acf03823c4cafdc43f106731ce5fce6de30228fe383831b8b9064ee0bd8"
REFERENCE_CODE_ANCHOR = "Thanh Bình"
NUMPY_SEED = 40001
FORMULAS = {
    "A": {"Minh Đức": 0.75, "Phạm Tuyên": 0.25},
    "B": {"Phạm Tuyên": 0.75, "Thanh Bình": 0.25},
    "C": {"Thanh Bình": 0.75, "Minh Đức": 0.25},
    "D": {"Minh Đức": 1.0 / 3.0, "Phạm Tuyên": 1.0 / 3.0, "Thanh Bình": 1.0 / 3.0},
}
INFERENCE_DEFAULTS = {
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
    "batch_size": None,
}


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def sha256_array(array: np.ndarray) -> str:
    return hashlib.sha256(np.ascontiguousarray(array).tobytes()).hexdigest()


def audio_metrics(path: Path) -> dict:
    info = sf.info(path)
    data, sample_rate = sf.read(path, always_2d=True, dtype="float32")
    mono = data.mean(axis=1, dtype=np.float64)
    return {
        "path": str(path.relative_to(ROOT)),
        "sha256": sha256_file(path),
        "size_bytes": path.stat().st_size,
        "duration_seconds": float(len(data) / sample_rate),
        "sample_rate_hz": int(sample_rate),
        "channels": int(data.shape[1]),
        "format": info.format,
        "subtype": info.subtype,
        "frames_header": int(info.frames),
        "frames_read": int(len(data)),
        "all_samples_finite": bool(np.isfinite(data).all()),
        "peak_abs": float(np.max(np.abs(data))) if data.size else 0.0,
        "rms": float(np.sqrt(np.mean(np.square(mono)))) if mono.size else 0.0,
        "clipped_samples_abs_ge_0_999": int(np.count_nonzero(np.abs(data) >= 0.999)),
    }


def valid_audio(metrics: dict) -> bool:
    return (
        metrics["duration_seconds"] > 0
        and metrics["sample_rate_hz"] == 48000
        and metrics["channels"] == 1
        and metrics["frames_header"] == metrics["frames_read"]
        and metrics["all_samples_finite"]
        and metrics["clipped_samples_abs_ge_0_999"] / max(1, metrics["frames_read"]) <= 0.01
    )


def cosine(left: np.ndarray, right: np.ndarray) -> float:
    return float(np.dot(left, right) / (np.linalg.norm(left) * np.linalg.norm(right)))


def build_geometry(presets: dict) -> tuple[dict, dict[str, np.ndarray]]:
    male_names = [name for name, data in presets.items() if data.get("gender") == "male"]
    male_embeddings = {name: np.asarray(presets[name]["speaker_emb"], dtype=np.float32) for name in male_names}
    inventory = []
    for name in male_names:
        data = presets[name]
        emb = male_embeddings[name]
        codes = np.asarray(data["codes"], dtype=np.int64)
        inventory.append(
            {
                "name": name,
                "region": data.get("region"),
                "style": data.get("style"),
                "description": data.get("description"),
                "speaker_emb_shape": list(emb.shape),
                "reference_codes_shape": list(codes.shape),
                "speaker_emb_norm": float(np.linalg.norm(emb)),
                "speaker_emb_finite": bool(np.isfinite(emb).all()),
                "reference_codes_finite": bool(np.isfinite(codes).all()),
                "speaker_emb_sha256": sha256_array(emb),
                "reference_codes_sha256": sha256_array(codes),
            }
        )
    pairwise = []
    for index, left_name in enumerate(male_names):
        for right_name in male_names[index + 1 :]:
            left, right = male_embeddings[left_name], male_embeddings[right_name]
            pairwise.append(
                {
                    "left": left_name,
                    "right": right_name,
                    "cosine_similarity": cosine(left, right),
                    "euclidean_distance": float(np.linalg.norm(left - right)),
                }
            )
    matrix = np.stack([male_embeddings[name] for name in male_names]).astype(np.float64)
    centered = matrix - matrix.mean(axis=0)
    _, singular, vt = np.linalg.svd(centered, full_matrices=False)
    variance = singular * singular / max(1, len(male_names) - 1)
    explained = variance / variance.sum()
    coordinates = centered @ vt.T

    blends = {}
    blend_vectors = {}
    for candidate, weights in FORMULAS.items():
        if any(weight < 0 for weight in weights.values()) or not np.isclose(sum(weights.values()), 1.0):
            raise RuntimeError(f"Non-convex formula for Candidate {candidate}")
        vector = sum(np.float32(weight) * male_embeddings[name] for name, weight in weights.items()).astype(np.float32)
        blend_vectors[candidate] = vector
        blends[candidate] = {
            "weights": weights,
            "speaker_emb_shape": list(vector.shape),
            "speaker_emb_norm": float(np.linalg.norm(vector)),
            "speaker_emb_finite": bool(np.isfinite(vector).all()),
            "speaker_emb_sha256": sha256_array(vector),
        }
    blend_pairwise = []
    for index, left_name in enumerate(blend_vectors):
        for right_name in list(blend_vectors)[index + 1 :]:
            left, right = blend_vectors[left_name], blend_vectors[right_name]
            blend_pairwise.append(
                {
                    "left": left_name,
                    "right": right_name,
                    "cosine_similarity": cosine(left, right),
                    "euclidean_distance": float(np.linalg.norm(left - right)),
                }
            )
    audit = {
        "vieneu_version": version("vieneu"),
        "voice_asset_path": str(VOICE_ASSET),
        "voice_asset_sha256": sha256_file(VOICE_ASSET),
        "total_preset_count": len(presets),
        "male_preset_count": len(male_names),
        "all_preset_shapes": {
            name: {
                "speaker_emb": list(np.asarray(data["speaker_emb"]).shape),
                "reference_codes": list(np.asarray(data["codes"]).shape),
                "speaker_emb_finite": bool(np.isfinite(np.asarray(data["speaker_emb"], dtype=np.float32)).all()),
                "reference_codes_finite": bool(np.isfinite(np.asarray(data["codes"], dtype=np.float64)).all()),
            }
            for name, data in presets.items()
        },
        "male_inventory": inventory,
        "male_pairwise": pairwise,
        "pca_explained_variance_ratio": [float(value) for value in explained],
        "pca_coordinates": {name: [float(value) for value in coordinates[index]] for index, name in enumerate(male_names)},
        "regional_policy": "Northern male embeddings only; accent allocation between embedding and codes is not proven separable.",
        "reference_code_anchor": REFERENCE_CODE_ANCHOR,
        "reference_code_anchor_reason": "Northern male storytelling preset; preferred over news for reflective cadence and neutral-Vietnamese risk control.",
        "reference_codes_shape": list(np.asarray(presets[REFERENCE_CODE_ANCHOR]["codes"]).shape),
        "reference_codes_sha256": sha256_array(np.asarray(presets[REFERENCE_CODE_ANCHOR]["codes"], dtype=np.int64)),
        "normalization_contract": "No speaker embedding input normalization. ONNX runtime applies Linear projection then LayerNorm to the projected anchor.",
        "blend_normalization_applied": False,
        "blends": blends,
        "blend_pairwise": blend_pairwise,
        "manual_voice_dict_runtime_gate": "PASS",
        "production_voice_registration": False,
    }
    return audit, blend_vectors


def main() -> None:
    if any(path.exists() for path in (AUDIO, MANIFEST, PROVENANCE, GEOMETRY)):
        raise FileExistsError("Phase 40A artifacts already exist; no overwrite or second cast allowed")
    if TEXT_PATH.read_text(encoding="utf-8").strip() != TEXT:
        raise RuntimeError("Frozen Vietnamese audition text mismatch")
    if sha256_file(VOICE_ASSET) != EXPECTED_VOICE_ASSET_SHA256:
        raise RuntimeError("Installed VieNeu voice asset hash changed")

    asset = json.loads(VOICE_ASSET.read_text(encoding="utf-8"))
    presets = asset["presets"]
    audit, blend_vectors = build_geometry(presets)
    if len(presets) != 20 or audit["male_preset_count"] != 9:
        raise RuntimeError("Unexpected VieNeu preset roster")
    if any(item["speaker_emb_shape"] != [192] for item in audit["male_inventory"]):
        raise RuntimeError("Unexpected male speaker embedding shape")

    started_utc = datetime.now(timezone.utc).isoformat()
    total_started = time.perf_counter()
    load_started = time.perf_counter()
    tts = Vieneu(backend="onnx")
    load_seconds = time.perf_counter() - load_started
    if tts.backend != "onnx" or tts.sample_rate != 48000:
        raise RuntimeError("Required VieNeu ONNX/48 kHz runtime unavailable")
    if set(tts._preset_voices) != set(presets):
        raise RuntimeError("Runtime preset roster differs from audited asset")

    fixed_codes = np.asarray(presets[REFERENCE_CODE_ANCHOR]["codes"], dtype=np.int64)
    probe_emb, probe_codes = tts._resolve_ref(
        {"speaker_emb": blend_vectors["A"], "codes": fixed_codes}, None, False, True
    )
    if not np.array_equal(probe_emb, blend_vectors["A"]) or not np.array_equal(probe_codes, fixed_codes):
        raise RuntimeError("Runtime changed the manual experimental voice profile")

    AUDIO.mkdir(parents=True, exist_ok=False)
    records = []
    for candidate in ("A", "B", "C", "D"):
        np.random.seed(NUMPY_SEED)
        output = AUDIO / f"candidate_{candidate}.wav"
        temporary = AUDIO / f".candidate_{candidate}.tmp.wav"
        generation_started = time.perf_counter()
        print(f"[Phase40A] Generating Candidate {candidate}/4 on CPU.", flush=True)
        waveform = tts.infer(
            TEXT,
            voice={"speaker_emb": blend_vectors[candidate], "codes": fixed_codes},
        )
        generation_seconds = time.perf_counter() - generation_started
        sf.write(temporary, np.asarray(waveform, dtype=np.float32), tts.sample_rate, subtype="PCM_16")
        metrics = audio_metrics(temporary)
        if not valid_audio(metrics):
            raise RuntimeError(f"Candidate {candidate} produced an invalid WAV: {metrics}")
        temporary.replace(output)
        records.append(
            {
                "candidate": candidate,
                "formula": FORMULAS[candidate],
                "speaker_emb_sha256": sha256_array(blend_vectors[candidate]),
                "fixed_reference_codes_preset": REFERENCE_CODE_ANCHOR,
                "fixed_reference_codes_sha256": sha256_array(fixed_codes),
                "numpy_seed": NUMPY_SEED,
                "generation_seconds": generation_seconds,
                "rtf": generation_seconds / metrics["duration_seconds"],
                "peak_process_rss_mib": resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1024.0,
                "audio": audio_metrics(output),
            }
        )
        print(f"[Phase40A] Candidate {candidate} saved ({metrics['duration_seconds']:.3f} s).", flush=True)

    names = sorted(path.name for path in AUDIO.glob("*.wav"))
    if names != [f"candidate_{candidate}.wav" for candidate in "ABCD"]:
        raise RuntimeError(f"Unexpected primary audition set: {names}")

    completed_utc = datetime.now(timezone.utc).isoformat()
    total_seconds = time.perf_counter() - total_started
    repository_commit = subprocess.check_output(["git", "-C", str(PROJECT), "rev-parse", "HEAD"], text=True).strip()
    manifest = {
        "phase": "40A",
        "execution_status": "PASS",
        "human_gate": "PENDING HUMAN QA",
        "shared_vietnamese_audition_text": TEXT,
        "reference_code_anchor": REFERENCE_CODE_ANCHOR,
        "inference_defaults": INFERENCE_DEFAULTS,
        "records": records,
    }
    provenance = {
        "phase": "40A",
        "candidate03_status": "RETIRED",
        "phase39a_status": "QWEN VOICEDESIGN CASTING = FAIL FOR BRAND IDENTITY",
        "openvoice_candidate03_status": "HUMAN FAIL",
        "seedvc_abcd_transfer": "CANCELLED — NO VALUE WITHOUT A STRONG TARGET IDENTITY",
        "production_modified": False,
        "production_voice_storage_modified": False,
        "user_voice_used": False,
        "new_model_downloaded": False,
        "license_status": "CONDITIONALLY COMMERCIAL-SAFE PENDING DERIVATIVE-ASSET INTERPRETATION",
        "started_utc": started_utc,
        "completed_utc": completed_utc,
        "repository_commit_before_phase40a": repository_commit,
        "repository_worktree_before_phase40a": "DIRTY; existing user changes preserved",
        "python": sys.version,
        "platform": platform.platform(),
        "vieneu_version": version("vieneu"),
        "backend": "onnx",
        "device": "cpu",
        "sample_rate_hz": tts.sample_rate,
        "voice_asset_path": str(VOICE_ASSET),
        "voice_asset_sha256": EXPECTED_VOICE_ASSET_SHA256,
        "shared_vietnamese_audition_text": TEXT,
        "fixed_reference_code_anchor": REFERENCE_CODE_ANCHOR,
        "fixed_reference_codes_sha256": sha256_array(fixed_codes),
        "formulas": FORMULAS,
        "numpy_seed": NUMPY_SEED,
        "inference_defaults": INFERENCE_DEFAULTS,
        "model_load_seconds": load_seconds,
        "total_wall_seconds": total_seconds,
        "peak_process_rss_mib": resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1024.0,
    }
    GEOMETRY.write_text(json.dumps(audit, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    MANIFEST.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    PROVENANCE.write_text(json.dumps(provenance, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print("PHASE40A_NATIVE_LATENT_CAST_READY", flush=True)


if __name__ == "__main__":
    main()
