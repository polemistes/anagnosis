"""Import Jebb's commentary (Perseus TEI P4) into an editable Markdown file.

Output format (texts/<slug>/commentary-<name>.md):

    # title: ...
    # author: ...

    ## 1            <- Greek line (or range like 1-3) the note refers to
    **κοινόν** (kindred) ... note text in Markdown, paragraphs separated by blank lines

Markdown subset used: **bold** (lemmas), *italic*, [text](#line) cross references to other notes.
"""
from __future__ import annotations

import re
from pathlib import Path

from lxml import etree

from . import greek
from .linenum import N_PATTERN, complete
from .tei_p4 import load as load_p4


def _md(el, grk: bool) -> str:
    tag = etree.QName(el).localname
    grk = grk or el.get("lang") == "greek"
    inner = _md_children(el, grk)
    if tag == "lemma":
        return f"**{inner.strip()}**"
    if tag in ("emph", "title", "hi"):
        return f"*{inner.strip()}*"
    if tag == "ref":
        target = el.get("target") or ""
        m = re.match(r"^cl(\d+)$", target)
        if m:
            return f"[{inner.strip()}](#{m.group(1)})"
        return inner
    if tag == "note":
        if el.get("place") == "marg":
            return ""  # marginal titles are used as headings by the introduction importer
        return f" ({inner.strip()}) "
    if tag == "l":
        return inner.strip() + " | "
    if tag == "lg":
        return " " + inner.strip().rstrip("| ").strip() + " "
    if tag == "p":
        return inner.strip() + "\n\n"
    if tag in ("pb", "milestone"):
        return ""
    return inner


def _md_children(el, grk: bool) -> str:
    parts = [_txt(el.text, grk)]
    for child in el:
        if isinstance(child.tag, str):  # skip comments and processing instructions
            parts.append(_md(child, grk))
        parts.append(_txt(child.tail, grk))
    return "".join(parts)


def _txt(s: str | None, grk: bool) -> str:
    if not s:
        return ""
    if grk:
        s = greek.betacode_to_unicode(s)
    s = s.replace("*", "\\*").replace("_", "\\_") if not grk else s
    return re.sub(r"\s+", " ", s)


def import_jebb_commentary(source: Path, out: Path, meta: dict[str, str]) -> int:
    root = load_p4(source)
    comm = None
    for d in root.iter("div1"):
        if d.get("type") == "commentary":
            comm = d
    if comm is None:
        # the Oedipus Tyrannus file: <div1 type="section" n="1-150"> sections of
        # <div2 type="commline" n="..."> notes, the first of a range (n="1-77") summarising it
        sections = [d for d in root.iter("div1") if d.get("type") in ("section", "sect")]
        if not sections:
            raise SystemExit("no <div1 type=commentary> found")
        return _import_sectioned(sections, out, meta)
    lines = [f"# {k}: {v}" for k, v in meta.items()]
    lines.append("")
    n_notes = 0

    def clean(md: str) -> str:
        md = re.sub(r"[ \t]+\n", "\n", md)
        md = re.sub(r"\n{3,}", "\n\n", md).strip()
        return re.sub(r" +", " ", md)

    def emit(heading: str, body: str) -> None:
        nonlocal n_notes
        lines.append(f"## {heading}")
        lines.append(body)
        lines.append("")
        n_notes += 1

    # The scene-setting paragraph that precedes the first episode joins its introduction.
    scene = [clean(_md(p, False)) for p in comm if isinstance(p.tag, str) and p.tag == "p"]

    def emit_intro(d2) -> None:
        """An episode's introduction: <div2><head>1-99</head><p>Prologue. ...</p>"""
        nonlocal scene
        head = d2.find("head")
        intro = [c for c in d2 if isinstance(c.tag, str) and c.tag == "p"]
        if head is None or not re.fullmatch(r"\d+-\d+", (head.text or "").strip()) or not intro:
            return
        body = "\n\n".join(clean(_md(p, False)) for p in intro)
        if scene:
            body = "\n\n".join(scene) + "\n\n" + body
            scene = []
        emit(head.text.strip(), body)

    def emit_line_note(d3) -> None:
        n = d3.get("n")
        head = d3.find("head")
        paragraphs = [c for c in d3 if isinstance(c.tag, str) and c.tag != "head"]
        # A <head> like "4-6" gives the range of the first note; the rest belong to line n.
        if head is not None and re.fullmatch(r"\d+-\d+", (head.text or "").strip()) and paragraphs:
            emit(head.text.strip(), clean(_md(paragraphs[0], False)))
            paragraphs = paragraphs[1:]
            if not paragraphs:
                return
        emit(n, clean("".join(_md(p, False) for p in paragraphs)))

    for d2 in comm.iter("div2"):
        emit_intro(d2)
        for d3 in d2.iter("div3"):
            emit_line_note(d3)
    out.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return n_notes


def _import_sectioned(sections, out: Path, meta: dict[str, str]) -> int:
    lines = [f"# {k}: {v}" for k, v in meta.items()]
    lines.append("")
    n_notes = 0

    def clean(md: str) -> str:
        md = re.sub(r"[ \t]+\n", "\n", md)
        md = re.sub(r"\n{3,}", "\n\n", md).strip()
        return re.sub(r" +", " ", md)

    def emit(heading: str, body: str) -> None:
        nonlocal n_notes
        if not body:
            return
        lines.append(f"## {heading}")
        lines.append(body)
        lines.append("")
        n_notes += 1

    for d1 in sections:
        rng = (d1.get("n") or "").strip()
        intro = [p for p in d1 if isinstance(p.tag, str) and p.tag == "p"]
        if intro and re.fullmatch(r"\d+-\d+", rng):
            emit(rng, clean("\n\n".join(_md(p, False) for p in intro)))
        for d2 in d1.iter("div2"):
            n = (d2.get("n") or "").strip()
            if not re.fullmatch(r"\d+[a-z]?(?:-\d+[a-z]?)?", n):
                continue
            paragraphs = [c for c in d2 if isinstance(c.tag, str) and c.tag != "head" and not c.tag.startswith("div")]
            emit(n, clean("".join(_md(p, False) for p in paragraphs)))
    out.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return n_notes


def parse_commentary_md(path: Path) -> tuple[dict[str, str], list[dict]]:
    """Read a commentary Markdown file into (meta, notes). Note keys: n, from, to, body."""
    meta: dict[str, str] = {}
    notes: list[dict] = []
    current: dict | None = None
    buf: list[str] = []

    def flush():
        if current is not None:
            current["body"] = "\n".join(buf).strip()
            notes.append(current)

    for raw in path.read_text(encoding="utf-8").splitlines():
        if current is None and raw.startswith("#") and not raw.startswith("##"):
            k, _, v = raw[1:].partition(":")
            meta[k.strip()] = v.strip()
            continue
        m = re.match(rf"^## ({N_PATTERN})(?:-({N_PATTERN}))?(?:\s+(ff?\.))?\s*$", raw)
        if m:
            flush()
            label = m.group(1) + (f"-{m.group(2)}" if m.group(2) else "") + (f" {m.group(3)}" if m.group(3) else "")
            current = {"n": label, "from": m.group(1), "to": complete(m.group(2), m.group(1)) if m.group(2) else m.group(1)}
            buf = []
            continue
        if current is not None:
            buf.append(raw)
    flush()
    return meta, notes
