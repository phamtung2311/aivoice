#!/usr/bin/env python3
"""Developer-only Phase 28A prosody experiment for the installed AIVoice engine.

This script deliberately calls ``TTSEngine`` directly: it does not start FastAPI,
write user history, alter a saved voice, or add a production control.  Generated
WAVs belong in ``experiments/emotion/output`` and are ignored by Git.
"""
from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import numpy as np
import soundfile as sf

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from backend.app.tts.engine import TTSEngine
from backend.app.tts.nlp import normalize_text
from backend.app.tts.text import chunk_sentences, preprocess_text, split_into_sentences

BASELINE = {"speed": 1.0, "temperature": 0.8, "top_k": 25, "top_p": 0.95, "repetition_penalty": 1.2}

# Each variation is intentionally small.  Bracketed cues are limited to the three
# cues documented by the *installed* VieNeu v3 Turbo phonemizer; these are not
# arbitrary emotion labels such as [happy] or [warm].
SCENARIOS: list[dict[str, Any]] = [
    {"id": "informational_neutral", "category": "neutral", "base": "Hôm nay chúng ta sẽ bắt đầu một thử nghiệm mới.", "text": "Hôm nay chúng ta sẽ bắt đầu một thử nghiệm mới.", "strategy": "neutral"},
    {"id": "thoughtful_neutral", "category": "thoughtful", "base": "Đó thực sự là một bài toán khó, nhưng nếu giải quyết được, mọi thứ có thể thay đổi.", "text": "Đó thực sự là một bài toán khó, nhưng nếu giải quyết được, mọi thứ có thể thay đổi.", "strategy": "neutral"},
    {"id": "thoughtful_ellipsis", "category": "thoughtful", "base": "Đó thực sự là một bài toán khó, nhưng nếu giải quyết được, mọi thứ có thể thay đổi.", "text": "Đó thực sự là một bài toán khó... Nhưng nếu giải quyết được, mọi thứ có thể thay đổi.", "strategy": "punctuation_ellipsis"},
    {"id": "thoughtful_split", "category": "thoughtful", "base": "Đó thực sự là một bài toán khó, nhưng nếu giải quyết được, mọi thứ có thể thay đổi.", "text": "Đó thực sự là một bài toán khó. Nếu giải quyết được, mọi thứ có thể thay đổi.", "strategy": "sentence_segmentation"},
    {"id": "happy_period", "category": "happy", "base": "Cuối cùng chúng ta cũng làm được rồi!", "text": "Cuối cùng chúng ta cũng làm được rồi.", "strategy": "punctuation_period"},
    {"id": "happy_exclamation", "category": "happy", "base": "Cuối cùng chúng ta cũng làm được rồi!", "text": "Cuối cùng chúng ta cũng làm được rồi!", "strategy": "punctuation_exclamation"},
    {"id": "sad_neutral", "category": "sad", "base": "Tôi không nghĩ mọi chuyện lại kết thúc như thế này.", "text": "Tôi không nghĩ mọi chuyện lại kết thúc như thế này.", "strategy": "neutral"},
    {"id": "sad_sigh", "category": "sad", "base": "Tôi không nghĩ mọi chuyện lại kết thúc như thế này.", "text": "[thở dài] Tôi không nghĩ mọi chuyện lại kết thúc như thế này.", "strategy": "native_inline_cue_sigh"},
    {"id": "surprise_period", "category": "surprise", "base": "Khoan đã, chuyện này thật sự xảy ra sao?", "text": "Khoan đã, chuyện này thật sự xảy ra sao.", "strategy": "punctuation_period"},
    {"id": "surprise_question", "category": "surprise", "base": "Khoan đã, chuyện này thật sự xảy ra sao?", "text": "Khoan đã, chuyện này thật sự xảy ra sao?", "strategy": "punctuation_question"},
    {"id": "gentle_neutral", "category": "gentle", "base": "Không sao đâu, cứ từ từ rồi mọi chuyện sẽ ổn.", "text": "Không sao đâu, cứ từ từ rồi mọi chuyện sẽ ổn.", "strategy": "neutral"},
    {"id": "gentle_pause", "category": "gentle", "base": "Không sao đâu, cứ từ từ rồi mọi chuyện sẽ ổn.", "text": "Không sao đâu... Cứ từ từ, rồi mọi chuyện sẽ ổn.", "strategy": "pause_rhythm"},
    {"id": "context_serious", "category": "context", "base": "Tôi không nghĩ mọi chuyện lại kết thúc như thế này.", "text": "Chúng ta cần nói chuyện nghiêm túc. Tôi không nghĩ mọi chuyện lại kết thúc như thế này.", "strategy": "semantic_context"},
    {"id": "happy_temperature_09", "category": "sampling", "base": "Cuối cùng chúng ta cũng làm được rồi!", "text": "Cuối cùng chúng ta cũng làm được rồi!", "strategy": "sampling_temperature", "parameters": {"temperature": 0.9}},
]


