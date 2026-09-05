# Phase 30I Report

## Timestamp

2026-08-31 (Asia/Ho_Chi_Minh)

## Status

QWEN_RUNTIME_BLOCKED (retry result; original QWEN_RAM_BLOCKED preflight is preserved below)

## Objective

Run the first isolated Qwen VoiceDesign → VieNeu Vietnamese synthetic-identity audio PoC with exactly three candidates. The PoC did not proceed beyond safe preflight.

## Production Safety

Git status was inspected before work. The repository already contains extensive unrelated modified, deleted, and untracked files; none were reverted, cleaned, or altered. Production backend/frontend, API, VieNeu engine, saved voices, production dependencies, and production Python 3.14 environment were untouched.

## Preflight

| Check | Result |
|---|---|
| Filesystem free space | 352 GB free; passes the 15 GB recommendation |
| Physical RAM | 15 GiB total; 2.8 GiB available |
| Swap / zram | 30 GiB total; 3.0 GiB already used |
| Python 3.12 | Not found on PATH |
| Existing Qwen cache | No Qwen3-TTS cache found under the inspected Hugging Face cache path |
| Existing local Torch installation | None found in inspected experiment/production site-packages path |

The model alone is 4.52 GB, before CPU PyTorch, tokenizer, runtime allocations, waveform buffers, and the operating system. With only 2.8 GiB available and swap already active, proceeding would create unsafe pressure and violates the explicit no-OOM/no-uncontrolled-swap constraint.

## Qwen Environment

Not created. Python 3.12 is unavailable, and no isolated environment was made. No system Python was altered.

## Model / Revision / License

No download/acquisition occurred, so no model revision was retrieved. The intended official identifier remains Qwen/Qwen3-TTS-12Hz-1.7B-VoiceDesign. Phase 30H observed Apache-2.0 on the official model card, but the exact revision/terms must be verified again immediately before a future acquisition.

## Voice Design Prompts

Not created or run. This avoids recording a misleading experiment setup for an audio PoC that was safely blocked.

## English Reference Text

Not created or synthesized.

## Qwen Candidate Generation

Not attempted. Zero candidates were generated; no retries occurred.

## Qwen Audio Validation

Not applicable. No Qwen audio exists.

## VieNeu Reference Encoding

Not attempted. No synthetic reference exists; production VieNeu was untouched.

## Vietnamese Test Text

Not synthesized.

## VieNeu Generation

Not attempted. No Vietnamese outputs exist.

## Measurements

| identity | Qwen duration | Qwen generation time | Qwen peak RSS | VieNeu duration | VieNeu generation time | VieNeu peak RSS | technical status |
|---|---:|---:|---:|---:|---:|---:|---|
| A | — | — | — | — | — | — | blocked at preflight |
| B | — | — | — | — | — | — | blocked at preflight |
| C | — | — | — | — | — | — | blocked at preflight |

## Blind Audition Layout

Not created. There are no source or Vietnamese WAV files because audio generation never started.

## Identity Preservation

Unmeasured.

## Vietnamese Quality

Unmeasured.

## Hardware Feasibility

Disk is sufficient. Current memory state is not: a 4.52 GB model cannot be responsibly loaded with 2.8 GiB available RAM and already-used zram, especially while preserving the active dirty workspace. Iris Xe is intentionally unused. CPU-only inference may be reconsidered only after memory availability is materially improved and Python 3.12 is available in an isolated environment.

## Findings

1. This machine has ample disk capacity for an isolated Qwen factory.
2. Current available RAM is insufficient for a safe 1.7B Qwen VoiceDesign CPU load.
3. Python 3.12 is absent, so the official recommended isolated runtime cannot presently be created.
4. The safety gate correctly prevented partial installation/download and an avoidable swap/OOM incident.

## Limitations

This is a preflight block, not an audio-quality result. No model, dependencies, or inference were run. Memory availability is point-in-time system state and can change after the user closes or stops other workloads.

## Decision

The original attempt was QWEN_RAM_BLOCKED. The retry cleared its RAM gate but
ended QWEN_RUNTIME_BLOCKED because model acquisition could not complete. Do not
substitute another model or bridge.

## User Listening Required

