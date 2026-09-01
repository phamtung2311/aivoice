#!/usr/bin/env python3
"""Finite local blind validation for Phase 29C; no production integration."""
from __future__ import annotations

import csv
import json
import random
import resource
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parent
PROJECT_ROOT = ROOT.parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from backend.app.tts.audio import edge_silence_samples, join_audios, save_wav
from backend.app.tts.engine import TTSEngine
from backend.app.tts.text import chunk_sentences, preprocess_text, split_into_sentences


REFERENCE = ROOT / "reference_audio" / "review_film.wav"
OUTPUT = ROOT / "outputs" / "phase29c"
SCRIPT = """Ngay từ cảnh mở đầu, bộ phim đã gieo vào người xem một câu hỏi rất nhỏ: vì sao một người đàn ông lại trở về căn nhà cũ đúng vào đêm mất điện? Nhân vật chính không phải anh hùng đặc biệt, chỉ là một kiến trúc sư đang cố hoàn tất bản thiết kế dang dở của cha mình. Nhưng khi những bức tường trong ngôi nhà liên tục thay đổi vị trí, anh nhận ra mỗi căn phòng đều cất giữ một ký ức mà gia đình từng cố quên đi. Nhịp kể ban đầu chậm rãi, rồi siết lại khi chiếc radio cũ phát ra giọng nói của một người đã mất từ nhiều năm trước. Cú lật đáng giá nhất không nằm ở việc ai là hung thủ, mà ở chỗ nhân vật chính hiểu rằng mình đã vô tình góp phần khóa kín bí mật ấy. Đến đoạn cuối, cuộc chạy trốn qua hành lang tối không chỉ tạo cảm giác nghẹt thở mà còn buộc anh lựa chọn giữa sự an toàn và sự thật. Đây là bộ phim biết kiên nhẫn, để nỗi sợ lớn dần từ những chi tiết rất bình thường."""
CANDIDATES = {
    "baseline": {},
    "candidate_c": {"temperature": 0.78, "top_p": 0.94, "repetition_penalty": 1.28},
}


def rss_mb() -> float:
    return resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1024.0


def float_audio(audio: object) -> np.ndarray:
    data = np.asarray(audio)
    if np.issubdtype(data.dtype, np.integer):
        data = data.astype(np.float32) / np.iinfo(data.dtype).max
    else:
        data = data.astype(np.float32)
    if data.size == 0 or data.ndim not in (1, 2):
        raise RuntimeError("Model returned no valid waveform")
    return data


def render(engine: TTSEngine, reference_voice: dict, sampling: dict) -> tuple[np.ndarray, dict]:
    """Use the current engine's text and measured-gap behavior without re-encoding."""
    model, sr = engine._model, engine._model.sample_rate
    clean = preprocess_text(SCRIPT)
    chunks = chunk_sentences(split_into_sentences(clean), max_chars=240)
    if not chunks:
        raise RuntimeError("Review script has no speakable chunks")
    audio_parts, chunk_info = [], []
    for index, chunk in enumerate(chunks):
        audio = float_audio(model.infer(chunk, voice=reference_voice, denoise=True, use_ref_codes=True, **sampling))
        leading, trailing = edge_silence_samples(audio)
        chunk_info.append({
            "index": index, "chars": len(chunk), "text_boundary": chunk[-48:],
            "leading_silence_ms": round(leading * 1000 / sr, 2),
            "trailing_silence_ms": round(trailing * 1000 / sr, 2),
        })
        audio_parts.append(audio)
    gaps = []
    for index, chunk in enumerate(chunks[:-1]):
        end = chunk.rstrip()[-1:] if chunk.strip() else ""
        target_ms = 130 if end in ".!?…" else 75 if end in ",;:" else 45
        present_ms = chunk_info[index]["trailing_silence_ms"] + chunk_info[index + 1]["leading_silence_ms"]
        gaps.append(max(0, int((target_ms - present_ms) * sr / 1000)))
    return join_audios(audio_parts, sr, gap_samples=gaps), {
        "outer_chunk_count": len(chunks), "chunk_boundaries": chunk_info,
        "inserted_gaps_ms": [round(gap * 1000 / sr, 2) for gap in gaps],
        "v3turbo_internal_chunk_behavior": "Not exposed by the current public adapter.",
    }


