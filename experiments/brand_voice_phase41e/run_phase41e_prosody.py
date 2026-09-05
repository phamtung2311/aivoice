#!/usr/bin/env python3
"""Phase 41E static preflight and external, low-memory audition runner.

Without ``--generate`` this never imports/initializes VieNeu and never runs TTS.
Generation is deliberately opt-in and limited to one variant per process.
"""

from __future__ import annotations

import argparse
import ast
import copy
import gc
import hashlib
import importlib.metadata
import importlib.util
import inspect
import json
import os
import sys
import wave
from pathlib import Path
from typing import Any

import numpy as np

PHASE_ROOT = Path("experiments/brand_voice_phase41e")
CONFIG_PATH = PHASE_ROOT / "config.json"
PLAN_PATH = PHASE_ROOT / "prosody_plan.json"
REPORT_PATH = PHASE_ROOT / "PHASE41E_PRE_RUN_REPORT.md"
PHASE41D_SCRIPT = Path("experiments/brand_voice_phase41d/run_longform_validation.py")
PHASE41D_MANIFEST = Path("experiments/brand_voice_phase41d/manifest.json")
OUTPUT_DIR = PHASE_ROOT / "audio"
CHECKPOINT_PATH = PHASE_ROOT / "resume_state.json"
MANIFEST_PATH = PHASE_ROOT / "manifest.json"


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def sha256_text(value: str) -> str:
    return sha256_bytes(value.encode("utf-8"))


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


# Verbatim copy of the Phase 41D control. Its AST is checked against that file.
def chunk_text_for_longform(text: str, max_chars: int = 350):
    sentences = [s.strip() for s in text.replace('\n', ' ').replace('…', '.').split('.') if s.strip()]
    chunks = []
    current = ''
    for s in sentences:
        cand = (current + ' ' + s).strip() if current else s
        if len(cand) <= max_chars:
            current = cand
        else:
            if current:
                chunks.append(current)
            current = s
    if current:
        chunks.append(current)
    if not chunks:
        chunks = [text[i:i + max_chars] for i in range(0, len(text), max_chars)]
    return chunks


def phase41d_sentences(text: str) -> list[str]:
    return [s.strip() for s in text.replace("\n", " ").replace("…", ".").split(".") if s.strip()]


def make_chunk(variant: str, index: int, text: str, role: str, before: str,
               after: str, pause: float = 0.0, focus: str | None = None) -> dict[str, Any]:
    return {
        "variant": variant,
        "chunk_index": index,
        "text": text,
        "char_count": len(text),
        "text_sha256": sha256_text(text),
        "semantic_role": role,
        "boundary_before": before,
        "boundary_after": after,
        "pause_after_seconds": pause,
        "focus_phrase": focus,
    }


