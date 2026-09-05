# PHASE 21.1 REMOVE CLONE PANEL REPORT

## Status

PASS

## Product decision

The user decided to remove the standalone “Clone giọng nói” panel from the main UI because Voice Lab already provides a better, complete cloning workflow and the duplicate panel made the page long and confusing.

From this phase on:

```text
VOICE LAB is the only voice-cloning / reference-experiment workflow.
```

Main UI flow is now:

```text
MAIN TTS → Saved voices / voice selector → History → VOICE LAB
```

## Removed UI

From `frontend/index.html`:

- The entire `<section class="card cardClone">` card: header `🎤 Clone giọng nói`, description, its private drop zone (`cloneDropzone`), hidden file input (`cloneInput`), file metadata row (`cloneFileMeta` + name/size/format/remove), status line (`cloneInfo`) and privacy note (`cloneNote`).
- The old enrollment row inside “Giọng đã lưu”: `<div class="saveVoiceRow">` (`saveVoiceName` input + `saveVoiceBtn`), which only worked together with the removed panel’s reference file.
- Guidance added next to saved voices: `Muốn tạo giọng riêng? Hãy dùng Voice Lab bên dưới.`

Kept untouched: main TTS card, advanced sampling panel, result/history column, and the whole Voice Lab section.

## Removed JavaScript

From `frontend/app.js` (net −138 lines across frontend+tests):

- DOM references: `cloneDropzone`, `cloneFileMeta`, `cloneFileNameEl`, `cloneFileSizeEl`, `cloneFileFormatEl`, `cloneFileRemove`, `cloneInput`, `cloneInfo`.
- Main-panel-only refs/state: `saveVoiceNameInput`, `saveVoiceBtn`, `selectedRefFile`.
- Functions: `probeWavDuration()`, `clearCloneFile()`, `handleCloneFile()`, `updateSaveVoiceState()` and the old save handler that POSTed `selectedRefFile` to `/api/voices/save`.
- Event listeners: clone input change, drop-zone click/keyboard/dragenter/dragover/dragleave/drop, remove-file button, save-voice-name input, save-voice button.
- Dead branches around synthesis: `usingClone` button label logic and the whole multipart `/api/tts/clone` request path inside `synthesize()`; cancel/timeout behavior unchanged.

Shared helpers deliberately NOT removed because Voice Lab reuses them: `CLONE_ACCEPTED_EXTENSIONS`, `REF_MAX_SECONDS`, `REF_MAX_BYTES`, `extensionOf()`, `formatFileSize()`, `canSaveVoiceReference()`, `SAVE_VOICE_FORMAT_HELP`, `waitForAudioDecode()`. Verified by grep: zero remaining references to any removed symbol; no null-access path left.

## Removed CSS

From `frontend/styles.css` (only styles whose sole consumer was the removed panel):

- Whole `── Clone dropzone ──` block: `.cardClone`, `.dropzone` (+hover/focus/drag), `.dropIcon`, `.dropMain strong`, `.formatsLine`, `.fileMeta`, `.fileName`, `.formatBadge`, `.cloneStatus`.
- `.saveVoiceRow{}` and `.cardDesc{}` (only usages were the clone panel enrollment row/description).
- Added one tiny rule for the new guidance line: `.savedVoicesGuide`.

Shared styles preserved unformatted: `.uploadLabel`, buttons, audio player, voice-preview list, saved-voice list, Voice Lab cards.

## Preserved backend clone contract

Backend untouched (zero backend diffs):

```text
POST /api/tts/clone   — still exists, still used by Voice Lab generate
POST /api/voices/save — still exists, still used only by Voice Lab “Lưu giọng này”
WAV / MP3 / M4A handling, speaker_emb + codes, 5 MiB cap, temp cleanup: unchanged
```

Frontend remains the single `/api/tts/clone` consumer via Voice Lab; identity submitted to `/api/voices/save` is still the original reference file, never the generated sample.

