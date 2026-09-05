# Phase 30K Report

## Timestamp

2026-08-31 (Asia/Ho_Chi_Minh).

## Status

`K_REFINEMENT_MANUAL_GENERATION_REQUIRED`

## Objective

Prepare a small, controlled Qwen VoiceDesign refinement around the user’s G2-06
primary direction. The experiment creates three new synthetic identities only;
it does not alter, condition on, or regenerate the original control.

## G2 Primary Anchor

Blind `06` resolves to original `G2-B`. Its prompt requested warm resonance, a
full medium-deep tone, subtle natural texture, intelligent conversational
delivery, relaxed human imperfections, close-mic presence, calm confidence, and
a memorable long-form podcast-host identity, while excluding exaggerated rasp,
artificial bass, commercial polish, theatrical delivery, generic TTS cadence,
and real-person imitation. This is prompt-attribute analysis only, not an
acoustic causal claim.

## Preserved Keepers

The protected collection now contains Phase30I `01`, Phase30I `02`, G2 `01`, G2
`05`, and G2 `06`. Every preserved artifact has a SHA-256 digest and byte size in
`keepers/KEEPERS_MANIFEST.json`; validation passed after adding the three G2
keepers. No keeper WAV, embedding, or code was changed or re-encoded.

## Refinement Hypothesis

The user likes G2-06’s underlying identity and requests a small increase in
natural depth and/or confident masculine presence. The test holds its broad
warm, intimate, conversational, recognizably human prompt direction constant.
Naturalness has priority over either requested adjustment.

## K-A Design

Slightly deeper natural male register and fuller low-mid resonance, retaining
warmth, close conversational presence, human imperfection, and the anchor’s
recognizable identity direction. It explicitly excludes extreme bass, forced low
pitch, booming resonance, trailer/radio delivery, and slow drama.

## K-B Design

Approximately the anchor’s natural depth direction with slightly firmer vocal
presence, confidence, body, clarity, and stable energy. It retains warmth,
approachability, intimacy, and human imperfection while excluding aggression,
advertising/newsreader delivery, theatrical authority, and caricature.

## K-C Design

Conservatively combines slight natural depth and slight strength: warm,
full-bodied low-mid resonance, calm confident intelligence, firm but approachable
presence, and conversational intimacy. Naturalness is explicitly prioritized.

## Cadence Constraints

All prompts request a natural medium conversational rhythm, connected phrasing,
and short natural pauses only at sentence or clause boundaries. They reject slow
dramatic cadence, long ordinary-word pauses, excessive breathiness, audible breath
acting, and whispery delivery. No speed processing is used.

## Manual Generator

`qwen_voice_factory/generate_phase30k_refinements.py` creates K-A, K-B, and K-C
sequentially. It is offline, CPU-only, local-checkpoint-only, uses
`torch.bfloat16` and eager attention, and is resumable: valid canonical WAVs are
preserved and skipped, while only a technical failure receives one retry. It does
not load VieNeu.

## Memory Safety

Before loading Qwen, the runner measures MemAvailable and swap usage. It exits
below 7 GiB, warns from 7–8 GiB, and proceeds at 8 GiB or above. It neither kills
processes nor changes swap/zram.

## Validation

The manual runner compiles with isolated Python 3.12. The local official
checkpoint exists; `qwen-tts` imports; Torch is CPU-only and CUDA is false.
Exactly three prompts and three expected output paths are defined. Qwen was not
loaded during validation.

## Future Blind Control Design

After manual source generation and a separate VieNeu bridge, a four-way blind
audition will compare original G2-06 as a hidden control with K-A, K-B, and K-C.
No randomization, bridge, Vietnamese synthesis, or selection is performed now.

## Production Changes

None.

## Decision

`K_REFINEMENT_MANUAL_GENERATION_REQUIRED`.

## Manual Refinement Generation Result

The user manually generated all three official local Qwen sources on attempt 1:
K-A 6.560 s / 240.543 s generation time, K-B 8.800 s / 321.207 s, and K-C
8.720 s / 328.639 s. No source was regenerated during this continuation.

## Refinement Source Verification

