"""Plato's Symposium: Jowett's translation, Bury's commentary and introduction, and the GLAUx
annotation, fitted to Burnet's lines (texts/symposium/grc.txt, from the transcription).

Burnet's lines are numbered by Stephanus page, section and line (172a1). Jowett marks only the
Stephanus pages, so his text is cut at the page marks and, within a page, at the sentence end
nearest to where each section begins in proportion to the Greek. Bury's notes are filed by
section and located on a line by their lemma. GLAUx (an automatic annotation of the Perseus
text of Burnet) is aligned word by word to the transcribed lines.
"""
from __future__ import annotations

import bisect
import difflib
import re
from collections import Counter, defaultdict
from pathlib import Path

from . import greek
from .linenum import SECTIONS, STEPHANUS

# ---------------------------------------------------------------- Burnet's lines


def stephanus(n: str) -> tuple[int, str, int]:
    m = STEPHANUS.match(n)
    if not m:
        raise ValueError(f"not a Stephanus line number: {n!r}")
    return int(m.group(1)), m.group(2), int(m.group(3))


def section_of(n: str) -> str:
    page, letter, _line = stephanus(n)
    return f"{page}{letter}"


# ---------------------------------------------------------------- Jowett

JOWETT_META = {
    "title": "Symposium",
    "translator": "Benjamin Jowett",
    "lang": "eng",
    "source": "Wikisource, The Dialogues of Plato (1892), vol. I, pp. 541-594, proofread transcription",
    "edition": "The Dialogues of Plato, translated by B. Jowett, third edition, Oxford, 1892",
    "license": "Public domain (Jowett died 1893); Wikisource transcription CC BY-SA 4.0",
}

_DROP = {"right sidenote", "left sidenote", "rh", "sidenotes begin", "sidenotes end", "smallrefs",
         "dhr", "nop", "ts", "0", "custom rule", "rule"}
_KEEP_FIRST = {"sc", "polytonic", "latin", "fine", "smaller", "larger", "xx-larger", "x-larger", "c",
               "center", "center block", "center line", "center inline", "cwnter inline", "uc", "i"}


def _template(body: str) -> str:
    """The text a Wikisource template without nested templates stands for."""
    name, _, rest = body.partition("|")
    key = name.strip().lower()
    args = rest.split("|") if rest else []
    if key in _DROP:
        return ""
    if key == "'":
        return "'"
    if key == "gap":
        return " "
    if key == "verse":
        m = re.search(r"(\d{3})", rest)
        return f" ⟦{m.group(1)}⟧ " if m else ""
    if key in _KEEP_FIRST:
        positional = [a for a in args if "=" not in a or a.startswith("'")]
        return positional[0] if positional else ""
    raise ValueError(f"unknown template {{{{{body[:40]}}}}}")


def _wiki_to_text(s: str) -> str:
    s = re.sub(r"<noinclude>.*?</noinclude>", "", s, flags=re.S)
    s = re.sub(r"<ref[^>]*>.*?</ref>", "", s, flags=re.S)
    s = re.sub(r"<ref[^>]*/>", "", s)
    s = re.sub(r"\{\|.*?\n\|\}", "", s, flags=re.S)  # tables (the list of persons)
    s = re.sub(r"\[\[(?:[^\]|]*\|)?([^\]]*)\]\]", r"\1", s)
    while True:
        t = re.sub(r"\{\{([^{}]*)\}\}", lambda m: _template(m.group(1)), s)
        if t == s:
            break
        s = t
    s = re.sub(r"<br\s*/?>\s*", " / ", s)
    s = re.sub(r"<[^>]+>", "", s)
    s = s.replace("'''", "").replace("''", "")
    return s


