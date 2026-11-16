"""Lucian's A True Story in Nilén's Teubner edition (1906) from the scan by OCR, with only the
doubtful places left for a reader to check (pipeline/PLAN-true-story.md, steps 1-4).

The Gorgias route (gorgias_pages.py) for a prose text whose edition numbers its lines by page:
each text page is read by Tesseract (tessdata_best grc); its lines are matched word by word to
the Perseus text (Harmon's Loeb, the check text, never shipped); every printed line gets the key
`page.line` (133.14: Nilén's page 133, line 14 counted from the top of the text, a book's title
being line 1 of its page) and the Perseus sections (book.section) that begin in it. Nilén's
margins are the check: his line numbers every fifth line and the Vulgate page numbers stand on
the inner side of the page (the left of an odd page, the right of an even one), his chapter
numbers (Perseus's sections) on the outer side. Every place where the OCR and Perseus disagree
is flagged. The apparatus under the short rule below the text is cut out, enlarged and read
twice by Tesseract (Greek first, Latin first) as a help for the reader, who writes it from the
image.

    python -m anagnosis_pipeline lucian-pages truestory fetch   the text leaves, as grey PNG
    python -m anagnosis_pipeline lucian-pages truestory ocr     Tesseract, hOCR per leaf
    python -m anagnosis_pipeline lucian-pages truestory draft   draft, crops, check sheets, batch files

Files (each saved as soon as it is made, so that a rerun goes on where it stopped):

    pipeline/build/drama-scans/<scan>/pages/leaf_0200.png     the page, grey (shared with drama-prose)
    pipeline/build/drama-scans/<scan>/hocr/leaf_0200.grc.hocr Tesseract's reading (grc, --psm 4)
    pipeline/build/drama-scans/<scan>/hocr/leaf_0200.margins.json   the margin numbers read
    pipeline/build/lucian-pages/<slug>/p-0200.md              the check sheet
    pipeline/build/lucian-pages/<slug>/p-0200-lines.png       the flagged lines, each labelled with its key
    pipeline/build/lucian-pages/<slug>/p-0200-app-l.png, -app-r.png   the apparatus, halves enlarged
    pipeline/build/lucian-pages/<slug>/pages.json, draft.json
    pipeline/transcriptions/lucian/<slug>/batch-NN.md         six pages each, never overwritten

The batch file, per page:

    === p-0200
    --- text
    133.1	ὑποφαινομένης οὐ σφόδρα βιαίως ἀνηγόμεθα, τῆς ἐπιούσης
    133.14	ἀνελθεῖν ἐπὶ κατασκοπῇ τῶν ἐν τῇ νήσῳ. §1.7 προελθόντες
    --- apparatus
    1/2	τῆς ἐπιούσης ΓΩIS τῇ ἐπιούσῃ Γ*ˣZNFv γρ mg. S
    5	πνέοντι ΓΩS πνεύματι ZNFI ex corr. Ωˣ
    --- notes

`§1.7` stands before the word where a section begins (Nilén's chapter number in the margin), `¶`
on a line of its own before a line he indents, `[title]` before a book's title line, `| ` after
the TAB for a line of verse. The apparatus items carry the line number as printed (5, 1/2, 20/22;
`-` for a note that names no line: "Libri: …", a subscription).
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
from pathlib import Path

from . import greek
from .drama import APOS, PLAYS, Play, skel

ROOT = Path(__file__).resolve().parent.parent.parent
PIPELINE = ROOT / "pipeline"
TESSDATA = PIPELINE / "tessdata"
TEI = "{http://www.tei-c.org/ns/1.0}"
PAGES_PER_BATCH = 6
ROUTE = "lucian-pages"


def out_dir(slug: str) -> Path:
    from .drama_pages import route_dir

    return route_dir(ROUTE, slug, PLAYS[slug].scan)


def transcriptions_dir(slug: str) -> Path:
    return PIPELINE / "transcriptions" / "lucian" / slug


def page_of(play: Play, leaf: int) -> int:
    return leaf - play.page_offset


# --- the Perseus text of a prose work (book.section) ----------------------------------------------

_ELISION = re.compile(r"(?<=[Ͱ-Ͽἀ-῿])['’᾽](?=\s|$|[,.;·:!?)\]⟩—])")
SEC, PARA, VERSE, VEND, GAP = "", "", "", "", ""
HEAD, QOPEN, QCLOSE = "\ue005", "\ue006", "\ue007"


def perseus_prose(path: Path, book: str = "", quotes: bool = False, headings: bool = False) -> tuple[list[dict], list[dict]]:
    """The words of a Perseus prose text divided into books and sections (div subtype book /
    section), in order: {'t' (the word as written, with its punctuation and brackets), 'skel',
    'sec' ('1.7'), 'newsec' (a section begins at it), 'para' (a <p> begins at it), 'glued' (no
    space before it), 'verse' (a line of verse begins at it), 'inverse', 'gap' (Perseus marks
    lost text after it), 'label': False}; and the notes taken out of the text: {'sec', 'after'
    (the index of the word the note follows, -1 before the first), 'n', 'text'}. A note in a
    heading belongs to the first section after it.

    For a work that is one file of a collection, without book divisions (a speech of Lysias,
    hude_pages.py): `book` is the number its sections are counted under ('12' gives 12.7);
    `quotes` writes a <q> as ‘…’ (the closing mark is kept apart from the elision sign);
    `headings` marks the words of a <label> (the Μάρτυρες, Νόμος set on a line of their own in a
    speech) with 'heading': True, and a section that Perseus begins with its label begins at the
    first word after it."""
    from lxml import etree

    root = etree.parse(str(path)).getroot()
    body = root.find(f".//{TEI}body")
    parts: list[str] = []
    notes: list[dict] = []
    book = [book]

    def text(s: str | None) -> None:
        if s:
            parts.append(s.replace("\n", " "))

    def walk(el) -> None:
        tag = etree.QName(el).localname
        if tag == "note":
            notes.append({"pos": len(parts), "n": el.get("n", ""), "text": " ".join("".join(el.itertext()).split())})
            return
        if tag == "head":
            for n in el.iter(f"{TEI}note"):
                notes.append({"pos": len(parts), "n": n.get("n", ""), "text": " ".join("".join(n.itertext()).split())})
            return
        if tag in ("bibl", "pb", "milestone"):
            return
        if tag == "gap":
            parts.append(GAP)
            return
        if tag == "div":
            if el.get("subtype") == "book":
                book[0] = el.get("n")
            elif el.get("subtype") == "section":
                parts.append(f" {SEC}{book[0]}.{el.get('n')}{SEC} ")
        if tag == "p":
            parts.append(f" {PARA} ")
        if tag == "l":
            parts.append(f" {VERSE}")
        if tag == "label" and headings:
            for n in el.iter(f"{TEI}note"):
                notes.append({"pos": len(parts), "n": n.get("n", ""), "text": " ".join("".join(n.itertext()).split())})
            bits = [el.text or ""] + [c.tail or "" for c in el.iter() if c is not el and etree.QName(c).localname == "note"] \
                + ["".join(c.itertext()) + (c.tail or "") for c in el if etree.QName(c).localname != "note"]
            for w in " ".join(bits).split():
                parts.append(f" {HEAD}{w} ")
            return
        open_, close = {"add": ("⟨", "⟩"), "del": ("[", "]")}.get(tag, ("", ""))
        if tag == "q" and quotes:
            open_, close = QOPEN, QCLOSE
        parts.append(open_)
        text(el.text)
        for child in el:
            walk(child)
            text(child.tail)
        parts.append(close)
        if tag == "l":
            parts.append(f"{VEND} ")

    walk(body)
    # the notes' positions as markers in the running text
    marked: list[str] = []
    by_pos: dict[int, list[int]] = {}
    for k, nt in enumerate(notes):
        by_pos.setdefault(nt["pos"], []).append(k)
    for i, p in enumerate(parts + [""]):
        for k in by_pos.get(i, []):
            marked.append(f" {k} ")
        marked.append(p)
    s = greek.nfc("".join(marked))
    s = _ELISION.sub(APOS, s)
    if quotes:
        s = re.sub(QOPEN + r"\s*", "‘", s)
        s = re.sub(r"\s*" + QCLOSE, "’", s)
    s = re.sub(r"([⟨\[“])\s+", r"\1", s)
    s = re.sub(r"\s+([⟩\]”])", r"\1", s)
    out: list[dict] = []
    sec, newsec, para, verse, inverse = "", False, False, False, False
    pieces: list[tuple[str, bool]] = []
    for raw in s.split():
        ps = re.split(r"(?<=[^\s—])—(?=[^\s—])", raw)
        for k, piece in enumerate(ps):
            pieces.append((piece + ("—" if k + 1 < len(ps) else ""), k > 0))
    for raw, glued in pieces:
        mk = re.fullmatch("(\\d+)", raw)
        if mk:
            notes[int(mk.group(1))]["after"] = len(out) - 1
            continue
        if raw.startswith(SEC) and raw.endswith(SEC) and len(raw) > 2:
            sec, newsec = raw.strip(SEC), True
            continue
        if raw == PARA:
            para = True
            continue
        ends = VEND in raw
        raw = raw.replace(VEND, "")
        if raw.startswith(VERSE):
            raw = raw[1:]
            verse = inverse = True
        gap = GAP in raw
        raw = raw.replace(GAP, "")
        heading = HEAD in raw
        raw = raw.replace(HEAD, "")
        if raw:
            tok = {"t": raw, "skel": skel(raw), "sec": sec, "newsec": newsec, "para": para, "glued": glued,
                   "verse": verse, "inverse": inverse, "gap": gap, "label": False}
            if heading and tok["skel"]:
                # the label's line is not the section's first word: the marks wait for the word after it
                tok.update(heading=True, newsec=False, para=False)
                out.append(tok)
                continue
            if tok["skel"]:
                out.append(tok)
                newsec = para = verse = False
            elif out:
                # punctuation standing alone goes with the word before; a dash keeps its space (Nilén: "ἀνέσεως — μέρος")
                out[-1]["t"] += (" " + raw) if raw[0] in "—–" else raw
        elif gap and out:
            out[-1]["gap"] = True
        if ends:
            inverse = False
    res = []
    for nt in notes:
        after = nt.get("after", -1)
        sec_ = out[after]["sec"] if after >= 0 else (out[0]["sec"] if out else "")
        res.append({"sec": sec_, "after": after, "n": nt["n"], "text": nt["text"]})
    return out, res


def perseus_sections(path: Path) -> dict[str, list[str]]:
    """Each section's words (as written), in order."""
    toks, _notes = perseus_prose(path)
    out: dict[str, list[str]] = {}
    for t in toks:
        out.setdefault(t["sec"], []).append(t["t"])
    return out


