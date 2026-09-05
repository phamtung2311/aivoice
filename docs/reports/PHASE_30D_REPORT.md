# Phase 30D Report

## Timestamp

2026-08-31 (Asia/Ho_Chi_Minh)

## Status

NATIVE_PRESET_POOL_INSUFFICIENT

## Objective

Re-audit the local VieNeu preset pool for a neutral/broad Vietnamese, warm,
deep, expressive, distinctive Podcast Brand Voice without changing a profile's
identity or fabricating character.

## User Feedback From Phase 30C

Phase 30C candidate 06: acceptable, but too ordinary.

Phase 30C candidate 09: acceptable, but too ordinary.

The user requests neutral/broad Vietnamese rather than strongly regional voices.
The two acceptable generic baselines are not finalists.

## Runtime Environment

`/home/tung/ai voice/.venv/bin/python`, Python 3.14.7, VieNeu 3.3.0, local
V3Turbo ONNX CPU.

## Full Preset Pool Audit

All 20 packaged profiles were inspected from the live `_preset_voices`
dictionary. Each exposes gender, style, description, `speaker_emb`, and `codes`.
Ten were auditioned in Phase 30C; ten remained untested. Phase 30D did not rely
on speaker names.

## Neutral Vietnamese Filtering

The packaged description for every one of the 20 profiles explicitly labels a
Bắc, Nam, or Trung regional delivery. The filter classifies a profile as
REGIONAL only from that explicit packaged descriptor. It does not claim a
linguistic analysis of the waveform, and it does not infer accent from a name.

## Regional Profiles Excluded

20 profiles were conservatively excluded because their packaged metadata
explicitly identifies a Bắc, Nam, or Trung regional delivery. This preserves the
user's neutral/broad requirement without forbidden DSP accent conversion.

## Previously Tested Profiles

10 profiles were used in Phase 30C; Phase 30C outputs, blind mapping, and
listening sheet remain unchanged. Candidate 06 and 09 remain internal
acceptable-generic baselines only and were not regenerated as Phase 30D files.

## Candidate Selection

0 new candidates. No packaged profile passed the neutral/broad filter, so the
set was not padded with regional, duplicate, or tuned variants.

## Audition Script

An original four-sentence, character-focused Vietnamese passage is prepared in
`phase30d_audition.txt` for a future valid neutral candidate. It was not
rendered because no profile was eligible.

## Generated WAVs

None in `outputs/phase30d/`.

## Generic Baselines

Not regenerated. Recasting candidate 06/09 with the new text would create two
regional-labelled baseline files while the current phase has no eligible neutral
candidates to compare; their preserved Phase 30C files remain evidence.

## Blind Mapping

An ignored `outputs/phase30d/phase30d_mapping.json` records the private complete
audit and an empty candidate mapping. It contains no production change and is
not disclosed before a future listening phase.

## Listening Instructions

`phase30d_listening_instructions.md` explains that no native-preset audition is
available. Future review will use neutral/broad, comfort, vocal character,
Podcast fit, and KEEP/REJECT decisions rather than a large numeric rubric.

## Performance

No Phase 30D audio inference was performed. No performance values exist.

## Production Changes

None.

## Regression Tests

Using `/home/tung/ai voice/.venv/bin/python`:

- `python -m py_compile experiments/special_voice_podcast/runner.py experiments/special_voice_podcast/phase30c_runner.py experiments/special_voice_podcast/phase30d_runner.py` — passed
- `python -m pytest tests/test_phase30b_podcast_voice.py tests/test_phase30c_podcast_candidates.py tests/test_phase30d_podcast_recast.py -q` — 11 passed
- `git diff --check` — passed

## Findings

The available native preset pool cannot presently satisfy both constraints:
neutral/broad Vietnamese and no accent conversion. Further sampling changes
would not create a new neutral identity or strong brand character.

## Limitations

The metadata filter is deliberately conservative. It does not prove that every
regional-labelled profile is equally recognizable to every listener; it applies
the user's exclusion requirement safely. No acoustic accent classifier was
added, and no agent subjective listening claim is made.

## Decision Pending

No native candidate should advance. The user may provide zero candidates; there
is no forced winner.

## Next Recommendation

Use a user-supplied or explicitly approved 6–8 second neutral Vietnamese,
warm, naturally distinctive podcast-style reference for VieNeu cloning. Validate
it with the existing Phase 30B scaffold, then run a blind short comparison. Do
not start long-form, tune presets, or integrate production.
