# Phase 28E-A — Zero-Cost GPU Feasibility for Vietnamese Universal Emotion PoC

## PHASE 28E-A RESULT

### 1. Status

**PASS — research/design only.** No account was created, no model was downloaded, no notebook was built or run, and AIVoice was not modified.

### 2. Zero-Budget Constraint

`MAXIMUM BUDGET = 0 VND`.

This report contains no paid GPU, paid plan, paid credit, hardware-purchase, or training recommendation.

### 3. Free GPU Options

| Rank | Legitimate current option | Rating | Why |
| ---: | --- | --- | --- |
| 1 | **Kaggle Notebooks free GPU** | **GREEN** | Official documentation currently states one free Tesla P100, 29 GB RAM, 20 GB saved output, 12-hour GPU session, and a weekly GPU quota (30 hours or higher depending on demand). |
| 2 | **Google Colab free tier** | **YELLOW** | Free GPU/TPU access exists, but Google explicitly says resources, GPU type, and usage limits are neither guaranteed nor fixed. |
| 3 | **Lightning AI free credits** | **YELLOW** | Public free monthly credits can cover GPU time, but account/credit availability and storage limits make it less predictable than Kaggle. |

Hugging Face community GPU grants are not a reliable immediate PoC platform: a grant is discretionary, and current Spaces GPU access otherwise requires an upgrade/card. It is not in the execution ladder. [Kaggle notebook documentation](https://www.kaggle.com/docs/notebooks), [Kaggle GPU quota documentation](https://www.kaggle.com/docs/efficient-gpu-usage), [Colab FAQ](https://research.google.com/colaboratory/intl/en-GB/faq.html), [Lightning free tier](https://lightning.ai/pricing)

### 4. Best Free Platform

**Kaggle Notebooks free GPU.**

It is the strongest zero-cost first attempt because its published P100 allocation has 16 GB VRAM, 29 GB system RAM, an explicitly documented 12-hour session limit, 20 GB persistent notebook output, and an explicit weekly GPU quota. A 12–20 WAV inference exercise is small relative to that quota.

### 5. Expected Free GPU

| Platform | GPU / VRAM | RAM | Disk/session | Availability / quota |
| --- | --- | ---: | --- | --- |
| Kaggle | Tesla P100 / 16 GB | 29 GB | 20 GB saved `/kaggle/working`, plus session scratch | 12-hour session; weekly GPU quota commonly 30 hours, may vary |
| Colab Free | GPU not guaranteed; T4-class allocation can occur but is not promised | Variable | Ephemeral VM disk; no documented persistent allocation | Limits fluctuate; idle/session termination possible |
| Lightning free tier | Credit-selected GPU is provider/account dependent | Provider dependent | First 10 GB Drive free | Monthly free credits; availability and fit need checking before use |

Kaggle's official documents also mention T4s as platform hardware, but only promise a single free P100 to notebooks; therefore plan against **P100 16 GB**, not an assumed T4/L4. P100 supports FP16 but has no Tensor Cores, so it is expected to be slower than T4 for half-precision inference—not a blocker for 12 short files.

### 6. T4 16GB Feasibility

**GREEN for a low-VRAM inference-only PoC, conditional on skipping Qwen emotion text and using short single-sentence inputs.**

The actual source loads GPT, S2Mel, Wav2Vec2-BERT, MaskGCT semantic codec, CAMPPlus, and BigVGAN. With FP16 where the source supports it, their static model footprint is materially below 16 GB; short-input activation/cache headroom is still required. The optional Qwen classifier adds ~1.19 GB and should not be loaded for first testing. A T4/P100 16 GB is not a production guarantee, but is a credible first free experiment target.

### 7. Can Qwen Emotion Classifier Be Disabled?

**YES.**

The fork constructor only creates `QwenEmotion` when config key `qwen_emo_path` names an existing directory. `use_emo_text=True` then requires that object; shared audio (`emo_audio_prompt`) and explicit vectors (`emo_vector`) do not. A future low-VRAM configuration copy can omit/null `qwen_emo_path`; use `use_emo_text=False` and do not fetch the `qwen0.6bemo4-merge/` directory. This avoids the bundled `model.safetensors` of **1,192,135,096 bytes (~1.19 GB)** and does not alter the core speaker+audio/vector route.

### 8. Minimum-VRAM Architecture

Required for the first PoC:

- Vietnamese `gpt.pth`;
- `s2mel.pth`;
- Vietnamese `bpe.model`, config, `feat1.pt`, `feat2.pt`, and Wav2Vec statistics;
- Wav2Vec2-BERT feature encoder;
- MaskGCT **semantic codec only**;
- CAMPPlus speaker model;
- BigVGAN **generator only**;
- one speaker reference, one optional shared emotion reference, text, and WAV writer.

Excluded: Gradio/web UI, training code, DeepSpeed, custom CUDA kernel, Qwen emotion-text classifier, full MaskGCT acoustic/S2A/T2S assets, BigVGAN discriminators/optimizers, multiple engine instances, and multi-file parallel generation.

Use IndexTTS-2 FP16; BF16 is unnecessary. CPU offload/sequential movement is theoretically possible but not required for an initial 16 GB run and is not exposed as a supported one-switch mode in this fork. Do not modify or implement it yet.

### 9. VRAM Matrix

| VRAM | Rating | Inference-only conclusion |
| ---: | --- | --- |
| 8 GB | **RED** | Too little safe headroom for all required modules and activations. |
| 12 GB | **ORANGE** | May be forced with source changes/offload but not a credible free PoC baseline. |
| 16 GB | **GREEN** | Credible low-VRAM PoC target when Qwen text classifier is skipped and inputs stay short. |
| 24 GB | **GREEN** | Comfortable headroom; not required for this zero-cost plan. |

### 10. RAM & Disk Requirements

| Resource | Minimum | Recommended |
| --- | ---: | ---: |
| System RAM | 16 GB | 25–32 GB |
| Disk | 15 GB | 20 GB |

Kaggle's 29 GB RAM is suitable. The local 15 GiB laptop is an unreliable CPU/offload setting.

Core vetted assets without Qwen are roughly: 5.89 GB bundle less 1.19 GB Qwen, plus Wav2Vec2-BERT (~2.32 GB), MaskGCT semantic codec (~177 MB), CAMPPlus (~28 MB), and BigVGAN generator (~449 MB): roughly **7.7 GB raw model assets**. Environment/cache/transient copies justify 15 GB minimum and 20 GB recommended.

### 11. Free Session Survival Plan

Generate sequentially, saving each WAV immediately. After every successful file, atomically update `manifest.json` with status, input names, settings, timing, and output checksum. On reconnect, the runner reads the manifest and skips completed valid outputs. Package outputs after smoke tests and again after the full matrix. A disconnect after sample 7/12 therefore preserves 1–7 and resumes from 8.

Do not persist model weights to Google Drive. On Kaggle, retain only outputs/manifest/logs in the notebook's saved output; re-download models in a new session if necessary.

### 12. Emotion Control for First Test

**BOTH, in order: SHARED AUDIO first, then VECTOR.**

Shared emotion audio provides the clearest first test of cross-speaker transfer. Explicit vectors then test whether no donor recording is needed. Exclude text/Qwen mode initially because it adds model size and confounds Vietnamese emotion-classifier quality.

### 13. Three-Step Smoke Test

1. `speaker_A.wav` + no external emotion → confirm Vietnamese base cloning works.
2. `speaker_A.wav` + `emotion_sad.wav` → confirm a change is audible without identity collapse.
3. `speaker_B.wav` + the **same** `emotion_sad.wav` → test transfer and donor/speaker leakage.

Stop before the matrix on broken Vietnamese, no audible emotion change, identity collapse, donor-timbre leakage, unrecoverable OOM, or a resource requiring payment.

### 14. Full PoC Plan

After smoke success only, create 12 core files: A/B/C × neutral/happy/sad/angry. Keep one neutral target sentence, one reference per target speaker, one shared donor clip per non-neutral emotion, fixed generation settings, and one medium `emo_alpha`. Add three emotion-disabled neutral controls and retain the emotion donor as a non-target comparison control.

### 15. Free GPU Fallback Ladder

```text
Kaggle Free P100 GPU
        ↓ unavailable / unsuitable
Google Colab Free GPU
        ↓ unavailable / insufficient VRAM
Lightning monthly free-credit GPU
        ↓ unavailable / cannot stay inside 0 VND
Single local CPU smoke attempt
        ↓ fail
STOP PHASE 28
```

No paid option appears in this ladder.

### 16. CPU Last Resort

**ORANGE / low-confidence technical possibility only.** Skipping Qwen may let static weights fit within 16 GB system RAM, but PyTorch overhead, temporary allocations, current zram pressure, autoregressive GPT generation, diffusion S2Mel, and no optimized CPU graph make it risky. One short WAV may take **tens of minutes to hours**, or fail from memory/dependency issues. It is not a sensible primary path and must stop if it becomes operationally unreasonable.

### 17. Future Notebook Structure

```text
00 — GPU / RAM / disk check
01 — install pinned dependencies
02 — download approved checkpoint subset
03 — download required auxiliary assets
04 — verify hashes / revisions
05 — load LOW-VRAM engine
06 — upload references
07 — smoke test
08 — universal emotion transfer test
09 — full 12-sample matrix
10 — package outputs
```

### 18. Exact Required Downloads

Required:

- From `dinhthuan/index-tts-2-vietnamese`: `config.yaml`, `gpt.pth`, `s2mel.pth`, `bpe.model`, `feat1.pt`, `feat2.pt`, `wav2vec2bert_stats.pt`.
- `facebook/w2v-bert-2.0` model weights/config.
- `amphion/MaskGCT` `semantic_codec/model.safetensors` only.
- `funasr/campplus` `campplus_cn_common.bin`.
- `nvidia/bigvgan_v2_22khz_80band_256x` `config.json` and `bigvgan_generator.pt`.

Skip: `qwen0.6bemo4-merge/`, BigVGAN discriminators/optimizers, and unrelated MaskGCT model families. Record final exact revisions and SHA-256 files before running.

### 19. Privacy Plan

Upload only intentionally selected test inputs: `speaker_A.wav`, `speaker_B.wav`, `speaker_C.wav`, and optional generic `emotion_happy.wav`, `emotion_sad.wav`, `emotion_angry.wav` recorded with explicit donor permission. Upload no AIVoice source, production database, saved voice library, API keys, or unrelated/private recordings.

### 20. Go / No-Go

#### FREE-GO-CONDITIONAL

A realistic zero-cost path exists: Kaggle's free P100 is sufficient in a Qwen-disabled low-VRAM mode. It remains conditional on obtaining a free GPU session, completing asset/provenance checks, and confirming actual peak VRAM before downloading the full experiment assets.

### 21. Phase 28E-B Recommendation

Design/build the isolated free-GPU notebook next, with explicit user approval before account use, model download, or reference upload. It must pin assets, default to Qwen-disabled Mode C, save per-sample state, and stop on the stated failure conditions.

### 22. Production Changes

**NONE.** Only this report was created. Stop and wait for review.
