# Phase 22.2 §6/§8: byte-level + phoneme-level comparison of
#   A) pre-Phase-22 preprocess (inline legacy copy from git history)
#   B) current preprocess_text()
#   C) raw input (no preprocessing)
# on the controlled diagnostic sentence. NO model load, NO inference.
import json
import re
import sys
import unicodedata

sys.path.insert(0, ".")

from backend.app.tts.text import preprocess_text as current_preprocess

SENTENCE = "Mọi người đang ở đây."


def legacy_preprocess(text):
    """Byte-for-byte copy of the pre-Phase-22 backend/app/tts/text.py logic."""
    if text is None:
        return ""
    text = re.sub(r"[\t\r]+", " ", text)
    text = re.sub(r" +", " ", text)
    lines = [ln.strip() for ln in text.splitlines()]
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


def fingerprint(label, value):
    return {
        "label": label,
        "repr": repr(value),
        "utf8_bytes_sha_len": (len(value.encode("utf-8")), len(value)),
        "codepoints": [f"U+{ord(c):04X}" for c in value],
    }


def main():
    variants = {
        "raw": SENTENCE,
        "raw_nfd": unicodedata.normalize("NFD", SENTENCE),
        "legacy_pre": legacy_preprocess(SENTENCE),
        "current_pre": current_preprocess(SENTENCE),
        "legacy_nfd": legacy_preprocess(unicodedata.normalize("NFD", SENTENCE)),
        "current_nfd": current_preprocess(unicodedata.normalize("NFD", SENTENCE)),
    }

    result = {"fingerprints": [fingerprint(k, v) for k, v in variants.items()]}

    # Byte/semantic equality of the exact diagnostic sentence.
    result["legacy_eq_current"] = variants["legacy_pre"] == variants["current_pre"]
    result["legacy_eq_raw"] = variants["legacy_pre"] == SENTENCE
    result["current_eq_raw"] = variants["current_pre"] == SENTENCE

    # Downstream equivalence through the real phonemizer (no inference).
    try:
        from sea_g2p import SEAPipeline

        pipe = SEAPipeline(lang="vi")
        phones = {name: pipe.run(text, punc_norm=True) for name, text in variants.items()}
        result["phonemes"] = phones
        result["phonemes_all_equal"] = len(set(phones.values())) == 1
    except Exception as exc:
        result["phonemes"] = {"error": repr(exc)}
        result["phonemes_all_equal"] = None

    # Legacy preprocessing applied to poisoned input, for contrast (documented
    # in Phase 22): shows the only behavioral delta of the new layer.
    poisoned = "Mọi ng\u200Bười đang ở đây."
    result["poisoned_legacy"] = legacy_preprocess(poisoned)
    result["poisoned_current"] = current_preprocess(poisoned)

    with open("/tmp/p222_textprobe.json", "w", encoding="utf-8") as handle:
        json.dump(result, handle, ensure_ascii=False, indent=1)
    print(json.dumps({k: v for k, v in result.items() if k not in ("fingerprints", "phonemes")},
                     ensure_ascii=False, indent=1))
    if isinstance(result.get("phonemes"), dict) and "error" not in result["phonemes"]:
        print("phonemes_current:", result["phonemes"]["current_pre"])
        print("phonemes_all_equal:", result["phonemes_all_equal"])


if __name__ == "__main__":
    main()
