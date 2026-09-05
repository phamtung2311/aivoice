#!/usr/bin/env python3
"""Phase 40C: three local latent refinements around Candidate B, with baseline control.

Rules enforced:
- Candidate B canonical assets are never overwritten or changed.
- reference_codes remain the frozen Thanh Bình codes.
- only speaker_emb is varied.
- only 3 refinements + untouched baseline are generated.
- no broad search, no model changes, no model downloads, no production library changes.
"""

from __future__ import annotations

import hashlib
import json
import os
import resource
import time
from pathlib import Path

import numpy as np
import soundfile as sf
from vieneu import Vieneu

ROOT = Path(__file__).resolve().parent
PROJECT_ROOT = ROOT.parents[1]
BASELINE_DIR = (PROJECT_ROOT / "experiments/brand_voice_phase40b/baseline/PODCAST_CANDIDATE_B_BASELINE").resolve()
AUDIO_DIR = ROOT / "audio"
BLIND_DIR = ROOT / "blind_audition"
COMMON_TEXT = (
    "Người ta hay nghĩ rằng một giọng nói tốt là giọng vang to. Nhưng thật ra, giọng podcast "
    "tốt là giọng biết dừng lại đúng lúc, đặt câu hỏi đúng chỗ, và để người nghe cảm nhận "
    "được một sự thật không cần ai nhấn mạnh. Khi ta lắng nghe đủ sâu, ta sẽ thấy rằng mỗi "
    "sự suy ngẫm đều mang trong mình một lý do để sống chậm, sống rõ, và sống có trách nhiệm."
)

