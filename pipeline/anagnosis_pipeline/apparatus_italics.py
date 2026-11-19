"""Italics in a critical apparatus that the drama route reads as plain text.

The text batches carry the apparatus without italics (INSTRUCTIONS-text.md: "Italics are
ignored"), but Jebb prints titles and Latin words in italics there as in his commentary (*Adv.
Crit.*, *O. T.*, *sic*, *v. l.*). The apparatus of the Antigone, the Ajax and the Electra as it
stood before the plays were re-read from the page (2026-11-17) had them, read from the page by
the earlier transcription. They are kept as a table per play,

    pipeline/transcriptions/drama/<play>/apparatus-italics.tsv    heading<TAB>phrase

one line for each italic phrase of a note (`extract`, run once on the old files), and the merge
sets exactly those phrases in italics again (`apply`): a phrase is looked for in the note under
the same heading, else under a heading at most three verses away (the re-reading renumbered
some lyric verses). What is not found is reported and left upright. No rule guesses italics."""
from __future__ import annotations

import re
from pathlib import Path

ITALIC = re.compile(r"(?<![*\\])\*(?!\*)([^*\n]+?)\*(?!\*)")
HEADING = re.compile(r"^## (.+)$", re.M)


def table_path(root: Path, slug: str) -> Path:
    return root / "pipeline" / "transcriptions" / "drama" / slug / "apparatus-italics.tsv"


def notes_of(md: str) -> list[tuple[str, str]]:
    """(heading, body) of each `## heading` note; the header before the first is left out."""
    parts = HEADING.split(md)
    return [(parts[i].strip(), parts[i + 1]) for i in range(1, len(parts) - 1, 2)]


def extract(md: str) -> list[tuple[str, str]]:
    """(heading, phrase) for every italic phrase with a Latin letter in it, in the file's order.
    A single letter (*a*, *b*: a manuscript's hand) is left out: it cannot be found again safely."""
    out = []
    for heading, body in notes_of(md):
        for m in ITALIC.finditer(body):
            phrase = m.group(1).strip()
            if len(phrase) > 1 and re.search(r"[A-Za-z]", phrase):
                out.append((heading, phrase))
    return out


def read_table(path: Path) -> list[tuple[str, str]]:
    if not path.exists():
        return []
    rows = []
    for raw in path.read_text(encoding="utf-8").splitlines():
        if raw.strip() and not raw.startswith("#"):
            heading, _, phrase = raw.partition("\t")
            rows.append((heading.strip(), phrase.strip()))
    return rows


def _pattern(phrase: str) -> re.Pattern:
    """The phrase with any spacing after its stops (O. T. and O.T.), not inside a longer word,
    and not already in italics."""
    core = r"\s*".join(re.escape(t) for t in re.split(r"\s+|(?<=\.)(?=\S)", phrase) if t)
    return re.compile(rf"(?<![A-Za-z*]){core}(?![A-Za-z*])")


def _number(heading: str) -> int | None:
    m = re.match(r"\d+", heading)
    return int(m.group()) if m else None


def apply(md: str, table: list[tuple[str, str]]) -> tuple[str, list[tuple[str, str]]]:
    """The apparatus with the table's phrases in italics, and the rows not found."""
    parts = HEADING.split(md)
    index: dict[str, list[int]] = {}
    for i in range(1, len(parts) - 1, 2):
        index.setdefault(parts[i].strip(), []).append(i + 1)
    numbers = sorted({(n, h) for h in index if (n := _number(h)) is not None})
    missing = []
    for heading, phrase in table:
        pattern = _pattern(phrase)
        places = list(index.get(heading, []))
        n = _number(heading)
        if n is not None:   # the same heading first, then the nearest ones
            near = sorted((abs(m - n), h) for m, h in numbers if h != heading and abs(m - n) <= 3)
            places += [i for _d, h in near for i in index[h]]
        for i in places:
            m = pattern.search(parts[i])
            if m:
                parts[i] = parts[i][:m.start()] + "*" + m.group() + "*" + parts[i][m.end():]
                break
        else:
            missing.append((heading, phrase))
    out = [parts[0]]
    for i in range(1, len(parts) - 1, 2):
        out += [f"## {parts[i]}", parts[i + 1]]
    return "".join(out), missing
