# PHASE 22.1 SAVED VOICE CONDITIONING REPORT

## Status

PASS — conditioning path understood from source, preset/saved structures compared, serialization verified, identity-only capability confirmed native, A/B pronunciation experiment prepared end-to-end. Final root-cause confirmation awaits the user's 8-step listening test. Zero agent-run real inference.

## User evidence

```text
Preset “người”:   “Mọi người đang ở đây.”  → ĐÚNG
Saved voice “người”: same exact text      → VẪN SAI (“ngờ i”-style)
```

Combined with Phase 22 (clean input → `ŋˈyə2j` correct phonemes), this moves the investigation off Unicode/text and onto saved-voice conditioning.

## VieNeu conditioning implementation

Source-inspected (`vieneu/v3turbo.py`, 3.3.0, unmodified):

```text
V3TurboVieNeuTTS.infer(
  text, ref_audio=None, voice: str|dict|None, style=None(deprecated/ignored),
  denoise=True, use_ref_codes: bool = True,
  temperature=0.8, top_k=25, top_p=0.95, max_new_frames=300,
  repetition_penalty=1.2, repetition_window, max_chars=256,
  silence_p=0.15, crossfade_p=0.0, apply_watermark=True, batch_size=None)
```

Control flow:

```text
speaker_emb, ref_codes = _resolve_ref(voice, ref_audio, denoise, use_ref_codes)
  ref_audio given  → engine.prepare_reference(..., use_ref_codes=use_ref_codes)
  voice str/dict   → _preset_voices lookup (saved voices registered here too)
  codes = preset.get("codes") if use_ref_codes else None
  fallback: voice=None → default preset; unknown name → ValueError
per chunk (phonemize → engine.infer(phonemes, speaker_emb, ref_codes, use_ref_codes, sampling))
```

Findings:

- `codes` are ALWAYS used when present (`use_ref_codes=True` default).
- `use_ref_codes=False` exists and yields `ref_codes=None` while keeping `speaker_emb` — speaker identity WITHOUT reference codes is a first-class native path.
- Reference codes feed the acoustic prompt (style is deprecated because “style đã nằm trong ref code”) — i.e. codes condition acoustic continuation, including prosody/pronunciation context from the enrollment clip.
- Preset voices use the SAME representation as saved voices (same dict keys, same resolve path).

## Preset profile structure

From `assets/voices_v3_turbo.json` loader: `{description: str, gender: str, style: str, speaker_emb: float32 flat (192-d per loader docstring), codes: int64 (or None)}`. Registered through the identical `_preset_voices` dict used for saved voices.

## Saved profile structure

Registered via native `add_voice(..., save=False)` into the same `_preset_voices`; persisted by us under `data/voices/voices.json` in Vieneu's own JSON shape: `{description, gender, style, speaker_emb: [6-decimal floats, flattened], codes: [ints]}`. Structure is identical to presets; only provenance differs.

## Persistence round-trip

```text
speaker_emb: float32 → JSON (flat, 6-decimal rounding) → float32
codes:       int64   → JSON ints → int64 (bit-exact)
dtype:       preserved on reload (float32 / int64)
shape:       emb flattened on store (matches vieneu save_voices() and preset assets); codes length preserved
precision:   emb values equal within ≤1e-6 (by-design quantization, NOT a bug — native presets ship the same way)
nesting:     none; no int/float corruption
```

No serialization defect found (Outcome D storage-bug hypothesis: RULED OUT). Verified by automated round-trip test without printing any biometric value.

## Reference-code behavior

Codes are passed per chunk unchanged (`use_ref_codes` forwarded by our engine into every Vieneu infer call); nothing is truncated; code length scales with enrollment duration (frames) and is kept in full. Our engine encodes the reference ONCE and reuses the same profile object for every chunk (Phase 17 fix re-proven by test). Presets ship their own pre-encoded codes, so the ONLY structural difference between the working preset and the failing saved voice is the CONTENT of emb+codes — not the mechanism.

## Identity-only support

```text
SUPPORTED
```

Verified from installed source (`codes = preset.get("codes") if use_ref_codes else None`). Exposed as a diagnostic only; no invented parameters.

## Experiment modes prepared

Voice Lab → Nâng cao → Round selector now includes:

```text
5 · Phát âm giọng clone (A/B)   [round=conditioning, saved-voice only]
Chế độ: A · Đầy đủ tham chiếu   (current behavior, emb + codes)
        B · Chỉ giữ đặc trưng giọng (identity-only, use_ref_codes=False)
```

