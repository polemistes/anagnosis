"""The page-by-page work on Jebb's Sophocles scans: critical notes, text check, appendix.

prepare() renders the pages of each play's scan (pipeline/build/sophocles-pages/<slug>/p-NNNN.png).
The transcribers write batch files (pipeline/transcriptions/sophocles/<slug>/batch-NN.md) with
a block per page:

    === p-0110
    --- numbers
    5 ὅθεν
    10 ἱκτηρίοις
    --- differences
    12: ours «πόλει» print «πόλις»
    --- apparatus
    ## 1
    **νέα**] νέαι Blaydes.
    --- notes
    (anything uncertain)

check_batch() checks a batch: the format, the order of the notes, and the printed line numbers
against texts/<slug>/grc.txt. merge() writes texts/<slug>/commentary-jebb-apparatus.md.
"""
from __future__ import annotations

import json
import re
import subprocess
from pathlib import Path

from . import greek

# scan, the PDF pages of the play's text and of its Appendix
SCANS = {
    "ajax": ("playsfragmentswi07sophuoft", (88, 295), (297, 324)),
    "electra": ("sophoclesplaysfr06soph", (102, 299), (301, 322)),
    "oedipustyrannus": ("playsfragmentswi01sophuoft", (110, 300), (301, 334)),
    "oedipuscoloneus": ("sophocles02soph_0", (100, 363), (365, 388)),
    "philoctetes": ("playsfragmentswi04sophuoft", (76, 297), (299, 324)),
    "trachiniae": ("sophocles05soph", (80, 257), (259, 284)),
}
SCAN_EDITIONS = {
    "ajax": "first edition 1896, reprinted 1914; Internet Archive playsfragmentswi07sophuoft (University of Toronto)",
    "electra": "first edition 1894, reprinted 1907; Internet Archive sophoclesplaysfr06soph (University of Florida)",
    "oedipustyrannus": "third edition 1893, reprinted 1914; Internet Archive playsfragmentswi01sophuoft (University of Toronto)",
    "oedipuscoloneus": "second edition 1889; Internet Archive sophocles02soph_0 (Boston College)",
    "philoctetes": "second edition 1898, reprinted 1914; Internet Archive playsfragmentswi04sophuoft (University of Toronto)",
    "trachiniae": "first edition 1892; Internet Archive sophocles05soph (Boston College)",
}
WIDTH = 1600  # px, as Antigone's pages (critical notes are legible at this size)


def _render(args) -> None:
    pdf, page, out = args
    if out.exists():
        return
    tmp = out.with_suffix("")
    subprocess.run(["pdftoppm", "-f", str(page), "-l", str(page), "-singlefile", "-png", "-scale-to-x", str(WIDTH),
                    "-scale-to-y", "-1", str(pdf), str(tmp)], check=True)


def prepare(sources: Path, out_dir: Path, slugs: list[str]) -> dict:
    from concurrent.futures import ProcessPoolExecutor

    jobs, index = [], {}
    for slug in slugs:
        scan, text, appendix = SCANS[slug]
        pdf = sources / "scans" / f"{scan}.pdf"
        d = out_dir / slug
        d.mkdir(parents=True, exist_ok=True)
        pages = list(range(text[0], text[1] + 1)) + list(range(appendix[0], appendix[1] + 1))
        for p in pages:
            jobs.append((pdf, p, d / f"p-{p:04d}.png"))
        index[slug] = {"scan": scan, "text": text, "appendix": appendix}
    with ProcessPoolExecutor(max_workers=8) as pool:
        list(pool.map(_render, jobs))
    (out_dir / "pages.json").write_text(json.dumps(index, indent=1), encoding="utf-8")
    return index


# ---------------------------------------------------------------- batches

