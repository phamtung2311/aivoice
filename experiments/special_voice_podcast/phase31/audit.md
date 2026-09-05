# Phase 31 — Podcast Voice audit

Audit date: 2026-09-01. This report describes the local checkout/runtime; it
does not promote any candidate to production.

## Current production identity

`podcast_brand_beta` is already a dedicated Special Voice, not a normal preset
and not the Review Film profile. `backend/app/tts/special_voices.py` points it
to the Phase 30M M-A keeper. Provisioning uses the saved native VieNeu speaker
embedding and reference codes; it does not re-encode the reference at startup.

| Artifact | Measured state |
| --- | --- |
| Reference | `keepers/phase30m_04/qwen_source.wav` |
| Reference duration | 8.72 s |
| Reference format | mono PCM WAV, 24 kHz |
| Reference peak / RMS | 0.71875 / 0.081989 |
| Clipping | 0 samples |
| Speaker embedding | 192 floats |
| Reference codes | 101 × 16 |
| Reference selection status | `PRIMARY_DISTINCTIVENESS_FINALIST`; pause diagnosis pending |
| Existing technical tests | 19.92 s and 19.36 s, mono 48 kHz, no clipping |

The reference is technically clean enough for the current clone path. Its
8.72-second duration is sufficient for enrollment but short for a definitive
long-form identity audit; it cannot establish whether breath placement,
microphone consistency, and phrase-level prosody remain representative over a
full episode. The original recording should not be replaced without explicit
user approval.

## Actual production pipeline

1. The Audio Studio sends `temperature`, `top_k`, `top_p`,
   `repetition_penalty`, text, voice and speed to `/api/long-audio/jobs`.
2. The long-audio worker normalizes text, preserves user prosody markers, then
   groups sentences into chunks of at most 240 characters.
3. Every chunk calls `TTSEngine.generate` with the same registered Podcast
   profile. The wrapper currently forwards only the four sampling controls.
4. At each join, the pipeline measures leading/trailing silence and inserts
   only any missing portion of a target gap: 130 ms after `.?!…`, 75 ms after
   `,;:`, otherwise 45 ms. It does not trim speech edges or crossfade.
5. Requested speed is applied afterwards with linear-resample playback speed,
   not native expressive pacing.

The visible Audio Studio defaults are temperature 0.8, top-k 25, top-p 0.95,
repetition penalty 1.2, and speed 1.0.

## Runtime capability versus exposed capability

The installed VieNeu 3.3.0 V3 Turbo ONNX runtime accepts `temperature`,
`top_k`, `top_p`, `repetition_penalty`, `repetition_window`, `silence_p`,
`crossfade_p`, `batch_size`, and `max_chars`. On this CPU/ONNX path, batch size
is documented by the runtime as GPU-only. The project wrapper currently exposes
only the first four sampling controls. `repetition_window`, `silence_p`, and
`crossfade_p` are therefore not valid production experiment knobs yet; the
existing audio joiner also has no crossfade implementation.

VieNeu's `style` argument is explicitly deprecated/ignored in V3 Turbo. The
engine therefore cannot create genuine Podcast expression through a style
prompt. Reference conditioning, readable text segmentation, punctuation,
explicit pauses and the four forwarded sampling controls are the meaningful
current levers.

## Phase 31 controlled audition

`runner.py` creates six blind candidates from the same text. Each differs from
the baseline in one factor only: temperature, top-p, repetition penalty, outer
chunk size, or sentence-boundary gap. It preserves the production profile and
writes the label-to-configuration mapping separately.

The first conversational audition has been generated under `outputs/conversation`.
All outputs are 48 kHz mono WAVs, 20.00–21.04 seconds long, have zero clipped
samples, and ran at RTF 0.51–0.61. A human listener must score them using
`listening_sheet.md` before any candidate is selected for story and long-form
validation.

## Reference capture guidance if a new reference is approved later

- Record one speaker only, 20–40 seconds, in a quiet treated room.
- Use a close, steady microphone position (roughly 15–20 cm) with pop filter;
  avoid AGC, reverb, noise suppression, music and compression.
- Deliver relaxed Vietnamese conversation at a medium natural pace, including
  short and long phrases plus one paragraph transition. Do not imitate
  advertising, a newsreader, trailer voice or Review Film delivery.
- Supply mono 48 kHz or 44.1 kHz PCM WAV, 16- or 24-bit, with no clipping and
  0.5–1 second of clean room tone at each edge.

No replacement reference is requested or installed by this phase.
