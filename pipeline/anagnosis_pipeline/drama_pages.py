"""The plays' Greek text and critical apparatus from the scans by OCR, with only the doubtful
places left for a reader to check (pipeline/PLAN-drama.md, steps 3-4).

The Gorgias route (gorgias_pages.py) for verse, parameterised by play (drama.PLAYS): each text
page is read by Tesseract (tessdata_best grc); its lines are matched word by word to the Perseus
text of the play (another edition, the check text); every printed verse is numbered by the
Perseus line its first word stands in (drama.number_verses), checked against the numbers printed
in the margin; speakers are placed where Perseus changes speaker, checked against the print's
abbreviations (ΚΛ., ΧΟ.). Every place where the OCR and Perseus disagree is flagged. The
apparatus at the foot of the page is cut out, enlarged and read twice by Tesseract (Greek first,
Latin or English first) as a help for the reader, who writes it from the image.

    python -m anagnosis_pipeline drama-pages <play> fetch    the text leaves, as grey PNG
    python -m anagnosis_pipeline drama-pages <play> ocr      Tesseract, hOCR per leaf
    python -m anagnosis_pipeline drama-pages <play> draft    the draft, page crops, check sheets, batch files

Files (each saved as soon as it is made, so that a rerun goes on where it stopped):

    pipeline/sources/scans/<scan>/jp2/<scan>_0042.jp2     the scan's image of leaf 42
    pipeline/build/drama-scans/<scan>/pages/leaf_0042.png the same, grey (shared by the text and prose routes)
    pipeline/build/drama-scans/<scan>/hocr/leaf_0042.grc.hocr   Tesseract's reading (grc, --psm 4)
    pipeline/build/drama-pages/<play>/pages               a link to the scan's pages
    pipeline/build/drama-pages/<play>/app/leaf_0042.*.txt the apparatus read twice
    pipeline/build/drama-pages/<play>/p-0042-lines.png    the flagged lines, each labelled with its number
    pipeline/build/drama-pages/<play>/p-0042-app-l.png, -app-r.png   the apparatus, halves enlarged
    pipeline/build/drama-pages/<play>/p-0042.md           the check sheet
    pipeline/build/drama-pages/<play>/pages.json, draft.json
    pipeline/transcriptions/drama/<play>/batch-NN.md      six pages each, never overwritten
"""
from __future__ import annotations

import difflib
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
from .drama import APOS, PLAYS, Play, base, number_verses, load_perseus, perseus_play, skel
from .gorgias_pages import _pair_gap, _sim, read_hocr, tesseract  # noqa: F401  (_pair_gap, _sim used via align)
from .gorgias_pages import align as align_words
from .gorgias_pages import assign_lines

ROOT = Path(__file__).resolve().parent.parent.parent
PIPELINE = ROOT / "pipeline"
TESSDATA = PIPELINE / "tessdata"
PAGES_PER_BATCH = 6


def scan_dirs(scan: str) -> tuple[Path, Path]:
    src = PIPELINE / "sources" / "scans" / scan
    build = PIPELINE / "build" / "drama-scans" / scan
    for d in (src / "jp2", build / "pages", build / "hocr"):
        d.mkdir(parents=True, exist_ok=True)
    return src, build


def route_dir(route: str, slug: str, scan: str) -> Path:
    """pipeline/build/<route>/<slug>/, with `pages` linked to the scan's page images."""
    d = PIPELINE / "build" / route / slug
    d.mkdir(parents=True, exist_ok=True)
    link = d / "pages"
    target = Path("..") / ".." / "drama-scans" / scan / "pages"
    if not link.exists() and not link.is_symlink():
        link.symlink_to(target)
    return d


# --- fetch and OCR -----------------------------------------------------------------------------

def fetch_leaf(scan: str, leaf: int) -> Path:
    """Leaf `leaf` of the scan as a grey PNG: from the jp2 zip, or, for a scan that has none, the
    Archive's page image (/page/n<N>_w<width>.jpg, N counted over the shown leaves, the largest
    width the server gives)."""
    src, build = scan_dirs(scan)
    png = build / "pages" / f"leaf_{leaf:04d}.png"
    if png.exists():
        return png
    jp2 = src / "jp2" / f"{scan}_{leaf:04d}.jp2"
    if not jp2.exists():
        url = f"https://archive.org/download/{scan}/{scan}_jp2.zip/{scan}_jp2%2F{scan}_{leaf:04d}.jp2"
        tmp = jp2.with_suffix(".part")
        r = subprocess.run(["curl", "-sfL", "--retry", "3", "-o", str(tmp), url])
        if r.returncode == 0 and tmp.exists() and tmp.stat().st_size > 1000:
            tmp.rename(jp2)
        else:
            tmp.unlink(missing_ok=True)
            jpg = src / "jp2" / f"{scan}_{leaf:04d}.jpg"
            from .drama import _scandata

            # the page images are numbered over the shown leaves only (n0 = the first shown leaf)
            shown = [l for l, ok in _scandata(scan) if ok]
            if leaf not in shown:
                raise SystemExit(f"{scan}: leaf {leaf} is hidden in the scan and has no page image")
            n = shown.index(leaf)
            for width in (3000, 2500, 2000, 1500):
                url = f"https://archive.org/download/{scan}/page/n{n}_w{width}.jpg"
                r = subprocess.run(["curl", "-sfL", "--retry", "3", "-o", str(tmp), url])
                if r.returncode == 0 and tmp.exists() and tmp.stat().st_size > 1000:
                    tmp.rename(jpg)
                    break
            else:
                raise SystemExit(f"{scan}: leaf {leaf} neither in the jp2 zip nor as a page image")
            subprocess.run(["magick", str(jpg), "-colorspace", "Gray", str(png) + ".part.png"], check=True)
            os.replace(str(png) + ".part.png", png)
            return png
    with tempfile.TemporaryDirectory() as t:
        subprocess.run(["opj_decompress", "-i", str(jp2), "-o", f"{t}/p.png"], check=True, capture_output=True)
        subprocess.run(["magick", f"{t}/p.png", "-colorspace", "Gray", str(png) + ".part.png"], check=True)
    os.replace(str(png) + ".part.png", png)
    return png


def ocr_leaf(scan: str, leaf: int) -> Path:
    _, build = scan_dirs(scan)
    hocr = build / "hocr" / f"leaf_{leaf:04d}.grc.hocr"
    if hocr.exists():
        return hocr
    png = fetch_leaf(scan, leaf)
    part = build / "hocr" / f"leaf_{leaf:04d}.grc.part"
    tesseract(png, part, "grc", 4, True)
    os.replace(str(part) + ".hocr", hocr)
    return hocr


def run(slug: str, step: str, workers: int = 4) -> None:
    play = PLAYS[slug]
    leaves = play.visible("text")
    if not leaves:
        raise SystemExit(f"{slug}: no text leaves in drama.PLAYS yet (step 2)")
    route_dir("drama-pages", slug, play.scan)
    if play.layout == "jebb":
        leaves = sorted(set(leaves) | {play.facing(l) for l in leaves})
    if step == "fetch":
        with ThreadPoolExecutor(workers) as ex:
            list(ex.map(lambda l: fetch_leaf(play.scan, l), leaves))
    elif step == "ocr":
        with ThreadPoolExecutor(workers) as ex:
            list(ex.map(lambda l: ocr_leaf(play.scan, l), leaves))
    else:
        raise SystemExit(f"unknown step {step!r}")
    print(f"{slug}: {step} done for {len(leaves)} leaves")


# --- the page's lines ----------------------------------------------------------------------------

LOOKALIKE = str.maketrans("ABEZHIKMNOPTYXabeikmnoptxyvu", "ΑΒΕΖΗΙΚΜΝΟΡΤΥΧαβεικμνοπτχγνυ")


