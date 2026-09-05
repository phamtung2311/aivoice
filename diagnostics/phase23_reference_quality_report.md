# Phase 23 — Reference Quality Optimization

## Status

Complete. Phase 23 adds reference-recording quality feedback only; it does not alter the TTS model, cloning behavior, enrollment, embeddings, speaker codes, or sampling parameters.

## Architecture

`POST /api/voice-lab/references/analyze` receives the uploaded reference bytes, calls the single `analyze_clip()` DSP entry point, returns the quality report, and saves metadata only. WAV/MP3 decode uses SoundFile; M4A/AAC has an FFmpeg pipe fallback with no retained file.

The browser analyzes once inside `setVoiceLabReference()` after a valid upload. The resulting report is attached to the in-memory reference metadata and is rendered in the existing Voice Lab reference card. Generate, playback, experiment history replay, and saved-voice operations do not call the analyzer.

`data/voice_lab/reference_history.json` is a small JSON history of metadata only. Explicit `PATCH /api/voice-lab/references/{reference_id}/preferred` updates the UI-only preferred flag; it neither selects the radio reference nor generates audio.

## Files modified

- `backend/app/tts/reference_quality.py`
- `backend/main.py`
- `backend/app/voice_lab.py`
- `frontend/app.js`
- `frontend/index.html`
- `frontend/styles.css`

## Files created

- `tests/test_phase23_reference_quality.py`
- `diagnostics/phase23_reference_quality_report.md`
- `diagnostics/phase23_work_report.md`

## DSP metrics

- Duration, sample rate, channels, peak, RMS, noise estimate
- Silence ratio plus leading and ending silence
- Clipping ratio/frame count and energy stability
- Bounded 0–100 score plus noise, volume, silence, clipping, and duration bars
- Strengths, weaknesses, practical tips, and a non-binding recommendation

## Performance impact

One local decode/DSP pass occurs per successful reference upload. No model is loaded and no TTS inference is invoked. Uploaded/decoded audio is held only for request processing; the persistent history contains filename, duration, score, sample rate, date, preferred, and quality report only.

## Regression

No TTS, clone, save-voice, speaker-code, chunking, or sampling code was changed. Preferred status is metadata-only and never silently changes the active reference.

## Tests

- `.venv/bin/python -m py_compile backend/app/tts/reference_quality.py backend/app/voice_lab.py backend/main.py` — PASS
- `node --check frontend/app.js` — PASS
- `git diff --check` — PASS
- Focused: `.venv/bin/python -m pytest -q tests/test_phase23_reference_quality.py tests/test_voice_lab.py tests/test_frontend_runtime_hotfix.py` — **31 passed**
- Full suite was started, but this execution runner terminates commands at its 30-second capture limit before reporting a final result. Run `.venv/bin/python -m pytest -q` in a normal terminal for the full-suite verdict.

## Manual verification

1. Open Voice Lab and upload a WAV, MP3, or M4A reference.
2. Confirm one quality report appears with score, five bars, strengths, weaknesses, tips, and recommendation.
3. Generate a sample repeatedly and replay history; confirm no new analysis request/report update occurs.
4. Click **Set Preferred** and confirm it changes only the explicit metadata label, not the selected reference or generation behavior.
5. Restart the backend and inspect reference history metadata; no audio files are created by analysis.

## Remaining issues

The CI-style full-suite command needs a runner with a capture timeout longer than 30 seconds. No functional Phase 23 issue is known from focused coverage.

## Recommended next step

Perform the manual browser verification above and run the full suite from a terminal with no 30-second command cap.
