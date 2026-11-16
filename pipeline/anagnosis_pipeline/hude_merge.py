"""Lysias from the checked batches (pipeline/transcriptions/lysias/): Hude's text and critical
apparatus, with the lemma check (pipeline/PLAN-lysias.md, step 5).

The batches hold Hude's printed lines keyed by the scan's leaf and the line's place on the page
(28.5), `§1.43` where a section begins, `¶` before a line he indents, `[label]` headings inside a
speech, `[hypothesis]` lines, and each speech's number and title as `[title]` lines. merge()
writes <texts>/<slug>/:

* grc.txt: the speeches as books (`== book 1 · ΥΠΕΡ ΤΟΥ ΕΡΑΤΟΣΘΕΝΟΥΣ ΦΟΝΟΥ ΑΠΟΛΟΓΙΑ`), one line
  per section (1.7), the printed lines joined; a paragraph or a heading Hude sets inside a
  section continues the section on a line of its own with a letter (1.30b); a long section is
  divided at sentence ends (lucian_merge.split_long); a heading inside a speech is a `!` line; a
  hypothesis is the speech's section 0 (34.0);
* commentary-hude-apparatus.md: each item under the section that holds its lemma (the item's
  printed line number, which refers to Hude's page, is not kept);

and pipeline/build/<slug>-merge.log: problems, and the apparatus lemmas not found in their lines
(SERIOUS where the text may have slipped to the check text's reading, WEAK for the rest).

The words' lemmas and syntax (GLAUx by speech), the translations and the commentaries are later
steps of the plan and are not written here yet.
"""
from __future__ import annotations

import difflib
import json
import re
from pathlib import Path

from .drama import PLAYS, TRANSCRIPTION_LICENSE, _meta_lines
from .hude_pages import APP_KEY, HYPOTHESIS, KEY, LABEL, SPEECHES, TITLE, check_tokens, is_numeral, out_dir, read_batches, transcriptions_dir
from .lucian_merge import LETTERS, _LOWER_GREEK, _find, _sk, greek_runs, lemma_of, split_long
from .lucian_pages import SECTION_MARK

ROOT = Path(__file__).resolve().parent.parent.parent
PIPELINE = ROOT / "pipeline"
# Evident misprints in Hude's text: the batches keep what is printed; the text shows the right
# reading and an apparatus note says so (the author's rule). Key: leaf.line -> (printed, right).
MISPRINTS: dict[str, dict[str, tuple[str, str]]] = {
    "lysias": {},
}
# which of several like words on the line an item means: "alt. τὴν del. Emperius"
ORDINAL = re.compile(r"^(pr|prius|alt|alterum|tert|tertium|quart)\.?\s+(?=\S)")
ORDINALS = {"pr": 0, "prius": 0, "alt": 1, "alterum": 1, "tert": 2, "tertium": 2, "quart": 3}


# --- the text --------------------------------------------------------------------------------

