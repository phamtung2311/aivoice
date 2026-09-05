# PHASE 40C — PODCAST BRAND SIGNATURE REFINEMENT

## 1. Phase 40B final human result

```
CANDIDATE B = PROMISING BASELINE
```

This baseline remains the strongest evidence in the project for a stable, natural, podcast-suitable Vietnamese narrator.

## 2. Verified canonical baseline hashes

Canonical Candidate B baseline is located at:

```
experiments/brand_voice_phase40b/baseline/PODCAST_CANDIDATE_B_BASELINE/
```

Verified with the project .venv runtime under the same Onnx/CPU/VieNeu 3.3.0 setup:

```
speaker_emb.npy
  file_sha256: 09ce43e1facce2878df2e4bc78581213804d1beca638e6861f8794ba3f63986e
  array_sha256: 0c0cbc23228c89cfc27b0d109603b42b3fa0ca071cf728801455ec2cae752b53

reference_codes.npy
  file_sha256: fe8f8e3e1766a7954595fa3a355e46aca8c3e27be4aba4bb1db8d9b60a960aa5
  array_sha256: 38964457925e5cf4362c90026e4bf552ddf1cf6acc35bc9555cd06c12603efb8
```

These match the required canonical hashes from the project evidence.

## 3. Exact shared Vietnamese audition text

```
Người ta hay nghĩ rằng một giọng nói tốt là giọng vang to. Nhưng thật ra, giọng podcast tốt là giọng biết dừng lại đúng lúc, đặt câu hỏi đúng chỗ, và để người nghe cảm nhận được một sự thật không cần ai nhấn mạnh. Khi ta lắng nghe đủ sâu, ta sẽ thấy rằng mỗi sự suy ngẫm đều mang trong mình một lý do để sống chậm, sống rõ, và sống có trách nhiệm.
```

This text is fixed for all four audition files.

## 4. Baseline embedding formula

```
B = 0.75 × Phạm Tuyên + 0.25 × Thanh Bình
```

This is the original Candidate B anchor. The canonical `.npy` asset was not modified.

## 5. R1 / R2 / R3 formulas

```
R1 = 0.82 × Phạm Tuyên + 0.18 × Thanh Bình
R2 = 0.68 × Phạm Tuyên + 0.32 × Thanh Bình
R3 = 0.70 × Phạm Tuyên + 0.20 × Thanh Bình + 0.10 × Minh Đức
```

All are convex blends. No negative coefficients. No extrapolation beyond observed preset space.

## 6. Explanation for each local latent move

### R1 — More Phạm Tuyên identity
- Slightly stronger personal narrator identity
- Keeps the storytelling anchor close to B
- Purpose: test whether a clearer brand fingerprint can emerge without losing naturalness

### R2 — Slightly more Thanh Bình body
- Adds more storytelling body and maturity
- Purpose: test whether a deeper, grounded cadence helps podcast fit while staying near the same identity

### R3 — Controlled third-anchor perturbation
- Uses a small Northern male adjustment around the B neighborhood
- Purpose: test whether brand distinctiveness improves via a subtle, controlled third anchor without losing stability or Vietnamese naturalness

## 7. Proof that reference codes remained identical

Canonical reference-code asset used for all outputs:

```
reference_codes.npy
array_sha256: 38964457925e5cf4362c90026e4bf552ddf1cf6acc35bc9555cd06c12603efb8
```

Every generated refinement reused the same fixed codes from Candidate B. No reference-code change occurred.

## 8. Generation settings

Exact stable config kept fixed across baseline and refinements:

```text
denoise: True
use_ref_codes: True
temperature: 0.8
top_k: 25
top_p: 0.95
max_new_frames: 300
repetition_penalty: 1.2
repetition_window: 64
max_chars: 256
silence_p: 0.15
crossfade_p: 0.0
apply_watermark: True
batch_size: None
backend: ONNX / CPU
sample_rate: 48 kHz
```

Only `speaker_emb` changed. No model changes, training, cloud/GPU use, or production replacement.

## 9. Generation metrics

Generated files:

- `audio/baseline_candidate_b.wav`
- `audio/refinement_r1.wav`
- `audio/refinement_r2.wav`
- `audio/refinement_r3.wav`

Observed metrics from the run:

```text
baseline_candidate_b.wav
  duration: 18.98 s
  generation_seconds: 11.784770
  rtf: 0.620905
  peak_abs: 0.924041748046875
  rms: 0.10548894102474653
  clipped_samples_abs_ge_0_999: 0

refinement_r1.wav
  duration: 18.02 s
  generation_seconds: 10.510757
  rtf: 0.583283
  peak_abs: 0.76824951171875
  rms: 0.10686139981756684
  clipped_samples_abs_ge_0_999: 0

refinement_r2.wav
  duration: 19.62 s
  generation_seconds: 11.189016
  rtf: 0.570286
  peak_abs: 0.9404296875
  rms: 0.09833187545203236
  clipped_samples_abs_ge_0_999: 0

refinement_r3.wav
  duration: 19.06 s
  generation_seconds: 10.846508
  rtf: 0.569072
  peak_abs: 0.88189697265625
  rms: 0.10314065181537524
  clipped_samples_abs_ge_0_999: 0
```

All WAVs are valid 48 kHz mono PCM-16 outputs with finite samples and no clipping above the tolerance thresholds used in the project.

## 10. Four audition WAVs and blind mapping

Primary four WAV files are in:

```
experiments/brand_voice_phase40c/audio/
```

Blind listening package:

```
experiments/brand_voice_phase40c/blind_audition/
```

Blind mapping saved in the registry:

```text
01.wav -> baseline_candidate_b.wav
02.wav -> refinement_r1.wav
03.wav -> refinement_r2.wav
04.wav -> refinement_r3.wav
```

## 11. Changed files / git status

Repository state was checked before making any Phase 40C change. We did not revert unrelated dirty files. The canonical Phase 40B baseline was not touched.

Created/updated for Phase 40C:

- `experiments/brand_voice_phase40c/generate_phase40c_refinements.py`
- `experiments/brand_voice_phase40c/manifest.json`
- `experiments/brand_voice_phase40c/provenance.json`
- `experiments/brand_voice_phase40c/PHASE40C_REPORT.md`
- `experiments/brand_voice_phase40c/audio/baseline_candidate_b.wav`
- `experiments/brand_voice_phase40c/audio/refinement_r1.wav`
- `experiments/brand_voice_phase40c/audio/refinement_r2.wav`
- `experiments/brand_voice_phase40c/audio/refinement_r3.wav`
- `experiments/brand_voice_phase40c/blind_audition/01.wav`
- `experiments/brand_voice_phase40c/blind_audition/02.wav`
- `experiments/brand_voice_phase40c/blind_audition/03.wav`
- `experiments/brand_voice_phase40c/blind_audition/04.wav`

No canonical Candidate B `.npy` or library voice assets were overwritten.

## 12. Current gate

```text
CANDIDATE B BRAND SIGNATURE REFINEMENT:
PENDING HUMAN QA
```

This phase does not auto-select a winner. A refinement wins only if the user clearly prefers it to the original Candidate B without damaging naturalness, stability, or long-form podcast comfort.

## STOP

```
KEEP CANDIDATE B IF NO CLEAR IMPROVEMENT EXISTS.
```

This is a successful outcome. The baseline remains the default channel voice unless a human clearly prefers a refinement.
