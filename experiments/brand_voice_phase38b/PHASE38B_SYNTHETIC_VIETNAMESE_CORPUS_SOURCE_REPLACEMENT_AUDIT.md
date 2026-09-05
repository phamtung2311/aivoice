# Phase 38B — Synthetic Vietnamese corpus source replacement audit

Audit date: 2026-09-03. This phase is research only. No package was installed,
no repository/model was downloaded, no audio was generated, no training was
started, and production was not changed.

## Executive decision

Phase 38A is a hard failure: only 4/12 clips passed human listening against a
required 10/12 gate. The current `Candidate 03 -> VieNeu clone -> corpus`
bridge must not be enlarged, tuned until it passes, or sent into VITS/Piper.

The one architecture worth testing next is a separation of responsibilities:

```text
frozen Candidate 03 Qwen reference (identity only)
  -> OpenVoice V2 target tone-colour embedding

VieNeu v3 bundled preset (Vietnamese pronunciation + timing only)
  -> one clean Vietnamese source utterance
  -> OpenVoice V2 CPU tone-colour conversion
  -> Candidate 03-coloured Vietnamese utterance
  -> human comparison of source and converted audio
```

This is **not** another attempt to rescue VieNeu's Candidate 03 clone. Candidate
03's VieNeu speaker embedding and reference codes are removed from the path.
VieNeu is demoted to a licensed base-speaker renderer; OpenVoice separately
imposes identity. OpenVoice's official demo uses this exact source-speaker to
target-speaker separation and explicitly selects CPU when CUDA is unavailable.
Its converter does not consume text or a language ID, so Vietnamese phonemes,
timing, emphasis and pauses must already be correct in the source waveform.

This architecture is recommended for **one reversible probe**, not yet for
corpus creation or production. Its largest technical risk is that OpenVoice may
transfer only a weak approximation of Candidate 03 from the 6.96-second target,
or introduce conversion artifacts. Its largest legal risk is that official
Qwen material still does not explicitly grant or describe generated-audio use
as downstream TTS training data. Consequently, a converted corpus and model
remain research-only unless that issue is cleared.

## 1. Phase 38A failure summary

Human result:

| Result | Clips | Evidence |
| --- | --- | --- |
| PASS | 03, 08, 09, 11 | 4/12; clip 03 still not distinctive enough for the final Brand Voice |
| abnormal long pause | 01, 04, 06, 07 | systematic timing failure; 04 was otherwise fairly deep |
| weak / no force / no focus | 02, 10, 12 | delivery failure |
| severe speech corruption | 05 | corpus-integrity failure |

`STAGE 0 CORPUS QUALITY = FAIL`. Technical success (12 valid WAV containers,
48 kHz mono, no clipping, low RAM) did not predict perceptual corpus quality.

## 2. Root failure categories

These are separate defects and must not be collapsed into “the voice is bad”:

| Category | Phase 38A evidence | Architectural consequence |
| --- | --- | --- |
| Corpus cleanliness | 8/12 rejected; clip 05 corrupt | No bulk generation or training from this source |
| Pause/prosody | 4 clips with abnormal long pauses | The linguistic/prosodic source must pass before identity conversion |
| Delivery strength | 3 clips weak or unfocused | Identity conversion cannot be assumed to create emphasis absent from source |
| Speaker identity | Candidate 03 conditioning did not yield uniformly convincing identity | Identity needs an independent target representation and A/B check |
| Brand distinctiveness | Even accepted clip 03 was not distinctive enough | Correct Vietnamese alone is not success; target similarity and channel recognition need their own gate |

The likely problem is not one measurable knob. VieNeu's single conditioned
generation simultaneously chose pronunciation, durations, prosody and speaker
identity, and failed in several independent ways. That is why another
temperature/speed/punctuation grid is not justified.

## 3. Requirements for a VieNeu replacement

A replacement bridge must:

1. accept a purely synthetic target reference or create a repeatable synthetic
   identity without any user recording;
2. preserve Vietnamese words and tones from a clean source;
3. avoid inventing pauses, stretching, corruption or sentence resets;
4. preserve strong, focused source delivery while transferring a clearly
   recognizable timbre;
