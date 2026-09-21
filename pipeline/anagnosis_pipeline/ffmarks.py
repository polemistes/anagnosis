"""Recover Jebb's "f." / "ff." marks from the OCR text of the 1891 scan.

Perseus dropped the marks from the commentary and the apparatus transcription reduced
labels to the first number. The OCR text (sophocles03soph_djvu.txt) reads digits and
"ff." reliably, so a heading `## 4` becomes `## 4 ff.` when an OCR paragraph starts
"4 ff." followed by the same Greek word the entry starts with.
"""
from __future__ import annotations

import re
from pathlib import Path

from . import greek

LABEL = re.compile(r"^\s*(\d{1,4})\s*(ff?\.)\s*(.*)$")
GREEK_WORD = re.compile(r"[Ͱ-Ͽἀ-῿]{3,}")


def _key(text: str) -> str | None:
    """Loose key of the first Greek word: first four letters, no diacritics."""
    m = GREEK_WORD.search(greek.nfc(text))
    return greek.strip_diacritics(m.group(0))[:4] if m else None


def ocr_labels(ocr: Path) -> dict[int, list[tuple[str, str | None]]]:
    out: dict[int, list[tuple[str, str | None]]] = {}
    rows = ocr.read_text(encoding="utf-8", errors="replace").splitlines()
    for i, raw in enumerate(rows):
        m = LABEL.match(raw)
        if not m:
            continue
        rest = m.group(3) or (rows[i + 1] if i + 1 < len(rows) else "")
        out.setdefault(int(m.group(1)), []).append((m.group(2), _key(rest)))
    return out


def apply_ff_marks(md_path: Path, ocr: Path) -> int:
    labels = ocr_labels(ocr)
    text = md_path.read_text(encoding="utf-8")
    blocks = re.split(r"(?m)^(?=## )", text)
    changed = 0
    for i, block in enumerate(blocks):
        m = re.match(r"^## (\d+)\n(.*)", block, re.S)
        if not m:
            continue
        n, body = int(m.group(1)), m.group(2)
        key = _key(body)
        if key is None:
            continue
        marks = [suffix for suffix, k in labels.get(n, []) if k == key]
        if not marks:
            continue
        suffix = "ff." if "ff." in marks else "f."
        blocks[i] = f"## {n} {suffix}\n{body}"
        changed += 1
    md_path.write_text("".join(blocks), encoding="utf-8")
    return changed
