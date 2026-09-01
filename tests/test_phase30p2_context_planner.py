from pathlib import Path
import re

from backend.app.tts.prosody import parse_prosody_script
from backend.app.tts.prosody_suggest import PLANNER_VERSION, plan_context_aware_prosody, suggest_prosody


FIXTURE = Path(__file__).parent / "fixtures" / "phase30p2_real_podcast.txt"


def test_section_is_stronger_than_an_ordinary_paragraph_transition():
    text = "Phần 1: Mở đầu\n\nĐây là phần mở đầu đủ dài để dẫn vào câu chuyện với nhiều chi tiết bình tĩnh, giúp người nghe hiểu rõ bối cảnh trước khi chuyển ý.\n\nVà rồi chúng ta chuyển sang một ý khác có liên quan."
    proposal = plan_context_aware_prosody(text)
    assert proposal["suggestions"][0]["marker"] == "|||"
    assert any(item["marker"] == "||" and item["reason"] == "ordinary_paragraph_transition" for item in proposal["suggestions"])


def test_question_answer_and_setup_reveal_are_contextual_not_question_mark_rules():
    text = "Không biết hôm nay của bạn thế nào? Với tôi, đó là một câu chuyện nhiều âm thanh và suy nghĩ. Bạn khỏe không? Tôi khỏe."
    proposal = plan_context_aware_prosody(text)
    assert len(proposal["suggestions"]) == 1
    item = proposal["suggestions"][0]
    assert item["marker"] == "||" and item["reason"] == "question_answer_transition"
    assert item["role_before"] in ("listener_question", "rhetorical_question")


def test_manual_markers_and_source_reconstruction_are_safe():
    text = "Phần 1: Mở đầu\n\nChúng ta giữ nhịp này | rồi mới nói tiếp về một câu chuyện đủ dài để phân tích."
    proposal = plan_context_aware_prosody(text)
    assert " | " in proposal["suggested_script"]
    assert "||||" not in proposal["suggested_script"]
    parse_prosody_script(proposal["suggested_script"])


def test_real_podcast_fixture_has_varied_semantic_output_and_preserves_lists():
    text = FIXTURE.read_text(encoding="utf-8")
    p1, p2 = suggest_prosody(text), plan_context_aware_prosody(text)
    markers = re.findall(r"\|{1,3}", p2["suggested_script"])
    assert p2["suggestion_version"] == PLANNER_VERSION
    assert p2["planner_mode"] == "context_aware"
    assert markers.count("|||") == 4
    assert markers.count("||") >= 3
    assert "Tiếng còi xe inh ỏi trên những ngã tư kẹt cứng, |" not in p2["suggested_script"]
    assert "không vấp váp, |" not in p2["suggested_script"]
    assert any(item["reason"] == "question_answer_transition" for item in p2["suggestions"])
    assert len(p1["suggestions"]) != len(p2["suggestions"])
    assert p2 == plan_context_aware_prosody(text)
    parse_prosody_script(p2["suggested_script"])


def test_context_planner_leaves_v1_1_safety_engine_available_as_fallback():
    fallback = suggest_prosody("Một câu ngắn, không cần thêm can thiệp.")
    assert fallback["suggestion_version"] == "vi_prosody_suggest_v1_1"
