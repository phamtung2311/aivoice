# Selected Phase 34 Clip C timeline

Clip C is Phase 34 Strategy A (current baseline). It made four outer `TTSEngine.generate()` calls/chunks, ending on sentence punctuation. No semantic markers were used and the app joiner inserted zero milliseconds at all three boundaries.

| Boundary | Chunk end | Next voiced onset | Effective generated edge silence | Joiner |
| --- | ---: | ---: | ---: | ---: |
| 0 → 1 | 00:14.240 | 00:14.359 | 227.75 ms | 0 ms |
| 1 → 2 | 00:27.600 | 00:27.819 | 356.75 ms | 0 ms |
| 2 → 3 | 00:38.720 | 00:38.967 | 352.52 ms | 0 ms |

These are audible-region edge measurements. The long low-energy regions in the complete waveform include native intra-chunk punctuation pauses as well; waveform appearance alone does not label them as joins.
