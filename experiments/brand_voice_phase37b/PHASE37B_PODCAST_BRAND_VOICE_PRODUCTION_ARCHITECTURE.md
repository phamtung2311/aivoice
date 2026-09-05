# Phase 37B — Podcast Brand Voice production architecture search

Audit date: 2026-09-02.  This is an architecture/provenance search only.  No
repository was cloned, no package or model was installed/downloaded, no audio
was generated, and production was not changed.

## Recommendation

**Choose Route B:**

```text
VoxCPM2 voice design (one-time GPU research)
  → Candidate 04, a synthetic Vietnamese podcast speaker
  → curated synthetic Vietnamese Brand Voice corpus
  → one-speaker Vietnamese VITS/Piper-class adaptation
  → frozen local ONNX podcast model + versioned speaker assets
```

This separates two jobs that have repeatedly conflicted in earlier phases:

1. a heavy model creates a distinctive, native-Vietnamese synthetic person;
2. a small single-speaker model renders that one person locally for every
   episode.

`openbmb/VoxCPM2` is the only candidate found here that clears the hard legal,
Vietnamese, synthetic-design and corpus-creation gates at once.  It is **not**
the final CPU renderer: official requirements are CUDA >=12.  Its value is the
one-time identity/corpus stage.  The final small renderer remains a separate,
locally runnable, frozen asset.

## Hard-filtered candidates

| Candidate / role | Explicit Vietnamese evidence | Synthetic identity without user voice | Code + weights / output terms | Local production route | Result |
| --- | --- | --- | --- | --- | --- |
| **VoxCPM2 — one-time designer/corpus renderer** | Official card lists Vietnamese among 30 languages; no language tag required. | Native text-described Voice Design; cloning/control also available. | Apache-2.0 code and weights; official card says commercial use allowed. No separate output prohibition found, subject to ordinary lawful-use/safety review. | No CPU final path promised; a corpus can be used to train a smaller local model. | **PASS — serious candidate.** |
| **Piper/VITS-class one-speaker model — final local renderer** | Official Piper catalogue includes `vi_VN`; its training path uses espeak-ng phonemization. | The new persistent identity would be the trained checkpoint, not a human prompt. | Piper code is GPL-3.0 (commercial use is possible, with copyleft distribution obligations); a new checkpoint's provenance must be entirely the project's synthetic corpus. | Native ONNX/C++ local CPU inference. | **PASS as the production-family route, not yet a selected base checkpoint.** |
| `NguyenAn05/regional-vi-vits-finetune` | Card declares Vietnamese character-based VITS and 3 speakers. | No native synthetic designer; would need adaptation. | The card says MIT, but its underlying corpus and modified Coqui stack provenance are insufficiently auditable for this channel. | CPU possible in principle but no verified deployed ONNX path. | **REJECT — provenance/implementation risk.** |
| `zalopay/vietnamese-tts` (F5-TTS) | Explicit Vietnamese, CC-BY-4.0 card. | Reference clone only; no persistent synthetic speaker asset. | Training data is described only as public Vietnamese voice + YouTube; permission/output provenance for a monetized Brand Voice is not demonstrated. | GPU-oriented; no established CPU production route. | **REJECT — provenance and local-production gate fail.** |
| `dangvansam/viet-tts` | Explicit Vietnamese clone toolkit. | Clone interface exists. | Source Apache-2.0, but upstream explicitly says pretrained models and samples are CC-BY-NC. | GPU-oriented. | **REJECT — non-commercial weights.** |
| Kani Vietnamese variants | Vietnamese finetune exists. | Adaptation may exist. | Current chain is connected to the already closed VieNeu branch; source/model provenance and CPU route are not sufficient here. | Not a cleared CPU path. | **REJECT — closed branch / insufficient new evidence.** |
| StyleTTS2 Vietnamese variants | No single official, commercially audited Vietnamese base found. | Trainable architecture, but not a cleared native Vietnamese checkpoint. | Base/code terms alone do not establish the downstream Vietnamese model/data terms. | GPU training; final CPU path unverified. | **REJECT — fails hard pre-filter.** |
| MeloTTS | Official language set does not establish Vietnamese support. | Has speakers but not native Vietnamese evidence. | Licence is not the deciding issue. | — | **REJECT — Vietnamese gate fail.** |
| OmniVoice, Gwen, VietVoice, V-TTS/Valtec, VieNeu tuning | Closed by prior decisions or licence/quality evidence. | — | — | — | **NOT REOPENED.** |

Hard-fail candidates were not allowed to win via score averaging.

## 1. Why VoxCPM2 is the designer

