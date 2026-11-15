#!/usr/bin/env python3
"""Route comparison, the mechanical half: Jebb's Trachiniae, pages 80-142 (the text) and 80-143
(the critical apparatus), as transcribed by route E (by eye: transcriptions/sophocles/trachiniae)
and by route O (OCR + flags: transcriptions/drama/trachiniae), compared word by word.

    pipeline/.venv/bin/python research/route-comparison/compare.py --state 854a0cb --out DIR
    pipeline/.venv/bin/python research/route-comparison/compare.py --state worktree --out DIR

--state is the state of route O: a git commit, or "worktree" for the files as they are on disk.
Route E is always read from the working tree (its files are finished).

Writes into DIR:
  items.jsonl         one disagreement per line, readings shuffled (for the blind adjudicators)
  key.jsonl           which reading is which route, and each one's relation to the reference
  summary.md          counts by kind, excluded convention differences, warnings
  verse-division.md   differences in verse division and numbering (reported, not adjudicated)
  streams/            the two normalised texts and apparatus, for inspection
"""
from __future__ import annotations

import argparse
import difflib
import json
import random
import re
import subprocess
import sys
import unicodedata
from collections import Counter, defaultdict
from dataclasses import dataclass, field
from pathlib import Path

PIPE = Path(__file__).resolve().parents[2]  # pipeline/
REPO = PIPE.parent
sys.path.insert(0, str(PIPE))

from anagnosis_pipeline.sophocles_pages import join_run_on, read_batches, read_reference, text_check  # noqa: E402

E_DIR = PIPE / "transcriptions/sophocles/trachiniae"
O_REL = "pipeline/transcriptions/drama/trachiniae"
FIRST_PAGE, LAST_TEXT_PAGE, LAST_APP_PAGE = 80, 142, 143
SEED = "trachiniae-route-comparison-2026-11-15"

ELISION = "’᾽ʼ'᾿"  # ’ ᾽ ʼ ' ᾿  -> ʼ
SUPERSCRIPT = str.maketrans("¹²³⁴⁵⁶⁷⁸⁹⁰", "1234567890")
GREEK = re.compile(r"[Ͱ-Ͽἀ-῿]")
OPENERS = "([⟨†‘“"
BRACKETS = set("[]⟨⟩†*")


def nfc(s: str) -> str:
    return unicodedata.normalize("NFC", s)


def page_no(stem: str) -> int:
    return int(stem[2:])


# ------------------------------------------------------------------ conventions, counted

class Conventions:
    """Differences by rule, not by reading: normalised away and counted per route."""

    def __init__(self):
        self.counts: dict[tuple[str, str, str], int] = Counter()  # (part, rule, route) -> n

    def add(self, part: str, rule: str, route: str, n: int = 1):
        if n:
            self.counts[(part, rule, route)] += n

    def sub(self, part, rule, route, pattern, repl, text, flags=0):
        new, n = re.subn(pattern, repl, text, flags=flags)
        self.add(part, rule, route, n)
        return new


CONV = Conventions()


def unify_elision(text: str, part: str, route: str) -> str:
    n = sum(text.count(c) for c in ELISION if c != "ʼ")
    CONV.add(part, "elision / apostrophe mark ’ ᾽ ' written ʼ", route, n)
    for c in ELISION:
        text = text.replace(c, "ʼ")
    return text


def norm_text_line(text: str, route: str) -> str:
    """A verse line of either route in one convention."""
    text = nfc(text)
    text = unify_elision(text, "text", route)
    text = CONV.sub("text", "asterisk before a conjecture (route O leaves it out by rule)", route,
                    r"\*(?=\S)", "", text)
    n = text.count("<") + text.count(">")
    CONV.add("text", "angle brackets < > written ⟨ ⟩ (pairs ×2)", route, n)
    text = text.replace("<", "⟨").replace(">", "⟩")
    return re.sub(r"\s+", " ", text).strip()


# ------------------------------------------------------------------ route O files

def o_files(state: str) -> dict[str, str]:
    if state == "worktree":
        d = REPO / O_REL
        return {p.name: p.read_text(encoding="utf-8") for p in sorted(d.glob("batch-*.md"))}
    names = subprocess.run(["git", "-C", str(REPO), "ls-tree", "--name-only", state, O_REL + "/"],
                           check=True, capture_output=True, text=True).stdout.split()
    out = {}
    for path in names:
        name = path.rsplit("/", 1)[-1]
        if re.match(r"batch-\d+\.md$", name):
            out[name] = subprocess.run(["git", "-C", str(REPO), "show", f"{state}:{path}"],
                                       check=True, capture_output=True, text=True).stdout
    return dict(sorted(out.items()))


