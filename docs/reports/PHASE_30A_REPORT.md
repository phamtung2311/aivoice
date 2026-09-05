# Phase 30A Report

## Timestamp

2026-08-28 (Asia/Ho_Chi_Minh)

## Status

REFERENCE_REQUIRED — R&D scaffold complete; no supplied `meme_breath.wav`, so no
audio generation or listening conclusion was attempted.

## Objective

Validate whether a permissioned, naturally airy Vietnamese Meme / Giọng Gió
reference transfers a distinctive but intelligible vocal character through the
existing local VieNeu V3Turbo engine.

## Previous State

Review Film is production Special Voice `review_film`. Its local reusable profile
was verified present with `speaker_emb`, `codes`, `is_special`, and Review Film
metadata. Phase 28 remains frozen.

## Files Created

- `experiments/special_voice_meme/README.md`
- `experiments/special_voice_meme/reference_contract.md`
- `experiments/special_voice_meme/test_sentences.json`
- `experiments/special_voice_meme/evaluation.csv`
- `experiments/special_voice_meme/runner.py`
- `tests/test_phase30a_meme_voice.py`

## Files Modified

- `.gitignore` — ignores supplied Meme/Breath references, outputs and measurements.
- This report.

## Production Changes

None. No profile was provisioned, no selector/API/inference behavior changed, and
no sampling override was introduced.

## Reference Status

Missing. Required path:
`experiments/special_voice_meme/reference_audio/meme_breath.wav`.

## Reference Validation

Pending reference supply. The runner will use existing lightweight DSP analysis
and reject an out-of-range duration before generation.

## Experiment Design

When a valid reference exists, the runner produces exactly six anonymized local
WAVs: three original smoke sentences, each rendered with one normal existing
control voice and the Meme/Breath reference. Both use native defaults and speed
1.0. Reference encoding is reused in memory; no profile is saved to production.

## Test Corpus

Nine original Vietnamese sentences cover statement, punchline, question,
exclamation, sarcasm-shaped text, numbers/common internet English, longer text,
fast conversation, and calm delivery.

## Generated Samples

None. Listening evidence pending.

## Listening Evaluation

The future blind sheet scores naturalness, meme suitability, distinctiveness,
airy/breathy character, clarity, consistency, robotic rhythm, preference and
notes. Mapping remains separate.

## Performance

Pending real generation. The runner records wall time, duration, RTF and peak RSS
for every sample.

## Regression Tests

Scaffold tests, Python compile checks and Git whitespace validation are required
before handoff. No broader model test is claimed unless it completes.

## Findings

Phase 29 evidence supports a reference-dominant experiment with native defaults;
there is no justification for a random sampling search before listening.

## Limitations

No permissioned Meme/Breath reference is available. No claim about vocal
character transfer, clarity, or production readiness can be made.

## Decision

Do not integrate Meme / Giọng Gió into production. Supply one appropriate
permissioned 6–8 second WAV, then run the fixed six-sample blind test.

## Next Recommendation

Wait for the reference and listening evidence; do not start Phase 30B.