5. run every required step on x86-64 CPU with 16 GB RAM, even if slowly;
6. operate entirely from local files after setup;
7. expose deterministic/pinnable code, checkpoints and parameters;
8. have a plausible long-form chunk strategy;
9. support provenance and eventual monetization without an unacknowledged
   output/corpus-rights assumption.

No audited model currently proves all nine. The next experiment therefore tests
the highest-uncertainty technical link before any corpus work.

## 4. Candidate 03's future role

Candidate 03 remains a useful **target identity reference**, not a universal
speaker embedding. Its canonical asset stays unchanged at:

`experiments/brand_speaker_phase33c/baseline_anchor/BRAND_CANDIDATE_03_BASELINE/qwen_source.wav`

- SHA-256: `3f3f5c6771ed437297ffdd89c5ea2aebd2d34dd531235ad5dd12e93bf18b5f06`
- exact transcript: `A quiet evening settles over the city. I speak clearly, naturally, and without rushing.`
- duration: 6.96 s

VieNeu's `speaker_emb.npy` and `reference_codes.npy` are engine-specific and
cannot be injected into OpenVoice, Seed-VC, kNN-VC, Piper or another backbone.
Those systems must independently extract identity from the canonical WAV.

Candidate 03 is optional after the next gate. If a converter cannot make it
distinctive in Vietnamese, the project should not force it through more
bridges. The permanent podcast person, not Candidate 03, is the protected goal.

## 5. Current CPU-capable synthetic-identity options

| Option | Identity mechanism | CPU status | Decision |
| --- | --- | --- | --- |
| Qwen3-TTS 1.7B VoiceDesign | text-described speaker, then freeze WAV/reference | **Locally proven CPU**: existing 4.3 GiB checkpoint, about 5.2 GB peak RSS in prior work; very slow is acceptable | Keep only as identity designer; official language set does not establish Vietnamese |
| OpenVoice V2 | extracts target tone-colour embedding from reference WAV | **Official CPU branch** in demo and API (`device="cpu"`) | Best next target-identity carrier |
| Seed-VC V1/V2 | target reference conditions zero-shot speech conversion | V1 source has an explicit CPU fallback; V2 also chooses CPU but hard-codes float16 in setup, so V2 CPU compatibility is not established | Serious fallback, not first probe |
| kNN-VC | non-parametric matching set from target reference features | Standard PyTorch operations make CPU plausible; official documentation does not publish a CPU benchmark | Technically credible, but 6.96 s is far shorter than the reference duration the authors say improves quality |
| Twinkle-VC (VLSP 2025) | Vietnamese zero-shot VC derived from Seed-VC/QuickVC | No released, pinned CPU inference path in its public two-commit repository | Strong Vietnamese research evidence, but not currently an auditable runnable package |
| Chatterbox Multilingual | zero-shot reference clone | Official code allows CPU, but the official 23-language list excludes Vietnamese | Reject for this task |
| VoxCPM2 | text-described voice design and clone | Official runtime requires CUDA 12+; no required local CPU path was established | Hard-gate fail |

## 6. Current CPU-capable Vietnamese-generation options

There is still no audited direct model that combines native Vietnamese,
reference-free distinctive speaker design, clean long-form delivery, clear
commercial corpus rights and a verified 16 GB CPU path.

| Generator role | Vietnamese evidence | CPU / local evidence | Fit now |
| --- | --- | --- | --- |
| VieNeu v3 bundled preset only | Native Vietnamese, 20 bundled regional/character voices | Official ONNX CPU path; locally installed 3.3.0 model cache is about 226 MiB | Use only as a base waveform in one new separated architecture; do not use Candidate 03 cloning |
| Existing VieNeu Candidate 03 clone | Phase 38A real human evidence | CPU proven | Rejected: 4/12 pass |
| VietVoice-TTS clone | Prior local phases produced good identity/Vietnamese in places | ONNX CPU proven locally | Rejected as a stable source: continuity/pronunciation trade-off remained |
| Qwen/Gwen clone paths | Candidate 03 identity source works in English | CPU technically ran, but corrected Vietnamese Gwen remained English-like; Qwen VoiceDesign has no official Vietnamese support | Rejected as Vietnamese renderer |
| V-TTS / Valtec zero-shot | Native Vietnamese claims and CPU API | Prior Phase 36M pinned-source audit found mutable checkpoint redirects and a CC BY-NC code lineage | Rejected: commercial/provenance gate remains unresolved |
| Piper/VITS from scratch | Vietnamese phonemization and CPU final inference are plausible | CPU training is technically possible but days/weeks; final ONNX CPU strong | A destination only after clean corpus exists; not a corpus source |

