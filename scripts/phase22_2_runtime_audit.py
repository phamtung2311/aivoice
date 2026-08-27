# Phase 22.2 runtime audit (§11). Read-only: never kills or restarts anything.
# Verifies WHICH code the live backend/frontend actually run, and compares
# process start times against source mtimes to expose stale-runtime mixes.
import json
import os
import pathlib
import urllib.request

ROOT = pathlib.Path(__file__).resolve().parent.parent
BACKEND_DIR = ROOT / "backend"
FRONTEND_DIR = ROOT / "frontend"


def proc_candidates():
    out = []
    for entry in os.listdir("/proc"):
        if not entry.isdigit():
            continue
        try:
            cmdline = (pathlib.Path("/proc") / entry / "cmdline").read_bytes().replace(b"\x00", b" ").decode(errors="replace").strip()
        except Exception:
            continue
        if not cmdline:
            continue
        lowered = cmdline.lower()
        if any(marker in lowered for marker in ("uvicorn", "backend.main", "main:app", "8000", "http.server", "5173", "vite")):
            try:
                cwd = os.readlink(f"/proc/{entry}/cwd")
            except Exception:
                cwd = "?"
            try:
                stat_fields = (pathlib.Path("/proc") / entry / "stat").read_text().rsplit(") ", 1)[1].split()
                ticks = int(stat_fields[19])
                started_s = (pathlib.Path("/proc/uptime").read_text().split()[0])
                uptime = float(started_s)
                import datetime
                started_at = datetime.datetime.now() - datetime.timedelta(seconds=uptime - ticks / os.sysconf("SC_CLK_TCK"))
                started_at = started_at.strftime("%Y-%m-%d %H:%M:%S")
            except Exception:
                started_at = "?"
            out.append({"pid": int(entry), "cwd": cwd, "started_at": started_at, "cmdline": cmdline[:200]})
    return out


def newest_source_mtime():
    newest = 0.0
    newest_path = ""
    import datetime
    for base in (BACKEND_DIR, FRONTEND_DIR):
        for p in base.rglob("*.py"):
            m = p.stat().st_mtime
            if m > newest:
                newest, newest_path = m, str(p)
        for p in base.rglob("*.js"):
            m = p.stat().st_mtime
            if m > newest:
                newest, newest_path = m, str(p)
        for p in base.rglob("*.html"):
            m = p.stat().st_mtime
            if m > newest:
                newest, newest_path = m, str(p)
    return newest_path, newest


def fetch(url, timeout=4):
    try:
        with urllib.request.urlopen(url, timeout=timeout) as r:
            return r.status, r.read()
    except Exception as exc:
        return None, repr(exc).encode()


def main():
    report = {"processes": proc_candidates()}
    newest_path, newest_mtime = newest_source_mtime()
    import datetime
    report["newest_source"] = {"path": newest_path, "mtime": datetime.datetime.fromtimestamp(newest_mtime).strftime("%Y-%m-%d %H:%M:%S")}

    status, body = fetch("http://127.0.0.1:8000/openapi.json")
    if status == 200:
        schema = json.loads(body)
        props = schema.get("components", {}).get("schemas", {}).get("TTSRequest", {}).get("properties", {})
        report["backend_openapi"] = {
            "tts_request_has_conditioning_mode": "conditioning_mode" in props,
            "title": schema.get("info", {}).get("title"),
        }
    else:
        report["backend_openapi"] = {"error": body[:200].decode(errors="replace")}

    status, body = fetch("http://127.0.0.1:8000/api/health")
    report["backend_health"] = body[:300].decode(errors="replace") if status == 200 else body[:200].decode(errors="replace")

    for port in (5173, 8000):
        status, body = fetch(f"http://127.0.0.1:{port}/")
        if status == 200 and b"app.js" in body:
            import re
            m = re.search(rb"app\.js\?v=([0-9.]+)", body)
            version = m.group(1).decode() if m else "?"
            status2, js = fetch(f"http://127.0.0.1:{port}/app.js?v={version}")
            served = js.decode(errors="replace") if status2 == 200 else ""
            report[f"served_frontend_{port}"] = {
                "asset_version": version,
                "has_build_21_1": "AIVOICE_FRONTEND_BUILD = '21.1'" in served,
                "has_conditioning_ui": "voiceLabConditioningMode" in served,
            }
            break
    else:
        report["served_frontend"] = "no HTML/app.js found on 5173 or 8000"

    print(json.dumps(report, ensure_ascii=False, indent=1))


if __name__ == "__main__":
    main()
