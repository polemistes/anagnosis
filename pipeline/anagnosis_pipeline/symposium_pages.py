"""Prepare the page-by-page transcription of Burnet's Symposium (text, lines and apparatus).

Burnet's Oxford text (Platonis Opera II) is the Perseus text, but Perseus has neither his
lines nor his apparatus. For every page of the scan platonisopera02platuoft (a reprint of
about 1935, good Greek OCR) this writes, under pipeline/build/symposium-pages/:

    s-0165.png               the page
    s-0165-v1.png, -v2.png   the text, enlarged, in two halves
    s-0165-app.png           the apparatus, enlarged
    s-0165.md                a draft: the Perseus text of the Stephanus sections on the page, the
                             OCR of the page's lines, and the OCR of the apparatus in this printing
                             and in the 1910 printing (operarecognovitb02platuoft), whose OCR reads
                             the Latin well but not the Greek
"""
from __future__ import annotations

import difflib
import json
import re
import subprocess
import tarfile
from collections import Counter, defaultdict
from pathlib import Path

from lxml import etree

from . import greek
from .odyssey_pages import _tokens, bbox_pages

SCAN = "platonisopera02platuoft"
SCAN_1910 = "operarecognovitb02platuoft"
FIRST, LAST = 165, 236  # the Symposium's pages in SCAN
OFFSET_1910 = 2  # the same page in the 1910 printing is two pages later
PERSEUS = "data/tlg0059/tlg011/tlg0059.tlg011.perseus-grc2.xml"
TEI = "{http://www.tei-c.org/ns/1.0}"


def perseus_sections(sources: Path) -> list[tuple[str, str]]:
    """(section, text) of the Perseus Burnet text, speaker labels written {ΑΠΟΛ.}."""
    with tarfile.open(sources / "corpora" / "canonical-greekLit.tar.gz") as tf:
        member = next(m for m in tf if m.name.endswith(PERSEUS))
        root = etree.fromstring(tf.extractfile(member).read())
    body = root.find(f".//{TEI}body")
    out: list[list] = []
    current = None

    def walk(el):
        nonlocal current
        tag = etree.QName(el).localname
        if tag == "milestone" and el.get("unit") == "section":
            current = [el.get("n"), []]
            out.append(current)
        elif tag == "label":
            if current is not None:
                current[1].append(" {" + "".join(el.itertext()).strip() + "} ")
            return  # the label's text is not walked again
        elif tag in ("note", "bibl"):
            return
        if el.text and tag != "label" and current is not None:
            current[1].append(el.text)
        for child in el:
            walk(child)
            if child.tail and current is not None:
                current[1].append(child.tail)

    walk(body)
    return [(n, re.sub(r"\s+", " ", greek.nfc("".join(parts))).strip()) for n, parts in out]


def _text_lines(page: dict, fallback_cut: float | None = None) -> tuple[list, list, float | None]:
    """The page's text lines and apparatus lines. The apparatus is set smaller (line height 7-8
    against 9-10) and closer (8 points apart against 12), below a gap: it begins at the first
    gap below which hardly any line has the text's height. Where none is found (the OCR of the
    1910 printing draws taller boxes), the cut found on the same page of the other scan is used."""
    tall = sorted((l for l in page["lines"] if (l[1] - l[0]) >= 6 and (l[3] - l[2]) >= 25), key=lambda l: l[0])
    cut = page["height"]
    for i in range(len(tall) - 2):
        below = tall[i + 1 :]
        first_small = (below[0][1] - below[0][0]) < 9 or below[1][0] - below[0][1] < 1.6
        if (below[0][0] - tall[i][1] > 4.5 and below[0][0] > page["height"] * 0.2 and first_small
                and sum(1 for l in below if (l[1] - l[0]) >= 9) <= 2):
            cut = (tall[i][1] + below[0][0]) / 2
            break
    if cut == page["height"] and fallback_cut:
        cut = fallback_cut
    lines = [l for l in page["lines"] if (l[3] - l[2]) >= 20]
    lines = [l for l in lines if not re.search(r"ΠΛΑΤΩΝΟΣ|ΣΥΜΠΟΣΙΟΝ", l[4]) or len(l[4]) > 40]
    greek_chars = lambda t: sum(1 for c in t if "Ͱ" <= c <= "῿" or "ἀ" <= c <= "῿")
    body = [l for l in lines if l[0] < cut and (l[1] - l[0]) >= 7.5 and greek_chars(l[4]) >= 4]
    app = [l for l in lines if l[0] > cut]
    app = [l for l in app if not re.fullmatch(r"\s*[\dΙΟιοSt. ]{1,8}\s*", l[4])]
    return sorted(body, key=lambda l: l[0]), sorted(app, key=lambda l: l[0]), (cut if cut < page["height"] else None)


