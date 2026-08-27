# PHASE 17 WORK REPORT

## Status

```text
PASS
```

## Executive summary

Phase 17 closes the platform-stabilization stage. Both supported frontend origins now pass normal and preflight CORS checks, the live backend and frontend are healthy, the frontend/API contracts remain aligned, clone identity is passed to VieNeu v3 through its native voice-profile representation, and the backend is still protected by a process-wide concurrency limit of one.

No real TTS inference, stress test, model download, dependency change, database change, reset, cleanup, commit, or push was performed. Browser automation was not connected, so DOM playback and IndexedDB behavior are code-audited but browser-interactive `NOT VERIFIED`, as permitted by the Phase 17 success criteria.

Platform stabilization is `PASS`. Readiness to begin a small, controlled branded-voice experiment is `PARTIAL`: the identity pipeline is ready, but experiment metadata/presets and a listening protocol do not exist yet, and the health endpoint reports the wrapper's stale v2 label while installed VieNeu 3.3.0 actually selects V3 Turbo by default.

## 17.1 CORS

```text
localhost: PASS
127.0.0.1: PASS
```

The allowlist is explicit and contains only:

```text
http://localhost:5173
http://127.0.0.1:5173
```

Both a normal `GET /api/health` with `Origin` and an `OPTIONS /api/tts` preflight returned the matching `access-control-allow-origin`. No wildcard was introduced.

## 17.2 Frontend runtime

```text
frontend HTTP: PASS (127.0.0.1:5173 -> 200)
backend health: PASS
voice list: PASS (20 preset voices)
JavaScript syntax: PASS
browser interactive verification: NOT AVAILABLE
```

The browser runtime connected successfully but reported no available browser instances. No standalone browser dependency or alternate automation stack was installed. Static initialization and HTTP contracts were checked instead.

## 17.3 History / IndexedDB

```text
metadata: localStorage key tts_history, normalized and capped at 20 entries
audio Blob: IndexedDB aivoice_history / history_audio, capped at 10 audio entries
replay old audio: idbGetAudio -> Blob validation -> Object URL -> audioEl.play
reload persistence: loadHistory reads localStorage and replay fetches the linked IndexedDB Blob
browser verified: NOT AVAILABLE
```

`playHistoryItem()` contains no `fetch()` or `synthesize()` call, so replay does not issue `POST /api/tts`. Regeneration is an explicitly separate `regenerateFromHistory()` action. Missing, undersized, unavailable, or corrupt audio falls back to a user-visible error instead of generating again or throwing an uncaught path.

## 17.4 Voice preview

```text
fixed text: Xin chao, day la giong doc mau cua aivoice. (Vietnamese diacritics in source)
API: POST /api/tts
history pollution: NO
parallel preview requests: NO; previous request is aborted
cache: in-memory per voice at speed 1.0
browser playback: NOT VERIFIED
```

The fixed preview request and WAV response contract passed with a direct dummy-engine test. Preview code does not call the history persistence path. No real inference was run.

## 17.5 Clone

```text
WAV: PASS
MP3: PASS (decoded with soundfile/libsndfile)
M4A: PASS (decoded with FFmpeg 8.1.2)
```

The UI accept list, drop validation, metadata display, 5 MiB limit, conversion status, FormData mapping, backend extension validation, duration validation, and temporary-file cleanup paths were audited. Direct endpoint-function smoke tests with a dummy engine produced WAV responses for valid WAV, MP3, and M4A fixtures.

The clone identity integration was corrected: `(speaker_emb, ref_codes)` is now reused as VieNeu v3's native `{speaker_emb, codes}` voice profile for every outer text chunk. Previously, `speaker_emb` was discarded and `ref_codes` was passed as an ignored extra keyword to `V3TurboVieNeuTTS.infer()`, which could fall back to the selected/default preset instead of the uploaded identity.

## 17.6 Saved voice