def assemble(pages: dict[str, dict], index: list[dict]) -> dict:
    """The units of the text and where each printed line's words went.

    Returns {'units': [{'n' ('1.7', '1.30b', '34.0'), 'para', 'before' (headings printed before
    it), 'words': [(word, key)]}], 'lines': {key: [(unit index, word index in unit, word)]},
    'titles': {speech: [title lines]}, 'problems': [...]}."""
    units: list[dict] = []
    lines: dict[str, list[tuple[int, int, str]]] = {}
    titles: dict[int, list[str]] = {}
    problems: list[str] = []
    speech = 0
    sec: str | None = None
    letter = 0
    pending_para = False
    pending_labels: list[str] = []
    in_title = False
    seen: set[str] = set()

    def new_unit(n: str, para: bool) -> dict:
        u = {"n": n, "para": para, "before": list(pending_labels), "words": []}
        pending_labels.clear()
        units.append(u)
        return u

    for p in index:
        block = pages.get(p["stem"])
        if block is None:
            problems.append(f"{p['stem']}: not transcribed")
            continue
        for e in block["errors"]:
            problems.append(f"{p['stem']}: {e}")
        for key, text in block["text"]:
            if key == "¶":
                pending_para = True
                continue
            if key == TITLE:
                if not in_title:
                    speech += 1
                    titles[speech] = []
                    sec, letter, in_title = None, 0, True
                    if pending_labels:
                        problems.append(f"{p['stem']}: a heading before a speech's title: {pending_labels}")
                        pending_labels.clear()
                titles[speech].append(text.strip())
                pending_para = False
                continue
            in_title = False
            if not KEY.match(key):
                problems.append(f"{p['stem']}: bad key {key!r}")
                continue
            if key in seen:
                problems.append(f"{p['stem']}: {key} twice; the second left out")
                continue
            seen.add(key)
            lines[key] = []
            if text.startswith(LABEL):
                pending_labels.append(text[len(LABEL):].strip())
                pending_para = False
                continue
            if text.startswith(HYPOTHESIS):
                n0 = f"{speech}.0"
                if sec != n0:
                    sec, letter = n0, 0
                    new_unit(n0, True)
                    pending_para = False
                elif pending_para:
                    letter += 1
                    new_unit(f"{n0}{LETTERS[letter - 1]}", True)
                    pending_para = False
                u = units[-1]
                for w in text[len(HYPOTHESIS):].split():
                    lines[key].append((len(units) - 1, len(u["words"]), w))
                    u["words"].append((w, key))
                continue
            pos = 0
            chunks: list[tuple[str | None, str]] = []
            for mk in SECTION_MARK.finditer(text):
                chunks.append((None, text[pos:mk.start()]))
                chunks.append((f"{mk.group(1)}.{mk.group(2)}", ""))
                pos = mk.end()
            chunks.append((None, text[pos:]))
            first_chunk = True
            for new, chunk in chunks:
                if new is not None:
                    if int(new.split(".")[0]) != speech:
                        problems.append(f"{p['stem']} {key}: section {new} in speech {speech} (by the titles)")
                    sec, letter = new, 0
                    new_unit(sec, pending_para and first_chunk)
                    if pending_para and first_chunk:
                        pending_para = False
                    continue
                words = chunk.split()
                if not words:
                    continue
                if sec is None or sec.endswith(".0"):
                    problems.append(f"{p['stem']} {key}: words before the speech's first section mark: {chunk[:40]!r}")
                    continue
                if (pending_para and first_chunk) or pending_labels:
                    # a paragraph or a heading Hude sets inside a section
                    letter += 1
                    new_unit(f"{sec}{LETTERS[letter - 1]}", pending_para and first_chunk)
                    pending_para = False
                first_chunk = False
                u = units[-1]
                for w in words:
                    lines[key].append((len(units) - 1, len(u["words"]), w))
                    u["words"].append((w, key))
            if pending_para:
                problems.append(f"{p['stem']} {key}: ¶ before a line without words")
                pending_para = False
    if pending_labels:
        problems.append(f"a heading after the last words of the text: {pending_labels}")
    # long sections divided at sentence ends; the headings stay before the part they stood before
    before = {id(u): u["before"] for u in units}
    firsts = [(ui, u["words"][0][1]) for ui, u in enumerate(units) if u["words"] and u["before"]]
    old_lines = lines
    new_units, lines = split_long(units, old_lines)
    for u in new_units:
        u["before"] = []
    for ui, key in firsts:
        k = next(i for i, (a, b, _w) in enumerate(old_lines[key]) if a == ui and b == 0)
        new_units[lines[key][k][0]]["before"] = before[id(units[ui])]
    return {"units": new_units, "lines": lines, "titles": titles, "problems": problems}


