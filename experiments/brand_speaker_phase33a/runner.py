#!/usr/bin/env python3
"""Finite Phase 33A blind speaker-identity cast.  Isolated R&D only."""
from __future__ import annotations

import hashlib
import json
import random
import shutil
import sys
import time
import argparse
from pathlib import Path

import numpy as np
import soundfile as sf

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))

# Private order deliberately avoids keeper labels in user-facing files.
CANDIDATES = [
    "phase30i_01",  # selected for distinct controlled texture
    "phase30i_02",  # selected for clean character contrast
    "g2_01",        # selected for fuller warm resonance
    "g2_05",        # selected for mature weighted resonance
]
PASSAGES = [
    (
        "conversational",
        "Có lúc tôi chỉ cần một người ngồi cạnh và hỏi: hôm nay của bạn thế nào? Không cần câu trả lời thật hay. Chúng ta có thể nói về một việc nhỏ, về ly cà phê đã nguội, hoặc về con đường vừa đi qua. Điều quan trọng là cuộc trò chuyện này được bắt đầu một cách bình thường, rồi chậm rãi trở nên gần gũi hơn.",
    ),
    (
        "reflective",
        "Buổi chiều đi qua rất nhẹ. Ánh sáng trên bàn đổi màu, tiếng xe ngoài phố cũng thưa dần, và tôi nhận ra mình đã lâu không dành một khoảng yên cho chính mình. Có vài điều chưa cần giải quyết ngay. Chỉ cần gọi đúng tên cảm giác đang có, thở chậm hơn một chút, rồi để ngày hôm nay khép lại tử tế.",
    ),
    (
        "informative",
        "Khi bắt đầu một dự án mới, hãy chia công việc thành những bước có thể kiểm tra. Trước hết xác định mục tiêu và người sẽ sử dụng kết quả. Sau đó chọn một cách đo đơn giản để biết điều gì đang hiệu quả. Mỗi tuần xem lại dữ liệu, ghi rõ điều cần sửa, rồi ưu tiên thay đổi nhỏ nhưng có bằng chứng thay vì làm lại mọi thứ cùng lúc.",
    ),
]
SAMPLING = {"temperature": 0.80, "top_k": 25, "top_p": 0.95, "repetition_penalty": 1.20}
TARGET_RMS = 0.09
PEAK_CEILING = 0.95
SEED = 33041


def metrics(audio: np.ndarray, sr: int) -> dict:
    x = np.asarray(audio, dtype=np.float32)
    return {
        "duration_seconds": round(float(len(x) / sr), 3),
        "sample_rate": int(sr),
        "channels": 1 if x.ndim == 1 else int(x.shape[1]),
        "peak": round(float(np.max(np.abs(x))), 6),
        "rms": round(float(np.sqrt(np.mean(np.square(x)))), 6),
        "clipped_samples": int(np.count_nonzero(np.abs(x) >= 1.0)),
        "sha256": hashlib.sha256(x.tobytes()).hexdigest(),
    }


def normalize_for_audition(audio: np.ndarray) -> tuple[np.ndarray, float]:
    x = np.asarray(audio, dtype=np.float32)
    rms = float(np.sqrt(np.mean(np.square(x))))
    peak = float(np.max(np.abs(x)))
    gain = TARGET_RMS / rms if rms > 1e-9 else 1.0
    if peak > 1e-9:
        gain = min(gain, PEAK_CEILING / peak)
    return (x * gain).astype(np.float32), float(gain)


