"""Lucian's A True Story from the checked batches (pipeline/transcriptions/lucian/<slug>/), Nilén's
text and apparatus, with the checks the brief requires (pipeline/PLAN-true-story.md, step 5).

The batches hold Nilén's printed lines with his page and line (133.14), `§1.7` where a section
begins, `¶` before a line he indents. merge() writes texts/<slug>/:

* grc.txt: one line per section (1.7), the lines joined; a paragraph Nilén begins inside a
  section continues the section on a line of its own with a letter (2.47b) after `@ `;
* commentary-nilen-apparatus.md: each item under the section that holds its lemma (the item's
  printed line number, which refers to Nilén's page, is not kept);
* tokens.tsv, syntax-nodes.tsv: GLAUx aligned to Nilén's words, the analyser for the rest;
* eng-harmon.txt: Harmon's translation by section (Perseus);
* commentary-jerram.md, introduction.md: Jerram's notes and introduction, once transcribed;

and pipeline/build/<slug>-merge.log (problems and the lemmas not found in their section),
<slug>-harmon-notes.md (Harmon's footnotes, each with Nilén's reading to confirm on the page),
<slug>-review.tsv (words whose lemma or parse is the analyser's).
"""
from __future__ import annotations

import difflib
import json
import re
from pathlib import Path

from . import greek
from .drama import PLAYS, TRANSCRIPTION_LICENSE, Play, _meta_lines, skel
from .lucian_pages import (APP_KEY, KEY, SECTION_MARK, out_dir, perseus_prose, read_batches, transcriptions_dir,
                           translation_sections)

ROOT = Path(__file__).resolve().parent.parent.parent
PIPELINE = ROOT / "pipeline"
LETTERS = "bcdefghijk"
# Misprints in the edition's text: the batches keep what is printed; the text shows the right
# reading and the apparatus says so (the author's decision, 2026-11-08). Key: Nilén's page.line.
MISPRINTS: dict[str, dict[str, tuple[str, str]]] = {
    "truestory": {
        "144.3": ("σκοκῶν", "σκοπῶν"),        # 1.18
        "144.7": ("μεγέθος", "μέγεθος"),      # 1.18
        "144.21": ("ἐξώγρησαν", "ἐζώγρησαν"),  # 1.18 (ζωγρέω; the printed ξ is a wrong sort)
    },
}


# --- the text --------------------------------------------------------------------------------

def assemble(pages: dict[str, dict], index: list[dict]) -> dict:
    """The units of the text and where each printed line's words went.

    Returns {'units': [{'n', 'para', 'words': [(word, key)]}], 'lines': {key: [(unit index,
    word index in unit, word)]}, 'titles': {book: text}, 'title_keys': {key: book},
    'problems': [...]}."""
    units: list[dict] = []
    lines: dict[str, list[tuple[int, int, str]]] = {}
    titles: dict[str, str] = {}
    title_keys: dict[str, str] = {}
    problems: list[str] = []
    sec = None
    letter = 0
    pending_para = False
    seen: set[str] = set()
    book_next = "1"
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
            if not KEY.match(key):
                problems.append(f"{p['stem']}: bad key {key!r}")
                continue
            if key in seen:
                problems.append(f"{p['stem']}: {key} twice; the second left out")
                continue
            seen.add(key)
            lines[key] = []
            if text.startswith("[title]"):
                titles[book_next] = text[len("[title]"):].strip()
                title_keys[key] = book_next
                book_next = str(int(book_next) + 1)
                pending_para = True
                continue
            text = re.sub(r"^\|\s*", "", text)
            pos = 0
            marks = list(SECTION_MARK.finditer(text))
            chunks: list[tuple[str | None, str]] = []
            for mk in marks:
                chunks.append((None, text[pos:mk.start()]))
                chunks.append((f"{mk.group(1)}.{mk.group(2)}", ""))
                pos = mk.end()
            chunks.append((None, text[pos:]))
            first_chunk = True
            for new, chunk in chunks:
                if new is not None:
                    sec, letter = new, 0
                    units.append({"n": sec, "para": pending_para and first_chunk, "words": []})
                    if pending_para and first_chunk:
                        pending_para = False
                    continue
                words = chunk.split()
                if not words:
                    continue
                if sec is None:
                    problems.append(f"{p['stem']} {key}: words before the first section mark: {chunk[:40]!r}")
                    continue
                if pending_para and first_chunk:
                    # a paragraph Nilén begins inside a section
                    letter += 1
                    units.append({"n": f"{sec}{LETTERS[letter - 1]}", "para": True, "words": []})
                    pending_para = False
                first_chunk = False
                u = units[-1]
                for w in words:
                    lines[key].append((len(units) - 1, len(u["words"]), w))
                    u["words"].append((w, key))
            if pending_para:
                problems.append(f"{p['stem']} {key}: ¶ before a line without words")
                pending_para = False
    units, lines = split_long(units, lines)
    return {"units": units, "lines": lines, "titles": titles, "title_keys": title_keys, "problems": problems}