The genuinely new evidence is VieNeu's official separation between stable
bundled presets and instant clone profiles, plus explicit rights for commercial
audio from bundled presets. Phase 38A tested the second path, not whether a
bundled preset can supply one clean base utterance for a different converter.

## 7. Voice-conversion bridge audit

### OpenVoice V2 — first choice

The official repository says V1/V2 perform tone-colour cloning and zero-shot
cross-lingual conversion, and that the source/reference languages need not be
in the converter's training set. The official cross-lingual notebook:

1. obtains `source_se` from the base speaker;
2. obtains `target_se` from the reference speaker;
3. calls `ToneColorConverter.convert(audio_src_path, src_se, tgt_se, ...)`.

The code loads source audio at the converter sample rate, computes a
spectrogram, and runs `model.voice_conversion`. It has no transcript and no
Vietnamese tokenizer in the conversion path. This is valuable here: linguistic
content and timing originate in the clean Vietnamese source rather than being
regenerated from Candidate 03's English transcript.

CPU classification: **officially supported in example code**, not merely
theoretical. The demo chooses `cuda:0` when available and `cpu` otherwise; the
API accepts `device='cpu'` and maps checkpoints/tensors to it. There is no
official i9-13900H RTF or RAM benchmark.

Version to pin for a future probe:

- code: `myshell-ai/OpenVoice` commit `74a1d14` (latest commit shown on the
  official main history, 2025-04-19);
- weights: official `myshell-ai/OpenVoiceV2` HF snapshot `f36e7ed`, 131 MB total;
- converter-only checkpoint is about 126 MB according to the official issue
  evidence. The current official HF snapshot avoids relying on the historical
  S3 link, which has had accessibility failures.

Limits: Vietnamese is not one of V2's six native **base-TTS** languages. That
does not block converter input, but it means MeloTTS must not be used to create
Vietnamese. OpenVoice can preserve source timing; it cannot repair a bad source
pause or invent authority that the source never contained. Watermarking should
remain at its documented default in an initial probe.

### Seed-VC — quality-oriented fallback

Seed-VC accepts arbitrary source audio and 1–30 s target reference without
training. The current V1 CLI explicitly falls back to `torch.device("cpu")` and
uses float32 when `--fp16 false`; the 25-step diffusion path is therefore
technically CPU-capable. V2 also selects CPU, but its setup fixes float16 and
has no published CPU validation, so it is not yet a safe V2 CPU claim.

The official model repository is 3.94 GB in total. A V1 offline checkpoint is
440 MB, while other configurations are 821 MB and require additional speaker,
semantic and vocoder assets. A conservative full experiment allowance is
2–5 GB downloads/cache and 6–12 GB RAM; these are planning estimates, not a
measured CPU run. Ten seconds could take many minutes or longer. Slowness is
not the rejection; the archived repository (2025-11-21), complex asset chain,
CPU uncertainty and GPL/output provenance make it second choice.

### kNN-VC — simple but reference-hungry fallback

kNN-VC uses WavLM features, nearest-neighbour replacement and a HiFi-GAN
vocoder. The matching stage requires no training. Official documentation lists
only PyTorch, torchaudio and NumPy for inference and accepts arbitrary 16 kHz
source and one or more target WAVs. It says longer cumulative target material
improves quality, with diminishing returns beyond five minutes. Candidate 03's
single 6.96 s reference therefore creates a major identity-quality risk.