def read_batches(directory: Path, prefix: str = "batch-", files: list[Path] | None = None) -> dict[str, dict]:
    pages: dict[str, dict] = {}
    for path in files if files is not None else sorted(directory.glob(f"{prefix}*.md")):
        stem, section = None, None
        for raw in path.read_text(encoding="utf-8").splitlines():
            m = re.match(r"^=== (p-\d{4})\s*$", raw)
            if m:
                stem = m.group(1)
                pages[stem] = {"numbers": [], "differences": [], "apparatus": [], "notes": [], "batch": path.name}
                section = None
                continue
            m = re.match(r"^--- (numbers|differences|apparatus|notes)\s*$", raw)
            if m:
                section = m.group(1)
                continue
            if stem is None or section is None:
                continue
            if section == "apparatus":
                pages[stem]["apparatus"].append(raw.rstrip())
            elif raw.strip():
                pages[stem][section].append(greek.nfc(raw.strip()))
    return pages


HEADING = re.compile(r"^## (\d+[a-z]?)(?:-(\d+[a-z]?))?\s*$")


def _grc_lines(texts: Path, slug: str) -> dict[str, str]:
    out = {}
    for raw in (texts / slug / "grc.txt").read_text(encoding="utf-8").splitlines():
        m = re.match(r"^(\d+[a-z]?)\t(.*)$", raw)
        if m:
            out[m.group(1)] = m.group(2)
    return out


def _skel(s: str) -> str:
    return re.sub(r"[^α-ω]", "", greek.strip_diacritics(s).replace("ς", "σ"))


def check_batch(path: Path, texts: Path, slug: str) -> list[str]:
    out: list[str] = []
    pages = read_batches(path.parent, files=[path])
    grc = read_reference(path.parent) or _grc_lines(texts, slug)
    prev = 0
    for stem, block in pages.items():
        for raw in block["numbers"]:
            m = re.match(r"^(\d+)\s+(\S+)", raw)
            if not m:
                out.append(f"{stem} numbers: '{raw}' is not 'N firstword'")
                continue
            n, word = m.group(1), m.group(2)
            ours = grc.get(n)
            if ours is None:
                out.append(f"{stem}: printed line {n} ({word}) has no line {n} in our text")
            elif _skel(ours.split()[0] if ours.split() else "") != _skel(word):
                out.append(f"{stem}: printed line {n} begins «{word}», ours begins «{ours.split()[0]}»: numbering differs")
        for raw in block["differences"]:
            if not DIFF.match(raw):
                out.append(f"{stem} differences: '{raw}' is not 'N: ours «…» print «…»'")
        for raw in block["apparatus"]:
            m = HEADING.match(raw)
            if m:
                n = int(re.match(r"\d+", m.group(1)).group())
                if n < prev:
                    out.append(f"{stem}: apparatus note {m.group(1)} comes after {prev}")
                prev = n
            elif raw.startswith("#"):
                out.append(f"{stem}: '{raw}' is not a heading '## N' or '## N-M'")
    return out


def join_run_on(before: str, after: str) -> str:
    """A paragraph or note continued on the next page; a word divided at the page's foot
    (ἀν- | εστέναζες) is joined again."""
    before, after = before.rstrip(), after.strip()
    if re.search(r"[\u0370-\u03ff\u1f00-\u1fffA-Za-z]-$", before) and re.match(r"[\u0370-\u03ff\u1f00-\u1fffA-Za-z]", after):
        return before[:-1] + after
    return before + " " + after


def merge(directory: Path, out: Path, header: str) -> tuple[int, str]:
    """The critical notes of all batches in page order, one entry per line number; a page's
    first paragraph beginning '+ ' continues the note from the page before. Returns the number
    of notes and the note on the manuscripts that precedes the first one (*Sigla.*)."""
    pages = read_batches(directory)
    entries: dict[str, list[str]] = {}
    order: list[str] = []
    preface: list[str] = []
    current = None
    for stem in sorted(pages):
        for raw in pages[stem]["apparatus"]:
            m = HEADING.match(raw)
            if m:
                current = m.group(1) + (f"-{m.group(2)}" if m.group(2) else "")
                if current not in entries:
                    entries[current] = []
                    order.append(current)
                elif entries[current] and entries[current][-1].strip():
                    entries[current].append("")
                continue
            if current is None:
                if raw.startswith("+ ") and preface:
                    preface[-1] = join_run_on(preface[-1], raw[2:])
                elif raw.strip():
                    preface.append(raw.strip())
                continue
            if raw.startswith("+ ") and entries[current]:
                entries[current][-1] = join_run_on(entries[current][-1], raw[2:])
            else:
                entries[current].append(raw)
    lines = [header]
    for n in order:
        body = "\n".join(entries[n]).strip("\n")
        body = re.sub(r"\n{3,}", "\n\n", body)
        body = bold_lemmas(body)
        lines.append(f"## {n}\n{body}\n")
    out.write_text("\n".join(lines), encoding="utf-8")
    return len(order), "\n\n".join(preface)


