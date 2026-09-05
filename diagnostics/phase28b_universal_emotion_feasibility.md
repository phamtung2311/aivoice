# Phase 28B — Universal Emotion Model & Hardware Feasibility

## 1. Status

PASS as a research-only audit. No model weights or dependencies were installed, no production behavior was changed, and no candidate is recommended for installation on this laptop yet.

## 2. Actual Machine Hardware

| Item | Verified result |
| --- | --- |
| OS / architecture | Linux, x86_64 |
| CPU | Intel Core i9-13900H, 14 physical cores / 20 logical CPUs, 5.4 GHz maximum |
| Relevant instructions | AVX2, FMA, AVX-VNNI; no AVX-512 reported |
| RAM | 15 GiB total; about 2.4 GiB available during audit |
| Swap | 30.5 GiB zram; 9.7 GiB already used |
| GPU | Intel Iris Xe integrated GPU; no NVIDIA CUDA device |
| Disk | 353 GiB free on the AIVoice filesystem |
| Python | 3.14.7 |
| PyTorch | not installed in AIVoice `.venv` |
| ONNX Runtime | 1.29.0 installed; CPU path works for current VieNeu |

The CPU is strong for ordinary CPU workloads, but memory headroom is currently poor for PyTorch-transformer TTS. BF16 is not a useful deployment assumption here: no PyTorch exists in the environment, AVX-512/BF16 is not reported, and the candidates’ official fast paths target CUDA.

## 3. Product Requirement Restatement

The requirement is not a laugh/sigh marker. A future engine must preserve an arbitrary speaker identity while independently applying reusable speaking style or emotion: `speaker A + sad`, `speaker B + sad`, and so on, without recording a separate emotional reference for each saved voice.

## 4. Candidate Models

| Candidate | Current verified finding |
| --- | --- |
| Chatterbox Multilingual V3 | Official 500M zero-shot cloning model with 23 named languages, but Vietnamese is absent from the official language list. It has an `exaggeration`/CFG-style expressiveness control, not documented speaker/emotion disentanglement. MIT license. |
| Qwen3-TTS 0.6B / 1.7B | Official Base variants clone from roughly 3 seconds; CustomVoice accepts instructions for nine built-in timbres; VoiceDesign accepts natural-language instructions. Official languages exclude Vietnamese. Critically, the documented Base clone call does not expose an instruction; VoiceDesign-then-Clone creates a new designed voice, not `existing arbitrary clone + new emotion` per request. Apache-2.0. |
| Gwen-TTS 0.6B | Vietnamese-focused Qwen3-TTS 0.6B fine-tune (about 1,000 hours) with few-second reference cloning and MIT license. Official quickstart requires CUDA 12.4, NVIDIA driver, ≥4 GiB VRAM, BF16, and FlashAttention 2. Its published clone call has no style/instruction argument, so survival of Qwen instruction control is unverified. |
| IndexTTS-2 / 2.5 | The strongest architecture match: separate timbre prompt and emotion prompt, with emotion text, vector, or audio-reference controls. Official 2.5 language listing is Chinese, English, Japanese, Spanish, and Arabic; Vietnamese is absent. Official acceleration/deployment guidance is CUDA/NVIDIA-centric. License must be reviewed separately before commercial use. |
| Fish Audio S2 Pro | Current S2 Pro is a 4B slow AR + 400M fast AR model, claims 50+ languages, rapid cloning, and free-form inline instruction tags (e.g. emotion/prosody). Its official license is Fish Audio Research License, not a permissive commercial license. Official serving recipe references an A800 80GB GPU. Vietnamese is not explicitly listed in the reviewed official material. |
| CosyVoice 3 | Current 0.5B generation, zero-shot/cross-lingual cloning and expressive voice-cloning research. Officially documented language coverage is Chinese, English, Japanese, Korean, German, Spanish, French, Italian, and Russian; Vietnamese is absent. No verified independent emotion controller for arbitrary cloned speakers was found. |

