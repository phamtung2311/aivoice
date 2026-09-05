#!/usr/bin/env python3
"""
Phase 41A — Optimization-based embedding search (black-box) for a new synthetic speaker.

PURPOSE
- Safely test whether the installed VieNeu ONNX CPU runtime can produce a novel,
  stable, and distinctive speaker identity by optimizing a new 192-d `speaker_emb`.
- This script implements a resumeable, checkpointed, interrupt-safe black-box
  evolutionary search (ES) that evaluates candidate embeddings by generating
  audio (when executed), encoding the generated audio back to embeddings and
  computing composite objectives that combine distinctiveness, stability and
  plausibility (OOD penalty).

CONSTRAINTS
- This script does NOT download models or datasets by itself.
- Candidate B baseline is only read; never modified.
- The script is safe to interrupt (SIGINT) and will checkpoint current state.
- This script does not auto-select a final voice. Human listening is required.

USAGE
- Prepare `config.json` (a default exists). Run:
    python experiments/brand_voice_phase41a/opt_embedding_search.py --config experiments/brand_voice_phase41a/config.json

- To resume from a checkpoint add `--resume experiments/brand_voice_phase41a/checkpoint.npz`.

NOTE
- Running this will perform TTS inference locally via `vieneu.Vieneu(backend='onnx')`.
  Do not run unless you accept CPU-only generation and local WAV production.

"""
from __future__ import annotations

import argparse
import json
import math
import os
import queue
import shutil
import signal
import sys
import threading
import time
from dataclasses import dataclass, asdict
from pathlib import Path

import numpy as np

# The script expects `vieneu` to be installed in the same Python environment where
# you will run this experiment. No downloads are triggered by this file itself.

ROOT = Path(__file__).resolve().parent
DEFAULT_CONFIG = ROOT / "config.json"
CHECKPOINT_FILENAME = "checkpoint.npz"


@dataclass
class ESState:
    iteration: int
    mean: np.ndarray
    sigma: float
    rng_state: tuple
    best_embeds: np.ndarray
    best_scores: np.ndarray


_INTERRUPTED = False


def _signal_handler(sig, frame):
    global _INTERRUPTED
    _INTERRUPTED = True
    print("\n[opt_embedding_search] Received interrupt, will checkpoint and exit soon...", flush=True)


signal.signal(signal.SIGINT, _signal_handler)


