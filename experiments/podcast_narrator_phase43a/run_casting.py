#!/usr/bin/env python3
"""Phase 43A: bounded, raw two-text synthetic narrator casting on local CPU.

This is intentionally a casting runner, not a prosody/long-form optimization
pipeline.  Each identity is a new convex combination of installed synthetic
male speaker embeddings; all use the same reference-code policy and inference
controls for both audition texts.
"""

from __future__ import annotations

import hashlib
import json
import os
import time
import argparse
from datetime import datetime, timezone
from importlib.metadata import version
from pathlib import Path

import numpy as np
import soundfile as sf
import vieneu
from vieneu import Vieneu


ROOT = Path(__file__).resolve().parent
VOICES = ROOT / "voices"
METADATA = ROOT / "metadata"
MANIFEST = METADATA / "casting_manifest.json"
VOICE_ASSET = Path(vieneu.__file__).resolve().parent / "assets" / "voices_v3_turbo.json"
EXPECTED_ASSET_SHA256 = "574e6acf03823c4cafdc43f106731ce5fce6de30228fe383831b8b9064ee0bd8"
REFERENCE_CODE_ANCHOR = "Thanh Bình"
MAX_ATTEMPTS = 3
TARGET_PEAK = 10 ** (-1 / 20)

TEXTS = {
    "A": """Có những ngày, chúng ta cảm thấy mình đã cố gắng rất nhiều,
nhưng mọi thứ dường như vẫn đứng yên.

Ta nhìn những người xung quanh,
rồi bất giác tự hỏi vì sao họ có thể đi nhanh đến vậy,
còn mình vẫn loay hoay với những điều rất nhỏ.

Nhưng có lẽ,
cuộc sống chưa bao giờ yêu cầu tất cả chúng ta phải đi cùng một tốc độ.

Có người cần đi thật xa mới hiểu mình muốn gì.
Cũng có người chỉ cần dừng lại một chút,
rồi nhận ra điều mình tìm kiếm vẫn luôn ở rất gần.""",
    "B": """Chiều hôm ấy, trời không mưa,
nhưng những đám mây vẫn phủ kín phía cuối con đường.

Anh đóng cửa sổ,
đặt cốc trà xuống bàn,
rồi ngồi im một lúc lâu.

Không có chuyện gì đặc biệt xảy ra.

Chỉ là sau rất nhiều ngày bận rộn,
anh bỗng nhận ra mình đã lâu lắm rồi
không thật sự ngồi xuống để nghe xem trong lòng mình đang nghĩ gì.

Đôi khi,
một khoảng lặng nhỏ lại khiến chúng ta hiểu được nhiều điều
hơn cả những ngày chạy thật nhanh.""",
}

# All values are convex weights of three installed *synthetic* Northern-male
# presets.  No built-in identity is passed through unchanged.
IDENTITIES = {
    "01": {
        "label": "DEEP WARM",
        "definition": "Nam trưởng thành; medium-low đến low, ấm, chest resonance vừa phải, mềm và điềm tĩnh.",
        "weights": {"Thanh Bình": 0.70, "Phạm Tuyên": 0.20, "Minh Đức": 0.10},
    },
    "02": {
        "label": "DARK TEXTURED",
        "definition": "Nam trưởng thành; medium-low, dark-neutral/matte texture nhẹ, có dấu ấn nhưng không theatrical.",
        "weights": {"Thanh Bình": 0.15, "Phạm Tuyên": 0.75, "Minh Đức": 0.10},
    },
    "03": {
        "label": "CALM AUTHORITY",
        "definition": "Nam trưởng thành; chắc, điềm tĩnh, có trọng lượng, kết câu tự nhiên hơi rơi.",
        "weights": {"Thanh Bình": 0.15, "Phạm Tuyên": 0.10, "Minh Đức": 0.75},
    },
    "04": {
        "label": "INTIMATE NIGHT PODCAST",
        "definition": "Nam low-medium; gần gũi, âm lượng cảm giác vừa phải, ít cảm giác đọc bài; không whisper/ASMR.",
        "weights": {"Thanh Bình": 0.55, "Phạm Tuyên": 0.40, "Minh Đức": 0.05},
    },
    "05": {
        "label": "REFLECTIVE PHILOSOPHER",
        "definition": "Nam trưởng thành trầm vừa; suy tư, có chiều sâu và semantic emphasis nhẹ; không giảng đạo.",
        "weights": {"Thanh Bình": 0.45, "Phạm Tuyên": 0.05, "Minh Đức": 0.50},
    },
    "06": {
        "label": "WARM STORYTELLER",
        "definition": "Nam ấm; conversational storytelling, cảm xúc kiềm chế, chuyển câu mềm.",
        "weights": {"Thanh Bình": 0.10, "Phạm Tuyên": 0.45, "Minh Đức": 0.45},
    },
    "07": {
        "label": "SOFT BARITONE",
        "definition": "Nam baritone nhẹ; body tốt, smooth, không bass-heavy/booming/radio.",
        "weights": {"Thanh Bình": 0.65, "Phạm Tuyên": 0.10, "Minh Đức": 0.25},
    },
    "08": {
        "label": "NATURAL MATURE",
        "definition": "Nam trưởng thành phổ thông; natural-first, chiều sâu vừa đủ, không cố tạo character.",
        "weights": {"Thanh Bình": 0.25, "Phạm Tuyên": 0.55, "Minh Đức": 0.20},
    },
}

