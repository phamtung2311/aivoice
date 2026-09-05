# Phase 40B human review — Candidate B cross-text validation

Listen directly in Vietnamese to exactly the three files in `audio/`:

1. `audio/passage_1_reflective.wav` — reflective / triết lý (10.00 s)
2. `audio/passage_2_explanatory.wav` — explanatory / giảng giải (11.28 s)
3. `audio/passage_3_storytelling.wav` — storytelling / kể chuyện có suy ngẫm (10.16 s)

All three used the unchanged Phase 40A Candidate B baseline (canonical
`speaker_emb.npy` + `reference_codes.npy` from
`baseline/PODCAST_CANDIDATE_B_BASELINE/`), one stable generation configuration,
no tuning, no variants, no blend, no post-processing.

## Task

Assess whether Candidate B keeps a distinct character across NEW texts and
remains suitable as a podcast voice. Judge:

1. chất giọng riêng (distinctive person, not a generic preset);
2. độ trầm / thân giọng (medium-low depth and vocal body);
3. lực và trọng tâm (force and semantic focus);
4. tự nhiên (natural, no drift / slurring / morph);
5. không nghỉ dài (no long awkward pauses);
6. không công nghiệp (not an industrial/generic narration sound);
7. ổn định cùng một người (all three sound like the same consistent person).

## Gate rule

- If all three passages still keep Candidate B's own character and fit a
  reflective podcast:

  `CANDIDATE B = PROMISING BASELINE`

- If only the Phase 40A clip sounded good but these three sound generic:

  `CANDIDATE B = CONTRAST EFFECT / UNSTABLE`

Candidate B is NOT developed further until you complete this review.

`CANDIDATE B CROSS-TEXT VALIDATION: PENDING HUMAN QA`