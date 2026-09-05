# Phase 37D — Zero-cost local Podcast Brand Voice architecture reset

## Executive decision

The only defensible zero-cost, local-only architecture to investigate next is:

```text
Qwen VoiceDesign CPU (identity designer, English reference only)
  -> frozen synthetic identity package
  -> VieNeu CPU/ONNX short Vietnamese source clips, individually human-QA'd
  -> one-speaker Vietnamese VITS/Piper-class model trained locally and resumably
  -> ONNX Runtime / Piper local CPU production renderer
```

This is a **research hypothesis**, not a promise of a good final voice.  A
single-speaker model can make a speaker identity persistent in its weights and
remove zero-shot reference dependence, but it cannot repair bad Vietnamese,
prosody, or artifacts already present in its synthetic training data.  The
first gate is therefore corpus-source quality, not model training.

No installation, download, synthesis, audio generation, training, GPU rental,
or production change occurred in this phase.

## 1. Phase 37C correction

VoxCPM2 is **BLOCKED — REQUIRED CUDA PATH DOES NOT SATISFY ZERO-COST LOCAL
HARDWARE CONSTRAINT.**  Phase 37C created only scripts and research records;
no rollback is needed.  They remain preserved at `../brand_voice_phase37c/` as
reference evidence and must not be installed, downloaded, run, or expanded
into a corpus.

The required machine is the i9-13900H / 16 GB RAM / Iris Xe Fedora laptop.
Local CPU execution is mandatory; slow but resumable work is permitted.

## 2. Existing local evidence (FACT)

### Qwen VoiceDesign

- Local checkpoint: `Qwen3-TTS-12Hz-1.7B-VoiceDesign`, 4.3 GiB on disk.
- Existing CPU runner: bfloat16 / eager attention.  It loaded in 1.27 s and
  reached 5.19 GB peak RSS in the Phase 30 Generation 2 run.
- Six 6.8–9.3 s designed English references took 300–595 s each (roughly
  44–78 RTF), so Qwen is acceptable only for occasional identity/reference
  work, not Vietnamese daily production.
- Candidate 03 is a frozen, portable reference package at
  `../brand_speaker_phase33c/baseline_anchor/BRAND_CANDIDATE_03_BASELINE/`.
  Its canonical `qwen_source.wav` is never modified.
- Fixed design text and a fixed seed help experiment control, but do **not**
  establish that independently generated Qwen references are a perfectly
  stable same speaker.  That remains an empirical identity-QA question.

Qwen's official card marks the 1.7B VoiceDesign weights Apache-2.0, but lists
ten major languages that do not include Vietnamese.  Its permitted role here
is therefore only **Synthetic Person Designer**, not Vietnamese podcast TTS.

### VieNeu as a short-corpus tool, not production narrator

Phase 30 measured short Candidate-style Vietnamese outputs on CPU at about
8.8–134 s generation time for 11.7–14.6 s audio, with 2.5–3.7 GB peak RSS.
Later listening evidence rejected its long-form continuity/prosody.  That does
not falsify a tightly QA'd 2–8 s corpus-source use, but it means every clip
must be individually accepted; no automatic bulk corpus is credible.

The currently installed VieNeu package is 3.3.0.  Its official v3 model card
declares CPU ONNX inference, Vietnamese support, Apache-2.0 assets, and
commercial use for generated audio from bundled voices.  A cloned Candidate 03
chain remains dependent on the separate Qwen-output rights audit below.

### Better CPU synthetic identity designer search

No smaller, locally CPU-proven, commercially cleared model found in this audit
materially improves the architecture over the already-local Qwen VoiceDesign
checkpoint. The recent stronger identity-design/zero-shot candidates audited
in Phases 36–37 either require CUDA, have insufficient Vietnamese/local CPU
evidence, are closed branches, or add a licensing/provenance uncertainty.
Qwen remains the designer by evidence, not an endorsement of its Vietnamese
production ability.

## 3. Licence and synthetic-data audit

| Asset/tool | Code | weights/assets | training-data provenance | output / synthetic-corpus use | classification |
| --- | --- | --- | --- | --- | --- |
| Qwen3-TTS VoiceDesign | Apache-2.0 (official repository) | Apache-2.0 official model card | not a dataset supplied by this project | No separate explicit output-ownership/corpus-training clause found in the card; source audio must be preserved with model/revision/prompt/seed provenance | **UNRESOLVED** for a monetizable derivative corpus; permissible experimental identity evidence only until terms are explicitly cleared |
| VieNeu v3 Turbo | Apache-2.0 | Card states all shipped artifacts Apache-2.0 | detailed training corpus not public | Card expressly permits commercial generated audio from bundled voices; cloning remains user responsibility | **CONDITIONALLY COMMERCIAL-SAFE** for a synthetic reference the project has rights to use; the chain inherits Qwen's unresolved point |
| Piper/VITS training tooling | Must pin and audit before install; published Piper-compatible implementations vary | No base is selected | use only the project's accepted synthetic corpus | a from-scratch model has no third-party voice/base-weight lineage, but code and phonemizer notices remain | **UNRESOLVED UNTIL PINNED**, potentially cleanest final model chain |
| Public Vietnamese pretrained checkpoints | varies per checkpoint | varies | frequently incomplete or restrictive provenance | cannot assume a fine-tuned checkpoint is commercial-safe | **NOT SELECTED** |

