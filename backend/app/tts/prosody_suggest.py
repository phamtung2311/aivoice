"""Sparse, deterministic Vietnamese prosody suggestions (selection policy v1.1)."""
from dataclasses import asdict, dataclass, field
import re

SUGGESTION_VERSION = "vi_prosody_suggest_v1_1"
PLANNER_VERSION = "vi_prosody_planner_v2"
STRONG_CONNECTORS = ("tuy nhiên", "trong khi đó", "mặt khác", "ngược lại", "nhưng")
REASONING_CONNECTORS = ("vì vậy", "do đó", "bởi vậy")
SOFT_CONNECTORS = ("quan trọng hơn", "nói cách khác", "và đôi khi", "thực tế", "đặc biệt", "có lẽ")
SUBORDINATE_STARTERS = ("khi", "nếu", "vì", "để", "mà", "dù")
ENUMERATION_DETERMINERS = ("một", "những", "các")


@dataclass(frozen=True)
class SuggestionConfig:
    min_clause_words: int = 8
    min_following_words: int = 7
    min_words_between_markers: int = 12
    min_chars_between_markers: int = 68
    selection_score: int = 4
    paragraph_score: int = 10
    strong_connector_score: int = 3
    reasoning_connector_score: int = 2
    long_clause_score: int = 1
    punctuation_sufficiency_penalty: int = 1
    enumeration_penalty: int = 5
    subordinate_penalty: int = 4


CONFIG = SuggestionConfig()


@dataclass(frozen=True)
class BoundaryCandidate:
    position: int
    marker: str
    punctuation: str | None
    context: str
    features: tuple[str, ...] = field(default_factory=tuple)
    reason: str = ""
    score: int = 0


_WORD_RE = re.compile(r"[\wÀ-ỹĐđ]+", re.UNICODE)
_MANUAL_MARKER_RE = re.compile(r"\|{1,3}")
_PROTECTED_TOKEN_RE = re.compile(r"\b\d{1,2}[/:]\d{1,2}(?:[/:]\d{2,4})?\b|\b\d{1,3}(?:[.,]\d{3})+(?:\s?(?:đ|vnđ|vnd))?\b|\b\d+[.,]\d+\b", re.I)


def _word_count(value: str) -> int:
    return len(_WORD_RE.findall(value))


def _sentence_window(text: str, position: int) -> tuple[str, str]:
    start = max(text.rfind(end, 0, position) for end in ".!?\n") + 1
    ends = [found for end in ".!?\n" if (found := text.find(end, position)) >= 0]
    return text[start:position], text[position:min(ends) if ends else len(text)]


def _inside_protected_token(text: str, position: int) -> bool:
    return any(match.start() < position < match.end() for match in _PROTECTED_TOKEN_RE.finditer(text))


def _near_manual_marker(text: str, position: int) -> bool:
    return any(abs(position - match.start()) <= 8 or abs(position - match.end()) <= 8 for match in _MANUAL_MARKER_RE.finditer(text))


def _starts_with(value: str, words: tuple[str, ...]) -> bool:
    return any(re.match(r"\s*" + re.escape(word) + r"\b", value, re.I) for word in words)


def _likely_enumeration(text: str, position: int) -> bool:
    before, after = _sentence_window(text, position)
    left, right = before.rsplit(",", 1)[-1].strip(), after.split(",", 1)[0].strip()
    repeated = any(re.match(r"^" + re.escape(word) + r"\b", left, re.I) and re.match(r"^" + re.escape(word) + r"\b", right, re.I) for word in ENUMERATION_DETERMINERS)
    comma_count = before.count(",") + after.count(",")
    coordinated = comma_count >= 2 and (_word_count(left) <= 6 or _word_count(right) <= 6 or bool(re.match(r"^(và|hoặc|hay|cũng như)\b", right, re.I)))
    return repeated or coordinated


def _connector_matches(text: str):
    for category, words in (("strong", STRONG_CONNECTORS), ("reasoning", REASONING_CONNECTORS), ("soft", SOFT_CONNECTORS)):
        pattern = "|".join(re.escape(item) for item in sorted(words, key=len, reverse=True))
        for match in re.finditer(r"\b(" + pattern + r")\b", text, re.I):
            yield category, match


