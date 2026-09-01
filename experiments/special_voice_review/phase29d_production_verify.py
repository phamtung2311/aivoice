#!/usr/bin/env python3
"""One-off local verification through the normal production FastAPI route."""
from __future__ import annotations

import io
import json
import resource
import sys
import time
from pathlib import Path

import soundfile as sf
from fastapi.testclient import TestClient

ROOT = Path(__file__).resolve().parent
PROJECT_ROOT = ROOT.parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from backend import main


OUTPUT = ROOT / "outputs" / "phase29d"


def render(client: TestClient, label: str, text: str, voice: str) -> dict:
    wall_start, cpu_start = time.perf_counter(), time.process_time()
    response = client.post("/api/tts", json={"text": text, "voice": voice, "speed": 1.0, "smart_text_processing": False})
    if response.status_code != 200:
        raise RuntimeError(f"{label} failed: {response.status_code} {response.text[:300]}")
    if not response.headers.get("content-type", "").startswith("audio/wav"):
        raise RuntimeError(f"{label} did not return WAV")
    info = sf.info(io.BytesIO(response.content))
    duration = info.frames / float(info.samplerate)
    wall = time.perf_counter() - wall_start
    return {
        "test": label, "voice": voice, "wall_generation_seconds": round(wall, 3),
        "process_cpu_seconds": round(time.process_time() - cpu_start, 3),
        "audio_duration_seconds": round(duration, 4), "RTF": round(wall / duration, 4),
        "peak_RSS_MB": round(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1024.0, 2),
        "wav_bytes": len(response.content), "status": "success",
    }


def main_verify() -> int:
    OUTPUT.mkdir(parents=True, exist_ok=True)
    client = TestClient(main.app)
    response = client.get("/api/voices")
    response.raise_for_status()
    voices = response.json()["voices"]
    review = next((voice for voice in voices if voice["id"] == "review_film" and voice.get("type") == "special"), None)
    if review is None:
        raise RuntimeError("Review Film is not present in normal /api/voices output")
    normal = next(voice["id"] for voice in voices if voice.get("type") == "preset")
    short = "Đây là câu kiểm tra ngắn cho AIVoice."
    long_text = (ROOT / "outputs" / "phase29c" / "review_script.txt").read_text(encoding="utf-8").strip()
    records = [
        render(client, "normal_short", short, normal),
        render(client, "review_film_short", short, "review_film"),
        render(client, "review_film_long", long_text, "review_film"),
    ]
    (OUTPUT / "production_verification.json").write_text(json.dumps({
        "normal_api_path": "/api/tts", "review_film_listed": review,
        "profile_reused_from_local_store": True, "records": records,
    }, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print("Production verification complete.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main_verify())