```text
WAV save: PASS
MP3/M4A save: intentionally rejected with UI guidance
list after save: PASS with dummy engine
reload persistence: PASS with fake VieNeu instance and temporary voice store
real user data changed: NO
```

Saved voices persist neither the raw WAV nor a database row. The local `data/voices/voices.json` representation contains a speaker embedding and reference acoustic codes plus description/gender/style metadata. A fresh `ModelLoader` restores those arrays into VieNeu without re-encoding the original reference.

## 17.7 Main TTS workflow

```text
text validation: empty rejected; 10,000-character API/UI limit aligned
chunking: outer sentence-aware chunks up to 400 characters; VieNeu v3 has its own 256-character default
voice: loaded from /api/voices and validated server-side
speed: 0.5x-2.0x; implemented as post-generation linear resampling
sampling: temperature, top_k, top_p, repetition_penalty forwarded only when supplied
invalid sampling: live HTTP 422 confirmed
generating state: set before request and cleared through finishRequest/finally
result validation: content type, WAV signature, and browser decode checked before replacing current audio
download: generated Blob -> temporary Object URL -> timestamped WAV
history: successful main generation stores metadata plus the generated Blob
```

The main flow is contract-complete. Browser interaction and a real generated WAV were not exercised in this phase.

## 17.8 Resource safety

```text
backend processes: 1 (PID 38927 at report time)
frontend processes: 1 (PID 31191 at report time)
backend port: 127.0.0.1:8000
frontend port: 127.0.0.1:5173
TTS_MAX_CONCURRENCY: 1
semaphore: process-wide threading.BoundedSemaphore around main TTS, clone inference, upload inference, and saved-voice enrollment
```

The final backend command and cwd are:

```text
.venv/bin/python -m uvicorn backend.main:app --host 127.0.0.1 --port 8000
/home/tung/ai voice
```

No concurrency benchmark, CPU stress, long text, duplicate model service, or mass generation was used.

## Bugs found and fixed

```text
backend/main.py
-> bug: CORS allowed localhost but blocked the running/documented 127.0.0.1 frontend origin
-> fix: explicit two-origin local allowlist
-> verification: live normal requests and OPTIONS preflight pass for both origins

backend/app/tts/engine.py
-> bug: clone encoding discarded speaker_emb and sent ref_codes through a keyword ignored by VieNeu v3 public infer()
-> fix: pass the encoded identity as native {speaker_emb, codes} voice profile for every chunk
-> verification: tests/test_engine_reference.py passes and installed VieNeu v3 source/signatures confirm the native representation
```

## Files changed this phase

```text
backend/main.py
backend/app/tts/engine.py
tests/test_engine_reference.py
diagnostics/phase17_work_report.md
```

Other modified and untracked workspace files predated Phase 17 and were preserved.

## Tests performed

```text
git status --short: baseline and final inspected
git diff --stat: baseline inspected
git diff --check: PASS before and after implementation

Live process checks:
ps, /proc/<pid>/cwd, /proc/<pid>/cmdline, /proc/<pid>/environ, ss
Result: PASS; one backend, one frontend, correct cwd/command, concurrency=1

Live HTTP:
GET /api/health: PASS
GET /api/voices: PASS
GET frontend /: PASS (200)
normal CORS for localhost and 127.0.0.1: PASS
OPTIONS preflight for localhost and 127.0.0.1: PASS
invalid main sampling: PASS (422)
current FormData clone parsing without reference: PASS (400 expected validation)
legacy query clone parsing without reference: PASS (400 expected validation)

Static/runtime checks:
python -m py_compile selected backend modules: PASS
node --check frontend/app.js: PASS
pytest --collect-only: PASS (55 tests collected)
tests/test_engine_reference.py: PASS (1 test)
saved voice persistence/reload with fake VieNeu and temporary store: PASS
frontend history/preview/clone-save static contract script: PASS

Direct endpoint-function assertions with a dummy engine:
health + fixed preview WAV contract: PASS
main invalid sampling -> 422: PASS
clone WAV/MP3/M4A -> WAV: PASS
clone invalid sampling -> 422: PASS
save WAV then list as saved: PASS
reject MP3 saved voice: PASS
legacy query parsing: PASS
```

