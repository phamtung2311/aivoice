# PHASE 19.3 MULTI-FORMAT SAVE VOICE REPORT

## Status

PASS (code and local contract tests). Real-browser save with the user's current M4A still requires the short user test below.

## Previous limitation

`/api/tts/clone` already accepted WAV, MP3, and M4A, but `/api/voices/save` rejected every non-WAV filename before reference preparation. Both the normal Clone panel and Voice Lab mirrored that backend limitation by disabling Save Voice for MP3/M4A.

## Root cause

The multi-format decoder was already present in `backend/main.py` as `_prepare_reference_wav()` and `_decode_audio_to_wav()`. The save endpoint had a separate hard-coded `.wav` guard and passed the raw upload temp path directly to enrollment instead of reusing that decoder.

## New Save Voice contract

```text
WAV: accepted and enrolled
MP3: decoded locally to temporary PCM WAV, then enrolled
M4A: decoded locally with FFmpeg to temporary WAV, then enrolled
```

Unsupported extensions return HTTP 400, oversize uploads return 413, unreadable audio returns 400, duration over 8 seconds returns 413, and duplicate names return 409 without overwrite.

## Reference processing

The endpoint validates the voice name and supported extension, rejects duplicate names before expensive decode, enforces 5 MiB, writes the original upload to a format-preserving temporary file, calls the same `_prepare_reference_wav()` used by clone, validates the decoded WAV and duration, and enrolls it through the existing concurrency semaphore and voice-store path.

No second decoder or dependency was added.

## Identity source

```text
original user reference
not generated TTS output
```

For MP3/M4A, only the original reference is decoded to a local temporary WAV. That WAV is supplied to native enrollment, which derives and persists `speaker_emb` plus `codes`. The generated Voice Lab sample is never submitted to `/api/voices/save`.

Frontend current-sample state retains the exact `File` object used for generation and now displays its filename. Replacing a slot afterward therefore cannot silently substitute the new file when saving the old sample.

## Temp cleanup

The original upload temp and converted WAV temp are both removed from one outer `finally` on:

- success;
- invalid/empty/oversize/unreadable audio;
- excessive duration;
- decoder failure;
- enrollment failure;
- duplicate race under the enrollment lock.

Raw reference audio and converted WAV are not persisted. Only the local saved profile metadata, embedding, and codes remain.

## Frontend behavior

Both Save Voice surfaces now treat `.wav`, `.mp3`, and `.m4a` as eligible. The button requires a supported current reference and non-empty name. UI wording is now:

```text
Hỗ trợ lưu giọng từ WAV, MP3 và M4A. File sẽ được xử lý cục bộ trên máy.
```

Voice Lab submits `current.reference.file`, not the generated sample Blob.

## Voice list refresh

On success, the frontend reloads `/api/voices` with the returned/new voice ID as the preferred selection. The saved voice appears immediately in the main selector, preview list, and saved-voice panel without page reload.

## Persistence across restart

A fake enrollment test saved an M4A-derived profile containing embedding/codes through the local voice store, then loaded it through a fresh store read. The voice and identity fields remained available. No biometric arrays were printed.

## Files modified

- `backend/main.py`
- `backend/app/tts/engine.py`
- `frontend/app.js`
- `frontend/index.html`
- `tests/test_frontend_runtime_hotfix.py`

## Files created

- `tests/test_multiformat_saved_voice.py`
- `diagnostics/phase19_3_multiformat_save_voice_report.md`

## Tests

```text
node --check frontend/app.js: PASS
python py_compile backend/main.py and voice modules: PASS
targeted pytest: 36 passed
git diff --check: PASS
served frontend build 19.3: PASS
```

Tests cover WAV/MP3/M4A save, invalid extension, oversize, duration >8 seconds, duplicate-before-decode, decode failure, engine failure, temp cleanup, description forwarding, profile reload, exact current-reference frontend contract, immediate voice refresh, and shared clone/save decoder usage.

The known Python 3.14 TestClient/AnyIO hang was avoided by directly exercising the async endpoint with in-memory `UploadFile` fixtures and a synchronous test executor shim. No dependency was changed.

## Regression

```text
History: PASS — user verified; IndexedDB/history code unchanged
Voice Lab audio: PASS — store/version/replay code unchanged
Clone WAV: PASS — route unchanged; shared helper contract intact
Clone MP3: PASS — route unchanged; shared MP3 decoder exercised
Clone M4A: PASS — route unchanged; shared FFmpeg decoder exercised
Saved voice WAV: PASS
Saved voice MP3: PASS
Saved voice M4A: PASS
Identity {speaker_emb,codes}: PASS
Concurrency: PASS — existing TTS_MAX_CONCURRENCY=1 semaphore retained
```

No real model inference, benchmark, dependency change, commit, push, or history architecture change was performed.

## USER MUST TEST

1. Restart the backend, then hard reload `http://localhost:5173`.
2. Upload current `a.m4a` and generate a sample.
3. Enter a unique voice name and click **Lưu giọng này**.
4. Confirm it appears selected in the main voice selector.
5. Generate a new sentence with the saved voice.

## Remaining issues

Real-browser enrollment quality and persistence after an actual backend restart require user confirmation. M4A save requires the already-installed local FFmpeg binary.

## Recommended next step

After the user confirms save works:

```text
ROUND 1 REFERENCE SELECTION / TEMPERATURE TUNING
```
