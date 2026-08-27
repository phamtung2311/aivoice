#!/usr/bin/env python3
"""Runtime diagnostics for VieNeu-TTS-v2.

Generates a JSON report with device, model, benchmark, memory, concurrency,
chunking, and output-consistency checks. Does NOT modify production code.
"""
import os
import time
import json
import gc
import math
import resource
import subprocess
from pathlib import Path
from typing import Any, Dict, List, Tuple
from concurrent.futures import ThreadPoolExecutor, as_completed

import numpy as np

from backend.app.tts.model import ModelLoader
from backend.app.tts.engine import TTSEngine
from backend.app.tts.text import preprocess_text, split_into_sentences, chunk_sentences
from backend.app.tts.audio import join_audios, save_wav


OUT_DIR = Path("output/diagnostics")
OUT_DIR.mkdir(parents=True, exist_ok=True)


def mem_kb() -> Dict[str, int]:
    """Return memory metrics in KB where available."""
    info = {}
    try:
        ru = resource.getrusage(resource.RUSAGE_SELF)
        # on Linux ru_maxrss is in kilobytes
        info["ru_maxrss_kb"] = int(ru.ru_maxrss)
    except Exception:
        info["ru_maxrss_kb"] = None

    # try /proc/self/status for VmRSS and VmSize
    try:
        with open("/proc/self/status", "r") as f:
            for line in f:
                if line.startswith("VmRSS:"):
                    parts = line.split()
                    info["VmRSS_kB"] = int(parts[1])
                if line.startswith("VmSize:"):
                    parts = line.split()
                    info["VmSize_kB"] = int(parts[1])
    except Exception:
        info.setdefault("VmRSS_kB", None)
        info.setdefault("VmSize_kB", None)

    return info


def count_vieneu_instances() -> int:
    cnt = 0
    for obj in gc.get_objects():
        try:
            if obj is None:
                continue
            t = type(obj)
            if t.__name__ == "Vieneu":
                cnt += 1
        except Exception:
            continue
    return cnt


def probe_gpu() -> Dict[str, Any]:
    out = {"nvidia_smi": None, "gpu_info": None}
    try:
        p = subprocess.run(["nvidia-smi", "--query-gpu=name,memory.total,memory.used", "--format=csv,noheader,nounits"], capture_output=True, text=True, timeout=5)
        if p.returncode == 0:
            out["nvidia_smi"] = p.stdout.strip().splitlines()
    except Exception:
        out["nvidia_smi"] = None
    return out