The direct endpoint script printed all PASS assertions, then required interruption while Python shut down its executor. This is recorded as the known environment problem, not as a clean suite exit.

## Known environment issues

```text
Python: 3.14.7
FastAPI: 0.141.1
Starlette: 1.6.0
httpx: 0.28.1
VieNeu: 3.3.0
```

- FastAPI/Starlette sync route execution through AnyIO/TestClient can hang in this environment. Full pytest was not run and dependencies were not changed. Collection, pure unit tests, direct-function assertions, syntax checks, and live HTTP validation were used.
- No browser instance was connected, so IndexedDB persistence, audio playback, and button behavior are browser-interactive `NOT VERIFIED`.
- `/api/health` reports `pnnbao-ump/VieNeu-TTS-v2` from the wrapper's `model_name`, but installed VieNeu 3.3.0's factory defaults to `V3TurboVieNeuTTS`; the supplied `model_name` is accepted through `**kwargs` and is not the V3 Turbo `backbone_repo`. Experiment records must use the actual runtime family, not the current health label.

# VOICE LAB READINESS

## Voice identity implementation

VieNeu v3 Turbo enrolls a reference into two complementary native components:

```text
speaker_emb: speaker anchor / identity representation
ref_codes: acoustic reference frames used in-context for fidelity
```

Clone requests convert supported uploads to a readable WAV, trim edge silence, optionally denoise, encode once, and now reuse the native voice dict across all chunks. A selected preset does not override the uploaded reference after the Phase 17 fix.

## Saved voice representation

The saved profile is local JSON containing `speaker_emb`, `codes`, and small metadata fields. The raw reference recording is not retained. This is sufficient to re-register the same voice identity on process restart without re-encoding, but the embedding/codes are biometric-like personal data and should remain local and protected.

## Native controllable parameters

```text
Native model controls exposed end-to-end:
temperature
top_k
top_p
repetition_penalty
reference speaker_emb
reference codes / use_ref_codes
inline emotion tokens through text phonemization

Accepted by VieNeu but not exposed by AIVoice UI/API:
repetition_window
max_new_frames
max_chars
silence_p / gap behavior
batch_size (GPU path; irrelevant to current CPU safety policy)
```

## Prosody capabilities

```text
speed: post-processing, not native prosody; linear resampling changes duration and pitch together
pause: punctuation/paragraph-driven chunk gaps in VieNeu v3 plus outer sentence chunking; no direct pause slider
intonation: no explicit native control exposed
pitch: no independent control exposed
energy: no independent control exposed
style: deprecated and ignored by VieNeu v3 Turbo; style is implied by reference identity/codes
```

Text punctuation and reference delivery are therefore the practical prosody levers. Speed should be treated cautiously in branded-voice evaluation because the current implementation is not pitch-preserving time stretch.

## Emotion capabilities

Installed `vieneu_utils` verifies these native inline mappings:

```text
[cười] / [chuckle] -> <|emotion_1|>
[thở dài] / [sigh] -> <|emotion_2|>
[hắng giọng] / [clear throat] -> <|emotion_3|>
```

These cues survive v3 phonemization and are supported by the emotion checkpoint path. Arbitrary named emotions are not verified. The clone form accepts only `natural`, mapped to `<|emotion_0|>`, but V3 Turbo's public `infer()` ignores the wrapper's extra `emotion_tag` keyword; the effective non-verbal controls are the inline text cues above.

## Sampling behavior

```text
temperature: divides logits; lower values reduce variation, higher values increase variation and artifact risk
top_k: keeps only the k strongest candidates before sampling
top_p: nucleus filtering within the top-k candidate set
repetition_penalty: penalizes recently generated acoustic codes per channel to reduce loops/repeated artifacts
```