- Locked baseline: `speed=1.0, temperature=0.8, top_k=25, top_p=0.95, repetition_penalty=1.2` (one variable = conditioning mode).
- Sentences from the controlled corpus (`Mọi người đang ở đây.` / `Người Việt Nam luôn yêu tiếng Việt.` / `Tôi cười với mọi người.`; `Mười người đang đứng ngoài cửa.` also in the quality corpus for the mười/người stress pair).
- Repeatability budget: 2 modes × 1 sentence × 2 runs = 4 samples max, one at a time (existing `TTS_MAX_CONCURRENCY=1` semaphore; no batching).
- Explicit boolean verdict `Đọc “người” đúng: YES/NO` is stored as `pronunciation_ok` and rendered as ✓/✗ in history — never folded into the average score.
- Experiment JSON records `saved_voice_id`, `conditioning_mode`, text id, sampling, run number, scores, notes, runtime — and NEVER `speaker_emb`/`codes` (test-enforced).
- UI uses human-readable labels only (“Đầy đủ tham chiếu” / “Chỉ giữ đặc trưng giọng”); `speaker_emb`/`use_ref_codes` appear nowhere in frontend source (test-enforced).

## Main production behavior

- `/api/tts` gained an optional `conditioning_mode` field; when absent the generate call is byte-identical to pre-22.1 (test asserts `use_ref_codes` is not passed and schema default is None).
- `identity_only` is accepted ONLY for saved (cloned) voices — presets and the clone route reject it (400/422). No default switch, no silent production change.
- Engine signature untouched; the diagnostic maps to the existing native `use_ref_codes` parameter.

## Tests

```text
node --check frontend/app.js: PASS
python -m py_compile backend/main.py backend/app/voice_lab.py backend/app/tts/voice_store.py backend/app/tts/model.py: PASS
pytest tests/test_phase22_1_saved_voice_conditioning.py → 12 passed
FULL SUITE pytest -q tests/ → 124 passed, 1 warning (pre-existing Starlette deprecation)
git diff --check: PASS
```

New coverage: profile round-trip dtype/shape/values incl. the 1e-6 quantization bound and bit-exact codes; conditioning round schema validation (saved voice + mode + baseline locked); evaluation requires explicit pronunciation verdict; experiment JSON free of identity arrays; identity-only via `/api/tts` (saved-voice pass, preset 400, unknown mode 422); production call invariance; engine `use_ref_codes` default-True + identity-only passthrough; one voice profile reused across chunks (Phase 17); frontend human-labels-only UI contract; Phase 22 Unicode hygiene still active.

## Regression

```text
Main TTS: PASS · History audio: PASS · Voice Lab rounds 1–4 + Save Voice WAV/MP3/M4A: PASS
Clone /api/tts/clone WAV/MP3/M4A: PASS (route untouched) · temperature workflow: PASS
Quality + pronunciation corpora: PASS · Unicode hygiene (Phase 22): PASS
CORS + runtime metadata + TTS_MAX_CONCURRENCY=1: PASS
No dependency changed; installed Vieneu/sea_g2p untouched; nothing committed/pushed/reset.
```

## Real inference

```text
0 (zero) agent-run inferences. All samples are user-triggered Voice Lab generations, one at a time.
```

## USER MUST TEST

```text
1. same saved voice
2. sentence “Mọi người đang ở đây.”
3. Full Reference Run 1
4. Full Reference Run 2
5. Identity-only Run 1
6. Identity-only Run 2
7. report which ones pronounce “người” correctly
8. report which mode sounds more like the original voice
```

Tick `Đọc “người” đúng` YES/NO for each run in Voice Lab; the history row will show A/B mode plus ✓/✗. Restart backend + hard reload first (backend and frontend changed).

## Root-cause status

Ranked by evidence:

1. **Reference-code conditioning on the cloned voice** — primary open candidate. Mechanism verified in source (codes condition the acoustic prompt); preset-vs-saved difference is now reducible to codes via the prepared A/B. Outcome A (FULL fails / identity-only succeeds) would confirm codes; Outcome C within a mode implicates sampling.
2. **Sampling stochasticity** — user reports intermittency; run-pair per mode will quantify it. If both modes fail while preset passes → Outcome B (speaker conditioning/model robustness).
3. **Saved-profile serialization bug** — RULED OUT at the storage layer (round-trip exact for codes; emb quantized ≤1e-6 identically to Vieneu's own format; presets restored through the same path).
4. **Text/Unicode/phonemizer** — RULED OUT (Phase 22 probe + preset listening evidence).

## Recommended next step

```text
REFERENCE-CODE CONDITIONING FIX
```

— primary, conditional on the user's 8-step A/B result confirming Outcome A. If instead both modes fail (Outcome B), switch to `LOWER-TEMPERATURE PRONUNCIATION TEST`; if identity-only also breaks similarity without pronunciation benefit, `MODEL LIMITATION / REFERENCE RE-ENROLLMENT EXPERIMENT`. Do not automatically continue.