def jowett_paragraphs(sources: Path) -> list[str]:
    """Jowett's Symposium as paragraphs, with Stephanus page marks written ⟦172⟧."""
    from .fetch import JOWETT_PAGES

    text = ""
    for n in JOWETT_PAGES:
        raw = (sources / "jowett" / f"{n}.wiki").read_text(encoding="utf-8")
        body = _wiki_to_text(raw)
        # a page that begins with an empty line begins a new paragraph
        sep = "\n\n" if re.match(r"^[ \t]*\n", body) else " "
        text += sep + body.strip()
    paras = [re.sub(r"\s+", " ", p).strip() for p in re.split(r"\n\s*\n", text)]
    paras = [p for p in paras if p]
    start = next(i for i, p in enumerate(paras) if "⟦172⟧" in p)
    paras = paras[start:]
    paras[0] = paras[0][paras[0].index("⟦172⟧"):]
    return paras


_SENTENCE_END = re.compile(r"[.?!;:](?:['’\"”)]*)\s+(?=\S)")


def jowett_segments(paras: list[str], lines: list[tuple[str, str]], greek_paragraphs: set[str] | None = None,
                    reach: int = 4) -> list[tuple[str, str, bool]]:
    """(first Greek line, English, begins a paragraph) segments: Jowett's paragraphs, cut also
    where a Stephanus section begins (at the sentence end nearest to the section's place in
    proportion to the Greek of its page). A paragraph of Jowett's that begins within `reach`
    lines of a paragraph of Burnet's is taken to begin with it."""
    order = {n: i for i, (n, _t) in enumerate(lines)}
    starts = sorted(order[n] for n in (greek_paragraphs or set()) if n in order)
    # the Greek: characters before each line, by page
    by_page: dict[int, list[tuple[str, int]]] = defaultdict(list)
    for n, text in lines:
        by_page[stephanus(n)[0]].append((n, len(text)))
    # the English as one string, with paragraph starts and page marks located
    eng, para_starts, marks = "", [], {}
    for p in paras:
        if eng:
            eng += " "
        para_starts.append(len(eng))
        for piece in re.split(r"(\s*⟦\d{3}⟧\s*)", p):
            m = re.fullmatch(r"\s*⟦(\d{3})⟧\s*", piece)
            if m:
                marks[int(m.group(1))] = len(eng)
                if eng and not eng.endswith(" "):
                    eng += " "
            else:
                eng += piece
    para_set = set(para_starts)
    ends = sorted({0} | {m.end() for m in _SENTENCE_END.finditer(eng)} | para_set)
    pages = sorted(by_page)
    missing = [p for p in pages if p not in marks]
    if missing:
        raise SystemExit(f"Jowett: no page mark for Stephanus pages {missing}")

    def snap(pos: int, lo: int, hi: int) -> int:
        cands = [e for e in ends if lo <= e <= hi] or [pos]
        return min(cands, key=lambda e: abs(e - pos))

    cuts: dict[int, str] = {}  # character offset -> first Greek line of the segment
    for k, page in enumerate(pages):
        start = marks[page]
        stop = marks[pages[k + 1]] if k + 1 < len(pages) else len(eng)
        glines = by_page[page]
        total = sum(c for _n, c in glines) or 1
        before, acc = [], 0
        for n, c in glines:
            before.append(acc)
            acc += c
        # section starts, then paragraph starts within the page by proportion
        sec_cuts: list[tuple[int, str]] = []
        page_start = snap(start, start - 400, start + 400)
        sec_cuts.append((page_start, glines[0][0]))
        for (n, _c), b in zip(glines, before):
            if stephanus(n)[2] == 1 and stephanus(n)[1] != "a":
                target = start + (stop - start) * b / total
                sec_cuts.append((snap(int(target), sec_cuts[-1][0] + 1, stop), n))
        for pos, n in sec_cuts:
            cuts[pos] = n
        for ps in para_starts:
            if not (page_start < ps < stop) or ps in cuts:
                continue
            frac = (ps - start) / max(1, stop - start)
            idx = min(len(glines) - 1, bisect.bisect_right(before, frac * total) - 1)
            # never before the section the cuts put it in
            sec_n = max((n for pos, n in sec_cuts if pos <= ps), key=lambda n: _ord(n), default=glines[0][0])
            n = glines[idx][0]
            if _ord(n) < _ord(sec_n):
                n = sec_n
            near = [k for k in starts if abs(k - order[n]) <= reach]
            if near:
                n = lines[min(near, key=lambda k: abs(k - order[n]))][0]
            cuts[ps] = n
    out = []
    positions = sorted(cuts)
    last = None
    for i, pos in enumerate(positions):
        end = positions[i + 1] if i + 1 < len(positions) else len(eng)
        text = eng[pos:end].strip()
        if not text:
            continue
        n = cuts[pos]
        if last is not None and _ord(n) < _ord(last):
            n = last  # keep the anchors in order
        out.append((n, text, pos in para_set or pos == 0))
        last = n
    return out


