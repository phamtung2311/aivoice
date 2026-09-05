# Phase 36K — Brand Voice renderer fallback decision

## Decision

Close VietVoice tuning.  The controlled Phase 36D–J sequence already varied
reference language, punctuation, requested duration, and speed.  It exposed a
real strength (Vietnamese timbre/force) but did not meet the listening gate for
both continuity and pronunciation at once.  More variants would be parameter
search, not new evidence.

**Select one next PoC: V-TTS zero-shot clone of the frozen Candidate 03
canonical WAV, on one short Vietnamese diagnostic sentence.**

This is **RESEARCH ONLY**. V-TTS publishes its project under CC BY-NC 4.0, so a
successful result cannot be made the monetized/channel production renderer
without a commercial permission or a replacement under production-suitable
terms.

No renderer was installed, downloaded, or run in this phase. No production or
canonical Candidate 03 asset was changed.

## Why this is the right next question

The core unresolved question is not whether another engine can pronounce
Vietnamese. It is whether the frozen synthetic Candidate 03 can survive a
Vietnamese-native, small CPU clone renderer without the repeated
termination/restart character heard in VieNeu and VietVoice.

V-TTS is the only currently audited candidate that simultaneously documents:

- Vietnamese-native text normalization/phonemization;
- zero-shot reference-WAV cloning without a transcript;
- a 3–10 second, clean, single-speaker reference requirement satisfied by the
  6.96-second Candidate 03 canonical Qwen WAV;
- CPU-only inference; and
- a modest 74.8M-parameter model.

Its claims are vendor/repository claims, not results independently established
in this workspace. The one-sample PoC is specifically intended to validate or
falsify them.

## Evidence distinction

`FACT` below means directly documented by the named official/project source.
`INFERENCE` is an engineering assessment for this Fedora i9-13900H / 16 GB RAM
machine, not a guaranteed benchmark.

| Renderer / architecture | Vietnamese and clone interface | Synthetic identity and prosody | CPU / local feasibility | Production licence | Decision |
| --- | --- | --- | --- | --- | --- |
| **V-TTS zero-shot** | **FACT:** Vietnamese-native phonemizer; clone API accepts a 3–10 s clean reference WAV; no transcript input. | **FACT:** separate 512-d speaker and 128-d style embeddings plus F0/energy prediction. **INFERENCE:** Candidate 03 portability is plausible, but long-form authority and identity stability remain unproven. | **FACT:** 74.8M / ~285 MB FP32; project claims CPU-only RTF 0.24–0.48 on an i5-14500. **INFERENCE:** comfortable within 16 GB, likely well inside the user's RTF target. | **Non-commercial only:** CC BY-NC 4.0; written permission required for commercial use. | **ONE selected PoC — RESEARCH ONLY.** |
| **VoxCPM2** | **FACT:** Vietnamese is in its official 30-language list. Clone accepts `reference_wav_path`; ultimate clone also accepts exact prompt WAV + transcript. | **FACT:** also offers native Voice Design, style instructions, context-aware synthesis and 48 kHz output. **INFERENCE:** this is the strongest eventual Strategy B architecture because it can create a new Vietnamese-native synthetic identity without Candidate 03. | **FACT:** 2B parameters; installation requirements state PyTorch >=2.5 and CUDA >=12. Docs expose a `cpu` UI device, but no CPU performance/RAM support promise is documented. **INFERENCE:** unsupported/high-risk on this 16 GB non-CUDA laptop. | **Commercially usable:** code and weights stated Apache-2.0. | Do not install/PoC on current hardware. Keep as the leading future GPU-capable Strategy B candidate. |
| **IndexTTS2 / current IndexTTS2.5** | **FACT:** official current language list is Chinese, English, Japanese, Spanish, Arabic—Vietnamese absent. It clones from a reference WAV; reference transcript is not required in its basic API. | **FACT:** emotion/timbre separation and duration controls exist. **INFERENCE:** those strengths do not offset unproven Vietnamese pronunciation. | **FACT:** official workflow emphasizes BF16/FP16, CUDA and vLLM; no official CPU support/RTF is stated. | **Restricted/unclear:** Bilibili Model Use License; official page directs commercial users to contact authors. | Reject for a Vietnamese PoC. The community Vietnamese fork is a separate adaptation/training project, not an official production-safe renderer. |
| **Qwen3-TTS Base** | **FACT:** ICL clone supports `ref_audio` + `ref_text`; the official supported-language set does not list Vietnamese. | **FACT:** strong clone/design family. **INFERENCE:** prior Qwen-family Gwen probes being English-like raise risk, though they do not prove Base identical. | **FACT:** 0.6B/1.7B variants, local possible but existing CPU VoiceDesign work was slow. | **Commercially usable in principle:** code is Apache-2.0; model/output terms still need per-release verification. | Reject for Vietnamese PoC: unsupported language is decisive. |
| **VieNeu** | Vietnamese works; frozen Candidate 03 transfer works. | Existing evidence: repeated continuity/chunk failures and limited authority control. | CPU practical. | Existing project/dependency terms were not re-opened here. | Preserve fallback/identity-transfer implementation only; no tuning. |
| **VietVoice-TTS** | Vietnamese and reference clone demonstrated. | Existing evidence: force/timbre positive but Phase 36D–J fails the combined continuity/pronunciation gate. | CPU ONNX works, but measured peak RSS ~4.8 GiB and slow. | MIT source; model terms still require normal release review. | Research checkpoint only; tuning closed. |
| **Gwen-TTS** | Candidate 03 Vietnamese output remained English-like even after explicit Vietnamese configuration. | No acceptable identity/quality result. | CPU probe ran; not relevant after quality failure. | Not reconsidered. | Rejected; do not revisit. |
| **Fish Speech / CosyVoice / F5-style routes documented earlier** | No audited, official Vietnamese-first clone/design path that meets this task. | Some are expressive/clone-capable, but synthetic identity or Vietnamese support is unproven for this use. | Typically GPU-first and/or large. | Research/restricted/unclear terms in prior audit. | Not serious next candidates. |

