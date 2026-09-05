# Phase 42C — Personal Voice Adaptation & Prosody/Identity Decoupling

Date: 2026-09-05 (Asia/Ho_Chi_Minh)  
Status: **CURRENT 2-MINUTE DATA INSUFFICIENT — CONDITIONAL RVC PATH SELECTED**

## 1. Prior human conclusions

Phase 42A is **TECHNICAL PIPELINE PASS / HUMAN QUALITY FAIL**. VieNeu v3
Turbo could approximate some timbre with a short prompt, but long sentences
had unacceptable intonation/pronunciation; its practical enrollment remains
about eight seconds. Phase 42B is **TECHNICAL PoC PASS / HUMAN QUALITY FAIL**:
the owner listened to all V-TTS/VieNeu candidates and concluded **“Tất cả đều
chả ra gì.”**

Zero-shot personal voice cloning is therefore closed. This report does not
reinterpret it as a reference-selection problem, and it did not rerender V-TTS
Test 4, modify the UI, or change production.

## 2. Architecture hypothesis

The proposed research architecture is:

```text
text → existing human-approved narrator/prosody render → trained personal VC → owner-like narrator
```

Voice conversion should learn speaker identity, texture, resonance and timbre
while preserving the carrier's words, timing, pauses, emphasis, sentence rhythm
and F0-led prosody. The carrier is frozen: Synthetic Candidate 03 + Phase 41E
`v3_semantic_focus` + Phase 41F 0.98x + Phase 41H V2 Natural Podcast cadence.
The verified historical WAV remains untouched at
`experiments/brand_voice_phase41h/audio/v2_natural.wav`, SHA256
`66a51b4ccedccec6016cc778ddafceaf4c0d42fad741ad36f711a7d25ef8dce5`.

## 3. Candidate audit matrix

