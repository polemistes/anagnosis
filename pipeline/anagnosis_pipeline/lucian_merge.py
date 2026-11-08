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
    return {"units": units, "lines": lines, "titles": titles, "title_keys": title_keys, "problems": problems}


# --- the apparatus ---------------------------------------------------------------------------

class _LowerGreek:
    """search(s): whether s holds a small Greek letter (not a siglum: Γ Ω are capitals)."""

    @staticmethod
    def search(s: str) -> bool:
        return any(c.islower() and ("Ͱ" <= c <= "Ͽ" or "ἀ" <= c <= "῿") for c in s)


_LOWER_GREEK = _LowerGreek()


def lemma_of(item: str) -> tuple[list[str], list[str]]:
    """The lemma of an apparatus item, as words: (first words, last words) for a range written
    "ἄν — διπλασιάσαντος]"; the words before a ']' if there is one, else the leading words that
    hold a small Greek letter (the sigla ΓΩSZ, Latin, numbers end it). ([], []) if the item
    begins otherwise ("pro οὐ spat. …", "Libri: …")."""
    if "]" in item:
        lem = item.split("]")[0].split()
    else:
        lem = []
        for t in item.split():
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


def _split_dash(text: str) -> tuple[str, str, str]:
    m = re.split(r"\s*[—–]\s*", text, maxsplit=1)
    return (m[0], "—", m[1] if len(m) > 1 else "")


def _sk(w: str) -> str:
    return skel(w).translate(str.maketrans("ςχ", "σκ"))


def _find(lemma: list[str], cands: list[tuple[int, int, str]]) -> int | None:
    """Where the lemma's words stand in a run of words (index into cands): an exact match of
    the skeletons first, else one where every word is close (a letter or two)."""
    ls = [_sk(w) for w in lemma if _sk(w)]
    if not ls:
        return None
    cs = [_sk(c[2]) for c in cands]
    for strict in (True, False):
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
            a, b = int(m.group(1)), int(m.group(2) or m.group(1))
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
            u = None
            if first:
                i = _find(first, own)
                hit = own[i] if i is not None else None
                if hit is None:
                    i = _find(first, cands)
                    hit = cands[i] if i is not None else None
                if hit is not None:
                    u = hit[0]
                    if last and _find(last, cands) is None:
                        misses.append(f"{page}.{n} (section {units[u]['n']}): the end of the lemma range “{' '.join(last)}” not found: {item}")
                else:
                    misses.append(f"{page}.{n} (lines {ka}{'-' + kb if kb != ka else ''}): lemma “{' '.join(first)}” not in the text: {item}")
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
                        misses.append(f"{page}.{n}: no Greek lemma; filed under {units[u]['n']}: {item}")
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
    from .drama import _tokens as drama_tokens

    return drama_tokens(play, doc, sources, out, lexicon, build)


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
    md = _meta_lines({
        "title": f"Critical apparatus ({play.app_editor_name})",
        "author": play.app_editor_name, "lang": "lat",
        "source": f"{play.edition}; transcribed from the Internet Archive scan {play.scan}",
        "license": TRANSCRIPTION_LICENSE,
    }) + [""]
    grouped: dict[int, list[str]] = {}
    for u, item in placed:
        grouped.setdefault(u, []).append(item)
    for u in sorted(grouped):
        md.append(f"## {units[u]['n']}")
        md.append("\n\n".join(grouped[u]))
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

    paras = merge_kind(tdir, "notes")
    if paras:
        n_notes, probs = jerram_notes(play, paras, units, out)
        problems += probs
        print(f"wrote commentary-{play.notes_editor}.md: {n_notes} notes")
    paras = merge_kind(tdir, "intro")
    if paras:
        md = _meta_lines({
            "title": "Introduction", "author": play.notes_editor_name,
            "source": f"{play.notes_edition}, the introduction; transcribed from the Internet Archive scan {play.scan_for('intro')}",
            "license": TRANSCRIPTION_LICENSE,
        }) + [""] + ["\n\n".join(paras)]
        (out / "introduction.md").write_text("\n".join(md).rstrip() + "\n", encoding="utf-8")
        print(f"wrote introduction.md: {sum(1 for p in paras if p.startswith('#'))} headings")

    log = build / f"{slug}-merge.log"
    log.write_text("\n".join(problems + ["", f"# lemmas not found ({len(misses)})"] + misses) + "\n", encoding="utf-8")
    print(f"{len(problems)} problems, {len(misses)} lemma misses ({log})")
    return len(problems)


def jerram_notes(play: Play, paras: list[str], units: list[dict], out: Path) -> tuple[int, list[str]]:
    """Jerram's notes under our sections: each note's heading is its book.section (1.7), given
    by the transcriber from Jerram's chapter heads (see INSTRUCTIONS-prose.md, Jerram)."""
    from .drama import notes_from_paragraphs

    problems: list[str] = []
    raw = notes_from_paragraphs(paras)
    have = {u["n"] for u in units}
    placed: list[tuple[str, list[str]]] = []
    for heading, body in raw:
        h = heading.split("-")[0]
        if h not in have:
            problems.append(f"jerram: note under {heading!r}, which is not a section of ours")
            continue
        if placed and placed[-1][0] == h:
            placed[-1][1].extend(body)
        else:
            placed.append((h, list(body)))
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


def main(slug: str) -> int:
    return merge(slug, PIPELINE / "sources", ROOT / "texts", PIPELINE / "build", ROOT / "data" / "lexicon.sqlite")
