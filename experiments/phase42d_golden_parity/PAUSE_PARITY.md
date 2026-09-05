# Phase 42D — Pause and tempo parity

## Result

**PASS**

The repaired Phase 41G regression plan emits:

| Boundary after current chunk | Count | Explicit addition | Total |
|---|---:|---:|---:|
| semantic thought | 31 | 0.10 s | 3.10 s |
| setup→resolution | 7 | 0.06 s | 0.42 s |
| paragraph transition | 16 | 0.32 s | 5.12 s |
| final | 1 | 0.00 s | 0.00 s |
| **Total** | **55 chunks / 54 gaps** | — | **8.64 s** |

The pause is stored on the current `RenderSegment` and written immediately after that chunk. The assembler checks that the chunk is not last, inserts the configured number of zero PCM frames, and does not measure or subtract existing waveform-edge silence.

Automatic Podcast Brand Voice mode ignores `tts_script`, `prosody_markup`, and `| / || / |||` markers. These cannot shift or replace automatic semantic pauses.

Tempo order remains:

semantic chunks
→ original-speed TTS
→ complete ordered assembly plus 8.64 s explicit V2 pauses
→ one final full-waveform `ffmpeg atempo=0.98`.

There is no per-chunk time stretch and no extra application of the ordinary UI speed.

