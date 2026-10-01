"""Line numbers: plain (12, 161b) for a play, book.line (1.12, 16.101) for an epic.

The database keeps one integer per line, n_int, so that ranges and ordering stay simple:
a plain number is itself, a book.line number is book * 1000 + line. No book of Homer has a
thousand lines, so the encoding is unambiguous; the app turns n_int back into a label.
"""
from __future__ import annotations

import re

LINE_N = re.compile(r"^(?:(\d+)\.)?(\d+)([a-z]?)$")
BOOK = 1000
# A line number as it may appear in headings and ranges, for embedding in larger patterns.
N_PATTERN = r"(?:\d+\.)?\d+[a-z]?"


def parts(n: str) -> tuple[int, str]:
    """(n_int, letter) of a line number; raises ValueError for anything else."""
    m = LINE_N.match(n)
    if not m:
        raise ValueError(f"bad line number {n!r}")
    book = int(m.group(1)) if m.group(1) else 0
    return book * BOOK + int(m.group(2)), m.group(3)


def valid(n: str) -> bool:
    return LINE_N.match(n) is not None


def book_of(n: str) -> str | None:
    m = LINE_N.match(n)
    return m.group(1) if m else None


def complete(to: str, frm: str) -> str:
    """The end of a range written short: '7' after '1.5' means '1.7'."""
    if "." not in to and book_of(frm):
        return f"{book_of(frm)}.{to}"
    return to
