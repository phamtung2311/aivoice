# PHASE 16 WORK REPORT

## Status

```text
PARTIAL
```

## Task

Persist the Phase 15 work report in the project, safely reload the verified AIVoice backend, and confirm that the live service loaded the Phase 15 clone compatibility code.

## Backend process before reload

```text
PID: 13882
Command: .venv/bin/python -m uvicorn backend.main:app --host 127.0.0.1 --port 8000
Working directory: /home/tung/ai voice
Port: 127.0.0.1:8000
Verified as aivoice backend: YES
```

Verification used `ps -fp 13882`, `/proc/13882/cwd`, `/proc/13882/cmdline`, and `ss -ltnp 'sport = :8000'`. All four checks identified the same project and process.

## Actions performed

1. Created `diagnostics/phase15_work_report.md` from the verified Phase 15 results.
2. Sent `SIGTERM` to the exact verified backend PID `13882`.
3. Confirmed PID `13882` exited and port 8000 was no longer listening.
4. Started the backend with the same verified command and explicit `TTS_MAX_CONCURRENCY=1`.
5. Waited for Uvicorn to report application startup complete.
6. Verified the new PID, command, working directory, listening port, health, voices, and both clone parameter sources.
7. Checked frontend HTTP availability and CORS behavior for both `127.0.0.1` and `localhost` origins.

## Backend process after reload

```text
PID: 34848
Command: .venv/bin/python -m uvicorn backend.main:app --host 127.0.0.1 --port 8000
Working directory: /home/tung/ai voice
Port: 127.0.0.1:8000
TTS_MAX_CONCURRENCY: 1
```

## Verification

```text
/api/health: PASS
/api/voices: PASS
Current clone contract: PASS - live FormData text reached the expected missing-reference validation; Phase 15 dummy ASGI request returned 200
Legacy clone contract: PASS - live query text reached the expected missing-reference validation; Phase 15 dummy ASGI request returned 200
Frontend connectivity: PARTIAL - frontend page returns 200, but the documented http://127.0.0.1:5173 origin is not allowed by backend CORS; http://localhost:5173 is allowed
```

The live current and legacy clone probes intentionally omitted `ref_audio`. Both returned `{"detail":"Thiếu tệp âm thanh tham chiếu"}`, proving the new process resolved text from the correct source without running inference.

## Files created

```text
diagnostics/phase15_work_report.md
diagnostics/phase16_work_report.md
```

## Files modified

```text
None
```

## Tests performed

```text
Process verification before reload:
ps -fp 13882
readlink -f /proc/13882/cwd
read /proc/13882/cmdline
ss -ltnp 'sport = :8000'
Result: PASS; PID 13882 was the AIVoice Uvicorn backend

Shutdown verification:
ps -p 13882 -o pid=,stat=,cmd=
ss -ltnp 'sport = :8000'
Result: PASS; process exited and port was free

Startup verification:
Uvicorn application startup complete
ps -fp 34848
readlink -f /proc/34848/cwd
ss -ltnp 'sport = :8000'
Result: PASS

GET /api/health:
Result: PASS; status=ok, model=pnnbao-ump/VieNeu-TTS-v2, device=cpu, max_text_length=10000

GET /api/voices:
Result: PASS; preset voice list returned

Current FormData live parsing:
POST /api/tts/clone with FormData text and no ref_audio
Result: PASS; reached missing-reference validation

Legacy query live parsing:
POST /api/tts/clone?text=Legacy%20query with no ref_audio
Result: PASS; reached missing-reference validation

Frontend HTTP:
GET http://127.0.0.1:5173/
Result: PASS; HTTP 200

CORS:
Origin http://localhost:5173
Result: PASS; access-control-allow-origin returned

Origin http://127.0.0.1:5173
Result: ISSUE; access-control-allow-origin was absent
```

## Existing changes preserved

All pre-existing modified and untracked workspace files were preserved. No reset, restore, cleanup, commit, push, dependency change, model benchmark, or real TTS inference was performed.

## Remaining issues

- Backend CORS allows `http://localhost:5173` but not the documented/running frontend origin `http://127.0.0.1:5173`; browsers opened at the latter origin cannot call the backend.
- Full and targeted pytest remain blocked by the known Python 3.14, Starlette 1.6.0, and httpx 0.28.1 TestClient/AnyIO incompatibility.

## Recommended next step

Align the backend CORS allowlist with the actual local frontend origin `http://127.0.0.1:5173` while preserving the existing `http://localhost:5173` origin.