def abbreviation(text: str) -> str | None:
    """A speaker's abbreviation (ΚΛ., ΧΟ., ΗΜΙΧ.) or name in capitals (ΧΟΡΟΣ.) as the OCR reads
    it, in Greek capitals without the stop; None if the text is not one."""
    t = unicodedata.normalize("NFC", text.strip()).strip("·:;,'’`\"")
    core = t.rstrip(".").replace(" ", "")
    core = "".join(c for c in unicodedata.normalize("NFD", core) if unicodedata.category(c) not in ("Mn",))
    if not core or len(core) > 12 or not all(c.isalpha() for c in core):
        return None
    core = core.translate(LOOKALIKE)
    if not all(c.isupper() for c in core):
        return None
    if len(core) == 1 and not t.endswith("."):
        return None
    return core


def match_speaker(abbr: str, names: list[str]) -> str | None:
    """The Perseus speaker an abbreviation stands for: its letters begin the name (or the names
    of a chorus's halves: ΧΟ. ΓΕ. for Χορὸς γερόντων); None if no name fits."""
    a = skel(abbr)
    best, score = None, 0.0
    for name in names:
        words = [skel(w) for w in name.split()]
        whole = "".join(words)
        if whole.startswith(a) or (len(words) > 1 and whole.startswith(a[:2]) and any(w.startswith(a[2:4]) for w in words[1:] if a[2:4])):
            s = 1.0 + len(a) / 10
        else:
            s = difflib.SequenceMatcher(None, a, whole[: len(a)]).ratio() if len(a) >= 2 else 0
        if s > score:
            best, score = name, s
    return best if score >= 0.66 else None


def _wordlike(w: dict, conf: int = 80) -> bool:
    return len(skel(w["text"])) >= 3 and w["conf"] >= conf


def _pct(xs: list[float], q: float) -> float:
    xs = sorted(xs)
    return xs[min(len(xs) - 1, max(0, int(q * len(xs))))] if xs else 0


def _ink_rows(path: Path, x0: int, x1: int) -> tuple[list[int], int, int]:
    from PIL import Image

    with Image.open(path) as im:
        g = im.convert("L")
        w, h = g.size
        x0, x1 = max(0, x0), min(w, x1)
        ink = g.crop((x0, 0, x1, h)).point(lambda v: 255 if v < 140 else 0).resize((1, h), Image.BOX)
        return list(ink.tobytes()), w, h


def _rule_below(path: Path, y_from: int) -> int | None:
    """A printed rule (a thin dark line across much of the page) below y_from, as on the pages
    where commentary follows the apparatus under a rule."""
    from PIL import Image

    with Image.open(path) as im:
        g = im.convert("L")
        w, h = g.size
        px = g.load()
        for y in range(max(0, y_from), h - 8):
            dark = sum(1 for x in range(int(w * 0.1), int(w * 0.9), 3) if px[x, y] < 120)
            if dark > 0.55 * (w * 0.8 / 3):
                above = sum(1 for x in range(int(w * 0.1), int(w * 0.9), 3) if px[x, max(0, y - 7)] < 120)
                below = sum(1 for x in range(int(w * 0.1), int(w * 0.9), 3) if px[x, min(h - 1, y + 7)] < 120)
                if above < 0.15 * (w * 0.8 / 3) and below < 0.15 * (w * 0.8 / 3):
                    return y
    return None


def rules(path: Path, y_from: int = 0) -> list[int]:
    """Every printed rule (a thin dark line across much of the page) below y_from, top to bottom."""
    out: list[int] = []
    y = y_from
    while True:
        r = _rule_below(path, y)
        if r is None:
            return out
        out.append(r)
        y = r + 12


APP_NUMBER = re.compile(r"^[\[(]?\d{1,4}[a-z]?[.,:][)\]]?$")
_LINE_X = re.compile(r"<span class='ocr_(?:line|caption|header|textfloat)' id='\w+' title=\"bbox (\d+) (\d+) (\d+) (\d+)([^\"]*)\">(.*?)</span>\s*(?=<span class='ocr_|</p>)", re.S)
_WORD_X = re.compile(r"<span class='ocrx_word' id='\w+' title='bbox (\d+) (\d+) (\d+) (\d+); x_wconf (\d+)'[^>]*>(.*?)</span>", re.S)


def read_lines(path: Path) -> list[dict]:
    """The hOCR's lines, as gorgias_pages.read_hocr, with Tesseract's estimate of the type size
    ('x_size': the apparatus is set smaller than the verse)."""
    import html

    t = path.read_text(encoding="utf-8")
    out = []
    for m in _LINE_X.finditer(t):
        words = [{"text": unicodedata.normalize("NFC", html.unescape(re.sub(r"<[^>]+>", "", w.group(6)))),
                  "bbox": [int(w.group(i)) for i in range(1, 5)], "conf": int(w.group(5))}
                 for w in _WORD_X.finditer(m.group(6))]
        words = [w for w in words if w["text"].strip()]
        if not words:
            continue
        xs = re.search(r"x_size ([\d.]+)", m.group(5))
        out.append({"bbox": [int(m.group(i)) for i in range(1, 5)], "words": words,
                    "x_size": float(xs.group(1)) if xs else 0.0})
    out.sort(key=lambda l: (l["bbox"][1], l["bbox"][0]))
    return out


def _good(l: dict) -> int:
    """How many of a line's words were read with confidence (letters, conf 80 or more)."""
    return sum(1 for w in l["words"] if _wordlike(w))


def _noise(l: dict) -> bool:
    """A line of a reader's handwriting, or specks: no word read with confidence."""
    return not any(w["conf"] >= 75 and len(skel(w["text"])) >= 2 for w in l["words"]) \
        and not abbreviation(" ".join(w["text"] for w in l["words"]))


APP_BARE = re.compile(r"^\d{1,4}[a-z]?$")


def _item_number(w: dict, bare: bool = False, right: float | None = None) -> bool:
    """An apparatus item's number as Tesseract reads it ("103.", "17."), not a smudge. With
    `bare` (Rzach's "215 ἧς scripsi") a number without a stop counts too, unless it stands right
    of `right` (a verse's margin number)."""
    t = w["text"].strip()
    if bare and APP_BARE.match(t) and (right is None or w["bbox"][0] < right):
        return w["conf"] >= 70 and (len(t) >= 2 or w["conf"] >= 85)
    return bool(APP_NUMBER.match(t)) and w["conf"] >= 70 and (len(re.sub(r"\D", "", t)) >= 2 or w["conf"] >= 85)


def _different(a: list[dict], b: list[dict]) -> bool:
    """Two OCR lines whose heights overlap hold different words where they stand over each
    other: two printed lines (their boxes stretched by a reader's notes), not one read twice."""
    sims = []
    for w in a:
        for v in b:
            ov = min(w["bbox"][2], v["bbox"][2]) - max(w["bbox"][0], v["bbox"][0])
            if ov > 0.5 * min(w["bbox"][2] - w["bbox"][0], v["bbox"][2] - v["bbox"][0]) and skel(w["text"]) and skel(v["text"]):
                sims.append(difflib.SequenceMatcher(None, skel(w["text"]), skel(v["text"])).ratio())
    return len(sims) >= 2 and sum(sims) / len(sims) < 0.5