def _ord(n: str) -> tuple[int, int, int]:
    page, letter, line = stephanus(n)
    return page, SECTIONS.index(letter), line


# ---------------------------------------------------------------- Bury

BURY_META = {
    "title": "Commentary on the Symposium",
    "author": "R. G. Bury",
    "lang": "eng",
    "source": "Perseus Digital Library, bury.symp.xml: The Symposium of Plato, edited with introduction, critical notes and commentary by R. G. Bury, Cambridge 1909",
    "license": "CC BY-SA 3.0 US",
}
INTRO_META = {
    "title": "Introduction (R. G. Bury)",
    "author": "R. G. Bury",
    "source": "Perseus Digital Library, bury.symp.xml: The Symposium of Plato, ed. R. G. Bury, Cambridge 1909, Introduction",
    "license": "CC BY-SA 3.0 US",
}


def _clean_md(md: str) -> str:
    md = re.sub(r"[ \t]+\n", "\n", md)
    md = re.sub(r"\n{3,}", "\n\n", md).strip()
    md = re.sub(r" +", " ", md)
    return re.sub(r" ([,.;:)])", r"\1", md)


def _bury_md(el) -> str:
    """Markdown of a Bury element; references to the Symposium become links to the line."""
    from lxml import etree

    from .commentary import _md

    for bibl in list(el.iter("bibl")):
        m = re.match(r"^Plat\. Sym(?:p)?\.\s*(\d{3})\s*([A-E])\b", bibl.get("n") or "")
        if m:
            target = f"{m.group(1)}{m.group(2).lower()}1"
            text = "".join(bibl.itertext()).strip()
            for child in list(bibl):
                bibl.remove(child)
            bibl.tag = "seg"  # rendered as its text
            bibl.text = f"⟦{target}|{text}⟧"
    md = _clean_md(_md(el, False))
    md = re.sub(r"\*([;:,.?!])\*", r"\1", md)
    return re.sub(r"⟦(\d{3}[a-e]1)\|([^⟧]*)⟧", r"[\2](#\1)", md)


def _skel(s: str) -> str:
    return greek.strip_diacritics(s).replace("ς", "σ").lower()


def _locate(lemma: str, words: list[tuple[str, str]], start_hint: int = 0) -> tuple[str, str] | None:
    """The first and last line of a lemma ("καὶ παίζων...περιμενεῖς") among the words of a
    passage [(skeleton, line)], searching from start_hint and then from the beginning."""
    parts = [p for p in re.split(r"\s*(?:\.\.\.|…|κτλ\.?)\s*", lemma) if p.strip()]
    if not parts:
        return None
    first = [_skel(w) for w, _s, _e in greek.words(parts[0])]
    last = [_skel(w) for w, _s, _e in greek.words(parts[-1])] if len(parts) > 1 else []
    if not first:
        return None
    skels = [w for w, _n in words]

    def find(seq: list[str], frm: int) -> int | None:
        for i in range(frm, len(skels) - len(seq) + 1):
            if skels[i : i + len(seq)] == seq:
                return i
        return None

    for frm in (start_hint, 0):
        i = find(first, frm)
        if i is None and len(first) > 1:
            i = find(first[:1], frm)  # Bury's text differs from Burnet's in places
        if i is None:
            continue
        end = i + len(first) - 1
        if last:
            j = find(last, i + len(first))
            if j is not None:
                end = j + len(last) - 1
        return words[i][1], words[min(end, len(words) - 1)][1]
    return None