def analyze_candidates(text: str, config: SuggestionConfig = CONFIG) -> list[BoundaryCandidate]:
    """Stage A: collect structured potential boundaries without selecting them."""
    candidates = []
    for match in re.finditer(r"(?<=\S)(\r?\n\s*\r?\n)", text):
        candidates.append(BoundaryCandidate(match.start(), "|||", "paragraph", "paragraph", ("major_structural_boundary",), "paragraph_boundary", config.paragraph_score))
    for category, match in _connector_matches(text):
        before, after = _sentence_window(text, match.start())
        punctuation = "," if before.rstrip().endswith(",") else None
        features, score = [f"{category}_connector"], 0
        if _word_count(before) >= config.min_clause_words: features.append("long_before"); score += config.long_clause_score
        if _word_count(after) >= config.min_following_words: features.append("long_after"); score += config.long_clause_score
        score += config.strong_connector_score if category == "strong" else config.reasoning_connector_score if category == "reasoning" else 0
        if punctuation: features.append("punctuation_sufficiency"); score -= config.punctuation_sufficiency_penalty
        if not before.strip(): features.append("sentence_initial")
        reason = "contextual_connector" if category in ("strong", "reasoning") else "soft_connector"
        candidates.append(BoundaryCandidate(match.start(), "|", punctuation, "connector", tuple(features), reason, score))
    # Punctuation candidates are retained for explainable suppression only.
    for match in re.finditer(r"[,;:]", text):
        if _inside_protected_token(text, match.end()): continue
        before, after = _sentence_window(text, match.end())
        features, reason, score = ["punctuation_sufficiency"], "punctuation_sufficient", -config.punctuation_sufficiency_penalty
        if match.group() == "," and _likely_enumeration(text, match.start()): features.append("enumeration"); reason = "enumeration"; score -= config.enumeration_penalty
        elif match.group() == "," and _starts_with(after, SUBORDINATE_STARTERS): features.append("subordinate_clause"); reason = "subordinate_clause"; score -= config.subordinate_penalty
        candidates.append(BoundaryCandidate(match.end(), "|", match.group(), "punctuation", tuple(features), reason, score))
    return sorted(candidates, key=lambda item: item.position)


def _suppressed(candidate: BoundaryCandidate, text: str, config: SuggestionConfig) -> str | None:
    if _near_manual_marker(text, candidate.position): return "manual_marker_locked"
    if candidate.context == "paragraph": return None
    if "sentence_initial" in candidate.features: return "sentence_initial_connector"
    if "enumeration" in candidate.features: return "enumeration"
    if "subordinate_clause" in candidate.features: return "subordinate_clause"
    if "soft_connector" in candidate.features: return "weak_soft_connector"
    if candidate.context == "punctuation": return "punctuation_sufficient"
    return "low_score" if candidate.score < config.selection_score else None


def select_candidates(text: str, candidates: list[BoundaryCandidate], config: SuggestionConfig = CONFIG) -> tuple[list[BoundaryCandidate], list[dict]]:
    """Stage B: score/suppress, then apply manual-marker and density guards."""
    selected, suppressed = [], []
    occupied = [match.start() for match in _MANUAL_MARKER_RE.finditer(text)]
    for candidate in sorted(candidates, key=lambda item: (-item.score, item.position)):
        why = _suppressed(candidate, text, config)
        if why is None and any(abs(candidate.position - pos) < config.min_chars_between_markers for pos in occupied): why = "too_close_to_selected_boundary"
        if why is None and occupied and _word_count(text[max(0, candidate.position-config.min_chars_between_markers):candidate.position]) < config.min_words_between_markers: why = "fragment_too_short"
        if why is None: selected.append(candidate); occupied.append(candidate.position)
        else:
            detail = asdict(candidate); detail["suppression_reason"] = why; suppressed.append(detail)
    return sorted(selected, key=lambda item: item.position), sorted(suppressed, key=lambda item: item["position"])


def _insertion(text: str, candidate: BoundaryCandidate) -> str:
    before, after = text[candidate.position-1:candidate.position], text[candidate.position:candidate.position+1]
    if before.isspace(): return candidate.marker + " "
    if after.isspace() or after in "\r\n": return " " + candidate.marker
    return " " + candidate.marker + " "


