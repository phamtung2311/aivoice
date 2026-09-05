# Phase 30J Report

## Timestamp

2026-08-31 (Asia/Ho_Chi_Minh).

## Status

`G2_MANUAL_GENERATION_REQUIRED`

## Objective

Freeze the two Phase 30I voices selected by the completed blind audition, reveal their original VoiceDesign identities, and prepare six new attribute-only synthetic VoiceDesign candidates. This phase ends before any Generation 2 VieNeu bridge or audition.

## Phase 30I User Verdict

The user judged blind audition `01` and `02` as “good; human-like; fairly acceptable.” `03` was weaker. Neither selected voice is declared the final brand voice.

## Keeper Preservation

Protected baselines now exist at `experiments/special_voice_podcast/keepers/phase30i_01/` and `experiments/special_voice_podcast/keepers/phase30i_02/`. Each contains the untouched original Qwen source WAV, matching Vietnamese audition WAV, original per-identity source and VieNeu measurements, exact prompt and English text in metadata, and reference conditioning created once with the existing VieNeu ONNX encoder (`denoise=False`, `use_ref_codes=True`). No audio was normalized, edited, mixed, or otherwise modified.

## Keeper Integrity

`experiments/special_voice_podcast/keepers/KEEPERS_MANIFEST.json` records the SHA-256 digest and byte size of every preserved keeper artifact. Validation passed for both keepers and all 14 hashed files. Keeper outputs are protected baselines and are not inputs for interpolation, averaging, code mixing, audio splicing, pitch/formant changes, or Qwen reference conditioning.

## Phase 30I Mapping

| Blind number | Original identity |
| --- | --- |
| 01 | C |
| 02 | B |
| 03 | A |

Thus the preserved keepers are `phase30i_01` / original `C` and `phase30i_02` / original `B`.

## Winning Prompt Characteristics

This is prompt-attribute analysis only, not an acoustic causal claim. `01` / C requested a deep, warm, resonant male voice with subtle believable texture, maturity, control, approachability, and no extreme rasp, theatrical delivery, artificial bass, or celebrity imitation. `02` / B requested a medium-deep to deep, clean but characterful timbre, calm confidence, intelligent conversational delivery, intimate microphone presence, subtle texture, and avoidance of generic TTS cadence, exaggerated bass, theatrical delivery, and real-person imitation.

The user did not rank 01 above 02, so G2-A is an explicit conceptual refinement of 01/C as a deterministic anchor, not a claim that it was perceptually stronger. The rest of the G2 set explores complementary variants of the shared approved attributes.

## Generation 2 Design

Six new identities are defined strictly from non-identifying attributes: a keeper-concept refinement, warm texture, intimate storytelling, calm hosting, mature resonance, and characterful natural distinctiveness. They retain the target of a naturally medium-deep/deep, warm, full-bodied male podcast voice with calm confidence and memorable but believable personality. No prompt names, references, or imitates a real person.

## G2 VoiceDesign Prompts

`experiments/special_voice_podcast/qwen_voice_factory/generation_2/prompts.json` contains exactly `G2-A` through `G2-F`. All use the unchanged Phase 30I English source text: “In this quiet moment, we can slow down, listen closely, and let a simple thought unfold with clarity.”

## Manual Generator

`qwen_voice_factory/generate_phase30j_g2.py` is a finite, resumable manual runner. It uses only the existing local official `Qwen/Qwen3-TTS-12Hz-1.7B-VoiceDesign` checkpoint and isolated Qwen Python environment. It is offline, CPU-only, uses `torch.bfloat16` and eager attention, and does not load VieNeu. It prints `[1/6] G2-A ...` through `[6/6] G2-F ...` with flushed terminal output.

A valid existing canonical output is skipped. An invalid existing output is not replaced until a newly generated temporary WAV passes technical validation; one technical retry is allowed for each identity.

## Memory Safety

Before loading Qwen, the runner prints MemAvailable and swap usage. It exits with `QWEN_RAM_BLOCKED` below 7 GiB, warns from 7 to 8 GiB, and proceeds at or above 8 GiB. It does not change swap/zram or kill user processes.

## Validation

- Both new scripts compile using the isolated Qwen Python.
- `qwen-tts` imported successfully.
- Torch is `2.13.0+cpu`; `torch.cuda.is_available()` is `False`.
- The official local model path and both required safetensors files exist.
- Exactly six G2 prompts and six expected output paths were verified.
- The keeper manifest and all 14 keeper hashes were verified.
- Qwen was not loaded and no G2 audio was generated during validation.

## User Action Required

Run the manual generator in a normal Fedora terminal, let all six candidates finish, then return its terminal output. Do not start VieNeu bridging in the same process or before reporting the result.

