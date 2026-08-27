# PHASE 19.1 BROWSER HOTFIX REPORT

## Status

```text
CODE PASS
LOCAL CONTRACT TEST PASS
```

## Browser verification status

```text
AWAITING USER
```

## History root cause

The real-browser wording is decisive evidence that the tab was not executing the Phase 19 frontend: it displayed `Audio không còn khả dụng`, while that string no longer exists anywhere in the current source. The static server used unversioned `app.js`/`styles.css`, so an open or cached tab could continue running the pre-hotfix history path even after workspace files changed.

The Phase 19 migration also stopped at IndexedDB version 2. That was not robust against an intermediate browser database already marked v2 but missing one store; IndexedDB would not rerun `onupgradeneeded`. Browser inspection was unavailable, so the actual `localhost` store list could not be read in this session. Phase 19.1 therefore adds a non-destructive v3 migration that creates either missing store.

No database is deleted or wiped.

## IndexedDB runtime schema

```text
version: 3
stores: history_audio, voice_lab_audio
migration: additive onupgradeneeded; create only missing stores
```

`window.aivoiceStorageDiagnostics()` is available in developer tools and reports only DB version, store names, metadata count, history-audio count, and Voice Lab audio count. It never reports text or audio content.

## History save flow

The new entry begins with `hasAudio=false`. The frontend validates the Blob, writes it under the generated history ID, immediately reads the same ID back, verifies the returned value is a Blob of the same size, and only then sets `hasAudio=true` in localStorage metadata. Open, upgrade, transaction, and verification failures retain metadata-only state and emit small structured diagnostics without audio content.

Assets are now requested as `app.js?v=19.1` and `styles.css?v=19.1`, preventing the Phase 19.1 HTML from reusing the old unversioned bundle.

## History replay flow

Replay remains:

```text
history item ID -> IndexedDB history_audio Blob -> Object URL -> audio player
```

`playHistoryItem()` has no fetch or `/api/tts` call, does not add history, and revokes prior playback URLs.

## Voice selection root cause

The live backend returns 20 valid voices beginning with Adam, Kim Thanh, Mai Anh, Minh Triết, and Minh Đức; it does not return `default`. Frontend error handling previously inserted a fabricated `default` option whenever `/api/voices` failed temporarily. Main TTS then sent that invalid ID, and backend correctly returned HTTP 400.

## Voice selection fix

Voice loading now accepts only non-empty IDs returned by `/api/voices`. Selection priority is:

```text
explicit preferred saved voice
current valid selection
persisted selection if still valid
first valid API voice
```

An invalid persisted value such as `default` is ignored. If no valid voice list is available, the selector and generate action stay disabled instead of inventing an ID. Voice refreshes use a sequence guard so an older request cannot overwrite a newer saved-voice refresh.

## API error handling

For 4xx/5xx responses the frontend safely reads a string `detail`, limits it to 300 characters, and displays it. It retains the existing generic Vietnamese fallback when JSON/detail is absent. Stack traces and arbitrary response objects are not displayed.

## History contrast fix

The runtime-created History buttons previously had no `secondary` class, so the intended Phase 19 rule did not apply. Every replay, download, regenerate, and delete button now receives the existing button class, plus History-specific active, hover, disabled, dark, and light token-based colors. Disabled text remains readable without low opacity.

## Canonical frontend origin

```text
http://localhost:5173
```

The frontend README and manual checklist now use this origin consistently. CORS support for both localhost and 127.0.0.1 remains intact, but their browser storage is intentionally not merged.

## Files modified

- `frontend/app.js`
- `frontend/index.html`
- `frontend/styles.css`
- `frontend/README.md`
- `diagnostics/phase19_manual_round1_checklist.md`
- `tests/test_frontend_runtime_hotfix.py` (created)
- `diagnostics/phase19_1_browser_hotfix_report.md` (created)

Existing Phase 15–19 workspace changes were preserved.

## Tests

```text
node --check frontend/app.js: PASS
python py_compile selected backend modules: PASS
pytest runtime hotfix + Voice Lab + identity: 19 passed
git diff --check: PASS
served http://localhost:5173 index references app.js?v=19.1: PASS
served app.js contains IndexedDB version 3: PASS
GET /api/health: PASS
GET /api/voices: PASS, 20 voices, no default ID
POST /api/tts with deliberate invalid voice: HTTP 400 before inference, detail preserved
```

Automated contracts cover schema version/stores, put-then-get before `hasAudio=true`, Blob-only replay, invalid/persisted default rejection, backend detail rendering, cache-busted assets, diagnostics counts, and explicit History contrast classes.

## Regression

Clone WAV/MP3/M4A, native `{speaker_emb, codes}` identity, WAV saved voices, Voice Lab metadata/audio stores, advanced sampling, both CORS origins, and `TTS_MAX_CONCURRENCY=1` remain unchanged. No real inference, dependency change, storage deletion, commit, or push was performed.

## USER MUST TEST NOW

1. Open only `http://localhost:5173` and perform a hard reload.
2. Confirm the voice selector shows a real name such as Adam, then generate `kiểm tra lịch sử âm thanh`.
3. Confirm the new History item has active **Nghe lại**, click it, and confirm audio plays.
4. Press F5, click **Nghe lại** again, and confirm the same audio still plays.
5. Confirm **Nghe lại**, **Tạo lại**, and **Xóa** are readable in the current theme.

## Remaining issues

The actual `localhost` IndexedDB schema and audio playback cannot be declared browser PASS until the user completes the checklist. Data under `http://127.0.0.1:5173` remains separate and is not migrated.

Recommended next step:

```text
WAIT FOR USER BROWSER VERIFICATION
```
