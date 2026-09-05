# Phase 30H Report

## Timestamp

2026-08-31 (Asia/Ho_Chi_Minh)

## Status

SYNTHETIC_REFERENCE_PATH_EXPERIMENTAL

## Objective

Determine whether a genuinely new, reusable, non-human synthetic speaker identity can be made locally and legally, then used as a reference for Vietnamese VieNeu output without changing production.

## Production Safety

Git status was inspected first and revealed extensive unrelated pre-existing edits. They were preserved. This phase installed nothing, downloaded nothing, created no environment, generated no voice, and changed no production backend, frontend, API, VieNeu engine, profile, saved voice, or dependency.

## Previous Constraints

VieNeu has no native new-speaker generator; it needs reference audio. Common Voice and other open-dataset speaker cloning are out of scope because consent/privacy/derivative use is unresolved. Voice conversion, random VieNeu embeddings, presets, DSP, and emotion-token tricks are not viable identity sourcing.

## Synthetic Voice Creation Definition

Valid: text-described voice design, virtual speaker generation, documented latent/identity sampling, or documented interpolation that yields a stable non-human identity. Invalid: pitch, EQ, bass, formant, reverb, speed, or a required human reference.

## Current Technology Landscape

Qwen3-TTS is the strongest current open local VoiceDesign release. Spark-TTS provides constrained virtual-speaker controls but only Chinese/English. Fish Speech, CosyVoice, F5-TTS, GPT-SoVITS, IndexTTS, Chatterbox, OpenVoice, and StyleTTS-derived systems provide cloning, style, or multilingual features but do not establish the required combination of new identity plus Vietnamese bridge plus rights/hardware fit.

## Direct Vietnamese Voice Design

None verified. Qwen3-TTS’s official 1.7B VoiceDesign supports Chinese, English, Japanese, Korean, German, French, Russian, Portuguese, Spanish, and Italian, not Vietnamese. No direct Vietnamese model found with documented non-human voice design, clear local weights, and acceptable commercial posture.

## Voice Design Candidates

Qwen3-TTS 12Hz 1.7B VoiceDesign is primary. It accepts target text plus natural-language instruction, is explicitly a VoiceDesign release, and its official documentation describes creating a synthetic short reference then reusing it as a clone prompt. Spark-TTS can create virtual speakers through gender/pitch/rate controls, but lacks Vietnamese. The other candidates are not documented stable new-identity factories.

## Virtual Speaker Generation

Spark-TTS is the closest secondary example: its repository reports controllable virtual speakers by gender, pitch, and rate. This is constrained identity creation, not rich semantic podcast-character design, and its language scope is Chinese/English. It is not selected.

## Cross-Lingual Bridge Options

No external bridge qualifies. Qwen, Spark, and CosyVoice officially exclude Vietnamese from their stated language sets. Community Vietnamese forks of F5/IndexTTS may be reference cloners but do not originate a new identity and often have non-commercial or permission-restricted weights. Adding an unsupported bridge would create a three-stage artifact chain.

## Two-Stage Architecture

Primary experimental option D:

Qwen3-TTS 1.7B VoiceDesign, English
→ selected clean synthetic English 6–8 second WAV
→ installed VieNeu reference encoder
→ VieNeu V3Turbo Vietnamese output

The external model is a one-time voice factory. If the experiment passes, VieNeu remains daily local production TTS.

## Identity Preservation

Within Qwen, its official VoiceDesign-to-Base workflow supports reusing the designed WAV as a clone prompt. Across Qwen to VieNeu, preservation is unverified. VieNeu’s installed path derives both a language-agnostic-looking speaker x-vector and time-varying MOSS codes; no evidence proves these retain a designed English timbre in Vietnamese. Identity-loss risk: HIGH/UNKNOWN.

## Synthetic Reference → VieNeu Compatibility

SUPPORTED_BY_INPUT_PATH / TECHNICALLY_PLAUSIBLE. Phase 30E code audit shows prepare_reference consumes waveform audio, trims/optionally denoises it, and derives speaker embedding plus MOSS codes without a reference-language or transcript argument. No code indicates a synthetic WAV is rejected. Compatibility is not quality validation.

## Vietnamese / Tonal Risks

The design model does not speak Vietnamese. VieNeu may retain useful timbre but distort identity/prosody while generating tonal Vietnamese. Main risks: wrong tones/intelligibility, accent coloration, speaker drift, metallic codec artifacts, noise/breath artifacts, and compounded TTS-on-TTS character. A 6–8 second reference cannot establish 10–30 minute listening comfort.

## CPU / RAM Feasibility

Qwen model card reports 4.52 GB for the 1.7B VoiceDesign repository. On i9-13900H, CPU loading/inference is plausible but slow; quality is prioritized and only three short factory samples are proposed. With 16 GB RAM, bf16 may be possible but standard PyTorch, tokenizer, audio buffers, and system usage create a RAM-risk margin; classify POSSIBLE_WITH_QUANTIZATION / RAM_RISK. Do not use float32. No benchmark was run.

## Intel Feasibility