Defaults are `0.8 / 25 / 0.95 / 1.2`. These parameters can influence stability, naturalness, and run-to-run variation, but they do not define speaker identity. Very restrictive sampling can flatten or destabilize delivery; very loose sampling can increase variation and artifacts. No grid benchmark was performed.

## Reference-audio constraints

```text
API upload size: <= 5 MiB
effective duration: <= 8 seconds on current ONNX V3 Turbo engine
clone formats: WAV, MP3, M4A
saved voice format: WAV only
channels: downmixed to mono
sample rate: flexible input; internal encoder/codec resampling handles required rates
edge silence: trimmed before enrollment
denoise: enabled by default when the engine denoiser is available
```

For stable identity experiments, the highest-value reference properties are one speaker, clean close-mic speech, little room noise/music/reverb, minimal leading/trailing silence, no clipping, and a consistent natural delivery. A clip long enough to cover varied Vietnamese phonemes but within the 8-second cap should be preferred; Phase 18 should compare several such references rather than assume one recording is optimal.

## Current limitations

- The health endpoint's model label does not identify the actual VieNeu V3 Turbo runtime.
- No style-preset object currently binds a saved voice to sampling/speed/text-cue settings.
- No listening rubric, fixed evaluation corpus, repeatability score, or experiment manifest exists.
- Speed is non-pitch-preserving post-processing.
- Browser persistence/playback remains unverified in an interactive browser.
- Saved voice profiles are local biometric-like arrays without encryption or authentication; this is acceptable for the current local personal tool but must remain local.

## Is AIVoice ready for branded-voice experiments?

```text
PARTIAL
```

The platform is ready to start a small, controlled experiment: reference identity can be cloned, persisted, reloaded, and combined with real sampling controls under a single-inference safety limit. It is not yet ready to declare a production branded voice because experiment reproducibility, listening evaluation, configuration presets, and the runtime model label still need to be addressed.

## Remaining blockers before Voice Lab

There is no blocker to starting a lightweight Phase 18 experiment. Before treating results as authoritative, Phase 18 must:

1. Record the actual VieNeu runtime family/version instead of trusting the current health model label.
2. Define fixed evaluation sentences, repeat count, and a listening rubric.
3. Record reference identity and parameter values together because saved voice currently persists identity only.
4. Perform one manual/browser verification of history replay and saved-voice selection if browser automation remains unavailable.

## Recommended Phase 18

### VOICE LAB - BRANDED VOICE EXPERIMENT

1. Prepare three clean 4-8 second WAV references from the same speaker (`Reference A/B/C`) with consistent natural delivery and different phonetic coverage.
2. Define a fixed six-sentence Vietnamese evaluation set: brand intro, short call-to-action, numbers/dates, punctuation-heavy sentence, longer narrative sentence, and one verified inline emotion cue.
3. Establish the native baseline: speed `1.0`, temperature `0.8`, top_k `25`, top_p `0.95`, repetition_penalty `1.2`.
4. Compare A/B/C at the baseline, two repeats each. Score identity consistency, pronunciation, naturalness, prosody, noise/artifacts, and repeatability on a simple 1-5 rubric.
5. Keep the best reference fixed. Vary one sampling dimension at a time with a small set, for example temperature `0.7/0.8/0.9`, then top_p `0.90/0.95`, then repetition_penalty `1.1/1.2/1.3`. Do not run a Cartesian grid.
6. Keep speed at `1.0` during identity selection. Evaluate speed separately only after the voice is stable because current resampling changes pitch.
7. Save the winning identity and write a lightweight branded-voice manifest containing actual runtime version, reference ID, sampling values, allowed text cues, evaluation date, and rubric scores.
8. Define at most two evidence-based style presets through text punctuation/cues and sampling, then re-run the same fixed sentences to confirm identity remains stable.

Phase 18 is not implemented in this report.
