"""The Shepherd of Hermas in Kirsopp Lake's Loeb edition (1913) from the scan by OCR, with only the
doubtful places left for a reader to check (pipeline/PLAN-hermas.md, steps 1-4).

The True Story's route (lucian_pages.py) for Lake's page: the Greek stands on the left-hand
(even) pages, his translation facing it. Each Greek page is read by Tesseract (grc); its words are
matched to Tauber and Macdonald's text of the same edition (the check text, hermas_text.py), which
gives every printed word its verse (book.chapter.verse of the 27 digital books). Lake prints:

* the running head THE APOSTOLIC FATHERS, the page number at the foot;
* the book's title (ΠΟΙΜΗΝ, ΟΡΑΣΙΣ Β …) and the chapter as a centred Roman numeral (I, II, XXIX);
* the verse number in the text before each verse ("2."); the verses run on in paragraphs, a new
  chapter's first verse indented;
* superscript footnote marks after words, numbered afresh on each page; the apparatus at the foot
  in small type, each item headed by its mark's number ("¹ τόπῳ ℵ* L₁, τρόπῳ ℵᶜAL₂(E).");
* Bible references in the left margin, in small type.

The marks are placed in the draft from First1KGreek's edition of the same text (its notes stand
where Lake's marks stand), numbered by page; the agent confirms each against the page. The
apparatus items are written by the agent from the image (Tesseract's two readings help); the
margin references are pre-filled from First1K and confirmed. The draft checks what the page itself
gives: each verse's printed number before its first word, each chapter numeral before the chapter's
first verse, and the OCR's words against Tauber's.

    python -m anagnosis_pipeline lake-pages hermas fetch|ocr|draft
    python -m anagnosis_pipeline lake-pages hermas latin-fetch|latin-ocr|latin-draft

Files (each saved as soon as it is made, so that a rerun goes on where it stopped):

    pipeline/build/drama-scans/<scan>/pages/leaf_0020.png       the page, grey
    pipeline/build/drama-scans/<scan>/hocr/leaf_0020.grc.hocr   Tesseract (grc); .lat.hocr (lat+grc) for the Latin pages
    pipeline/build/lake-pages/<slug>/p-0020.md                  the check sheet
    pipeline/build/lake-pages/<slug>/p-0020-lines.png           the flagged verses, each labelled
    pipeline/build/lake-pages/<slug>/p-0020-app-l.png, -app-r.png   the apparatus, halves enlarged
    pipeline/build/lake-pages/<slug>/p-0020-margin.png          the left margin (the references)
    pipeline/build/lake-pages/<slug>/pages.json, draft.json     (latin-pages.json, latin-draft.json)
    pipeline/transcriptions/hermas/batch-NN.md                  six pages each, never overwritten
    pipeline/transcriptions/hermas/batch-latin.md               the Latin end

The batch file, per page (`=== l-0302` for a Latin page's block):

    === p-0020
    --- text
    1.1.3+	ὑδάτων. διαβὰς οὖν τὸν ποταμὸν ἐκεῖνον ἦλθον …
    1.1.4	προσευχομένου δέ μου ἠνοίγη ὁ οὐρανός, …
    [chapter]	II
    ¶
    1.2.1	Μετὰ τὸ λαλῆσαι αὐτὴν …
    --- apparatus
    1	τόπῳ ℵ* L₁, τρόπῳ ℵᶜAL₂(E).
    2	θυγατέρα A, dominam E.
    --- margin
    1.1.6	Ps. 2, 4; 123, 1;
    --- notes

A verse is keyed by its reference (1.1.4) without Lake's printed number; a verse begun on the page
before continues as `1.1.3+`. `[title]` and `[chapter]` lines hold the headings as printed, `¶`
stands before a verse Lake begins on a new indented line. A footnote mark is written as the
superscript digit after the word (and its stop) where Lake prints it: αὐτῇ,¹.
"""
from __future__ import annotations

import json
import os
import re
import sys
import unicodedata
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from . import greek
from .drama import PLAYS, Play, skel

ROOT = Path(__file__).resolve().parent.parent.parent
PIPELINE = ROOT / "pipeline"
PAGES_PER_BATCH = 6
ROUTE = "lake-pages"
SUP = "⁰¹²³⁴⁵⁶⁷⁸⁹"
SUP_RE = re.compile(f"[{SUP}]+")
# Tesseract's readings of a printed verse number that are not digits (Lake's 5 read as ὅ or δ)
VNUM = re.compile(r"^(\d{1,2})[.,͵·]$|^([ὅδὃ])[.,]$")


def to_sup(n: int) -> str:
    return "".join(SUP[int(c)] for c in str(n))


def from_sup(s: str) -> int:
    return int("".join(str(SUP.index(c)) for c in s))


def out_dir(slug: str) -> Path:
    from .drama_pages import route_dir

    return route_dir(ROUTE, slug, PLAYS[slug].scan)


def transcriptions_dir(slug: str) -> Path:
    return PIPELINE / "transcriptions" / slug


def page_of(play: Play, leaf: int) -> int:
    return leaf - play.page_offset


# --- fetch and OCR ------------------------------------------------------------------------------

def ocr_latin(scan: str, leaf: int) -> Path:
    """A Latin page read with Tesseract's Latin and Greek models (hOCR, psm 4)."""
    from .drama_pages import fetch_leaf, scan_dirs
    from .gorgias_pages import tesseract

    _, build = scan_dirs(scan)
    hocr = build / "hocr" / f"leaf_{leaf:04d}.lat.hocr"
    if hocr.exists():
        return hocr
    png = fetch_leaf(scan, leaf)
    part = build / "hocr" / f"leaf_{leaf:04d}.lat.part"
    tesseract(png, part, "lat+grc", 4, True)
    os.replace(str(part) + ".hocr", hocr)
    return hocr


def run(slug: str, step: str, workers: int = 4) -> None:
    from .drama_pages import fetch_leaf, ocr_leaf

    play = PLAYS[slug]
    latin = step.startswith("latin-")
    leaves = play.visible("latin" if latin else "text")
    if not leaves:
        raise SystemExit(f"{slug}: no leaves in drama.PLAYS yet (step 2)")
    out_dir(slug)
    step = step.removeprefix("latin-")
    with ThreadPoolExecutor(workers) as ex:
        if step == "fetch":
            list(ex.map(lambda l: fetch_leaf(play.scan, l), leaves))
        elif step == "ocr":
            list(ex.map(lambda l: (ocr_latin if latin else ocr_leaf)(play.scan, l), leaves))
        else:
            raise SystemExit(f"unknown step {step!r}")
    print(f"{slug}: {step} done for {len(leaves)} {'Latin ' if latin else ''}leaves")