def merge_appendix(directory: Path, out: Path, header: str) -> int:
    """Jebb's Appendix from the page batches (appendix-*.md, brief APPENDIX.md). Returns the
    number of notes (## headings)."""
    paras = merge_pages(directory, "appendix-")
    out.write_text(header.rstrip("\n") + "\n\n" + "\n\n".join(paras) + "\n", encoding="utf-8")
    return sum(1 for p in paras if p.startswith("## "))


def merge_pages(directory: Path, prefix: str) -> list[str]:
    """The paragraphs of prose pages transcribed in batches (<prefix>*.md: === p-NNNN blocks of
    Markdown): the pages in order, a paragraph that begins '+ ' joined to the one it continues
    (a footnote of the page before stays after it)."""
    pages: dict[str, list[str]] = {}
    for path in sorted(directory.glob(f"{prefix}*.md")):
        stem = None
        for raw in path.read_text(encoding="utf-8").splitlines():
            m = re.match(r"^=== (p-\d{4})\b", raw)
            if m:
                stem = m.group(1)
                pages[stem] = []
            elif stem is not None:
                pages[stem].append(raw.rstrip())
    paras: list[str] = []
    for stem in sorted(pages):
        for block in re.split(r"\n\s*\n", "\n".join(pages[stem])):
            rows = [r.strip() for r in block.splitlines() if r.strip()]
            while rows and rows[0].startswith("#"):
                paras.append(rows.pop(0))  # a heading written without the blank line after it
            if not rows:
                continue
            text = greek.nfc(" ".join(rows))
            if text.startswith("+ ") and paras:
                k = len(paras) - 1
                while k > 0 and paras[k].startswith("[Note:"):
                    k -= 1
                paras[k] = join_run_on(paras[k], text[2:])
            else:
                paras.append(text)
    return paras


# ---------------------------------------------------------------- the commentary (Philoctetes)

def _rule_y(path: Path) -> float | None:
    """Where the commentary begins: the thin rule under the critical notes, as a fraction of the
    page's height (on the WIDTH-px page image)."""
    from PIL import Image

    im = Image.open(path).convert("L")
    w, h = im.size
    px = im.load()
    rows = [sum(1 for x in range(0, w, 2) if px[x, y] < 140) for y in range(h)]
    half = w / 2
    for y in range(int(h * 0.12), int(h * 0.97) - 9):
        band = max(rows[y], rows[y + 1], rows[y + 2])
        if band > half * 0.45 and rows[y - 6] < half * 0.3 and rows[y + 9] < half * 0.3:
            return (y + 4) / h
    return None