def import_bury(source: Path, lines: list[tuple[str, str]], out: Path) -> tuple[int, int]:
    """Bury's commentary, each note under the line its lemma is on (the first line of its
    section where the lemma is not found). Returns (notes, notes not located)."""
    from .tei_p4 import load as load_p4

    root = load_p4(source)
    comm = next(t for t in root.iter("text") if t.get("n") == "comm")
    by_section: dict[str, list[tuple[str, str]]] = defaultdict(list)
    first_line: dict[str, str] = {}
    for n, text in lines:
        sec = section_of(n)
        first_line.setdefault(sec, n)
        for w, _s, _e in greek.words(re.sub(r"\{[^}]*\}", " ", text)):
            by_section[sec].append((_skel(w), n))
    sections = list(first_line)
    notes: list[list] = []  # [heading, [paragraphs]]
    lost = 0
    for div in comm.iter("div1"):
        sec = (div.get("n") or "").lower()
        if sec not in first_line:
            # Bury's sections are Stephanus's; a section Burnet's lines lack goes to the nearest before it
            earlier = [s for s in sections if _sec_ord(s) <= _sec_ord(sec)] if re.fullmatch(r"\d{3}[a-e]", sec) else []
            sec = earlier[-1] if earlier else sections[0]
        k = sections.index(sec)
        words = by_section[sec] + (by_section[sections[k + 1]] if k + 1 < len(sections) else [])
        hint = 0
        for p in div:
            if not isinstance(p.tag, str) or p.tag != "p":
                continue
            lemma_el = p.find("lemma")
            starts_with_lemma = lemma_el is not None and not (p.text or "").strip()
            body = _bury_md(p)
            if not body:
                continue
            if starts_with_lemma:
                from .commentary import _md

                lemma = re.sub(r"[*\\]", "", _md(lemma_el, True)).strip()
                found = _locate(lemma, words, hint)
                if found is None:
                    lost += 1
                    heading = first_line[sec]
                else:
                    a, b = found
                    heading = a if a == b else f"{a}-{b}"
                    hint = next((i for i, (_w, n) in enumerate(words) if n == a), hint)
                notes.append([heading, [body]])
            elif notes and section_of(notes[-1][0].split("-")[0]) == sec:
                notes[-1][1].append(body)
            else:
                notes.append([first_line[sec], [body]])
    # notes on the same line join; the notes are kept in the order of the text
    merged: list[list] = []
    for heading, body in notes:
        if merged and merged[-1][0] == heading:
            merged[-1][1].extend(body)
        else:
            merged.append([heading, list(body)])
    md = [f"# {k}: {v}" for k, v in BURY_META.items()] + [""]
    for heading, body in merged:
        md.append(f"## {heading}")
        md.append("\n\n".join(body))
        md.append("")
    out.write_text("\n".join(md) + "\n", encoding="utf-8")
    return len(merged), lost


def _sec_ord(sec: str) -> tuple[int, int]:
    return int(sec[:3]), SECTIONS.index(sec[3])


def import_bury_introduction(source: Path, out: Path) -> int:
    from .tei_p4 import load as load_p4

    root = load_p4(source)
    intro = next(t for t in root.iter("text") if t.get("n") == "intro")
    md = [f"# {k}: {v}" for k, v in INTRO_META.items()] + ["", "# Introduction", ""]
    count = 0

    def walk(el, level: int) -> None:
        nonlocal count
        for child in el:
            if not isinstance(child.tag, str):
                continue
            if child.tag in ("div1", "div2", "div3"):
                head = child.find("head")
                if head is not None:
                    md.append("#" * level + " " + _clean_md("".join(head.itertext())))
                    md.append("")
                    count += 1
                walk(child, level + 1)
            elif child.tag == "p":
                body = _bury_md(child)
                if body:
                    md.append(body)
                    md.append("")
            elif child.tag not in ("head", "pb", "milestone"):
                walk(child, level)

    walk(intro.find("body") if intro.find("body") is not None else intro, 2)
    out.write_text("\n".join(md).rstrip() + "\n", encoding="utf-8")
    return count