def translation_sections(path: Path) -> list[tuple[str, str]]:
    """A Perseus translation divided into books and sections: [(book.section, text)], the
    footnotes left out."""
    from lxml import etree

    root = etree.parse(str(path)).getroot()
    body = root.find(f".//{TEI}body")
    out: list[tuple[str, str]] = []

    def flat(el) -> str:
        bits: list[str] = []

        def w(e) -> None:
            tag = etree.QName(e).localname
            if tag in ("note", "head", "bibl"):
                return
            if tag == "l":
                bits.append(" ")
            if e.text:
                bits.append(e.text)
            for c in e:
                w(c)
                if c.tail:
                    bits.append(c.tail)
            if tag in ("l", "p"):
                bits.append(" ")

        w(el)
        return " ".join("".join(bits).split())

    for bk in body.iter(f"{TEI}div"):
        if bk.get("subtype") != "book":
            continue
        for sc in bk.iter(f"{TEI}div"):
            if sc.get("subtype") == "section":
                out.append((f"{bk.get('n')}.{sc.get('n')}", flat(sc)))
    return out


# --- fetch, OCR, the page ---------------------------------------------------------------------

def run(slug: str, step: str, workers: int = 4) -> None:
    from .drama_pages import fetch_leaf, ocr_leaf

    play = PLAYS[slug]
    leaves = play.visible("text")
    if not leaves:
        raise SystemExit(f"{slug}: no text leaves in drama.PLAYS yet (step 2)")
    out_dir(slug)
    with ThreadPoolExecutor(workers) as ex:
        if step == "fetch":
            list(ex.map(lambda l: fetch_leaf(play.scan, l), leaves))
        elif step == "ocr":
            list(ex.map(lambda l: ocr_leaf(play.scan, l), leaves))
        else:
            raise SystemExit(f"unknown step {step!r}")
    print(f"{slug}: {step} done for {len(leaves)} leaves")


