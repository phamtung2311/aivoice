#!/usr/bin/env python3
"""Create the small handoff ZIP without models or private reference audio."""
from __future__ import annotations

import zipfile
from pathlib import Path

from common import LOG_PATH, MANIFEST_PATH, OUTPUTS, ROOT, environment_text


def main() -> int:
    environment = ROOT / "environment.txt"
    environment.write_text(environment_text(), encoding="utf-8")
    package = ROOT / "aivoice_phase28_poc.zip"
    allowed = [MANIFEST_PATH, environment, LOG_PATH, ROOT / "evaluation_template.md"]
    allowed.extend(sorted(path for path in OUTPUTS.rglob("*") if path.is_file()))
    missing = [path for path in (MANIFEST_PATH, ROOT / "evaluation_template.md") if not path.is_file()]
    if missing:
        print("PACKAGE: FAIL — missing " + ", ".join(str(path.name) for path in missing))
        return 1
    with zipfile.ZipFile(package, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for path in allowed:
            if path.is_file():
                archive.write(path, path.relative_to(ROOT))
    print(f"PACKAGE: PASS — {package}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