INFERENCE = {
    "denoise": True,
    "use_ref_codes": True,
    "temperature": 0.8,
    "top_k": 25,
    "top_p": 0.95,
    "max_new_frames": 800,
    "repetition_penalty": 1.2,
    "repetition_window": 64,
    "max_chars": 800,
    "silence_p": 0.15,
    "crossfade_p": 0.0,
    "apply_watermark": True,
    "batch_size": 1,
}


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def sha256_array(array: np.ndarray) -> str:
    return hashlib.sha256(np.ascontiguousarray(array).tobytes()).hexdigest()


def metrics(array: np.ndarray, sample_rate: int) -> dict:
    mono = np.asarray(array, dtype=np.float32).reshape(-1)
    peak = float(np.max(np.abs(mono))) if mono.size else 0.0
    return {
        "duration_seconds": len(mono) / sample_rate,
        "frames": int(len(mono)),
        "sample_rate_hz": sample_rate,
        "channels": 1,
        "finite": bool(np.isfinite(mono).all()),
        "peak_abs": peak,
        "rms": float(np.sqrt(np.mean(np.square(mono, dtype=np.float64)))) if mono.size else 0.0,
    }


def valid(record: dict) -> bool:
    return (
        record["finite"]
        and 10.0 <= record["duration_seconds"] <= 180.0
        and record["peak_abs"] > 0.001
        and record["rms"] > 0.0001
    )


def valid_existing_wav(path: Path) -> tuple[dict, str] | None:
    """Return verified metrics/hash for a recoverable prior WAV, never rewriting it."""
    try:
        info = sf.info(path)
        if info.samplerate != 48000 or info.channels != 1 or info.subtype != "PCM_16":
            return None
        audio, sample_rate = sf.read(path, dtype="float32", always_2d=False)
        result = metrics(audio, sample_rate)
        if not valid(result):
            return None
        return result, sha256_file(path)
    except Exception:
        return None


def write_manifest(data: dict) -> None:
    METADATA.mkdir(parents=True, exist_ok=True)
    temporary = MANIFEST.with_suffix(".tmp")
    temporary.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    os.replace(temporary, MANIFEST)


def blend(presets: dict, weights: dict[str, float]) -> np.ndarray:
    if not np.isclose(sum(weights.values()), 1.0) or any(value < 0.0 for value in weights.values()):
        raise RuntimeError(f"Invalid non-convex weights: {weights}")
    return sum(
        np.float32(weight) * np.asarray(presets[name]["speaker_emb"], dtype=np.float32)
        for name, weight in weights.items()
    ).astype(np.float32)


