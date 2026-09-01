from collections import Counter
from pathlib import Path

from backend.app.tts.prosody import parse_prosody_script
from backend.app.tts.prosody_suggest import SUGGESTION_VERSION, analyze_candidates, suggest_prosody


FIXTURE = Path(__file__).parent / "fixtures" / "phase30p1_real_passage.txt"


def _reconstruct_source(proposal):
    script = proposal["suggested_script"]
    prior = 0
    removals = []
    for item in proposal["suggestions"]:
        start = item["position"] + prior
        removals.append((start, len(item["insertion"])))
        prior += len(item["insertion"])
    for start, length in reversed(removals):
        script = script[:start] + script[start + length:]
    return script


def test_repeated_mot_enumeration_is_suppressed():
    text = "Có khi nó bắt đầu từ một thói quen nhỏ, một người mà chúng ta tình cờ gặp, một câu nói vô tình nghe được hoặc một buổi tối yên tĩnh."
    proposal = suggest_prosody(text)
    assert proposal["suggestions"] == []
    assert "enumeration" in {item["suppression_reason"] for item in proposal["debug"]["suppressed"]}


def test_repeated_nhung_and_coordinated_lists_are_suppressed():
    for text in (
        "Mỗi ngày có những công việc quen thuộc, những cuộc trò chuyện quen thuộc và những suy nghĩ bình thường kéo dài.",
        "Trong phòng có sách, nhạc và trà, nhưng chúng ta vẫn cần nói thêm đủ nhiều để hiểu nhau.",
        "Ta có thể chọn sách, nhạc hoặc trà, nhưng phần quan trọng là còn đủ thời gian để trò chuyện cùng nhau.",
    ):
        proposal = suggest_prosody(text)
        assert not any(item["context"] == "punctuation" for item in proposal["suggestions"])


def test_subordinate_commas_and_semicolon_colon_are_punctuation_sufficient():
    for text in (
        "Một buổi tối yên tĩnh, khi chúng ta có đủ thời gian để suy nghĩ về những điều quan trọng, thường đã đủ tự nhiên.",
        "Chúng ta tiếp tục quan sát, mà không cần vội vàng thêm một nhịp nghỉ nhân tạo vào câu nói này.",
        "Đó là một phần quan trọng của hành trình; cũng có những thứ cần được giữ nguyên trong câu chuyện này.",
        "Điều cần nhớ là: punctuation đã tạo một ranh giới rõ ràng cho người nghe trong trường hợp này.",
    ):
        proposal = suggest_prosody(text)
        assert proposal["suggestions"] == []


def test_substantial_internal_contrast_is_selected_but_sentence_initial_is_not():
    contrast = "Những suy nghĩ tưởng như rất bình thường, nhưng khi tất cả liên tục nối tiếp nhau thì chúng ta vẫn cần thời gian để nhìn lại chính mình."
    selected = suggest_prosody(contrast)
    assert len(selected["suggestions"]) == 1
    assert selected["suggestions"][0]["reason"] == "contextual_connector"
    initial = suggest_prosody("Tuy nhiên, nhìn lại quá khứ không có nghĩa là chúng ta phải tiếc nuối về những lựa chọn đã qua.")
    assert initial["suggestions"] == []


def test_soft_connector_and_long_sentence_without_transition_do_not_force_marker():
    soft = "Và có lẽ chính những khoảnh khắc rất bình thường như vậy lại khiến một người dần hiểu rõ hơn mình thực sự muốn điều gì."
    long_plain = "Khi mọi người cùng ngồi lại để xem xét các thông tin đã có từ nhiều nguồn khác nhau và cố gắng đặt từng chi tiết vào đúng bối cảnh của nó, chúng ta có thể hiểu vấn đề rõ hơn mà không cần thêm một chỉ dẫn nghỉ nào."
    assert suggest_prosody(soft)["suggestions"] == []
    assert suggest_prosody(long_plain)["suggestions"] == []


def test_canonical_automatic_spacing_and_manual_marker_preservation():
    proposal = suggest_prosody("Chúng ta đã suy nghĩ rất lâu về câu chuyện này, nhưng điều quan trọng là vẫn còn thời gian để lắng nghe nhau.")
    assert ", | nhưng" in proposal["suggested_script"]
    assert ",|" not in proposal["suggested_script"]
    manual = "Chúng ta giữ nhịp này | nhưng vẫn tiếp tục nói đủ dài để không bị tự động thay đổi."
    assert suggest_prosody(manual)["suggested_script"] == manual


def test_automatic_insertions_reconstruct_source_and_parser_accepts_script():
    source = "Chúng ta đã suy nghĩ rất lâu về câu chuyện này, nhưng điều quan trọng là vẫn còn thời gian để lắng nghe nhau.\n\nĐoạn sau bắt đầu một ý khác."
    proposal = suggest_prosody(source)
    assert _reconstruct_source(proposal) == source
    parse_prosody_script(proposal["suggested_script"])


def test_real_five_paragraph_regression_is_sparse_and_explainable():
    source = FIXTURE.read_text(encoding="utf-8")
    proposal = suggest_prosody(source)
    selected_reasons = [item["reason"] for item in proposal["suggestions"]]
    suppression = Counter(item["suppression_reason"] for item in proposal["debug"]["suppressed"])
    assert proposal["suggestion_version"] == SUGGESTION_VERSION
    assert len(proposal["suggestions"]) == 7
    assert selected_reasons.count("paragraph_boundary") == 4
    assert selected_reasons.count("contextual_connector") == 3
    assert "những công việc quen thuộc, |" not in proposal["suggested_script"]
    assert "một thói quen nhỏ, |" not in proposal["suggested_script"]
    assert "một người mà chúng ta tình cờ gặp, |" not in proposal["suggested_script"]
    assert "một buổi tối yên tĩnh, | khi" not in proposal["suggested_script"]
    assert suppression["enumeration"] >= 1
    assert proposal == suggest_prosody(source)
    assert len(analyze_candidates(source)) == proposal["debug"]["candidate_count"]