The official docs do not claim CPU speed, RAM, Vietnamese testing, or
Candidate-03-length adequacy. It is likely to fit 16 GB with WavLM-Large and a
vocoder, but that remains an inference until measured. Output is 16 kHz, a
clear fidelity disadvantage for a permanent podcast corpus.

### Twinkle-VC and EZ-VC — newer 2025 evidence, not runnable finalists

Twinkle-VC is directly relevant: its VLSP 2025 paper reports first place on the
Vietnamese voice-conversion challenge (MOS 4.29 ± 0.16, target-speaker MOS
3.65 ± 0.23, WER 9.83). However, the linked public repository contains only
two commits, describes forks of Seed-VC and QuickVC, and exposes no release,
packaged checkpoint, complete licence, frozen dependency manifest or verified
CPU recipe. This is evidence that Vietnamese-specialized VC can work—not a
reproducible zero-cost local component today. Code/weights/output rights and
CPU feasibility are **UNRESOLVED**, so it cannot be the next experiment.

EZ-VC is a proper 2025 official implementation and documents NVIDIA, AMD,
Intel XPU and Apple paths, but its authors explicitly license pretrained weights
CC BY-NC. That makes it **PERSONAL-ONLY** and a future monetization trap, even
before CPU/RAM quality testing. It is excluded rather than hidden by a high
research score.

### RVC / so-vits-svc / speaker-specific VC

These normally obtain strong identity by training on substantial target-speaker
audio. Candidate 03 has only 6.96 s. Training on a synthetic target corpus would
reintroduce the exact missing-corpus problem, while training from a user voice
is forbidden. They are not serious next bridges.

## 8. Speaker embedding / adapter architecture audit

- Speaker embeddings are not interchangeable tensors. VieNeu's 192-vector,
  OpenVoice tone-colour representation, Seed-VC conditioning, ECAPA/x-vector,
  and Piper speaker IDs inhabit different learned spaces.
- Extracting an x-vector from Candidate 03 does not make a Vietnamese acoustic
  model understand that vector unless the model was trained with the exact
  encoder/conditioning contract.
- A LoRA, adapter, learned speaker token or GST can stabilize identity only
  after an objective supplies target evidence. With no human recording and no
  clean Candidate 03 Vietnamese corpus, adaptation is circular.
- Optimizing a speaker token only for reconstruction of the English 6.96 s
  reference does not establish Vietnamese pronunciation or long-form identity.

Therefore there is no justified direct `Candidate 03 embedding -> Vietnamese
backbone` route today. OpenVoice/Seed-VC are valid because they implement their
own trained cross-speaker conversion contract; arbitrary embedding injection is
not.

## 9. Direct synthetic Vietnamese identity possibilities

The attractive ideal is `description/random latent -> stable new Vietnamese
person`. Current audited options do not clear all gates:

- VoxCPM2 has direct design and Vietnamese, but the required official runtime
  is CUDA 12+.
- Qwen VoiceDesign is locally proven on CPU but does not officially support
  Vietnamese.
- Chatterbox has CPU and synthetic/reference cloning but not Vietnamese in its
  official multilingual list.
- Sampling/interpolating speaker tables inside a Vietnamese multi-speaker VITS
  is mathematically possible, but is not a documented identity-design method.
  Off-manifold embeddings can produce instability or blends rather than a
  coherent new person, and there is no target criterion without recordings.
- Training a new single-speaker VITS/Piper from scratch can freeze a synthetic
  identity only after the clean corpus already exists; it does not solve corpus
  creation.

Conclusion: **no direct reference-free Vietnamese synthetic-person generator is
currently defensible under the mandatory CPU/local constraints.**

## 10. Licensing audit

This is an engineering provenance assessment, not legal advice.