SPLIT_LIMIT = 550   # characters: a section longer than this is divided at sentence ends
SPLIT_MIN = 200     # no part shorter than this


def split_long(units: list[dict], lines: dict[str, list[tuple[int, int, str]]]) -> tuple[list[dict], dict]:
    """Long sections divided at sentence ends into lines of their own (1.7, 1.7b, 1.7c), so that
    no line is taller than the reader's page (the app pages by whole lines; 22 sections are longer
    than a phone's page). The parts of a section are lettered in order, a paragraph's continuation
    (2.47b) among them; only the first carries the section's number in the app."""
    out: list[dict] = []
    remap: dict[tuple[int, int], tuple[int, int]] = {}
    for ui, u in enumerate(units):
        words = u["words"]
        parts: list[list[int]] = [[]]
        length = 0
        for wi, (w, _k) in enumerate(words):
            parts[-1].append(wi)
            length += len(w) + 1
            ends = re.search(r"[.·;:]['’”»)]*$", w) is not None
            rest = sum(len(x) + 1 for x, _k2 in words[wi + 1:])
            if ends and rest >= SPLIT_MIN and length >= SPLIT_MIN:
                # cut here if the next sentence would carry the part past the limit
                nxt = 0
                for x, _k2 in words[wi + 1:]:
                    nxt += len(x) + 1
                    if re.search(r"[.·;:]['’”»)]*$", x):
                        break
                if length + nxt > SPLIT_LIMIT:
                    parts.append([])
                    length = 0
        for k, part in enumerate(p for p in parts if p):
            nu = {"n": u["n"], "para": u["para"] and k == 0, "words": [words[wi] for wi in part]}
            for j, wi in enumerate(part):
                remap[(ui, wi)] = (len(out), j)
            out.append(nu)
    # letters in order within each section
    count: dict[str, int] = {}
    for u in out:
        base = re.sub(r"[a-z]$", "", u["n"])
        k = count.get(base, 0)
        u["n"] = base if k == 0 else f"{base}{LETTERS[k - 1]}"
        count[base] = k + 1
    new_lines = {key: [(*remap[(a, b)], w) for a, b, w in entries] for key, entries in lines.items()}
    return out, new_lines


# --- the apparatus ---------------------------------------------------------------------------

class _LowerGreek:
    """search(s): whether s holds a small Greek letter (not a siglum: Γ Ω are capitals)."""

    @staticmethod
    def search(s: str) -> bool:
        return any(c.islower() and ("Ͱ" <= c <= "Ͽ" or "ἀ" <= c <= "῿") for c in s)


_LOWER_GREEK = _LowerGreek()


def correct_misprints(slug: str, text: dict, problems: list[str]) -> list[tuple[int, str]]:
    """The right reading in the text where the edition misprints a word (MISPRINTS), and for each
    an apparatus note on its section, marked as this edition's: [(unit index, note)]."""
    notes: list[tuple[int, str]] = []
    for key, (printed, right) in MISPRINTS.get(slug, {}).items():
        done = False
        for k, (u, wi, w) in enumerate(text["lines"].get(key, [])):
            if printed in w:
                new = w.replace(printed, right)
                text["lines"][key][k] = (u, wi, new)
                word, wkey = text["units"][u]["words"][wi]
                text["units"][u]["words"][wi] = (word.replace(printed, right), wkey)
                notes.append((u, f"{right} [Print has: {printed}]"))
                done = True
                break
        if not done:
            problems.append(f"misprint {key}: “{printed}” not found on the line")
    return notes


def lemma_of(item: str) -> tuple[list[str], list[str]]:
    """The lemma of an apparatus item, as words: (first words, last words) for a range written
    "ἄν — διπλασιάσαντος]"; the words before a ']' if there is one, else the leading words that
    hold a small Greek letter (the sigla ΓΩSZ, Latin, numbers end it). ([], []) if the item
    begins otherwise ("pro οὐ spat. …", "Libri: …")."""
    head = item.split("]")[0].split() if "]" in item else []
    if head and all(_LOWER_GREEK.search(t) or t in ("—", "–") or re.fullmatch(r"[⟨⟩\[\]()·,.]+", t) for t in head):
        lem = head
    else:
        lem = []
        for t in item.split():
            if t.startswith("(") and lem:
                break  # "μινῴου (ι ex η corr.) S*": the parenthesis reports a detail of the reading
            core = t.strip(",.;:·()⟨⟩[]")
            if t in ("—", "–") or (core and _LOWER_GREEK.search(core) and not re.search(r"[A-Za-z]", core)):
                lem.append(t)
                continue
            break
    while lem and lem[-1] in ("—", "–"):
        lem.pop()
    if not lem:
        return [], []
    text = " ".join(lem)
    if "—" in text or "–" in text:
        a, _, b = _split_dash(text)
        return a.split(), b.split()
    return lem, []


