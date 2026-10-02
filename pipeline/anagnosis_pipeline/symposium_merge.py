"""Burnet's Symposium from the page-by-page transcription (pipeline/transcriptions/symposium/).

read_batches() reads the batch files; check_batch() checks one batch against the Perseus text
of Burnet's edition (which has his words but not his lines) and the OCR drafts.
"""
from __future__ import annotations

import difflib
import json
import re
import unicodedata
from pathlib import Path

from . import greek
from .linenum import STEPHANUS, SECTIONS

ITEM_N = re.compile(r"^(\d+)([a-e])(\d+)(?:-(?:(\d+)([a-e]))?(\d+))?$")


def read_batches(directory: Path) -> dict[str, dict]:
    """Page blocks by stem: {'text': [(n, line)], 'apparatus': [(n, item)], 'notes': [str], 'batch': name}.
    A '¶' line (a new paragraph) is kept in the text as ('¶', '')."""
    pages: dict[str, dict] = {}
    for path in sorted(directory.glob("batch-*.md")):
        stem, section = None, None
        for raw in path.read_text(encoding="utf-8").splitlines():
            m = re.match(r"^=== (s-\d{4})\s*$", raw)
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
            if section == "text" and raw.strip() == "¶":
                pages[stem]["text"].append(("¶", ""))
                continue
            n, sep, body = raw.partition("\t")
            if not sep:
                pages[stem].setdefault("errors", []).append(f"no TAB: {raw[:60]!r}")
                continue
            pages[stem][section].append((n.strip(), unicodedata.normalize("NFC", body.strip())))
    return pages


def _skel(s: str) -> str:
    return greek.strip_diacritics(s).replace("ς", "σ").lower()


def _words(text: str) -> list[str]:
    text = re.sub(r"\{[^}]*\}", " ", text)
    return [_skel(w) for w, _s, _e in greek.words(text)]


def perseus_sections(pages_dir: Path, sources: Path) -> list[tuple[str, str]]:
    cache = pages_dir / "perseus-sections.json"
    if cache.exists():
        return [tuple(x) for x in json.loads(cache.read_text(encoding="utf-8"))]
    from .symposium_pages import perseus_sections as read

    sections = read(sources)
    cache.write_text(json.dumps(sections, ensure_ascii=False), encoding="utf-8")
    return sections


def _key(n: str) -> tuple[int, int, int] | None:
    m = STEPHANUS.match(n)
    return (int(m.group(1)), SECTIONS.index(m.group(2)), int(m.group(3))) if m else None


def _follows(prev: tuple[int, int, int], cur: tuple[int, int, int]) -> bool:
    """Whether line cur may follow line prev: the next line, the first line of the next section,
    or the first line of the next Stephanus page."""
    return (cur == (prev[0], prev[1], prev[2] + 1) or cur == (prev[0], prev[1] + 1, 1)
            or cur == (prev[0] + 1, 0, 1))


def check_batch(path: Path, pages_dir: Path, sources: Path) -> list[str]:
    """Problems in one batch file: format, numbering, line counts against the OCR, apparatus
    numbers, and differences in wording from the Perseus text of the sections the batch covers."""
    import tempfile

    out: list[str] = []
    with tempfile.TemporaryDirectory() as tmp:
        (Path(tmp) / "batch-x.md").write_text(path.read_text(encoding="utf-8"), encoding="utf-8")
        pages = read_batches(Path(tmp))
    index = {p["stem"]: p for p in json.loads((pages_dir / "pages.json").read_text(encoding="utf-8"))}
    prev = None
    words: list[tuple[str, str, str]] = []  # (skeleton, word as written, line number)
    numbers: set[str] = set()
    for stem, block in pages.items():
        for e in block.get("errors", []):
            out.append(f"{stem}: {e}")
        if stem not in index:
            out.append(f"{stem}: unknown page")
            continue
        lines = [(n, t) for n, t in block["text"] if n != "¶"]
        draft_n = index[stem]["lines"]
        if abs(len(lines) - draft_n) > 2:
            out.append(f"{stem}: {len(lines)} lines, the OCR has {draft_n}")
        if not block["apparatus"]:
            out.append(f"{stem}: no apparatus")
        for n, text in lines:
            numbers.add(n)
            if text != unicodedata.normalize("NFC", text):
                out.append(f"{stem} {n}: not NFC")
            if re.search(r"['᾽]", text) or re.search(r"[Ͱ-Ͽἀ-῿]’", text):
                out.append(f"{stem} {n}: elision written other than ʼ")
            if re.search(r"(?<!\w)-|-$", text) or re.search(r"\w-\s*$", text):
                out.append(f"{stem} {n}: a divided word? write it whole on the line where it begins")
            for label in re.findall(r"\{([^}]*)\}", text):
                if not re.fullmatch(r"[Α-ΩΆ-Ώ]+\.", label):
                    out.append(f"{stem} {n}: odd speaker label {{{label}}}")
            cur = _key(n)
            if cur is None:
                out.append(f"{stem}: bad number {n!r}")
                continue
            if prev is not None and not _follows(prev, cur):
                out.append(f"{stem}: {n} follows {prev[0]}{SECTIONS[prev[1]]}{prev[2]}")
            prev = cur
            for w, _s, _e in greek.words(re.sub(r"\{[^}]*\}", " ", text)):
                words.append((_skel(w), w, n))
        for n, item in block["apparatus"]:
            m = ITEM_N.match(n)
            if not m:
                out.append(f"{stem}: bad apparatus number {n!r}")
                continue
            first = f"{m.group(1)}{m.group(2)}{m.group(3)}"
            if first not in numbers:
                out.append(f"{stem}: apparatus {n} names a line not on this page")
    # the wording against Perseus, over the sections the batch covers
    sections = perseus_sections(pages_dir, sources)
    keys = [STEPHANUS.match(w[2]) for w in words]
    secs = {f"{m.group(1)}{m.group(2)}" for m in keys if m}
    pw: list[str] = []
    for sec, text in sections:
        if sec in secs:
            pw.extend(_words(text))
    ours = [w[0] for w in words]
    sm = difflib.SequenceMatcher(None, ours, pw, autojunk=False)
    for op, a0, a1, b0, b1 in sm.get_opcodes():
        if op == "equal":
            continue
        if op == "insert" and (a0 == 0 or a0 == len(ours)):
            continue  # the batch begins or ends inside a section
        where = words[a0][2] if a0 < len(words) else words[-1][2]
        if op == "replace" and a1 - a0 == b1 - b0 == 1 and words[a0][1][:1].isupper():
            continue  # a capital may differ only in its accent or breathing mark
        mine = " ".join(w[1] for w in words[a0:a1]) or "(nothing)"
        theirs = " ".join(pw[b0:b1]) or "(nothing)"
        out.append(f"{where}: written {mine!s} | Perseus has {theirs}")
    return out
