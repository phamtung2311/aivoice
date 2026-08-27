"""Conservative Vietnamese-friendly input hygiene (Phase 22).

Scope is intentionally small and reversible:

1. Map Unicode *separator/zero-width* characters that the downstream G2P
   (sea_g2p, Rust core) turns into real spaces — silently splitting Vietnamese
   syllables — into harmless equivalents BEFORE normalization:
       U+00A0/U+2007/U+202F (space-like)      -> regular space
       U+200B/U+200C/U+200D/U+2060/U+FEFF      -> removed
       U+00AD (soft hyphen)                    -> removed
   Empirical evidence (Phase 22 probe): ``ng\\u200Bười`` normalized to
   ``ng ười`` inside sea_g2p, which then read the orphan ``ng`` with its English
   G letter name — matching the reported “ngờ i” mispronunciation.
2. Compose everything to Unicode NFC. VieNeu (vieneu/vieneu_utils/sea_g2p 0.9.0)
   contains no unicodedata usage anywhere, and identical handling was measured,
   but canonical composition keeps chunk length accounting predictable and is
   the documented-safe direction for future layers.

This layer NEVER folds accents (no ``người``->``nguoi``), never changes letters,
numbers or case, and is idempotent.
"""

import unicodedata

# Characters collapsed into plain ASCII space (word-separators in disguise).
_SPACE_LIKE = {
    "\u00A0": " ",  # NO-BREAK SPACE
    "\u2007": " ",  # FIGURE SPACE
    "\u202F": " ",  # NARROW NO-BREAK SPACE
}

# Invisible joiners/boundary artifacts inside words. sea_g2p converts some of
# them into real spaces (breaking the syllable) or drops them silently; either
# way they must not reach G2P attached to a Vietnamese syllable.
_INVISIBLE_REMOVED = {
    "\u200B": "",  # ZERO WIDTH SPACE
    "\u200C": "",  # ZERO WIDTH NON-JOINER
    "\u200D": "",  # ZERO WIDTH JOINER
    "\u2060": "",  # WORD JOINER
    "\uFEFF": "",  # BOM / ZERO WIDTH NO-BREAK SPACE
    "\u00AD": "",  # SOFT HYPHEN
}

_TRANSLATION = {**_SPACE_LIKE, **_INVISIBLE_REMOVED}
_TRANSLATION_TABLE = str.maketrans(_TRANSLATION)

# Repeated space-like leftovers after translation are handled by callers.


def normalize_vi_input(text: str) -> str:
    """Return ``text`` with dangerous invisible characters mapped out and NFC-composed.

    Purely cosmetic transformations only; visually identical Vietnamese output is
    guaranteed for well-formed precomposed input.
    """
    if text is None:
        return ""
    return unicodedata.normalize("NFC", text.translate(_TRANSLATION_TABLE))


def audit_invisible_characters(text: str):
    """Dev/test helper: list characters the layer would rewrite, without rewriting."""
    if text is None:
        return []
    seen = []
    for char in text:
        if char in _TRANSLATION and char not in seen:
            seen.append(char)
    return [f"U+{ord(char):04X}" for char in seen]
