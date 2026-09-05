# Phase 29A — Special Voice Pack Architecture & Review Film Voice R&D

## Status

**PARTIAL.** The audit and isolated controlled R&D package are complete. The central listening experiment is intentionally not run because no permissioned Review Film reference was supplied and Phase 29A does not authorize producing test audio. Source evidence makes the approach technically credible, but it cannot establish convincing Review Film quality without blind listening.

## Production safety

No backend, frontend, API, model, saved-voice storage, Voice Lab, Audio Studio, NLP, sampling default, or production dependency was changed. The only repository-level configuration change is `.gitignore` entries for locally generated Review Film experiment outputs, references, and measurements.

## Actual current voice architecture

```text
frontend/app.js
  → POST /api/tts in backend/main.py (TTSRequest)
  → optional backend.app.tts.nlp.normalize_text()
  → TTSEngine.generate() in backend/app/tts/engine.py
  → preprocess_text() / split_into_sentences() / chunk_sentences()
  → ModelLoader.infer() in backend/app/tts/model.py
  → Vieneu(mode v3turbo, backend onnx)
  → V3TurboVieNeuTTS.infer()
  → ONNX V3 Turbo acoustic decoding + MOSS codec
  → TTSEngine join_audios(), measured gap insertion, optional resample_audio(speed)
  → audio.save_wav() → temporary API WAV response
```

`backend/main.py` validates optional sampling values, serializes inference through `_TTS_SEMAPHORE`, and forwards only explicitly supplied settings. `TTSEngine` uses a 240-character outer chunk boundary. The V3 Turbo layer then has its own natural text normalization/chunking (default maximum 256 characters).

Preset and saved voices are native VieNeu profile dictionaries containing `speaker_emb` and `codes`. `ModelLoader` restores saved profiles from `data/voices/voices.json` through `voice_store.serialize_profile()` / `deserialize_profile()`. Reference audio is pre-cleaned/trimmed and prepared into the same two values; it is encoded once per `TTSEngine.generate()` call and reused for the call's chunks.

## VieNeu control surface

| Class | Verified controls |
| --- | --- |
| Native generation | `temperature` (default 0.8), `top_k` (25), `top_p` (0.95), `repetition_penalty` (1.2), repetition window, frame cap, reference speaker embedding/codes, denoise, and reference-code inclusion. Sampling uses NumPy RNG; the public V3 CPU path has no explicit seed parameter. |
| Text | Existing Vietnamese normalization, punctuation-aware sentence/chunk segmentation, automatic gap categories, and optional AIVoice Smart Text Processing before `/api/tts`. |
| Post-process | Existing insertion-only measured chunk gaps, WAV PCM-16 write, optional linear-resample speed change. |
| Unsupported | No supported independent pitch contour, energy, duration, prosody vector, semantic style instruction, or usable external emotion controller. `style` is accepted as metadata but V3 Turbo explicitly ignores it at inference and fixes the natural-style token. |

CPU V3Turbo is an ONNX Runtime route at 48 kHz, defaulting to int8 graphs. It is a GREEN local-first deployment base.

## Reference style transfer finding

Source code supports **PARTIAL architectural evidence** for reference-driven specialized style: voice conditioning consists of a 192-dimensional speaker embedding plus optional reference audio codes; V3 Turbo documentation states the natural delivery is implied by the reference voice. It does not expose an independently controllable style parameter.

Therefore a carefully performed Review Film reference may influence generated cadence/timbre, but this cannot be quantified from source alone. The deliberate Phase 29B comparison must test a neutral versus Review Film-style reference while holding script and settings fixed. It must check identity, naturalness, Review suitability, and robotic rhythm by human listeners.

## Review Film voice definition

The desired character is observable as: stable narrator identity; medium to medium-fast natural pace; phrase-level rather than word-by-word grouping; clear consonants; controlled falling/rising sentence endings; moderate energy; short naturally occurring dramatic pauses; intelligible names/numbers; restrained variation between setup, reveal, action, and reflective lines; no caricature cues.

Reference choice carries the primary character. The R&D candidates do not use global speed changes, pitch shifts, cue tags, automatic comma insertion, or text rewriting.

## Special voice profile design

