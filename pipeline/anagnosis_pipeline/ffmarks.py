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


def hocr_labels(hocr_files: list[Path]) -> dict[int, str]:
    """Jebb's "f." / "ff." after a note's number, from our own OCR of the pages (Tesseract hOCR):
    a line that begins with the number and "f." / "ff." and stands indented against the lines near
    it in its column (a note's heading is indented; a reference that happens to begin a line, "cp.
    on 110 f., and Append. | 155 ff.", is not). The number -> "f." or "ff." ("ff." where both)."""
    import html

    found: dict[int, str] = {}
    for f in hocr_files:
        t = f.read_text(encoding="utf-8")
        lines = []
        for m in re.finditer(r"class='ocr_line'[^>]*title=\"bbox ([0-9 ]+);[^\"]*\"(.*?)(?=class='ocr_line'|\Z)", t, re.S):
            ws = [html.unescape(re.sub("<[^>]+>", "", w))
                  for w in re.findall(r"class='ocrx_word'[^>]*>(.*?)</span>", m.group(2), re.S)]
            lines.append((tuple(map(int, m.group(1).split())), ws))
        for b, ws in lines:
            if len(ws) < 2:
                continue
            a = ws[0].translate(str.maketrans("IlOo", "1100"))
            if not (re.fullmatch(r"\d{1,4}", a) and re.fullmatch(r"(?:ff?|fF|fl|ﬀ|ﬁ)[.,]?", ws[1])):
                continue
            near = sorted(x[0][0] for x in lines if abs(x[0][0] - b[0]) < 150 and abs(x[0][1] - b[1]) < 600)
            if b[0] - near[max(0, len(near) // 10)] < 20:
                continue
            mark = "ff." if ws[1].startswith(("ff", "fF", "ﬀ")) else "f."
            n = int(a)
            found[n] = "ff." if "ff." in (mark, found.get(n)) else mark
    return found


def apply_hocr_marks(md_path: Path, hocr_files: list[Path]) -> int:
    """Headings without a mark (`## 120`) get the f. / ff. that hocr_labels finds for their number."""
    labels = hocr_labels(hocr_files)
    text = md_path.read_text(encoding="utf-8")

    def mark(m: re.Match) -> str:
        n = int(m.group(1))
        return f"## {n} {labels[n]}" if n in labels else m.group(0)

    new, count = re.subn(r"(?m)^## (\d+)$", mark, text)
    count = sum(1 for a, b in zip(text.split("\n"), new.split("\n")) if a != b)
    md_path.write_text(new, encoding="utf-8")
    return count
