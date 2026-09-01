"""Serial generation, manifest, reference, and OOM safeguards."""
from __future__ import annotations

import time
from pathlib import Path
from typing import Any

from common import OUTPUTS, REFERENCES, ROOT, clear_cuda_cache, cuda_snapshot, load_run_manifest, log, output_is_valid, save_run_manifest, sha256
from engine_adapter import generate


def speaker_path(name: str) -> Path:
    return REFERENCES / "speakers" / f"{name}.wav"


def emotion_path(name: str) -> Path:
    return REFERENCES / "emotions" / f"emotion_{name}.wav"


def require_paths(paths: list[Path]) -> None:
    missing = [str(path.relative_to(ROOT)) for path in paths if not path.is_file()]
    if missing:
        raise FileNotFoundError("Missing reference audio. Upload only permissioned files:\n- " + "\n- ".join(missing))


def run_sample(engine: Any, *, sample_id: str, speaker: str, emotion: str, mode: str, text: str, generation: dict, vector: list[float] | None = None) -> dict[str, Any]:
    manifest = load_run_manifest()
    existing = manifest["samples"].get(sample_id)
    if existing and output_is_valid(existing):
        log(f"SKIP {sample_id}: existing output hash is valid")
        return existing

    spk = speaker_path(speaker)
    donor = None if emotion == "neutral" or mode == "vector" else emotion_path(emotion)
    required = [spk] + ([donor] if donor is not None else [])
    require_paths(required)
    suffix = "vector" if mode == "vector" else emotion
    output = OUTPUTS / f"{speaker}_{suffix}.wav"
    record: dict[str, Any] = {
        "sample_id": sample_id,
        "output_path": str(output.relative_to(ROOT)),
        "speaker": speaker,
        "speaker_reference": str(spk.relative_to(ROOT)),
        "emotion": emotion,
        "emotion_mode": mode,
        "emotion_donor": str(donor.relative_to(ROOT)) if donor else None,
        "emo_alpha": generation["emo_alpha"],
        "vector": vector,
        "input_text": text,
        "generation": generation,
        "vram_before": cuda_snapshot(),
        "started_at": time.time(),
        "status": "running",
    }
    manifest["samples"][sample_id] = record
    save_run_manifest(manifest)

    try:
        generate(engine, speaker=spk, text=text, output=output, generation=generation, emotion_audio=donor, emotion_vector=vector)
        if not output.is_file() or output.stat().st_size == 0:
            raise RuntimeError("Engine returned without a non-empty WAV output.")
        record.update({"status": "success", "sha256": sha256(output), "output_bytes": output.stat().st_size})
    except RuntimeError as exc:
        record.update({"status": "failed", "error": repr(exc)})
        if "out of memory" in str(exc).lower():
            clear_cuda_cache()
            record["oom"] = True
        manifest["samples"][sample_id] = record
        save_run_manifest(manifest)
        log(f"STOP {sample_id}: {exc!r}")
        raise
    finally:
        record["ended_at"] = time.time()
        record["duration_seconds"] = record["ended_at"] - record["started_at"]
        record["vram_after"] = cuda_snapshot()
        manifest["samples"][sample_id] = record
        save_run_manifest(manifest)
    log(f"DONE {sample_id}. LISTEN before continuing.")
    return record