| Component | Code | weights / voice assets | data provenance | output / derivatives / monetization | Classification |
| --- | --- | --- | --- | --- |
| Qwen3-TTS VoiceDesign | Apache-2.0 | official card: Apache-2.0 | detailed training corpus not supplied here | No official clause found that explicitly addresses generated-audio ownership or using output to train another TTS | **UNRESOLVED** for downstream corpus/model; ordinary model use is permissive |
| VieNeu v3 bundled presets | Apache-2.0 | card says all model, ONNX, tokenizer and preset assets are Apache-2.0 | detailed internal corpus gated; card says preset speakers/rightsholders consented | card explicitly permits preset-generated audio in commercial/monetized content; it does not explicitly discuss training another TTS | **CONDITIONALLY COMMERCIAL-SAFE** for published audio; **UNRESOLVED** for synthetic training corpus |
| OpenVoice V2 | MIT | official HF model card/snapshot: MIT; repo says V1/V2 free for commercial/research use | detailed converter training-data provenance not disclosed in audited official material | commercial use is explicit; no explicit output-as-training-data clause found | **CONDITIONALLY COMMERCIAL-SAFE** for conversion use; **UNRESOLVED** for downstream training corpus |
| Seed-VC | GPL-3.0 | official HF repository metadata: GPL-3.0 | component datasets/checkpoints span several upstream models; complete rights chain is not summarized | GPL allows commercial software use with copyleft duties, but output/corpus and target-voice rights are not explicitly settled | **CONDITIONALLY COMMERCIAL-SAFE** for software; **UNRESOLVED** for corpus/derived model |
| kNN-VC | MIT | checkpoints distributed through repo releases/torch hub; upstream WavLM/vocoder notices still need a pinned inventory | paper/repo identifies WavLM and a LibriSpeech-trained vocoder; complete checkpoint notice audit still required | no explicit output-to-training grant found | **UNRESOLVED** until all checkpoint/data notices are pinned |
| Twinkle-VC | no root licence found in the published two-commit repository | no reproducibly released checkpoint found | VLSP Vietnamese data/evaluation is described by the paper, but redistribution/training rights are not packaged with a runnable release | no output/corpus grant found | **UNRESOLVED — not selectable** |
| EZ-VC | MIT | authors explicitly state pretrained models are CC BY-NC | upstream components/datasets require separate notices | non-commercial weights block a monetized required path | **PERSONAL-ONLY — reject** |
| Piper/VITS future destination | implementation-dependent; current Piper family is GPL-3.0 | from-scratch project checkpoint would avoid a public voice, but trainer/frontend notices remain | only accepted project corpus | distribution obligations and synthetic-corpus rights must be cleared before training | **UNRESOLVED UNTIL PINNED** |

## 11. Synthetic-output-to-training-data rights

No audited official source explicitly says the complete proposed chain may be
used as:

```text
Qwen-designed reference
  -> OpenVoice-converted Vietnamese audio
  -> training corpus for a new TTS
  -> monetized derived model
```

Therefore that chain is **UNRESOLVED** for training. In particular:

- Apache-2.0 on Qwen code/weights is not an explicit statement about copyright
  or contractual status of generated audio.
- VieNeu explicitly permits commercial/monetized *content* from bundled voices,
  but its card does not explicitly grant training a competing/derived TTS.
- OpenVoice explicitly permits commercial/research model use, but its MIT grant
  does not expressly characterize generated waveform ownership or downstream
  corpus training.

The next probe may remain a private research audition. Do not produce a corpus,
train Piper/VITS, distribute a derived model, or claim monetization clearance
until written official terms or legal review resolve this chain.

## 12. CPU, RAM and disk feasibility

Local machine facts: Intel i9-13900H, 20 logical CPUs / 14 cores, AVX2 and
AVX-VNNI, x86-64, 16 GB RAM, Fedora 44, no CUDA; about 338 GB disk free at
audit time. A local Python 3.12.14 runtime already exists from an isolated prior
experiment, but a future OpenVoice venv must be separate.

