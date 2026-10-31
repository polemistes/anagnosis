"""What the checked text and Tesseract's reading of the page still disagree on, after the agents
have answered the flags (pipeline/PLAN-drama.md, Decisions: Agamemnon step 4).

The draft flags a line where the OCR and Perseus differ in letters, read with confidence. The
editions differ from Perseus also in punctuation, brackets and daggers, which the flags do not
compare, and in words Tesseract read rightly but without confidence. Once a play's batches are
checked, every verse is compared again with the OCR of its printed line, word by word, with its
punctuation: each difference that Tesseract read with some confidence is a residual, listed with
a crop of its line for an agent to settle against the page.

    python -m anagnosis_pipeline drama-residuals <play> [batch-NN.md …]

writes pipeline/build/drama-pages/<play>/residuals/r-NNNN.md and r-NNNN.png per page that has
residuals, and residuals.json.
"""
from __future__ import annotations

import difflib
import json
import re
import unicodedata
from pathlib import Path

from . import greek
from .drama import APOS, PLAYS, read_text_batches, skel

ROOT = Path(__file__).resolve().parent.parent.parent
PIPELINE = ROOT / "pipeline"
PUNCT = ",.;·:!?"


def _marks(word: str) -> tuple[str, str, str]:
    """(what stands before the letters, the letters with their accents, what stands after)."""
    m = re.match(r"^([^\w]*)(.*?)([^\w]*)$", word)
    return (m.group(1), m.group(2), m.group(3)) if m else ("", word, "")


def _trail(after: str) -> str:
    """The punctuation after a word as one class: ',' '.' '·' ';' ':' '!' or ''."""
    after = after.replace(APOS, "").replace("’", "")
    for c in after:
        if c in PUNCT:
            return c
    return ""


def _ocr_trail(after: str) -> str:
    """The OCR's punctuation as the print's: Tesseract writes the raised stop as · ' " or ˙."""
    after = after.replace("”", "·").replace('"', "·").replace("˙", "·").replace("᾽", "")
    return _trail(after)


def _letters(core: str) -> str:
    return unicodedata.normalize("NFC", core.lower().replace(APOS, "").replace("ʼ", ""))


def page_residuals(play, layout: dict, items: list[tuple[str, str]]) -> list[dict]:
    from .drama_pages import ocr_stream

    lines, ocr = ocr_stream([layout], play.adscript)
    # the OCR's words with their punctuation, by printed line
    words: list[tuple[str, str, int]] = []  # (n, word as checked, index)
    for n, text in items:
        for w in text.split():
            if skel(w):
                words.append((n, w, len(words)))
            elif words and w.strip() and w.strip() not in "*†":
                words[-1] = (words[-1][0], words[-1][1] + w, words[-1][2])
    a = [skel(w) for _n, w, _i in words]
    b = [t["skel"] for t in ocr]
    out: list[dict] = []
    sm = difflib.SequenceMatcher(None, a, b, autojunk=False)

    def add(n, kind, mine, theirs, o):
        pl = lines[ocr[o]["line"]] if o is not None else None
        out.append({"n": n, "kind": kind, "text": mine, "ocr": theirs, "y0": pl["y0"] if pl else None,
                    "y1": pl["y1"] if pl else None, "conf": ocr[o]["conf"] if o is not None else None})

    for op, a0, a1, b0, b1 in sm.get_opcodes():
        if op == "equal" or (op == "replace" and a1 - a0 == b1 - b0):
            for i, o in zip(range(a0, a1), range(b0, b1)):
                n, mine, _ = words[i]
                t = ocr[o]
                pa, ca, sa = _marks(mine)
                pb, cb, sb = _marks(t["t"])
                if op == "replace":
                    sim = difflib.SequenceMatcher(None, a[i], b[o]).ratio()
                    if t["conf"] >= 75 and sim < 0.9:
                        add(n, "word", mine, t["t"], o)
                        continue
                    if sim < 0.9:
                        continue
                if t["conf"] >= 90 and _letters(ca) != _letters(cb):
                    add(n, "accent", mine, t["t"], o)
                if t["conf"] >= 80 and _trail(sa) != _ocr_trail(sb):
                    add(n, "punctuation", mine, t["t"], o)
                for c in "[]⟨⟩†":
                    if t["conf"] >= 70 and ((c in pa + sa) != (c in pb + sb)) and not (c in "⟨⟩" and ("<" in pb + sb or ">" in pb + sb)):
                        add(n, "bracket", mine, t["t"], o)
                        break
        elif op in ("replace", "insert"):
            for o in range(b0, b1):
                t = ocr[o]
                if t["conf"] >= 75 and len(t["skel"]) >= 2:
                    n = words[a0][0] if a0 < len(words) else words[-1][0]
                    add(n, "ocr-only", "", t["t"], o)
    return out


def residuals(slug: str, files: list[Path] | None = None) -> list[dict]:
    from PIL import Image, ImageDraw, ImageFont

    from .drama_pages import page_layout, route_dir, scan_dirs

    play = PLAYS[slug]
    tdir = PIPELINE / "transcriptions" / "drama" / slug
    pages = read_text_batches(tdir, files)
    out_dir = route_dir("drama-pages", slug, play.scan) / "residuals"
    out_dir.mkdir(exist_ok=True)
    _, sbuild = scan_dirs(play.scan)
    try:
        font = ImageFont.truetype("DejaVuSans-Bold.ttf", 30)
    except OSError:
        font = ImageFont.load_default()
    everything = []
    for stem, block in sorted(pages.items()):
        leaf = int(stem[2:])
        items = [(a, b) for a, b in block["items"] if a not in ("@", "!")]
        res = page_residuals(play, page_layout(play, leaf), items)
        noted = {re.match(r"^(\d+[a-z]?)", x).group(1) for x in block["notes"] if re.match(r"^\d", x)}
        for r in res:
            r["stem"] = stem
            r["noted"] = r["n"] in noted
        everything += res
        for old in out_dir.glob(f"r-{leaf:04d}.*"):
            old.unlink()
        if not res:
            continue
        md = [f"# Residuals on {stem} (leaf {leaf})", "",
              f"Image: r-{leaf:04d}.png (each line once, labelled with the verse number); the whole page: ../pages/leaf_{leaf:04d}.png", ""]
        for k, r in enumerate(res, 1):
            what = {"word": f"the text has «{r['text']}», the OCR reads «{r['ocr']}»",
                    "accent": f"accents: the text has «{r['text']}», the OCR reads «{r['ocr']}»",
                    "punctuation": f"punctuation: the text has «{r['text']}», the OCR reads «{r['ocr']}»",
                    "bracket": f"brackets or dagger: the text has «{r['text']}», the OCR reads «{r['ocr']}»",
                    "ocr-only": f"the OCR reads «{r['ocr']}» here, the text has nothing"}[r["kind"]]
            md.append(f"{k}. {r['n']}: {what}" + (" (the line is noted in the batch)" if r["noted"] else ""))
        (out_dir / f"r-{leaf:04d}.md").write_text("\n".join(md) + "\n", encoding="utf-8")
        with Image.open(sbuild / "pages" / f"leaf_{leaf:04d}.png") as im:
            g = im.convert("L")
            spans = []
            for r in res:
                if r["y0"] is not None and (r["n"], r["y0"]) not in [(s[0], s[1]) for s in spans]:
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
            sheet.save(out_dir / f"r-{leaf:04d}.png")
    (out_dir / "residuals.json").write_text(json.dumps(everything, ensure_ascii=False, indent=0), encoding="utf-8")
    return everything
