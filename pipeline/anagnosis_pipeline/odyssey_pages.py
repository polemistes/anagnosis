"""Prepare the page-by-page transcription of Allen's Odyssey (text and apparatus).

For every page of the clean scan (homeriopera03home, homeriopera04home) this writes, under
pipeline/build/odyssey-pages/:

    p3-0021.png       the page
    p3-0021-app.png   the apparatus, enlarged
    p3-0021.md        a draft: the Perseus text of the lines on the page, with what two OCRs read
                      (the clean copy, and the Toronto copy of another printing), and the
                      Toronto OCR of the apparatus, which reads the Latin

The lines on a page are found by aligning the OCR of the verse (taken from the PDFs' text
layer) with the Perseus text. Verse and apparatus are told apart by the height of the OCR
lines: verse is set larger than the apparatus.
"""
from __future__ import annotations

import difflib
import html
import json
import re
import subprocess
from collections import Counter, defaultdict
from pathlib import Path

from . import greek
from .textfmt import parse_file

CLEAN = {3: "homeriopera03home", 4: "homeriopera04home"}
OTHER = {3: "homerioperarecog03homeuoft", 4: "homerioperarecog04homeuoft"}
VOLUME_BOOKS = {3: range(1, 13), 4: range(13, 25)}

GREEK_CHAR = re.compile(r"[Ͱ-Ͽἀ-῿]")


def _key(tok: str) -> str:
    k = greek.strip_diacritics(greek.nfc(tok)).lower().replace("ς", "σ")
    return re.sub(r"[^α-ω]", "", k)


def _tokens(text: str) -> list[str]:
    return [k for k in (_key(t) for t in re.split(r"[\s\-—]+", text)) if k]


def bbox_pages(pdf: Path) -> list[dict]:
    """Visual lines of every page: {'page', 'width', 'height', 'lines': [(y0, y1, x0, x1, text)]}."""
    out = subprocess.run(["pdftotext", "-bbox-layout", str(pdf), "-"], capture_output=True, check=True).stdout.decode("utf-8")
    pages = []
    for pno, pm in enumerate(re.finditer(r'<page width="([\d.]+)" height="([\d.]+)">(.*?)</page>', out, re.S), 1):
        frags = []
        for m in re.finditer(r'<line xMin="([\d.]+)" yMin="([\d.]+)" xMax="([\d.]+)" yMax="([\d.]+)">(.*?)</line>', pm.group(3), re.S):
            words = [html.unescape(w) for w in re.findall(r">([^<]*)</word>", m.group(5))]
            frags.append((float(m.group(2)), float(m.group(4)), float(m.group(1)), float(m.group(3)), " ".join(words)))
        # merge fragments on the same visual line
        frags.sort(key=lambda f: ((f[0] + f[1]) / 2, f[2]))
        lines: list[list] = []
        for f in frags:
            mid = (f[0] + f[1]) / 2
            if lines and abs(mid - (lines[-1][0] + lines[-1][1]) / 2) < 2.5 and abs((f[1] - f[0]) - (lines[-1][1] - lines[-1][0])) < 3:
                last = lines[-1]
                last[0], last[1] = min(last[0], f[0]), max(last[1], f[1])
                last[2], last[3] = min(last[2], f[2]), max(last[3], f[3])
                last[4].append(f)
            else:
                lines.append([f[0], f[1], f[2], f[3], [f]])
        visual = []
        for y0, y1, x0, x1, parts in lines:
            parts.sort(key=lambda p: p[2])
            visual.append((y0, y1, x0, x1, " ".join(p[4] for p in parts)))
        pages.append({"page": pno, "width": float(pm.group(1)), "height": float(pm.group(2)), "lines": visual})
    return pages


def _is_verse(line, width: float) -> bool:
    y0, y1, x0, x1, text = line
    if y1 - y0 < 7.5:
        return False
    body = _strip_number(text)
    toks = [t for t in body.split() if sum(1 for c in t if GREEK_CHAR.match(c)) >= 2]
    return len(toks) >= 3 and (x1 - x0) > width * 0.3


