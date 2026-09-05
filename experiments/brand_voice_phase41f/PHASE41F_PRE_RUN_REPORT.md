# Phase 41F Static Pre-Run Report

## Status

**PHASE41F STATIC PREFLIGHT: PASS**

This phase is static only at this checkpoint. No TTS inference and no FFmpeg audio transformation were run while preparing this report.

## Phase 41E human result and frozen winner

- Blind human winner: `04.wav`
- Saved Phase 41E mapping: Blind 04 = `v3_semantic_focus`
- Frozen designation: **PHASE41E PROSODY WINNER = `v3_semantic_focus`**
- Human positive finding: semantic emphasis / semantic stress is successful and quite good.
- Remaining issue: the overall delivery is slightly too fast.

The winning chunk structure and emphasis behavior will not be redesigned or rerendered in Phase 41F. Candidate 03's embedding and reference codes remain frozen.

## Exact winning source

- Path: `experiments/brand_voice_phase41e/audio/v3_semantic_focus_final.wav`
- SHA256: `51e4bd659d4d3d9d9dae236f08d5d6c9aaa704cf825553cd81cf5707bb874569`
- Duration: 68.88 seconds
- Format: mono, 48,000 Hz, PCM16 WAV
- Phase 41E structure: 8 focus-aware chunks, zero inserted manual silence

The path, SHA256, duration, and Blind 04 mapping were verified directly from the saved mapping, manifest, checkpoint, and WAV on disk.

## Phase 41F isolation design

All four Phase 41F candidates derive from the exact same frozen source waveform:

| Output | FFmpeg tempo | Intended change | Expected duration |
|---|---:|---|---:|
| `baseline.wav` | 1.00x | Byte-identical file copy | 68.880000s |
| `tempo_98.wav` | 0.98x | 2% slower | 70.285714s |
| `tempo_96.wav` | 0.96x | 4% slower | 71.750000s |
| `tempo_94.wav` | 0.94x | 6% slower | 73.276596s |

Expected duration is calculated as `68.88 / tempo`. Actual encoded duration may differ by a small number of samples because `atempo` operates in finite analysis windows; the post-run manifest will record measured durations.

This design removes unseeded TTS generation from the comparison. The semantic emphasis, chunk rendering, voice identity, waveform content, EQ, level policy, and compression policy all share one source. Only temporal delivery changes. No candidate is slower than 0.94x.

## FFmpeg audit

- Executable: `/usr/bin/ffmpeg`
- Installed version: 8.1.2
- `atempo` filter: available
- Supported local range reported by FFmpeg: 0.5 to 100
- Requested range: 0.94 to 1.00

FFmpeg `atempo` changes tempo without the linked pitch change produced by naive resampling. The script does not request pitch shifting, resampling-based slowdown, formant adjustment, EQ, normalization, compression, or loudness processing. “Pitch-preserving” does not imply mathematically lossless transformation: non-baseline candidates necessarily pass through a time-scale-modification algorithm and PCM re-encoding.

Exact filter commands prepared by the script are equivalent to:

```bash
ffmpeg -nostdin -hide_banner -loglevel warning -y -i SOURCE -map_metadata -1 -filter:a "atempo=0.98" -ar 48000 -ac 1 -c:a pcm_s16le tempo_98.wav
ffmpeg -nostdin -hide_banner -loglevel warning -y -i SOURCE -map_metadata -1 -filter:a "atempo=0.96" -ar 48000 -ac 1 -c:a pcm_s16le tempo_96.wav
ffmpeg -nostdin -hide_banner -loglevel warning -y -i SOURCE -map_metadata -1 -filter:a "atempo=0.94" -ar 48000 -ac 1 -c:a pcm_s16le tempo_94.wav
```

`baseline.wav` is created as a byte-identical copy rather than passed through FFmpeg.

## Script safety and post-transform blind design

Prepared script: `experiments/brand_voice_phase41f/run_phase41f_tempo.sh`

Before writing audio, it requires FFmpeg/FFprobe and verifies the source SHA256. It writes transformed audio to temporary files and then atomically renames them. It verifies mono 48 kHz PCM16 output, records source/output hashes and measured durations in `manifest.json`, and verifies that the baseline remains byte-identical.

After transformation, the script creates `blind/01.wav` through `blind/04.wav`. It randomizes the candidate mapping once with `secrets.SystemRandom`, stores the mapping separately in `blind_mapping.json`, and preserves an existing valid mapping rather than reshuffling on rerun. Listener-facing filenames and the review sheet do not reveal tempo values.

The blind review asks:

1. Which pace feels most natural?
2. Which keeps the good emphasis of Phase 41E?
3. Which is easiest to listen to long-term?
4. At what point does it start feeling artificially slow?

## Static checks

- Phase 41E Blind 04 mapping verified: **PASS**
- Winning source path/hash/duration verified: **PASS**
- Winning V3 structure frozen: **PASS**
- Canonical Candidate 03 hashes unchanged: **PASS**
- FFmpeg 8.1.2 available: **PASS**
- FFmpeg `atempo` available: **PASS**
- All four candidates use one exact source: **PASS**
- Baseline specified as byte-identical copy: **PASS**
- Pitch-preserving tempo commands prepared: **PASS**
- No TTS call in Phase 41F script: **PASS**
- No audio transformation run during static preflight: **PASS**
- Blind one-time randomization and review template prepared: **PASS**

## External execution command

Close VS Code/Codex, then run:

```bash
cd "/home/tung/ai voice" && bash experiments/brand_voice_phase41f/run_phase41f_tempo.sh
```

STOP BEFORE TRANSFORMATION.
