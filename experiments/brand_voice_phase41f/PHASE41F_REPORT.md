# Phase 41F Final Report

## Result

**PHASE41F HUMAN QA: PASS**

The blind human winner is `03.wav`. The saved one-time mapping identifies Blind 03 as `tempo_98`, the 0.98x pitch-preserving tempo candidate.

Human feedback: “03 nghe là hợp lý nhất.” The resulting conclusion is that 0.98x provides the most reasonable and natural pace among the four Phase 41F choices while retaining the semantic emphasis that won Phase 41E.

No TTS inference and no new FFmpeg transformation were run during this reveal/freeze step.

## Frozen rendering stack

**CURRENT BEST PODCAST RENDERING STACK =**

Synthetic Candidate 03  
+ Phase41E `v3_semantic_focus`  
+ Phase41F `0.98x` winning tempo

The Phase 41E V3 chunk structure, generated prosody, semantic stress, speaker embedding, and reference codes remain frozen. Phase 41F changes only temporal delivery by deriving every candidate from the same exact Phase 41E waveform.

Candidate 03 remains:

- `status = candidate`
- `is_final_brand_voice = false`

This human result selects the best current rendering stack; it does not promote Candidate 03 to final brand voice status.

## Blind winner mapping

- PHASE41F BLIND WINNER: `03`
- Mapped candidate: `tempo_98`
- Winning tempo: `0.98x`
- Transform method: FFmpeg `atempo=0.98`
- Human conclusion: pace feels most reasonable/natural

## Exact winning WAV

- Path: `experiments/brand_voice_phase41f/audio/tempo_98.wav`
- SHA256: `a643129523b912e9e8efc06f25746a09d45efd8862d0ac58534a1e7d212bc423`
- Measured duration: `70.27408333333334` seconds
- Format: mono, 48,000 Hz, PCM16 WAV
- Blind copy: `experiments/brand_voice_phase41f/blind/03.wav`
- Blind-copy SHA256: `a643129523b912e9e8efc06f25746a09d45efd8862d0ac58534a1e7d212bc423`

## Frozen Phase 41E source

- Variant: `v3_semantic_focus`
- Path: `experiments/brand_voice_phase41e/audio/v3_semantic_focus_final.wav`
- SHA256: `51e4bd659d4d3d9d9dae236f08d5d6c9aaa704cf825553cd81cf5707bb874569`
- Duration: `68.88` seconds

The Phase 41F manifest binds the winning WAV to this source hash. The 0.98x result is about 1.394083 seconds longer than the source; its measured duration is 0.011631 seconds shorter than the mathematical estimate of 70.285714 seconds because FFmpeg `atempo` operates with finite processing windows.

## Candidate audit trail

| Candidate | Tempo | Expected duration | Measured duration | SHA256 |
|---|---:|---:|---:|---|
| `baseline` | 1.00x | 68.880000s | 68.880000s | `51e4bd659d4d3d9d9dae236f08d5d6c9aaa704cf825553cd81cf5707bb874569` |
| `tempo_98` | 0.98x | 70.285714s | 70.274083s | `a643129523b912e9e8efc06f25746a09d45efd8862d0ac58534a1e7d212bc423` |
| `tempo_96` | 0.96x | 71.750000s | 71.740146s | `8b44fa8f28d714b24fda4e5df6ddc892b901dfdced9d8191fb0b083ff8ab8733` |
| `tempo_94` | 0.94x | 73.276596s | 73.270729s | `518690838c166c8d677942017ce154fc98117614733853d4b0782c8edc764c43` |

## Integrity and isolation

- Blind 03 mapping matches `tempo_98`: **PASS**
- Blind 03 and winning source-copy hashes match: **PASS**
- Winning WAV hash and duration match `manifest.json`: **PASS**
- Phase 41E source SHA256 matches the frozen manifest source: **PASS**
- Phase 41E `v3_semantic_focus` prosody preserved: **PASS**
- Candidate 03 embedding/reference identity remains frozen: **PASS**
- No TTS rerender in Phase 41F: **PASS**
- No new FFmpeg transform during winner reveal: **PASS**
- Candidate remains unpromoted: **PASS**

## Final designation

CURRENT BEST PODCAST RENDERING STACK =
Synthetic Candidate 03
+ Phase41E v3_semantic_focus
+ Phase41F 0.98x winning tempo

PHASE41F BLIND WINNER = 03  
WINNING TEMPO = 0.98x