def suggest_prosody(text: str, config: SuggestionConfig = CONFIG) -> dict:
    if not isinstance(text, str) or not text.strip(): raise ValueError("Text must contain speakable content")
    candidates = analyze_candidates(text, config)
    selected, suppressed = select_candidates(text, candidates, config)
    pieces, metadata, cursor = [], [], 0
    for candidate in selected:
        insertion = _insertion(text, candidate)
        pieces.extend((text[cursor:candidate.position], insertion)); cursor = candidate.position
        detail = asdict(candidate); detail["insertion"] = insertion; metadata.append(detail)
    pieces.append(text[cursor:])
    return {"suggested_script": "".join(pieces), "suggestion_version": SUGGESTION_VERSION, "suggestions": metadata, "debug": {"candidate_count": len(candidates), "suppressed": suppressed}}


_SECTION_TITLE_RE = re.compile(r"(?im)^(?:(?:phần|chương)\s+(?:\d+|[ivxlcdm]+)|mở đầu|kết luận)\s*:[^\n]*")
_ANSWER_STARTERS = ("với tôi", "có lẽ", "đây chính là", "đó là", "thực ra", "câu trả lời")
_PARAGRAPH_TRANSITION_STARTERS = ("và rồi", "đây chính là", "mục tiêu", "để đạt", "cảm ơn", "và có lẽ")


def _sentence_spans(text: str) -> list[tuple[int, int, str]]:
    """Small deterministic sentence scanner that preserves source positions."""
    spans = []
    for match in re.finditer(r"[^.!?\n]+[.!?]+", text):
        value = match.group().strip()
        if value:
            start = match.start() + len(match.group()) - len(match.group().lstrip())
            spans.append((start, match.end(), value))
    return spans


def analyze_context_proposals(text: str, config: SuggestionConfig = CONFIG) -> list[BoundaryCandidate]:
    """Propose only discourse boundaries; Phase30P.1 still validates them."""
    candidates: list[BoundaryCandidate] = []
    for match in _SECTION_TITLE_RE.finditer(text):
        candidates.append(BoundaryCandidate(match.end(), "|||", "section", "semantic", ("section_title", "section_transition"), "section_transition", 10))
    spans = _sentence_spans(text)
    for index, (_start, end, sentence) in enumerate(spans[:-1]):
        next_start, _next_end, next_sentence = spans[index + 1]
        gap = text[end:next_start]
        if "\n\n" in gap and _starts_with(next_sentence, _PARAGRAPH_TRANSITION_STARTERS):
            # Ordinary paragraph changes get a medium candidate, unlike a title.
            candidates.append(BoundaryCandidate(end, "||", "paragraph", "semantic", ("paragraph_transition",), "ordinary_paragraph_transition", 4))
        if sentence.endswith("?") and _starts_with(next_sentence, _ANSWER_STARTERS):
            role_before = "rhetorical_question" if _word_count(sentence) >= 8 else "listener_question"
            candidates.append(BoundaryCandidate(end, "||", "?", "semantic", (role_before, "answer_reveal"), "question_answer_transition", 7))
        elif sentence.endswith("?"):
            candidates.append(BoundaryCandidate(end, "|", "?", "semantic", ("question",), "question_without_reveal", 1))
    return sorted(candidates, key=lambda item: item.position)


def plan_context_aware_prosody(text: str, config: SuggestionConfig = CONFIG) -> dict:
    """Context planner → existing P1 selection/rendering; never rewrites source."""
    if not isinstance(text, str) or not text.strip():
        raise ValueError("Text must contain speakable content")
    try:
        semantic = analyze_context_proposals(text, config)
        selected, suppressed = select_candidates(text, semantic, config)
        pieces, metadata, cursor = [], [], 0
        for candidate in selected:
            insertion = _insertion(text, candidate)
            pieces.extend((text[cursor:candidate.position], insertion)); cursor = candidate.position
            detail = asdict(candidate)
            detail.update({"insertion": insertion, "role_before": candidate.features[0],
                           "role_after": candidate.features[-1], "planner_score": candidate.score,
                           "safety_decision": "accepted"})
            metadata.append(detail)
        pieces.append(text[cursor:])
        return {"suggested_script": "".join(pieces), "suggestion_version": PLANNER_VERSION,
                "planner_mode": "context_aware", "suggestions": metadata,
                "debug": {"semantic_proposal_count": len(semantic), "candidate_count": len(semantic), "suppressed": suppressed}}
    except Exception as error:
        fallback = suggest_prosody(text, config)
        fallback.update({"planner_mode": "v1_1_fallback", "planner_error": str(error)})
        return fallback