def short_rule(path: Path) -> int | None:
    """The top of the short rule Nilén sets between the text and the apparatus: a band of ink at
    most 14 pixels high with 12 blank rows above (the descenders of the last line come close) and
    20 below, 8-40 % of the page wide and at least 30 % inked (the rule is faint and broken on many
    pages); the first such band below the top quarter of the page (the end of a book has a second,
    the closing ornament)."""
    from PIL import Image

    with Image.open(path) as im:
        g = im.convert("L")
    W, H = g.size
    m = int(0.04 * W)
    found: list[int] = []
    for thr in (170, 190):
        ink = g.crop((m, 0, W - m, H)).point(lambda v, t=thr: 255 if v < t else 0)
        w = W - 2 * m
        rows = [v * w / 255 for v in ink.resize((1, H), Image.BOX).tobytes()]

        def blank(a: int, b: int) -> bool:
            seg = rows[max(0, a):max(0, b)]
            return bool(seg) and max(seg) <= 0.004 * W

        y = int(0.25 * H)
        while y < int(0.97 * H):
            if rows[y] < 0.008 * W or not blank(y - 14, y - 2):
                y += 1
                continue
            y1 = y
            while y1 < H and rows[y1] >= 0.002 * W and y1 - y < 18:
                y1 += 1
            if y1 - y <= 14 and blank(y1 + 1, y1 + 22):
                cols = ink.crop((0, y, w, y1)).resize((w, 1), Image.BOX).tobytes()
                xs = [x for x, v in enumerate(cols) if v > 0]
                if xs:
                    span = xs[-1] - xs[0]
                    if 0.08 * W <= span <= 0.4 * W and len(xs) >= 0.3 * span:
                        found.append(y)
                        break
            y = y1 + 1
    return min(found) if found else None


def page_layout(play: Play, leaf: int) -> dict:
    """drama_pages.page_layout with the apparatus taken as everything under the short rule (or,
    where no rule is found, as that function finds it)."""
    from .drama_pages import page_layout as drama_layout, scan_dirs

    _, sbuild = scan_dirs(play.scan)
    png = sbuild / "pages" / f"leaf_{leaf:04d}.png"
    rule = short_rule(png)
    lay = drama_layout(play, leaf, app_y=rule)
    lay["short_rule"] = rule
    # a book's title in spaced capitals, read with little confidence, is passed over as noise:
    # put it back, as the page's first line
    from .drama_pages import ocr_leaf, read_lines

    first = min((p["y0"] for p in lay["lines"]), default=lay["height"])
    have = any(is_title(" ".join(w["text"] for w in p["words"])) for p in lay["lines"])
    if not have:
        for l in read_lines(ocr_leaf(play.scan, leaf)):
            text = " ".join(w["text"] for w in l["words"])
            if l["bbox"][3] <= first + 10 and l["bbox"][1] > lay["head_y"] and is_title(text):
                lay["lines"].insert(0, {"y0": l["bbox"][1], "y1": l["bbox"][3], "oy0": l["bbox"][1], "oy1": l["bbox"][3],
                                        "words": l["words"], "left_m": [], "right_m": [], "x0": l["bbox"][0], "x1": l["bbox"][2]})
                break
    return lay


def is_title(text: str) -> bool:
    """A book's title as Tesseract reads it: ΑΛΗΘΩΝ ΔΙΗΓΗΜΑΤΩΝ Α, in capitals."""
    letters = [c for c in text if c.isalpha()]
    caps = letters and sum(c.isupper() for c in letters) >= 0.8 * len(letters)
    return bool(caps and len(letters) >= 10 and re.search(r"ΑΛΗ|ΔΙΗΓ|ΗΜΑ|ΘΩΝ|ΤΩΝ", text))