| Route/tool | Model/download | RAM planning | CPU status and wall-time expectation |
| --- | ---: | ---: | --- |
| Existing VieNeu v3 preset source | already cached, about 226 MiB | Phase 38A observed <1 GB process RSS with current ONNX path | Official ONNX CPU; a short utterance is seconds, locally demonstrated |
| OpenVoice V2 converter | official HF snapshot 131 MB; isolated CPU PyTorch environment makes total new disk roughly 1.5–3 GB | estimate 2–4 GB | Official CPU code path; no official RTF. Estimate: seconds to a few minutes for one 5–8 s clip |
| Seed-VC V1 | at least 440 MB primary checkpoint plus semantic/speaker/vocoder assets; allow 2–5 GB | estimate 6–12 GB | Explicit PyTorch CPU fallback; expect many minutes or longer per 10 s; no official CPU benchmark |
| kNN-VC | WavLM-Large + HiFi-GAN; exact release inventory must be measured before download; allow roughly 1–3 GB | estimate 4–8 GB | PyTorch CPU plausible, no official CPU benchmark; likely minutes rather than real time |
| Qwen VoiceDesign | existing local checkpoint about 4.3 GiB | prior measured peak about 5.2 GB | Locally proven CPU, roughly 44–78 RTF in prior experiments |
| Future VITS/Piper training | no base selected; allow 5–40 GB working disk by stage | 8–14 GB cautious target | CPU technically possible and resumable; days/weeks, not yet justified |

OpenVINO/ONNX: the existing VieNeu source already uses ONNX Runtime CPU and is
the only route with a documented optimized CPU graph. OpenVoice, Seed-VC and
kNN-VC are PyTorch pipelines. No official ONNX/OpenVINO export is documented
for their complete conversion stacks, so Intel GPU/OpenVINO acceleration must
not be assumed. PyTorch CPU can use oneDNN/AVX automatically where supported;
Intel Extension for PyTorch is optional and not part of the first probe.

## 13. Final local production feasibility

If the OpenVoice probe passes, there are two local endpoints:

1. **Direct two-stage production:** VieNeu preset renders each natural
   Vietnamese utterance, then OpenVoice converts it to the frozen target
   embedding. Both stages run locally on CPU. This avoids a corpus/training
   rights claim but still requires monetization review of the final converted
   audio chain. Long-form stability is handled by natural utterance grouping,
   not arbitrary comma splitting.
2. **Later distillation:** only after corpus rights are resolved and a 12-clip
   gate passes, curate converted clips and train a single-speaker VITS/Piper,
   then export ONNX. This offers the most portable permanent narrator but is
   not authorized or justified now.

The direct two-stage renderer is the present architecture target because it can
be fully local without any training. Distillation is optional, not a required
stage hidden behind unavailable compute.

## 14. Five complete architecture candidates

### Route A — recommended

```text
Qwen Candidate 03 reference
  -> OpenVoice V2 target embedding
VieNeu licensed preset -> clean Vietnamese source
  -> OpenVoice CPU conversion
  -> direct local podcast renderer
  -> optional later QA corpus/distillation only after rights clearance
```

It separates pronunciation/prosody from identity and is entirely local/CPU.

### Route B — higher-complexity VC fallback

```text
Qwen Candidate 03 reference
VieNeu licensed preset -> clean Vietnamese source
  -> Seed-VC V1 float32 CPU conversion
  -> direct local renderer
  -> optional later distillation
```

Potentially stronger identity transfer, but much heavier, archived, slower and
legally more complex. V2 CPU is not yet established.

### Route C — non-parametric VC fallback

```text
Qwen Candidate 03 reference set
VieNeu licensed preset -> clean Vietnamese source
  -> WavLM kNN matching + HiFi-GAN CPU
  -> direct local renderer or QA corpus
```

No converter training is required, but the 6.96 s target and 16 kHz output are
poor fits for a high-fidelity permanent podcast voice.

### Route D — direct multilingual clone

```text
Candidate 03 reference -> Chatterbox Multilingual CPU -> Vietnamese
```

This is operationally simple but fails the Vietnamese evidence gate: Vietnamese
is absent from the official supported-language list. It is retained only to
show why a popular direct-clone option does not win the matrix.

### Route E — Vietnamese-specialized Twinkle-VC

```text
clean Vietnamese source -> Twinkle-VC -> Candidate 03 -> local output/corpus
```

The 2025 Vietnamese evaluation is the strongest language-specific evidence in
this audit, but the public artifact does not supply a pinned pretrained release,
licence or CPU recipe. The architecture is serious research and a present hard
gate failure as an implementable product route.

