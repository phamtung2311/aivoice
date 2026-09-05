# Phase 33B — Wide VoiceDesign Cast

Status: blind Vietnamese audition ready. This is isolated R&D only: no user recording, production voice, UI, API, model, or production profile was changed.

## Scope completed

- Exactly four synthetic male Qwen VoiceDesign sources were generated sequentially from the same English source text, on the existing local CPU workflow.
- Exactly one paired VieNeu conditioning profile was encoded from each corresponding source. No embedding interpolation, cross-pair mixing, or manual identity editing was used.
- Exactly one identical Vietnamese probe was synthesized for each transfer at speed 1.0, with identical sampling, chunking and pause policy.
- The audition folder contains exactly four randomized presentation copies. It contains neither Qwen sources nor a mapping.

## Qwen source verification

All sources are mono 24 kHz and have zero clipped samples.

| Private source | Duration | Peak | RMS | Clipped |
| --- | ---: | ---: | ---: | ---: |
| A | 6.720 s | 0.582031 | 0.115651 | 0 |
| B | 6.560 s | 0.554688 | 0.078981 | 0 |
| C | 6.080 s | 0.656250 | 0.096121 | 0 |
| D | 6.960 s | 0.726562 | 0.077419 | 0 |

The raw sources are retained privately under `sources/`.

## VieNeu transfer verification

Each reference produced its own 192-value speaker embedding and its own paired reference-code array. All Vietnamese outputs are mono 48 kHz with zero clipped samples.

| Private transfer | Duration | Peak | RMS | Clipped |
| --- | ---: | ---: | ---: | ---: |
| A | 14.560 s | 0.635925 | 0.108613 | 0 |
| B | 13.440 s | 0.764160 | 0.106492 | 0 |
| C | 13.440 s | 0.735474 | 0.103259 | 0 |
| D | 14.240 s | 0.825989 | 0.102815 | 0 |

Raw Vietnamese outputs are retained privately under `raw_vietnamese/`; profiles are retained under `conditioning/`.

## Blind audition

Audition copies receive only constant per-clip gain to RMS 0.09 (with no pitch, formant, timing, or spectral processing). Each is mono 48 kHz, zero-clipped, and the private mapping is stored only in `private_mapping.json`.

- `audition/Candidate 01.wav` — 13.440 s
- `audition/Candidate 02.wav` — 14.560 s
- `audition/Candidate 03.wav` — 14.240 s
- `audition/Candidate 04.wav` — 13.440 s

For the first judgment, answer only:

1. Do these immediately sound like four different people?
2. Which pairs, if any, still sound like the same person?
3. Which voices are immediately recognizable or distinctive?

Do not judge which is best yet. The mapping remains private until the blind assessment is complete.