def speech_title(lines: list[str]) -> tuple[str, str]:
    """(the speech's number as printed, its title) from the [title] lines: the Roman numeral
    stands first; a hypothesis's own heading (ΥΠΟΘΕΣΙΣ …) is not part of the title."""
    numeral = lines[0] if lines and is_numeral(lines[0]) else ""
    rest = [l for l in (lines[1:] if numeral else lines) if not l.startswith("ΥΠΟΘΕΣΙΣ")]
    return numeral, " ".join(rest)


def correct_misprints(slug: str, text: dict, problems: list[str]) -> list[tuple[int, str]]:
    """The right reading in the text where the edition misprints a word (MISPRINTS), and for each
    an apparatus note on its section, marked as this edition's: [(unit index, note)]."""
    notes: list[tuple[int, str]] = []
    for key, (printed, right) in MISPRINTS.get(slug, {}).items():
        done = False
        for k, (u, wi, w) in enumerate(text["lines"].get(key, [])):
            if printed in w:
                text["lines"][key][k] = (u, wi, w.replace(printed, right))
                word, wkey = text["units"][u]["words"][wi]
                text["units"][u]["words"][wi] = (word.replace(printed, right), wkey)
                notes.append((u, f"{right}: Hude prints {printed}, a misprint; corrected in this edition."))
                done = True
                break
        if not done:
            problems.append(f"misprint {key}: “{printed}” not found on the line")
    return notes


# --- the apparatus ---------------------------------------------------------------------------

