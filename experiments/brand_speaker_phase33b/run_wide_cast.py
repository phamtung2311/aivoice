#!/usr/bin/env python3
"""Phase 33B: finite CPU-only Qwen VoiceDesign -> VieNeu identity-transfer PoC.

This is isolated R&D. It creates exactly four source designs and four Vietnamese
probes, preserves all raw artefacts locally, and exposes only randomized audition
copies. It neither reads user recordings nor mutates production state.
"""
from __future__ import annotations

import gc
import hashlib
import json
import os
import random
import resource
import shutil
import sys
import time
from pathlib import Path

os.environ.setdefault("HF_HUB_OFFLINE", "1")
os.environ.setdefault("TRANSFORMERS_OFFLINE", "1")

import numpy as np
import psutil
import soundfile as sf
import torch
from qwen_tts import Qwen3TTSModel

HERE = Path(__file__).resolve().parent
PROJECT = HERE.parents[1]
QWEN_ROOT = PROJECT / "experiments" / "special_voice_podcast" / "qwen_voice_factory"
MODEL = QWEN_ROOT / "models" / "Qwen3-TTS-12Hz-1.7B-VoiceDesign"
SOURCES = HERE / "sources"
CONDITIONING = HERE / "conditioning"
RAW = HERE / "raw_vietnamese"
AUDITION = HERE / "audition"
METRICS = HERE / "metrics" / "metrics.json"
PRIVATE_MAPPING = HERE / "private_mapping.json"

SOURCE_TEXT = "A quiet evening settles over the city. I speak clearly, naturally, and without rushing."
VIETNAMESE_TEXT = (
    "Có những ngày chúng ta không cần phải nói thật nhiều. Chỉ cần một giọng nói rõ ràng, "
    "một nhịp kể vừa phải, và vài phút bình yên để nghe lại điều mình đang nghĩ. "
    "Câu chuyện này bắt đầu rất đơn giản, rồi từ từ mở ra theo cách tự nhiên nhất."
)
SAMPLING = {"temperature": 0.80, "top_k": 25, "top_p": 0.95, "repetition_penalty": 1.20}
SPEED = 1.0
SEED = 33117
TARGET_RMS = 0.09
PEAK_CEILING = 0.95

# These are identity briefs, not acting directions. The text, language, speed and
# all bridge settings stay fixed. Labels never appear in the public audition.
CANDIDATES = {
    "A": "An adult male voice with a genuinely low perceived register, dense dark chest resonance, substantial vocal weight, a smooth rounded surface, and calm natural articulation. It should sound like a real person, not a bass effect: neutral delivery, no theatrical emotion, no accent, no rasp.",
    "B": "An adult male voice with a medium-to-medium-high perceived register, lean vocal body, dry close resonance, crisp precise articulation, and a faint natural grain. Keep it neutral and real: low bass, little breathiness, no acting, no accent, no exaggerated pace.",
    "C": "A young adult male voice with a clearly brighter higher register, light vocal weight, open forward resonance, clean smooth timbre, and clear airy-but-not-breathy articulation. Neutral and natural, not excited, not accented, not theatrical.",
    "D": "A mature adult male voice with a medium-low register, dark-neutral back resonance, a controlled matte texture with restrained natural grain, and a firm broad vocal body. It must be clearly unlike a smooth bass narrator: neutral delivery, no forced rasp, no accent, no acting.",
}


def say(message: str) -> None:
    print(message, flush=True)


def peak_rss_mb() -> float:
    return round(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1024, 2)


def memory() -> dict:
    vm, swap = psutil.virtual_memory(), psutil.swap_memory()
    return {"ram_available_bytes": vm.available, "ram_used_bytes": vm.used, "swap_used_bytes": swap.used}


def audio_metrics(path: Path) -> dict:
    data, rate = sf.read(path, always_2d=True)
    mono = data.mean(axis=1)
    peak = float(np.max(np.abs(mono))) if mono.size else 0.0
    rms = float(np.sqrt(np.mean(np.square(mono)))) if mono.size else 0.0
    clipped = int(np.count_nonzero(np.abs(mono) >= 0.999))
    return {
        "duration_seconds": round(float(mono.size / rate), 3),
        "sample_rate": int(rate),
        "channels": int(data.shape[1]),
        "peak": round(peak, 6),
        "rms": round(rms, 6),
        "clipped_samples": clipped,
        "clipping_ratio": round(clipped / max(1, mono.size), 8),
        "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
    }


def valid(metrics: dict, *, expected_rate: int | None = None) -> bool:
    return (
        metrics["duration_seconds"] > 0
        and metrics["channels"] == 1
        and metrics["clipping_ratio"] <= 0.01
        and (expected_rate is None or metrics["sample_rate"] == expected_rate)
    )