def read_o(state: str) -> dict[str, dict]:
    pages: dict[str, dict] = {}
    for name, content in o_files(state).items():
        stem = section = None
        for raw in content.splitlines():
            m = re.match(r"^=== (p-\d{4})\s*$", raw)
            if m:
                stem = m.group(1)
                pages[stem] = {"text": [], "apparatus": [], "notes": [], "batch": name}
                section = None
                continue
            m = re.match(r"^--- (text|apparatus|notes)\s*$", raw)
            if m:
                section = m.group(1)
                continue
            if stem and section and raw.strip():
                pages[stem][section].append(raw.rstrip("\n"))
    return pages


# ------------------------------------------------------------------ the text: lines

@dataclass
class VLine:
    n: str          # verse number as that route has it
    text: str
    page: int | None = None
    ref: str | None = None  # for route E: the reference line it came from


def reference_lines() -> list[VLine]:
    out = []
    for raw in (E_DIR / "reference-grc.txt").read_text(encoding="utf-8").splitlines():
        m = re.match(r"^(\d+[a-z]?)\t(.*)$", raw)
        if m:
            out.append(VLine(m.group(1), nfc(m.group(2)), ref=m.group(1)))
    return out


def _find(text: str, ours: str) -> int:
    """Position of `ours` in `text`, preferring a match on word boundaries."""
    pat = r"(?<![^\s⟨\[(†])" + re.escape(ours) + r"(?=$|[\s,.·;:!?⟩\])—])"
    m = re.search(pat, text)
    if m:
        return m.start()
    return text.find(ours)


def route_e_lines(warnings: list[str]) -> tuple[list[VLine], list[tuple[str, bool, str, str, str]]]:
    """The reference with route E's differences applied (only the pages 80-142)."""
    pages = read_batches(E_DIR)
    lines = [VLine(l.n, l.text, ref=l.ref) for l in reference_lines()]
    diffs = []
    for stem in sorted(pages):
        if not FIRST_PAGE <= page_no(stem) <= LAST_TEXT_PAGE:
            continue
        for raw in pages[stem]["differences"]:
            m = re.match(r"^(\d+[a-z]?)(\+?): ours «(.*)» print «(.*)»\s*$", raw)
            if not m:
                warnings.append(f"route E {stem}: difference line not understood: {raw}")
                continue
            diffs.append((m.group(1), bool(m.group(2)), m.group(3), m.group(4), stem))
    elide = lambda s: "".join("ʼ" if c in ELISION else c for c in nfc(s))  # noqa: E731
    for n, insert, ours, printed, stem in diffs:
        ours_n = elide(ours)
        printed_raw = nfc(printed)  # conventions are normalised later, with the whole line
        idx = next((i for i, l in enumerate(lines) if l.ref == n), None)
        if idx is None:
            nums = [(i, int(re.match(r"\d+", l.ref).group())) for i, l in enumerate(lines) if l.ref]
            target = int(re.match(r"\d+", n).group())
            idx = min(nums, key=lambda t: abs(t[1] - target))[0]
        if insert:
            lines.insert(idx + 1, VLine(n + "+", printed_raw, ref=None))
            continue
        window = sorted(range(max(0, idx - 8), min(len(lines), idx + 9)), key=lambda i: abs(i - idx))
        hit = None
        if ours_n:
            hit = next((i for i in window if _find(elide(lines[i].text), ours_n) >= 0), None)
            if hit is None:
                warnings.append(f"route E {stem}: «{ours}» not found near {n}; difference not applied")
                continue
        else:
            hit = idx
        line = lines[hit]
        if hit != idx:
            warnings.append(f"route E {stem}: «{ours}» at {n} found in line {line.ref} instead")
        t = elide(line.text)
        if not printed_raw.strip() and ours_n.strip() == t.strip():
            del lines[hit]
        elif ours_n:
            p = _find(t, ours_n)
            line.text = t[:p] + printed_raw + t[p + len(ours_n):]
        else:
            line.text = (t + " " + printed_raw).strip()
    return lines, diffs


def route_o_lines(pages: dict[str, dict]) -> tuple[list[VLine], list[tuple[int, str]]]:
    out, speakers = [], []
    for stem in sorted(pages):
        p = page_no(stem)
        if not FIRST_PAGE <= p <= LAST_TEXT_PAGE:
            continue
        for raw in pages[stem]["text"]:
            if raw.startswith("@"):
                speakers.append((len(out), raw[1:].strip()))
                continue
            if raw.startswith("!"):
                out.append(VLine("!", raw[1:].strip(), page=p))
                continue
            m = re.match(r"^(\d+[a-z]?)\t(.*)$", raw)
            if m:
                out.append(VLine(m.group(1), nfc(m.group(2)), page=p))
    return out, speakers


# ------------------------------------------------------------------ the text: tokens

@dataclass
class Tok:
    form: str
    skel: str
    verse: str
    page: int | None
    starts: bool  # first word of its verse line


def skeleton(s: str) -> str:
    d = unicodedata.normalize("NFD", s.lower())
    d = "".join(c for c in d if not unicodedata.combining(c))
    d = d.replace("ς", "σ").replace("ϲ", "σ")
    return "".join(c for c in d if c.isalpha())


