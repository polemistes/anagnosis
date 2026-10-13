"""Find the words of the Woodhouse OCR that need a look at the scan.

Writes pipeline/build/woodhouse-flags.tsv, one suspect per line:

    <line>\t<kind>\t<token>\t<page>\t<headword>\t<text of the line>

Kinds:
    greek     a Greek word whose letters are found nowhere (Morpheus forms, LSJ, Middle Liddell)
    accent    a Greek word whose letters are known but not with these accents and breathings
    english   an English word found in no English source we have, and at most twice in Woodhouse
    mixed     a word that mixes Greek and Latin letters (ο for o, Ρ for P)
    markup    a line whose tags do not pair up

<page> is the page of the 1910 scan (woodhouse-1910-english-attic-greek-dictionary, the PDF page)
where the entry's headword was found, or the last page found before it.

The corrections made after looking go to pipeline/transcriptions/woodhouse/ (see woodhouse.py).
Corrections already made are applied first, so that a rerun lists what is left.
"""
from __future__ import annotations

import gzip
import json
import re
import subprocess
import sys
import unicodedata
from collections import Counter
from pathlib import Path

from . import woodhouse
from .greek import strip_diacritics

SCAN = "scans/woodhouse-1910-english-attic-greek-dictionary.pdf"
GREEK = re.compile(r"[Ͱ-Ͽἀ-῿][Ͱ-Ͽἀ-῿̀-ͯ]*")
LATIN = re.compile(r"[A-Za-z]+")
ANY_WORD = re.compile(r"[A-Za-zͰ-Ͽἀ-῿][A-Za-zͰ-Ͽἀ-῿̀-ͯ]*")
GRAVE = "̀"
ACUTE = "́"
ACCENTS = {"́", "̀", "͂"}


def _is_greek(c: str) -> bool:
    return "Ͱ" <= c <= "Ͽ" or "ἀ" <= c <= "῿"


def accent_form(word: str) -> str:
    """The word compared for its accents: lower case, a grave written acute, a second accent
    (thrown back by an enclitic) dropped, length marks dropped, NFC."""
    d = unicodedata.normalize("NFD", word.lower()).replace(GRAVE, ACUTE)
    d = d.replace("̄", "").replace("̆", "")
    marks = [i for i, c in enumerate(d) if c in ACCENTS]
    if len(marks) > 1:
        d = d[: marks[-1]] + d[marks[-1] + 1 :]
    return unicodedata.normalize("NFC", d).replace("ς", "σ")


def greek_vocabulary(sources: Path) -> tuple[set[str], set[str]]:
    """(letters only, with accents) of every Greek word in Morpheus' analyses, LSJ and Middle Liddell."""
    build = sources.parent / "build"
    loose: set[str] = set()
    accented: set[str] = set()

    def add(w: str) -> None:
        loose.add(strip_diacritics(w).replace("ς", "σ"))
        accented.add(accent_form(w))

    with gzip.open(build / "morpheus-analyses.tsv.gz", "rt", encoding="utf-8") as f:
        for row in f:
            form = row.split("\t", 1)[0]
            add(form)
    for name in ("lsj.jsonl", "ml.jsonl"):
        with open(build / name, encoding="utf-8") as f:
            for row in f:
                e = json.loads(row)
                add(e["headword"])
                for w in GREEK.findall(re.sub(r"<[^>]+>", " ", e["html"])):
                    add(w)
    return loose, accented


def english_vocabulary(sources: Path) -> set[str]:
    """Lower-case English words of the definitions in LSJ and Middle Liddell and of the translations."""
    build = sources.parent / "build"
    words: set[str] = set()
    for name in ("lsj.jsonl", "ml.jsonl"):
        with open(build / name, encoding="utf-8") as f:
            for row in f:
                words.update(w.lower() for w in LATIN.findall(re.sub(r"<[^>]+>", " ", json.loads(row)["html"])))
    for path in list(sources.glob("*eng*.xml")) + list(sources.glob("*commentary.xml")) + list((sources / "jowett").glob("*")):
        if path.is_file():
            words.update(w.lower() for w in LATIN.findall(path.read_text(encoding="utf-8", errors="replace")))
    dict_words = Path("/usr/share/dict/cracklib-small")
    if dict_words.exists():
        words.update(w.strip().lower() for w in dict_words.read_text(errors="replace").split("\n"))
    return words


def scan_pages(sources: Path) -> list[str]:
    """The text of every page of the 1910 scan (its own OCR), page 1 first."""
    out = subprocess.run(["pdftotext", "-enc", "UTF-8", str(sources / SCAN), "-"], capture_output=True, check=True).stdout
    return out.decode("utf-8").split("\f")


def headword_pages(entries: list, pages: list[str], supplement: int | None) -> dict[int, int]:
    """The PDF page of each entry (by its line): the first page, from the previous entry's on and
    up to 15 pages ahead (2 in the Supplement, whose OCR runs the columns together), where a line
    begins with the headword and a comma or full stop; else the previous entry's page."""
    out: dict[int, int] = {}
    current = 1
    for e in entries:
        word = e.headword.split(",")[0].split(" ")[0]
        pat = re.compile(r"(?m)^\s*" + re.escape(word) + r"\s*[,.]")
        ahead = 3 if supplement is not None and e.line >= supplement else 15
        for p in range(current, min(current + ahead, len(pages) + 1)):
            if pat.search(pages[p - 1]):
                current = p
                break
        out[e.line] = current
    return out