def place_apparatus(pages: dict[str, dict], index: list[dict], text: dict) -> tuple[list[tuple[int, str]], list[str], list[str]]:
    """Each item under the unit that holds its lemma: [(unit index, item)], the lemma misses (for
    the log), problems. An item names a line of its page (3, 22-23); its lemma, the Greek words
    it begins with ("εἴητε marg. Ald.: εἰ ἦτε C H X"; "alt. τὴν del. Emperius" means the second
    τὴν of the line), is looked for on that line, then on the lines beside it. A miss is SERIOUS
    where the text may have slipped to the check text's reading: a `lemma]` that is not in the
    text, or Hude's first reading missing from the line while a later reading of the same item
    stands there. Everything else that matches nothing (a conjecture printed without the word it
    replaces, a note in Latin) is WEAK and filed under the section of the line's first word."""
    lines = text["lines"]
    units = text["units"]
    ordered = list(lines)
    where_key = {k: i for i, k in enumerate(ordered)}
    placed: list[tuple[int, str]] = []
    misses: list[str] = []
    problems: list[str] = []
    for p in index:
        block = pages.get(p["stem"])
        if block is None:
            continue
        leaf = p["leaf"]
        keys = [k for k, _t in block["text"] if KEY.match(k)]
        last_unit = None
        for n, item in block["apparatus"]:
            m = APP_KEY.match(n)
            if not m:
                problems.append(f"{p['stem']}: bad apparatus number {n!r}")
                continue
            if n == "-":
                if last_unit is None:
                    last_unit = next((lines[k][0][0] for k in keys if lines.get(k)), len(units) - 1 if units else None)
                if last_unit is not None:
                    placed.append((last_unit, item))
                continue
            a, b = int(m.group(1)), int(m.group(2) or m.group(3) or m.group(1))
            ka, kb = f"{leaf}.{a}", f"{leaf}.{b}"
            if ka not in lines:
                problems.append(f"{p['stem']}: apparatus {n} names line {ka}, which the text does not have")
                continue
            ia = where_key[ka]
            ib = where_key.get(kb, ia)
            own = [c for k in ordered[ia: ib + 1] for c in lines[k]]
            cands = [c for k in ordered[max(0, ia - 1): ib + 2] for c in lines[k]]
            mo = ORDINAL.match(item)
            nth = ORDINALS[mo.group(1)] if mo else 0
            rest = item[mo.end():] if mo else item
            first, last = lemma_of(rest)
            runs = greek_runs(rest)
            where = f"{leaf}.{n}"
            hit = None
            exact = False
            if first:
                # the nth exact occurrence on the item's own line(s)
                pos, found = 0, []
                while pos < len(own):
                    i = _find(first, own[pos:], exact=True)
                    if i is None:
                        break
                    found.append(own[pos + i])
                    pos += i + 1
                if found:
                    hit, exact = found[min(nth, len(found) - 1)], True
                    if nth and len(found) <= nth:
                        misses.append(f"WEAK {where}: “{mo.group(1)}.” but the line has {len(found)} of “{' '.join(first)}”: {item}")
                if hit is None:
                    i = _find(first, cands, exact=True)
                    if i is not None:
                        hit, exact = cands[i], True
                        misses.append(f"WEAK {where}: “{' '.join(first)}” stands on a line beside the one named: {item}")
                if hit is None:
                    i = _find(first, own) if own else None
                    hit = own[i] if i is not None else None
                if hit is None:
                    # an insertion or a rearrangement: most of the lemma's words on the line
                    ws = {_sk(c[2]): c for c in reversed(own)}
                    got = [ws[_sk(w)] for w in first if _sk(w) in ws]
                    if got and len(got) >= max(1, len([w for w in first if _sk(w)]) - 1):
                        hit = got[0]
                later = any(_find(r, own, exact=True) is not None for r in runs[1:])
                bracket = "]" in rest.split(":")[0] and not re.match(r"^\S*\[", rest)
                if not exact and (bracket or (later and ":" in rest)):
                    why = "the lemma] is not in the text" if bracket else "a later reading of the item stands in the text"
                    misses.append(f"SERIOUS {where}: Hude's reading “{' '.join(first)}” is not on the line as written ({why}) "
                                  f"(the line: {' '.join(c[2] for c in own)}): {item}")
                elif hit is None:
                    misses.append(f"WEAK {where}: “{' '.join(first)}” matches nothing on the line: {item}")
                elif last and _find(last, cands) is None:
                    misses.append(f"WEAK {where}: the end of the lemma range “{' '.join(last)}” not found: {item}")
            u = hit[0] if hit is not None else None
            if u is None:
                # a note in Latin: the section of the Greek word it names, else the line's first word
                named = re.search(r"(?:post|ante|inter|pro|supra)\s+([^\s,;:]+)", rest)
                if named and _LOWER_GREEK.search(named.group(1)):
                    i = _find([named.group(1)], own) if own else None
                    if i is not None:
                        u = own[i][0]
                if u is None:
                    if own:
                        u = own[0][0]
                    else:
                        # an item on a heading's line: the part the heading stands before
                        u = next((lines[k][0][0] for k in ordered[ia:] if lines[k]), cands[0][0] if cands else None)
                        if u is None:
                            problems.append(f"{p['stem']}: apparatus {n}: no words on the lines it names")
                            continue
            placed.append((u, item))
            last_unit = u
    return placed, misses, problems


# --- merge -----------------------------------------------------------------------------------

def base(n: str) -> str:
    return re.sub(r"[a-z]$", "", n)


