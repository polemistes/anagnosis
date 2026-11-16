"""Lysias in Hude's Oxford text (1912) from the scan by OCR, with only the doubtful places left for
a reader to check (pipeline/PLAN-lysias.md, steps 1-4).

The True Story's route (lucian_pages.py) for Hude's page. Each text page is read by Tesseract
(tessdata_best grc); its words are matched to the Perseus text of the 34 speeches (Lamb's Loeb
Greek, the check text, never shipped), which gives every printed word its speech and section.
Hude prints no page numbers, so a printed line is keyed by the scan's leaf and its place on the
page: `28.5` is line 5 of leaf 28 (the page image p-0028). What Hude prints:

* a running head (the Stephanus page in brackets, ΛΥΣΙΟΥ or the speech's title, the speech's
  number): not text;
* at the head of a speech, on a fresh page, its number (a Roman numeral) and its title in
  capitals: not counted as lines; before speeches known from Dionysius, his hypothesis in smaller
  type (counted);
* the text, with the line numbers by fives (5, 10, 15 …, beginning anew on every page) in the
  inner margin (the left of a right-hand page, i.e. of an odd leaf) and the section numbers in the
  outer margin, a section beginning at the start of a line or inside it after a wider space; the
  Stephanus pages stand in square brackets in the outer margin too (not recorded);
* headings inside a speech, centred in small capitals (ΜΑΡΤΥΡΕΣ. ΝΟΜΟΣ.): counted as lines;
* the critical apparatus at the foot in small type, keyed to the page's lines ("3 εἴητε marg.
  Ald. : εἰ ἦτε C H X   6 τὰς ⟨μεγίστας⟩ Reiske"), no rule above it; a printer's signature under
  it on some pages ("LYS. 1", "1*").

    python -m anagnosis_pipeline hude-pages lysias fetch   the text leaves, as grey PNG
    python -m anagnosis_pipeline hude-pages lysias ocr     Tesseract, hOCR per leaf
    python -m anagnosis_pipeline hude-pages lysias draft   draft, crops, check sheets, batch files

Files (each saved as soon as it is made, so that a rerun goes on where it stopped):

    pipeline/build/drama-scans/<scan>/pages/leaf_0028.png       the page, grey
    pipeline/build/drama-scans/<scan>/hocr/leaf_0028.grc.hocr   Tesseract's reading (grc, --psm 4)
    pipeline/build/drama-scans/<scan>/hocr/leaf_0028.hude-margins.json   the margin numbers read
    pipeline/build/hude-pages/<slug>/p-0028.md                  the check sheet
    pipeline/build/hude-pages/<slug>/p-0028-lines.png           the flagged lines, each labelled with its key
    pipeline/build/hude-pages/<slug>/p-0028-app-l.png, -app-r.png   the apparatus, halves enlarged
    pipeline/build/hude-pages/<slug>/pages.json, draft.json
    pipeline/transcriptions/<slug>/batch-NN.md                  six pages each, never overwritten

The batch file, per page:

    === p-0028
    --- text
    28.1	τῶν ἐσομένων ἐκείνῃ τῇ νυκτί, οὓς οἷός τε ἦ παρέλαβον. Καί
    28.2	μοι ἀνάβητε τούτων μάρτυρες.
    28.3	[label] ΜΑΡΤΥΡΕΣ.
    ¶
    28.4	§1.43 Τῶν μὲν μαρτύρων ἀκηκόατε, ὦ ἄνδρες· σκέψασθε δὲ
    --- apparatus
    1	ἦν L
    10	⟨ἂν⟩ αὐτὸν Francken
    --- notes

`§1.43` stands before the word where a section begins (speech.section; Hude's section number in
the margin), `¶` on a line of its own before a line he indents, `[label] ` after the TAB of a
heading inside a speech, `[hypothesis] ` after the TAB of a line of Dionysius's hypothesis, and a
speech's number and title as lines without a key (`[title]<TAB>ΥΠΕΡ ΤΟΥ ΕΡΑΤΟΣΘΕΝΟΥΣ ΦΟΝΟΥ`).
The apparatus items carry the line number as printed (3, 22-23; `-` for a note that names no
line); an item printed without a number belongs to the line of the item before it and is given
that number.
"""
from __future__ import annotations

import json
import os
import re
import subprocess
import sys
import tempfile
import unicodedata
from collections import Counter
from concurrent.futures import ThreadPoolExecutor
from functools import lru_cache
from pathlib import Path

from . import greek
from .drama import APOS, PLAYS, Play, skel
from .lucian_pages import SECTION_MARK, _lowercase, fold, perseus_prose, read_batches  # noqa: F401  (read_batches: the batch format is the True Story's)

ROOT = Path(__file__).resolve().parent.parent.parent
PIPELINE = ROOT / "pipeline"
TESSDATA = PIPELINE / "tessdata"
PAGES_PER_BATCH = 6
ROUTE = "hude-pages"
SPEECHES = 34
LABEL, HYPOTHESIS, TITLE = "[label]", "[hypothesis]", "[title]"
# Pages the scan keeps only as the camera's whole frame (the book on its mat between two rulers,
# 3744 x 5616 pixels): the page's rectangle in the frame, (left, top, right, bottom). The page
# image is cut to it once, so that it looks like every other page of the scan.
FRAMES: dict[str, dict[int, tuple[int, int, int, int]]] = {
    "orationesrecogno00lysi": {36: (1050, 700, 3470, 4460), 37: (195, 670, 2570, 4410),
                               44: (1050, 700, 3490, 4470), 45: (210, 660, 2575, 4400)},
}


def out_dir(slug: str) -> Path:
    from .drama_pages import route_dir

    return route_dir(ROUTE, slug, PLAYS[slug].scan)


def transcriptions_dir(slug: str) -> Path:
    return PIPELINE / "transcriptions" / slug


# --- the check text: the 34 speeches of the Perseus Lysias ------------------------------------------

def check_file(play: Play, sources: Path, speech: int) -> Path:
    return sources / "drama" / f"{play.tlg}.tlg{speech:03d}.perseus-grc2.xml"


def check_tokens(play: Play, sources: Path) -> tuple[list[dict], list[dict]]:
    """The words of the 34 speeches in order, as lucian_pages.perseus_prose gives a work's (the
    section of a word is speech.section: '12.7'), with Lamb's footnotes; a quotation is in ‘ ’,
    the words of a heading (Μάρτυρες) carry 'heading': True."""
    toks: list[dict] = []
    notes: list[dict] = []
    for k in range(1, SPEECHES + 1):
        t, n = perseus_prose(check_file(play, sources, k), book=str(k), quotes=True, headings=True)
        for x in n:
            if x["after"] >= 0:
                x["after"] += len(toks)
        toks += t
        notes += n
    return toks, notes


@lru_cache(maxsize=2)
def _check_sections(slug: str, sources: str) -> dict[str, list[str]]:
    toks, _notes = check_tokens(PLAYS[slug], Path(sources))
    out: dict[str, list[str]] = {}
    for t in toks:
        out.setdefault(t["sec"], []).append(t["t"])
    return out


def check_sections(play: Play, sources: Path) -> dict[str, list[str]]:
    """Each section's words (as written, headings included), in order."""
    return _check_sections(play.slug, str(sources))


# --- fetch, OCR, the page ---------------------------------------------------------------------

def cut_frames(scan: str) -> list[int]:
    """The page images of the leaves in FRAMES cut to the page (once: a page image narrower than
    the camera's frame has been cut already). Returns the leaves cut now."""
    from PIL import Image

    from .drama_pages import fetch_leaf

    done = []
    for leaf, box in FRAMES.get(scan, {}).items():
        png = fetch_leaf(scan, leaf)
        with Image.open(png) as im:
            if im.size[0] <= box[2]:
                continue
            page = im.crop(box)
        page.save(str(png) + ".part.png")
        os.replace(str(png) + ".part.png", png)
        done.append(leaf)
    return done


def run(slug: str, step: str, workers: int | None = None) -> None:
    from .drama_pages import fetch_leaf, ocr_leaf

    play = PLAYS[slug]
    leaves = play.visible("text")
    workers = workers or int(os.environ.get("DRAMA_WORKERS", "4"))
    out_dir(slug)
    with ThreadPoolExecutor(workers) as ex:
        if step == "fetch":
            list(ex.map(lambda l: fetch_leaf(play.scan, l), leaves))
            cut_frames(play.scan)
        elif step == "ocr":
            cut_frames(play.scan)  # before Tesseract sees them
            list(ex.map(lambda l: ocr_leaf(play.scan, l), leaves))
        else:
            raise SystemExit(f"unknown step {step!r}")
    print(f"{slug}: {step} done for {len(leaves)} leaves")


def _line_text(words: list[dict]) -> str:
    return " ".join(w["text"] for w in sorted(words, key=lambda w: w["bbox"][0]))


