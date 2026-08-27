#!/usr/bin/env python3
"""Run a battery of TTS tests using the local TTSEngine and write outputs to output/tests

This script demonstrates usage of the backend TTSEngine defined in
`backend/app/tts/engine.py` and produces several WAV files for quick verification.
"""
import sys
import time
import os
from pathlib import Path

# ensure repository root is on sys.path so `backend` package is importable
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from backend.app.tts import TTSEngine


TESTS = [
    ("short", "Xin chào!"),
    ("vietnamese_marks", "Tiếng Việt có dấu: tiếng, Việt, thử nghiệm: ô, ê, ă, ầ, ế."),
    ("multi_sentence", "Hôm nay trời đẹp. Chúng ta đi dạo nhé? Tôi rất vui!"),
    ("long_paragraph", (
        "Một đoạn văn dài để thử khả năng chia câu và ghép audio. "
        "Nội dung này gồm nhiều câu, một số câu dài hơn để kiểm tra tính năng chunking. "
        "Hệ thống sẽ chia văn bản thành các phần nhỏ hơn, xử lý từng phần và ghép lại.")),
]


def run_tests(device: str = None):
    out_dir = Path("output/tests")
    out_dir.mkdir(parents=True, exist_ok=True)

    print("Initializing engine...")
    engine = TTSEngine(device=device)

    voices = engine.get_voices()
    print("Available voices:", voices)

    created = []

    # basic tests (speed 1.0)
    for name, text in TESTS:
        print(f"Generating test '{name}' (speed=1.0)")
        path = engine.generate(text, voice=(voices[0] if voices else "default"), speed=1.0, out_path=out_dir / f"{name}_1.0.wav")
        created.append(path)
        print(" ->", path)

    # speed variations on a representative sentence
    rep_text = "Xin chào, đây là bài kiểm tra tốc độ phát âm."
    for sp in (0.5, 1.0, 1.5):
        name = f"speed_{sp}"
        print(f"Generating '{name}'")
        path = engine.generate(rep_text, voice=(voices[0] if voices else "default"), speed=sp, out_path=out_dir / f"{name}.wav")
        created.append(path)

    print("\nCreated files:")
    for p in created:
        print(" -", p)

    print("\nUsage: play the WAV files in `output/tests/` with your preferred player.")


if __name__ == "__main__":
    dev = None
    if len(sys.argv) >= 2:
        dev = sys.argv[1]
    run_tests(device=dev)
