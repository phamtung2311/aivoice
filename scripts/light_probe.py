#!/usr/bin/env python3
"""Lightweight environment probe for local TTS.

Writes JSON to output/diagnostics/light_probe_report.json and prints it.
Does NOT load or instantiate the TTS model.
"""
import os
import json
import platform
import subprocess
from pathlib import Path
import re

OUT = Path("output/diagnostics")
OUT.mkdir(parents=True, exist_ok=True)
OUT_FILE = OUT / "light_probe_report.json"


def read_model_defaults():
    fn = Path("backend/app/tts/model.py")
    info = {"model_name": None, "backend": None}
    try:
        text = fn.read_text()
        # find default model_name string
        m = re.search(r"self\.model_name\s*=\s*model_name\s+or\s+[\"']([^\"']+)[\"']", text)
        if m:
            info["model_name"] = m.group(1)
        m2 = re.search(r"self\.backend\s*=\s*backend\s+or\s+[\"']([^\"']+)[\"']", text)
        if m2:
            info["backend"] = m2.group(1)
    except Exception:
        pass
    return info


def check_models_folder(model_name):
    res = {"model_cached": False, "model_source": None}
    # check conventional local models dir
    # look for folder name that contains model_name components
    try:
        base = Path("models")
        if base.exists():
            for p in base.iterdir():
                # handle names like models--pnnbao-ump--VieNeu-TTS-v2
                if model_name and model_name.replace("/", "--") in p.name:
                    res["model_cached"] = True
                    res["model_source"] = str(p)
                    return res
    except Exception:
        pass
    return res


def onnx_info():
    info = {"installed": False, "providers": None, "device": None, "version": None}
    try:
        import onnxruntime as ort
        info["installed"] = True
        try:
            info["version"] = ort.__version__
        except Exception:
            info["version"] = None
        try:
            # get available providers
            info["providers"] = list(ort.get_available_providers())
        except Exception:
            info["providers"] = None
        try:
            info["device"] = ort.get_device()
        except Exception:
            info["device"] = None
    except Exception:
        pass
    return info


def nvidia_info():
    info = {"nvidia_smi": False, "gpus": []}
    try:
        p = subprocess.run(["nvidia-smi", "--query-gpu=name,memory.total", "--format=csv,noheader,nounits"], capture_output=True, text=True, timeout=3)
        if p.returncode == 0 and p.stdout:
            info["nvidia_smi"] = True
            for line in p.stdout.strip().splitlines():
                name, mem = [s.strip() for s in line.split(",", 1)]
                info["gpus"].append({"name": name, "memory_total": mem})
    except Exception:
        pass
    return info


def torch_info():
    info = {"installed": False, "cuda_available": None, "version": None}
    try:
        import torch
        info["installed"] = True
        try:
            info["version"] = torch.__version__
            info["cuda_available"] = bool(torch.cuda.is_available())
        except Exception:
            pass
    except Exception:
        pass
    return info


def env_vars_check():
    keys = ["CUDA_VISIBLE_DEVICES", "HF_HOME", "TRANSFORMERS_OFFLINE", "HF_DATASETS_OFFLINE", "VINEU_DEVICE", "VINEU_BACKEND"]
    out = {}
    for k in keys:
        out[k] = os.environ.get(k)
    return out


def system_info():
    info = {}
    try:
        info["platform"] = platform.platform()
        info["machine"] = platform.machine()
        info["processor"] = platform.processor()
        info["python_version"] = platform.python_version()
    except Exception:
        pass
    # memory from /proc/meminfo
    try:
        with open("/proc/meminfo") as f:
            for line in f:
                if line.startswith("MemTotal:"):
                    parts = line.split()
                    info["ram_kb"] = int(parts[1])
                    break
    except Exception:
        info["ram_kb"] = None
    return info


def read_backend_config():
    # inspect backend/main.py for any explicit device settings
    info = {"engine_device_field": None}
    try:
        text = Path("backend/main.py").read_text()
        m = re.search(r"device\s*=\s*([\"']?\w+[\"']?)", text)
        if m:
            info["engine_device_field"] = m.group(1)
    except Exception:
        pass
    return info


def main():
    info = {}
    defaults = read_model_defaults()
    info.update(defaults)
    models_check = check_models_folder(info.get("model_name"))
    info.update(models_check)
    info["framework_probe"] = onnx_info()
    info["nvidia"] = nvidia_info()
    info["torch"] = torch_info()
    info["env_vars"] = env_vars_check()
    info["system"] = system_info()
    info["backend_config"] = read_backend_config()

    # device inference: conservative
    device = "unknown"
    gpu_available = False
    gpu_name = None
    if info["framework_probe"].get("installed"):
        dev = info["framework_probe"].get("device")
        if dev:
            device = dev
    if info["nvidia"].get("nvidia_smi") and info["nvidia"].get("gpus"):
        gpu_available = True
        gpu_name = info["nvidia"]["gpus"][0]["name"]

    info_out = {
        "model_name": info.get("model_name") or "unknown",
        "model_source": info.get("model_source") or ("local" if info.get("model_cached") else "unknown"),
        "framework": "onnxruntime" if info.get("framework_probe", {}).get("installed") else "unknown",
        "device": device,
        "gpu_available": gpu_available,
        "gpu_name": gpu_name or None,
        "cpu": info.get("system", {}).get("processor") or info.get("system", {}).get("machine") or "unknown",
        "ram_kb": info.get("system", {}).get("ram_kb"),
        "model_cached": bool(info.get("model_cached")),
        "cpu_heavy_reason": "unknown",
        "recommendation": "If GPU is available and onnxruntime has CUDA provider, configure ModelLoader to use device='cuda' when instantiating; otherwise run with concurrency=1 to avoid CPU spikes.",
        "details": info,
    }

    OUT_FILE.write_text(json.dumps(info_out, indent=2, ensure_ascii=False))
    print(json.dumps(info_out, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