def margin_marks(play: Play, layout: dict) -> list[dict]:
    """The numbers printed in both margins beside the text lines: [{'y', 'side' ('l'/'r'),
    'kind' ('line', 'vulgate', 'chapter'), 'n'}]. For each printed line, the ink beyond its words
    on either side is cut out, enlarged and read by Tesseract's English model limited to digits
    (cached). On an odd page the line numbers and the Vulgate pages stand left, the chapter
    numbers right; on an even page the other way round. A number on the inner side is a line
    number if it is at most 30, else a Vulgate page."""
    from PIL import Image, ImageOps

    from .drama_pages import scan_dirs

    _, sbuild = scan_dirs(play.scan)
    leaf = layout["leaf"]
    cache = sbuild / "hocr" / f"leaf_{leaf:04d}.margins.json"
    if cache.exists():
        raw = json.loads(cache.read_text())
    else:
        H = layout["line_h"]
        env = dict(os.environ, OMP_THREAD_LIMIT="1")
        raw = []
        # the column's edges: where the lines begin, and the median end of their last word of
        # letters (the lines are justified; a number set beyond the column is not a word of it)
        ends = sorted(max(w["bbox"][2] for w in ws) for p in layout["lines"]
                      if (ws := [w for w in p["words"] if len(skel(w["text"])) >= 2]))
        col_r = ends[len(ends) // 2] if ends else layout["right"]
        col_l = layout["left"]
        with Image.open(sbuild / "pages" / f"leaf_{leaf:04d}.png") as im, tempfile.TemporaryDirectory() as t:
            g = im.convert("L")
            W = g.size[0]
            for p in layout["lines"]:
                for side in ("l", "r"):
                    if side == "r":
                        x0, x1 = col_r + 6, W - 8
                    else:
                        x0, x1 = 8, col_l - 6
                    if x1 - x0 < 0.5 * H:
                        continue
                    strip = g.crop((x0, max(0, p["oy0"] - 6), x1, p["oy1"] + 6))
                    cols = list(strip.point(lambda v: 255 if v < 140 else 0).resize((strip.size[0], 1), Image.BOX).tobytes())
                    ink = [x for x, v in enumerate(cols) if v > 6]
                    if not ink:
                        continue
                    if side == "r":
                        a = b = ink[0]
                        for x in ink:
                            if x - b > 0.8 * H:
                                break
                            b = x
                    else:
                        a = b = ink[-1]
                        for x in reversed(ink):
                            if a - x > 0.8 * H:
                                break
                            a = x
                    if b - a < 0.15 * H or b - a > 2.5 * H:
                        continue
                    piece = strip.crop((max(0, a - 10), 0, min(strip.size[0], b + 10), strip.size[1]))
                    piece = ImageOps.expand(piece.resize((piece.size[0] * 2, piece.size[1] * 2), Image.LANCZOS), 40, fill=255)
                    path = Path(t) / "n.png"
                    piece.save(path)
                    reads = []
                    for psm in ("7", "8", "10", "13"):
                        out = subprocess.run(["tesseract", str(path), "stdout", "--tessdata-dir", str(TESSDATA), "-l", "eng", "--psm", psm,
                                              "-c", "tessedit_char_whitelist=0123456789"], capture_output=True, text=True, env=env).stdout.strip()
                        if re.fullmatch(r"\d{1,3}", out):
                            reads.append(int(out))
                    if reads:
                        best = Counter(reads).most_common(1)[0][0]
                        raw.append([(p["oy0"] + p["oy1"]) // 2, side, best])
        cache.write_text(json.dumps(raw))
    odd = page_of(play, leaf) % 2 == 1
    inner = "l" if odd else "r"
    marks = []
    for y, side, n in raw:
        if side == inner:
            kind = "line" if n <= 30 else "vulgate"
        else:
            kind = "chapter"
        marks.append({"y": y, "side": side, "kind": kind, "n": n})
    return marks


# --- the OCR's words ---------------------------------------------------------------------------

def ocr_stream(layouts: list[dict]) -> tuple[list[dict], list[dict]]:
    """The printed lines of the text in order ({'leaf', 'y0', 'y1', 'x0', 'indent', 'line_h',
    'ocr', 'title'}) and the OCR's words ({'t', 'skel', 'line', 'conf'}). A word divided at the
    end of a line is joined and belongs to the line where it begins (unless that would leave the
    next line without a word of its own). A book's title (ΑΛΗΘΩΝ ΔΙΗΓΗΜΑΤΩΝ Α) is a line of its
    own, without words."""
    from .drama_pages import DASHES, ocr_norm

    lines: list[dict] = []
    toks: list[dict] = []
    for lay in layouts:
        for p in lay["lines"]:
            ws = sorted(p["words"], key=lambda w: w["bbox"][0])
            text = " ".join(w["text"] for w in ws)
            li = len(lines)
            title = is_title(text)
            # where the line's words begin (a chapter number read as a letter, "δ." for 5, is not one)
            x0 = min((w["bbox"][0] for w in ws if len(skel(w["text"])) >= 2), default=p["x0"])
            lines.append({"leaf": lay["leaf"], "y0": p["y0"], "y1": p["y1"], "oy0": p.get("oy0", p["y0"]), "oy1": p.get("oy1", p["y1"]),
                          "x0": x0, "indent": x0 - lay["left"], "line_h": lay["line_h"],
                          "ocr": text, "title": title})
            if title:
                continue
            for w in ws:
                for piece in DASHES.split(ocr_norm(w["text"])):
                    if not piece.strip():
                        continue
                    if not skel(piece) and toks and toks[-1]["line"] == li and re.fullmatch(r"[.,·;:'\"”᾽˙]+", piece.strip()):
                        toks[-1]["t"] += piece.strip()  # Nilén's stop set off by a space ("ἦν .")
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


def fold(play: Play, lines: list[dict], ocr: list[dict]) -> None:
    """The OCR's letters as Nilén's Teubner type means them (ϑ is θ, ϰ is κ), its skeletons
    folded as the check text's (χ counts as κ)."""
    if play.ocr_fold:
        tr = str.maketrans(play.ocr_fold)
        for t in ocr:
            t["t"] = t["t"].translate(tr)
            t["skel"] = skel(t["t"])
        for pl in lines:
            pl["ocr"] = pl["ocr"].translate(tr)
    if play.skel_fold:
        tr = str.maketrans(play.skel_fold[0::2], play.skel_fold[1::2])
        for t in ocr:
            t["skel"] = t["skel"].translate(tr)


# --- the draft ---------------------------------------------------------------------------------

def number_lines(play: Play, lines: list[dict], pers: list[dict]) -> list[dict]:
    """Nilén's lines with their keys: {'n' ('133.14'), 'page', 'count', 'words' (Perseus
    indexes), 'line' (printed line), 'title', 'starts' ([(Perseus index, section)] of the
    sections that begin on the line), 'flags'}. The lines of a page are counted from the top of
    the text, a book's title being line 1; a printed line no Perseus word was placed on is
    passed over (and flagged on the line before)."""
    by_line: dict[int, list[int]] = {}
    for j, t in enumerate(pers):
        by_line.setdefault(t["line"], []).append(j)
    out: list[dict] = []
    count: dict[int, int] = {}
    for li, pl in enumerate(lines):
        words = by_line.get(li)
        page = page_of(play, pl["leaf"])
        if not words and not pl["title"]:
            if len(skel(pl["ocr"])) >= 8:
                pl["dropped"] = True
            continue
        count[page] = count.get(page, 0) + 1
        c = count[page]
        starts = [(j, pers[j]["sec"]) for j in (words or []) if pers[j]["newsec"]]
        flags: list[str] = []
        if len(starts) > 1:
            flags.append(f"two sections begin on this line ({', '.join(s for _j, s in starts)})")
        out.append({"n": f"{page}.{c}", "page": page, "count": c, "words": words or [], "line": li, "title": pl["title"],
                    "starts": starts, "flags": flags, "leaf": pl["leaf"]})
    return out


def check_margins(play: Play, numbered: list[dict], lines: list[dict], layouts: dict[int, dict]) -> None:
    """The keys against Nilén's line numbers, the sections against his chapter numbers."""
    by_leaf: dict[int, list[dict]] = {}
    for L in numbered:
        by_leaf.setdefault(L["leaf"], []).append(L)
    for leaf, Ls in by_leaf.items():
        lay = layouts[leaf]
        marks = margin_marks(play, lay)
        pitch = lay["line_h"] * 1.3
        seen_line: set[int] = set()
        seen_chap: set[int] = set()
        page_secs = {int(sec.split(".")[1]) for L in Ls for _j, sec in L["starts"]}
        for mk in marks:
            near = min(Ls, key=lambda L: abs((lines[L["line"]]["oy0"] + lines[L["line"]]["oy1"]) / 2 - mk["y"]))
            if abs((lines[near["line"]]["oy0"] + lines[near["line"]]["oy1"]) / 2 - mk["y"]) > 0.6 * pitch:
                continue
            near.setdefault("marks", []).append(f"{mk['kind']} {mk['n']}")
            if mk["kind"] == "line":
                # Tesseract reads Nilén's 5 as 3 and his 15 as 13: a number at a fifth line confirms
                # it whatever it reads; elsewhere only a plausible misnumbering is reported
                if near["count"] % 5 == 0:
                    seen_line.add(id(near))
                elif mk["n"] % 5 == 0 and abs(mk["n"] - near["count"]) <= 3:
                    near["flags"].append(f"the margin reads line {mk['n']} here, but the line is {near['n']}")
            elif mk["kind"] == "chapter":
                secs = [int(sec.split(".")[1]) for _j, sec in near["starts"]]
                if secs:
                    seen_chap.add(id(near))  # the value is often misread (2 as 9); the place is the check
                elif mk["n"] in page_secs or any(mk["n"] - 1 <= x <= mk["n"] + 1 for x in page_secs):
                    near["flags"].append(f"the margin has a chapter number (read “{mk['n']}”) at this line, "
                                         "but Perseus begins no section here")
        for L in Ls:
            if L["count"] % 5 == 0 and id(L) not in seen_line:
                L["flags"].append(f"no line number read in the margin, though {L['n']} should have one ({L['count']})")
            if L["starts"] and id(L) not in seen_chap:
                L["flags"].append(f"no chapter number read in the margin, though section {L['starts'][-1][1]} begins on this line")


def line_texts(numbered: list[dict], lines: list[dict], ocr: list[dict], pers: list[dict], match: list[int | None]) -> None:
    """Each line's text (L['text']) with its § markers, paragraphs (L['para']), and the flags
    that come from comparing the words with the OCR."""
    from .drama_pages import _accent_letters, _capitalise, _starts_upper

    paired_o = {o for o in match if o is not None}
    by_line_o: dict[int, list[int]] = {}
    for k, t in enumerate(ocr):
        by_line_o.setdefault(t["line"], []).append(k)
    for L in numbered:
        pl = lines[L["line"]]
        flags = L["flags"]
        if L["title"]:
            L["text"] = "[title] " + pl["ocr"]
            L["para"] = False
            continue
        out: list[str] = []
        for j in L["words"]:
            t = pers[j]
            w = t["t"]
            o = match[j]
            if o is not None and t["sim"] >= 0.8:
                # the case of the first letter as printed (Perseus capitalises the inscription
                # "Ἄχρι τούτων", Nilén does not; Nilén begins a paragraph with a capital)
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
                flags.append(f"{w}: not found in the OCR; check it is printed on this line")
            elif t["sim"] < 1.0 and ocr[o]["conf"] >= 70:
                flags.append(f"{w}: the OCR reads “{ocr[o]['t']}”")
            elif t["sim"] == 1.0 and len(t["skel"]) >= 4 and ocr[o]["conf"] >= 95:
                if _accent_letters(w) != _accent_letters(ocr[o]["t"]):
                    flags.append(f"{w}: the OCR reads “{ocr[o]['t']}” (accents)")
            if t.get("guess"):
                flags.append(f"{w}: which line it stands on is a guess")
            if t.get("gap"):
                flags.append(f"{w}: Perseus marks a gap (lost text) after this word; copy what Nilén prints (* * *)")
        for k in by_line_o.get(L["line"], []):
            if k not in paired_o and len(ocr[k]["skel"]) >= 4 and ocr[k]["conf"] >= 80:
                flags.append(f"the OCR reads “{ocr[k]['t']}” on this line, which Perseus does not have here")
        verse = bool(L["words"]) and pers[L["words"][0]]["inverse"]
        text = " ".join(out)
        if verse:
            text = "| " + text
            if any(not pers[j]["inverse"] for j in L["words"]):
                flags.append("verse and prose on one line")
        if "*" in pl["ocr"]:
            flags.append("the OCR reads an asterisk on this line: copy Nilén's * (a lacuna, or προ*ελθεῖν) where printed")
        for open_, close, name in (("[", "]", "square brackets"), ("⟨", "⟩", "angle brackets")):
            o_has = any(c in pl["ocr"] for c in (open_, close) + (("<", ">") if open_ == "⟨" else ()))
            d_has = open_ in text or close in text
            if o_has and not d_has:
                flags.append(f"the OCR shows {name} on this line, Perseus has none: copy Nilén's")
            elif d_has and not o_has:
                flags.append(f"Perseus has {name} on this line, the OCR shows none: check the print")
        indented = pl["indent"] > 0.6 * pl["line_h"]
        L["para"] = indented and not verse
        if L["para"] and out:
            # Nilén begins every paragraph with a capital (the OCR often loses its breathing)
            k = 1 if out[0].startswith("§") and len(out) > 1 else 0
            if not _starts_upper(out[k]):
                out[k] = _capitalise(out[k])
                text = ("| " if verse else "") + " ".join(out)
        L["text"] = text
    for k, L in enumerate(numbered):
        nxt = numbered[k + 1]["line"] if k + 1 < len(numbered) else len(lines)
        for li in range(L["line"] + 1, nxt):
            if lines[li].get("dropped"):
                L["flags"].append(f"the next printed line, read as “{lines[li]['ocr'][:60]}”, matched no Perseus words")


def _lowercase(word: str) -> str:
    m = re.match(r"^([“‘\[⟨(]*)(.)(.*)$", word, re.S)
    if not m:
        return word
    d = unicodedata.normalize("NFD", m.group(2))
    return m.group(1) + unicodedata.normalize("NFC", d[0].lower() + d[1:]) + m.group(3)


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
    pers, _notes = perseus_prose(sources / play.perseus)
    if play.skel_fold:
        tr = str.maketrans(play.skel_fold[0::2], play.skel_fold[1::2])
        for t in pers:
            t["skel"] = t["skel"].translate(tr)
    match = align(ocr, pers)
    mended = realign(ocr, pers, match)
    if mended:
        print(f"{play.slug}: {mended} stretches aligned again", file=sys.stderr)
    found = [j for j, o in enumerate(match) if o is not None]
    lo = max(0, found[0] - 12) if found else 0
    hi = min(len(pers), found[-1] + 13) if found else 0
    if lo > 0 or hi < len(pers):
        print(f"{play.slug}: the pages hold Perseus {pers[lo]['sec']}–{pers[hi - 1]['sec']}; "
              f"{lo} words before and {len(pers) - hi} after were not found", file=sys.stderr)
    sub, subm = pers[lo:hi], match[lo:hi]
    assign_lines(lines, ocr, sub, subm)
    numbered = number_lines(play, lines, sub)
    check_margins(play, numbered, lines, layouts)
    line_texts(numbered, lines, ocr, sub, subm)
    for L in numbered:
        pl = lines[L["line"]]
        L["y0"], L["y1"], L["ocr"] = pl["y0"], pl["y1"], pl["ocr"]
        L["flags"] = list(dict.fromkeys(L["flags"]))
    return numbered, layouts, lines, sub


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
    for b, leaf in enumerate(leaves):
        Ls = by_leaf.get(leaf, [])
        stem = f"p-{leaf:04d}"
        page = page_of(play, leaf)
        for old in od.glob(f"{stem}-*.png"):
            old.unlink()
        lay = layouts[leaf]
        app = apparatus_images(play, leaf, lay, od, stem) if lay["app_y"] is not None else {}
        flagged = [L for L in Ls if L["flags"]]
        has_lines = lines_image(play, leaf, flagged, od / f"{stem}-lines.png")
        md = [f"# Page {page} ({stem}, leaf {leaf}): lines {Ls[0]['n']}–{Ls[-1]['n']}" if Ls else f"# Page {page} ({stem}, leaf {leaf})", ""]
        imgs = [f"pages/leaf_{leaf:04d}.png (the whole page)"]
        if has_lines:
            imgs.append(f"{stem}-lines.png (the flagged lines, each with its key)")
        if app:
            imgs.append(f"{stem}-app-l.png and {stem}-app-r.png (the apparatus, left and right half, enlarged)")
        md.append("Images: " + "; ".join(imgs))
        md.append("")
        md.append(f"Page {page} is {'odd' if page % 2 else 'even'}: the line numbers (every fifth line) and the Vulgate "
                  f"page numbers stand in the {'left' if page % 2 else 'right'} margin, the chapter numbers in the "
                  f"{'right' if page % 2 else 'left'}.")
        if lay.get("short_rule") is None:
            md.append("")
            md.append("**The short rule above the apparatus was not found on this page**: check where the text ends.")
        md.append("")
        md.append("## Flags on the text")
        md.append("")
        if flagged:
            for L in flagged:
                md.append(f"* {L['n']}  `{L['text']}`")
                for f in L["flags"]:
                    md.append(f"    * {f}")
        else:
            md.append("None: the OCR agrees with Perseus on every line, and the margins with the keys.")
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
        index.append({"stem": stem, "leaf": leaf, "page": page, "first": Ls[0]["n"] if Ls else None,
                      "last": Ls[-1]["n"] if Ls else None, "lines": len(Ls), "flagged": len(flagged),
                      "batch": b // PAGES_PER_BATCH + 1, "apparatus": bool(app), "rule": lay.get("short_rule") is not None,
                      "sections": [s for L in Ls for _j, s in L["starts"]]})
    (od / "pages.json").write_text(json.dumps(index, ensure_ascii=False, indent=1), encoding="utf-8")
    (od / "draft.json").write_text(json.dumps(
        [{k: L.get(k) for k in ("n", "leaf", "text", "para", "flags", "y0", "y1", "ocr", "marks")} for L in numbered],
        ensure_ascii=False, indent=0), encoding="utf-8")
    transcriptions.mkdir(parents=True, exist_ok=True)
    for b in range(0, len(leaves), PAGES_PER_BATCH):
        path = transcriptions / f"batch-{b // PAGES_PER_BATCH + 1:02d}.md"
        if path.exists():
            continue
        out = []
        for leaf in leaves[b : b + PAGES_PER_BATCH]:
            out.append(f"=== p-{leaf:04d}")
            out.append("--- text")
            for L in by_leaf.get(leaf, []):
                if L["para"]:
                    out.append("¶")
                out.append(f"{L['n']}\t{L['text']}")
            out.append("--- apparatus")
            out.append("--- notes")
            out.append("")
        path.write_text("\n".join(out), encoding="utf-8")
    return index


# --- reading and checking a batch -------------------------------------------------------------

KEY = re.compile(r"^(\d+)\.(\d+)$")
APP_KEY = re.compile(r"^(?:(\d+)(?:/(\d+)| et (\d+))?(?: sqq?\.)?|-)$")
SECTION_MARK = re.compile(r"§(\d+)\.(\d+)")


def read_batches(directory: Path, files: list[Path] | None = None) -> dict[str, dict]:
    """Page blocks by stem: {'text': [(key, text)] with ('¶', '') for a paragraph, 'apparatus':
    [(number, item)], 'notes': [str], 'errors': [str], 'batch': name}."""
    pages: dict[str, dict] = {}
    for path in files or sorted(directory.glob("batch-*.md")):
        stem, part = None, None
        for raw in path.read_text(encoding="utf-8").splitlines():
            m = re.match(r"^=== (p-\d{4})\s*$", raw)
            if m:
                stem = m.group(1)
                pages[stem] = {"text": [], "apparatus": [], "notes": [], "errors": [], "batch": path.name}
                part = None
                continue
            m = re.match(r"^--- (text|apparatus|notes)\s*$", raw)
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
    """A batch line's Greek without the markers (§1.7, | , [title])."""
    text = SECTION_MARK.sub(" ", text)
    text = re.sub(r"^\|\s*", "", text)
    return text


def check_batch(slug: str, path: Path, sources: Path) -> list[str]:
    """Remarks on one checked batch file: pages missing or foreign, keys that do not run on,
    section marks out of order, apparatus numbers naming no line of the page, elision, NFC,
    divided words, spaces before punctuation, and every place where the words differ from
    Perseus (each a change made on checking; '(noted)' where the page's notes name the line)."""
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
    for stem, block in pages.items():
        for e in block["errors"]:
            remarks.append(f"{stem}: {e}")
        page = by_stem[stem]["page"] if stem in by_stem else None
        for raw in block["notes"]:
            mm = re.match(r"^(\d+\.\d+|\d+)", raw)
            if mm:
                noted.add(mm.group(1) if "." in mm.group(1) else f"{page}.{mm.group(1)}")
        count = 0
        for key, text in block["text"]:
            if key == "¶":
                continue
            mm = KEY.match(key)
            if not mm:
                remarks.append(f"{stem}: bad key {key!r} (page.line)")
                continue
            if page is not None and int(mm.group(1)) != page:
                remarks.append(f"{stem} {key}: the page is {page}")
            count += 1
            if int(mm.group(2)) != count:
                remarks.append(f"{stem} {key}: line {count} of the page by its place: the numbering does not run on")
            if text != unicodedata.normalize("NFC", text):
                remarks.append(f"{stem} {key}: not NFC")
            if text.startswith("[title]"):
                continue
            if re.search(r"[Ͱ-Ͽἀ-῿][’'᾽]", text) or re.search(r"[᾽']", text):
                remarks.append(f"{stem} {key}: elision written other than ʼ")
            if re.search(r"[Ͱ-Ͽἀ-῿]-\s*$", text):
                remarks.append(f"{stem} {key}: a divided word? write it whole on the line where it begins")
            if re.search(r"\s[.,·;:]", plain(text)):
                remarks.append(f"{stem} {key}: a space before a stop (Nilén's spacing is not copied)")
            if re.search(r"§(?!\d+\.\d+\s)", text + " "):
                remarks.append(f"{stem} {key}: a section mark not written §book.section followed by a space")
            for mk in SECTION_MARK.finditer(text):
                cur = (int(mk.group(1)), int(mk.group(2)))
                if prev_sec is not None and not (cur == (prev_sec[0], prev_sec[1] + 1) or cur == (prev_sec[0] + 1, 1)):
                    remarks.append(f"{stem} {key}: section {cur[0]}.{cur[1]} follows {prev_sec[0]}.{prev_sec[1]}")
                prev_sec = cur
            # the words, each with the section it stands in
            pos = 0
            for mk in list(SECTION_MARK.finditer(text)) + [None]:
                chunk = text[pos: mk.start() if mk else len(text)]
                for w, _s, _e in greek.words(re.sub(r"^\|\s*", "", chunk)):
                    words.append((skel(w), w, key))
                if mk is not None:
                    secs.append(f"{mk.group(1)}.{mk.group(2)}")
                    pos = mk.end()
        if count and stem in by_stem and abs(count - by_stem[stem]["lines"]) > 2:
            remarks.append(f"{stem}: {count} lines, the draft had {by_stem[stem]['lines']}")
        if count and not block["apparatus"] and not any("no apparatus" in x for x in block["notes"]):
            remarks.append(f"{stem}: no apparatus (if the page prints none, say “no apparatus on this page” under notes)")
        for n, item in block["apparatus"]:
            mm = APP_KEY.match(n)
            if not mm:
                remarks.append(f"{stem}: bad apparatus number {n!r} (5, 1/2, 8 et 9, 18 sq., or - for a note on no line)")
                continue
            if n != "-":
                a, b = int(mm.group(1)), int(mm.group(2) or mm.group(3) or mm.group(1))
                if not (1 <= a <= max(count, 1)) or b < a or b > count + 3:
                    remarks.append(f"{stem}: apparatus {n} names a line not on this page (it has {count})")
            if item != unicodedata.normalize("NFC", item):
                remarks.append(f"{stem} {n}: apparatus not NFC")
            if not item.strip():
                remarks.append(f"{stem} {n}: an empty apparatus item")
    # wording against Perseus, over the sections the batch touches (and the one before its first mark)
    if words:
        sections = perseus_sections(sources / play.perseus)
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
            remarks.append(f"{where}: written {mine} | Perseus has {theirs}{tag}")
    return remarks


def residuals(slug: str, files: list[Path] | None = None) -> list[dict]:
    """The residual pass (pipeline/transcriptions/lucian/RESIDUALS.md): what the checked lines and
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
        items = [(k, plain(t)) for k, t in block["text"] if k != "¶" and not t.startswith("[title]")]
        res = page_residuals(play, page_layout(play, leaf), items, stream)
        noted = {m.group(1) for x in block["notes"] if (m := re.match(r"^(\d+\.\d+)", x))}
        for r in res:
            r["stem"] = stem
            r["noted"] = r["n"] in noted
        everything += res
        for old in od.glob(f"r-{leaf:04d}.*"):
            old.unlink()
        if not res:
            continue
        md = [f"# Residuals on {stem} (leaf {leaf}, Nilén's p. {page_of(play, leaf)})", "",
              f"Image: r-{leaf:04d}.png (each line once, labelled with its key); the whole page: ../pages/leaf_{leaf:04d}.png", ""]
        for k, r in enumerate(res, 1):
            what = {"word": f"the text has «{r['text']}», the OCR reads «{r['ocr']}»",
                    "accent": f"accents: the text has «{r['text']}», the OCR reads «{r['ocr']}»",
                    "punctuation": f"punctuation: the text has «{r['text']}», the OCR reads «{r['ocr']}»",
                    "bracket": f"brackets or asterisk: the text has «{r['text']}», the OCR reads «{r['ocr']}»",
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
        print(f"{slug}: {len(index)} pages, {n} lines, {f} flagged ({100 * f // max(n, 1)} %); "
              f"apparatus found on {sum(1 for p in index if p['apparatus'])}, short rule on {sum(1 for p in index if p['rule'])}")
    else:
        run(slug, step)


if __name__ == "__main__":
    main(sys.argv[1:])