def tokenize_lines(lines: list[VLine], route: str) -> list[Tok]:
    toks: list[Tok] = []
    pending = ""  # an opening bracket or dagger standing alone, for the next word
    for line in lines:
        text = norm_text_line(line.text, route)
        first = True
        for w in text.split(" "):
            if not w:
                continue
            if not any(c.isalpha() for c in w):
                if all(c in OPENERS for c in w):
                    pending += w
                elif toks:
                    toks[-1].form += w
                else:
                    pending += w
                continue
            w = pending + w
            pending = ""
            toks.append(Tok(w, skeleton(w), line.n if route != "R" else line.ref, line.page, first))
            first = False
    return toks


def segments(a: list[Tok], b: list[Tok]) -> list[tuple[int, int, int, int]]:
    """Alignment of a (the reference) with b, on the letters only, as segments
    (a0, a1, b0, b1); matched words are one segment each."""
    sm = difflib.SequenceMatcher(None, [t.skel for t in a], [t.skel for t in b], autojunk=False)
    out = []
    for op, a0, a1, b0, b1 in sm.get_opcodes():
        if op == "equal":
            out.extend((a0 + k, a0 + k + 1, b0 + k, b0 + k + 1) for k in range(a1 - a0))
        else:
            out.append((a0, a1, b0, b1))
    return out


def regions(nref: int, seg_e, seg_o):
    """Regions of the reference on which both alignments agree to cut, each with the route E and
    route O words that answer it. Yields (r0, r1, (e0, e1), (o0, o1))."""
    def cuts(segs):
        c = set()
        for a0, a1, _, _ in segs:
            c.add(a0)
            c.add(a1)
        return c

    common = sorted(cuts(seg_e) & cuts(seg_o) | {0, nref})

    def span(segs, r0, r1):
        if r0 < r1:
            sel = [s for s in segs if (s[0] < s[1] and r0 <= s[0] and s[1] <= r1)
                   or (s[0] == s[1] and r0 < s[0] < r1)]
        else:
            sel = [s for s in segs if s[0] == s[1] == r0]
        if not sel:
            return None
        return min(s[2] for s in sel), max(s[3] for s in sel)

    out = []
    for i, k in enumerate(common):
        out.append((k, k))  # insertions at this cut
        if i + 1 < len(common):
            out.append((k, common[i + 1]))
    for r0, r1 in out:
        e, o = span(seg_e, r0, r1), span(seg_o, r0, r1)
        yield r0, r1, e, o


def render(forms: list[str]) -> str:
    return " ".join(forms)


def classify_text(ef: list[str], of: list[str]) -> tuple[str, list[str]]:
    if not ef or not of:
        return "text-missing-word", ["word present in only one"]
    se, so = skeleton("".join(ef)), skeleton("".join(of))
    if se != so:
        return "text-word", ["letters"]
    aspects = []
    letters = lambda s: "".join(c for c in s if c.isalpha() or unicodedata.combining(c))  # noqa: E731

    def with_marks(fs):
        return nfc("".join(letters(unicodedata.normalize("NFD", f)) for f in fs))

    if with_marks(ef).lower() != with_marks(of).lower():
        aspects.append("accent/breathing")
    if with_marks(ef) != with_marks(of) and with_marks(ef).lower() == with_marks(of).lower():
        aspects.append("capitals")
    def rest(f, brackets):
        return "".join(c for c in nfc(f) if not c.isalpha() and not unicodedata.combining(c)
                       and (c in BRACKETS) == brackets)

    def marks(fs, brackets):
        if len(ef) == len(of):
            return [rest(f, brackets) for f in fs]
        return "".join(rest(f, brackets) for f in fs)

    if marks(ef, True) != marks(of, True):
        aspects.append("brackets/daggers/asterisks")
    if marks(ef, False) != marks(of, False):
        aspects.append("punctuation")
    if len(ef) != len(of):
        aspects.append("word division")
    order = [("brackets/daggers/asterisks", "text-bracket"), ("accent/breathing", "text-accent"),
             ("punctuation", "text-punctuation"), ("word division", "text-word-division"),
             ("capitals", "text-capitals")]
    for a, k in order:
        if a in aspects:
            return k, aspects
    return "text-other", aspects


