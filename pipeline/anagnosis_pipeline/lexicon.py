"""Convert Perseus lexica (LSJ, Middle Liddell) to a list of entries with HTML bodies.

The HTML uses only <p>, <b>, <i>, <span>, <a> and <br> so that the app can render it with
a minimal HTML-to-styled-text converter.
"""
from __future__ import annotations

import html
import re
from dataclasses import dataclass
from pathlib import Path

from lxml import etree

from . import greek
from .tei_p4 import load as load_p4

GRAM_TAGS = {"gramGrp", "pos", "gen", "itype", "tns", "mood", "per", "num", "pron", "case", "gram"}
SKIP_TAGS = {"pb", "milestone", "index"}


@dataclass
class Entry:
    lexicon: str
    key: str          # raw betacode key from the source, e.g. "a)gaqo/s" or "a)1"
    headword: str     # Unicode headword, without homograph number
    homograph: int    # 0 if none
    html: str
    sort_key: str     # for alphabetical ordering


def _text(s: str | None, grk: bool) -> str:
    if not s:
        return ""
    if grk:
        s = greek.betacode_to_unicode(s)
    return html.escape(s, quote=False)


def _render(el, grk: bool, out: list[str]) -> None:
    """Append the HTML rendering of `el` (children and tails handled here) to out."""
    tag = etree.QName(el).localname
    grk = grk or el.get("lang") == "greek"
    if tag in SKIP_TAGS:
        return
    if tag == "sense":
        level = int(el.get("level") or 1)
        n = el.get("n") or ""
        indent = " " * max(level - 1, 0)
        out.append(f'<p class="sense">{indent}')
        if n and n != "0":
            out.append(f"<b>{html.escape(n)}.</b> ")
        _children(el, grk, out)
        out.append("</p>")
        return
    open_, close = "", ""
    if tag in ("orth",):
        open_, close = '<b class="orth">', "</b>"
    elif tag in ("tr", "trans"):
        open_, close = '<i class="tr">' if tag == "tr" else "", "</i>" if tag == "tr" else ""
    elif tag in ("foreign", "quote", "lemma"):
        open_, close = f'<span class="{tag}">', "</span>"
    elif tag == "cit":
        open_, close = '<span class="cit">', "</span>"
    elif tag == "bibl":
        n = el.get("n")
        attr = f' data-ref="{html.escape(n, quote=True)}"' if n else ""
        open_, close = f'<span class="bibl"{attr}>', "</span>"
    elif tag == "ref":
        target = el.get("target") or ""
        attr = f' data-ref="{html.escape(target, quote=True)}"' if target else ""
        open_, close = f'<span class="ref"{attr}>', "</span>"
    elif tag in GRAM_TAGS:
        open_, close = '<span class="gram">', "</span>"
    elif tag in ("usg", "etym", "note", "xr", "abbr", "lbl", "date", "placeName", "author", "title", "biblScope", "hi", "emph"):
        cls = "i" if tag in ("hi", "emph", "title") else "span"
        open_, close = f'<{cls} class="{tag}">', f"</{cls}>"
    elif tag in ("entryFree", "entry", "form", "item", "list", "p", "div", "num", "date", "term"):
        pass
    else:
        open_, close = f'<span class="{tag}">', "</span>"
    out.append(open_)
    _children(el, grk, out)
    out.append(close)


def _children(el, grk: bool, out: list[str]) -> None:
    out.append(_text(el.text, grk))
    for child in el:
        if isinstance(child.tag, str):  # skip comments and processing instructions
            _render(child, grk, out)
        # the tail belongs to the parent's language, not the child's
        out.append(_text(child.tail, grk))


_WS = re.compile(r"\s+")


def render_entry(el) -> str:
    out: list[str] = []
    _children(el, False, out)
    s = "".join(out)
    s = _WS.sub(" ", s)
    s = s.replace(" </p>", "</p>").replace("<p class=\"sense\"> ", "<p class=\"sense\">")
    # the head matter (before the first sense) becomes its own paragraph
    if not s.startswith("<p"):
        i = s.find("<p")
        head, rest = (s, "") if i < 0 else (s[:i], s[i:])
        s = f"<p class=\"head\">{head.strip()}</p>{rest}"
    return s.strip()


def _split_key(key: str) -> tuple[str, int]:
    m = re.match(r"^(.*?)(\d+)$", key)
    if m:
        return m.group(1), int(m.group(2))
    return key, 0


def parse_lexicon(path: Path, lexicon: str, p4: bool) -> list[Entry]:
    if p4:
        root = load_p4(path)
    else:
        parser = etree.XMLParser(load_dtd=False, resolve_entities=False, huge_tree=True)
        root = etree.parse(str(path), parser).getroot()
    entries: list[Entry] = []
    for el in root.iter("entryFree", "entry"):
        key = el.get("key") or ""
        if not key:
            continue
        base, homograph = _split_key(key)
        headword = greek.betacode_to_unicode(base)
        entries.append(
            Entry(
                lexicon=lexicon,
                key=key,
                headword=headword,
                homograph=homograph,
                html=render_entry(el),
                sort_key=greek.strip_diacritics(headword),
            )
        )
    return entries


def parse_lsj(sources: Path) -> list[Entry]:
    entries: list[Entry] = []
    for path in sorted((sources / "lsj").glob("grc.lsj.perseus-eng*.xml"), key=lambda p: int(re.search(r"eng(\d+)", p.name).group(1))):
        entries.extend(parse_lexicon(path, "lsj", p4=False))
    return entries


def parse_middle_liddell(sources: Path) -> list[Entry]:
    return parse_lexicon(sources / "middle-liddell.xml", "ml", p4=True)
