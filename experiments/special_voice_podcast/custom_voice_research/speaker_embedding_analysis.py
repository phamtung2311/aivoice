#!/usr/bin/env python3
"""Read-only geometry analysis of live packaged VieNeu speaker anchors."""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parent
PROJECT_ROOT = ROOT.parents[2]
sys.path.insert(0, str(PROJECT_ROOT))


def main() -> int:
    from backend.app.tts.engine import TTSEngine

    engine = TTSEngine(backend="onnx")
    profiles, names = engine._model._v._preset_voices, engine.get_preset_names()
    x = np.stack([np.asarray(profiles[name]["speaker_emb"], dtype=np.float32) for name in names])
    norms = np.linalg.norm(x, axis=1)
    cosine = (x / norms[:, None]) @ (x / norms[:, None]).T
    distance = np.linalg.norm(x[:, None] - x[None, :], axis=2)
    mask = ~np.eye(len(x), dtype=bool)
    codes = [np.asarray(profiles[name]["codes"]) for name in names]
    result = {"method": "read-only NumPy analysis; no inference or profile mutation", "preset_count": len(names), "speaker_embedding": {"shape": list(x.shape), "dtype": str(x.dtype), "value_min": float(x.min()), "value_max": float(x.max()), "mean": float(x.mean()), "std": float(x.std()), "norm_min": float(norms.min()), "norm_max": float(norms.max()), "norm_mean": float(norms.mean()), "pairwise_cosine_min": float(cosine[mask].min()), "pairwise_cosine_max": float(cosine[mask].max()), "pairwise_cosine_mean": float(cosine[mask].mean()), "pairwise_euclidean_min": float(distance[mask].min()), "pairwise_euclidean_max": float(distance[mask].max()), "pairwise_euclidean_mean": float(distance[mask].mean())}, "reference_codes": {"dtype": str(codes[0].dtype), "n_vq": int(codes[0].shape[1]), "frame_count_min": min(int(c.shape[0]) for c in codes), "frame_count_max": max(int(c.shape[0]) for c in codes), "token_min": min(int(c.min()) for c in codes), "token_max": max(int(c.max()) for c in codes)}, "interpretation_limit": "Numerical separation does not validate interpolation, mixing, or synthetic speaker creation."}
    (ROOT / "speaker_embedding_analysis.json").write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