def compare_text(e_lines, o_lines, ref_lines, items, keys, report):
    last_o = next(l.n for l in reversed(o_lines) if re.match(r"\d", l.n))

    def stop_at(lines):
        i = next((i for i, l in enumerate(lines) if l.ref == last_o), None)
        if i is None:  # a lettered or added verse: the last reference line not after it
            target = int(re.match(r"\d+", last_o).group())
            cands = [i for i, l in enumerate(lines) if l.ref and int(re.match(r"\d+", l.ref).group()) <= target]
            i = cands[-1] if cands else None
        # route E's added lines right after it belong to the same page
        while i is not None and i + 1 < len(lines) and lines[i + 1].ref is None:
            i += 1
        return i

    stop_ref, stop_e = stop_at(ref_lines), stop_at(e_lines)
    if stop_ref is None or stop_e is None:
        raise SystemExit(f"route O's last verse {last_o} not found in the reference")
    # the inserted lines just after the last verse would belong to the next page
    R = tokenize_lines(ref_lines[: stop_ref + 1], "R")
    E = tokenize_lines(e_lines[: stop_e + 1], "E")
    O = tokenize_lines(o_lines, "O")
    report["tokens"] = {"reference": len(R), "E": len(E), "O": len(O)}
    seg_e, seg_o = segments(R, E), segments(R, O)
    regs = []
    for r0, r1, e, o in regions(len(R), seg_e, seg_o):
        et = E[e[0]:e[1]] if e else []
        ot = O[o[0]:o[1]] if o else []
        if not et and not ot and r0 == r1:
            continue
        regs.append((r0, r1, et, ot))
    # verse of each region, from the reference (neutral between the routes)
    o_page_of = {}
    o_first_last = defaultdict(lambda: [None, None])
    for l in o_lines:
        o_page_of[l.n] = l.page
    for i, l in enumerate(o_lines):
        fl = o_first_last[l.page]
        if fl[0] is None:
            fl[0] = l.n
        fl[1] = l.n

    def ref_verse(r0, r1):
        if r0 < r1:
            return R[r0].verse
        return R[r0 - 1].verse if r0 > 0 else R[0].verse

    def disagree(reg):
        return [t.form for t in reg[2]] != [t.form for t in reg[3]]

    per_verse = Counter()
    # consecutive disagreeing regions (no agreeing word between them) make one item
    runs, k = [], 0
    while k < len(regs):
        if disagree(regs[k]):
            j = k
            while j + 1 < len(regs) and disagree(regs[j + 1]):
                j += 1
            runs.append((k, j))
            k = j + 1
        else:
            k += 1
    for k, kend in runs:
        r0, r1 = regs[k][0], regs[kend][1]
        et = [t for reg in regs[k:kend + 1] for t in reg[2]]
        ot = [t for reg in regs[k:kend + 1] for t in reg[3]]
        ef, of = [t.form for t in et], [t.form for t in ot]
        rf = [t.form for t in R[r0:r1]]
        kind, aspects = classify_text(ef, of)
        verse = ref_verse(r0, r1)
        per_verse[verse] += 1
        iid = f"T{verse}-{per_verse[verse]}"
        # context: the neighbouring words where the two routes agree
        before, after = [], []
        j = k - 1
        while j >= 0 and len(before) < 6:
            if disagree(regs[j]):
                before.insert(0, "⟦…⟧")
            else:
                before[0:0] = [t.form for t in regs[j][2]]
            j -= 1
        j = kend + 1
        while j < len(regs) and len(after) < 6:
            if disagree(regs[j]):
                after.append("⟦…⟧")
            else:
                after.extend(t.form for t in regs[j][2])
            j += 1
        before, after = before[-6:], after[:6]
        pages = set()
        src = ot or (regs[k - 1][3] if k else []) or et
        for t in src:
            if t.page:
                pages.add(t.page)
        if not pages and et:
            # route O has nothing here: the page of the nearest route O word
            for j in range(k - 1, -1, -1):
                if regs[j][3]:
                    pages.add(regs[j][3][-1].page)
                    break
        for p in list(pages):
            fl = o_first_last[p]
            if src and src[0].verse == fl[0] and p - 2 >= FIRST_PAGE:
                pages.add(p - 2)
            if src and src[-1].verse == fl[1] and p + 2 <= LAST_TEXT_PAGE:
                pages.add(p + 2)
        e_rel = "= reference" if ef == rf else "changed from reference"
        o_rel = "= reference" if of == rf else "changed from reference"
        add_item(items, keys, iid, kind, aspects,
                 where={"leaves": sorted(pages), "verse": verse,
                        "look_at": "the Greek text at the top of the (even) page; the verse is numbered as in "
                                   "the Perseus text, the printed margin may differ by a verse or two in the lyrics"},
                 context_before=render(before), context_after=render(after),
                 e=render(ef) or "(nothing)", o=render(of) or "(nothing)",
                 e_rel=e_rel, o_rel=o_rel, reference=render(rf) or "(nothing)")
    # the verse division and numbering, where the words agree
    vd = []
    for r0, r1, et, ot in regs:
        if len(et) != 1 or len(ot) != 1:
            if len(et) == len(ot):
                pairs = list(zip(et, ot))
            else:
                continue
        else:
            pairs = [(et[0], ot[0])]
        for te, to in pairs:
            if te.starts != to.starts or (te.starts and to.starts and te.verse != to.verse):
                vd.append((te, to))
    report["verse_division"] = vd
    report["streams"] = (R, E, O)


# ------------------------------------------------------------------ the apparatus

@dataclass
class Note:
    key: str
    text: str
    pages: list[int] = field(default_factory=list)
    route: str = ""


