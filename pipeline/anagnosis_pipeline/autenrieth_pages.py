"""Prepare the page-by-page transcription of Autenrieth's Homeric Dictionary.

G. Autenrieth, A Homeric Dictionary for Schools and Colleges, translated by R. P. Keep, revised
by Isaac Flagg (New York: Harper, 1891), Internet Archive scan homericdictiona00aute (PIMS,
University of Toronto, 400 ppi, Greek OCR). The book is in the public domain (Autenrieth died
1900, Keep 1904, Flagg 1931).

The dictionary is printed in two columns under a running head that names the first and the
last headword of the page. For every dictionary page this writes, under
pipeline/build/autenrieth-pages/:

    a-0019.png                     the page
    a-0019-l1.png, -l2.png         the left column, enlarged, upper and lower half
    a-0019-r1.png, -r2.png         the right column, likewise
    a-0019.md                      a draft: the OCR of the running head and of each column
"""
from __future__ import annotations

import html
import json
import re
import subprocess
from pathlib import Path

SCAN = "homericdictiona00aute"
FIRST, LAST = 19, 315  # the dictionary's pages in the scan (page 1 of the book is pdf page 19)
PAGE_OFFSET = 18


def fragments(pdf: Path) -> list[dict]:
    """The OCR's words on every page: {'page', 'width', 'height', 'frags': [(y0, y1, x0, x1, text)]}.
    Words, not lines: the OCR's lines often run across the gutter from one column into the other."""
    out = subprocess.run(["pdftotext", "-bbox-layout", str(pdf), "-"], capture_output=True, check=True).stdout.decode("utf-8")
    pages = []
    word = re.compile(r'<word xMin="([\d.]+)" yMin="([\d.]+)" xMax="([\d.]+)" yMax="([\d.]+)">([^<]*)</word>')
    for pno, pm in enumerate(re.finditer(r'<page width="([\d.]+)" height="([\d.]+)">(.*?)</page>', out, re.S), 1):
        frags = [(float(m.group(2)), float(m.group(4)), float(m.group(1)), float(m.group(3)), html.unescape(m.group(5)))
                 for m in word.finditer(pm.group(3))]
        pages.append({"page": pno, "width": float(pm.group(1)), "height": float(pm.group(2)), "frags": frags})
    return pages


def _lines(frags: list) -> list[tuple]:
    """Fragments of one column merged into visual lines, top to bottom."""
    frags = sorted(frags, key=lambda f: ((f[0] + f[1]) / 2, f[2]))
    lines: list[list] = []
    for f in frags:
        mid = (f[0] + f[1]) / 2
        if lines and abs(mid - (lines[-1][0] + lines[-1][1]) / 2) < 3:
            last = lines[-1]
            last[0], last[1] = min(last[0], f[0]), max(last[1], f[1])
            last[2], last[3] = min(last[2], f[2]), max(last[3], f[3])
            last[4].append(f)
        else:
            lines.append([f[0], f[1], f[2], f[3], [f]])
    return [(y0, y1, x0, x1, " ".join(p[4] for p in sorted(parts, key=lambda p: p[2]))) for y0, y1, x0, x1, parts in lines]


def gutter(body: list, x0: float, x1: float) -> float:
    """x of the gutter between the columns: in the middle of the text block, the middle of the
    widest strip that the fewest words cover. (Not the middle of the text block: a line or a
    woodcut that sticks out on one side moves that into a column and cuts off its letters.)"""
    if not body:
        return (x0 + x1) / 2
    w = x1 - x0
    xs = [x0 + w * 0.3 + i * 0.5 for i in range(int(w * 0.4 / 0.5))]
    cover = [sum(1 for f in body if f[2] <= x <= f[3]) for x in xs]
    least = min(cover)
    best, start = (0, 0, 0), None
    for i, c in enumerate(cover + [least + 1]):
        if c == least and start is None:
            start = i
        elif c != least and start is not None:
            best = max(best, (i - start, start, i - 1))
            start = None
    return (xs[best[1]] + xs[best[2]]) / 2


