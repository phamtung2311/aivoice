#!/usr/bin/env python3
"""Phase 31 controlled Podcast Voice audition runner.

This is R&D only. It never mutates the provisioned ``podcast_brand_beta``
profile or production defaults. Candidate labels are blind; the configuration
mapping is written separately to ``private_mapping.json``.
"""
from __future__ import annotations

import argparse
import json
import random
import sys
import time
from pathlib import Path

import numpy as np
import soundfile as sf

ROOT = Path(__file__).resolve().parents[3]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from backend.app.tts.audio import edge_silence_samples, join_audios, save_wav
from backend.app.tts.engine import TTSEngine
from backend.app.tts.nlp import normalize_text
from backend.app.tts.text import chunk_sentences, split_into_sentences

VOICE = "podcast_brand_beta"
BASELINE = {"temperature": 0.8, "top_k": 25, "top_p": 0.95, "repetition_penalty": 1.2}

TESTS = {
    "conversation": """Có những buổi tối, tôi không cần một câu trả lời thật lớn. Chỉ cần ngồi yên vài phút, pha một ly trà, rồi nghe thành phố chậm lại sau khung cửa sổ. Có thể hôm nay chưa phải là một ngày hoàn hảo, nhưng chúng ta vẫn có thể chọn nói với mình nhẹ nhàng hơn một chút. Và đôi khi, chính khoảng lặng nhỏ ấy lại giúp mọi thứ trở về đúng nhịp của nó.""",
    "story": """Chiều hôm đó, mưa đến sớm hơn thường lệ. Con hẻm nhỏ trước nhà loang ánh đèn, còn chiếc xe đạp cũ vẫn tựa bên hiên như chờ một người chưa về.

Tôi nhớ đã đứng rất lâu dưới mái che, nghe tiếng mưa rơi lên mái tôn, rồi bỗng nhận ra mình không còn vội nữa. Có những điều chỉ khi ta chậm lại mới nhìn thấy: một lời hứa cũ, một khuôn mặt thân quen, hay cảm giác bình yên đã bị bỏ quên giữa những ngày quá nhiều việc.

Đến khi mưa ngớt, con hẻm vẫn vậy. Nhưng tôi biết, có điều gì đó trong mình đã dịu đi.""",
    "long": """Chúng ta thường nghĩ một thay đổi lớn phải bắt đầu bằng một quyết định thật dứt khoát. Nhưng phần lớn những lần trưởng thành trong đời lại đến từ những điều rất nhỏ: một buổi sáng thức dậy sớm hơn, một cuộc gọi ta không trì hoãn, hay một lần bình tĩnh nói ra điều mình thực sự cần.

Tôi từng có một giai đoạn luôn muốn mọi thứ phải rõ ràng ngay lập tức. Công việc phải có kết quả, kế hoạch phải đúng, những người bên cạnh phải hiểu mình mà không cần giải thích. Càng mong như vậy, tôi càng thấy mệt. Bởi cuộc sống hiếm khi đi theo một đường thẳng. Nó giống một cuộc trò chuyện dài hơn, có lúc im lặng, có lúc lúng túng, và cũng có những đoạn ta cần nghe kỹ mới hiểu được ý nghĩa.

Rồi một ngày, tôi bắt đầu tập thay đổi một thói quen rất nhỏ. Mỗi khi cảm thấy vội, tôi dừng lại vài giây trước khi trả lời. Không phải để né tránh, mà để cho cảm xúc có thời gian lắng xuống. Sau khoảng nghỉ đó, câu nói thường khác đi. Nhẹ hơn, rõ hơn, và ít làm tổn thương người đối diện hơn.

Điều thú vị là, sự bình tĩnh không khiến chúng ta chậm chạp. Nó giúp ta biết điều gì đáng làm trước, điều gì có thể chờ, và điều gì không cần mang theo quá lâu. Khi có thêm khoảng trống trong đầu, ta nghe được nhiều hơn: tiếng nói của người khác, những tín hiệu nhỏ của cơ thể, và cả mong muốn thật của mình.

Có thể hôm nay bạn chưa cần thay đổi cả cuộc đời. Chỉ cần thử để lại một khoảng nghỉ giữa hai suy nghĩ. Uống một ngụm nước. Đi chậm hơn một đoạn đường. Hoặc gọi cho một người mà bạn vẫn muốn hỏi thăm. Những việc nhỏ ấy không giải quyết mọi thứ ngay lập tức, nhưng chúng nhắc ta rằng mình vẫn đang có mặt trong chính cuộc sống của mình.

Và nếu ngày mai lại trở nên bận rộn, cũng không sao. Ta có thể bắt đầu lại từ một khoảng lặng khác.""",
}

