# Speaker anonymization research

VoicePrivacy 2024 B1 uses an external speaker pool to derive a pseudo-speaker
x-vector, then synthesizes source bottleneck/F0 features. This changes identity
beyond simple DSP, but does not establish a Podcast Voice Factory.

- The challenge evaluates privacy/intelligibility, not warmth or brand character.
- Its 2024 B1 baseline is utterance-level, not proof of a stable identity across
  recordings.
- Official evaluation is English/LibriSpeech-oriented; Vietnamese tonal quality
  is unverified.
- F0, rhythm, energy, and much prosody survive. A flat/sharp source performance
  cannot be assumed to become warm, deep, expressive narration.
- Speaker pool/model/data provenance requires a commercial review.

Source: [VoicePrivacy baselines](https://www.voiceprivacychallenge.org/resources/)
and [2024 evaluation plan](https://arxiv.org/abs/2404.02677).
