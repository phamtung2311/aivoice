# PHASE 22.3 REAL PRONUNCIATION DIAGNOSTIC REPORT

## Status

COMPLETE — 8 real diagnostic samples generated through the live production backend; manifest + WAVs saved. Waiting on user listening. No production change made.

## Real inference count

8 (the maximum budget). All via the already-running backend singleton (uvicorn PID 64780) at `127.0.0.1:8000/api/tts`; one request at a time; no second model process; no benchmark.

## Preset used

`Trúc Ly` (explicit preset ID from `/api/voices`, type=`preset`) — used for all preset samples.

## Saved voice used

`tùng` (type `saved`) — user-selected (the registry also contains `tùng 2`; that one was NOT auto-run to avoid silently picking the wrong identity).

## Files generated

All under `diagnostics/audio/phase22_3/`:

```text
preset_t08_r1.wav        Trúc Ly  · full · temp 0.8 · run 1
preset_t08_r2.wav        Trúc Ly  · full · temp 0.8 · run 2
preset_t08_r3.wav        Trúc Ly  · full · temp 0.8 · run 3
preset_t07_r1.wav        Trúc Ly  · full · temp 0.7 · run 1
saved_full_t08_r1.wav    tùng     · full · temp 0.8 · run 1
saved_full_t08_r2.wav    tùng     · full · temp 0.8 · run 2
saved_full_t07_r1.wav    tùng     · full · temp 0.7 · run 1
saved_identity_t08_r1.wav tùng    · identity_only · temp 0.8 · run 1
```

## Exact generation settings

Every request: `text = "Mọi người đang ở đây."`, `speed=1.0`, `top_k=25`, `top_p=0.95`, `repetition_penalty=1.2`; temperature = 0.8 or 0.7 as labeled; `conditioning_mode` only on the identity-only sample (`identity_only`), which is valid only for a saved voice. No hidden preferred-config override: the diagnostic bypassed the browser, so no localStorage/selector/candidate-config could leak in.

## Manifest path

`diagnostics/audio/phase22_3/manifest.json` — contains only filename, voice_id, voice_type, conditioning_mode, temperature, top_k, top_p, repetition_penalty, speed, duration, sample_rate (plus peak/rms added for the structural section). No text beyond the fixed test id, **no embeddings/codes**.

## Structural metrics

```text
preset_t08_r1          sr=48000 dur=1.44s peak=0.483 rms=0.105
preset_t08_r2          sr=48000 dur=1.84s peak=0.379 rms=0.106
preset_t08_r3          sr=48000 dur=1.44s peak=0.425 rms=0.107
preset_t07_r1          sr=48000 dur=1.44s peak=0.408 rms=0.112
saved_full_t08_r1      sr=48000 dur=6.24s peak=0.727 rms=0.066
saved_full_t08_r2      sr=48000 dur=6.56s peak=0.701 rms=0.073
saved_full_t07_r1      sr=48000 dur=2.08s peak=0.757 rms=0.090
saved_identity_t08_r1  sr=48000 dur=2.08s peak=0.482 rms=0.086
```

(Numerical observation only — duration/peak differ between preset (~1.4s) and saved-full (~6s); NO pronunciation verdict is inferred from these numbers.)

## Production code changed

NO. Only new files: `scripts/phase22_3_real_pronunciation_probe.py` plus the diagnostics output. No default temperature, conditioning, profile, phonemizer, normalization, chunking, or frontend change.

## USER MUST LISTEN

Play each file and mark `ĐÚNG / SAI` for the word "người":

```text
preset_t08_r1.wav          : Đúng / Sai
preset_t08_r2.wav          : Đúng / Sai
preset_t08_r3.wav          : Đúng / Sai
preset_t07_r1.wav          : Đúng / Sai

saved_full_t08_r1.wav      : Đúng / Sai
saved_full_t08_r2.wav      : Đúng / Sai
saved_full_t07_r1.wav      : Đúng / Sai
saved_identity_t08_r1.wav  : Đúng / Sai
```

Also answer:

```text
- saved FULL hay saved IDENTITY-ONLY giống voice gốc hơn?
- file nào đọc "người" SAI? (liệt kê tên)
```

## Interpretation guide

After you report the table:

```text
Case A  preset 0.8 mixed đúng/sai        → stochastic/model acoustic evidence strong
Case B  preset 0.8 sai hết, 0.7 đúng    → temperature-sensitive pronunciation robustness
Case C  preset đúng, saved-full sai, saved-identity đúng → reference-code conditioning implicated
Case D  preset đúng, cả hai saved sai   → speaker-conditioning/reference/model limitation
Case E  mọi thứ sai                      → broader model/acoustic or test-word weakness
```

No decision is made before your listening result.

## Recommended next step

WAIT FOR USER LISTENING RESULTS — then map to the matching case above. Do not tune production automatically.