def main() -> None:
    parser = argparse.ArgumentParser(description="Run or resume bounded Phase 43A casting")
    parser.add_argument("--voice", choices=tuple(IDENTITIES), help="Run one identity only")
    parser.add_argument("--text", choices=tuple(TEXTS), help="Run one text only (requires --voice)")
    args = parser.parse_args()
    if args.text and not args.voice:
        parser.error("--text requires --voice")
    if sha256_file(VOICE_ASSET) != EXPECTED_ASSET_SHA256:
        raise RuntimeError("Installed VieNeu voice asset hash differs from the audited Phase 40A asset")

    asset = json.loads(VOICE_ASSET.read_text(encoding="utf-8"))
    presets = asset["presets"]
    if any(name not in presets or presets[name].get("gender") != "male" for name in ("Thanh Bình", "Phạm Tuyên", "Minh Đức")):
        raise RuntimeError("Expected Northern male preset inventory is unavailable")
    reference_codes = np.asarray(presets[REFERENCE_CODE_ANCHOR]["codes"], dtype=np.int64)
    vectors = {identity: blend(presets, details["weights"]) for identity, details in IDENTITIES.items()}
    if len({sha256_array(vector) for vector in vectors.values()}) != len(vectors):
        raise RuntimeError("Casting identities unexpectedly collide")

    if MANIFEST.exists():
        manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
        if manifest.get("phase") != "43A" or manifest.get("status") == "COMPLETE — HUMAN QA PENDING":
            raise RuntimeError("Refusing to overwrite a completed or non-Phase-43A casting manifest")
        existing = {(entry["voice"], entry["text"]): entry for entry in manifest.get("outputs", [])}
        for key, entry in existing.items():
            selected = entry.get("selected")
            if selected is None:
                continue
            path = ROOT / selected["path"]
            verified = valid_existing_wav(path) if path.is_file() else None
            if verified is not None and verified[1] != selected["sha256"]:
                # Interrupted concurrent writers may leave a technically valid
                # final file paired with a stale manifest hash.  The filesystem
                # artifact is authoritative here: preserve it and record the
                # reconciliation; never regenerate or overwrite it.
                observed_metrics, observed_sha256 = verified
                selected["sha256"] = observed_sha256
                selected["size_bytes"] = path.stat().st_size
                selected["final_metrics"] = observed_metrics
                entry["integrity_events"] = entry.get("integrity_events", []) + [{
                    "event": "reconciled stale-manifest hash against valid existing WAV without rerender",
                    "verified_sha256": observed_sha256,
                }]
                write_manifest(manifest)
            elif not path.is_file() or verified is None:
                # A sandbox-interrupted process can leave a later concurrent write
                # after its earlier manifest record. Preserve the mismatching file
                # for audit, then permit one bounded technical retry for this slot.
                quarantine = METADATA / "quarantine"
                quarantine.mkdir(parents=True, exist_ok=True)
                if path.exists():
                    archived = quarantine / f"{path.stem}.integrity-mismatch.{int(time.time())}{path.suffix}"
                    os.replace(path, archived)
                else:
                    archived = None
                entry["integrity_events"] = entry.get("integrity_events", []) + [{
                    "event": "post-interruption hash mismatch",
                    "expected_sha256": selected["sha256"],
                    "observed_sha256": sha256_file(archived) if archived else None,
                    "quarantined_path": str(archived.relative_to(ROOT)) if archived else None,
                }]
                entry["selected"] = None
                write_manifest(manifest)
                print(f"[Phase43A] {key}: mismatching artifact quarantined; bounded retry permitted", flush=True)
        print(f"[Phase43A] Resuming {len(existing)} recorded output slots.", flush=True)
    else:
        VOICES.mkdir(parents=True, exist_ok=False)
        started = datetime.now(timezone.utc).isoformat()
        manifest = {
        "phase": "43A",
        "status": "RUNNING",
        "started_utc": started,
        "engine": {
            "package": "vieneu",
            "version": version("vieneu"),
            "backend": "onnx",
            "sample_rate_hz": 48000,
            "voice_asset": str(VOICE_ASSET),
            "voice_asset_sha256": EXPECTED_ASSET_SHA256,
            "package_license": "Apache-2.0 per installed package metadata; model-weight commercial terms not independently re-audited in this casting-only phase",
        },
        "policy": {
            "synthetic_only": True,
            "owner_audio_used": False,
            "candidate03_used": False,
            "raw_casting": "No Phase 41E/41F/41H prosody, manual pause, tempo, pitch, EQ, compression, or formant treatment.",
            "attempt_limit_per_voice_text": MAX_ATTEMPTS,
            "stochastic_note": "VieNeu exposes no supported deterministic seed; no seed claim is made.",
            "normalization": "Per-file PCM peak normalization to -1 dBFS only; no EQ, compression, pitch, formant, or tempo processing.",
        },
        "reference_code_policy": {
            "anchor": REFERENCE_CODE_ANCHOR,
            "shape": list(reference_codes.shape),
            "sha256_array": sha256_array(reference_codes),
            "reason": "same installed Northern storytelling reference-code policy for every synthetic blend; no candidate receives bespoke codes",
        },
        "texts": {
            key: {"exact_text": text, "sha256_utf8": hashlib.sha256(text.encode("utf-8")).hexdigest()}
            for key, text in TEXTS.items()
        },
        "inference": INFERENCE,
        "identities": {
            identity: {
                **details,
                "speaker_emb_shape": list(vectors[identity].shape),
                "speaker_emb_sha256": sha256_array(vectors[identity]),
                "speaker_emb_norm": float(np.linalg.norm(vectors[identity])),
            }
            for identity, details in IDENTITIES.items()
        },
            "outputs": [],
        }
        write_manifest(manifest)

    engine = Vieneu(backend="onnx")
    if engine.backend != "onnx" or engine.sample_rate != 48000:
        raise RuntimeError("Required local VieNeu ONNX / 48-kHz runtime unavailable")

    identity_items = [(args.voice, IDENTITIES[args.voice])] if args.voice else list(IDENTITIES.items())
    text_items = [(args.text, TEXTS[args.text])] if args.text else list(TEXTS.items())
    for identity, details in identity_items:
        for text_key, text in text_items:
            existing_entry = next(
                (entry for entry in manifest["outputs"] if entry["voice"] == f"VOICE {identity}" and entry["text"] == text_key),
                None,
            )
            if existing_entry and existing_entry.get("selected") is not None:
                print(f"[Phase43A] VOICE {identity} text {text_key}: verified existing output reused", flush=True)
                continue
            destination = VOICES / f"voice{identity}_{text_key}.wav"
            attempts = list(existing_entry.get("attempts", [])) if existing_entry else []
            selected = None
            recovered = valid_existing_wav(destination) if destination.is_file() else None
            if recovered is not None and existing_entry is None:
                # A process may have completed its atomic WAV write immediately
                # before interruption.  Adopt only an already-valid target;
                # this keeps the generation policy intact and never overwrites it.
                recovered_metrics, recovered_sha256 = recovered
                selected = {
                    "attempt": 1,
                    "result": "ACCEPTED_TECHNICAL_RECOVERED_EXISTING",
                    "generation_seconds": None,
                    "final_metrics": recovered_metrics,
                    "path": str(destination.relative_to(ROOT)),
                    "sha256": recovered_sha256,
                    "size_bytes": destination.stat().st_size,
                }
                attempts.append(selected)
                print(f"[Phase43A] VOICE {identity} text {text_key}: valid existing output adopted", flush=True)
            for attempt in range(len(attempts) + 1, MAX_ATTEMPTS + 1):
                if selected is not None:
                    break
                started_attempt = time.perf_counter()
                try:
                    waveform = engine.infer(
                        text,
                        voice={"speaker_emb": vectors[identity], "codes": reference_codes},
                        **INFERENCE,
                    )
                    raw = metrics(waveform, engine.sample_rate)
                    if not valid(raw):
                        raise RuntimeError(f"technical invalid waveform: {raw}")
                    scale = TARGET_PEAK / raw["peak_abs"]
                    normalized = np.asarray(waveform, dtype=np.float32).reshape(-1) * np.float32(scale)
                    final = metrics(normalized, engine.sample_rate)
                    temporary = destination.with_suffix(".tmp.wav")
                    sf.write(temporary, normalized, engine.sample_rate, subtype="PCM_16")
                    os.replace(temporary, destination)
                    info = sf.info(destination)
                    if info.samplerate != 48000 or info.channels != 1 or info.frames != final["frames"]:
                        raise RuntimeError("written WAV header does not match generated audio")
                    selected = {
                        "attempt": attempt,
                        "result": "ACCEPTED_TECHNICAL",
                        "generation_seconds": time.perf_counter() - started_attempt,
                        "raw_metrics": raw,
                        "peak_normalization_gain": float(scale),
                        "final_metrics": final,
                        "path": str(destination.relative_to(ROOT)),
                        "sha256": sha256_file(destination),
                        "size_bytes": destination.stat().st_size,
                    }
                    attempts.append(selected)
                    break
                except Exception as error:
                    attempts.append(
                        {
                            "attempt": attempt,
                            "result": "TECHNICAL_DEFECT",
                            "generation_seconds": time.perf_counter() - started_attempt,
                            "error": f"{type(error).__name__}: {error}",
                        }
                    )
            entry = {
                    "voice": f"VOICE {identity}",
                    "identity_label": details["label"],
                    "text": text_key,
                    "attempt_count": len(attempts),
                    "attempts": attempts,
                    "selected": selected,
                }
            if existing_entry is not None:
                manifest["outputs"][manifest["outputs"].index(existing_entry)] = entry
            else:
                manifest["outputs"].append(entry)
            write_manifest(manifest)
            if selected is None:
                manifest["status"] = "TECHNICAL_INCOMPLETE"
                write_manifest(manifest)
                raise RuntimeError(f"VOICE {identity} text {text_key} exhausted {MAX_ATTEMPTS} technical attempts")
            print(f"[Phase43A] VOICE {identity} text {text_key}: attempt {selected['attempt']} accepted", flush=True)

    all_done = (
        len(manifest["outputs"]) == len(IDENTITIES) * len(TEXTS)
        and all(entry.get("selected") is not None for entry in manifest["outputs"])
    )
    manifest["status"] = "COMPLETE — HUMAN QA PENDING" if all_done else "RUNNING"
    if all_done:
        manifest["completed_utc"] = datetime.now(timezone.utc).isoformat()
    write_manifest(manifest)
    print("PHASE43A_CASTING_COMPLETE" if all_done else "PHASE43A_CASTING_PARTIAL", flush=True)


if __name__ == "__main__":
    main()