## 15. Decision matrix

Scores are 1 (weak) to 5 (strong). “Risk” is scored as manageability: 5 means
low implementation risk. A score is not proof of listening quality.

| Complete route | Distinctive | Same person | Vietnamese | Pause/prosody | Long-form | No user | CPU identity | CPU corpus | CPU train/adapt | CPU final | 0 VND | Licence clarity | Portable | Risk | HARD GATE |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| **A. VieNeu preset -> OpenVoice V2 -> Candidate 03; direct CPU** | 4 | 4 | 4 | 4 | 3 | 5 | 5 | 5 | 5 (none required) | 5 | 5 | 3 | 4 | 4 | **PASS, listening/licence gates remain** |
| B. VieNeu preset -> Seed-VC V1 -> Candidate 03; direct CPU | 4 | 4 | 4 | 4 | 3 | 5 | 5 | 3 | 5 (none required) | 3 | 5 | 2 | 3 | 2 | **NOT CLEARED — CPU smoke required** |
| C. VieNeu preset -> kNN-VC -> Candidate 03 | 3 | 3 | 4 | 4 | 3 | 5 | 4 | 3 | 5 (none required) | 3 | 5 | 2 | 3 | 3 | **NOT CLEARED — CPU/reference validation required** |
| D. Chatterbox direct Candidate 03 clone | 4 | 4 | 1 | 2 | 3 | 5 | 4 | 4 | 5 (none required) | 4 | 5 | 4 | 4 | 3 | **FAIL — no official Vietnamese support** |
| E. Twinkle-VC Vietnamese source -> Candidate 03 | 4 | 4 | 5 | 4 | 4 | 5 | 1 | 1 | 1 | 1 | 2 | 1 | 2 | 1 | **FAIL — no pinned runnable/licensed CPU release** |

Routes B/C are not allowed to outrank Route A merely because slowness is
acceptable. Their lower rank comes from reference adequacy, unverified CPU
execution details, fidelity and rights—not speed itself.

## 16. One recommended architecture

Choose **Route A: licensed Vietnamese preset source -> OpenVoice V2 tone-colour
conversion -> frozen Candidate 03 target -> direct local CPU production**.

1. **Identity creation:** retain the canonical Qwen-designed Candidate 03 WAV;
   OpenVoice extracts its own target embedding once.
2. **Vietnamese generation:** a VieNeu bundled preset, not a clone, creates the
   source utterance with native Vietnamese text handling.
3. **Corpus/adaptation:** none is required for the first viable endpoint. A
   corpus is an optional later branch only after rights and quality gates.
4. **Identity stabilization:** freeze target WAV hash, OpenVoice revision,
   target embedding hash, source preset and conversion settings.
5. **Final local production:** sequential VieNeu ONNX CPU rendering followed by
   OpenVoice PyTorch CPU conversion, in natural sentence groups.
6. **Why it addresses Phase 38A:** it stops asking VieNeu's Candidate 03 clone
   conditioning to solve identity, timing and pronunciation simultaneously.
7. **Largest risk:** OpenVoice may not impose enough distinctive Candidate 03
   identity, and it cannot improve bad source prosody. Legal use of Qwen output
   in a derived training corpus also remains unresolved.

This is the best *testable* architecture, not a declaration that the permanent
Brand Voice has been solved.

## 17. Exactly one next experiment — proposal only

### Phase 38C: one OpenVoice V2 CPU separation probe

Create one source/converted pair for a single Vietnamese utterance deliberately
containing two natural clauses and a focal phrase. Use one fixed bundled
northern male preset with a firm delivery (proposed: `Minh Đức`, character
`News`) at documented/default settings. Convert that exact waveform once into
the frozen Candidate 03 target with OpenVoice V2 defaults. No grid, no retry,
no post-processing, no corpus creation.

