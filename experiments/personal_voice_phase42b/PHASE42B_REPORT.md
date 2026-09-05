# Phase 42B — Personal Voice Prosody PoC with V-TTS

Date: 2026-09-05 (Asia/Ho_Chi_Minh)  
Status: **TECHNICAL PoC PASS / HUMAN QUALITY FAIL**

## Human conclusion recorded after the PoC

The owner auditioned the entire V-TTS/VieNeu comparison and concluded:
**“Tất cả đều chả ra gì.”** This closes the zero-shot personal-voice cloning
direction. It is not a reason to tune V-TTS, change reference selection, run
Test 4, or polish the Phase 42A UI. Phase 42C instead separates the proven
narration/prosody carrier from trainable speaker-identity conversion.

## Objective and scope

This is an isolated, local CPU research comparison of V-TTS and the existing
VieNeu baseline using the project owner's private recording. It tests whether
V-TTS's single-reference speaker/style path is perceptually more useful for
personal-voice prosody. It does not change, install, or promote a production
voice; it does not alter Candidate 03, Phase 41, Phase 42D, planner, tempo,
embedding, reference codes, or production configuration.

The source recording remains private and gitignored. Its Phase 42A source
SHA256 is `1bfc4f9b65b7babf028d0c79a3ef53ac838c979660844595a2b4f872e447c147`
(AAC M4A, mono, 48 kHz, 125.354667 s). Reference WAVs were copied
byte-for-byte only, never denoised, normalized, EQ'd, time-stretched, or
otherwise processed.

| role | Phase 42B ID | SHA256 | duration |
| --- | --- | --- | ---: |
| neutral/stable pitch | REF-N | `18563b07584d72464a9d68551e4de09f65aabff4f6db8ca0fd91d27f029e11ed` | 6.020 s |
| reflective/lower pitch | REF-R | `e0d56087e2e94803cf938d32261a0a75a4a917a7caac308fd61267e618482876` | 6.480 s |
| gently emphasized/wider pitch | REF-E | `d2fa6986453f2c90f518471b0ebbde52ef2217cb2ab9bce0c5ca10c9eb207cf9` | 7.320 s |

V-TTS accepts one 3–10 second reference per render. It feeds that same clip to
its speaker and style encoders; it exposes no supported independent
speaker/style references nor native same-speaker multi-reference averaging.

## Isolated V-TTS environment and pinned weights

- Source checkout: `source/v-tts`, detached commit
  `e22eef3267869375e40a096b376cde94aa41e610`.
- Environment: `.venv-phase42b-vtts`, Python 3.12.14, CPU-only
  `torch==2.5.1+cpu` / `torchaudio==2.5.1+cpu`; the production `.venv` was not
  modified.
- Checkpoint Space provenance: reachable historical redirect target
  `letrggghieu/v-zeroshot-voice-cloning`, pinned commit
  `83deb9f5ab591ca79840c9042dbef37dd2e5780e` after the configured upstream
  namespace returned HTTP 401.
- Verified weight SHA256: `G_175000.pth`
  `9d1c82cf10b667340e02e1a5b666c4ef020b9fce2491e3b4be3c9183fdc9bb0c`
  (803,111,837 bytes); H/ASP speaker encoder
  `8f96efb20cbeeefd81fd8336d7f0155bf8902f82f9474e58ccb19d9e12345172`
  (44,610,930 bytes). Config is pinned non-LFS blob
  `e62bab61596c6eeb45c67e59143252747d1ed068` (29,259 bytes).
- V-TTS is licensed **CC BY-NC 4.0**. This PoC is research-only and is not a
  production or commercial-use approval.

The source calls `torch.load(..., weights_only=False)` for its pinned model and
emitted PyTorch's pickle-security warning. The checkpoint hashes and immutable
Space revision mitigate, but do not eliminate, that supply-chain risk.

## Renders and measurements

All V-TTS candidates are direct raw `clone_voice` outputs: CPU, four threads,
24 kHz mono WAV, no Phase 41 prosody/pause/tempo processing, no EQ, loudness,
compression, pitch or formant manipulation. The runner rejects reference clips
outside 3–10 seconds, refuses overwrites, and requires at least 5 GiB
`MemAvailable` before loading the model.