def greek_runs(item: str) -> list[list[str]]:
    """The item's readings: runs of words holding a small Greek letter, separated by sigla, Latin
    and numbers. Nilén's positive items ("πνέοντι ΓΩS πνεύματι ZNFI") have two or more, the first
    being his text's reading; a negative item ("οὐκέτι F") has one, a variant."""
    runs: list[list[str]] = []
    cur: list[str] = []
    for t in item.replace("]", " ] ").split():
        core = t.strip(",.;:·()⟨⟩[]")
        if core and _LOWER_GREEK.search(core) and not re.search(r"[A-Za-z]", core):
            cur.append(t)
        elif t in ("—", "–") and cur:
            cur.append(t)
        else:
            if cur:
                runs.append(cur)
            cur = []
    if cur:
        runs.append(cur)
    return runs


def _split_dash(text: str) -> tuple[str, str, str]:
    m = re.split(r"\s*[—–]\s*", text, maxsplit=1)
    return (m[0], "—", m[1] if len(m) > 1 else "")


def _sk(w: str) -> str:
    return skel(w).translate(str.maketrans("ςχ", "σκ"))


def _find(lemma: list[str], cands: list[tuple[int, int, str]], exact: bool = False) -> int | None:
    """Where the lemma's words stand in a run of words (index into cands): an exact match of
    the skeletons first, else (unless `exact`) one where every word is close (a letter or two)."""
    ls = [_sk(w) for w in lemma if _sk(w)]
    if not ls:
        return None
    cs = [_sk(c[2]) for c in cands]
    for strict in ((True,) if exact else (True, False)):
        for i in range(len(cs) - len(ls) + 1):
            ok = True
            for k, l in enumerate(ls):
                c = cs[i + k]
                if strict:
                    ok = c == l
                else:
                    ok = c == l or (len(l) >= 3 and difflib.SequenceMatcher(None, c, l).ratio() >= 0.75)
                if not ok:
                    break
            if ok:
                return i
    return None


def place_apparatus(pages: dict[str, dict], index: list[dict], text: dict) -> tuple[list[tuple[int, str]], list[str], list[str]]:
    """Each item under the unit that holds its lemma: [(unit index, item)], the lemma misses
    (for the log and the step-5 agent), problems."""
    lines = text["lines"]
    units = text["units"]
    placed: list[tuple[int, str]] = []
    misses: list[str] = []
    problems: list[str] = []
    for p in index:
        block = pages.get(p["stem"])
        if block is None:
            continue
        page = p["page"]
        keys = [k for k, _t in block["text"] if KEY.match(k)]
        last_unit = None
        for n, item in block["apparatus"]:
            m = APP_KEY.match(n)
            if not m:
                problems.append(f"{p['stem']}: bad apparatus number {n!r}")
                continue
            if n == "-":
                if last_unit is None:
                    first = next((lines[k][0][0] for k in keys if lines.get(k)), None)
                    last_unit = first if first is not None else (len(units) - 1 if units else None)
                if last_unit is not None:
                    placed.append((last_unit, item))
                continue
            a, b = int(m.group(1)), int(m.group(2) or m.group(3) or m.group(1))
            if "sq" in n:
                b = a + 1
            ka, kb = f"{page}.{a}", f"{page}.{b}"
            if ka not in lines:
                problems.append(f"{p['stem']}: apparatus {n} names line {ka}, which the text does not have")
                continue
            if ka in text["title_keys"] and kb == ka:
                book = text["title_keys"][ka]
                u = next((i for i, x in enumerate(units) if x["n"] == f"{book}.1"), 0)
                placed.append((u, item))
                last_unit = u
                continue
            # the words of the lines named, and one line on either side
            ordered = [k for k in lines]
            ia = ordered.index(ka)
            ib = ordered.index(kb) if kb in lines else ia
            window_keys = ordered[max(0, ia - 1): ib + 2]
            cands = [c for k in window_keys for c in lines[k]]
            own = [c for k in ordered[ia: ib + 1] for c in lines[k]]
            first, last = lemma_of(item)
            # a slip to Harmon's reading shows as Nilén's first reading missing from the text while
            # a later reading of the same item stands there; or an explicit lemma] not found
            runs = [r for r in greek_runs(item) if [w for w in r if w.strip("΄'") not in ("γρ",)]]
            later_in_text = any(_find(r, cands, exact=True) is not None for r in runs[1:])
            positive = "]" in item or later_in_text
            where = f"{page}.{n} (lines {ka}{'-' + kb if kb != ka else ''})"
            u = None
            if first:
                i = _find(first, own, exact=True)
                hit = own[i] if i is not None else None
                if hit is None:
                    i = _find(first, cands, exact=True)
                    hit = cands[i] if i is not None else None
                exact = hit is not None
                if hit is None:
                    i = _find(first, cands)
                    hit = cands[i] if i is not None else None
                if hit is None:
                    # a variant in another order or with a word added: most of its words on the lines
                    ws = {_sk(c[2]): c for c in cands}
                    found = [ws[_sk(w)] for w in first if _sk(w) in ws]
                    if found and len(found) >= max(1, len([w for w in first if _sk(w)]) - 1):
                        hit = found[0]
                if hit is not None:
                    u = hit[0]
                    if last and _find(last, cands) is None:
                        misses.append(f"WEAK {where}: the end of the lemma range “{' '.join(last)}” not found: {item}")
                if positive and not exact:
                    near = f" (the text there: {' '.join(c[2] for c in own)})"
                    why = "a later reading of the item stands in the text" if later_in_text else "the lemma] is not in the text"
                    misses.append(f"SERIOUS {where}: Nilén's reading “{' '.join(first)}” is not in the text as written ({why})"
                                  f"{near}: {item}")
                elif hit is None:
                    misses.append(f"WEAK {where}: variant “{' '.join(first)}” matches nothing on the lines: {item}")
            if u is None:
                # an addition or a note in Latin: the section of the Greek word it names, else the line's
                named = re.search(r"(?:post|ante|inter|pro|supra)\s+([^\s,;:]+)", item)
                if named and _LOWER_GREEK.search(named.group(1)):
                    i = _find([named.group(1)], cands)
                    if i is not None:
                        u = cands[i][0]
                if u is None:
                    if own:
                        u = own[0][0]
                    elif cands:
                        u = cands[0][0]
                    else:
                        problems.append(f"{p['stem']}: apparatus {n}: no words on the lines it names")
                        continue
                    if not first:
                        misses.append(f"WEAK {page}.{n}: no Greek lemma; filed under {units[u]['n']}: {item}")
            placed.append((u, item))
            last_unit = u
    return placed, misses, problems


