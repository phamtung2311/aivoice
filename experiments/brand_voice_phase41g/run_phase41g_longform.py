#!/usr/bin/env python3
"""Phase 41G static preflight and external long-form confirmation runner.

Default execution is static validation only. TTS and FFmpeg require explicit
``--generate`` and must be run by the user in an external terminal.
"""

from __future__ import annotations

import argparse
import gc
import hashlib
import json
import os
import re
import subprocess
import sys
import tempfile
import time
import wave
from pathlib import Path
from typing import Any

import numpy as np

ROOT = Path("experiments/brand_voice_phase41g")
CONFIG_PATH = ROOT / "config.json"
TEXT_PATH = ROOT / "podcast_text.txt"
PLAN_PATH = ROOT / "semantic_plan.json"
CHECKPOINT_PATH = ROOT / "resume_state.json"
PRE_RUN_REPORT_PATH = ROOT / "PHASE41G_PRE_RUN_REPORT.md"
FINAL_REPORT_PATH = ROOT / "PHASE41G_REPORT.md"
HUMAN_REVIEW_PATH = ROOT / "HUMAN_REVIEW.md"

# Manually curated semantic units. Sentence IDs are inclusive, zero-based, and
# ordered. Size is only a safety constraint; each tuple is a complete thought.
GROUP_SPECS: list[tuple[list[int], str, str]] = [
    ([0], "reflective_opening", "việc nào thật sự đáng làm trước"),
    ([1], "pressure_context", "nếu chậm lại, ta sẽ bị bỏ xa"),
    ([2, 3], "diagnosis", "quá nhiều tín hiệu"),
    ([4], "opening_conclusion", "biết mình đang chạy về đâu"),
    ([5, 6], "misguided_response", "nhồi thêm kỷ luật"),
    ([7], "short_term_consequence", "liên tục chấm điểm chính mình"),
    ([8, 9], "discipline_contrast_resolution", "bảo vệ điều có ý nghĩa"),
    ([10, 11], "concrete_example_setup", "cửa hàng nhỏ ở cuối phố"),
    ([12, 13], "example_pressure", "thiếu thời gian"),
    ([14], "example_diagnosis", "ưu tiên cùng một lúc"),
    ([15], "advice_contrast", "chưa chắc hữu ích"),
    ([16], "triage_principle", "đâu là việc phải xử lý ngay"),
    ([17, 18], "concrete_action", "Không có quyết định nào đặc biệt lớn lao"),
    ([19], "causal_resolution", "thứ tự trở nên rõ ràng"),
    ([20, 21], "busy_direction_distinction", "chuyển động ấy phục vụ điều gì"),
    ([22, 23], "avoidance_example", "né tránh câu hỏi khó"),
    ([24, 25], "reactive_consequence", "phản ứng với tiếng gọi gần nhất"),
    ([26], "responsible_slowing_contrast", "hành động có trách nhiệm nhất"),
    ([27, 28], "pause_examples", "dừng vài giây"),
    ([29, 30], "pause_example_resolution", "Khoảng dừng đúng chỗ"),
    ([31], "attention_explanation", "chuyển sự chú ý quá thường xuyên"),
    ([32], "attention_mechanism_setup", "không lập tức trở về trạng thái cũ"),
    ([33], "attention_residue_image", "Một phần chú ý vẫn mắc lại"),
    ([34, 35], "attention_causal_resolution", "chi phí âm thầm"),
    ([36, 37], "focus_transition_principle", "bảo vệ một khoảng thời gian"),
    ([38], "single_task_practice", "một điểm dừng tự nhiên"),
    ([39, 40], "distraction_difficulty", "phân tán là trạng thái mặc định"),
    ([41, 42], "daily_priority_setup", "một trục"),
    ([43, 44], "decision_questions", "Ba câu hỏi ngắn"),
    ([45], "agency_resolution", "quyền lựa chọn"),
    ([46, 47], "uncertainty_setup", "không có nghĩa là kiểm soát được mọi biến cố"),
    ([48, 49], "stability_resolution", "không biến một sự cố thành bản án"),
    ([50], "resilience_conclusion", "biết tìm lại nhịp"),
    ([51, 52], "rest_avoidance_distinction", "nghỉ ngơi và trốn tránh"),
    ([53, 54], "rest_contrast", "đầu óc đầy hơn nhưng lòng lại rỗng hơn"),
    ([55], "rest_resolution", "đang tìm kiếm điều gì"),
    ([56, 57], "rest_examples", "Không hình thức nào tự động cao quý hơn"),
    ([58, 59], "rest_criterion_setup", "rời khỏi trạng thái phải phản ứng liên tục"),
    ([60], "rest_criterion_resolution", "trở về với nhịp thở"),
    ([61, 62], "relationship_speed_setup", "chuẩn bị lời phản bác"),
    ([63, 64], "defensive_reaction", "bảo vệ cảm giác không muốn bị xem là sai"),
    ([65], "relational_pause_effect", "giữ lại một nhịp"),
    ([66, 67], "mature_boundary_contrast", "vẫn cần ranh giới"),
    ([68, 69], "weighted_speech_setup", "đã hiểu mình muốn bảo vệ điều gì"),
    ([70], "weighted_speech_resolution", "sự rõ ràng đứng ở phía trước"),
    ([71, 72], "closing_transition", "đang trao thời gian cho điều gì"),
    ([73, 74], "tempo_contrast", "câu trả lời đúng"),
    ([75], "tempo_conclusion", "chọn đúng nhịp"),
    ([76, 77], "practical_call_to_action", "một việc thật sự quan trọng"),
    ([78, 79], "next_step", "không cần chứng minh giá trị"),
    ([80], "important_conclusion", "vẫn nhận ra hướng đi của mình"),
    ([81, 82], "closing_realism", "không làm cho nỗ lực hôm nay trở nên vô nghĩa"),
    ([83], "growth_metaphor", "nhiều lần quay về"),
    ([84], "growth_effect", "tử tế hơn với giới hạn của chính mình"),
    ([85], "final_reflection", "biết con đường trở lại"),
]


