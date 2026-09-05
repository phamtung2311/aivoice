# Phase 37 — synthetic Brand Voice architecture decision

## Decision

**Recommended architecture: portable synthetic identity corpus → OmniVoice
multilingual clone renderer → local CPU production feasibility gate.**

Candidate 03 remains the first portable identity test asset, not a permanent
constraint. If OmniVoice proves Vietnamese quality/continuity but Candidate 03
does not transfer with enough character, create Candidate 04 synthetically with
a licensed designer and build a multi-reference corpus before any adaptation.

No model, dependency or audio was downloaded/generated in this phase.

## Serious architectures

| Architecture | Vietnamese | identity/prosody | CPU and licence | Decision |
| --- | --- | --- | --- | --- |
| **OmniVoice** | FACT: official project claims 600+ languages, including Vietnamese through language-agnostic multilingual synthesis. | FACT: clone from WAV+transcript, reusable clone prompt, voice design, auto voice, duration/speed controls; training pipeline is public. INFERENCE: strongest new test of Candidate 03 portability and future corpus adaptation. | FACT: Apache-2.0 code; current checkpoint is reported as ~612M/3.1 GB. Official docs show CUDA/MPS examples; a separate local C++ CPU/Vulkan route exists but must be independently audited. **SLOW BUT TESTABLE**, not yet production-proven. | **Selected next research architecture.** |
| VoxCPM2 | FACT: official Vietnamese support, 2B, direct Voice Design, cloning, style control and Apache-2.0. | Best native Candidate-04 architecture: new Vietnamese synthetic identity can be designed without any reference. | Official install calls for CUDA >=12; 16 GB non-CUDA path is not credible now. | Future GPU research / Strategy B; not current PoC. |
| Qwen3-TTS | FACT: VoiceDesign + clone + Apache; official languages exclude Vietnamese. | Candidate 03 creator, not Vietnamese renderer. | Existing CPU work slow; unsupported Vietnamese. | Preserve as one-time identity designer only. |
| Qwen-Audio-3.0-TTS | Cloud documentation lists Vietnamese and cloning/design controls. | Potentially strong, but local weights/terms/CPU route were not established in this audit. | Cloud is not an eventual production dependency. | Watchlist only. |
| Fish Speech S2 Pro | Multilingual clone/prosody claims; Vietnamese not sufficiently verified here. | Strong style/clone potential, but no auditable native synthetic speaker workflow for this goal. | ~5B/GPU-first; research licence signal. | Research-only, not local production. |
| CosyVoice | Clone/control and Apache code, but official local Vietnamese evidence was not established. | Potential clone path but weak brand-identity evidence. | GPU-oriented. | Not selected. |
| F5/E2-TTS | Community Vietnamese only; official Base is zh/en and CC BY-NC model. | Clone, but not a clean commercial foundation. | GPU-first. | Reject. |
| Spark-TTS | Voice design and Apache. | Strong virtual-speaker mechanism. | Officially Chinese/English only. | Reject for Vietnamese. |
| IndexTTS | Clone/prosody controls but official current list excludes Vietnamese; restricted model terms. | Not a safe Vietnamese foundation. | GPU-oriented. | Reject. |

## Strategy comparison

**Strategy A — Candidate 03 → OmniVoice:** highest information for lowest
identity disruption. Use the untouched canonical Qwen WAV and exact English
transcript for one Vietnamese diagnostic. It tests cross-language synthetic
identity preservation, Vietnamese pronunciation and phrase flow together.

**Strategy B — native Candidate 04:** VoxCPM2 is the best documented route:
Vietnamese plus direct text-described Voice Design plus commercial Apache terms.
It is blocked by current non-CUDA hardware, so it cannot be the next local
experiment. OmniVoice design mode exists but was trained for Chinese/English
attributes; direct Vietnamese design is explicitly less certain.

## Brand Voice reference corpus

A single seven-second English clip is a fragile portable identity interface. A
future `BRAND_VOICE_IDENTITY/` should contain 30–120 seconds of entirely
synthetic, clean references and exact transcripts across neutral narration,
Vietnamese tones, phrase lengths and controlled emphasis. This would allow
multi-reference clone prompting, speaker-adaptation/fine-tuning and an auditable
identity record. It cannot repair an engine with poor Vietnamese, so corpus
creation follows—not precedes—the short renderer gate.

## Adaptation conclusion

The likely eventual architecture is: one heavy licensed synthetic designer →
Vietnamese synthetic corpus → small commercially usable Vietnamese production
model adapted to that corpus. This is preferable to forcing a single inference
engine to design, clone and narrate. No Vietnamese adaptation base with both
clear commercial terms and a proven CPU path was found in this audit; do not
train yet.

## Matrix (1 poor, 5 strong; inference scores)

| Candidate | VI | synthetic identity | stable/distinctive | prosody/long form | CPU | adapt | licence | risk |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| OmniVoice | 4 | 5 | 4 | 4 | 3 | 4 | 5 | 3 |
| VoxCPM2 | 5 | 5 | 5 | 5 | 1 | 4 | 5 | 5 |
| Qwen3-TTS | 1 | 5 | 4 | 4 | 2 | 4 | 5 | 3 |
| Fish S2 Pro | 2 | 3 | 4 | 5 | 1 | 3 | 1 | 5 |
| CosyVoice | 2 | 3 | 3 | 3 | 2 | 3 | 4 | 4 |
| F5 / Spark / Index | 1 | 2 | 3 | 3 | 1 | 2 | 1 | 4 |

## Exactly one next experiment — requires approval

**OmniVoice provenance/API audit only.** Do not install or download weights.
Inspect its official repository and exact Hugging Face checkpoint/model-card
revision, weight/output licences, Vietnamese language ID/frontend, reference
clone interface, checkpoint size and CPU/quantized route. If terms or Vietnamese
support are unresolved, reject before install. If verified, the next separately
approved one-output PoC uses only Candidate 03 plus its exact transcript and a
single short Vietnamese diagnostic. Acceptance requires correct pronunciation,
continuous coherent narration, authority and recognizable character; otherwise
reject early.

**STOP — waiting for approval before the OmniVoice provenance/API audit.**
