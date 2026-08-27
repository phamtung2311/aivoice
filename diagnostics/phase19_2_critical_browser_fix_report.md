# PHASE 19.2 CRITICAL BROWSER FIX REPORT

## Status

```text
CODE PASS
LOCAL CONTRACT TEST PASS
```

## Browser status

```text
AWAITING USER
```

## `tx is not defined` root cause

The exact failure was in `frontend/app.js`, function `idbRun()`.

`const tx` was declared inside the `try` block, but `tx.oncomplete`, `tx.onerror`, and `tx.onabort` were assigned after that block. Because `const` is block-scoped, the first handler assignment referenced an undeclared variable and threw `ReferenceError: tx is not defined`.

Both `history_audio` and `voice_lab_audio` use `idbRun()`, so the one scope error explains both the Voice Lab crash and newly generated main History entries falling back to metadata-only state.

## Transaction fix

The transaction, object store, request, and all three transaction handlers now live in the same local `try` scope. There is no global transaction variable.

Success semantics are:

```text
open database
-> create local transaction
-> run store request
-> wait for tx.oncomplete
-> read request.result
-> close database
-> resolve Promise
```

Request, transaction, abort, open, missing-store, and blocked-upgrade failures are logged with the store/mode but no Blob content. `db.onversionchange` closes old connections. A blocked v3 upgrade records `BlockedError` and tells the user to close older AIVoice tabs.

## Main History persistence

Main History now follows:

```text
generated WAV Blob
-> create history ID with hasAudio=false
-> put Blob into history_audio
-> wait for transaction completion
-> get the same ID
-> verify Blob type and size
-> set hasAudio=true
-> save localStorage metadata
```

`addHistoryEntryWithAudio()` returns a boolean and absorbs storage failures. A successful TTS result remains in the player. If persistence fails, the UI reports `Đã tạo audio nhưng chưa lưu được vào lịch sử.` instead of changing the result into a generic generation failure.

## Voice Lab persistence

Voice Lab uses the same corrected transaction helper. `persistVoiceLabAudio()` writes the generated WAV to `voice_lab_audio`, waits for transaction completion, reads it back, verifies it, and only then PATCHes experiment `has_audio=true`.

The current sample and in-memory player are established immediately after clone generation, before experiment/IndexedDB persistence. A storage error therefore no longer clears the sample or produces `tx is not defined` as a generation error.

## Generation/persistence separation

Main TTS and Voice Lab now distinguish:

```text
generation failed -> no valid audio was generated
storage failed -> generated audio remains playable; history persistence warning only
```

Voice Lab also keeps the selected reference/current sample state when experiment metadata or IndexedDB persistence fails, so WAV Save Voice eligibility is not lost.

## Save Voice status

```text
M4A: clone supported; Save Voice disabled with explicit WAV-required guidance
MP3: clone supported; Save Voice disabled with explicit WAV-required guidance
WAV: Save Voice enabled when a current sample exists and a non-empty name is entered
```

For the user's current `a.m4a`, `b.m4a`, and `c.m4a` references, the disabled Save Voice action is expected. The UI now says that the M4A/MP3 sample can clone but the WAV version of the same reference is required for long-term saving. No silent conversion was added.

## IndexedDB schema

```text
database: aivoice_history
version: 3
stores: history_audio, voice_lab_audio
migration: additive; create each missing store for every older-version upgrade
deletion/wipe: none
```

`window.aivoiceStorageDiagnostics()` returns only frontend build, origin, DB version, store names, metadata/audio counts, and a sanitized `lastStorageError`.

## Frontend build

```text
AIVOICE_FRONTEND_BUILD: 19.2
assets: styles.css?v=19.2, app.js?v=19.2
canonical origin: http://localhost:5173
```

Build and origin are also logged once in the console. The running static server was checked and is serving build 19.2.

## Files modified

- `frontend/app.js`
- `frontend/index.html`
- `tests/test_frontend_runtime_hotfix.py`
- `tests/test_voice_lab.py`
- `diagnostics/phase19_2_critical_browser_fix_report.md` (created)

Existing workspace changes were preserved. Backend code was not changed in Phase 19.2.

## Tests

```text
node --check frontend/app.js: PASS
python py_compile selected backend modules: PASS
pytest frontend runtime + Voice Lab + native identity: 25 passed
mock IndexedDB transaction completion test: PASS
git diff --check: PASS
served index references app.js?v=19.2: PASS
served app.js exposes frontend build 19.2: PASS
GET /api/health: PASS
GET /api/voices: PASS, 20 voices
```

Regression coverage verifies local `tx` scope, `tx.oncomplete` resolution, put/read-back ordering, main `hasAudio` ordering, Voice Lab `has_audio` ordering, playable sample before persistence, WAV gate, M4A guidance, and build 19.2.

## Regression

Clone WAV/MP3/M4A, native `{speaker_emb, codes}` identity, WAV saved voices, Voice Lab experiment metadata, advanced sampling, both local CORS origins, and `TTS_MAX_CONCURRENCY=1` remain intact. No dependency, backend contract, database deletion, inference benchmark, commit, or push was performed.

## USER MUST TEST

1. Hard reload `http://localhost:5173`.
2. Main: generate `test audio 19.2`, play **Nghe lại**, press F5, then play **Nghe lại** again.
3. Voice Lab with current M4A: generate one sample, confirm no `tx is not defined`, play it, press F5, then replay it from experiment history.
4. Confirm M4A shows WAV-required Save Voice guidance.
5. Upload the WAV version, generate a sample, enter a name, save it, and confirm the voice appears in the main selector.

## Recommended next step

```text
WAIT FOR USER BROWSER VERIFICATION
```