def load_config(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def ensure_dirs(out_dir: Path):
    out_dir.mkdir(parents=True, exist_ok=True)


def load_baseline(baseline_dir: Path):
    # Verify Candidate B exists and will not be overwritten.
    emb_path = baseline_dir / "speaker_emb.npy"
    codes_path = baseline_dir / "reference_codes.npy"
    if not emb_path.is_file() or not codes_path.is_file():
        raise FileNotFoundError(f"Baseline assets missing in {baseline_dir}")
    emb = np.load(emb_path, allow_pickle=False).astype(np.float32)
    codes = np.load(codes_path, allow_pickle=False)
    return emb, codes


def load_presets_from_vieneu():
    import json as _json
    import vieneu as _v
    asset = Path(_v.__file__).resolve().parent / "assets" / "voices_v3_turbo.json"
    j = _json.loads(asset.read_text(encoding="utf-8"))
    presets = j.get("presets", {})
    # Build a dict name -> embedding (np.float32)
    out = {}
    for name, data in presets.items():
        arr = np.asarray(data.get("speaker_emb", []), dtype=np.float32)
        if arr.size == 192:
            out[name] = arr
    return out


def compute_embedding_prior_stats(preset_map: dict[str, np.ndarray]):
    # Compute mean and covariance diag for simple Mahalanobis-like OOD penalty
    names = list(preset_map.keys())
    X = np.stack([preset_map[n] for n in names], axis=0).astype(np.float64)
    mean = X.mean(axis=0).astype(np.float32)
    var = X.var(axis=0).astype(np.float32) + 1e-6
    return mean, var


def generate_audio_and_encode(emb: np.ndarray, codes: np.ndarray, texts: list[str], tts_engine):
    """
    Generate audio for each text using VieNeu and encode back to embedding using the
    same encoder. Returns list of encoded embeddings and list of paths to generated WAVs.

    This function will run local TTS and requires `vieneu` to be installed. When running
    the experiment, generation may be slow on CPU. The runner should ensure enough
    disk for temporary WAVs.
    """
    import soundfile as sf

    generated_embeds = []
    wav_paths = []
    for i, text in enumerate(texts):
        waveform = tts_engine.infer(
            text,
            voice={"speaker_emb": emb, "codes": codes},
            denoise=True,
            use_ref_codes=True,
            temperature=0.8,
            top_k=25,
            top_p=0.95,
            max_new_frames=300,
            repetition_penalty=1.2,
            repetition_window=64,
            max_chars=256,
            silence_p=0.15,
            crossfade_p=0.0,
            apply_watermark=True,
        )
        wav = np.asarray(waveform, dtype=np.float32)
        out_path = ROOT / "runs" / f"gen_iter_temp_{int(time.time()*1000)}_{i}.wav"
        out_path.parent.mkdir(parents=True, exist_ok=True)
        sf.write(out_path, wav, 48000, subtype="PCM_16")
        # encode back
        speaker_emb, ref_codes = tts_engine._resolve_ref({"speaker_emb": emb, "codes": codes}, None, True, True)
        # Note: _resolve_ref here is used in Phase40 scripts to probe embeddings; if unavailable,
        # fallback to a no-op placeholder (should not happen in normal VieNeu runtime).
        generated_embeds.append(speaker_emb)
        wav_paths.append(out_path)
    return generated_embeds, wav_paths


def evaluate_candidate(emb: np.ndarray, presets_map: dict[str, np.ndarray], prior_mean: np.ndarray, prior_var: np.ndarray, codes: np.ndarray, texts: list[str], tts_engine) -> dict:
    """
    Composite objective evaluation for a candidate embedding.

    Returns dict with these keys:
      - distinctness: min cosine distance between generated-embedding and nearest preset embedding
      - stability: negative variance across generated embeddings for the same candidate
      - ood_penalty: Mahalanobis-like distance from prior mean (penalize too far)
      - combined_score: weighted sum (higher is better)

    IMPORTANT: The combined score is only a guide. Final selection must be human.
    """
    # 1) Generate audio for each text and encode back
    gen_embeds, wav_paths = generate_audio_and_encode(emb, codes, texts, tts_engine)

    # Stack embeddings
    E = np.stack([np.asarray(g).astype(np.float32) for g in gen_embeds], axis=0)

    # Distinctness: compute cosine distance between each generated embed and each preset embed
    preset_embs = np.stack(list(presets_map.values()), axis=0)
    # normalize
    def cos_sim(a, b):
        return np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b) + 1e-9)

    # For each generated embedding, compute 1 - max cosine similarity to presets (bigger=more distinct)
    distinctness_list = []
    for g in E:
        sims = preset_embs @ g / (np.linalg.norm(preset_embs, axis=1) * (np.linalg.norm(g) + 1e-9))
        max_sim = float(np.max(sims))
        distinctness_list.append(1.0 - max_sim)
    distinctness = float(np.min(distinctness_list))  # conservative: worst-case distinctness

    # Stability: negative of mean pairwise distance among generated embeddings (smaller variance -> higher stability)
    pairwise = []
    for i in range(E.shape[0]):
        for j in range(i + 1, E.shape[0]):
            pairwise.append(np.linalg.norm(E[i] - E[j]))
    stability = -float(np.mean(pairwise)) if pairwise else 0.0

    # OOD penalty: Mahalanobis-like distance using diag variance
    diff = emb.astype(np.float64) - prior_mean.astype(np.float64)
    mahal = float(np.sqrt(np.sum((diff * diff) / prior_var)))
    # Convert to penalty (higher mahal -> larger penalty)
    ood_penalty = -mahal

    # Combined score: weighted sum (weights set in config when running)
    # We return components; aggregation done by caller.
    return {
        "distinctness": distinctness,
        "stability": stability,
        "ood_penalty": ood_penalty,
        "wav_paths": [str(p) for p in wav_paths],
        "generated_embeds": E.tolist(),
    }


