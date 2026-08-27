# PHASE 19 WORK REPORT

## Status

PASS (code, persistence contracts, and local API smoke checks). Browser audio interaction remains a manual verification item because no browser instance was available to this session.

## Executive summary

Voice Lab is now a Round 1 workflow: select a reference, generate a baseline sample, listen, score, save the useful WAV reference as a reusable voice, and compare stored samples later. Main TTS history and Voice Lab experiments now persist audio blobs in IndexedDB, with metadata kept separately and accurately downgraded when cleanup removes audio.

## History root cause

The browser database used the permanently fixed IndexedDB version `1`. If `aivoice_history` had already been created without `history_audio` (for example by an earlier frontend build), `onupgradeneeded` could not run again. `idbPutAudio()` then failed its transaction; the UI intentionally caught that failure and wrote a metadata-only entry with `hasAudio=false`. This exactly produces history rows with text but no replayable audio.

## History audio fix

```text
main TTS save: Blob -> aivoice_history/history_audio; metadata -> localStorage tts_history
schema migration: IndexedDB version 2 creates missing stores without clearing existing data
replay: IndexedDB Blob -> Object URL -> existing audio player; no POST /api/tts path
reload: localStorage metadata and IndexedDB Blob use the same item ID
legacy fallback: disabled “Nghe lại” + “Chỉ lưu nội dung”
cleanup: max 20 metadata / 10 blobs; cleanup changes hasAudio=false rather than removing metadata
```

History replay revokes the previous history Object URL and never writes a new history item.

## History UI fix

History buttons now use explicit foreground color, borders, and readable disabled labels in both themes. Metadata-only items are a normal legacy state rather than a severe “audio unavailable” error.

## Voice Lab Save Voice

```text
WAV: enabled after a current sample exists and a name is entered
MP3: blocked with WAV guidance
M4A: blocked with WAV guidance
missing reference/sample: blocked
duplicate name: backend 409 is shown without overwrite
voice list refresh: /api/voices reloads immediately after save
main TTS reuse: saved voice is selected and appears in preview/list without page reload
```

The action submits the original reference WAV that created the current sample, never the generated sample audio. Optional description is stored in the local saved-voice profile.

## Voice Lab audio persistence

Each experiment gets its server ID first, then its WAV Blob is stored under that ID in IndexedDB store `voice_lab_audio`; server metadata is patched to `has_audio=true` only after storage succeeds. Experiment history replay reads that Blob directly and does not regenerate. The cap is 25 samples; cleanup removes the Blob and updates its record to `has_audio=false`.

## Round 1 workflow

Round 1 is locked to speed 1.0, temperature 0.8, top_k 25, top_p 0.95, and repetition penalty 1.2. The technical fields sit under **Nâng cao**; generated records are always `reference_selection`. Run number auto-increments for the selected reference/evaluation sentence.

## UX simplification

The main path is now Mẫu A/B/C → câu đánh giá → tạo → nghe/chấm → lưu. Vietnamese labels were applied to the primary Voice Lab sections and history.

## Files created

- `diagnostics/phase19_manual_round1_checklist.md`
- `diagnostics/phase19_work_report.md`

## Files modified

- `frontend/app.js`
- `frontend/index.html`
- `frontend/styles.css`
- `backend/main.py`
- `backend/app/voice_lab.py`
- `backend/app/tts/model.py`
- `tests/test_voice_lab.py`

## Tests

```text
node --check frontend/app.js: PASS
python py_compile backend/main.py backend/app/voice_lab.py backend/app/tts/model.py: PASS
pytest -q tests/test_voice_lab.py tests/test_engine_reference.py: 12 passed
GET /api/health: PASS (local running backend)
GET /api/voices: PASS (local running backend)
git diff --check: PASS
```

Coverage includes experiment audio-status persistence, Voice Lab Blob ID mapping/replay contract, baseline lock, save-voice UI contract, and the absence of a fetch path in `playHistoryItem()`.

## Manual browser verification

No browser instance was available through the connected browser surface, so interactive IndexedDB/audio playback must be verified with `diagnostics/phase19_manual_round1_checklist.md`.

## Regression

The Phase 17 clone identity structure `{speaker_emb, codes}`, `/api/health`, `/api/voices`, main `/api/tts`, clone/upload routes, WAV-only saved voice enrollment, and `TTS_MAX_CONCURRENCY=1` were preserved. No dependency, model, concurrency, database, reset, commit, or push change was made.

## Resource safety

Voice Lab continues to generate only one sample at a time through the existing clone endpoint and shared concurrency semaphore. No inference batch or benchmark was run.

## Remaining issues

Interactive playback and actual reference quality still need a human browser/listening pass. Existing metadata-only history cannot recover audio that was never stored; it is now labeled accurately.

## USER ACTION REQUIRED

1. Reload the frontend once to apply the IndexedDB v2 migration.
2. Upload Reference A/B/C and generate one Round 1 sample at a time.
3. Listen and score each sample; replay them from experiment history after reload.
4. Save the best WAV reference with **Lưu giọng này**, then create main TTS using the saved voice and verify main-history replay.

## Recommended Phase 20

TEMPERATURE TUNING ON SELECTED REFERENCE
