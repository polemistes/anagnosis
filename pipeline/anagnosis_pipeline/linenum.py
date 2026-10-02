"""Line numbers: plain (12, 161b) for a play, book.line (1.12, 16.101) for an epic.

The database keeps one integer per line, n_int, so that ranges and ordering stay simple:
a plain number is itself, a book.line number is book * 1000 + line. No book of Homer has a
thousand lines, so the encoding is unambiguous; the app turns n_int back into a label.
"""
from __future__ import annotations

import re

_PLAIN = re.compile(r"^(?:(\d+)\.)?(\d+)([a-z]?)$")
# Plato is cited by Stephanus page, section and Burnet's line within the section: 172a1.
STEPHANUS = re.compile(r"^(\d+)([a-e])(\d+)$")
LINE_N = re.compile(r"^(?:(?:\d+\.)?\d+[a-z]?|\d+[a-e]\d+)$")
BOOK = 1000
SECTIONS = "abcde"
# A line number as it may appear in headings and ranges, for embedding in larger patterns.
N_PATTERN = r"(?:\d+[a-e]\d+|(?:\d+\.)?\d+[a-z]?)"


def parts(n: str) -> tuple[int, str]:
    """(n_int, letter) of a line number; raises ValueError for anything else.

    A Stephanus line 172a1 is page * 1000 + section * 100 + line (172001; 172b3 is 172103).
    """
    m = STEPHANUS.match(n)
    if m:
        return int(m.group(1)) * BOOK + SECTIONS.index(m.group(2)) * 100 + int(m.group(3)), ""
    m = _PLAIN.match(n)
    if not m:
        raise ValueError(f"bad line number {n!r}")
    book = int(m.group(1)) if m.group(1) else 0
    return book * BOOK + int(m.group(2)), m.group(3)


def valid(n: str) -> bool:
    return LINE_N.match(n) is not None


def stephanus_section(n: str) -> str | None:
    """'172a' for the line 172a1; None for other kinds of number."""
    m = STEPHANUS.match(n)
    return f"{m.group(1)}{m.group(2)}" if m else None


def book_of(n: str) -> str | None:
    m = _PLAIN.match(n)
    return m.group(1) if m else None


def complete(to: str, frm: str) -> str:
    """The end of a range written short: '7' after '1.5' means '1.7'; after '172a3', '5' means
    '172a5' and 'b2' means '172b2'."""
    m = STEPHANUS.match(frm)
    if m:
        if re.fullmatch(r"\d+", to):
            return f"{m.group(1)}{m.group(2)}{to}"
        if re.fullmatch(r"[a-e]\d+", to):
            return f"{m.group(1)}{to}"
        return to
    if "." not in to and book_of(frm):
        return f"{book_of(frm)}.{to}"
    return to