The official sources are [OpenBMB/VoxCPM](https://github.com/OpenBMB/VoxCPM)
and [the `openbmb/VoxCPM2` model card](https://huggingface.co/openbmb/VoxCPM2).
The card explicitly documents Vietnamese, 2B parameters, text-only Voice
Design, reference cloning, an optional reference-transcript continuation mode,
48 kHz output, and Apache-2.0 commercial use.  Its clone source distinguishes
isolated `reference_wav_path` from the transcript-paired continuation prompt,
which is useful for avoiding accidental reference-text continuation.

For this project, use **Voice Design first**, not Candidate 03 clone.  A future
Candidate 04 design brief can express the desired narrator directly:

> mature Vietnamese male, medium-low register, warm dark resonance, calm
> authority, restrained natural texture, neutral national pronunciation,
> unhurried podcast narration, no announcer exaggeration

This is only a design direction, not a claim that the first output will pass.
The identity becomes real only if listening validates it, then it is frozen as
the corpus source.  Candidate 03 remains an archived comparison asset and is
not part of this route unless a later approved A/B comparison needs it.

### VoxCPM2 resource and licence facts before any download

| Item | Verified value |
| --- | --- |
| Official model repo / revision inspected | `openbmb/VoxCPM2` at `32279effe8c19989596f05d353d1447f51d9e915` |
| Model licence | Apache-2.0 (card metadata and card text) |
| Official code licence | Apache-2.0 |
| Primary generator weight | `model.safetensors`, 4,580,080,592 bytes, SHA-256 `f7f964cfa9da23653baec6e6f7750719977ad944ed9f95fe52fe3a620506891d` |
| AudioVAE | `audiovae.pth`, 376,951,122 bytes, SHA-256 `94b5d51e107e0507d4acc976cfdadb64edd6fd06d1f751dadbf2fd1594274bf1` |
| Tokenizer / configs | `tokenizer.json` 3,676,772 bytes plus small `config.json`, custom tokenizer module and token configs |
| Minimum model snapshot | about **4.96 GB decimal** / 4.62 GiB |
| Official runtime requirement | Python >=3.10, PyTorch >=2.5, **CUDA >=12.0** |
| Official output | 48 kHz (the short code sample may write at model sample rate; do not hard-code 16 kHz) |

The raw BF16 weight and AudioVAE alone are about 5 GB.  OpenBMB does not publish
a minimum VRAM or RAM figure.  Plan a **24 GB CUDA GPU** for the one-time
research stage as the cautious target; 16 GB may work but is not guaranteed,
and this must be verified before downloading.  This workstation's Iris Xe and
16 GB system RAM do not satisfy the documented CUDA route.  CPU inference is
not a viable final-production assumption for VoxCPM2.

Expected one-time research footprint: roughly 5 GB weights + a separate
environment/cache, so reserve 10–15 GB disk.  If a paid GPU is needed, budget
only for design/audition and later corpus creation/training—not episode
rendering.  No recurring paid/cloud inference belongs in the final system.

## 2. The frozen Brand Voice asset, not a fragile 7-second prompt

After a Candidate 04 passes listening, create an auditable project-owned
synthetic corpus; never mix human recordings and never overwrite its sources.

```text
BRAND_VOICE_PODCAST/
  identity_description.txt
  identity_manifest.json
  references/
    neutral_01.wav
    reflective_01.wav
    authority_01.wav
    conversational_01.wav
  transcripts/
  vietnamese_corpus/
    audio/
    manifest.jsonl
    qa/
  speaker_assets/
    candidate04_design.json
    seed_and_renderer_revision.json
    training_recipe.lock
    frozen_model.onnx
    frozen_model.onnx.json
```

`identity_manifest.json` records the design description, renderer/model
revision, seed where supported, exact text, licence evidence, waveform hash,
duration, transcript, QA decision and parent source for every file.  It makes
the voice portable to later engines without pretending a single embedding is
universal.

### Corpus size and composition

The user-proposed 30 s -> 2 min ladder is useful for identity audition and
pipeline validation, but **not enough to promise a robust podcast model**.
Use it in stages:

| Stage | Synthetic material | Purpose |
| --- | ---: | --- |
| Identity seed | 20–60 s, 4 styles | Confirm Candidate 04 is one person across normal/reflective/authoritative/conversational delivery. |
| Pilot corpus | 5–10 min, 3–12 s natural utterances | Validate Vietnamese text normalization, audio QA, transcript alignment and a first adaptation. |
| Podcast corpus | 20–60 min, sentence groups / short paragraphs | Minimum realistic target for a durable one-speaker podcast model; include natural punctuation, tones, dates/numbers only after a dedicated normalization plan, and topic/register variation. |

This is an engineering estimate, not an upstream guarantee.  More clean,
consistent, correctly transcribed synthetic material is preferable to a larger
but artifact-contaminated corpus.  Every generated corpus clip must pass human
listening and automated QA before it becomes training data; do not distill
mispronunciations or long-pause artifacts into the permanent model.

## 3. Final Vietnamese-local renderer: VITS/Piper-class checkpoint

Piper's official implementation supplies a local C/C++ runtime, ONNX voice
format and a documented training path.  It supports Vietnamese in its voice
catalogue; the training documentation accepts transcripted audio and uses
espeak-ng phonemization.  This makes a single-speaker VITS/Piper-class model
the right **production target**: a trained checkpoint is the permanent speaker
asset, runs locally, and needs no recurring clone prompt or cloud service.

Important legal implementation detail: current `OHF-Voice/piper1-gpl` is
GPL-3.0.  GPL permits commercial use, but distributing a derivative integration
can trigger copyleft/source obligations.  Before adopting its executable inside
the AIVoice product, perform a focused licence/packaging audit and keep the
runtime boundary explicit.  The corpus and trained weights must originate only
from this project’s Apache-cleared synthetic pipeline; do not inherit any
unclear Vietnamese voice/data checkpoint.

Training feasibility:

- Training/adaptation needs a temporary CUDA GPU; the i9/Iris Xe machine is
  reserved for final ONNX inference and QA, not model training.
- A pilot can test a small adaptation with 5–10 minutes.  It is not evidence
  that the voice is ready for multi-hour narration.
- Full fine-tuning versus a lightweight adapter must be chosen after the
  training-base audit.  A one-speaker VITS checkpoint is simpler and more
  portable than a permanent zero-shot clone stack; a LoRA/adapter is useful
  only if the chosen base makes export/merge and commercial provenance clear.
- The expected final inference model is far smaller than VoxCPM2 and has an
  ONNX CPU route.  Actual RTF, quality and paragraph continuity are acceptance
  tests; no unmeasured speed claim is made.

## 4. Podcast-specific risk controls

| Need | Architecture response |
| --- | --- |
| One recognizable person | Freeze a selected Candidate 04, all curated corpus clips and the resulting one-speaker checkpoint. |
| Comfortable long-form flow | Train on coherent 3–12 s utterances and some short paragraphs; render natural sentence groups, never arbitrary comma splits.  Do a dedicated long-form audition before production. |
| Authority without radio acting | Include neutral, reflective and firm-but-calm material; reject exaggerated or regional deliveries at corpus QA. |
| Vietnamese tones and punctuation | Keep Unicode text intact; establish deterministic Vietnamese normalization before corpus generation, then use exactly the same front end at production. |
| Speaker drift | One frozen model/ONNX configuration and versioned corpus; do not regenerate a new voice per episode. |
| Future migration | Preserve WAVs, exact transcripts, configuration, hashes and manifest rather than only one binary embedding. |

## 5. Decision matrix

Scores are architecture fit, not proof of audio quality.  A hard licence or
Vietnamese failure remains a rejection irrespective of score.

| Architecture | VI quality | podcast flow | identity stability | distinctive creation | trainability | CPU production | commercial licence | portability | implementation risk |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| **VoxCPM2 -> curated corpus -> VITS/Piper class** | 4 | 4 | 5 after adaptation | 5 | 4 | 5 | 5 | 5 | 3 |
| VoxCPM2 only | 4 | 4 | 3 via prompt/reference | 5 | 4 | 1 | 5 | 3 | 3 |
| Direct Piper existing VI voice | 3 | 2 | 2 | 1 | 3 | 5 | 3 | 3 | 2 |
| Regional Vietnamese VITS finetune | 3 | 3 | 3 | 1 | 3 | 4 | hard fail | 3 | 4 |
| Zalo F5 clone | 4 | 3 | 2 | 1 | 2 | 1 | hard fail | 2 | 4 |

## Exactly one next experiment — proposal only

**Phase 37C proposal: one VoxCPM2 GPU Candidate 04 Voice-Design audition.**

This is one coherent, short Vietnamese narration generated from a fixed
podcast-oriented design description and a recorded seed/revision.  It does not
clone Candidate 03, uses no user audio, does not create a corpus, does not tune
parameters and does not modify production.

It maximizes information because it answers the first irreversible question:
can the only legally cleared synthetic designer produce a Vietnamese narrator
with enough character, correct pronunciation and unbroken short-form flow to
justify corpus work?

Acceptance requires all six gates:

1. correct Vietnamese pronunciation;
2. natural single-utterance continuity;
3. one credible synthetic person;
4. calm authority/warmth rather than announcer acting;
5. no obvious robotic stop-start behavior; and
6. enough distinctiveness for a podcast identity.

If it fails, do not generate a corpus and do not train a small model.  If it
passes, the next separately approved phase is corpus design and QA, not
production integration.

Expected prerequisite for that future one-output audition: one temporary CUDA
12+ machine, preferably 24 GB VRAM, about 5 GB model download and 10–15 GB
available disk.  Time/cost are provider-dependent; this audit does not commit
to a paid provider or cloud account.

## Stop point

No dependency, code checkout, model download, audio generation, Candidate 04
creation or production modification was performed.  Candidate 03 remains
preserved.  **STOP before any install/download.**
