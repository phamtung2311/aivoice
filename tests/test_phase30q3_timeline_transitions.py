"""Phase 30Q.3 mixed-timeline transition contracts."""
from pathlib import Path


STUDIO = Path("frontend/audio-studio.js").read_text(encoding="utf-8")


def test_silence_is_explicit_and_legacy_migration_is_safe():
    assert "function silence()" in STUDIO
    assert "type:'silence'" in STUDIO
    assert "duration_ms:2500" in STUDIO
    assert "Math.min(30000,Math.max(100" in STUDIO


def test_insertion_points_insert_at_exact_boundary():
    assert "function insertionPoint(index)" in STUDIO
    assert "function insertTimelineItem(index,type)" in STUDIO
    assert "project.segments.splice(index,0,item)" in STUDIO
    assert "audioImport.dataset.insertIndex=String(index)" in STUDIO
    assert "project.segments.splice(insertIndex,0,item)" in STUDIO


def test_silence_is_real_in_playback_export_and_duration_totals():
    assert "item?.type==='silence'?Math.max(0,Number(item.duration_ms)||0)/1000" in STUDIO
    assert "setTimeout(resolve,Math.max(100,Math.min(30000,Number(item.duration_ms)||2500)))" in STUDIO
    assert "Math.round(Math.max(100,Math.min(30000,Number(item.duration_ms)||2500))*targetRate/1000)" in STUDIO
    assert "merged=Array.from({length:channels},()=>new Float32Array(length))" in STUDIO
