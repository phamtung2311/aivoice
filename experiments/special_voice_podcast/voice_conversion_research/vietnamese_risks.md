# Vietnamese / tonal-language risks

VC language independence does not prove Vietnamese quality. Relevant risks are
tone flattening/replacement, wrong F0 contour, vowel/consonant distortion,
speaker leakage, metallic vocoder artifacts, and unstable breathiness. A bad VC
WAV would contaminate the later VieNeu reference.

Source preservation generally remains substantial for F0/tone, rhythm, prosody,
energy, and emotion; timbre/speaker identity is the intended transformation.

`VieNeu preset → VC → VieNeu clone` is **HIGH_RISK**: source quality is clean,
but generic TTS prosody and codec/VC artifacts can compound on re-cloning.