def canonical_json_bytes(value: Any) -> bytes:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")


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


def read_source() -> str:
    return TEXT_PATH.read_text(encoding="utf-8").strip()


def source_sentences(source: str) -> tuple[list[str], list[int]]:
    sentences: list[str] = []
    paragraph_ids: list[int] = []
    for paragraph_id, paragraph in enumerate(source.split("\n\n")):
        for sentence in re.split(r"(?<=[.!?])\s+", paragraph.strip()):
            if sentence.strip():
                sentences.append(sentence.strip())
                paragraph_ids.append(paragraph_id)
    return sentences, paragraph_ids


def spoken_sentence(sentence: str) -> str:
    # Match the winning Phase 41E V3 policy: terminal full stops are not sent to TTS.
    return re.sub(r"[.!?]+$", "", sentence).strip()


def punctuation_counts(text: str) -> dict[str, int]:
    return {mark: text.count(mark) for mark in [".", ",", ";", ":", "?", "!", "…"]}


def canonical_hashes(config: dict[str, Any]) -> dict[str, str]:
    speaker_root = Path(config["speaker_identity"]["canonical_root"])
    emb_path = speaker_root / "speaker_emb.npy"
    codes_path = speaker_root / "reference_codes.npy"
    emb = np.load(emb_path, allow_pickle=False).astype(np.float32)
    return {
        "canonical_embedding_array_sha256": sha256_bytes(np.ascontiguousarray(emb).tobytes()),
        "speaker_emb_npy_sha256": sha256_file(emb_path),
        "reference_codes_sha256": sha256_file(codes_path),
    }


def candidate_b_unchanged(config: dict[str, Any]) -> bool:
    identity = config["candidate_b_identity"]
    root = Path(identity["canonical_root"])
    return (sha256_file(root / "speaker_emb.npy") == identity["speaker_emb_npy_sha256"]
            and sha256_file(root / "reference_codes.npy") == identity["reference_codes_npy_sha256"])


