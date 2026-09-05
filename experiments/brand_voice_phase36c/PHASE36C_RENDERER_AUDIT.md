# Phase 36C — next Vietnamese renderer selection

## Decision boundary

Gwen is rejected for Candidate 03 migration: both the original and explicit `language="Vietnamese"` probes were English-like. VieNeu remains the frozen baseline/checkpoint, not a production target. Candidate 03 canonical assets and `BEST_KNOWN_BRAND_VOICE_CHECKPOINT` remain unchanged.

This is an audit only. No renderer assets were installed, downloaded, or run. No production files were edited.

## Local asset audit

No local checkout/model directory was found for IndexTTS2, VoxCPM2, Qwen3-TTS Base, VietVoice-TTS, or V-TTS. The usable frozen anchor remains:

- reference WAV: `experiments/brand_speaker_phase33c/baseline_anchor/BRAND_CANDIDATE_03_BASELINE/qwen_source.wav`
- exact English reference transcript: the Phase 33C canonical transcript
- checkpoint: `experiments/brand_voice_phase35b/BEST_KNOWN_BRAND_VOICE_CHECKPOINT/phase34_clip_c.wav`

## Candidate comparison

| Candidate | Vietnamese evidence / clone interface | Transcript | CPU / memory practicality on i9-13900H, 16 GB | Identity, continuity and control outlook | Setup risk / PoC decision |
|---|---|---|---|---|---|
| **VietVoice-TTS** | Vietnamese-first repository. Its documented clone call takes `reference_audio` and `reference_text`; it exposes speed, seed, accent, emotion, and a conservative cross-fade option. | Required for its documented clone path. Candidate 03's pristine WAV and exact English transcript form the exact reference pair; cross-lingual reference conditioning must be validated, not assumed. | CPU extras are explicitly supported through ONNX Runtime. Exact model size/RAM is not published in the inspected docs, so measure rather than assume. | Best evidence alignment for Vietnamese pronunciation plus reference-conditioned identity. Exposed controls make a narrow continuity/authority comparison possible, but claimed quality is not yet verified against Candidate 03. | Medium: new source install, but MIT license and direct CPU path. **Worth one small PoC.** |
| **V-TTS** | Vietnamese-native zero-shot clone with a dedicated Vietnamese phonemizer and a direct `clone_voice(text, reference_audio, output_path)` API. Docs specify a 3–10 s clean, single-speaker reference and say any reference language is accepted. | Not required by documented clone API. | Documented 74.8M parameters (~285 MB FP32); CPU-only benchmark claims RTF ~0.24–0.48 on an i5-14500. Comfortable on this machine if the claim holds. | It extracts identity plus style/prosody embeddings, so basic Candidate 03 retention is plausible. Authority and nuanced long-form prosody are the main uncertainty. | Low technical risk, but **CC BY-NC 4.0** prevents commercial production absent written permission. Good fallback research candidate, **not first PoC**. |
| **VoxCPM2** | Official model card lists Vietnamese among 30 supported languages. Direct clone accepts `reference_wav_path`; `prompt_text` is optional for prompt/continuation conditioning. It accepts natural-language control instructions. | Optional for cloning; useful with exact transcript for prompt conditioning. | 2B parameters, bfloat16, documented ~8 GB VRAM; official requirements specify CUDA 12/PyTorch 2.5. CPU-only is not a supported, memory-safe path on this 16 GB laptop. | Strongest potential for expressive speech, cloning, and semantic controls; 48 kHz output. | High footprint/runtime risk. **Do not PoC without GPU or a documented low-memory CPU path.** |
| **IndexTTS2** | Minimal official synth takes text and a reference `--voice` WAV. It has controllability features, but inspected official material does not establish Vietnamese support. | No transcript in documented minimal CLI. | CLI detects/uses CPU, but no reliable official CPU RAM/RTF for this laptop. Assets are not local. | Good potential in supported languages; Vietnamese intelligibility and identity transfer both unproven. | High language risk and restrictive model license. **Not worth a Vietnamese Candidate 03 PoC.** |
| **Qwen3-TTS Base (0.6B/1.7B)** | Strong interface: `ref_audio` + `ref_text` for ICL cloning; speaker-only mode trades away quality. Official language list has 10 languages and **does not include Vietnamese**. | Required for preferred ICL clone; optional only in lower-quality speaker-only mode. | Smaller than VoxCPM2, but it is not a credible Vietnamese model regardless of CPU feasibility. A new download would be needed. | Strong identity/contextual control in supported languages; Vietnamese is outside documented capability. | High language risk, especially after Gwen. **Reject for this Vietnamese PoC.** |

## Recommended next PoC — exactly one

**VietVoice-TTS CPU clone PoC.**

After explicit approval to install/download, generate exactly one short natural Vietnamese Candidate 03 clone from the canonical pristine reference WAV and exact transcript. Compare it blindly against the unchanged Phase 34 checkpoint on the same target text. Do not tune a grid, alter Candidate 03, or touch production.

This is the smallest high-information test because it is the only audited candidate that simultaneously documents Vietnamese-first synthesis, reference-WAV-plus-transcript cloning, CPU support, and controllable settings.

## Sources consulted (official project/model documentation)

- VietVoice-TTS README: Vietnamese clone API, CPU package option, controls, MIT license.
- V-TTS README: Vietnamese zero-shot clone interface, 74.8M CPU claim, reference constraints, CC BY-NC license.
- VoxCPM2 model card and source CLI: Vietnamese in 30 supported languages, 2B/BF16/~8GB VRAM, clone/prompt/control interface.
- IndexTTS2 official CLI and README: reference-WAV synthesis and CPU device detection.
- Qwen3-TTS official README/source: Base clone conditioning and official 10-language list excluding Vietnamese.