# Each candidate alters exactly one factor from the production baseline.
CANDIDATES = {
    "A": {**BASELINE, "chunk_chars": 240, "sentence_gap_ms": 130},
    "B": {**BASELINE, "temperature": 0.72, "chunk_chars": 240, "sentence_gap_ms": 130},
    "C": {**BASELINE, "top_p": 0.90, "chunk_chars": 240, "sentence_gap_ms": 130},
    "D": {**BASELINE, "repetition_penalty": 1.10, "chunk_chars": 240, "sentence_gap_ms": 130},
    "E": {**BASELINE, "chunk_chars": 180, "sentence_gap_ms": 130},
    "F": {**BASELINE, "chunk_chars": 240, "sentence_gap_ms": 175},
}


def audio_metrics(path: Path, started: float, chunks: list[str]) -> dict:
    audio, sample_rate = sf.read(path, dtype="float32", always_2d=False)
    mono = np.asarray(audio, dtype=np.float32)
    if mono.ndim == 2:
        mono = mono.mean(axis=1)
    duration = len(mono) / sample_rate
    return {
        "duration_seconds": round(duration, 3),
        "generation_seconds": round(time.monotonic() - started, 3),
        "rtf": round((time.monotonic() - started) / duration, 3) if duration else None,
        "sample_rate": int(sample_rate),
        "channels": 1 if audio.ndim == 1 else int(audio.shape[1]),
        "peak": round(float(np.max(np.abs(mono))), 6),
        "rms": round(float(np.sqrt(np.mean(np.square(mono)))), 6),
        "clipped_samples": int(np.count_nonzero(np.abs(mono) >= 0.999)),
        "silence_ratio": round(float(np.mean(np.abs(mono) < 0.003)), 4),
        "chunk_count": len(chunks),
        "average_chunk_chars": round(sum(map(len, chunks)) / len(chunks), 1),
    }


def render(engine: TTSEngine, text: str, config: dict, output: Path) -> tuple[dict, list[str]]:
    clean = normalize_text(text)
    chunks = chunk_sentences(split_into_sentences(clean), max_chars=config["chunk_chars"])
    if not chunks:
        raise ValueError("No speakable chunks")
    generated = []
    started = time.monotonic()
    # Fixed seed makes differences attributable to the candidate setting rather
    # than a fresh random sampling path.
    np.random.seed(31001)
    for chunk in chunks:
        path = output.parent / f".{output.stem}_{len(generated):02d}.wav"
        engine.generate(chunk, voice=VOICE, speed=1.0, out_path=str(path),
                        temperature=config["temperature"], top_k=config["top_k"],
                        top_p=config["top_p"], repetition_penalty=config["repetition_penalty"])
        generated.append(path)
    audios, sample_rate = [], None
    for path in generated:
        audio, current_rate = sf.read(path, dtype="float32", always_2d=False)
        audios.append(np.asarray(audio, dtype=np.float32))
        sample_rate = int(current_rate) if sample_rate is None else sample_rate
        if sample_rate != int(current_rate):
            raise ValueError("Incompatible generated sample rates")
        path.unlink(missing_ok=True)
    gaps = []
    for index, chunk in enumerate(chunks[:-1]):
        _leading, trailing = edge_silence_samples(audios[index])
        leading, _trailing = edge_silence_samples(audios[index + 1])
        target = config["sentence_gap_ms"] if chunk.rstrip().endswith((".", "!", "?", "…")) else 75
        existing = (leading + trailing) * 1000 / sample_rate
        gaps.append(max(0, round((target - existing) * sample_rate / 1000)))
    save_wav(str(output), join_audios(audios, sample_rate, gap_samples=gaps), sample_rate)
    return audio_metrics(output, started, chunks), chunks


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate blind Phase 31 Podcast candidates.")
    parser.add_argument("--test", choices=TESTS, default="conversation")
    parser.add_argument("--candidates", nargs="+", choices=CANDIDATES, default=list(CANDIDATES))
    args = parser.parse_args()
    phase = Path(__file__).resolve().parent
    output_dir = phase / "outputs" / args.test
    output_dir.mkdir(parents=True, exist_ok=True)
    blind_order = list(CANDIDATES)
    random.Random(31031).shuffle(blind_order)
    mapping = {f"Podcast_{chr(65 + blind_order.index(candidate))}": candidate for candidate in CANDIDATES}
    measurements = []
    engine = TTSEngine(backend="onnx")
    try:
        for candidate in args.candidates:
            label = next(name for name, mapped in mapping.items() if mapped == candidate)
            output = output_dir / f"{label}.wav"
            metrics, chunks = render(engine, TESTS[args.test], CANDIDATES[candidate], output)
            measurements.append({"label": label, "test": args.test, "metrics": metrics})
            print(f"READY {label}: {metrics['duration_seconds']}s, {metrics['chunk_count']} chunks", flush=True)
    finally:
        del engine
    (phase / "private_mapping.json").write_text(json.dumps({"candidates": CANDIDATES, "mapping": mapping}, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    (phase / "measurements.json").write_text(json.dumps(measurements, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print("PHASE31_AUDITION_READY", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