# --- Harmon's footnotes ----------------------------------------------------------------------

def harmon_checklist(sources: Path, play: Play, text: dict, placed: list[tuple[int, str]]) -> str:
    """Harmon's footnotes, each with the place in Nilén's text (page and line), the words there
    and Nilén's apparatus on that section, for a reader to confirm against the page."""
    toks, notes = perseus_prose(sources / play.perseus)
    units = text["units"]
    by_sec: dict[str, list[int]] = {}
    for i, u in enumerate(units):
        by_sec.setdefault(re.sub(r"[a-z]$", "", u["n"]), []).append(i)
    app_by_unit: dict[int, list[str]] = {}
    for u, item in placed:
        app_by_unit.setdefault(u, []).append(item)
    out = ["# Harmon's footnotes: Nilén's reading to confirm", "",
           "Harmon's Loeb (the check text) marks with a footnote each place where his text departs from "
           "the manuscripts or adopts a conjecture. For each, the words of Nilén's text at that place as "
           "the batches have them, the page and line, and Nilén's apparatus on that section. Confirm on the "
           "page crop that the text has Nilén's reading, not Harmon's.", ""]
    for k, nt in enumerate(notes, 1):
        after = nt["after"]
        ctx = " ".join(t["t"] for t in toks[max(0, after - 4): after + 4]) if after >= 0 else "(the title)"
        out.append(f"## {k}. {nt['sec']} ({nt['n']})")
        out.append("")
        out.append(f"* Harmon's note: {nt['text']}")
        out.append(f"* Harmon's text: … {ctx} …")
        ws = [(w, key, i) for i in by_sec.get(nt["sec"], []) for w, key in units[i]["words"]]
        if after >= 0 and ws:
            # the word of ours nearest Harmon's: the best match of the context's skeletons
            target = [skel(t["t"]) for t in toks[max(0, after - 2): after + 3]]
            best, score = 0, -1.0
            for j in range(len(ws)):
                seq = [skel(w) for w, _k, _i in ws[max(0, j - 2): j + 3]]
                s = difflib.SequenceMatcher(None, seq, target).ratio()
                if s > score:
                    best, score = j, s
            lo, hi = max(0, best - 5), min(len(ws), best + 6)
            out.append(f"* Nilén's text (as transcribed), {ws[best][1]}: … {' '.join(w for w, _k, _i in ws[lo:hi])} …")
        else:
            out.append("* Nilén's text: section not found" if after >= 0 else "* (a note on the title)")
        items = [it for i in by_sec.get(nt["sec"], []) for it in app_by_unit.get(i, [])]
        lem = {skel(w) for w in re.findall(r"[Ͱ-Ͽἀ-῿ʼ]+", nt["text"])}
        rel = [it for it in items if lem & {skel(w) for w in re.findall(r"[Ͱ-Ͽἀ-῿ʼ]+", it)}]
        out.append("* Nilén's apparatus there: " + (" ‖ ".join(rel) if rel else "(no item on these words)"))
        out.append("* Verdict: ")
        out.append("")
    return "\n".join(out) + "\n"


# --- tokens ---------------------------------------------------------------------------------

def _tokens(play: Play, doc, sources: Path, out: Path, lexicon: Path, build: Path) -> int:
    """drama._tokens, with the hand analyses (keyed by section and form: "1.29 κατετέθημεν") put on
    whichever line of the section holds the form (1.29 or 1.29b: the parts depend on the split)."""
    import dataclasses

    from .drama import _tokens as drama_tokens
    from .drama_fixes import HAND_ANALYSES

    expanded: dict[str, tuple[str, str]] = {}
    for key, value in HAND_ANALYSES.get(play.slug, {}).items():
        sec, _, form = key.partition(" ")
        for line in doc.lines:
            if re.sub(r"[a-z]$", "", line.n) == sec and form in [w for w, _s, _e in greek.words(line.text)]:
                expanded[f"{line.n} {form}"] = value
    return drama_tokens(dataclasses.replace(play, hand_analyses={**play.hand_analyses, **expanded}), doc, sources, out, lexicon, build)


