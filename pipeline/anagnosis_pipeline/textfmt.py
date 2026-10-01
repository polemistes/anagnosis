"""The editable plain-text format used for texts and translations in texts/.

    # key: value            header line (only before the first content line)
    // comment              ignored
    == kind [label]         section, level = number of '=' minus 1 (== is level 1)
    @ Speaker               speaker change (empty name closes the speech)
    !<TAB>text              stage direction
    <n><TAB>text            a line; n is digits optionally followed by a letter (161b),
                            or book.line for an epic (1.12)

For translations, <n> is the first Greek line the paragraph corresponds to.
Blank lines are ignored. A document is a flat, ordered list of items.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path

from .linenum import LINE_N, parts as _n_parts


@dataclass
class Section:
    level: int
    kind: str
    label: str = ""


@dataclass
class Speaker:
    name: str


@dataclass
class Stage:
    text: str


@dataclass
class Line:
    n: str
    text: str

    @property
    def sort_key(self) -> tuple[int, str]:
        return _n_parts(self.n)


Item = Section | Speaker | Stage | Line


@dataclass
class Document:
    meta: dict[str, str] = field(default_factory=dict)
    items: list[Item] = field(default_factory=list)

    @property
    def lines(self) -> list[Line]:
        return [i for i in self.items if isinstance(i, Line)]


def parse(text: str, source: str = "<string>") -> Document:
    doc = Document()
    seen_content = False
    for lineno, raw in enumerate(text.splitlines(), 1):
        s = raw.rstrip()
        if not s.strip() or s.startswith("//"):
            continue
        if s.startswith("#"):
            if seen_content:
                raise ValueError(f"{source}:{lineno}: header after content")
            key, _, value = s[1:].partition(":")
            doc.meta[key.strip()] = value.strip()
            continue
        seen_content = True
        if s.startswith("="):
            m = re.match(r"^(=+)\s*(\S+)\s*(.*)$", s)
            if not m:
                raise ValueError(f"{source}:{lineno}: bad section line")
            doc.items.append(Section(len(m.group(1)) - 1, m.group(2), m.group(3).strip()))
        elif s.startswith("@"):
            doc.items.append(Speaker(s[1:].strip()))
        elif s.startswith("!"):
            doc.items.append(Stage(s[1:].strip()))
        else:
            n, sep, body = s.partition("\t")
            if not sep or not LINE_N.match(n.strip()):
                raise ValueError(f"{source}:{lineno}: expected '<n><TAB>text', got {s[:40]!r}")
            doc.items.append(Line(n.strip(), body.strip()))
    return doc


def parse_file(path: Path) -> Document:
    return parse(path.read_text(encoding="utf-8"), str(path))


def serialize(doc: Document) -> str:
    out: list[str] = []
    for k, v in doc.meta.items():
        out.append(f"# {k}: {v}")
    if doc.meta:
        out.append("")
    prev: Item | None = None
    for item in doc.items:
        if isinstance(item, Section):
            if prev is not None:
                out.append("")
            label = f" {item.label}" if item.label else ""
            out.append(f"{'=' * (item.level + 1)} {item.kind}{label}")
        elif isinstance(item, Speaker):
            if prev is not None and not isinstance(prev, Section):
                out.append("")
            out.append(f"@ {item.name}")
        elif isinstance(item, Stage):
            out.append(f"!\t{item.text}")
        elif isinstance(item, Line):
            out.append(f"{item.n}\t{item.text}")
        prev = item
    return "\n".join(out) + "\n"


def write_file(path: Path, doc: Document) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(serialize(doc), encoding="utf-8")
