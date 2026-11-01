"""The plays' English pages by OCR: the editors' notes and introductions, and Starkie's
translation of the Clouds (pipeline/PLAN-drama.md, steps 6-7), by the route of the Expositor's
Greek Testament (egt_ocr.py): Tesseract with the English and Greek models, Greek words read again
with the Greek model, and every word the OCR doubts flagged for an agent to check against a crop.

    python -m anagnosis_pipeline drama-prose <play> notes|intro|trans fetch|ocr|draft

The draft of each page is written into the batch files pipeline/transcriptions/drama/<play>/
notes-NN.md, intro-NN.md or trans-NN.md (eight pages each; a file that exists is never
overwritten) as a block

    === p-0250
    ## 779
    **ὁ δῆμος**: as if there was an ἐκκλησία in Hades.
    --- flags
    1 ἐκκλησία [greek] →
    --- notes

and the crops under pipeline/build/drama-prose/<play>/: p-0250-flags.png (the lines that hold a
flagged word, numbered, the word boxed), p-0250-col-l.png and -col-r.png (the columns; one
column: -col-l.png only). merge_kind() and merge_translation() read the checked batches for
drama.merge_play.
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
from .drama import PLAYS, Play, bold_lemma, note_heading
from .drama_pages import fetch_leaf, route_dir, scan_dirs

ROOT = Path(__file__).resolve().parent.parent.parent
PIPELINE = ROOT / "pipeline"
PAGES_PER_BATCH = 8
KINDS = ("notes", "intro", "trans")


# --- fetch and OCR -----------------------------------------------------------------------------

def ocr_leaf(scan: str, leaf: int) -> Path:
    from .egt_ocr import tesseract

    _, build = scan_dirs(scan)
    hocr = build / "hocr" / f"leaf_{leaf:04d}.eng.hocr"
    if hocr.exists():
        return hocr
    png = fetch_leaf(scan, leaf)
    part = build / "hocr" / f"leaf_{leaf:04d}.eng.part"
    tesseract(png, part, "eng+grc", 3)
    os.replace(str(part) + ".hocr", hocr)
    return hocr


def run(slug: str, kind: str, step: str, workers: int = 4) -> None:
    play = PLAYS[slug]
    leaves = play.visible(kind)
    if not leaves:
        raise SystemExit(f"{slug}: no {kind} leaves in drama.PLAYS yet (step 2)")
    scan = play.scan_for(kind)
    route_dir("drama-prose", slug, scan)
    if step == "fetch":
        with ThreadPoolExecutor(workers) as ex:
            list(ex.map(lambda l: fetch_leaf(scan, l), leaves))
    elif step == "ocr":
        with ThreadPoolExecutor(workers) as ex:
            list(ex.map(lambda l: ocr_leaf(scan, l), leaves))
    elif step == "draft":
        index = write_draft(slug, kind)
        print(f"{slug} {kind}: {len(index)} pages, {sum(p['flags'] for p in index)} flags")
        return
    else:
        raise SystemExit(f"unknown step {step!r}")
    print(f"{slug} {kind}: {step} done for {len(leaves)} leaves")


# --- the page --------------------------------------------------------------------------------

def _region(play: Play, kind: str, leaf: int, lines: list[dict], size: tuple[int, int]) -> tuple[list[dict], float]:
    """The lines of the page that hold the notes (introduction, translation), each marked with its
    column ('left', 'right' or 'one'), without the running head, page number and signature, in
    reading order. Returns them and the gutter's x (0 for one column)."""
    from .drama_pages import _rule_below

    W, H = size
    body = [l for l in lines if l["bbox"][3] > 0.065 * H]
    # the running head (NOTES. LINES 412-450. / AGAMEMNON. / INTRODUCTION.) a little lower down
    body = [l for l in body if not (l["bbox"][1] < 0.1 * H and len(l["words"]) <= 5
                                    and _capitals(" ".join(w["text"] for w in l["words"])))]
    # a page number or signature alone at the foot
    body = [l for l in body if not (l["bbox"][1] > 0.88 * H and len(l["words"]) <= 2
                                    and len(" ".join(w["text"] for w in l["words"])) <= 7
                                    and re.search(r"\d", " ".join(w["text"] for w in l["words"])))]
    top = 0
    if play.layout == "jebb" and kind in ("notes", "trans"):
        from .drama_pages import rules as _rules

        png = scan_dirs(play.scan_for(kind))[1] / "pages" / f"leaf_{leaf:04d}.png"
        found = _rules(png, int(0.1 * H))
        if kind == "notes":
            top = (found[-1] + 5) if found else 0  # the commentary: under the last rule
        else:
            body = [l for l in body if not found or l["bbox"][3] < found[0]]  # the translation: above the first
    body = [l for l in body if l["bbox"][1] >= top]
    if not body:
        return [], 0
    x0 = min(l["bbox"][0] for l in body)
    x1 = max(l["bbox"][2] for l in body)
    width = x1 - x0
    xs = range(int(x0 + width * 0.4), int(x0 + width * 0.6), 4)
    cover = [(sum(1 for l in body if l["bbox"][0] < x < l["bbox"][2]), abs(x - (x0 + x1) / 2), x) for x in xs]
    best = min(cover) if cover else (len(body), 0, 0)
    two = best[0] <= max(1, len(body) // 12) and len(body) >= 8
    mid = best[2] if two else 0
    for l in body:
        l["region"] = ("left" if (l["bbox"][0] + l["bbox"][2]) / 2 < mid else "right") if two else "one"
    order = sorted(body, key=lambda l: ({"left": 0, "one": 0, "right": 1}[l["region"]], l["bbox"][1]))
    return order, mid


def _join_lines(texts: list[str]) -> str:
    """Printed lines joined into running text; a word divided at a line's end written whole."""
    out = ""
    for t in texts:
        t = t.strip()
        if not t:
            continue
        if out.endswith("-") and re.search(r"[^\W\d_]-$", out) and re.match(r"[^\W\d_]", t) and t[:1].islower():
            out = out[:-1] + t
        elif out:
            out += " " + t
        else:
            out = t
    return out


SMALL_WORDS = {"a", "an", "and", "as", "at", "but", "by", "for", "from", "in", "into", "of", "on", "or", "the", "to", "with"}


def title_case(text: str) -> str:
    """A heading printed in capitals, as ordinary capitals and small letters: THE STORY AND THE
    PLOT OF THE AGAMEMNON -> The Story and the Plot of the Agamemnon."""
    out = []
    for k, w in enumerate(text.strip(" .,").split()):
        core = w.strip("().,;:—-")
        if re.fullmatch(r"[IVXLC]+", core) and len(core) <= 5 and k > 0:
            out.append(w)
        elif k > 0 and core.lower() in SMALL_WORDS:
            out.append(w.lower())
        else:
            out.append(w[:1].upper() + w[1:].lower())
    return " ".join(out)


def _capitals(text: str) -> bool:
    letters = [c for c in text if c.isalpha()]
    return len(letters) >= 4 and sum(c.isupper() for c in letters) >= 0.8 * len(letters)


def _reread_strip(scan: str, leaf: int, box: tuple[int, int, int, int]) -> list[dict]:
    """The lines Tesseract (eng+grc) finds in a part of the page read on its own (cached)."""
    import tempfile

    from .drama_pages import read_lines
    from .egt_ocr import tesseract

    _, sbuild = scan_dirs(scan)
    x0, y0, x1, y1 = box
    cache = sbuild / "hocr" / f"leaf_{leaf:04d}.eng-strip-{x0}-{y0}-{x1}-{y1}.hocr"
    if not cache.exists():
        from PIL import Image

        with Image.open(sbuild / "pages" / f"leaf_{leaf:04d}.png") as im, tempfile.TemporaryDirectory() as t:
            im.crop(box).save(Path(t) / "s.png")
            tesseract(Path(t) / "s.png", Path(t) / "s", "eng+grc", 6)
            cache.write_text((Path(t) / "s.hocr").read_text(encoding="utf-8"), encoding="utf-8")
    out = []
    for l in read_lines(cache):
        for w in l["words"]:
            w["bbox"] = [w["bbox"][0] + x0, w["bbox"][1] + y0, w["bbox"][2] + x0, w["bbox"][3] + y0]
        l["bbox"] = [l["bbox"][0] + x0, l["bbox"][1] + y0, l["bbox"][2] + x0, l["bbox"][3] + y0]
        out.append(l)
    return out


def analyse_page(play: Play, kind: str, leaf: int, voc, names: set[str]) -> dict:
    """The page's text in Markdown with the flagged words, and the data for its crops."""
    from PIL import Image

    from .drama_pages import read_lines
    from .egt_ocr import check_words

    scan = play.scan_for(kind)
    _, sbuild = scan_dirs(scan)
    img = Image.open(sbuild / "pages" / f"leaf_{leaf:04d}.png").convert("L")
    lines = read_lines(ocr_leaf(scan, leaf))
    order, mid = _region(play, kind, leaf, lines, img.size)
    cols: dict[str, list[dict]] = {}
    for l in order:
        cols.setdefault(l["region"], []).append(l)
    # a printed line Tesseract skipped: where two lines of a column stand a line too far apart,
    # the strip between them is read again on its own
    for region, col in cols.items():
        if len(col) < 4:
            continue
        tops = [l["bbox"][1] for l in col]
        pitch = sorted(b - a for a, b in zip(tops, tops[1:]))[len(tops) // 2]
        h = sorted(l["bbox"][3] - l["bbox"][1] for l in col)[len(col) // 2]
        x0 = min(l["bbox"][0] for l in col) - 10
        x1 = max(l["bbox"][2] for l in col) + 10
        extra = []
        for a, b in zip(col, col[1:]):
            if b["bbox"][1] - a["bbox"][1] > 1.75 * pitch:
                near = {w["text"] for w in a["words"] + b["words"]}
                strip = (max(0, x0), a["bbox"][1] + int(0.7 * pitch), min(img.width, x1), b["bbox"][1] + int(0.25 * pitch))
                for l in _reread_strip(scan, leaf, strip):
                    sure = [w for w in l["words"] if w["conf"] >= 60 and len(w["text"]) >= 3]
                    if len(sure) >= 2 and sum(1 for w in sure if w["text"] in near) < 0.5 * len(sure):
                        l["region"] = region
                        l["reread"] = True
                        extra.append(l)
        if extra:
            lines.extend(extra)
            col.extend(extra)
            col.sort(key=lambda l: l["bbox"][1])
    order = [l for region in cols for l in cols[region]]
    # footnotes: lines in smaller type at the foot of the column, after a gap
    foot: dict[str, list[dict]] = {}
    for region, col in cols.items():
        sizes = sorted(l["x_size"] for l in col if l["x_size"])
        if len(col) < 6 or not sizes:
            continue
        xs = sizes[len(sizes) // 2]
        h = sorted(l["bbox"][3] - l["bbox"][1] for l in col)[len(col) // 2]
        k = len(col)
        while k > 0 and col[k - 1]["x_size"] and col[k - 1]["x_size"] <= 0.85 * xs:
            k -= 1
        if 0 < k < len(col) and col[k]["bbox"][1] - col[k - 1]["bbox"][3] > 0.35 * h:
            foot[region] = col[k:]
            cols[region] = col[:k]
            continue
        # or after a wider gap than the lines', beginning with a note's mark, in the lower part
        gaps = sorted(b["bbox"][1] - a["bbox"][3] for a, b in zip(col, col[1:]))
        usual = gaps[len(gaps) // 2] if gaps else 0
        for k in range(len(col) - 1, max(0, len(col) - 8), -1):
            first = " ".join(w["text"] for w in col[k]["words"])
            if (col[k]["bbox"][1] > 0.6 * img.height and col[k]["bbox"][1] - col[k - 1]["bbox"][3] > usual + 0.5 * h
                    and re.match(r"^[\d¹²³⁴⁵⁶⁷⁸⁹*†‡!]{1,2}\s", first)):
                foot[region] = col[k:]
                cols[region] = col[:k]
                break
    idx = [lines.index(l) for l in order]
    flags = check_words(lines, idx, img, voc, names, leaf)
    # paragraphs: a line indented by about an em, a centred line, a line in capitals, or a line
    # beginning with a note's number begins one; so does a line after a short line that ends a
    # sentence
    paras: list[dict] = []
    for region, col in cols.items():
        lefts = sorted(l["bbox"][0] for l in col)
        left = lefts[len(lefts) // 5] if lefts else 0
        rights = sorted(l["bbox"][2] for l in col)
        right = rights[int(len(rights) * 0.8)] if rights else 0
        h = sorted(l["bbox"][3] - l["bbox"][1] for l in col)[len(col) // 2] if col else 30
        prev = None
        for l in col:
            text = " ".join(w["text"] for w in l["words"])
            indent = l["bbox"][0] - left
            centred = (abs((l["bbox"][0] + l["bbox"][2]) / 2 - (left + right) / 2) < 2 * h
                       and (l["bbox"][2] - l["bbox"][0]) < 0.6 * (right - left))
            caps = _capitals(text) and len(text) < 90
            numbered = kind == "notes" and note_heading(text, play.note_start) is not None
            short_end = prev is not None and prev["bbox"][2] < right - 3 * h and re.search(r"[.?!:]['’”)]?$", prev["text"])
            new = (prev is None or indent > 0.8 * h or centred or caps or numbered or bool(short_end)
                   or (prev is not None and prev["caps"]))
            entry = {"text": text, "bbox": l["bbox"], "centred": centred, "caps": caps}
            if new or not paras:
                paras.append({"lines": [entry], "region": region, "indent": indent > 0.8 * h})
            else:
                paras[-1]["lines"].append(entry)
            prev = entry
        for l in foot.get(region, []):
            text = " ".join(w["text"] for w in l["words"])
            if paras and paras[-1].get("foot") and not re.match(r"^[\d¹²³⁴⁵⁶⁷⁸⁹*†‡!]", text):
                paras[-1]["lines"].append({"text": text})
            else:
                paras.append({"lines": [{"text": text}], "region": region, "indent": False, "foot": True})
    md: list[str] = []
    for k, p in enumerate(paras):
        text = _join_lines([x["text"] for x in p["lines"]])
        if p.get("foot"):
            md.append(f"[Note: {text}]")
            md.append("")
            continue
        heading = len(p["lines"]) == 1 and (p["lines"][0]["caps"] or (p["lines"][0]["centred"] and len(text) < 80))
        if kind == "notes":
            h = note_heading(text, play.note_start)
            if h:
                n, end = h
                md.append(f"## {n}")
                body = bold_lemma(text[end:].strip())
                if body:
                    md.append(body)
                md.append("")
                continue
            if k == 0 and not p["indent"]:
                text = "+ " + text  # the note runs on from the page before
        elif kind == "intro":
            m = re.match(r"^§\s*(\d+)\.?\s*(.*)$", text)
            if m:
                md.append(f"## § {m.group(1)}")
                md.append("")
                text = m.group(2)
                if not text:
                    continue
            elif heading:
                md.append("# " + (title_case(text) if _capitals(text) else text.strip(" .")))
                md.append("")
                continue
            elif k == 0 and not p["indent"]:
                text = "+ " + text
        elif kind == "trans":
            m = re.match(r"^([A-Z][A-Za-z]+(?:\s[A-Z][A-Za-z]+)?)\.\s+(.*)$", text)
            if m:
                md.append(f"@ {m.group(1).title()}")
                text = "N\t" + m.group(2)
            elif heading:
                continue  # AGON II, ODE: the Greek text carries the sections
            elif k == 0 and not p["indent"]:
                text = "+ " + text
        md.append(text)
        md.append("")
    return {"leaf": leaf, "md": "\n".join(md).strip(), "flags": flags, "lines": lines, "mid": mid,
            "order": idx, "size": list(img.size)}


def _crops(play: Play, kind: str, page: dict, out_dir: Path, stem: str) -> None:
    """p-NNNN-flags.png: each line with a flagged word, numbered, the word boxed; the columns."""
    from PIL import Image, ImageDraw, ImageFont

    _, sbuild = scan_dirs(play.scan_for(kind))
    img = Image.open(sbuild / "pages" / f"leaf_{page['leaf']:04d}.png").convert("L")
    lines = page["lines"]
    try:
        font = ImageFont.truetype("DejaVuSans-Bold.ttf", 30)
    except OSError:
        font = ImageFont.load_default()
    by_line: dict[int, list[tuple[int, dict]]] = {}
    for k, f in enumerate(page["flags"], 1):
        by_line.setdefault(f["line"], []).append((k, f))
    crops = []
    for li in sorted(by_line, key=lambda li: page["order"].index(li) if li in page["order"] else li):
        x0, y0, x1, y1 = lines[li]["bbox"]
        h = y1 - y0
        cx, cy = max(0, x0 - 20), max(0, y0 - h // 2)
        c = img.crop((cx, cy, min(img.width, x1 + 20), min(img.height, y1 + h // 2))).convert("RGB")
        d = ImageDraw.Draw(c)
        for k, f in by_line[li]:
            w = lines[li]["words"][f["word"]]
            d.rectangle([w["bbox"][0] - cx - 3, w["bbox"][1] - cy - 3, w["bbox"][2] - cx + 3, w["bbox"][3] - cy + 3],
                        outline=(220, 0, 0), width=3)
        crops.append((",".join(str(k) for k, _f in by_line[li]), c))
    if crops:
        label_w = 130
        sheet = Image.new("RGB", (label_w + max(c.width for _n, c in crops), sum(c.height + 8 for _n, c in crops)), (255, 255, 255))
        dr = ImageDraw.Draw(sheet)
        y = 0
        for n, c in crops:
            sheet.paste(c, (label_w, y))
            dr.text((6, y + c.height // 2 - 16), n, fill=(0, 0, 0), font=font)
            dr.line((0, y + c.height + 3, sheet.width, y + c.height + 3), fill=(170, 170, 170), width=2)
            y += c.height + 8
        sheet.save(out_dir / f"{stem}-flags.png", optimize=True)
    regions: dict[str, list[list[int]]] = {}
    for li in page["order"]:
        regions.setdefault(lines[li].get("region", "one"), []).append(lines[li]["bbox"])
    for region, boxes in regions.items():
        x0 = min(b[0] for b in boxes) - 15
        y0 = min(b[1] for b in boxes) - 15
        x1 = max(b[2] for b in boxes) + 15
        y1 = max(b[3] for b in boxes) + 15
        c = img.crop((max(0, x0), max(0, y0), min(img.width, x1), min(img.height, y1)))
        if region != "one":
            c = c.resize((int(c.width * 1.4), int(c.height * 1.4)), Image.LANCZOS)
        c.save(out_dir / f"{stem}-col-{'r' if region == 'right' else 'l'}.png", optimize=True)


def write_draft(slug: str, kind: str) -> list[dict]:
    from .egt_ocr import FLAG_KINDS, vocabularies

    play = PLAYS[slug]
    scan = play.scan_for(kind)
    out_dir = route_dir("drama-prose", slug, scan)
    leaves = play.visible(kind)
    voc = vocabularies()
    names = _names(scan, leaves, voc)
    with ThreadPoolExecutor(int(os.environ.get("DRAMA_WORKERS", "4"))) as ex:
        pages = list(ex.map(lambda l: analyse_page(play, kind, l, voc, names), leaves))
    index = []
    trans_starts = _greek_speech_starts(slug) if kind == "trans" else {}
    for b, page in enumerate(pages):
        stem = f"p-{page['leaf']:04d}"
        _crops(play, kind, page, out_dir, stem)
        if kind == "trans":
            page["md"] = _number_speeches(page["md"], trans_starts.get(page["leaf"] - 1, []), play)
        index.append({"stem": stem, "leaf": page["leaf"], "batch": b // PAGES_PER_BATCH + 1, "flags": len(page["flags"])})
    (out_dir / f"{kind}.json").write_text(json.dumps(index, indent=1), encoding="utf-8")
    tdir = PIPELINE / "transcriptions" / "drama" / slug
    tdir.mkdir(parents=True, exist_ok=True)
    for b in range(0, len(pages), PAGES_PER_BATCH):
        path = tdir / f"{kind}-{b // PAGES_PER_BATCH + 1:02d}.md"
        if path.exists():
            continue
        out = []
        for page in pages[b : b + PAGES_PER_BATCH]:
            out.append(f"=== p-{page['leaf']:04d}")
            out.append(page["md"])
            out.append("--- flags")
            for k, f in enumerate(page["flags"], 1):
                alt = f" (Greek model: {f['alt']})" if f.get("alt") and f["alt"] != f["text"] else ""
                out.append(f"{k} {f['token']} [{f['kind']}]{alt} →")
            out.append("--- notes")
            out.append("")
        path.write_text("\n".join(out), encoding="utf-8")
    (out_dir / "FLAG_KINDS.md").write_text("\n".join(f"* **{k}**: {v}" for k, v in FLAG_KINDS.items()) + "\n", encoding="utf-8")
    return index


def _names(scan: str, leaves: list[int], voc) -> set[str]:
    """Capitalised words in Latin letters that the OCR read with confidence at least three times
    (the scholars' names: Hermann, Wecklein, Paley), taken as known."""
    from collections import Counter

    from .egt_ocr import TOKEN, _script
    from .gorgias_pages import read_hocr

    _, sbuild = scan_dirs(scan)
    _, _, english = voc
    seen: Counter[str] = Counter()
    for leaf in leaves:
        p = sbuild / "hocr" / f"leaf_{leaf:04d}.eng.hocr"
        if not p.exists():
            continue
        for l in read_hocr(p):
            for w in l["words"]:
                for tok in TOKEN.findall(w["text"]):
                    if tok[:1].isupper() and not tok.isupper() and _script(tok) == "latin" and w["conf"] >= 90 and tok.lower() not in english:
                        seen[tok] += 1
    return {t for t, n in seen.items() if n >= 3}


# --- Starkie's translation ---------------------------------------------------------------------

def _greek_speech_starts(slug: str) -> dict[int, list[tuple[str, str]]]:
    """From the text draft: for each Greek page (leaf), the speeches that begin on it: (line, speaker)."""
    path = PIPELINE / "build" / "drama-pages" / slug / "draft.json"
    if not path.exists():
        return {}
    out: dict[int, list[tuple[str, str]]] = {}
    for v in json.loads(path.read_text(encoding="utf-8")):
        if v.get("speaker"):
            out.setdefault(v["leaf"], []).append((v["n"], v["speaker"]))
    return out


def _number_speeches(md: str, starts: list[tuple[str, str]], play: Play) -> str:
    """Each speech of a translation page (`@ Name` then `N<TAB>…`) given the line of the k-th
    speech that begins on the facing Greek page, and the Greek speaker's English name."""
    english = {v: k.title() for k, v in play.speakers.items()}
    out = []
    k = 0
    pending = None
    for line in md.split("\n"):
        if line.startswith("@ "):
            pending = line
            continue
        if line.startswith("N\t"):
            if k < len(starts):
                n, sp = starts[k]
                out.append(f"@ {english.get(sp, pending[2:] if pending else sp)}")
                out.append(f"{n}\t{line[2:]}")
            else:
                out.append(pending or "@ ?")
                out.append(f"?\t{line[2:]}")
            k += 1
            pending = None
            continue
        out.append(line)
    return "\n".join(out)


# --- reading the checked batches ----------------------------------------------------------------

def read_prose_batches(directory: Path, kind: str, files: list[Path] | None = None) -> dict[str, dict]:
    """Page blocks: {'md': [lines], 'flags': [lines], 'notes': [lines], 'batch': name}."""
    pages: dict[str, dict] = {}
    for path in files if files is not None else sorted(directory.glob(f"{kind}-*.md")):
        stem, section = None, None
        for raw in path.read_text(encoding="utf-8").splitlines():
            m = re.match(r"^=== (p-\d{4})\s*$", raw)
            if m:
                stem = m.group(1)
                pages[stem] = {"md": [], "flags": [], "notes": [], "batch": path.name}
                section = "md"
                continue
            m = re.match(r"^--- (flags|notes)\s*$", raw)
            if m and stem is not None:
                section = m.group(1)
                continue
            if stem is not None:
                pages[stem][section].append(raw.rstrip())
    return pages


def _paragraphs(md_lines: list[str]) -> list[str]:
    out: list[str] = []
    for block in re.split(r"\n\s*\n", "\n".join(md_lines)):
        rows = [r.strip() for r in block.splitlines() if r.strip()]
        while rows and rows[0].startswith("#"):
            out.append(rows.pop(0))
        if rows:
            # elision as in the texts (ʼ); the OCR's ᾽ is never a quotation mark
            out.append(greek.nfc(" ".join(rows)).replace("᾽", "ʼ"))
    return out


def merge_kind(directory: Path, kind: str) -> list[str]:
    """The checked notes or introduction as paragraphs in page order (headings as paragraphs of
    their own); a page's paragraph that begins '+ ' joined to the last paragraph of the page
    before (not to a footnote after it)."""
    from .sophocles_pages import join_run_on

    pages = read_prose_batches(directory, kind)
    paras: list[str] = []
    for stem in sorted(pages):
        for p in _paragraphs(pages[stem]["md"]):
            if p.startswith("+ ") and paras:
                k = len(paras) - 1
                while k > 0 and paras[k].startswith("[Note:"):
                    k -= 1
                paras[k] = join_run_on(paras[k], p[2:])
            elif p.startswith("+ "):
                paras.append(p[2:])
            else:
                paras.append(p)
    return paras


def merge_translation(directory: Path) -> list[tuple[str, str, str]]:
    """Starkie's translation from trans-NN.md: (speaker or '', line, text) segments; '+ ' continues
    the segment before."""
    from .sophocles_pages import join_run_on

    pages = read_prose_batches(directory, "trans")
    segs: list[list[str]] = []
    speaker = ""
    for stem in sorted(pages):
        for raw in pages[stem]["md"]:
            if not raw.strip():
                continue
            if raw.startswith("@ "):
                speaker = raw[2:].strip()
                continue
            if raw.startswith("+ ") and segs:
                segs[-1][2] = join_run_on(segs[-1][2], raw[2:])
                continue
            n, sep, text = raw.partition("\t")
            if sep and re.fullmatch(r"\d+[a-z]?", n.strip()):
                segs.append([speaker, n.strip(), greek.nfc(text.strip())])
                speaker = ""
            elif segs:
                segs[-1][2] = join_run_on(segs[-1][2], raw)
    return [tuple(s) for s in segs]


# --- the checker --------------------------------------------------------------------------------

_GREEK = re.compile(r"[Ͱ-Ͽἀ-῿][Ͱ-Ͽἀ-῿ʼ’᾽]*")
_VOWEL_START = re.compile(r"^[αεηιουωρ]", re.I)


def check_prose(slug: str, kind: str, path: Path, texts: Path) -> list[str]:
    """Remarks on one checked prose batch: pages missing or out of order, headings, run-on marks,
    flags not answered, Greek not precomposed or without a breathing on an initial vowel or rho,
    and (notes, translation) line numbers that grc.txt lacks."""
    out_dir = PIPELINE / "build" / "drama-prose" / slug
    index = json.loads((out_dir / f"{kind}.json").read_text(encoding="utf-8"))
    pages = read_prose_batches(path.parent, kind, files=[path])
    m = re.search(rf"{kind}-(\d+)", path.name)
    expected = [p["stem"] for p in index if m and p["batch"] == int(m.group(1))]
    remarks: list[str] = []
    if list(pages) != [s for s in expected if s in pages]:
        remarks.append("the pages are not in page order")
    for stem in expected:
        if stem not in pages:
            remarks.append(f"{stem}: missing from the batch")
    for stem in pages:
        if stem not in expected:
            remarks.append(f"{stem}: not a page of this batch")
    numbers: set[str] = set()
    grc = texts / slug / "grc.txt"
    if grc.exists():
        for raw in grc.read_text(encoding="utf-8").splitlines():
            mm = re.match(r"^(\d+[a-z]?)\t", raw)
            if mm:
                numbers.add(mm.group(1))
    prev_note = -1
    prev_sec = 0
    for stem, block in pages.items():
        noted = " ".join(block["notes"])
        md = [l for l in block["md"] if l.strip()]
        if not md:
            if "blank" not in noted.lower() and "no text" not in noted.lower():
                remarks.append(f"{stem}: empty page (say so under notes if the page is blank)")
            continue
        first = md[0]
        if kind == "notes" and not (first.startswith("## ") or first.startswith("+ ")):
            remarks.append(f"{stem}: the page begins neither with a note's heading nor with '+ ' (a note run on)")
        for k, raw in enumerate(md):
            if raw.startswith("+ ") and k > 0:
                remarks.append(f"{stem}: '+ ' inside the page (only the page's first paragraph may run on)")
            if raw.startswith("#"):
                if kind == "notes":
                    mm = re.match(r"^## (\d+)([a-z]?)(?:-(\d+)([a-z]?))?$", raw)
                    if not mm:
                        remarks.append(f"{stem}: heading “{raw}” is not '## N' or '## N-M'")
                        continue
                    n = int(mm.group(1))
                    if n < prev_note:
                        remarks.append(f"{stem}: note {raw[3:]} comes after {prev_note}")
                    prev_note = n
                    if numbers and mm.group(1) + mm.group(2) not in numbers and raw[3:] not in noted and mm.group(1) not in noted:
                        remarks.append(f"{stem}: note {raw[3:]}: no line {mm.group(1)}{mm.group(2)} in texts/{slug}/grc.txt (say why under notes)")
                elif kind == "intro":
                    mm = re.match(r"^## § (\d+)(?: — .+)?$", raw)
                    if mm:
                        n = int(mm.group(1))
                        if n != prev_sec + 1 and n != 1:
                            remarks.append(f"{stem}: § {n} after § {prev_sec}")
                        prev_sec = n
                    elif not re.match(r"^#{1,3} \S", raw):
                        remarks.append(f"{stem}: heading “{raw}” is not well formed")
            if kind == "trans":
                if not (raw.startswith("@ ") or raw.startswith("+ ") or re.match(r"^\d+[a-z]?\t", raw)):
                    remarks.append(f"{stem}: “{raw[:50]}” is neither '@ Speaker', 'N<TAB>text' nor a run-on '+ '")
                mm = re.match(r"^(\d+[a-z]?)\t", raw)
                if mm and numbers and mm.group(1) not in numbers:
                    remarks.append(f"{stem}: translation line {mm.group(1)} is not a line of grc.txt")
            if raw != unicodedata.normalize("NFC", raw):
                remarks.append(f"{stem}: not NFC: “{raw[:40]}”")
            for g in _GREEK.findall(raw):
                letters = unicodedata.normalize("NFD", g)
                if _VOWEL_START.match(letters) and letters[0].islower() and not re.search("[̓̔]", letters[:4]):
                    at = raw.find(g)
                    if at > 0 and raw[at - 1] in "ʼ’᾽'":
                        continue  # prodelision: ʼκεῖνος
                    remarks.append(f"{stem}: “{g}” begins with a vowel or rho but has no breathing")
        for raw in block["flags"]:
            if not raw.strip():
                continue
            mm = re.match(r"^\d+ .*→\s*(.*)$", raw)
            if not mm:
                remarks.append(f"{stem}: flag line “{raw[:50]}” is not 'k word [kind] → answer'")
            elif not mm.group(1).strip():
                remarks.append(f"{stem}: flag not answered: “{raw[:50]}”")
    return remarks


def main(argv: list[str]) -> None:
    run(argv[0], argv[1], argv[2])


if __name__ == "__main__":
    main(sys.argv[1:])
