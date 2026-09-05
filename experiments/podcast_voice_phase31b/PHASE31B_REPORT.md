# PHASE 31B REPORT

## Why Phase 31 candidates sounded similar

Phase 31 only varied small sampling values around one reference, one segmentation
scheme and one pause policy.  Those controls mostly affect local articulation and
were not strong enough to alter the perceived conversational role.  The same short
M-A reference also supplies the same speaker identity and prosodic prior to every
candidate.  Consequently the candidates retained nearly identical rhythm,
emphasis and energy.

## Experiment hypotheses

This round keeps the approved M-A identity, voice preset, speed (1.0) and sampling
profile fixed.  It tests whether **prosodic phrasing**, rather than micro-tuning
sampling, creates perceptually useful podcast directions:

- denser clause phrasing should sound more intimate and close;
- longer sentence/paragraph thought groups should create reflection and breathing;
- narrative punctuation should create a storytelling cadence;
- large grouped passages and short transitions should feel clean and continuous.

## Candidate A–D

Four blind-labelled files were rendered from the same 714-character Vietnamese
podcast script.  Each label maps one-to-one to a distinct direction, but the
label-to-direction mapping is kept private until the listening verdict.

| File | Duration | Generation time | RTF | PCM |
| --- | ---: | ---: | ---: | --- |
| Podcast A | 44.657 s | 27.107 s | 0.607 | mono, 48 kHz |
| Podcast B | 43.889 s | 22.277 s | 0.508 | mono, 48 kHz |
| Podcast C | 43.173 s | 20.548 s | 0.476 | mono, 48 kHz |
| Podcast D | 41.920 s | 23.224 s | 0.554 | mono, 48 kHz |

## Segmentation differences

The four candidates use intentionally distinct rendering units: two use
fine-grained clause/narrative units (21 units each), one uses sentence units
(9 units), and one uses long grouped units (4 units).  This is a meaningful
change in thought grouping, rather than a parameter sweep.  Full boundaries are
kept in the private `chunk_logs/` files for reproduction.

## Pause strategy differences

Silence is insertion-only: existing speech audio was not trimmed, cut or
crossfaded.  Each direction receives its own clause, sentence, question and
paragraph pause targets.  The measured output silence ratios were respectively
25.32%, 24.01%, 27.39% and 24.22% for A–D.  Differences should therefore be heard
primarily as pacing and thought separation, not as a changed speaker identity.

## Reference-conditioning findings

Only one approved clean source for the M-A identity was found:
`special_voice_podcast/keepers/phase30m_04/qwen_source.wav` (8.72 s).  It is
technically usable but gives limited long-form prosody to condition from.  No
alternate approved long M-A reference exists locally, so this round does not mix
identities or use generated output as reference.  The isolated, future-only
20–40 second reference experiment is documented in `reference_v2_plan.md` and
requires approval before execution.

## Metrics

All four files have unique SHA-256 hashes, are mono 48 kHz WAVs and have zero
clipped samples.  Peak levels range from 0.7164 to 0.879059; RMS levels range
from 0.099641 to 0.107743.  Machine-readable measurements are in the private
`metrics/metrics.json`; the runner and report do not change production audio.

## Perceptual distinctiveness assessment

The candidates now have materially different segmentation and pause architectures
(21 / 21 / 9 / 4 units), so this is a genuine test of conversational behavior.
However, final perceptual distinctiveness must be decided blind by listening.
If they still feel too similar, the evidence points to a reference/model
conditioning limit—not a reason to keep searching tiny sampling adjustments.

## Files changed

- `runner.py` — reproducible, isolated A–D renderer and metrics collection.
- `README.md` — audition instructions without label mapping.
- `reference_v2_plan.md` — approval-gated longer-reference proposal.
- `.gitignore` — keeps generated audio, mappings, logs and metrics local.
- `PHASE31B_REPORT.md` — this technical report.

## Production status

**No production profile was changed.**  No Review Film work, UI work, dependency
addition, model download or bulk generation was performed.  These are isolated
R&D outputs only.
