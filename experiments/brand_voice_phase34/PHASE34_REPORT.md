# Phase 34 — Brand Voice Prosody & Authority

## Phase 33C mapping (revealed)

| Blind clip | Real variant |
| --- | --- |
| Clip A | D — Signature |
| Clip B | B — Natural |
| Clip C | C — Stable |
| Clip D | A — Baseline |

Phase 34 therefore uses the winning Clip A configuration throughout: temperature 0.82, top-k 25, top-p 0.97, repetition penalty 1.15, speed 1.0.

## Audit answers

1. **Why commas can sound unnatural:** the app only inserts a 75 ms target at *outer chunk boundaries*, not at every comma inside a generated chunk. VieNeu itself receives punctuation after normalization/phonemization and generates its own intra-chunk prosody. In the Phase 33C long passage, every outer boundary already contained more than the target silence, so the insertion-only joiner added `0 ms`. Thus an unnatural comma is primarily native model prosody or a text/chunk framing issue, not a fixed 75 ms gap being added after every comma. Treating all commas equally would be linguistically wrong.
2. **Likely stretched words:** existing diagnostics have chunk duration and edge silence but no phoneme/word alignment, so they cannot truthfully timestamp a particular stretched syllable. The evidence supports generation-level duration/stop timing and punctuation/chunk context as candidates; speed was 1.0, so resampling did not cause it. Sampling can influence duration, but Phase 34 deliberately holds it fixed.
3. **Genuine emphasis/authority controls:** supported and usable: Vietnamese text normalization, sentence/chunk grouping, internal TTS-only punctuation rewriting, and the project’s explicit `|`, `||`, `|||` semantic boundary markers. These markers are removed before VieNeu and only request measured-deficit joins. They are a boundary control, not a pitch/emphasis control.
4. **Not controlled:** the installed CPU VieNeu path exposes no supported independent word-emphasis, pitch contour, duration, breathiness, vocal force, or authority parameter. `style` is deprecated/ignored; `speaker_emb` and paired reference codes remain fixed. Inline emotion/cue mechanisms are technically present in broader VieNeu code paths but are unverified for this cloned v3 path and previously sounded artificial, so they were not used.

## Four strategies

All use Candidate 03’s frozen `[192]` embedding and `[87,16]` codes, identical semantic content, speed 1.0, output format and decoding baseline.

| Strategy | Change |
| --- | --- |
| A — current baseline | Original text and existing app chunk policy. |
| B — pause-aware | Same words/punctuation; semantic phrases rendered as explicit 70/140 ms marker boundaries. |
| C — authority-aware | TTS-only punctuation restructure into firmer sentence groups; no words added/removed, no marker joins. |
| D — combined | The authority-oriented punctuation structure plus explicit semantic phrase boundaries. |

No sampling grid, pitch/formant transformation, effects, embedding operation or production change was used. The identity is untouched.

## Output verification

All raw outputs are mono 48 kHz with zero clipped samples; audition copies receive constant-gain normalization only.

| Private strategy | Duration | Peak | RMS | RTF |
| --- | ---: | ---: | ---: | ---: |
| A | 42.480 s | 0.791443 | 0.101237 | 0.888 |
| B | 42.720 s | 0.897369 | 0.101175 | 0.592 |
| C | 43.120 s | 0.876801 | 0.095743 | 0.671 |
| D | 42.080 s | 0.993988 | 0.100089 | 0.581 |

The blind audition mapping remains private in `private_mapping.json`. The four files are `audition/Clip_A.wav` through `audition/Clip_D.wav`.

## Production status

Podcast Beta and production voices are unchanged; Candidate 03 is not registered as final Brand Voice.