def _crop_commentary(args) -> None:
    import tempfile

    from PIL import Image

    pdf, page, rule, out_dir, stem = args
    if (out_dir / f"{stem}-r2.png").exists():
        return
    with tempfile.TemporaryDirectory() as tmp:
        subprocess.run(["pdftoppm", "-f", str(page), "-l", str(page), "-singlefile", "-png", "-scale-to-x", "3000",
                        "-scale-to-y", "-1", str(pdf), f"{tmp}/p"], check=True)
        im = Image.open(f"{tmp}/p.png").convert("L")
    w, h = im.size
    top = int(rule * h) if rule is not None else int(h * 0.08)
    region = im.crop((0, top, w, h))
    px = region.load()
    rw, rh = region.size
    # the text block's edges and the gutter: columns with (almost) no ink
    ink = [sum(1 for y in range(0, rh, 3) if px[x, y] < 140) for x in range(rw)]
    inked = [x for x in range(rw) if ink[x] > 2]
    left, right = (inked[0], inked[-1]) if inked else (0, rw)
    mid_lo, mid_hi = left + (right - left) * 4 // 10, left + (right - left) * 6 // 10
    gutter = min(range(mid_lo, mid_hi), key=lambda x: (ink[x], abs(x - (left + right) // 2)))
    rows = [sum(1 for x in range(left, right, 3) if px[x, y] < 140) for y in range(rh)]
    inked_rows = [y for y in range(rh) if rows[y] > 1]
    bottom = (inked_rows[-1] + 10) if inked_rows else rh
    for side, (x0, x1) in (("l", (max(0, left - 20), gutter + 12)), ("r", (gutter - 12, min(rw, right + 20)))):
        # split the column in two at a gap between lines near its middle
        mid = bottom // 2
        gaps = [y for y in range(int(bottom * 0.4), int(bottom * 0.6)) if rows[y] == 0] or [mid]
        cut = min(gaps, key=lambda y: abs(y - mid))
        for part, (y0, y1) in (("1", (0, cut + 15)), ("2", (cut - 15, bottom))):
            region.crop((x0, y0, x1, y1)).save(out_dir / f"{stem}-{side}{part}.png", optimize=True)


def prepare_commentary(sources: Path, pages_dir: Path, slug: str) -> int:
    from concurrent.futures import ProcessPoolExecutor

    scan, text, _appendix = SCANS[slug]
    pdf = sources / "scans" / f"{scan}.pdf"
    out = pages_dir / f"{slug}-commentary"
    out.mkdir(parents=True, exist_ok=True)
    jobs = []
    for p in range(text[0], text[1] + 1):
        stem = f"p-{p:04d}"
        jobs.append((pdf, p, _rule_y(pages_dir / slug / f"{stem}.png"), out, stem))
    with ProcessPoolExecutor(max_workers=8) as pool:
        list(pool.map(_crop_commentary, jobs))
    return len(jobs)


# ---------------------------------------------------------------- the text check, applied

DIFF = re.compile(r"^(\d+[a-z]?)(\+?): ours «(.*)» print «(.*)»\s*$")


def text_check(directory: Path, prefix: str = "batch-") -> tuple[list[tuple[str, str]], list[tuple[str, bool, str, str]]]:
    """The printed line numbers (number, first word) and the differences
    (our line, insert-after?, ours, print) the batches report, in page order. With prefix
    "lines-": the second pass over the lyrics, whose differences re-divide the verses of the
    text as imported with the first (keyed by its numbers)."""
    pages = read_batches(directory, prefix)
    anchors, diffs = [], []
    for stem in sorted(pages):
        for raw in pages[stem]["numbers"]:
            m = re.match(r"^(\d+)\s+(\S+)", raw)
            if m:
                anchors.append((m.group(1), m.group(2)))
        for raw in pages[stem]["differences"]:
            m = DIFF.match(raw)
            if m:
                diffs.append((m.group(1), bool(m.group(2)), m.group(3), m.group(4)))
    return anchors, diffs


def read_reference(directory: Path) -> dict[str, str]:
    """The text the batches compared (reference-grc.txt: texts/<play>/grc.txt as it stood while
    they were made), whose line numbers their differences use: number -> text."""
    path = directory / "reference-grc.txt"
    if not path.exists():
        return {}
    out = {}
    for raw in path.read_text(encoding="utf-8").splitlines():
        m = re.match(r"^(\d+[a-z]?)\t(.*)$", raw)
        if m:
            out[m.group(1)] = m.group(2)
    return out


def bold_lemmas(text: str) -> str:
    """Jebb's lemma before ']' in bold where the transcription has it plain (the later volumes
    print it in ordinary type): at the start of a note or after a dash."""
    def repl(m: re.Match) -> str:
        lemma = m.group(2)
        if "**" in lemma or not re.search(r"[Ͱ-Ͽἀ-῿]", lemma) or re.search(r"[A-Za-z]{3,}", lemma):
            return m.group(0)
        return f"{m.group(1)}**{lemma.strip()}**]"
    return re.sub(r"(^|—\s*|\.\s{1,2})((?:(?!\.\s)[^\]\*—\n]){1,60}?)\](?=[\s,:;.])", repl, text, flags=re.M)
