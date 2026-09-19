# Code maintenance notes

## Where to make changes

| Responsibility | File |
| --- | --- |
| HTTP endpoints, dependency injection and inference coordination | `backend/main.py` |
| Request schemas and text length contract | `backend/app/schemas.py` |
| Uploaded reference decoding and temporary WAV preparation | `backend/app/reference_audio.py` |
| Sampling parameter validation | `backend/app/validation.py` |
| Local inference | `backend/app/tts/engine.py` |
| Long-form job state and recovery | `backend/app/tts/long_audio.py` |
| Shared PCM WAV encoding | `frontend/audio-utils.js` |
| TTS workspace and Voice Lab | `frontend/app.js` |
| Standalone timeline editor, playback and export | `frontend/audio-studio.js` |

Both HTML entry points load `audio-utils.js` before their page script. It has no
DOM dependencies and is exercised in Node by `tests/test_audio_utils.py`.
Request schemas remain imported by `backend.main` so existing callers retain
their imports and FastAPI dependency overrides continue to work.

## Fixes included with the extraction

- Reject non-finite sampling values and fractional integer parameters before
  inference. Previously `NaN` bypassed range comparisons.
- Release workspace playback object URLs when `audio.play()` rejects, as well
  as when playback ends or audio decoding fails.
- Correct timeline silence conversion: clamp milliseconds to 100–30000, then
  divide by 1000. Previously a 2500 ms pause became 0.03 seconds.
- Freeze silence progress while paused and resolve its pending wait on Stop.
- Make standalone WAV export readable in stages: decode, resample, assemble,
  encode and download. Handle AudioContext construction failure in its error path.

## Validation on 2026-09-19

- Full pytest run: **251 passed, 10 failed** (261 collected).
- New behavioral tests: WAV headers, stereo PCM interleaving, clipping, invalid
  channel/rate input, playback rejection cleanup, silence duration/pause/stop,
  and sampling validation.
- JavaScript syntax checks and project smoke check passed; 34 API routes remain.
- No browser listening session or real model synthesis was performed for this refactor.

The full suite is not green. Remaining failures concern hard-coded frontend
build 21.1, obsolete editor-source expectations, removed phase reports, and an
old assertion limiting the special-voice catalog to two entries. In particular,
the old silence test expects a `setTimeout` implementation; the new behavioral
test checks elapsed time instead. These failures are left visible rather than
silenced or used to restore removed UI features.

## Recommended next work

1. Replace brittle frontend source-string assertions with browser interaction
   tests for generate, pause/resume, reload persistence and export. Decide which
   historical research-document checks belong outside the production suite.
2. Split endpoint groups into FastAPI routers after moving shared runtime state
   into explicit dependencies; avoid circular imports through `backend.main`.
3. Split the timeline renderer and project storage out of the page scripts.
   Define a storage error policy so quota failures never report a successful save.
4. Audit standalone queued playback: its async Promise executor can leave waits
   pending when playback is rejected, and object URLs need cleanup per segment.
5. Document a reproducible model install and test environment, then add CI for
   the checks that do not require model inference.