Not applicable; no audition files exist.

## Recommended Next Step

Free sufficient physical RAM by stopping user-owned heavy workloads, then re-run preflight. Proceed only when there is enough available memory for the model plus CPU runtime with a conservative margin, and after Python 3.12 can be provided in a new isolated environment without modifying the system or production environment.

## Production Changes

NONE.

## Regression / Static Checks

git diff --check must pass. No experiment script was created, so no Python compile check applies.

## Retry

### Memory Recheck

Retry preflight passed the requested memory gate: 8.8 GiB was available at
initial recheck (later 8.2–8.3 GiB while installing). Physical memory was 15 GiB
total. Zram was 30 GiB total with 1.8–2.0 GiB used. The process listing showed
no meaningful user-owned high-memory consumer. No process was killed.

### Python 3.12 Environment

The system package route required an interactive sudo password, so it was not
used. A workspace-local uv 0.12.7 installation provisioned isolated CPython
3.12.14 at qwen_voice_factory/.python, then created
qwen_voice_factory/.venv. Production Python 3.14.7 remained untouched.

### Qwen Runtime

Installed qwen-tts 0.1.1 into the isolated environment using uv explicit
CPU-only PyTorch selection. Verified torch 2.13.0+cpu and CUDA False. No
NVIDIA, CUDA, ROCm, flash-attn, or Iris Xe stack was installed. The expected
flash-attn-missing warning was observed but is non-fatal for CPU.

### Model Acquisition

Verified the intended official source again: Qwen/Qwen3-TTS-12Hz-1.7B-
VoiceDesign, revision main, with Apache-2.0 stated on the model card and the
official code repository. The official Hugging Face client began the 13-file
transfer but runner interruption left stale file locks. After clearing only
those stale locks, resumable direct transfers from the same official model URL
were attempted. The main 3.56 GiB weight transfer never advanced materially;
the tokenizer-weight transfer reached only a partial 682,293,092 bytes at about
15 KB/s before the runner terminated the transfer. No alternate model/source
was tried and no complete checkpoint exists.

### Model Load Measurements

Not applicable: the checkpoint is incomplete, so no model load was attempted.
The hard memory gate was not tested and no Qwen process was placed under load.

### Candidate Generation

Not attempted. No synthetic identity, Qwen WAV, retry, or stylistic selection
was generated.

### Qwen Audio Validation

Not applicable; no source WAV exists.

### VieNeu Bridge

Not attempted. VieNeu was not loaded or modified.

### Audition Layout

Not created. There are no source_01–03 or vietnamese_01–03 audition WAVs.

### Retry Decision

QWEN_RUNTIME_BLOCKED. The local isolated runtime is valid and memory preflight
passes, but current checkpoint acquisition cannot complete reliably in the
execution environment. Stop here; do not substitute another model, bridge, or
source, and do not start Phase 30J.

## Retry 2

### Environment Verification

Verified the existing isolated environment without reinstalling: CPython
3.12.14, qwen-tts import OK, torch 2.13.0+cpu, and torch.cuda.is_available()
False. The flash-attn warning is expected for CPU and no CUDA/ROCm/Iris Xe stack
is installed. Production Python and its environment remain untouched.

### Memory Recheck

At Retry 2 inspection, memory showed 15 GiB total and 7.3 GiB available with
1.9 GiB zram used. This is below the preferred 8 GiB pre-load target but above
the hard 7 GiB stop threshold. No model load is authorized until the complete
checkpoint is present and physical available RAM is rechecked at >=8 GiB.

### Existing Partial Model Cache

No active download process was present. The local official snapshot directory
contained all small configs/assets, a root speech_tokenizer/model.safetensors of
682,293,092 bytes (matching the previously observed approximately 650.6 MiB
download target), a 268,367,798-byte resumable main-weight incomplete cache
blob, and a 32,768-byte root main model.safetensors partial. Snapshot disk use
was 900 MB. All stale zero-byte .lock files were removed only after confirming
there was no active download owner; no payload, incomplete data, blob, or
completed asset was deleted.

### Resume Method

