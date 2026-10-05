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


BETACODE = re.compile(r"[a-z*()/\\=|+' ]*[/\\=][a-z*()/\\=|+' ]*")


def _md(el, grk: bool) -> str:
    tag = etree.QName(el).localname
    if el.get("lang"):
        # a language stated on an element holds for it, also inside a Greek quotation (an
        # English aside, a metrical scheme): only "greek" is betacode, or a text that is
        # plainly betacode under another label (the OC's lemma tiqh/nais marked Latin)
        own = ((el.text or "") + "".join(c.tail or "" for c in el)).strip()
        grk = el.get("lang") == "greek" or (el.get("lang") in ("la", "en") and BETACODE.fullmatch(own) is not None
                                             and re.search(r"[a-z][()]*[/\\=]", own) is not None)
    if tag == "p":
        _open[0] = 0
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
        s = inner.strip()
        return f" {s} " if s.startswith("(") else f" ({s}) "
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
    if grk and not _plain_english(s):
        s, _open[0] = _beta(s, _open[0])
    else:
        _open[0] = max(0, _open[0] + s.count("(") - s.count(")"))
        s = s.replace("*", "\\*").replace("_", "\\_")
    return re.sub(r"\s+", " ", s)


# Perseus writes ordinary parentheses inside Greek quotations, where betacode reads ( and ) as
# breathings, and it writes an elision as ) too. A breathing stands before an accent, after *
# (a capital), or after a word's first vowel or two, also behind one or two consonants in a
# crasis (ka)gw/, tou)/noma, prou)/sthmen); a ) that ends a word is an elision (e)ntau=q),
# xqo/ni)), and one that begins it a prodelision (h)\ )gw/); any other ( or ) is a
# parenthesis. The parentheses and the elisions are kept apart from the conversion. A
# quotation that ends in a vowel and ) while the paragraph has a parenthesis open closes it:
# (e)stefanwme/noi) where the ( stands in the English before the quotation.
OPEN, CLOSE, ELIDED = "\ue000", "\ue001", "\ue002"
BREATHING_AFTER = re.compile(r"[bgdzqklmncprstfxyv]{0,2}[aeiouhwr]{1,2}")
ENGLISH = {"the", "and", "of", "to", "in", "is", "with", "this", "that", "not", "do", "as", "by", "for",
           "at", "on", "it", "be", "which", "from", "or", "an", "are", "was", "his", "her", "we", "they",
           "after", "would", "could", "should", "but", "if", "when", "who", "what", "so", "than"}


def _plain_english(s: str) -> bool:
    """English left untagged inside a Greek element: no betacode accents, several English words."""
    if re.search(r"[a-z*][/\\=|+]|[aeiouhwr][()][/\\=|]", s):
        return False
    return sum(w.lower() in ENGLISH for w in re.findall(r"[A-Za-z]+", s)) >= 2


_open = [0]  # parentheses opened earlier in the paragraph and not yet closed


def _beta(s: str, outer: int = 0) -> tuple[str, int]:
    """Betacode to Unicode, parentheses and elisions as described above; with the count of
    parentheses open before the text and after it."""
    protected = _protect_parens(s, outer)
    outer = max(0, outer + protected.count(OPEN) - protected.count(CLOSE))
    out = greek.betacode_to_unicode(protected)
    out = re.sub("σ(?=" + CLOSE + ")", "ς", out)  # a final sigma before the parenthesis
    return out.replace(OPEN, "(").replace(CLOSE, ")").replace(ELIDED, "\u02bc"), outer


def _protect_parens(s: str, outer: int = 0) -> str:
    out = []
    depth = 0  # parentheses opened in this text and not yet closed
    tokens = re.split(r"(\s+)", s)
    last = max((k for k, t in enumerate(tokens) if t.strip()), default=-1)
    for k, token in enumerate(tokens):
        token = re.sub(r"([()])\*(?=[a-z])", r"*\1", token)  # )*ismhnou= for *)ismhnou=
        letters, breathed = "", False
        chars = []
        for i, c in enumerate(token):
            if c not in "()":
                if c.isalpha():
                    letters += c.lower()
                elif c not in "/\\=+|*^_":
                    letters, breathed = "", False  # a new word after '...', a digit, an elision
                chars.append(c)
                continue
            prev = token[i - 1] if i else ""
            nxt = token[i + 1] if i + 1 < len(token) else ""
            at_end = not re.search(r"[A-Za-z*]", token[i + 1:])
            word_end = not (nxt.isalpha() or (nxt and nxt in "/\\=|+*"))
            if nxt and nxt in "/\\=|":
                kind = c  # an accent follows: a breathing
            elif prev.isalpha() and nxt.isalpha():
                kind = c  # inside a word (a missing space or accent in the source): as betacode reads it
            elif prev == "*" or ((prev.isalpha() or prev in "^_") and prev and not breathed and BREATHING_AFTER.fullmatch(letters)):
                kind = c
            elif c == ")" and depth and at_end:
                kind = CLOSE
            elif c == ")" and not depth and outer and k == last and at_end and prev in "aeiouhw":
                kind = CLOSE
                outer -= 1
            elif c == ")" and word_end and (prev.isalpha() or (prev and prev in "/\\=|+()")):
                kind = ELIDED
            elif c == ")" and not (prev.isalpha() or prev == "*") and nxt.isalpha():
                kind = c  # prodelision: the converter writes it as an apostrophe
            else:
                kind = OPEN if c == "(" else CLOSE
            if kind == OPEN:
                depth += 1
            elif kind == CLOSE:
                depth = max(0, depth - 1)
            elif kind in "()":
                breathed = True
            chars.append(kind)
        out.append("".join(chars))
    return "".join(out)


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
