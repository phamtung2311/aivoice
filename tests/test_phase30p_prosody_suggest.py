import re

from backend import main as main_mod
from backend.app.tts.prosody import parse_prosody_script
from backend.app.tts.prosody_suggest import PLANNER_VERSION, SUGGESTION_VERSION, suggest_prosody


def _markers(script):
    return re.findall(r"\|{1,3}", script)


def test_short_sentence_gets_no_pointless_marker():
    proposal = suggest_prosody("Hôm nay trời đẹp.")
    assert proposal["suggested_script"] == "Hôm nay trời đẹp."
    assert proposal["suggestions"] == []


def test_comma_heavy_sentence_is_not_mechanically_marked():
    source = "Trong căn phòng nhỏ, có sách, có nhạc, có trà, và có những cuộc trò chuyện ngắn vào mỗi buổi tối."
    proposal = suggest_prosody(source)
    assert len(_markers(proposal["suggested_script"])) < source.count(",")


def test_long_connector_clause_gets_a_selective_explainable_boundary():
    source = "Chúng ta đã đi qua một ngày rất dài với nhiều cuộc họp và nhiều suy nghĩ chưa kịp gọi tên, nhưng điều quan trọng là vẫn còn thời gian để ngồi lại và lắng nghe nhau."
    proposal = suggest_prosody(source)
    assert "nhưng" in proposal["suggested_script"]
    assert any(item["reason"] == "contextual_connector" for item in proposal["suggestions"])
    assert len(proposal["suggestions"]) == 1


def test_paragraph_boundary_is_major_but_not_terminal():
    source = "Đoạn đầu là một suy nghĩ đủ dài để được giữ nguyên.\n\nĐoạn sau mở ra một chủ đề khác."
    proposal = suggest_prosody(source)
    assert "|||\n\n" in proposal["suggested_script"]
    assert proposal["suggested_script"].endswith("khác.")
    assert proposal["suggestions"][0]["reason"] == "paragraph_boundary"


def test_numbers_dates_times_and_money_are_not_split_or_corrupted():
    source = "Lúc 20:45 ngày 10/05/2026, chi phí là 1.250.000đ, nhưng nhóm vẫn dành thêm thời gian để kiểm tra từng chi tiết quan trọng trước khi quyết định."
    proposal = suggest_prosody(source)
    for token in ("20:45", "10/05/2026", "1.250.000đ"):
        assert token in proposal["suggested_script"]
    assert "20:|45" not in proposal["suggested_script"]
    assert "1.|250" not in proposal["suggested_script"]


def test_manual_markers_are_preserved_and_result_is_parser_valid():
    source = "Chúng ta giữ nhịp này | nhưng vẫn cần nói thêm đủ nhiều để hệ thống không tự chen vào gần lựa chọn của người dùng."
    proposal = suggest_prosody(source)
    assert " | " in proposal["suggested_script"]
    assert "||||" not in proposal["suggested_script"]
    parse_prosody_script(proposal["suggested_script"])


def test_is_deterministic_insert_only_and_parser_accepts_result():
    source = "Có những điều cần nói thật chậm, vì vậy chúng ta chọn một nhịp vừa đủ để người nghe theo kịp."
    first, second = suggest_prosody(source), suggest_prosody(source)
    assert first == second
    assert first["suggestion_version"] == SUGGESTION_VERSION
    # This source has no manual markers, so removing proposed insertions exactly
    # reconstructs it; suggestions never rewrite source characters.
    assert re.sub(r"\|{1,3}", "", first["suggested_script"]) == source
    parse_prosody_script(first["suggested_script"])


def test_suggestion_endpoint_exposes_separate_versions_and_explainability():
    response = main_mod.tts_prosody_suggest(main_mod.ProsodySuggestionRequest(
        text="Đoạn đầu đủ dài để trở thành một ý riêng.\n\nĐoạn sau bắt đầu một ý khác."
    ))
    assert response["prosody_version"] == "podcast_prosody_v1"
    assert response["suggestion_version"] == PLANNER_VERSION
    assert response["planner_mode"] == "context_aware"
    assert response["suggestions"] == []