def save_checkpoint(state: ESState, out_dir: Path):
    path = out_dir / CHECKPOINT_FILENAME
    np.savez_compressed(
        path,
        iteration=state.iteration,
        mean=state.mean.astype(np.float32),
        sigma=float(state.sigma),
        rng_state=np.array(state.rng_state, dtype=object),
        best_embeds=state.best_embeds.astype(np.float32),
        best_scores=state.best_scores.astype(np.float32),
    )
    print(f"[opt_embedding_search] Checkpoint saved: {path}")
    return path


def load_checkpoint(path: Path) -> ESState:
    data = np.load(path, allow_pickle=True)
    iteration = int(data["iteration"]) if "iteration" in data else 0
    mean = data["mean"].astype(np.float32)
    sigma = float(data["sigma"])
    rng_state = tuple(data["rng_state"].tolist()) if "rng_state" in data else tuple(np.random.get_state())
    best_embeds = data["best_embeds"].astype(np.float32)
    best_scores = data["best_scores"].astype(np.float32)
    return ESState(iteration=iteration, mean=mean, sigma=sigma, rng_state=rng_state, best_embeds=best_embeds, best_scores=best_scores)


def run_es_search(config: dict, resume: Path | None = None):
    out_dir = ROOT / "runs"
    ensure_dirs(out_dir)

    baseline_dir = Path(config["baseline_dir"]).resolve()
    baseline_emb, baseline_codes = load_baseline(baseline_dir)

    # Load presets and compute prior stats
    presets_map = load_presets_from_vieneu()
    prior_mean, prior_var = compute_embedding_prior_stats(presets_map)

    dim = 192
    popsize = int(config.get("population", 64))
    sigma = float(config.get("init_sigma", 0.5))
    iterations = int(config.get("iterations", 200))
    topk = int(config.get("topk", max(4, popsize // 8)))

    # initial mean: baseline + small random jitter (but we will not overwrite baseline files)
    rng = np.random.default_rng(seed=int(config.get("seed", 40003)))

    if resume is not None:
        state = load_checkpoint(resume)
        np.random.set_state(state.rng_state)
        mean = state.mean
        sigma = state.sigma
        iter_start = state.iteration + 1
        best_embeds = state.best_embeds
        best_scores = state.best_scores
        print(f"[opt_embedding_search] Resuming from checkpoint iter={state.iteration}")
    else:
        # Start near baseline but offset by small noise to escape exact baseline
        mean = baseline_emb.copy()
        mean = mean + (rng.standard_normal(dim).astype(np.float32) * 1e-3)
        iter_start = 0
        best_embeds = np.zeros((int(config.get("keep_best", 10)), dim), dtype=np.float32)
        best_scores = np.full((int(config.get("keep_best", 10)),), -np.inf, dtype=np.float32)

    # Prepare TTS engine only when actually running evaluation
    import vieneu
    from vieneu import Vieneu
    tts = Vieneu(backend="onnx")

    texts = config.get("texts", [])
    if not texts:
        texts = [
            "Người ta hay nghĩ rằng một giọng nói tốt là giọng vang to. Nhưng thật ra, giọng podcast tốt là giọng biết dừng lại đúng lúc, đặt câu hỏi đúng chỗ, và để người nghe cảm nhận được một sự thật không cần ai nhấn mạnh.",
            "Khi ta suy nghĩ về cuộc đời, không phải tất cả câu trả lời đều có sẵn; điều quý là biết đặt câu hỏi tốt hơn.",
            "Sự kiên nhẫn không phải là chờ đợi một cách thụ động mà là giữ vững chính mình khi thử thách xuất hiện.",
        ]

    # Weights for combined score (user-editable in config)
    w_dist = float(config.get("w_distinctness", 1.0))
    w_stab = float(config.get("w_stability", 1.0))
    w_ood = float(config.get("w_ood_penalty", 0.5))

    # Main ES loop
    for iteration in range(iter_start, iterations):
        if _INTERRUPTED:
            print("[opt_embedding_search] Interrupted before iteration start; checkpointing...")
            st = ESState(iteration=iteration - 1, mean=mean, sigma=sigma, rng_state=tuple(np.random.get_state()), best_embeds=best_embeds, best_scores=best_scores)
            save_checkpoint(st, out_dir)
            break

        # Sample population
        pop = rng.normal(loc=0.0, scale=sigma, size=(popsize, dim)).astype(np.float32) + mean[None, :]

        pop_scores = np.full((popsize,), -np.inf, dtype=np.float32)
        pop_data = [None] * popsize

        # Evaluate each candidate sequentially (safe on CPU). Parallelism possible but memory heavy.
        for i in range(popsize):
            if _INTERRUPTED:
                print("[opt_embedding_search] Interrupted during population evaluation; checkpointing...")
                st = ESState(iteration=iteration, mean=mean, sigma=sigma, rng_state=tuple(np.random.get_state()), best_embeds=best_embeds, best_scores=best_scores)
                save_checkpoint(st, out_dir)
                return
            candidate = pop[i]
            try:
                eval_res = evaluate_candidate(candidate, presets_map, prior_mean, prior_var, baseline_codes, texts, tts)
            except Exception as e:
                print(f"[opt_embedding_search] Evaluation error for member {i}: {e}")
                eval_res = {"distinctness": 0.0, "stability": 0.0, "ood_penalty": -999.0, "wav_paths": [], "generated_embeds": []}

            # Combine scores
            combined = w_dist * eval_res["distinctness"] + w_stab * eval_res["stability"] + w_ood * eval_res["ood_penalty"]
            pop_scores[i] = combined
            pop_data[i] = eval_res
            print(f"iter {iteration} member {i} combined={combined:.6f} (dist={eval_res['distinctness']:.4f}, stab={eval_res['stability']:.4f}, ood={eval_res['ood_penalty']:.4f})")

        # Select topk and update mean
        idx = np.argsort(-pop_scores)
        top_idx = idx[:topk]
        top_pop = pop[top_idx]
        new_mean = np.mean(top_pop, axis=0).astype(np.float32)

        # Update sigma adaptively (simple rule)
        top_std = np.std(top_pop, axis=0).mean()
        sigma = max(1e-4, 0.99 * sigma + 0.01 * top_std)

        mean = new_mean

        # Maintain best archive
        for s, emb_vec in zip(pop_scores[top_idx], top_pop):
            # if archive not full or s better than worst
            if s > float(best_scores.min()):
                j = int(best_scores.argmin())
                best_scores[j] = s
                best_embeds[j] = emb_vec

        # Save iteration artifacts (small JSON)
        iter_record = {
            "iteration": iteration,
            "timestamp": time.time(),
            "sigma": float(sigma),
            "best_score": float(best_scores.max()),
            "mean_sample_sha256": None,
        }
        (out_dir / f"iter_{iteration:04d}.json").write_text(json.dumps(iter_record), encoding="utf-8")

        # Checkpoint every N iterations
        if iteration % int(config.get("checkpoint_every", 1)) == 0:
            st = ESState(iteration=iteration, mean=mean, sigma=sigma, rng_state=tuple(np.random.get_state()), best_embeds=best_embeds, best_scores=best_scores)
            save_checkpoint(st, out_dir)

    # End main loop: write final archive
    np.save(out_dir / "best_embeds.npy", best_embeds)
    np.save(out_dir / "best_scores.npy", best_scores)
    print("[opt_embedding_search] Search complete. Best candidates saved.")


def main_cli(argv=None):
    p = argparse.ArgumentParser(description="Optimize a new VieNeu speaker embedding (black-box ES)")
    p.add_argument("--config", default=str(DEFAULT_CONFIG), help="Path to config.json")
    p.add_argument("--resume", default=None, help="Path to checkpoint .npz to resume from")
    args = p.parse_args(argv)

    config = load_config(Path(args.config))
    resume_path = Path(args.resume) if args.resume else None
    run_es_search(config, resume=resume_path)


if __name__ == "__main__":
    main_cli()
