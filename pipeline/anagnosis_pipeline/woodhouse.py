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
exactly once and is replaced by <new> (in both, \\t stands for a tab). <page> is the PDF page of
the 1910 scan that shows the reading (woodhouse_pages.py). Lines starting with # are comments.
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


def read_lines(sources: Path) -> list[str]:
    """The DSL file's lines; lines[0] is line 1."""
    text = (sources / SOURCE).read_text(encoding="utf-8-sig")
    return text.replace("\r\n", "\n").split("\n")


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
            old, new = (x.replace("\\t", "\t") for x in parts[1:3])
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
                out.add((int(n), word))
    return out


def entries(lines: list[str]) -> list[Entry]:
    """The dictionary's entries in order, from Abandon on (the front matter is left out).

    The DSL breaks a line after some abbreviations ("[i]I." / "T.[/i] 287)."): a line whose tags
    are left open is joined to the next, with a space, under the first line's number."""
    out: list[Entry] = []
    started = False
    for n, text in enumerate(lines, 1):
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


def main(sources: Path) -> None:
    """Applies every correction and reports those that fail; then counts the entries."""
    lines = apply_corrections(read_lines(sources), read_corrections())
    es = entries(lines)
    print(f"{len(read_corrections())} corrections apply; {len(es)} entries; {sum(1 for e in es for _, t in e.lines if open_tags(t))} lines with open tags")


if __name__ == "__main__":
    import sys

    main(Path(sys.argv[1]) if len(sys.argv) > 1 else Path(__file__).resolve().parent.parent / "sources")
