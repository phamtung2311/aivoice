# Phase 28A — Emotion & Expression Feasibility Research

## 1. Status

PARTIAL. The production path and installed engine were audited, a reproducible isolated experiment was added, and fourteen controlled local WAVs were generated. The engine has verified non-verbal inline cues, but a human listening review is still required before classifying any mechanism as emotionally useful or repeatable.

## 2. Current Engine Findings

The installed package is `vieneu 3.3.0`, using `V3TurboVieNeuTTS` with the local ONNX backend. Its actual `infer` signature exposes `temperature`, `top_k`, `top_p`, `repetition_penalty`, `repetition_window`, `max_new_frames`, `silence_p`, `crossfade_p`, `batch_size`, and reference voice inputs.

| Finding | Classification | Evidence / implication |
| --- | --- | --- |
| Inline `[cười]`, `[thở dài]`, `[hắng giọng]` cues | SUPPORTED AND EXPOSED IN TEXT | Installed `vieneu_utils.phonemize_text_with_emotions` converts them to `<|emotion_1|>`, `<|emotion_2|>`, and `<|emotion_3|>`. The experiment confirmed that conversion directly. |
| Arbitrary labels such as `[warm]`, `[happy]`, `[sad]` | NOT SUPPORTED | Unknown bracketed labels are not mapped to special tokens. |
| `style` argument | NOT SUPPORTED FOR CONTROL | The installed V3 Turbo source explicitly marks it deprecated and ignored; output remains natural style. |
| `temperature`, `top_k`, `top_p`, `repetition_penalty` | SUPPORTED AND EXPOSED | Current engine wrapper and `/api/tts` already forward these optional sampling controls. |
| `speed` | SUPPORTED AND EXPOSED | AIVoice applies a final deterministic resample after synthesis; it is tempo, not an emotion control. |
| `max_new_frames`, `repetition_window`, `silence_p`, `crossfade_p`, `batch_size` | SUPPORTED BUT NOT CURRENTLY USED | Exposed by native V3 Turbo but not forwarded by `TTSEngine.generate`; no production enabling was done. |
| `emotion_tag` keyword | POSSIBLY AVAILABLE / NEEDS EXPERIMENT | AIVoice wrapper can accept/forward it, but V3 Turbo `infer` receives arbitrary kwargs and does not use it in its sampling path. The clone endpoint only permits `natural`; it is not evidence for emotion control. |
| Pitch, energy, duration, style embedding manipulation, instruction prompt control | NOT SUPPORTED | No public V3 Turbo parameter was found for these controls. |

## 3. Production TTS Path

`frontend/app.js` posts text, selected voice, speed, and optional sampling values to `POST /api/tts` in `backend/main.py`. With Smart Text Processing enabled, `backend.app.tts.nlp.normalize_text` runs first. `TTSEngine.generate` in `backend/app/tts/engine.py` calls `preprocess_text`, then `split_into_sentences` and `chunk_sentences` (240-character outer chunks). For each chunk, `ModelLoader.infer` in `backend/app/tts/model.py` inspects the installed VieNeu signature and forwards supported sampling fields to V3 Turbo. Generated chunks are measured and joined in `backend/app/tts/audio.py`; only measured pause deficits are inserted, then speed is implemented by resampling and WAV is written.

Saved/cloned references enter `TTSEngine.generate` as `ref_audio`, are encoded once through native `encode_reference`, and are reused as a `speaker_emb`/`codes` voice profile for all chunks. No Phase 28A production path was changed.

Expression-relevant caveat: the outer AIVoice splitter preserves `.`, `!`, `?`, `…`, commas, and newlines; it canonicalizes `...` to `…`. The installed sea-g2p layer can normalize punctuation, including adding/changing a final mark in some short inputs. The experiment records both the wrapper input and outer chunks, while the installed native phonemizer is the final text-to-phoneme stage.

## 4. Experiment Added

- `experiments/emotion/run.py` — developer-only controlled WAV generator using the existing `TTSEngine`.
- `experiments/emotion/README.md` — repeatable run instructions.
- `experiments/emotion/.gitignore` — excludes generated WAVs, manifest, and listening index.

Each manifest record stores original/base text, transformed source text, Smart Text Processing result, exact wrapper input, exact outer chunks, parameters, selected voice, timestamp, output name, native wrapper diagnostics, and duration/RMS/peak/edge-silence metrics. It neither starts the API server nor changes user data/history.

## 5. Strategies Tested