def merge(slug: str, sources: Path, texts: Path, build: Path) -> int:
    from .textfmt import Document, Line, Section, Speaker, Stage, write_file

    play = PLAYS[slug]
    tdir = transcriptions_dir(slug)
    index_path = out_dir(slug) / "pages.json"
    if not index_path.exists() or not any(tdir.glob("batch-*.md")):
        print(f"{slug}: no text batches yet")
        return 0
    index = json.loads(index_path.read_text(encoding="utf-8"))
    pages = read_batches(tdir)
    text = assemble(pages, index)
    problems = list(text["problems"])
    units = text["units"]
    misprint_notes = correct_misprints(slug, text, problems)
    out = texts / slug
    out.mkdir(parents=True, exist_ok=True)

    # sections against the check text: every section once, in order; every speech with its title
    toks, _notes = check_tokens(play, sources)
    want = list(dict.fromkeys(t["sec"] for t in toks))
    have = list(dict.fromkeys(base(u["n"]) for u in units if not base(u["n"]).endswith(".0")))
    if have != want:
        sm = difflib.SequenceMatcher(None, have, want, autojunk=False)
        for op, a0, a1, b0, b1 in sm.get_opcodes():
            if op != "equal":
                problems.append(f"sections: ours {have[a0:a1]} where the check text has {want[b0:b1]}")
    for k in range(1, SPEECHES + 1):
        if k not in text["titles"]:
            problems.append(f"speech {k}: no [title] lines")

    meta = {
        "title": play.title, "author": play.author, "lang": "grc",
        "source": f"{play.edition}; read from the Internet Archive scan {play.scan} by OCR, matched word by word to the "
                  f"Perseus Digital Library text ({play.tlg}.tlg001-{SPEECHES:03d}.perseus-grc2, Lamb's Loeb), and checked "
                  "against the scan where the two disagreed",
        "edition": play.edition,
        "license": TRANSCRIPTION_LICENSE,
        "layout": "prose",
        "pronunciation": play.pronunciation,
    }
    doc = Document(meta=meta)
    book = None
    for u in units:
        b = u["n"].split(".")[0]
        if b != book:
            book = b
            _numeral, title = speech_title(text["titles"].get(int(b), []))
            doc.items.append(Section(1, "book", f"{b} · {title}" if title else b))
        for heading in u["before"]:
            doc.items.append(Stage(heading))
        if u["para"]:
            doc.items.append(Speaker(""))
        doc.items.append(Line(u["n"], " ".join(w for w, _k in u["words"])))
    write_file(out / "grc.txt", doc)
    print(f"wrote {out / 'grc.txt'}: {len(units)} lines ({len(have)} sections of {len(want)}), "
          f"{len(text['titles'])} speeches, {sum(1 for u in units if u['para'])} paragraphs, from {len(pages)} pages")

    placed, misses, probs = place_apparatus(pages, index, text)
    problems += probs
    placed += misprint_notes
    md = _meta_lines({
        "title": f"Critical apparatus ({play.app_editor_name})",
        "author": play.app_editor_name, "lang": "lat",
        "source": f"{play.edition}; transcribed from the Internet Archive scan {play.scan}",
        "license": TRANSCRIPTION_LICENSE,
    }) + [""]
    grouped: dict[str, list[str]] = {}
    for u, item in sorted(placed, key=lambda x: x[0]):
        grouped.setdefault(base(units[u]["n"]), []).append(item)
    for sec, items in grouped.items():
        md.append(f"## {sec}")
        # every asterisk and plus sign of the apparatus is printed: an asterisk is written \* so
        # that two in one item cannot become italics (build.md_to_html)
        md.append("\n\n".join(items).replace("*", "\\*"))
        md.append("")
    (out / f"commentary-{play.app_editor}-apparatus.md").write_text("\n".join(md) + "\n", encoding="utf-8")
    serious = [x for x in misses if x.startswith("SERIOUS")]
    print(f"wrote commentary-{play.app_editor}-apparatus.md: {len(grouped)} sections, {len(placed)} items; "
          f"lemmas not found: {len(serious)} serious, {len(misses) - len(serious)} weak")

    log = [f"# merge-lysias {slug}", "", f"## Problems ({len(problems)})", ""] + [f"* {x}" for x in problems]
    log += ["", f"## Apparatus lemmas not found on their lines ({len(misses)})", "",
            "SERIOUS: the text may have slipped to the check text's reading; look at the page. WEAK: a conjecture, a "
            "variant in another order, a note in Latin; read through once.", ""] + [f"* {x}" for x in sorted(misses)]
    (build / f"{slug}-merge.log").write_text("\n".join(log) + "\n", encoding="utf-8")
    print(f"{len(problems)} problems; log in {build / f'{slug}-merge.log'}")
    return len(problems)
