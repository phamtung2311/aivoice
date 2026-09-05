"""Data definitions for validated local Special Voices.

Definitions contain presentation metadata and the development reference location;
the reusable biometric-like profile itself remains in the local voice store.
"""
from __future__ import annotations

from pathlib import Path


SPECIAL_VOICES = {
    "podcast_brand_voice_v1": {
        "id": "podcast_brand_voice_v1",
        "display_name": "🎙️ Podcast Brand Voice",
        "category": "Podcast / Brand Voice",
        "status": "candidate",
        "is_final_brand_voice": False,
        "description": "Giọng podcast dài — nhịp tự nhiên, nhấn trọng tâm, tối ưu nghe lâu.",
        "is_special": True,
        "special_type": "podcast_brand_voice",
        "recommended_use": "Long-form Vietnamese podcast, philosophy, psychology, life lessons, reflective narration.",
        "speaker": "Synthetic Candidate 03",
        "source_voice_id": "podcast_synthetic_candidate_03",
        "prosody_profile": "phase41e_v3_semantic_focus",
        "tempo": 0.98,
        "pause_profile": "phase41h_v2",
        "pipeline_version": "podcast_brand_voice_v1",
        # Logical rendering profile only. It resolves to Candidate 03 at runtime
        # and never duplicates or rewrites canonical speaker arrays.
        "baseline_dir": Path("experiments/brand_voice_phase41b/baseline/PODCAST_SYNTHETIC_CANDIDATE_03"),
        "speaker_embedding_path": Path("experiments/brand_voice_phase41b/baseline/PODCAST_SYNTHETIC_CANDIDATE_03/speaker_emb.npy"),
        "reference_codes_path": Path("experiments/brand_voice_phase41b/baseline/PODCAST_SYNTHETIC_CANDIDATE_03/reference_codes.npy"),
    },
    "review_film": {
        "id": "review_film",
        "display_name": "🎬 Review Film",
        "category": "Special Voice",
        "description": "Giọng kể chuyện chuyên cho nội dung review phim và tóm tắt cốt truyện.",
        "is_special": True,
        "special_type": "review_film",
        "recommended_use": "Review phim, tóm tắt cốt truyện và kể chuyện.",
        "reference_path": Path("experiments/special_voice_review/reference_audio/review_film.wav"),
    },
    "podcast_brand_beta": {
        "id": "podcast_brand_beta",
        "display_name": "🎙️ Podcast Brand (Beta)",
        "category": "Special Voice",
        "description": "Giọng podcast ấm, trò chuyện, dùng thử cho nội dung dài. Beta: chưa phải brand voice chính thức.",
        "is_special": True,
        "special_type": "podcast",
        "recommended_use": "Podcast, narration và nội dung trò chuyện dài.",
        # This is the canonical M-A source keeper. Provisioning below reuses
        # its verified native VieNeu embedding/codes, never regenerates it.
        "reference_path": Path("experiments/special_voice_podcast/keepers/phase30m_04/qwen_source.wav"),
        "speaker_embedding_path": Path("experiments/special_voice_podcast/keepers/phase30m_04/speaker_emb.npy"),
        "reference_codes_path": Path("experiments/special_voice_podcast/keepers/phase30m_04/reference_codes.npy"),
    },
    "podcast_candidate_b": {
        "id": "podcast_candidate_b",
        "display_name": "🎙️ Podcast Candidate B (Thử nghiệm)",
        "category": "Podcast / Experimental",
        "status": "candidate",
        "is_final_brand_voice": False,
        "description": "Giọng thử nghiệm Phase 40B từ tổ hợp 0.75 Phạm Tuyên + 0.25 Thanh Bình. Chưa phải Brand Voice chính thức, chờ đánh giá người nghe.",
        "is_special": True,
        "special_type": "podcast_candidate",
        "recommended_use": "Nghe thử và đánh giá; chưa dùng cho sản xuất.",
        # Canonical Phase 40B Candidate B baseline (immutable .npy files).
        # The profile stored in data/voices/voices.json is a rounded UI/library
        # copy and is NEVER used as a source for cross-text validation.
        "baseline_dir": Path("experiments/brand_voice_phase40b/baseline/PODCAST_CANDIDATE_B_BASELINE"),
        "speaker_embedding_path": Path("experiments/brand_voice_phase40b/baseline/PODCAST_CANDIDATE_B_BASELINE/speaker_emb.npy"),
        "reference_codes_path": Path("experiments/brand_voice_phase40b/baseline/PODCAST_CANDIDATE_B_BASELINE/reference_codes.npy"),
        "baseline_manifest_path": Path("experiments/brand_voice_phase40b/baseline/PODCAST_CANDIDATE_B_BASELINE/manifest.json"),
    },
    "podcast_synthetic_candidate_03": {
        "id": "podcast_synthetic_candidate_03",
        "display_name": "🎙️ Synthetic Podcast Candidate 03",
        "category": "Podcast / Experimental",
        "status": "candidate",
        "is_final_brand_voice": False,
        "description": "Synthetic Podcast Candidate 03 — frozen from Phase 41A blind audition (KEEP).",
        "is_special": True,
        "special_type": "synthetic_podcast_candidate",
        "recommended_use": "Podcast / YouTube thử nghiệm; đã vượt blind human audition.",
        "baseline_dir": Path("experiments/brand_voice_phase41b/baseline/PODCAST_SYNTHETIC_CANDIDATE_03"),
        "speaker_embedding_path": Path("experiments/brand_voice_phase41b/baseline/PODCAST_SYNTHETIC_CANDIDATE_03/speaker_emb.npy"),
        "reference_codes_path": Path("experiments/brand_voice_phase41b/baseline/PODCAST_SYNTHETIC_CANDIDATE_03/reference_codes.npy"),
        "baseline_manifest_path": Path("experiments/brand_voice_phase41b/baseline/PODCAST_SYNTHETIC_CANDIDATE_03/manifest.json"),
    },
}