def layout(page: dict) -> dict:
    """The running head, the column boundary and each column's lines."""
    frags = [f for f in page["frags"] if f[4].strip()]
    if not frags:
        return {"head": "", "left": [], "right": [], "mid": page["width"] / 2, "left_end": page["width"] / 2,
                "right_start": page["width"] / 2, "top": 0, "bottom": page["height"], "x0": 0, "x1": page["width"]}
    top_y = min(f[0] for f in frags)
    head = [f for f in frags if f[0] < top_y + 12]
    body = [f for f in frags if f[0] >= top_y + 12]
    x0 = min(f[2] for f in body) if body else 0
    x1 = max(f[3] for f in body) if body else page["width"]
    mid = gutter(body, x0, x1)
    left = [f for f in body if (f[2] + f[3]) / 2 < mid]
    right = [f for f in body if (f[2] + f[3]) / 2 >= mid]
    # where the left column's lines end and the right column's begin
    ends = sorted(f[3] for f in left)
    starts = sorted(f[2] for f in right)
    left_end = ends[int(len(ends) * 0.97)] if ends else mid
    right_start = starts[int(len(starts) * 0.03)] if starts else mid
    return {
        "head": " ".join(f[4] for f in sorted(head, key=lambda f: f[2])),
        "left": _lines(left), "right": _lines(right), "mid": mid, "left_end": left_end, "right_start": right_start,
        "top": min((f[0] for f in body), default=top_y), "bottom": max((f[1] for f in body), default=page["height"]),
        "x0": x0, "x1": x1,
    }


def _split(lines: list, top: float, bottom: float) -> float:
    """Where to cut a column in two: in the gap between the two middle lines."""
    if len(lines) < 2:
        return (top + bottom) / 2
    k = len(lines) // 2
    return (lines[k - 1][1] + lines[k][0]) / 2


def _render_page(args) -> None:
    """The page at 400 dpi, cut into the column halves, and a smaller whole page (one rendering)."""
    import tempfile

    from PIL import Image

    pdf, pno, out_dir, stem, boxes = args
    if all((out_dir / f"{name}.png").exists() for name, _box in boxes) and (out_dir / f"{stem}.png").exists():
        return
    with tempfile.TemporaryDirectory() as tmp:
        subprocess.run(["pdftoppm", "-r", "400", "-f", str(pno), "-l", str(pno), "-singlefile", "-png", str(pdf), f"{tmp}/p"], check=True)
        img = Image.open(f"{tmp}/p.png")
        s = 400 / 72
        for name, (x0, y0, x1, y1) in boxes:
            box = (max(0, int(x0 * s)), max(0, int(y0 * s)), min(img.width, int(x1 * s)), min(img.height, int(y1 * s)))
            img.crop(box).save(out_dir / f"{name}.png", optimize=True)
        img.resize((img.width * 150 // 400, img.height * 150 // 400)).save(out_dir / f"{stem}.png", optimize=True)


def prepare(sources: Path, out_dir: Path) -> list[dict]:
    from concurrent.futures import ProcessPoolExecutor

    out_dir.mkdir(parents=True, exist_ok=True)
    pdf = sources / "scans" / f"{SCAN}.pdf"
    pages = {p["page"]: p for p in fragments(pdf) if FIRST <= p["page"] <= LAST}
    index = []
    jobs = []
    for pno in sorted(pages):
        page = pages[pno]
        lay = layout(page)
        stem = f"a-{pno:04d}"
        top, bottom = lay["top"] - 6, lay["bottom"] + 4
        boxes = []
        for side, lines, x0, x1 in (("l", lay["left"], lay["x0"] - 6, max(lay["mid"] + 2, lay["left_end"] + 6)),
                                    ("r", lay["right"], min(lay["mid"] - 2, lay["right_start"] - 8), lay["x1"] + 6)):
            cut = _split(lines, top, bottom)
            for part, (y0, y1) in (("1", (top, cut + 3)), ("2", (cut - 3, bottom))):
                boxes.append((f"{stem}-{side}{part}", (x0, y0, x1, y1)))
        jobs.append((pdf, pno, out_dir, stem, boxes))
        md = [f"# Page {stem}: Autenrieth, Homeric Dictionary, page {pno - PAGE_OFFSET}", ""]
        md.append(f"Images: {stem}.png (whole page); {stem}-l1.png, {stem}-l2.png (left column, upper and lower half); "
                  f"{stem}-r1.png, {stem}-r2.png (right column, upper and lower half)")
        md += ["", "## OCR of the running head (first and last headword of the page, page number)", "", lay["head"], ""]
        md += ["## OCR of the left column (accents, italics and the Greek book letters are unreliable)", ""]
        md += [l[4] for l in lay["left"]]
        md += ["", "## OCR of the right column", ""]
        md += [l[4] for l in lay["right"]]
        (out_dir / f"{stem}.md").write_text("\n".join(md) + "\n", encoding="utf-8")
        index.append({"stem": stem, "pdf_page": pno, "page": pno - PAGE_OFFSET, "head": lay["head"],
                      "left_lines": len(lay["left"]), "right_lines": len(lay["right"])})
    (out_dir / "pages.json").write_text(json.dumps(index, ensure_ascii=False, indent=1), encoding="utf-8")
    with ProcessPoolExecutor(max_workers=8) as pool:
        list(pool.map(_render_page, jobs))
    return index
