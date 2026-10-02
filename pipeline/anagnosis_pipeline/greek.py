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
_TOKEN = re.compile(r"\{[^}]*\}|[ʼ᾽᾿]?[Ͱ-Ͽἀ-῿̀-ͯ]+(?:⟨[Ͱ-Ͽἀ-῿̀-ͯ]+⟩[Ͱ-Ͽἀ-῿̀-ͯ]*)*[ʼ᾽᾿]?|[^\s]")


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


def betacode_to_unicode(s: str) -> str:
    return nfc(beta_code.beta_code_to_greek(s))
