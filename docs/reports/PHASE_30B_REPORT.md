# Phase 30B Report

## Timestamp

2026-08-31 (Asia/Ho_Chi_Minh)

## Status

REFERENCE_REQUIRED

## Objective

Build isolated, local R&D infrastructure to select and validate a distinctive,
warm, deep, comfortable Vietnamese Podcast Brand Voice using the existing
VieNeu V3Turbo ONNX CPU architecture.

## Direction Change

Primary R&D target is Podcast Brand Voice. Meme/Breath R&D is paused because of
the project direction change; no Meme/Breath files were deleted.

## Previous Production State

Review Film remains the existing provisioned Special Voice. No production
profile, endpoint, sampling default, UI, Voice Lab, Audio Studio, History,
Smart Text Processing, normal/saved/cloned voice behavior was changed.

## Podcast Brand Voice Specification

The target is a recognizable, warm, full-bodied, naturally deep and intimate
Vietnamese narrator with calm confidence, clear phrase rhythm, controlled
expressiveness, and long-listening comfort. Deep-but-muddy, monotone, robotic,
theatrical, unstable, rushed, fatiguing, or generic TTS-like candidates fail.
Brand distinctiveness, memorability, and channel suitability are listening
criteria rather than mathematical claims.

## Files Created

- `experiments/special_voice_podcast/README.md`
- `experiments/special_voice_podcast/podcast_voice_spec.md`
- `experiments/special_voice_podcast/reference_contract.md`
- `experiments/special_voice_podcast/test_sentences.json`
- `experiments/special_voice_podcast/long_form_script.txt`
- `experiments/special_voice_podcast/evaluation.csv`
- `experiments/special_voice_podcast/runner.py`
- `tests/test_phase30b_podcast_voice.py`

## Files Modified

- `.gitignore` — ignores Podcast R&D references, outputs, and measurements.

## Production Changes

None.

## Reference Status

No Podcast reference was supplied at
`experiments/special_voice_podcast/reference_audio/podcast_reference.wav`.

## Reference Contract

Only a user-supplied or explicitly approved reference may be used. The initial
clip should be 6–8 seconds, one Vietnamese speaker, clean, naturally warm and
conversational, with clear consonants, phrase rhythm, a useful pause, and a
natural ending. Separate candidates remain separate identities; they are never
mixed.

## Reference Validation

Not run because no reference exists. The runner reuses lightweight local DSP to
record duration, sample rate, channels, peak, RMS, clipping, leading/trailing
silence, and a basic noise warning. It rejects clear duration, clipping,
silence, and level failures rather than silently repairing them.

## Experiment Architecture

The runner validates one permissioned candidate, encodes it once into
`speaker_emb + codes`, and compares three identical texts against a selected
existing normal control voice. Both use the existing local engine, native
sampling defaults, speed 1.0, normal chunking, and WAV output. It creates six
anonymized files, a separate mapping, a listening sheet, and performance data.
No parameter search, synthetic depth, or mastering is applied.

## Short Test Corpus

Twelve original Vietnamese sentences cover reflection, story, seriousness,
question, gentle emotion, slight drama, explanation, date/numbers, English,
complex phrasing, impact, and a soft closing. The initial test uses only
`reflective`, `serious_observation`, and `long_complex`.

## Long-form Test Plan

The original 406-word monologue follows hook → thought → observation →
development → reflection → soft conclusion, for an intended roughly 2.5–3 minute
spoken duration. It is prepared but deliberately not rendered.
After a STRONG or PROMISING blind result and user approval, a future 90–180
second run should examine identity consistency, chunk transitions, rhythm drift,
pronunciation, ending repetition, fatigue, expressiveness, RTF, and RAM.

## Generated Samples

None. Long-form generation was not run.

## Listening Evidence

None. No candidate may be classified STRONG, PROMISING, WEAK, or REJECT before
the user listens blind. The sheet asks which voice is preferable for 20 minutes,
less ordinary-TTS-like, warmer, naturally deeper, better rhythm, engaging but
not overacted, memorable, and more likely to become a recognizable channel
voice.

## Performance

No inference ran. When short samples are generated, each record includes wall
generation seconds, audio duration, RTF, and peak RSS MB.

## Regression Tests

`python -m py_compile experiments/special_voice_podcast/runner.py` and `git diff
--check` passed. The Podcast scaffold tests passed when executed directly with
the active interpreter because this environment has no pytest module. The
existing Review Film API regression test could not import because this same
interpreter lacks NumPy; no production inference was attempted. Static review
confirms the existing `review_film` / `🎬 Review Film` definition remains in
`backend/app/tts/special_voices.py`.

## Findings

Phase 29's reference-dominant evidence is reflected in this reference-first,
no-tuning design. A valid reference is the next material input.

## Limitations

No audio reference, generated audio, listening result, long-form validation, or
brand classification exists yet. The lightweight validator cannot judge whether
the speaker's delivery is suitable; that still needs human listening.

## Decision

Stop at REFERENCE_REQUIRED. Do not start long-form validation, production
integration, or Podcast mastering.

## Next Recommendation

Provide one permissioned 6–8 second Vietnamese WAV at
`experiments/special_voice_podcast/reference_audio/podcast_reference.wav`, then
run the short blind comparison with an available normal control voice. Review
the six anonymized WAVs before any next step.
