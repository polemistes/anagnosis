"""Merge the transcription of Allen's Odyssey into texts/odyssey/.

Reads pipeline/transcriptions/odyssey/batch-*.md (see INSTRUCTIONS.md there) and writes:

    texts/odyssey/grc.txt                          Allen's text
    texts/odyssey/commentary-allen-apparatus.md    his apparatus criticus
    texts/odyssey/tokens.tsv, syntax-nodes.tsv     the treebank re-aligned to his text

The treebank was made on the Perseus text. Where Allen's word is the treebank's word, its
annotation stands; where he reads differently, the word keeps the treebank's place in the
sentence (head and relation) and takes its lemma and parse from the analyser, choosing the
analysis nearest the treebank's; words the treebank lacks take the analyser's first analysis.
Every word so annotated is listed in pipeline/build/odyssey-review.tsv for checking, together
with words of the transcription that neither the draft nor either OCR supports.
"""
from __future__ import annotations

import csv
import json
import re
import sqlite3
import sys
import unicodedata
import zlib
from collections import defaultdict
from pathlib import Path

from . import greek
from .linenum import LINE_N, parts
from .odyssey import GREEK_META, TREEBANK, align, fix_lemma, read_treebank, section_for, syntax_nodes
from .textfmt import Document, Line, write_file

APPARATUS_META = {
    "title": "Apparatus criticus",
    "author": "Thomas W. Allen",
    "lang": "lat",
    "source": "Homeri Opera III-IV, ed. T. W. Allen, editio altera, Oxford 1917, 1919 (apparatus criticus), "
    "transcribed from the Internet Archive scans homeriopera03home and homeriopera04home",
    "license": "CC BY-SA 4.0 (transcription; the edition is in the public domain)",
}

ITEM_N = re.compile(r"^(\d+)\.(\d+)([a-z]?)(?:-(\d+|[a-z]))?$")


def read_batches(directory: Path) -> dict[str, dict]:
    """Page blocks by stem: {'text': [(n, line)], 'apparatus': [(n, item)], 'notes': [str], 'batch': name}."""
    pages: dict[str, dict] = {}
    for path in sorted(directory.glob("batch-*.md")):
        stem, section = None, None
        for raw in path.read_text(encoding="utf-8").splitlines():
            m = re.match(r"^=== (p\d-\d{4})\s*$", raw)
            if m:
                stem = m.group(1)
                pages[stem] = {"text": [], "apparatus": [], "notes": [], "batch": path.name}
                section = None
                continue
            m = re.match(r"^--- (text|apparatus|notes)\s*$", raw)
            if m:
                section = m.group(1)
                continue
            if stem is None or section is None or not raw.strip():
                continue
            if section == "notes":
                pages[stem]["notes"].append(raw.strip())
                continue
            n, sep, body = raw.partition("\t")
            if not sep:
                pages[stem].setdefault("errors", []).append(f"no TAB: {raw[:60]!r}")
                continue
            pages[stem][section].append((n.strip(), unicodedata.normalize("NFC", body.strip())))
    return pages


def _skel(s: str) -> str:
    return greek.strip_diacritics(s).replace("ς", "σ")


def _words(text: str) -> list[str]:
    return [_skel(w) for w, _s, _e in greek.words(text)]


def _draft_witnesses(md: Path) -> list[str]:
    """All the draft's readings of the page (D, A and B), for checking the transcription."""
    out = []
    for raw in md.read_text(encoding="utf-8").splitlines():
        m = re.match(r"^(?:[\d.a-z]+)?\t(D|A|B): (.*)$", raw)
        if m:
            out.append(m.group(2))
    return out


class Analyser:
    """Analyses of a form from data/lexicon.sqlite (the app's word analyser)."""

    def __init__(self, path: Path):
        self.db = sqlite3.connect(path)
        self.cache: dict[str, list[tuple[str, str, str, str]]] = {}

    def __call__(self, form: str) -> list[tuple[str, str, str, str]]:
        key = greek.strip_diacritics(form.replace(greek.APOSTROPHE, ""))
        if key not in self.cache:
            row = self.db.execute("SELECT analyses FROM forms WHERE form_key = ?", (key,)).fetchone()
            self.cache[key] = [tuple(l.split("\t")) for l in zlib.decompress(row[0]).decode("utf-8").splitlines()] if row else []
        return self.cache[key]


def _accent_key(s: str) -> str:
    """A form with grave accents read as acute, for comparing a form in a verse with a dictionary form."""
    return unicodedata.normalize("NFC", unicodedata.normalize("NFD", s.replace(greek.APOSTROPHE, "")).replace("̀", "́")).lower()


