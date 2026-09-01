#!/usr/bin/env python3
"""One-time local provisioning for the validated Review Film native profile."""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from backend.app.tts.engine import TTSEngine
from backend.app.tts.special_voices import SPECIAL_VOICES


def main() -> int:
    definition = SPECIAL_VOICES["review_film"]
    reference = ROOT / definition["reference_path"]
    if not reference.is_file():
        raise SystemExit(f"Validated Review Film reference missing: {reference}")
    engine = TTSEngine(backend="onnx")
    engine.install_special_voice("review_film", str(reference), definition)
    print("Review Film special voice profile is installed locally.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
