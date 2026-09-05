# PHASE 33 — SYNTHETIC BRAND SPEAKER R&D REPORT

## 1. Current speaker-space audit

Read-only audit of installed VieNeu V3 Turbo registry, local saved profiles and preserved
synthetic Podcast keepers found 33 stored records:

| Source | Records | Representation |
| --- | ---: | --- |
| VieNeu built-ins | 20 | float32 speaker embedding [192] + int64 reference codes [T,16] |
| Local saved profiles | 5 | same [192] + codes representation |
| Preserved synthetic keepers | 8 | same [192] + codes representation |
| Numerically unique embeddings | 30 | duplicate records removed only for counting |

Three saved records are byte-equivalent embeddings. The saved Podcast Beta embedding has
cosine similarity 1.0 with its canonical synthetic keeper, as expected because it is
provisioned from that keeper rather than newly encoded.

The aggregate geometry is separated: closest non-duplicate cosine similarity is 0.819044
and most distant is -0.025703. PCA first five components explain 19.69%, 9.81%, 6.96%,
6.68% and 5.60% of variance. This establishes that the 192-d representation contains
non-collapsed speaker anchors. It does **not** establish perceptual distance or validate
vector arithmetic. Private labels and blind mappings are not exposed.

## 2. Can VieNeu synthesize a new speaker?

**No supported mechanism exists in the installed V3 Turbo path.**

- Interpolation: architecturally possible only as raw numerical arithmetic, but the
  model has never exposed, trained or validated interpolation. Its x-vector is passed
  through a learned projection and LayerNorm then added to every token row; an
  intermediate vector is not guaranteed to correspond to a real or coherent speaker.
- Extrapolation/perturbation: even less justified. It can leave the training
  distribution and there is no decoder-side constraint that makes the result a valid
  person-like identity.
- Speaker-token creation: unavailable. Built-in names are records of precomputed
  embeddings/codes; `add_voice()` encodes a reference and saves it. It does not train
  a token, latent or adapter.

Therefore Path B, synthetic embedding interpolation, is rejected as the next PoC. It
would test undefined behaviour, not speaker design.

## 3. Reference-code dependency

A VieNeu voice comprises both a global 192-d `speaker_emb` and time-varying MOSS
`codes [T,16]`. The embedding is a persistent anchor; codes are inserted into the
prompt as acoustic context. Codes cannot be interpreted as identity-only: the installed
source does not disentangle speaker, prosody, source content and recording artefacts.

A novel embedding without matching codes can technically run with
`use_ref_codes=False`, but that deliberately removes the fidelity context. It is not
evidence that an arbitrary embedding is usable. Conversely, pairing one person's
embedding with another source's codes is unsupported. VieNeu requires a coherent,
paired reference for reliable cloning.

## 4. Existing-speaker casting opportunity

The 20 packaged records are explicitly Vietnamese-oriented built-ins (regional and
gender metadata) and use the same native representation. The eight preserved synthetic
keepers are more relevant: they were created earlier from Qwen VoiceDesign descriptions,
then encoded by VieNeu and used for Vietnamese samples. This demonstrates a pre-existing
cross-model route, but not a proven brand identity.

No built-in or keeper is promoted. A future blind cast must test identity stability over
unrelated Vietnamese passages, not choose a “nicest” sample. The prior Podcast Beta is
only one synthetic keeper and Phase 31/31B already showed its current delivery still
feels too generic.

## 5. Voice-design model research

| Model / path | Design new identity from text | Reusable identity | Vietnamese | Production CPU path | Licence / concern | Result |
| --- | --- | --- | --- | --- | --- | --- |
| Qwen3-TTS 1.7B VoiceDesign | Yes | Generated audio is reusable as a reference; no documented designed-speaker token | Official list excludes Vietnamese | No validated CPU long-form path | Apache-2.0 code; review weights/output terms | Best current design source for a small GPU cast |
| Existing Qwen VoiceDesign → VieNeu | Yes, already used in Phase 30 assets | VieNeu stores the resulting paired profile | Yes through VieNeu | Yes, VieNeu ONNX | Cross-model identity/artifact risk | Most evidence-backed current route |
| Gwen-TTS 0.6B | No reviewed text-to-voice-design API; clone only | Reference prompt / built-in speakers | Vietnamese-primary | CUDA path documented; CPU/ONNX not validated | MIT claim but TikTok-crawled training provenance requires review | Strong Vietnamese clone PoC later, not a speaker-design engine |
| IndexTTS2 Vietnamese community adaptation | No reviewed voice-design primitive | Clone / emotion conditioning | Community claim | Heavy PyTorch; CPU practicality unproven | Bilibili licence and community-maintenance risk | Adaptation research, not initial cast |
| VoxCPM2 | Claims voice design, controllable cloning and LoRA | Claims reusable model/conditioning workflows | Multilingual claim; Vietnamese not independently validated here | 2B, GPU first; no credible CPU production route yet | Must review model terms/weights | Watchlist, not first PoC |
| CosyVoice 3 / F5-TTS | Not Vietnamese-first design route | Clone / training mechanisms | Official language support excludes Vietnamese or is community-only | GPU-oriented | Weight/licence barriers; F5 base CC-BY-NC | Reject |

