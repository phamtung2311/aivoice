# Phase 46 — Safe project housekeeping

Status: **COMPLETE — SAFE EXPLORER/DOCUMENTATION CLEANUP**

## Scope and protection

Production runtime, frozen voice assets, requirements, backups, Phase 45 records, tests, model assets, source code, reports, audio, and user data were protected. The worktree was already substantially dirty, so Phase 46 did not move or delete historical experiment directories. `docs/PROJECT_HOUSEKEEPING_AUDIT.md` records the inventory and rationale.

## Changes made

- Added display-only VS Code exclusions in `.vscode/settings.json` for historical experiment families and regenerable caches. The production Phase 45 folder remains visible.
- Added a concise project map to `README.md` and a production/historical distinction to `experiments/README.md`.
- Removed only regenerable `__pycache__` directories, `*.pyc` files, and `.pytest_cache`.
- Created this report and `PHASE46_MOVE_MAP.md`.

No model cache, backup, production artifact, WAV, embedding, reference-code file, configuration, or source file was removed. No historical audio was deleted.

## Verification

- `PYTHONPATH=. .venv/bin/python scripts/verify_production_voice_bundle.py`: PASS before and after cleanup.
- Production backup SHA256: `31bd9644ba03830b7bf0f0dd786ea616adf25e7c3c754e41741d139988f89f22` (unchanged).
- `PYTHONPATH=. .venv/bin/python -m pytest -q tests/test_phase42_podcast_brand_voice.py`: PASS (15 passed).
- `node --check frontend/audio-studio.js`: PASS.
- `git diff --check`: PASS.

## Web regression

`GET /api/voices` was checked read-only against the running backend and returned all three frozen production IDs: `podcast_deep_warm`, `podcast_warm_storyteller`, and `podcast_soft_baritone`. No backend source or voice configuration was changed as part of Phase 46. No real TTS request was made during cleanup.

## Size and archive decision

Project size after cleanup: approximately `34G`. A precise pre-cleanup size was not captured before the cache-only removal; the cleanup objective was organization and safety, not disk reclamation. Historical experiments were retained in place rather than archived because moving a dirty, research-heavy tree would create unnecessary reference risk.
