"""Runtime identity metadata used by health checks and Voice Lab records."""

from importlib import metadata
from typing import Any, Dict


def _package_version(package: str) -> str:
    try:
        return metadata.version(package)
    except metadata.PackageNotFoundError:
        return "unknown"
    except Exception:
        return "unknown"


def get_runtime_metadata(engine: Any) -> Dict[str, str]:
    """Return JSON-safe metadata from the actually loaded TTS implementation."""
    loader = getattr(engine, "_model", None)
    runtime = getattr(loader, "_v", None)
    runtime_type = type(runtime) if runtime is not None else None
    runtime_module = getattr(runtime_type, "__module__", "") if runtime_type else ""
    runtime_family = runtime_module.rsplit(".", 1)[-1] if runtime_module else "unknown"
    runtime_class = getattr(runtime_type, "__name__", "unknown") if runtime_type else "unknown"
    runtime_backend = (
        getattr(runtime, "backend", None)
        or getattr(loader, "backend", None)
        or getattr(engine, "backend", None)
        or "unknown"
    )
    device = getattr(engine, "device", None) or getattr(loader, "device", None)
    if not device and str(runtime_backend).lower() == "onnx":
        device = "cpu"

    return {
        "engine_library": "vieneu",
        "engine_version": _package_version("vieneu"),
        "runtime_family": str(runtime_family),
        "runtime_class": str(runtime_class),
        "runtime_backend": str(runtime_backend),
        "device": str(device or "unknown"),
    }