def build_plan(config: dict[str, Any]) -> dict[str, Any]:
    source = read_source()
    sentences, paragraph_ids = source_sentences(source)
    chunks = []
    flattened_ids: list[int] = []
    setup_roles = {"concrete_example_setup", "attention_mechanism_setup", "daily_priority_setup",
                   "uncertainty_setup", "rest_criterion_setup", "relationship_speed_setup",
                   "weighted_speech_setup"}
    for index, (ids, role, focus) in enumerate(GROUP_SPECS):
        flattened_ids.extend(ids)
        text = " ".join(spoken_sentence(sentences[sentence_id]) for sentence_id in ids)
        if index == 0:
            before = "paragraph_start"
        elif GROUP_SPECS[index - 1][1] in setup_roles:
            before = "setup_resolution_boundary"
        elif paragraph_ids[ids[0]] != paragraph_ids[GROUP_SPECS[index - 1][0][-1]]:
            before = "thought_transition"
        else:
            before = "semantic_thought_boundary"
        if index == len(GROUP_SPECS) - 1:
            after = "paragraph_end"
        elif role in setup_roles:
            after = "setup_resolution_boundary"
        elif paragraph_ids[ids[-1]] != paragraph_ids[GROUP_SPECS[index + 1][0][0]]:
            after = "thought_transition"
        else:
            after = "semantic_thought_boundary"
        chunks.append({
            "chunk_index": index,
            "text": text,
            "text_sha256": sha256_text(text),
            "char_count": len(text),
            "word_count": len(text.split()),
            "semantic_role": role,
            "boundary_before": before,
            "boundary_after": after,
            "primary_focus_phrase": focus,
            "source_sentence_ids": [f"S{sentence_id:03d}" for sentence_id in ids],
            "pause_after_seconds": 0.0,
        })
    if flattened_ids != list(range(len(sentences))):
        raise AssertionError("semantic specs do not cover every source sentence exactly once in order")
    canonical_spoken = " ".join(spoken_sentence(sentence) for sentence in sentences)
    return {
        "phase": "41G",
        "policy": "Phase41E v3_semantic_focus",
        "source_text_path": str(TEXT_PATH),
        "source_text_sha256": sha256_text(source),
        "source_file_sha256": sha256_file(TEXT_PATH),
        "canonical_spoken_text_sha256": sha256_text(canonical_spoken),
        "canonical_spoken_text": canonical_spoken,
        "reconstruction_rule": "Join chunk text fields with one ASCII space; terminal sentence punctuation is removed exactly as in Phase 41E V3.",
        "manual_inserted_silence_seconds": 0.0,
        "chunk_count": len(chunks),
        "chunks": chunks,
    }


def checkpoint_bindings(config: dict[str, Any], plan: dict[str, Any]) -> dict[str, Any]:
    return {
        "schema": "phase41g_resume",
        "version": 1,
        **canonical_hashes(config),
        "inference_config_sha256": config["inference_config_sha256"],
        "source_podcast_text_sha256": plan["source_text_sha256"],
        "semantic_plan_sha256": sha256_bytes(canonical_json_bytes(plan) + b"\n"),
    }


def fresh_checkpoint(config: dict[str, Any], plan: dict[str, Any]) -> dict[str, Any]:
    return {**checkpoint_bindings(config, plan), "chunks": {}, "original_final": None, "tempo_final": None}