Qwen officially documents VoiceDesign, but its listed languages exclude Vietnamese.
The design can nevertheless make a short supported-language source voice; VieNeu may
then condition on its waveform to speak Vietnamese. This is technically plausible,
and has already been exercised by existing Phase 30 keepers. It is a hypothesis about
identity transfer, not proof that Qwen’s designed identity will survive Vietnamese
cloning.

## 6. Qwen3-TTS VoiceDesign findings

Qwen VoiceDesign accepts natural-language description and generates speech directly;
it does not provide a documented persistent “designed speaker token” comparable to a
custom voice registry. Its reusable object is therefore the generated audio. Qwen’s
Base clone workflow can save a reusable voice prompt from reference audio, but that is
a separate cloning capability, not a persistent VoiceDesign identity API.

For the target prompt (“Vietnamese male, warm-dark, intimate, slightly textured,
restrained”), Qwen can express the **speaker description**, but official Vietnamese
synthesis is unsupported. A supported-language source sample can establish timbre and
vocal character, then become an approved synthetic asset for VieNeu. The existing
Phase 30 Qwen → VieNeu workflow is the only local evidence that this bridge can
produce Vietnamese output at all.

Consistency must be tested, not assumed: generate several designed samples, lock a
single clean approved source, encode it once in VieNeu, then run the identity-grouping
test. Re-generating from the same prompt is not a safe identity-preservation method.

## 7. Vietnamese-first alternatives

Gwen-TTS is Vietnamese-primary and supports few-second zero-shot reference cloning, so
it is a credible **future Vietnamese quality comparator**. Its reviewed documentation
does not expose voice design, speaker adaptation, a synthetic-reference study,
fine-tuning recipe, quantized runtime, or ONNX CPU route. It cannot replace Qwen as
the initial synthetic-speaker caster.

The remaining Vietnamese candidates are retained only where they add a distinct
capability: IndexTTS community fine-tuning for later adaptation, and VoxCPM2 as a
watchlist design/LoRA model pending direct Vietnamese and licence evidence. None has
enough verified evidence to supersede the existing Qwen → VieNeu route now.

## 8. Cross-model synthetic-reference feasibility

```
VoiceDesign source clip → consent/licence + QC → locked Brand Speaker asset
                         → VieNeu encodes embedding + codes
                         → local Vietnamese ONNX production inference
```

This is technically plausible and already partially demonstrated by the preserved
synthetic keepers. It has serious failure modes:

- designed timbre can weaken or shift when VieNeu re-synthesizes Vietnamese;
- source language/accent/prosody may contaminate Vietnamese delivery;
- synthetic noise, breath effects or codec artefacts can be re-cloned;
- a generated prompt alone does not establish ownership, model-weight rights or
  commercial permission;
- second-generation dataset training can amplify pronunciation and identity errors.

Use only a locked, dry, clean, non-imitative synthetic source. Do not claim any output
is unique; recognizability needs listener evidence.

## 9. Synthetic speaker dataset / adaptation feasibility

A dedicated checkpoint is technically a **Level 3** route, not the next action:

1. cast and lock one speaker after blind identity tests;
2. generate or commission a controlled dataset, then manually reject drift/artifacts;
3. use text-accurate, diverse Vietnamese utterances;
4. fine-tune/adapt a model with a documented training path;
5. evaluate against the locked identity before considering local deployment.

A minimal research corpus is likely tens of minutes; a more robust single-speaker
adaptation usually needs multiple clean hours. Synthetic-on-synthetic data carries
teacher-error and mode-collapse risk, so it should mix only approved, diverse,
human-QC’d source material and never be assumed scientifically equivalent to natural
speaker data. This route needs a temporary GPU and a model with verified training and
commercial rights. It is premature until a cast identity passes recognition testing.

## 10. Four Brand Speaker concepts

| Concept | Speaker character | Signature cue | Why not generic AI narration |
| --- | --- | --- | --- |
| Ember | Low-mid warm timbre, dense but not bass-heavy resonance, medium vocal weight, soft grain | Ends settle downward with a warm final consonant | Has a contained, close physical presence instead of broadcast polish |
| Slate | Dry close-mic timbre, medium-low pitch, lean vocal weight, lightly textured onset | Crisp consonants arrive before a relaxed vowel body | Deliberately dry and intelligent rather than smooth audiobook gloss |
| Lantern | Warm-clear upper mids, moderate weight, smooth texture, conversational pitch | Brief friendly lift on an invitation then immediate grounded landing | Recognizable openness without sales energy or news cadence |
| Harbor | Dark-neutral resonance, quiet heavy core, restrained dynamics, rounded articulation | A small held beat before an important noun, then an unforced finish | Narrative gravity without movie-trailer bass or theatrical acting |

