Local static frontend for the Local TTS backend.

Use `http://localhost:5173` as the canonical frontend origin so browser history
and IndexedDB stay in one origin-scoped storage area:

```bash
python -m http.server 5173 --bind localhost -d frontend
```

Then open: http://localhost:5173 in your browser. The UI calls the backend at http://127.0.0.1:8000.
