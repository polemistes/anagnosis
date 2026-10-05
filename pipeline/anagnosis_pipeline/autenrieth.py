"""Autenrieth's Homeric Dictionary from the page-by-page transcription (pipeline/transcriptions/autenrieth/).

read_batches() reads the batch files; check_batch() checks one batch against the conventions
of INSTRUCTIONS.md and the OCR drafts; parse_autenrieth() turns all batches into dictionary
entries for the reader's shared lexicon.
"""
from __future__ import annotations

import html
import json
import re
import unicodedata
from pathlib import Path

from . import greek

ENTRY_START = re.compile(r"^(?:(\d+)\.\s+)?\*\*([^*]+)\*\*")
BOOK_REF = re.compile(r"(?<![\w.])([Α-Ωα-ω]) (\d+)")
LATIN_REF = re.compile(r"(?<![\w.,])([A-Za-z]) (\d{1,3})(?![\d.])")
MIXED = re.compile(r"\S*[A-Za-z][Ͱ-Ͽἀ-῿]\S*|\S*[Ͱ-Ͽἀ-῿][A-Za-z]\S*")


def read_batches(directory: Path) -> dict[str, dict]:
    """Page blocks by stem: {'head': str, 'left': [lines], 'right': [lines], 'notes': [lines], 'batch': name}."""
    pages: dict[str, dict] = {}
    for path in sorted(directory.glob("batch-*.md")):
        stem, section = None, None
        for raw in path.read_text(encoding="utf-8").splitlines():
            m = re.match(r"^=== (a-\d{4})\s*$", raw)
            if m:
                stem = m.group(1)
                pages[stem] = {"head": "", "left": [], "right": [], "notes": [], "batch": path.name}
                section = None
                continue
            m = re.match(r"^--- (head|left|right|notes)\s*$", raw)
            if m:
                section = m.group(1)
                continue
            if stem is None or section is None or not raw.strip():
                continue
            line = unicodedata.normalize("NFC", raw.strip())
            if section == "head":
                pages[stem]["head"] = line
            else:
                pages[stem][section].append(line)
    return pages


def headword(line: str) -> str | None:
    m = ENTRY_START.match(line)
    return m.group(2).strip(" ,:;.()") if m else None


def sort_key(word: str) -> str:
    """Alphabetical order as the dictionary keeps it: no diacritics, hyphens or case; σ for ς."""
    s = greek.strip_diacritics(word).replace("ς", "σ").replace("-", "").replace("ϝ", "").replace(" ", "")
    return "".join(c for c in s if "α" <= c <= "ω")


def lemma_of(word: str) -> str:
    """The headword as a lemma: without the hyphens of a compound or a trailing mark."""
    return greek.nfc(word.replace("-", "").strip(" ,:;.†()"))


