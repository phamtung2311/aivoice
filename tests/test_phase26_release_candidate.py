"""Phase 26 release-candidate UI, version, and documentation contracts."""

from pathlib import Path

from backend.main import APP_VERSION, BUILD_DATE, health


ROOT = Path('.')
APP = (ROOT / 'frontend' / 'app.js').read_text(encoding='utf-8')
HTML = (ROOT / 'frontend' / 'index.html').read_text(encoding='utf-8')
STUDIO_HTML = (ROOT / 'frontend' / 'audio-studio.html').read_text(encoding='utf-8')
CSS = (ROOT / 'frontend' / 'styles.css').read_text(encoding='utf-8')
README = (ROOT / 'README.md').read_text(encoding='utf-8')


class Engine:
    model_name = 'local-model'


def test_version_metadata_is_exposed_without_touching_model_behavior():
    assert APP_VERSION == '1.0.0'
    assert BUILD_DATE == '2026-08-27'
    payload = health(Engine())
    assert payload['version'] == '1.0.0'
    assert payload['build_date'] == '2026-08-27'


def test_about_dialog_and_accessible_workspace_tabs_exist():
    assert 'id="aboutDialog"' in HTML
    assert 'id="aboutBtn"' in HTML
    assert 'aria-modal="true"' in HTML
    assert 'href="audio-studio.html"' in HTML
    assert 'aria-controls="mainWorkspace"' in HTML
    assert 'function updateAboutDetails' in APP
    assert 'aboutDialog?.showModal()' in APP


def test_release_polish_keeps_visible_status_and_keyboard_focus_contracts():
    assert 'id="studioStatus"' in STUDIO_HTML
    assert 'function setStudioStatus' in APP
    assert '`Đang tạo Segment ${index+1}...`' in APP
    assert "'Đã xuất WAV.'" in APP
    assert ':focus-visible{' in CSS
    assert 'button:disabled{' in CSS
    assert '.aboutDialog' in CSS


def test_readme_contains_release_operator_documentation():
    for heading in ('## Installation', '## Running', '## Features', '## Screenshots', '## Architecture', '## Troubleshooting', '## FAQ', '## Roadmap'):
        assert heading in README