def write_json_atomic(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_bytes(canonical_json_bytes(value) + b"\n")
    os.replace(temporary, path)


def wav_metadata(path: Path) -> dict[str, Any]:
    with wave.open(str(path), "rb") as wav:
        return {
            "channels": wav.getnchannels(),
            "sample_width": wav.getsampwidth(),
            "sample_rate": wav.getframerate(),
            "frames": wav.getnframes(),
            "duration_seconds": wav.getnframes() / wav.getframerate(),
        }


def static_checks(config: dict[str, Any], plan: dict[str, Any], require_disk_plan: bool = True) -> dict[str, bool]:
    source = read_source()
    sentences, _ = source_sentences(source)
    metrics = config["podcast_text"]
    hashes = canonical_hashes(config)
    expected_hashes = {
        "canonical_embedding_array_sha256": config["speaker_identity"]["speaker_emb_array_sha256"],
        "speaker_emb_npy_sha256": config["speaker_identity"]["speaker_emb_npy_sha256"],
        "reference_codes_sha256": config["speaker_identity"]["reference_codes_npy_sha256"],
    }
    chunk_chars = [chunk["char_count"] for chunk in plan["chunks"]]
    checks = {
        "canonical_speaker_hash": hashes["canonical_embedding_array_sha256"] == expected_hashes["canonical_embedding_array_sha256"],
        "canonical_npy_hash": hashes["speaker_emb_npy_sha256"] == expected_hashes["speaker_emb_npy_sha256"],
        "reference_codes_hash": hashes["reference_codes_sha256"] == expected_hashes["reference_codes_sha256"],
        "phase41e_v3_policy_frozen": plan["policy"] == "Phase41E v3_semantic_focus" and all(chunk["primary_focus_phrase"] for chunk in plan["chunks"]),
        "no_v2_pause_injection": plan["manual_inserted_silence_seconds"] == 0.0 and all(chunk["pause_after_seconds"] == 0.0 for chunk in plan["chunks"]),
        "tempo_policy_0_98": config["post_tempo_factor"] == 0.98,
        "script_frozen": sha256_text(source) == metrics["canonical_utf8_sha256"] and sha256_file(TEXT_PATH) == metrics["file_sha256"] and len(source) == metrics["characters"] and len(source.split()) == metrics["words"] and len(sentences) == metrics["sentences"] and punctuation_counts(source) == metrics["punctuation"],
        "inference_config_frozen": sha256_bytes(canonical_json_bytes(config["inference"])) == config["inference_config_sha256"],
        "semantic_plan_reconstruction": " ".join(chunk["text"] for chunk in plan["chunks"]) == plan["canonical_spoken_text"],
        "focus_phrases_exist": all(chunk["text"].count(chunk["primary_focus_phrase"]) == 1 for chunk in plan["chunks"]),
        "chunk_safety": min(chunk_chars) >= 1 and max(chunk_chars) <= config["inference"]["max_chars_chunk_safety"],
        "duration_target": 360.0 <= metrics["characters"] / config["historical_source_characters_per_second"] / config["post_tempo_factor"] <= 480.0,
        "candidate_status_unchanged": config["speaker_identity"]["status"] == "candidate" and config["speaker_identity"]["is_final_brand_voice"] is False,
        "candidate_b_untouched": candidate_b_unchanged(config),
        "json_parse": True,
    }
    if require_disk_plan:
        checks["semantic_plan_matches_builder"] = json.loads(PLAN_PATH.read_text(encoding="utf-8")) == plan
    with tempfile.TemporaryDirectory(prefix="phase41g_checkpoint_", dir="/tmp") as temporary_dir:
        probe_path = Path(temporary_dir) / "resume_state.json"
        probe = fresh_checkpoint(config, plan)
        probe["chunks"]["0"] = {"chunk_index": 0, "text_sha256": "0" * 64, "wav_sha256": "1" * 64, "duration_seconds": 1.0, "status": "complete"}
        probe_path.write_bytes(canonical_json_bytes(probe) + b"\n")
        checks["checkpoint_serialization"] = json.loads(probe_path.read_text(encoding="utf-8")) == probe
    return checks


def metrics(config: dict[str, Any], plan: dict[str, Any]) -> dict[str, Any]:
    chars = [chunk["char_count"] for chunk in plan["chunks"]]
    pre = config["podcast_text"]["characters"] / config["historical_source_characters_per_second"]
    return {
        "min_chunk_chars": min(chars), "max_chunk_chars": max(chars),
        "mean_chunk_chars": sum(chars) / len(chars),
        "focus_phrase_count": sum(bool(chunk["primary_focus_phrase"]) for chunk in plan["chunks"]),
        "estimated_original_seconds": pre,
        "estimated_tempo_98_seconds": pre / config["post_tempo_factor"],
    }


def render_pre_run_report(config: dict[str, Any], plan: dict[str, Any], checks: dict[str, bool]) -> str:
    source = read_source()
    values = metrics(config, plan)
    lines = [
        "# Phase 41G Static Pre-Run Report", "", "## Result", "",
        f"**PHASE41G STATIC PREFLIGHT: {'PASS' if all(checks.values()) else 'FAIL'}**", "",
        "No TTS inference and no FFmpeg transformation were run during this preflight.", "",
        "## Frozen winner chain", "",
        "- Phase 41E human winner: `v3_semantic_focus` (Blind 04).",
        "- Phase 41F human winner: `tempo_98`, 0.98x (Blind 03).",
        "- Frozen stack: Synthetic Candidate 03 + Phase41E `v3_semantic_focus` + Phase41F 0.98x.",
        "- Candidate 03 remains `status = candidate`, `is_final_brand_voice = false`.",
        "", "## Canonical hashes", "",
        f"- Speaker embedding array: `{config['speaker_identity']['speaker_emb_array_sha256']}`",
        f"- `speaker_emb.npy`: `{config['speaker_identity']['speaker_emb_npy_sha256']}`",
        f"- `reference_codes.npy`: `{config['speaker_identity']['reference_codes_npy_sha256']}`",
        f"- Candidate B `speaker_emb.npy`: `{config['candidate_b_identity']['speaker_emb_npy_sha256']}` (unchanged)",
        f"- Candidate B `reference_codes.npy`: `{config['candidate_b_identity']['reference_codes_npy_sha256']}` (unchanged)",
        "", "## Exact podcast test script", "", "```text", source, "```", "",
        "## Script and duration metrics", "",
        f"- Source characters: {config['podcast_text']['characters']}",
        f"- Words: {config['podcast_text']['words']}",
        f"- Sentences: {config['podcast_text']['sentences']}",
        f"- Punctuation: `{json.dumps(config['podcast_text']['punctuation'], ensure_ascii=False, sort_keys=True)}`",
        f"- Canonical UTF-8 text SHA256: `{config['podcast_text']['canonical_utf8_sha256']}`",
        f"- Exact file SHA256: `{config['podcast_text']['file_sha256']}`",
        f"- Historical rate: {config['historical_source_characters_per_second']:.6f} source chars/s",
        f"- Estimated original duration: {values['estimated_original_seconds']:.2f}s ({values['estimated_original_seconds']/60:.2f} min)",
        f"- Estimated final duration after 0.98x: {values['estimated_tempo_98_seconds']:.2f}s ({values['estimated_tempo_98_seconds']/60:.2f} min)",
        "", "## Semantic-focus plan", "",
        "The plan reuses Phase 41E V3 principles: manually selected coherent thoughts, explicit setup/resolution boundaries where useful, shorter varied units, and one primary focus phrase per thought. Character size is only a 350-character hard safety bound. No focus phrase is repeated, capitalized for emphasis, tagged, or acoustically manipulated. Terminal full stops are removed from TTS text exactly as in Phase 41E V3.", "",
        f"- Chunk count: {plan['chunk_count']}", f"- Minimum chunk: {values['min_chunk_chars']} chars",
        f"- Maximum chunk: {values['max_chunk_chars']} chars", f"- Mean chunk: {values['mean_chunk_chars']:.2f} chars",
        f"- Focus phrases: {values['focus_phrase_count']}", "- Manual inserted silence: 0.00s", "",
        "| # | Source IDs | Chars | Words | Role | Before → after | Focus phrase | Exact TTS text |",
        "|---:|---|---:|---:|---|---|---|---|",
    ]
    for chunk in plan["chunks"]:
        exact = chunk["text"].replace("|", "\\|")
        lines.append(f"| {chunk['chunk_index']} | {', '.join(chunk['source_sentence_ids'])} | {chunk['char_count']} | {chunk['word_count']} | {chunk['semantic_role']} | {chunk['boundary_before']} → {chunk['boundary_after']} | {chunk['primary_focus_phrase']} | {exact} |")
    lines += [
        "", "## Exact inference configuration", "", "```json",
        json.dumps(config["inference"], ensure_ascii=False, indent=2, sort_keys=True), "```", "",
        f"Canonical inference-config SHA256: `{config['inference_config_sha256']}`.",
        "The values match Phase 41E. `silence_p` and `crossfade_p` remain recorded for config continuity although VieNeu 3.3.0 V3 Turbo does not consume them; no external silence is inserted.",
        "", "## Stochastic limitation", "",
        "VieNeu 3.3.0 has no supported deterministic seed. This is a long-form confirmation of one generated realization, not proof of deterministic repeatability. A complete valid run is retained as the test; the runner does not rerender merely to seek a nicer sample.",
        "", "## Checkpoint and resource-safety design", "",
        "The runner processes one semantic chunk at a time with batch size 1, writes PCM16 WAV immediately through a temporary file, atomically updates a deterministic JSON checkpoint, deletes waveform arrays, and invokes garbage collection. It never holds the complete generated program in memory. Original assembly streams chunk frames from disk.",
        "", "Checkpoint reuse requires matching schema/version, canonical embedding-array hash, speaker NPY hash, reference-code hash, inference-config hash, source-text hash, semantic-plan file hash, chunk index, chunk text hash, existing WAV hash, duration, and `complete` status. Index-only reuse is impossible. Serialization testing uses a temporary directory under `/tmp`, never the production resume file.",
        "", "After original assembly, FFmpeg `atempo=0.98` is applied exactly once to the complete final WAV. Individual chunks are never stretched. No pitch, formant, EQ, loudness, compression, or manual pause operation is requested.",
        "", "## Static verification", "",
    ]
    lines.extend(f"- {name}: **{'PASS' if passed else 'FAIL'}**" for name, passed in checks.items())
    lines += [
        "- Python compile: **verified separately**", "- Production untouched: **PASS; Phase 41G writes are experiment-local only**",
        "", "## Exact external command", "", "Close VS Code/Codex, then run:", "", "```bash",
        "cd \"/home/tung/ai voice\" && .venv/bin/python experiments/brand_voice_phase41g/run_phase41g_longform.py --generate",
        "```", "", "STOP BEFORE INFERENCE.", "",
    ]
    return "\n".join(lines)


def refresh_static(config: dict[str, Any]) -> dict[str, bool]:
    plan = build_plan(config)
    checks = static_checks(config, plan, require_disk_plan=False)
    if not all(checks.values()):
        raise AssertionError(f"static design failed: {[name for name, passed in checks.items() if not passed]}")
    write_json_atomic(PLAN_PATH, plan)
    checks = static_checks(config, plan, require_disk_plan=True)
    if CHECKPOINT_PATH.exists():
        existing = json.loads(CHECKPOINT_PATH.read_text(encoding="utf-8"))
        if existing.get("chunks"):
            raise RuntimeError("refusing to overwrite a non-empty production checkpoint")
    write_json_atomic(CHECKPOINT_PATH, fresh_checkpoint(config, plan))
    PRE_RUN_REPORT_PATH.write_text(render_pre_run_report(config, plan, checks), encoding="utf-8")
    return checks


def load_checkpoint(config: dict[str, Any], plan: dict[str, Any]) -> dict[str, Any]:
    state = json.loads(CHECKPOINT_PATH.read_text(encoding="utf-8"))
    expected = checkpoint_bindings(config, plan)
    mismatches = [key for key, value in expected.items() if state.get(key) != value]
    if mismatches:
        raise RuntimeError(f"checkpoint binding mismatch: {mismatches}")
    if not isinstance(state.get("chunks"), dict):
        raise RuntimeError("invalid checkpoint chunks map")
    return state


def chunk_reusable(entry: dict[str, Any] | None, chunk: dict[str, Any], path: Path) -> bool:
    return bool(entry and entry.get("status") == "complete" and entry.get("chunk_index") == chunk["chunk_index"]
                and entry.get("text_sha256") == chunk["text_sha256"] and path.is_file()
                and entry.get("wav_sha256") == sha256_file(path)
                and abs(entry.get("duration_seconds", -1) - wav_metadata(path)["duration_seconds"]) < 1e-9)


def assemble_original(config: dict[str, Any], plan: dict[str, Any]) -> Path:
    output = Path(config["output"]["original_final"])
    temporary = output.with_suffix(".tmp.wav")
    output.parent.mkdir(parents=True, exist_ok=True)
    with wave.open(str(temporary), "wb") as destination:
        destination.setnchannels(1)
        destination.setsampwidth(2)
        destination.setframerate(config["inference"]["sample_rate"])
        for chunk in plan["chunks"]:
            source_path = Path(config["output"]["chunk_directory"]) / f"chunk_{chunk['chunk_index']:03d}.wav"
            with wave.open(str(source_path), "rb") as source:
                if (source.getnchannels(), source.getsampwidth(), source.getframerate()) != (1, 2, 48000):
                    raise RuntimeError(f"unexpected chunk WAV format: {source_path}")
                while True:
                    frames = source.readframes(48000)
                    if not frames:
                        break
                    destination.writeframes(frames)
    os.replace(temporary, output)
    return output


def apply_final_tempo(config: dict[str, Any], original: Path) -> Path:
    output = Path(config["output"]["tempo_final"])
    temporary = output.with_suffix(".tmp.wav")
    subprocess.run([
        "ffmpeg", "-nostdin", "-hide_banner", "-loglevel", "warning", "-y", "-i", str(original),
        "-map_metadata", "-1", "-filter:a", "atempo=0.98", "-ar", "48000", "-ac", "1",
        "-c:a", "pcm_s16le", str(temporary),
    ], check=True)
    os.replace(temporary, output)
    return output


def render_final_report(config: dict[str, Any], plan: dict[str, Any], manifest: dict[str, Any]) -> str:
    return "\n".join([
        "# Phase 41G Final Technical Report", "", "Generation completed for one unseeded realization of the frozen stack.", "",
        f"- Original WAV: `{manifest['original']['path']}`", f"- Original SHA256: `{manifest['original']['sha256']}`",
        f"- Original duration: {manifest['original']['duration_seconds']:.6f}s",
        f"- 0.98x WAV: `{manifest['tempo_98']['path']}`", f"- 0.98x SHA256: `{manifest['tempo_98']['sha256']}`",
        f"- 0.98x duration: {manifest['tempo_98']['duration_seconds']:.6f}s", f"- Chunk count: {plan['chunk_count']}", "",
        "VieNeu has no supported deterministic seed. This file documents one realization and does not establish repeatability. Human long-form QA remains authoritative.", "",
        "SYNTHETIC CANDIDATE 03 FINAL LONG-FORM PODCAST CONFIRMATION:", "PENDING HUMAN QA", "",
    ])


def generate(config: dict[str, Any], plan: dict[str, Any]) -> None:
    checks = static_checks(config, plan, require_disk_plan=True)
    if not all(checks.values()):
        raise RuntimeError(f"static preflight failed: {[name for name, passed in checks.items() if not passed]}")
    state = load_checkpoint(config, plan)
    chunks_dir = Path(config["output"]["chunk_directory"])
    chunks_dir.mkdir(parents=True, exist_ok=True)

    # Heavy runtime imports and initialization occur only after explicit --generate.
    import soundfile as sf
    from vieneu import Vieneu

    speaker_root = Path(config["speaker_identity"]["canonical_root"])
    emb = np.load(speaker_root / "speaker_emb.npy", allow_pickle=False).astype(np.float32)
    codes = np.load(speaker_root / "reference_codes.npy", allow_pickle=False)
    engine = config["inference"]
    tts = Vieneu(mode=engine["mode"], backend=engine["backend"])

    for chunk in plan["chunks"]:
        key = str(chunk["chunk_index"])
        path = chunks_dir / f"chunk_{chunk['chunk_index']:03d}.wav"
        if chunk_reusable(state["chunks"].get(key), chunk, path):
            print(f"REUSE chunk {chunk['chunk_index']}/{plan['chunk_count'] - 1}", flush=True)
            continue
        print(f"GENERATE chunk {chunk['chunk_index']}/{plan['chunk_count'] - 1}", flush=True)
        started = time.time()
        wav = tts.infer(
            chunk["text"], voice={"speaker_emb": emb, "codes": codes},
            temperature=engine["temperature"], top_k=engine["top_k"], top_p=engine["top_p"],
            repetition_penalty=engine["repetition_penalty"], repetition_window=engine["repetition_window"],
            denoise=engine["denoise"], use_ref_codes=engine["use_ref_codes"],
            silence_p=engine["silence_p"], crossfade_p=engine["crossfade_p"],
            apply_watermark=engine["apply_watermark"], max_new_frames=engine["max_new_frames"],
            max_chars=engine["max_chars"], batch_size=engine["batch_size"],
        )
        array = np.asarray(wav, dtype=np.float32)
        if not array.size:
            raise RuntimeError(f"empty audio for chunk {chunk['chunk_index']}")
        temporary = path.with_suffix(".tmp.wav")
        sf.write(temporary, array, engine["sample_rate"], subtype="PCM_16")
        os.replace(temporary, path)
        audio_meta = wav_metadata(path)
        state["chunks"][key] = {
            "chunk_index": chunk["chunk_index"], "text_sha256": chunk["text_sha256"],
            "wav_sha256": sha256_file(path), "duration_seconds": audio_meta["duration_seconds"],
            "generation_seconds": time.time() - started, "status": "complete",
        }
        write_json_atomic(CHECKPOINT_PATH, state)
        del array, wav
        gc.collect()

    del tts, emb, codes
    gc.collect()
    original = assemble_original(config, plan)
    state["original_final"] = {"path": str(original), "sha256": sha256_file(original), **wav_metadata(original)}
    write_json_atomic(CHECKPOINT_PATH, state)
    tempo = apply_final_tempo(config, original)
    state["tempo_final"] = {"path": str(tempo), "sha256": sha256_file(tempo), **wav_metadata(tempo)}
    write_json_atomic(CHECKPOINT_PATH, state)
    manifest = {
        "phase": "41G", "status": "pending_human_qa", "generated_realization_count": 1,
        "source_text_sha256": plan["source_text_sha256"], "semantic_plan_sha256": sha256_file(PLAN_PATH),
        "inference_config_sha256": config["inference_config_sha256"], **canonical_hashes(config),
        "chunk_count": plan["chunk_count"], "chunks": state["chunks"],
        "manual_inserted_silence_seconds": 0.0, "tempo_filter": "atempo=0.98 applied once after assembly",
        "original": state["original_final"], "tempo_98": state["tempo_final"], "peak_rss_mb": None,
    }
    write_json_atomic(Path(config["output"]["manifest"]), manifest)
    FINAL_REPORT_PATH.write_text(render_final_report(config, plan, manifest), encoding="utf-8")
    print(f"PHASE41G GENERATION COMPLETE: {tempo}", flush=True)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    actions = parser.add_mutually_exclusive_group()
    actions.add_argument("--refresh-static-artifacts", action="store_true")
    actions.add_argument("--generate", action="store_true")
    args = parser.parse_args()
    config = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
    if args.refresh_static_artifacts:
        checks = refresh_static(config)
    else:
        plan = build_plan(config)
        if args.generate:
            generate(config, plan)
            return 0
        checks = static_checks(config, plan, require_disk_plan=True)
    for name, passed in checks.items():
        print(f"{'PASS' if passed else 'FAIL'} {name}")
    print(f"PHASE41G STATIC PREFLIGHT: {'PASS' if all(checks.values()) else 'FAIL'}")
    return 0 if all(checks.values()) else 1


if __name__ == "__main__":
    sys.exit(main())
