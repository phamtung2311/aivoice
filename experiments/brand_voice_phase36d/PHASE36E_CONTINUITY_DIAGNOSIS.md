# Phase 36E — VietVoice continuity diagnosis

## Baseline preserved

The immutable Phase 36D baseline is:

`experiments/brand_voice_phase36d/output/vietvoice_candidate03_raw.wav`

No baseline sample, Candidate 03 asset, production file, or third-party VietVoice source was changed.

## 1. Measured silence structure

Measurement uses the baseline WAV only: mono 24 kHz waveform, 20 ms RMS frames at 10 ms hops, low-energy threshold -40 dBFS. Positions are approximate because waveform analysis cannot assign words with certainty.

| Region (s) | Duration | Interpretation from waveform + target order |
|---|---:|---|
| 0.00–1.16 | 1.16 s | Leading generated silence. |
| 1.69–2.06 | 0.37 s | Internal low-energy gap; no source punctuation is available at this early point. |
| 2.60–3.40 | 0.80 s | Internal low-energy gap; no punctuation boundary. |
| 3.79–4.47 | 0.68 s | Internal low-energy gap; no punctuation boundary. |
| 4.70–5.01 | 0.31 s | Internal low-energy gap; no punctuation boundary. |
| 5.46–6.39 | 0.93 s | Longest internal gap. It most likely corresponds to the comma after `mạch,`: that boundary follows roughly two-thirds of the 15 target words. This is an inference, not alignment proof. |
| 6.98–7.12 | 0.14 s | Brief internal gap; no punctuation boundary. |
| 7.54–7.75 | 0.21 s | Ending silence. |

The threshold gives effectively the same major regions from -50 to -30 dBFS. About 3.23 seconds of the 7.75-second output are identifiable internal low-energy intervals. The comma is a plausible contributor to the single longest pause, but several material pauses occur with no punctuation. Therefore comma handling alone cannot explain the full continuity failure.

## 2. Exact text and pause path

Call path:

`TTSApi.synthesize_to_file()` → `TTSApi.synthesize()` → `TTSEngine.synthesize()` → `TTSEngine._prepare_inputs()` → ONNX `preprocess` / repeated `transformer` / `decode` sessions → `AudioProcessor.save_audio()`.

### Text preprocessing

`TextProcessor.clean_text()`:

- retains Vietnamese letters, ASCII letters/numbers, spaces and ` .,!?'@$%&/:;()`;
- replaces invalid characters with spaces;
- replaces `;`, `:`, `(` and `)` with comma;
- collapses duplicate periods/commas and whitespace;
- appends a final period only when the text lacks `.`, `?`, `!`, or `,`.

The baseline comma is therefore preserved unchanged and is sent as a model text character. There is no code that inserts an audio pause for comma, period, or any other punctuation.

### What `pause_punctuation = ".,?!:"` really does

It is used only in `TextProcessor.calculate_text_length()` for duration/chunk estimation. It is passed to `re.findall()` as a regular expression. As written it is malformed for a punctuation character set: the leading `.` is a wildcard and the expression requires a later `!:` sequence. The baseline reference and target both produce **zero matches**, so no punctuation weighting was applied in this render.

It is not used to create audio silence, punctuation labels, prosody control, or post-generation timing.

### Chunking, crossfade and silence trim

- The logged `Single chunk` branch sets exactly `chunks = [target_text]`.
- The code invokes one preprocess/transformer/decode sequence and `concatenate_with_crossfade_improved()` returns the single wave unchanged except flattening. No crossfade executes for one wave.
- No silence trimming exists in the installed source.
- `cross_fade_duration` only applies when there are multiple generated waves.
- `max_chunk_duration=15` only chooses the single-versus-multiple-chunk branch. At the estimated 14.72 seconds (reference + target), it does not otherwise affect generated prosody.

Classification: the internal pauses in this baseline are **model-generated under a requested target duration**. They are not code-inserted nor post-processing artifacts.

## 3. Exact duration-estimation mechanism

`TTSEngine._prepare_inputs()` does not use phoneme or ONNX-predicted duration. It calculates:

```text
speaking_rate = weighted_UTF8_byte_length(reference_text) / reference_audio_duration
target_duration = max(weighted_UTF8_byte_length(target_text) / speaking_rate / speed, 1.0)
```

For this run:

| Input | UTF-8 bytes | `pause_punctuation` matches | Weighted length |
|---|---:|---:|---:|
| Canonical English reference | 87 | 0 | 87 |
| Vietnamese target | 97 | 0 | 97 |

Reference duration is 6.96 seconds, so the code computes `87 / 6.96 = 12.5` weighted bytes/s. At speed 1.0 it requests `97 / 12.5 = 7.76` seconds of target audio. The actual WAV duration is 7.754667 seconds, confirming that the ONNX input length is being tightly driven by this reference-byte heuristic.

The reference duration therefore directly affects target duration. Vietnamese UTF-8 diacritics increase byte count relative to English, so an English reference transcript can inflate a Vietnamese target's requested duration even with a relatively short target sentence. This supports the stretched/fragmented perception but does not prove how each individual pause is allocated by the model.

## 4. One-variable continuity experiment

Selected test: **remove only the comma**.

| Field | Baseline | Phase 36E probe |
|---|---|---|
| Target text | `Một câu chuyện rõ ràng cần được kể liền mạch, có điểm nhấn đúng chỗ.` | `Một câu chuyện rõ ràng cần được kể liền mạch có điểm nhấn đúng chỗ.` |
| Reference / identity / transcript | Frozen Candidate 03 | Unchanged |
| Seed, speed, NFE, fuse, provider | 9527, 1.0, 32, 1, CPU | Unchanged |
| Expected heuristic duration | 7.76 s | 7.68 s (one fewer UTF-8 byte) |
| Hypothesis isolated | The model interprets the comma as the longest generated pause. | Same |

This is preferred over speed manipulation now because the comma is the only textual boundary correlating with the longest measured silence. It does **not** claim to solve the other non-punctuation gaps. No parameter grid, speaker change, post-processing, or source modification is involved.

Prepared output (no overwrite):

`experiments/brand_voice_phase36d/output/vietvoice_candidate03_phase36e_comma_removed.wav`

## Execution

CPU synthesis previously took about 140 seconds, and the agent environment has interrupted long generations. The one expensive render must be run manually with:

```bash
cd '/home/tung/ai voice' && experiments/brand_voice_phase36d/.venv_py312/bin/python experiments/brand_voice_phase36d/run_vietvoice_continuity_punctuation_probe.py
```

The script rejects an existing output, performs exactly one synthesis, and writes raw WAV plus metrics. It does not generate a VieNeu control or modify production.