Primary evidence: [Chatterbox official README](https://github.com/resemble-ai/chatterbox/blob/master/README.md), [Qwen3-TTS official README](https://github.com/QwenLM/Qwen3-TTS/blob/main/README.md), [Gwen-TTS official repository](https://github.com/ggroup-ai-lab/gwen-tts), [IndexTTS official repository](https://github.com/index-tts/index-tts), [IndexTTS 2.5 technical report](https://index-tts.github.io/index-tts2-5.github.io/), and [Fish Speech official release](https://github.com/fishaudio/fish-speech/releases).

## 5. Vietnamese Support Matrix

| Model | Classification | Reason |
| --- | --- | --- |
| Chatterbox Multilingual V3 | UNSUPPORTED | Vietnamese is not in the official 23-language list. |
| Qwen3-TTS Base / CustomVoice / VoiceDesign | UNSUPPORTED | Vietnamese is not among the official 10 languages. |
| Gwen-TTS 0.6B | COMMUNITY-FINETUNED | Vietnamese is its stated primary fine-tune target; it is not an official Qwen language release. |
| IndexTTS-2 / 2.5 | UNSUPPORTED | Official languages exclude Vietnamese. |
| Fish Speech S2 Pro | CROSS-LINGUAL ONLY | Broad 50+/80+ language claim, but Vietnamese was not explicitly verified in official language material reviewed. |
| CosyVoice 3 | UNSUPPORTED | Official 9-language list excludes Vietnamese. |

## 6. Emotion Architecture Matrix

Control types: 0 none, 1 text/semantic only, 2 discrete paralinguistic tags, 3 emotion reference audio, 4 numeric vectors, 5 natural-language instructions, 6 speaker/emotion disentanglement.

| Model | Types | Distinction |
| --- | --- | --- |
| Chatterbox V3 | 1, possibly scalar expressiveness | Exaggeration is not a reusable named emotion or independent style channel. |
| Qwen3-TTS Base | 1 | Clone only; no verified instruction control on arbitrary cloned voice. |
| Qwen3-TTS CustomVoice / VoiceDesign | 5 | Instructions apply to built-in timbres or designed voice, not proven arbitrary clone + independent emotion. |
| Gwen-TTS | 1 | Published API shows cloning and sampling controls, not emotion instruction. |
| IndexTTS-2.5 | 3, 4, 5, 6 | Explicit timbre/emotion separation; best research architecture, blocked by Vietnamese/hardware. |
| Fish Speech S2 Pro | 2, 5 | Free-form tags are expressive controls, but no verified formal speaker/emotion disentanglement. |
| CosyVoice 3 | 1, 3 | Expressive/emotion cloning is reference-dependent; no verified reusable independent style controller. |

## 7. Hardware Feasibility Matrix

| Model | Weight / runtime implication | Laptop rating | Estimated CPU category |
| --- | --- | --- | --- |
| Chatterbox V3 | 500M; ~2GB FP32 weights plus PyTorch/runtime | ORANGE | 5–20× realtime estimate; CPU code path exists but Vietnamese blocks product use. |
| Qwen3-TTS 0.6B | official repository about 2.52GB total / 1.83GB model file; PyTorch runtime required | ORANGE | 5–20× realtime estimate; CPU/quantized paths are community work, not official deployment path. |
| Qwen3-TTS 1.7B | several GB of weights plus tokenizer/codec/runtime | RED | extremely slow / memory-tight without CUDA. |
| Gwen-TTS 0.6B | CUDA/BF16/FlashAttention official requirement | RED | no supported CPU path documented. |
| IndexTTS-2 / 2.5 | multi-component PyTorch stack; official acceleration requires NVIDIA CUDA/TensorRT | RED | impractical. |
| Fish Speech S2 Pro | 4.4B total AR parameters; GPU serving documentation uses A800 80GB | RED | impractical. |
| CosyVoice 3 | ~0.5B but PyTorch stack; no verified CPU deployment recipe | ORANGE | 5–20× realtime estimate; Vietnamese still blocks product. |

Quantization may lower stored weight memory but does not remove codec, activation, tokenizer, framework, or CPU latency costs. It is therefore not enough to change any RED verdict on this machine.

## 8. Full Scoring Matrix

Scores are 0–5; a Vietnamese or licensing blocker overrides a high total.

| Model | VI | Clone | Speaker | Emotion | Independence | Range | CPU | RAM | Maturity | Offline | Integration | Hardware |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| Chatterbox V3 | 0 | 4 | 4 | 2 | 1 | 2 | 2 | 2 | 4 | 4 | 3 | ORANGE |
| Qwen3-TTS 0.6B Base | 0 | 4 | 4 | 1 | 0 | 1 | 2 | 2 | 4 | 4 | 3 | ORANGE |
| Qwen3-TTS 1.7B family | 0 | 4 | 4 | 4 | 1 | 4 | 0 | 1 | 4 | 3 | 2 | RED |
| Gwen-TTS 0.6B | 4 | 4 | 4 | 1 | 0 | 1 | 0 | 1 | 2 | 4 | 3 | RED |
| IndexTTS-2.5 | 0 | 4 | 5 | 5 | 5 | 5 | 0 | 0 | 3 | 3 | 1 | RED |
| Fish Speech S2 Pro | 2 | 4 | 4 | 5 | 2 | 5 | 0 | 0 | 3 | 3 | 1 | RED |
| CosyVoice 3 | 0 | 4 | 4 | 3 | 2 | 3 | 1 | 2 | 4 | 4 | 2 | ORANGE |

## 9. Top Three Candidates

1. **IndexTTS-2.5**: closest technical architecture to the product requirement because it explicitly separates a timbre prompt from an emotion prompt and offers vector/text/reference control. It is research-relevant, not a Vietnamese or laptop candidate.
2. **Fish Speech S2 Pro**: strongest broad expressive-control claim and rapid cloning, but very large, research-licensed, and its Vietnamese coverage is not explicitly verified here.
3. **Gwen-TTS 0.6B**: closest Vietnamese cloning candidate. It is not currently an emotion-system candidate because its public API/docs do not demonstrate arbitrary clone + reusable emotion instruction.

## 10. Best Fit Now

None meets the product requirement on this exact laptop. If forced to choose the least unsuitable technical trial, Chatterbox has a CPU path and 500M scale, but Vietnamese is an explicit hard blocker and it must not be selected for AIVoice production.

## 11. Best Quality With Stronger GPU

**Fish Speech S2 Pro**, conditional on a separate Vietnamese quality and licensing evaluation. It offers the broadest documented natural-language expression controls and cloning, but requires serious CUDA-class hardware and does not establish formal emotion/speaker disentanglement.

## 12. Major Technical Risks

- **RAM / CPU time:** current memory headroom is too low; zram use signals immediate swap pressure for PyTorch models.
- **Dependencies:** Gwen requires CUDA/FlashAttention; IndexTTS acceleration is CUDA/TensorRT; Fish’s preferred server path is GPU-oriented.
- **Vietnamese:** all official candidates except Gwen lack documented Vietnamese support; Fish’s coverage claim is insufficient evidence of quality.
- **Voice drift:** Qwen VoiceDesign-then-Clone changes the reference persona rather than applying a fresh emotion to the same saved voice.
- **Emotion quality:** tags/instructions can be paralinguistic or semantic rather than reusable style control; human listening remains mandatory.
- **Quantization:** may save storage/RAM, but can affect expressiveness/cloning and cannot establish a supported CPU stack.
- **License:** Fish Audio Research License needs product/legal review; Index model terms need a separate review.

## 13. Possible Future AIVoice Integration

Do not replace VieNeu. A later adapter seam could keep the existing engine for standard Vietnamese TTS and use a second isolated expressive-engine adapter for explicitly selected experiments. The conceptual request would carry text, voice identity, optional emotion, and strength; the adapter must declare whether it truly supports speaker/style separation. Existing saved voice profiles must not be silently reused across incompatible engines.

## 14. Phase 28C Recommendation

Do not install a model on this laptop. The evidence supports decision **D**: no reviewed candidate currently satisfies Vietnamese + arbitrary cloned speaker + independently reusable emotion + usable local hardware. The highest-value future proof-of-concept, only after access to a suitable NVIDIA GPU and explicit approval, is **IndexTTS-2.5** as an architecture experiment; it must first clear Vietnamese support, so it is not an AIVoice product migration recommendation.

## 15. Production Changes

NONE.
