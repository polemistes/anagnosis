"""Woodhouse's English-Greek Dictionary.

S. C. Woodhouse, English-Greek Dictionary: A Vocabulary of the Attic Language (London: Routledge,
1910), with the author's Supplement of Proper Names. Woodhouse died in 1955, so the book is in the
public domain (in Europe since 2026).

The text is the OCR made by Akemdwr and posted to the Internet Archive in 2018
(archive.org/details/Woodhouse, Woodhouse.dsl, an ABBYY Lingvo DSL file), corrected by us against
the 1910 scans. The DSL file is kept as downloaded; our corrections stand apart from it, in
pipeline/transcriptions/woodhouse/corrections-*.tsv, one per line:

    <line>\t<old>\t<new>\t<page>\t<note>

<line> is the line of Woodhouse.dsl (1-based, as downloaded); <old> must occur in that line
exactly once and is replaced by <new> (in both, \\t stands for a tab and \\n for a line break,
which splits a line in two). <page> is the PDF page of
the 1910 scan that shows the reading (woodhouse_pages.py). Lines starting with # are comments.
Fixes that hold for the whole text (a misreading the OCR makes throughout, a misprint the book
repeats) are rules in global.tsv, applied after the corrections, one per line:

    <regular expression>\t<replacement>\t<note>

Words that were flagged (woodhouse_qa.py) and found right in the scan are listed in
checked-*.tsv as <line>\t<word>, so that a rerun of the flagger leaves them out.

In the DSL an entry is an English headword at the start of a line, followed by its lines, each
indented with a tab: [b] marks the part of speech, [i] the English, [c brown] the marks of usage
(P., V., Ar.) and the authors, [c darkviolet] grammar (gen., mid.). Woodhouse's marks of vowel
length are colours on the vowel: red long, blue short, purple either.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path

SOURCE = "woodhouse/Woodhouse.dsl"
TRANSCRIPTIONS = Path(__file__).resolve().parent.parent / "transcriptions" / "woodhouse"


@dataclass
class Entry:
    line: int  # the headword's line in the DSL file
    headword: str
    lines: list[tuple[int, str]] = field(default_factory=list)  # (line number, text without its tab)


def _nfc(s: str) -> str:
    import unicodedata

    return unicodedata.normalize("NFC", s)


def read_lines(sources: Path) -> list[str]:
    """The DSL file's lines, in NFC (the file mixes the tonos and the oxia, ά and ά); lines[0] is line 1."""
    text = (sources / SOURCE).read_text(encoding="utf-8-sig")
    return _nfc(text.replace("\r\n", "\n")).split("\n")


def read_corrections(directory: Path = TRANSCRIPTIONS) -> list[tuple[int, str, str, str, str, str]]:
    """(line, old, new, page, note, file:line) for every correction, in file order."""
    out = []
    for path in sorted(directory.glob("corrections-*.tsv")):
        for i, raw in enumerate(path.read_text(encoding="utf-8").split("\n"), 1):
            if not raw.strip() or raw.startswith("#"):
                continue
            parts = raw.split("\t")
            if len(parts) < 3:
                raise ValueError(f"{path.name}:{i}: expected line, old, new")
            parts += [""] * (5 - len(parts))
            old, new = (_nfc(x.replace("\\t", "\t").replace("\\n", "\n")) for x in parts[1:3])
            out.append((int(parts[0]), old, new, parts[3], parts[4], f"{path.name}:{i}"))
    return out


def apply_corrections(lines: list[str], corrections) -> list[str]:
    """The lines with the corrections made; a correction whose old text is not found once fails."""
    lines = list(lines)
    errors = []
    for n, old, new, _page, _note, where in corrections:
        text = lines[n - 1]
        count = text.count(old)
        if count != 1:
            errors.append(f"{where}: line {n}: {old!r} found {count} times")
            continue
        lines[n - 1] = text.replace(old, new)
    if errors:
        raise ValueError("Woodhouse corrections that do not apply:\n" + "\n".join(errors))
    return lines


def read_checked(directory: Path = TRANSCRIPTIONS) -> set[tuple[int, str]]:
    """(line, word) of the flagged words found right in the scan."""
    out = set()
    for path in sorted(directory.glob("checked-*.tsv")):
        for raw in path.read_text(encoding="utf-8").split("\n"):
            if raw.strip() and not raw.startswith("#"):
                n, word = raw.split("\t")[:2]
                out.add((int(n), _nfc(word)))
    return out