Apache-2.0 permits use of the software/weights; it does not itself settle every
copyright or downstream training-data question.  This is not legal advice.
Before monetization, retain a provenance manifest for every accepted clip and
obtain a written/official clarification for the Qwen-output-to-training-data
step if the card/repository has no explicit answer.

## 4. Vietnamese one-speaker training options

| Architecture | Vietnamese/frontend | identity form | CPU training / production | licence/provenance | decision |
| --- | --- | --- | --- | --- | --- |
| **Piper-compatible VITS, one speaker, from scratch** | Piper training accepts eSpeak-NG language phonemes; its voice catalogue includes `vi_VN`.  Vietnamese numbers/dates/abbreviations must be normalized in dataset text before phonemization. | Dedicated single-speaker checkpoint: identity lives in weights. | PyTorch training is technically CPU-capable but upstream examples strongly recommend GPU.  Export to ONNX and native local CPU inference are documented. | Tool/source must be pinned.  Do not inherit any public Vietnamese checkpoint or voice. | **BEST ZERO-COST ARCHITECTURE TO TEST** |
| Raw VITS | `espeak-ng` has Vietnamese voice support; a custom Vietnamese text normalizer is still required. | Dedicated checkpoint. | CPU technically possible; adversarial training is slow.  ONNX deployment exists in community work but Piper gives a clearer end-to-end path. | MIT original implementation, but no cleared Vietnamese base/data is selected. | **FALLBACK IMPLEMENTATION, not first choice** |
| Coqui VITS / VITS2 | Can train new languages and use eSpeak; no verified clean Vietnamese base is selected. | Dedicated checkpoint. | CPU package exists, but official repository says tested Python <3.12; current Fedora runtime is 3.14, adding compatibility risk. | Framework MPL-2.0; model/checkpoint terms separate. | **REJECT for first local PoC** |
| Matcha-TTS + vocoder | No verified native Vietnamese frontend/checkpoint in its official distribution. | Dedicated checkpoint possible. | Fast inference architecture, but training requires a separate acoustic/vocoder/data recipe; CPU final route not demonstrated here. | MIT code; weights/datasets separate. | **REJECT — more components, no Vietnamese gate** |
| FastSpeech2 / Glow-TTS + vocoder | Need a Vietnamese frontend, duration/aligner and vocoder choices. | Dedicated checkpoint possible. | CPU possible in theory but composition/training risk is higher than VITS/Piper. | No commercially audited Vietnamese base selected. | **REJECT — unnecessary integration risk** |

VITS/Piper is not selected because it is fashionable; it is selected because it
is the only serious route found here that combines a single-speaker checkpoint,
Vietnamese phoneme route, explicit dataset preprocessing, export to ONNX, and
local CPU production without an external inference service.

## 5. Dataset and corpus strategy

All future training data must be one synthetic identity, short, clean, and
traceable:

1. Prepare text before synthesis: Vietnamese numerals, dates, abbreviations,
   foreign terms and punctuation normalized into intended spoken form.
2. Generate only 2–8 s utterances using frozen Candidate 03 conditioning and
   an already-installed local VieNeu path.  Do not tune the renderer.
3. Human QA each clip: correct words and tones, one stable person, no stretched
   syllables, no abnormal pauses, no clipping, no obvious reference reset.
4. Keep WAV, exact transcript, source engine/version, reference hash,
   parameters, duration and human accept/reject rationale in a manifest.
5. Keep held-out text for evaluation; never train on it.

Coverage eventually includes introductions, explanations, reflection, firm
statements, short/medium sentence lengths, ordinary punctuation, tone/phoneme
coverage and common podcast vocabulary.  It deliberately excludes extreme
emotion and long paragraphs.

Dataset ladder:

| Stage | accepted duration | purpose |
| --- | ---: | --- |
| 0 | 30–60 s | prove speaker and pronunciation consistency |
| 1 | 3–5 min | preprocessing + tiny one-speaker training feasibility |
| 2 | 10–20 min | evaluate identity/pronunciation stability |
| 3 | 30–60 min | candidate production corpus, only if prior gates pass |

Five minutes may reveal whether the pipeline functions, but is not evidence of
podcast-quality generalization.  Thirty to sixty minutes of unusually clean,
varied speech is a reasonable *target*, not a guaranteed sufficient dataset.