def copy_profile(keeper: str, private_name: str) -> dict:
    src = ROOT / "experiments/special_voice_podcast/keepers" / keeper
    dst = HERE / "source_profiles" / private_name
    dst.mkdir(parents=True, exist_ok=True)
    for name in ("speaker_emb.npy", "reference_codes.npy", "metadata.json"):
        shutil.copy2(src / name, dst / name)
    return {
        "speaker_emb": np.load(dst / "speaker_emb.npy", allow_pickle=False),
        "codes": np.load(dst / "reference_codes.npy", allow_pickle=False),
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--from-clip", type=int, default=1, help="resume generation without reprocessing earlier clips")
    parser.add_argument("--rescue-clip", type=int, help="render one stalled clip as the same fixed sentence chunks")
    args = parser.parse_args()
    if not 1 <= args.from_clip <= 12:
        raise SystemExit("--from-clip must be in 1..12")
    from backend.app.tts.engine import TTSEngine

    audition = HERE / "audition"
    raw_dir = HERE / "raw_outputs"
    metrics_dir = HERE / "metrics"
    for directory in (audition, raw_dir, metrics_dir, HERE / "source_profiles"):
        directory.mkdir(parents=True, exist_ok=True)
    shutil.copy2(HERE / "LISTEN_FIRST.md", audition / "LISTEN_FIRST.md")

    profiles = {f"Speaker {i + 1}": copy_profile(keeper, f"Speaker_{i + 1}") for i, keeper in enumerate(CANDIDATES)}
    jobs = [(speaker, p_index, kind, text) for speaker in profiles for p_index, (kind, text) in enumerate(PASSAGES)]
    rng = random.Random(SEED)
    rng.shuffle(jobs)
    mapping = {}
    engine = TTSEngine(backend="onnx")
    rows = []

    for clip_index, (speaker, passage_index, kind, text) in enumerate(jobs, start=1):
        if args.rescue_clip is not None and clip_index != args.rescue_clip:
            continue
        if clip_index < args.from_clip:
            continue
        label = f"Clip {clip_index:02d}"
        raw_path = raw_dir / f"{label}.wav"
        audition_path = audition / f"{label}.wav"
        started = time.perf_counter()
        diagnostics = None
        if args.rescue_clip == clip_index:
            # Same engine, sampling and insertion-only joins; splitting the stalled
            # paragraph into its already-normalized sentence units keeps each CPU
            # call bounded. This is a retry of this one technical failure only.
            from backend.app.tts.audio import edge_silence_samples, join_audios, save_wav
            from backend.app.tts.text import chunk_sentences, split_into_sentences, preprocess_text
            chunks = split_into_sentences(preprocess_text(text))
            parts = []
            for unit_index, chunk in enumerate(chunks):
                np.random.seed(9100 + passage_index * 10 + unit_index)
                generated = engine._model.infer(chunk, voice=profiles[speaker], denoise=False, use_ref_codes=True, **SAMPLING)
                arr = np.asarray(generated, dtype=np.float32)
                parts.append(arr.astype(np.float32) / np.iinfo(arr.dtype).max if np.issubdtype(arr.dtype, np.integer) else arr)
            sr_fixed = int(engine._model.sample_rate)
            gaps = []
            for unit_index, chunk in enumerate(chunks[:-1]):
                _lead, trail = edge_silence_samples(parts[unit_index])
                lead, _trail = edge_silence_samples(parts[unit_index + 1])
                target = 130 if chunk.rstrip()[-1:] in ".!?…" else 75 if chunk.rstrip()[-1:] in ",;:" else 45
                gaps.append(max(0, int((target - (trail + lead) * 1000 / sr_fixed) * sr_fixed / 1000)))
            save_wav(str(raw_path), join_audios(parts, sr_fixed, gap_samples=gaps), sr_fixed)
            diagnostics = {"outer_chunk_count": len(chunks), "inserted_gap_ms": [round(g * 1000 / sr_fixed, 2) for g in gaps]}
        elif not raw_path.exists():
            # Same draw seed for the same passage across all speakers; only conditioning varies.
            # A bounded retry seed is used only for Clip 09, whose original draw
            # repeatedly missed EOS on CPU; sampling parameters remain identical.
            np.random.seed({9: 9912, 10: 10117}.get(clip_index, 9100 + passage_index))
            engine.generate(
                text, voice=profiles[speaker], speed=1.0, out_path=str(raw_path),
                max_chunk_chars=240, denoise=False, use_ref_codes=True,
                quality_diagnostics=True, **SAMPLING,
            )
            diagnostics = engine.last_generation_diagnostics
        raw, sr = sf.read(raw_path, dtype="float32", always_2d=False)
        presented, gain = normalize_for_audition(raw)
        sf.write(audition_path, presented, int(sr), subtype="PCM_16")
        raw_m, presentation_m = metrics(raw, int(sr)), metrics(presented, int(sr))
        if raw_m["channels"] != 1 or raw_m["sample_rate"] != 48000:
            raise RuntimeError(f"{label}: unsupported generated format {raw_m}")
        if raw_m["clipped_samples"] or presentation_m["clipped_samples"]:
            raise RuntimeError(f"{label}: clipping detected")
        rows.append({
            "clip": label, "raw": raw_m, "audition": presentation_m,
            "gain": round(gain, 6), "generation_seconds": round(time.perf_counter() - started, 3),
            "chunk_count": diagnostics["outer_chunk_count"] if diagnostics else None,
            "inserted_gap_ms": diagnostics["inserted_gap_ms"] if diagnostics else None,
        })
        mapping[label] = {"speaker": speaker, "passage_index": passage_index + 1, "passage_kind": kind}
        print(f"READY {label}", flush=True)

    if args.from_clip > 1 or args.rescue_clip is not None:
        print("PHASE33A_PARTIAL_READY", flush=True)
        return 0
    if len(mapping) != 12 or any(sorted(v["speaker"] for v in mapping.values()).count(speaker) != 3 for speaker in profiles):
        raise RuntimeError("blind assignment invariant failed")
    (HERE / "private_mapping.json").write_text(json.dumps({"seed": SEED, "mapping": mapping}, indent=2) + "\n", encoding="utf-8")
    (metrics_dir / "metrics.json").write_text(json.dumps({"normalization": {"target_rms": TARGET_RMS, "peak_ceiling": PEAK_CEILING}, "clips": rows}, indent=2) + "\n", encoding="utf-8")
    print("PHASE33A_AUDITION_READY", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