def is_numeral(text: str) -> bool:
    """A speech's number as Tesseract reads it: I, XII, XXXIV, in Latin or Greek look-alike
    letters (ΙΠ for II, ΧΙΝ for XIV, ὟΥΙ for XXI: the accents are not looked at)."""
    d = unicodedata.normalize("NFD", text.strip().rstrip(".").replace(" ", ""))
    t = "".join(c for c in d if not unicodedata.combining(c))
    return bool(t) and len(t) <= 7 and re.fullmatch(r"[IVXLΙΧΥΛΠΝΨ1l|]+", t) is not None


def to_roman(n: int) -> str:
    out = ""
    for value, letters in ((10, "X"), (9, "IX"), (5, "V"), (4, "IV"), (1, "I")):
        while n >= value:
            out += letters
            n -= value
    return out


def is_caps(text: str) -> bool:
    """A line in capitals: a speech's title, a heading inside a speech (ΜΑΡΤΥΡΕΣ.)."""
    letters = [c for c in text if c.isalpha()]
    return len(letters) >= 4 and sum(c.isupper() for c in letters) >= 0.8 * len(letters)


def _lower_words(text: str) -> int:
    return sum(1 for w in text.split() if len(skel(w)) >= 2 and sum(c.islower() for c in w) >= 0.6 * sum(c.isalpha() for c in w))


def _solid(l: dict) -> bool:
    """An OCR line of print (not the thin rows of accents Tesseract reads apart, nor a speck)."""
    return l["bbox"][3] - l["bbox"][1] >= 40 and any(len(re.sub(r"\W", "", w["text"])) >= 2 and w["conf"] >= 30 for w in l["words"])


def head_bottom(lines: list[dict], H: int) -> int | None:
    """Where the running head ends: Hude's head ("[92] ΛΥΣΙΟΥ [I", "I] ΥΠΕΡ ΤΟΥ … [93]") is the
    topmost line of print on every page but a speech's first, where the print begins lower (the
    speech's number stands a tenth of the page down or more). The pages of the scan are not cut
    alike, so the head's place is measured on each page. None on a speech's first page."""
    # (the head's spaced capitals and bracketed figures are often read with no confidence at all)
    type_ = [l for l in lines if l["bbox"][3] - l["bbox"][1] >= 40 and l["x_size"] >= 40]
    big = sorted((l for l in type_ if any(len(re.sub(r"\W", "", w["text"])) >= 2 for w in l["words"])), key=lambda l: l["bbox"][1])
    if not big or big[0]["bbox"][1] > 0.09 * H:
        return None
    top = big[0]
    band = [l for l in type_ if top["bbox"][1] - 20 <= l["bbox"][1] < top["bbox"][3] - 0.3 * (top["bbox"][3] - top["bbox"][1])]
    return max(l["bbox"][3] for l in band)