## 6. CPU cost and operational estimates

Facts: Piper's own guide documents preprocessing, checkpoints and ONNX export,
but its recommended training command is GPU-based.  It does not publish a
reliable i9-13900H timing table.  The numbers below are therefore estimates,
not benchmarks.

| Work | RAM / disk | i9-13900H estimate | operating rule |
| --- | --- | --- | --- |
| Stage 0 short-source pilot | 3–5 GB RAM; <0.5 GB new disk | 10–60 min depending on accepted/rejected takes | sequential; stop immediately on speaker drift |
| Dataset prep, 3–5 min | 4–8 GB RAM; 1–3 GB working disk | 1–4 h, dominated by human QA | transcript/normalization review first |
| small VITS/Piper pilot | 8–14 GB RAM; 5–15 GB working disk | days, potentially longer, at batch size constrained by RAM | checkpoint frequently; resume after thermal breaks |
| 30–60 min final experiment | 8–16 GB RAM; 15–40 GB working disk | many days to weeks; not responsibly predictable before pilot | AC power, cooling, low-priority workload, resumable checkpoints |
| exported ONNX production | likely hundreds of MB, model-dependent | target is practical CPU rendering; must benchmark after training | no claim of 7–8 min/3 min audio until measured |

CPU training should use modest batches, reserve several GB RAM for Fedora, run
while plugged in, monitor temperature/thermal throttling, and write epoch or
step checkpoints frequently.  A process can be stopped/resumed only if the
selected trainer's checkpoint and optimizer state are retained.

## 7. Decision matrix (1 weak — 5 strong)

Hard-gate failures are not rescued by the average.

| Route | VI | distinctive identity | stable identity | long-form after training | CPU design | CPU train | CPU production | zero-cost | licence | portable | risk |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| Qwen identity -> VieNeu short QA -> Piper/VITS from scratch -> ONNX | 4 | 4 | 4 | 3 | 5 | 2 | 5 | 5 | 3 | 5 | 3 |
| Qwen -> VieNeu directly for podcast | 3 | 4 | 3 | 1 | 5 | n/a | 4 | 5 | 3 | 3 | 2 |
| Train raw VITS from synthetic corpus | 3 | 4 | 4 | 3 | 5 | 2 | 3 | 5 | 3 | 3 | 4 |
| Matcha/FastSpeech2 component stack | 2 | 4 | 4 | 3 | 5 | 2 | 3 | 5 | 3 | 3 | 5 |
| VoxCPM2 CUDA architecture | 4 | 5 | 4 | 4 | 0 | 0 | 0 | **0** | 4 | 3 | 5 |

## 8. Exactly one next experiment — proposed, NOT executed

**Stage 0: Candidate 03 short-source corpus viability pilot.**

Generate a fixed set of **12** 2–8 s Vietnamese utterances through the existing
local VieNeu CPU path using frozen Candidate 03 conditioning and current
production-independent settings.  It is one experiment, no parameter grid and
no training.  Each clip receives a blind human accept/reject decision against
the QA rules above.  The output is a provenance manifest plus only accepted
WAV/transcript pairs; rejected clips are retained only as audit evidence and
never enter a training set.

| Requirement | Planned value |
| --- | --- |
| New files/downloads | no model download; approximately 12 WAVs + JSON/CSV manifest, <0.5 GB |
| CPU/RAM | existing CPU ONNX path; 3–5 GB expected from local historic measurements |
| Expected wall time | **ESTIMATE** 10–60 min synthesis plus listening/QA; sequential and safely stoppable between clips |
| Licence gate | do not promote accepted clips beyond research until Qwen synthetic-output-to-corpus use is explicitly cleared; preserve full provenance |
| Acceptance gate | at least 10/12 have correct Vietnamese, stable same synthetic person, no abnormal pause/stretch/clipping; otherwise **stop**, do not train |
| What it proves | whether this particular source can form clean short training data; it does not prove final model quality |

If the pilot fails, the proposed architecture stops before any multi-day CPU
training.  If it passes, the next decision is a separate, auditable Piper/VITS
toolchain and licence pin—not automatic training.

## Sources consulted

- Qwen official VoiceDesign card: <https://huggingface.co/Qwen/Qwen3-TTS-12Hz-1.7B-VoiceDesign>
- VieNeu v3 official card and licensing FAQ: <https://huggingface.co/pnnbao-ump/VieNeu-TTS-v3-Turbo>
- Piper training and ONNX export guide: <https://github.com/rhasspy/piper/blob/master/TRAINING.md>
- Piper Vietnamese voice catalogue: <https://github.com/rhasspy/piper/blob/master/VOICES.md>
- Original VITS implementation: <https://github.com/jaywalnut310/vits>
- Matcha-TTS official repository: <https://github.com/shivammehta25/Matcha-TTS>

No action follows this report without user approval.
