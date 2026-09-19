# AIVoice 1.0.0

**A privacy-first Vietnamese AI voice studio that runs entirely on your computer.**

AIVoice combines local text-to-speech, reusable voice profiles, a reference-audio lab, and a multi-segment production timeline. Text, recordings, generated WAV files, and project data stay on the local machine—no account or cloud API key required.

> Portfolio project · FastAPI · vanilla JavaScript · local ML inference · audio processing

## Why this project

Most TTS demos stop at a text box and a play button. AIVoice explores the engineering needed around the model: Vietnamese text normalization, bounded inference concurrency, reference-audio validation, resumable long-form jobs, persistent browser audio, and a practical editing workflow.

### Highlights

- **Production-oriented API:** validation, safe upload limits, local-only CORS, concurrency control, job progress, cancellation, resume, and idempotency.
- **Vietnamese speech pipeline:** deterministic normalization for dates, time, money, percentages, fractions, decimals, and a custom pronunciation dictionary.
- **Long-form podcast workflow:** semantic chunk planning, inspectable progress, disk-backed recovery, targeted segment regeneration, and WAV export.
- **Privacy by design:** models and voice data remain local; personal biometric recordings are excluded from version control.
- **Quality discipline:** 251 collected checks cover API behavior, NLP, audio jobs, voice profiles, frontend regressions, and production-voice parity.

## Project map

`backend/` runtime · `frontend/` web UI · `assets/production_voices/` final identities · `docs/` restore records · `requirements/` dependency snapshots · `scripts/` utilities · `tests/` tests · `backups/` private backup · `experiments/` historical research.

Production voice set: **AIVoice Podcast Voice Set v1** — `podcast_deep_warm`, `podcast_warm_storyteller`, `podcast_soft_baritone`.

## Installation

Requirements: Python 3.11+ and FFmpeg (required for the Podcast Brand Voice final pass and M4A imports).

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Place supported local model files under `models/`. No cloud account or API key is required.

## Running

Run the backend:

```bash
uvicorn backend.main:app --host 127.0.0.1 --port 8000
```

In a second terminal, serve the frontend:

```bash
python -m http.server 5173 --bind 127.0.0.1 --directory frontend
```

Open [http://127.0.0.1:5173](http://127.0.0.1:5173). API documentation is available at [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs).

Verify a checkout without generating audio:

```bash
python scripts/check_project.py
pytest
```

## Screenshots

The repository intentionally does not commit private voice recordings or generated audio. Before publishing the portfolio, capture the TTS workspace, Voice Lab, and Audio Studio using non-sensitive demo content and place the images in `docs/screenshots/`.

## Features

- Local TTS with preset and saved voices
- Voice Lab for reference comparison, quality feedback, and listening evaluation
- Optional Smart Text Processing for dates, money, time, percentages, fractions, decimals, and local brand pronunciations
- Audio Studio for local multi-segment projects, targeted regeneration, sequential playback, and WAV export
- Local history and browser IndexedDB audio persistence
- One-click **🎙️ Podcast Brand Voice** with dynamic semantic planning, long-form recovery, natural V2 breathing pauses, and final 0.98x tempo
- Dark/light theme, keyboard-visible focus, accessible status messages, and an About dialog

## Architecture

See [the code maintenance map](docs/CODE_MAINTENANCE.md) for module responsibilities,
refactor validation results, and remaining maintenance work.

```text
Frontend (static HTML/CSS/JS)
  ├─ Main TTS → POST /api/tts → local TTS engine → WAV
  ├─ Voice Lab → local reference analysis / controlled samples
  ├─ Smart Text Processing → deterministic local regex + JSON dictionary
  └─ Audio Studio → localStorage metadata + IndexedDB WAV blobs

FastAPI backend
  ├─ validation, normalization and bounded inference
  ├─ local TTS runtime and saved-voice store
  ├─ resumable long-audio job service
  └─ Voice Lab metadata and quality analysis
```

The static frontend deliberately avoids a build tool: it can be audited and served with Python's standard library. Generated audio blobs live in IndexedDB; lightweight project metadata lives in localStorage. The backend serializes model inference by default and writes completed long-form chunks to disk so an interrupted job can be resumed.

## API at a glance

| Endpoint | Purpose |
|---|---|
| `GET /api/health` | Runtime and model readiness |
| `GET /api/voices` | Built-in, production, and locally saved voices |
| `POST /api/tts` | Short-form/local TTS generation |
| `POST /api/tts/prosody/suggest` | Deterministic Vietnamese pause planning |
| `POST /api/long-audio/jobs` | Start an inspectable long-form render |
| `GET /api/long-audio/jobs/{id}` | Read progress and chunk state |
| `POST /api/long-audio/jobs/{id}/resume` | Reuse verified chunks after interruption |

See the interactive OpenAPI page at `/docs` for complete schemas.

## Testing

`pytest` is intentionally scoped to `tests/`; research benchmarks under `experiments/` are not production tests and may require separate model environments.

```bash
python scripts/check_project.py   # fast structure/import/API smoke check
pytest -q                         # complete automated suite
```

The test suite uses fakes and temporary stores where possible, so most checks do not require an expensive synthesis run.

## Troubleshooting

- **Backend unavailable:** confirm Uvicorn is running on port 8000 and refresh the page.
- **No voices listed:** verify local model assets under `models/` and check the backend terminal output.
- **M4A reference fails:** install FFmpeg or use WAV/MP3.
- **Audio history unavailable:** close older AIVoice tabs, reload, and allow browser storage for the local origin.
- **Audio Studio export fails:** generate each segment and ensure ready segments use one engine sample rate.

## FAQ

**Is data uploaded to a cloud service?** No. AIVoice is designed for local operation.

**Does Smart Text Processing change my original text?** No. It creates a deterministic spoken form only for the TTS request and can be turned off in Advanced settings.

**Can Audio Studio regenerate one segment only?** Yes. Each segment has its own text, voice, settings, WAV blob, and Generate/Regenerate action.

**Where do I add a brand pronunciation?** Edit `data/nlp/custom_dictionary.json`; changes are picked up locally.

## Roadmap

- Add public-safe screenshots and a short product demo
- Complete browser accessibility and long-form listening QA
- Additional deterministic pronunciation dictionary entries
- Optional project import/export metadata workflow

## License

Source code is provided as a portfolio project. Model weights, voice assets, and third-party runtimes may have separate licenses; review [the production voice license notes](docs/PRODUCTION_VOICE_LICENSE.md) before redistribution or commercial use.