def apparatus_top(lines: list[dict], W: int, H: int, head_y: int) -> tuple[int | None, int | None]:
    """Where Hude's apparatus begins and ends, (top, bottom), or (None, None) on a page without
    one. There is no rule above it, and neither sign of it is sure alone: Tesseract sizes a last
    line of text as small as the apparatus now and then, and its boxes for the apparatus's lines
    are uneven. But the lines of the apparatus stand closer together than the lines of the text
    (two thirds of their pitch), and the text ends a good line and a half above it. From the foot
    of the page upwards a line is taken as apparatus if it stands within the apparatus's pitch of
    the line below, or is in the small type and within a text line and a third of it; a single
    line at the foot (the two or three words under a speech's last lines) is apparatus if it is
    lower than the text's lines and a gap stands above it."""
    from .drama_pages import _signature

    wide = [l for l in lines if _solid(l) and l["bbox"][1] > head_y and l["bbox"][2] - l["bbox"][0] >= 0.25 * W
            and not _signature(l, W, H)]
    wide.sort(key=lambda l: l["bbox"][1])
    if len(wide) < 2:
        return None, None
    upper = wide[: max(3, len(wide) // 2)]
    steps = sorted(b["bbox"][1] - a["bbox"][1] for a, b in zip(upper, upper[1:]) if b["bbox"][1] - a["bbox"][1] > 20)
    heights = sorted(l["bbox"][3] - l["bbox"][1] for l in upper)
    if not steps:
        return None, None
    pitch, height = steps[len(steps) // 2], heights[len(heights) // 2]
    sizes = sorted(l["x_size"] for l in upper if l["x_size"] > 0)
    size = sizes[len(sizes) // 2] if sizes else 0
    # from the lowest line of print, however short; a stray mark under the apparatus (a library's
    # stamp, a pencilled number) is passed over
    foot = sorted((l for l in lines if _solid(l) and l["bbox"][1] > head_y and not _signature(l, W, H)), key=lambda l: -l["bbox"][1])
    block: list[dict] = []
    for lowest in foot[:3]:
        block = [lowest]
        for l in reversed([x for x in wide if x["bbox"][1] < lowest["bbox"][1] - 10]):
            step = block[-1]["bbox"][1] - l["bbox"][1]
            if step <= 0.78 * pitch or (step <= 1.3 * pitch and 0 < l["x_size"] <= 0.92 * size):
                block.append(l)
            else:
                break
        if len(block) > 1:
            break
        above = [x for x in wide if x["bbox"][1] < lowest["bbox"][1] - 10]
        gap = lowest["bbox"][1] - above[-1]["bbox"][1] if above else 0
        if gap > 1.25 * pitch and lowest["bbox"][3] - lowest["bbox"][1] <= 0.92 * height and lowest["bbox"][1] < 0.93 * H:
            break
        block = []
    if not block:
        return None, None
    top = min(l["bbox"][1] for l in block)
    # short lines at the foot (the apparatus's last words) belong to it; the signature does not
    low = [l for l in lines if l["bbox"][1] >= top and _solid(l) and not _signature(l, W, H)]
    sigs = [l for l in lines if l["bbox"][1] > top and _signature(l, W, H)]
    bottom = max(l["bbox"][3] for l in low) + int(0.4 * height)
    for sg in sigs:
        if sg["bbox"][1] > max(l["bbox"][1] for l in block):
            bottom = min(bottom, sg["bbox"][1] - 4)
    return top - int(0.2 * height), min(H - 5, bottom)


def page_layout(play: Play, leaf: int) -> dict:
    """drama_pages.page_layout, with the running head and the apparatus found as Hude's page has
    them (head_bottom, apparatus_top); the lines of the text block it passed over as noise put
    back (a short last line of a paragraph read with little confidence; a speech's Roman
    numeral); a line Tesseract read twice left out; and each line's kind: 'title' (the number and
    title at the head of a speech, on a page without a running head) or 'text'; 'caps' marks a
    line in capitals (a heading inside a speech)."""
    import dataclasses

    from PIL import Image

    from .drama_pages import ocr_leaf, page_layout as drama_layout, read_lines, scan_dirs

    _, sbuild = scan_dirs(play.scan)
    with Image.open(sbuild / "pages" / f"leaf_{leaf:04d}.png") as im:
        W, H = im.size
    ocr_lines = read_lines(ocr_leaf(play.scan, leaf))
    head = head_bottom(ocr_lines, H)
    head_y = head + 3 if head is not None else int(0.005 * H)
    app_y, app_end = apparatus_top(ocr_lines, W, H, head_y)
    lay = drama_layout(dataclasses.replace(play, head_frac=(head_y + 1) / H), leaf, app_y=app_y if app_y is not None else H - 5)
    lay["app_y"], lay["app_end"] = app_y, app_end
    lay["head_y"] = head_y
    lh = lay["line_h"]
    text_end = app_y if app_y is not None else int(0.95 * H)
    lay["lines"] = [q for q in lay["lines"] if (q["y0"] + q["y1"]) / 2 < text_end]
    mid = (lay["left"] + lay["right"]) / 2
    margin = 0.3 * lh
    for l in ocr_lines:
        x0, y0, x1, y1 = l["bbox"]
        if y0 <= head_y or y1 > text_end + 0.3 * lh or (y1 - y0) < 0.45 * lh:
            continue
        if any(min(y1, q["y1"]) - max(y0, q["y0"]) > 0.3 * (y1 - y0) for q in lay["lines"]):
            continue
        words = [w for w in l["words"] if w["bbox"][2] >= lay["left"] - margin and w["bbox"][0] <= lay["right"] + margin]
        text = _line_text(words)
        centred = bool(words) and abs((words[0]["bbox"][0] + words[-1]["bbox"][2]) / 2 - mid) < 0.06 * W
        lettered = any(len(skel(w["text"])) >= 4 and w["conf"] >= 40 for w in words)
        if not (lettered or (centred and is_numeral(text))):
            continue
        lay["lines"].append({"y0": y0, "y1": y1, "oy0": y0, "oy1": y1, "words": words, "left_m": [], "right_m": [],
                             "x0": min(w["bbox"][0] for w in words), "x1": max(w["bbox"][2] for w in words), "put_back": True})
    lay["lines"].sort(key=lambda q: q["y0"])
    # a line Tesseract read twice: the scraps of a line ("ρ ή γὰρ μ μμάχ") set over half of it
    kept: list[dict] = []
    for q in lay["lines"]:
        if kept:
            k = kept[-1]
            over = min(q["y1"], k["y1"]) - max(q["y0"], k["y0"])
            if over > 0.4 * min(q["y1"] - q["y0"], k["y1"] - k["y0"]):
                nq, nk = len(skel(_line_text(q["words"]))), len(skel(_line_text(k["words"])))
                if nq < 0.5 * nk:
                    continue
                if nk < 0.5 * nq:
                    kept[-1] = q
                    continue
        kept.append(q)
    lay["lines"] = kept
    lay["start_page"] = head is None
    in_title = lay["start_page"]
    hyp_from = None
    for k, q in enumerate(lay["lines"]):
        text = _line_text(q["words"])
        q["caps"] = is_caps(text)
        if in_title and _lower_words(text) >= 3:
            in_title = False
        q["kind"] = "title" if in_title else "text"
        if in_title and re.search(r"ΠΟΘΕ[ΣC]", label_form(text)):
            hyp_from = k + 1
    if hyp_from is not None:
        # Dionysius's hypothesis under its heading, in smaller type set closer: its lines run on
        # at their own pitch; the speech begins after a wider step
        rest = lay["lines"][hyp_from:]
        steps = [b["y0"] - a["y0"] for a, b in zip(rest, rest[1:])]
        if len(steps) >= 3:
            own = sorted(steps[:3])[1]
            for a, step in zip(rest, steps + [10 ** 6]):
                a["kind"] = "hypothesis"
                if step > 1.3 * own:
                    break
    # a numeral put back anywhere but in a title block is noise
    lay["lines"] = [q for q in lay["lines"] if not (q.get("put_back") and q["kind"] == "text" and is_numeral(_line_text(q["words"])))]
    return lay


# --- the margins --------------------------------------------------------------------------------

def _clusters(rows: list[int], gap: int, low: int) -> list[tuple[int, int]]:
    """Runs of rows that hold ink (more than `low` dark pixels), joined across fewer than `gap`
    blank rows: [(first row, last row + 1)]."""
    out: list[tuple[int, int]] = []
    start = last = None
    for y, v in enumerate(rows):
        if v > low:
            if start is None:
                start = y
            elif y - last > gap:
                out.append((start, last + 1))
                start = y
            last = y
    if start is not None:
        out.append((start, last + 1))
    return out


def margin_marks(play: Play, layout: dict) -> list[dict]:
    """The numbers printed in both margins beside the text: [{'y' (centre), 'side' ('l'/'r'),
    'kind' ('line', 'section', 'stephanus'), 'n' (None where no number could be read)}]. Each
    margin, a strip beyond the column, is divided into its clusters of ink (a number; a Stephanus
    page set over or under a section number makes two); each cluster is cut out, enlarged and
    read by Tesseract's English model limited to digits, three ways, the commonest reading kept
    (cached). Hude's old-style figures are often misread (10 as 1, 3 as 8), so the place of a
    number is what the draft relies on. On an odd leaf (a right-hand page) the line numbers stand
    left and the section numbers and Stephanus pages right; on an even leaf the other way round.
    A Stephanus page is told by its square brackets, which stand taller than any figure."""
    from PIL import Image, ImageOps

    from .drama_pages import scan_dirs

    _, sbuild = scan_dirs(play.scan)
    leaf = layout["leaf"]
    cache = sbuild / "hocr" / f"leaf_{leaf:04d}.hude-margins.json"
    if cache.exists():
        raw = json.loads(cache.read_text())
    else:
        H = layout["line_h"]
        env = dict(os.environ, OMP_THREAD_LIMIT="1")
        raw = []
        body = [p for p in layout["lines"] if p["kind"] == "text"]
        ends = sorted(max(w["bbox"][2] for w in ws) for p in body
                      if (ws := [w for w in p["words"] if len(skel(w["text"])) >= 2]))
        col_r = ends[len(ends) // 2] if ends else layout["right"]
        col_l = layout["left"]
        if body:
            top = max(0, min(p["oy0"] for p in body) - H)
            bottom = (layout["app_y"] - 4) if layout["app_y"] is not None else min(layout["height"], max(p["oy1"] for p in body) + H)
            with Image.open(sbuild / "pages" / f"leaf_{leaf:04d}.png") as im, tempfile.TemporaryDirectory() as t:
                g = im.convert("L")
                W = g.size[0]
                reach = int(0.115 * W)
                for side in ("l", "r"):
                    x0, x1 = (max(8, col_l - reach), col_l - 8) if side == "l" else (col_r + 8, min(W - 8, col_r + reach))
                    if x1 - x0 < H or bottom - top < H:
                        continue
                    strip = g.crop((x0, top, x1, bottom))
                    ink = strip.point(lambda v: 255 if v < 140 else 0)
                    w = strip.size[0]
                    rows = [round(v * w / 255) for v in ink.resize((1, strip.size[1]), Image.BOX).tobytes()]
                    for a, b in _clusters(rows, gap=int(0.12 * H), low=1):
                        if b - a < 0.25 * H or b - a > 2.4 * H:
                            continue
                        parts = [(a, b)]
                        if b - a > 1.25 * H:
                            # two numbers set one over the other: cut at the emptiest row near the middle
                            lo, hi = a + (b - a) // 3, b - (b - a) // 3
                            cut = min(range(lo, hi), key=lambda y: rows[y])
                            parts = [(a, cut), (cut, b)]
                        for ya, yb in parts:
                            cols = list(ink.crop((0, ya, w, yb)).resize((w, 1), Image.BOX).tobytes())
                            xs = [x for x, v in enumerate(cols) if v > 6]
                            if not xs or xs[-1] - xs[0] < 0.12 * H or xs[-1] - xs[0] > 3.2 * H:
                                continue
                            piece = strip.crop((max(0, xs[0] - 10), max(0, ya - 8), min(w, xs[-1] + 10), min(strip.size[1], yb + 8)))
                            piece = ImageOps.expand(piece.resize((piece.size[0] * 2, piece.size[1] * 2), Image.LANCZOS), 40, fill=255)
                            path = Path(t) / "n.png"
                            piece.save(path)
                            reads = []
                            for psm in ("7", "8", "13"):
                                out = subprocess.run(["tesseract", str(path), "stdout", "--tessdata-dir", str(TESSDATA), "-l", "eng", "--psm", psm,
                                                      "-c", "tessedit_char_whitelist=0123456789"], capture_output=True, text=True, env=env).stdout.strip()
                                if re.fullmatch(r"\d{1,3}", out.replace(" ", "")):
                                    reads.append(int(out.replace(" ", "")))
                            n = Counter(reads).most_common(1)[0][0] if reads else None
                            raw.append([top + (ya + yb) // 2, side, n, yb - ya, xs[-1] - xs[0]])
        cache.write_text(json.dumps(raw))
    inner = "l" if leaf % 2 == 1 else "r"
    marks = []
    for y, side, n, h, _w in raw:
        if side == inner:
            kind = "line"
        else:
            kind = "stephanus" if h >= 0.94 * layout["line_h"] else "section"
        marks.append({"y": y, "side": side, "kind": kind, "n": n})
    return marks


# --- the OCR's words ---------------------------------------------------------------------------

def ocr_stream(layouts: list[dict]) -> tuple[list[dict], list[dict]]:
    """The printed lines of the text in order ({'leaf', 'y0', 'y1', 'oy0', 'oy1', 'x0', 'indent',
    'line_h', 'ocr', 'kind' ('title'/'hypothesis'/'text'), 'caps', 'centred'}) and the OCR's
    words ({'t', 'skel', 'line', 'conf'}). A word divided at the end of a line is joined and
    belongs to the line where it begins (unless that would leave the next line without a word of
    its own). The lines of a title and of a hypothesis have no words (the check text has neither)."""
    from .drama_pages import DASHES, ocr_norm

    lines: list[dict] = []
    toks: list[dict] = []
    for lay in layouts:
        mid = (lay["left"] + lay["right"]) / 2
        for p in lay["lines"]:
            ws = sorted(p["words"], key=lambda w: w["bbox"][0])
            text = " ".join(w["text"] for w in ws)
            li = len(lines)
            # where the line's words begin (a one-letter word, ὦ ἄνδρες, counts if Tesseract is sure of it)
            x0 = min((w["bbox"][0] for w in ws if len(skel(w["text"])) >= 2 or (skel(w["text"]) and w["conf"] >= 40)), default=p["x0"])
            centred = abs((p["x0"] + p["x1"]) / 2 - mid) < 0.06 * lay["width"] and (p["x1"] - p["x0"]) < 0.8 * (lay["right"] - lay["left"])
            lines.append({"leaf": lay["leaf"], "y0": p["y0"], "y1": p["y1"], "oy0": p.get("oy0", p["y0"]), "oy1": p.get("oy1", p["y1"]),
                          "x0": x0, "indent": x0 - lay["left"], "line_h": lay["line_h"], "ocr": ocr_norm(text),
                          "kind": p["kind"], "caps": p["caps"], "centred": centred, "start_page": lay["start_page"]})
            if p["kind"] in ("title", "hypothesis"):
                continue
            for w in ws:
                for piece in DASHES.split(ocr_norm(w["text"])):
                    if not piece.strip():
                        continue
                    if not skel(piece) and toks and toks[-1]["line"] == li and re.fullmatch(r"[.,·;:'\"”᾽˙’]+", piece.strip()):
                        toks[-1]["t"] += piece.strip()  # a stop read apart from its word; the dots of a lacuna
                        continue
                    toks.append({"t": piece, "skel": skel(piece), "line": li, "conf": w["conf"]})
    count = Counter(t["line"] for t in toks if t["skel"])
    for k, t in enumerate(toks):
        last = k + 1 == len(toks) or toks[k + 1]["line"] != t["line"]
        t["hyph"] = last and t["t"].rstrip().endswith(("-", "‐", "¬")) and len(t["skel"]) > 0
    joined: list[dict] = []
    for t in toks:
        if joined and joined[-1].get("hyph") and t["line"] > joined[-1]["line"] and t["skel"]:
            prev = joined[-1]
            prev["t"] = prev["t"].rstrip().rstrip("-‐¬") + t["t"]
            prev["skel"] = skel(prev["t"])
            prev["hyph"] = False
            prev["joined"] = True
            if count[t["line"]] == 1:
                prev["line"] = t["line"]
            continue
        joined.append(t)
    return lines, [t for t in joined if t["skel"]]


# --- the draft ---------------------------------------------------------------------------------

def label_form(word: str) -> str:
    """A heading of the check text as Hude sets it: capitals without accents (Μάρτυρες → ΜΑΡΤΥΡΕΣ)."""
    d = unicodedata.normalize("NFD", word)
    return unicodedata.normalize("NFC", "".join(c for c in d if not unicodedata.combining(c))).upper().strip(".,·;:")


def number_lines(lines: list[dict], pers: list[dict]) -> list[dict]:
    """Hude's lines with their keys: {'n' ('28.5', or '[title]' for a line of a speech's title),
    'leaf', 'count', 'kind' ('title', 'text', 'label', 'hypothesis', 'extra'), 'words' (check-text
    indexes), 'line' (printed line), 'starts' ([(index, section)] of the sections that begin on
    the line), 'flags'}. The lines of a page are counted from the top of the text: a speech's
    number and title are not counted, a heading inside a speech (ΜΑΡΤΥΡΕΣ.) and the lines of a
    hypothesis are. A printed line on which no word of the check text was placed is kept with
    Tesseract's reading if it holds words (a hypothesis; a heading or words the check text
    lacks), and passed over if it holds none (flagged on the line before)."""
    by_line: dict[int, list[int]] = {}
    for j, t in enumerate(pers):
        by_line.setdefault(t["line"], []).append(j)
    out: list[dict] = []
    count: dict[int, int] = {}
    seen_text: set[int] = set()   # leaves on which a line of the speech itself has stood
    pending: list[str] = []   # notes on left-out words that fell on a line of a title
    for li, pl in enumerate(lines):
        every = by_line.get(li, [])
        words = [j for j in every if not pers[j].get("left_out")]
        leaf = pl["leaf"]
        for j in every:
            if "left_out_run" in pers[j]:
                size, first, last, secs = pers[j]["left_out_run"]
                pending.append(f"{size} words of the check text (“{first} … {last}”) are not on the page here and were left out of the draft"
                               + (f", with the beginning of its section{'s' if len(secs) > 1 else ''} {', '.join(secs)}" if secs else "")
                               + ": if Hude prints them (here or on a line near), type them from the image; number the sections as his margin does")
        if pl["kind"] == "title" and not words:
            out.append({"n": TITLE, "leaf": leaf, "count": 0, "kind": "title", "words": [], "line": li, "starts": [], "flags": []})
            continue
        flags: list[str] = pending
        pending = []
        if pl["kind"] == "hypothesis" and not words:
            kind = "hypothesis"
            flags.append("a line of the hypothesis (not in the check text): type it from the image")
        elif not words:
            letters = len(skel(pl["ocr"]))
            if letters < 5:
                if letters >= 2:
                    pl["dropped"] = True
                pending = flags
                continue
            if pl["caps"] and pl["centred"]:
                kind = "label"
                flags.append("a heading in capitals that the check text does not have here: check it is printed, and its letters")
            elif pl["start_page"] and leaf not in seen_text:
                kind = "hypothesis"
                flags.append("a line of the hypothesis (not in the check text): type it from the image")
            else:
                kind = "extra"
                flags.append("this printed line matched no words of the check text: if it is a line of the text, type it "
                             "from the image; if it is not (a smudge, a margin note), delete it and renumber")
        else:
            kind = "label" if all(pers[j].get("heading") for j in words) else "text"
            seen_text.add(leaf)
        count[leaf] = count.get(leaf, 0) + 1
        c = count[leaf]
        starts = [(j, pers[j]["sec"]) for j in words if pers[j]["newsec"]]
        if len(starts) > 1:
            flags.append(f"two sections begin on this line ({', '.join(s for _j, s in starts)})")
        out.append({"n": f"{leaf}.{c}", "leaf": leaf, "count": c, "kind": kind, "words": words, "line": li,
                    "starts": starts, "flags": flags})
    return out


def check_margins(play: Play, numbered: list[dict], lines: list[dict], layouts: dict[int, dict]) -> None:
    """The keys against Hude's line numbers, the sections against his section numbers."""
    by_leaf: dict[int, list[dict]] = {}
    for L in numbered:
        if L["kind"] != "title":
            by_leaf.setdefault(L["leaf"], []).append(L)

    def centre(L: dict) -> float:
        return (lines[L["line"]]["oy0"] + lines[L["line"]]["oy1"]) / 2

    for leaf, Ls in by_leaf.items():
        lay = layouts[leaf]
        marks = margin_marks(play, lay)
        pitch = lay["line_h"] * 1.25
        seen_line: set[int] = set()
        seen_sec: set[int] = set()
        off_line: list[dict] = []
        loose: list[tuple[dict, dict]] = []   # section numbers beside a line where no section begins
        page_secs = {int(sec.split(".")[1]) for L in Ls for _j, sec in L["starts"]}
        for mk in marks:
            near = min(Ls, key=lambda L: abs(centre(L) - mk["y"]))
            dist = abs(centre(near) - mk["y"])
            n = mk["n"]
            shown = "?" if n is None else str(n)
            if mk["kind"] == "line":
                if dist > 0.6 * pitch:
                    continue
                near.setdefault("marks", []).append(f"line {shown}")
                if near["count"] % 5 == 0:
                    # a number at a fifth line confirms it, whatever Tesseract made of the figures
                    seen_line.add(id(near))
                else:
                    off_line.append(near)
            elif mk["kind"] == "section":
                # a section number set over or under a Stephanus page stands half a line off
                starting = [L for L in Ls if L["starts"] and abs(centre(L) - mk["y"]) <= 0.8 * pitch]
                if starting:
                    best = min(starting, key=lambda L: abs(centre(L) - mk["y"]))
                    best.setdefault("marks", []).append(f"section {shown}")
                    seen_sec.add(id(best))
                elif dist <= 0.8 * pitch:
                    near.setdefault("marks", []).append(f"section {shown}")
                    loose.append((mk, near))
            elif dist <= 0.8 * pitch:
                near.setdefault("marks", []).append(f"Stephanus [{shown}]")
        # numbers beside lines that are not fifth lines: if the page's fifth lines went without, the count is off
        missing = [L for L in Ls if L["count"] % 5 == 0 and id(L) not in seen_line]
        for L in off_line:
            if missing:
                L["flags"].append(f"the margin has a line number at this line, which is {L['n']} by the count: count the page's lines")
        for L in Ls:
            if L["count"] % 5 == 0 and id(L) not in seen_line:
                L["flags"].append(f"no line number read in the margin, though {L['n']} should have one ({L['count']})")
            if L["starts"] and id(L) not in seen_sec:
                # Hude's number beside a line near by: the editions begin the section at different words
                by = [(mk, near) for mk, near in loose if abs(centre(near) - centre(L)) <= 2.2 * pitch]
                if by:
                    mk, near = min(by, key=lambda x: abs(centre(x[1]) - centre(L)))
                    loose.remove((mk, near))
                    L["flags"].append(f"the check text begins section {L['starts'][-1][1]} on this line, but Hude's section number seems to "
                                      f"stand beside {near['n']}: put the § mark on Hude's line (the brief: where a section begins)")
                    near["flags"].append(f"Hude's section number seems to stand beside this line (the check text begins section "
                                         f"{L['starts'][-1][1]} on {L['n']})")
                else:
                    L["flags"].append(f"no section number read in the margin, though section {L['starts'][-1][1]} begins on this line")
        for mk, near in loose:
            n = mk["n"]
            if n is not None and (n in page_secs or any(n - 1 <= x <= n + 1 for x in page_secs)):
                near["flags"].append(f"the margin has a section number (read “{n}”) at this line, "
                                     "but the check text begins no section here")


def line_texts(numbered: list[dict], lines: list[dict], ocr: list[dict], pers: list[dict], match: list[int | None]) -> None:
    """Each line's text (L['text']) with its § marks, paragraphs (L['para']), and the flags that
    come from comparing the words with the OCR."""
    from .drama_pages import _accent_letters, _capitalise, _starts_upper

    paired_o = {o for o in match if o is not None}
    by_line_o: dict[int, list[int]] = {}
    for k, t in enumerate(ocr):
        by_line_o.setdefault(t["line"], []).append(k)
    # the speech that begins on a page (its section 1 begins there), for the numeral of its title
    begins: dict[int, int] = {}
    for L in numbered:
        for _j, sec in L["starts"]:
            if sec.endswith(".1") and L["leaf"] not in begins:
                begins[L["leaf"]] = int(sec.split(".")[0])
    numeral_seen: set[int] = set()
    for L in numbered:
        pl = lines[L["line"]]
        flags = L["flags"]
        L["para"] = False
        if L["kind"] == "title":
            text = re.sub(r"\s*(?:[5S]teph\.?|\[?\d{1,3}\]?)\s*$", "", pl["ocr"]).strip()
            text = re.sub(r"\s*(?:[5S]teph\.?)\s*", " ", text).strip()
            speech = begins.get(L["leaf"])
            first = L["leaf"] not in numeral_seen
            numeral_seen.add(L["leaf"])
            if first and speech and (is_numeral(text) or len(skel(text)) <= 5):
                # the first line of the title block is the speech's number: Tesseract reads the
                # Roman numerals badly (ΧΧῚΙ, ΙΠ), the number is known from the check text
                L["text"] = to_roman(speech)
                flags.append(f"the speech's number: {to_roman(speech)} by the check text (the OCR reads “{pl['ocr']}”); check the print")
            else:
                L["text"] = label_form(text)
                flags.append("the speech's title: check every letter against the print (capitals, no accents)"
                             + (f"; the speech's number ({to_roman(speech)}) was not read: add it above as the first [title] line" if first and speech else ""))
            continue
        if L["kind"] in ("hypothesis", "extra"):
            L["text"] = (HYPOTHESIS + " " if L["kind"] == "hypothesis" else "") + pl["ocr"]
            continue
        if L["kind"] == "label" and not L["words"]:
            L["text"] = f"{LABEL} {label_form(pl['ocr'])}."
            continue
        out: list[str] = []
        moved = False
        for j in L["words"]:
            t = pers[j]
            w = t["t"]
            o = match[j]
            if t.get("left_out"):
                continue  # noted on the line by number_lines
            moved = moved or bool(t.get("moved"))
            if t.get("heading"):
                w = label_form(w)
            elif o is not None and t["sim"] >= 0.8:
                # the case of the first letter as printed (Hude begins a new train of thought with
                # a capital, also inside a line: "αὐτήν. Πρῶτον μὲν οὖν"; Lamb does not)
                if _starts_upper(ocr[o]["t"]) and not _starts_upper(w):
                    w = _capitalise(w)
                elif not _starts_upper(ocr[o]["t"]) and _starts_upper(w) and ocr[o]["conf"] >= 90 and t["sim"] == 1.0:
                    w = _lowercase(w)
            if t["newsec"]:
                out.append(f"§{t['sec']}")
            if t.get("glued") and out and not out[-1].startswith("§"):
                out[-1] += w
            else:
                out.append(w)
            if o is None:
                flags.append(f"{w}: not found in the OCR; check it is printed" + (", and on which line" if t.get("guess") else " on this line"))
            elif t["sim"] < 1.0:
                # also where Tesseract was unsure: the check text is another edition, and a reading
                # of Hude's own (ἑορακυῖα for ἑωρακυῖα) may hide behind a doubtful reading
                flags.append(f"{w}: the OCR{'' if ocr[o]['conf'] >= 70 else ', unsure,'} reads “{ocr[o]['t']}”")
            elif t["sim"] == 1.0 and len(t["skel"]) >= 4 and ocr[o]["conf"] >= 95 and not t.get("heading") and not t.get("run_on"):
                if _accent_letters(w) != _accent_letters(ocr[o]["t"]):
                    flags.append(f"{w}: the OCR reads “{ocr[o]['t']}” (accents)")
            if t.get("guess") and o is not None:
                flags.append(f"{w}: which line it stands on is a guess")
            if t.get("gap"):
                flags.append(f"{w}: the check text marks a gap (lost text) after this word; copy what Hude prints (. . .)")
        for k in by_line_o.get(L["line"], []):
            # a word Hude prints and Lamb lacks; a short one (ἣ, καὶ, μὲν) only where Tesseract is sure of it
            if k not in paired_o and (len(ocr[k]["skel"]) >= 4 and ocr[k]["conf"] >= 80 or
                                      ocr[k]["conf"] >= 90 and SHORT_WORD.match(ocr[k]["t"]) and re.search("[αεηιουω]", ocr[k]["skel"])):
                flags.append(f"the OCR reads “{ocr[k]['t']}” on this line, which the check text does not have here")
        text = " ".join(out)
        if L["kind"] == "label":
            text = f"{' '.join(out)}."
        if moved:
            flags.append("these words stand in another place in the check text: Hude prints them here; number the sections as his margin does")
        for f in bracket_flags(text, pl["ocr"]):
            flags.append(f)
        if "‘" in text or "’" in text:
            flags.append("the check text has quotation marks on this line: copy Hude's (‘ ’) where he prints them")
        if re.search(r"\.\s*\.\s*\.", pl["ocr"]) and not any(pers[j].get("gap") for j in L["words"]):
            flags.append("the OCR reads a row of dots on this line (a lacuna?): copy what Hude prints (. . .)")
        if L["kind"] == "label":
            L["text"] = f"{LABEL} {text}"
            continue
        L["para"] = pl["indent"] > 0.95 * pl["line_h"] and not pl["centred"]  # Hude indents by a line's height and a fifth; a lost first letter is less
        L["text"] = text
    real = [L for L in numbered if L["kind"] != "title"]
    for k, L in enumerate(real):
        nxt = real[k + 1]["line"] if k + 1 < len(real) else len(lines)
        for li in range(L["line"] + 1, nxt):
            if lines[li].get("dropped"):
                L["flags"].append(f"below this line the OCR read “{lines[li]['ocr'][:60]}”, which was passed over: "
                                  "check that no printed line is missing")


SHORT_WORD = re.compile(r"^[Ͱ-Ͽἀ-῿ʼ]{1,4}[.,·;:]?$")
MOVE_MIN = 15      # words: a passage the print has in another place than the check text
LEFT_OUT_MIN = 8   # words: a run of the check text that the page does not show is left out of the draft
# Tesseract's readings of Hude's δʼ (the apostrophe taken for a breathing or an accent)
DELTA_ELIDED = {"ὃ", "ὅ", "ὁ", "δ", "δ᾽", "δʼ", "ὃʼ", "δ'", "ὃ᾽"}


def transposed(ocr: list[dict], pers: list[dict], match: list[int | None]) -> list[tuple[int, int, int]]:
    """Passages the print has in another place than the check text (Hude prints 13.65-66 after
    13.68): a run of check words that matched nothing and, within a few pages, a run of printed
    words that matched nothing and are the same words. [(first, end) of the run in the check
    text, the index it is to stand before], for build_draft to move the words and align again."""
    import difflib

    def runs(flags: list[bool]) -> list[tuple[int, int]]:
        out, start = [], None
        for i, f in enumerate(flags + [False]):
            if f and start is None:
                start = i
            elif not f and start is not None:
                if i - start >= MOVE_MIN:
                    out.append((start, i))
                start = None
        return out

    paired = {o for o in match if o is not None}
    lost = runs([m is None for m in match])
    extra = runs([k not in paired for k in range(len(ocr))])
    by_ocr = {o: j for j, o in enumerate(match) if o is not None}
    moves = []
    for a, b in lost:
        words = [t["skel"] for t in pers[a:b]]
        for c, d in extra:
            nxt = next((by_ocr[k] for k in range(d, len(ocr)) if k in by_ocr), len(pers))
            if abs(nxt - a) > 3000 or a <= nxt <= b:
                continue
            if difflib.SequenceMatcher(None, words, [t["skel"] for t in ocr[c:d]], autojunk=False).ratio() >= 0.7:
                moves.append((a, b, nxt))
                break
    return moves


def mend(ocr: list[dict], pers: list[dict], match: list[int | None]) -> None:
    """Two things Tesseract does on Hude's page that would flag a sound line: it reads δʼ as ὃ
    (the check word δʼ is paired with such a reading standing free in its place), and it runs two
    words together (ὑπὸτῶν: both words are paired with the one reading)."""
    paired = {o for o in match if o is not None}
    n = len(pers)
    for j, t in enumerate(pers):
        if match[j] is not None:
            continue
        before = next((match[k] for k in range(j - 1, max(-1, j - 6), -1) if match[k] is not None), None)
        after = next((match[k] for k in range(j + 1, min(n, j + 6)) if match[k] is not None), None)
        if t["skel"] == "δ" and before is not None and after is not None:
            free = [o for o in range(before + 1, after) if o not in paired and ocr[o]["t"].strip(".,·;:") in DELTA_ELIDED]
            if len(free) == 1:
                match[j] = free[0]
                paired.add(free[0])
                t["sim"] = 1.0
                continue
        for k, joined in ((j - 1, lambda a, b: a + b), (j + 1, lambda a, b: b + a)):
            if 0 <= k < n and match[k] is not None and pers[k].get("sim", 0) < 1.0:
                first, second = (pers[k], t) if k < j else (t, pers[k])
                if ocr[match[k]]["skel"] == first["skel"] + second["skel"]:
                    match[j] = match[k]
                    t["sim"] = pers[k]["sim"] = 1.0
                    t["run_on"] = pers[k]["run_on"] = True
                    break


def left_out(pers: list[dict], match: list[int | None]) -> None:
    """Runs of LEFT_OUT_MIN or more check words that matched nothing on the page (a passage Hude
    does not print, or prints in another form): marked 'left_out' with the run's size on its
    first word, so that the draft notes them once instead of writing them into a line."""
    j, n = 0, len(pers)
    while j < n:
        if match[j] is not None:
            j += 1
            continue
        k = j
        while k < n and match[k] is None:
            k += 1
        if k - j >= LEFT_OUT_MIN:
            for x in range(j, k):
                pers[x]["left_out"] = True
            pers[j]["left_out_run"] = (k - j, " ".join(t["t"] for t in pers[j:j + 4]), " ".join(t["t"] for t in pers[k - 3:k]),
                                       sorted({t["sec"] for t in pers[j:k] if t["newsec"]}, key=lambda s_: [int(x) for x in s_.split(".")]))
        j = k


def bracket_flags(text: str, ocr: str) -> list[str]:
    """Flags on a line's brackets. Tesseract reads Hude's angle brackets ⟨ ⟩ as round ones, so the
    two kinds are counted together: the OCR's opening round or angle brackets against the
    draft's; square brackets by whether the line has any (one that Tesseract sets inside a word,
    "Τ]ειραιᾶ" for Πειραιᾶ, is a misread letter)."""
    flags = []
    o_round = len(re.findall(r"[(<〈⟨]", ocr))
    d_round = len(re.findall(r"[(⟨]", text))
    if o_round > d_round:
        flags.append("the OCR shows more round or angle brackets on this line than the check text has: copy Hude's "
                     "(Tesseract reads his ⟨ ⟩ as ( ); look which kind is printed)")
    elif d_round > o_round:
        flags.append("the check text has round or angle brackets on this line that the OCR does not show: check the print")
    o_square = bool(re.search(r"(?:^|\s)\[|\](?:[\s.,·;:]|$)", ocr))
    d_square = "[" in text or "]" in text
    if o_square and not d_square:
        flags.append("the OCR shows square brackets on this line, the check text has none: copy Hude's")
    elif d_square and not o_square:
        flags.append("the check text has square brackets on this line, the OCR shows none: check the print")
    return flags


def build_draft(play: Play, sources: Path) -> tuple[list[dict], dict[int, dict], list[dict], list[dict]]:
    from .drama_pages import realign
    from .gorgias_pages import align, assign_lines

    leaves = play.visible("text")
    workers = int(os.environ.get("DRAMA_WORKERS", "4"))
    with ThreadPoolExecutor(workers) as ex:
        layouts = dict(zip(leaves, ex.map(lambda l: page_layout(play, l), leaves)))
        list(ex.map(lambda l: margin_marks(play, layouts[l]), leaves))
    lines, ocr = ocr_stream([layouts[l] for l in leaves])
    fold(play, lines, ocr)
    pers, _notes = check_tokens(play, sources)
    if play.skel_fold:
        tr = str.maketrans(play.skel_fold[0::2], play.skel_fold[1::2])
        for t in pers:
            t["skel"] = t["skel"].translate(tr)
    match = align(ocr, pers)
    moves = transposed(ocr, pers, match)
    if moves:
        # the check text's words in the print's order (from the end, so that the indexes hold)
        for a, b, at in sorted(moves, reverse=True):
            block = pers[a:b]
            for t in block:
                t["moved"] = True
            del pers[a:b]
            at = at - (b - a) if at > a else at
            pers[at:at] = block
            print(f"{play.slug}: {block[0]['sec']}–{block[-1]['sec']} ({b - a} words) stand before {pers[at + len(block)]['sec']} "
                  "in the print: moved in the check text", file=sys.stderr)
        match = align(ocr, pers)
    mended = realign(ocr, pers, match)
    if mended:
        print(f"{play.slug}: {mended} stretches aligned again", file=sys.stderr)
    mend(ocr, pers, match)
    left_out(pers, match)
    found = [j for j, o in enumerate(match) if o is not None]
    lo = max(0, found[0] - 12) if found else 0
    hi = min(len(pers), found[-1] + 13) if found else 0
    if lo > 0 or hi < len(pers):
        print(f"{play.slug}: the pages hold {pers[lo]['sec']}–{pers[hi - 1]['sec']} of the check text; "
              f"{lo} words before and {len(pers) - hi} after were not found", file=sys.stderr)
    sub, subm = pers[lo:hi], match[lo:hi]
    assign_lines(lines, ocr, sub, subm)
    numbered = number_lines(lines, sub)
    check_margins(play, numbered, lines, layouts)
    line_texts(numbered, lines, ocr, sub, subm)
    for L in numbered:
        pl = lines[L["line"]]
        L["y0"], L["y1"], L["ocr"] = pl["y0"], pl["y1"], pl["ocr"]
        L["flags"] = list(dict.fromkeys(L["flags"]))
    return numbered, layouts, lines, sub


def batch_lines(Ls: list[dict]) -> list[str]:
    """A page's lines as the batch file has them."""
    out = []
    for L in Ls:
        if L["para"]:
            out.append("¶")
        out.append(f"{L['n']}\t{L['text']}")
    return out


def write_draft(slug: str, sources: Path, transcriptions: Path) -> list[dict]:
    """The check sheets, crops, pages.json and draft.json; the batch files that do not exist yet."""
    from .drama_pages import apparatus_images, lines_image

    play = PLAYS[slug]
    od = out_dir(slug)
    numbered, layouts, _lines, _pers = build_draft(play, sources)
    by_leaf: dict[int, list[dict]] = {}
    for L in numbered:
        by_leaf.setdefault(L["leaf"], []).append(L)
    index = []
    leaves = play.visible("text")
    # Tesseract's two readings of each apparatus are the slow part: made side by side (and kept)
    with ThreadPoolExecutor(int(os.environ.get("DRAMA_WORKERS", "4"))) as ex:
        list(ex.map(lambda l: apparatus_images(play, l, layouts[l], od, f"p-{l:04d}") if layouts[l]["app_y"] is not None else {}, leaves))
    for b, leaf in enumerate(leaves):
        Ls = by_leaf.get(leaf, [])
        counted = [L for L in Ls if L["kind"] != "title"]
        stem = f"p-{leaf:04d}"
        for old in od.glob(f"{stem}-*.png"):
            old.unlink()
        lay = layouts[leaf]
        app = apparatus_images(play, leaf, lay, od, stem) if lay["app_y"] is not None else {}
        flagged = [L for L in Ls if L["flags"]]
        has_lines = lines_image(play, leaf, flagged, od / f"{stem}-lines.png")
        odd = leaf % 2 == 1
        md = [f"# Leaf {leaf} ({stem}): lines {counted[0]['n']}–{counted[-1]['n']}" if counted else f"# Leaf {leaf} ({stem})", ""]
        imgs = [f"pages/leaf_{leaf:04d}.png (the whole page)"]
        if has_lines:
            imgs.append(f"{stem}-lines.png (the flagged lines, each with its key)")
        if app:
            imgs.append(f"{stem}-app-l.png and {stem}-app-r.png (the apparatus, left and right half, enlarged)")
        md.append("Images: " + "; ".join(imgs))
        md.append("")
        md.append(f"This is a {'right' if odd else 'left'}-hand page: the line numbers (5, 10, 15 …) stand in the "
                  f"{'left' if odd else 'right'} margin, the section numbers (and the Stephanus pages, in square brackets) in the "
                  f"{'right' if odd else 'left'}.")
        if lay["app_y"] is None:
            md.append("")
            md.append("**No apparatus was found on this page**: check the foot of the page; if it prints none, say so under notes.")
        md.append("")
        md.append("## Flags on the text")
        md.append("")
        if flagged:
            for L in flagged:
                md.append(f"* {L['n']}  `{L['text']}`")
                for f in L["flags"]:
                    md.append(f"    * {f}")
        else:
            md.append("None: the OCR agrees with the check text on every line, and the margins with the keys.")
        md.append("")
        md.append("## The lines of the page (the draft) beside Tesseract's reading of them")
        md.append("")
        for L in Ls:
            marks = f"   [margin: {', '.join(L.get('marks', []))}]" if L.get("marks") else ""
            md.append(f"{L['n']}\t{L['text']}\n\t\tOCR: {L['ocr']}{marks}")
        md.append("")
        md.append(f"## Tesseract's readings of the apparatus ({play.app_langs[0]}; {play.app_langs[1]}). Both garble sigla and numbers")
        if app:
            for key in ("first", "second"):
                md.append("")
                md.append("```")
                md.append(app.get(key, ""))
                md.append("```")
        else:
            md.append("")
            md.append("(no apparatus found on this page)")
        (od / f"{stem}.md").write_text("\n".join(md) + "\n", encoding="utf-8")
        index.append({"stem": stem, "leaf": leaf, "page": leaf, "first": counted[0]["n"] if counted else None,
                      "last": counted[-1]["n"] if counted else None, "lines": len(counted), "flagged": len(flagged),
                      "flags": sum(len(L["flags"]) for L in Ls), "titles": sum(1 for L in Ls if L["kind"] == "title"),
                      "batch": b // PAGES_PER_BATCH + 1, "apparatus": bool(app),
                      "sections": [s for L in Ls for _j, s in L["starts"]]})
    (od / "pages.json").write_text(json.dumps(index, ensure_ascii=False, indent=1), encoding="utf-8")
    (od / "draft.json").write_text(json.dumps(
        [{k: L.get(k) for k in ("n", "leaf", "kind", "text", "para", "flags", "y0", "y1", "ocr", "marks")} for L in numbered],
        ensure_ascii=False, indent=0), encoding="utf-8")
    transcriptions.mkdir(parents=True, exist_ok=True)
    for b in range(0, len(leaves), PAGES_PER_BATCH):
        path = transcriptions / f"batch-{b // PAGES_PER_BATCH + 1:02d}.md"
        if path.exists():
            continue
        out = []
        for leaf in leaves[b: b + PAGES_PER_BATCH]:
            out.append(f"=== p-{leaf:04d}")
            out.append("--- text")
            out += batch_lines(by_leaf.get(leaf, []))
            out.append("--- apparatus")
            out.append("--- notes")
            out.append("")
        path.write_text("\n".join(out), encoding="utf-8")
    return index


# --- reading and checking a batch -------------------------------------------------------------

KEY = re.compile(r"^(\d+)\.(\d+)$")
# an apparatus item's number: 3, a range 22-23 (or 8, 9), or - for a note on no line; the groups
# are those of lucian_pages.APP_KEY (first line, range end, second line), so that
# lucian_merge.place_apparatus reads both
APP_KEY = re.compile(r"^(?:(\d+)(?:-(\d+)|, (\d+))?|-)$")
MARKER = re.compile(r"^\[(?:label|hypothesis)\]\s*")


def plain(text: str) -> str:
    """A batch line's Greek without the markers (§1.7, [label], [hypothesis])."""
    return SECTION_MARK.sub(" ", MARKER.sub("", text))


def quote_remarks(text: str, open_: bool) -> tuple[list[str], bool]:
    """Remarks on the elision signs and quotation marks of a line, and whether a quotation is
    open after it. Elision is ʼ (U+02BC); ‘ opens and ’ closes a quotation (Hude's single
    marks), so a ’ counts as a closing mark only while a quotation is open. (Hude sets a new ‘
    before a sentence inside a quotation that is still open, "πεύσει. ‘ἔστι δʼ’ ἔφη
    ‘Ἐρατοσθένης": the marks are not counted, a quotation is open or it is not.)"""
    remarks: list[str] = []
    if re.search(r"[᾽']", text):
        remarks.append("elision written other than ʼ (U+02BC), or a quotation mark written ' (‘ ’ are Hude's)")
    for c in text:
        if c == "‘":
            open_ = True
        elif c == "’":
            if open_:
                open_ = False
            else:
                remarks.append("a ’ where no quotation is open: elision is ʼ (U+02BC); a quotation begins with ‘")
    return remarks, open_


def check_batch(slug: str, path: Path, sources: Path) -> list[str]:
    """Remarks on one checked batch file: pages missing or foreign, keys that do not run on,
    section marks out of order, apparatus numbers naming no line of the page, elision and
    quotation marks, NFC, divided words, spaces before punctuation, and every place where the
    words differ from the check text (each a change made on checking; '(noted)' where the page's
    notes name the line)."""
    import difflib

    play = PLAYS[slug]
    index = json.loads((out_dir(slug) / "pages.json").read_text(encoding="utf-8"))
    pages = read_batches(path.parent, files=[path])
    m = re.search(r"batch-(\d+)", path.name)
    expected = [p["stem"] for p in index if m and p.get("batch") == int(m.group(1))]
    by_stem = {p["stem"]: p for p in index}
    remarks: list[str] = []
    for stem in expected:
        if stem not in pages:
            remarks.append(f"{stem}: missing from the batch")
    for stem in pages:
        if stem not in expected:
            remarks.append(f"{stem}: not a page of this batch")
    words: list[tuple[str, str, str]] = []  # (skel, word, key)
    secs: list[str] = []
    noted: set[str] = set()
    prev_sec: tuple[int, int] | None = None
    open_quotes = False
    for stem, block in pages.items():
        for e in block["errors"]:
            remarks.append(f"{stem}: {e}")
        leaf = by_stem[stem]["leaf"] if stem in by_stem else None
        for raw in block["notes"]:
            mm = re.match(r"^(\d+\.\d+|\d+)", raw)
            if mm:
                noted.add(mm.group(1) if "." in mm.group(1) else f"{leaf}.{mm.group(1)}")
        count = 0
        para = False
        for key, text in block["text"]:
            if key == "¶":
                para = True
                continue
            if key == TITLE:
                if text != unicodedata.normalize("NFC", text):
                    remarks.append(f"{stem} {key}: not NFC")
                if not text.strip():
                    remarks.append(f"{stem}: an empty [title] line")
                if count:
                    remarks.append(f"{stem}: a [title] line after line {count}: a speech's title stands at the head of its page")
                para = False
                continue
            mm = KEY.match(key)
            if not mm:
                remarks.append(f"{stem}: bad key {key!r} (leaf.line, or [title])")
                continue
            if leaf is not None and int(mm.group(1)) != leaf:
                remarks.append(f"{stem} {key}: the leaf is {leaf}")
            count += 1
            if int(mm.group(2)) != count:
                remarks.append(f"{stem} {key}: line {count} of the page by its place: the numbering does not run on")
            if text != unicodedata.normalize("NFC", text):
                remarks.append(f"{stem} {key}: not NFC")
            if not text.strip():
                remarks.append(f"{stem} {key}: an empty line")
            body = MARKER.sub("", text)
            if re.search(r"\[(?!label\]|hypothesis\])[a-z]+\]", text) or (text.startswith("[") and not MARKER.match(text) and re.match(r"^\[[a-z]", text)):
                remarks.append(f"{stem} {key}: an unknown marker (only [label] and [hypothesis])")
            if para and MARKER.match(text) and text.startswith(LABEL):
                remarks.append(f"{stem} {key}: ¶ before a heading (a heading is centred, not a paragraph)")
            para = False
            qr, open_quotes = quote_remarks(body, open_quotes)
            for r in qr:
                remarks.append(f"{stem} {key}: {r}")
            if re.search(r"[Ͱ-Ͽἀ-῿]-\s*$", body):
                remarks.append(f"{stem} {key}: a divided word? write it whole on the line where it begins")
            if re.search(r"\s[,·;:]", plain(text)) or re.search(r"[^\s.]\s\.(?!\s*\.)", plain(text)):
                remarks.append(f"{stem} {key}: a space before a stop")
            if re.search(r"§(?!\d+\.\d+\s)", text + " "):
                remarks.append(f"{stem} {key}: a section mark not written §speech.section followed by a space")
            if text.startswith(HYPOTHESIS):
                continue  # the hypothesis is not in the check text
            for mk in SECTION_MARK.finditer(text):
                cur = (int(mk.group(1)), int(mk.group(2)))
                if text.startswith(LABEL):
                    remarks.append(f"{stem} {key}: a section mark on a heading's line (it stands before the first word after the heading)")
                if prev_sec is not None and not (cur == (prev_sec[0], prev_sec[1] + 1) or cur == (prev_sec[0] + 1, 1)):
                    remarks.append(f"{stem} {key}: section {cur[0]}.{cur[1]} follows {prev_sec[0]}.{prev_sec[1]}")
                prev_sec = cur
            # the words, each with the section it stands in
            pos = 0
            for mk in list(SECTION_MARK.finditer(body)) + [None]:
                chunk = body[pos: mk.start() if mk else len(body)]
                for w, _s, _e in greek.words(chunk):
                    words.append((skel(w), w, key))
                if mk is not None:
                    secs.append(f"{mk.group(1)}.{mk.group(2)}")
                    pos = mk.end()
        if count and stem in by_stem and abs(count - by_stem[stem]["lines"]) > 2:
            remarks.append(f"{stem}: {count} lines, the draft had {by_stem[stem]['lines']}")
        if count and not block["apparatus"] and not any("no apparatus" in x for x in block["notes"]):
            remarks.append(f"{stem}: no apparatus (if the page prints none, say “no apparatus on this page” under notes)")
        last_n = 0
        for n, item in block["apparatus"]:
            mm = APP_KEY.match(n)
            if not mm:
                remarks.append(f"{stem}: bad apparatus number {n!r} (3, 22-23, or - for a note on no line)")
                continue
            if n != "-":
                a, b = int(mm.group(1)), int(mm.group(2) or mm.group(3) or mm.group(1))
                if not (1 <= a <= max(count, 1)) or b < a or b > count:
                    remarks.append(f"{stem}: apparatus {n} names a line not on this page (it has {count})")
                if a < last_n:
                    remarks.append(f"{stem}: apparatus {n} after {last_n}: the items stand in the order of the lines")
                last_n = a
            if item != unicodedata.normalize("NFC", item):
                remarks.append(f"{stem} {n}: apparatus not NFC")
            if not item.strip():
                remarks.append(f"{stem} {n}: an empty apparatus item")
            if re.match(r"^\d+\s", item):
                remarks.append(f"{stem} {n}: the item begins with a number: one item per line, its line number before the TAB")
            if re.search(r"[᾽']", item):
                remarks.append(f"{stem} {n}: apparatus: elision written other than ʼ (U+02BC)")
    # wording against the check text, over the sections the batch touches (and the one before its first mark)
    if words:
        sections = check_sections(play, sources)
        order = list(sections)
        if secs:
            first = order.index(secs[0]) if secs[0] in order else 0
            last = order.index(secs[-1]) if secs[-1] in order else len(order) - 1
            span = order[max(0, first - 1): last + 1]
        else:
            span = order
        pw = [(skel(piece), piece) for s in span for t in sections[s] for piece in re.split(r"[—–]+", t) if skel(piece)]
        if play.skel_fold:
            tr = str.maketrans(play.skel_fold[0::2], play.skel_fold[1::2])
            pw = [(a.translate(tr), b) for a, b in pw]
            words = [(a.translate(tr), b, c) for a, b, c in words]
        ours = [w[0] for w in words]
        sm = difflib.SequenceMatcher(None, ours, [p[0] for p in pw], autojunk=False)
        for op, a0, a1, b0, b1 in sm.get_opcodes():
            if op == "equal":
                continue
            if op == "insert" and (a0 == 0 or a0 == len(ours)):
                continue  # the batch begins or ends inside a section
            if op == "replace" and (a0 == 0 or a1 == len(ours)) and b1 - b0 > a1 - a0:
                cut = pw[b1 - (a1 - a0):b1] if a0 == 0 else pw[b0:b0 + (a1 - a0)]
                if [p[0] for p in cut] == ours[a0:a1]:
                    continue
                b0, b1 = (b1 - (a1 - a0), b1) if a0 == 0 else (b0, b0 + (a1 - a0))
            where = words[a0][2] if a0 < len(words) else words[-1][2]
            mine = " ".join(w[1] for w in words[a0:a1]) or "(nothing)"
            theirs = " ".join(p[1] for p in pw[b0:b1]) or "(nothing)"
            tag = " (noted)" if where in noted else ""
            remarks.append(f"{where}: written {mine} | the check text has {theirs}{tag}")
    return remarks


def known_misreading(r: dict) -> bool:
    """A residual that is one of Tesseract's standing misreadings of this print, not a question
    for a reader: the raised stop read as an apostrophe (διοικοῦσαʼ for διοικοῦσα·), δʼ read as ὃ,
    Hude's angle brackets read as round ones (the review reads the brackets' kind)."""
    text, ocr = r.get("text") or "", r.get("ocr") or ""
    if r["kind"] == "punctuation" and text.endswith("·") and re.search(r"[ʼ᾽’'\"”˙]$", ocr):
        return True
    if text.strip(".,·;:") == "δʼ" and ocr.strip(".,·;:") in DELTA_ELIDED:
        return True
    if r["kind"] == "bracket" and text.replace("⟨", "(").replace("⟩", ")") == ocr.replace("〈", "(").replace("〉", ")").replace("<", "(").replace(">", ")"):
        return True
    return False


def residuals(slug: str, files: list[Path] | None = None) -> list[dict]:
    """The residual pass (pipeline/transcriptions/<slug>/RESIDUALS.md): what the checked lines and
    Tesseract's reading of them still disagree on (words, accents, punctuation, brackets), per
    page, with a crop of the lines: residuals/r-NNNN.md and r-NNNN.png, residuals.json."""
    from PIL import Image, ImageDraw, ImageFont

    from .drama_pages import scan_dirs
    from .drama_residuals import page_residuals

    play = PLAYS[slug]
    pages = read_batches(transcriptions_dir(slug), files)
    od = out_dir(slug) / "residuals"
    od.mkdir(exist_ok=True)
    _, sbuild = scan_dirs(play.scan)
    try:
        font = ImageFont.truetype("DejaVuSans-Bold.ttf", 30)
    except OSError:
        font = ImageFont.load_default()

    def stream(layout):
        lines, ocr = ocr_stream([layout])
        fold(play, lines, ocr)
        return lines, ocr

    everything = []
    for stem, block in sorted(pages.items()):
        leaf = int(stem[2:])
        items = [(k, plain(t)) for k, t in block["text"] if KEY.match(k) and not t.startswith(HYPOTHESIS)]
        lay = page_layout(play, leaf)
        lay["lines"] = [p for p in lay["lines"] if p["kind"] != "title"]
        res = [r for r in page_residuals(play, lay, items, stream) if not known_misreading(r)]
        noted = {m.group(1) for x in block["notes"] if (m := re.match(r"^(\d+\.\d+)", x))}
        for r in res:
            r["stem"] = stem
            r["noted"] = r["n"] in noted
        everything += res
        for old in od.glob(f"r-{leaf:04d}.*"):
            old.unlink()
        if not res:
            continue
        md = [f"# Residuals on {stem} (leaf {leaf})", "",
              f"Image: r-{leaf:04d}.png (each line once, labelled with its key); the whole page: ../pages/leaf_{leaf:04d}.png", ""]
        for k, r in enumerate(res, 1):
            what = {"word": f"the text has «{r['text']}», the OCR reads «{r['ocr']}»",
                    "accent": f"accents: the text has «{r['text']}», the OCR reads «{r['ocr']}»",
                    "punctuation": f"punctuation: the text has «{r['text']}», the OCR reads «{r['ocr']}»",
                    "bracket": f"brackets: the text has «{r['text']}», the OCR reads «{r['ocr']}»",
                    "ocr-only": f"the OCR reads «{r['ocr']}» here, the text has nothing"}[r["kind"]]
            md.append(f"{k}. {r['n']}: {what}" + (" (the line is noted in the batch)" if r["noted"] else ""))
        (od / f"r-{leaf:04d}.md").write_text("\n".join(md) + "\n", encoding="utf-8")
        with Image.open(sbuild / "pages" / f"leaf_{leaf:04d}.png") as im:
            g = im.convert("L")
            spans = []
            for r in res:
                if r["y0"] is not None and (r["n"], r["y0"]) not in [(x[0], x[1]) for x in spans]:
                    spans.append((r["n"], r["y0"], r["y1"]))
            crops = [(n, g.crop((20, max(0, y0 - 14), g.size[0] - 20, y1 + 12))) for n, y0, y1 in spans]
        if crops:
            sheet = Image.new("L", (230 + max(c.size[0] for _n, c in crops), sum(c.size[1] + 10 for _n, c in crops)), 255)
            d = ImageDraw.Draw(sheet)
            y = 0
            for n, c in crops:
                sheet.paste(c, (230, y))
                d.text((8, y + c.size[1] // 2 - 18), n, fill=0, font=font)
                y += c.size[1] + 10
            sheet.save(od / f"r-{leaf:04d}.png")
    (od / "residuals.json").write_text(json.dumps(everything, ensure_ascii=False, indent=0), encoding="utf-8")
    return everything


def main(argv: list[str]) -> None:
    slug, step = argv[0], argv[1]
    if step == "draft":
        index = write_draft(slug, PIPELINE / "sources", transcriptions_dir(slug))
        n = sum(p["lines"] for p in index)
        f = sum(p["flagged"] for p in index)
        print(f"{slug}: {len(index)} pages, {n} lines, {f} flagged ({100 * f // max(n, 1)} %), "
              f"{sum(p['flags'] for p in index)} flags; apparatus found on {sum(1 for p in index if p['apparatus'])} pages; "
              f"{sum(1 for p in index if p['titles'])} pages with a title; {(len(index) + PAGES_PER_BATCH - 1) // PAGES_PER_BATCH} batches")
    else:
        run(slug, step)


if __name__ == "__main__":
    main(sys.argv[1:])