def _strip_number(text: str) -> str:
    return re.sub(r"\s+[\dΙΟιοΣ5]{1,3}\s*$", "", text).strip()


def align_lines(pages: list[dict], draft: list[tuple[str, str]], books) -> dict[tuple[int, int], int]:
    """(page, visual line index) -> draft line index, for the OCR lines that are verse.

    Candidate lines (tall enough, with Greek words) are aligned word by word with the draft;
    a candidate counts as verse when at least two of its words match one draft line.
    """
    idx = [i for i, (n, _) in enumerate(draft) if int(n.split(".")[0]) in books]
    dt, dline = [], []
    for i in idx:
        for k in _tokens(draft[i][1]):
            dt.append(k)
            dline.append(i)
    ot, oline = [], []
    for p in pages:
        for li, l in enumerate(p["lines"]):
            if _is_verse(l, p["width"]):
                for k in _tokens(_strip_number(l[4])):
                    ot.append(k)
                    oline.append((p["page"], li))
    votes: dict[tuple[int, int], Counter] = defaultdict(Counter)
    sm = difflib.SequenceMatcher(None, ot, dt, autojunk=False)
    for a, b, size in sm.get_matching_blocks():
        for k in range(size):
            votes[oline[a + k]][dline[b + k]] += 1
    out = {}
    for key, v in votes.items():
        di, count = v.most_common(1)[0]
        if count >= 2:
            out[key] = di
    return out


def split_page(page: dict, aligned: dict[tuple[int, int], int]) -> tuple[list, list, float | None]:
    """(verse lines, apparatus lines, y where the apparatus starts) of a page."""
    verse_ids = sorted(li for (pno, li) in aligned if pno == page["page"])
    if not verse_ids:
        return [], [], None
    verse = [page["lines"][li] for li in verse_ids]
    bottom = max(l[1] for l in verse)
    app = [l for li, l in enumerate(page["lines"])
           if li not in verse_ids and l[0] > bottom - 1 and (l[1] - l[0]) < 9.5 and (l[3] - l[2]) > page["width"] * 0.08]
    # the running foot ("HOM. III.") and the page number, and any handwriting below them
    foot = [l for l in app if re.search(r"(ΗΟΜ|ΠΟΜ|HOM|ΒΟΜ|ΠΟΝ|HoM)", l[4])]
    if foot:
        app = [l for l in app if l[0] < foot[0][0] - 1]
    app = [l for l in app if not re.fullmatch(r"\s*[\dΙΟιο]{1,3}\s*", l[4])]
    return verse, app, bottom + 1.5


def _draft_lines(texts: Path) -> list[tuple[str, str]]:
    return [(l.n, l.text) for l in parse_file(texts / "odyssey" / "grc.txt").lines]


def _pages_of_lines(aligned: dict[tuple[int, int], int], draft_ids: list[int]) -> dict[int, list[int]]:
    """Draft line indices on each page; a line no OCR line matched follows its predecessor."""
    votes: dict[int, Counter] = defaultdict(Counter)
    for (pno, _li), di in aligned.items():
        votes[di][pno] += 1
    out: dict[int, list[int]] = defaultdict(list)
    current = 0
    for i in draft_ids:
        p = votes[i].most_common(1)[0][0] if votes[i] else current
        p = max(p, current)  # a page never goes backwards
        current = p
        out[p].append(i)
    return out