def check_batch(path: Path, pages_dir: Path) -> list[str]:
    import tempfile

    out: list[str] = []
    with tempfile.TemporaryDirectory() as tmp:
        (Path(tmp) / "batch-x.md").write_text(path.read_text(encoding="utf-8"), encoding="utf-8")
        pages = read_batches(Path(tmp))
    index = {p["stem"]: p for p in json.loads((pages_dir / "pages.json").read_text(encoding="utf-8"))}
    prev_word, prev_where = None, None
    for stem, block in pages.items():
        if stem not in index:
            out.append(f"{stem}: unknown page")
            continue
        heads: list[str] = []
        for side in ("left", "right"):
            lines = block[side]
            if not lines:
                out.append(f"{stem} {side}: empty column")
                continue
            for i, line in enumerate(lines):
                where = f"{stem} {side} {i + 1}"
                if line.startswith("+ "):
                    if i > 0:
                        out.append(f"{where}: a continuation (+) only at the top of a column")
                    continue
                hw = headword(line)
                if hw is None:
                    out.append(f"{where}: neither a headword in **bold** nor a continuation (+): {line[:60]!r}")
                    continue
                heads.append(hw)
                key = sort_key(hw)
                if prev_word is not None and key and key < sort_key(prev_word):
                    out.append(f"{where}: {hw} comes after {prev_word} ({prev_where}): out of alphabetical order?")
                prev_word, prev_where = hw, where
            text = " ".join(lines)
            for m in LATIN_REF.finditer(text):
                out.append(f"{stem} {side}: '{m.group(0)}' - a Latin letter as a book letter? Use the Greek letter")
            for m in MIXED.finditer(text):
                if not re.search(r"[A-Za-z]{2,}\.?$", m.group(0)) or re.search(r"[Ͱ-Ͽἀ-῿]", m.group(0)):
                    out.append(f"{stem} {side}: '{m.group(0)}' mixes Greek and Latin letters")
            if re.search(r"['᾽’](?=\s|$)", re.sub(r"‘[^’]*’", "", text)) and re.search(r"[Ͱ-Ͽἀ-῿]['᾽]", text):
                out.append(f"{stem} {side}: elision written with ' or ᾽: use ʼ")
            # a column much shorter than the OCR's: something left out
            ocr = _ocr_column(pages_dir / f"{stem}.md", side)
            mine = len(re.sub(r"[^A-Za-zͰ-Ͽἀ-῿]", "", text))
            theirs = len(re.sub(r"[^A-Za-zͰ-Ͽἀ-῿]", "", ocr))
            if theirs > 200 and mine < 0.85 * theirs:
                out.append(f"{stem} {side}: {mine} letters against {theirs} in the OCR: a part left out?")
            if theirs > 200 and mine > 1.2 * theirs:
                out.append(f"{stem} {side}: {mine} letters against {theirs} in the OCR: a part written twice?")
        # the running head names the first and last headword of the page
        if "|" not in block["head"]:
            out.append(f"{stem}: running head missing (--- head: first | last)")
        elif heads:
            first, last = [h.strip() for h in block["head"].split("|", 1)]
            if sort_key(first) != sort_key(heads[0]):
                out.append(f"{stem}: running head {first} but the first headword is {heads[0]}")
            if sort_key(last) != sort_key(heads[-1]):
                out.append(f"{stem}: running head {last} but the last headword is {heads[-1]}")
    return out


def check_all(directory: Path, pages_dir: Path) -> list[str]:
    """Checks across the batches: every page transcribed once, the alphabetical order from page
    to page, and the seams where an entry runs on into the next column."""
    out: list[str] = []
    index = [p["stem"] for p in json.loads((pages_dir / "pages.json").read_text(encoding="utf-8"))]
    seen: dict[str, str] = {}
    for path in sorted(directory.glob("batch-*.md")):
        for raw in path.read_text(encoding="utf-8").splitlines():
            m = re.match(r"^=== (a-\d{4})\s*$", raw)
            if m:
                if m.group(1) in seen:
                    out.append(f"{m.group(1)}: in {seen[m.group(1)]} and in {path.name}")
                seen[m.group(1)] = path.name
    missing = [s for s in index if s not in seen]
    if missing:
        out.append(f"{len(missing)} pages not transcribed yet: {missing[0]} … {missing[-1]}")
    pages = read_batches(directory)
    columns = [(stem, side, pages[stem][side]) for stem in index if stem in pages for side in ("left", "right")]
    prev_word = prev_where = None
    for (stem, side, lines), nxt in zip(columns, columns[1:] + [None]):
        for i, line in enumerate(lines):
            hw = headword(line)
            if hw is None:
                continue
            if prev_word and prev_where.split()[0] != stem and sort_key(hw) and sort_key(hw) < sort_key(prev_word):
                out.append(f"{stem} {side} {i + 1}: {hw} comes after {prev_word} ({prev_where}): out of alphabetical order?")
            prev_word, prev_where = hw, f"{stem} {side} {i + 1}"
        if nxt is None or not lines or not nxt[2] or index.index(nxt[0]) - index.index(stem) > 1:
            continue
        last, first = lines[-1], nxt[2][0]
        where = f"{stem} {side} → {nxt[0]} {nxt[1]}"
        if first.startswith("+ "):
            head = re.match(r"\+ ([^\W\d_]+)", first)
            tail = re.search(r"([^\W\d_]+)[^\w]*$", last)
            if head and tail and len(head.group(1)) > 1 and tail.group(1) != head.group(1) \
                    and tail.group(1).endswith(head.group(1)) and not last.rstrip().endswith("-"):
                out.append(f"{where}: '{tail.group(1)}' is written whole and its end '{head.group(1)}' again on the next column?")
        elif last.rstrip().endswith("-") and re.search(r"[^\W\d_]-$", last.rstrip()):
            out.append(f"{where}: the column ends in a divided word but the next does not go on with it (+)")
    return out