# --- merge -----------------------------------------------------------------------------------

def merge(slug: str, sources: Path, texts: Path, build: Path, lexicon: Path) -> int:
    from .textfmt import Document, Line, Section, Speaker, write_file

    play = PLAYS[slug]
    tdir = transcriptions_dir(slug)
    od = out_dir(slug)
    index_path = od / "pages.json"
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

    # sections against Perseus: every section once, in order
    toks, _notes = perseus_prose(sources / play.perseus)
    want = list(dict.fromkeys(t["sec"] for t in toks))
    have = [u["n"] for u in units if not re.search(r"[a-z]$", u["n"])]
    if have != want:
        sm = difflib.SequenceMatcher(None, have, want, autojunk=False)
        for op, a0, a1, b0, b1 in sm.get_opcodes():
            if op != "equal":
                problems.append(f"sections: ours {have[a0:a1]} where Perseus has {want[b0:b1]}")

    meta = {
        "title": play.title, "author": play.author, "lang": "grc",
        "source": f"{play.edition}; read from the Internet Archive scan {play.scan} by OCR, matched word by word to the "
                  f"Perseus Digital Library text ({play.tlg}.perseus-grc2, Harmon's Loeb), and checked against the scan "
                  "where the two disagreed",
        "edition": play.edition,
        "license": TRANSCRIPTION_LICENSE,
        "layout": "prose",
        "syntax": "automatic",
        "pronunciation": play.pronunciation,
    }
    doc = Document(meta=meta)
    book = None
    for u in units:
        b = u["n"].split(".")[0]
        if b != book:
            book = b
            numeral = {"1": "Α", "2": "Β"}.get(b, b)
            doc.items.append(Section(1, "book", f"{b} · {numeral}"))
        if u["para"]:
            doc.items.append(Speaker(""))
        doc.items.append(Line(u["n"], " ".join(w for w, _k in u["words"])))
    write_file(out / "grc.txt", doc)
    print(f"wrote {out / 'grc.txt'}: {len(units)} lines ({len(have)} sections), "
          f"{sum(1 for u in units if u['para'])} paragraphs, from {len(pages)} pages")

    # the apparatus
    placed, misses, probs = place_apparatus(pages, index, text)
    problems += probs
    placed += misprint_notes
    md = _meta_lines({
        "title": f"Critical apparatus ({play.app_editor_name})",
        "author": play.app_editor_name, "lang": "lat",
        "source": f"{play.edition}; transcribed from the Internet Archive scan {play.scan}",
        "license": TRANSCRIPTION_LICENSE,
    }) + [""]
    # under the section (1.2), not its parts (1.2b): the parts are the reader's page lines, the
    # section is the unit the notes speak to (and the app looks a note's line up by its number)
    grouped: dict[str, list[str]] = {}
    for u, item in sorted(placed, key=lambda x: x[0]):
        grouped.setdefault(re.sub(r"[a-z]$", "", units[u]["n"]), []).append(item)
    for sec, items in grouped.items():
        md.append(f"## {sec}")
        # every asterisk of Nilén's apparatus is printed (Γ* the first hand, *** erased letters):
        # written \\* so that two in one item cannot become italics (build.md_to_html)
        md.append("\n\n".join(items).replace("*", "\\*"))
        md.append("")
    (out / f"commentary-{play.app_editor}-apparatus.md").write_text("\n".join(md) + "\n", encoding="utf-8")
    print(f"wrote commentary-{play.app_editor}-apparatus.md: {len(grouped)} sections, {len(placed)} items; "
          f"{len(misses)} lemmas not found in their lines")
    (build / f"{slug}-harmon-notes.md").write_text(harmon_checklist(sources, play, text, placed), encoding="utf-8")

    # lemmas, morphology, syntax
    review = _tokens(play, doc, sources, out, lexicon, build)
    print(f"review list: {review} words in {build / f'{slug}-review.tsv'}")

    # Harmon's translation by section
    rows = translation_sections(sources / play.trans_file)
    have_n = {u["n"] for u in units}
    eng = []
    for n, t in rows:
        if n not in have_n:
            problems.append(f"translation: section {n} not in the Greek")
        eng.append(f"{n}\t{t}")
    tmeta = {"title": play.title_en, "translator": play.translator, "lang": "eng",
             "source": f"Perseus Digital Library, {Path(play.trans_file).stem}: {play.trans_edition}",
             "license": play.trans_license}
    (out / f"eng-{play.trans_key}.txt").write_text("\n".join(_meta_lines(tmeta) + [""] + eng) + "\n", encoding="utf-8")
    print(f"wrote eng-{play.trans_key}.txt: {len(eng)} sections")

    # Jerram's notes and introduction, once transcribed (steps 6-7)
    from .drama_prose import merge_kind

    def checked(kind: str) -> bool:
        """Whether the kind's batches exist and every flag in them is answered (the drafts are
        not merged before the agents have checked them)."""
        files = sorted(tdir.glob(f"{kind}-*.md"))
        return bool(files) and not any(re.search(r"(?m)^\d+ .*→\s*$", f.read_text(encoding="utf-8")) for f in files)

    paras = merge_kind(tdir, "notes") if checked("notes") else []
    if paras:
        n_notes, probs = jerram_notes(play, paras, units, out, sources, build)
        problems += probs
        print(f"wrote commentary-{play.notes_editor}.md: {n_notes} notes")
    paras = merge_kind(tdir, "intro") if checked("intro") else []
    if paras and paras[0].strip() == "# Introduction":
        paras = paras[1:]  # the app's sheet is already headed "Introduction"
    if paras:
        md = _meta_lines({
            "title": "Introduction", "author": play.notes_editor_name,
            "source": f"{play.notes_edition}, the introduction; transcribed from the Internet Archive scan {play.scan_for('intro')}",
            "license": TRANSCRIPTION_LICENSE,
        }) + [""] + ["\n\n".join(paras)]
        (out / "introduction.md").write_text("\n".join(md).rstrip() + "\n", encoding="utf-8")
        print(f"wrote introduction.md: {sum(1 for p in paras if p.startswith('#'))} headings")

    # the Dickinson College Commentaries' notes (step 8), from the saved pages
    dcc = sources / "dcc" / "lucian-true"
    if dcc.exists() and any(dcc.glob("*-*.html")):
        n_dcc, probs = write_dcc(dcc, units, out / "commentary-dcc.md")
        problems += probs
        print(f"wrote commentary-dcc.md: {n_dcc} paragraphs")

    log = build / f"{slug}-merge.log"
    serious = [m for m in misses if m.startswith("SERIOUS")]
    weak = [m for m in misses if not m.startswith("SERIOUS")]
    log.write_text("\n".join(problems + ["", f"# Nilén's readings (positive items) not found in the text as written ({len(serious)})"]
                             + serious + ["", f"# variants that match nothing, items without a Greek lemma ({len(weak)})"] + weak) + "\n",
                   encoding="utf-8")
    print(f"{len(problems)} problems, {len(serious)} positive lemmas not in the text, {len(weak)} weak misses ({log})")
    return len(problems)


