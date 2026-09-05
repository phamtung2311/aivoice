# Phase 42C — Personal Voice Recording Plan for RVC Feasibility

This plan is for a **future research-only RVC voice-conversion corpus**. It is
not a request to upload audio anywhere. Keep every recording local under the
gitignored Phase 42C private-data directory; do not commit, cloud-upload, send
to an API, or enable telemetry.

## Amount and sessions

- Current verified clean corpus: 125.354667 seconds (2.089 minutes). This is a
  sanity-check-sized sample, not enough for the selected RVC path.
- Upstream RVC documentation recommends at least **10 minutes of low-noise
  speech**. There is no upstream guarantee that a smaller amount is technically
  adequate or production-quality.
- Minimum collection gate here: **12 verified usable minutes**, after removing
  mistakes, long silence, clipping, music, and other speakers. This deliberately
  exceeds the documented 10-minute recommendation.
- Preferred first training corpus: **25–30 usable minutes**, not a claim of
  production sufficiency. It provides enough material to make the first CPU
  adaptation assessment meaningful.
- Record 3–4 sessions, each 8–12 minutes, on different days if practical.
  Keep microphone distance, room and input gain consistent within a session.

## Capture and file rules

- Capture mono WAV at 48 kHz if possible (24-bit preferred; 16-bit acceptable).
  M4A/AAC is acceptable only if the original is preserved and decoding is
  recorded in the manifest.
- Use a quiet room, fixed mouth-to-mic distance, no music, no reverb effect,
  no noise suppression, no automatic enhancement, no compressor, no EQ, no
  pitch/formant processing, and no background speaker.
- Each raw clip: 20–60 seconds. Start/end with about 0.5 seconds of quiet, but
  do not insert long theatrical pauses.
- Retake a line containing a cough, interruption, clipped input, stumble, or
  non-owner voice. Preserve original takes locally for traceability; mark
  rejected takes rather than silently replacing them.

## Coverage mix for 25–30 usable minutes

| category | target share | goal |
| --- | ---: | --- |
| neutral explanatory narration | 45% | stable everyday identity and sentence rhythm |
| reflective, calm delivery | 20% | lower-energy phrasing without whispering |
| gentle emphasis / contrast | 15% | controlled semantic stress, not acting |
| questions, numbers, names, lists | 10% | endings, punctuation, difficult pronunciation |
| longer connected paragraphs | 10% | continuity and breath/pause behavior |

Include Vietnamese tone coverage across ordinary words and minimal pairs where
natural: ngang, huyền, sắc, hỏi, ngã, nặng. Include initial/final contrasts
such as tr/ch, s/x, d/gi/r, l/n, v/d, t/c, n/ng/nh, plus numbers, dates, common
proper names and English/product terms that occur in the channel.

No transcript needs to be invented for RVC's content/F0 pipeline. Still retain
the reading script and a per-file `read_text` field only after the owner has
confirmed it matches the actual take. Any ad-lib or mismatch must be labeled
`transcript_unverified`, not force-aligned.
