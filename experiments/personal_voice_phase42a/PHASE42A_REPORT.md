# Phase 42A — Personal Voice Reference Lab + 2026 Engine Audit

Audit date: 2026-09-04 (Asia/Ho_Chi_Minh)  
Overall status: **TECHNICAL PIPELINE PASS / HUMAN QUALITY FAIL**

The local workflow and controlled corpus passed. A real project-owner source was
subsequently uploaded and real VieNeu candidates were auditioned. Human result:
the candidate sounded only “ná ná” (roughly similar) to the real voice and was
worse than the earlier Voice Lab clone. The long-reference corpus did not solve
long-sentence prosody, pacing, or occasional pronunciation issues. Therefore
Phase 42A is closed: do not continue a VieNeu long-reference workaround.

## 1. Current architecture audit

- Application: FastAPI backend plus static browser UI.
- Installed TTS package: `vieneu==3.3.0`.
- Actual factory default: `Vieneu(mode="v3turbo")`; the application's historical
  `pnnbao-ump/VieNeu-TTS-v2` label was not used by the factory as a v2 selector.
  Runtime metadata now names the actual default model,
  `pnnbao-ump/VieNeu-TTS-v3-Turbo`.
- Actual CPU backend: VieNeu v3 Turbo ONNX int8 (`OnnxV3LiteEngine`), 48 kHz;
  `onnxruntime==1.29.0`.
- Hardware observed: Intel Core i9-13900H, x86_64, 14 cores / 20 logical CPUs,
  15 GiB visible RAM. At audit time 5.3 GiB was available and swap was active;
  those momentary values are not a capacity benchmark.
- `TTSEngine.generate()` preprocesses and chunks target text. For a clone it
  encodes the reference once, builds `{speaker_emb, codes}`, and reuses that
  profile for every target-text chunk.
- No default engine, Candidate 03 asset, Phase 41 artifact, Phase 42D planner,
  pause policy, tempo, pitch, or formant setting was changed.

Evidence inspected: `backend/app/tts/model.py`, `backend/app/tts/engine.py`,
the installed `vieneu/factory.py`, `vieneu/v3turbo.py`, and
`vieneu/_v3_turbo_engine/onnx_runtime_lite.py`.

## 2. Current VieNeu reference behavior

The effective reference path is:

1. Existing short-reference UI accepts WAV/MP3/M4A, caps the browser selection
   at 5 MiB and 8.0 seconds.
2. Backend decodes compressed input to WAV, reads its duration, and discovers
   the engine's `prepare_reference(..., max_seconds=8.0)` default.
3. The public v3 wrapper trims silence at both edges.
4. The ONNX engine takes only the first 8.0 seconds if a longer waveform reaches
   it, optionally denoises to mono 44.1 kHz, extracts a 192-dimensional speaker
   embedding, and encodes acoustic reference codes.
5. Target generation receives both the speaker embedding and reference codes.
   The reference is enrolled once and reused for all text chunks.

`ref_text` is accepted by a low-level compatibility signature but is not used in
this v3 Turbo enrollment path. There is a distinct speaker embedding, but no
separately exposed style/prosody embedding. In v3 Turbo the `style` argument is
deprecated and ignored; style information is described as implicit in the
speaker embedding plus reference codes.