def unbalanced(text: str) -> bool:
    stack: list[str] = []
    for m in woodhouse.TAG.finditer(text):
        name = m.group(2).split(" ")[0]
        if m.group(1):
            if not stack or stack[-1] != name:
                return True
            stack.pop()
        else:
            stack.append(name)
    return bool(stack)


def _neighbours(word: str) -> set[str]:
    """Words one letter away: a letter changed, dropped, added, or two swapped."""
    letters = "abcdefghijklmnopqrstuvwxyz"
    splits = [(word[:i], word[i:]) for i in range(len(word) + 1)]
    return ({a + b[1:] for a, b in splits if b} | {a + c + b[1:] for a, b in splits if b for c in letters}
            | {a + c + b for a, b in splits for c in letters} | {a + b[1] + b[0] + b[2:] for a, b in splits if len(b) > 1})


def lemma_key(lemma: str) -> str:
    return strip_diacritics(re.sub(r"\d+$", "", lemma)).replace("ς", "σ")


def main(sources: Path) -> None:
    from .morpheus_forms import run_morpheus

    lines = woodhouse.corrected_lines(sources)
    entries = woodhouse.entries(lines)
    print("vocabularies ...", file=sys.stderr)
    loose, accented = greek_vocabulary(sources)
    english = english_vocabulary(sources)
    headwords = set()
    for name in ("lsj.jsonl", "ml.jsonl"):
        with open(sources.parent / "build" / name, encoding="utf-8") as f:
            headwords.update(lemma_key(json.loads(row)["headword"]) for row in f)
    # the Supplement of Proper Names follows the last entry of the dictionary, Zone
    supplement = next((entries[i + 1].line for i, e in enumerate(entries[:-1]) if e.headword == "Zone"), None)
    print("scan pages ...", file=sys.stderr)
    pages = headword_pages(entries, scan_pages(sources), supplement)
    checked = woodhouse.read_checked()

    # each entry's physical lines: from its headword to the line before the next headword
    spans = []
    for i, e in enumerate(entries):
        end = entries[i + 1].line if i + 1 < len(entries) else len(lines) + 1
        spans.append((e, [(n, lines[n - 1]) for n in range(e.line, end) if lines[n - 1].strip()]))

    # how often each English word occurs in Woodhouse itself
    en_count: Counter[str] = Counter()
    for _, phys in spans:
        for _, text in phys:
            en_count.update(w.lower() for w in LATIN.findall(woodhouse.plain(text)))
    common = {w for w, c in en_count.items() if c >= 5}

    # the Greek words not attested with these accents, given to Morpheus
    words = set()
    for _, phys in spans:
        for _, text in phys:
            words.update(w for w in GREEK.findall(woodhouse.plain(text)) if accent_form(w) not in accented and not w.endswith("ʼ"))
    print(f"morpheus: {len(words)} words ...", file=sys.stderr)
    analysed = run_morpheus(sorted(words), sources / "morpheus")

    def good(w: str) -> bool:
        return any(lemma_key(lem) in headwords and (not dial or re.search(r"attic|epic|ionic", dial))
                   for lem, _tag, dial in analysed.get(w, []))

    flags = []
    counts: Counter[str] = Counter()
    for e, phys in spans:
        def row(n, kind, tok, text):
            if (n, tok) not in checked:
                flags.append((n, kind, tok, pages[e.line], e.headword, text)); counts[kind] += 1
        for n, text in e.lines:
            if unbalanced(text):
                row(n, "markup", "", text)
        in_supplement = supplement is not None and e.line >= supplement
        # a headword with markup, Greek, a colon or a small letter is a line of the entry before
        h = e.headword
        if re.search(r"[\[\]:;Ͱ-Ͽἀ-῿]", h) or h[0].islower() or len(h) > 40:
            row(e.line, "headword", h, h)
        elif not in_supplement:
            for tok in LATIN.findall(h):
                low = tok.lower()
                if low not in english and en_count[low] <= 2 and _neighbours(low) & common:
                    row(e.line, "headword", tok, h)
        for n, text in phys:
            if n == e.line:
                continue  # the headword
            p = woodhouse.plain(text)
            for tok in ANY_WORD.findall(p):
                has_g = any(_is_greek(c) for c in tok)
                has_l = any(c.isascii() and c.isalpha() for c in tok)
                if has_g and has_l:
                    row(n, "mixed", tok, text)
                elif has_g:
                    if tok.endswith("ʼ") or accent_form(tok) in accented or good(tok):
                        continue
                    key = strip_diacritics(tok).replace("ς", "σ")
                    row(n, "accent" if key in loose else "greek", tok, text)
                elif not in_supplement and len(tok) > 1:
                    low = tok.lower()
                    if low not in english and en_count[low] <= 2 and _neighbours(low) & common:
                        row(n, "english", tok, text)
            # a Greek letter among the marks of usage (Ρ. for P.)
            for m in re.finditer(r"\[c brown\]([^\[]*)\[/c\]", text):
                if any(_is_greek(c) for c in m.group(1)):
                    row(n, "mixed", m.group(1), text)

    out = sources.parent / "build" / "woodhouse-flags.tsv"
    with open(out, "w", encoding="utf-8") as f:
        for n, kind, tok, page, head, text in flags:
            f.write(f"{n}\t{kind}\t{tok}\t{page}\t{head}\t{text}\n")
    print(f"{out}: {len(flags)} flags " + ", ".join(f"{k} {v}" for k, v in counts.most_common()), file=sys.stderr)


if __name__ == "__main__":
    main(Path(sys.argv[1]) if len(sys.argv) > 1 else Path(__file__).resolve().parent.parent / "sources")