| test | reference | V-TTS output | SHA256 | duration | peak / clipping | generation / RTF / peak RSS |
| --- | --- | --- | --- | ---: | --- | --- |
| Test 1 short | REF-N | `outputs/vtts_raw_ref_n_test1_short.wav` | `cfba33109d8e94199319aa8e975220a40512d60bb5b702cca5c2757f6cfc3017` | 2.773333 s | 0.548798 / no | 2.971 s / 1.071 / 1519.7 MiB |
| Test 2 long sentence | REF-R | `outputs/vtts_raw_ref_r_test2_long_sentence.wav` | `a0c4e411be257b2fb2adee14ac5fdbc97b13782dc0dca4780b26867cf0d20667` | 9.514667 s | 0.561462 / no | 7.413 s / 0.779 / 1543.0 MiB |
| Test 3 podcast paragraph | REF-E | `outputs/vtts_raw_ref_e_test3_podcast_paragraph.wav` | `f6bbcd46a37882bd4f3e4f8d1cfc407f30dba6f542f28cafca63c827615d2e4f` | 30.229333 s | 0.594025 / no | 23.702 s / 0.784 / 2592.8 MiB |

The text SHA256 values, reference hashes, model/weight hashes, available RAM,
load time, CUDA status (`false`) and output metrics are preserved in ignored
per-render manifests under `metadata/`. Test 4 was deliberately not rendered:
human evidence from Tests 1–3 is the gate.

## Matched VieNeu comparison

VieNeu has no supported deterministic seed, so it is a baseline for human
comparison, not a deterministic A/B. The first two matching artifacts were
already generated in Phase 42A and are reused unchanged. The missing Test 3 /
REF-E baseline was rendered once with the normal `TTSEngine.generate()` path
only; this did not alter any persistent model, planner, voice, or config.

| test | reference | VieNeu artifact | SHA256 | duration | format / clipping |
| --- | --- | --- | --- | ---: | --- |
| Test 1 | REF-N | `../personal_voice_phase42a/outputs/vieneu_ref_202a40af97ff_test1_short_0570e460.wav` | `25cafe1c9bc9190c04a87756cdba47197d6f99775c6005c1b540d2d6c813b9a3` | 2.960000 s | 48 kHz mono / no |
| Test 2 | REF-R | `../personal_voice_phase42a/outputs/vieneu_ref_ec062a6e0b33_test2_long_sentence_9538ffcc.wav` | `35e84c5eda27540feb9e0570b225e5913d81c4c706a4c08e59687a173ac58b9b` | 14.000000 s | 48 kHz mono / no |
| Test 3 | REF-E | `outputs/vieneu_baseline_ref_e_test3_podcast_paragraph.wav` | `d4fc952493a2359abf6a7304b656af7cf9b0590faa23215f92236d67c615c2a7` | 47.711125 s | 48 kHz mono / no |

The Test 3 baseline has four normal outer chunks (177/201/226/115 characters)
and one measured 31.12 ms silence-deficit join. This is standard engine joining,
not the Phase 41E/41F/41H stack. Its manifest records peak 0.817505, no
clipping, and no postprocessing.

## Limitations and decision gate

- V-TTS's output and VieNeu's output may vary across renders. Do not treat
  duration, peak, RTF, architecture, or an individual sample as proof of a
  winner.
- Different engines naturally produce different sample rates and durations;
  playback volume should be matched by the listener.
- This is a small single-reference-per-test exploration, not evidence that
  V-TTS faithfully represents the owner's voice across contexts.
- No model was downloaded or inference run beyond the three required V-TTS
  tests and one missing matching VieNeu Test 3 baseline. No Test 4 was run.
- No human winner has been declared. The real listening gate is
  `HUMAN_REVIEW.md`; only an explicit human result can decide whether another
  research test is worthwhile.

## File and project status

- Private source, checkpoint, reference, output, and metadata folders are
  gitignored. Public audit scripts and Markdown reports are the only intended
  tracked Phase 42B artifacts.
- No Phase 41/42 production artifact was changed. The working tree was already
  dirty before this PoC; Phase 42B changes are limited to its own directory and
  the existing private-data ignore rules.
- Human listening package: ready, six existing WAV paths enumerated in
  `HUMAN_REVIEW.md`.

**Next action: human listening only. Do not promote V-TTS, render Test 4, or
integrate any engine until the owner records a result.**