def audio_metrics(path: Path) -> dict[str, float | int]:
    audio, sample_rate = sf.read(path, dtype="float32", always_2d=False)
    samples = np.asarray(audio, dtype=np.float32)
    amplitude = np.max(np.abs(samples), axis=1) if samples.ndim == 2 else np.abs(samples)
    audible = np.flatnonzero(amplitude > 0.003)
    leading = int(audible[0]) if audible.size else len(amplitude)
    trailing = int(len(amplitude) - audible[-1] - 1) if audible.size else len(amplitude)
    return {
        "sample_rate": int(sample_rate),
        "channels": int(samples.shape[1]) if samples.ndim == 2 else 1,
        "duration_seconds": round(float(samples.shape[0]) / sample_rate, 3),
        "peak": round(float(np.max(amplitude)) if amplitude.size else 0.0, 6),
        "rms": round(float(np.sqrt(np.mean(np.square(samples)))) if samples.size else 0.0, 6),
        "leading_silence_ms": round(leading * 1000 / sample_rate, 2),
        "trailing_silence_ms": round(trailing * 1000 / sample_rate, 2),
    }


def final_engine_input(text: str, smart_text: bool) -> tuple[str, str, list[str]]:
    """Return API-equivalent pre-engine text and exact outer chunks passed to infer."""
    api_text = normalize_text(text) if smart_text else text
    preprocessed = preprocess_text(api_text)
    chunks = chunk_sentences(split_into_sentences(preprocessed), max_chars=240)
    return api_text, preprocessed, chunks


def write_index(records: list[dict[str, Any]], path: Path) -> None:
    lines = ["# Phase 28A listening index", "", "Listen in each pair/group in the listed order. Metrics are supporting evidence only; rate audible expression manually.", ""]
    for record in records:
        lines.extend([
            f"## {record['id']}", "",
            f"- Strategy: `{record['strategy']}`",
            f"- Base: {record['base_text']}",
            f"- Exact input sent to the engine wrapper: {record['engine_input']}",
            f"- WAV: [{record['output_filename']}]({record['output_filename']})",
            f"- Duration / RMS: {record['metrics']['duration_seconds']} s / {record['metrics']['rms']}", "",
        ])
    path.write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate controlled local Phase 28A expression comparisons.")
    parser.add_argument("--voice", default=None, help="Existing preset or saved voice name. Defaults to the engine default voice.")
    parser.add_argument("--only", action="append", default=[], help="Scenario id to generate; repeat to select multiple.")
    parser.add_argument("--no-smart-text", action="store_true", help="Match /api/tts with Smart Text Processing disabled.")
    args = parser.parse_args()

    selected = [item for item in SCENARIOS if not args.only or item["id"] in set(args.only)]
    unknown = set(args.only) - {item["id"] for item in SCENARIOS}
    if unknown:
        parser.error(f"Unknown scenario id(s): {', '.join(sorted(unknown))}")
    if not selected:
        parser.error("No scenarios selected")

    output_dir = ROOT / "experiments" / "emotion" / "output"
    output_dir.mkdir(parents=True, exist_ok=True)
    engine = TTSEngine(cache_model=True)
    voice = args.voice
    records: list[dict[str, Any]] = []
    for scenario in selected:
        parameters = {**BASELINE, **scenario.get("parameters", {})}
        api_text, preprocessed, chunks = final_engine_input(scenario["text"], not args.no_smart_text)
        filename = f"{scenario['id']}.wav"
        out_path = output_dir / filename
        print(f"Generating {scenario['id']} → {out_path}")
        engine.generate(api_text, voice=voice, out_path=str(out_path), quality_diagnostics=True, **parameters)
        records.append({
            "id": scenario["id"], "category": scenario["category"], "strategy": scenario["strategy"],
            "base_text": scenario["base"], "source_text": scenario["text"], "smart_text_processing": not args.no_smart_text,
            "api_processed_text": api_text, "engine_input": preprocessed, "engine_outer_chunks": chunks,
            "parameters": parameters, "voice": voice, "generated_at": datetime.now(timezone.utc).isoformat(),
            "output_filename": filename, "metrics": audio_metrics(out_path),
            "engine_diagnostics": engine.last_generation_diagnostics,
        })
    manifest = {"phase": "28A", "engine": "AIVoice TTSEngine (installed VieNeu)", "records": records}
    (output_dir / "manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    write_index(records, output_dir / "LISTENING_INDEX.md")
    print(f"Wrote {len(records)} sample(s), manifest.json, and LISTENING_INDEX.md in {output_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