def page_layout(play: Play, leaf: int, app_y: int | None = None) -> dict:
    """The page's printed lines (top to bottom, each with its words and the words beside it in the
    margins), where the apparatus begins and ends, the column's edges, the line height.

    The apparatus is found from the foot of the page upwards: lines in smaller type (Tesseract's
    x_size well under the verse's) are taken until the first verse line in full-size type with
    words read with confidence; a reader's handwriting (no word read with confidence) is passed
    over; the block counts as the apparatus if it holds an item number ("103."). On a page where
    a printed rule follows (commentary under the apparatus), only what stands above the rule.
    With `app_y` (the short rule above Nilén's apparatus, lucian_pages.short_rule) the apparatus
    is everything below it."""
    from PIL import Image

    from .gorgias_pages import _edge

    _, sbuild = scan_dirs(play.scan)
    png = sbuild / "pages" / f"leaf_{leaf:04d}.png"
    lines = read_lines(ocr_leaf(play.scan, leaf))
    with Image.open(png) as im:
        W, Hpage = im.size
    head = [l for l in lines if l["bbox"][3] < 0.075 * Hpage]
    head_y = max((l["bbox"][3] for l in head), default=int(0.03 * Hpage))
    body = [l for l in lines if l not in head and not _noise(l)]
    good = [l for l in body if _good(l) >= 2]
    heights = sorted(l["bbox"][3] - l["bbox"][1] for l in good) or [50]
    H = heights[len(heights) // 2]
    upper = [l for l in good if l["bbox"][1] < 0.7 * Hpage and l["x_size"] > 0] or good
    sizes = sorted(l["x_size"] for l in upper) or [H]
    XS = sizes[len(sizes) // 2]
    rule = _rule_below(png, int(0.2 * Hpage)) if play.layout == "jebb" else None
    limit = rule if rule else Hpage
    between = None
    if rule is not None:
        # Starkie: the text, a rule, the apparatus, a second rule, the commentary
        nxt = _rule_below(png, rule + 12)
        if nxt is not None and nxt - rule > 0.5 * H:
            between = (rule, nxt)
    # the apparatus, from the foot up
    block: list[dict] = []
    for l in sorted((l for l in body if l["bbox"][3] <= limit + 5), key=lambda l: -l["bbox"][1]):
        has_num = any(_item_number(w, play.app_bare_numbers, 0.85 * W) for w in l["words"])
        if l["x_size"] > 0.92 * XS and _good(l) >= 3 and not has_num:
            break  # a verse
        if l["x_size"] <= 0.9 * XS or has_num:
            block.append(l)
    given_app_y = app_y
    app_y = app_end = None
    if given_app_y is not None:
        app_y, app_end = given_app_y + 4, Hpage - 10
    elif between is not None:
        app_y, app_end = between[0] + 4, between[1] - 4
    elif block and any(_item_number(w, play.app_bare_numbers, 0.85 * W) for l in block for w in l["words"]):
        app_y = max(0, min(l["bbox"][1] for l in block) - int(0.25 * H))
        app_end = min(limit, max(l["bbox"][3] for l in block) + int(0.4 * H))
        if play.app_to_foot:
            app_end = max([app_end] + [l["bbox"][3] + int(0.3 * H) for l in lines
                                       if l["bbox"][1] > app_y and l["bbox"][3] <= limit])
    text_lines = [l for l in body if (app_y is None or (l["bbox"][1] + l["bbox"][3]) / 2 < app_y)
                  and (rule is None or l["bbox"][3] < rule)]
    # split boxes that hold two printed lines; drop accents read as lines of their own
    split: list[dict] = []
    for l in text_lines:
        if l["bbox"][3] - l["bbox"][1] < 1.7 * H:
            split.append(l)
            continue
        groups: list[list[dict]] = []
        for w in sorted(l["words"], key=lambda w: (w["bbox"][1] + w["bbox"][3]) / 2):
            yc = (w["bbox"][1] + w["bbox"][3]) / 2
            if groups and yc - sum((v["bbox"][1] + v["bbox"][3]) / 2 for v in groups[-1]) / len(groups[-1]) < 0.6 * H:
                groups[-1].append(w)
            else:
                groups.append([w])
        for g in groups:
            sure = [w for w in g if w["conf"] >= 60] or g  # a reader's notes do not stretch the line
            split.append({"bbox": [min(w["bbox"][0] for w in g), min(w["bbox"][1] for w in sure),
                                   max(w["bbox"][2] for w in g), max(w["bbox"][3] for w in sure)], "words": g})
    solid = [l for l in split if any(len(skel(w["text"])) >= 4 for w in l["words"])]
    keep = []
    for l in split:
        if l in solid:
            keep.append(l)
            continue
        on_solid = any(min(l["bbox"][3], o["bbox"][3]) - max(l["bbox"][1], o["bbox"][1]) > 0.4 * (l["bbox"][3] - l["bbox"][1])
                       for o in solid)
        if not on_solid and (l["bbox"][3] - l["bbox"][1]) >= 0.5 * H:
            keep.append(l)
    keep.sort(key=lambda l: (l["bbox"][1] + l["bbox"][3]) / 2)
    # printed lines: boxes whose heights overlap by half are one line (measured against the box
    # that began the line, so that one tall box does not chain two lines together)
    printed: list[dict] = []
    for l in keep:
        y0, y1 = l["bbox"][1], l["bbox"][3]
        if printed:
            p = printed[-1]
            ov = min(y1, p["oy1"]) - max(y0, p["oy0"])
            if ov > 0.5 * min(y1 - y0, p["oy1"] - p["oy0"]) and not (
                    _good(l) >= 2 and _good(p) >= 2 and _different(l["words"], p["words"])):
                p["words"] += l["words"]
                p["y0"], p["y1"] = min(p["y0"], y0), max(p["y1"], y1)
                continue
        printed.append({"y0": y0, "y1": y1, "oy0": y0, "oy1": y1, "words": list(l["words"])})
    # a line Tesseract skipped: where two lines stand a line too far apart, the strip between
    # them is read again on its own
    if len(printed) > 3:
        tops = [p["y0"] for p in printed]
        pitch = sorted(b - a for a, b in zip(tops, tops[1:]))[len(tops) // 2]
        extra = []
        for a, b in zip(printed, printed[1:]):
            if b["oy0"] - a["oy0"] > 1.6 * pitch:
                y0, y1 = a["oy0"] + int(0.75 * pitch), b["oy0"] + int(0.1 * pitch)
                if y1 - y0 < 0.6 * H:
                    continue
                near = {skel(w["text"]) for w in a["words"] + b["words"] if len(skel(w["text"])) >= 3}
                for words in _reread(play.scan, leaf, y0, y1, H):
                    found = [skel(w["text"]) for w in words if w["conf"] >= 75 and len(skel(w["text"])) >= 3]
                    if found and sum(1 for x in found if x in near) < 0.5 * len(found):
                        ys = [w["bbox"][1] for w in words] + [w["bbox"][3] for w in words]
                        extra.append({"y0": min(ys), "y1": max(ys), "oy0": min(ys), "oy1": max(ys), "words": words, "reread": True})
        printed = sorted(printed + extra, key=lambda p: p["y0"])
    for p in printed:
        ws = sorted(p["words"], key=lambda w: w["bbox"][0])
        kept: list[dict] = []
        for w in ws:
            if kept:
                k = kept[-1]
                ov = min(w["bbox"][2], k["bbox"][2]) - max(w["bbox"][0], k["bbox"][0])
                if ov > 0.5 * min(w["bbox"][2] - w["bbox"][0], k["bbox"][2] - k["bbox"][0]):
                    if w["conf"] > k["conf"]:
                        kept[-1] = w
                    continue
            kept.append(w)
        p["words"] = kept
    # the column: where the confident words of most lines begin and end
    firsts, lasts = [], []
    for p in printed:
        gw = [w for w in p["words"] if _wordlike(w)]
        if len(gw) >= 2:
            firsts.append(gw[0]["bbox"][0] if len(gw) < 2 or gw[1]["bbox"][0] - gw[0]["bbox"][2] < 2 * H else gw[1]["bbox"][0])
            lasts.append(gw[-1]["bbox"][2])
    left = _edge(firsts, "left") if firsts else 0
    right = int(_pct(lasts, 0.95)) if lasts else W
    out = []
    for p in printed:
        margin = 0.3 * H
        p["left_m"] = [w for w in p["words"] if w["bbox"][2] < left - margin]
        p["right_m"] = [w for w in p["words"] if w["bbox"][0] > right + margin]
        p["words"] = [w for w in p["words"] if w not in p["left_m"] and w not in p["right_m"]]
        if not p["words"]:
            continue
        p["x0"] = min(w["bbox"][0] for w in p["words"])
        p["x1"] = max(w["bbox"][2] for w in p["words"])
        out.append(p)
    return {"leaf": leaf, "lines": out, "app_y": app_y, "app_end": app_end, "left": left, "right": right,
            "head_y": head_y, "line_h": H, "x_size": XS, "width": W, "height": Hpage, "rule": rule}


def _reread(scan: str, leaf: int, y0: int, y1: int, H: int) -> list[list[dict]]:
    """The lines Tesseract finds in a strip of the page read on its own (cached)."""
    _, sbuild = scan_dirs(scan)
    cache = sbuild / "hocr" / f"leaf_{leaf:04d}.strip-{y0}-{y1}.hocr"
    if not cache.exists():
        from PIL import Image

        with Image.open(sbuild / "pages" / f"leaf_{leaf:04d}.png") as im, tempfile.TemporaryDirectory() as t:
            im.crop((0, y0, im.size[0], y1)).save(Path(t) / "s.png")
            tesseract(Path(t) / "s.png", Path(t) / "s", "grc", 6, True)
            cache.write_text((Path(t) / "s.hocr").read_text(encoding="utf-8"), encoding="utf-8")
    out = []
    for l in read_hocr(cache):
        for w in l["words"]:
            w["bbox"] = [w["bbox"][0], w["bbox"][1] + y0, w["bbox"][2], w["bbox"][3] + y0]
        if l["bbox"][3] - l["bbox"][1] > 0.4 * H:
            out.append(l["words"])
    return out


def margin_numbers(play: Play, layout: dict) -> list[tuple[int, int]]:
    """The numbers printed in the margin beside the verses: [(y centre, number)]. For each
    printed line, the ink beyond its last word read with confidence (before its first, for an
    edition that numbers in the left margin) is cut out, enlarged and read by Tesseract's English
    model limited to digits (cached)."""
    from PIL import Image, ImageOps

    _, sbuild = scan_dirs(play.scan)
    leaf = layout["leaf"]
    cache = sbuild / "hocr" / f"leaf_{leaf:04d}.numbers-{play.margin_numbers}.json"
    if cache.exists():
        return [tuple(x) for x in json.loads(cache.read_text())]
    H = layout["line_h"]
    env = dict(os.environ, OMP_THREAD_LIMIT="1")
    marks: list[tuple[int, int]] = []
    with Image.open(sbuild / "pages" / f"leaf_{leaf:04d}.png") as im, tempfile.TemporaryDirectory() as t:
        g = im.convert("L")
        W = g.size[0]
        for p in layout["lines"]:
            gw = [w for w in p["words"] if w["conf"] >= 75 and len(skel(w["text"])) >= 2]
            if not gw:
                continue
            if play.margin_numbers == "right":
                x0, x1 = max(w["bbox"][2] for w in gw) + int(0.5 * H), W - 8
            else:
                x0, x1 = 8, min(w["bbox"][0] for w in gw) - int(0.5 * H)
            if x1 - x0 < 0.5 * H:
                continue
            strip = g.crop((x0, max(0, p["oy0"] - 6), x1, p["oy1"] + 6))
            # the first cluster of ink on the side of the text: the number
            cols = list(strip.point(lambda v: 255 if v < 140 else 0).resize((strip.size[0], 1), Image.BOX).tobytes())
            ink = [x for x, v in enumerate(cols) if v > 6]
            if not ink:
                continue
            if play.margin_numbers == "right":
                a = ink[0]
                b = a
                for x in ink:
                    if x - b > 1.2 * H:
                        break
                    b = x
            else:
                b = ink[-1]
                a = b
                for x in reversed(ink):
                    if a - x > 1.2 * H:
                        break
                    a = x
            if b - a < 0.25 * H or b - a > 4 * H:
                continue
            piece = strip.crop((max(0, a - 8), 0, min(strip.size[0], b + 8), strip.size[1]))
            piece = ImageOps.expand(piece.resize((piece.size[0] * 2, piece.size[1] * 2), Image.LANCZOS), 30, fill=255)
            path = Path(t) / "n.png"
            piece.save(path)
            out = subprocess.run(["tesseract", str(path), "stdout", "--tessdata-dir", str(TESSDATA), "-l", "eng", "--psm", "7",
                                  "-c", "tessedit_char_whitelist=0123456789"], capture_output=True, text=True, env=env).stdout.strip()
            if re.fullmatch(r"\d{1,4}", out):
                marks.append(((p["oy0"] + p["oy1"]) // 2, int(out)))
    cache.write_text(json.dumps(marks))
    return marks


# --- matching the OCR to Perseus -------------------------------------------------------------

DASHES = re.compile(r"[—–]+|-{2,}|(?<=[.,;·:!?’”\"'])-+")
_SPACING = {"᾿": "̓", "῾": "̔", "῎": "̓́", "῍": "̓̀", "῞": "̔́",
            "῝": "̔̀", "῏": "̓͂", "῟": "̔͂"}


def ocr_norm(s: str) -> str:
    """The OCR's word as printed: a breathing written before a capital put on it (᾿Α to Ἀ); elision ʼ."""
    s = unicodedata.normalize("NFC", s)
    s = re.sub("([᾿῾῎῍῞῝῏῟])([ΑΕΗΙΟΥΩΡ])", lambda m: unicodedata.normalize("NFC", m.group(2) + _SPACING[m.group(1)]), s)
    return re.sub(r"(?<=[^\W\d_])[᾽’'](?=\s|$|[,.;·:])", APOS, s)


def fold_ocr(play: Play, lines: list[dict], ocr: list[dict]) -> tuple[list[dict], list[dict]]:
    """The OCR's letters as the edition's typeface means them (Play.ocr_fold: Rzach's ϑ is θ),
    and its skeletons folded as the check text's (Play.skel_fold)."""
    if play.ocr_fold:
        tr = str.maketrans(play.ocr_fold)
        for t in ocr:
            t["t"] = t["t"].translate(tr)
            t["skel"] = skel(t["t"], play.adscript)
        for pl in lines:
            pl["ocr"] = pl["ocr"].translate(tr)
    if play.skel_fold:
        tr = str.maketrans(play.skel_fold[0::2], play.skel_fold[1::2])
        for t in ocr:
            t["skel"] = t["skel"].translate(tr)
    return lines, ocr


def ocr_stream(layouts: list[dict], adscript: bool) -> tuple[list[dict], list[dict]]:
    """The printed lines of the text in order ({'leaf', 'y0', 'y1', 'x0', 'ocr', 'abbr', 'heading',
    'noise', 'margin'}) and the OCR's words ({'t', 'skel', 'line', 'conf'}). A speaker's
    abbreviation at the start of a line, or a line that is only a speaker's name in capitals, is
    kept apart from the words. A word divided at the end of a verse is joined and stays on the
    verse where it begins."""
    lines: list[dict] = []
    toks: list[dict] = []
    pending_heading = None
    for lay in layouts:
        for p in lay["lines"]:
            ws = sorted(p["words"], key=lambda w: w["bbox"][0])
            text = " ".join(w["text"] for w in ws)
            whole = abbreviation(text)
            if whole and len(ws) <= 2:
                pending_heading = whole  # ΧΟΡΟΣ. centred above the speech, or the play's title
                lines.append({"leaf": lay["leaf"], "y0": p["y0"], "y1": p["y1"], "x0": p["x0"], "ocr": text,
                              "heading": whole, "abbr": None, "noise": False, "margin": []})
                continue
            abbr = None
            lm = " ".join(w["text"] for w in sorted(p["left_m"], key=lambda w: w["bbox"][0]) if w["conf"] >= 50)
            if lm and abbreviation(lm):
                abbr = abbreviation(lm)
            elif ws and ws[0]["conf"] >= 50 and abbreviation(ws[0]["text"]) and len(ws) > 1 \
                    and (ws[0]["text"].strip().endswith(".") or len(skel(ws[0]["text"])) <= 3):
                abbr = abbreviation(ws[0]["text"])
                ws = ws[1:]
                # ΧΟ. ΓΕ.: a second abbreviation
                if ws and len(ws) > 1 and abbreviation(ws[0]["text"]) and ws[0]["text"].strip().endswith("."):
                    abbr += " " + abbreviation(ws[0]["text"])
                    ws = ws[1:]
            if abbr is None and pending_heading:
                abbr = pending_heading
            pending_heading = None
            li = len(lines)
            # where the line's words end (not a margin number), for turnovers (build_draft)
            tx1 = max((w["bbox"][2] for w in ws if sum(c.isalpha() for c in w["text"]) >= 2), default=p["x0"])
            lines.append({"leaf": lay["leaf"], "y0": p["y0"], "y1": p["y1"], "x0": p["x0"], "ocr": text,
                          "abbr": abbr, "heading": None, "noise": bool(p.get("noise")), "margin": p["right_m"] + p["left_m"],
                          "tx1": tx1, "right": lay.get("right"), "xs": lay.get("x_size") or 50})
            if p.get("noise"):
                continue
            # a reader's scribble after a word divided at the verse's end is not the line's end
            while len(ws) > 1 and ws[-1]["conf"] < 50 and any(w["text"].rstrip().endswith(("-", "‐")) and w["conf"] >= 50 for w in ws[:-1]):
                ws = ws[:-1]
            for w in ws:
                for piece in DASHES.split(ocr_norm(w["text"])):
                    if piece.strip():
                        toks.append({"t": piece, "skel": skel(piece, adscript), "line": li, "conf": w["conf"]})
    # a word divided at the end of a line: joined, on the line where it begins
    for k, t in enumerate(toks):
        last = k + 1 == len(toks) or toks[k + 1]["line"] != t["line"]
        t["hyph"] = last and t["t"].rstrip().endswith(("-", "‐", "¬")) and len(t["skel"]) > 0
    joined: list[dict] = []
    for t in toks:
        if joined and joined[-1].get("hyph") and t["line"] == joined[-1]["line"] + 1 and t["skel"]:
            prev = joined[-1]
            prev["t"] = prev["t"].rstrip().rstrip("-‐¬") + t["t"]
            prev["skel"] = skel(prev["t"], adscript)
            prev["hyph"] = False
            prev["joined"] = True
            continue
        joined.append(t)
    return lines, [t for t in joined if t["skel"]]


def _starts_upper(word: str) -> bool:
    letters = [c for c in word if c.isalpha()]
    return bool(letters) and letters[0].isupper()


def _capitalise(word: str) -> str:
    m = re.match(r"^([“‘\[⟨(]*)(.)(.*)$", word, re.S)
    if not m:
        return word
    d = unicodedata.normalize("NFD", m.group(2))
    return m.group(1) + unicodedata.normalize("NFC", d[0].upper() + d[1:]) + m.group(3)


def _accent_letters(s: str) -> str:
    return re.sub(r"[^\w]", "", unicodedata.normalize("NFC", s.lower().replace(APOS, "")))


def _dp_pairs(O: list[dict], P: list[dict]) -> list[tuple[int, int, float]]:
    """The best monotone pairing of two word lists (as gorgias_pages._pair_gap, without its size
    limit): a pair scores its similarity less 0.3, words may stay unpaired."""
    n, m = len(O), len(P)
    if not n or not m:
        return []

    def sim(a: str, b: str) -> float:
        if a == b:
            return 1.0
        if not a or not b or abs(len(a) - len(b)) > 3 or (a[:2] != b[:2] and a[-2:] != b[-2:]):
            return 0.0
        return difflib.SequenceMatcher(None, a, b, autojunk=False).ratio()

    prev = [0.0] * (m + 1)
    back: list[bytearray] = []
    os_ = [o["skel"] for o in O]
    ps_ = [p["skel"] for p in P]
    for i in range(1, n + 1):
        cur = [0.0] * (m + 1)
        bk = bytearray(m + 1)
        a = os_[i - 1]
        for j in range(1, m + 1):
            best, how = prev[j], 1
            if cur[j - 1] > best:
                best, how = cur[j - 1], 2
            s = sim(a, ps_[j - 1])
            if s >= 0.45 and prev[j - 1] + s - 0.3 > best:
                best, how = prev[j - 1] + s - 0.3, 3
            cur[j] = best
            bk[j] = how
        back.append(bk)
        prev = cur
    pairs = []
    i, j = n, m
    while i > 0 and j > 0:
        how = back[i - 1][j]
        if how == 3:
            pairs.append((i - 1, j - 1, sim(os_[i - 1], ps_[j - 1])))
            i, j = i - 1, j - 1
        elif how == 1:
            i -= 1
        else:
            j -= 1
    return pairs[::-1]


def realign(ocr: list[dict], toks: list[dict], match: list[int | None], run: int = 15, reach: int = 250) -> int:
    """Mend the global alignment where it has skipped a stretch: difflib joins blocks greedily, so
    where a passage is repeated (a refrain) it may pair the print's first copy with Perseus's
    second and leave everything between unmatched. Around every run of `run` or more unmatched
    Perseus words the neighbourhood is aligned again by _dp_pairs, and taken if it pairs clearly
    more words. Returns the number of stretches mended."""
    mended = 0
    j = 0
    n = len(toks)
    while j < n:
        if match[j] is not None:
            j += 1
            continue
        k = j
        while k < n and match[k] is None:
            k += 1
        if k - j < run:
            j = k
            continue
        lo, hi = max(0, j - reach), min(n, k + reach)
        o_lo = next((match[x] + 1 for x in range(lo - 1, -1, -1) if match[x] is not None), 0)
        o_hi = next((match[x] for x in range(hi, n) if match[x] is not None), len(ocr))
        before = sum(1 for x in range(lo, hi) if match[x] is not None and toks[x].get("sim", 0) >= 1.0)
        pairs = _dp_pairs(ocr[o_lo:o_hi], toks[lo:hi])
        exact = sum(1 for _a, _b, s in pairs if s >= 1.0)
        if exact > before + 5:
            for x in range(lo, hi):
                match[x] = None
                toks[x]["sim"] = 0.0
            for a, b, s in pairs:
                match[lo + b] = o_lo + a
                toks[lo + b]["sim"] = s
            mended += 1
        j = max(k, hi)
    return mended


def build_draft(play: Play, sources: Path) -> tuple[list[dict], dict[int, dict], list[dict], dict]:
    """The automatic text: verses {'n', 'leaf', 'text', 'speaker' (a new speaker's name, or
    None), 'flags', 'y0', 'y1', 'ocr', 'stages' (directions before the verse)}, the layouts, the
    printed lines and the Perseus text."""
    leaves = play.visible("text")
    workers = int(os.environ.get("DRAMA_WORKERS", "4"))
    with ThreadPoolExecutor(workers) as ex:
        layouts = dict(zip(leaves, ex.map(lambda l: page_layout(play, l), leaves)))
        list(ex.map(lambda l: margin_numbers(play, layouts[l]), leaves))
    lines, ocr = fold_ocr(play, *ocr_stream([layouts[l] for l in leaves], play.adscript))
    pers = load_perseus(play, sources)
    toks = pers["tokens"]
    if play.adscript:
        for t in toks:
            t["skel"] = skel(t["t"], True)
    for t in toks:
        t["label"] = False
        t["newsec"] = t["first"]
        t["para"] = t["newsp"]
    match = align_words(ocr, toks)
    mended = realign(ocr, toks, match)
    if mended:
        print(f"{play.slug}: {mended} stretches aligned again (a repeated passage or a lost stretch)", file=sys.stderr)
    # the stretch of Perseus the pages hold (all of it once every text page is read): words far
    # before the first word found or after the last are not on these pages
    found = [j for j, o in enumerate(match) if o is not None]
    lo = max(0, found[0] - 12) if found else 0
    hi = min(len(toks), found[-1] + 13) if found else 0
    if lo > 0 or hi < len(toks):
        print(f"{play.slug}: the pages hold Perseus lines {toks[lo]['n']}–{toks[hi - 1]['n']}; "
              f"{lo} words before and {len(toks) - hi} after were not found", file=sys.stderr)
    assign_lines(lines, ocr, toks[lo:hi], match[lo:hi])
    # the printed verses: each printed line's words, split where a new speaker begins inside it
    by_line: dict[int, list[int]] = {}
    for j in range(lo, hi):
        by_line.setdefault(toks[j]["line"], []).append(j)
    verses: list[dict] = []
    for li, pl in enumerate(lines):
        words = by_line.get(li)
        if not words:
            if not pl.get("heading") and not pl.get("noise") and len(skel(pl["ocr"])) >= 6:
                pl["dropped"] = True
            continue
        cur: list[int] = []
        for j in words:
            if toks[j]["newsp"] and cur:
                verses.append({"line": li, "words": cur, "split": len(verses) > 0 and verses[-1]["line"] == li})
                cur = []
            cur.append(j)
        verses.append({"line": li, "words": cur, "split": bool(verses) and verses[-1]["line"] == li})
    # a turnover: the end of a verse too long for the measure, set indented on the next printed
    # line (Starkie's anapaests: "… τὸν κακοδαίμονʼ | ἔχοντα."), is part of the verse above
    merged: list[dict] = []
    for v in verses:
        prev = merged[-1] if merged else None
        if prev is not None and not v["split"] and v["line"] == prev["line"] + 1:
            a, b = lines[prev["line"]], lines[v["line"]]
            first, last = toks[v["words"][0]], toks[prev["words"][-1]]
            if (a["leaf"] == b["leaf"] and a.get("right") and not first["newsp"] and first["n"] == last["n"]
                    and a["tx1"] >= a["right"] - 3 * a["xs"] and b["x0"] >= a["x0"] + 1.5 * a["xs"]
                    and not b.get("abbr")):
                prev["words"] = prev["words"] + v["words"]
                prev.setdefault("turnover", []).append(v["line"])
                continue
        merged.append(v)
    verses = merged
    numbers = number_verses([v["words"] for v in verses], toks)
    stages_after: dict[int, list[str]] = {}
    for after, text in pers["stages"]:
        stages_after.setdefault(after, []).append(text)
    word_verse = {j: k for k, v in enumerate(verses) for j in v["words"]}
    paired_o = {o for o in match if o is not None}
    ocr_by_line: dict[int, list[int]] = {}
    for k, t in enumerate(ocr):
        ocr_by_line.setdefault(t["line"], []).append(k)
    names = pers["speakers"]
    out: list[dict] = []
    for k, (v, (n, nflags)) in enumerate(zip(verses, numbers)):
        pl = lines[v["line"]]
        flags = list(nflags)
        for tl in v.get("turnover", []):
            flags.append(f"the indented line “{lines[tl]['ocr']}” below was joined to this verse as its turnover "
                         "(the end of a verse too long for the line); check the print sets it so")
        words: list[str] = []
        first_tok = toks[v["words"][0]]
        speaker = first_tok["speaker"] if first_tok["newsp"] else None
        for j in v["words"]:
            t = toks[j]
            w = t["t"]
            o = match[j]
            if o is not None and _starts_upper(ocr[o]["t"]) and not _starts_upper(w) and t["sim"] >= 0.8:
                w = _capitalise(w)
            words.append(w)
            if o is None:
                flags.append(f"{w}: not found in the OCR; check it is printed on this line")
            elif t["sim"] < 1.0 and ocr[o]["conf"] >= 80:
                flags.append(f"{w}: the OCR reads “{ocr[o]['t']}”")
            elif t["sim"] == 1.0 and len(t["skel"]) >= 4 and ocr[o]["conf"] >= 95:
                a, b = _accent_letters(w), _accent_letters(ocr[o]["t"])
                if play.adscript:
                    b = _accent_letters(_adscript_to_subscript(ocr[o]["t"]))
                if a != b:
                    flags.append(f"{w}: the OCR reads “{ocr[o]['t']}” (accents)")
            if t.get("guess"):
                flags.append(f"{w}: which line it stands on is a guess")
            if t.get("gap"):
                flags.append(f"{w}: Perseus marks a gap (lost text) after this word; copy what the edition prints")
        # OCR words no Perseus word was matched to
        if not v["split"]:
            for o in ocr_by_line.get(v["line"], []):
                if o not in paired_o and len(ocr[o]["skel"]) >= 4 and ocr[o]["conf"] >= 85:
                    flags.append(f"the OCR reads “{ocr[o]['t']}” on this line, which Perseus does not have here")
        # brackets and daggers
        if not v["split"]:
            text_now = " ".join(words)
            for open_, close, name in (("[", "]", "square brackets"), ("⟨", "⟩", "angle brackets")):
                o_has = any(c in pl["ocr"] for c in (open_, close) + (("<", ">") if open_ == "⟨" else ()))
                d_has = open_ in text_now or close in text_now
                if o_has and not d_has:
                    flags.append(f"the OCR shows {name} on this line, Perseus has none: copy the print's")
                elif d_has and not o_has:
                    flags.append(f"Perseus has {name} on this line ({text_now[:40]}…), the OCR shows none: check the print")
            if "†" in pl["ocr"]:
                flags.append("the OCR reads a dagger † on this line: copy it where the print has it")
            if re.match(r"^\s*\(", pl["ocr"]) and re.search(r"\)\s*$", pl["ocr"]):
                flags.append("a bracketed line: a stage direction?")
        # the speaker against the print
        if not v["split"]:
            abbr = pl.get("abbr")
            if speaker is not None:
                if abbr is None:
                    flags.append(f"Perseus changes speaker here ({speaker}), the print shows none")
                else:
                    who = match_speaker(abbr, names)
                    if who != speaker:
                        flags.append(f"the print's “{abbr}.” does not match Perseus's speaker {speaker}"
                                     + (f" (it may be {who})" if who else "") + ": check the speaker")
            elif abbr is not None:
                who = match_speaker(abbr, names)
                flags.append(f"a speaker change in the print that Perseus does not have here (the print reads “{abbr}.”"
                             + (f", {who}" if who else "") + ")")
        elif speaker is not None:
            flags.append(f"Perseus changes speaker ({speaker}) inside the printed line: split here; check the print")
        # stage directions Perseus has before this verse
        stages = list(stages_after.get(v["words"][0] - 1, []))
        for j in v["words"][:-1]:
            for s in stages_after.get(j, []):
                flags.append(f"Perseus has the stage direction “{s}” inside this verse, after {toks[j]['t']}: "
                             "if the edition prints it, write it as a `!` line where it stands (split the verse there)")
        if k == 0 and -1 in stages_after:
            stages = stages_after[-1] + stages
        for s in stages:
            flags.append(f"Perseus has the stage direction “{s}” before this verse: keep it as the edition prints it, or remove it")
        out.append({"n": n, "leaf": pl["leaf"], "text": " ".join(words), "speaker": speaker, "flags": flags,
                    "y0": pl["y0"], "y1": max([pl["y1"]] + [lines[tl]["y1"] for tl in v.get("turnover", [])]), "ocr": " | ".join([pl["ocr"]] + [lines[tl]["ocr"] for tl in v.get("turnover", [])]), "stages": [f"({s})" if not s.startswith("(") else s for s in stages],
                    "line": v["line"], "perseus": first_tok["n"]})
    # stage directions after the last word
    last = hi - 1
    if last in stages_after and out:
        out[-1]["flags"].append("Perseus has a stage direction after the last verse: " + "; ".join(stages_after[last]))
    # a printed line the OCR read that matched no Perseus word: on the verse before it
    by_li = {v["line"]: k for k, v in enumerate(out)}
    for li, pl in enumerate(lines):
        if pl.get("dropped"):
            prev = max((x for x in by_li if x < li), default=None)
            target = out[by_li[prev]] if prev is not None else (out[0] if out else None)
            if target is not None:
                target["flags"].append(f"after this verse: this printed line matched no Perseus words: “{pl['ocr'][:70]}”")
    # lost verses Perseus marks (<l> with only a gap): on the verse where the next Perseus line begins
    for li, line in enumerate(pers["lines"]):
        if line["gap"]:
            nxt = next((x for x in pers["lines"][li + 1:] if x["words"]), None)
            if nxt is not None:
                k = word_verse.get(nxt["words"][0])
                if k is not None:
                    out[k]["flags"].append(f"Perseus marks a lost verse ({line['n']}) before this one: copy what the edition prints there")
    check_margins(play, out, layouts)
    for v in out:
        v["flags"] = list(dict.fromkeys(v["flags"]))
    return out, layouts, lines, pers


def _adscript_to_subscript(s: str) -> str:
    d = unicodedata.normalize("NFD", s)
    d = re.sub(r"([αηωΑΗΩ][̀-ͯ]*)ι(?![̈́̀͂])", lambda m: m.group(1) + "ͅ", d)
    return unicodedata.normalize("NFC", d)


def check_margins(play: Play, verses: list[dict], layouts: dict[int, dict]) -> None:
    """Compare the verse numbers with the numbers printed in the margin."""
    by_leaf: dict[int, list[dict]] = {}
    for v in verses:
        by_leaf.setdefault(v["leaf"], []).append(v)
    for leaf, vs in by_leaf.items():
        lay = layouts[leaf]
        marks = margin_numbers(play, lay)
        pitch = lay["line_h"] * 1.25
        found = 0
        for y, num in marks:
            near = min(vs, key=lambda v: abs((v["y0"] + v["y1"]) / 2 - y))
            if abs((near["y0"] + near["y1"]) / 2 - y) > 0.7 * pitch:
                continue
            b = base(near["n"])
            if num % 5 or abs(num - b) > 8:
                continue  # a speck, handwriting, or a misread number
            found += 1
            if num != b:
                near["flags"].append(f"the margin reads {num} at a line numbered {near['n']}")
        if not found and len(vs) >= 10:
            vs[0]["flags"].append("no margin number was read on this page: check the numbering against the page")


# --- crops, check sheets, batches ---------------------------------------------------------------

def apparatus_images(play: Play, leaf: int, layout: dict, out_dir: Path, stem: str, suffix: str = "app") -> dict:
    """The apparatus cut out of the page, its halves enlarged (<stem>-app-l.png, -app-r.png), and
    Tesseract's two readings of it."""
    from PIL import Image

    _, sbuild = scan_dirs(play.scan)
    res: dict[str, str] = {}
    if layout["app_y"] is None:
        return res
    y0, y1 = layout["app_y"] - 10, layout["app_end"] or layout["height"]
    (out_dir / "app").mkdir(exist_ok=True)
    with Image.open(sbuild / "pages" / f"leaf_{leaf:04d}.png") as im:
        g = im.convert("L")
        w = g.size[0]
        # the apparatus is set to the full measure, wider than the verse: the page's ink, not the column
        cols = list(g.crop((0, y0, w, y1)).point(lambda v: 255 if v < 140 else 0).resize((w, 1), Image.BOX).tobytes())
        ink = [x for x, v in enumerate(cols) if v > 3]
        x0 = max(0, (ink[0] if ink else 0) - 25)
        x1 = min(w, (ink[-1] if ink else w) + 25)
        crop = g.crop((x0, y0, x1, y1))
        cw = crop.size[0]
        half = cw // 2
        for side, box in (("l", (0, 0, half + 90, crop.size[1])), ("r", (half - 90, 0, cw, crop.size[1]))):
            part = crop.crop(box)
            part.resize((int(part.size[0] * 1.6), int(part.size[1] * 1.6)), Image.LANCZOS).save(out_dir / f"{stem}-{suffix}-{side}.png")
        big = out_dir / "app" / f"leaf_{leaf:04d}.png"
        if not big.exists():
            crop.resize((cw * 2, crop.size[1] * 2), Image.LANCZOS).save(big)
    for langs, ext in ((play.app_langs[0], "first"), (play.app_langs[1], "second")):
        txt = out_dir / "app" / f"leaf_{leaf:04d}.{ext}.txt"
        if not txt.exists():
            with tempfile.TemporaryDirectory() as t:
                tesseract(big, Path(t) / "a", langs, 6, False)
                txt.write_text(unicodedata.normalize("NFC", (Path(t) / "a.txt").read_text(encoding="utf-8")), encoding="utf-8")
        res[ext] = txt.read_text(encoding="utf-8").strip()
    return res


def facing_apparatus(play: Play, leaf: int, out_dir: Path, stem: str) -> dict:
    """For a Jebb-layout volume: the apparatus continued on the facing page under the translation
    (the small type above the rule that heads the commentary), as <stem>-app2-l.png, -app2-r.png."""
    lay = page_layout(play, leaf)
    if lay["app_y"] is None:
        return {}
    return apparatus_images(play, leaf, lay, out_dir, stem, "app2")


def lines_image(play: Play, leaf: int, verses: list[dict], path: Path) -> bool:
    """The flagged verses of a page cut out, one under another, each labelled with its number."""
    from PIL import Image, ImageDraw, ImageFont

    if not verses:
        return False
    _, sbuild = scan_dirs(play.scan)
    with Image.open(sbuild / "pages" / f"leaf_{leaf:04d}.png") as im:
        g = im.convert("L")
        w = g.size[0]
        seen = set()
        crops = []
        for v in verses:
            key = (v["y0"], v["y1"])
            label = v["n"] if key not in seen else v["n"] + " (same)"
            seen.add(key)
            crops.append((label, g.crop((max(0, 20), max(0, v["y0"] - 14), w - 20, v["y1"] + 12))))
    label_w = 230
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
    sheet.save(path)
    return True


def write_draft(slug: str, sources: Path, transcriptions: Path) -> list[dict]:
    """The check sheets, crops, pages.json and draft.json; the batch files that do not exist yet."""
    play = PLAYS[slug]
    out_dir = route_dir("drama-pages", slug, play.scan)
    verses, layouts, lines, pers = build_draft(play, sources)
    by_leaf: dict[int, list[dict]] = {}
    for v in verses:
        by_leaf.setdefault(v["leaf"], []).append(v)
    names = pers["speakers"]
    index = []
    leaves = play.visible("text")
    for b, leaf in enumerate(leaves):
        vs = by_leaf.get(leaf, [])
        stem = f"p-{leaf:04d}"
        for old in out_dir.glob(f"{stem}-*.png"):
            old.unlink()
        app = apparatus_images(play, leaf, layouts[leaf], out_dir, stem)
        # the apparatus run on to the facing page; where that page is the translation (Starkie), only
        # when the page has a second rule: the run-on stands between the two, above the commentary
        app2 = {}
        if play.layout == "jebb":
            f = play.facing(leaf)
            if not play.trans_leaves or len(rules(scan_dirs(play.scan)[1] / "pages" / f"leaf_{f:04d}.png", 300)) >= 2:
                app2 = facing_apparatus(play, f, out_dir, stem)
        flagged = [v for v in vs if v["flags"]]
        has_lines = lines_image(play, leaf, flagged, out_dir / f"{stem}-lines.png")
        md = [f"# Page {stem} (leaf {leaf}): verses {vs[0]['n']}–{vs[-1]['n']}" if vs else f"# Page {stem} (leaf {leaf})", ""]
        imgs = [f"pages/leaf_{leaf:04d}.png (the whole page)"]
        if has_lines:
            imgs.append(f"{stem}-lines.png (the flagged verses, each with its number)")
        if app:
            imgs.append(f"{stem}-app-l.png and {stem}-app-r.png (the apparatus, left and right half, enlarged)")
        if app2:
            imgs.append(f"{stem}-app2-l.png and {stem}-app2-r.png (the apparatus continued on the facing page, leaf {play.facing(leaf)})")
        md.append("Images: " + "; ".join(imgs))
        md.append("")
        md.append("Perseus's speakers in this play (write `@ Name` with one of these): " + ", ".join(names))
        md.append("")
        md.append("## Flags on the text")
        md.append("")
        if flagged:
            for v in flagged:
                md.append(f"* {v['n']}  `{v['text']}`")
                for f in v["flags"]:
                    md.append(f"    * {f}")
        else:
            md.append("None: the OCR agrees with Perseus on every verse, and the margin with the numbers.")
        md.append("")
        md.append("## The verses of the page (the draft) beside Tesseract's reading of the printed line")
        md.append("")
        for v in vs:
            if v["speaker"]:
                md.append(f"@ {v['speaker']}")
            md.append(f"{v['n']}\t{v['text']}\n\t\tOCR: {v['ocr']}")
        md.append("")
        md.append(f"## Tesseract's readings of the apparatus ({play.app_langs[0]}; {play.app_langs[1]}). Both garble sigla and numbers")
        for name, a in (("", app), (" (facing page)", app2)):
            if not a:
                continue
            md.append("")
            md.append(f"```{name}")
            md.append(a.get("first", ""))
            md.append("```")
            md.append("")
            md.append("```")
            md.append(a.get("second", ""))
            md.append("```")
        if not app and not app2:
            md.append("")
            md.append("(no apparatus found on this page)")
        (out_dir / f"{stem}.md").write_text("\n".join(md) + "\n", encoding="utf-8")
        index.append({"stem": stem, "leaf": leaf, "first": vs[0]["n"] if vs else None, "last": vs[-1]["n"] if vs else None,
                      "lines": len(vs), "flagged": len(flagged), "batch": b // PAGES_PER_BATCH + 1,
                      "apparatus": bool(app or app2)})
    (out_dir / "pages.json").write_text(json.dumps(index, ensure_ascii=False, indent=1), encoding="utf-8")
    (out_dir / "draft.json").write_text(json.dumps(
        [{k: v[k] for k in ("n", "leaf", "text", "speaker", "flags", "y0", "y1", "ocr", "stages", "perseus")} for v in verses],
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
            for v in by_leaf.get(leaf, []):
                for s in v["stages"]:
                    out.append(f"!\t{s}")
                if v["speaker"]:
                    out.append(f"@ {v['speaker']}")
                out.append(f"{v['n']}\t{v['text']}")
            out.append("--- apparatus")
            out.append("--- notes")
            out.append("")
        path.write_text("\n".join(out), encoding="utf-8")
    return index


# --- checking a batch -------------------------------------------------------------------------

def check_batch(slug: str, path: Path, sources: Path) -> list[str]:
    """Remarks on one checked batch file: format, numbering, speakers, apparatus numbers, pages
    missing, elision, divided words, and every place where the words differ from Perseus (each a
    change made on checking; '(noted)' where the page's notes mention the line)."""
    from .drama import APP_N, LINE_N, read_text_batches

    play = PLAYS[slug]
    out_dir = PIPELINE / "build" / "drama-pages" / slug
    index = json.loads((out_dir / "pages.json").read_text(encoding="utf-8"))
    pages = read_text_batches(path.parent, files=[path])
    m = re.search(r"batch-(\d+)", path.name)
    expected = [p["stem"] for p in index if m and p.get("batch") == int(m.group(1))]
    remarks: list[str] = []
    for stem in expected:
        if stem not in pages:
            remarks.append(f"{stem}: missing from the batch")
    for stem in pages:
        if stem not in expected:
            remarks.append(f"{stem}: not a page of this batch")
    pers = load_perseus(play, sources)
    names = set(pers["speakers"])
    by_stem = {p["stem"]: p for p in index}
    prev: tuple[int, str] | None = None
    words: list[tuple[str, str, str]] = []  # (skel, word, line)
    noted: set[str] = set()
    for stem, block in pages.items():
        for e in block["errors"]:
            remarks.append(f"{stem}: {e}")
        for raw in block["notes"]:
            mm = re.match(r"^(\d+[a-z]?)", raw)
            if mm:
                noted.add(mm.group(1))
                noted.add(str(base(mm.group(1))))
        numbers: list[str] = []
        for a, b in block["items"]:
            if a == "@":
                if b not in names:
                    remarks.append(f"{stem}: speaker “{b}” is not one of Perseus's names ({', '.join(sorted(names))})")
                continue
            if a == "!":
                if not b:
                    remarks.append(f"{stem}: an empty stage direction")
                continue
            mm = LINE_N.match(a)
            if not mm:
                remarks.append(f"{stem}: bad line number {a!r}")
                continue
            key = (int(mm.group(1)), mm.group(2))
            if prev is not None and key <= prev:
                remarks.append(f"{stem}: {a} follows {prev[0]}{prev[1]}: the numbering does not run on")
            prev = key
            numbers.append(a)
            if b != unicodedata.normalize("NFC", b):
                remarks.append(f"{stem} {a}: not NFC")
            if re.search(r"[Ͱ-Ͽἀ-῿][’'᾽]", b) or re.search(r"[᾽']", b):
                remarks.append(f"{stem} {a}: elision written other than ʼ")
            if re.search(r"[Ͱ-Ͽἀ-῿]-\s*$", b):
                remarks.append(f"{stem} {a}: a divided word? write it whole at the end of this verse")
            if "*" in b:
                remarks.append(f"{stem} {a}: an asterisk (leave Sidgwick's mark of a conjecture out)")
            for w, _s, _e in greek.words(b):
                words.append((skel(w), w, a))
        if not numbers and by_stem.get(stem, {}).get("lines"):
            remarks.append(f"{stem}: no verses, the draft had {by_stem[stem]['lines']}")
        elif stem in by_stem and abs(len(numbers) - by_stem[stem]["lines"]) > 3:
            remarks.append(f"{stem}: {len(numbers)} verses, the draft had {by_stem[stem]['lines']}")
        page_bases = {base(n) for n in numbers}
        if numbers and not block["apparatus"] and not any("no apparatus" in x for x in block["notes"]):
            remarks.append(f"{stem}: no apparatus (if the page prints none, say “no apparatus on this page” under notes)")
        for n, item in block["apparatus"]:
            mm = APP_N.match(n)
            if not mm:
                remarks.append(f"{stem}: bad apparatus number {n!r}")
                continue
            if int(mm.group(1)) not in page_bases and n not in noted and mm.group(1) not in noted:
                remarks.append(f"{stem}: apparatus {n} names a line not on this page")
            if re.search(r"\s[:;]", item):
                remarks.append(f"{stem} {n}: a space before a colon or semicolon")
            if item != unicodedata.normalize("NFC", item):
                remarks.append(f"{stem} {n}: apparatus not NFC")
    # wording against Perseus, over the Perseus lines the batch covers
    if words:
        lo = min(base(w[2]) for w in words)
        hi = max(base(w[2]) for w in words)
        # a few Perseus lines more on each side: a verse at the batch's edge may hold words of its
        # neighbour (what Perseus has beyond our first and last words is not reported)
        pw = [(skel(piece), piece) for t in pers["tokens"] if lo - 6 <= t["base"] <= hi + 6
              for piece in re.split(r"[—–]+", t["t"]) if skel(piece)]
        import difflib

        ours = [w[0] for w in words]
        sm = difflib.SequenceMatcher(None, ours, [p[0] for p in pw], autojunk=False)
        for op, a0, a1, b0, b1 in sm.get_opcodes():
            if op == "equal":
                continue
            if op == "insert" and (a0 == 0 or a0 == len(ours)):
                continue
            if op == "replace" and (a0 == 0 or a1 == len(ours)) and b1 - b0 > a1 - a0:
                # at the edge, Perseus's extra words are the neighbours': compare only as many
                theirs_cut = pw[b1 - (a1 - a0):b1] if a0 == 0 else pw[b0:b0 + (a1 - a0)]
                if [p[0] for p in theirs_cut] == ours[a0:a1]:
                    continue
                b0, b1 = (b1 - (a1 - a0), b1) if a0 == 0 else (b0, b0 + (a1 - a0))  # the neighbours' words are not ours
            where = words[a0][2] if a0 < len(words) else words[-1][2]
            mine = " ".join(w[1] for w in words[a0:a1]) or "(nothing)"
            theirs = " ".join(p[1] for p in pw[b0:b1]) or "(nothing)"
            tag = " (noted)" if where in noted or str(base(where)) in noted else ""
            remarks.append(f"{where}: written {mine} | Perseus has {theirs}{tag}")
    return remarks


def main(argv: list[str]) -> None:
    slug, step = argv[0], argv[1]
    if step == "draft":
        index = write_draft(slug, PIPELINE / "sources", PIPELINE / "transcriptions" / "drama" / slug)
        print(f"{slug}: {len(index)} pages, {sum(p['lines'] for p in index)} verses, {sum(p['flagged'] for p in index)} flagged")
    else:
        run(slug, step)


if __name__ == "__main__":
    main(sys.argv[1:])