def normalize_for_audition(data: np.ndarray) -> tuple[np.ndarray, float]:
    mono = np.asarray(data, dtype=np.float32)
    rms = float(np.sqrt(np.mean(np.square(mono))))
    peak = float(np.max(np.abs(mono)))
    gain = TARGET_RMS / rms if rms > 1e-9 else 1.0
    if peak > 1e-9:
        gain = min(gain, PEAK_CEILING / peak)
    return (mono * gain).astype(np.float32), round(gain, 6)


def ensure_layout() -> None:
    for directory in (SOURCES, CONDITIONING, RAW, AUDITION, METRICS.parent):
        directory.mkdir(parents=True, exist_ok=True)


def require_local_model() -> None:
    required = (MODEL / "model.safetensors", MODEL / "speech_tokenizer" / "model.safetensors")
    if not MODEL.is_dir() or not all(path.is_file() for path in required):
        raise SystemExit("LOCAL_QWEN_MODEL_REQUIRED")
    if memory()["ram_available_bytes"] < 7 * 2**30:
        raise SystemExit("QWEN_RAM_BLOCKED: at least 7 GiB available RAM is required")


def run_qwen_sources() -> list[dict]:
    existing = []
    for identity in CANDIDATES:
        path = SOURCES / f"source_{identity}.wav"
        if path.is_file() and valid(audio_metrics(path)):
            existing.append({"identity": identity, "preserved_existing": True, "audio": audio_metrics(path)})
    if len(existing) == len(CANDIDATES):
        say("[Qwen] Four valid sources already exist; preserving them.")
        return existing
    if existing:
        raise SystemExit("PARTIAL_SOURCE_SET_REFUSED: delete only the incomplete Phase 33B artefacts before a clean retry")

    say("[Qwen] Loading local VoiceDesign checkpoint on CPU.")
    started_load = time.perf_counter()
    model = Qwen3TTSModel.from_pretrained(str(MODEL), device_map="cpu", dtype=torch.bfloat16, attn_implementation="eager")
    records = []
    try:
        for position, (identity, instruction) in enumerate(CANDIDATES.items(), start=1):
            target = SOURCES / f"source_{identity}.wav"
            temporary = target.with_name(f".{target.stem}.tmp.wav")
            started = time.perf_counter()
            say(f"[Qwen {position}/4] Generating source {identity}.")
            with torch.inference_mode():
                wavs, rate = model.generate_voice_design(text=SOURCE_TEXT, language="English", instruct=instruction)
            sf.write(temporary, wavs[0], rate)
            metrics = audio_metrics(temporary)
            if not valid(metrics):
                raise RuntimeError(f"QWEN_SOURCE_INVALID {identity}: {metrics}")
            temporary.replace(target)
            records.append({
                "identity": identity,
                "generation_seconds": round(time.perf_counter() - started, 3),
                "peak_process_rss_mb": peak_rss_mb(),
                "audio": audio_metrics(target),
            })
            say(f"[Qwen {position}/4] saved {metrics['duration_seconds']:.2f}s.")
    finally:
        del model
        gc.collect()
    return [{"qwen_load_seconds": round(time.perf_counter() - started_load, 3), **record} for record in records]