def norm_note(text: str, route: str) -> str:
    text = nfc(text)
    text = CONV.sub("apparatus", "bold lemma markers ** (route E)", route, r"\*\*", "", text)
    text = CONV.sub("apparatus", "italics markers *…* (route E)", route, r"\*([^*\s][^*]*?)\*", r"\1", text)
    text = unify_elision(text, "apparatus", route)
    n = sum(text.count(c) for c in "¹²³⁴⁵⁶⁷⁸⁹⁰")
    CONV.add("apparatus", "superscript figure (V² written V2 by route E)", route, n)
    text = text.translate(SUPERSCRIPT)
    n = text.count("<") + text.count(">")
    CONV.add("apparatus", "angle brackets < > written ⟨ ⟩ (pairs ×2)", route, n)
    text = text.replace("<", "⟨").replace(">", "⟩")
    text = CONV.sub("apparatus", "en dash – or ‒ written —", route, r"[–‒]", "—", text)
    text = CONV.sub("apparatus", "ellipsis character … written ...", route, r"…", "...", text)
    return re.sub(r"\s+", " ", text).strip()


def norm_key(key: str) -> str:
    return re.sub(r"\s*[-–—]\s*", "-", key.strip())


def read_e_notes(warnings) -> tuple[list[Note], str]:
    pages = read_batches(E_DIR)
    notes: list[Note] = []
    sigla = ""
    for stem in sorted(pages):
        p = page_no(stem)
        if not FIRST_PAGE <= p <= LAST_APP_PAGE:
            continue
        cur: Note | None = None
        in_sigla = False
        first = True
        for raw in pages[stem]["apparatus"]:
            line = raw.strip()
            if not line:
                in_sigla = False
                continue
            m = re.match(r"^## (\S+)\s*$", line)
            if m:
                cur = Note(norm_key(m.group(1)), "", [p], "E")
                notes.append(cur)
                in_sigla = False
                first = False
                continue
            if line.startswith("*Sigla.*"):
                sigla = line[len("*Sigla.*"):].strip()
                in_sigla = True
                first = False
                continue
            if in_sigla:
                sigla += " " + line
                continue
            if first and line.startswith("+ "):
                if not notes:
                    warnings.append(f"route E {stem}: a run-on with no note before it")
                    continue
                cur = notes[-1]
                cur.text = join_run_on(cur.text, line[2:])
                cur.pages.append(p)
                first = False
                continue
            first = False
            if cur is None:
                warnings.append(f"route E {stem}: apparatus text outside a note: {line[:60]}")
                continue
            cur.text = (cur.text + " " + line).strip()
    return notes, sigla


def read_o_notes(pages, warnings) -> tuple[list[Note], str]:
    notes, sigla = [], ""
    for stem in sorted(pages):
        p = page_no(stem)
        if not FIRST_PAGE <= p <= LAST_TEXT_PAGE:
            continue
        for raw in pages[stem]["apparatus"]:
            m = re.match(r"^(\S+)\t(.*)$", raw)
            if not m:
                warnings.append(f"route O {stem}: apparatus line not understood: {raw[:60]}")
                continue
            notes.append(Note(norm_key(m.group(1)), m.group(2).strip(), [p], "O"))
        for raw in pages[stem]["notes"]:
            if raw.startswith("Sigla:"):
                sigla = raw[len("Sigla:"):].strip()
    return notes, sigla


TOKEN = re.compile(r"\u02bc?(?:(?!\u02bc)[\w\u0300-\u036f])+\u02bc?|\S")  # a space after an elision mark is not significant
# characters that print alike: Latin capitals typed for Greek ones (XO for ΧΟ), the modifier
# letter ʽ for the spacing rough breathing ῾. Compared alike, shown as written.
LOOKALIKE = str.maketrans({"A": "Α", "B": "Β", "E": "Ε", "Z": "Ζ", "H": "Η", "I": "Ι", "K": "Κ",
                           "M": "Μ", "N": "Ν", "O": "Ο", "P": "Ρ", "T": "Τ", "X": "Χ", "Y": "Υ",
                           "\u02bd": "\u1ffe"})


def lookalike_key(tok: str) -> str:
    """Latin capitals count as Greek only in a token of capitals that are all look-alikes."""
    if re.fullmatch(r"[ABEZHIKMNOPTXY]{2,}", tok) or re.search(r"[Ͱ-Ͽἀ-῿]", tok):
        return tok.translate(LOOKALIKE)
    return tok.replace("\u02bd", "\u1ffe")


def ntokens(text: str) -> list[str]:
    return TOKEN.findall(text)


def detok(toks: list[str]) -> str:
    out = ""
    for t in toks:
        if not out:
            out = t
        elif t in ",.;:)]⟩·!?" or out[-1] in "([⟨‘“" or t == "ʼ" and out[-1] in ",.":
            out += t
        else:
            out += " " + t
    return out


