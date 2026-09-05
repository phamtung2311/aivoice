# Phase 46 project housekeeping audit

| Path | Category | Runtime use | Move/delete | Action |
|---|---|---|---|---|
| `backend/`, `frontend/` | Production runtime | Yes | No | Protected |
| `assets/production_voices/`, `requirements/`, verifier | Production assets | Yes | No | Protected |
| `backups/`, Phase 45 record, production docs | Production record | Yes | No | Protected |
| `tests/`, `data/`, `models/` | Active/runtime data | Potentially | No | Retained |
| Historical experiment folders | Historical research | Lineage/docs | No automatic move | Explorer-hidden only |
| `__pycache__/`, `*.pyc`, `.pytest_cache/` | Reproducible cache | No | Yes | Remove |
| Existing dirty/untracked files | Unknown | Unknown | No | Untouched |

Worktree was already substantially dirty on `main`; no reset, checkout, clean, experiment move, or deletion of user artifacts was performed. Restore hidden Explorer folders by removing rules from `.vscode/settings.json`.
