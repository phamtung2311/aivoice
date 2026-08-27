"""Phase 22.3 — REAL-INFERENCE pronunciation diagnostic (preset vs saved vs temp).

Invokes the ALREADY-RUNNING production backend at 127.0.0.1:8000 (/api/tts),
reusing its loaded singleton model. Bypasses the browser so selector/localStorage
cannot contaminate the test. This is the actual production request path — no TTS
logic is duplicated and no second model process is started.

Total automatic inference budget: 8 very short samples, one request at a time.

Manifest + WAVs only. NEVER prints or stores embeddings/codes.
"""

import io
import json
import pathlib
import sys
import urllib.request
import wave

import numpy as np

API = "http://127.0.0.1:8000"
FIXED_TEXT = "Mọi người đang ở đây."
OUT_DIR = pathlib.Path("diagnostics") / "audio" / "phase22_3"
SAMPLING = {"speed": 1.0, "top_k": 25, "top_p": 0.95, "repetition_penalty": 1.2}
DEFAULT_PRESET = "Trúc Ly"
DEFAULT_SAVED = "tùng"


def read_audio_metrics(wav_bytes):
    """(sample_rate, duration_s, peak, rms) via minimal WAV parse; no values logged."""
    try:
        with wave.open(io.BytesIO(wav_bytes), "rb") as wf:
            sr = wf.getframerate()
            n = wf.getnframes()
            ch = wf.getnchannels()
            sampw = wf.getsampwidth()
            raw = wf.readframes(n)
        if sampw == 2:
            audio = np.frombuffer(raw, dtype=np.int16).astype(np.float32) / 32768.0
        elif sampw == 4:
            audio = np.frombuffer(raw, dtype=np.int32).astype(np.float32) / 2147483648.0
        else:
            audio = np.frombuffer(raw, dtype=np.uint8).astype(np.float32)
            audio = (audio - 128.0) / 128.0
        if ch > 1:
            audio = audio.reshape(ch, -1).mean(axis=0)
        peak = float(np.max(np.abs(audio))) if audio.size else 0.0
        rms = float(np.sqrt(np.mean(np.square(audio)))) if audio.size else 0.0
        return sr, round(float(n) / sr, 3), round(peak, 4), round(rms, 4)
    except Exception as exc:
        return None, None, None, repr(exc)


def post_api(payload, timeout=180):
    req = urllib.request.Request(
        API + "/api/tts",
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        if resp.status != 200:
            raise RuntimeError(f"HTTP {resp.status}")
        return resp.read()


def generate(filename, voice, voice_type, temperature, conditioning=None):
    payload = {"text": FIXED_TEXT, "voice": voice, "temperature": temperature, **SAMPLING}
    if conditioning:
        payload["conditioning_mode"] = conditioning
    entry = {
        "filename": filename,
        "voice_id": voice,
        "voice_type": voice_type,
        "conditioning_mode": conditioning or "full",
        "temperature": temperature,
        "top_k": SAMPLING["top_k"],
        "top_p": SAMPLING["top_p"],
        "repetition_penalty": SAMPLING["repetition_penalty"],
        "speed": SAMPLING["speed"],
        "duration": None,
        "sample_rate": None,
        "peak": None,
        "rms": None,
        "error": None,
    }
    try:
        wav = post_api(payload)
        out_path = OUT_DIR / filename
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_bytes(wav)
        sr, duration, peak, rms = read_audio_metrics(wav)
        entry["sample_rate"] = sr
        entry["duration"] = duration
        entry["peak"] = peak
        entry["rms"] = rms
        print(f"OK   {filename}  sr={sr} dur={duration}s peak={peak} rms={rms}")
    except Exception as exc:
        entry["error"] = repr(exc)
        print(f"FAIL {filename}  {exc}")
    return entry


def main(argv):
    preset = argv[1] if len(argv) > 1 else DEFAULT_PRESET
    saved = argv[2] if len(argv) > 2 else DEFAULT_SAVED

    plan = [
        ("preset_t08_r1.wav", preset, "preset", 0.8, None),
        ("preset_t08_r2.wav", preset, "preset", 0.8, None),
        ("preset_t08_r3.wav", preset, "preset", 0.8, None),
        ("preset_t07_r1.wav", preset, "preset", 0.7, None),
        ("saved_full_t08_r1.wav", saved, "saved", 0.8, None),
        ("saved_full_t08_r2.wav", saved, "saved", 0.8, None),
        ("saved_full_t07_r1.wav", saved, "saved", 0.7, None),
        ("saved_identity_t08_r1.wav", saved, "saved", 0.8, "identity_only"),
    ]

    manifest = [generate(*item) for item in plan]
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    manifest_path = OUT_DIR / "manifest.json"
    manifest_path.write_text(
        json.dumps(
            {"text": FIXED_TEXT, "preset": preset, "saved": saved, "samples": manifest},
            ensure_ascii=False,
            indent=1,
        ),
        encoding="utf-8",
    )
    ok = sum(1 for m in manifest if not m["error"])
    print("Manifest:", manifest_path)
    print(f"Generated OK: {ok} / {len(manifest)}; Failed: {len(manifest) - ok}")


if __name__ == "__main__":
    main(sys.argv)