## Voice Lab regression

```text
Reference A/B/C upload + WAV/MP3/M4A validation: PASS (code untouched)
Generate sample via /api/tts/clone: PASS
Listen + rubric evaluation + experiment history: PASS
Save Voice WAV/MP3/M4A → /api/voices/save with original-reference identity: PASS
Temperature Round 0.7/0.8/0.9 workflow + candidate persistence: PASS
Phase 20 quality fixes: PASS — backend untouched
IndexedDB sample storage/replay: PASS — untouched
```

## Saved voices regression

Panel kept: view (`savedVoicesList`), preview (▶), use (`selectValidVoice`), delete (`DELETE /api/voices/{id}`), error surface `saveVoiceInfo`, main selector grouping “Giọng đã lưu”. Only the old enrollment row was removed; saving new voices happens exclusively in Voice Lab.

## Main TTS regression

`synthesize()` now always sends JSON `{text, voice, speed}` (+ manual advanced sampling or Phase 21 preferred-candidate config) to `/api/tts` — identical payload semantics to the previous non-clone branch. Regenerate, download, cancel, timeout, history blob persistence, temperature-candidate auto-config, and voice selector refresh unchanged. Contract tests assert the `/api/tts` JSON path stays intact and `playHistoryItem` remains blob-only replay.

## Files modified

- `frontend/index.html`
- `frontend/app.js`
- `frontend/styles.css`
- `tests/test_frontend_runtime_hotfix.py`

No backend file changed. No dependency added or removed. Nothing committed/pushed/reset/restored.

## Files created

- `diagnostics/phase21_1_remove_clone_panel_report.md`
- Optional navigation only inside existing files: `openVoiceLabBtn` button + guidance sentence.

## Tests

```text
node --check frontend/app.js: PASS
git diff --check: PASS
PYTHONPATH=. .venv/bin/pytest -q tests/test_frontend_runtime_hotfix.py tests/test_voice_lab.py tests/test_phase21_temperature_tuning.py tests/test_phase20_voice_quality.py tests/test_multiformat_saved_voice.py tests/test_clone_formats.py
→ 56 passed
PYTHONPATH=. .venv/bin/pytest -q tests/
→ 101 passed, 1 warning (pre-existing Starlette deprecation warning)
```

Updated contracts: cache-bust assertions → `v=21.1`; build marker → `21.1`; multi-format Save eligibility gate no longer slices through deleted clone functions; new test `test_phase21_1_duplicate_clone_panel_removed_and_contracts_kept` asserts panel markup/JS/CSS markers are gone while `id="voiceLab"`, saved-voice preview/delete, `openVoiceLabBtn`, one Voice Lab `/api/tts/clone` call, and one Voice Lab `/api/voices/save` call survive. Clone API existence itself is covered by `tests/test_clone_formats.py` + `tests/test_sampling_params.py`.

## Frontend build

```text
styles.css?v=21.0 → v=21.1
app.js?v=21.0     → v=21.1
const AIVOICE_FRONTEND_BUILD = '21.0' → '21.1'
```

Hard reload will load the new UI without stale assets.

## USER MUST TEST

```text
1. hard reload localhost:5173
2. confirm Clone panel is gone
3. scroll to Voice Lab
4. upload A/B/C
5. generate one sample
6. Save Voice
7. confirm saved voice appears in main selector
8. generate main TTS
9. replay History
```

## Remaining issues

- Real-browser confirmation of the 9 steps above is pending user execution.
- Pre-existing observation (unchanged, out of scope): the main “Biểu cảm” select currently affects nothing in the preset/saved-voice `/api/tts` payload — it previously mattered only on the removed clone path. Left as-is to avoid feature expansion.

## Recommended next step

```text
CONTINUE TEMPERATURE LISTENING / PHASE 22 AFTER USER SELECTION
```

Do not automatically start.