| candidate | licence / provenance | adaptation and prosody | data / transcript | local CPU and Vietnamese viability | decision |
| --- | --- | --- | --- | --- | --- |
| **RVC** — `RVC-Project/Retrieval-based-Voice-Conversion-WebUI`, audited remote HEAD `81eed5e8f68b6bed1789f682fe78cdd324495afc` | Code MIT ([license](https://github.com/RVC-Project/Retrieval-based-Voice-Conversion-WebUI/blob/main/LICENSE)); its published pretrained collection labels itself MIT ([model page](https://huggingface.co/lj1995/VoiceConversionWebUI/tree/main/pretrained)). Exact future files must still be revision-pinned and SHA256-verified before download. | Trainable single-speaker VITS/RVC VC. Converts an existing waveform, uses F0 and HuBERT/content features; source timing/content are intended to carry through. F0 model is required for this hypothesis. Retrieval can reduce timbre leakage but can also introduce artifacts. | Upstream recommends `>=10 min` low-noise speech ([README](https://github.com/RVC-Project/Retrieval-based-Voice-Conversion-WebUI)); no supported technical minimum or reusable-voice guarantee is stated. Transcript/alignment is not required: dataset preprocessing, F0 extraction and content features are the workflow. | Current CLI documents CPU preprocessing, PM/RMVPE F0, CPU HuBERT feature extraction, CPU training by omitting GPU IDs, and offline CPU inference ([CLI](https://github.com/RVC-Project/Retrieval-based-Voice-Conversion-WebUI/blob/main/docs/en/cli.md)). Linux CPU is explicitly the Intel/AMD path ([README](https://github.com/RVC-Project/Retrieval-based-Voice-Conversion-WebUI)). Language is source-audio-driven rather than a Vietnamese text front end; Vietnamese-specific quality remains unproven until a local PoC. | **Conditionally selected.** Meets the architecture and preliminary commercial/local gates; no download, installation, training, benchmark, or quality claim yet. |
| OpenVoice | Repository/UI expressly refers to CC BY-NC 4.0 ([source](https://github.com/myshell-ai/OpenVoice/blob/main/openvoice/openvoice_app.py)). | Tone-color conversion is a useful architectural comparator, but its own FAQ says it clones tone color, not accent/emotion, and expects a base speaker to supply language/style ([FAQ](https://github.com/myshell-ai/OpenVoice/blob/main/docs/QA.md)). It is not the requested trained personal adaptation path. | Short reference zero-shot; no local personal training plan audited. | CPU may be possible but does not cure the non-commercial gate; Vietnamese quality would depend on a separate base TTS. | **Rejected**: non-commercial and wrong adaptation target. |
| so-vits-svc | AGPL-3.0; repository is archived and focuses on singing VC ([repository](https://github.com/svc-develop-team/so-vits-svc)). | Trainable F0 VC but optimized/documented for singing; speech/prosody, current maintenance and dependency risks are unacceptable here. | Requires a corpus; no verified Vietnamese speech or CPU-training evidence accepted for this project. | No validated 16-GB Linux CPU path; archived source and specialist dependencies increase risk. | **Rejected**: unsuitable/archived, not a safe local podcast route. |

### RVC-specific risk register

- Architecture: source content can leak into output or retrieval can create
  artifacts; F0 extraction errors can affect tone and intonation; consonants,
  breaths and unvoiced regions are risk points. RVC exposes `protect`, RMS
  envelope mixing, retrieval blend and F0 method controls, but none will be
  tuned until a bounded PoC.
- Accent/prosody: it may preserve source cadence better than zero-shot TTS,
  because it receives audio rather than generating timing from text. This is a
  hypothesis, not an established Vietnamese result.
- Dependency/model risk: current published pretrained directory is about 1.1
  GB and contains PyTorch pickle checkpoints; pinning SHA256 and source revision
  is mandatory before use. Do not trust a community voice model or unknown
  training data.
- Model/compute: exported inference models are commonly tens of MB while
  full training checkpoints are larger; exact size, RSS, disk use, CPU time,
  swap behavior and output quality remain unmeasured locally.

## 4. Hardware feasibility and CPU benchmark gate

Target hardware is i9-13900H, 16 GB RAM, Intel Iris Xe, Fedora Linux, no
NVIDIA. RVC's current upstream code/docs provide CPU paths for all required
stages, so there is no *documented* NVIDIA-only blocker. Its configuration also
labels CPU training as slower. Upstream supplies no credible CPU
steps-per-second, RAM or total-training-time estimate for this machine.

**No tiny benchmark was run.** Installing/downloading the framework and its
base weights before having a corpus above the documented data floor would spend
private-data/compute budget without testing reusable adaptation. A 125-second
overfit result would only demonstrate that a model can memorize an inadequate
sample; it could not validate the intended long-form narrator use. Therefore:

- 1k / 5k / recommended-schedule estimates: **unknown until bounded local
  benchmark; must not be invented**.
- Next benchmark, after data gate: isolated `.venv-phase42c-rvc`, pinned MIT
  base assets, batch size 1, 10–100 steps maximum; record step time, peak RSS,
  CPU utilisation, swap, disk and checkpoint size. Stop if RSS approaches 16
  GB, swap thrashes, or extrapolation is unreasonable.

## 5. Personal-data assessment and collection gate

The verified existing source is local/private: AAC M4A, mono, 48 kHz,
125.354667 seconds, SHA256
`1bfc4f9b65b7babf028d0c79a3ef53ac838c979660844595a2b4f872e447c147`.
That is 2.089 minutes—about 21% of RVC's documented `>=10 min` recommendation.
It is **SANITY-CHECK-SIZED ONLY**, not evidence that fine-tuning/adaptation
works or fails.

No transcript is required by RVC's content/F0 workflow. The project will never
invent one: any optional read-text manifest field is only entered after owner
verification. The complete local-only collection instructions are in
`PERSONAL_VOICE_RECORDING_PLAN.md`, with a practical Vietnamese coverage script
in `PERSONAL_VOICE_RECORDING_SCRIPT.md`. Minimum collection gate is 12 verified
usable minutes; preferred first corpus is 25–30 usable minutes. Those targets
are an explicit conservative project policy, not an upstream production claim.

## 6. PoC and audio status

No Phase 42C source audio was copied, decoded, trimmed, segmented, uploaded,
downloaded, generated, converted or altered. No model/framework environment was
installed. No audio shortlist exists. The only prospective carrier is the
existing frozen Phase 41H WAV named above; it was SHA256-verified read-only.

Private Phase 42C source/derived data/checkpoints/outputs/metadata and future
environment are gitignored. No cloud/API/Hugging Face upload or telemetry was
used with owner audio.

## 7. Commands, files and git status

Commands executed in this phase were read-only: read prior reports/reviews and
metadata; SHA256/FFprobe verification of existing Phase 41H and owner source;
remote read-only `git ls-remote` for the RVC HEAD; and `git status`/diff
whitespace validation. No TTS, VC, training, download or install command ran.

Files changed/created:

- `.gitignore` — Phase 42C private data and future environment exclusions.
- `experiments/personal_voice_phase42b/HUMAN_REVIEW.md` and
  `PHASE42B_REPORT.md` — recorded supplied Phase 42B human fail.
- `experiments/personal_voice_phase42c/PHASE42C_REPORT.md`.
- `experiments/personal_voice_phase42c/PHASE42C_CHECKPOINT.md`.
- `experiments/personal_voice_phase42c/PERSONAL_VOICE_RECORDING_PLAN.md`.
- `experiments/personal_voice_phase42c/PERSONAL_VOICE_RECORDING_SCRIPT.md`.

The worktree was already substantially dirty with unrelated product and
historical-experiment changes. This phase did not modify those files; its own
changes are confined to the paths listed above and `.gitignore`.

## 8. Recommendation / next phase

This phase resolves to decision **C**: **CURRENT 2-MINUTE DATA INSUFFICIENT**.
The viable conditional direction is trainable RVC voice conversion, not adapted
TTS and not another zero-shot clone. First collect and verify at least 12 clean
minutes locally. Then, and only then, run the bounded isolated CPU benchmark;
promote the path only if license/provenance are pinned, CPU memory/time are
reasonable, and human listening confirms identity, clean conversion and
prosody preservation on the frozen narrator carrier.
