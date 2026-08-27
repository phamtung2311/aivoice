# Dev-only Phase 22 diagnostic probe. Controlled corpus words only; prints no
# private text beyond the fixed word list below. No model load, pure text tools.
import json
import unicodedata

from sea_g2p import SEAPipeline

WORDS = [
    "người",
    "mọi người",
    "cười",
    "tươi",
    "lười",
    "rượu",
    "mượn",
    "nguyễn",
    "nghiêng",
    "khuỷu",
    "thuở",
]

SENTENCES = [
    "Mọi người đang ở đây.",
    "Người Việt Nam luôn yêu tiếng Việt.",
]

INVISIBLE_CASES = {
    "nbsp_between": "mọi\u00A0người",
    "zwsp_inside": "ng\u200Bười",
    "zwj_inside": "ng\u200Dười",
    "soft_hyphen_inside": "ng\u00ADười",
}

def entry_for(raw: str, pipe: SEAPipeline):
    out = {}
    out["input_codepoints"] = [f"U+{ord(c):04X}" for c in raw]
    for name, fn in (
        ("audit_dropped", lambda s: list(pipe.normalizer.audit(s))),
        ("normalized", lambda s: pipe.normalizer.normalize(s)),
        ("phonemes", lambda s: pipe.run(s, punc_norm=True)),
    ):
        try:
            value = fn(raw)
            if isinstance(value, list):
                value = [f"{c!r}" if isinstance(c, str) else repr(c) for c in value]
            elif isinstance(value, str):
                value = {"text": value,
                         "codepoints": [f"U+{ord(c):04X}" for c in value]}
            out[name] = value
        except Exception as exc:  # keep probe alive per-case
            out[name] = {"error": repr(exc)}
    return out


def main():
    pipe = SEAPipeline(lang="vi")
    report = {"words": {}, "sentences": {}, "invisible": {}}
    for word in WORDS:
        nfc = unicodedata.normalize("NFC", word)
        nfd = unicodedata.normalize("NFD", word)
        entry = {"NFC": entry_for(nfc, pipe), "NFD": entry_for(nfd, pipe)}
        entry["same_normalized"] = (
            entry["NFC"]["normalized"].get("text")
            == entry["NFD"]["normalized"].get("text")
        )
        entry["same_phonemes"] = (
            entry["NFC"]["phonemes"].get("text")
            == entry["NFD"]["phonemes"].get("text")
        )
        report["words"][word] = entry
    for sentence in SENTENCES:
        report["sentences"][sentence] = {
            form: entry_for(unicodedata.normalize(form, sentence), pipe)
            for form in ("NFC", "NFD")
        }
    for label, case in INVISIBLE_CASES.items():
        report["invisible"][label] = {
            "control_nfc_word": entry_for("người", pipe),
            "case": entry_for(case, pipe),
        }
    with open("/tmp/p22_probe.json", "w", encoding="utf-8") as handle:
        json.dump(report, handle, ensure_ascii=False, indent=1)
    summary = []
    for word, entry in report["words"].items():
        summary.append(f"{word}: same_norm={entry['same_normalized']} same_phon={entry['same_phonemes']}")
    print("\n".join(summary))


if __name__ == "__main__":
    main()
