# Phase 33C — Candidate 03 Brand Voice Refinement

## Revealed Candidate 03 identity

Blind **Candidate 03** is Phase 33B private source **D**: **Dark / Textured**.

Its exact Qwen VoiceDesign instruction was:

> A mature adult male voice with a medium-low register, dark-neutral back resonance, a controlled matte texture with restrained natural grain, and a firm broad vocal body. It must be clearly unlike a smooth bass narrator: neutral delivery, no forced rasp, no accent, no acting.

The paired VieNeu profile is the independently encoded `speaker_emb_D.npy` (shape `[192]`) and `reference_codes_D.npy` (shape `[87, 16]`). No other Phase 33B candidate has been used in this phase.

## Frozen identity anchor

`baseline_anchor/BRAND_CANDIDATE_03_BASELINE/` is immutable by SHA-256 manifest and contains the original Qwen source WAV, exact instruction/configuration, the paired embedding and codes, and the Phase 33B raw Vietnamese output. It is never written by the refinement runner.

## Audit before refinement

The Qwen source is mono 24 kHz, 6.960 s, zero-clipped. Its estimated voiced F0 median is 93.59 Hz (10th–90th percentile 73.00–142.10 Hz); median spectral centroid is 2325 Hz. The original Vietnamese transfer is mono 48 kHz, 14.240 s, zero-clipped; estimated voiced F0 median is 97.81 Hz (77.37–122.83 Hz), with median centroid 1741 Hz. F0 and centroid are descriptive measurements, not an explanation of preference or identity.

| Category | Candidate 03 finding | Treatment |
| --- | --- | --- |
| Speaker identity | Medium-low register, firm weight, darker-neutral resonance and controlled matte grain | Preserve: same frozen embedding and paired codes in every render |
| Prosody/style | Neutral delivery; original transfer had roughly 102 ms leading and 177 ms trailing silence | Keep speed, chunking and pause-deficit policy fixed; test only conservative decoding changes |
| Rendering risk | No clipping/invalid-channel issue in the anchor; pronunciation, phrase endings and sustained pleasantness still require listening | Test short, normal and 49-second stress passage; no pitch/formant/spectral edit |

## Exact refinement strategy

VieNeu exposes no separate naturalness, stability or signature control that is independent of identity. The smallest defensible experiment therefore holds identity, Vietnamese text, speed `1.0`, chunking `240`, pause policy, `denoise=false`, `use_ref_codes=true`, seed `33131`, format and normalization policy fixed. Only sampling differs:

| Variant | Intent | Temperature | Top-k | Top-p | Repetition penalty |
| --- | --- | ---: | ---: | ---: | ---: |
| A | Baseline | 0.80 | 25 | 0.95 | 1.20 |
| B | Natural: slightly less sampling variance | 0.72 | 25 | 0.95 | 1.20 |
| C | Stable: conservative decoding | 0.65 | 20 | 0.90 | 1.25 |
| D | Signature: slightly wider repeatable decoding | 0.82 | 25 | 0.97 | 1.15 |

These are rendering hypotheses only. They do not claim to add a new identity or a model-supported “signature” feature.

## Output verification

All twelve raw outputs are mono 48 kHz with zero clipped samples. Constant-gain audition copies target RMS 0.09 only; no pitch, formant, timing or spectral post-processing was applied.

| Passage | Variant | Duration | Peak | RMS | RTF |
| --- | --- | ---: | ---: | ---: | ---: |
| 1 — hook | A | 10.320 s | 0.887848 | 0.097529 | 0.592 |
| 1 — hook | B | 10.320 s | 0.705505 | 0.104977 | 0.426 |
| 1 — hook | C | 10.960 s | 0.889099 | 0.100672 | 0.655 |
| 1 — hook | D | 10.800 s | 0.807220 | 0.104874 | 0.586 |
| 2 — narration | A | 20.480 s | 0.760590 | 0.098980 | 0.658 |
| 2 — narration | B | 22.160 s | 0.784058 | 0.101554 | 0.528 |
| 2 — narration | C | 20.800 s | 0.878052 | 0.099688 | 0.509 |
| 2 — narration | D | 19.760 s | 0.791992 | 0.100418 | 0.629 |
| 3 — stress | A | 49.520 s | 0.938110 | 0.101027 | 0.535 |
| 3 — stress | B | 47.840 s | 0.896576 | 0.098271 | 0.498 |
| 3 — stress | C | 49.600 s | 0.887268 | 0.101042 | 0.533 |
| 3 — stress | D | 49.040 s | 0.841949 | 0.097004 | 0.473 |

## Blind audition

The same randomized private A/B/C/D mapping is used for each passage. `audition/` exposes only `Passage_1/Clip_A.wav` through `Clip_D.wav`, and the mapping remains only in `private_mapping.json`.

Please assess which version is most pleasant, natural, clear/stable in Vietnamese, distinctive, and most suitable for repeated channel listening. Also answer the mandatory identity check: **do all four still sound like the same person?** A rendering that sounds better but loses Candidate 03 identity does not win.

## Production status

Production is untouched. Candidate 03 is not registered as a final Brand Voice and Podcast Beta is unchanged.
