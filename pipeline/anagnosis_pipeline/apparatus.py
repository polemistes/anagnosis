"""Tools for the critical apparatus transcription: merge batches and verify lemmas."""
from __future__ import annotations

import re
import sys
from pathlib import Path

from . import greek
from .commentary import parse_commentary_md
from .linenum import N_PATTERN, parts
from .textfmt import parse_file

HEADER = """# title: Critical notes
# author: Richard C. Jebb
# lang: eng
# source: Sophocles, The Plays and Fragments, Part III: The Antigone, 2nd ed., Cambridge University Press 1891 (critical notes), transcribed from the Internet Archive scan sophocles03soph
# license: CC BY-SA 4.0 (transcription; the 1891 edition is in the public domain)
"""


def merge(batch_dir: Path, out: Path) -> int:
    """Concatenate batch-NN.md files in order, merging repeated headings."""
    entries: dict[str, list[str]] = {}
    order: list[str] = []
    for path in sorted(batch_dir.glob("batch-*.md")):
        current = None
        for raw in path.read_text(encoding="utf-8").splitlines():
            m = re.match(rf"^##\s+({N_PATTERN}(?:-{N_PATTERN})?)\s*$", raw)
            if m:
                current = m.group(1)
                if current not in entries:
                    entries[current] = []
                    order.append(current)
                elif entries[current] and entries[current][-1].strip():
                    entries[current].append("")
                continue
            if current is not None and not raw.startswith("# ") and not raw.startswith("*Sigla.*"):
                entries[current].append(raw)  # the sigla preface lives in sigla.md instead
    lines = [HEADER]
    for n in order:
        body = "\n".join(entries[n]).strip("\n")
        lines.append(f"## {n}\n{body}\n")
    out.write_text("\n".join(lines), encoding="utf-8")
    return len(order)


def _loose(s: str) -> str:
    """Diacritics stripped, final sigma and iota adscript normalised, for fuzzy matching."""
    t = greek.strip_diacritics(s).replace("ς", "σ")
    return re.sub(r"([αηω])ι\b", r"\1", t)


def _norm(s: str) -> str:
    return greek.nfc(s).replace("’", "").replace("'", "").replace("ʼ", "").replace("᾽", "")


def verify(apparatus: Path, grc: Path, show_accents: bool = False) -> int:
    """Report lemmas most of whose words do not occur near their line.

    Jebb also prints manuscript readings in bold, so single missing words are normal; an entry
    is reported when fewer than half of a lemma's Greek words occur (ignoring diacritics)
    within two lines before and three lines after the cited line.
    """
    doc = parse_file(grc)
    lines = doc.lines
    by_n = {l.n: i for i, l in enumerate(lines)}
    ints = sorted({parts(l.n)[0] for l in lines})
    by_int = {}
    for l in lines:
        by_int.setdefault(parts(l.n)[0], l.n)
    meta, notes = parse_commentary_md(apparatus)
    problems = 0
    accents = 0
    prev_int = 0
    for note in notes:
        n = note["from"]
        n_int = parts(n)[0]
        if n_int < prev_int:
            print(f"ORDER  {n}: out of order (after {prev_int})")
            problems += 1
        prev_int = n_int
        idx = by_n.get(n)
        if idx is None:
            later = [i for i in ints if i >= n_int]
            idx = by_n.get(by_int[later[0]]) if later else None
        if idx is None:
            print(f"NOLINE {n}: no such line")
            problems += 1
            continue
        to_int = parts(note["to"])[0]
        end = idx
        while end + 1 < len(lines) and parts(lines[end + 1].n)[0] <= to_int:
            end += 1
        window = " ".join(l.text for l in lines[max(0, idx - 2) : end + 4])
        window_loose = _loose(window)
        window_exact = _norm(window)
        # all Greek words quoted in the entry (bold lemmas and MS readings alike)
        words = [w for w in re.split(r"[\s,;·.|\*\]\[()—]+", _norm(note["body"])) if re.search(r"[Ͱ-Ͽἀ-῿]", w) and len(w) > 2]
        if not words:
            continue
        hits = [w for w in words if _loose(w) in window_loose]
        if not hits or (len(words) >= 4 and len(hits) * 3 < len(words)):
            print(f"MISS   {n}: {len(hits)}/{len(words)} quoted words near line {n} ({lines[idx].text[:50]}): {' '.join(words[:8])}")
            problems += 1
        else:
            diff = [w for w in hits if w not in window_exact]
            if diff:
                accents += 1
                if show_accents:
                    print(f"ACCENT {n}: {diff} vs {lines[idx].text[:60]}")
    print(f"{len(notes)} entries, {problems} problems, {accents} lemmas with accent/spelling differences (mostly MS readings)")
    return problems


APPENDIX_HEADER = """# title: Appendix
# author: Richard C. Jebb
# source: Sophocles, The Plays and Fragments, Part III: The Antigone, 2nd ed., Cambridge University Press 1891, Appendix (pp. 241-268), transcribed from the Internet Archive scan sophocles03soph
# license: CC BY-SA 4.0 (transcription; the 1891 edition is in the public domain)

"""


def merge_appendix(batch_dir: Path, out: Path) -> int:
    """Concatenate appendix-NN.md files into the Appendix document (headings become 'Line n')."""
    parts: list[str] = []
    n = 0
    for path in sorted(batch_dir.glob("appendix-*.md")):
        for raw in path.read_text(encoding="utf-8").splitlines():
            m = re.match(r"^##\s+(.+?)\s*$", raw)
            if m:
                label = m.group(1).replace("-", "–")
                if parts and parts[-1] != "":
                    parts.append("")
                parts.append(f"## Line{'s' if '–' in label else ''} {label}")
                parts.append("")
                n += 1
            elif not raw.startswith("# "):
                parts.append(raw)
    out.write_text(APPENDIX_HEADER + "\n".join(parts).strip() + "\n", encoding="utf-8")
    return n
