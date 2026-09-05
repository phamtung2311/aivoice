# PHASE 33A — BLIND SYNTHETIC SPEAKER CASTING REPORT

## Candidate selection rationale

Four existing synthetic male speaker profiles were selected privately from the eight
preserved keepers. Selection combined prior design intent, clean source status,
previous human-audition history and embedding separation; it did not simply choose
the four numerically farthest vectors. The set was chosen to cover noticeably
different target character hypotheses while avoiding current-production labels and
all user-recorded voices.

Keeper IDs, Qwen descriptions, concepts, prior rankings and the current Podcast Beta
relationship are intentionally withheld until both identity-test rounds finish.

## Test passages

Exactly three unrelated Vietnamese texts are used by every hidden profile:

1. conversational: ordinary, direct interaction;
2. reflective: quiet thought and phrase endings;
3. informative: neutral explanation without emotional framing.

Each was written for approximately 20–30 seconds at the evaluated speed; realized
durations span 16.48–22.56 seconds because stop-token timing is model-dependent. Text, normalization,
chunking, sampling, pause handling, output format and loudness presentation are fixed
across speakers.

## Generation verification

- Engine: existing local VieNeu V3 Turbo CPU ONNX path.
- Speaker conditioning: one pre-existing paired embedding + reference-code profile.
- Sampling: temperature 0.80, top-k 25, top-p 0.95, repetition penalty 1.20.
- Speed: 1.0.
- Chunking: existing 240-character sentence grouping.
- Pause handling: existing insertion-only measured-silence-deficit policy.
- Exactly 12 final audition clips: four profiles × three passages.
- No Qwen generation, download, GPU use, model training or profile registration.

## Audio metrics

Raw and presentation-copy metrics are retained privately in `metrics/metrics.json`.
Each source WAV is preserved in `raw_outputs/`. The audition copy applies only a
constant per-clip gain toward RMS 0.09, with a 0.95 peak ceiling. It never changes
pitch, formants, timing or spectral content. If peak protection reduces that gain,
the achieved RMS is recorded. All clips must be mono 48 kHz with zero clipped samples.
Verification passed for all 12: audition RMS is 0.089559–0.090000, peak is
0.579141–0.950000, and clipped-sample count is zero.

## Blind-test setup

The `audition/` folder contains only randomized `Clip 01.wav` through
`Clip 12.wav` and `LISTEN_FIRST.md`. Assignment was shuffled with a fixed private
seed; each hidden speaker occurs once per passage and clip numbers do not encode
speaker, passage, keeper, prior status or concept.

Round One tests grouping only. Ground truth remains in `private_mapping.json`. After
the user submits four groups, evaluation will use optimal group-label assignment, then
report correct clips, percentage and confusion. Recognition Round Two follows only
after that result.

## Files created

- `audition/Clip 01.wav` … `audition/Clip 12.wav`
- `audition/LISTEN_FIRST.md`
- `raw_outputs/` (private)
- `source_profiles/` (private)
- `metrics/` (private)
- `private_mapping.json` (private)
- `runner.py`
- this report

## Production status

The user's recorded voice was not used.

No production voice was changed.