| Strategy | Samples | Result |
| --- | --- | --- |
| Neutral baseline | `informational_neutral`, `thoughtful_neutral`, `sad_neutral`, `gentle_neutral` | UNKNOWN — HUMAN LISTENING REQUIRED |
| Punctuation: period/exclamation/question/ellipsis | thoughtful, happy, surprise pairs | UNKNOWN — HUMAN LISTENING REQUIRED; metrics differ in several pairs but do not establish emotional quality. |
| Pause/rhythm via native punctuation segmentation | `gentle_neutral`, `gentle_pause`, `thoughtful_split` | UNKNOWN — HUMAN LISTENING REQUIRED. |
| Sentence segmentation | `thoughtful_neutral`, `thoughtful_split` | UNKNOWN — HUMAN LISTENING REQUIRED. |
| Native non-verbal cue | `sad_neutral`, `sad_sigh` | MODERATE for *cue support*: `[thở dài]` is demonstrably converted to a native special token and sample duration rises 2.40 → 2.72 s. Emotional usefulness is UNKNOWN — HUMAN LISTENING REQUIRED. |
| Semantic context | `sad_neutral`, `context_serious` | UNKNOWN — HUMAN LISTENING REQUIRED; wording changes what is spoken, so this cannot prove a reusable style control. |
| Existing synthesis parameter | `happy_exclamation`, `happy_temperature_09` | UNKNOWN — HUMAN LISTENING REQUIRED. Temperature is a sampling control, not demonstrated emotion control. |

## 6. Generated Samples

All files are local developer artifacts under `experiments/emotion/output/`:

- `informational_neutral.wav`
- `thoughtful_neutral.wav`, `thoughtful_ellipsis.wav`, `thoughtful_split.wav`
- `happy_period.wav`, `happy_exclamation.wav`, `happy_temperature_09.wav`
- `sad_neutral.wav`, `sad_sigh.wav`
- `surprise_period.wav`, `surprise_question.wav`
- `gentle_neutral.wav`, `gentle_pause.wav`
- `context_serious.wav`

The exact record index is `experiments/emotion/output/LISTENING_INDEX.md`; complete metadata is `experiments/emotion/output/manifest.json`. These outputs are Git-ignored.

## 7. How I Should Listen/Test

From the repository root:

```bash
.venv/bin/python experiments/emotion/run.py
xdg-open experiments/emotion/output/LISTENING_INDEX.md
```

Listen in pairs: neutral → variant → neutral → variant. In particular, compare thoughtful neutral/ellipsis/split, happy period/exclamation/temperature, sad neutral/sigh, surprise period/question, and gentle neutral/pause. Judge pauses, terminal intonation, naturalness, and whether a cue sounds like the intended non-verbal event. Do not rate semantic-context samples as a style control unless the unchanged target portion clearly changes in a repeatable way.

## 8. Regression Results

- `experiments/emotion/run.py` compilation: PASS.
- Native cue-token probe: PASS for `[cười]`, `[thở dài]`, and `[hắng giọng]`.
- Targeted Phase 23–26 regression suite: PASS, `23 passed in 2.03s`.
- Full test suite collection: PASS, `154 tests collected in 2.03s`.
- Full suite execution could not complete in the current 30-second command-runner window; it reaches tests that exercise the real engine/API and needs to be run from a normal terminal for a final total. No failure attributable to Phase 28A was observed.
- Initial targeted run found three stale Audio Studio test assertions caused by the already-existing standalone-page migration (old cache-buster and old `index.html` location). Tests were updated only to target the current standalone page; production code was not changed.

## 9. Files Changed

Production files: none.

Experiment/developer files:

- `experiments/emotion/.gitignore`
- `experiments/emotion/README.md`
- `experiments/emotion/run.py`
- `diagnostics/phase28a_emotion_feasibility.md`
- `tests/test_phase25_audio_studio.py` (stale cache-buster assertion)
- `tests/test_phase26_release_candidate.py` (stale inline-Audio-Studio assertions)

## 10. Important Limitations

The current evidence does not prove broad controls such as warm, serious, thoughtful, happy, sad, gentle, confident, or storytelling. Punctuation and text changes can change duration or output, but metrics cannot establish emotional delivery. The only verified native expression mechanism is three discrete non-verbal cues; `style` is explicitly ignored by the installed V3 Turbo engine. There is no verified pitch, energy, duration, or style-embedding control. Saved reference audio may influence natural delivery but Phase 28A did not test or alter voice conditioning.

## 11. Recommendation for Phase 28B

B. Expose existing native model controls — narrowly and only after the listening review: treat the verified `[cười]`, `[thở dài]`, and `[hắng giọng]` cues as a separate non-verbal-cue capability, not a general emotion system. If listening confirms useful punctuation/pause effects, a later controlled text-level processor can be considered, but Phase 28A does not justify arbitrary emotion tags or a full Emotion UI.
