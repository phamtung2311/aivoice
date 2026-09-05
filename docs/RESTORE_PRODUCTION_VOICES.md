# Restore AIVoice Podcast Voice Set v1

1. Copy/clone the project and private `backups/aivoice_production_voice_set_v1.tar.zst`; verify its SHA256 from the Phase 45 report, then extract with `tar --zstd -xf`.
2. Install Python 3.14, FFmpeg/libsndfile, then create `.venv`.
3. Install `requirements/production_voice_requirements.txt`. The known-good production environment was Python **3.14.7**; do not assume another 3.14.x release is equivalent. Reproduce it first before changing dependency versions.
4. Restore the exact VieNeu V3 Turbo model assets identified in `MODEL_ASSET_MANIFEST.sha256`.
5. Restore `assets/production_voices/`; run `PYTHONPATH=. .venv/bin/python scripts/verify_production_voice_bundle.py`.
6. Start the backend with `.venv/bin/uvicorn backend.main:app --host 127.0.0.1 --port 8000` and frontend with `python -m http.server 5173 --bind localhost -d frontend`.
7. Confirm `/api/voices` lists the three stable IDs. Render the shared smoke text and compare by ear with the stored reference audio. VieNeu has no supported deterministic seed, so bit identity is not expected.
