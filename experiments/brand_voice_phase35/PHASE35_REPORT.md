# Phase 35 — Continuous Speech / Chunk Boundary Audit

Phase 34 Clip C maps to Strategy A: the unmarked current baseline. Candidate 03 identity, paired `[192]` embedding, `[87,16]` codes, decoding (0.82/25/0.97/1.15), speed and model are frozen.

## Diagnosis

1. The selected 665-character Phase 34 passage made **four independent outer VieNeu calls**: 234, 187, 183 and 58 characters. These are sentence-group chunks; no grammatical sentence was split mid-sentence, but multiple sentences were grouped and every group begins a fresh model call.
2. All three outer boundaries have 228–357 ms generated edge silence, align with the strongest audible stops, and have `0 ms` joiner insertion. Thus the repeated reset is consistent with independent utterances plus native sentence-ending cadence, not a 75 ms joiner defect.
3. The selected strategy had **no semantic markers**, so markers did not contribute to Clip C’s stops.
4. Conservative final-WAV low-energy detection finds many >=100 ms regions, including the three outer boundaries, but also internal native punctuation pauses. It cannot establish that every low-energy region is a literal silence or perceptual reset.
5. Current VieNeu exposes default internal `max_chars=256`; source code accepts a caller-provided larger value and shows no separate hard 240-character limit. The app’s 240 policy is therefore conservative outer chunking, not a runtime requirement. Increasing it can increase token/frame work and CPU time, so the PoC uses 1000 only for this short 350-character test.

## Continuity PoC

| Strategy | Architecture | Calls | Duration |
| --- | --- | ---: | ---: |
| A | Current app baseline, outer cap 240 | 2 | 25.20 s |
| B | One direct VieNeu call per grammatical sentence; no comma splitting | 3 | 25.20 s |
| C | One direct VieNeu call for the entire passage, `max_chars=1000` | 1 | 24.00 s |

All outputs are 48 kHz mono, unclipped, use the frozen identity and same decoding. No crossfade, trim, speed edit or authority optimization was used. The safest path to continuity is first to validate C by listening; if stable, use a bounded larger internal call size only for passages that fit its validated limit, otherwise split only at sentence endings.

Production remains untouched.