def prepare(sources: Path, texts: Path, out_dir: Path, refresh_crops: bool = False) -> list[dict]:
    """Write images and drafts for every page; returns the page index (also pages.json)."""
    out_dir.mkdir(parents=True, exist_ok=True)
    draft = _draft_lines(texts)
    index = []
    for vol in (3, 4):
        books = VOLUME_BOOKS[vol]
        clean_pdf = sources / "scans" / f"{CLEAN[vol]}.pdf"
        other_pdf = sources / "scans" / f"{OTHER[vol]}.pdf"
        clean_pages = bbox_pages(clean_pdf)
        other_pages = bbox_pages(other_pdf)
        draft_ids = [i for i, (n, _) in enumerate(draft) if int(n.split(".")[0]) in books]
        clean_aligned = align_lines(clean_pages, draft, books)
        other_aligned = align_lines(other_pages, draft, books)
        on_page = _pages_of_lines(clean_aligned, draft_ids)
        other_on_page = _pages_of_lines(other_aligned, draft_ids)
        by_number = {p["page"]: p for p in clean_pages}
        other_by_number = {p["page"]: p for p in other_pages}
        clean_ocr = {}
        for (pno, li), di in sorted(clean_aligned.items()):
            clean_ocr.setdefault(di, _strip_number(by_number[pno]["lines"][li][4]))
        other_ocr = {}
        for (pno, li), di in sorted(other_aligned.items()):
            other_ocr.setdefault(di, _strip_number(other_by_number[pno]["lines"][li][4]))
        other_page_of = {i: p for p, ids in other_on_page.items() for i in ids}
        for pno in sorted(on_page):
            ids = on_page[pno]
            page = by_number[pno]
            _verse, _app, app_top = split_page(page, clean_aligned)
            stem = f"p{vol}-{pno:04d}"
            # images: the page, and the apparatus enlarged
            if not (out_dir / f"{stem}.png").exists():
                subprocess.run(["pdftoppm", "-r", "220", "-f", str(pno), "-l", str(pno), "-singlefile", "-png",
                                str(clean_pdf), str(out_dir / stem)], check=True)
            if app_top is not None and (refresh_crops or not (out_dir / f"{stem}-app.png").exists()):
                scale = 400 / 72
                y = max(0, int((app_top - 4) * scale))
                h = int((page["height"] - app_top + 4) * scale)
                subprocess.run(["pdftoppm", "-r", "400", "-f", str(pno), "-l", str(pno), "-singlefile", "-png",
                                "-y", str(y), "-H", str(h), "-x", "0", "-W", str(int(page["width"] * scale)),
                                str(clean_pdf), str(out_dir / f"{stem}-app")], check=True)
            # the Toronto copy's page with most of these lines, for its apparatus OCR
            other_pno = Counter(other_page_of.get(i) for i in ids if other_page_of.get(i)).most_common(1)
            other_app = []
            if other_pno:
                _v, other_app, _y = split_page(other_by_number[other_pno[0][0]], other_aligned)
            md = [f"# Page {stem}: Odyssey {draft[ids[0]][0]}–{draft[ids[-1]][0]}", ""]
            md.append(f"Images: {stem}.png (whole page), {stem}-app.png (apparatus, enlarged)")
            md.append("")
            md.append("## Draft of the text")
            md.append("D = Perseus text (another edition: Murray's Loeb); A = OCR of this scan; B = OCR of another printing")
            md.append("")
            for i in ids:
                n, text = draft[i]
                md.append(f"{n}\tD: {text}")
                md.append(f"\tA: {clean_ocr.get(i, '(not read)')}")
                md.append(f"\tB: {other_ocr.get(i, '(not read)')}")
            md.append("")
            md.append("## OCR of the apparatus in another printing (Latin reliable; Greek, sigla and numbers not)")
            md.append("")
            md.extend(l[4] for l in other_app)
            (out_dir / f"{stem}.md").write_text("\n".join(md) + "\n", encoding="utf-8")
            index.append({"stem": stem, "volume": vol, "pdf_page": pno, "first": draft[ids[0]][0], "last": draft[ids[-1]][0],
                          "lines": len(ids), "apparatus_found": app_top is not None})
    (out_dir / "pages.json").write_text(json.dumps(index, ensure_ascii=False, indent=1), encoding="utf-8")
    return index