def choose_analysis(form: str, analyses: list, near: str = "", lemma: str = "") -> tuple[str, str] | None:
    """(lemma, postag) for a form: the analysis that best agrees with the treebank's lemma and
    tag (`lemma`, `near`), an analysis of exactly this form counting a little extra."""
    pool = [a for a in analyses if len(a) >= 3]
    if not pool:
        return None

    def score(a):
        s = 1 if _accent_key(a[0]) == _accent_key(form) else 0
        if lemma and greek.lemma_key(a[1]) == greek.lemma_key(lemma):
            s += 3
        if near:
            s += sum(1 for x, y in zip(a[2].ljust(9, "-"), near.ljust(9, "-")) if x == y)
        return s

    best = max(pool, key=score)  # max keeps the first of equals: the analyser lists treebank analyses first
    return best[1], best[2][:9]


def merge(transcriptions: Path, pages_dir: Path, texts: Path, sources: Path, lexicon: Path, build: Path) -> int:
    pages = read_batches(transcriptions)
    index = json.loads((pages_dir / "pages.json").read_text(encoding="utf-8"))
    problems: list[str] = []
    review: list[dict] = []
    missing = [p["stem"] for p in index if p["stem"] not in pages]
    if missing:
        problems.append(f"{len(missing)} pages not transcribed: {', '.join(missing[:12])}{' ...' if len(missing) > 12 else ''}")

    # --- the text, in page order
    lines: list[tuple[str, str, str]] = []  # (n, text, stem)
    for p in index:
        block = pages.get(p["stem"])
        if block is None:
            continue
        for e in block.get("errors", []):
            problems.append(f"{p['stem']}: {e}")
        for n, text in block["text"]:
            if not LINE_N.match(n) or "." not in n:
                problems.append(f"{p['stem']}: bad line number {n!r}")
                continue
            lines.append((n, text, p["stem"]))
        # words neither the draft nor the OCRs have
        witnesses = set()
        for w in _draft_witnesses(pages_dir / f"{p['stem']}.md"):
            witnesses.update(_words(w))
        for n, text in block["text"]:
            for word in greek.words(text):
                if _skel(word[0]) not in witnesses:
                    review.append({"line": n, "form": word[0], "lemma": "", "postag": "", "reason": "transcribed word not in the draft or either OCR"})
    seen: dict[str, str] = {}
    prev = None
    for n, _text, stem in lines:
        if n in seen:
            problems.append(f"{stem}: line {n} also on {seen[n]}")
        seen[n] = stem
        cur = parts(n)
        if prev is not None:
            pb, cb = prev[0] // 1000, cur[0] // 1000
            if cb == pb and cur[0] != prev[0] + 1 and not (cur[0] == prev[0] and cur[1] > prev[1]) and not (cur[0] == prev[0] + 1 and cur[1] == ""):
                problems.append(f"{stem}: {n} follows {prev[0] // 1000}.{prev[0] % 1000}{prev[1]}")
            if cb != pb and (cb != pb + 1 or cur[0] % 1000 != 1):
                problems.append(f"{stem}: book changes at {n}")
        prev = cur

    doc = Document(meta=dict(GREEK_META))
    book = None
    for n, text, _stem in lines:
        b = int(n.split(".")[0])
        if b != book:
            doc.items.append(section_for(b))
            book = b
        doc.items.append(Line(n, text))
    out = texts / "odyssey"
    write_file(out / "grc.txt", doc)
    print(f"wrote {out / 'grc.txt'}: {len(doc.lines)} lines from {len(pages)} pages")

    # --- the apparatus
    notes: list[tuple[str, list[str]]] = []
    for p in index:
        block = pages.get(p["stem"])
        if block is None:
            continue
        for n, item in block["apparatus"]:
            m = ITEM_N.match(n)
            if not m:
                problems.append(f"{p['stem']}: bad apparatus number {n!r}")
                continue
            bk, ln, letter, end = m.groups()
            if ln == "0" and not letter:  # a note on the book's title: shown with its first line
                heading, body = f"{bk}.1", f"*(title)* {item}"
            elif letter:  # an added line: filed under the line it follows, with its own label
                label = f"{ln}{letter}" + (f"–{end}" if end else "")
                heading, body = f"{bk}.{ln}", f"*{label}* {item}"
            else:
                heading, body = (f"{bk}.{ln}-{end}" if end else f"{bk}.{ln}"), item
            if notes and notes[-1][0] == heading:
                notes[-1][1].append(body)
            else:
                notes.append((heading, [body]))
    md = [f"# {k}: {v}" for k, v in APPARATUS_META.items()] + [""]
    for heading, items in notes:
        md.append(f"## {heading}")
        md.append("\n\n".join(items))
        md.append("")
    (out / "commentary-allen-apparatus.md").write_text("\n".join(md) + "\n", encoding="utf-8")
    print(f"wrote {out / 'commentary-allen-apparatus.md'}: {len(notes)} notes, {sum(len(i) for _, i in notes)} items")

    # --- the treebank, re-aligned to Allen's text
    from .import_perseus import write_syntax_nodes, write_tokens

    tb = read_treebank(sources / TREEBANK)
    rows, _warnings = align(doc, tb, keep_tb_form=True)
    analyse = Analyser(lexicon)
    by_line: dict[str, list[dict]] = defaultdict(list)
    for r in rows:
        tb_form = r.pop("tb_form", "")
        same = tb_form and _skel(tb_form) == _skel(r["form"])
        if r["lemma"] and r["postag"] and same:
            continue
        if r["lemma"] and r["postag"] and not tb_form:
            continue  # a word the treebank split in two, annotated from its parts
        chosen = choose_analysis(r["form"], analyse(r["form"]), r["postag"], r["lemma"])
        reason = ("the treebank leaves it without lemma or parse" if same
                  else f"reads {r['form']} where the treebank has {tb_form}" if tb_form
                  else "a word the treebank splits" if "+" in r["word_id"] else "not in the treebank")
        if chosen is None:
            if not r["lemma"]:
                reason += "; the analyser does not know the form"
            review.append({"line": r["line"], "form": r["form"], "lemma": r["lemma"], "postag": r["postag"], "reason": reason})
            continue
        r["lemma"], r["postag"] = fix_lemma(chosen[0]), chosen[1]
        review.append({"line": r["line"], "form": r["form"], "lemma": r["lemma"], "postag": r["postag"], "reason": reason})
    write_tokens(out / "tokens.tsv", rows)
    used = set()
    for r in rows:
        for wid in r["word_id"].split("+"):
            if wid:
                used.add((r["sentence"], wid))
    write_syntax_nodes(out / "syntax-nodes.tsv", syntax_nodes(tb, used))
    without = sum(1 for r in rows if not r["lemma"])
    print(f"wrote {out / 'tokens.tsv'}: {len(rows)} words, {without} without lemma; {len(review)} for review")

    build.mkdir(parents=True, exist_ok=True)
    with (build / "odyssey-review.tsv").open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["line", "form", "lemma", "postag", "reason"], delimiter="\t", lineterminator="\n")
        w.writeheader()
        w.writerows(review)
    (build / "odyssey-merge.log").write_text("\n".join(problems) + "\n", encoding="utf-8")
    for p in problems[:40]:
        print("  " + p, file=sys.stderr)
    print(f"{len(problems)} problems (pipeline/build/odyssey-merge.log); review list in pipeline/build/odyssey-review.tsv")
    return len(problems)


