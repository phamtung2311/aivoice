#!/usr/bin/env python3
"""Read-only VieNeu speaker-space audit for Phase 33.

It reads packaged presets, local saved profiles, and preserved synthetic keepers.
It does not load a model, synthesize audio, mutate profiles, or reveal private
voice labels in the generated aggregate report.
"""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[2]
OUT = Path(__file__).resolve().parent / "speaker_space_metrics.json"
PRESETS = ROOT / ".venv/lib/python3.14/site-packages/vieneu/assets/voices_v3_turbo.json"
SAVED = ROOT / "data/voices/voices.json"
KEEPERS = ROOT / "experiments/special_voice_podcast/keepers"


def add(records: list[dict], group: str, key: str, emb) -> None:
    arr = np.asarray(emb, dtype=np.float32).reshape(-1)
    if arr.shape != (192,) or not np.isfinite(arr).all():
        return
    records.append({"group": group, "key": key, "embedding": arr})


def pairs(x: np.ndarray, records: list[dict]) -> list[dict]:
    norms = np.linalg.norm(x, axis=1)
    cosine = (x / norms[:, None]) @ (x / norms[:, None]).T
    euclidean = np.linalg.norm(x[:, None] - x[None, :], axis=2)
    result = []
    for i in range(len(records)):
        for j in range(i + 1, len(records)):
            result.append({
                "a": records[i], "b": records[j],
                "cosine": float(cosine[i, j]), "euclidean": float(euclidean[i, j]),
            })
    return result


def safe_pair(item: dict) -> dict:
    return {
        "groups": [item["a"]["group"], item["b"]["group"]],
        "cosine": round(item["cosine"], 6), "euclidean": round(item["euclidean"], 6),
    }


def main() -> int:
    records: list[dict] = []
    for key, value in json.loads(PRESETS.read_text(encoding="utf-8"))["presets"].items():
        add(records, "built_in", key, value.get("speaker_emb"))
    for key, value in json.loads(SAVED.read_text(encoding="utf-8")).get("voices", {}).items():
        add(records, "saved", key, value.get("speaker_emb"))
    for p in sorted(KEEPERS.glob("*/speaker_emb.npy")):
        add(records, "synthetic_keeper", p.parent.name, np.load(p, allow_pickle=False))

    x = np.stack([r["embedding"] for r in records])
    all_pairs = pairs(x, records)
    all_pairs.sort(key=lambda item: item["cosine"], reverse=True)
    # Drop effectively duplicate records when reporting distinct-space neighbours.
    non_duplicate = [p for p in all_pairs if p["cosine"] < 0.99999]
    farthest = sorted(all_pairs, key=lambda item: item["cosine"])[:5]
    u, s, _ = np.linalg.svd(x - x.mean(axis=0), full_matrices=False)
    pc_var = (s ** 2 / (len(x) - 1))
    pc_ratio = pc_var / pc_var.sum()
    groups = {g: sum(r["group"] == g for r in records) for g in sorted({r["group"] for r in records})}
    exact_special = [p for p in all_pairs if set((p["a"]["group"], p["b"]["group"])) == {"saved", "synthetic_keeper"} and p["cosine"] > 0.99999]
    unique_embeddings = []
    for record in records:
        if not any(np.allclose(record["embedding"], prior, rtol=0, atol=1e-6) for prior in unique_embeddings):
            unique_embeddings.append(record["embedding"])
    output = {
        "method": "read-only NumPy geometry; labels suppressed in aggregate output",
        "record_count": len(records), "numerically_unique_embedding_count": len(unique_embeddings), "records_by_group": groups,
        "embedding_shape": [len(records), 192],
        "nearest_non_duplicate_pairs": [safe_pair(p) for p in non_duplicate[:5]],
        "most_distant_pairs": [safe_pair(p) for p in farthest],
        "exact_or_near_exact_saved_keeper_pairs": len(exact_special),
        "pca_explained_variance_ratio": [round(float(v), 6) for v in pc_ratio[:5]],
        "geometry_interpretation": "The embedding space is numerically separated, but geometry alone does not validate interpolation, extrapolation, or perceptual speaker similarity.",
    }
    OUT.write_text(json.dumps(output, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(output, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
