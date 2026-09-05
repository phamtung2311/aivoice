# Voice Conversion landscape

Real VC uses learned speaker/content/decoder conditioning, not pitch shifting,
EQ, formants, speed, or reverb. Most VC projects solve conversion to a known
target, not new-identity creation.

- **Seed-VC** is active zero-shot VC but its upstream README says it clones a
  target voice from a 1–30-second reference: TYPE 1 target-reference VC.
- **OpenVoice V2** is target-reference cloning; its official native language
  list excludes Vietnamese: TYPE 1.
- **RVC** converts toward a trained target; upstream recommends at least ten
  minutes of low-noise target speech: TYPE 2.
- **VoicePrivacy B1-style anonymization** derives a pseudo-speaker x-vector from
  a pool and resynthesizes speech while retaining source bottleneck/F0 features.
  This is TYPE 3-adjacent research, not a verified Vietnamese brand factory.

Sources: [Seed-VC](https://github.com/Plachtaa/seed-vc),
[OpenVoice](https://github.com/myshell-ai/openvoice),
[RVC](https://github.com/RVC-Project/Retrieval-based-Voice-Conversion-WebUI),
[VoicePrivacy 2024](https://github.com/Voice-Privacy-Challenge/Voice-Privacy-Challenge-2024).
