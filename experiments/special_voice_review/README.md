# Review Film Voice — isolated R&D package

This package prepares a controlled local-CPU experiment for a specialized Vietnamese Review Film voice. It does **not** change AIVoice production behavior, default voices, saved voices, Voice Lab, or Phase 28 research.

## Purpose

Test whether a deliberately selected **single Review Film reference voice**, combined with a small number of native VieNeu sampling configurations, produces an identity-stable narrator/reviewer delivery. This is not universal emotion control and does not use artificial cue tags, global pitch shifting, or punctuation injection.

## Before running

1. Place one permissioned, clean Review Film-style reference WAV at `reference_audio/review_film_reference.wav`. This path is gitignored.
2. Review [reference_contract.md](reference_contract.md).
3. Run a candidate, for example:

```bash
.venv/bin/python experiments/special_voice_review/runner.py \
  --reference experiments/special_voice_review/reference_audio/review_film_reference.wav \
  --candidate baseline
```

4. Generate each candidate separately, then perform blind listening using `evaluation.csv`. Do not infer quality from metrics alone.

Generated WAVs and measurements are deliberately ignored by Git.

## Candidate policy

- `baseline`: no explicit sampling overrides; reproduces current native defaults.
- `review_candidate_a`: slightly lower sampling diversity, intended to test steadier narrator cadence.
- `review_candidate_b`: slightly higher diversity, intended to test natural phrase variation.
- `review_candidate_c`: balanced diversity with a modestly stronger repetition penalty, intended to test less repeated/word-by-word rhythm.

All candidates keep speed at `1.0`, use existing local preprocessing/chunking, and differ only in documented native generation settings. They are hypotheses, not claimed improvements.

## Future profile direction

If listener results justify it, a future special voice should extend the existing voice metadata/profile mechanism rather than create a second TTS pipeline. See `special_voice_profile_design.md`. No production schema is changed here.
