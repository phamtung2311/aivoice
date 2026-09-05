#!/usr/bin/env python3
"""External-only Phase 42D smoke render; Codex must not execute this file."""
from __future__ import annotations

import json
from pathlib import Path
import time
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / "experiments/brand_voice_phase41g/podcast_text.txt"
OUTPUT = Path(__file__).with_name("phase42d_smoke.wav")
API = "http://127.0.0.1:8000"


def request_json(url: str, *, payload: dict | None = None) -> dict:
    body = json.dumps(payload, ensure_ascii=False).encode("utf-8") if payload else None
    request = Request(url, data=body, headers={"Content-Type": "application/json"})
    with urlopen(request, timeout=30) as response:
        return json.loads(response.read())


def main() -> None:
    # The first frozen paragraph corresponds to validated chunks 0–3 and about
    # 30 seconds of generated narration before the final 0.98 tempo adjustment.
    excerpt = SOURCE.read_text(encoding="utf-8").strip().split("\n\n", 1)[0]
    job = request_json(f"{API}/api/long-audio/jobs", payload={
        "text": excerpt,
        "voice": "podcast_brand_voice_v1",
        # Deliberately non-profile values: the brand route must ignore them.
        "speed": 1.7,
        "temperature": 0.2,
        "top_k": 5,
        "top_p": 0.6,
        "repetition_penalty": 1.8,
        "smart_text_processing": True,
        "tts_script": "NỘI DUNG NÀY KHÔNG ĐƯỢC DÙNG |||",
        "prosody_markup": True,
        "idempotency_key": f"phase42d-smoke-{time.time_ns()}",
    })
    job_id = job["job_id"]
    while True:
        state = request_json(f"{API}/api/long-audio/jobs/{job_id}")
        print(f"{state['state']}: {state.get('completed_chunks', 0)}/{state.get('total_chunks', '?')}")
        if state["state"] == "COMPLETED":
            break
        if state["state"] in {"FAILED", "CANCELLED"}:
            raise RuntimeError(state.get("error") or state["state"])
        time.sleep(1)
    with urlopen(f"{API}/api/long-audio/jobs/{job_id}/audio", timeout=30) as response:
        OUTPUT.write_bytes(response.read())
    print(f"WAV: {OUTPUT}")
    print(f"Manifest: {ROOT / 'data/jobs' / job_id / 'podcast_pipeline_manifest.json'}")


if __name__ == "__main__":
    main()
