# Phase 42B checkpoint

Updated: 2026-09-05 Asia/Ho_Chi_Minh

## Completed

- Located real private source `X. Bình Minh 2.m4a` in Phase 42A metadata:
  AAC, mono, 48 kHz, 125.354667 seconds, SHA256
  `1bfc4f9b65b7babf028d0c79a3ef53ac838c979660844595a2b4f872e447c147`.
- Located three existing derived source regions and their SHA256 values in
  `experiments/personal_voice_phase42a/metadata/src_fb562cbea3980f3e.json`.
- Confirmed V-TTS public API takes one 3–10 second `reference_audio`; it sends
  that single clip to both its speaker encoder and style encoder. It exposes no
  independent speaker/style references or supported multi-reference averaging.
- Cloned a separate, pinned V-TTS source checkout at
  `experiments/personal_voice_phase42b/source/v-tts`, detached commit
  `e22eef3267869375e40a096b376cde94aa41e610` (upstream `dev` HEAD at time of
  audit). License is CC BY-NC 4.0: research only.
- Created isolated `.venv-phase42b-vtts` using Python 3.12.14. Installed CPU
  only `torch==2.5.1+cpu`, `torchaudio==2.5.1+cpu`, plus the minimal runtime
  stack (`numpy==1.26.4`, `scipy==1.14.1`, `soundfile==0.13.1`,
  `librosa==0.9.2`, `viphoneme==3.0.0`, `vinorm==2.0.7`, `underthesea==8.3.0`,
  `eng-to-ipa==0.0.2`, `huggingface_hub==0.36.0`) and editable `v-tts` source.
  No CUDA package was installed and production `.venv` was untouched.
- Applied an isolated Python 3.12 compatibility patch only to the Phase 42B
  venv copy of `vinorm`: replace removed stdlib `imp.find_module` with the
  module directory. This does not alter V-TTS source or its audio algorithm.
- Pinned reachable checkpoint provenance after the upstream code's configured
  `v-tts/v-zeroshot-voice-cloning` namespace returned HTTP 401. Its historical
  redirect target resolves to `letrggghieu/v-zeroshot-voice-cloning` at Space
  commit `83deb9f5ab591ca79840c9042dbef37dd2e5780e`:

  | file | size | SHA256 |
  | --- | ---: | --- |
  | `pretrained/zeroshot/G_175000.pth` | 803,111,837 | `9d1c82cf10b667340e02e1a5b666c4ef020b9fce2491e3b4be3c9183fdc9bb0c` |
  | `pretrained/hasp/pytorch_model.bin` | 44,610,930 | `8f96efb20cbeeefd81fd8336d7f0155bf8902f82f9474e58ccb19d9e12345172` |
  | `pretrained/zeroshot/config.json` | 29,259 | non-LFS blob `e62bab61596c6eeb45c67e59143252747d1ed068` |

## Completed after the initial checkpoint

- The isolated import/phonemizer gate passed after the documented `vinorm`
  compatibility repair. Checkpoints were downloaded exactly once and verified
  against the pinned SHA256 values above.
- Three selected reference clips were copied byte-for-byte into the ignored
  Phase 42B private-reference directory. `metadata/references.json` records
  their roles, paths, hashes, duration, format, and the explicit no-processing
  statement.
- V-TTS raw CPU renders completed sequentially, with the 5 GiB RAM guard and
  four CPU threads:

  | test / reference | output SHA256 | duration |
  | --- | --- | ---: |
  | Test 1 / REF-N | `cfba33109d8e94199319aa8e975220a40512d60bb5b702cca5c2757f6cfc3017` | 2.773333 s |
  | Test 2 / REF-R | `a0c4e411be257b2fb2adee14ac5fdbc97b13782dc0dca4780b26867cf0d20667` | 9.514667 s |
  | Test 3 / REF-E | `f6bbcd46a37882bd4f3e4f8d1cfc407f30dba6f542f28cafca63c827615d2e4f` | 30.229333 s |

  Each has an ignored per-run manifest in `metadata/`; all three are 24 kHz,
  mono, and did not clip.
- The controlled VieNeu side reuses the existing Phase 42A artifacts for
  matching Test 1 / REF-N and Test 2 / REF-R (no rerender). One missing,
  matching Test 3 / REF-E baseline was rendered once without changing
  production configuration: SHA256
  `d4fc952493a2359abf6a7304b656af7cf9b0590faa23215f92236d67c615c2a7`,
  47.711125 s, 48 kHz, mono, no clipping. The normal engine made four outer
  chunks and only a 31.12 ms measured-silence deficit join; no Phase 41
  prosody/tempo/mastering stack was used.
- `PHASE42B_REPORT.md` and `HUMAN_REVIEW.md` now provide the audit and six-file
  human comparison. No Test 4 was run: it is explicitly gated on human review.

## Current remaining step

Human listening only. The owner must compare the paired raw V-TTS and VieNeu
files documented in `HUMAN_REVIEW.md`. Do not infer a winner from durations,
peaks, or architecture; do not run Test 4 or make any production integration
without a human result and separate authorization.