def _ocr_column(md: Path, side: str) -> str:
    if not md.exists():
        return ""
    text = md.read_text(encoding="utf-8")
    title = "## OCR of the left column" if side == "left" else "## OCR of the right column"
    i = text.find(title)
    if i < 0:
        return ""
    rest = text[i:].split("\n", 1)[1]
    j = rest.find("\n## ")
    return rest if j < 0 else rest[:j]


# ---------------------------------------------------------------- the entries

def also_headwords(line: str) -> list[str]:
    """The further headwords printed in bold right after the first: '**ἁμαρτῇ**, **ἁμαρτῆ** (…)'."""
    m = ENTRY_START.match(line)
    out, i = [], m.end() if m else 0
    while m:
        m = re.compile(r",? \*\*([^*]+)\*\*").match(line, i)
        if m:
            out.append(m.group(1).strip(" ,:;."))
            i = m.end()
    return out


def entries_from(pages: dict[str, dict]) -> list[tuple[str, int, str]]:
    """(headword, homograph, text) of every entry in page order, continuations joined."""
    out: list[list] = []
    for stem in sorted(pages):
        before_break = None  # where a new letter begins halfway down the left column
        page_start = len(out)
        for side in ("left", "right"):
            for line in pages[stem][side]:
                if line.startswith("+ "):
                    if out:
                        # at the top of the right column, a page where a new letter begins halfway
                        # down goes on with the entry before the letter's heading
                        target = out[before_break] if side == "right" and before_break is not None else out[-1]
                        rest = line[2:].strip()
                        # a word divided between two columns, written as two parts ("build-", "+ ing …")
                        if re.search(r"[^\W\d_]-$", target[2]) and re.match(r"[^\W\d_]", rest) and rest[:1].islower():
                            target[2] = target[2][:-1] + rest
                        else:
                            target[2] += " " + rest
                    continue
                m = ENTRY_START.match(line)
                if not m:
                    continue
                hw = m.group(2).strip(" ,:;.()")
                if side == "left" and len(out) > page_start and sort_key(hw)[:1] and sort_key(out[-1][0])[:1] \
                        and sort_key(hw)[:1] > sort_key(out[-1][0])[:1]:
                    before_break = len(out) - 1
                out.append([hw, int(m.group(1) or 0), line])
    return [(h, n, t) for h, n, t in out]


def render(text: str) -> str:
    """An entry's line as HTML: bold headwords, italic meanings, the references to Homer muted."""
    s = html.escape(text, quote=False)
    s = re.sub(r"\*\*(.+?)\*\*", r'<b class="orth">\1</b>', s)
    s = re.sub(r"\*(.+?)\*", r'<i class="tr">\1</i>', s)
    s = re.sub(r"(?<![\w.])([Α-Ωα-ω] \d+(?:[-–]\d+)?(?: ff?\.)?(?:,? \d+(?:[-–]\d+)?(?: ff?\.)?)*)", r'<span class="bibl">\1</span>', s)
    # an entry divided into numbered senses: each sense a paragraph
    s = re.sub(r"\s*—\s*\((\d+)\)\s*", r'</p><p class="sense"><b>(\1)</b> ', s)
    s = re.sub(r"\s*—\s*([IVX]+)\.\s+", r'</p><p class="sense"><b>\1.</b> ', s)
    return f'<p class="head">{s}</p>'


