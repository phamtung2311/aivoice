"""Shared, isolated utilities for the Phase 28 Kaggle PoC.

Nothing here imports AIVoice production code or downloads models at import time.
"""
from __future__ import annotations

import hashlib
import json
import os
import shutil
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
CONFIG_PATH = ROOT / "poc_config.json"
ASSETS_PATH = ROOT / "assets_manifest.json"
MANIFEST_PATH = ROOT / "manifest.json"
OUTPUTS = ROOT / "outputs"
LOG_PATH = ROOT / "generation_log.txt"
MODEL_DIR = ROOT / "model"
HF_HOME = ROOT / "hf-home"
HF_CACHE = HF_HOME / "hub"
REFERENCES = ROOT / "references"


def now() -> str:
    return datetime.now(timezone.utc).isoformat()


def load_json(path: Path) -> dict[str, Any]:
    with path.open(encoding="utf-8") as handle:
        return json.load(handle)


def atomic_json(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    temporary.replace(path)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def free_disk_gb(path: Path = ROOT) -> float:
    return shutil.disk_usage(path).free / (1024 ** 3)


def configure_hf_environment() -> None:
    HF_HOME.mkdir(parents=True, exist_ok=True)
    os.environ["HF_HOME"] = str(HF_HOME)
    os.environ["HF_HUB_CACHE"] = str(HF_CACHE)
    os.environ["INDEXTTS_DISABLE_AUTO_DOWNLOAD"] = "1"


def load_run_manifest() -> dict[str, Any]:
    if MANIFEST_PATH.exists():
        return load_json(MANIFEST_PATH)
    return {
        "schema_version": 1,
        "created_at": now(),
        "updated_at": now(),
        "samples": {},
        "environment": {},
        "checkpoint_revisions": {},
    }


def save_run_manifest(manifest: dict[str, Any]) -> None:
    manifest["updated_at"] = now()
    atomic_json(MANIFEST_PATH, manifest)


def log(message: str) -> None:
    line = f"{now()} {message}"
    print(line)
    with LOG_PATH.open("a", encoding="utf-8") as handle:
        handle.write(line + "\n")


def output_is_valid(record: dict[str, Any]) -> bool:
    if record.get("status") != "success" or not record.get("output_path") or not record.get("sha256"):
        return False
    path = ROOT / record["output_path"]
    return path.is_file() and sha256(path) == record["sha256"]


def cuda_snapshot() -> dict[str, Any]:
    try:
        import torch
    except ImportError:
        return {"available": False, "reason": "PyTorch not installed"}
    if not torch.cuda.is_available():
        return {"available": False, "reason": "CUDA unavailable"}
    device = torch.cuda.current_device()
    properties = torch.cuda.get_device_properties(device)
    total = properties.total_memory
    allocated = torch.cuda.memory_allocated(device)
    reserved = torch.cuda.memory_reserved(device)
    return {
        "available": True,
        "device": torch.cuda.get_device_name(device),
        "total_vram_bytes": total,
        "allocated_bytes": allocated,
        "reserved_bytes": reserved,
        "free_estimate_bytes": max(total - reserved, 0),
        "max_allocated_bytes": torch.cuda.max_memory_allocated(device),
    }


def clear_cuda_cache() -> None:
    try:
        import torch
        if torch.cuda.is_available():
            torch.cuda.empty_cache()
    except ImportError:
        pass


def set_best_effort_seed(seed: int | None) -> None:
    if seed is None:
        return
    import random
    random.seed(seed)
    try:
        import numpy as np
        np.random.seed(seed)
    except ImportError:
        pass
    try:
        import torch
        torch.manual_seed(seed)
        if torch.cuda.is_available():
            torch.cuda.manual_seed_all(seed)
    except ImportError:
        pass


def environment_text() -> str:
    lines = [f"generated_at={now()}", f"python={sys.version}", f"root={ROOT}"]
    try:
        import torch
        lines.extend([f"torch={torch.__version__}", f"cuda_available={torch.cuda.is_available()}"])
        if torch.cuda.is_available():
            lines.extend([f"cuda_runtime={torch.version.cuda}", f"gpu={torch.cuda.get_device_name(0)}"])
    except ImportError:
        lines.append("torch=not-installed")
    lines.append(subprocess.getoutput("nvidia-smi --query-gpu=name,memory.total --format=csv,noheader 2>/dev/null"))
    return "\n".join(lines).strip() + "\n"
