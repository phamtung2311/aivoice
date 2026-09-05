#!/usr/bin/env python3
"""Phase 40B Task 3: cross-text validation of the frozen Candidate B baseline.

Exactly three NEW passages are generated with the unchanged Candidate B baseline
(canonical .npy in baseline/PODCAST_CANDIDATE_B_BASELINE), the same reference
codes, and one stable generation configuration equal to Phase 40A's defaults.

No tuning: no embedding/code change, no temperature/top-k/top-p/speed change,
no variants, no new blend, no post-processing.
"""
from __future__ import annotations

import hashlib
import json
import platform
import resource
import subprocess
import sys
from datetime import datetime, timezone
from importlib.metadata import version
from pathlib import Path

import numpy as np
import soundfile as sf
import time
import vieneu
from vieneu import Vieneu

ROOT = Path(__file__).resolve().parent
PROJECT = ROOT.parents[1]
AUDIO = ROOT / "audio"
TEXTS = ROOT / "texts"
BASELINE = ROOT / "baseline" / "PODCAST_CANDIDATE_B_BASELINE"
MANIFEST = ROOT / "manifest.json"
PROVENANCE = ROOT / "provenance.json"

VOICE_ASSET = Path(vieneu.__file__).resolve().parent / "assets" / "voices_v3_turbo.json"
EXPECTED_VOICE_ASSET_SHA256 = "574e6acf03823c4cafdc43f106731ce5fce6de30228fe383831b8b9064ee0bd8"

TEXTS_EXPECTED = {
    "passage_1_reflective": (
        "Người ta hay nghĩ rằng trưởng thành là khi mọi câu hỏi đều có câu trả lời. "
        "Nhưng thật ra, trưởng thành là biết đặt những câu hỏi tốt hơn, và đủ điềm tĩnh "
        "để lắng nghe câu trả lời của chính mình."
    ),
    "passage_2_explanatory": (
        "Một podcast không chỉ là giọng đọc. Điều tạo nên sức hút là nhịp điệu, sự chân "
        "thật, và những khoảng lặng đủ để người nghe tự suy nghĩ. Giọng tốt không át nội "
        "dung, mà đưa nội dung đến gần hơn."
    ),
    "passage_3_storytelling": (
        "Tôi nhớ buổi chiều đứng trước sân ga, chờ một chuyến tàu không hẹn giờ. Lúc ấy "
        "tôi chưa biết rằng những chuyến muộn nhất thường dạy ta kiên nhẫn nhất, và sự "
        "kiên nhẫn ấy luôn có lý do của nó."
    ),
}

