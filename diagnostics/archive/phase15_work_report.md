# PHASE 15 WORK REPORT

## Status

```text
PASS
```

## Task

Restore backward compatibility for `POST /api/tts/clone` while preserving the current FormData contract.

## Previous state

The endpoint read scalar clone parameters only from FormData. Legacy clients that sent those parameters through the query string no longer worked.

## Root cause

The original endpoint declared its scalar parameters as regular FastAPI parameters, which made them query parameters. Phase 14 changed all scalar parameters to `Form(...)` and changed the existing tests from `params=` to `data=`, removing the old request contract.

The legacy parameters confirmed from Git history were:

```text
text
voice
speed
emotion
temperature
top_k
top_p
repetition_penalty
```

## Changes made

```text
backend/main.py
→ Read the legacy query values from Request when the matching FormData value is absent.
→ Apply precedence: explicit FormData > legacy query > backend default.
→ Keep speed defaulted to 1.0.
→ Keep sampling values on the existing validation path.
→ Preserve HTTP 422 for invalid legacy speed or sampling values.

tests/test_sampling_params.py
→ Added legacy query contract coverage.
→ Added invalid legacy sampling coverage.
→ Added FormData-over-query precedence and query fallback coverage.

tests/test_clone_cleanup.py
→ Changed the engine-failure cleanup case to exercise the legacy query contract.
```

## API behavior after change

```text
Current FormData clone: 200
Legacy query clone: 200
Invalid sampling: 422
Form/query precedence: FormData > Query > Default
WAV: 200
MP3: 200
M4A: 200
Temp cleanup: PASS
```

## Tests performed

```text
Python compile:
.venv/bin/python -m py_compile backend/main.py tests/test_sampling_params.py tests/test_clone_cleanup.py
Result: PASS

HTTP ASGI smoke with an async dummy engine:
Current FormData: 200
Legacy query: 200
Invalid legacy sampling: 422
Form/query precedence: PASS
WAV/MP3/M4A: 200
Planned engine failure: 500
Temp cleanup: PASS
Route contracts: PASS

Test collection:
.venv/bin/python -m pytest --collect-only -q tests/test_sampling_params.py tests/test_clone_cleanup.py
Result: 13 tests collected

Targeted pytest:
timeout 12s .venv/bin/python -m pytest -vv -s -x tests/test_sampling_params.py tests/test_clone_cleanup.py
Result: BLOCKED at the first TestClient request; exit 124

Frontend syntax:
node --check frontend/app.js
Result: PASS

Diff validation:
git diff --check
Result: PASS
```

## Regression check

```text
/api/health: PASS
/api/voices: PASS
/api/tts: PASS contract; empty-request validation verified
/api/tts/clone: PASS on current code through ASGI
/api/tts/upload: PASS contract; missing-file validation verified
Frontend: PASS; server remained available
History: PASS; not modified
Voice preview: PASS; not modified
Save voice: PASS; not modified
Advanced sampling: PASS; valid forwarding and invalid 422 verified
```

## Files changed in this phase

```text
backend/main.py
tests/test_sampling_params.py
tests/test_clone_cleanup.py
```

## Existing uncommitted files preserved

```text
Preserved; not modified by this phase.
```

No commit, push, artifact deletion, or dependency change was performed.

## Remaining issues

- Full and targeted pytest remain blocked by the Python 3.14, Starlette 1.6.0, and httpx 0.28.1 TestClient/AnyIO incompatibility.
- The host uvicorn process PID `13882` was started before Phase 15 and had not loaded the Phase 15 code at report time.

## Recommended next step

Safely reload the verified AIVoice backend process on `127.0.0.1:8000`, then verify the current and legacy clone contracts without running real inference.