A future special voice should be a small metadata layer over an existing native voice profile—not another TTS pipeline:

```text
SpecialVoiceProfile
  id / display name / category
  existing native speaker_emb + codes voice
  bounded native sampling overrides
  optional explicit text-processing selection
  safe existing chunk/pause policy
  reference-quality guidance and metadata
```

Do not change the native voice serialization. This pattern can later support Product Review, Meme/Breath identity, Sarcastic/Edgy Comedy, and Horror Story with a profile/reference/configuration rather than duplicated inference code. Smart Text Processing remains separate from “how it is spoken” and must never rewrite scripts silently.

## Experiment package

Created `experiments/special_voice_review/`:

- `README.md`
- `test_sentences.json` — 10 original Vietnamese sentences
- `experiment_config.json` — profile concept and four controlled candidates
- `runner.py` — isolated local renderer with measurements
- `reference_contract.md`
- `special_voice_profile_design.md`
- `evaluation.csv`

Generated `outputs/`, `reference_audio/`, and `measurements.json` are ignored by Git. No generated audio/reference/model is present.

## Candidate strategy

| Candidate | Difference from baseline | Purpose |
| --- | --- | --- |
| baseline | No explicit sampling overrides | Reproduce native production defaults |
| review_candidate_a | temp 0.72, top-p 0.92, repeat 1.24 | Test steadier narrator cadence |
| review_candidate_b | temp 0.86, top-k 30, top-p 0.96, repeat 1.18 | Test slightly more phrase variation |
| review_candidate_c | temp 0.78, top-p 0.94, repeat 1.28 | Test balanced variation / less repetition |

Every candidate keeps `speed=1.0`, existing 240-character outer chunks, denoise, reference codes, and existing gap behavior. These are hypotheses only; none changes production defaults.

## Reference recording contract

For current V3 ONNX cloning, use clean mono WAV with about 6–8 seconds usable speech (the current clone pipeline caps at 8 seconds). Record one stable narrator/reviewer with medium pace, clear consonants, moderate energy, two or three complete phrases, a controlled ending, minimal edge silence, no music/noise/reverb/clipping, and permission to use the voice.

Reference Quality DSP can warn about duration, noise, silence, peak/clipping and loudness. Background music/reverb detection remains a required human check; no heavyweight ML detector is added.

## Evaluation and performance method

Blind-listen to anonymized candidate folders and complete `evaluation.csv`. Scores are Naturalness, Review suitability, Clarity, Voice consistency (all 1–5), and Robotic rhythm (1 natural to 5 extremely robotic), with preferred sample, notes, and manual comparison to current VieNeu.

The runner records per-sentence wall time, process CPU time, Linux peak RSS, generated audio duration, RTF when duration is available, and existing generation diagnostics. A result that is slightly nicer but materially slower must be explicitly flagged.

## Regression tests

Before scaffolding, system `pytest` was unavailable outside `.venv`. A direct full-suite invocation through `.venv` did not complete within the 30-second local tool window because existing API test modules initialize the global VieNeu engine before mock dependency overrides. This is a test-environment limitation, not a reported test PASS.

After scaffolding:

- `.venv/bin/python -m py_compile experiments/special_voice_review/runner.py`: PASS.
- `PYTHONPATH=. .venv/bin/pytest -q tests/test_phase29_special_voice_review.py`: **3 passed**.
- Experiment JSON/static validation: PASS.
- `git diff --check`: PASS.

## Phase 28 status

**FROZEN and untouched.** `experiments/index_emotion_kaggle/` was not changed, executed, deleted, or integrated.

## Main research answer

**PARTIAL.** VieNeu can realistically be the local CPU engine for a specialized Vietnamese Review Film voice because reference identity/codes and bounded native sampling settings are available while normal inference stays ONNX/CPU. However, it lacks an explicit prosody/style controller, and source code alone cannot prove that a Review Film reference transfers enough delivery character or avoids robotic rhythm. The critical evidence remains a controlled blind listening test.

## Next recommendation

**Phase 29B — Generate and blind-test real Review Film voice candidates.**

Use a single permissioned Review Film-style reference, run baseline plus the three controlled candidates, collect the RTF/RSS records, and decide from blinded human listening. Do not start automatically.