def read_rules(directory: Path = TRANSCRIPTIONS) -> list[tuple[re.Pattern, str, str]]:
    """(pattern, replacement, note) of each rule in global.tsv."""
    path = directory / "global.tsv"
    if not path.exists():
        return []
    out = []
    for raw in path.read_text(encoding="utf-8").split("\n"):
        if raw.strip() and not raw.startswith("#"):
            parts = raw.split("\t") + [""]
            out.append((re.compile(_nfc(parts[0])), _nfc(parts[1]), parts[2]))
    return out


def apply_rules(lines: list[str], rules) -> list[str]:
    for pattern, replacement, _note in rules:
        lines = [pattern.sub(replacement, line) for line in lines]
    return lines


def corrected_lines(sources: Path) -> list[str]:
    """The DSL's lines with every correction and global rule applied."""
    return apply_rules(apply_corrections(read_lines(sources), read_corrections()), read_rules())


def entries(lines: list[str]) -> list[Entry]:
    """The dictionary's entries in order, from Abandon on (the front matter is left out).

    The DSL breaks a line after some abbreviations ("[i]I." / "T.[/i] 287)."): a line whose tags
    are left open is joined to the next, with a space, under the first line's number."""
    out: list[Entry] = []
    started = False
    # a line split by a correction keeps its number for each of its parts
    split = [(n, part) for n, line in enumerate(lines, 1) for part in line.split("\n")]
    for n, text in split:
        if not text or text.startswith("#"):
            continue
        if not text[0].isspace():
            started = started or text == "Abandon"
            if started:
                out.append(Entry(n, text.strip()))
        elif started and out:
            body = out[-1].lines
            if body and open_tags(body[-1][1]):
                body[-1] = (body[-1][0], body[-1][1] + " " + text.lstrip("\t"))
            else:
                body.append((n, text.lstrip("\t")))
    return out


TAG = re.compile(r"\[(/?)(b|i|sup|s|c(?: [a-z]+)?)\]")


def open_tags(text: str) -> list[str]:
    """The tags opened in the text and not closed, outermost first."""
    stack: list[str] = []
    for m in TAG.finditer(text):
        name = m.group(2).split(" ")[0]
        if not m.group(1):
            stack.append(name)
        elif stack and stack[-1] == name:
            stack.pop()
    return stack


def plain(text: str) -> str:
    """The text without its markup."""
    return TAG.sub("", text)


def main(sources: Path, only: str | None = None) -> None:
    """Applies the corrections (all, or those of one file) and reports those that fail; then
    counts the entries."""
    corrections = [c for c in read_corrections() if only is None or c[5].split(":")[0] == only]
    lines = apply_rules(apply_corrections(read_lines(sources), corrections), read_rules())
    es = entries(lines)
    print(f"{len(corrections)} corrections apply; {len(es)} entries; {sum(1 for e in es for _, t in e.lines if open_tags(t))} lines with open tags")


if __name__ == "__main__":
    import sys

    main(Path(__file__).resolve().parent.parent / "sources", sys.argv[1] if len(sys.argv) > 1 else None)


# ------------------------------------------------------------------ the entries as the app shows them

MACRON, BREVE = "̄", "̆"
LENGTH = {"red": MACRON, "blue": BREVE, "purple": MACRON + BREVE}
GREEK_WORD = re.compile(r"[Ͱ-Ͽἀ-῿][Ͱ-Ͽἀ-῿̀-ͯʼ]*")
ARTICLES = {"ὁ", "ἡ", "τό", "οἱ", "αἱ", "τά", "τὸ", "τὰ"}


def english_key(s: str) -> str:
    """The search key of an English headword: lower case, letters and single spaces only
    ("Advised, Be" gives "advised be", "Ædile" "aedile"). The app makes the same key of what is typed."""
    import unicodedata

    s = s.lower().replace("æ", "ae").replace("œ", "oe")
    s = "".join(c for c in unicodedata.normalize("NFD", s) if not unicodedata.combining(c))
    return " ".join(re.sub(r"[^a-z]+", " ", s).split())


