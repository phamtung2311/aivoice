import re
from typing import List


def preprocess_text(text: str) -> str:
    if text is None:
        return ""
    # normalize whitespace, preserve Vietnamese unicode
    # remove control characters except newline
    text = re.sub(r"[\t\r]+", " ", text)
    text = re.sub(r" +", " ", text)
    # strip leading/trailing whitespace on each line but preserve blank lines
    lines = [ln.strip() for ln in text.splitlines()]
    # remove consecutive blank lines
    cleaned_lines = []
    prev_blank = False
    for ln in lines:
        if ln == "":
            if not prev_blank:
                cleaned_lines.append("")
            prev_blank = True
        else:
            cleaned_lines.append(ln)
            prev_blank = False

    return "\n".join(cleaned_lines).strip()


def split_into_sentences(text: str) -> List[str]:
    """Split text into sentence-like chunks using Vietnamese punctuation rules.

    Splits on: ., ?, !, … and newlines. Keeps punctuation at sentence end.
    """
    if not text:
        return []

    # Normalize ellipsis to single char
    text = text.replace("...", "…")

    # split on newline first
    parts = []
    for line in text.split("\n"):
        line = line.strip()
        if not line:
            parts.append("")
            continue

        # use regex to split after punctuation followed by space
        tokens = re.split(r'(?<=[\.!?…])\s+', line)
        for t in tokens:
            t = t.strip()
            if t:
                parts.append(t)
    # remove empty
    return [p for p in parts if p != ""]


def chunk_sentences(sentences: List[str], max_chars: int = 400) -> List[str]:
    """Group sentences into chunks that are at most `max_chars` long.

    Avoid splitting sentences across chunks when possible.
    """
    if max_chars < 1:
        raise ValueError("max_chars must be positive")

    chunks = []
    current = []
    cur_len = 0
    for s in sentences:
        slen = len(s)
        if cur_len + slen + (1 if current else 0) <= max_chars:
            current.append(s)
            cur_len += slen + (1 if current else 0)
        else:
            if current:
                chunks.append(" ".join(current))
            # A model limit must never turn into a mid-token cut.  A token longer
            # than the configured limit is retained whole; the caller can decide
            # whether to reject it, but spoken text must not be silently damaged.
            # Prefer punctuation before a plain whitespace boundary for long
            # sentences, then fall back to whitespace-delimited words.
            if slen > max_chars:
                words = s.split()
                buf = []
                word_index = 0
                while word_index < len(words):
                    w = words[word_index]
                    candidate_length = len(" ".join([*buf, w]))
                    if not buf or candidate_length <= max_chars:
                        buf.append(w)
                        word_index += 1
                        continue

                    # When possible, make the boundary at the latest natural
                    # phrase mark already inside this safe word sequence.
                    punctuation_index = next(
                        (index for index in range(len(buf) - 1, -1, -1)
                         if re.search(r"[,;:]$", buf[index])),
                        None,
                    )
                    if punctuation_index is not None:
                        chunks.append(" ".join(buf[:punctuation_index + 1]))
                        buf = buf[punctuation_index + 1:]
                        continue
                    chunks.append(" ".join(buf))
                    buf = []
                if buf:
                    chunks.append(" ".join(buf))
                current = []
                cur_len = 0
            else:
                current = [s]
                cur_len = slen
    if current:
        chunks.append(" ".join(current))
    return chunks
