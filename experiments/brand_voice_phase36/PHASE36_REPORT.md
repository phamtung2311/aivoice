# Phase 36 — Brand Voice Engine Migration Audit

## Phase 35B mapping

`Clip_A = one_sentence_per_call`; `Clip_B = two_related_sentence_group`; `Clip_C = current_240`; `Clip_D = adaptive_single_350`.

Clip D is preserved as the best Phase 35B continuity configuration, but is not promoted. `BEST_KNOWN_BRAND_VOICE_CHECKPOINT` from Phase 34 remains frozen unchanged.

## Candidate 03 portability

Candidate 03 survives independently of VieNeu. Its portable identity package is the pristine Qwen VoiceDesign WAV, its exact English transcript, the exact VoiceDesign description, measurements/listening notes, and any future synthetic reference corpus made from that same identity. A longer corpus is technically possible without the user's voice, but should only be generated for a chosen new clone engine and kept clean/transcribed.

VieNeu `speaker_emb [192]` and `reference_codes [87,16]` are architecture-specific conditioning assets. There is no evidence another engine can consume them. They remain a VieNeu implementation, not the identity.

## Local asset audit

Present: Qwen3-TTS VoiceDesign 1.7B checkpoint (~4.3 GB), Phase 30 Qwen CPU environment, Candidate 03 source/reference/anchor manifests. Absent: Qwen Base checkpoint, Gwen-TTS, IndexTTS2, VoxCPM/VoxCPM2 runtimes/checkpoints. No download or new generation was performed.

## Candidate comparison

| Engine/path | Vietnamese | Candidate 03 clone | continuity / emphasis | CPU i9 / 16 GB | GPU-local future | licence/local fit | evidence |
| --- | --- | --- | --- | --- | --- | --- | --- |
| **Gwen-TTS 0.6B** | **Strong** — Vietnamese primary | **Strong** — direct reference clone + transcript | Medium — expressive claim, must test | Weak/Unknown | Strong — docs state CUDA 12.4, >=4 GB VRAM | Strong — MIT claim; review model/data policy | Strong official repo |
| Qwen3-TTS Base | Weak — Vietnamese not officially listed | Strong — native VoiceDesign→clone workflow | Medium for supported languages; Vietnamese unknown | Weak (current 1.7B CPU source was very slow) | Strong | Medium | Strong official docs, weak Vietnamese evidence |
| IndexTTS2 | Unknown/Weak Vietnamese evidence | Strong zero-shot reference conditioning | Strong advertised emotion/duration control | Weak | Medium/Strong | Medium — official commercial terms need review | Medium; no Vietnamese proof |
| VoxCPM2 | Unknown — claims 30 languages, no verified Vietnamese result here | Strong on paper, clone/control instruction | Strong on paper | Unknown | Medium/Strong | Strong Apache-2.0 | Medium; Vietnamese evidence insufficient |

Gwen is trained from Qwen3-TTS 0.6B on approximately 1,000 hours of Vietnamese audio and exposes direct cloning from reference WAV plus transcript. Its repository recommends normalizing and splitting text before inference, so it is promising but does not prove long-form continuity. [Gwen-TTS](https://github.com/ggroup-ai-lab/gwen-tts)

Qwen officially documents VoiceDesign → reusable Base clone prompt, but its published primary-language list excludes Vietnamese; it is not the recommended production path until Vietnamese quality is demonstrated. [Qwen3-TTS](https://github.com/QwenLM/Qwen3-TTS/blob/main/README.md)

## Strategic conclusion

VieNeu is now the likely rendering bottleneck: repeated controlled tests retained Candidate 03 identity but did not achieve continuous, forceful, semantically directed Vietnamese delivery. That is not proof of a universal VieNeu defect, but it is sufficient to stop further chunk/join tuning for this project.

Recommended architecture: **Qwen VoiceDesign identity asset → Gwen-TTS Vietnamese clone engine → local production inference**. This separates identity design from Vietnamese rendering, retains free/local inference as the goal, and directly tests the suspected bridge loss.

## Exactly one recommended next PoC

After explicit approval to download/install Gwen-TTS, generate only **two** outputs on the same Vietnamese Phase 34 test passage: (1) frozen Phase 34 Clip C control; (2) one Gwen-TTS clone from Candidate 03 pristine Qwen reference and exact transcript, using Gwen’s documented normalization. No corpus expansion, no tuning grid, no production registration. The falsifier is simple: if the Gwen clip does not both retain recognizable Candidate 03 identity and clearly improve continuity/emphasis in blind listening, reject this migration path before further work.

No production modification, user recording, model training, paid dependency, or large download occurred in this phase.