# --- the page ------------------------------------------------------------------------------------

def _text(l: dict) -> str:
    return " ".join(w["text"] for w in sorted(l["words"], key=lambda w: w["bbox"][0]))


def is_chapter(text: str) -> bool:
    """A chapter numeral as Tesseract reads it: I, II, XXIX (Latin or Greek look-alike letters)."""
    t = text.strip().rstrip(".").replace(" ", "")
    return bool(t) and len(t) <= 8 and re.fullmatch(r"[IVXLΙΧVΛ1l|]+", t) is not None


def is_heading(text: str, l: dict, lay: dict) -> bool:
    """A book's title: a short centred line, mostly capitals (ΠΟΙΜΗΝ, ΟΡΑΣΙΣ Β, ΕΝΤΟΛΗ Α) or in
    small capitals (Similitudo X)."""
    letters = [c for c in text if c.isalpha()]
    if len(letters) < 3 or len(text) > 60:
        return False
    x0, x1 = l["bbox"][0], l["bbox"][2]
    mid = (lay["left"] + lay["right"]) / 2
    centred = abs((x0 + x1) / 2 - mid) < 0.08 * lay["width"] and (x1 - x0) < 0.7 * (lay["right"] - lay["left"])
    caps = sum(c.isupper() for c in letters) >= 0.7 * len(letters)
    return centred and (caps or len(text.split()) <= 3)