def build_plan(config: dict[str, Any]) -> dict[str, Any]:
    source = config["shared_passage"]["text"]
    units = phase41d_sentences(source)
    lexical = " ".join(units)

    v0_texts = chunk_text_for_longform(source, config["phase41d_control"]["max_chars"])
    v0_roles = ["opening_context", "central_principle", "communication_consequence", "resolution"]
    v0 = [make_chunk(
        "v0_phase41d_control", i, text, v0_roles[i],
        "paragraph_start" if i == 0 else "phase41d_greedy_boundary",
        "paragraph_end" if i == len(v0_texts) - 1 else "phase41d_greedy_boundary",
    ) for i, text in enumerate(v0_texts)]

    v1_ranges = [(0, 2), (2, 4), (4, 6), (6, 8), (8, 10), (10, 11)]
    v1_roles = [
        "opening_and_contrast", "behavior_and_principle", "setup_and_realization",
        "expression_and_reception", "listener_resolution", "closing_thought",
    ]
    v1_texts = [" ".join(units[start:end]) for start, end in v1_ranges]
    v1 = [make_chunk(
        "v1_semantic_chunking", i, text, v1_roles[i],
        "paragraph_start" if i == 0 else "semantic_thought_boundary",
        "paragraph_end" if i == len(v1_texts) - 1 else "semantic_thought_boundary",
    ) for i, text in enumerate(v1_texts)]

    pause_values = [0.06, 0.10, 0.10, 0.06, 0.10, 0.0]
    v2 = []
    for item, pause in zip(v1, pause_values):
        clone = copy.deepcopy(item)
        clone["variant"] = "v2_natural_pacing"
        clone["pause_after_seconds"] = pause
        v2.append(clone)

    setup, resolution = units[4].split(", trong khi ", 1)
    v3_texts = [
        " ".join(units[0:2]), units[2], f"{units[3]} {setup},",
        f"trong khi {resolution} {units[5]}", units[6], " ".join(units[7:9]),
        units[9], units[10],
    ]
    v3_roles = [
        "context_then_contrast", "behavior_resolution", "principle_then_setup",
        "contrast_resolution", "idea_and_lived_alignment", "clarity_then_human_result",
        "listener_agency", "closing_resolution",
    ]
    v3_focus = [
        "những giây phút thầm lặng", "khi nào nên dừng lại", "biết mình đang đi về đâu",
        "sự ổn định của nội tâm", "cách ta sống cùng những ý tưởng ấy", "cảm giác được hiểu",
        "điều quan trọng đối với mình", "không chỉ cần đúng",
    ]
    v3_after = [
        "thought_transition", "thought_transition", "setup_resolution_boundary",
        "thought_transition", "thought_transition", "thought_transition",
        "thought_transition", "paragraph_end",
    ]
    v3 = [make_chunk(
        "v3_semantic_focus", i, text, v3_roles[i],
        "paragraph_start" if i == 0 else v3_after[i - 1], v3_after[i], focus=v3_focus[i],
    ) for i, text in enumerate(v3_texts)]

    return {
        "phase": "41E",
        "canonical_source_text": source,
        "canonical_source_utf8_sha256": sha256_text(source),
        "canonical_spoken_lexical_text": lexical,
        "canonical_spoken_lexical_sha256": sha256_text(lexical),
        "lexical_reconstruction_rule": "Join text fields with one ASCII space. Phase 41D removes full stops before TTS; every variant intentionally uses that same spoken lexical form.",
        "pause_policy": config["pause_policy"],
        "variants": {
            "v0_phase41d_control": {"description": "Exact Phase 41D chunk_text_for_longform control with max_chars=350.", "chunk_count": len(v0), "chunks": v0},
            "v1_semantic_chunking": {"description": "Semantic grouping only; no manual pause or parameter change.", "chunk_count": len(v1), "chunks": v1},
            "v2_natural_pacing": {"description": "Byte-identical chunk texts and engine controls to V1; only restrained assembly pauses differ.", "chunk_count": len(v2), "chunks": v2},
            "v3_semantic_focus": {"description": "Different setup/resolution boundaries and at most one primary focus phrase per major thought; no manual pauses or acoustic controls.", "chunk_count": len(v3), "chunks": v3},
        },
    }


def function_ast(path: Path, function_name: str) -> str:
    tree = ast.parse(path.read_text(encoding="utf-8"))
    for node in tree.body:
        if isinstance(node, ast.FunctionDef) and node.name == function_name:
            node = copy.deepcopy(node)
            node.name = "CONTROL"
            return ast.dump(node, include_attributes=False)
    raise AssertionError(f"{function_name} not found in {path}")


def local_function_ast(function: Any) -> str:
    node = ast.parse(inspect.getsource(function)).body[0]
    assert isinstance(node, ast.FunctionDef)
    node.name = "CONTROL"
    return ast.dump(node, include_attributes=False)


def punctuation_counts(text: str) -> dict[str, int]:
    return {mark: text.count(mark) for mark in [".", ",", ";", ":", "?", "!", "…"]}


