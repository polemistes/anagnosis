"""Lodge's introduction to the Gorgias by OCR, for checking against the scan.

Gonzalez Lodge, Plato, Gorgias (Boston: Ginn, 1890; College Series of Greek Authors), preface
and introduction (pp. iii-iv, 1-32). Perseus has Lodge's commentary but not his introduction,
which the notes cite ("See Introd. § 4"). Read from the Internet Archive scan gorgiasss00platuoft
(the 1896 printing, Robarts Library, Toronto, 400 ppi), leaves 8-9 (preface) and 10-41.

    python -m anagnosis_pipeline lodge-intro        the leaves, Tesseract (eng+grc), a draft and the
                                                    suspect words of each page

Files, under pipeline/sources/scans/gorgiasss00platuoft/ and pipeline/build/lodge-intro/:

    pages/leaf_0010.png      the page, grey
    leaf_0010.txt            Tesseract's text of the page (eng+grc, --psm 3)
    leaf_0010.md             the check sheet: the draft, and the suspect words
Checked pages are written to pipeline/transcriptions/gorgias-lodge-intro/page-0010.md.
"""
from __future__ import annotations

import os
import re
import subprocess
import tempfile
import unicodedata
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
PIPELINE = ROOT / "pipeline"
TESSDATA = PIPELINE / "tessdata"
SCAN = "gorgiasss00platuoft"
LEAVES = range(8, 42)
SRC = PIPELINE / "sources" / "scans" / SCAN
BUILD = PIPELINE / "build" / "lodge-intro"


def fetch_leaf(leaf: int) -> Path:
    (SRC / "jp2").mkdir(parents=True, exist_ok=True)
    (BUILD / "pages").mkdir(parents=True, exist_ok=True)
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
        subprocess.run(["magick", f"{t}/p.png", "-colorspace", "Gray", "-normalize", str(png) + ".part.png"], check=True)
    os.replace(str(png) + ".part.png", png)
    return png


def ocr_leaf(leaf: int) -> str:
    txt = BUILD / f"leaf_{leaf:04d}.txt"
    if not txt.exists():
        png = fetch_leaf(leaf)
        env = dict(os.environ, OMP_THREAD_LIMIT="1")
        with tempfile.TemporaryDirectory() as t:
            subprocess.run(["tesseract", str(png), f"{t}/o", "--tessdata-dir", str(TESSDATA), "-l", "eng+grc", "--psm", "3"],
                           check=True, capture_output=True, env=env)
            txt.write_text(unicodedata.normalize("NFC", Path(f"{t}/o.txt").read_text(encoding="utf-8")), encoding="utf-8")
    return txt.read_text(encoding="utf-8")


def check_sheet(leaf: int, text: str) -> None:
    from .egt_ocr import vocabularies, word_problems

    voc = vocabularies()
    names = {"Gorgias", "Socrates", "Callicles", "Polus", "Chaerephon", "Plato", "Leontini", "Athens", "Athenians",
             "Protagoras", "Prodicus", "Hippias", "Isocrates", "Thrasymachus", "Tisias", "Corax", "Empedocles",
             "Antiope", "Euripides", "Pericles", "Nicias", "Aristocrates", "Arginusae", "Syracuse", "Pherecrates",
             "Meno", "Phaedrus", "Republic", "Apology", "Deuschle", "Cron", "Ginn", "Thompson", "Schanz", "Stallbaum",
             "Sauppe", "Towle", "Aristotle", "Rhetoric", "Thessaly", "Larissa", "Aleuadae", "Xenophon", "Anabasis"}
    flags = []
    words = text.split()
    for k, w in enumerate(words):
        prev = words[k - 1] if k else ""
        nxt = words[k + 1] if k + 1 < len(words) else ""
        if w.endswith("-") and nxt:
            continue  # a divided word: the agent joins it
        for kind, tok in word_problems(w, prev, nxt, voc, names):
            flags.append(f"{kind}: {tok}")
    md = [f"# Leaf {leaf}: Tesseract's text (eng+grc)", "", f"Image: pages/leaf_{leaf:04d}.png", "",
          "## Suspect words (not in the word lists, Greek with unknown accents, digits among letters)", ""]
    md += [f"* {f}" for f in dict.fromkeys(flags)] or ["None."]
    md += ["", "## The draft", "", "```", text.strip(), "```"]
    (BUILD / f"leaf_{leaf:04d}.md").write_text("\n".join(md) + "\n", encoding="utf-8")


def run() -> None:
    with ThreadPoolExecutor(4) as ex:
        texts = list(ex.map(ocr_leaf, LEAVES))
    for leaf, text in zip(LEAVES, texts):
        check_sheet(leaf, text)


# ---------------------------------------------------------------- assembling

META = {
    "title": "Introduction (G. Lodge)",
    "author": "Gonzalez Lodge",
    "source": "Plato, Gorgias, edited on the basis of Deuschle-Cron's edition by Gonzalez Lodge, Boston: Ginn & Company, 1890 (1896 printing), Preface and Introduction, pp. iii-iv, 1-32; transcribed from the Internet Archive scan gorgiasss00platuoft",
    "license": "CC BY-SA 4.0 (transcription; the book is in the public domain)",
}


def assemble(transcriptions: Path, out: Path) -> int:
    """introduction.md from the checked pages: their text joined (a paragraph that runs over a
    page is joined), the footnotes of each page after the paragraph they belong to."""
    pages = sorted(transcriptions.glob("page-*.md"))
    body: list[str] = []
    notes: list[str] = []
    for p in pages:
        text = p.read_text(encoding="utf-8")
        main, _, foot = text.partition("\n--- footnotes\n")
        main = main.strip()
        if main.startswith("…"):
            # continues the paragraph of the page before
            if body:
                body[-1] = body[-1].rstrip() + " " + main[1:].lstrip().split("\n\n", 1)[0]
                rest = main[1:].lstrip().split("\n\n", 1)
                main = rest[1] if len(rest) > 1 else ""
            else:
                main = main[1:].lstrip()
        if main:
            body.extend(x.strip() for x in main.split("\n\n") if x.strip())
        notes.extend(x.strip() for x in foot.strip().split("\n") if x.strip())
    md = [f"# {k}: {v}" for k, v in META.items()] + [""]
    md += ["\n\n".join(body), ""]
    if notes:
        md += ["## Notes", ""] + [f"{n}\n" for n in notes]
    out.write_text("\n".join(md).rstrip() + "\n", encoding="utf-8")
    return len(pages)
