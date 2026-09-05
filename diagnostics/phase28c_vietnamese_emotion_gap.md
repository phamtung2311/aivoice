# Phase 28C — Vietnamese Universal Emotion Gap Investigation

## PHASE 28C RESULT

### 1. Status

**PASS — research-only investigation complete.** No production code, model, dependency, checkpoint, API, or TTS behavior was changed. No multi-GB model was downloaded or benchmarked.

The current gap is real: no verified candidate simultaneously provides strong Vietnamese, arbitrary cloned-speaker identity, reusable independent emotion/style, and realistic CPU-only local operation on this laptop.

### 2. Gwen-TTS Deep Findings

Gwen is not an unknown Qwen variant. Its public checkpoint configuration identifies it as `Qwen3TTSForConditionalGeneration`, `tts_model_size: 0b6`, and `tts_model_type: base`, derived from **`Qwen/Qwen3-TTS-12Hz-0.6B-Base`**. The public model card says it was fine-tuned on approximately 1,000 hours of Vietnamese TikTok material. Its configuration includes a Vietnamese language ID (`vietnamese: 2068`) and no built-in speaker table, consistent with the Base clone architecture. [Gwen model card](https://huggingface.co/g-group-ai-lab/gwen-tts-0.6B)

The public repository contains inference code and metadata, but no training implementation. Therefore the following are **UNKNOWN**, not inferred: full fine-tune versus LoRA/adapters, which modules were frozen, and whether codec, speaker conditioning, text components, or decoder were updated.

The public `inference.py` loads `Qwen3TTSModel` and calls `generate_voice_clone(text, ref_audio, ref_text, ...)`. It exposes sampling settings only. The `language` argument is even commented out in that wrapper. There is no instruction/style argument, no instruction preprocessing, and no instruction embedding path in the published Gwen inference route.

### 3. Hidden Instruction Hypothesis

**DISPROVED for the public Gwen checkpoint and its supported Base clone API.**

The relevant upstream Base method is `generate_voice_clone(...)`; its documented arguments are text, language, reference audio/text, clone prompt controls, and ordinary generation options. It does not document a semantic `instruct` argument. Passing generic `**kwargs` through generation is not evidence of an undisclosed instruction-conditioning channel.

Qwen exposes instruction text in different model modes, not in Base cloning: `generate_custom_voice(..., speaker=..., instruct=...)` and `generate_voice_design(..., instruct=...)`. Qwen maintainers’ own discussions requesting `instruct` for `generate_voice_clone` corroborate that the requested arbitrary-clone-plus-instruction feature is absent rather than merely omitted by Gwen's UI. [Qwen3-TTS API and model-mode documentation](https://github.com/QwenLM/Qwen3-TTS/blob/main/README.md)

Thus there is no demonstrated seam of the form “Gwen wrapper omits instruction but the underlying Base checkpoint accepts it.” Recovering a hidden instruction call is not a credible Phase 28D path.

### 4. Qwen3-TTS Architecture Findings

| Qwen mode | Arbitrary reference cloning | Built-in/designed speaker | Natural-language instruction | Existing arbitrary clone + new emotion instruction | Vietnamese official support |
| --- | --- | --- | --- | --- | --- |
| Base | Yes | No fixed speaker catalogue | No documented semantic instruction path | **No** | No |
| CustomVoice | No arbitrary clone path | Yes, named built-in speakers | Yes | No: instruction applies to built-in speaker mode | No |
| VoiceDesign | Not an existing-reference clone mode | Creates a new designed voice | Yes | No: it designs a voice; it does not preserve an arbitrary existing clone | No |

The important distinction is that VoiceDesign can create a voice with an instructed character, but that does not establish `saved arbitrary Voice A + sad → same Voice A, sad delivery`. No upstream Qwen mode reviewed here provides that exact combination at inference time.

### 5. Can Qwen Become Vietnamese + Universal Emotion?

**POSSIBLY, but not through the current Gwen Base checkpoint alone.**

Simple continued Vietnamese fine-tuning of Base can improve Vietnamese cloning, as Gwen demonstrates, but Base has no verified reusable instruction/emotion interface to preserve. Starting from an expressive Qwen mode would require a deliberately designed adaptation, not a wrapper change.

The most credible theoretical recipe is **multi-task adaptation**: keep original expressive/instruction-conditioned data in training while adding licensed Vietnamese speech, including expressive Vietnamese recordings and aligned style descriptions. This reduces catastrophic forgetting risk. A Vietnamese-only neutral corpus is useful for pronunciation and linguistic coverage but does not prove that semantic emotion transfers to Vietnamese. A LoRA/adapters approach while freezing style-sensitive components is plausible as an experiment, but not established as sufficient.

Emotion-labelled recordings are needed to validate reusable emotions; richer instruction-captioned multi-speaker data is needed for broad styles such as warm, storytelling, serious, and confident. Synthetic emotional audio may help with augmentation or bootstrapping, but cannot replace licensed human Vietnamese expressive speech: it can reproduce source-model artifacts and gives circular emotion labels.

### 6. Vietnamese Dataset Findings

| Resource | Approximate scope | Labels / speakers | License and availability | TTS suitability |
| --- | --- | --- | --- | --- |
| VLSP-EMO | About 5 hours | One speaker; neutral, happy, sad, angry | Released through the VLSP task; commercial rights must be confirmed separately | Useful small emotion proof/evaluation set; far too small and single-speaker for universal emotion training |
| VLSP-NEU | About 4 hours | Another speaker, neutral | VLSP task resource; commercial rights unresolved in reviewed material | Neutral companion material only |
| VNEMOS | Vietnamese speech-emotion-recognition resource | Emotion annotation reported; audited hours/speaker/licence not established here | Availability/rights require source-level confirmation | Not automatically TTS-ready; designed for recognition, not necessarily clean text-audio synthesis pairs |
| viVoice / large ordinary Vietnamese corpora | Large plain Vietnamese speech resources | Not an expressive-label resource | Licence and release terms vary by corpus | Useful for text/voice coverage, not independent emotion learning |
| Gwen's stated TikTok corpus | About 1,000 hours claimed | Not publicly documented as a licensed emotional multi-speaker corpus | Rights, labels, and reproducible access unknown | Cannot be treated as an available commercial training set |

VLSP explicitly describes the small emotion and neutral corpora above. [VLSP emotional-speech task resource](https://vlsp.org.vn/vi/node/56)  The central missing asset is a commercially cleared, multi-speaker Vietnamese corpus whose audio, transcript, speaker identity, and reusable emotion/style label are all reliable.

### 7. Existing Vietnamese Expressive Models Found

Only these are serious enough to retain:

- **Gwen-TTS 0.6B:** credible Vietnamese arbitrary cloning candidate, but no verified independent emotion control.
- **Community IndexTTS2 Vietnamese adaptation:** source exposes separate speaker prompt plus emotion audio/vector/text arguments. It is the closest discovered architectural match, but model quality, checkpoint provenance, licence, and claimed retention of English/Chinese have not been independently reproduced. [Vietnamese IndexTTS2 adaptation source](https://github.com/iamdinhthuan/index-tts-finetune-vietnamese)
- **LEMAS-TTS (0.3B):** multilingual ONNX-oriented zero-shot TTS listing Vietnamese among supported languages. No documented reusable independent emotion channel was found, so it does not satisfy the target requirement. [LEMAS-TTS model card](https://huggingface.co/LEMAS-Project/LEMAS-TTS)
- **ViZipVoice:** Vietnamese cloning/community direction, but no verified arbitrary-speaker-plus-independent-emotion interface.
- **Vietnamese emotion-conditioned VITS research:** evidence of emotional Vietnamese synthesis research, but no verified production-ready universal cloning checkpoint.

### 8. IndexTTS Vietnamese Adaptation

**HARD.** It is materially more concrete than starting from scratch, but not a one-click fine-tune.

The community Vietnamese IndexTTS2 source includes Vietnamese BPE/tokenizer training, preprocessing, semantic/acoustic feature extraction, prompt-target pairing, and GPT fine-tuning. Its checked configuration has distinct speaker and emotion conditioning modules and its inference path accepts `spk_audio_prompt`, `emo_audio_prompt`, `emo_alpha`, and optional Qwen-derived `emo_text`. This is architectural evidence that speaker and emotion can be supplied separately.

However, source presence does not prove universal identity preservation on Vietnamese. It requires audited weights, compatible tokenizer/config/checkpoints, clean Vietnamese aligned data, GPU training, listening tests, speaker-similarity tests, emotion-recognition/human tests, and commercial licence clearance. The public source calls for CUDA and uses a multi-component GPT + semantic codec + S2Mel + BigVGAN stack. It should not be conflated with an audited IndexTTS-2.5 Vietnamese implementation.

### 9. Small Model Findings

| Candidate | Scale / deployment direction | Why it matters | Requirement gap |
| --- | --- | --- | --- |
| LEMAS-TTS | 0.3B, ONNX-oriented | Credible small multilingual/Vietnamese local-TTS lead | No verified reusable emotion/style controller |
| NeuTTS-2E | Small expressive model, quantized/GGUF direction | Shows sub-1B expression is possible | English-oriented fixed speaker set; not arbitrary Vietnamese cloning | 
| VieNeu V3 Turbo | Existing compact ONNX production engine | Works locally and has Vietnamese quality | Native non-verbal cues are not universal emotion control |
| Gwen / Qwen 0.6B | Sub-1B model family | Vietnamese cloning (Gwen) / research base | CUDA/PyTorch-oriented; no Base emotion interface |

Universal emotion does not inherently require multi-billion parameters, but no credible sub-1B candidate reviewed combines the four AIVoice requirements today. [NeuTTS project](https://github.com/neuphonic/neutts)

### 10. Local Inference Feasibility

On the verified i9-13900H / 15 GiB RAM / Intel Iris Xe / no-CUDA laptop:

- **Production now:** VieNeu remains the only verified practical local engine.
- **Potential later local trial:** a small ONNX model such as LEMAS might be technically testable after a separate Vietnamese-quality and licensing audit, but it does not solve emotion.
- **Not realistic now:** Gwen/Qwen, IndexTTS, and Fish-style expressive stacks are PyTorch/CUDA-oriented and are unsafe deployment assumptions with current RAM headroom and no NVIDIA GPU.

### 11. Training Feasibility

This laptop cannot reasonably train or fine-tune a universal expressive system. Its integrated GPU offers no CUDA path, available memory is already constrained, and the relevant training stacks assume CUDA.

Training elsewhere then exporting/quantizing locally is **plausible in principle**, but architecture dependent:

- A narrow LoRA/prototype experiment generally needs a modern NVIDIA GPU with roughly **24–48 GiB VRAM** and days of iteration.
- A Vietnamese expressive multi-task adaptation that tries to retain existing language/style behavior is more realistically **48–80 GiB VRAM**, several days to weeks, substantial checkpoint/cache storage, and a curated multi-speaker corpus. This is **HIGH** cost/risk for one developer, though not impossible with rented GPU access.
- Dataset storage should be planned from tens to hundreds of GiB once raw audio, features, cache, validation sets, and checkpoints are retained.

No exact rental price is stated because duration, GPU availability, dataset size, and experiment failures dominate cost.

### 12. ONNX / INT8 / OpenVINO Potential

| Architecture | Classification | Reason |
| --- | --- | --- |
| VieNeu V3 Turbo | **ONNX FRIENDLY** | Existing production route already proves this |
| LEMAS-TTS | **ONNX FRIENDLY** | Project/model documentation explicitly targets ONNX-class deployment; emotion gap remains |
| Qwen/Gwen autoregressive TTS + codec | **POSSIBLE BUT COMPLEX** | Autoregressive loops, custom generation, codec stages, and dynamic cache make a complete CPU ONNX route non-trivial |
| IndexTTS multi-component stack | **POOR FIT** | GPT generation, semantic codec, S2Mel, BigVGAN, and emotion components would require a multi-model export/validation project |
| Fish Speech | **POOR FIT** | Large autoregressive components and GPU-oriented serving make local CPU export a poor product bet |

INT8 reduces weight memory, not the total inference, codec, activation, control-flow, or quality-validation burden. OpenVINO may improve some ONNX components but does not solve missing Vietnamese emotion data or speaker/style disentanglement.

### 13. VieNeu External Emotion Controller

**BLOCKED.** The audited VieNeu V3 Turbo integration accepts text, reference conditioning, and ordinary sampling controls. It exposes no input for externally predicted pitch contour, durations, energy, pauses, or prosody embeddings. An external controller cannot make VieNeu consume controls that its inference interface and model path do not accept.

Punctuation, speed, and native `[cười]`/`[thở dài]`-type cues may remain optional presentation tools, but they do not satisfy the universal-emotion requirement.

### 14. Ranked Technical Paths

| Rank | Path | Feasibility | Vietnamese / universal-emotion potential | Hardware / difficulty / risk |
| ---: | --- | --- | --- |
| 1 | **C — Adapt IndexTTS emotion architecture to Vietnamese** | HARD | High potential; source demonstrates separate conditioning seam | External GPU required; community checkpoint/licence/quality risks |
| 2 | **B — Fine-tune expressive Qwen for Vietnamese** | HARD to research-scale | High potential only with deliberate multi-task expressive training | External 48–80 GiB class GPU and licensed expressive data; high forgetting risk |
| 3 | **F — Wait for a future model/hardware** | Technically safest | Unknown timing; could deliver a stronger supported Vietnamese model | Lowest engineering risk, highest product-delay risk |
| 4 | **D — Fish/CosyVoice/other expressive model** | Moderate research feasibility | Expression promising, Vietnamese and identity-independence not verified | Heavy hardware, support/licence risk |
| 5 | **E — External VieNeu emotion controller** | BLOCKED | Cannot meet target without a prosody-conditioning input | Interface/architecture blocker |
| 6 | **A — Recover hidden Gwen instruction capability** | DISPROVED for published Base clone route | None evidenced | Wrong architectural assumption |

### 15. Most Promising Path

**Path C — a carefully isolated IndexTTS Vietnamese adaptation evaluation.**

It is the only discovered route with direct code-level evidence of independently supplied speaker and emotion inputs alongside a Vietnamese adaptation workflow. This is a research lead, not an integration recommendation and not permission to replace VieNeu.

### 16. What Would Be Required

1. Obtain explicit permission to use a CUDA GPU environment; keep it isolated from AIVoice production.
2. Audit the community checkpoint's provenance, exact upstream version, licence and commercial restrictions before any use.
3. Build a rights-cleared Vietnamese dataset plan: clean transcript/audio pairs, multiple identities, and deliberate neutral/happy/sad/angry/other expressive recordings; do not rely on SER-only data.
4. Preserve speaker and emotion channels in the training/inference design; do not train a reference-dependent emotional clone and call it universal.
5. Define a small controlled evaluation: at least several unseen reference speakers crossed with several requested emotions, scored by blinded human listeners for both identity preservation and perceived emotion.
6. Only after that succeeds, evaluate export, quantization, latency, RAM, and a non-invasive adapter boundary. Existing VieNeu voices must never be silently treated as compatible with a second engine.

### 17. Phase 28D Recommendation

**C. Design an IndexTTS Vietnamese adaptation experiment.**

Do not execute it yet. The next phase should first produce an experiment specification covering asset/licence audit, a small external-GPU budget, data provenance, control matrix, success thresholds, and rollback/no-production-integration boundaries.

### 18. Production Changes

**NONE.** Only this research report was created. Stop here and await review.
