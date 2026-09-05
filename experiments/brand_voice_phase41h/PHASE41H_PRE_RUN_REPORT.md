# Phase 41H — Static pre-run report

## Objective and frozen stack

Phase 41G human QA found the 7+ minute narration too fast and continuous: 0.98x tempo alone did not provide enough breathing room between ideas. Phase 41H isolates semantic pause cadence without changing articulation tempo or regenerating speech.

The frozen stack is Synthetic Candidate 03 + Phase41E `v3_semantic_focus` + Phase41F `0.98x`. Candidate 03 remains `status = candidate` and `is_final_brand_voice = false`.

No TTS inference is part of this phase. All candidates must reuse the exact 55 Phase 41G chunk WAVs. Speaker embedding, reference codes, lexical content, chunking, focus behavior, pitch, formants, EQ, loudness, and compression remain unchanged. `atempo=0.98` is applied exactly once, after complete assembly—not to individual chunks.

## Source integrity

- Phase 41G semantic plan SHA256: `67b4d48416ccb47b4f2586c9188cf313d30836554241a757a85152f6802196d9`
- Phase 41G manifest SHA256: `46bdd3834f050fd918af98488984f112a7dda0370b30d6ab2135b2d00bd4dd02`
- Phase 41G original WAV SHA256: `df05aac12b2a48a4b80fe9d7502f3585af813f075268b3bccd1bdebda515d25b`
- Original assembled duration: `433.040000 s`
- Existing Phase 41G 0.98x WAV SHA256: `b6da66aed6d371176a8d3223e332b1c904ef64639416251811e96ba9521f6e6a`
- Existing Phase 41G 0.98x duration: `441.8669375 s`
- Source format: 48,000 Hz, mono, 16-bit PCM
- Chunk count: 55
- On-disk chunk hashes matching the 55 Phase 41G manifest entries: 55/55 (PASS)

The external runner revalidates the manifest/plan hashes, every chunk hash, WAV parameters, chunk count, and V0 pre-tempo reconstruction hash before invoking FFmpeg.

## Current effective-gap audit

This audit is labeled **SIGNAL-LEVEL EDGE SILENCE HEURISTIC**. Split each mono PCM16 chunk into non-overlapping 10 ms frames. From each file edge, count contiguous complete frames with RMS at or below `-45 dBFS` (`32768 × 10^(-45/20)`). At a boundary, the diagnostic edge duration is the preceding chunk's trailing low-energy duration plus the following chunk's leading low-energy duration. Resolution is 10 ms.

This is an amplitude-based engineering heuristic, not phonetic segmentation or a perceived semantic gap. Low-energy speech tails, breaths, room tone, and silence can be conflated. The listener's report that V0 remains too continuous is authoritative. These measurements remain diagnostic only and are not subtracted from Phase 41H's explicit pauses.

| Boundary set | Count | Min | Median | Mean | Max |
|---|---:|---:|---:|---:|---:|
| All inter-chunk boundaries | 54 | 0.240 s | 0.300 s | 0.304815 s | 0.550 s |
| `semantic_thought_boundary` | 31 | 0.240 s | 0.300 s | 0.309355 s | 0.550 s |
| `setup_resolution_boundary` | 7 | 0.270 s | 0.290 s | 0.294286 s | 0.320 s |
| Source `thought_transition` | 16 | 0.250 s | 0.295 s | 0.300625 s | 0.430 s |
| Derived `paragraph_transition` | 16 | 0.250 s | 0.295 s | 0.300625 s | 0.430 s |

The source text has 17 paragraphs and 16 paragraph crossings. Phase 41G labels every one of those crossings `thought_transition`. Phase 41H retains that source label in `pause_plan.json` but derives the separate assembly class `paragraph_transition`. No standalone major `thought_transition` exists in this source. The one final `paragraph_end` follows chunk 54, where there is no following chunk and therefore no inter-chunk pause insertion.

Boundary counts used for assembly are: 31 semantic, 7 setup→resolution, 0 standalone thought transitions, and 16 paragraph transitions, for 54 inter-chunk boundaries. Final paragraph-end count is 1 and is reported separately.

## Exact pause policies and expected effects

All values below are explicit additional silence inserted before the final 0.98x process. Existing chunk-edge samples remain untouched, and their measured low-energy duration is not subtracted. This deliberately tests additional semantic breathing space at the assembly layer; the values are experimental heuristics, not scientifically derived timing.

| Variant | Semantic | Setup→resolution | Thought transition | Paragraph transition | Boundaries changed | Added silence | Average/boundary |
|---|---:|---:|---:|---:|---:|---:|---:|
| V0 current | 0.00 s | 0.00 s | 0.00 s | 0.00 s | 0 | 0.000 s | 0.000000 s |
| V1 light | 0.06 s | 0.04 s | 0.14 s | 0.22 s | 54 | 5.660 s | 0.104815 s |
| V2 natural | 0.10 s | 0.06 s | 0.22 s | 0.32 s | 54 | 8.640 s | 0.160000 s |
| V3 spacious | 0.14 s | 0.08 s | 0.30 s | 0.42 s | 54 | 11.620 s | 0.215185 s |

Added-time breakdown is V1: semantic 1.860 s, setup→resolution 0.280 s, standalone thought 0.000 s, paragraph 3.520 s; V2: 3.100 s, 0.420 s, 0.000 s, 5.120 s; V3: 4.340 s, 0.560 s, 0.000 s, 6.720 s. Setup→resolution remains the shortest class in every experimental variant, preserving connection and avoiding theatrical emphasis.

The strength check passes: V1 adds several seconds, V2 adds 8.640 s before atempo and exceeds V0 by an expected 8.816327 s after atempo, and V3 is meaningfully more spacious than V2.

## Expected durations

| Variant | Before 0.98x | Expected after 0.98x |
|---|---:|---:|
| V0 current | 433.040 s | 441.8669375 s |
| V1 light | 438.700 s | 447.6424477 s |
| V2 natural | 441.680 s | 450.6832640 s |
| V3 spacious | 444.660 s | 453.7240804 s |

Post-tempo values are calibrated from the already observed Phase 41G V0 FFmpeg output, adding inserted duration divided by 0.98. Exact future results may differ by a few samples because of FFmpeg filter buffering.

## Output and blind design

The runner will create `audio/v0_current.wav`, `audio/v1_light.wav`, `audio/v2_natural.wav`, and `audio/v3_spacious.wav`, then a one-time randomized `blind/01.wav` through `blind/04.wav`. The mapping is saved only in `blind_mapping.json`; listener filenames and WAV metadata do not identify variants. If a mapping already exists, the runner validates and reuses it rather than randomizing again.

After execution, `manifest.json` will record actual durations, added-pause counts, gap metrics, SHA256, peak/clipping, and source chunk integrity. No TTS metrics are applicable because no synthesis occurs.

## External execution

FFmpeg 8.1.2 is installed and exposes the pitch-preserving `atempo` audio filter. The exact filter invocation used for each completely assembled waveform is equivalent to:

```text
ffmpeg -hide_banner -loglevel error -y -i <pretempo.wav> -map_metadata -1 -af atempo=0.98 -c:a pcm_s16le -ar 48000 -ac 1 <final.wav>
```

Run externally from the repository root:

```bash
python3 experiments/brand_voice_phase41h/run_phase41h_pause.py --execute
```

Static preflight only is complete. No Phase 41H audio or blind mapping has been created yet.