The official Hugging Face CLI from the existing isolated environment is the
correct resume mechanism. It reuses the local-dir metadata/cache and will only
fetch unresolved files. The agent command runner repeatedly terminates transfers
after short execution windows and cannot reliably keep this multi-gigabyte
foreground task alive.

### Download Progress

The estimated unresolved main-weight remainder is roughly 3.3 GiB, based on the
official card's approximately 3.56 GiB main safetensors and the 268 MB partial
blob. This is an estimate; the Hugging Face client is authoritative at resume.

### Completed Checkpoint Verification

Not reached. Required final check after terminal download: the command must
finish successfully, model.safetensors must be approximately 3.56 GiB rather
than 32 KiB, the tokenizer weight must remain present, and a zero-download local
load/resolve check must succeed.

### Model Load RAM Test

Not reached. Recheck available physical RAM before loading; do not load if it is
below 8 GiB.

### Candidate Generation

Not reached.

### VieNeu Bridge

Not reached.

### Audition Files

Not created.

### Retry 2 Decision

DOWNLOAD_REQUIRES_USER_TERMINAL. The Python/runtime is healthy, the official
partial cache is preserved and unlocked, but persistent model transfer is not
available to this coding-agent command runner. Do not load the model or create
audio until the user-run official resume command completes.

## Retry 3

### Local Checkpoint Verification

Verified locally without network access: the official Qwen VoiceDesign snapshot
directory is 4.3 GB and contains model.safetensors (3.6 GB),
speech_tokenizer/model.safetensors (651 MB), config.json, tokenizer_config.json,
vocab.json, merges.txt, and speech-tokenizer configuration assets.

### RAM Before Load

Before the initial generation attempt, MemAvailable was 8.2 GiB and zram usage
was 759.6 MiB. No significant user-owned memory consumer was listed.

### Qwen Model Load

The dedicated local CPU model-load test passed. It used the official local path,
device_map=cpu, torch.bfloat16, eager attention, offline environment flags, and
no CUDA, ROCm, flash-attn, or Iris Xe acceleration.

### Memory Measurements

Load time: 1.246 seconds. Process peak RSS: 1675.88 MB. MemAvailable before
load: 8,391,995,392 bytes; after load: 8,129,847,296 bytes. Swap used before:
1,230,790,656 bytes; after: 1,696,612,352 bytes. This is a successful real load
test, not a RAM block.

### VoiceDesign Candidate A

Not completed. The first authorized source-generation process reached Qwen's
generation stage (the model emitted its normal pad-token generation message),
but this coding-agent runner terminated the foreground process at its 30-second
execution boundary before a WAV was written.

### VoiceDesign Candidate B

Not attempted. The phase prohibits uncontrolled background work and repeated
generation retries.

### VoiceDesign Candidate C

Not attempted. The phase prohibits uncontrolled background work and repeated
generation retries.

### Source Audio Measurements

Not available: no Qwen WAV was completed, so no technical retry was consumed and
no source audio was assessed.

### Qwen Memory Release

The terminated foreground generation process was no longer present. The
standalone load-test process exited cleanly after writing its measurement.

### VieNeu Reference Encoding

Not attempted because all three source WAVs are required before bridging.

### Vietnamese Generation

Not attempted; production VieNeu code and environment remain untouched.

### Blind Audition Layout

Not created. No source or Vietnamese audition files exist.

### Retry 3 Decision

QWEN_RUNTIME_BLOCKED. The real model-load test proves the checkpoint and CPU RAM
fit, but the coding-agent execution runner terminates the slower CPU voice
generation before a valid 6–8 second WAV completes. No background process, new
model, new bridge, production modification, or Phase 30J work was started.

## Retry 4

### Why Manual Generation Is Required

Retry 3 proved that the local checkpoint loads safely on CPU, but this coding
agent's foreground command runner terminates slower CPU generation at roughly 30
seconds. A normal user Fedora terminal has no such agent timeout and is required
for the one-time source-generation stage.

### Manual Runner

Created qwen_voice_factory/generate_phase30i_sources.py. It is a finite
foreground script, not a daemon or production service. It uses only the existing
isolated Python 3.12 environment and local official VoiceDesign model.

### VoiceDesign Prompts

