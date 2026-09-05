#!/usr/bin/env bash
set -euo pipefail

# Phase 41F must be run externally after the static preflight. It never invokes TTS.
readonly ROOT="experiments/brand_voice_phase41f"
readonly SOURCE="experiments/brand_voice_phase41e/audio/v3_semantic_focus_final.wav"
readonly EXPECTED_SOURCE_SHA256="51e4bd659d4d3d9d9dae236f08d5d6c9aaa704cf825553cd81cf5707bb874569"
readonly AUDIO_DIR="$ROOT/audio"
readonly BLIND_DIR="$ROOT/blind"

command -v ffmpeg >/dev/null
command -v ffprobe >/dev/null

actual_source_sha256="$(sha256sum "$SOURCE" | cut -d ' ' -f 1)"
if [[ "$actual_source_sha256" != "$EXPECTED_SOURCE_SHA256" ]]; then
    echo "Source hash mismatch; refusing Phase 41F transformation." >&2
    exit 1
fi

mkdir -p "$AUDIO_DIR" "$BLIND_DIR"

# The baseline remains byte-identical to the winning Phase 41E WAV.
cp -- "$SOURCE" "$AUDIO_DIR/baseline.tmp.wav"
mv -- "$AUDIO_DIR/baseline.tmp.wav" "$AUDIO_DIR/baseline.wav"

render_tempo() {
    local tempo="$1"
    local output_name="$2"
    local temporary="$AUDIO_DIR/${output_name}.tmp.wav"
    ffmpeg -nostdin -hide_banner -loglevel warning -y \
        -i "$SOURCE" -map_metadata -1 -filter:a "atempo=${tempo}" \
        -ar 48000 -ac 1 -c:a pcm_s16le "$temporary"
    mv -- "$temporary" "$AUDIO_DIR/${output_name}.wav"
}

render_tempo "0.98" "tempo_98"
render_tempo "0.96" "tempo_96"
render_tempo "0.94" "tempo_94"

# Record hashes, measured durations, and source binding without changing audio.
.venv/bin/python - <<'PY'
import hashlib
import json
import wave
from pathlib import Path

root = Path("experiments/brand_voice_phase41f")
source = Path("experiments/brand_voice_phase41e/audio/v3_semantic_focus_final.wav")
tempos = {"baseline": 1.00, "tempo_98": 0.98, "tempo_96": 0.96, "tempo_94": 0.94}

def sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def duration(path):
    with wave.open(str(path), "rb") as wav:
        if (wav.getnchannels(), wav.getsampwidth(), wav.getframerate()) != (1, 2, 48000):
            raise RuntimeError(f"unexpected output format: {path}")
        return wav.getnframes() / wav.getframerate()

source_duration = duration(source)
manifest = {
    "phase": "41F",
    "source_path": str(source),
    "source_sha256": sha256(source),
    "source_duration_seconds": source_duration,
    "method": "FFmpeg atempo; pitch-preserving tempo adjustment; no TTS rerender",
    "candidates": {},
}
for name, tempo in tempos.items():
    path = root / "audio" / f"{name}.wav"
    manifest["candidates"][name] = {
        "tempo": tempo,
        "path": str(path),
        "sha256": sha256(path),
        "expected_duration_seconds": source_duration / tempo,
        "measured_duration_seconds": duration(path),
    }
if manifest["candidates"]["baseline"]["sha256"] != manifest["source_sha256"]:
    raise RuntimeError("baseline is not byte-identical to Phase 41E winner")
temporary = root / "manifest.json.tmp"
temporary.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
temporary.replace(root / "manifest.json")
PY

# Randomize once. If a valid mapping already exists, preserve it on reruns.
.venv/bin/python - <<'PY'
import hashlib
import json
import secrets
import shutil
from datetime import datetime, timezone
from pathlib import Path

root = Path("experiments/brand_voice_phase41f")
blind = root / "blind"
mapping_path = root / "blind_mapping.json"
sources = {
    "baseline": root / "audio" / "baseline.wav",
    "tempo_98": root / "audio" / "tempo_98.wav",
    "tempo_96": root / "audio" / "tempo_96.wav",
    "tempo_94": root / "audio" / "tempo_94.wav",
}
sha256 = lambda path: hashlib.sha256(path.read_bytes()).hexdigest()

if mapping_path.exists():
    mapping = json.loads(mapping_path.read_text(encoding="utf-8"))
    ordered = [mapping["files"][f"{index:02d}.wav"]["candidate"] for index in range(1, 5)]
    if set(ordered) != set(sources):
        raise RuntimeError("existing blind mapping is invalid; refusing to randomize again")
else:
    ordered = list(sources)
    secrets.SystemRandom().shuffle(ordered)
    mapping = {
        "phase": "41F",
        "created_utc": datetime.now(timezone.utc).isoformat(),
        "randomization": "one-time secrets.SystemRandom shuffle",
        "files": {},
    }

for index, candidate in enumerate(ordered, 1):
    name = f"{index:02d}.wav"
    source = sources[candidate]
    target = blind / name
    shutil.copyfile(source, target)
    mapping["files"][name] = {
        "candidate": candidate,
        "source_path": str(source),
        "source_sha256": sha256(source),
        "blind_sha256": sha256(target),
    }

temporary = root / "blind_mapping.json.tmp"
temporary.write_text(json.dumps(mapping, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
temporary.replace(mapping_path)
mapping_path.chmod(0o600)
PY

cp -- "$ROOT/HUMAN_REVIEW_TEMPLATE.md" "$BLIND_DIR/HUMAN_REVIEW.md"
echo "PHASE41F TEMPO TRANSFORMS COMPLETE"