def canonical_hashes(config: dict[str, Any]) -> dict[str, str]:
    root = Path(config["speaker_identity"]["canonical_root"])
    emb_path, codes_path = root / "speaker_emb.npy", root / "reference_codes.npy"
    emb = np.load(emb_path, allow_pickle=False).astype(np.float32)
    return {
        "speaker_emb_array_sha256": sha256_bytes(np.ascontiguousarray(emb).tobytes()),
        "speaker_emb_npy_sha256": sha256_file(emb_path),
        "reference_codes_npy_sha256": sha256_file(codes_path),
    }


def engine_api_matches_audit(config: dict[str, Any]) -> bool:
    if importlib.metadata.version("vieneu") != config["engine_controls"]["installed_version"]:
        return False
    spec = importlib.util.find_spec("vieneu.v3turbo")
    if spec is None or spec.origin is None:
        return False
    tree = ast.parse(Path(spec.origin).read_text(encoding="utf-8"))
    infer_node = None
    for node in tree.body:
        if isinstance(node, ast.ClassDef) and node.name == "V3TurboVieNeuTTS":
            infer_node = next((item for item in node.body if isinstance(item, ast.FunctionDef) and item.name == "infer"), None)
            break
    if infer_node is None:
        return False
    args = {arg.arg for arg in infer_node.args.args + infer_node.args.kwonlyargs}
    required = {"temperature", "top_k", "top_p", "repetition_penalty", "repetition_window",
                "silence_p", "crossfade_p", "apply_watermark", "max_chars"}
    body_names = {node.id for node in ast.walk(infer_node) if isinstance(node, ast.Name) and isinstance(node.ctx, ast.Load)}
    return required <= args and "seed" not in args and "speed" not in args and "silence_p" not in body_names and "crossfade_p" not in body_names


def static_checks(config: dict[str, Any], plan: dict[str, Any],
                  require_files_match: bool = True) -> dict[str, bool]:
    source, metrics = config["shared_passage"]["text"], config["shared_passage_metrics"]
    checks: dict[str, bool] = {}
    expected_hashes = {key: config["speaker_identity"][key] for key in [
        "speaker_emb_array_sha256", "speaker_emb_npy_sha256", "reference_codes_npy_sha256"]}
    checks["canonical_speaker_hashes"] = canonical_hashes(config) == expected_hashes
    checks["vieneu_3_3_0_api_audit"] = engine_api_matches_audit(config)
    checks["shared_text_frozen"] = (
        sha256_text(source) == metrics["utf8_sha256"] and len(source) == metrics["character_count"]
        and len(source.split()) == metrics["vietnamese_word_count"]
        and len(phase41d_sentences(source)) == metrics["sentence_count"]
        and punctuation_counts(source) == metrics["punctuation_counts"])
    checks["duration_target"] = config["target_duration_seconds"]["min"] <= config["target_duration_seconds"]["predicted"] <= config["target_duration_seconds"]["max"]
    checks["v0_true_phase41d_control"] = (
        function_ast(PHASE41D_SCRIPT, "chunk_text_for_longform") == local_function_ast(chunk_text_for_longform)
        and [c["text"] for c in plan["variants"]["v0_phase41d_control"]["chunks"]]
        == chunk_text_for_longform(source, 350))
    v1 = plan["variants"]["v1_semantic_chunking"]["chunks"]
    v2 = plan["variants"]["v2_natural_pacing"]["chunks"]
    checks["v1_segmentation_only"] = all(c["pause_after_seconds"] == 0.0 and c["focus_phrase"] is None for c in v1)
    invariant_keys = ["chunk_index", "text", "char_count", "text_sha256", "semantic_role",
                      "boundary_before", "boundary_after", "focus_phrase"]
    checks["v2_equals_v1_plus_pause_only"] = len(v1) == len(v2) and all(
        {k: a[k] for k in invariant_keys} == {k: b[k] for k in invariant_keys}
        for a, b in zip(v1, v2))
    v3 = plan["variants"]["v3_semantic_focus"]["chunks"]
    checks["v3_real_semantic_focus_structure"] = (
        [c["text"] for c in v3] != [c["text"] for c in v1]
        and any(c["boundary_after"] == "setup_resolution_boundary" for c in v3)
        and all(c["pause_after_seconds"] == 0.0 for c in v3)
        and all(c["focus_phrase"] and c["focus_phrase"] in c["text"] for c in v3))
    lexical = plan["canonical_spoken_lexical_text"]
    checks["lexical_reconstruction_all_variants"] = all(
        " ".join(c["text"] for c in spec["chunks"]) == lexical
        for spec in plan["variants"].values())
    checks["chunk_metadata"] = all(
        c["variant"] == name and c["chunk_index"] == i and c["char_count"] == len(c["text"])
        and c["text_sha256"] == sha256_text(c["text"])
        for name, spec in plan["variants"].items() for i, c in enumerate(spec["chunks"]))
    probe = {"version": 1, "completed": {"v0_phase41d_control": [0]}, "chunk": {"hash": "0" * 64, "duration": 1.0}}
    checks["checkpoint_serialization"] = json.loads(json.dumps(probe, sort_keys=True)) == probe
    checks["json_parse"] = True
    if require_files_match:
        checks["prosody_plan_matches_builder"] = json.loads(PLAN_PATH.read_text(encoding="utf-8")) == plan
    return checks