def apparatus_top(lines: list[dict], H: int, W: int) -> tuple[int | None, list[dict]]:
    """Where Lake's apparatus begins: the run of lines in small type at the foot of the page (above
    the page number); None if the page prints none. Also the lines that are the page number or the
    signature at the foot (to be left out of the text)."""
    body = [l for l in lines if l["bbox"][3] > 0.075 * H]
    upper = [l for l in body if l["bbox"][1] < 0.6 * H and l["x_size"] > 0 and sum(1 for w in l["words"] if len(skel(w["text"])) >= 3) >= 3]
    sizes = sorted(l["x_size"] for l in upper)
    XS = sizes[len(sizes) // 2] if sizes else 60
    foot: list[dict] = []
    block: list[dict] = []
    for l in sorted(body, key=lambda l: -l["bbox"][1]):
        text = _text(l)
        if l["bbox"][1] > 0.85 * H and len(text.replace(" ", "")) <= 5 and not block:
            foot.append(l)  # the page number, a signature (B 2)
            continue
        small = l["x_size"] and l["x_size"] <= 0.85 * XS
        long_ = sum(1 for w in l["words"] if len(skel(w["text"])) >= 3) >= 3
        if small or (not long_ and block and l["bbox"][3] - l["bbox"][1] < 0.8 * XS):
            block.append(l)
            continue
        break
    block = [l for l in block if len(_text(l)) > 2]
    if not block:
        return None, foot
    return min(l["bbox"][1] for l in block) - 8, foot


def page_layout(play: Play, leaf: int, latin: bool = False) -> dict:
    """drama_pages.page_layout with the apparatus found by its small type at the foot; the page
    number left out; each printed line marked as a title, a chapter numeral or text."""
    from PIL import Image

    from .drama_pages import ocr_leaf, page_layout as drama_layout, read_lines, scan_dirs

    _, sbuild = scan_dirs(play.scan)
    hocr = ocr_latin(play.scan, leaf) if latin else ocr_leaf(play.scan, leaf)
    lines = read_lines(hocr)
    with Image.open(sbuild / "pages" / f"leaf_{leaf:04d}.png") as im:
        W, H = im.size
    app_y, foot = apparatus_top(lines, H, W)
    lay = drama_layout(play, leaf, app_y=app_y if app_y is not None else H - 5, hocr=hocr)
    if app_y is None:
        lay["app_y"] = lay["app_end"] = None
    foot_y = min((l["bbox"][1] for l in foot), default=H)
    lay["lines"] = [p for p in lay["lines"] if p["y0"] < foot_y - 5]
    # a chapter numeral read with little confidence (Ι, II) is passed over as a speck: put it back
    text_end = app_y if app_y is not None else foot_y
    mid = (lay["left"] + lay["right"]) / 2
    for l in lines:
        t = _text(l)
        x0, y0, x1, y1 = l["bbox"]
        # a numeral, or a book's title read with no confidence (“Ὅριασις".6β,,): a short centred line
        centred = abs((x0 + x1) / 2 - mid) < 0.05 * W and (x1 - x0) <= 0.45 * W and re.search(r"\w", t)
        if not centred or y0 <= max(lay["head_y"], 0.1 * H) or y1 >= text_end or (y1 - y0) < 0.35 * lay["line_h"]:
            continue
        if any(min(y1, p["y1"]) - max(y0, p["y0"]) > 0.3 * (y1 - y0) for p in lay["lines"]):
            continue
        lay["lines"].append({"y0": y0, "y1": y1, "oy0": y0, "oy1": y1, "words": l["words"], "left_m": [], "right_m": [],
                             "x0": x0, "x1": x1})
    lay["lines"].sort(key=lambda p: p["y0"])
    lay["latin"] = latin
    for p in lay["lines"]:
        t = _text(p)
        if _numeral_shape(p["x0"], p["x1"], W, mid, t):
            p["kind"] = "chapter"
        elif is_heading(t, {"bbox": [p["x0"], p["y0"], p["x1"], p["y1"]]}, lay):
            p["kind"] = "title"
        else:
            p["kind"] = "text"
    # the running head, where it stands lower than drama_pages expects
    lay["lines"] = [p for p in lay["lines"] if not (p["kind"] == "title" and p["y1"] < 0.1 * H)]
    return lay


def _numeral_shape(x0: int, x1: int, W: int, mid: float, text: str) -> bool:
    """A chapter numeral by its shape: a short line (at most a tenth of the page wide, two words)
    centred on the column. Tesseract's Greek model reads II as ἐδ, so the letters are not asked."""
    return (x1 - x0) <= 0.1 * W and abs((x0 + x1) / 2 - mid) < 0.05 * W and len(text.split()) <= 2 and bool(text.strip())


def to_roman(n: int) -> str:
    out = ""
    for v, r in ((100, "C"), (90, "XC"), (50, "L"), (40, "XL"), (10, "X"), (9, "IX"), (5, "V"), (4, "IV"), (1, "I")):
        while n >= v:
            out += r
            n -= v
    return out


# --- the OCR's words ---------------------------------------------------------------------------

def ocr_stream(layouts: list[dict]) -> tuple[list[dict], list[dict], list[dict]]:
    """The printed lines in order ({'leaf', 'y0', 'y1', 'oy0', 'oy1', 'x0', 'indent', 'line_h',
    'ocr', 'kind'}), the OCR's words ({'t', 'skel', 'line', 'conf'}) without the verse numbers,
    and the verse numbers read ({'n' (int, or None for a letter read for a 5), 'line', 'before'
    (the index of the next OCR word)}). A word divided at the end of a line is joined and belongs
    to the line where it begins."""
    from .drama_pages import DASHES, ocr_norm

    lines: list[dict] = []
    toks: list[dict] = []
    nums: list[dict] = []
    for lay in layouts:
        for p in lay["lines"]:
            ws = sorted(p["words"], key=lambda w: w["bbox"][0])
            li = len(lines)
            # where the line's print begins (a verse number at the start is part of the line)
            x0 = min((w["bbox"][0] for w in ws if w["conf"] >= 40 and re.search(r"\w", w["text"])), default=p["x0"])
            lines.append({"leaf": lay["leaf"], "y0": p["y0"], "y1": p["y1"], "oy0": p.get("oy0", p["y0"]), "oy1": p.get("oy1", p["y1"]),
                          "x0": x0, "indent": x0 - lay["left"], "line_h": lay["line_h"], "ocr": " ".join(w["text"] for w in ws),
                          "kind": p["kind"]})
            if p["kind"] != "text":
                continue
            for w in ws:
                m = VNUM.match(w["text"].strip())
                if m:
                    nums.append({"n": int(m.group(1)) if m.group(1) else None, "line": li, "before": len(toks), "conf": w["conf"]})
                    continue
                if _weak_number(w):
                    # a number the Greek model turns into a letter or splits ("Ἰ.", "δ.", "9" ":"): it
                    # counts as a verse number only where the check text begins a verse
                    d = re.sub(r"\D", "", w["text"])
                    nums.append({"n": int(d) if d else None, "line": li, "before": len(toks), "conf": w["conf"], "weak": True})
                for piece in DASHES.split(ocr_norm(w["text"])):
                    if not piece.strip():
                        continue
                    toks.append({"t": piece, "skel": skel(piece), "line": li, "conf": w["conf"]})
    for k, t in enumerate(toks):
        last = k + 1 == len(toks) or toks[k + 1]["line"] != t["line"]
        t["hyph"] = last and t["t"].rstrip().endswith(("-", "‐", "¬")) and len(t["skel"]) > 0
    joined: list[dict] = []
    remap: dict[int, int] = {}
    count: dict[int, int] = {}
    for t in toks:
        if t["skel"]:
            count[t["line"]] = count.get(t["line"], 0) + 1
    for k, t in enumerate(toks):
        if joined and joined[-1].get("hyph") and t["line"] > joined[-1]["line"] and t["skel"]:
            prev = joined[-1]
            prev["t"] = prev["t"].rstrip().rstrip("-‐¬") + t["t"]
            prev["skel"] = skel(prev["t"])
            prev["hyph"] = False
            prev["joined"] = True
            if count.get(t["line"]) == 1:
                prev["line"] = t["line"]
            remap[k] = len(joined) - 1
            continue
        remap[k] = len(joined)
        joined.append(t)
    keep = [k for k, t in enumerate(joined) if t["skel"]]
    newidx = {old: new for new, old in enumerate(keep)}
    out = [joined[k] for k in keep]
    for nm in nums:
        b = remap.get(nm["before"], len(joined))
        while b < len(joined) and b not in newidx:
            b += 1
        nm["before"] = newidx.get(b, len(out))
    return lines, out, nums


# --- the draft -------------------------------------------------------------------------------

# Tesseract's misreadings of Lake's verse numbers: printed -> read (counted on the whole draft)
_NUM_MISREAD = {2: {3, 5, 9}, 3: {5, 8, 9}, 8: {3}, 7: {1}, 1: {7}, 5: {None, 6}, 6: {0, 5, 9}, 9: {0}}


def _ocr_noise(ours: str, read: str) -> bool:
    """Differences the Greek model makes on Lake's type that no page bears out: a piece of the
    word (its beginning or end, three letters or more), and λ read as χ, ζ as ἕ, Latin c as e."""
    a, b = skel(ours), skel(read)
    if len(b) >= 3 and len(b) < len(a) and (a.startswith(b) or a.endswith(b)):
        return True
    fold = str.maketrans({"χ": "λ", "e": "c"})
    b2 = b.translate(fold)
    a2 = a.translate(fold)
    return a2 == b2 or (a2.replace("ζ", "ε") == b2)


def _weak_number(w: dict) -> bool:
    """A short token that is no Greek word: digits, or one letter read at low confidence, with
    or without a stop after it."""
    t = w["text"].strip().rstrip(".,:;·΄'’")
    if not t or len(t) > 2:
        return False
    if t.isdigit():
        return True
    return len(skel(t)) <= 1 and w["conf"] < 60


def build_draft(play: Play, latin: bool = False) -> dict:
    from .drama_pages import realign
    from .gorgias_pages import align, assign_lines
    from .hermas_text import chapters_in, first1k_marks, headings, tauber_text

    leaves = play.visible("latin" if latin else "text")
    workers = int(os.environ.get("DRAMA_WORKERS", "4"))
    with ThreadPoolExecutor(workers) as ex:
        layouts = dict(zip(leaves, ex.map(lambda l: page_layout(play, l, latin), leaves)))
    lines, ocr, nums = ocr_stream([layouts[l] for l in leaves])
    pers = tauber_text(part="latin" if latin else "greek")
    if play.skel_fold:
        tr = str.maketrans(play.skel_fold[0::2], play.skel_fold[1::2])
        for t in ocr + pers:
            t["skel"] = t["skel"].translate(tr)
    match = align(ocr, pers)
    mended = realign(ocr, pers, match)
    if mended:
        print(f"{play.slug}: {mended} stretches aligned again", file=sys.stderr)
    # the stretch of the check text the pages hold
    found = [j for j, o in enumerate(match) if o is not None]
    lo = max(0, found[0] - 8) if found else 0
    hi = min(len(pers), found[-1] + 9) if found else 0
    while lo > 0 and not pers[lo]["newsec"]:
        lo -= 1
    if lo > 0 or hi < len(pers):
        print(f"{play.slug}: the pages hold {pers[lo]['sec']}–{pers[hi - 1]['sec']}; "
              f"{lo} words before and {len(pers) - hi} after were not found", file=sys.stderr)
    pers, match = pers[lo:hi], match[lo:hi]
    assign_lines(lines, ocr, pers, match)
    marks = []
    if not latin:
        for mk in first1k_marks():
            if lo <= mk["after"] < hi:
                mk["after"] -= lo
                marks.append(mk)

    # each check-text word's page; a verse begins on the page of its first word
    for j, t in enumerate(pers):
        t["leaf"] = lines[t["line"]]["leaf"] if t.get("line") is not None else None
    for j, t in enumerate(pers):
        if t["leaf"] is None:
            t["leaf"] = next((pers[k]["leaf"] for k in range(j - 1, -1, -1) if pers[k]["leaf"] is not None), leaves[0])
    # the footnote marks, numbered by page in order
    mark_after: dict[int, list[dict]] = {}
    per_page: dict[int, int] = {}
    for mk in sorted((m for m in marks if m["kind"] == "app"), key=lambda m: m["after"]):
        leaf = pers[mk["after"]]["leaf"] if mk["after"] >= 0 else leaves[0]
        per_page[leaf] = per_page.get(leaf, 0) + 1
        mk["num"] = per_page[leaf]
        mk["leaf"] = leaf
        mark_after.setdefault(mk["after"], []).append(mk)
    margin_by_leaf: dict[int, list[tuple[str, str]]] = {}
    for mk in marks:
        if mk["kind"] == "bibl" and mk["after"] >= 0:
            margin_by_leaf.setdefault(pers[mk["after"]]["leaf"], []).append((pers[mk["after"]]["sec"], mk["text"]))

    # the verse numbers read: before which check-text word each stands
    o2p = {o: j for j, o in enumerate(match) if o is not None}
    num_before: dict[int, dict] = {}
    for nm in nums:
        o = nm["before"]
        j = None
        while o < len(ocr) and j is None:
            j = o2p.get(o)
            if j is None and ocr[o]["skel"] and len(ocr[o]["skel"]) >= 3:
                break
            o += 1
        if j is not None:
            num_before[j] = nm

    entries: dict[int, list[dict]] = {l: [] for l in leaves}
    verse = None
    for j, t in enumerate(pers):
        leaf = t["leaf"]
        if verse is None or t["sec"] != verse["sec"] or leaf != verse["leaf"]:
            cont = not t["newsec"]
            verse = {"type": "verse", "sec": t["sec"], "key": t["sec"] + ("+" if cont else ""), "leaf": leaf,
                     "words": [], "flags": [], "line": t.get("line"), "first": j, "para": False}
            entries[leaf].append(verse)
        verse["words"].append(j)
    for leaf, es in entries.items():
        for e in es:
            _verse_text(e, pers, ocr, match, mark_after, num_before, lines)
    # OCR words no check-text word was matched to, by line
    paired = {o for o in match if o is not None}
    for k, t in enumerate(ocr):
        if k not in paired and len(t["skel"]) >= 4 and t["conf"] >= 80:
            near = [e for e in entries.get(lines[t["line"]]["leaf"], []) if any(pers[j].get("line") == t["line"] for j in e["words"])]
            if near:
                near[0]["flags"].append(f"the OCR reads “{t['t']}” on a line of this verse, which Tauber does not have here")
    # verse numbers read before a word where Tauber begins no verse
    for j, nm in num_before.items():
        if not pers[j]["newsec"] and not nm.get("weak") and nm["n"] is not None and nm["conf"] >= 80:
            e = _entry_of(entries, pers, j)
            if e is not None:
                e["flags"].append(f"the OCR reads a verse number “{nm['n']}.” before “{pers[j]['t']}”, where Tauber begins no verse")
    # the headings and chapter numerals, placed among the verses by their printed line
    for li, pl in enumerate(lines):
        if pl["kind"] == "text":
            continue
        es = entries[pl["leaf"]]
        pos = next((k for k, e in enumerate(es) if e.get("line") is not None and e["line"] > li), len(es))
        es.insert(pos, {"type": pl["kind"], "text": pl["ocr"], "line": li, "flags": []})
    heads = headings()
    for leaf, es in entries.items():
        for k, e in enumerate(es):
            if e["type"] != "verse" or e["key"].endswith("+"):
                continue
            t = pers[e["first"]]
            prev = es[k - 1] if k > 0 else None
            # a book's title above its first chapter: Lake's heading as Tauber has it
            title = next((x for x in reversed(es[:k]) if x["type"] == "title"), None)
            book = int(t["sec"].split(".")[0])
            if t["sec"].endswith(".1.1") and title is not None and not title.get("done"):
                import difflib

                want = heads.get(book, "")
                title["done"] = True
                if skel(title["text"]) != skel(want):
                    if difflib.SequenceMatcher(None, skel(title["text"]), skel(want)).ratio() >= 0.6:
                        title["flags"].append(f"the title is read “{title['text']}”; written as Tauber has Lake's heading: check it against the page")
                        title["text"] = want
                    else:
                        title["flags"].append(f"the title is read “{title['text']}” (Tauber's heading of the book: “{want}”): copy what Lake prints")
            elif t["sec"].endswith(".1.1") and book > 1 and title is None:
                e["flags"].append(f"{t['sec']} begins a book, but no title line was found above it: copy Lake's heading as [title] if he prints one")
            if t["newchapter"]:
                chap = int(t["sec"].split(".")[1])
                if prev is None or prev["type"] != "chapter":
                    # a book of one chapter has no numeral (Mandates 1 and 2 on p. 70)
                    if chapters_in(book) > 1:
                        e["flags"].append(f"chapter {chap} begins here, but no chapter numeral was found above the verse")
                else:
                    got = ocr_roman(prev["text"])
                    if got != chap:
                        prev["flags"].append(f"the numeral is read “{prev['text']}”; written {to_roman(chap)}, Tauber's chapter here: check")
                    prev["text"] = to_roman(chap)
            elif prev is not None and prev["type"] == "chapter":
                prev["flags"].append("a chapter numeral is read here, but Tauber begins no chapter")
    # first1k's number of each footnote against ours
    for mk in marks:
        if mk["kind"] == "app" and mk.get("num") and mk["n"] and mk["n"].isdigit() and int(mk["n"]) != mk["num"]:
            e = _entry_of(entries, pers, mk["after"])
            if e is not None:
                e["flags"].append(f"the footnote mark after “{pers[mk['after']]['t']}” is numbered {mk['num']} here, "
                                  f"{mk['n']} in First1K: check which page it is on and its number")
    for es in entries.values():
        for e in es:
            e["flags"] = list(dict.fromkeys(e["flags"]))
            if e["type"] == "verse":
                ls = [pers[j]["line"] for j in e["words"] if pers[j].get("line") is not None]
                e["y0"] = min((lines[l]["oy0"] for l in ls), default=0)
                e["y1"] = max((lines[l]["oy1"] for l in ls), default=0)
            else:
                e["y0"], e["y1"] = lines[e["line"]]["oy0"], lines[e["line"]]["oy1"]
    return {"layouts": layouts, "lines": lines, "entries": entries, "margin": margin_by_leaf, "pers": pers,
            "marks": per_page}


def _entry_of(entries: dict[int, list[dict]], pers: list[dict], j: int) -> dict | None:
    for e in entries.get(pers[j]["leaf"], []):
        if e["type"] == "verse" and j in e["words"]:
            return e
    return None


def _verse_text(e: dict, pers: list[dict], ocr: list[dict], match: list[int | None], mark_after: dict,
                num_before: dict, lines: list[dict]) -> None:
    """The verse's words as Tauber has them, with the footnote marks, and the flags from the OCR."""
    from .drama_pages import _accent_letters

    out: list[str] = []
    flags = e["flags"]
    for j in e["words"]:
        t = pers[j]
        w = t["t"]
        o = match[j]
        for mk in mark_after.get(j, []):
            w += to_sup(mk["num"])
            flags.append(f"{w}: a footnote mark ({mk['num']}) after this word (First1K's place): check it on the page")
        if t.get("glued") and out:
            out[-1] += w
        else:
            out.append(w)
        if o is None:
            flags.append(f"{t['t']}: not found in the OCR; check it is printed here")
        elif t["sim"] < 1.0 and ocr[o]["conf"] >= 70 and not _ocr_noise(t["t"], ocr[o]["t"]):
            flags.append(f"{t['t']}: the OCR reads “{ocr[o]['t']}”")
        elif t["sim"] == 1.0 and len(t["skel"]) >= 4 and ocr[o]["conf"] >= 95 and _accent_letters(t["t"]) != _accent_letters(ocr[o]["t"]):
            flags.append(f"{t['t']}: the OCR reads “{ocr[o]['t']}” (accents)")
        if t.get("guess"):
            flags.append(f"{t['t']}: which line it stands on is a guess")
    first = pers[e["words"][0]]
    if first["newsec"]:
        v = int(first["sec"].split(".")[2])
        nm = num_before.get(e["words"][0])
        if nm is None:
            # Lake prints "1." under every chapter numeral; the OCR often loses it there
            if not (v == 1 and first["newchapter"]):
                flags.append(f"no verse number “{v}.” read before “{first['t']}”: check that verse {v} begins here")
        elif nm.get("weak") and nm["n"] is None:
            pass  # something stands where the number is printed: the check text's verse is taken
        elif nm["n"] != v and nm["n"] not in _NUM_MISREAD.get(v, set()):
            flags.append(f"the verse number before “{first['t']}” is read “{nm['n']}.”; Tauber's verse is {v}")
        # a verse Lake begins on an indented line of its own
        li = first.get("line")
        if li is not None and match[e["words"][0]] is not None:
            o = match[e["words"][0]]
            first_on_line = not any(ocr[k]["line"] == li for k in range(max(0, o - 3), o))
            if first_on_line and lines[li]["indent"] > 0.6 * lines[li]["line_h"]:
                e["para"] = True
    e["text"] = " ".join(out)


def write_draft(slug: str, latin: bool = False) -> list[dict]:
    """The check sheets, crops, pages.json and draft.json; the batch files that do not exist yet."""
    from .drama_pages import apparatus_images, lines_image, scan_dirs

    play = PLAYS[slug]
    od = out_dir(slug)
    d = build_draft(play, latin)
    entries, layouts = d["entries"], d["layouts"]
    leaves = play.visible("latin" if latin else "text")
    pfx = "l" if latin else "p"
    index = []
    _, sbuild = scan_dirs(play.scan)
    for b, leaf in enumerate(leaves):
        es = entries.get(leaf, [])
        verses = [e for e in es if e["type"] == "verse"]
        stem = f"{pfx}-{leaf:04d}"
        page = page_of(play, leaf)
        for old in od.glob(f"{stem}-*.png"):
            old.unlink()
        lay = layouts[leaf]
        app = apparatus_images(play, leaf, lay, od, stem) if lay["app_y"] is not None else {}
        flagged = [e for e in es if e["flags"]]
        has_lines = lines_image(play, leaf, [{"n": e.get("key", e["type"]), "y0": e["y0"], "y1": e["y1"]} for e in flagged],
                                od / f"{stem}-lines.png")
        margin_words = _margin_image(play, leaf, lay, od / f"{stem}-margin.png")
        rng = f"{verses[0]['key']}–{verses[-1]['sec']}" if verses else "no verses"
        md = [f"# Page {page} ({stem}, leaf {leaf}): {rng}", ""]
        imgs = [f"pages/leaf_{leaf:04d}.png (the whole page)"]
        if has_lines:
            imgs.append(f"{stem}-lines.png (the flagged verses, each labelled)")
        if app:
            imgs.append(f"{stem}-app-l.png and {stem}-app-r.png (the apparatus, left and right half, enlarged)")
        if margin_words is not None:
            imgs.append(f"{stem}-margin.png (the left margin: the Bible references)")
        md += ["Images: " + "; ".join(imgs), ""]
        if lay["app_y"] is None:
            md += ["**No apparatus was found at the foot of this page**: check whether it prints one.", ""]
        md += ["## Flags", ""]
        if flagged:
            for e in flagged:
                md.append(f"* {e.get('key', '[' + e['type'] + ']')}  `{e['text'][:200]}`")
                for f in e["flags"]:
                    md.append(f"    * {f}")
        else:
            md.append("None: the OCR agrees with Tauber on every verse.")
        md += ["", "## The page's lines as Tesseract read them", ""]
        md += [f"\t{l['ocr']}" for l in d["lines"] if l["leaf"] == leaf]
        if margin_words:
            md += ["", "## The left margin as Tesseract read it", "", "\t" + " ".join(margin_words)]
        md += ["", f"## Tesseract's readings of the apparatus ({play.app_langs[0]}; {play.app_langs[1]}). Both garble sigla and numbers"]
        if app:
            for key in ("first", "second"):
                md += ["", "```", app.get(key, ""), "```"]
        else:
            md += ["", "(no apparatus found on this page)"]
        (od / f"{stem}.md").write_text("\n".join(md) + "\n", encoding="utf-8")
        index.append({"stem": stem, "leaf": leaf, "page": page, "first": verses[0]["key"] if verses else None,
                      "last": verses[-1]["sec"] if verses else None, "verses": len(verses), "flagged": len(flagged),
                      "entries": len(es), "batch": "latin" if latin else b // PAGES_PER_BATCH + 1,
                      "apparatus": bool(app), "marks": d["marks"].get(leaf, 0),
                      "secs": list(dict.fromkeys(e["sec"] for e in verses))})
    name = "latin-" if latin else ""
    (od / f"{name}pages.json").write_text(json.dumps(index, ensure_ascii=False, indent=1), encoding="utf-8")
    (od / f"{name}draft.json").write_text(json.dumps(
        [{"leaf": l, **{k: e.get(k) for k in ("type", "key", "sec", "text", "para", "flags", "y0", "y1")}}
         for l, es in entries.items() for e in es], ensure_ascii=False, indent=0), encoding="utf-8")
    tdir = transcriptions_dir(slug)
    tdir.mkdir(parents=True, exist_ok=True)
    groups = [("batch-latin.md", leaves)] if latin else [
        (f"batch-{b // PAGES_PER_BATCH + 1:02d}.md", leaves[b:b + PAGES_PER_BATCH]) for b in range(0, len(leaves), PAGES_PER_BATCH)]
    for name_, group in groups:
        path = tdir / name_
        if path.exists():
            continue
        out = []
        for leaf in group:
            out += [f"=== {pfx}-{leaf:04d}", "--- text"]
            for e in entries.get(leaf, []):
                if e["type"] == "verse":
                    if e["para"]:
                        out.append("¶")
                    out.append(f"{e['key']}\t{e['text']}")
                else:
                    out.append(f"[{e['type']}]\t{e['text']}")
            out.append("--- apparatus")
            out.append("--- margin")
            for sec, ref in d["margin"].get(leaf, []):
                out.append(f"{sec}\t{ref}")
            out += ["--- notes", ""]
        path.write_text("\n".join(out), encoding="utf-8")
    return index


def _margin_image(play: Play, leaf: int, lay: dict, path: Path) -> list[str] | None:
    """The left margin beside the text (Lake's Bible references), enlarged; the words Tesseract read
    there. None if the margin holds no ink."""
    from PIL import Image

    from .drama_pages import scan_dirs

    _, sbuild = scan_dirs(play.scan)
    words = [w["text"] for p in lay["lines"] for w in p.get("left_m", [])]
    y0 = lay["head_y"] + 10
    y1 = lay["app_y"] or lay["height"] - 60
    x1 = max(10, lay["left"] - 12)
    with Image.open(sbuild / "pages" / f"leaf_{leaf:04d}.png") as im:
        g = im.convert("L").crop((0, y0, x1, y1))
        ink = sum(1 for v in g.point(lambda v: 255 if v < 120 else 0).getdata() if v)
        if ink < 200:
            return None
        g.resize((g.size[0] * 2, g.size[1] * 2), Image.LANCZOS).save(path)
    return words


# --- reading and checking a batch -------------------------------------------------------------

VKEY = re.compile(r"^(\d+)\.(\d+)\.(\d+)(\+?)$")
STEM = re.compile(r"^=== ([pl]-\d{4})\s*$")


def read_batches(directory: Path, files: list[Path] | None = None, latin: bool | None = None) -> dict[str, dict]:
    """Page blocks by stem: {'text': [(key, text)] with ('¶', ''), ('[title]', text), ('[chapter]',
    text); 'apparatus': [(number, item)]; 'margin': [(verse, reference)]; 'notes': [str];
    'errors': [str]; 'batch': name}. latin None: every batch; True: batch-latin.md; False: the
    Greek batches."""
    pages: dict[str, dict] = {}
    if files is None:
        files = sorted(directory.glob("batch-*.md"))
        if latin is not None:
            files = [f for f in files if (f.name == "batch-latin.md") == latin]
    for path in files:
        stem, part = None, None
        for raw in path.read_text(encoding="utf-8").splitlines():
            m = STEM.match(raw)
            if m:
                stem = m.group(1)
                pages[stem] = {"text": [], "apparatus": [], "margin": [], "notes": [], "errors": [], "batch": path.name}
                part = None
                continue
            m = re.match(r"^--- (text|apparatus|margin|notes)\s*$", raw)
            if m:
                part = m.group(1)
                continue
            if stem is None or part is None or not raw.strip():
                continue
            if part == "notes":
                pages[stem]["notes"].append(raw.strip())
                continue
            if part == "text" and raw.strip() == "¶":
                pages[stem]["text"].append(("¶", ""))
                continue
            n, sep, body = raw.partition("\t")
            if not sep:
                pages[stem]["errors"].append(f"no TAB: {raw[:60]!r}")
                continue
            pages[stem][part].append((n.strip(), unicodedata.normalize("NFC", body.strip())))
    return pages


def plain(text: str) -> str:
    """A verse without its footnote marks."""
    return SUP_RE.sub("", text)


def marks_in(text: str) -> list[int]:
    return [from_sup(m.group(0)) for m in SUP_RE.finditer(text)]


def check_batch(slug: str, path: Path) -> list[str]:
    """Remarks on one checked batch file: pages missing or foreign, keys malformed or out of order,
    a continuation not first on its page, chapter numerals against the chapters, footnote marks
    against the apparatus numbers (each mark one item, numbered 1, 2, 3 on the page), margin keys
    naming verses of the page, elision, NFC, divided words, and every place where the words differ
    from Tauber's (each a change made on checking; '(noted)' where the page's notes name the verse)."""
    import difflib

    from .hermas_text import chapters_in, sec_key, tauber_sections

    latin = path.name == "batch-latin.md"
    index = json.loads((out_dir(slug) / ("latin-pages.json" if latin else "pages.json")).read_text(encoding="utf-8"))
    pages = read_batches(path.parent, files=[path])
    m = re.search(r"batch-(\d+)", path.name)
    expected = [p["stem"] for p in index if (latin or (m and p.get("batch") == int(m.group(1))))]
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
    prev: tuple[int, int, int] | None = None
    for stem, block in pages.items():
        for e in block["errors"]:
            remarks.append(f"{stem}: {e}")
        for raw in block["notes"]:
            for mm in re.finditer(r"\b(\d+\.\d+\.\d+)\b", raw):
                noted.add(mm.group(1))
        page_secs: set[str] = set()
        page_marks: list[int] = []
        pending_chapter: int | None = None
        for k, (key, text) in enumerate(block["text"]):
            if key == "¶":
                continue
            if key in ("[title]", "[chapter]"):
                if key == "[chapter]":
                    pending_chapter = roman(text)
                    if pending_chapter is None:
                        remarks.append(f"{stem}: chapter numeral {text!r} is not a Roman number")
                else:
                    page_marks += marks_in(text)  # Lake's note on a title (p. 68: Ἀποκάλυψις εʹ¹)
                    if re.search(r"[΄'’]", text):
                        remarks.append(f"{stem}: [title] {text!r}: write the numeral sign as ʹ")
                continue
            mm = VKEY.match(key)
            if not mm:
                remarks.append(f"{stem}: bad key {key!r} (book.chapter.verse, or book.chapter.verse+ for a verse continued)")
                continue
            cur = (int(mm.group(1)), int(mm.group(2)), int(mm.group(3)))
            sec = f"{cur[0]}.{cur[1]}.{cur[2]}"
            page_secs.add(sec)
            if mm.group(4):
                if any(VKEY.match(kk) for kk, _t in block["text"][:k]):
                    remarks.append(f"{stem} {key}: a continuation (+) must be the page's first verse")
                if prev is not None and cur != prev:
                    remarks.append(f"{stem} {key}: continues a verse, but the verse before is {'.'.join(map(str, prev))}")
            else:
                if prev is not None and cur <= prev:
                    remarks.append(f"{stem} {key}: comes after {'.'.join(map(str, prev))}")
                new_chapter = prev is None or cur[:2] != prev[:2]
                if prev is not None and new_chapter and cur[2] != 1:
                    remarks.append(f"{stem} {key}: a chapter that does not begin with verse 1")
                if prev is not None and not new_chapter and cur[2] != prev[2] + 1:
                    remarks.append(f"{stem} {key}: verse {cur[2]} follows verse {prev[2]}")
                if new_chapter and prev is not None and pending_chapter is None and chapters_in(cur[0]) > 1:
                    remarks.append(f"{stem} {key}: chapter {cur[1]} begins, but no [chapter] line stands before it")
                if pending_chapter is not None and pending_chapter != cur[1]:
                    remarks.append(f"{stem} {key}: the [chapter] line above reads {pending_chapter}, the verse's chapter is {cur[1]}")
                if pending_chapter is not None and not new_chapter:
                    remarks.append(f"{stem} {key}: a [chapter] line before a verse that begins no chapter")
            pending_chapter = None
            prev = cur
            if text != unicodedata.normalize("NFC", text):
                remarks.append(f"{stem} {key}: not NFC")
            if re.search(r"[Ͱ-Ͽἀ-῿][’'᾽]", text):
                remarks.append(f"{stem} {key}: elision written other than ʼ")
            if re.search(r"[Ͱ-Ͽἀ-῿]-\s*$", text):
                remarks.append(f"{stem} {key}: a divided word? write it whole on the page where it begins")
            if re.match(r"^\d+\.\s", text):
                remarks.append(f"{stem} {key}: Lake's printed verse number is not copied (the key carries it)")
            if re.search(r"\s[.,·;:]", re.sub(r"\.( \.)+", "", plain(text))):  # not Lake's dots of omission
                remarks.append(f"{stem} {key}: a space before a stop")
            page_marks += marks_in(text)
            pieces = re.findall(r"[^\W\d_]+", plain(text)) if latin else [w for w, _s, _e in greek.words(plain(text))]
            for w in pieces:
                if skel(w):  # not the keraia of a numeral (ιβʹ), which the tokenizer splits off
                    words.append((skel(w), w, sec))
            if not latin:
                for w in re.findall(r"[A-Za-z]{2,}", plain(text)):
                    remarks.append(f"{stem} {key}: Latin letters “{w}” in the Greek text")
            secs.append(sec)
        # the marks against the apparatus
        nums = []
        for n, item in block["apparatus"]:
            if not re.fullmatch(r"\d{1,2}", n):
                remarks.append(f"{stem}: bad apparatus number {n!r} (the footnote's number as printed: 1, 2, 3)")
                continue
            nums.append(int(n))
            if item != unicodedata.normalize("NFC", item):
                remarks.append(f"{stem} {n}: apparatus not NFC")
            if not item.strip():
                remarks.append(f"{stem} {n}: an empty apparatus item")
        if page_marks != list(range(1, len(page_marks) + 1)):
            remarks.append(f"{stem}: the footnote marks in the text run {page_marks}, not 1, 2, 3 …")
        if sorted(nums) != sorted(page_marks):
            remarks.append(f"{stem}: the apparatus numbers {nums} do not answer the marks in the text {page_marks}"
                           " (an item whose mark stands in the other block of a shared page goes there)")
        for sec, ref in block["margin"]:
            if sec not in page_secs:
                remarks.append(f"{stem}: margin reference {ref!r} keyed to {sec}, which is not a verse of the page")
            if not ref.strip():
                remarks.append(f"{stem}: an empty margin reference")
        if stem in by_stem and by_stem[stem]["verses"] and not page_secs:
            remarks.append(f"{stem}: no verses, the draft had {by_stem[stem]['verses']}")
    # wording against Tauber, over the verses the batch touches
    first_key = next((kk for block in pages.values() for kk, _t in block["text"] if VKEY.match(kk)), "")
    runs_on = _verses_run_on(slug, latin)
    if words:
        sections = tauber_sections(part="latin" if latin else "greek")
        order = sorted(sections, key=sec_key)
        lo = order.index(secs[0]) if secs[0] in order else 0
        hi = order.index(secs[-1]) if secs[-1] in order else len(order) - 1
        span = order[lo: hi + 1]
        pw = [(skel(piece), piece, s) for s in span for t in sections[s] for piece in re.split(r"[—–]+", t) if skel(piece)]
        ours = [w[0] for w in words]
        sm = difflib.SequenceMatcher(None, ours, [p[0] for p in pw], autojunk=False)
        ops = sm.get_opcodes()
        for k, (op, a0, a1, b0, b1) in enumerate(ops):
            if op == "equal":
                # the same letters: the accents and breathings too (a misprint of Lake's: κάρδίᾳ)
                for i in range(a1 - a0):
                    mine, theirs = _accented(words[a0 + i][1]), _accented(pw[b0 + i][1])
                    if mine != theirs:
                        where = words[a0 + i][2]
                        tag = " (noted)" if where in noted else ""
                        remarks.append(f"{where}: accents: written {words[a0 + i][1]} | Tauber has {pw[b0 + i][1]}{tag}")
                continue
            # a verse divided between two batch files: its other part is in the file before or after
            if op == "insert" and k == 0 and first_key.endswith("+"):
                continue
            if op == "insert" and k == len(ops) - 1 and a0 == len(ours) and secs[-1] in runs_on:
                continue
            where = words[a0][2] if a0 < len(words) else words[-1][2]
            mine = " ".join(w[1] for w in words[a0:a1]) or "(nothing)"
            theirs = " ".join(p[1] for p in pw[b0:b1]) or "(nothing)"
            tag = " (noted)" if where in noted else ""
            remarks.append(f"{where}: written {mine} | Tauber has {theirs}{tag}")
    return remarks


def _accented(word: str) -> str:
    """A word's letters with their accents and breathings, without stops, marks or elision."""
    w = unicodedata.normalize("NFC", plain(word)).replace("ς", "σ")
    return "".join(c for c in w if unicodedata.category(c)[0] == "L" and c not in "ʼʹ").lower()


def _verses_run_on(slug: str, latin: bool) -> set[str]:
    """The verses the draft divided between a page and the next (keyed `+` on the second)."""
    f = out_dir(slug) / ("latin-draft.json" if latin else "draft.json")
    if not f.exists():
        return set()
    return {e["sec"] for e in json.loads(f.read_text(encoding="utf-8")) if e.get("key") and e["key"].endswith("+")}


def roman(text: str) -> int | None:
    """A Roman numeral as written: II -> 2."""
    t = text.strip().rstrip(".").replace(" ", "")
    vals = {"I": 1, "V": 5, "X": 10, "L": 50, "C": 100}
    if not t or any(c not in vals for c in t):
        return None
    total = 0
    for k, c in enumerate(t):
        v = vals[c]
        total += -v if k + 1 < len(t) and vals[t[k + 1]] > v else v
    return total


def ocr_roman(text: str) -> int | None:
    """A chapter numeral as Tesseract reads it (Greek look-alike letters, 1 or l for I)."""
    return roman(text.strip().translate(str.maketrans("ΙΧ1l|Λ", "IXIIIV")))


def residuals(slug: str, files: list[Path] | None = None) -> list[dict]:
    """The residual pass (pipeline/transcriptions/hermas/RESIDUALS.md): what the checked verses and
    Tesseract's reading of the page still disagree on (words, accents, punctuation, brackets), per
    page, with a crop of the lines: residuals/r-NNNN.md and r-NNNN.png, residuals.json."""
    from PIL import Image, ImageDraw, ImageFont

    from .drama_pages import scan_dirs
    from .drama_residuals import page_residuals

    play = PLAYS[slug]
    pages = read_batches(transcriptions_dir(slug), files, latin=False if files is None else None)
    od = out_dir(slug) / "residuals"
    od.mkdir(exist_ok=True)
    _, sbuild = scan_dirs(play.scan)
    try:
        font = ImageFont.truetype("DejaVuSans-Bold.ttf", 30)
    except OSError:
        font = ImageFont.load_default()

    def stream(layout):
        from .drama_pages import fold_ocr

        lines, ocr, _nums = ocr_stream([layout])
        return fold_ocr(play, lines, ocr)  # ξ and ζ folded on both sides, as in the draft

    everything = []
    for stem, block in sorted(pages.items()):
        leaf = int(stem[2:])
        latin = stem.startswith("l-")
        items = [(k, plain(t)) for k, t in block["text"] if VKEY.match(k)]
        res = page_residuals(play, page_layout(play, leaf, latin), items, stream)
        noted = {m.group(1) for x in block["notes"] for m in re.finditer(r"\b(\d+\.\d+\.\d+)\b", x)}
        for r in res:
            r["stem"] = stem
            r["noted"] = r["n"].rstrip("+") in noted
        everything += res
        for old in od.glob(f"r-{stem}.*"):
            old.unlink()
        if not res:
            continue
        md = [f"# Residuals on {stem} (leaf {leaf}, Lake's p. {page_of(play, leaf)})", "",
              f"Image: r-{stem}.png (each line once, labelled with its verse); the whole page: ../pages/leaf_{leaf:04d}.png", ""]
        for k, r in enumerate(res, 1):
            what = {"word": f"the text has «{r['text']}», the OCR reads «{r['ocr']}»",
                    "accent": f"accents: the text has «{r['text']}», the OCR reads «{r['ocr']}»",
                    "punctuation": f"punctuation: the text has «{r['text']}», the OCR reads «{r['ocr']}»",
                    "bracket": f"brackets: the text has «{r['text']}», the OCR reads «{r['ocr']}»",
                    "ocr-only": f"the OCR reads «{r['ocr']}» here, the text has nothing"}[r["kind"]]
            md.append(f"{k}. {r['n']}: {what}" + (" (the verse is noted in the batch)" if r["noted"] else ""))
        (od / f"r-{stem}.md").write_text("\n".join(md) + "\n", encoding="utf-8")
        with Image.open(sbuild / "pages" / f"leaf_{leaf:04d}.png") as im:
            g = im.convert("L")
            spans = []
            for r in res:
                if r["y0"] is not None and (r["n"], r["y0"]) not in [(x[0], x[1]) for x in spans]:
                    spans.append((r["n"], r["y0"], r["y1"]))
            crops = [(n, g.crop((20, max(0, y0 - 14), g.size[0] - 20, y1 + 12))) for n, y0, y1 in spans]
        if crops:
            sheet = Image.new("L", (230 + max(c.size[0] for _n, c in crops), sum(c.size[1] + 10 for _n, c in crops)), 255)
            dr = ImageDraw.Draw(sheet)
            y = 0
            for n, c in crops:
                sheet.paste(c, (230, y))
                dr.text((8, y + c.size[1] // 2 - 18), n, fill=0, font=font)
                y += c.size[1] + 10
            sheet.save(od / f"r-{stem}.png")
    (od / "residuals.json").write_text(json.dumps(everything, ensure_ascii=False, indent=0), encoding="utf-8")
    return everything


def main(argv: list[str]) -> None:
    slug, step = argv[0], argv[1]
    if step in ("draft", "latin-draft"):
        latin = step == "latin-draft"
        index = write_draft(slug, latin)
        n = sum(p["entries"] for p in index)
        v = sum(p["verses"] for p in index)
        f = sum(p["flagged"] for p in index)
        print(f"{slug}{' (Latin)' if latin else ''}: {len(index)} pages, {v} verse blocks ({n} entries with headings), "
              f"{f} flagged ({100 * f // max(n, 1)} %); apparatus found on {sum(1 for p in index if p['apparatus'])}, "
              f"footnote marks placed {sum(p['marks'] for p in index)}")
    else:
        run(slug, step)


if __name__ == "__main__":
    main(sys.argv[1:])