def jerram_line_map(play: Play, sources: Path, build: Path | None = None) -> dict[str, list[tuple[str, str]]]:
    """Jerram's own lines ('1.4': book I, line 4), each with the words on it as (skeleton,
    section): his text pages (Play.notes_text_leaves) read by Tesseract, the Greek lines matched
    word by word to the Perseus text (a line counts as Greek if a third of its words are matched;
    his English summaries and running heads are not), and numbered by the numbers printed every
    fifth line in the right margin (between them, by counting; a page without one runs on from
    the page before; each book starts again at 1). Cached in build/<slug>-jerram-lines.json."""
    from PIL import Image

    from .drama_pages import DASHES, ocr_leaf, ocr_norm, read_lines, scan_dirs
    from .gorgias_pages import align

    cache = (build or PIPELINE / "build") / f"{play.slug}-jerram-lines.json"
    if cache.exists():
        return {k: [tuple(x) for x in v] for k, v in json.loads(cache.read_text(encoding="utf-8")).items()}
    scan = play.notes_scan
    _, sbuild = scan_dirs(scan)
    leaves = [l for a, b in play.notes_text_leaves for l in range(a, b + 1)]
    plines: list[dict] = []
    ocr: list[dict] = []
    for leaf in leaves:
        with Image.open(sbuild / "pages" / f"leaf_{leaf:04d}.png") as im:
            W, H = im.size
        for l in read_lines(ocr_leaf(scan, leaf)):
            if l["bbox"][3] < 0.07 * H:
                continue  # the running head: BOOK I. 5
            ws = sorted(l["words"], key=lambda w: w["bbox"][0])
            num = None
            # his line numbers stand in the outer margin: at the right of a right-hand page, at the
            # left of a left-hand one
            if ws and re.fullmatch(r"\d{1,3}", ws[-1]["text"].strip("._,")) and ws[-1]["bbox"][0] > 0.8 * W:
                num = int(ws[-1]["text"].strip("._,"))
                ws = ws[:-1]
            elif ws and re.fullmatch(r"\d{1,3}", ws[0]["text"].strip("._,")) and ws[0]["bbox"][2] < 0.2 * W:
                num = int(ws[0]["text"].strip("._,"))
                ws = ws[1:]
            li = len(plines)
            plines.append({"leaf": leaf, "num": num, "text": " ".join(w["text"] for w in ws)})
            for w in ws:
                for piece in DASHES.split(ocr_norm(w["text"])):
                    if skel(piece):
                        ocr.append({"t": piece, "skel": skel(piece), "line": li, "conf": w["conf"]})
    toks, _notes = perseus_prose(sources / play.perseus)
    match = align(ocr, toks)
    by_line: dict[int, list[int]] = {}
    for j, o in enumerate(match):
        if o is not None:
            by_line.setdefault(ocr[o]["line"], []).append(j)
    count = {li: sum(1 for t in ocr if t["line"] == li) for li in range(len(plines))}
    # a Greek line: half its words matched, two of them of three letters or more (a line of loose
    # accents read on its own matches a letter or two by chance; an English summary nothing)
    def is_greek(li: int) -> bool:
        hits = by_line.get(li, [])
        return bool(count[li]) and len(hits) >= count[li] / 2 and sum(1 for j in hits if len(toks[j]["skel"]) >= 3) >= 2

    greek_lines = [li for li in range(len(plines)) if is_greek(li)]
    out: dict[str, list[tuple[str, str]]] = {}
    book, n = None, 0
    by_leaf: dict[int, list[int]] = {}
    for li in greek_lines:
        by_leaf.setdefault(plines[li]["leaf"], []).append(li)
    for leaf in leaves:
        gl = by_leaf.get(leaf, [])
        if not gl:
            continue
        # the book of each line from the sections of its words; a new book starts at 1. The
        # page's printed numbers (multiples of 5, near where the count has got to; the OCR
        # misreads some: 338 for 340) fix the numbering of its lines; a page without one runs on
        b0 = toks[by_line[gl[0]][0]]["sec"].split(".")[0]
        start = 0 if b0 != book else n
        anchors: list[tuple[int, int]] = []  # (index on the page, printed number)
        for i, li in enumerate(gl):
            num = plines[li]["num"]
            if num and num % 5 == 0 and abs(num - (start + i + 1)) <= 8 and (not anchors or num > anchors[-1][1]):
                anchors.append((i, num))
        for i, li in enumerate(gl):
            b = toks[by_line[li][0]]["sec"].split(".")[0]
            if b != book:
                book, n = b, 0
            # from the nearest anchor before the line (after it, for the lines above the first)
            before = [a for a in anchors if a[0] <= i]
            if before:
                n = before[-1][1] + (i - before[-1][0])
            elif anchors:
                n = max(n + 1, anchors[0][1] - (anchors[0][0] - i))
            else:
                n += 1
            out[f"{book}.{n}"] = [(t["skel"], t["sec"]) for t in (toks[j] for j in by_line[li])]
    cache.write_text(json.dumps(out, ensure_ascii=False), encoding="utf-8")
    return out