def kind_app(a: list[str], b: list[str]) -> tuple[str, list[str]]:
    joined = "".join(a + b)
    aspects = []
    if GREEK.search(joined):
        kind = "apparatus-greek"
        sa, sb = skeleton("".join(a)), skeleton("".join(b))
        if sa == sb and "".join(a) != "".join(b):
            al = [t for t in a if any(c.isalpha() for c in t)]
            bl = [t for t in b if any(c.isalpha() for c in t)]
            aspects.append("accent/breathing" if al != bl else "punctuation/spacing only")
        elif sa != sb:
            aspects.append("letters")
    else:
        kind = "apparatus-other"
        if skeleton("".join(a)) == skeleton("".join(b)):
            aspects.append("punctuation/spacing only")
    return kind, aspects


def compare_apparatus(items, keys, report, o_pages, warnings):
    e_notes, e_sigla = read_e_notes(warnings)
    o_notes, o_sigla = read_o_notes(o_pages, warnings)
    for n in e_notes:
        n.text = norm_note(n.text, "E")
    for n in o_notes:
        n.text = norm_note(n.text, "O")
    sig_e = norm_note(e_sigla, "E")
    sig_o = norm_note(o_sigla, "O")
    pairs: list[tuple[Note | None, Note | None]] = [(Note("sigla", sig_e, [FIRST_PAGE], "E"), Note("sigla", sig_o, [FIRST_PAGE], "O"))]
    sm = difflib.SequenceMatcher(None, [n.key for n in e_notes], [n.key for n in o_notes], autojunk=False)
    for op, a0, a1, b0, b1 in sm.get_opcodes():
        if op == "equal":
            pairs.extend(zip(e_notes[a0:a1], o_notes[b0:b1]))
            continue
        ea, ob = list(e_notes[a0:a1]), list(o_notes[b0:b1])
        # within a block: pair by number, then by the words (a misnumbered note)
        used = set()
        block = []
        for x in ea:
            j = next((j for j, y in enumerate(ob) if j not in used and y.key == x.key), None)
            if j is None:
                best = max(((difflib.SequenceMatcher(None, ntokens(x.text), ntokens(y.text)).ratio(), j)
                            for j, y in enumerate(ob) if j not in used), default=(0, None))
                j = best[1] if best[0] >= 0.6 else None
            if j is not None:
                used.add(j)
                block.append((x, ob[j]))
            else:
                block.append((x, None))
        block.extend((None, y) for j, y in enumerate(ob) if j not in used)
        pairs.extend(block)
    occ = Counter()
    report["notes"] = {"E": len(e_notes), "O": len(o_notes)}
    report["unpaired"] = []
    report["truncated"] = []
    last_e = e_notes[-1] if e_notes else None
    for x, y in pairs:
        key = (x or y).key
        occ[key] += 1
        base = f"{key}" + (f"#{occ[key]}" if occ[key] > 1 else "")
        leaves = sorted(set((x.pages if x else []) + (y.pages if y else [])) |
                        {p + 1 for p in (y.pages if y else []) if p % 2 == 0})
        if x is None or y is None:
            have = x or y
            report["unpaired"].append((have.route, have.key, have.pages, have.text[:80]))
            iid = f"N{base}"
            add_item(items, keys, iid, "missing-note", ["a note only one route has"],
                     where={"leaves": leaves, "note": key,
                            "look_at": "the critical apparatus (small type under the text, continued on the facing page)"},
                     context_before="", context_after="",
                     e=f"{x.key}  {x.text}" if x else "(no such note)",
                     o=f"{y.key}  {y.text}" if y else "(no such note)",
                     e_rel=None, o_rel=None, reference=None)
            continue
        if x.key != y.key:
            iid = f"K{base}"
            add_item(items, keys, iid, "apparatus-number", ["the note's line number"],
                     where={"leaves": leaves, "note": f"{x.key} / {y.key}",
                            "look_at": "the bold line number at the start of the note"},
                     context_before="", context_after=detok(ntokens(x.text))[:120],
                     e=x.key, o=y.key, e_rel=None, o_rel=None, reference=None)
        ta, tb = ntokens(x.text), ntokens(y.text)
        # the bold line number repeated as the first words of the note ("397 and 399 are given …")
        for toks, other, route in ((ta, tb, "E"), (tb, ta, "O")):
            if toks and toks[0] == key.split("-")[0] and (not other or other[0] != toks[0]):
                del toks[0]
                CONV.add("apparatus", "the note's line number repeated at the start of its text", route)
        ka, kb = [lookalike_key(t) for t in ta], [lookalike_key(t) for t in tb]
        ops = [op for op in difflib.SequenceMatcher(None, ka, kb, autojunk=False).get_opcodes()]
        for tag, a0, a1, b0, b1 in ops:
            if tag == "equal":
                for u, v in zip(ta[a0:a1], tb[b0:b1]):
                    if u != v:
                        CONV.add("apparatus", "look-alike characters (Latin XO for Greek ΧΟ; ʽ for ῾)",
                                 "E" if lookalike_key(u) != u else "O")
        # the end of route E's last note may lie beyond p-0143
        if x is last_e and ops and ops[-1][0] == "insert" and ops[-1][1] == len(ta) and max(x.pages) == LAST_APP_PAGE:
            report["truncated"].append((x.key, detok(tb[ops[-1][3]:ops[-1][4]])))
            ops = ops[:-1]
        groups, cur = [], None
        for op in ops:
            tag, a0, a1, b0, b1 = op
            if tag == "equal":
                if cur and (a1 - a0) <= 2 and op is not ops[-1]:
                    cur["gap"].append(op)
                continue
            if cur and cur["gap"] and sum(g[2] - g[1] for g in cur["gap"]) <= 2:
                cur["a1"], cur["b1"] = a1, b1
                cur["gap"] = []
            else:
                cur = {"a0": a0, "a1": a1, "b0": b0, "b1": b1, "gap": []}
                groups.append(cur)
        # the note as display units: agreeing words, and a placeholder for each disagreement
        units: list[tuple[str, object]] = []
        for a in range(len(ta) + 1):
            for gi, g in enumerate(groups):
                if g["a0"] == a:
                    units.append(("diff", gi))
            if a < len(ta) and not any(g["a0"] <= a < g["a1"] for g in groups):
                units.append(("tok", ta[a]))

        def context(gi, before):
            at = units.index(("diff", gi))
            seq = units[:at][::-1] if before else units[at + 1:]
            got = []
            for kind_, u in seq:
                if len(got) >= 8:
                    break
                got.append(u if kind_ == "tok" else "⟦…⟧")
            return detok(got[::-1] if before else got)

        for gi, g in enumerate(groups, 1):
            ra, rb = ta[g["a0"]:g["a1"]], tb[g["b0"]:g["b1"]]
            kind, aspects = kind_app(ra, rb)
            iid = f"A{base}-{gi}"
            add_item(items, keys, iid, kind, aspects,
                     where={"leaves": leaves, "note": key,
                            "look_at": "the critical apparatus note with this number"},
                     context_before=context(gi - 1, True),
                     context_after=context(gi - 1, False),
                     e=detok(ra) or "(nothing)", o=detok(rb) or "(nothing)",
                     e_rel=None, o_rel=None, reference=None)
    report["app_pairs"] = pairs