## Scored decision matrix

Scores are 1 (poor) to 5 (strong). They compare the present project and
hardware, not vendor popularity. The scores do not override the licence column.

| Candidate | Vietnamese | Candidate-03 preservation / synthetic-identity potential | Distinctiveness | Continuity / prosody | Long-form | CPU | Licence | Implementation risk | Result |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| V-TTS zero-shot | 4 | 3 | 3 | 3 | 3 | 5 | 1 | 3 | Best small **research** test |
| VoxCPM2 | 5 | 5 | 5 | 5 | 5 | 1 | 5 | 5 | Best future GPU/production architecture, blocked locally |
| IndexTTS2.5 | 1 | 4 | 4 | 5 | 4 | 1 | 2 | 5 | Reject now |
| Qwen3-TTS Base | 1 | 5 | 5 | 4 | 4 | 2 | 4 | 4 | Reject now |
| VieNeu | 3 | 4 | 3 | 1 | 1 | 5 | 2 | 1 | Frozen fallback only |
| VietVoice | 4 | 3 | 3 | 2 | 2 | 3 | 3 | 2 | Stop tuning |

## Strategy A versus Strategy B

### Strategy A — preserve Candidate 03

Run the V-TTS research PoC using only:

- `experiments/brand_speaker_phase33c/baseline_anchor/BRAND_CANDIDATE_03_BASELINE/qwen_source.wav`
- the one short Vietnamese diagnostic target to be chosen before execution.

The V-TTS API does not need the English transcript. No user recording, new
speaker, or modification to Candidate 03 is involved. This is the lowest-cost
test of whether identity portability—not the Qwen-designed identity itself—is
the bottleneck.

### Strategy B — stronger Vietnamese-native synthetic identity

Do **not** discard Candidate 03 yet. If the V-TTS short gate fails, the evidence
will say that a small Vietnamese clone renderer cannot provide the required
quality, not that no synthetic identity works. The strongest documented
replacement architecture is VoxCPM2 Voice Design: it can design a fresh voice
directly in Vietnamese and then clone/control it, with Apache-2.0 code/weights.
But its official install requirement is CUDA 12, so it is not a valid local CPU
PoC on the present machine. This is a future hardware/renderer path, not an
action authorized in Phase 36K.

## Exact next PoC (requires approval)

**V-TTS Candidate 03 zero-shot Vietnamese diagnostic — RESEARCH ONLY**

1. Create a new isolated experiment directory and virtual environment; do not
   touch `/home/tung/ai voice/.venv` or production.
2. Before download, inspect the checked-out current V-TTS release, its exact
   model asset names, hashes if published, and its CC BY-NC terms again.
3. Download only the zero-shot model assets, not the optional multi-speaker or
   app artifacts. The documented model is ~285 MB FP32; the project advertises
   a ~165 MB ONNX edge artifact, but it is not yet verified that the clone path
   uses it. A conservative isolated experiment budget is **about 1–2.5 GB**
   including a CPU PyTorch runtime and dependencies; exact size must be reported
   before download.
4. Generate exactly one short Vietnamese diagnostic target from the unmodified
   6.96-second canonical Candidate 03 WAV, using documented defaults. No target
   transcript, tuning grid, or production integration.
5. Validate the raw WAV and let the user listen directly before a blind control
   comparison or any long-form test.

### Short acceptance gate

Reject V-TTS early if any of these fail by listening:

A. correct Vietnamese pronunciation;
B. clearly acceptable continuity;
C. one coherent person rather than generic/fragmented speech;
D. enough Candidate-03-like character/authority;
E. no obvious robotic phrase fragmentation.

Only if A–E pass may we test identity stability on unrelated passages. No
long-form benchmark comes before this gate.

## Stop point

**STOP — waiting for user approval before any V-TTS clone, environment, or
model asset is installed/downloaded.**

## Sources re-audited

- V-TTS project README: Vietnamese phonemizer, zero-shot API, CPU claims,
  component sizes and CC BY-NC 4.0 terms.
- VoxCPM2 official repository/docs: Vietnamese support, 2B model, voice design,
  clone interfaces, Apache-2.0 statement and CUDA requirement.
- IndexTTS official repository: current supported languages, clone interface,
  GPU-oriented setup and Bilibili Model Use License.
- Qwen3-TTS official source/API: Base clone prompt mechanism; project records
  retain the official ten-language list which excludes Vietnamese.