def parse_autenrieth(transcriptions: Path):
    from .lexicon import Entry

    pages = read_batches(transcriptions)
    entries = []
    for hw, homograph, text in entries_from(pages):
        lemma = lemma_of(hw)
        if not lemma:
            continue
        entries.append(Entry(lexicon="autenrieth", key=hw, headword=lemma, homograph=homograph,
                             html=render(text), sort_key=greek.strip_diacritics(lemma)))
    return entries


def second_headwords(transcriptions: Path, entries: list) -> list[tuple[str, object]]:
    """(lemma key, entry) for the further bold headwords of an entry (**αἰ**, **αἴ**)."""
    by_text = {e.html: e for e in entries}
    out = []
    for _hw, _n, text in entries_from(read_batches(transcriptions)):
        e = by_text.get(render(text))
        for other in also_headwords(text):
            key = greek.lemma_key(lemma_of(other))
            if e is not None and key and key != greek.lemma_key(e.headword):
                out.append((key, e))
    return out


# ---------------------------------------------------------------- the texts' lemmas

# a lemma in the singular whose word Autenrieth lists in the plural (peoples, mostly)
PLURALS = [("ος", "οι"), ("ης", "αι"), ("η", "αι"), ("α", "αι"), ("ψ", "πες"), ("ξ", "κες"), ("ξ", "γες"),
           ("ευς", "ηες"), ("ων", "ωνες"), ("ων", "ονες"), ("ις", "ιδες")]


def _loose(word: str) -> str:
    return greek.strip_diacritics(word.replace("-", "")).replace("ς", "σ")


def extra_keys(texts: Path, entries: list, taken: set[str] = frozenset()) -> list[tuple[str, object]]:
    """(lemma key, entry) for the lemmas of the texts that read Autenrieth (their grc.txt header
    `# dictionaries:` names it) that Autenrieth lists under another spelling: other accents or
    breathing, a movable nu, or the plural (Ἀχαιοί for Ἀχαιός). A lemma whose other spelling is
    itself a lemma of the texts is a different word, and is left alone."""
    import csv

    from .build import read_aliases

    keys = {greek.lemma_key(e.headword) for e in entries} | set(taken)
    by_loose: dict[str, list] = {}
    for e in entries:
        by_loose.setdefault(_loose(e.headword), []).append(e)
    lemmas: set[str] = set()
    aliases: dict[str, str] = {}
    for work in sorted(p for p in texts.iterdir() if (p / "grc.txt").exists()):
        head = (work / "grc.txt").read_text(encoding="utf-8")[:4000]
        m = re.search(r"^# dictionaries:\s*(.*)$", head, re.M)
        if not m or "autenrieth" not in m.group(1).split() or not (work / "tokens.tsv").exists():
            continue
        aliases.update(read_aliases(work / "aliases.tsv"))
        with (work / "tokens.tsv").open(encoding="utf-8", newline="") as f:
            for r in csv.DictReader(f, delimiter="\t", quoting=csv.QUOTE_NONE):
                if r.get("lemma"):
                    lemmas.add(greek.lemma_key(r["lemma"]))
    lemma_loose = {_loose(k) for k in lemmas if k in keys}
    out = []
    for k in sorted(lemmas):
        if k in keys or aliases.get(k) in keys:
            continue
        base = _loose(k)
        tries = [(base, False), (base[:-1] if base.endswith("ν") else base + "ν", False)]
        if len(base) > 3:
            tries += [(base[: -len(a)] + b, True) for a, b in PLURALS if base.endswith(a)]
        for t, plural in tries:
            found = by_loose.get(t)
            if plural and found:
                found = [e for e in found if e.headword[:1].isupper()]
            if not found or (t != base and t in lemma_loose):
                continue
            if t == base and t in lemma_loose:
                break  # the texts have the other spelling as a word of its own
            if len({greek.lemma_key(e.headword) for e in found}) == 1:
                out += [(k, e) for e in found]
            break
    return out