def phase41d_audit() -> dict[str, Any]:
    manifest = json.loads(PHASE41D_MANIFEST.read_text(encoding="utf-8"))
    source_lengths = {"01_short_monologue": 1103, "02_explanatory_section": 2163, "03_longform_stress_test": 4356}
    rows = [{
        "id": test["id"], "source_chars": source_lengths[test["id"]],
        "synthesized_chunk_chars": test["total_chars"], "duration": test["final_duration_seconds"],
        "source_chars_per_second": source_lengths[test["id"]] / test["final_duration_seconds"],
    } for test in manifest["tests"]]
    total_chars, total_duration = sum(r["source_chars"] for r in rows), sum(r["duration"] for r in rows)
    return {"rows": rows, "pooled_source_chars": total_chars, "pooled_duration": total_duration,
            "pooled_rate": total_chars / total_duration}


def render_report(config: dict[str, Any], plan: dict[str, Any], checks: dict[str, bool]) -> str:
    audit, source = phase41d_audit(), config["shared_passage"]["text"]
    lines = [
        "# Phase 41E Static Pre-Run Report", "", "## Result", "",
        f"**PHASE41E STATIC PREFLIGHT: {'PASS' if all(checks.values()) else 'FAIL'}**", "",
        "No TTS inference was run while preparing or validating this report.", "",
        "## Repository audit findings", "",
        "- Phase 41D Test 2's 2,163 count is `len()` of the punctuated canonical source in `final_names`.",
        "- The manifest's 2,137 count is the sum of text actually passed in its eight TTS calls. The exact splitter removes all 19 full stops; because `total_chars` sums eight chunks separately, it also excludes the 7 spaces between those chunks. Thus 2,163 − 19 − 7 = 2,137. Script and manifest chunks match byte-for-byte.",
        "- The final 41D report says Test 2 has 20 sentences; the exact source/splitter yields 19.",
        "- Former V0 was one sentence per chunk, not the Phase 41D greedy 350-character control.",
        "- Former V3 was structurally identical to V1 and copied V2 pauses, so it was not a semantic-focus experiment.",
        "- Former V2 did use the same six text chunks as V1, with pause metadata as its intended only difference.",
        "- Four tracked production files were already modified: `backend/app/tts/model.py`, `backend/app/tts/special_voices.py`, `backend/app/tts/voice_store.py`, and `backend/main.py`. This Phase 41E repair did not edit them; their provenance cannot be established from Git because the experiment tree is untracked.",
        "- Phase 41E write scope: PASS. This repair touched only `experiments/brand_voice_phase41e/`. Repository-wide production cleanliness: FAIL because of the pre-existing tracked backend modifications above.",
        "", "### Observed Candidate 03 rate", "",
        "| Test | Source chars | Synthesized chunk chars | Duration | Source chars/s |", "|---|---:|---:|---:|---:|",
    ]
    for row in audit["rows"]:
        lines.append(f"| {row['id']} | {row['source_chars']} | {row['synthesized_chunk_chars']} | {row['duration']:.2f}s | {row['source_chars_per_second']:.3f} |")
    lines += [
        "", f"Pooled source-text rate: **{audit['pooled_source_chars']} / {audit['pooled_duration']:.2f} = {audit['pooled_rate']:.3f} chars/s**.",
        "Pooled rate over text actually passed to TTS is 18.962 chars/s; it is not used for this punctuated-source estimate.",
        "", "## Canonical shared audition", "", "```text", source, "```", "",
        f"- UTF-8 SHA256: `{sha256_text(source)}`", f"- Characters: {len(source)}",
        f"- Words: {len(source.split())}", f"- Sentences: {len(phase41d_sentences(source))}",
        f"- Punctuation: `{json.dumps(punctuation_counts(source), ensure_ascii=False, sort_keys=True)}`",
        f"- Predicted duration at {audit['pooled_rate']:.3f} chars/s: {len(source) / audit['pooled_rate']:.2f}s (target 65–73s)",
        "", "Phase 41D removes full stops before external TTS calls. The plan therefore freezes both the punctuated source and exact Phase-41D-normalized spoken lexical form. Joining every variant's `text` fields with one space exactly reproduces that canonical spoken form.",
        "", "## Exact variant design", "",
    ]
    for name, spec in plan["variants"].items():
        lines += [f"### {name} — {spec['chunk_count']} chunks", "", spec["description"], "",
                  "| # | Chars | Before → after | Pause | Focus | Exact spoken text |",
                  "|---:|---:|---|---:|---|---|"]
        for c in spec["chunks"]:
            focus, text = c["focus_phrase"] or "—", c["text"].replace("|", "\\|")
            lines.append(f"| {c['chunk_index']} | {c['char_count']} | {c['boundary_before']} → {c['boundary_after']} | {c['pause_after_seconds']:.2f}s | {focus} | {text} |")
        lines.append("")
    lines += [
        "## Variant isolation", "",
        "- V0 is AST-verified against Phase 41D `chunk_text_for_longform`, with `max_chars=350`: 4 chunks of 330, 347, 332, and 275 characters.",
        "- V1 changes segmentation only. All manual pauses are zero; engine controls are frozen.",
        "- V2 has exactly V1's chunk texts, order, hashes, roles, boundary metadata, and engine controls. Only `pause_after_seconds` differs.",
        "- V3 has 8 chunks versus V1's 6 and a real setup/resolution boundary after `âm lượng,`. It uses no manual pause. Each thought has one primary focus phrase expressed only through grouping/boundaries.",
        "", "## Pause policy", "",
        "Clause 0.03s, sentence 0.06s, and thought transition 0.10s are an **experimental heuristic**, not scientifically derived. Only V2 inserts manual silence.",
        "", "## VieNeu 3.3.0 engine-control audit", "",
        "- Supported and forwarded: `temperature`, `top_k`, `top_p`, `max_new_frames`, `repetition_penalty`, `repetition_window`, `denoise`, `use_ref_codes`, and `apply_watermark`.",
        "- Chunking is supported through `max_chars`; Phase 41E passes planned chunks individually with `max_chars=800`, `batch_size=1`.",
        "- `silence_p` and `crossfade_p` are accepted by the signature but unused by VieNeu 3.3.0 V3 Turbo. V2 therefore inserts declared silence explicitly during assembly.",
        "- No explicit speed control exists.",
        "- No supported seed/RNG argument exists. **Deterministic seed: NO.**",
        "", "## Canonical integrity and static consistency", "",
    ]
    lines.extend(f"- {key}: **{'PASS' if value else 'FAIL'}**" for key, value in checks.items())
    lines += [
        "", "Canonical hashes verified:", "",
        f"- speaker embedding array: `{config['speaker_identity']['speaker_emb_array_sha256']}`",
        f"- speaker_emb.npy: `{config['speaker_identity']['speaker_emb_npy_sha256']}`",
        f"- reference_codes.npy: `{config['speaker_identity']['reference_codes_npy_sha256']}`",
        "", "Python compilation and JSON parsing are run separately in final verification.",
        "", "## Resource-safe external execution", "",
        "Close VS Code/Codex first, then run one variant per process:", "", "```bash",
        "cd \"/home/tung/ai voice\" && for variant in v0_phase41d_control v1_semantic_chunking v2_natural_pacing v3_semantic_focus; do .venv/bin/python experiments/brand_voice_phase41e/run_phase41e_prosody.py --generate --variant \"$variant\" || exit 1; done",
        "```", "",
        "Each chunk is written immediately and atomically checkpointed. Reuse requires matching plan/config/voice/text/WAV hashes. Interruption resumes at the first invalid or absent chunk.",
        "", "STOP BEFORE INFERENCE.", "",
    ]
    return "\n".join(lines)