def jerram_notes(play: Play, paras: list[str], units: list[dict], out: Path, sources: Path | None = None,
                 build: Path | None = None) -> tuple[int, list[str]]:
    """Jerram's notes under our sections. The batches head each note with his line number
    (`## 4`) under `# Book I` / `# Book II`; the section is that of the word on his line that
    the note's lemma names (else of the line's first word), from jerram_line_map."""
    problems: list[str] = []
    jmap = jerram_line_map(play, sources or PIPELINE / "sources", build)
    have = {u["n"] for u in units}
    placed: list[tuple[str, list[str]]] = []
    book = "1"
    cur: tuple[str, list[str]] | None = None
    notes: list[tuple[str, str, list[str]]] = []  # (book, his line, paragraphs)
    for p in paras:
        mb = re.match(r"^# Book ([IVX]+)$", p)
        if mb:
            book = {"I": "1", "II": "2"}.get(mb.group(1), mb.group(1))
            continue
        mh = re.match(r"^##\s+(\d+)(?:-(\d+))?\s*$", p)
        if mh:
            notes.append((book, mh.group(1), []))
        elif notes:
            notes[-1][2].append(p)
        else:
            problems.append(f"jerram: a paragraph before the first note: {p[:60]}")
    for bk, line, body in notes:
        words = jmap.get(f"{bk}.{line}")
        if not words:
            near = [int(k.split(".")[1]) for k in jmap if k.startswith(bk + ".") and int(k.split(".")[1]) <= int(line)]
            words = jmap.get(f"{bk}.{max(near)}") if near else None
            problems.append(f"jerram: his line {bk}.{line} not found in his text; filed by line {bk}.{max(near) if near else '?'}")
        if not words:
            continue
        sec = words[0][1]
        lemma = re.match(r"^\*\*(.+?)\*\*", body[0]) if body else None
        if lemma:
            ls = [skel(w) for w in re.findall(r"[Ͱ-Ͽἀ-῿ʼ]+", lemma.group(1)) if skel(w)]
            found = False
            # the lemma on his line; else on a line near it (his number misprinted or misread)
            for d in (0, -1, 1, -2, 2, -3, 3) + tuple(x for k in range(4, 13) for x in (-k, k)):
                ws = jmap.get(f"{bk}.{int(line) + d}", [])
                hit = next((s for sk, s in ws if ls and sk == ls[0]), None)
                if hit:
                    sec, found = hit, True
                    if d:
                        problems.append(f"jerram: the lemma of his note {bk}.{line} stands on his line {bk}.{int(line) + d}")
                    break
            if ls and not found:
                problems.append(f"jerram: the lemma of his note {bk}.{line} ({lemma.group(1)}) is not on his lines {int(line) - 12}-{int(line) + 12}; "
                                f"filed under {sec}")
        if sec not in have:
            problems.append(f"jerram: note on his {bk}.{line} goes to section {sec}, which we do not have")
            continue
        if placed and placed[-1][0] == sec:
            placed[-1][1].extend(body)
        else:
            placed.append((sec, list(body)))
    md = _meta_lines({
        "title": f"Commentary ({play.notes_editor_name})",
        "author": play.notes_editor_name, "lang": "eng",
        "source": f"{play.notes_edition}, the notes; transcribed from the Internet Archive scan {play.scan_for('notes')}",
        "license": TRANSCRIPTION_LICENSE,
    }) + [""]
    for h, body in placed:
        md.append(f"## {h}")
        md.append("\n\n".join(body))
        md.append("")
    (out / f"commentary-{play.notes_editor}.md").write_text("\n".join(md) + "\n", encoding="utf-8")
    return sum(len(b) for _h, b in placed), problems


