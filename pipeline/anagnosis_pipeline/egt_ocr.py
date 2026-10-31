"""OCR of the Expositor's Greek Testament, and the words in it that need a look at the scan.

The Expositor's Greek Testament, ed. W. Robertson Nicoll (London: Hodder and Stoughton,
1897-1910), five volumes, public domain. Volume 1 (the Synoptic Gospels by A. B. Bruce, John by
Marcus Dods) is read from the Internet Archive scan expositorsgreek01nico (1910 printing,
University of Toronto, Robarts Library, 500 ppi, 890 leaves), the cleanest of the five open copies.

A page has a running head, then (usually) the Greek text of the verses with marginal
references and short textual footnotes, both full width, then the commentary in two columns.
Only the commentary is checked; the rest is kept in the OCR but not flagged.

Steps (each leaf's result is saved as soon as it is done, so a rerun continues where it stopped):

    python -m anagnosis_pipeline.egt_ocr fetch 150-169     the leaves' JPEG 2000 images, as grey PNG
    python -m anagnosis_pipeline.egt_ocr ocr 150-169       Tesseract (tessdata_best eng+grc), hOCR per leaf
    python -m anagnosis_pipeline.egt_ocr analyse 150-169   lines, columns, word repairs, flags
    python -m anagnosis_pipeline.egt_ocr proof 150-169 152,160,166 pilot
                                                           a proof page of the flagged lines (and of
                                                           every line of leaves 152, 160, 166)
    python -m anagnosis_pipeline.egt_ocr evaluate <proof corrections .tsv>
                                                           the pilot's numbers

Files, under pipeline/sources/egt/<scan>/ (downloads) and pipeline/build/egt/<scan>/:

    jp2/<scan>_0150.jp2       the scan's original image of leaf 150
    pages/leaf_0150.png       the same, grey
    hocr/leaf_0150.hocr       Tesseract's reading, with each word's box and confidence
    lines/leaf_0150.json      the page's lines: region (head, top, left, right), words, repairs, flags
    text/leaf_0150.txt        the commentary, column by column, one printed line per line
    flags.tsv                 one suspect word per line (see FLAG_KINDS)
"""
from __future__ import annotations

import html
import json
import os
import pickle
import re
import subprocess
import sys
import tempfile
import unicodedata
from collections import Counter
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
PIPELINE = ROOT / "pipeline"
TESSDATA = PIPELINE / "tessdata"
SCAN = "expositorsgreek01nico"

FLAG_KINDS = {
    "latin": "a word in Latin letters found in no English word list (often Greek read as Latin letters)",
    "greek": "a Greek word whose letters are found in no Greek source",
    "accent": "a Greek word whose letters are known, but not with these accents and breathings",
    "mixed": "a word that mixes Greek and Latin letters",
    "digit": "digits run together with letters (1 for I, 0 for θ), or a lone 1 where a word is expected",
    "rare": "a capitalised or foreign word in Latin letters, read with confidence (a name, a German or Latin quotation)",
    "conf": "a word that passes the word checks but that Tesseract read with low confidence",
}
CONF_LIMIT = 65

GREEK_CH = "\u0370-\u03ff\u1f00-\u1fff"
APOS = "'’ʼ᾽"
TOKEN = re.compile(rf"[^\W\d_]+(?:[{APOS}][^\W\d_]+)*[{APOS}]?|\d+")
# the dash between notes (—), as the OCR gives it, and as the Greek model gives it (-- or "word.- ")
DASH = re.compile(r"—|–|-{2,3}|(?<=[.,;:!?)])-(?=\s|$)")
ROMAN = re.compile(r"^(?=[ivxlc]+$)c{0,3}(xc|xl|l?x{0,3})(ix|iv|v?i{0,3})$", re.I)
# abbreviations and Latin words of the commentary that no English word list has
KNOWN = {
    "vide", "cf", "ver", "vv", "vers", "ch", "chap", "ff", "sc", "ie", "eg", "viz", "etc", "ibid", "loc", "cit",
    "op", "al", "pp", "seq", "sqq", "infra", "supra", "ad", "in", "et", "sq", "ii", "iii", "mk", "lk", "jo", "jn",
    "matt", "mt", "lev", "deut", "ex", "exod", "gen", "num", "isa", "jer", "ezek", "ps", "pss", "prov", "eccl",
    "dan", "hos", "mic", "zech", "mal", "macc", "ecclus", "sir", "wisd", "rom", "cor", "gal", "eph", "phil",
    "col", "thess", "tim", "tit", "philem", "heb", "jas", "pet", "rev", "apoc", "acts", "lxx", "wh", "tr", "rv",
    "av", "kal", "grot", "beng", "mey", "weiss", "hahn", "parall", "bk", "vol", "cp", "comp", "ib", "id",
    "nt", "ot", "mss", "ms", "codd", "cod", "om", "ins", "add", "aor", "perf", "pres", "imperf", "fut", "inf",
    "ptc", "part", "subj", "opt", "imper", "gen", "dat", "acc", "nom", "voc", "pl", "sing", "mid", "pass",
}


def leaves(spec: str) -> list[int]:
    out: list[int] = []
    for part in spec.split(","):
        a, _, b = part.partition("-")
        out += list(range(int(a), int(b or a) + 1))
    return out