| Item | Proposed value before execution |
| --- | --- |
| Tool/version | `myshell-ai/OpenVoice` commit `74a1d14`; official OpenVoiceV2 HF snapshot `f36e7ed`; existing VieNeu SDK 3.3.0 |
| Environment | new experiment-only Python 3.12 venv under `experiments/brand_voice_phase38c/`; do not touch production `.venv` |
| Required local inputs | canonical Candidate 03 `qwen_source.wav`; exact fixed Vietnamese text; frozen preset name/settings |
| Downloads | OpenVoice source plus official 131 MB V2 checkpoint snapshot; CPU-only Python dependencies. VieNeu model is already cached |
| Disk | reserve 3 GB for venv, checkpoint, logs and WAVs; current free disk about 338 GB |
| RAM | estimated 2–4 GB peak for OpenVoice plus short sequential VieNeu run; never load both engines concurrently if avoidable |
| CPU | x86-64 PyTorch CPU conversion; no CUDA, cloud, OpenVINO or Iris Xe required |
| Expected wall time | setup 10–30 min depending on downloads; one source + one conversion estimated 1–10 min. These are estimates; measure load, synthesis, conversion, RSS and RTF |
| Licence | OpenVoice code/weights MIT; VieNeu/preset Apache-2.0 and preset audio commercially permitted; Qwen reference Apache-2.0 model but generated-output/downstream-training rights unresolved |
| Outputs | `source_vietnamese.wav`, `candidate03_openvoice.wav`, `metrics.json`, `provenance.json`, and a short listening sheet; raw files only |
| What success proves | a clean Vietnamese waveform can retain words/timing/force while gaining a stable, noticeably Candidate 03-like tone on CPU |
| Acceptance gate | source itself: correct, no abnormal pause/corruption, firm focus; conversion: same words and pause structure, no new artifact, audibly closer to Candidate 03, meaningfully more distinctive than source, not exhausting. Both must pass; otherwise stop OpenVoice |
| Rollback | delete only `experiments/brand_voice_phase38c/` and any dedicated OpenVoice cache/venv after recording hashes; no production rollback exists because production is untouched |

One clip cannot prove corpus yield or long-form comfort. It is intentionally a
cheap falsification test. If it passes, a later separately approved phase may
test a small multi-register gate. If it fails, do not tune OpenVoice or create a
corpus; evaluate Seed-VC V1 CPU compatibility next as a new decision.

## 18. Stop point

No Phase 38C directory, environment, source clip, target embedding, converted
audio or corpus was created. No production or canonical Candidate 03 file was
modified. Phase 38B stops before execution.

## Authoritative sources

- [OpenVoice official repository and commercial-use statement](https://github.com/myshell-ai/OpenVoice)
- [OpenVoice official usage guide](https://github.com/myshell-ai/OpenVoice/blob/main/docs/USAGE.md)
- [OpenVoice official CPU-capable API](https://github.com/myshell-ai/OpenVoice/blob/main/openvoice/api.py)
- [OpenVoice official cross-lingual conversion notebook](https://github.com/myshell-ai/OpenVoice/blob/main/demo_part2.ipynb)
- [OpenVoice V2 official 131 MB MIT checkpoint](https://huggingface.co/myshell-ai/OpenVoiceV2)
- [Seed-VC official archived repository](https://github.com/Plachtaa/seed-vc)
- [Seed-VC official model repository and asset sizes](https://huggingface.co/Plachta/Seed-VC/tree/main)
- [kNN-VC official repository/API](https://github.com/bshall/knn-vc)
- [Twinkle-VC official VLSP 2025 paper](https://aclanthology.org/2025.vlsp-1.15/)
- [Twinkle-VC public research repository](https://github.com/Twinkle-Team/voice_conversion)
- [EZ-VC official repository and non-commercial checkpoint notice](https://github.com/EZ-VC/EZ-VC)
- [VieNeu v3 official CPU/preset/licensing card](https://huggingface.co/pnnbao-ump/VieNeu-TTS-v3-Turbo)
- [Qwen3-TTS VoiceDesign official card](https://huggingface.co/Qwen/Qwen3-TTS-12Hz-1.7B-VoiceDesign)
- [Chatterbox official repository](https://github.com/resemble-ai/chatterbox)