def run_vieneu_transfer(source_records: list[dict]) -> list[dict]:
    sys.path.insert(0, str(PROJECT))
    from backend.app.tts.engine import TTSEngine

    engine = TTSEngine(backend="onnx")
    records = []
    try:
        for position, identity in enumerate(CANDIDATES, start=1):
            source = SOURCES / f"source_{identity}.wav"
            source_audio = audio_metrics(source)
            emb_path = CONDITIONING / f"speaker_emb_{identity}.npy"
            codes_path = CONDITIONING / f"reference_codes_{identity}.npy"
            if emb_path.exists() != codes_path.exists():
                raise SystemExit(f"INCOMPLETE_CONDITIONING: {identity}")
            if emb_path.exists():
                speaker_emb = np.load(emb_path, allow_pickle=False)
                codes = np.load(codes_path, allow_pickle=False)
                encode_seconds = None
            else:
                started_encode = time.perf_counter()
                speaker_emb, codes = engine._model.encode_reference(str(source), denoise=False, use_ref_codes=True)
                encode_seconds = round(time.perf_counter() - started_encode, 3)
                np.save(emb_path, np.asarray(speaker_emb))
                np.save(codes_path, np.asarray(codes))
            if np.asarray(speaker_emb).shape != (192,) or np.asarray(codes).ndim != 2:
                raise RuntimeError(f"CONDITIONING_SHAPE_INVALID {identity}")
            target = RAW / f"vietnamese_{identity}.wav"
            if target.is_file() and valid(audio_metrics(target), expected_rate=48000):
                records.append({"identity": identity, "source_audio": source_audio, "preserved_existing": True, "audio": audio_metrics(target)})
                continue
            temporary = target.with_name(f".{target.stem}.tmp.wav")
            started = time.perf_counter()
            np.random.seed(SEED)
            say(f"[VieNeu {position}/4] Encoding verified; synthesizing probe {identity}.")
            engine.generate(
                VIETNAMESE_TEXT,
                voice={"speaker_emb": speaker_emb, "codes": codes},
                speed=SPEED,
                out_path=str(temporary),
                max_chunk_chars=240,
                denoise=False,
                use_ref_codes=True,
                quality_diagnostics=True,
                **SAMPLING,
            )
            metrics = audio_metrics(temporary)
            if not valid(metrics, expected_rate=48000):
                raise RuntimeError(f"VIENEU_OUTPUT_INVALID {identity}: {metrics}")
            temporary.replace(target)
            records.append({
                "identity": identity,
                "source_audio": source_audio,
                "encode_seconds": encode_seconds,
                "generation_seconds": round(time.perf_counter() - started, 3),
                "speaker_emb_shape": list(np.asarray(speaker_emb).shape),
                "reference_codes_shape": list(np.asarray(codes).shape),
                "audio": audio_metrics(target),
                "peak_process_rss_mb": peak_rss_mb(),
                "generation_diagnostics": engine.last_generation_diagnostics,
            })
    finally:
        del engine
        gc.collect()
    return records


def build_blind_audition() -> dict:
    if PRIVATE_MAPPING.exists():
        mapping = json.loads(PRIVATE_MAPPING.read_text(encoding="utf-8"))
        if set(mapping) != {f"Candidate {number:02d}.wav" for number in range(1, 5)} or set(mapping.values()) != set(CANDIDATES):
            raise SystemExit("PRIVATE_MAPPING_INVALID")
    else:
        identities = list(CANDIDATES)
        random.Random(SEED).shuffle(identities)
        mapping = {f"Candidate {number:02d}.wav": identity for number, identity in enumerate(identities, start=1)}
        PRIVATE_MAPPING.write_text(json.dumps(mapping, indent=2) + "\n", encoding="utf-8")
    for name, identity in mapping.items():
        raw_path = RAW / f"vietnamese_{identity}.wav"
        data, rate = sf.read(raw_path, dtype="float32", always_2d=False)
        presented, gain = normalize_for_audition(data)
        audition_path = AUDITION / name
        sf.write(audition_path, presented, rate, subtype="PCM_16")
        metrics = audio_metrics(audition_path)
        if metrics["clipped_samples"]:
            raise RuntimeError(f"AUDITION_CLIPPED {name}")
        mapping[name] = {"identity": identity, "presentation_gain": gain, "audition_audio": metrics}
    # Keep identity values in the local private mapping only. The public audition
    # folder intentionally contains no text, source clip or explanatory metadata.
    private = {name: item["identity"] for name, item in mapping.items()}
    presentation = {name: {"gain": item["presentation_gain"], "audio": item["audition_audio"]} for name, item in mapping.items()}
    PRIVATE_MAPPING.write_text(json.dumps(private, indent=2) + "\n", encoding="utf-8")
    return presentation


def main() -> int:
    ensure_layout()
    require_local_model()
    before = memory()
    say(f"[Phase33B] CPU sequential run. Available RAM: {before['ram_available_bytes'] / 2**30:.2f} GiB.")
    source_records = run_qwen_sources()
    transfer_records = run_vieneu_transfer(source_records)
    if len(source_records) != 4 or len(transfer_records) != 4:
        raise RuntimeError("PHASE33B_INCOMPLETE")
    presentation = build_blind_audition()
    result = {
        "phase": "33B",
        "purpose": "wide Qwen VoiceDesign identity-transfer PoC",
        "offline": True,
        "device": "cpu",
        "source_text_language": "English",
        "vietnamese_text": VIETNAMESE_TEXT,
        "settings": {"sampling": SAMPLING, "speed": SPEED, "max_chunk_chars": 240, "denoise": False, "use_ref_codes": True, "seed": SEED},
        "memory_before": before,
        "sources": source_records,
        "transfers": transfer_records,
        "audition_presentation": presentation,
    }
    METRICS.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    say("PHASE33B_WIDE_CAST_AUDITION_READY")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        say(f"PHASE33B_FAILED: {exc!r}")
        raise
