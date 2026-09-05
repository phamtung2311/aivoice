# Phase 36M — pinned V-TTS provenance verification

## Decision

**PROVENANCE/LICENSING UNRESOLVED — REJECT V-TTS.**

No dependencies, venv, model binaries, inference, Candidate 03 change, or
production change occurred. Do not seek unofficial mirrors.

## Pinned checkout

- Path: `experiments/brand_voice_phase36m/source/v-tts-v1.0.5`
- Tag: `v1.0.5`
- Full commit: `a5e77a138960c1101c022a61614d6ee72aeccadc`
- State: detached HEAD; clean `git status --short`
- Disk use: 348 MB

## Material source mismatch

The pinned tag is not the V-TTS-branded `dev` source audited in Phase 36L. It
is Valtec-branded: Python package `valtec_tts`, distribution `valtec-tts`,
author `Valtec Team`, and CC BY-NC copyright to Valtec Team. The zero-shot API
shape is technically similar, but the actual remote source changes from the
previous `v-tts/...` Space to `valtecAI-team/...`. Therefore Phase 36L dev API
evidence cannot establish provenance for the pinned tag.

## Exact clone retrieval chain

`valtec_tts/zeroshot.py` requests these mutable default-branch Space files (no
`revision` argument anywhere):

| Remote | Type | Path |
| --- | --- | --- |
| `valtecAI-team/valtec-zeroshot-voice-cloning` | Space | `pretrained/zeroshot/G_175000.pth` |
| same | Space | `pretrained/zeroshot/config.json` |
| same | Space | `pretrained/hasp/pytorch_model.bin` |

It also has a hidden second chain: `src/models/encoders.py` looks for
`pretrained/hasp/pytorch_model.bin` relative to the current working directory,
not the zero-shot cache. If absent it downloads the unpinned default revision of
`Edresson/Speaker_Encoder_H_ASP/pytorch_model.bin`. Hence runtime can use an
extra mutable third-party asset.

## Metadata-only remote check

The Valtec Space redirects to `letrggghieu/v-zeroshot-voice-cloning`; current
main has later rebrand commits, proving the tag has no frozen remote companion.
Current metadata lists, but source does not pin, these assets:

| File | Bytes | LFS SHA-256 OID |
| --- | ---: | --- |
| `G_175000.pth` | 803,111,837 | `9d1c82cf10b667340e02e1a5b666c4ef020b9fce2491e3b4be3c9183fdc9bb0c` |
| `config.json` | 29,259 | not supplied |
| H-ASP `pytorch_model.bin` | 44,610,930 | `8f96efb20cbeeefd81fd8336d7f0155bf8902f82f9474e58ccb19d9e12345172` |

Their current total is 847,752,026 bytes. This is not a reproducible v1.0.5
manifest because the source follows mutable default branches and redirects.

## Licensing result

- **Code:** CC BY-NC 4.0; commercial use prohibited.
- **Main zero-shot weights:** **UNRESOLVED.** No release-pinned model card or
  separate terms were found.
- **Generated output:** **UNRESOLVED.** No output grant was found.
- **Edresson speaker encoder:** its page says MIT, but that does not grant terms
  for the main checkpoint and the runtime does not pin its revision.

Even though Candidate 03 is technically compatible with the clone API, this
renderer fails the project’s auditability and eventual local-production route.
V-TTS is closed.