These are timbre/weight/articulation identities, not pause presets. Any actual cast
prompt must forbid imitation of a real person and must be evaluated blind.

## 11. Recognizability evaluation protocol

Use 4–5 candidates × 3 unrelated Vietnamese passages = 12–15 randomized clips.

1. **Identity grouping:** listeners group clips they believe are the same speaker.
2. **Recognition:** after a reference clip, identify the same speaker among new clips.
3. **Distinctiveness:** 1–5 scales for generic↔distinctive, forgettable↔memorable,
   artificial↔believable, inconsistent↔stable.
4. **Quality after identity:** pronunciation, naturalness, fatigue and artifacts.

Pass condition: grouping and recognition materially above chance across passages, with
no severe Vietnamese or fatigue failure. A high quality score alone does not pass.

## 12. Decision matrix

Scores: 1 = poor/high risk, 5 = strong/low risk.

| Path | Distinctiveness | Vietnamese | Stability | R&D ease | CPU production | Ownership/control | Licence risk | Decision |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| A. VieNeu existing-speaker casting | 2 | 5 | 4 | 5 | 5 | 1 | 3 | Useful baseline only |
| B. VieNeu embedding synthesis | 1 | 2 | 1 | 2 | 5 | 2 | 3 | Reject: unsupported |
| C. VoiceDesign → synthetic reference → VieNeu | 4 | 3 | 3 | 4 | 5 | 3 | 3 | **Best next evidence path** |
| D. Vietnamese-first alternative model | 3 | 4 | 3 | 2 | 1 | 3 | 2 | Follow only if C fails |
| E. Synthetic speaker → dataset → dedicated adaptation | 5 | 4 | 5 | 1 | 2 | 4 | 2 | Long-term route after a cast passes |

## 13. Recommended ONE next PoC

**Synthetic speaker identity-casting PoC using four existing Qwen-designed keepers,
then VieNeu Vietnamese rendering.**

It is the highest-information experiment because it tests the actual desired chain
without downloads, user recording, training, vector manipulation, or production
change. After approval, use four existing synthetic assets (one per concept where
possible), render exactly three unrelated Vietnamese passages each, blind filenames,
and run the protocol above. This is finite (12 clips), not bulk dataset generation.

If no candidate groups/recognizes above chance, declare the Qwen → VieNeu bridge
insufficient for distinctive identity and move to a GPU Gwen/alternative-model
comparison—not another VieNeu parameter sweep.

## 14. Expected cost / compute

Phase 33 itself used only local read-only NumPy analysis. The recommended PoC needs
the existing VieNeu CPU ONNX path and a small finite render set; no GPU, download or
cloud cost. A later *new* Qwen VoiceDesign cast would need temporary GPU capacity
appropriate for a 1.7B model; it is R&D compute, not a production dependency.
Final candidate production remains conditional on successful local VieNeu CPU
inference.

## 15. Risks and failure criteria

Stop the current path if any of these occurs:

- listeners cannot group identities across passages above chance;
- identity changes materially across text;
- Vietnamese has repeated pronunciation/accent defects;
- output is distinctive only because it sounds artificial, raspy or tiring;
- required model/data terms do not permit intended use;
- the source resembles a real person or lacks a clear provenance record.

Failure means evidence of a bridge/model ceiling, not a reason to micro-tune sampling.

## 16. Files changed

- `experiments/podcast_voice_phase33/analyze_speaker_space.py`
- `experiments/podcast_voice_phase33/speaker_space_metrics.json` (local ignored output)
- `experiments/podcast_voice_phase33/.gitignore`
- `experiments/podcast_voice_phase33/PHASE33_REPORT.md`

## 17. Production status

**The user's recorded voice is NOT part of the Brand Voice strategy.**

**No production voice was changed.** No new audio was generated, no heavy model was
downloaded, no training ran, and no Podcast, Review Film, UI or API contract changed.

Sources: [installed VieNeu inference source](../../.venv/lib/python3.14/site-packages/vieneu/_v3_turbo_engine/inference_v3_turbo.py), [Qwen3-TTS](https://github.com/QwenLM/Qwen3-TTS/blob/main/README.md), [Qwen reusable clone-prompt demo](https://github.com/QwenLM/Qwen3-TTS/blob/main/qwen_tts/cli/demo.py), [Gwen-TTS](https://github.com/ggroup-ai-lab/gwen-tts), [IndexTTS Vietnamese toolkit](https://github.com/iamdinhthuan/index-tts-finetune-vietnamese), [VoxCPM2](https://github.com/xlf-x/VoxCPM2).

`WAITING FOR USER APPROVAL OF SYNTHETIC BRAND SPEAKER POC`