def main() -> int:
    if not REFERENCE.is_file():
        raise SystemExit(f"Missing required reference: {REFERENCE}")
    if OUTPUT.exists() and any(OUTPUT.iterdir()):
        raise SystemExit(f"Refusing to overwrite existing Phase 29C artifacts: {OUTPUT}")
    OUTPUT.mkdir(parents=True)
    (OUTPUT / "review_script.txt").write_text(SCRIPT + "\n", encoding="utf-8")

    print("Loading existing local ONNX engine; no production state will be saved.", flush=True)
    engine = TTSEngine(backend="onnx")
    print("Encoding the Phase 29B reference once and reusing it for both samples.", flush=True)
    speaker_emb, codes = engine._model.encode_reference(str(REFERENCE), denoise=True, use_ref_codes=True)
    reference_voice = {"speaker_emb": speaker_emb, "codes": codes}
    order = list(CANDIDATES)
    random.Random(29030).shuffle(order)
    private_mapping, public_records = {}, []
    for number, candidate in enumerate(order, start=1):
        sample_id = f"long_sample_{number:02d}"
        np.random.seed(29030)  # same isolated RNG state: only sampling configuration differs.
        wall_start, cpu_start = time.perf_counter(), time.process_time()
        audio, diagnostics = render(engine, reference_voice, CANDIDATES[candidate])
        wall, cpu = time.perf_counter() - wall_start, time.process_time() - cpu_start
        output = OUTPUT / f"{sample_id}.wav"
        save_wav(str(output), audio, engine._model.sample_rate)
        duration = float(audio.shape[0]) / engine._model.sample_rate
        metric = {
            "sample_id": sample_id, "wall_generation_seconds": round(wall, 3),
            "process_cpu_seconds": round(cpu, 3), "audio_duration_seconds": round(duration, 4),
            "RTF": round(wall / duration, 4), "peak_RSS_MB": round(rss_mb(), 2),
            "chunk_count": diagnostics["outer_chunk_count"], "chunking": diagnostics,
            "timestamp": datetime.now(timezone.utc).isoformat(), "status": "success",
        }
        public_records.append(metric)
        private_mapping[sample_id] = {"candidate": candidate, "metrics": metric}
        print(f"DONE {sample_id}: {metric['wall_generation_seconds']}s; RTF={metric['RTF']}", flush=True)
    baseline, candidate_c = private_mapping[[k for k, v in private_mapping.items() if v['candidate'] == 'baseline'][0]], private_mapping[[k for k, v in private_mapping.items() if v['candidate'] == 'candidate_c'][0]]
    private_mapping["candidate_c_vs_baseline"] = {
        "RTF_delta": round(candidate_c["metrics"]["RTF"] - baseline["metrics"]["RTF"], 4),
        "peak_RSS_MB_delta": round(candidate_c["metrics"]["peak_RSS_MB"] - baseline["metrics"]["peak_RSS_MB"], 2),
    }
    (OUTPUT / "phase29c_mapping.json").write_text(json.dumps(private_mapping, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    (OUTPUT / "phase29c_metrics.json").write_text(json.dumps({
        "reference_encoding": {"encoded_once": True, "same_reference": True, "speaker_emb_shape": list(np.asarray(speaker_emb).shape), "codes_shape": list(np.asarray(codes).shape), "denoise": True, "use_ref_codes": True},
        "records": public_records,
    }, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    fields = ["sample_id", "review_suitability_1_5", "naturalness_1_5", "rhythm_1_5", "clarity_1_5", "voice_consistency_1_5", "robotic_rhythm_1_5", "long_form_stability_1_5", "preferred", "notes"]
    with (OUTPUT / "phase29c_listening.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows({"sample_id": r["sample_id"]} for r in public_records)
    (OUTPUT / "phase29c_listening.md").write_text(
        "# Phase 29C — Nghe mù long-form\\n\\n"
        "Nghe cả hai file hoàn chỉnh trước khi chọn. Không mở `phase29c_mapping.json` trước khi hoàn tất chấm điểm.\\n\\n"
        "1. Mẫu nào giống người thuyết minh Review Film hơn?\\n2. Mẫu nào tự nhiên hơn?\\n3. Mẫu nào có nhịp tốt hơn và ít máy móc hơn?\\n4. Mẫu nào chuyển câu tốt hơn?\\n5. Bạn sẽ chọn mẫu nào cho AIVoice Review Film?\\n\\n"
        "Điền kết quả vào `phase29c_listening.csv`; robotic rhythm: 1 = tự nhiên, 5 = rất máy móc.\\n",
        encoding="utf-8",
    )
    print("Generated two anonymized long-form files. Stop for human listening.", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
