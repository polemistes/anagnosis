"""Burnet's Gorgias from the scan by OCR: his lines and apparatus, with only the doubtful places
left for a reader to check.

Burnet's Oxford text (Platonis Opera III, Oxford 1903) is the Perseus text (tlg0059.tlg023.perseus-grc2),
but Perseus has neither his lines nor his apparatus. The scan is the Internet Archive's
platonisopera03platuoft (a Milford reprint of the 1903 edition, Robarts Library, Toronto); the
Gorgias is on leaves 261-377.

Unlike the Symposium, whose pages were read and typed out whole, the Gorgias is read by Tesseract
(tessdata_best grc, pipeline/tessdata). The text itself is not typed at all: Tesseract's lines are
matched word by word to the Perseus text, which gives the line breaks, and Burnet's line numbers
follow from the Stephanus sections Perseus marks, checked against the numbers and letters printed
in the margin. Every place where the OCR and Perseus disagree, and every line whose number the
margin does not confirm, is flagged. The apparatus is read by Tesseract twice (Greek first, Latin
first) and must be checked against the image by a reader: Tesseract garbles its sigla and numbers.

Steps (each leaf's result is saved as soon as it is done, so a rerun continues where it stopped):

    python -m anagnosis_pipeline gorgias-pages fetch       the leaves, as grey PNG
    python -m anagnosis_pipeline gorgias-pages ocr         Tesseract, hOCR per leaf; apparatus crops read twice
    python -m anagnosis_pipeline gorgias-pages draft       the draft transcription, page images for checking,
                                                           and a check sheet per page

Files, under pipeline/sources/scans/platonisopera03platuoft/ (downloads) and pipeline/build/gorgias-pages/:

    jp2/<scan>_0263.jp2       the scan's original image of leaf 263
    pages/leaf_0263.png       the same, grey
    hocr/leaf_0263.hocr       Tesseract's reading of the page (grc, --psm 4)
    app/leaf_0263.png         the apparatus, enlarged twice
    app/leaf_0263.grc.txt     its OCR, Greek model first; .lat.txt, Latin model first
    g-0263-app.png            the apparatus for the reader (enlarged)
    g-0263-lines.png          the flagged lines of the page, each with its number, for the reader
    g-0263.md                 the check sheet: flags, OCR of the apparatus
    pages.json                the page index (stem, leaf, first and last line, lines)
    draft.json                the automatic text: lines with numbers, flags
"""
from __future__ import annotations

import difflib
import html
import json
import os
import re
import subprocess
import tarfile
import tempfile
import unicodedata
from collections import Counter
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from . import greek
from .linenum import SECTIONS

ROOT = Path(__file__).resolve().parent.parent.parent
PIPELINE = ROOT / "pipeline"
TESSDATA = PIPELINE / "tessdata"
SCAN = "platonisopera03platuoft"
FIRST, LAST = 261, 377  # the Gorgias's leaves in SCAN
PERSEUS = "data/tlg0059/tlg023/tlg0059.tlg023.perseus-grc2.xml"
TEI = "{http://www.tei-c.org/ns/1.0}"
SRC = PIPELINE / "sources" / "scans" / SCAN
BUILD = PIPELINE / "build" / "gorgias-pages"


def _dirs() -> None:
    for d in (SRC / "jp2", BUILD / "pages", BUILD / "hocr", BUILD / "app"):
        d.mkdir(parents=True, exist_ok=True)


# --- fetch and OCR -----------------------------------------------------------------------------

def fetch_leaf(leaf: int) -> Path:
    _dirs()
    png = BUILD / "pages" / f"leaf_{leaf:04d}.png"
    if png.exists():
        return png
    jp2 = SRC / "jp2" / f"{SCAN}_{leaf:04d}.jp2"
    if not jp2.exists():
        url = f"https://archive.org/download/{SCAN}/{SCAN}_jp2.zip/{SCAN}_jp2%2F{SCAN}_{leaf:04d}.jp2"
        tmp = jp2.with_suffix(".part")
        subprocess.run(["curl", "-sfL", "--retry", "3", "-o", str(tmp), url], check=True)
        tmp.rename(jp2)
    with tempfile.TemporaryDirectory() as t:
        subprocess.run(["opj_decompress", "-i", str(jp2), "-o", f"{t}/p.png"], check=True, capture_output=True)
        subprocess.run(["magick", f"{t}/p.png", "-colorspace", "Gray", str(png) + ".part.png"], check=True)
    os.replace(str(png) + ".part.png", png)
    return png


def tesseract(image: Path, out_base: Path, langs: str, psm: int, hocr: bool) -> None:
    env = dict(os.environ, OMP_THREAD_LIMIT="1")
    cmd = ["tesseract", str(image), str(out_base), "--tessdata-dir", str(TESSDATA), "-l", langs, "--psm", str(psm)]
    if hocr:
        cmd += ["-c", "tessedit_create_hocr=1"]
    subprocess.run(cmd, check=True, capture_output=True, env=env)


def ocr_leaf(leaf: int) -> Path:
    hocr = BUILD / "hocr" / f"leaf_{leaf:04d}.hocr"
    if hocr.exists():
        return hocr
    png = fetch_leaf(leaf)
    part = BUILD / "hocr" / f"leaf_{leaf:04d}.part"
    tesseract(png, part, "grc", 4, True)
    os.replace(str(part) + ".hocr", hocr)
    return hocr


_LINE = re.compile(r"<span class='ocr_(?:line|caption|header|textfloat)' id='(\w+)' title=\"bbox (\d+) (\d+) (\d+) (\d+)[^\"]*\">(.*?)</span>\s*(?=<span class='ocr_|</p>)", re.S)
_WORD = re.compile(r"<span class='ocrx_word' id='\w+' title='bbox (\d+) (\d+) (\d+) (\d+); x_wconf (\d+)'[^>]*>(.*?)</span>", re.S)


