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

def read_batches(directory: Path, prefix: str = "batch-") -> dict[str, dict]:
    pages: dict[str, dict] = {}
    for path in sorted(directory.glob(f"{prefix}*.md")):
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
    pages = read_batches(path.parent, path.name.rsplit(".", 1)[0])
    grc = _grc_lines(texts, slug)
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
            if not re.match(r"^\d+[a-z]?: ours «.*» print «.*»", raw):
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
                if raw.strip():
                    preface.append(raw.strip())
                continue
            if raw.startswith("+ ") and entries[current]:
                entries[current][-1] = entries[current][-1].rstrip() + " " + raw[2:].strip()
            else:
                entries[current].append(raw)
    lines = [header]
    for n in order:
        body = "\n".join(entries[n]).strip("\n")
        body = re.sub(r"\n{3,}", "\n\n", body)
        lines.append(f"## {n}\n{body}\n")
    out.write_text("\n".join(lines), encoding="utf-8")
    return len(order), "\n\n".join(preface)
