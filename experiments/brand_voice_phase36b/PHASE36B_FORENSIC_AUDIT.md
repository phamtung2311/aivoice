# Phase 36B forensic audit

## Blind mapping

- Clip A = VieNeu
- Clip B = Gwen

## Trace result

`run_cpu_short_benchmark.py` passed the Vietnamese benchmark as `text=TEXT`, the pristine Candidate 03 source WAV as `ref_audio`, and its English transcript as `ref_text`. They were not swapped.

The Gwen raw WAV is not the source/reference WAV: it has a different SHA-256, duration (9.200 s versus 6.960 s) and sample count. Step C copied `gwen.wav` only for blind Clip B, and VieNeu only for Clip A.

The target text received no Gwen-specific normalization beyond its existing Unicode form. More importantly, the actual call omitted the explicit `language="Vietnamese"` argument. Gwen's official README example passes that argument; the cloned repository's helper has the same argument commented out. This is a concrete configuration/preprocessing mistake consistent with language-tokenizer selection falling back incorrectly.

## Classification

`CONFIG/PREPROCESSING ERROR`

The smallest correction is to pass `language="Vietnamese"` to `generate_voice_clone` and use a documented Vietnamese normalization path. This audit does not generate again. Candidate 03, the Phase 34 checkpoint and production remain untouched.