CONFIG = {
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

FORMULAS = {
    "baseline_candidate_b": {
        "description": "Untouched canonical Candidate B control",
        "weights": {"Phạm Tuyên": 0.75, "Thanh Bình": 0.25},
    },
    "refinement_r1": {
        "description": "Slightly stronger Phạm Tuyên identity; more personal narrator nuance while keeping storytelling codes fixed",
        "weights": {"Phạm Tuyên": 0.82, "Thanh Bình": 0.18},
    },
    "refinement_r2": {
        "description": "Slightly more Thanh Bình body for a mature storytelling anchor",
        "weights": {"Phạm Tuyên": 0.68, "Thanh Bình": 0.32},
    },
    "refinement_r3": {
        "description": "Controlled third-anchor perturbation around B using a nearby Northern male anchor",
        "weights": {"Phạm Tuyên": 0.70, "Thanh Bình": 0.20, "Minh Đức": 0.10},
    },
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


def linear_blend(weights: dict[str, float], preset_map: dict[str, np.ndarray]) -> np.ndarray:
    total = sum(weights.values())
    if not np.isclose(total, 1.0, atol=1e-8):
        raise ValueError(f"Blend weights must sum to 1.0, got {total}")
    if any(weight < 0 for weight in weights.values()):
        raise ValueError("No negative coefficients allowed")
    blended = np.zeros(192, dtype=np.float32)
    for name, weight in weights.items():
        blended += np.asarray(preset_map[name], dtype=np.float32) * weight
    return blended.astype(np.float32)


def main() -> None:
    ROOT.mkdir(parents=True, exist_ok=True)
    AUDIO_DIR.mkdir(parents=True, exist_ok=True)
    BLIND_DIR.mkdir(parents=True, exist_ok=True)

    baseline_emb = np.load(BASELINE_DIR / "speaker_emb.npy", allow_pickle=False).astype(np.float32)
    baseline_codes = np.load(BASELINE_DIR / "reference_codes.npy", allow_pickle=False)

    # Use the Phase 40A measured geometry: Candidate B is local center, and all refinements remain near B.
    phase40a_geometry = json.loads((PROJECT_ROOT / "experiments/brand_voice_phase40a/embedding_geometry.json").read_text(encoding="utf-8"))
    if phase40a_geometry["blends"]["B"]["speaker_emb_sha256"] != sha256_array(baseline_emb):
        raise RuntimeError("Canonical Candidate B embedding hash mismatch with Phase 40A geometry")

    try:
        import vieneu
        from pathlib import Path as P
        asset_json = P(vieneu.__file__).resolve().parent / "assets" / "voices_v3_turbo.json"
        presets = json.loads(asset_json.read_text(encoding="utf-8"))["presets"]
    except Exception as exc:  # pragma: no cover
        raise RuntimeError(f"Failed to load installed VieNeu preset list: {exc}")

    speaker_lookup = {}
    for name, preset in presets.items():
        if name in {"Phạm Tuyên", "Thanh Bình", "Minh Đức"}:
            emb = np.asarray(preset.get("speaker_emb", []), dtype=np.float32)
            if emb.size == 192:
                speaker_lookup[name] = emb

    missing = [name for name in ["Phạm Tuyên", "Thanh Bình", "Minh Đức"] if name not in speaker_lookup]
    if missing:
        raise RuntimeError(f"Missing required preset embeddings in installed VieNeu assets: {missing}")

    voice_profiles = {
        "baseline_candidate_b": {"speaker_emb": baseline_emb, "codes": baseline_codes},
    }
    for name, formula in FORMULAS.items():
        if name == "baseline_candidate_b":
            continue
        weights = formula["weights"]
        emb = linear_blend(weights, speaker_lookup)
        voice_profiles[name] = {"speaker_emb": emb, "codes": baseline_codes}

    # Final safety gate: no reference code change.
    if sha256_array(baseline_codes) != "38964457925e5cf4362c90026e4bf552ddf1cf6acc35bc9555cd06c12603efb8":
        raise RuntimeError("Reference codes changed unexpectedly")

    np.random.seed(40002)
    engine = Vieneu(backend="onnx")
    mapping = {}
    order = ["baseline_candidate_b", "refinement_r1", "refinement_r2", "refinement_r3"]
    blind_labels = ["01.wav", "02.wav", "03.wav", "04.wav"]
    blind_map = {}
    for label, blind_name in zip(order, blind_labels):
        profile = voice_profiles[label]
        output_path = AUDIO_DIR / f"{label}.wav"
        start = time.perf_counter()
        rss_before = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
        waveform = engine.infer(
            COMMON_TEXT,
            voice={"speaker_emb": profile["speaker_emb"], "codes": profile["codes"]},
            **CONFIG,
        )
        elapsed = time.perf_counter() - start
        rss_after = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
        wav = np.asarray(waveform, dtype=np.float32)
        sf.write(output_path, wav, 48000, subtype="PCM_16")
        metrics = audio_metrics(output_path)
        metrics.update({
            "generation_seconds": round(elapsed, 6),
            "rtf": round(elapsed / max(metrics["duration_seconds"], 1e-9), 6),
            "peak_process_rss_mib": round((rss_after - rss_before) / 1024, 6) if rss_after >= rss_before else round(rss_after / 1024, 6),
            "speaker_emb_sha256": sha256_array(profile["speaker_emb"]),
            "reference_codes_sha256": sha256_array(profile["codes"]),
            "formula": FORMULAS[label]["weights"],
            "text": COMMON_TEXT,
        })
        mapping[label] = metrics
        blind_map[blind_name] = f"{label}.wav"
        sf.write(BLIND_DIR / blind_name, wav, 48000, subtype="PCM_16")

    manifest = {
        "phase": "40C",
        "task": "podcast_brand_signature_refinement",
        "canonical_baseline": {
            "path": "experiments/brand_voice_phase40b/baseline/PODCAST_CANDIDATE_B_BASELINE",
            "speaker_emb_sha256": "0c0cbc23228c89cfc27b0d109603b42b3fae0ca071cf728801455ec2cae752b53" if False else "0c0cbc23228c89cfc27b0d109603b42b3fa0ca071cf728801455ec2cae752b53",
            "reference_codes_sha256": "38964457925e5cf4362c90026e4bf552ddf1cf6acc35bc9555cd06c12603efb8",
            "baseline_formula": {"Phạm Tuyên": 0.75, "Thanh Bình": 0.25},
            "reference_codes_fixed": True,
        },
        "shared_audition_text": COMMON_TEXT,
        "generation_config": CONFIG,
        "local_geometric_moves": FORMULAS,
        "results": mapping,
        "blind_mapping": blind_map,
        "status": "CANDIDATE B BRAND SIGNATURE REFINEMENT: PENDING HUMAN QA",
    }
    (ROOT / "manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")

    # Also retain a separate provenance note documenting that the production baseline remains untouched.
    provenance = {
        "phase": "40C",
        "baseline_untouched": True,
        "production_library_voice_untouched": True,
        "reference_codes_changed": False,
        "new_model_downloaded": False,
        "model_changed": False,
        "user_voice_recording_used": False,
        "cloud_or_gpu_used": False,
        "winner_rule": "A refinement wins only if clearly preferred to baseline while preserving naturalness and podcast fit.",
    }
    (ROOT / "provenance.json").write_text(json.dumps(provenance, ensure_ascii=False, indent=2), encoding="utf-8")

    print(json.dumps({"status": "generated", "files": list(sorted(str(p.relative_to(ROOT)) for p in AUDIO_DIR.glob("*.wav")))}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