def read_hocr(path: Path) -> list[dict]:
    """The page's lines: {'bbox': [x0,y0,x1,y1], 'words': [{'text','bbox','conf'}]}, top to bottom."""
    t = path.read_text(encoding="utf-8")
    lines = []
    for m in _LINE.finditer(t):
        words = [{"text": unicodedata.normalize("NFC", html.unescape(re.sub(r"<[^>]+>", "", w.group(6)))),
                  "bbox": [int(w.group(i)) for i in range(1, 5)], "conf": int(w.group(5))}
                 for w in _WORD.finditer(m.group(6))]
        words = [w for w in words if w["text"].strip()]
        if words:
            lines.append({"bbox": [int(m.group(i)) for i in range(2, 6)], "words": words})
    lines.sort(key=lambda l: (l["bbox"][1], l["bbox"][0]))
    return lines


def run(step: str, workers: int = 4) -> None:
    leaves = range(FIRST, LAST + 1)
    if step == "fetch":
        with ThreadPoolExecutor(workers) as ex:
            list(ex.map(fetch_leaf, leaves))
    elif step == "ocr":
        with ThreadPoolExecutor(workers) as ex:
            list(ex.map(ocr_leaf, leaves))
    else:
        raise SystemExit(f"unknown step {step!r}")


# --- the Perseus text as a stream of words -----------------------------------------------------

# markers placed in the running text, removed again from the words they stick to
SEC, PARA, VERSE, GAP = "", "", "", ""


def perseus_tokens(sources: Path) -> list[dict]:
    """Burnet's words in the Perseus text, in order: {'t': the word as it is written (with its
    punctuation, brackets ⟨⟩ [] and quotation marks “ ”), 'skel': its letters without accents,
    'sec': its Stephanus section (447a), 'newsec': a section begins at it, 'para': a paragraph
    (a speech, or a paragraph within one) begins at it, 'label': it is a speaker's name ({ΚΑΛ.}),
    'verse': it begins a line of verse, 'inverse': it is in verse, 'gap': Perseus marks a gap
    after it}."""
    from lxml import etree

    with tarfile.open(sources / "corpora" / "canonical-greekLit.tar.gz") as tf:
        member = next(m for m in tf if m.name.endswith(PERSEUS))
        root = etree.fromstring(tf.extractfile(member).read())
    body = root.find(f".//{TEI}body")
    parts: list[str] = []
    in_verse = [0]

    def text(s: str | None) -> None:
        if s:
            parts.append(s.replace("\n", " ") if not in_verse[0] else s.replace("\n", " "))

    def walk(el) -> None:
        tag = etree.QName(el).localname
        if tag == "milestone":
            if el.get("unit") == "section":
                parts.append(f" {SEC}{el.get('n')}{SEC} ")
            elif el.get("unit") == "para":
                parts.append(f" {PARA} ")
            return
        if tag in ("note", "bibl", "head"):
            return
        if tag == "gap":
            parts.append(GAP)
            return
        if tag == "p":
            parts.append(f" {PARA} ")
        if tag == "label":
            parts.append(" {" + "".join(el.itertext()).strip() + "} ")
            return
        if tag == "l":
            parts.append(f" {VERSE}")
            in_verse[0] += 1
        open_, close = {"add": ("⟨", "⟩"), "del": ("[", "]"), "q": ("“", "”")}.get(tag, ("", ""))
        parts.append(open_)
        text(el.text)
        for child in el:
            walk(child)
            text(child.tail)
        parts.append(close)
        if tag == "l":
            in_verse[0] -= 1
            parts.append(f"{VERSE}e ")

    walk(body)
    s = greek.nfc("".join(parts))
    # a bracket or quotation mark opened or closed next to a space belongs to the word beside it
    s = re.sub(r"([⟨\[“])\s+", r"\1", s)
    s = re.sub(r"\s+([⟩\]”])", r"\1", s)
    out: list[dict] = []
    sec, newsec, para, verse, inverse = "", False, False, False, False
    pieces: list[tuple[str, bool]] = []  # (piece, glued to the piece before)
    for raw in s.split():
        parts_ = re.split(r"(?<=[^\s—])—(?=[^\s—])", raw)
        for k, piece in enumerate(parts_):
            pieces.append((piece + ("—" if k + 1 < len(parts_) else ""), k > 0))
    for raw, glued in pieces:
        if raw.startswith(SEC) and raw.endswith(SEC) and len(raw) > 2:
            sec, newsec = raw.strip(SEC), True
            continue
        if raw == PARA:
            para = True
            continue
        if VERSE + "e" in raw:
            raw = raw.replace(VERSE + "e", "")
            ends_verse = True
        else:
            ends_verse = False
        if raw.startswith(VERSE):
            raw = raw[1:]
            verse = inverse = True
        gap = GAP in raw
        raw = raw.replace(GAP, "")
        if raw:
            tok = {"t": raw, "skel": skel(raw), "sec": sec, "newsec": newsec, "para": para, "glued": glued,
                   "label": raw.startswith("{"), "verse": verse, "inverse": inverse, "gap": gap}
            if tok["skel"] or tok["label"]:
                out.append(tok)
                newsec = para = verse = False
            elif out:
                out[-1]["t"] += raw  # punctuation standing alone (a dash) goes with the word before
        elif gap and out:
            out[-1]["gap"] = True
        if ends_verse:
            inverse = False
    return out


def skel(s: str) -> str:
    """A word's letters, lower case, without accents, breathings or punctuation."""
    s = unicodedata.normalize("NFD", s.lower())
    s = "".join(c for c in s if unicodedata.category(c) in ("Ll", "Lu", "Lo"))
    return unicodedata.normalize("NFC", s).replace("ς", "σ")


# --- the page's lines ----------------------------------------------------------------------------

DASHES = re.compile(r"[—–]+|-{2,}|(?<=[.,;·:!?’”\"'])-+")


def _gr_letters(s: str) -> int:
    return sum(1 for c in s if "Ͱ" <= c <= "Ͽ" or "ἀ" <= c <= "῿")


