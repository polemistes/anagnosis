"""Import Jebb's Introduction (and the sections on manuscripts and the ancient arguments)
from the Perseus commentary file into an editable Markdown document."""
from __future__ import annotations

import re
from pathlib import Path

from lxml import etree

from . import greek
from .commentary import _md_children
from .tei_p4 import load as load_p4


def _md_with_headings(el, grk: bool) -> tuple[str, str | None]:
    """Markdown of a section, and the title taken from its first marginal note (if any)."""
    title = None
    for note in el.iter("note"):
        if note.get("place") == "marg":
            title = re.sub(r"\s+", " ", "".join(note.itertext())).strip().rstrip(".")
            break
    return _md_children(el, grk), title


# The Perseus headings of the ancient arguments are Greek capitals in betacode or bare numerals.
HYPOTHESES_TITLES = {
    1: "I. The argument of Aristophanes of Byzantium",
    2: "II. The argument of Salustius",
    3: "III. A third argument",
    4: "The persons of the drama",
    5: "Structure of the play",
}


def import_introduction(source: Path, out: Path, meta: dict[str, str]) -> int:
    root = load_p4(source)
    lines = [f"# {k}: {v}" for k, v in meta.items()]
    lines.append("")
    n = 0
    chapters = [
        ("introduction", "Introduction", False),
        ("texts", "Manuscripts, editions and commentaries", False),
        ("hypotheses", "The ancient arguments", True),
    ]
    for part, chapter, grk_default in chapters:
        d1 = next((d for d in root.iter("div1") if d.get("n") == part), None)
        if d1 is None:
            continue
        lines.append(f"# {chapter}")
        lines.append("")
        for i, d2 in enumerate(d1.findall("div2"), 1):
            head = d2.find("head")
            body, title = _md_with_headings(d2, grk_default)
            if head is not None:
                htxt = "".join(head.itertext()).strip()
                title = HYPOTHESES_TITLES.get(i) if part == "hypotheses" else htxt
                body = body.replace(_md_children(head, grk_default), "", 1)
            body = re.sub(r"[ \t]+\n", "\n", body)
            body = re.sub(r"\n{3,}", "\n\n", body).strip()
            body = re.sub(r" +", " ", body)
            lines.append(f"## {i}. {title}" if title else f"## {i}")
            lines.append("")
            lines.append(body)
            lines.append("")
            n += 1
    # The later volumes' files: one <div1 type="introduction"> of numbered sections (§ 1, § 2 ...)
    # whose headings Perseus left out
    d1 = next((d for d in root.iter("div1") if d.get("type") == "introduction"), None)
    if d1 is not None and n == 0:
        lines.append("# Introduction")
        lines.append("")
        for d2 in d1.findall("div2"):
            body, _title = _md_with_headings(d2, False)
            body = re.sub(r"[ \t]+\n", "\n", body)
            body = re.sub(r"\n{3,}", "\n\n", body).strip()
            body = re.sub(r" +", " ", body)
            lines.append(f"## § {d2.get('n') or n + 1}")
            lines.append("")
            lines.append(body)
            lines.append("")
            n += 1
    out.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return n