prompts.json now records exactly three attribute-only, non-imitative prompts:
Warm Deep Storyteller (A), Calm Distinctive Host (B), and Deep Textured Narrator
(C). No real person, public figure, creator, actor, narrator, or existing voice
is referenced.

### English Source Text

All three use the same original text: “In this quiet moment, we can slow down,
listen closely, and let a simple thought unfold with clarity.”

### Memory Safety

Before load, the runner prints MemAvailable and swap use. It exits with
QWEN_RAM_BLOCKED below 7 GiB, warns from 7–8 GiB, and otherwise uses the Retry 3
configuration: offline local model, CPU, torch.bfloat16, and eager attention.
It does not alter swap or use CUDA, ROCm, flash-attn, or Iris Xe.

### Output Paths

The three finite outputs are reference_audio/qwen_candidate_A.wav,
reference_audio/qwen_candidate_B.wav, and reference_audio/qwen_candidate_C.wav.
Objective duration, format, peak, RMS, clipping, and generation timing records
are written to measurements/source_generation.json. A valid existing output is
preserved on a future restart; an invalid generation receives only one technical
retry.

### Validation

The manual runner compiled with the isolated Python 3.12.14. Lightweight imports
verified qwen-tts and torch 2.13.0+cpu with CUDA False. Local model-path checks
passed. No model was loaded and no audio was generated during this preparation.

### User Command

Use the absolute Python and script paths stated in the Retry 4 handoff.

### Retry 4 Decision

MANUAL_QWEN_GENERATION_REQUIRED. Wait for the user to run the finite offline
source generator and return its terminal output before attempting VieNeu bridge
work.

## Retry 5

### Source Verification

All user-generated Qwen references were present and technically valid: each is
mono 24 kHz with no clipped samples. A: 8.080 s, peak 0.361328, RMS 0.062838.
B: 7.120 s, peak 0.648438, RMS 0.090596. C: 8.960 s, peak 0.585938, RMS
0.096027. No Qwen model was loaded and no source was regenerated.

### VieNeu Reference Encoding

All three references were independently passed through the existing native
VieNeu reference path, with denoise=False and use_ref_codes=True. Each produced
its own speaker embedding of shape [192] and own reference-code array: A
[99,16], B [87,16], C [101,16]. No embeddings or codes were mixed.

### Vietnamese Test Passage

All candidates used exactly this same text and punctuation: “Có những câu
chuyện không cần phải kể thật nhanh. Chỉ cần một giọng nói đủ gần gũi, một
khoảng dừng đúng lúc, và đôi khi chính những điều rất bình thường lại khiến
chúng ta muốn ngồi lại, lắng nghe lâu hơn một chút.”

### Generation Settings

Existing VieNeu ONNX production defaults were used with speed=1.0, denoise=False,
no DSP, no pitch/formant/EQ/bass/compression/reverb changes, no emotion tags, and
the same NumPy seed before each generation.

### Vietnamese Measurements

All outputs are playable, mono 48 kHz, and non-clipped. A: 13.440 s, peak
0.622437, RMS 0.100309, encode 2.089 s, generate 13.065 s. B: 10.480 s, peak
0.661072, RMS 0.105427, encode 0.720 s, generate 11.576 s. C: 11.840 s, peak
0.649597, RMS 0.112049, encode 0.971 s, generate 12.239 s. Peak process RSS
was 2.88 GB. Detailed records are in measurements/vieneu_generation.json.

### Blind Mapping

One deterministic A/B/C-to-number mapping was created in private_mapping.json.
It is intentionally omitted from this report and the normal handoff so the user
can audition blind. Each source_NN.wav and vietnamese_NN.wav pair is the same
identity.

### Identity Preservation Test

The technical pairing test is complete: three source WAVs and their matching
three Vietnamese reference-conditioned outputs exist. No automatic perceptual
or brand-quality verdict was made.

### User Listening Required

Listen to source_01 then vietnamese_01, then repeat for 02 and 03. Judge
same-person similarity, Vietnamese naturalness, remaining genericness, and
whether any voice invites continued listening. Do not infer those qualities from
the listed signal metrics.

### Retry 5 Decision

AUDITION_SET_GENERATED. This is technical success only; selection or further
optimization awaits user listening. Production changes remain NONE.