DCC_META = {
    "title": "Commentary (Dickinson College Commentaries)",
    "author": "Eric Casey, Evan Hayes, Stephen Nimis",
    "lang": "eng",
    "source": "Lucian, True History, notes by Eric Casey, Evan Hayes, and Stephen Nimis, Dickinson College "
              "Commentaries (2023), https://dcc.dickinson.edu/lucian-true/ ; the notes only (their vocabulary "
              "lists are left out); their text is Harmon's, so a lemma may differ from Nilén's words",
    "license": "CC BY-SA (Dickinson College Commentaries)",
}


def dcc_notes(page: str) -> list[str]:
    """The notes of one DCC page (the field 'field-notes'), as Markdown paragraphs: the italic
    summary as *…*, each note's lemma (the text before the first colon) in bold."""
    import html as htmlmod

    m = re.search(r'field--name-field-notes[^>]*>(.*?)</details>', page, re.S)
    if not m:
        return []
    out: list[str] = []
    for p in re.findall(r"<p[^>]*>(.*?)</p>", m.group(1), re.S):
        t = re.sub(r"<br\s*/?>", " ", p)
        t = re.sub(r"</?(?:em|i)>", "*", t)
        t = re.sub(r"</?(?:strong|b)>", "**", t)
        t = re.sub(r"<[^>]+>", "", t)
        t = htmlmod.unescape(t).replace("\xa0", " ")
        t = " ".join(t.split())
        t = re.sub(r"\*\s*\*", "", t).strip()
        if not t or t == "*" or t == "VERB LIST":
            continue  # a link to the site's list of verbs, not a note
        t = greek.nfc(t)
        if not t.startswith("*"):
            mm = re.match(r"^([^:*]{1,90}?):\s", t)
            if mm and re.search(r"[Ͱ-Ͽἀ-῿]", mm.group(1)):
                t = f"**{mm.group(1).strip()}**: {t[mm.end():]}"
            else:
                # no colon ("γινομένης = γιγνομένης", "ἔρρει impf. of ῥέω"): the Greek words that
                # open the note are its lemma
                words = t.split(" ")
                k = 0
                while k < len(words) and (re.search(r"[Ͱ-Ͽἀ-῿]", words[k]) and not re.search(r"[A-Za-z]", words[k])
                                          or words[k] in ("...", "…")):
                    k += 1
                while k > 0 and words[k - 1] in ("...", "…"):
                    k -= 1
                if k:
                    lemma = " ".join(words[:k]).rstrip(";,")
                    t = f"**{lemma}**" + t[len(" ".join(words[:k])):]
        out.append(t)
    return out


def write_dcc(src: Path, units: list[dict], out_path: Path) -> tuple[int, list[str]]:
    """commentary-dcc.md from the saved pages (pipeline/sources/dcc/lucian-true/<b>-<s>.html)."""
    have = {u["n"] for u in units}
    problems: list[str] = []
    md = _meta_lines(DCC_META) + [""]
    n = 0
    # one page per section (1-7.html), or per range (2-7-2-10.html: filed under its first section)
    files = sorted((p for p in src.glob("*-*.html") if re.fullmatch(r"\d+-\d+(?:-\d+-\d+)?", p.stem)),
                   key=lambda p: tuple(int(x) for x in p.stem.split("-")))
    for f in files:
        sec = ".".join(f.stem.split("-")[:2])
        notes = dcc_notes(f.read_text(encoding="utf-8"))
        if not notes:
            problems.append(f"dcc: no notes on {f.name}")
            continue
        if sec not in have:
            problems.append(f"dcc: section {sec} not in our text")
            continue
        md.append(f"## {sec}")
        md.append("\n\n".join(notes))
        md.append("")
        n += len(notes)
    out_path.write_text("\n".join(md) + "\n", encoding="utf-8")
    return n, problems


def main(slug: str) -> int:
    return merge(slug, PIPELINE / "sources", ROOT / "texts", PIPELINE / "build", ROOT / "data" / "lexicon.sqlite")
