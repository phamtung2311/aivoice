# Phase 35B — Continuity Recovery

## Phase 35 mapping

`Clip_A = current_240`, `Clip_B = one_sentence_per_call`, `Clip_C = adaptive_single_1000`.

All were rejected. None is promoted. Phase 34 Clip C remains the recovery anchor.

## What changed in Phase 35 versus the real winner

Phase 34 Clip C used a 665-character, 42.48-second passage, seed 34001, current outer 240 grouping (four calls), Candidate 03 frozen conditioning and 0.82/25/0.97/1.15 decoding. Phase 35 used a different 351-character, 25.2-second passage, seed 35001 and architectures of two, three, or one call. It retained the same identity, decoding, speed 1.0, format and audition gain policy.

Therefore degradation cannot be assigned to utterance length: text, seed and architecture all changed. Phase 35’s single-call result also does not demonstrate that fewer calls are better.

## Recovery anchor

`BEST_KNOWN_BRAND_VOICE_CHECKPOINT/` preserves the exact Phase 34 Clip C audition WAV, paired Candidate 03 embedding/codes, Phase 34 metrics and SHA-256 manifest. It is never overwritten.

## Length/grouping evidence

The installed runtime has no hard app requirement for 240 characters; it has a default internal 256-character grouping. Phase 35B does not claim a universal optimum. It holds a new 277-character passage, seed and decoding fixed and compares only grouping:

| Private strategy | Calls | Duration | Result to listen for |
| --- | ---: | ---: | --- |
| A — current 240 | 2 | 19.20 s | current control |
| B — sentence calls | 3 | 20.08 s | sentence reset cost |
| C — two related sentences | 2 | 19.20 s | semantic grouping |
| D — single 350 | 1 | 18.16 s | longest tested unit |

All four are 48 kHz mono and zero-clipped. This is evidence about a narrow 277-character test only; human listening decides whether any grouping is acceptable. Assembly is not the demonstrated dominant fault: the same conditioning/decode can sound different because a model utterance’s native prosody resets at independent calls. No trim/crossfade was applied.

Production remains unchanged.
