# PHASE 21 TEMPERATURE TUNING REPORT

## Status

PASS — implementation ready. Temperature winner is **UNSELECTED** until the user explicitly selects one.

## Quality gate

AWAITING USER LISTENING. No new user listening result was supplied during this phase, so no structural problem is hidden by sampling changes and no temperature is treated as a winner.

## Selected saved voice

Selected at run time from the main **Giọng đọc** selector. Temperature Round rejects preset voices and requires an existing saved/custom voice. The user-selected speaker profile is not modified.

## Baseline

```text
speed: 1.0
temperature: 0.8
top_k: 25
top_p: 0.95
repetition_penalty: 1.2
```

## Temperature candidates

```text
0.7 — thiên về ổn định
0.8 — baseline cân bằng
0.9 — thiên về biến hóa
```

These are guidance labels only; code makes no perceptual-quality claim.

## Blind comparison

Not implemented. Voice Lab remains intentionally small and user-triggered: generate one persisted sample at a time, score it, then generate the next candidate using exactly the same selected quality text. No automated batch or parallel inference was added.

## Repeatability workflow

- Screening: select the saved voice, same quality sentence, then generate one sample at each 0.7 / 0.8 / 0.9.
- Repeatability: retain at most two user-selected candidates; use two quality texts with two runs each.
- `temperature_summary()` reports only user-entered evaluation data: evaluated-run count, average score, criterion averages, and missing-word count. It does not use waveform metrics to choose a winner.

## Missing-word tracking

Existing missing-word flag and note persist with every evaluation. Experiment history now renders a visible `⚠ Có mất/nuốt chữ` warning, so an average score cannot conceal this failure.

## Preferred configuration persistence

`data/voice_lab/temperature_candidates.json` is created only after an explicit **Chọn temperature này** confirmation. It stores, per saved voice, its ID, temperature, locked sampling values, selection time, and user-score summary. It never stores or rewrites `speaker_emb` or `codes`. This is a candidate configuration, not a final branded-voice manifest.

## Main TTS integration

When the selected main voice has a saved candidate configuration and Advanced controls are closed, main `/api/tts` automatically receives that preferred sampling configuration. If the user opens Advanced and changes a field, those manual values win for that request. **Khôi phục mặc định** restores the selected voice candidate when present.

## Files created

- `tests/test_phase21_temperature_tuning.py`
- `diagnostics/phase21_temperature_tuning_report.md`

## Files modified

- `backend/app/voice_lab.py`
- `backend/main.py`
- `frontend/app.js`
- `frontend/index.html`
- `tests/test_frontend_runtime_hotfix.py`

## Tests

```text
PYTHONPATH=. .venv/bin/pytest -q tests/test_phase21_temperature_tuning.py tests/test_phase20_voice_quality.py tests/test_engine_reference.py tests/test_voice_lab.py tests/test_frontend_runtime_hotfix.py tests/test_multiformat_saved_voice.py
46 passed

node --check frontend/app.js: PASS
python -m py_compile selected backend modules: PASS
git diff --check: PASS
```

Coverage includes candidate whitelist, fixed sampling values, saved-voice-only temperature runs, explicit selection requirement, config persistence without identity data, user-score-only summary, saved-voice `/api/tts` path, manual override precedence, Phase 20 edge/chunk tests, Voice Lab audio persistence, and multi-format Save Voice contracts.

## Regression

```text
History: PASS — unchanged persistence architecture
Save Voice WAV/MP3/M4A: PASS — retained contract tests
Clone: PASS — unchanged clone path / shared reference processing
Voice Lab audio: PASS — same IndexedDB Blob/replay path
Chunk fix: PASS — retained Phase 20 tests
Speaker identity: PASS — candidate config excludes speaker_emb/codes
Concurrency: PASS — no parallel generation added; TTS_MAX_CONCURRENCY=1 retained
```

## Real inference

0. No real model inference, benchmark, or automated sampling batch was run.

## USER ACTION REQUIRED

1. Restart backend and hard reload `http://localhost:5173`.
2. Select the saved voice, then make two baseline runs at **0.8 / speed 1.0** with the same quality sentence.
3. If there is no structural loss, generate the same sentence at **0.7**, **0.8**, and **0.9**, one at a time; score and mark missing words.
4. Use **Chọn temperature này** only for the value you explicitly prefer.

## Recommended next step

If a temperature is selected: **PHASE 22 — TOP_P + LONG-FORM PROSODY TUNING**.

If structural loss remains: **VOICE PIPELINE INVESTIGATION CONTINUATION**.
