"""Greek string utilities: normalisation, tokenisation, betacode."""
from __future__ import annotations

import re
import unicodedata

import beta_code

APOSTROPHE = "ʼ"  # MODIFIER LETTER APOSTROPHE, used for elision in the texts
APOSTROPHE_LIKE = "ʼ’'̓᾿᾽"  # ʼ ’ ' ̓ ᾿ ᾽

# Word characters: Greek letters plus the elision apostrophe. Everything else splits.
# A speaker's name printed in a prose text is written in braces, {ΑΠΟΛ.}: one token, not a word.
# a word may hold an editor's addition: Ἀγάθων⟨ος⟩
# a numeral keeps its keraia (ρʹ, λεʹ: U+0374, which NFC makes U+02B9)
_TOKEN = re.compile(r"\{[^}]*\}|[ʼ᾽᾿]?[Ͱ-Ͽἀ-῿̀-ͯ]+(?:⟨[Ͱ-Ͽἀ-῿̀-ͯ]+⟩[Ͱ-Ͽἀ-῿̀-ͯ]*)*(?:\u02b9|[ʼ᾽᾿])?|[^\s]")


def nfc(s: str) -> str:
    return unicodedata.normalize("NFC", s)


def nfd(s: str) -> str:
    return unicodedata.normalize("NFD", s)


def strip_diacritics(s: str) -> str:
    """Base letters only, lowercased, apostrophes removed. Used for fuzzy comparison."""
    return "".join(
        c for c in nfd(s).lower() if not unicodedata.combining(c) and c not in APOSTROPHE_LIKE and c not in "⟨⟩"
    )


def is_word(tok: str) -> bool:
    return not tok.startswith("{") and any(c.isalpha() for c in tok)


def tokenize(line: str) -> list[tuple[str, int, int]]:
    """Split a line of Greek text into (token, start, end) triples.

    Words keep a trailing elision apostrophe; punctuation becomes single-char tokens.
    Editorial brackets ⟨ ⟩ [ ] are punctuation.
    """
    return [(m.group(0), m.start(), m.end()) for m in _TOKEN.finditer(nfc(line))]


def words(line: str) -> list[tuple[str, int, int]]:
    return [t for t in tokenize(line) if is_word(t[0])]


def lemma_key(lemma: str) -> str:
    """Key used to join treebank lemmas to lexicon headwords: NFC, lowercase, no homograph digits."""
    s = nfc(lemma).strip()
    s = re.sub(r"\d+$", "", s)
    return s.lower()


# Betacode marks vowel length with ^ (short) and _ (long), among the other marks of the letter
# ("a^)/kouon", "ka^ta^", "i_"). The converter does not know them: it leaves ^ beside the vowel,
# makes _ a dash, and a mark that stands before a breathing breaks the breathing ("α^ʼ ́κουον").
# They are taken out before the conversion and set over the vowel afterwards, as in print: ᾰ, ῑ, ἄ̆.
_BREVE, _MACRON = "\ue000", "\ue001"   # placeholders, which the converter passes through
_LENGTH = re.compile(r"(\*[)(/\\=+|^_]*)?([aeiouhwAEIOUHW])([)(/\\=+|^_]*)")
_MARKED = re.compile(r"(.)([\u0300-\u036f]*)([\ue000\ue001]+)", re.S)


def _length_out(m: re.Match) -> str:
    capital, letter, marks = m.group(1) or "", m.group(2), m.group(3)
    found = capital + marks
    if "^" not in found and "_" not in found:
        return m.group(0)
    holders = "".join(_BREVE if c == "^" else _MACRON for c in found if c in "^_")
    return capital.replace("^", "").replace("_", "") + letter + marks.replace("^", "").replace("_", "") + holders


def _length_in(m: re.Match) -> str:
    letter = nfd(m.group(1) + m.group(2))
    mark = "\u0306" if m.group(3)[0] == _BREVE else "\u0304"
    return letter[0] + mark + letter[1:]


def betacode_to_unicode(s: str) -> str:
    """Betacode to Unicode, with the marks of vowel length over their vowel (ᾰ, ῑ)."""
    if "^" not in s and "_" not in s:
        return nfc(beta_code.beta_code_to_greek(s))
    out = beta_code.beta_code_to_greek(_LENGTH.sub(_length_out, s))
    return nfc(_MARKED.sub(_length_in, out))
