"""Data definitions for validated local Special Voices.

Definitions contain presentation metadata and the development reference location;
the reusable biometric-like profile itself remains in the local voice store.
"""
from __future__ import annotations

from pathlib import Path


SPECIAL_VOICES = {
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
}
