# VieNeu V3Turbo speaker audit

Each installed preset is a float32 `speaker_emb` `[192]` plus int64 reference
`codes` `[T,16]`. The frozen ONNX speaker encoder creates the x-vector from
16-kHz, 80-bin Kaldi fbank features. `prepare_reference()` loads a WAV, trims to
eight seconds, optionally denoises, then creates both the x-vector and MOSS
codec codes from the same reference.

```text
reference WAV → speaker encoder → speaker_emb [192]
              → MOSS codec      → ref_codes [T,16]
```

The learned x-vector projection is added to every model-input row. Reference
codes become in-context audio-code rows when enabled. Codes are time-varying
acoustic tokens; source does not separate their identity, prosody, content, and
style contribution. A nonzero arbitrary vector passes basic sanitation, but the
source supplies no speaker prior, sampler, new-speaker API, seed, or support for
interpolation/mixing. Therefore VieNeu is reference-conditioned for new identity
creation; mixing anchors/codes from different references is unsupported.
