# PHASE 22.2 PRESET PRONUNCIATION REGRESSION REPORT

## Status

PARTIAL — no code regression found that can explain the preset behavior change; documented exact evidence, added automated guards, and left production unchanged per §19 (no speculative edit while the cause is not proven).

## User evidence

```text
Before:
Preset “người”           → ĐÚNG
Saved cloned “người”     → SAI (“ngờ i”-style)

After Phase 22.1 backend restart:
Preset “người”           → reported SAI
```

## Exact regression found

None in source. The preset inference path is provably byte-identical to pre-Phase-22/22.1:

```text
engine.py   → untouched (only text/main/model/voice_store/voice_lab changed)
audio.py    → untouched
text.py     → only adds normalize_vi_input() (NFC + invisible cleanup) at the top
               · for clean text output is byte-identical to legacy (probe)
model.py    → refactor of USER saved-voice persistence only (serialize/deserialize moved
               into voice_store); preset handling untouched
main.py     → additive; when conditioning_mode is absent the generate call is unchanged
voice_lab.py→ schema additions only; not on the main TTS path
```

## Phase responsible

Not Phase 22 / Phase 22.1 / not runtime stale. Prime remaining candidates:
1) **Sampling stochasticity**: user ran each voice once; "người" is a known weak point; single-sample correctness is NOT significant evidence.
2) **Voice selector still on the saved voice**: localStorage persists the selection; after Save Voice the app auto-selects the saved voice — a plain Generate may actually have used the saved voice, not the preset.

## Preset request payload

Main TTS `POST /api/tts` from `frontend/app.js synthesize()`:

```text
{ text, voice, speed }
 (+ temperature/top_k/top_p/repetition_penalty ONLY when Advanced panel is open
   or the selected voice has a saved Phase-21 candidate config)
No conditioning_mode is ever added by synthesize() (verified statically + new test).
```

Absent `conditioning_mode` ⇒ `engine_kwargs = {}` ⇒ `generate(..., **{})` is byte-identical to pre-22.1.

## Preprocessing comparison

For the fixed diagnostic sentence (and the whole §6 corpus), via `scripts/phase22_2_text_probe.py` (byte-level, no model load):

```text
legacy_pre == current_pre == raw  → True (byte-identical)
phonemes_all_equal (raw / legacy / current / NFD variants) → True
current phonemes: mˌɔ6j ŋˈyə2j ɗˌaːŋ ˈəː4 ɗˈəɪ.
```

The only behavioral delta of Phase 22 hygiene is on poisoned input (zero-width/soft-hyphen inside a word), confirmed again:

```text
legacy: "Mọi ng​ười đang ở đây."  (splits "ng"+zero-width+"ười")
current: "Mọi người đang ở đây."   (cleaned)
```

## Conditioning path

- `conditioning_mode` lives only on `TTSRequest` and is read only in Voice Lab sample generation for **saved-N** voices; ordinary preset/saved main-TTS never sends it (regression test proves it; producer statically located in Voice Lab).
- `identity_only` is rejected for presets (HTTP 400) at the API layer. Private-preset inference never sees `use_ref_codes=False`.

## Runtime process verification

- Backend: PID 64780 `uvicorn backend.main:app --host 127.0.0.1 --port 8000`, cwd `<...>/ai voice`, started 21:28:03 — **after** newest source mtime (21:21:32) ⇒ running Phase-22.1 code.
- `/openapi.json`: `TTSRequest.conditioning_mode` present ⇒ Phase-22.1 backend live.
- Frontend: `python3 -m http.server 5173 --directory frontend`; served `app.js?v=21.1`, build marker 21.1, conditioning UI present ⇒ current.
- No stale mix: new backend + new frontend.

## Fix made

None (deliberately). Source change was not proven responsible; a speculative production change would violate §19. Phase 22 Unicode hygiene and Phase 22.1 Voice-Lab experiment infrastructure remain safely isolated and do not affect preset inference (proven above).

## Files modified

- `tests/test_phase22_2_preset_regression.py` (new)
- `scripts/phase22_2_runtime_audit.py` (new, diagnostic)
- `scripts/phase22_2_text_probe.py` (new, diagnostic)

No production code changed in this phase.

## Tests

```text
pytest tests/test_phase22_2_preset_regression.py → 7 passed
FULL SUITE → 131 passed, 1 warning (pre-existing Starlette deprecation)
git diff --check → PASS
node --check frontend/app.js → PASS
```

New contracts: preset ordinary TTS never receives `identity_only`; absent `conditioning_mode` preserves the legacy inference call; frontend main `synthesize()` never sends `conditioning_mode` (payload `{text, voice, speed}`); diagnostic sentence survives preprocessing byte-identically to legacy; Phase-22 invisible cleanup still works; Phase-20 chunking intact; history replay untouched (blob-only); Save Voice still Voice-Lab-only.

## Real inference

0 (none performed by the agent).

## USER MUST TEST

```text
1. Hard reload localhost:5173 (frontend serve is current; backend PID 64780 is current).
2. In the voice selector, explicitly click a PRESET (e.g. “Trúc Ly” under “Giọng mặc định”) — do NOT rely on the auto-selected saved voice.
3. Run the text “Mọi người đang ở đây.” 3 times (speed 1.0 / 0.8 / 25 / 0.95 / 1.2).
4. Report: Run 1 → đúng/sai · Run 2 → đúng/sai · Run 3 → đúng/sai.
5. Only after preset is confirmed restored, test the saved voice again.
```

## Recommended next step

Do NOT recommend further tuning until preset baseline is restored. If the preset is 3/3 correct again → the earlier "preset wrong" was either the wrong voice selected (saved voice auto-selection) or stochastic single-sample noise → return to the Phase 22.1 A/B saved-voice diagnosis. If the preset is 3/3 wrong, reconfirm the running source under the exact process and capture the exact request including which voice id was sent. Do not automatically continue.