def _is_junk(line: dict, typical_height: int = 50) -> bool:
    """A line of accents and breathings read on its own (Tesseract does this above many lines).
    A line of short words is kept here; page_layout drops it if it lies on a line of text."""
    toks = [skel(w["text"]) for w in line["words"]]
    height = line["bbox"][3] - line["bbox"][1]
    if not toks or max(len(t) for t in toks) == 0:
        return True
    if any(len(t) >= 4 for t in toks):
        return False
    return height < 0.5 * typical_height or len(toks) > 6


def apparatus_top(leaf: int) -> int | None:
    """Where the apparatus begins: below the first blank band of 45 pixels or more under the
    top third of the page (the text's lines are at most about 35 apart, the apparatus about 55
    below the text)."""
    from PIL import Image

    with Image.open(BUILD / "pages" / f"leaf_{leaf:04d}.png") as im:
        g = im.convert("L")
        w, h = g.size
        ink = g.crop((200, 0, w - 200, h)).point(lambda v: 255 if v < 140 else 0).resize((1, h), Image.BOX)
        rows = list(ink.tobytes())
    band = None
    for y, v in enumerate(rows):
        if v <= 1 and band is None:
            band = y
        elif v > 1 and band is not None:
            if y - band >= 45 and band > h // 3:
                return y
            band = None
    return None