K-A, K-B, and K-C are valid, non-empty, playable mono 24 kHz WAVs with no
clipped samples. Their duration, sample rate, channels, peak, RMS, and clipping
measurements match `generation_3/measurements/source_generation.json`.

## Keeper Revalidation

All five protected keepers were revalidated before bridging: Phase30I 01,
Phase30I 02, G2 01, G2 05, and G2 06. All 35 preserved artifacts match their
recorded SHA-256 digests and byte sizes. No keeper was modified.

## Control Reproducibility

The CONTROL used the byte-identical preserved G2-06 Qwen source and its saved
speaker embedding/reference codes; no control re-encoding occurred. A fresh
Vietnamese regeneration with the same text, seed 30109, `speed=1.0`, and
`denoise=False` is byte-identical to the preserved original: duration, format,
peak/RMS, and SHA-256 all match. Status: `CONTROL_REPRODUCIBILITY_EXACT`.
The blind audition nevertheless uses the preserved original G2-06 Vietnamese
WAV as the perceptual control.

## VieNeu Refinement Bridge

K-A, K-B, and K-C were independently encoded through the existing VieNeu ONNX
reference path using `denoise=False` and `use_ref_codes=True`. Each generated
one technically valid Vietnamese sample with the identical Phase 30I passage,
`speed=1.0`, and NumPy seed 30109. No subjective retry, audio processing,
conditioning mixing, or production-engine modification occurred.

## Blind Audition

`generation_3/audition/` contains four source/Vietnamese pairs randomized once
between CONTROL, K-A, K-B, and K-C. The private mapping is stored separately in
`generation_3/private_mapping.json` and is intentionally not revealed here.
Hash validation confirms each pair retains a matching identity. The control
pair contains the preserved original G2-06 source and Vietnamese WAV.

## User Listening Required

Listen to Vietnamese files 01–04 first and rank solely by listening: naturalness,
male presence, depth, strength, distinctiveness, Vietnamese pronunciation,
comfortable long listening, and channel-brand potential. Then optionally inspect
the matching English source files for identity preservation. No metric-based
winner is asserted.

## Current Decision

`K_REFINEMENT_AUDITION_GENERATED`. Wait for the user’s blind listening result.

## User Blind Verdict

The completed four-way Vietnamese blind verdict is recorded faithfully:

- `01`: okay / selected.
- `02`: rejected.
- `03`: okay.
- `04`: okay / selected.

Both `01` and `04` are selected. No preference between the two is inferred or
recorded.

## Mapping Revealed

The completed mapping is `01 → CONTROL` (original G2-06 / G2-B), `02 → K-C`
(slightly deeper + stronger), `03 → K-B` (slightly stronger), and `04 → K-A`
(slightly deeper).

## Selected Finalists

The two remaining candidate identities are CONTROL / original G2-06 / G2-B and
K-A / slightly deeper. Neither is declared the final brand voice.

## Finalist Preservation

`keepers/phase30k_01/finalist_link.json` records the selected CONTROL and links
to the canonical, byte-identical existing `keepers/g2_06/` artifacts; this avoids
duplicating or altering the original control WAVs and conditioning. The selected
K-A finalist is fully preserved at `keepers/phase30k_04/` with untouched Qwen
and Vietnamese WAVs, copied conditioning, exact prompt/text, measurements, and
metadata.

## Keeper Integrity

The keeper manifest now contains seven protected entries. All artifacts,
including all pre-existing Phase30I and G2 keepers, passed SHA-256 and byte-size
revalidation after the finalist update.

## Phase 30K Final Decision

`PHASE30K_TWO_FINALISTS_SELECTED`. Two candidate identities remain and neither
is automatically ranked or declared the final brand voice.

## Phase 30L Plan Only — Finalist Long-Form Validation

The next phase should compare only these two finalists under identical production
settings on conversational podcast, reflective storytelling,
informational/explanatory speech, and a long continuous Vietnamese passage. It
should assess identity stability, naturalness, pronunciation, cadence,
long-listening comfort, distinctiveness, brand recognizability, breathiness,
feminine quality, unnatural pauses, drift, and missing/truncated words. A longer
stability test is required before any final brand-identity decision. No Phase 30L
audio or execution is performed here.
