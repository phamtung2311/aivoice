# Phase 42D — Semantic planner parity

## Regression result

| Metric | Before Phase 42D | After Phase 42D |
|---|---:|---:|
| validated chunks | 55 | 55 |
| production chunks | 54 | 55 |
| matching inter-chunk boundaries | 47 | **54/54** |
| validated-only boundaries | 7 | **0** |
| production-only boundaries | 6 | **0** |
| exact validated TTS strings | 0/54 | **55/55** |
| paragraphs | 17 | 17 |
| lexical reconstruction | PASS | PASS |

Fixture:

- source: `experiments/brand_voice_phase41g/podcast_text.txt`
- stripped source SHA256: `04e27a95375cef05ff87bd2d930b581254f039350e092b1b2dd0939cefcfecb7`
- validated plan: `experiments/brand_voice_phase41g/semantic_plan.json`

## General reasons behind the former mismatches

The 13 symmetric boundary differences came from six recurring discourse patterns:

1. A short anaphoric state sentence and its following explanation were greedily attached backward instead of grouped as a new thought.
2. A “không phải … mà …” thesis was merged into the first item of a parallel example sequence.
3. Demonstrative/sequence transitions such as “Điều này”, “Sau đó”, and recurrence markers were allowed to land at the end of the previous chunk.
4. Terminal periods counted toward the 220-character packing ceiling, splitting a contrast pair that fits under the validated spoken-text policy.
5. A sequential next step was absorbed into a call-to-action chunk rather than beginning the following thought.
6. Closing recurrence/reflection sentences were greedily merged rather than given rhetorical boundaries.

## Repair strategy

The existing length-aware sentence packer remains. Phase 42D adds small general rules:

- remove sentence-terminal punctuation through one centralized semantic-to-TTS conversion before length decisions;
- start a new thought at selected anaphoric state labels and general sequence/recurrence/conclusion connectives;
- keep a leading `không phải … mà …` contrast thesis self-contained;
- classify setup boundaries using rhetorical-example, practical-setup, qualification, scenario, and adversative patterns;
- keep every paragraph boundary explicit.

No full fixture sentence, source-sentence ID, or Phase 41G chunk index is embedded in production code. The regression test reads the fixture separately and proves exact parity.

## TTS text policy

`semantic_chunk_to_tts_text` is the single conversion point. It:

- preserves every lexical token;
- preserves internal commas, semicolons, colons, and quotation marks;
- removes sentence-terminal `. ! ? …` exactly as the validated Phase 41G plan did;
- collapses whitespace only;
- never inserts manual pause markers.

After planning, production bypasses the generic local text preprocessing and splitter. VieNeu receives the approved chunk string directly.