def dirs(scan: str = SCAN) -> tuple[Path, Path]:
    src = PIPELINE / "sources" / "egt" / scan
    build = PIPELINE / "build" / "egt" / scan
    for d in (src / "jp2", build / "pages", build / "hocr", build / "lines", build / "text"):
        d.mkdir(parents=True, exist_ok=True)
    return src, build


# --- fetch -------------------------------------------------------------------------------------

def fetch_leaf(leaf: int, scan: str = SCAN) -> Path:
    src, build = dirs(scan)
    png = build / "pages" / f"leaf_{leaf:04d}.png"
    if png.exists():
        return png
    jp2 = src / "jp2" / f"{scan}_{leaf:04d}.jp2"
    if not jp2.exists():
        url = f"https://archive.org/download/{scan}/{scan}_jp2.zip/{scan}_jp2%2F{scan}_{leaf:04d}.jp2"
        tmp = jp2.with_suffix(".part")
        subprocess.run(["curl", "-sfL", "--retry", "3", "-o", str(tmp), url], check=True)
        tmp.rename(jp2)
    with tempfile.TemporaryDirectory() as t:
        subprocess.run(["opj_decompress", "-i", str(jp2), "-o", f"{t}/p.png"], check=True, capture_output=True)
        subprocess.run(["magick", f"{t}/p.png", "-colorspace", "Gray", str(png) + ".part.png"], check=True)
    os.replace(str(png) + ".part.png", png)
    return png


# --- ocr ---------------------------------------------------------------------------------------

def tesseract(image: Path, out_base: Path, langs: str = "eng+grc", psm: int = 3) -> None:
    env = dict(os.environ, OMP_THREAD_LIMIT="1")
    subprocess.run(["tesseract", str(image), str(out_base), "--tessdata-dir", str(TESSDATA), "-l", langs,
                    "--psm", str(psm), "-c", "tessedit_create_hocr=1"], check=True, capture_output=True, env=env)


def ocr_leaf(leaf: int, scan: str = SCAN) -> Path:
    _, build = dirs(scan)
    hocr = build / "hocr" / f"leaf_{leaf:04d}.hocr"
    if hocr.exists():
        return hocr
    png = fetch_leaf(leaf, scan)
    part = build / "hocr" / f"leaf_{leaf:04d}.part"
    tesseract(png, part)
    os.replace(str(part) + ".hocr", hocr)
    return hocr


# --- reading the hOCR --------------------------------------------------------------------------

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


