"""Build the inflected-forms table for the analyser.

Sources: Morpheus (MPL-2.0), run by morpheus_forms.py over the forms of the open Perseus
corpus (pipeline/build/morpheus-analyses.tsv.gz), and the Perseus treebanks (hand-verified
analyses). Stored compactly: one row per diacritic-less form key, with all analyses packed as
"form\\tlemma\\tpostag\\tsource" lines.
"""
from __future__ import annotations

import re
import sqlite3
import sys
import zlib
from collections import defaultdict
from pathlib import Path

from lxml import etree

from . import greek

FORMS_SCHEMA = """
CREATE TABLE forms (form_key TEXT NOT NULL PRIMARY KEY, analyses BLOB NOT NULL) WITHOUT ROWID;
"""


def _strip_length_marks(s: str) -> str:
    """Morpheus writes vowel length as macron/breve; the plain form is the usual spelling."""
    return "".join(c for c in greek.nfd(s) if c not in "̄̆").replace("ᾱ", "α").replace("ᾰ", "α")


# Morpheus's dialect labels for the literary dialects of the texts read here
MAIN_DIALECTS = {"attic", "epic", "ionic", "homeric"}


def morpheus_analyses(path: Path):
    """Yield (form, lemma, postag) from morpheus-analyses.tsv.gz (see morpheus_forms.py). Where a
    form has an analysis valid in Attic, Epic or Ionic (or in every dialect), its analyses valid only
    in other dialects (a Doric or Aeolic contraction that happens to look the same) are left out."""
    import gzip
    import itertools

    def rows():
        with gzip.open(path, "rt", encoding="utf-8") as f:
            for raw in f:
                form, lemma, postag, *rest = raw.rstrip("\n").split("\t")
                yield form, lemma, postag, set((rest[0] if rest else "").split())

    for form, group in itertools.groupby(rows(), key=lambda r: r[0]):
        group = list(group)
        main = [r for r in group if not r[3] or r[3] & MAIN_DIALECTS]
        for _f, lemma, postag, _d in (main or group):
            yield greek.nfc(_strip_length_marks(form)), greek.nfc(lemma), postag


def treebank_analyses(tb_dir: Path):
    for path in sorted(tb_dir.glob("*.tb.xml")):
        for _, w in etree.iterparse(str(path), tag="word"):
            form = w.get("form") or ""
            lemma = w.get("lemma") or ""
            postag = w.get("postag") or ""
            if form and lemma and postag and not w.get("artificial") and greek.is_word(form) and not w.get("insertion_id"):
                form = greek.nfc(form.replace("̓", "ʼ"))  # elision written with a combining comma
                yield form, re.sub(r"\d+$", "", greek.nfc(lemma)), postag
            w.clear()


def build_forms(db: sqlite3.Connection, sources: Path) -> None:
    db.executescript(FORMS_SCHEMA)
    table: dict[str, dict[tuple[str, str, str], str]] = defaultdict(dict)  # key -> (lemma_key, postag, source) -> "form\\tlemma"
    n = 0
    morpheus_path = sources.parent / "build" / "morpheus-analyses.tsv.gz"
    if not morpheus_path.exists():
        raise SystemExit(f"{morpheus_path} is missing: run 'build-morpheus-forms' first")
    if morpheus_path.exists():
        for form, lemma, postag in morpheus_analyses(morpheus_path):
            key = greek.strip_diacritics(form)
            table[key].setdefault((greek.lemma_key(lemma), postag, "morpheus"), f"{form}\t{lemma}")
            n += 1
        print(f"forms: {n} Morpheus analyses", file=sys.stderr)
    tb_dir = sources / "treebanks"
    if tb_dir.exists():
        m = 0
        for form, lemma, postag in treebank_analyses(tb_dir):
            key = greek.strip_diacritics(form)
            table[key].setdefault((greek.lemma_key(lemma), postag, "treebank"), f"{form}\t{lemma}")
            m += 1
        print(f"forms: {m} treebank analyses", file=sys.stderr)
    rows = []
    for key, analyses in table.items():
        # treebank analyses first (hand-verified), then Morpheus; drop Morpheus duplicates of treebank ones
        seen = set()
        lines = []
        for (lemma_key, postag, source), fl in sorted(analyses.items(), key=lambda kv: (kv[0][2] != "treebank", kv[0][0], kv[0][1])):
            if (lemma_key, postag) in seen:
                continue
            seen.add((lemma_key, postag))
            lines.append(f"{fl}\t{postag}\t{source}")
        rows.append((key, zlib.compress("\n".join(lines).encode("utf-8"), 9)))
    db.executemany("INSERT INTO forms VALUES (?, ?)", rows)
    print(f"forms: {len(rows)} form keys, {sum(len(v) for v in table.values())} analyses")