def check_batch(path: Path, pages_dir: Path) -> list[str]:
    """Problems in one batch file: format, numbering, line counts against the draft, and
    transcribed words that neither the draft nor the OCRs support."""
    import tempfile

    out: list[str] = []
    with tempfile.TemporaryDirectory() as tmp:
        (Path(tmp) / "batch-x.md").write_text(path.read_text(encoding="utf-8"), encoding="utf-8")
        pages = read_batches(Path(tmp))
    index = {p["stem"]: p for p in json.loads((pages_dir / "pages.json").read_text(encoding="utf-8"))}
    prev = None
    for stem, block in pages.items():
        for e in block.get("errors", []):
            out.append(f"{stem}: {e}")
        if stem not in index:
            out.append(f"{stem}: unknown page")
            continue
        draft_n = index[stem]["lines"]
        if abs(len(block["text"]) - draft_n) > 2:
            out.append(f"{stem}: {len(block['text'])} lines, the draft has {draft_n}")
        if not block["apparatus"]:
            out.append(f"{stem}: no apparatus")
        witnesses = set()
        for w in _draft_witnesses(pages_dir / f"{stem}.md"):
            witnesses.update(_words(w))
        for n, text in block["text"]:
            if text != unicodedata.normalize("NFC", text):
                out.append(f"{stem} {n}: not NFC")
            if "'" in text or "’" in text or "᾽" in text:
                out.append(f"{stem} {n}: apostrophe other than ʼ")
            odd = [w for w, _s, _e in greek.words(text) if _skel(w) not in witnesses]
            if odd:
                out.append(f"{stem} {n}: words no draft reading has: {' '.join(odd)}")
            if not LINE_N.match(n):
                out.append(f"{stem}: bad number {n!r}")
                continue
            cur = parts(n)
            if prev is not None and cur[0] // 1000 == prev[0] // 1000 and cur[0] != prev[0] + 1 and not cur[1]:
                out.append(f"{stem}: {n} follows {prev[0] // 1000}.{prev[0] % 1000}{prev[1]}")
            prev = cur
    return out