def layout(lines: list[dict]) -> float:
    """Mark each line's region: 'head' (running head), 'top' (the Greek text, marginal references and
    footnotes), 'left' or 'right' (the commentary columns). Returns the gutter's x."""
    if not lines:
        return 0.0
    x0 = min(l["bbox"][0] for l in lines)
    x1 = max(l["bbox"][2] for l in lines)
    width = x1 - x0
    # the gutter: the x in the middle fifth of the text block that the fewest lines cross
    xs = range(int(x0 + width * 0.4), int(x0 + width * 0.6), 4)
    cover = [(sum(1 for l in lines if l["bbox"][0] < x < l["bbox"][2]), abs(x - (x0 + x1) / 2), x) for x in xs]
    mid = min(cover)[2]
    top_y = min(l["bbox"][1] for l in lines)
    for l in lines:
        l["region"] = None
        if l["bbox"][1] < top_y + 80:
            l["region"] = "head"
    # going up from the bottom, the columns run until a line that crosses the gutter
    body = [l for l in lines if l["region"] is None]
    start = None
    for l in sorted(body, key=lambda l: -l["bbox"][1]):
        text = " ".join(w["text"] for w in l["words"])
        crosses = (l["bbox"][0] < mid - 15 and l["bbox"][2] > mid + 15 and len(text) > 6
                   and l["bbox"][2] - l["bbox"][0] > width * 0.15)
        if crosses:
            start = l["bbox"][3]
            break
    for l in body:
        if start is not None and l["bbox"][1] < start:
            l["region"] = "top"
        else:
            l["region"] = "left" if (l["bbox"][0] + l["bbox"][2]) / 2 < mid else "right"
    # footnotes to the Greek text in half-width lines above the commentary: a column's first lines
    # that begin with a footnote number and end in a gap wider than the commentary's line spacing
    for side in ("left", "right"):
        col = sorted((l for l in lines if l["region"] == side), key=lambda l: l["bbox"][1])
        if len(col) < 6:
            continue
        gaps = sorted(b["bbox"][1] - a["bbox"][3] for a, b in zip(col, col[1:]))
        typical = gaps[len(gaps) // 2]
        height = sorted(l["bbox"][3] - l["bbox"][1] for l in col)[len(col) // 2]
        first = col[0]["words"][0]["text"]
        other = [l["bbox"][1] for l in lines if l["region"] == ("right" if side == "left" else "left")]
        higher = bool(other) and col[0]["bbox"][1] < min(other) - height * 0.5
        if not (re.match(r"^[\d¹²³⁴⁵⁶⁷⁸⁹!ℵ]|^[Nℵ][A-Z]*$", first) or higher):
            continue
        for k in range(min(5, len(col) - 1)):
            if col[k + 1]["bbox"][1] - col[k]["bbox"][3] > typical + height * 0.6:
                for l in col[: k + 1]:
                    l["region"] = "top"
                break
    # a 'column' with fewer than three lines on a side is not the commentary (a footnote, a heading)
    for side in ("left", "right"):
        if sum(1 for l in lines if l["region"] == side) < 3:
            for l in lines:
                if l["region"] == side:
                    l["region"] = "top"
    return mid


# --- vocabularies ------------------------------------------------------------------------------

def accent_form(word: str) -> str:
    from .woodhouse_qa import accent_form as af
    return af(word.replace("ϑ", "θ").replace("ϐ", "β"))


def loose_form(word: str) -> str:
    from .greek import strip_diacritics
    return strip_diacritics(word.replace("ϑ", "θ").replace("ϐ", "β")).replace("ς", "σ")


def vocabularies() -> tuple[set[str], set[str], set[str]]:
    """(Greek letters only, Greek with accents, English lower case), cached in build/egt/vocab.pickle."""
    cache = PIPELINE / "build" / "egt" / "vocab.pickle"
    if cache.exists():
        return pickle.loads(cache.read_bytes())
    from .woodhouse_qa import english_vocabulary, greek_vocabulary
    sources = PIPELINE / "sources"
    loose, accented = greek_vocabulary(sources)
    nt = ROOT / "texts" / "newtestament" / "tokens.tsv"
    with open(nt, encoding="utf-8") as f:
        next(f)
        for row in f:
            form = row.split("\t")[2]
            loose.add(loose_form(form))
            accented.add(accent_form(form))
    english = english_vocabulary(sources)
    words = sources / "dictionaries" / "en_GB.words"
    english.update(w.strip().lower() for w in words.read_text(encoding="utf-8").split("\n") if w.strip())
    out = (loose, accented, english)
    cache.parent.mkdir(parents=True, exist_ok=True)
    cache.write_bytes(pickle.dumps(out))
    return out


# --- checking the words ------------------------------------------------------------------------

def _script(tok: str) -> str:
    g = any("Ͱ" <= c <= "Ͽ" or "ἀ" <= c <= "῿" for c in tok)
    l = any(c.isalpha() and ("a" <= c.lower() <= "z" or "À" <= c <= "ɏ") for c in tok)
    return "mixed" if g and l else "greek" if g else "latin" if l else "other"


def english_ok(tok: str, english: set[str], names: set[str]) -> bool:
    t = tok.replace("’", "'").strip("'")
    low = t.lower()
    if low in english or low in KNOWN or ROMAN.match(low) or t in names:
        return True
    if low.endswith("'s") and (low[:-2] in english or t[:-2] in names):
        return True
    if low.endswith("eth") and (low[:-3] in english or low[:-3] + "e" in english or low[:-4] in english):
        return True  # archaic verb forms: healeth, putteth
    return len(low) == 1 and low in "aiovs"


def token_problem(tok: str, voc, names: set[str]) -> str | None:
    loose, accented, english = voc
    tok = tok.strip(APOS) if _script(tok) == "latin" else tok
    if not tok or tok.isdigit():
        return None
    s = _script(tok)
    if s == "mixed":
        return "mixed"
    if s == "greek":
        if accent_form(tok) in accented or tok.endswith(("ʼ", "’", "᾽", "'")) and accent_form(tok[:-1]) in accented:
            return None
        return "accent" if loose_form(tok) in loose else "greek"
    if s == "latin" and not english_ok(tok, english, names):
        return "latin"
    return None


def rare_or_latin(tok: str, word: dict) -> str:
    """A Latin-letter word unknown to English: 'rare' when it looks like a name or a foreign word
    read with confidence, else 'latin'."""
    odd = re.search(r"[^\x00-\x7f’‘“”—–]|[@¢{}|#¥]|\d|[a-z][A-Z]|ii", tok)
    return "rare" if word["conf"] >= 85 and not odd else "latin"


def word_problems(text: str, prev: str, nxt: str, voc, names: set[str]) -> list[tuple[str, str]]:
    """(kind, token) for each suspect token of one OCR word."""
    out = []
    core = text.strip("“”‘’\"'()[],.;:!?—-")
    if core == "1" and (prev.endswith(("“", '"', "‘")) or text.startswith(("“", '"', "‘")) or nxt[:1].islower()):
        out.append(("digit", text))
    if re.search(r"\d[^\W\d_]|[^\W\d_]\d", text) and not re.search(r"\d(st|nd|rd|th)\b", text):
        out.append(("digit", text))
    for tok in TOKEN.findall(text):
        k = token_problem(tok, voc, names)
        if k:
            out.append((k, tok))
    return out


def regrc(images: list[Path], work: Path) -> list[str]:
    """Each word image read again with the Greek model alone, as a raw line (--psm 13; --psm 7
    returns nothing for some words), with one Tesseract run for all."""
    if not images:
        return []
    lst = work / "list.txt"
    lst.write_text("\n".join(str(p) for p in images) + "\n", encoding="utf-8")
    env = dict(os.environ, OMP_THREAD_LIMIT="1")
    out = subprocess.run(["tesseract", str(lst), "stdout", "--tessdata-dir", str(TESSDATA), "-l", "grc", "--psm", "13"],
                         capture_output=True, env=env, check=True).stdout.decode("utf-8")
    pages = out.split("\f")
    return [unicodedata.normalize("NFC", p.strip()) for p in pages[: len(images)]] + [""] * (len(images) - len(pages))


COMMON = set("""a an and are as at be but by for from he her his i if in is it its me my no not of on one or our she so
that the their them they this to us was we were which who will with you""".split())


def _letters(seg: str) -> int:
    return sum(1 for c in seg if c.isalpha())


def _known_greek(seg: str, accented: set[str], orig: str = "") -> bool:
    """The Greek model's reading is taken only when every word of it is a known Greek form with
    these accents, it has no word with two capitals, and about as many letters as the OCR read."""
    toks = [t for t in TOKEN.findall(seg) if not t.isdigit()]
    if not toks or len(toks) > 2:
        return False
    if any(sum(1 for c in t if c.isupper()) > 1 for t in toks):
        return False
    n, m = _letters(seg), _letters(orig)
    if n < 2 or m and not (0.6 <= n / m <= 1.6):
        return False
    return all(_script(t) == "greek" and (accent_form(t) in accented or accent_form(t.rstrip(APOS)) in accented)
               for t in toks)


def _strip_punct(seg: str) -> tuple[str, str, str]:
    m = re.match(r"^(\W*?)(\w.*?\w|\w)?(\W*)$", seg.strip(), re.S)
    return (m.group(1), m.group(2) or "", m.group(3)) if m else ("", seg.strip(), "")


def merge_greek(orig: str, alt: str, suspect, accented: set[str]) -> str | None:
    """The word with each suspect dash-separated part replaced by the Greek model's reading of it,
    where that reading is a known Greek form; None when nothing is replaced."""
    o_parts, a_parts = DASH.split(orig), DASH.split(alt)
    o_dashes = DASH.findall(orig)
    if len(o_parts) != len(a_parts):
        if len(o_parts) == 1 or not a_parts:
            return None
        # the Greek model often misses the dash before an English word: compare the last parts only
        a_parts = [""] * (len(o_parts) - 1) + [a_parts[-1]] if len(a_parts) < len(o_parts) else a_parts[-len(o_parts):]
    changed = False
    out = []
    for i, (o, a) in enumerate(zip(o_parts, a_parts)):
        # the part before a dash is the end of an English sentence: only a broken word is replaced
        if suspect(o, i == 0 and len(o_parts) > 1) and _known_greek(a, accented, o):
            lead, _, trail = _strip_punct(o)
            _, a_core, _ = _strip_punct(a)
            lead = "".join(c for c in lead if c in "“‘\"'([«")
            out.append(lead + a_core + trail)
            changed = True
        else:
            out.append(o)
    if not changed:
        return None
    res = out[0]
    for d, part in zip(o_dashes, out[1:]):
        res += d + part
    return res


def column_order(lines: list[dict]) -> list[int]:
    """The commentary's lines in reading order: the left column, then the right."""
    return [i for side in ("left", "right") for i, l in enumerate(lines) if l["region"] == side]


def analyse_leaf(leaf: int, voc, names: set[str], scan: str = SCAN) -> dict:
    from PIL import Image

    _, build = dirs(scan)
    lines = read_hocr(ocr_leaf(leaf, scan))
    mid = layout(lines)
    img = Image.open(build / "pages" / f"leaf_{leaf:04d}.png")
    order = column_order(lines)
    flags = check_words(lines, order, img, voc, names, leaf)
    page = {"leaf": leaf, "scan": scan, "mid": mid, "size": list(img.size), "lines": lines}
    (build / "lines" / f"leaf_{leaf:04d}.json").write_text(json.dumps(page, ensure_ascii=False), encoding="utf-8")
    text = []
    for side in ("left", "right"):
        text.append(f"## {side}")
        for li, l in enumerate(lines):
            if l["region"] == side:
                text.append(f"{li:03d}\t" + " ".join(w["text"] for w in l["words"]))
    (build / "text" / f"leaf_{leaf:04d}.txt").write_text("\n".join(text) + "\n", encoding="utf-8")
    return {"leaf": leaf, "flags": flags, "repaired": sum(1 for l in lines for w in l["words"] if w.get("repaired")),
            "words": sum(len(l["words"]) for l in lines if l["region"] in ("left", "right")),
            "lines": sum(1 for l in lines if l["region"] in ("left", "right"))}


def check_words(lines: list[dict], order: list[int], img, voc, names: set[str], leaf: int) -> list[dict]:
    """The words of the lines `order` (in reading order) checked: suspect words read again with
    the Greek model (a known Greek form replaces the OCR's word: w['repaired'], w['alt']), and
    each word's problems (w['flags']). Returns the flags, one per suspect token."""
    _, accented, english = voc
    for li in order:
        for w in lines[li]["words"]:
            w["ocr"] = w["text"]

    def suspect(seg: str, conf: int, near_greek: bool, before_dash: bool = False) -> bool:
        toks = TOKEN.findall(seg)
        latin = [t for t in toks if _script(t) == "latin"]
        # Latin letters are taken for misread Greek only when Tesseract doubted them, or when they
        # hold what English does not (é, @, ¢, digits, a capital inside the word: BéBAqra)
        odd = bool(re.search(r"[^\x00-\x7f’‘“”—–]|[@¢{}|]|\d|[a-z][A-Z]", seg))
        if latin and conf >= 80 and not odd:
            return False
        if any(token_problem(t, voc, names) for t in toks):
            return True
        if before_dash:
            return False
        # a short word in Latin letters, read with doubt, after a dash or beside Greek: τὸ read as ro
        return (bool(latin) and near_greek and all(len(t.strip(APOS)) <= 6 for t in latin)
                and not any(t.lower().strip(APOS) in COMMON | KNOWN or t in names for t in latin))

    # words divided at the end of a line: check the whole word
    joined: dict[tuple[int, int], str] = {}
    for a, b in zip(order, order[1:]):
        last, first = lines[a]["words"][-1], lines[b]["words"][0]
        if re.search(r"[^\W\d_]-$", last["text"]) and not last["text"].endswith("--"):
            m1 = TOKEN.findall(last["text"])
            m2 = TOKEN.findall(first["text"])
            if m1 and m2:
                whole = (m1[-1] + m2[0], m1[-1], m2[0])
                joined[(a, len(lines[a]["words"]) - 1)] = whole
                joined[(b, 0)] = whole

    # the words to read again with the Greek model
    todo = []
    for li in order:
        ws = lines[li]["words"]
        for wi, w in enumerate(ws):
            if (li, wi) in joined and (not token_problem(joined[(li, wi)][0], voc, names)
                                       or not token_problem(joined[(li, wi)][1], voc, names)
                                       and not token_problem(joined[(li, wi)][2], voc, names)):
                continue
            near = (any(_script(t) == "greek" for x in ws[max(0, wi - 1): wi + 2] if x is not w for t in TOKEN.findall(x["text"]))
                    or bool(DASH.search(w["text"])) or wi > 0 and ws[wi - 1]["text"].endswith(("—", "--")))
            parts = DASH.split(w["text"])
            if any(suspect(p, w["conf"], near, i == 0 and len(parts) > 1) for i, p in enumerate(parts)):
                todo.append((li, wi, near))
    with tempfile.TemporaryDirectory() as t:
        paths = []
        for k, (li, wi, _near) in enumerate(todo):
            x0, y0, x1, y1 = lines[li]["words"][wi]["bbox"]
            h = y1 - y0
            p = Path(t) / f"w{k:04d}.png"
            img.crop((max(0, x0 - h // 3), max(0, y0 - h // 3), x1 + h // 3, y1 + h // 3)).save(p)
            paths.append(p)
        again = regrc(paths, Path(t))
    for (li, wi, near), g in zip(todo, again):
        w = lines[li]["words"][wi]
        g = " ".join(g.split())
        if not g:
            continue
        w["alt"] = g
        merged = merge_greek(w["text"], g, lambda seg, bd: suspect(seg, w["conf"], near, bd), accented)
        if merged and merged != w["text"]:
            w["text"] = merged
            w["repaired"] = True

    flags = []
    for li in order:
        ws = lines[li]["words"]
        for wi, w in enumerate(ws):
            prev = ws[wi - 1]["text"] if wi else ""
            nxt = ws[wi + 1]["text"] if wi + 1 < len(ws) else ""
            probs = word_problems(w["text"], prev, nxt, voc, names)
            if (li, wi) in joined:
                whole, a_part, b_part = joined[(li, wi)]
                toks = TOKEN.findall(w["text"])
                piece = toks[-1] if wi == len(ws) - 1 and toks else toks[0] if toks else ""
                probs = [(k, t) for k, t in probs if t != piece]
                # a divided word, or a compound whose hyphen falls at the line end (self-defence)
                k = token_problem(whole, voc, names)
                if k and not (token_problem(a_part, voc, names) is None and token_problem(b_part, voc, names) is None):
                    probs.append((k, whole))
            probs = [(rare_or_latin(t, w) if k == "latin" else k, t) for k, t in probs]
            # a compound with a hyphen inside the line: both parts known
            if any(k in ("latin", "rare") for k, _ in probs) and "-" in w["text"].strip("-"):
                parts = [p for p in re.split(r"-", w["text"]) if TOKEN.findall(p)]
                if len(parts) > 1 and all(token_problem(TOKEN.findall(p)[0], voc, names) is None for p in parts):
                    probs = [(k, t) for k, t in probs if k not in ("latin", "rare")]
            letters = any(c.isalnum() for c in w["text"])
            if not probs and not w.get("repaired") and w["conf"] < (CONF_LIMIT if letters else 40):
                probs = [("conf", w["text"])]
            w["flags"] = sorted({k for k, _ in probs})
            for k, tok in probs:
                flags.append({"leaf": leaf, "line": li, "word": wi, "kind": k, "token": tok, "text": w["text"],
                              "alt": w.get("alt", ""), "conf": w["conf"]})
    return flags


def proper_names(leaf_list: list[int], voc, scan: str = SCAN) -> set[str]:
    """Capitalised Latin-letter words that the OCR read with confidence at least three times
    (the commentators' names: Weiss, Keim, Fritzsche)."""
    _, build = dirs(scan)
    _, _, english = voc
    seen: Counter[str] = Counter()
    for leaf in leaf_list:
        p = build / "hocr" / f"leaf_{leaf:04d}.hocr"
        if not p.exists():
            continue
        for l in read_hocr(p):
            for w in l["words"]:
                for tok in TOKEN.findall(w["text"]):
                    if tok[:1].isupper() and not tok.isupper() and _script(tok) == "latin" and w["conf"] >= 90 and tok.lower() not in english:
                        seen[tok] += 1
    return {t for t, n in seen.items() if n >= 3}


PROOF_HTML = r"""<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>EGT proof</title>
<style>
:root { --fix:#cfe3fb; --bg:#faf8f3; --fg:#1d1b18; --muted:#6b665d; --line:#ddd6c8; --mark:#ffe08a; --done:#e3f1e0; --card:#fff; --accent:#2f5d8a; }
@media (prefers-color-scheme: dark) { :root:not([data-theme="light"]) { --bg:#1b1a18; --fg:#ece8df; --muted:#a39d91; --line:#3a3731; --mark:#7a5d00; --done:#23361f; --card:#24221f; --accent:#8db6e0; --fix:#203a57; } }
body { margin:0; background:var(--bg); color:var(--fg); font:16px/1.45 "Gentium Plus","GFS Didot","Noto Serif",serif; }
header { position:sticky; top:0; z-index:2; background:var(--bg); border-bottom:1px solid var(--line); padding:8px 16px; display:flex; gap:12px; flex-wrap:wrap; align-items:center; }
header .stat { color:var(--muted); font-size:14px; }
button { font:inherit; font-size:14px; padding:4px 10px; border:1px solid var(--line); border-radius:6px; background:var(--card); color:var(--fg); cursor:pointer; }
main { max-width:1100px; margin:0 auto; padding:8px 16px 200px; }
h2 { font-size:17px; margin:28px 0 6px; color:var(--muted); font-weight:normal; }
.row { background:var(--card); border:1px solid var(--line); border-radius:8px; padding:8px 10px; margin:8px 0; }
.row.done { background:var(--done); }
.row img { display:block; max-width:100%; height:auto; background:#fff; border-radius:4px; }
.ocr { margin:4px 0; color:var(--muted); font-size:15px; }
.ocr mark { background:var(--mark); color:inherit; padding:0 2px; border-radius:3px; }
.ocr mark.fix { background:var(--fix); }
.edit { display:flex; gap:8px; align-items:center; }
.edit input { flex:1; font:inherit; font-size:18px; padding:4px 6px; border:1px solid var(--line); border-radius:4px; background:var(--bg); color:var(--fg); min-width:0; }
.meta { font-size:12px; color:var(--muted); }
.alt { font-size:13px; margin-top:3px; }
.alt button { font-size:13px; padding:1px 6px; }
.help { font-size:13px; color:var(--muted); max-width:1100px; margin:8px auto 0; padding:0 16px; }
</style></head><body>
<header><strong>Expositor's Greek Testament: proof</strong>
<span class="stat" id="stat"></span>
<button id="dl">Download corrections</button>
<button id="next">Next unchecked</button></header>
<p class="help">Each box shows a printed line from the scan, the OCR beneath it with the suspect words marked, and an editable copy.
Yellow marks a suspect word; blue marks a word the program has already replaced with the Greek model's reading (hover to see what the OCR had), which needs checking too.
Make the copy match the print, then press <b>Enter</b>: the line is marked as checked and the next one opens. A line that is already right: just press Enter.
Write Greek with accents and breathings as printed; keep the line's hyphen at the end if the print has one. Your work is kept in this browser as you go; <b>Download corrections</b> saves it as a file.
Pages marked <i>read every line</i> show all their lines, not only the flagged ones, so that we can count the errors the flags miss.</p>
<main id="main"></main>
<script>
const DATA = __DATA__;
const KEY = "egt-proof-" + DATA.id;
let state = {};
try { state = JSON.parse(localStorage.getItem(KEY) || "{}"); } catch (e) {}
function save() { try { localStorage.setItem(KEY, JSON.stringify(state)); } catch (e) {} stat(); }
function esc(s) { return s.replace(/&/g,"&amp;").replace(/</g,"&lt;").replace(/>/g,"&gt;"); }
const main = document.getElementById("main");
const rows = [];
for (const page of DATA.pages) {
  const h = document.createElement("h2");
  h.textContent = `Leaf ${page.leaf} (book page ${page.page})` + (page.full ? " — read every line" : "");
  main.appendChild(h);
  for (const ln of page.lines) {
    const id = page.leaf + ":" + ln.line;
    const div = document.createElement("div");
    div.className = "row";
    const ocrHtml = ln.words.map(w => w.flag ? `<mark title="${w.flag}">${esc(w.text)}</mark>`
      : w.fixed ? `<mark class="fix" title="OCR read ${esc(w.fixed)}; replaced by the Greek model's reading">${esc(w.text)}</mark>` : esc(w.text)).join(" ");
    const alts = ln.words.filter(w => w.alt).map(w => `<button data-from="${esc(w.text)}" data-to="${esc(w.alt)}">${esc(w.text)} → ${esc(w.alt)}</button>`).join(" ");
    div.innerHTML = `<img loading="lazy" src="${ln.img}" alt="">
      <div class="ocr">${ocrHtml}</div>
      <div class="edit"><input spellcheck="false" lang="grc"><button class="ok">✓</button></div>
      ${alts ? `<div class="alt">Greek model reads: ${alts}</div>` : ""}
      <div class="meta">${page.leaf} · ${ln.side} ${ln.line}${ln.flags ? " · " + ln.flags : ""}</div>`;
    const input = div.querySelector("input");
    const st = state[id];
    input.value = st ? st.text : ln.text;
    if (st && st.checked) div.classList.add("done");
    const confirm = () => {
      state[id] = { text: input.value, checked: true, ocr: ln.text, leaf: page.leaf, line: ln.line, full: page.full ? 1 : 0, flagged: ln.flags ? 1 : 0 };
      div.classList.add("done"); save();
      const i = rows.findIndex(r => r.id === id);
      for (let j = i + 1; j < rows.length; j++) { if (!rows[j].div.classList.contains("done")) { rows[j].input.focus(); rows[j].div.scrollIntoView({block:"center"}); break; } }
    };
    input.addEventListener("keydown", e => { if (e.key === "Enter") { e.preventDefault(); confirm(); } });
    input.addEventListener("input", () => { state[id] = Object.assign(state[id] || { ocr: ln.text, leaf: page.leaf, line: ln.line, full: page.full ? 1 : 0, flagged: ln.flags ? 1 : 0 }, { text: input.value }); save(); });
    div.querySelector(".ok").addEventListener("click", confirm);
    div.querySelectorAll(".alt button").forEach(b => b.addEventListener("click", () => { input.value = input.value.replace(b.dataset.from, b.dataset.to); input.focus(); }));
    main.appendChild(div);
    rows.push({ id, div, input });
  }
}
function stat() {
  const done = rows.filter(r => r.div.classList.contains("done")).length;
  document.getElementById("stat").textContent = `${done} of ${rows.length} lines checked`;
}
stat();
document.getElementById("next").addEventListener("click", () => { const r = rows.find(r => !r.div.classList.contains("done")); if (r) { r.input.focus(); r.div.scrollIntoView({block:"center"}); } });
document.getElementById("dl").addEventListener("click", () => {
  const head = "leaf\tline\tfull\tflagged\tchecked\tocr\ttext\n";
  const body = Object.values(state).map(s => [s.leaf, s.line, s.full, s.flagged, s.checked ? 1 : 0, s.ocr, s.text].join("\t")).join("\n");
  const a = document.createElement("a");
  a.href = URL.createObjectURL(new Blob([head + body + "\n"], { type: "text/tab-separated-values" }));
  a.download = "egt-proof-" + DATA.id + ".tsv"; a.click();
});
</script></body></html>
"""


def proof(leaf_list: list[int], full: set[int], name: str, scan: str = SCAN) -> Path:
    """build/egt/<scan>/proof-<name>/index.html: the flagged lines (every line of the leaves in
    `full`) with the printed line cut from the scan, for checking in a browser."""
    from PIL import Image

    _, build = dirs(scan)
    out = build / f"proof-{name}"
    (out / "img").mkdir(parents=True, exist_ok=True)
    pages = []
    for leaf in leaf_list:
        page = json.loads((build / "lines" / f"leaf_{leaf:04d}.json").read_text(encoding="utf-8"))
        img = Image.open(build / "pages" / f"leaf_{leaf:04d}.png")
        head = " ".join(w["text"] for l in page["lines"] if l["region"] == "head" for w in l["words"])
        num = next((t for t in re.findall(r"\b\d{1,3}\b", head)), "")
        rows = []
        for side in ("left", "right"):
            col = [(li, l) for li, l in enumerate(page["lines"]) if l["region"] == side]
            for li, l in col:
                flagged = [w for w in l["words"] if w.get("flags")]
                repaired = [w for w in l["words"] if w.get("repaired")]
                if not flagged and not repaired and leaf not in full:
                    continue
                x0, y0, x1, y1 = l["bbox"]
                h = y1 - y0
                crop = img.crop((max(0, x0 - 20), max(0, y0 - h // 2), min(img.width, x1 + 20), min(img.height, y1 + h // 2)))
                crop = crop.resize((crop.width * 6 // 10, crop.height * 6 // 10), Image.LANCZOS)
                fn = f"img/{leaf:04d}-{li:03d}.png"
                crop.save(out / fn, optimize=True)
                rows.append({"line": li, "side": side, "img": fn, "text": " ".join(w["text"] for w in l["words"]),
                             "flags": ", ".join(sorted({k for w in flagged for k in w["flags"]} | ({"repaired"} if repaired else set()))),
                             "words": [{"text": w["text"], "flag": ", ".join(w.get("flags", [])),
                                        "fixed": w["ocr"] if w.get("repaired") else "", "alt": w.get("alt", "")
                                        if w.get("alt") and w.get("alt") != w["text"] and w.get("flags") else ""}
                                       for w in l["words"]]})
        pages.append({"leaf": leaf, "page": num, "full": leaf in full, "lines": rows})
    data = {"id": f"{scan}-{name}", "pages": pages}
    (out / "index.html").write_text(PROOF_HTML.replace("__DATA__", json.dumps(data, ensure_ascii=False)), encoding="utf-8")
    return out / "index.html"


def _align(ocr: list[str], text: list[str]) -> list[tuple[list[int], str]]:
    """For each changed stretch of the OCR line: (indexes of the OCR words, what the proof has)."""
    import difflib

    out = []
    for op, i1, i2, j1, j2 in difflib.SequenceMatcher(a=ocr, b=text, autojunk=False).get_opcodes():
        if op == "equal":
            continue
        if op == "replace" and i2 - i1 == j2 - j1:
            out += [([i], text[j]) for i, j in zip(range(i1, i2), range(j1, j2))]
        else:
            out.append((list(range(i1, i2)) or [max(0, i1 - 1)], " ".join(text[j1:j2])))
    return out


def evaluate(proof_tsv: Path, scan: str = SCAN) -> str:
    """The pilot's numbers from the proof's corrections: errors per page, how many the flags
    caught, how good the repairs were, and how the models' text-only corrections compare."""
    import csv

    _, build = dirs(scan)
    rows = list(csv.DictReader(open(proof_tsv, encoding="utf-8"), delimiter="\t"))
    checked = {(int(r["leaf"]), int(r["line"])): r for r in rows if r["checked"] == "1"}
    pages: dict[int, dict] = {}
    truth: dict[str, str] = {}  # leaf:line:word -> the word as the proof has it
    stats: Counter[str] = Counter()
    kinds: Counter[str] = Counter()
    kinds_err: Counter[str] = Counter()
    conf_err: list[tuple[int, bool]] = []
    for (leaf, li), r in checked.items():
        if leaf not in pages:
            pages[leaf] = json.loads((build / "lines" / f"leaf_{leaf:04d}.json").read_text(encoding="utf-8"))
        words = pages[leaf]["lines"][li]["words"]
        ocr = [w["text"] for w in words]
        changes = _align(ocr, r["text"].split())
        changed = {i for idx, _ in changes for i in idx}
        for idx, new in changes:
            for i in idx:
                truth[f"{leaf}:{li}:{i}"] = new if len(idx) == 1 else new + " (joined)"
        for i, w in enumerate(words):
            key = f"{leaf}:{li}:{i}"
            truth.setdefault(key, w["text"])
            err = i in changed
            marked = bool(w.get("flags")) or bool(w.get("repaired"))
            for k in w.get("flags", []):
                kinds[k] += 1
                kinds_err[k] += err
            if w.get("repaired"):
                stats["repaired"] += 1
                stats["repaired_right"] += not err
            if r["full"] == "1":
                stats["full_words"] += 1
                stats["full_errors"] += err
                stats["full_errors_marked"] += err and marked
                conf_err.append((w["conf"], err))
                if err and not marked:
                    stats["missed"] += 1
                    print(f"missed  {leaf}:{li}  {w['text']!r} -> {dict(changes).get(i, '?') if False else next(n for idx, n in changes if i in idx)!r}  (conf {w['conf']})")
    out = [f"lines checked: {len(checked)}",
           f"repairs right: {stats['repaired_right']} of {stats['repaired']}"]
    out.append("flags by kind (real errors / flags): " + ", ".join(f"{k} {kinds_err[k]}/{n}" for k, n in kinds.most_common()))
    if stats["full_words"]:
        out.append(f"read-every-line pages: {stats['full_words']} words, {stats['full_errors']} errors, "
                   f"{stats['full_errors_marked']} of them flagged or repaired, {stats['missed']} missed")
        for lim in (50, 65, 75, 85, 90):
            caught = sum(1 for c, e in conf_err if e and c < lim)
            flagged = sum(1 for c, _ in conf_err if c < lim)
            out.append(f"  confidence below {lim}: {flagged} words, {caught} of the errors")
    mc = build / "modelcheck"
    for model in ("opus", "fable"):
        f = mc / f"{model}.tsv"
        if not f.exists():
            continue
        score: Counter[str] = Counter()
        for r in csv.DictReader(open(f, encoding="utf-8"), delimiter="\t"):
            if r["id"] not in truth:
                continue
            right = unicodedata.normalize("NFC", (r.get("text") or "").strip()) == unicodedata.normalize("NFC", truth[r["id"]])
            score[f"{r['verdict']} {'right' if right else 'wrong'}"] += 1
        out.append(f"{model}: " + ", ".join(f"{k} {v}" for k, v in sorted(score.items())))
    return "\n".join(out)


def main(argv: list[str]) -> None:
    step, spec = argv[0], argv[1]
    todo = leaves(spec) if step != "evaluate" else []
    if step == "fetch":
        with ThreadPoolExecutor(max_workers=4) as pool:
            for p in pool.map(fetch_leaf, todo):
                print(p.name, file=sys.stderr)
    elif step == "ocr":
        workers = int(os.environ.get("EGT_WORKERS", "4"))
        with ThreadPoolExecutor(max_workers=workers) as pool:
            for p in pool.map(ocr_leaf, todo):
                print(p.name, file=sys.stderr)
    elif step == "analyse":
        voc = vocabularies()
        names = proper_names(todo, voc)
        _, build = dirs()
        results = []
        with ThreadPoolExecutor(max_workers=int(os.environ.get("EGT_WORKERS", "4"))) as pool:
            for r in pool.map(lambda leaf: analyse_leaf(leaf, voc, names), todo):
                results.append(r)
                print(f"leaf {r['leaf']}: {r['lines']} lines, {r['words']} words, {r['repaired']} repaired, "
                      f"{len(r['flags'])} flags", file=sys.stderr)
        kinds: Counter[str] = Counter()
        with open(build / "flags.tsv", "w", encoding="utf-8") as f:
            f.write("leaf\tline\tword\tkind\ttoken\ttext\talt\tconf\n")
            for r in sorted(results, key=lambda r: r["leaf"]):
                for fl in r["flags"]:
                    kinds[fl["kind"]] += 1
                    f.write("\t".join(str(fl[k]) for k in ("leaf", "line", "word", "kind", "token", "text", "alt", "conf")) + "\n")
        total_words = sum(r["words"] for r in results)
        print(f"{len(results)} leaves, {total_words} words, {sum(r['repaired'] for r in results)} repaired, "
              f"{sum(kinds.values())} flags: " + ", ".join(f"{k} {v}" for k, v in kinds.most_common()), file=sys.stderr)
        print(f"names taken as known: {', '.join(sorted(names))}", file=sys.stderr)
    elif step == "evaluate":
        print(evaluate(Path(spec)))
    elif step == "proof":
        full = set(leaves(argv[2])) if len(argv) > 2 and argv[2] else set()
        name = argv[3] if len(argv) > 3 else "pilot"
        print(proof(todo, full, name))
    else:
        raise SystemExit(f"unknown step {step}")


if __name__ == "__main__":
    main(sys.argv[1:])