def _length_marks(text: str) -> str:
    """Woodhouse's colours made marks again: the macron or breve goes on the first letter, before
    its breathing and accent, so that they stand above it (ᾰ́)."""
    import unicodedata

    def mark(m: re.Match) -> str:
        inner = unicodedata.normalize("NFD", m.group(2))
        if not inner:
            return ""
        return unicodedata.normalize("NFC", inner[0] + LENGTH[m.group(1)] + inner[1:])

    return re.sub(r"\[c (red|blue|purple)\]([^\[]*)\[/c\]", mark, text)


def _renderings(text: str) -> str:
    """The Greek renderings stand out: each run of up to three Greek words between punctuation,
    outside brackets, and not a bare article, is wrapped in <span class="tr">. Longer runs are
    quotations and stay plain. The text is HTML already; tags are passed over."""
    out = []
    depth = 0
    pos = 0
    # split into tags and text; work on the text pieces only
    for m in re.finditer(r"<[^>]+>|[^<]+", text):
        piece = m.group(0)
        if piece.startswith("<"):
            out.append(piece)
            continue
        # runs of Greek words separated only by spaces
        segs = re.split(r"([(),;:.\[\]]|\s+and\s+|\s+or\s+)", piece)
        for seg in segs:
            if seg in ("(", "["):
                depth += 1
            elif seg in (")", "]"):
                depth = max(0, depth - 1)
            words = GREEK_WORD.findall(seg)
            stripped = seg.strip()
            if (depth == 0 and words and 1 <= len(words) <= 3 and stripped == " ".join(words)
                    and not (len(words) == 1 and words[0] in ARTICLES)):
                lead = seg[: len(seg) - len(seg.lstrip())]
                trail = seg[len(seg.rstrip()):]
                out.append(f'{lead}<span class="tr">{stripped}</span>{trail}')
            else:
                out.append(seg)
        pos = m.end()
    return "".join(out)


def render_line(text: str) -> str:
    """One line of an entry as HTML."""
    import html as htmlmod

    s = _length_marks(text)
    s = htmlmod.escape(s, quote=False)
    s = re.sub(r"\[sup\]([^\[]*)\[/sup\]", r"\1", s)
    s = re.sub(r"\[s\][^\[]*\[/s\]", "", s)
    s = s.replace("[c brown]", '<span class="usg">').replace("[c darkviolet]", '<span class="gram">')
    s = re.sub(r"\[c [a-z]+\]", "<span>", s).replace("[/c]", "</span>")
    s = s.replace("[b]", "<b>").replace("[/b]", "</b>").replace("[i]", "<i>").replace("[/i]", "</i>")
    s = re.sub(r"\s+", " ", s).strip()
    return _renderings(s)


def render_entry(e: Entry) -> str:
    """The entry as HTML: the headword with its part of speech, then a paragraph per line."""
    import html as htmlmod

    lines = [t for _, t in e.lines if t.strip()]
    head = f'<b class="orth">{htmlmod.escape(e.headword, quote=False)}</b>'
    if lines and re.fullmatch(r"\[b\][^\[]*\[/b\]", lines[0].strip()):
        head += f', <span class="gram">{htmlmod.escape(lines[0].strip()[3:-4], quote=False)}</span>'
        lines = lines[1:]
    out = [f'<p class="head">{head}</p>']
    out += [f'<p class="sense">{render_line(t)}</p>' for t in lines if not re.fullmatch(r"\[i\]_+\[/i\]", t.strip())]
    return "".join(out)


def parse_woodhouse(sources: Path):
    """The dictionary's entries (lexicon.Entry), corrected; one headword printed twice (Late, adj.
    and adv.) gives homographs 1 and 2."""
    from collections import Counter

    from .lexicon import Entry as LexEntry

    es = entries(corrected_lines(sources))
    counts = Counter(english_key(e.headword) for e in es)
    seen: Counter[str] = Counter()
    out = []
    for e in es:
        key = english_key(e.headword)
        if not key:
            continue
        seen[key] += 1
        homograph = seen[key] if counts[key] > 1 else 0
        out.append(LexEntry("woodhouse", e.headword, e.headword, homograph, render_entry(e), key))
    return out