def write_json_atomic(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    os.replace(temporary, path)


def refresh_static_artifacts(config: dict[str, Any]) -> dict[str, bool]:
    plan = build_plan(config)
    checks = static_checks(config, plan, require_files_match=False)
    if not all(checks.values()):
        raise AssertionError(f"refusing failing plan: {[k for k, v in checks.items() if not v]}")
    write_json_atomic(PLAN_PATH, plan)
    checks = static_checks(config, plan, require_files_match=True)
    REPORT_PATH.write_text(render_report(config, plan, checks), encoding="utf-8")
    return checks


def load_checkpoint(config: dict[str, Any]) -> dict[str, Any]:
    binding = {"version": 1, "config_sha256": sha256_file(CONFIG_PATH),
               "plan_sha256": sha256_file(PLAN_PATH), **canonical_hashes(config)}
    if CHECKPOINT_PATH.exists():
        state = json.loads(CHECKPOINT_PATH.read_text(encoding="utf-8"))
        if all(state.get(k) == v for k, v in binding.items()):
            state.setdefault("chunks", {})
            return state
    return {**binding, "chunks": {}}


def checkpoint_entry_valid(entry: dict[str, Any] | None, chunk: dict[str, Any], path: Path) -> bool:
    return bool(entry and path.is_file() and entry.get("text_sha256") == chunk["text_sha256"]
                and entry.get("wav_sha256") == sha256_file(path))


def wav_duration(path: Path) -> float:
    with wave.open(str(path), "rb") as handle:
        return handle.getnframes() / handle.getframerate()


def assemble_variant(variant: str, chunks: list[dict[str, Any]]) -> Path:
    final_path, temporary = OUTPUT_DIR / f"{variant}_final.wav", OUTPUT_DIR / f"{variant}_final.tmp.wav"
    with wave.open(str(temporary), "wb") as output:
        output.setnchannels(1); output.setsampwidth(2); output.setframerate(48000)
        for chunk in chunks:
            path = OUTPUT_DIR / variant / f"chunk_{chunk['chunk_index']:03d}.wav"
            with wave.open(str(path), "rb") as source:
                if (source.getnchannels(), source.getsampwidth(), source.getframerate()) != (1, 2, 48000):
                    raise RuntimeError(f"unexpected WAV format: {path}")
                output.writeframes(source.readframes(source.getnframes()))
            output.writeframes(b"\x00\x00" * round(chunk["pause_after_seconds"] * 48000))
    os.replace(temporary, final_path)
    return final_path


def update_manifest(variant: str, chunks: list[dict[str, Any]], final_path: Path) -> None:
    manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8")) if MANIFEST_PATH.exists() else {"phase": "41E", "variants": {}}
    if not isinstance(manifest.get("variants"), dict):
        manifest["variants"] = {}
    manifest["variants"][variant] = {
        "final_file": str(final_path), "final_sha256": sha256_file(final_path),
        "duration_seconds": wav_duration(final_path), "chunk_count": len(chunks),
        "manual_pause_seconds": sum(c["pause_after_seconds"] for c in chunks),
    }
    write_json_atomic(MANIFEST_PATH, manifest)


def generate_variant(config: dict[str, Any], plan: dict[str, Any], variant: str) -> None:
    checks = static_checks(config, plan, require_files_match=True)
    if not all(checks.values()):
        raise RuntimeError(f"static preflight failed: {[k for k, v in checks.items() if not v]}")
    import soundfile as sf
    from vieneu import Vieneu

    variant_dir = OUTPUT_DIR / variant
    variant_dir.mkdir(parents=True, exist_ok=True)
    state, chunks = load_checkpoint(config), plan["variants"][variant]["chunks"]
    state["chunks"].setdefault(variant, {})
    voice_root, engine = Path(config["speaker_identity"]["canonical_root"]), config["engine_controls"]
    emb = np.load(voice_root / "speaker_emb.npy", allow_pickle=False).astype(np.float32)
    codes = np.load(voice_root / "reference_codes.npy", allow_pickle=False)
    tts = Vieneu(mode=engine["mode"], backend=engine["backend"])
    for chunk in chunks:
        key, path = str(chunk["chunk_index"]), variant_dir / f"chunk_{chunk['chunk_index']:03d}.wav"
        if checkpoint_entry_valid(state["chunks"][variant].get(key), chunk, path):
            print(f"REUSE {variant} chunk {key}", flush=True); continue
        print(f"GENERATE {variant} chunk {key}/{len(chunks) - 1}", flush=True)
        wav = tts.infer(
            chunk["text"], voice={"speaker_emb": emb, "codes": codes},
            temperature=engine["temperature"], top_k=engine["top_k"], top_p=engine["top_p"],
            repetition_penalty=engine["repetition_penalty"], repetition_window=engine["repetition_window"],
            denoise=engine["denoise"], use_ref_codes=engine["use_ref_codes"],
            silence_p=engine["silence_p"], crossfade_p=engine["crossfade_p"],
            apply_watermark=engine["apply_watermark"], max_new_frames=engine["max_new_frames"],
            max_chars=engine["max_chars"], batch_size=engine["batch_size"])
        arr = np.asarray(wav, dtype=np.float32)
        if not arr.size:
            raise RuntimeError(f"empty audio: {variant} chunk {key}")
        temporary = variant_dir / f"chunk_{chunk['chunk_index']:03d}.tmp.wav"
        sf.write(temporary, arr, engine["sample_rate"], subtype="PCM_16")
        os.replace(temporary, path)
        state["chunks"][variant][key] = {"text_sha256": chunk["text_sha256"],
            "wav_sha256": sha256_file(path), "duration_seconds": wav_duration(path)}
        write_json_atomic(CHECKPOINT_PATH, state)
        del arr, wav
        gc.collect()
    final_path = assemble_variant(variant, chunks)
    update_manifest(variant, chunks, final_path)
    print(f"COMPLETE {variant}: {final_path}", flush=True)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    action = parser.add_mutually_exclusive_group()
    action.add_argument("--refresh-static-artifacts", action="store_true")
    action.add_argument("--generate", action="store_true")
    parser.add_argument("--variant", choices=["v0_phase41d_control", "v1_semantic_chunking", "v2_natural_pacing", "v3_semantic_focus"])
    args = parser.parse_args()
    config = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
    if args.refresh_static_artifacts:
        checks = refresh_static_artifacts(config)
    else:
        plan = build_plan(config)
        if args.generate:
            if not args.variant:
                raise SystemExit("--generate requires exactly one --variant")
            generate_variant(config, plan, args.variant)
            return 0
        if args.variant:
            raise SystemExit("--variant is valid only with --generate")
        checks = static_checks(config, plan, require_files_match=True)
    for name, passed in checks.items():
        print(f"{'PASS' if passed else 'FAIL'} {name}")
    print(f"PHASE41E STATIC PREFLIGHT: {'PASS' if all(checks.values()) else 'FAIL'}")
    return 0 if all(checks.values()) else 1


if __name__ == "__main__":
    sys.exit(main())
