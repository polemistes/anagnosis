"""Page images of Woodhouse's English-Greek Dictionary, for checking the OCR (woodhouse.py).

The 1910 scan woodhouse-1910-english-attic-greek-dictionary (Internet Archive, 600 ppi, from
Google) is printed in two columns. For each page asked for this writes, under
pipeline/build/woodhouse-pages/:

    p0021.png                    the page, small
    p0021-l1.png ... -l3.png     the left column at 400 dpi, in three parts, top to bottom
    p0021-r1.png ... -r3.png     the right column, likewise

The parts are cut between lines. PDF page 21 is page 15 of the book.

    python -m anagnosis_pipeline.woodhouse_pages 21 22 30-35
    python -m anagnosis_pipeline.woodhouse_pages batches     (the flags in batches, and their pages)
"""
from __future__ import annotations

import subprocess
import sys
import tempfile
from pathlib import Path

from .autenrieth_pages import fragments, layout

SCAN = "woodhouse-1910-english-attic-greek-dictionary"
DPI = 400


def _cuts(lines: list, top: float, bottom: float, parts: int = 3) -> list[float]:
    """Where to cut a column into parts: in the gaps between lines, near equal heights."""
    cuts = [top - 4]
    for k in range(1, parts):
        aim = top + (bottom - top) * k / parts
        gaps = [(lines[i][1] + lines[i + 1][0]) / 2 for i in range(len(lines) - 1)]
        cuts.append(min(gaps, key=lambda g: abs(g - aim)) if gaps else aim)
    cuts.append(bottom + 4)
    return cuts


def _render(args) -> None:
    from PIL import Image

    pdf, pno, out_dir, boxes = args
    stem = f"p{pno:04d}"
    if all((out_dir / f"{name}.png").exists() for name, _ in boxes):
        return
    with tempfile.TemporaryDirectory() as tmp:
        subprocess.run(["pdftoppm", "-r", str(DPI), "-f", str(pno), "-l", str(pno), "-singlefile", "-png", str(pdf), f"{tmp}/p"], check=True)
        img = Image.open(f"{tmp}/p.png")
        s = DPI / 72
        for name, (x0, y0, x1, y1) in boxes:
            box = (max(0, int(x0 * s)), max(0, int(y0 * s)), min(img.width, int(x1 * s)), min(img.height, int(y1 * s)))
            img.crop(box).save(out_dir / f"{name}.png", optimize=True)
        img.resize((img.width * 120 // DPI, img.height * 120 // DPI)).save(out_dir / f"{stem}.png", optimize=True)


def render(sources: Path, out_dir: Path, wanted: list[int]) -> None:
    from concurrent.futures import ProcessPoolExecutor

    out_dir.mkdir(parents=True, exist_ok=True)
    pdf = sources / "scans" / f"{SCAN}.pdf"
    pages = {p["page"]: p for p in fragments(pdf)}
    jobs = []
    for pno in wanted:
        page = pages.get(pno)
        if not page:
            continue
        lay = layout(page)
        stem = f"p{pno:04d}"
        boxes = [(stem, (0, 0, page["width"], page["height"]))]
        for side, lines, x0, x1 in (("l", lay["left"], lay["x0"] - 6, lay["mid"] + 2), ("r", lay["right"], lay["mid"] - 2, lay["x1"] + 6)):
            cuts = _cuts(lines, lay["top"], lay["bottom"])
            for k in range(3):
                boxes.append((f"{stem}-{side}{k + 1}", (x0, cuts[k] - 2, x1, cuts[k + 1] + 2)))
        jobs.append((pdf, pno, out_dir, boxes[1:]))
    with ProcessPoolExecutor(max_workers=12) as pool:
        list(pool.map(_render, jobs))


def _pages(args: list[str]) -> list[int]:
    out = []
    for a in args:
        if "-" in a:
            lo, hi = a.split("-")
            out.extend(range(int(lo), int(hi) + 1))
        else:
            out.append(int(a))
    return out


def batches(sources: Path, flags: Path, out_dir: Path, n: int = 20) -> None:
    """Splits the flags (woodhouse_qa.py) into n batches of whole pages, near equal in flags, as
    batch-01.tsv ...: <line> <kind> <token> <page> <crop> <headword> <text>, where <crop> is the
    part of the page (l1 ... r3) where the entry's headword stands, if found; and renders the pages."""
    pdf = sources / "scans" / f"{SCAN}.pdf"
    rows = [r.rstrip("\n").split("\t") for r in flags.read_text(encoding="utf-8").splitlines() if r]
    wanted = sorted({int(r[3]) for r in rows})
    pages = {p["page"]: p for p in fragments(pdf) if p["page"] in wanted}
    crops: dict[int, list[tuple[str, float, float, float, float]]] = {}
    for pno, page in pages.items():
        lay = layout(page)
        boxes = []
        for side, lines, x0, x1 in (("l", lay["left"], 0, lay["mid"]), ("r", lay["right"], lay["mid"], page["width"])):
            cuts = _cuts(lines, lay["top"], lay["bottom"])
            boxes += [(f"{side}{k + 1}", x0, cuts[k], x1, cuts[k + 1]) for k in range(3)]
        crops[pno] = boxes

    def crop_of(pno: int, headword: str) -> str:
        word = headword.split(",")[0].split(" ")[0]
        page = pages.get(pno)
        if not page:
            return ""
        for y0, y1, x0, x1, text in page["frags"]:
            if text.rstrip(",.") == word:
                for name, bx0, by0, bx1, by1 in crops[pno]:
                    if bx0 <= x0 < bx1 and by0 <= (y0 + y1) / 2 < by1:
                        return name
        return ""

    by_page: dict[int, list[list[str]]] = {}
    for r in rows:
        by_page.setdefault(int(r[3]), []).append(r)
    total = len(rows)
    out_dir.mkdir(parents=True, exist_ok=True)
    batch, size, k = [], 0, 1
    for pno in sorted(by_page):
        for r in by_page[pno]:
            batch.append([r[0], r[1], r[2], r[3], crop_of(pno, r[4]), r[4], r[5]])
        size += len(by_page[pno])
        if size >= total * k / n and k < n:
            (out_dir / f"batch-{k:02d}.tsv").write_text("".join("\t".join(b) + "\n" for b in batch), encoding="utf-8")
            batch, k = [], k + 1
    if batch:
        (out_dir / f"batch-{k:02d}.tsv").write_text("".join("\t".join(b) + "\n" for b in batch), encoding="utf-8")
    render(sources, out_dir.parent / "woodhouse-pages", wanted)


if __name__ == "__main__":
    root = Path(__file__).resolve().parent.parent
    if sys.argv[1:] == ["batches"]:
        batches(root / "sources", root / "build" / "woodhouse-flags.tsv", root / "build" / "woodhouse-batches")
    else:
        render(root / "sources", root / "build" / "woodhouse-pages", _pages(sys.argv[1:]))