def prepare(sources: Path, out_dir: Path) -> list[dict]:
    out_dir.mkdir(parents=True, exist_ok=True)
    sections = perseus_sections(sources)
    pdf = sources / "scans" / f"{SCAN}.pdf"
    pdf_1910 = sources / "scans" / f"{SCAN_1910}.pdf"
    pages = {p["page"]: p for p in bbox_pages(pdf) if FIRST <= p["page"] <= LAST}
    pages_1910 = {p["page"]: p for p in bbox_pages(pdf_1910) if FIRST + OFFSET_1910 <= p["page"] <= LAST + OFFSET_1910}

    # which sections each page holds: align the OCR words of the pages with the Perseus words
    dt, dsec = [], []
    for i, (_n, text) in enumerate(sections):
        for k in _tokens(re.sub(r"\{[^}]*\}", " ", text)):
            dt.append(k)
            dsec.append(i)
    ot, opage = [], []
    for pno in sorted(pages):
        body, _app, _y = _text_lines(pages[pno])
        for l in body:
            for k in _tokens(l[4]):
                ot.append(k)
                opage.append(pno)
    votes: dict[int, Counter] = defaultdict(Counter)
    for a, b, size in difflib.SequenceMatcher(None, ot, dt, autojunk=False).get_matching_blocks():
        for k in range(size):
            votes[opage[a + k]][dsec[b + k]] += 1

    index = []
    for pno in sorted(pages):
        page = pages[pno]
        body, app, app_top = _text_lines(page)
        secs = sorted(votes[pno])
        first, last = (secs[0], secs[-1]) if secs else (0, 0)
        stem = f"s-{pno:04d}"
        scale = 400 / 72
        if not (out_dir / f"{stem}.png").exists():
            subprocess.run(["pdftoppm", "-r", "220", "-f", str(pno), "-l", str(pno), "-singlefile", "-png", str(pdf), str(out_dir / stem)], check=True)
        if body:
            top = max(0.0, body[0][0] - 14)
            bottom = app_top or (body[-1][1] + 3)
            k = len(body) // 2
            cut = (body[k - 1][1] + body[k][0]) / 2 if k > 0 else (top + bottom) / 2
            for part, (y0, y1) in (("v1", (top, cut)), ("v2", (cut - 1, bottom))):
                subprocess.run(["pdftoppm", "-r", "400", "-f", str(pno), "-l", str(pno), "-singlefile", "-png",
                                "-x", "0", "-y", str(int(y0 * scale)), "-W", str(int(page["width"] * scale)),
                                "-H", str(int((y1 - y0) * scale)), str(pdf), str(out_dir / f"{stem}-{part}")], check=True)
        if app_top is not None:
            y = int((app_top - 4) * scale)
            h = int((page["height"] - app_top + 4) * scale)
            subprocess.run(["pdftoppm", "-r", "400", "-f", str(pno), "-l", str(pno), "-singlefile", "-png",
                            "-x", "0", "-y", str(y), "-W", str(int(page["width"] * scale)), "-H", str(h),
                            str(pdf), str(out_dir / f"{stem}-app")], check=True)
        p1910 = pages_1910.get(pno + OFFSET_1910)
        app_1910 = _text_lines(p1910, app_top)[1] if p1910 else []
        md = [f"# Page {stem}: Symposium, sections {sections[first][0]}–{sections[last][0]} (approximately)", ""]
        md.append(f"Images: {stem}.png (whole page); {stem}-v1.png and {stem}-v2.png (upper and lower half of the text, enlarged); {stem}-app.png (apparatus, enlarged)")
        md.append("")
        md.append("## D: the Perseus text (Burnet's text, without his lines) of the sections on or near this page")
        md.append("")
        for i in range(max(0, first - 1), min(len(sections), last + 2)):
            md.append(f"[{sections[i][0]}] {sections[i][1]}")
        md.append("")
        md.append("## A: OCR of this page's lines (this scan; margin letters and numbers included)")
        md.append("")
        md.extend(l[4] for l in body)
        md.append("")
        md.append("## OCR of the apparatus in this printing (Greek mostly right)")
        md.append("")
        md.extend(l[4] for l in app)
        md.append("")
        md.append("## OCR of the apparatus in the 1910 printing (Latin and sigla right, Greek garbled)")
        md.append("")
        md.extend(l[4] for l in app_1910)
        (out_dir / f"{stem}.md").write_text("\n".join(md) + "\n", encoding="utf-8")
        index.append({"stem": stem, "pdf_page": pno, "first": sections[first][0], "last": sections[last][0], "lines": len(body)})
    (out_dir / "pages.json").write_text(json.dumps(index, ensure_ascii=False, indent=1), encoding="utf-8")
    return index
