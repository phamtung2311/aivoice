# Phase 46 — Safe project housekeeping

Status: **COMPLETE — SAFE EXPLORER/DOCUMENTATION CLEANUP**

Production runtime, frozen voice assets, requirements, backups, Phase 45 record, tests, model assets, source code, reports, audio, and user data were protected. The worktree was already dirty, so historical experiments were not moved or deleted. `docs/PROJECT_HOUSEKEEPING_AUDIT.md` records the inventory and rationale.

VS Code Explorer now hides historical experiment families and regenerable caches through `.vscode/settings.json`; this is display-only and reversible. README and experiment index now identify AIVoice Podcast Voice Set v1 and its stable IDs. Regenerable `__pycache__`, `.pyc`, and `.pytest_cache` entries were removed. No model cache, backup, production artifact, WAV, embedding, reference-code file, configuration, or source file was removed.

Verification: `scripts/verify_production_voice_bundle.py` passed; frontend Audio Studio JavaScript syntax and `git diff --check` passed. The sandbox blocked a final localhost API smoke, but the running backend had previously exposed all three production IDs.
