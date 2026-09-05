"""Frozen Phase 43A experimental podcast identities (raw VieNeu V3 Turbo)."""
from __future__ import annotations
import hashlib, json
from pathlib import Path
import numpy as np

VOICE_ASSET_SHA256 = "574e6acf03823c4cafdc43f106731ce5fce6de30228fe383831b8b9064ee0bd8"
_ROOT = Path(__file__).resolve().parents[3]
_ASSETS = _ROOT / 'assets' / 'production_voices'
ANCHOR = "Thanh Bình"
PODCAST_VOICES = {
 "podcast_deep_warm": {"display_name":"Podcast — Deep Warm","phase43a_voice":"01","weights":{"Thanh Bình":.70,"Phạm Tuyên":.20,"Minh Đức":.10},"embedding_sha256":"7a132f56cb1411ca3db676f51a1a0382330473c34db31e5c38cf321485fbd0a7"},
 "podcast_warm_storyteller": {"display_name":"Podcast — Warm Storyteller","phase43a_voice":"06","weights":{"Thanh Bình":.10,"Phạm Tuyên":.45,"Minh Đức":.45},"embedding_sha256":"1c468e5f518241ab291ee5e7a70b3e3a7acd8e2ed6e778839850835d08260d24"},
 "podcast_soft_baritone": {"display_name":"Podcast — Soft Baritone","phase43a_voice":"07","weights":{"Thanh Bình":.65,"Phạm Tuyên":.10,"Minh Đức":.25},"embedding_sha256":"36de71e82728334ecb53fa6d855a1f9a22e112fc89b76d0a825c3c4aff6f3940"},
}
def _hash(a): return hashlib.sha256(np.ascontiguousarray(a).tobytes()).hexdigest()
def resolve_podcast_voice(voice_id: str) -> dict:
    if voice_id not in PODCAST_VOICES: raise ValueError(f"Unknown production podcast voice: {voice_id}")
    meta=PODCAST_VOICES[voice_id]
    emb=np.load(_ASSETS/(voice_id+'_embedding.npy'),allow_pickle=False).astype(np.float32,copy=False)
    if emb.shape!=(192,) or _hash(emb)!=meta['embedding_sha256']: raise RuntimeError('Frozen podcast embedding verification failed')
    codes=np.load(_ASSETS/'thanh_binh_reference_codes.npy',allow_pickle=False)
    if hashlib.sha256((_ASSETS/'thanh_binh_reference_codes.npy').read_bytes()).hexdigest()!='fe8f8e3e1766a7954595fa3a355e46aca8c3e27be4aba4bb1db8d9b60a960aa5': raise RuntimeError('Frozen reference-code anchor verification failed')
    return {'speaker_emb':emb,'codes':codes}
