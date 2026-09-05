# Phase 30Q.1 Report — Reliable Long-Form Generation

## Audit finding

The existing long-audio surface is **Audio Studio** (`audio-studio.html` and
`audio-studio.js`), a browser-local timeline project. Before this phase it
generated each segment via synchronous `POST /api/tts`, then retained WAV blobs
in IndexedDB and exported them in the browser. It was not a backend long-job
pipeline.

Normal TTS follows `index.html` → `app.js:synthesize` → `POST /api/tts` →
`main.py:tts` → shared semaphore → `TTSEngine.generate` / `generate_prosody` →
temporary WAV response → IndexedDB history. Its former 180-second browser
AbortController timeout could abandon the response while synchronous backend
work continued. HTTP disconnect does not cancel the Python/VieNeu work.

`FRONTEND TIMEOUT: 180 seconds (removed)`

`BACKEND AFTER FRONTEND TIMEOUT: continues`

`DUPLICATE JOB RISK: queued duplicate work was possible; overlapping heavy
inference was already prevented by the process-wide semaphore.`

## Existing capability matrix (before 30Q.1)

| Feature | Existing |
| --- | --- |
| Chunking | YES (inside `TTSEngine`) |
| Sequential synthesis | YES (engine chunks; Studio segments are user-triggered) |
| Job ID / progress / polling / cancellation / retry / resume | NO |
| Partial-result persistence | YES, browser-local completed Studio segments only |
| Duplicate protection | UI-only per page |
| Prosody support | Normal TTS YES; Audio Studio NO |
| Special Voice support | YES (same `/api/tts` voice registry) |

## Implemented

Audio Studio now uses a single local long-job extension of its existing
generation path: `POST /api/long-audio/jobs`, status polling, cooperative
`DELETE` cancellation, and final-audio retrieval. Jobs persist completed
chunk WAVs and metadata below ignored `data/jobs/<job-id>/` for diagnostics.
They split only clean prosody segments, synthesize sequentially, reuse the
existing `podcast_prosody_v1` parser, and assemble with the established
silence-deficit join behaviour. Markers never reach VieNeu.

Every chunk acquires the existing `_TTS_SEMAPHORE`; therefore normal TTS,
Audio Studio, Voice Lab, previews, and cloning remain limited to one heavy
inference at a time. Repeated Studio submission with the same idempotency token
returns its existing job. The Studio button is busy while a job is active.

Cancellation is truthful and cooperative: an active native inference is not
forcibly interrupted; no next chunk begins and the job becomes `CANCELLED`.

Normal TTS no longer has an elapsed-time failure path. It stays active with an
elapsed-time heartbeat until a server/network error, result, or explicit user
cancellation. Cancelling the browser request explains that the in-flight native
work may finish before another heavy job is admitted.

The normal TTS page also provides **Tạo Audio dài**, a one-click handoff that
keeps the entered original text, selected voice, speed, and editable TTS Script
when opening Audio Studio.

Podcast Brand Beta remains the ordinary `podcast_brand_beta` voice lookup, so
it resolves through the installed M-A profile without re-encoding or modifying
keeper artifacts. Audio Studio adds an editable TTS Script field and forwards
the approved Phase 30P.2 markers unchanged to the shared parser.

## Verification

`PYTHONPATH=. .venv/bin/pytest -q tests/test_phase30q1_long_audio.py tests/test_phase25_audio_studio.py`

Result: **6 passed**.

Python compilation, JavaScript syntax checks, and `git diff --check` passed.