# ------------------------------------------------------------------ items

def add_item(items, keys, iid, kind, aspects, where, context_before, context_after, e, o,
             e_rel, o_rel, reference):
    while any(it["id"] == iid for it in items):
        iid += "'"
    swap = random.Random(f"{SEED}:{iid}").random() < 0.5
    r1, r2 = (o, e) if swap else (e, o)
    items.append({"id": iid, "kind": kind, "aspects": aspects, "where": where,
                  "context": f"{context_before} [[ reading ]] {context_after}".strip(),
                  "context_before": context_before, "context_after": context_after,
                  "reading_1": r1, "reading_2": r2})
    keys.append({"id": iid, "reading_1": "O" if swap else "E", "reading_2": "E" if swap else "O",
                 "E": {"reading": e, "vs_reference": e_rel},
                 "O": {"reading": o, "vs_reference": o_rel},
                 "reference": reference})


# ------------------------------------------------------------------ main

def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--state", required=True, help='route O state: a git commit, or "worktree"')
    ap.add_argument("--out", required=True, type=Path)
    args = ap.parse_args()
    out: Path = args.out
    out.mkdir(parents=True, exist_ok=True)
    (out / "streams").mkdir(exist_ok=True)
    warnings: list[str] = []
    items, keys, report = [], [], {}

    o_pages = read_o(args.state)
    o_lines, o_speakers = route_o_lines(o_pages)
    e_lines, e_diffs = route_e_lines(warnings)
    ref = reference_lines()
    compare_text(e_lines, o_lines, ref, items, keys, report)
    compare_apparatus(items, keys, report, o_pages, warnings)

    with open(out / "items.jsonl", "w", encoding="utf-8") as f:
        for it in items:
            f.write(json.dumps(it, ensure_ascii=False) + "\n")
    with open(out / "key.jsonl", "w", encoding="utf-8") as f:
        for k in keys:
            f.write(json.dumps(k, ensure_ascii=False) + "\n")

    R, E, O = report["streams"]
    for name, toks in (("text-reference", R), ("text-E", E), ("text-O", O)):
        with open(out / "streams" / f"{name}.txt", "w", encoding="utf-8") as f:
            cur = None
            line = []
            for t in toks:
                if t.starts and line:
                    f.write(f"{cur}\t{' '.join(line)}\n")
                    line = []
                if t.starts or cur is None:
                    cur = t.verse
                line.append(t.form)
            if line:
                f.write(f"{cur}\t{' '.join(line)}\n")
    with open(out / "streams" / "apparatus-paired.txt", "w", encoding="utf-8") as f:
        for x, y in report["app_pairs"]:
            f.write(f"E {x.key if x else '-'}\t{x.text if x else ''}\nO {y.key if y else '-'}\t{y.text if y else ''}\n\n")

    # verse division
    with open(out / "verse-division.md", "w", encoding="utf-8") as f:
        f.write(f"# Verse division and numbering: route E and route O (state {args.state})\n\n")
        f.write("Reported, not adjudicated. Route E keeps the reference's division except where its first "
                "pass re-divided (lyrics were not re-divided by rule); route O divides as printed.\n"
                "Each row: a word where one route begins a verse and the other does not, or both begin "
                "one with different numbers. `start N` = the word begins verse N; `in N` = inside verse N.\n\n")
        f.write("| difference | word | route E | route O |\n|---|---|---|---|\n")
        for te, to in report["verse_division"]:
            what = "numbering" if te.starts and to.starts else "division"
            f.write(f"| {what} | {te.form} | {'start' if te.starts else 'in'} {te.verse} | {'start' if to.starts else 'in'} {to.verse} |\n")
        nd = Counter("numbering" if te.starts and to.starts else "division" for te, to in report["verse_division"])
        f.write(f"\nDivision differences: {nd['division']}; numbering differences: {nd['numbering']}.\n")

    # summary
    kinds = Counter(it["kind"] for it in items)
    with open(out / "summary.md", "w", encoding="utf-8") as f:
        f.write(f"# Route comparison, Trachiniae pp. 80-143: route E vs route O (state `{args.state}`)\n\n")
        f.write(f"Text: verses 1-{o_lines[-1].n} (pages 80-{LAST_TEXT_PAGE}); words: reference {report['tokens']['reference']}, "
                f"route E {report['tokens']['E']}, route O {report['tokens']['O']}.\n")
        f.write(f"Apparatus: route E {report['notes']['E']} notes (pages 80-{LAST_APP_PAGE}), "
                f"route O {report['notes']['O']} notes (pages 80-{LAST_TEXT_PAGE} with the facing pages); "
                "plus the sigla paragraph.\n\n")
        f.write("## Disagreements for adjudication (items.jsonl)\n\n| kind | items |\n|---|---|\n")
        for k, n in sorted(kinds.items()):
            f.write(f"| {k} | {n} |\n")
        f.write(f"| **total** | **{len(items)}** |\n\n")
        f.write(f"Not adjudicated: {len(report['verse_division'])} words where the verse division or "
                "numbering differs (verse-division.md). Speaker labels are not compared.\n\n")
        f.write("## Convention differences excluded (normalised before comparing)\n\n"
                "Occurrences normalised in each route's files (not all of them differ from the other route).\n\n"
                "| part | rule | route E | route O |\n|---|---|---|---|\n")
        rules = sorted({(p, r) for p, r, _ in CONV.counts})
        for p, r in rules:
            f.write(f"| {p} | {r} | {CONV.counts.get((p, r, 'E'), 0)} | {CONV.counts.get((p, r, 'O'), 0)} |\n")
        f.write("\nAlso by rule, not counted: spacing (whitespace collapsed; spaces around punctuation, "
                "dashes and the upright stroke | ignored in the apparatus, which is compared as words and "
                "single marks); \"f.\"/\"ff.\" after a note number (both routes drop it); the sigla note "
                "(route E `*Sigla.*` paragraph, route O `Sigla:` under notes) compared as a note of its own; "
                "Unicode NFC.\n\n")
        if report["truncated"]:
            f.write("## Route E's range ends at p-0143\n\n")
            for k, rest in report["truncated"]:
                f.write(f"* note {k}: route E stops where the note runs on to p-0144; the rest in route O "
                        f"(not compared): «{rest[:100]}»\n")
            f.write("\n")
        if report["unpaired"]:
            f.write("## Notes only one route has\n\n")
            for route, k, pages, text in report["unpaired"]:
                f.write(f"* route {route}, note {k} (p. {pages}): {text}\n")
            f.write("\n")
        if warnings:
            f.write("## Warnings\n\n" + "".join(f"* {w}\n" for w in warnings) + "\n")
    with open(out / "summary.md", "a", encoding="utf-8") as f:
        f.write("## Files\n\n* `items.jsonl`: for the adjudicators (readings shuffled per item, fixed seed)\n"
                "* `key.jsonl`: which reading is which route, and its relation to the reference (not for the adjudicators)\n"
                "* `verse-division.md`: verse division and numbering differences (not adjudicated)\n"
                "* `streams/`: the normalised texts of both routes and the reference, and the paired apparatus notes\n\n"
                f"Made with: `pipeline/.venv/bin/python research/route-comparison/compare.py --state {args.state} --out {out}` "
                "(from pipeline/).\n")
    print(f"{len(items)} items; " + ", ".join(f"{k} {n}" for k, n in sorted(kinds.items())))
    for w in warnings:
        print("warning:", w)


if __name__ == "__main__":
    main()
