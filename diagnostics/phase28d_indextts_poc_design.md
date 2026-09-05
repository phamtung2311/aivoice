# Phase 28D — Vietnamese IndexTTS Universal Emotion Proof-of-Concept Design

## PHASE 28D RESULT

### 1. Status

**PASS — design and provenance audit complete.** This phase did not install IndexTTS, download weights, train, rent a GPU, or alter AIVoice production behavior.

### 2. Vietnamese IndexTTS Project Audit

`iamdinhthuan/index-tts-finetune-vietnamese` is a public community project that is simultaneously:

- **A:** source code;
- **B:** a training/adaptation recipe (metadata → Vietnamese BPE → preprocessing → GPT fine-tuning);
- **C:** inference-capable Vietnamese adaptation source; and
- **D:** a public Hugging Face Vietnamese checkpoint bundle.

It is not yet a **verified complete reproducible adaptation**: the repository documents a workflow and a checkpoint, but does not provide auditable training-data provenance, a released training run, a reproducible evaluation set, or independent quality evidence. It is based on **IndexTTS-2**, not IndexTTS-2.5. [Community repository](https://github.com/iamdinhthuan/index-tts-finetune-vietnamese), [checkpoint model card](https://huggingface.co/dinhthuan/index-tts-2-vietnamese)

### 3. Checkpoint Availability

**AVAILABLE — but not yet approved for use.** The public model is `dinhthuan/index-tts-2-vietnamese`, marked as a fine-tune of `IndexTeam/IndexTTS-2`; it is neither gated nor disabled. The listed bundle is **5,891,410,195 bytes (~5.89 GB)**.

| Component | Exact public filename | Approx. size | Role |
| --- | --- | ---: | --- |
| Vietnamese GPT | `gpt.pth` | 1.74 GB | IndexTTS2 semantic/autoregressive generator |
| S2Mel | `s2mel.pth` | 1.20 GB | Acoustic generation stage |
| Qwen emotion model | `qwen0.6bemo4-merge/model.safetensors` | 1.19 GB | Optional text-to-emotion-vector classification |
| Vietnamese BPE | `bpe.model` | 0.43 MB | Text tokenizer |
| Emotion/speaker matrices | `feat1.pt`, `feat2.pt` | <0.5 MB | Vector-emotion support |
| Statistics/config | `wav2vec2bert_stats.pt`, `config.yaml` | small | Feature normalization/configuration |

Initialization also fetches external dependencies named in source: `facebook/w2v-bert-2.0`, `amphion/MaskGCT` semantic codec, `funasr/campplus`, and `nvidia/bigvgan_v2_22khz_80band_256x`. Their versions are not pinned by checksum in the Vietnamese model card, so the exact final runtime download size is **not fully determined** from the checkpoint bundle alone.

### 4. Provenance & License Risk

**HIGH RISK for commercial/product use; PARTIALLY CLEAR for an isolated research PoC.**

| Item | Audit result |
| --- | --- |
| Checkpoint author/host | Publicly uploaded by Hugging Face user `dinhthuan` |
| Claimed base | `IndexTeam/IndexTTS-2` |
| Training dataset | Not documented with source, rights, speakers, or consent |
| Training procedure | High-level recipe only; no audited run artifacts |
| GitHub code licence | Repository API reports no declared licence |
| Hugging Face card tag | Apache-2.0, but the card itself says commercial use requires permission from IndexTTS authors |
| Upstream model terms | Require separate review; official materials have carried special model-use terms/requests for commercial authorization |
| Releases/signing | No GitHub releases; reviewed recent commits were unsigned and repository history is short |

The apparent Apache tag must not be taken as commercial clearance for derivative weights or training data. The upstream licence question is publicly documented as ambiguous, and the community checkpoint does not document data provenance. [Upstream licence discussion](https://github.com/index-tts/index-tts/issues/228), [Vietnamese model card limitations](https://huggingface.co/dinhthuan/index-tts-2-vietnamese)

### 5. Emotion Interface

The source has genuinely distinct inputs, but this is **partially disentangled**, not proven universal.

```text
speaker reference (spk_audio_prompt)
  → 15-second maximum waveform
  → Wav2Vec-derived speaker condition + reference mel/style/prompt condition
  → GPT and S2Mel

emotion audio (emo_audio_prompt)
  → separate 15-second maximum waveform
  → Wav2Vec-derived emotion condition
  → GPT.merge_emovec(speaker_condition, emotion_condition, alpha=emo_alpha)
  → GPT generation
```

The `emo_vector` route uses a fixed eight-axis representation ordered `[happy, angry, sad, afraid, disgusted, melancholic, surprised, calm]`. The source selects emotion-matrix rows relative to the target speaker style unless random mode is enabled, then combines that vector with the speaker-derived condition. `use_emo_text`/`emo_text` is not a free-form TTS instruction: an included Qwen 0.6B classifier turns supplied text into that eight-axis vector. When vector/text mode is active, the implementation disables a separate emotion-audio prompt and uses the speaker reference as the audio condition.

Therefore two parameters do not prove identity-safe transfer. The exact cross-speaker behavior must be measured.

### 6. Universal Emotion Feasibility

**PLAUSIBLE.**

The shared-emotion-audio pathway is architecturally capable of `speaker A + emotion reference X` and separately `speaker B + the same emotion reference X`. The vector pathway can request sadness without an emotional audio recording for each speaker. Neither route has Vietnamese identity-preservation evidence for unseen references, so “universal” remains an experimental hypothesis.

### 7. Supported Emotion Modes

| Mode | Supported by source | Exact mechanism / limitation |
| --- | --- | --- |
| Text | Yes, indirectly | `emo_text` is classified by bundled Qwen into an 8-axis vector; it is not direct `emotion_text="sad"` semantic conditioning. Vietnamese behavior of that classifier is unvalidated. |
| Vector | Yes | Real eight-value vector in fixed order; no invented named vectors. Source limits total strength to 0.8 and applies per-emotion bias. |
| Shared emotion audio | Yes | `emo_audio_prompt` can differ from `spk_audio_prompt`; one donor clip can be reused across A/B/C. Identity leakage is a mandatory test. |
| Strength | Yes | `emo_alpha` 0.0–1.0 blends external audio emotion; for vector/text it scales the vector before inference. |

For the initial PoC, use **Mode C first**, then **Mode B** if Mode C passes leakage. Mode A is optional and should not be judged until Qwen emotion classification on Vietnamese is separately validated.

### 8. Speaker × Emotion PoC Matrix

Use three previously unseen, clean Vietnamese speaker references (A, B, C), each distinct in acoustics. Use this same emotionally neutral text in every core sample:

> Hôm nay chúng ta sẽ cùng nhau thử nghiệm một hệ thống giọng nói mới.

| Speaker | Neutral | Happy | Sad | Angry |
| --- | --- | --- | --- | --- |
| A | `A_neutral.wav` | `A_happy.wav` | `A_sad.wav` | `A_angry.wav` |
| B | `B_neutral.wav` | `B_happy.wav` | `B_sad.wav` | `B_angry.wav` |
| C | `C_neutral.wav` | `C_happy.wav` | `C_sad.wav` | `C_angry.wav` |

This is exactly **12 core outputs**. Add an emotion-disabled output per speaker, plus the emotion donor as a non-target control. Do not sweep strength until this matrix has passed.

### 9. Evaluation Protocol

1. **Identity test:** blind listeners receive each A/B/C emotion set and rate whether the voice remains the same person from 1–5.
2. **Emotion test:** separately and blindly label every output neutral/happy/sad/angry/unclear; do not disclose the requested label.
3. **Naturalness test:** 1–5 rating, independently of identity/emotion.
4. **Leakage test:** compare `A + X_sad`, `B + X_sad`, and `C + X_sad` with donor X. Listeners explicitly report whether output timbre resembles X. This is mandatory for shared emotion audio.
5. Lock text, speaker reference, seed where available, and all generation settings across core cells. Change only the emotion input.

### 10. Passing Thresholds

- Identity rating: **mean ≥4.0/5** for every target speaker; no emotion may show systematic catastrophic drift.
- Emotion recognition: **≥70%** correct across the 12 core samples, excluding only explicitly marked `unclear` from a secondary diagnostic—not from the primary rate.
- Naturalness: **mean ≥3.5/5**.
- Leakage: no consistent identification of donor X as the generated speaker; any systematic donor-timbre transfer is a failure.
- Vietnamese quality: must not be materially worse than VieNeu in a matched listening comparison.

All conditions must pass together. “They sound different” is not success.

### 11. Reference Audio Requirements

| Input | Verified source requirement | PoC operating rule |
| --- | --- | --- |
| Speaker reference | WAV/FLAC; card recommends 22.05 kHz; source truncates to 15 seconds; transcript not requested | Supply 8–15 s clean, single-speaker, dry speech; mono WAV preferred; minimize leading/trailing silence |
| Emotion reference | Source separately loads and truncates to 15 seconds at 16 kHz | Supply 5–15 s clean, expressive single speaker; use the same donor clip for every target in Mode C |

The source uses `librosa.load`, so it handles common channel/sample-rate inputs, then resamples internally. It does not establish a minimum duration, studio mandate, or explicit silence-normalization rule; clean speech is therefore a PoC quality precaution, not an invented hard requirement.

### 12. Vietnamese Frontend Findings

The checkpoint includes `bpe.model` and configures a 12,000-token BPE vocabulary. Source optionally uses `ViCleaner`; without it, raw text is retained before a restrictive normalization stage that permits alphanumeric/whitespace plus only `.`, `?`, and `,` punctuation. Vietnamese diacritics are Unicode alphanumeric and should survive that filter.

This establishes a Vietnamese tokenizer path, not full Vietnamese text normalization quality. Numbers, dates, abbreviations, markdown, quotes, and punctuation have not been verified in audio. The PoC text should be passed directly as Unicode Vietnamese and must not modify AIVoice Smart Text Processing.

### 13. GPU Requirements

This is **inference only**, not training.

| Tier | Assessment |
| --- | --- |
| RTX 3060 12 GB | Not a safe recommendation: upstream IndexTTS-2 guidance is already about 10 GB and this Vietnamese bundle additionally loads a ~1.19 GB Qwen emotion model plus runtime activations. It may be an unsupported narrow-fit experiment only. |
| RTX 3090 24 GB / RTX 4090 24 GB / L4 24 GB / A10 24 GB | **Recommended minimum practical class** for the isolated PoC; enough headroom for FP16 model initialization, external assets, and diagnostics. |
| A100 40/80 GB | Unnecessary for the 12–20 sample inference PoC; useful only if a later training phase is approved. |

Plan for CUDA-capable Linux, Python **3.10+**, PyTorch **2.6+**, and CUDA **12.4-compatible** wheels as declared in the project. FlashAttention is not required by the checked IndexTTS2 inference path; custom CUDA kernel/DeepSpeed are optional accelerators, not PoC prerequisites. Upstream guidance lists roughly 10 GB VRAM for IndexTTS-2, but that does not account for this fork’s extra Qwen classifier. [IndexTTS hardware guidance](https://github.com/index-tts/index-tts/wiki/%E6%8E%A8%E8%8D%90%E9%85%8D%E7%BD%AE)

### 14. Expected PoC Cost

For isolated environment setup, checkpoint download, initialization, 12 core + 3–8 controls, WAV export, and a small retry allowance: **2–5 GPU-hours** is a reasonable planning range. This is **LOW** cost on a 24 GB rental GPU, before any human listening time. It excludes training, repeated tuning, or data collection. Exact provider cost is intentionally not fabricated.

### 15. Required Downloads

Do not download in this phase.

- Vietnamese checkpoint bundle: **5.89 GB**.
- External Wav2Vec-BERT, MaskGCT semantic codec, CAMPPlus speaker model, and BigVGAN vocoder: required by source; individual version/size pinning is incomplete in the Vietnamese release.
- Python/CUDA environment and package cache: additional disk space.

Provision **at least 20 GB free disk**, preferably **30 GB**, to accommodate models, Hugging Face cache duplication, Python packages, temporary files, and generated WAVs. This is a safe operational allocation, not a claimed model-weight total.

### 16. Isolated Environment Design

```text
phase28e-index-poc/
  .venv/                 # separate Python environment
  model/                 # separate checkpoint download location
  hf-cache/              # separate Hugging Face cache
  references/
    speakers/            # manually copied A/B/C references only
    emotions/            # shared donor clips only
  outputs/
  manifest.json
  environment-lock.txt
  run_poc.py             # future only
  evaluation/
```

No AIVoice `.venv`, production database, Voice Lab history, saved voice storage, or frontend/backend code may be mounted or modified. Automatic download must be disabled until the exact model revision and file hashes are approved.

### 17. Future Runner Specification

`run_poc.py` must be implemented only in a later approved phase. It should:

1. Load the approved model and auxiliary assets once.
2. Read an immutable manifest with checkpoint revision/hash, references, one text, emotion mechanism/value, `emo_alpha`, seed/generation settings, and expected output locations.
3. Generate one file for each speaker × emotion cell serially.
4. Log initialization time, per-file generation time, device/GPU name, peak VRAM if available, output SHA-256, and errors.
5. Write no production data and make no model-selection decisions.

For first-pass comparison, use `use_random=False`; lock `top_p`, `top_k`, temperature, beams, and repetition penalty. The checked source exposes sampling parameters but has no dedicated fixed-seed argument; a future runner would need to seed Python/PyTorch explicitly and record that this is a best-effort determinism claim.

### 18. Checkpoint-First Decision Tree

```text
Vietnamese checkpoint exists?
        |
   +----+----+
   |         |
  YES        NO
   |         |
audit        FALLBACK ONLY:
provenance   estimate minimal adaptation
and licence
   |
usable for isolated research?
   |
 +----+----+
 |         |
YES        NO
 |          |
direct       stop / resolve licence-provenance issue
inference PoC
 |
3 speakers × 4 emotions
 |
+-------------------+
|                   |
PASS                FAIL
|                   |
design future       stop / investigate adaptation only if
adapter boundary    Vietnamese checkpoint failure is diagnosable
```

Training is not the default next step.

### 19. Fine-Tuning Fallback

**FALLBACK ONLY — not recommended now because a downloadable checkpoint exists.**

If that checkpoint fails provenance/licence or inference evaluation, start from an explicitly licensed IndexTTS-2 base only after written model-use clarification. Retain the compatible BPE/config/conditioning design, train or extend Vietnamese tokenizer support, and use a rights-cleared multi-speaker Vietnamese corpus with expressive labels. Neutral Vietnamese speech alone is not sufficient to establish reusable emotion. A minimal credible adaptation still needs external CUDA, multiple unseen-speaker evaluation, and a checkpoint compatibility plan; it must be a separate design phase, not a reactive production task.

### 20. Major Risks

- Unresolved rights and data provenance for the community fine-tune.
- Conflicting/unclear commercial terms between code, base model, and community checkpoint.
- Donor-timbre leakage from shared emotion audio.
- Vector mode appears partly speaker-style-selected in source, so its apparent independence must be measured.
- Qwen text emotion is a classifier, not a semantic TTS instruction, and Vietnamese classification quality is unverified.
- Vietnamese pronunciation/text normalization may underperform VieNeu.
- 5.89 GB bundle plus unpinned auxiliary downloads, CUDA/PyTorch dependency drift, and GPU memory failure.
- Sampling randomness, artificial delivery, or industrial artifacts can invalidate an otherwise functional call path.

### 21. Go / No-Go Recommendation

#### GO-B

A downloadable Vietnamese checkpoint exists and is technically credible enough for a **small isolated, non-production rented-GPU inference PoC**, but it must first pass provenance/licence checks. Specifically, obtain written clarification for commercial/derivative use if AIVoice is a product path, record checkpoint hashes/revisions, and keep the trial strictly research-only until evaluation passes.

### 22. Phase 28E Recommendation

Design the exact execution phase for the isolated rented-GPU PoC: pinned environment, approved asset manifest, manual reference-consent checklist, fixed 12-sample matrix, control samples, failure-stop rules, and blinded listener worksheet. Do **not** execute Phase 28E yet.

### 23. Production Changes

**NONE.** Only this research report was created. Stop and wait for review.
