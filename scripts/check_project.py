"""Fast, dependency-light checks for a portfolio reviewer or CI job."""

from __future__ import annotations

import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def fail(message: str) -> None:
    print(f"FAIL  {message}")
    raise SystemExit(1)


def main() -> None:
    required = (
        "backend/main.py",
        "frontend/index.html",
        "frontend/audio-studio.html",
        "data/nlp/custom_dictionary.json",
        "requirements.txt",
    )
    missing = [path for path in required if not (ROOT / path).is_file()]
    if missing:
        fail("missing required files: " + ", ".join(missing))

    dictionary_path = ROOT / "data/nlp/custom_dictionary.json"
    try:
        dictionary = json.loads(dictionary_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        fail(f"invalid pronunciation dictionary: {exc}")
    if not isinstance(dictionary, dict):
        fail("pronunciation dictionary must contain a JSON object")

    sys.path.insert(0, str(ROOT))
    try:
        from backend.main import APP_VERSION, app
    except Exception as exc:  # pragma: no cover - diagnostic entry point
        fail(f"backend import failed: {exc}")

    paths = {route.path for route in app.routes}
    expected_paths = {"/api/health", "/api/voices", "/api/tts", "/api/long-audio/jobs"}
    absent = sorted(expected_paths - paths)
    if absent:
        fail("missing public API routes: " + ", ".join(absent))

    print(f"PASS  AIVoice {APP_VERSION} imports successfully")
    print(f"PASS  {len(paths)} API routes registered")
    print(f"PASS  pronunciation dictionary loaded ({len(dictionary)} entries)")
    print("PASS  required frontend and runtime files are present")


if __name__ == "__main__":
    main()
