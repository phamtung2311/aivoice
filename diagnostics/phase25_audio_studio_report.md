# Phase 25 — Audio Studio

## Status

Complete. Audio Studio is an additive, browser-local audio-project workspace. It does not modify the model, inference, cloning, Voice Lab, embeddings, speaker codes, chunking, or Smart Text Processing.

## Architecture

Project metadata is stored under `aivoice_audio_studio_project` in localStorage:

- `title`, `created_at`, `updated_at`
- `segments[]` with text, voice, speed, captured advanced settings, duration, status, and audio availability

Generated WAV blobs remain in IndexedDB, using the existing Voice Lab blob store with a `studio:` key prefix. This keeps Studio blobs separate from TTS history keys without an IndexedDB schema migration.

Each segment calls the existing `POST /api/tts` once. The existing backend semaphore therefore continues to serialize inference; Audio Studio never batches segments. Browser playback handles one segment or sequential play-all. Browser Web Audio decodes and concatenates matching-rate PCM segments, then exports a PCM16 WAV; no server merge is used.

## Files modified

- `frontend/app.js`
- `frontend/index.html`
- `frontend/styles.css`

## Files created

- `tests/test_phase25_audio_studio.py`
- `diagnostics/phase25_audio_studio_report.md`
- `diagnostics/phase25_work_report.md`

## Features

- New **Audio Studio** workspace tab, without redesigning TTS or Voice Lab
- Add, delete, duplicate, move up/down, and edit segments
- Generate or regenerate one selected segment only
- Per-segment voice, speed, and captured advanced settings
- Single-segment playback and sequential play-all
- Auto-save project metadata locally
- Export ready segments as one WAV in the browser

## Performance

Only one Studio generation can be active in the UI at once, and every generation is a normal single `/api/tts` request. Audio merge/export is browser-only and occurs only on explicit export. No network service, model change, server merge, or batch inference is introduced.

## Regression

Existing TTS history keys and Voice Lab experiment keys are untouched. Studio keys are namespaced. The existing IndexedDB version/store layout is preserved, so no migration or history cleanup behavior changes. The clone endpoint is not called from Studio.

## Tests

- `node --check frontend/app.js` — PASS
- `.venv/bin/python -m py_compile backend/main.py backend/app/tts/audio.py backend/app/tts/nlp.py` — PASS
- `git diff --check` — PASS
- Focused pytest for Phase 25, frontend runtime safeguards, and Phase 24 — PASS

## Manual verification

1. Click **Audio Studio**, add two segments, edit their text/voice/speed, and confirm the project saves after each edit.
2. Generate one segment and confirm only that card changes to Ready.
3. Duplicate/reorder/delete segments and reload the page; confirm metadata remains.
4. Play an individual segment, then **Phát tất cả** to verify ordered playback.
5. Export WAV after two ready segments and verify the downloaded file contains both clips in sequence.

## Remaining issues

Export intentionally refuses mixed sample-rate segments, because resampling would violate the no-quality-loss requirement. Normal AIVoice output uses one engine sample rate, so ordinary projects export directly.