Fedora Linux CPU execution is plausible because Qwen exposes CPU device handling. No official ONNX, OpenVINO, IPEX, or Intel Iris Xe path was verified for VoiceDesign. Treat Iris Xe as unavailable; do the potential PoC on CPU only. No CUDA is required, but no speed promise is made.

## Python / Environment Requirements

The official Qwen guide recommends a fresh isolated Python 3.12 environment and qwen-tts package. Phase 30I must not touch the production Python 3.14 VieNeu environment. Qwen’s GPU-oriented FlashAttention guidance is optional and should not be installed for CPU-only operation.

## Licensing / Commercial Risk

Qwen’s official repository and selected Hugging Face weights card list Apache-2.0. This is favorable but not a complete output/provenance warranty; archive the exact revision and model card, review notices and generated-output terms at acquisition, and avoid prompts seeking a real person. Spark needs separate code/weights review. Fish Speech is research-licensed; common Vietnamese forks frequently use NC or permission-restricted weights. Classification for primary: REVIEW_REQUIRED, not automatically low risk.

## Provenance Risk

Qwen is explicitly designed for voice creation, which is preferable to sourcing a public person or anonymous corpus speaker. It does not establish mathematical uniqueness nor guarantee no resemblance to training speakers. Use attribute-only prompts, preserve the generation record, reject any accidental recognizable resemblance, and do not claim that generated output is legally risk-free.

## Technology Comparison

| technology | new identity | Vietnamese | bridge | 16 GB CPU | license posture | fit |
|---|---|---|---|---|---|---|
| Qwen3-TTS 1.7B VoiceDesign | Yes | No | VieNeu input-path only | Possible / RAM risk | Apache listed; review | Primary experimental |
| Spark-TTS 0.5B | Constrained virtual | No | None | Possible | Review | No |
| Fish Speech S2 Pro | Not proven | Unverified | Unverified | Not realistic | Research | No |
| CosyVoice 3 | No | No | None | RAM risk | Review | No |
| F5 / IndexTTS Vietnamese forks | No | Community | Reference only | Varies | NC/restricted often | No |

Full required-field comparison is in experiments/special_voice_podcast/synthetic_reference_research/technology_comparison.md.

## Architecture Comparison

A Direct Vietnamese VoiceDesign: unavailable.
B VoiceDesign → external Vietnamese bridge → VieNeu: unsupported, too many artifact stages.
C Virtual speaker generator → Vietnamese TTS → VieNeu: unsupported.
D Qwen VoiceDesign English → VieNeu Vietnamese: primary experimental path.
E Permissioned human reference → VieNeu: production-safe fallback.

## Primary Path

Qwen3-TTS-12Hz-1.7B-VoiceDesign, English description
→ one clean synthetic English reference WAV
→ VieNeu encode_reference
→ Vietnamese VieNeu V3Turbo

This is the only selected path.

## Phase 30I Download Budget

Do not download in Phase 30H. Phase 30I would need:

| Item | Source | Approximate size / requirement |
|---|---|---|
| VoiceDesign weights plus included tokenizer assets | Qwen/Qwen3-TTS-12Hz-1.7B-VoiceDesign | 4.52 GB listed |
| Qwen runtime and dependencies | qwen-tts from PyPI in separate Python 3.12 venv | estimate 3–6 GB including CPU PyTorch and cache; verify resolver before proceeding |
| Official source code, optional | QwenLM/Qwen3-TTS | small relative to weights |
| Temporary audio / logs | local experiment folder | under 1 GB |
| Working disk | isolated experiment directory | reserve 12 GB minimum, preferably 15 GB |
| RAM | i9 CPU execution | 16 GB present; bf16 only, close other heavy apps; no float32 |
| GPU | none | CPU only; Iris Xe not used |

No Vietnamese bridge checkpoint is budgeted. VieNeu is already installed and must remain untouched.

## Findings

1. Qwen3-TTS VoiceDesign is documented genuine synthetic voice creation and has an official synthetic-reference reuse workflow.
2. It has no Vietnamese support.
3. No external Vietnamese cross-lingual bridge cleared the technical, licensing, and hardware constraints.
4. Installed VieNeu can technically accept a Qwen synthetic WAV and is the simplest possible Vietnamese bridge, but cross-language quality and identity preservation are unproven.
5. The architecture is a one-time factory plus existing production engine, not an attempt to replace VieNeu.

## Limitations

No model was installed, downloaded, or run. No CPU/RAM benchmark, seed reproducibility test, Vietnamese audition, or legal review occurred. Model cards/release terms can change. This is not legal advice.

## Decision

SYNTHETIC_REFERENCE_PATH_EXPERIMENTAL.

It is a valid research PoC only, not a production-approved brand-voice path. If the minimal audition fails, do not create a more complicated chain; choose directly permissioned custom reference audio.

## Recommended Phase 30I

One experiment only: in a fresh Python 3.12 environment, make at most three Qwen English synthetic identities, select the best clean 6–8 second WAV, then make one short Vietnamese VieNeu blind audition. Stop on quality or identity failure.

## Production Changes

NONE.

## Regression / Static Checks

git diff --check passed. No fake tests were added; this was documentary research.

