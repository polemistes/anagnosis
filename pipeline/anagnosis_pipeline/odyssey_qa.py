"""Lines of the Odyssey transcription to look at again.

A line is listed when both OCR readings of Allen's page (A and B, from two printings) agree
on a word that the transcription lacks, while the transcription has, in its place, the word of
the Perseus draft (D), which is another edition. That is where a transcriber may have followed
the draft instead of the page. OCR errors the two readings share also turn up; the image decides.
"""
from __future__ import annotations

import difflib
import re
from collections import Counter
from pathlib import Path

from . import greek
from .odyssey_merge import read_batches


def _key(t: str) -> str:
    return re.sub(r"[^α-ω]", "", greek.strip_diacritics(t).lower().replace("ς", "σ"))


def _toks(t: str) -> list[str]:
    return [k for k in (_key(x) for x in re.split(r"[\s\-—]+", t)) if k]


def _drafts(pages_dir: Path, stem: str) -> list[dict]:
    out = []
    m = re.match(r"^(p\d-)(\d{4})$", stem)
    for k in (-1, 0, 1):
        path = pages_dir / f"{m.group(1)}{int(m.group(2)) + k:04d}.md"
        if not path.exists():
            continue
        cur = None
        for raw in path.read_text(encoding="utf-8").splitlines():
            r = re.match(r"^([\d.a-z]+)?\t(D|A|B): (.*)$", raw)
            if not r:
                continue
            if r.group(1):
                cur = {"n": r.group(1)}
                out.append(cur)
            if cur is not None:
                cur[r.group(2)] = r.group(3)
    return out


def flag(transcriptions: Path, pages_dir: Path) -> list[dict]:
    pages = read_batches(transcriptions)
    found = []
    for stem in sorted(pages):
        drafts = _drafts(pages_dir, stem)
        for n, text in pages[stem]["text"]:
            t = _toks(text)
            # the draft entry that best matches this line
            best, score = None, 0.0
            for d in drafts:
                s = difflib.SequenceMatcher(None, t, _toks(d.get("D", ""))).ratio()
                if s > score:
                    best, score = d, s
            if best is None or score < 0.5:
                continue
            a, b, dd = Counter(_toks(best.get("A", ""))), Counter(_toks(best.get("B", ""))), Counter(_toks(best.get("D", "")))
            tc = Counter(t)
            ocr_both = {w for w in a if w in b and len(w) > 1}
            missing = [w for w in ocr_both if tc[w] < min(a[w], b[w]) and dd[w] < min(a[w], b[w])]
            from_draft = [w for w in tc if dd[w] and not a[w] and not b[w] and len(w) > 1]
            if missing and from_draft:
                found.append({"stem": stem, "n": n, "text": text, "A": best.get("A", ""), "B": best.get("B", ""),
                              "D": best.get("D", ""), "ocr": " ".join(missing), "draft": " ".join(from_draft)})
    return found


def write_report(found: list[dict], out: Path) -> None:
    lines = ["# Odyssey transcription: lines to check against the page", ""]
    for f in found:
        lines.append(f"## {f['n']} ({f['stem']})")
        lines.append(f"transcribed: {f['text']}")
        lines.append(f"both OCRs: {f['ocr']}  |  transcription and Perseus: {f['draft']}")
        lines.append(f"A: {f['A']}")
        lines.append(f"B: {f['B']}")
        lines.append("")
    out.write_text("\n".join(lines) + "\n", encoding="utf-8")
