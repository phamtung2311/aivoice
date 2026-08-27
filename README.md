# AIVoice 1.0.0

Local Vietnamese AI voice generation and lightweight audio production. AIVoice runs on your machine: text, reference audio, generated WAV files, Voice Lab experiments, and Audio Studio projects stay local.

## Installation

Requirements: Python 3.11+, the included `.venv` (recommended), and FFmpeg for optional M4A reference support.

```bash
python -m venv .venv
.venv/bin/pip install -r requirements.txt
```

Place supported local model files under `models/`. No cloud account or API key is required.

## Running

```bash
.venv/bin/uvicorn backend.main:app --host 127.0.0.1 --port 8000
```

Serve `frontend/` with any local static server, then open its local URL. The frontend expects the API at `http://127.0.0.1:8000`.

## Features

- Local TTS with preset and saved voices
- Voice Lab for reference comparison, quality feedback, and listening evaluation
- Optional Smart Text Processing for dates, money, time, percentages, fractions, decimals, and local brand pronunciations
- Audio Studio for local multi-segment projects, targeted regeneration, sequential playback, and WAV export
- Local history and browser IndexedDB audio persistence
- Dark/light theme, keyboard-visible focus, accessible status messages, and an About dialog

## Screenshots

_Screenshot placeholder: add current captures of the TTS workspace, Voice Lab, and Audio Studio before public distribution._

## Architecture

```text
Frontend (static HTML/CSS/JS)
  ├─ Main TTS → POST /api/tts → local TTS engine → WAV
  ├─ Voice Lab → local reference analysis / controlled samples
  ├─ Smart Text Processing → deterministic local regex + JSON dictionary
  └─ Audio Studio → localStorage metadata + IndexedDB WAV blobs

FastAPI backend
  ├─ local TTS runtime and saved-voice store
  ├─ Voice Lab metadata/report JSON
  └─ no cloud calls or external AI services
```

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

- Release-candidate manual accessibility and browser verification
- Additional deterministic pronunciation dictionary entries
- Optional project import/export metadata workflow

## License

Review the licenses of the included model/runtime and dependencies before redistribution.