INFERENCE_CONFIG = {
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
NUMPY_SEED = 40002


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


def verify_baseline() -> dict:
    manifest = json.loads((BASELINE / "manifest.json").read_text(encoding="utf-8"))
    if manifest.get("name") != "PODCAST_CANDIDATE_B_BASELINE":
        raise RuntimeError("Baseline manifest name mismatch")
    loaded = {}
    for key in ("speaker_emb.npy", "reference_codes.npy"):
        path = BASELINE / key
        record = manifest["files"][key]
        if not path.is_file() or path.stat().st_size != record["size_bytes"]:
            raise RuntimeError(f"Baseline {key} missing or wrong size")
        if sha256_file(path) != record["sha256"]:
            raise RuntimeError(f"Baseline {key} file hash mismatch")
        arr = np.load(path, allow_pickle=False)
        if sha256_array(arr) != record["array_sha256"]:
            raise RuntimeError(f"Baseline {key} array hash mismatch")
        loaded[key] = arr
    return loaded


def verify_texts() -> dict:
    loaded = {}
    for key, expected in TEXTS_EXPECTED.items():
        text = (TEXTS / f"{key}.txt").read_text(encoding="utf-8").strip()
        if text != expected:
            raise RuntimeError(f"Frozen text mismatch for {key}")
        loaded[key] = text
    return loaded


def main() -> None:
    if MANIFEST.exists() or PROVENANCE.exists() or list(AUDIO.glob("*.wav")):
        raise FileExistsError("Phase 40B validation artifacts already exist; no second run")
    if sha256_file(VOICE_ASSET) != EXPECTED_VOICE_ASSET_SHA256:
        raise RuntimeError("Installed VieNeu voice asset hash changed")
    baseline = verify_baseline()
    texts = verify_texts()

    started_utc = datetime.now(timezone.utc).isoformat()
    total_started = time.perf_counter()

    load_started = time.perf_counter()
    tts = Vieneu(backend="onnx")
    load_seconds = time.perf_counter() - load_started
    if tts.backend != "onnx" or tts.sample_rate != 48000:
        raise RuntimeError("Required VieNeu ONNX/48 kHz runtime unavailable")

    probe_emb, probe_codes = tts._resolve_ref(
        {"speaker_emb": baseline["speaker_emb.npy"], "codes": baseline["reference_codes.npy"]},
        None,
        True,
        True,
    )
    if not np.array_equal(probe_emb, baseline["speaker_emb.npy"]):
        raise RuntimeError("Runtime modified the canonical Candidate B embedding")
    if not np.array_equal(probe_codes, baseline["reference_codes.npy"]):
        raise RuntimeError("Runtime modified the canonical Candidate B reference codes")

    AUDIO.mkdir(parents=True, exist_ok=True)
    categories = {
        "passage_1_reflective": "reflective / triết lý",
        "passage_2_explanatory": "explanatory / giảng giải",
        "passage_3_storytelling": "storytelling / kể chuyện có suy ngẫm",
    }
    records = []
    for index, (key, text) in enumerate(texts.items(), 1):
        output = AUDIO / f"{key}.wav"
        temporary = AUDIO / f".{key}.tmp.wav"
        np.random.seed(NUMPY_SEED)
        generation_started = time.perf_counter()
        print(f"[Phase40B] Generating {key} ({index}/3) on CPU.", flush=True)
        waveform = tts.infer(
            text,
            voice={
                "speaker_emb": baseline["speaker_emb.npy"],
                "codes": baseline["reference_codes.npy"],
            },
            **INFERENCE_CONFIG,
        )
        generation_seconds = time.perf_counter() - generation_started
        sf.write(temporary, np.asarray(waveform, dtype=np.float32), tts.sample_rate, subtype="PCM_16")
        tmp_metrics = audio_metrics(temporary)
        if not valid_audio(tmp_metrics):
            raise RuntimeError(f"{key} produced an invalid WAV: {tmp_metrics}")
        temporary.replace(output)
        metrics = audio_metrics(output)
        records.append(
            {
                "passage": key,
                "category": categories[key],
                "text": text,
                "text_chars": len(text),
                "speaker_emb_file": "baseline/PODCAST_CANDIDATE_B_BASELINE/speaker_emb.npy",
                "speaker_emb_sha256": sha256_array(baseline["speaker_emb.npy"]),
                "reference_codes_file": "baseline/PODCAST_CANDIDATE_B_BASELINE/reference_codes.npy",
                "reference_codes_sha256": sha256_array(baseline["reference_codes.npy"]),
                "numpy_seed": NUMPY_SEED,
                "generation_seconds": round(generation_seconds, 3),
                "rtf": round(generation_seconds / metrics["duration_seconds"], 3),
                "peak_process_rss_mib": round(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1024.0, 3),
                "audio": metrics,
            }
        )
        print(f"[Phase40B] {key} saved ({metrics['duration_seconds']:.3f} s).", flush=True)

    names = sorted(path.name for path in AUDIO.glob("*.wav"))
    if names != [f"{key}.wav" for key in texts]:
        raise RuntimeError(f"Unexpected primary validation set: {names}")

    completed_utc = datetime.now(timezone.utc).isoformat()
    total_seconds = time.perf_counter() - total_started
    try:
        repo_commit = subprocess.check_output(
            ["git", "-C", str(PROJECT), "rev-parse", "HEAD"], text=True
        ).strip()
    except Exception:
        repo_commit = "UNKNOWN"

    manifest = {
        "phase": "40B",
        "task": "cross_text_validation",
        "execution_status": "PASS",
        "human_gate": "PENDING HUMAN QA",
        "candidate": "B",
        "embedding_formula": {"Phạm Tuyên": 0.75, "Thanh Bình": 0.25},
        "embedding_normalization_applied": False,
        "reference_codes_preset": "Thanh Bình",
        "reference_codes_styles": "Bắc - kể chuyện",
        "inference_config": INFERENCE_CONFIG,
        "numpy_seed": NUMPY_SEED,
        "records": records,
    }
    provenance = {
        "phase": "40B",
        "task": "cross_text_validation",
        "baseline_package": "experiments/brand_voice_phase40b/baseline/PODCAST_CANDIDATE_B_BASELINE",
        "canonical_source": (
            "Canonical .npy files from the frozen baseline package, used directly by "
            "the native Vieneu runtime. The rounded data/voices/voices.json copy is "
            "UI/library-only and was NOT used here."
        ),
        "phase40a_human_qa": {"A": "NO", "B": "INTERESTING", "C": "NO", "D": "NO"},
        "production_modified": False,
        "production_voice_storage_modified": False,
        "user_voice_used": False,
        "new_model_downloaded": False,
        "tuning_or_variants": False,
        "post_processing": False,
        "started_utc": started_utc,
        "completed_utc": completed_utc,
        "repository_commit_before_phase40b": repo_commit,
        "python": sys.version,
        "platform": platform.platform(),
        "vieneu_version": version("vieneu"),
        "backend": "onnx",
        "device": "cpu",
        "sample_rate_hz": tts.sample_rate,
        "voice_asset_path": str(VOICE_ASSET),
        "voice_asset_sha256": EXPECTED_VOICE_ASSET_SHA256,
        "model_load_seconds": round(load_seconds, 3),
        "total_wall_seconds": round(total_seconds, 3),
        "peak_process_rss_mib": round(
            resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1024.0, 3
        ),
    }

    MANIFEST.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    PROVENANCE.write_text(
        json.dumps(provenance, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print("PHASE40B_CROSS_TEXT_VALIDATION_READY", flush=True)


if __name__ == "__main__":
    main()