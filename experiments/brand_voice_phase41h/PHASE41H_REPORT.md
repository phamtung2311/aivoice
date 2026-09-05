# Phase 41H — Final report

## Human result

**PHASE41H HUMAN WINNER = V2**  
**LONG-FORM CADENCE = PASS**

The selected V2 Natural Podcast Cadence resolves the Phase 41G complaint that the long-form delivery felt too continuous and lacked enough breathing space between ideas. The winning intervention changes assembly-layer pauses only.

## Frozen current stack

CURRENT BEST LONG-FORM RENDERING STACK:

- Synthetic Candidate 03
- Phase41E `v3_semantic_focus`
- Phase41F `0.98x` tempo
- Phase41H V2 semantic pause cadence

Candidate 03 remains:

- `status = candidate`
- `is_final_brand_voice = false`

This result does not promote Candidate 03 to final brand voice.

## Winning WAV

- Path: `experiments/brand_voice_phase41h/audio/v2_natural.wav`
- SHA256: `66a51b4ccedccec6016cc778ddafceaf4c0d42fad741ad36f711a7d25ef8dce5`
- Duration: `450.685375 s`
- Frames: `21,632,898`
- Format: 48,000 Hz, mono, 16-bit PCM
- Peak: `-0.005038 dBFS` (`32749` PCM16)
- Clipped samples: `0`

The pre-tempo V2 assembly is `experiments/brand_voice_phase41h/audio/pretempo/v2_natural.wav`, SHA256 `435850fdc0ae61d854812809c2532a9fb66616cec6c9a682856e54a80fb38b63`, duration `441.680000 s`. FFmpeg `atempo=0.98` was applied once to the complete assembly.

## Exact V2 pause policy

These values are explicit additional silence inserted before the final tempo operation. Existing chunk-edge waveforms remain untouched.

| Boundary class | Count | Addition per boundary | Total addition |
|---|---:|---:|---:|
| Semantic thought boundary | 31 | +0.10 s | 3.10 s |
| Setup→resolution boundary | 7 | +0.06 s | 0.42 s |
| Standalone thought transition | 0 | +0.22 s | 0.00 s |
| Paragraph transition | 16 | +0.32 s | 5.12 s |
| **Total** | **54** | — | **8.64 s** |

The source contains 17 paragraphs. All 16 Phase 41G `thought_transition` labels coincide with paragraph crossings and are therefore classified as `paragraph_transition` for assembly. The final `paragraph_end` follows chunk 54 and has no subsequent chunk.

## Source integrity and isolation

- Frozen source: the exact 55 Phase 41G chunk WAVs
- On-disk hashes matching Phase 41H manifest: `55/55` — **PASS**
- Phase 41G manifest SHA256: `46bdd3834f050fd918af98488984f112a7dda0370b30d6ab2135b2d00bd4dd02`
- Phase 41G semantic plan SHA256: `67b4d48416ccb47b4f2586c9188cf313d30836554241a757a85152f6802196d9`
- New TTS inference: **NONE**
- Speaker embedding/reference codes changed: **NO**
- Semantic-focus structure or lexical content changed: **NO**
- Global tempo lowered beyond 0.98x: **NO**
- Pitch, formants, EQ, loudness, or compression changed intentionally: **NO**

Phase 41H therefore isolates explicit semantic pause cadence at the assembly layer while preserving the selected voice identity, generated chunk realizations, semantic emphasis, and tempo.

## Final designation

PHASE41H HUMAN WINNER = V2  
LONG-FORM CADENCE = PASS
