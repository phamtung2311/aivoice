# PHASE 20 VOICE QUALITY REPORT

## Status

PASS (structural pipeline audit, targeted fixes, and automated contracts). Human listening is still required to judge perceived quality.

## User quality symptoms

- The saved cloned voice is recognizably similar but sometimes rushed or hesitant.
- A later word can sound quiet or disappear, including the observed phrase `tháng 5 năm 2026`.
- Date reading is currently working; date normalization was not treated as the cause.

## Pipeline audit

```text
Text: backend/app/tts/text.py preprocess_text -> split_into_sentences -> chunk_sentences
Outer chunking: previously 400 chars; now 240 chars, below the known ~256-char VieNeu internal limit
VieNeu chunking: engine calls ModelLoader.infer once per outer chunk; a 240-char outer limit avoids the known two-level 400/256 interaction for normal text
Output processing: generated arrays are validated; no generated-audio silence trim or denoise occurs after inference
Concatenation: backend/app/tts/audio.py join_audios; now preservation + measured optional gaps
Speed: backend/app/tts/audio.py resample_audio runs only when speed != 1.0 and remains a linear resampler (therefore baseline is 1.0)
Final WAV: soundfile writes a validated non-empty PCM_16 WAV at model sample rate
```

## Root causes found

1. Every generated chunk previously received a 10 ms fade-in and fade-out before concatenation. That attenuated the first and last speech samples of every chunk, including the first and final chunks. This was a direct structural risk for weak phonemes and clipped endings.
2. The 400-character outer chunk target could cause a second, hidden VieNeu split around its known ~256-character limit. This made boundary placement less observable and could undermine pacing.
3. Chunks were previously concatenated with no gap. There was no mechanism to avoid a rushed boundary when the model returned no natural edge silence.

## Fixes made

- Removed output fades/trims entirely; reference preprocessing was not changed.
- Set the engine outer chunk default to 240 characters and kept hard fallback strictly token/whitespace based. A token is never cut; a token longer than the limit is retained intact.
- Prefer comma/semicolon/colon boundaries before ordinary whitespace when a long sentence must split.
- Added conservative punctuation-aware pause targets (45 ms plain boundary, 75 ms phrase mark, 130 ms sentence end), but only insert the deficit after measuring trailing/leading near-silence. Existing model pauses are not doubled.
- Validate non-empty mono/stereo generated chunks and compatible channel layouts before joining.
- Added opt-in engine diagnostics (`quality_diagnostics=True`) with chunk count, char count, ending punctuation, duration, peak, RMS, edge-silence metrics, inserted gaps, and final metrics. It contains no speaker embedding, codes, or source text.

## Chunking

`chunk_sentences()` preserves punctuation and never splits a word, number/date token, abbreviation token, or emotion token internally. Paragraph/newline preprocessing remains conservative. The Phase 20 quality corpus includes a long sentence and multi-sentence paragraph that cross outer chunk boundaries.

## Audio edge handling

Generated output has no silence trimming, denoise, fade-in, or fade-out after model inference. Only insertion of zero-valued inter-chunk gap samples is permitted; the first and last samples of real generated chunks remain present. The final WAV writer rejects empty output and preserves the engine sample rate.

## Pause/concatenation

The join is ordered `chunk 1 -> optional measured gap -> chunk 2 ...`; it neither overlaps nor deletes samples. Gap insertion is intentionally conservative and depends on measured existing edge silence rather than an unconditional delay.

## Saved voice consistency

The engine encodes a supplied reference once, constructs one `{speaker_emb, codes}` profile, and passes that same profile to every generated chunk. The existing saved-voice profile path remains unchanged and is covered by multi-chunk regression.

## Sampling experiment readiness

Voice Lab keeps `speed=1.0`, `top_k=25`, `top_p=0.95`, and `repetition_penalty=1.2` for the Temperature round. Round 2 now sends the selected 0.7, 0.8, or 0.9 value rather than displaying controls that were ignored. No temperature is claimed to be better.

## Quality test corpus

Created `data/voice_lab/quality_corpus.json`, centrally defining five neutral cases:

- short normal sentence;
- repeated `tháng 5 năm 2026` construction;
- numeric/date sentence;
- 150–250-character long sentence;
- multi-sentence paragraph for boundaries and final-chunk listening.

Voice Lab loads this separate quality corpus while retaining the existing rubric. Users can persist a `Có mất/nuốt chữ` flag and an optional affected-word note with each evaluation.

## Files created

- `data/voice_lab/quality_corpus.json`
- `tests/test_phase20_voice_quality.py`
- `diagnostics/phase20_voice_quality_report.md`

## Files modified

- `backend/app/tts/text.py`
- `backend/app/tts/audio.py`
- `backend/app/tts/engine.py`
- `backend/app/voice_lab.py`
- `backend/main.py`
- `frontend/app.js`
- `frontend/index.html`
- `tests/test_voice_lab.py`
- `tests/test_frontend_runtime_hotfix.py`

## Tests

```text
PYTHONPATH=. .venv/bin/pytest -q tests/test_phase20_voice_quality.py tests/test_engine_reference.py tests/test_voice_lab.py tests/test_frontend_runtime_hotfix.py tests/test_multiformat_saved_voice.py
41 passed

node --check frontend/app.js: PASS
python -m py_compile selected backend modules: PASS
git diff --check: PASS
```

Coverage includes safe punctuation/word boundaries, first/last sample preservation, ordered gap insertion, final chunk inclusion, final WAV sample rate, multi-chunk `{speaker_emb, codes}` reuse, quality corpus persistence, missing-word flag persistence, Voice Lab temperature wiring, history persistence contracts, and WAV/MP3/M4A save contracts.

## Real inference performed

0. No real model inference or benchmark was run. This phase makes structural/audio-metric claims only, not subjective quality claims.

## Regression

No IndexedDB/history code was changed. Save Voice and clone reference enrollment remain WAV/MP3/M4A. `/api/health`, `/api/voices`, `/api/tts`, `/api/tts/clone`, `/api/tts/upload`, CORS, runtime metadata, sampling validation, and single-inference concurrency were retained. No dependency, model, reset, restore, commit, or push change was made.

## USER MUST TEST

1. Restart the backend and hard reload `http://localhost:5173`.
2. Select the saved voice/reference and choose the quality paragraph. Generate Run 1 then Run 2 at **speed 1.0** and **temperature 0.8**.
3. Listen specifically for missing/quiet words, rushed pacing, first-word loss, and end-of-sentence clipping. Mark `Có mất/nuốt chữ` and name the affected word if present.
4. If both runs are structurally clean, compare one sentence at temperature **0.7**, **0.8**, and **0.9**, one sample at a time, keeping the other values fixed.

## Recommended next step

TEMPERATURE TUNING