def _edge(xs: list[int], side: str, tol: int = 10) -> int:
    """The column's edge: the leftmost (or rightmost) x near which at least a sixth of the lines
    begin (end)."""
    need = max(3, len(xs) // 6)
    cands = [x for x in xs if sum(1 for v in xs if abs(v - x) <= tol) >= need]
    if not cands:
        return min(xs) if side == "left" else max(xs)
    best = min(cands) if side == "left" else max(cands)
    near = [v for v in xs if abs(v - best) <= tol]
    return sorted(near)[len(near) // 2]


def _wordlike(w: dict) -> bool:
    return len(skel(w["text"])) >= 3


def _reread(leaf: int, y0: int, y1: int) -> list[list[dict]]:
    """The lines Tesseract finds in a strip of the page read on its own (cached)."""
    cache = BUILD / "hocr" / f"leaf_{leaf:04d}.strip-{y0}-{y1}.hocr"
    if not cache.exists():
        from PIL import Image

        with Image.open(BUILD / "pages" / f"leaf_{leaf:04d}.png") as im, tempfile.TemporaryDirectory() as t:
            im.crop((0, y0, im.size[0], y1)).save(Path(t) / "s.png")
            tesseract(Path(t) / "s.png", Path(t) / "s", "grc", 6, True)
            cache.write_text((Path(t) / "s.hocr").read_text(encoding="utf-8"), encoding="utf-8")
    out = []
    for l in read_hocr(cache):
        for w in l["words"]:
            w["bbox"] = [w["bbox"][0], w["bbox"][1] + y0, w["bbox"][2], w["bbox"][3] + y0]
        if l["bbox"][3] - l["bbox"][1] > 20:
            out.append(l["words"])
    return out


def page_layout(leaf: int) -> dict:
    """The page's text lines (printed lines, top to bottom, each with its words; words in the
    margin apart), the column's left and right edge, where the apparatus begins."""
    lines = read_hocr(BUILD / "hocr" / f"leaf_{leaf:04d}.hocr")
    app_y = apparatus_top(leaf)
    head = [l for l in lines if l["bbox"][1] < 160 and l["bbox"][3] < 200]
    body = [l for l in lines if l not in head and (app_y is None or (l["bbox"][1] + l["bbox"][3]) / 2 < app_y)]
    heights = sorted(l["bbox"][3] - l["bbox"][1] for l in body if any(len(skel(w["text"])) >= 4 for w in l["words"]))
    typical_h = heights[len(heights) // 2] if heights else 50
    real = [l for l in body if not _is_junk(l, typical_h)]
    # a box that holds two printed lines: its words split by their height on the page
    split: list[dict] = []
    for l in real:
        if l["bbox"][3] - l["bbox"][1] < 1.7 * typical_h:
            split.append(l)
            continue
        groups: list[list[dict]] = []
        for w in sorted(l["words"], key=lambda w: (w["bbox"][1] + w["bbox"][3]) / 2):
            yc = (w["bbox"][1] + w["bbox"][3]) / 2
            if groups and yc - sum((v["bbox"][1] + v["bbox"][3]) / 2 for v in groups[-1]) / len(groups[-1]) < 0.6 * typical_h:
                groups[-1].append(w)
            else:
                groups.append([w])
        for g in groups:
            split.append({"bbox": [min(w["bbox"][0] for w in g), min(w["bbox"][1] for w in g),
                                   max(w["bbox"][2] for w in g), max(w["bbox"][3] for w in g)], "words": g})
    real = [l for l in split if not _is_junk(l, typical_h)]
    # a line of two-letter words that overlaps a line of longer words is that line's accents
    solid = [l for l in real if max(len(skel(w["text"])) for w in l["words"]) >= 4]
    real = [l for l in real if l in solid or not any(
        min(l["bbox"][3], o["bbox"][3]) - max(l["bbox"][1], o["bbox"][1]) > 0.4 * (l["bbox"][3] - l["bbox"][1]) for o in solid)]
    # printed lines: OCR lines whose heights overlap by half are one printed line
    real.sort(key=lambda l: (l["bbox"][1] + l["bbox"][3]) / 2)
    printed: list[dict] = []
    for l in real:
        y0, y1 = l["bbox"][1], l["bbox"][3]
        if printed:
            p = printed[-1]
            ov = min(y1, p["y1"]) - max(y0, p["y0"])
            if ov > 0.5 * min(y1 - y0, p["y1"] - p["y0"]):
                p["words"] += l["words"]
                p["y0"], p["y1"] = min(p["y0"], y0), max(p["y1"], y1)
                continue
        printed.append({"y0": y0, "y1": y1, "words": list(l["words"])})
    for p in printed:
        # where two OCR lines read the same word, keep the surer reading
        ws = sorted(p["words"], key=lambda w: w["bbox"][0])
        keep: list[dict] = []
        for w in ws:
            if keep:
                k = keep[-1]
                ov = min(w["bbox"][2], k["bbox"][2]) - max(w["bbox"][0], k["bbox"][0])
                if ov > 0.5 * min(w["bbox"][2] - w["bbox"][0], k["bbox"][2] - k["bbox"][0]):
                    if w["conf"] > k["conf"]:
                        keep[-1] = w
                    continue
            keep.append(w)
        p["words"] = keep
    # a line Tesseract skipped: where two lines stand a line too far apart, the strip between
    # them is read again on its own
    if len(printed) > 3:
        tops = [p["y0"] for p in printed]
        pitch = sorted(b - a for a, b in zip(tops, tops[1:]))[len(tops) // 2]
        extra = []
        for a, b in zip(printed, printed[1:]):
            if b["y0"] - a["y0"] > 1.6 * pitch:
                y0, y1 = a["y0"] + int(0.75 * pitch), b["y0"] + int(0.1 * pitch)
                if y1 - y0 < 30:
                    continue
                for words in _reread(leaf, y0, y1):
                    if any(len(skel(w["text"])) >= 2 for w in words):
                        ys = [w["bbox"][1] for w in words] + [w["bbox"][3] for w in words]
                        extra.append({"y0": min(ys), "y1": max(ys), "words": words})
        printed = sorted(printed + extra, key=lambda p: p["y0"])
    # the column: where most lines begin, and where full lines end
    firsts = [min((w["bbox"][0] for w in p["words"] if _wordlike(w)), default=None) for p in printed]
    lasts = [max((w["bbox"][2] for w in p["words"] if _wordlike(w)), default=None) for p in printed]
    left = _edge([x for x in firsts if x is not None], "left") if printed else 0
    right = _edge([x for x in lasts if x is not None], "right") if printed else 0
    for p in printed:
        p["margin"] = [w for w in p["words"] if w["bbox"][2] < left - 12 or w["bbox"][0] > right + 20]
        p["words"] = [w for w in p["words"] if w not in p["margin"]]
        p["x0"] = min((w["bbox"][0] for w in p["words"]), default=left)
    printed = [p for p in printed if p["words"]]
    return {"leaf": leaf, "lines": printed, "app_y": app_y, "left": left, "right": right,
            "head_y": max((l["bbox"][3] for l in head), default=150), "line_h": typical_h}


def _mark(s: str) -> str:
    """A margin mark as Tesseract reads it, made one of: a number, or a letter b-e; '' if neither."""
    s = s.strip().replace(" ", "").lower()
    s = s.replace("o", "0").replace("i", "1").replace("l", "1").replace("s", "5")
    if re.fullmatch(r"[bcde]", s):
        return s
    if re.fullmatch(r"\d{1,3}", s):
        return s
    return ""


def margin_marks(leaf: int, layout: dict) -> list[tuple[int, str]]:
    """The numbers and letters in the margins beside the text: [(y centre, '5' / '10' / 'b' / '451')].
    Each mark is cut out of a strip beside the column by its ink, enlarged, and read on its own by
    Tesseract's English model limited to digits and the letters a-e (cached in
    hocr/leaf_NNNN.margin.json)."""
    cache = BUILD / "hocr" / f"leaf_{leaf:04d}.margin.json"
    if cache.exists():
        return [tuple(x) for x in json.loads(cache.read_text())]
    from PIL import Image, ImageOps

    top = layout["head_y"] + 10
    bottom = (layout["app_y"] or 2600) - 10
    marks: list[tuple[int, str]] = []
    env = dict(os.environ, OMP_THREAD_LIMIT="1")
    with Image.open(BUILD / "pages" / f"leaf_{leaf:04d}.png") as im:
        g = im.convert("L")
        w = g.size[0]
        strips = [(0, max(0, layout["left"] - 8)), (min(w, layout["right"] + 15), w)]
        with tempfile.TemporaryDirectory() as t:
            for x0, x1 in strips:
                if x1 - x0 < 20:
                    continue
                strip = g.crop((x0 + 10 if x0 == 0 else x0, top, x1 - 10 if x1 == w else x1, bottom))
                ink = strip.point(lambda v: 255 if v < 140 else 0)
                rows = list(ink.resize((1, ink.size[1]), Image.BOX).tobytes())
                y, n = 0, len(rows)
                while y < n:
                    if rows[y] == 0:
                        y += 1
                        continue
                    y1 = y
                    while y1 < n and rows[y1 - 1 if y1 > y else y1] > 0 and y1 - y < 60:
                        y1 += 1
                    # join pieces separated by a gap of a few pixels (the dot of an i, 1 and 0)
                    while y1 + 4 < n and any(rows[y1 + k] > 0 for k in range(1, 5)) and y1 - y < 60:
                        y1 += 1
                        while y1 < n and rows[y1] > 0 and y1 - y < 60:
                            y1 += 1
                    if y1 - y >= 8:
                        piece = strip.crop((0, max(0, y - 4), strip.size[0], min(n, y1 + 4)))
                        bbox = ImageOps.invert(piece).point(lambda v: 255 if v > 115 else 0).getbbox()
                        if bbox:
                            piece = piece.crop((max(0, bbox[0] - 6), 0, min(piece.size[0], bbox[2] + 6), piece.size[1]))
                            piece = ImageOps.expand(piece.resize((piece.size[0] * 2, piece.size[1] * 2)), 30, fill=255)
                            path = Path(t) / "piece.png"
                            piece.save(path)
                            out = ""
                            for psm in ("7", "10"):
                                out = subprocess.run(["tesseract", str(path), "stdout", "--tessdata-dir", str(TESSDATA), "-l", "eng",
                                                      "--psm", psm], capture_output=True, text=True, env=env).stdout.strip()
                                out = _mark(out)
                                if out:
                                    break
                            marks.append((top + (y + y1) // 2, out))
                    y = y1 + 1
    cache.write_text(json.dumps(marks))
    return marks


# --- matching the OCR to Perseus -----------------------------------------------------------------

def ocr_stream(layouts: list[dict]) -> tuple[list[dict], list[dict]]:
    """All the printed lines of the text, in order, and the OCR's words: {'t', 'skel', 'line', 'conf'}.
    A word divided at the end of a line is joined and belongs to the line where it begins."""
    lines: list[dict] = []
    toks: list[dict] = []
    for lay in layouts:
        for p in lay["lines"]:
            li = len(lines)
            lines.append({"leaf": lay["leaf"], "y0": p["y0"], "y1": p["y1"], "x0": p["x0"],
                          "indent": p["x0"] - lay["left"], "line_h": lay["line_h"],
                          "ocr": " ".join(w["text"] for w in p["words"]), "margin": p["margin"]})
            for w in p["words"]:
                for piece in DASHES.split(ocr_norm(w["text"])):
                    if piece.strip():
                        toks.append({"t": piece, "skel": skel(piece), "line": li, "conf": w["conf"]})
    # the last word of each line, if it ends in a hyphen, is joined with the first of the next;
    # the whole word stands on the line where it begins, unless that would leave the next line
    # without a word of its own (then it stands there)
    count = Counter(t["line"] for t in toks if t["skel"])
    for k, t in enumerate(toks):
        last = k + 1 == len(toks) or toks[k + 1]["line"] != t["line"]
        t["hyph"] = last and t["t"].rstrip().endswith(("-", "‐", "¬")) and len(t["skel"]) > 0
    joined: list[dict] = []
    for t in toks:
        if joined and joined[-1].get("hyph") and t["line"] == joined[-1]["line"] + 1 and t["skel"]:
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


_SPACING = {"᾿": "\u0313", "῾": "\u0314", "῎": "\u0313\u0301", "῍": "\u0313\u0300", "῞": "\u0314\u0301",
            "῝": "\u0314\u0300", "῏": "\u0313\u0342", "῟": "\u0314\u0342"}


def ocr_norm(s: str) -> str:
    """The OCR's word as Burnet prints it: a breathing (and accent) written before a capital is put
    on it (᾿Α to Ἀ); elision written ʼ."""
    s = unicodedata.normalize("NFC", s)
    s = re.sub("([᾿῾῎῍῞῝῏῟])([ΑΕΗΙΟΥΩ])", lambda m: unicodedata.normalize("NFC", m.group(2) + _SPACING[m.group(1)]), s)
    return re.sub(r"(?<=[^\W\d_])[᾽’'](?=\s|$|[,.;·:])", "ʼ", s)


def _sim(a: str, b: str) -> float:
    if a == b:
        return 1.0
    return difflib.SequenceMatcher(None, a, b, autojunk=False).ratio()


def _pair_gap(O: list[dict], P: list[dict]) -> list[tuple[int, int, float]]:
    """Pairs (i in O, j in P, similarity) of the words in a gap between two exact matches, by the
    best alignment of similar words (a word read wrongly, or divided and not joined)."""
    n, m = len(O), len(P)
    if n == 0 or m == 0:
        return []
    if n * m > 4000:  # a long stretch the OCR has lost: pair nothing
        return []
    score = [[0.0] * (m + 1) for _ in range(n + 1)]
    back = [[0] * (m + 1) for _ in range(n + 1)]
    sims = [[_sim(O[i]["skel"], P[j]["skel"]) for j in range(m)] for i in range(n)]
    for i in range(1, n + 1):
        for j in range(1, m + 1):
            best, how = score[i - 1][j], 1
            if score[i][j - 1] > best:
                best, how = score[i][j - 1], 2
            s = sims[i - 1][j - 1]
            if s >= 0.45 and score[i - 1][j - 1] + s - 0.3 > best:
                best, how = score[i - 1][j - 1] + s - 0.3, 3
            score[i][j], back[i][j] = best, how
    pairs = []
    i, j = n, m
    while i > 0 and j > 0:
        how = back[i][j]
        if how == 3:
            pairs.append((i - 1, j - 1, sims[i - 1][j - 1]))
            i, j = i - 1, j - 1
        elif how == 1:
            i -= 1
        else:
            j -= 1
    return pairs[::-1]


def align(ocr: list[dict], pers: list[dict]) -> list[int | None]:
    """For each Perseus word, the OCR word it was read as (index), or None."""
    sm = difflib.SequenceMatcher(None, [t["skel"] for t in ocr], [t["skel"] for t in pers], autojunk=False)
    match: list[int | None] = [None] * len(pers)
    sim: list[float] = [0.0] * len(pers)
    prev_o, prev_p = -1, -1
    for a, b, size in sm.get_matching_blocks():
        for i, j, s in _pair_gap(ocr[prev_o + 1 : a], pers[prev_p + 1 : b]):
            match[prev_p + 1 + j] = prev_o + 1 + i
            sim[prev_p + 1 + j] = s
        for k in range(size):
            match[b + k] = a + k
            sim[b + k] = 1.0
        prev_o, prev_p = a + size - 1, b + size - 1
    for j, t in enumerate(pers):
        t["sim"] = sim[j]
    return match


def assign_lines(lines: list[dict], ocr: list[dict], pers: list[dict], match: list[int | None]) -> None:
    """Give each Perseus word the printed line it stands on (t['line']), and mark the words whose
    line is a guess (t['guess'])."""
    n = len(pers)
    line: list[int | None] = [ocr[o]["line"] if o is not None else None for o in match]
    # a speaker's name the OCR does not show is one Perseus adds: left out. The OCR garbles the
    # names in quick exchanges ("ΔΛ." for ΠΩΛ.): a capitalised scrap where the name should be
    # means it is printed
    def capitals(tok: str) -> bool:
        letters = [c for c in tok if c.isalpha()]
        return len(letters) >= 1 and sum(c.isupper() for c in letters) >= max(1, len(letters) - 1) and len(letters) <= 5

    for j, t in enumerate(pers):
        if t["label"] and match[j] is None:
            o0 = next((match[k] for k in range(j - 1, -1, -1) if match[k] is not None), -1)
            o1 = next((match[k] for k in range(j + 1, n) if match[k] is not None), len(ocr))
            scraps = [ocr[o] for o in range(o0 + 1, o1) if capitals(ocr[o]["t"])]
            if scraps:
                t["label_guess"] = scraps[0]["t"]
                line_hint = scraps[0]["line"]
                t["line_hint"] = line_hint
            else:
                t["drop"] = True
    for j, t in enumerate(pers):
        if t.get("line_hint") is not None:
            line[j] = t["line_hint"]
    # unpaired words between paired ones: on the line of their neighbours if both agree; else
    # spread over the lines of the unpaired OCR words between them, in order
    j = 0
    while j < n:
        if line[j] is not None:
            j += 1
            continue
        k = j
        while k < n and line[k] is None:
            k += 1
        before = line[j - 1] if j > 0 else (line[k] if k < n else 0)
        after = line[k] if k < n else before
        if before == after:
            for x in range(j, k):
                line[x] = before
        elif all(pers[x]["newsec"] or pers[x]["para"] or pers[x].get("drop") for x in range(j, k)):
            for x in range(j, k):
                line[x] = after  # what begins a section or a speech goes with what follows
        else:
            o0 = match[j - 1] if j > 0 and match[j - 1] is not None else -1
            o1 = match[k] if k < n and match[k] is not None else len(ocr)
            loose = [ocr[o]["line"] for o in range(o0 + 1, o1)]
            for x in range(j, k):
                if loose:
                    idx = min(len(loose) - 1, (x - j) * len(loose) // (k - j))
                    line[x] = min(max(loose[idx], before), after)
                else:
                    line[x] = before
                pers[x]["guess"] = True
        j = k
    for j, o in enumerate(match):
        if o is not None and ocr[o].get("joined"):
            pers[j]["joined"] = True
    # lines never go back
    last = 0
    for j in range(n):
        if line[j] < last:
            pers[j]["guess"] = True
            line[j] = last
        last = line[j]
        pers[j]["line"] = line[j]


def number_lines(lines: list[dict], pers: list[dict]) -> list[dict]:
    """Burnet's lines with their numbers: {'n', 'words' (Perseus indexes), 'line' (printed line),
    'flags'}. A line where a Stephanus section begins is line 1 of that section."""
    by_line: dict[int, list[int]] = {}
    for j, t in enumerate(pers):
        by_line.setdefault(t["line"], []).append(j)
    # a section that Perseus begins at a word divided over two lines begins, in Burnet, on the
    # line that holds the word's second part
    carry: dict[int, int] = {}
    for li, words in by_line.items():
        last = words[-1]
        if pers[last]["newsec"] and pers[last].get("joined") and li + 1 in by_line:
            carry[li + 1] = last
    out: list[dict] = []
    sec, count = None, 0
    for li, pl in enumerate(lines):
        words = by_line.get(li)
        if not words:
            if len(skel(pl["ocr"])) >= 8:
                pl["dropped"] = True
            continue
        flags: list[str] = []
        starts = [j for j in words if pers[j]["newsec"] and not (j == words[-1] and li + 1 in carry and carry[li + 1] == j)]
        if li in carry:
            starts = [carry[li]] + starts
        if starts:
            new = pers[starts[-1]]["sec"]
            if len(starts) > 1:
                flags.append(f"two sections begin on this line ({', '.join(pers[j]['sec'] for j in starts)})")
            if starts[-1] != words[0] and starts[-1] not in carry.values():
                flags.append(f"section {new} begins inside the line (Perseus marks it at {pers[starts[-1]]['t']})")
            sec, count = new, 1
        else:
            count += 1
        page, letter = int(sec[:-1]), sec[-1]
        out.append({"n": f"{page}{letter}{count}", "sec": sec, "count": count, "words": words, "line": li, "flags": flags})
    return out


def check_margins(numbered: list[dict], lines: list[dict], layouts: dict[int, dict]) -> None:
    """Compare the line numbers with the numbers and letters printed in the margin."""
    by_leaf: dict[int, list[dict]] = {}
    for L in numbered:
        by_leaf.setdefault(lines[L["line"]]["leaf"], []).append(L)
    for leaf, Ls in by_leaf.items():
        lay = layouts[leaf]
        marks = margin_marks(leaf, lay)
        pitch = lay["line_h"] * 1.3
        seen: set[int] = set()
        for y, mark in marks:
            near = min(Ls, key=lambda L: abs((lines[L["line"]]["y0"] + lines[L["line"]]["y1"]) / 2 - y))
            dy = abs((lines[near["line"]]["y0"] + lines[near["line"]]["y1"]) / 2 - y)
            if dy > pitch * 0.6:
                continue
            seen.add(id(near))
            c, sec = near["count"], near["sec"]
            if mark.isdigit() and len(mark) == 3:
                ok = c == 1 and sec[-1] == "a" and sum(x == y for x, y in zip(mark, sec[:3])) >= 2
            elif mark in ("5", "10") and not (c == 1 and sec[-1] == "e"):
                ok = str(c) == mark
            elif c % 5 == 0 and mark in ("0", "01", "1", "3", "8", "9", "d", "4"):
                ok = True  # 5 or 10, misread
            elif c == 1 and sec[-1] == "e" and mark in ("5", "6", "0"):
                ok = True  # e, misread
            elif mark in "bcde" and mark:
                ok = c == 1 and (sec.endswith(mark) or {mark, sec[-1]} == {"c", "e"})
            else:
                continue  # a speck, a hyphen or quotation mark beyond the line's end, or a mark not read
            if not ok:
                near["flags"].append(f"the margin reads “{mark or '?'}” here, but the line is numbered {near['n']}")
        for L in Ls:
            expected = L["count"] == 1 or L["count"] % 5 == 0
            if expected and id(L) not in seen:
                L["flags"].append(f"no number or letter found in the margin, though {L['n']} should have one")


# --- the draft -----------------------------------------------------------------------------------

def _capitalise(word: str) -> str:
    m = re.match(r"^([“‘\[⟨(]*)(.)(.*)$", word, re.S)
    if not m:
        return word
    first = m.group(2)
    up = unicodedata.normalize("NFC", unicodedata.normalize("NFD", first)[0].upper() + unicodedata.normalize("NFD", first)[1:])
    return m.group(1) + up + m.group(3)


def _starts_upper(word: str) -> bool:
    letters = [c for c in word if c.isalpha()]
    return bool(letters) and letters[0].isupper()


def line_texts(numbered: list[dict], lines: list[dict], ocr: list[dict], pers: list[dict], match: list[int | None]) -> None:
    """Write each line's text (L['text']), mark paragraphs (L['para']) and verse, and add the flags
    that come from comparing the words with the OCR."""
    paired_o = {o for o in match if o is not None}
    by_line_o: dict[int, list[int]] = {}
    for k, t in enumerate(ocr):
        by_line_o.setdefault(t["line"], []).append(k)
    capital_next = False
    for L in numbered:
        pl = lines[L["line"]]
        indented = pl["indent"] > 0.5 * pl["line_h"]
        words = [j for j in L["words"] if not pers[j].get("drop")]
        out: list[str] = []
        flags = L["flags"]
        first = True
        for j in words:
            t = pers[j]
            w = t["t"]
            o = match[j]
            if t["label"]:
                if not first:
                    # a speech run on in the line: “Ναί.—ΣΩ. Δεύτερον”
                    out[-1] = out[-1].rstrip("—") + "—" + w
                else:
                    out.append(w)
                    if not indented:
                        L["runon"] = True  # the dash ends the line before
                capital_next = True
                if t.get("label_guess"):
                    flags.append(f"{t['t']}: the OCR reads “{t['label_guess']}” here; check the name is printed")
                first = False
                continue
            if o is not None and _starts_upper(ocr[o]["t"]) and not _starts_upper(w) and t["sim"] >= 0.8:
                w = _capitalise(w)
            elif capital_next and not _starts_upper(w):
                w = _capitalise(w)
            capital_next = False
            if t.get("glued") and out:
                out[-1] += w
            else:
                out.append(w)
            first = False
            # the word against the OCR
            if o is None:
                flags.append(f"{w}: not found in the OCR; check it is printed on this line")
            elif t["sim"] < 1.0 and ocr[o]["conf"] >= 80:
                flags.append(f"{w}: the OCR reads “{ocr[o]['t']}”")
            elif t["sim"] == 1.0 and len(t["skel"]) >= 4 and ocr[o]["conf"] >= 95:
                a = re.sub(r"[^\w]", "", unicodedata.normalize("NFC", w.lower()))
                b = re.sub(r"[^\w]", "", unicodedata.normalize("NFC", ocr[o]["t"].lower()))
                if a != b:
                    flags.append(f"{w}: the OCR reads “{ocr[o]['t']}” (accents)")
            if t.get("guess"):
                flags.append(f"{w}: which line it stands on is a guess")
            if t.get("gap"):
                flags.append(f"{w}: Perseus marks a gap (lost text) after this word; copy what Burnet prints")
        for j in L["words"]:
            if pers[j].get("drop"):
                flags.append(f"{pers[j]['t']}: Perseus has this speaker's name here, the OCR shows none: left out; add it if printed")
        # OCR words that no Perseus word was matched to
        for k in by_line_o.get(L["line"], []):
            if k not in paired_o and len(ocr[k]["skel"]) >= 4 and ocr[k]["conf"] >= 85:
                flags.append(f"the OCR reads “{ocr[k]['t']}” on this line, which Perseus does not have here")
        verse = bool(words) and pers[words[0]]["inverse"] and not pers[words[0]]["label"]
        text = " ".join(out)
        if verse:
            text = "| " + text
            if any(not pers[j]["inverse"] for j in words):
                flags.append("verse and prose on one line")
        L["text"] = text
        L["para"] = indented and bool(words) and (pers[words[0]]["label"] or pers[words[0]]["para"]) and not verse
        if indented and not L["para"] and not verse:
            flags.append("the line is indented, but Perseus begins no speech or paragraph here")
        L["leaf"] = pl["leaf"]
    for k, L in enumerate(numbered):
        if L.get("runon") and k > 0 and not numbered[k - 1]["text"].endswith("—"):
            numbered[k - 1]["text"] += "—"
    # a printed line the OCR read but that matched no Perseus word
    for k, L in enumerate(numbered):
        nxt = numbered[k + 1]["line"] if k + 1 < len(numbered) else len(lines)
        for li in range(L["line"] + 1, nxt):
            if lines[li].get("dropped"):
                L["flags"].append(f"the next printed line, read as “{lines[li]['ocr'][:60]}”, matched no Perseus words")


def build_draft(sources: Path) -> list[dict]:
    layouts = {leaf: page_layout(leaf) for leaf in range(FIRST, LAST + 1)}
    lines, ocr = ocr_stream([layouts[l] for l in range(FIRST, LAST + 1)])
    pers = perseus_tokens(sources)
    match = align(ocr, pers)
    assign_lines(lines, ocr, pers, match)
    numbered = number_lines(lines, pers)
    check_margins(numbered, lines, layouts)
    line_texts(numbered, lines, ocr, pers, match)
    for L in numbered:
        L["y0"], L["y1"] = lines[L["line"]]["y0"], lines[L["line"]]["y1"]
        L["ocr"] = lines[L["line"]]["ocr"]
        L["flags"] = list(dict.fromkeys(L["flags"]))
    return numbered, layouts


def apparatus_images(leaf: int, layout: dict, stem: str) -> dict:
    """The apparatus cut out of the page: for the reader the whole width (g-NNNN-app.png) and its
    left and right halves enlarged (-app-l.png, -app-r.png); for Tesseract the whole enlarged
    twice, read with the Greek model first and with the Latin model first."""
    from PIL import Image

    out = {}
    if layout["app_y"] is None:
        return out
    y0 = layout["app_y"] - 12
    with Image.open(BUILD / "pages" / f"leaf_{leaf:04d}.png") as im:
        g = im.convert("L")
        w, h = g.size
        # the apparatus ends above the signature or the page's foot: the last ink in the lower part
        ink = g.crop((0, y0, w, h)).point(lambda v: 255 if v < 140 else 0).resize((1, h - y0), Image.BOX)
        rows = list(ink.tobytes())
        last = max((k for k, v in enumerate(rows) if v > 0), default=len(rows) - 1)
        y1 = min(h, y0 + last + 14)
        crop = g.crop((40, y0, w - 40, y1))
        crop.save(BUILD / f"{stem}-app.png")
        cw = crop.size[0]
        half = cw // 2
        for side, box in (("l", (0, 0, half + 90, crop.size[1])), ("r", (half - 90, 0, cw, crop.size[1]))):
            part = crop.crop(box)
            part.resize((int(part.size[0] * 1.6), int(part.size[1] * 1.6)), Image.LANCZOS).save(BUILD / f"{stem}-app-{side}.png")
        big = BUILD / "app" / f"leaf_{leaf:04d}.png"
        if not big.exists():
            crop.resize((cw * 2, crop.size[1] * 2), Image.LANCZOS).save(big)
    for langs, ext in (("grc+lat", "grc"), ("lat+grc", "lat")):
        txt = BUILD / "app" / f"leaf_{leaf:04d}.{ext}.txt"
        if not txt.exists():
            with tempfile.TemporaryDirectory() as t:
                tesseract(big, Path(t) / "a", langs, 6, False)
                txt.write_text((Path(t) / "a.txt").read_text(encoding="utf-8"), encoding="utf-8")
        out[ext] = txt.read_text(encoding="utf-8").strip()
    return out


def lines_image(leaf: int, Ls: list[dict], stem: str) -> bool:
    """The flagged lines of a page, one under the other, each with its number (g-NNNN-lines.png)."""
    from PIL import Image, ImageDraw, ImageFont

    if not Ls:
        return False
    with Image.open(BUILD / "pages" / f"leaf_{leaf:04d}.png") as im:
        g = im.convert("L")
        w = g.size[0]
        crops = [(L["n"], g.crop((60, max(0, L["y0"] - 14), w - 40, L["y1"] + 12))) for L in Ls]
    label_w = 190
    height = sum(c.size[1] + 10 for _n, c in crops)
    sheet = Image.new("L", (label_w + max(c.size[0] for _n, c in crops), height), 255)
    draw = ImageDraw.Draw(sheet)
    try:
        font = ImageFont.truetype("DejaVuSans-Bold.ttf", 34)
    except OSError:
        font = ImageFont.load_default()
    y = 0
    for n, c in crops:
        sheet.paste(c, (label_w, y))
        draw.text((8, y + c.size[1] // 2 - 18), n, fill=0, font=font)
        draw.line((0, y + c.size[1] + 4, sheet.size[0], y + c.size[1] + 4), fill=160, width=2)
        y += c.size[1] + 10
    sheet.save(BUILD / f"{stem}-lines.png")
    return True


PAGES_PER_BATCH = 6


def write_draft(sources: Path, transcriptions: Path) -> list[dict]:
    """The draft batch files (never overwriting one that exists), the check sheets and images,
    pages.json and draft.json."""
    numbered, layouts = build_draft(sources)
    by_leaf: dict[int, list[dict]] = {}
    for L in numbered:
        by_leaf.setdefault(L["leaf"], []).append(L)
    index = []
    for leaf in range(FIRST, LAST + 1):
        Ls = by_leaf.get(leaf, [])
        stem = f"g-{leaf:04d}"
        app = apparatus_images(leaf, layouts[leaf], stem)
        flagged = [L for L in Ls if L["flags"]]
        has_lines = lines_image(leaf, flagged, stem)
        md = [f"# Page {stem} (leaf {leaf}): lines {Ls[0]['n']}–{Ls[-1]['n']}" if Ls else f"# Page {stem} (leaf {leaf})", ""]
        md.append(f"Images: pages/leaf_{leaf:04d}.png (the whole page); {stem}-app.png (the apparatus), "
                  f"{stem}-app-l.png and {stem}-app-r.png (its left and right half, enlarged)"
                  + (f"; {stem}-lines.png (the flagged lines, each with its number)" if has_lines else ""))
        md.append("")
        md.append("## Flags on the text")
        md.append("")
        if flagged:
            for L in flagged:
                md.append(f"* {L['n']}  `{L['text']}`")
                for f in L["flags"]:
                    md.append(f"    * {f}")
        else:
            md.append("None: the OCR agrees with Perseus on every line, and the margin with the numbers.")
        md.append("")
        md.append("## The lines of the page (the draft) beside Tesseract's reading of them")
        md.append("")
        for L in Ls:
            md.append(f"{L['n']}\t{L['text']}\n\t\tOCR: {L['ocr']}")
        md.append("")
        md.append("## Tesseract's readings of the apparatus (Greek model first; Latin model first). Both garble sigla and numbers")
        md.append("")
        md.append("```")
        md.append(app.get("grc", "(no apparatus found)"))
        md.append("```")
        md.append("")
        md.append("```")
        md.append(app.get("lat", ""))
        md.append("```")
        (BUILD / f"{stem}.md").write_text("\n".join(md) + "\n", encoding="utf-8")
        index.append({"stem": stem, "leaf": leaf, "first": Ls[0]["n"] if Ls else None, "last": Ls[-1]["n"] if Ls else None,
                      "lines": len(Ls), "flagged": len(flagged)})
    (BUILD / "pages.json").write_text(json.dumps(index, ensure_ascii=False, indent=1), encoding="utf-8")
    (BUILD / "draft.json").write_text(json.dumps(
        [{k: L[k] for k in ("n", "leaf", "text", "para", "flags", "y0", "y1", "ocr")} for L in numbered],
        ensure_ascii=False, indent=0), encoding="utf-8")
    # the batch files
    transcriptions.mkdir(parents=True, exist_ok=True)
    leaves = [p["leaf"] for p in index]
    for b in range(0, len(leaves), PAGES_PER_BATCH):
        path = transcriptions / f"batch-{b // PAGES_PER_BATCH + 1:02d}.md"
        if path.exists():
            continue
        out = []
        for leaf in leaves[b : b + PAGES_PER_BATCH]:
            out.append(f"=== g-{leaf:04d}")
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