Conclusion: raising the application constant to 30–180 seconds would be false
support. VieNeu 3.3.0 truncates at 8 seconds before enrollment, so later audio
does not add context. Phase 42A deliberately leaves this limit unchanged and
uses a long recording only as a corpus from which good 3–8 second references
are selected. This matches the upstream implementation, which defines
`_MAX_REF_SECONDS = 8.0` and truncates before speaker/code extraction:
[VieNeu v3 Turbo reference implementation](https://github.com/pnnbao97/VieNeu-TTS/blob/main/src/vieneu/_v3_turbo_engine/inference_v3_turbo.py).

## 3. Engine comparison

| Candidate | Reference mechanism | Prosody representation | Multi-reference | Local status |
| --- | --- | --- | --- | --- |
| VieNeu 3.3.0 v3 Turbo | 3–8 s; 192-d speaker embedding + acoustic codes; later audio truncated | Implicit in embedding/codes; separate `style` control is ignored | No documented native pool/averaging in inspected API | Installed, CPU ONNX int8, production baseline |
| V-TTS | Upstream recommends 3–10 s; zero-shot | Claims separate 512-d speaker and 128-d style encoders plus F0/energy prosody predictor | Documents speaker interpolation, not a validated same-speaker multi-take enrollment policy | Technically attractive CPU research candidate, not production-eligible |
| Gwen-TTS 0.6B | Few-second prompt; normal mode requires exact `ref_text`; x-vector-only can omit it with lower quality | Discrete audio prompt/context from Qwen3-TTS; reusable clone prompt | Reusable single prompt and batch generation documented; no supported averaging/prompt pool found | Not installed; CUDA-first upstream path; research only on this laptop |

The V-TTS architecture and claimed CPU benchmark are documented by its current
upstream README: 74.8M parameters, about 285 MB FP32, RTF 0.236–0.475 on an
i5-14500, PyTorch 2+, and Linux recommended. Those are publisher claims, not
measurements from this machine. See [tronghieuit/v-tts](https://github.com/tronghieuit/v-tts).

Gwen-TTS is a Vietnamese fine-tune of Qwen3-TTS. Its card reports 0.9B stored
parameters in BF16 despite the 0.6B product name. It uses `ref_audio` plus an
exact `ref_text`; its upstream tested environment is Python 3.11, CUDA 12.4,
NVIDIA driver >=550.54 and >=4 GB VRAM, with BF16 and FlashAttention 2. See the
[Gwen-TTS repository](https://github.com/ggroup-ai-lab/gwen-tts) and
[model card](https://huggingface.co/g-group-ai-lab/gwen-tts-0.6B).

## 4. License findings

- Installed VieNeu Python distribution declares Apache-2.0. Model/dependency
  terms still need to remain in any release bill of materials.
- V-TTS upstream declares CC BY-NC 4.0, non-commercial only, with written
  permission required for commercial use. It cannot be the monetized production
  dependency under the stated project goal.
- The existing pinned local `v1.0.5` audit also found mutable/unpinned checkpoint
  provenance and unresolved output terms; see
  `experiments/brand_voice_phase36m/PHASE36M_VTTS_SOURCE_PROVENANCE_VERIFICATION.md`.
  Therefore the present source copy is not promoted merely because the current
  README makes stronger quality/performance claims.
- Gwen-TTS declares MIT for its released model. Downstream deployment must still
  comply with base model/runtime and dataset/voice-consent obligations. The
  repository says its Vietnamese fine-tune used roughly 1,000 hours crawled
  from TikTok; this is a provenance consideration for production review, not a
  technical performance result.

## 5. CPU/local feasibility

- **VieNeu: viable and already proven locally.** ONNX int8 CPU is the current
  production path and does not need NVIDIA.
- **V-TTS: plausible for an isolated CPU PoC.** Its small architecture and
  upstream i5 CPU numbers fit the target hardware, but license and pinned-weight
  provenance block production. No new environment, package, model or TTS run was
  created because there is no user reference to compare and an older pinned
  source audit already rejected production use.
- **Gwen-TTS: RESEARCH ONLY / NOT LOCAL-PRODUCTION-VALIDATED.** Raw BF16 weights
  alone are roughly 1.8 GB for 0.9B parameters, but runtime, tokenizer/codec,
  attention state and generation buffers add substantial memory. The official
  examples are CUDA/BF16/FlashAttention based. The CLI exposes a CPU device, but
  no official CPU latency/RSS result, Intel GPU path, supported ONNX/OpenVINO/GGUF
  export, or quantized CPU recipe was found in the inspected project sources.
  “May load in 16 GB” is not the same as viable 20-minute local production, so no
  heavy install or multi-GB download was attempted. Qwen itself recommends a
  fresh isolated environment: [Qwen3-TTS upstream](https://github.com/QwenLM/Qwen3-TTS).

## 6. M4A workflow implementation

New “Giọng cá nhân” workflow:

- browser accepts `.m4a`, `.wav`, `.mp3`, `.aac`;
- source duration is enforced at 30–180 seconds and size at 64 MiB;
- original filename, byte count and SHA256 are stored, and original bytes are
  preserved without modification;
- FFprobe records codec, duration, source sample rate and channels;
- FFmpeg locally decodes stream 0 to PCM S16LE, mono, 48 kHz;
- no denoise, compression, loudness normalization, EQ, pitch or formant change;
- normalized metrics include duration, peak, RMS, clipped-sample count and
  silence ratio;
- personal source/derived folders are gitignored because voice recordings are
  biometric/personal data;
- UI provides source playback, extraction, engine/reference/test selection and
  playback for an explicitly generated candidate.

Implemented in `backend/app/personal_voice_lab.py`, API routes in
`backend/main.py`, and the additive panel in `frontend/index.html` / `app.js`.

## 7. Reference segmentation design

The long source is never sent directly to VieNeu. A conservative 20 ms RMS
heuristic detects speech and proposes at most eight 3–8 second windows whose end
is moved toward a nearby low-energy frame. Suggestions are only helpers: the UI
copies their timestamps into editable start/end fields. Extraction is sample-
accurate through local FFmpeg and creates a new PCM WAV with SHA256 and metrics.

The user must listen for complete, clean, natural sentences. The algorithm does
not detect coughs, verbal mistakes, other speakers or semantic completeness.
Transcript remains empty unless the user supplies it; the system never invents
one. VieNeu does not require it, while Gwen normal clone mode does.

## 8. Experiments run

No TTS inference ran in Phase 42A.

Executed preprocessing tests used a generated 180 Hz waveform with periodic
silence, not a voice:

- WAV original-byte/SHA preservation;
- PCM mono 48 kHz decode and non-destructive-policy metadata;
- automatic segment proposal and 3–8 second extraction;
- a real AAC-in-M4A container encoded and decoded with system FFmpeg;
- candidate endpoint contract with a dummy zero waveform engine only;
- UI/API contract assertions;
- Phase 42 production regression tests.

An attempted loopback Uvicorn/curl smoke could not cross the coding sandbox's
isolated socket boundary (`curl: failed to open socket: Operation not permitted`).
The server itself reached application startup successfully. This is not counted
as phone-M4A web acceptance; that gate remains for the user in the normal host
browser.

## 9. Audio artifacts

Real user-source artifacts: **none**.  
Real TTS candidates: **none**.  
Blind/A-B package: **not created**.

The synthetic test files existed only under pytest temporary directories and
`/tmp`; they are validation fixtures, not listening candidates. Runtime output
locations are reserved as:

- `experiments/personal_voice_phase42a/source/`
- `experiments/personal_voice_phase42a/normalized/`
- `experiments/personal_voice_phase42a/references/`
- `experiments/personal_voice_phase42a/outputs/`
- `experiments/personal_voice_phase42a/metadata/`

No file will be overwritten: source, reference and output IDs include random
identifiers and each generated candidate has a separate manifest.

## 10. Objective observations

- The earlier “short words sound similar, long passages do not” finding is
  consistent with an engine whose prompt contains speaker identity and short
  acoustic codes but whose long target prosody is generated stochastically from
  text chunks.
- VieNeu can receive different natural speaking styles by selecting different
  3–8 second clips, but the existence of reference codes does not prove faithful
  reproduction of a person's general speaking habits.
- Longer source recording is valuable for **selection diversity**, not as a
  longer VieNeu model prompt.
- V-TTS is the clearest architecture-level experiment for separating identity
  and style on CPU, but current licensing prevents it from answering the final
  production question.
- Gwen is more capable on paper and supports reusable prompts, but current
  upstream evidence does not establish acceptable CPU long-form throughput on
  this 16 GB, non-NVIDIA system.

No winner is declared. There is no perceptual evidence in this phase yet.

## 11. Known limitations

- No owner recording was provided; identity and prosody fidelity are untested.
- Silence segmentation is not VAD, diarization, ASR or semantic segmentation.
- There is no waveform visualization; timestamps and audio playback are the
  minimal UI. This follows the phase priority of evidence over polish.
- No automatic transcript is added. This avoids a new heavy dependency and false
  text, but means Gwen testing would require manual correction.
- No native multi-reference enrollment was found for VieNeu, and embedding
  averaging was intentionally not invented.
- VieNeu has no supported deterministic seed, so later renders must be treated as
  containing both intended reference effects and stochastic generation effects.
- The full HTTP upload gate and real audio decode must be repeated outside the
  sandbox with the actual phone file.

## 12. Human listening candidates

**None yet. Do not listen to or score the synthetic fixtures.**

After a real upload, the smallest valid shortlist should use the same Test 2 and
Test 3 text with three independently selected VieNeu references:

- `vieneu_<refA>_test2_long_sentence_<run>.wav`
- `vieneu_<refB>_test2_long_sentence_<run>.wav`
- `vieneu_<refC>_test2_long_sentence_<run>.wav`
- `vieneu_<refA>_test3_podcast_paragraph_<run>.wav`
- `vieneu_<refB>_test3_podcast_paragraph_<run>.wav`
- `vieneu_<refC>_test3_podcast_paragraph_<run>.wav`

These are future naming patterns, not files currently claimed to exist. The
human rubric is in `experiments/personal_voice_phase42a/HUMAN_REVIEW.md`.

## 13. Recommendation for Phase 42B

1. Run the app normally and upload one clean 30–180 second phone M4A from the
   project owner.
2. Confirm original playback, SHA, codec, duration and PCM decode metadata.
3. Select three complete 5–8 second utterances: neutral, reflective, and gently
   emphasized. Do not create 15/30 second VieNeu inputs.
4. Generate one run per reference for Test 1–3, then shortlist by human listening.
   Render Test 4 only for references that pass the first gate.
5. If identity is good but style varies with reference, compare selected baseline
   against personal clone + the existing Phase41E/41F/41H structural stack in a
   separate one-variable experiment. Preserve 0.98x and V2 cadence initially.
6. Only if a research comparison is still useful, prepare V-TTS in a separate
   Python environment with pinned source/assets and label every result
   `RESEARCH ONLY`. Do not ship it without commercial permission and resolved
   checkpoint/output terms.
7. Defer Gwen CPU PoC until upstream or a reproducible isolated benchmark shows
   a supported CPU/quantized path likely to meet 16 GB and long-form throughput.

## 14. Git diff / files changed

Phase 42A files:

- modified: `.gitignore`
- modified: `backend/app/tts/model.py` (correct runtime model label only)
- added: `backend/app/personal_voice_lab.py`
- modified: `backend/main.py`
- modified: `frontend/index.html`
- modified: `frontend/app.js`
- modified: `frontend/styles.css`
- added: `experiments/personal_voice_phase42a/test_set.json`
- added: `experiments/personal_voice_phase42a/HUMAN_REVIEW.md`
- added: `experiments/personal_voice_phase42a/PHASE42A_REPORT.md`
- added: `tests/test_phase42a_personal_voice_lab.py`

The worktree was already substantially dirty before Phase 42A, including Phase
42/42D and many historical experiment changes. No reset, deletion, checkout,
commit, or cleanup of user files was performed. Consequently repository-wide
`git diff --stat` is not a Phase 42A-only measure.

## 15. Commands and tests executed

Read-only audit commands included `git status --short`, `rg`, `sed`, `lscpu`,
`free -h`, package metadata inspection, model-cache inspection, and FFmpeg/
FFprobe version checks.

Tool versions observed:

- Python 3.14.7 project venv
- VieNeu 3.3.0
- ONNX Runtime 1.29.0
- SoundFile 0.14.0
- FastAPI 0.141.1
- FFmpeg/FFprobe 8.1.2 at `/usr/bin`

Verification commands:

```bash
PYTHONPATH=. .venv/bin/pytest -q \
  tests/test_phase42a_personal_voice_lab.py \
  tests/test_phase42_podcast_brand_voice.py
.venv/bin/python -m compileall -q backend
node --check frontend/app.js
```

Final result: **20 passed in 3.88s** (including real M4A encode/decode and 15
Phase 42 production regressions); Python compilation and JavaScript syntax check
passed. No TTS inference ran.

## Acceptance matrix

| Criterion | Status |
| --- | --- |
| Phone M4A through real host browser | PENDING actual user file / host smoke |
| Local conversion/preprocess | PASS with real AAC/M4A test container |
| Preserve long source | PASS in implementation/test |
| Extract short reference | PASS in implementation/test |
| VieNeu clone with owner's voice | PENDING owner recording |
| Controlled identity/prosody corpus | PASS (fixed texts); listening PENDING |
| New approach audit | PASS (V-TTS and Gwen audited) |
| V-TTS PoC | NOT RUN; no owner reference, production license/provenance blocked |
| Gwen CPU PoC | NOT RUN; no supported/validated local CPU path found |
| No false long-reference claim | PASS |
| Production/historical preservation | PASS; 15 relevant regressions passed |
| Audio A/B artifacts and human gate | PENDING |

## Closure addendum — actual user recording and human QA

After this technical report was initially created, the owner uploaded real
source `X. Bình Minh 2.m4a` (AAC, mono, 48 kHz, 125.354667 seconds; original
SHA256 `1bfc4f9b65b7babf028d0c79a3ef53ac838c979660844595a2b4f872e447c147`).
The long-source preservation, local decode and segment pipeline therefore have
real-user evidence. Real VieNeu outputs were generated in the private ignored
`outputs/` directory and human-auditioned.

Human decision: **TECHNICAL PIPELINE PASS / HUMAN QUALITY FAIL**. The new
candidate was only “ná ná” giọng thật and worse than the previous Voice Lab
clone. A longer source corpus did not overcome VieNeu's short-reference,
long-form prosody or occasional pronunciation limitations. This addendum
supersedes the earlier “waiting/no real candidate” placeholders above. The
result is not a reason to alter the 8-second VieNeu limit or continue the
long-reference workaround.

**PHASE 42A FINAL STATUS: TECHNICAL PIPELINE PASS / HUMAN QUALITY FAIL**