def make_text_of_length(n: int) -> str:
    base = "Xin chào, đây là bài kiểm tra giọng nói. "
    if n <= len(base):
        return base[:n]
    # repeat and trim
    s = base * (n // len(base) + 2)
    return s[:n]


def infer_sample(model: ModelLoader, text: str, voice: str = None) -> Tuple[np.ndarray, float, Dict[str, int]]:
    t0 = time.time()
    audio = model.infer(text, voice=voice)
    t1 = time.time()
    # ensure numpy
    audio = np.asarray(audio)
    mem = mem_kb()
    return audio, (t1 - t0), mem


def run_length_benchmarks(model: ModelLoader, lengths: List[int], repeats: int = 3) -> Dict[str, Any]:
    results = {}
    for L in lengths:
        key = str(L)
        results[key] = []
        txt = make_text_of_length(L)
        for i in range(repeats):
            before = mem_kb()
            try:
                audio, dura, mid_mem = infer_sample(model, txt)
                after = mem_kb()
                sample_rate = getattr(model, "sample_rate", None)
                results[key].append({
                    "time_s": dura,
                    "samples": int(audio.size),
                    "duration_s": float(audio.size) / sample_rate if sample_rate else None,
                    "dtype": str(audio.dtype),
                    "min": float(np.nanmin(audio)) if audio.size else None,
                    "max": float(np.nanmax(audio)) if audio.size else None,
                    "mem_before": before,
                    "mem_mid": mid_mem,
                    "mem_after": after,
                })
            except Exception as e:
                results[key].append({"error": str(e)})
    return results


def memory_chunk_test(model: ModelLoader, chunks_counts: List[int], long_text_sizes: List[int]) -> Dict[str, Any]:
    out = {}
    # 1,5,10 chunks: create text with that many short sentences
    for c in chunks_counts:
        txt = ("Xin chào. " * c).strip()
        # split into sentences and chunks
        pre = preprocess_text(txt)
        sents = split_into_sentences(pre)
        chunks = chunk_sentences(sents)
        data = {"input_chars": len(txt), "sentences": len(sents), "chunks": len(chunks)}
        mem_before = mem_kb()
        audios = []
        mem_after_each = []
        try:
            for i, ch in enumerate(chunks):
                a, t, mem_mid = infer_sample(model, ch)
                audios.append(a)
                mem_after_each.append({"i": i, "mem_mid": mem_mid})
            mem_before_join = mem_kb()
            joined = join_audios(audios, getattr(model, "sample_rate", 24000))
            mem_after_join = mem_kb()
            out[f"chunks_{c}"] = {
                "meta": data,
                "mem_before": mem_before,
                "mem_after_each": mem_after_each,
                "mem_before_join": mem_before_join,
                "mem_after_join": mem_after_join,
                "peak_ru_maxrss_kb": resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
            }
        except Exception as e:
            out[f"chunks_{c}"] = {"error": str(e)}

    # long texts 5k and 10k
    for L in long_text_sizes:
        txt = make_text_of_length(L)
        pre = preprocess_text(txt)
        sents = split_into_sentences(pre)
        chunks = chunk_sentences(sents)
        mem_before = mem_kb()
        audios = []
        mem_after_each = []
        try:
            for i, ch in enumerate(chunks):
                a, t, mem_mid = infer_sample(model, ch)
                audios.append(a)
                mem_after_each.append({"i": i, "mem_mid": mem_mid})
            mem_before_join = mem_kb()
            joined = join_audios(audios, getattr(model, "sample_rate", 24000))
            mem_after_join = mem_kb()
            out[f"long_{L}"] = {
                "meta": {"input_chars": L, "sentences": len(sents), "chunks": len(chunks)},
                "mem_before": mem_before,
                "mem_after_each": mem_after_each,
                "mem_before_join": mem_before_join,
                "mem_after_join": mem_after_join,
                "peak_ru_maxrss_kb": resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
            }
        except Exception as e:
            out[f"long_{L}"] = {"error": str(e)}

    return out


def concurrency_test(model: ModelLoader, concurrency: int, runs: int = 4) -> Dict[str, Any]:
    results = {"concurrency": concurrency, "runs": runs, "details": []}
    texts = [make_text_of_length(200 + i * 10) for i in range(runs)]
    for run_idx in range(1):
        start = time.time()
        successes = 0
        failures = 0
        details = []
        mem_start = mem_kb()
        with ThreadPoolExecutor(max_workers=concurrency) as ex:
            futures = {ex.submit(infer_sample, model, txt): i for i, txt in enumerate(texts)}
            for fut in as_completed(futures):
                i = futures[fut]
                try:
                    audio, dura, mem_mid = fut.result()
                    details.append({"i": i, "time_s": dura, "samples": int(audio.size), "min": float(np.nanmin(audio)) if audio.size else None, "max": float(np.nanmax(audio)) if audio.size else None, "mem_mid": mem_mid})
                    successes += 1
                except Exception as e:
                    failures += 1
                    details.append({"i": i, "error": str(e)})
        mem_end = mem_kb()
        end = time.time()
        results["details"].append({"start_time": start, "end_time": end, "duration_s": end - start, "successes": successes, "failures": failures, "mem_start": mem_start, "mem_end": mem_end, "per_request": details, "peak_ru_maxrss_kb": resource.getrusage(resource.RUSAGE_SELF).ru_maxrss})
    return results


def output_consistency_test(model: ModelLoader, repeats: int = 5) -> Dict[str, Any]:
    txt = "Xin chào, đây là bài kiểm tra giọng nói."
    sr = getattr(model, "sample_rate", 24000)
    out = {"input": txt, "sample_rate": sr, "runs": []}
    for i in range(repeats):
        try:
            audio, dura, mem = infer_sample(model, txt)
            # try saving to ensure WAV opens
            p = OUT_DIR / f"consistency_{i}.wav"
            try:
                save_wav(str(p), audio, sr)
                saved = True
            except Exception:
                saved = False
            out["runs"].append({"i": i, "time_s": dura, "samples": int(audio.size), "min": float(np.nanmin(audio)) if audio.size else None, "max": float(np.nanmax(audio)) if audio.size else None, "dtype": str(audio.dtype), "saved_wav": saved})
        except Exception as e:
            out["runs"].append({"i": i, "error": str(e)})
    return out


def chunking_inspect(texts: List[str], max_chars: int = 400) -> Dict[str, Any]:
    out = {}
    for i, t in enumerate(texts):
        pre = preprocess_text(t)
        sents = split_into_sentences(pre)
        chunks = chunk_sentences(sents, max_chars=max_chars)
        out[f"input_{i}"] = {"input_len": len(t), "sentences": len(sents), "chunks": len(chunks), "chunk_lengths": [len(c) for c in chunks], "chunks": chunks}
    return out


def pipeline_timing(model: ModelLoader, text: str) -> Dict[str, Any]:
    timings = {}
    t0 = time.time()
    pre_t0 = time.time()
    pre = preprocess_text(text)
    pre_t1 = time.time()
    timings["preprocess_s"] = pre_t1 - pre_t0

    split_t0 = time.time()
    sents = split_into_sentences(pre)
    split_t1 = time.time()
    timings["split_s"] = split_t1 - split_t0

    chunk_t0 = time.time()
    chunks = chunk_sentences(sents)
    chunk_t1 = time.time()
    timings["chunk_s"] = chunk_t1 - chunk_t0

    infer_times = []
    audios = []
    mems = []
    for ch in chunks:
        a, dura, mem = infer_sample(model, ch)
        infer_times.append(dura)
        audios.append(a)
        mems.append(mem)

    join_t0 = time.time()
    joined = join_audios(audios, getattr(model, "sample_rate", 24000))
    join_t1 = time.time()
    timings["infer_times"] = infer_times
    timings["join_s"] = join_t1 - join_t0
    timings["total_s"] = time.time() - t0
    timings["mems"] = mems
    timings["samples_joined"] = int(joined.size)
    return timings


def main():
    report: Dict[str, Any] = {"meta": {"cwd": os.getcwd(), "time": time.time()}}

    # model/device probe
    try:
        engine = TTSEngine(cache_model=False)
        # do not auto-load yet
    except Exception:
        engine = None

    model = None
    try:
        model = ModelLoader()
        report["model_name"] = model.model_name
        report["model_backend"] = model.backend
        report["model_device_requested"] = model.device
        report["sample_rate"] = getattr(model, "sample_rate", None)
    except Exception as e:
        report["model_error"] = str(e)

    report["vieneu_instances"] = count_vieneu_instances()
    report["gpu_probe"] = probe_gpu()
    report["mem_initial"] = mem_kb()

    if model is None:
        outp = OUT_DIR / "report_error.json"
        outp.write_text(json.dumps(report, indent=2))
        print("Model failed to initialize. See", outp)
        return

    # quick single inference to capture dtype/shape/minmax and sample_rate
    try:
        a, t, mem = infer_sample(model, "Xin chào, đây là bài kiểm tra.")
        report["probe_audio"] = {"time_s": t, "dtype": str(a.dtype), "shape": list(a.shape), "min": float(np.nanmin(a)) if a.size else None, "max": float(np.nanmax(a)) if a.size else None, "mem_mid": mem}
    except Exception as e:
        report["probe_error"] = str(e)

    # benchmarks lengths
    lengths = [50, 100, 200, 400, 600, 1000]
    report["length_benchmarks"] = run_length_benchmarks(model, lengths, repeats=3)

    # memory chunk tests
    report["memory_tests"] = memory_chunk_test(model, [1, 5, 10], [5000, 10000])

    # concurrency tests
    conc_results = {}
    for c in [2, 4, 8]:
        try:
            conc_results[str(c)] = concurrency_test(model, concurrency=c, runs=4)
        except Exception as e:
            conc_results[str(c)] = {"error": str(e)}
    report["concurrency"] = conc_results

    # output consistency
    report["consistency"] = output_consistency_test(model, repeats=5)

    # chunking checks
    texts = ["Xin chào. Đây là câu ngắn.", "Câu một. Câu hai! Câu ba?", "".join(["Từ " + str(i) + " " for i in range(200)]) , "A\nB\nC", "Một câu dài " + ("x" * 500)]
    report["chunking"] = chunking_inspect(texts, max_chars=400)

    # pipeline timing
    report["pipeline_timing"] = pipeline_timing(model, make_text_of_length(1000))

    outp = OUT_DIR / f"diagnostics_report_{int(time.time())}.json"
    outp.write_text(json.dumps(report, indent=2, ensure_ascii=False))
    print("Diagnostics complete. Report:", outp)


if __name__ == "__main__":
    main()