## Production Changes

None. No backend, frontend, API, production engine, production dependencies, saved voices, or production selector changed.

## Decision

`G2_MANUAL_GENERATION_REQUIRED`. Wait for the user’s source-generation result before the separate Phase 30J VieNeu bridge and blind audition continuation.

## G2 Source Generation Result

The user completed all six local official Qwen VoiceDesign sources on attempt 1.
Recorded generation times are: G2-A 595.434 s, G2-B 299.769 s, G2-C 493.796 s,
G2-D 372.894 s, G2-E 402.620 s, and G2-F 361.692 s. No Qwen source was
regenerated during this continuation.

## G2 Source Verification

All six source WAVs exist, are playable mono 24 kHz WAVs, have non-zero duration,
and have no clipped samples. Their observed duration, sample rate, channel count,
peak, RMS, and clipping measurements exactly match
`generation_2/measurements/source_generation.json`.

## Keeper Revalidation

Before the G2 bridge, the protected Phase 30I keeper manifest was revalidated.
Both `phase30i_01` and `phase30i_02` remain byte-identical to their recorded
SHA-256 digests: 14 of 14 preserved keeper artifacts passed. No keeper audio or
conditioning was touched.

## G2 VieNeu Reference Encoding

Each G2 source was independently encoded using the same existing VieNeu ONNX
reference path as Phase 30I, with `denoise=False` and `use_ref_codes=True`.
Experiment-only, per-identity speaker embeddings and reference-code arrays were
persisted under `generation_2/conditioning/`. No embeddings, codes, or source
identities were mixed. The production encoder was not modified.

## G2 Vietnamese Generation

Each independent conditioning pair generated exactly one Vietnamese sample using
the unchanged Phase 30I passage, `speed=1.0`, `denoise=False`, no emotion tags,
and NumPy seed 30109 before each generation. All six first attempts were
technically valid; no subjective retries, post-processing, speed changes, or
other audio transformations were applied.

## G2 Measurements

All six Vietnamese outputs are playable, mono 48 kHz, non-empty, and unclipped.
Their measured durations are 12.320 s, 11.760 s, 14.560 s, 11.840 s, 13.520 s,
and 11.680 s respectively in original G2-A through G2-F order. Encoding,
generation, peak/RMS, conditioning-shape, RSS, and technical-status records are
in `generation_2/measurements/vieneu_generation.json`. Metrics are not used to
rank the candidates.

## G2 Blind Audition

A separate Generation 2 audition directory contains exactly six source/Vietnamese
pairs, numbered `01` through `06`. A single deterministic randomization was
created and saved only in `generation_2/private_mapping.json`; the mapping is
intentionally not disclosed here. Hash validation confirms all six audition
pairs point to their matching source identity and Vietnamese output. The Phase
30I audition directory and the two preserved keepers were not included.

## User Listening Required

For each numbered pair, listen to `source_NN` followed by `vietnamese_NN` and
judge identity preservation, human-likeness in Vietnamese, distinctiveness,
long-form podcast suitability, and brand potential. This report makes no
automatic perceptual judgment or winner selection.

## Phase 30J Current Decision

`G2_AUDITION_SET_GENERATED`. Technical generation is complete only. Wait for
the user’s blind listening result before any further Phase 30J action.

## G2 User Verdict

The completed blind listening verdict is recorded in meaning as follows:

- `01`: fairly good, but slightly too slow.
- `02`: male voice, but perceived as too feminine for the target identity; rejected as a primary direction.
- `03`: strongly too feminine for the intended target; rejected.
- `04`: overly long inter-word pauses and distracting audible breathing; rejected.
- `05`: fairly good.
- `06`: highest potential of the six.

The preferred G2 candidates are `01`, `05`, and `06`; `06` is primary. The
desired future refinement is only slightly deeper with slightly stronger, more
masculine vocal presence, while retaining its fundamental identity and naturalness.

## G2 Mapping Revealed

The completed mapping is `01 → G2-A`, `02 → G2-F`, `03 → G2-D`, `04 → G2-C`,
`05 → G2-E`, and `06 → G2-B`.

## G2 Keepers

The selected audition artifacts are permanently preserved as `keepers/g2_01/`,
`keepers/g2_05/`, and `keepers/g2_06/`. Each has untouched Qwen and Vietnamese
WAVs, copied existing per-identity conditioning arrays, original prompt/text,
measurements, metadata, SHA-256, and byte-size records. The keeper manifest was
revalidated before and after the update; all five keeper baselines are intact.

## Phase 30J Final Decision

`G2_LISTENING_COMPLETE`. G2-06 / original G2-B is the prompt-design anchor for
the separate Phase 30K refinement experiment. No production change was made.
