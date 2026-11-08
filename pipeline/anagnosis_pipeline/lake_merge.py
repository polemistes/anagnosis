"""The Shepherd of Hermas from the checked batches (pipeline/transcriptions/hermas/), Lake's text and
apparatus, with the checks the brief requires (pipeline/PLAN-hermas.md, step 5).

The batches hold Lake's verses page by page (1.1.3, a verse continued from the page before as
1.1.3+), his footnote marks as superscript digits, his apparatus items by their footnote number,
the margin references by verse. merge() writes texts/<slug>/:

* grc.txt: one line per verse (book.chapter.verse of the 27 digital books), `== book Vision 1 ·
  Ὅρασις αʹ` and `=== chapter 1 · 9` (the chapter with its continuous number), `@ ` before a
  paragraph (each chapter, and where Lake begins a verse on an indented line);
* commentary-lake-apparatus.md: each item under the verse that holds its mark;
* tokens.tsv, syntax-nodes.tsv: GLAUx aligned to Lake's words, the analyser for the rest;
* eng-lake.txt: Lake's translation by verse (Perseus), to 26.30.2;
* commentary-lake.md: Lake's notes to his translation (his footnotes, his side-headings in the
  margin of the English) and his Bible references in the margin of the Greek, by verse;
* appendix.md: the end of the Shepherd in the Latin version (batch-latin.md), with Lake's English;
* aliases.tsv: the lemmas the dictionaries list under another headword (Koine spellings);
* commentary-taylor.md, introduction.md: Taylor's notes, Lake's and Taylor's introductions and
  Taylor's appendix on Hermas and the Gospels, once transcribed;

and pipeline/build/<slug>-merge.log (problems; the apparatus against First1K's), <slug>-review.tsv.
"""
from __future__ import annotations

import difflib
import json
import re
import unicodedata
from pathlib import Path

from . import greek
from .drama import PLAYS, TRANSCRIPTION_LICENSE, _meta_lines, skel
from .hermas_text import (BOOK_NAMES, LAST_GREEK, book_name, cite, compare_form, continuous_chapter, first1k_marks,
                          headings, lake_notes, lake_translation, sec_key, tauber_sections)
from .lake_pages import SUP_RE, VKEY, marks_in, out_dir, plain, read_batches, transcriptions_dir

ROOT = Path(__file__).resolve().parent.parent.parent
PIPELINE = ROOT / "pipeline"
# Misprints in Lake's Greek: the batches keep what is printed; the text shows the right reading and
# the apparatus says so (the author's rule, 2026-11-08). Key: the verse.
# Lake's misprints in the Greek text, each checked on the page (the batch notes; PLAN-hermas.md,
# step 5): verse -> [(as printed, the right reading)], whole words. Misprints inside Lake's own
# apparatus notes stay as printed.
MISPRINTS: dict[str, dict[str, list[tuple[str, str]]]] = {
    "hermas": {
        "1.2.2": [("κάρδίᾳ", "καρδίᾳ")],
        "2.2.5": [("μενανοίας", "μετανοίας")],
        "3.7.6": [("βασανισθωσιν", "βασανισθῶσιν")],
        "3.12.2": [("αλλὰ", "ἀλλὰ")],
        "11.2.6": [("ἀσύμποφα", "ἀσύμφορα")],
        "13.1.10": [("φυχῇ", "ψυχῇ")],
        "14.1.10": [("αὐτῇς", "αὐτῆς")],
        "16.1.8": [("και", "καὶ")],
        "21.1.7": [("δυναται", "δύναται")],
        "22.1.1": [("κα", "καὶ")],
        "22.2.2": [("δε", "δὲ")],
        "22.5.4": [("καί", "καὶ")],
        "23.2.6": [("ἀπο", "ἀπὸ")],
        "23.4.4": [("ἡμερα", "ἡμέρα")],
        "24.1.4": [("ἁμαρτιας", "ἁμαρτίας"), ("θίψεσι", "θλίψεσι")],
        "25.2.2": [("ῥάβδοὺς", "ῥάβδους")],
        "25.6.3": [("μενανοήσωσι", "μετανοήσωσι")],
        "25.6.4": [("ἐπαισχυνθεντες", "ἐπαισχυνθέντες")],
        "25.9.3": [("πράξέις", "πράξεις")],
        "26.1.10": [("το", "τὸ")],
        "26.4.1": [("κυκλῳ", "κύκλῳ")],
        "26.9.1": [("αὐτων", "αὐτῶν")],
        "26.11.2": [("ἀκοκριθεῖσαι", "ἀποκριθεῖσαι")],
        "26.11.7": [("παρθένον", "παρθένων")],
        "26.12.5": [("τῆν", "τὴν")],
        "26.16.5": [("σφαγῖδα", "σφραγῖδα")],
        "26.29.1": [("κακια", "κακία")],
    },
}
# misprints in a book's printed title: book -> (as printed, right)
TITLE_MISPRINTS: dict[str, dict[int, tuple[str, str]]] = {
    "hermas": {8: ("Εντολὴ", "Ἐντολὴ")},
}
# Attic headwords (GLAUx's lemmas, LSJ's) -> the Koine headword under which Abbott-Smith lists the
# word; extended from the merge log's list of lemmas Abbott-Smith lacks
KOINE: dict[str, str] = {
    "γίγνομαι": "γίνομαι", "γιγνώσκω": "γινώσκω", "ἐθέλω": "θέλω", "πορεύω": "πορεύομαι", "ἀποκρίνω": "ἀποκρίνομαι",
    "οὕτως": "οὕτω", "φοβέω": "φοβέομαι",
}


# --- the text ---------------------------------------------------------------------------------

def title_label(title: str) -> str:
    """A printed title as a section label: without Lake's footnote mark and full stop, the numeral
    sign as ʹ ("Ὅρασις βʹ." -> "Ὅρασις βʹ")."""
    t = unicodedata.normalize("NFC", plain(title)).translate(str.maketrans({"΄": "ʹ", "'": "ʹ", "’": "ʹ"}))
    return re.sub(r"\s+", " ", t).strip().rstrip(".").strip()


def assemble(pages: dict[str, dict], index: list[dict]) -> dict:
    """The verses in order: {'verses': [{'sec', 'words': [str], 'para', 'stem'}], 'marks': {(stem,
    number): verse}, 'titles': {book: [text]}, 'problems': [...]}; the footnote marks stay on the
    words (superscripts) until write time."""
    verses: list[dict] = []
    by_sec: dict[str, dict] = {}
    marks: dict[tuple[str, int], str] = {}
    titles: dict[int, list[str]] = {}
    problems: list[str] = []
    pending_para = False
    pending_titles: list[str] = []
    title_marks: list[tuple[str, int]] = []  # a note on a title belongs to the book's first verse
    for p in index:
        stem = p["stem"]
        block = pages.get(stem)
        if block is None:
            problems.append(f"{stem}: not transcribed")
            continue
        for e in block["errors"]:
            problems.append(f"{stem}: {e}")
        for key, text in block["text"]:
            if key == "¶":
                pending_para = True
                continue
            if key == "[title]":
                pending_titles.append(text)
                title_marks += [(stem, k) for k in marks_in(text)]
                continue
            if key == "[chapter]":
                continue
            m = VKEY.match(key)
            if not m:
                problems.append(f"{stem}: bad key {key!r}")
                continue
            sec = f"{m.group(1)}.{m.group(2)}.{m.group(3)}"
            words = text.split()
            for k in marks_in(text):
                marks[(stem, k)] = sec
            for tm in title_marks:
                marks[tm] = sec
            title_marks = []
            if m.group(4):
                v = by_sec.get(sec)
                if v is None:
                    problems.append(f"{stem} {key}: continues a verse not seen before")
                    continue
                v["words"] += words
                continue
            if sec in by_sec:
                problems.append(f"{stem}: {sec} twice; the second left out")
                continue
            if pending_titles:
                titles[int(m.group(1))] = pending_titles
                pending_titles = []
            v = {"sec": sec, "words": words, "para": pending_para or m.group(3) == "1", "stem": stem}
            pending_para = False
            verses.append(v)
            by_sec[sec] = v
    return {"verses": verses, "marks": marks, "titles": titles, "problems": problems}


def correct_misprints(slug: str, text: dict, problems: list[str]) -> list[tuple[str, str]]:
    """The right reading where Lake misprints a word (MISPRINTS, TITLE_MISPRINTS), and for each an
    apparatus note on its verse (a title's on the book's first verse), marked as this edition's:
    [(verse, note)]."""
    notes = []
    by_sec = {v["sec"]: v for v in text["verses"]}

    def letters(w: str) -> str:
        return "".join(c for c in SUP_RE.sub("", w) if c.isalpha())

    for sec, fixes in MISPRINTS.get(slug, {}).items():
        v = by_sec.get(sec)
        for printed, right in fixes:
            hits = [i for i, w in enumerate(v["words"]) if letters(w) == printed] if v else []
            if len(hits) != 1:
                problems.append(f"misprint {sec}: “{printed}” found {len(hits)} times in the verse")
                continue
            k = hits[0]
            v["words"][k] = v["words"][k].replace(printed, right)
            notes.append((sec, f"{right}: Lake prints {printed}, a misprint; corrected in this edition."))
    for book, (printed, right) in TITLE_MISPRINTS.get(slug, {}).items():
        titles = text["titles"].get(book, [])
        if not any(printed in t for t in titles):
            problems.append(f"title misprint, book {book}: “{printed}” not in {titles}")
            continue
        text["titles"][book] = [t.replace(printed, right) for t in titles]
        first = next((v["sec"] for v in text["verses"] if v["sec"].startswith(f"{book}.")), None)
        notes.append((first, f"{right} (the title): Lake prints {printed}, without the breathing; corrected in this edition."))
    return notes


# --- the apparatus against First1K's ----------------------------------------------------------

def compare_first1k(placed: list[tuple[str, str]]) -> list[str]:
    """Our items against First1K's notes of the same verse: pairs whose letters differ, and items
    on either side with no counterpart. Comparison in Beta letters without accents
    (hermas_text.compare_form)."""
    theirs: dict[str, list[dict]] = {}
    for mk in first1k_marks():
        if mk["kind"] == "app":
            theirs.setdefault(mk["sec"], []).append(mk)
    ours: dict[str, list[str]] = {}
    for sec, item in placed:
        ours.setdefault(sec, []).append(item)
    out: list[str] = []
    for sec in sorted(set(ours) | set(theirs), key=sec_key):
        if sec_key(sec) > sec_key(LAST_GREEK):
            continue
        a = ours.get(sec, [])
        b = theirs.get(sec, [])
        used: set[int] = set()
        for item in a:
            fa = compare_form(item)
            best, score = None, 0.0
            for k, mk in enumerate(b):
                if k in used:
                    continue
                s = difflib.SequenceMatcher(None, fa, compare_form(mk["beta"], beta=True)).ratio()
                if s > score:
                    best, score = k, s
            if best is None or score < 0.5:
                out.append(f"{cite(sec)} ({sec}): ours only: {item}")
                continue
            used.add(best)
            if score < 0.97:
                out.append(f"{cite(sec)} ({sec}): differs ({score:.2f}): ours «{item}» | First1K «{b[best]['text']}» (Beta: {b[best]['beta']})")
        for k, mk in enumerate(b):
            if k not in used:
                out.append(f"{cite(sec)} ({sec}): First1K only: «{mk['text']}» (Beta: {mk['beta']})")
    return out


# --- tokens -----------------------------------------------------------------------------------

def _tokens(play, doc, sources: Path, out: Path, lexicon: Path, build: Path) -> int:
    from .lucian_merge import _tokens as lucian_tokens

    return lucian_tokens(play, doc, sources, out, lexicon, build)


def write_aliases(out: Path, sources: Path, build: Path, problems: list[str]) -> int:
    """aliases.tsv: (a) lemmas no dictionary has under the given spelling, found under another
    (nt.resolve_lemmas, as import-nt); (b) GLAUx's Attic headwords that Abbott-Smith lists in their
    Koine form (KOINE, and the regular changes: γιγν -> γιν, an active in -ω -> a middle in
    -ομαι). Lemmas no dictionary has under any spelling go to the log."""
    import collections
    import csv

    from .build import load_lexica
    from .nt import resolve_lemmas

    rows = list(csv.DictReader((out / "tokens.tsv").open(encoding="utf-8"), delimiter="\t"))
    counts = collections.Counter(r["lemma"] for r in rows if r["lemma"])
    lexica = load_lexica(sources, build)
    every = {e.headword for entries in lexica.values() for e in entries}
    abbott = {greek.lemma_key(e.headword): e.headword for e in lexica.get("abbott-smith", [])}
    aliases, missing = resolve_lemmas(sorted(counts), every)
    koine = 0
    for lemma in sorted(counts):
        key = greek.lemma_key(lemma)
        if key in abbott or lemma in aliases:
            continue
        cands = [KOINE.get(lemma, "")]
        cands += [lemma.replace("γιγν", "γιν")] if "γιγν" in lemma else []
        for end, repl in (("ω", "ομαι"), ("έω", "έομαι"), ("άω", "άομαι"), ("όω", "όομαι"), ("ημι", "αμαι")):
            if lemma.endswith(end):
                cands.append(lemma[: -len(end)] + repl)
        hit = next((abbott[greek.lemma_key(c)] for c in cands if c and greek.lemma_key(c) in abbott), None)
        if hit and hit != lemma:
            aliases[lemma] = hit
            koine += 1
    with (out / "aliases.tsv").open("w", encoding="utf-8") as f:
        f.write("# lemma\theadword under which a dictionary lists it (made by 'merge-hermas': Koine spellings for Abbott-Smith, other spellings for LSJ)\n")
        for lemma in sorted(aliases):
            f.write(f"{lemma}\t{aliases[lemma]}\n")
    no_abbott = [l for l in sorted(counts, key=lambda l: -counts[l])
                 if greek.lemma_key(l) not in abbott and greek.lemma_key(aliases.get(l, "")) not in abbott]
    problems.append(f"aliases: {len(aliases)} ({koine} to Abbott-Smith's Koine headwords); "
                    f"{len(missing)} lemmas in no dictionary under any spelling: {', '.join(missing[:80])}")
    problems.append(f"lemmas Abbott-Smith lacks ({len(no_abbott)}; LSJ has most), the commonest: "
                    + ", ".join(f"{l} {counts[l]}" for l in no_abbott[:60]))
    return len(aliases)


# --- merge ------------------------------------------------------------------------------------

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
    pages = read_batches(tdir, latin=False)
    text = assemble(pages, index)
    problems = list(text["problems"])
    verses = text["verses"]
    misprint_notes = correct_misprints(slug, text, problems)
    out = texts / slug
    out.mkdir(parents=True, exist_ok=True)

    # every verse once, in order, against Tauber
    want = sorted(tauber_sections(), key=sec_key)
    have = [v["sec"] for v in verses]
    if have != want:
        sm = difflib.SequenceMatcher(None, have, want, autojunk=False)
        for op, a0, a1, b0, b1 in sm.get_opcodes():
            if op != "equal":
                problems.append(f"verses: ours {have[a0:a1]} where Tauber has {want[b0:b1]}")
    # the words against Tauber (what the agents changed, for the log)
    tw = tauber_sections()
    changed = 0
    for v in verses:
        mine = [skel(w) for w in plain(" ".join(v["words"])).split() if skel(w)]
        theirs = [skel(w) for w in tw.get(v["sec"], []) if skel(w)]
        if mine != theirs:
            changed += 1
            problems.append(f"wording {v['sec']}: «{plain(' '.join(v['words']))}» | Tauber «{' '.join(tw.get(v['sec'], []))}»")

    heads = headings()
    meta = {
        "title": play.title, "author": play.author, "lang": "grc",
        "source": f"{play.edition}; read from the Internet Archive scan {play.scan} by OCR, matched word by word to "
                  "J. Tauber and S. Macdonald's Open Apostolic Fathers text of the same edition, and checked against "
                  "the scan where the two disagreed",
        "edition": play.edition,
        "license": TRANSCRIPTION_LICENSE,
        "layout": "prose",
        "syntax": "automatic",
        "dictionaries": "abbott-smith ml lsj",
        "pronunciation": play.pronunciation,
        "citation": "dotted",
    }
    doc = Document(meta=meta)
    book = chapter = None
    for v in verses:
        b, c, _vv = (int(x) for x in v["sec"].split("."))
        if b != book:
            book, chapter = b, None
            printed = [title_label(t) for t in text["titles"].get(b, []) if skel(t) != skel("ΠΟΙΜΗΝ")]
            label = printed[-1] if printed else heads.get(b, "")
            doc.items.append(Section(1, "book", f"{book_name(b)} · {label}" if label else book_name(b)))
        if c != chapter:
            chapter = c
            doc.items.append(Section(2, "chapter", f"{c} · {continuous_chapter(b, c)}"))
        if v["para"]:
            doc.items.append(Speaker(""))
        doc.items.append(Line(v["sec"], plain(" ".join(v["words"]))))
    write_file(out / "grc.txt", doc)
    print(f"wrote {out / 'grc.txt'}: {len(verses)} verses, {sum(1 for v in verses if v['para'])} paragraphs, "
          f"from {len(pages)} pages; {changed} verses worded otherwise than Tauber")

    # the apparatus: each item under the verse of its mark
    placed: list[tuple[str, str]] = []
    for p in index:
        block = pages.get(p["stem"])
        if block is None:
            continue
        for n, item in block["apparatus"]:
            sec = text["marks"].get((p["stem"], int(n))) if n.isdigit() else None
            if sec is None:
                problems.append(f"{p['stem']}: apparatus {n} has no mark in the page's text")
                continue
            placed.append((sec, item))
    placed += misprint_notes
    md = _meta_lines({
        "title": f"Critical apparatus ({play.app_editor_name})",
        "author": play.app_editor_name, "lang": "eng",
        "source": f"{play.edition}; transcribed from the Internet Archive scan {play.scan}",
        "license": TRANSCRIPTION_LICENSE,
    }) + [""]
    grouped: dict[str, list[str]] = {}
    for sec, item in sorted(placed, key=lambda x: sec_key(x[0])):
        grouped.setdefault(sec, []).append(item)
    for sec, items in grouped.items():
        md += [f"## {sec}", "\n\n".join(items), ""]
    (out / f"commentary-{play.app_editor}-apparatus.md").write_text("\n".join(md) + "\n", encoding="utf-8")
    print(f"wrote commentary-{play.app_editor}-apparatus.md: {len(grouped)} verses, {len(placed)} items")
    comparison = compare_first1k(placed)

    # lemmas, morphology, syntax
    review = _tokens(play, doc, sources, out, lexicon, build)
    print(f"review list: {review} words in {build / f'{slug}-review.tsv'}")
    n_alias = write_aliases(out, sources, build, problems)
    print(f"wrote aliases.tsv: {n_alias}")

    # Lake's translation by verse, to 26.30.2
    rows = lake_translation(sources / play.trans_file)
    have_n = {v["sec"] for v in verses}
    eng = []
    for n, t in rows:
        if sec_key(n) > sec_key(LAST_GREEK):
            continue
        if n not in have_n:
            problems.append(f"translation: verse {n} not in the Greek")
        eng.append(f"{n}\t{t}")
    tmeta = {"title": play.title_en, "translator": play.translator, "lang": "eng",
             "source": f"Perseus Digital Library, {Path(play.trans_file).stem}: {play.trans_edition}",
             "license": play.trans_license}
    (out / f"eng-{play.trans_key}.txt").write_text("\n".join(_meta_lines(tmeta) + [""] + eng) + "\n", encoding="utf-8")
    print(f"wrote eng-{play.trans_key}.txt: {len(eng)} verses")

    # Lake's notes: his footnotes and side-headings to the translation, the margin references
    margin: dict[str, list[str]] = {}
    for p in index:
        for sec, ref in pages.get(p["stem"], {}).get("margin", []):
            margin.setdefault(sec, []).append(ref)
    notes = lake_notes(sources / play.trans_file)
    by_sec: dict[str, list[str]] = {}
    for nt in notes:
        if sec_key(nt["sec"]) > sec_key(LAST_GREEK):
            continue
        if nt["kind"] == "marginal":
            by_sec.setdefault(nt["sec"], []).append(f"*{nt['text']}*")
    for sec, refs in margin.items():
        by_sec.setdefault(sec, []).append("Bible references in the margin: " + " ".join(refs))
    for nt in notes:
        if sec_key(nt["sec"]) <= sec_key(LAST_GREEK) and nt["kind"] != "marginal":
            lemma = f"**…{nt['after']}**: " if nt["after"] and nt["after"] != "(the heading)" else ""
            by_sec.setdefault(nt["sec"], []).append(lemma + nt["text"])
    md = _meta_lines({
        "title": "Commentary (Kirsopp Lake)", "author": "Kirsopp Lake", "lang": "eng",
        "source": f"{play.trans_edition}: his footnotes and the side-headings in the margin of his translation "
                  f"(Perseus Digital Library, {Path(play.trans_file).stem}), and the Bible references in the margin "
                  f"of his Greek text (transcribed from the scan {play.scan})",
        "license": "CC BY-SA 4.0 (Perseus Digital Library; the transcription of the margin)",
    }) + [""]
    for sec in sorted(by_sec, key=sec_key):
        if sec not in have_n:
            problems.append(f"lake notes: verse {sec} not in the Greek")
            continue
        md += [f"## {sec}", "\n\n".join(by_sec[sec]), ""]
    (out / "commentary-lake.md").write_text("\n".join(md) + "\n", encoding="utf-8")
    print(f"wrote commentary-lake.md: {len(by_sec)} verses")

    # the Latin end
    if (tdir / "batch-latin.md").exists() and (od / "latin-pages.json").exists():
        n_app = write_appendix(play, sources, tdir, od, out, problems)
        print(f"wrote appendix.md: {n_app} sections")

    # Taylor's notes, the introductions (steps 6-7)
    taylor_notes_and_introduction(play, tdir, out, have_n, problems)

    log = build / f"{slug}-merge.log"
    log.write_text("\n".join(problems + ["", f"# the apparatus against First1K's ({len(comparison)})"] + comparison) + "\n",
                   encoding="utf-8")
    print(f"{len(problems)} problems, {len(comparison)} apparatus differences from First1K ({log})")
    return len([p for p in problems if not p.startswith(("aliases:", "lemmas Abbott-Smith", "wording "))])


# --- the appendix: the Latin end ---------------------------------------------------------------

def write_appendix(play, sources: Path, tdir: Path, od: Path, out: Path, problems: list[str]) -> int:
    """appendix.md: from Sim. 9.30.3 to the end, section by section, Lake's Latin and Greek as he
    prints them, his English (Perseus), his apparatus items there and his notes to the English."""
    index = json.loads((od / "latin-pages.json").read_text(encoding="utf-8"))
    pages = read_batches(tdir, latin=True)
    text = assemble(pages, index)
    problems += [f"latin: {p}" for p in text["problems"]]
    eng = dict(lake_translation(sources / play.trans_file))
    items: dict[str, list[str]] = {}
    for p in index:
        block = pages.get(p["stem"])
        if block is None:
            continue
        for n, item in block["apparatus"]:
            sec = text["marks"].get((p["stem"], int(n))) if n.isdigit() else None
            if sec is None:
                problems.append(f"latin {p['stem']}: apparatus {n} has no mark in the page's text")
                continue
            items.setdefault(sec, []).append(item)
    lake = {}
    for nt in lake_notes(sources / play.trans_file):
        if sec_key(nt["sec"]) > sec_key(LAST_GREEK) and nt["kind"] != "marginal":
            lake.setdefault(nt["sec"], []).append(nt["text"])
    md = _meta_lines({
        "title": "The end of the Shepherd in the Latin version",
        "author": "Kirsopp Lake",
        "source": f"{play.edition}, pp. 290-304: the Latin version (L₁) with the Greek of the papyri, transcribed from "
                  f"the Internet Archive scan {play.scan}; Lake's translation from the Perseus Digital Library "
                  f"({Path(play.trans_file).stem})",
        "license": TRANSCRIPTION_LICENSE + "; the translation CC BY-SA 4.0 (Perseus Digital Library)",
    }) + [""]
    intro = INTRO_APPENDIX.strip()
    md += [intro, ""]
    book = chapter = None
    for v in text["verses"]:
        b, c, vv = (int(x) for x in v["sec"].split("."))
        if b != book:
            book = b
            printed = text["titles"].get(b)
            md += [f"# {book_name(b)}" + (f" · {title_label(printed[-1])}" if printed else ""), ""]
        if (b, c) != chapter:
            chapter = (b, c)
            md += [f"## Chapter {c} ({continuous_chapter(b, c)})", ""]
        md += [f"**{cite(v['sec'])}** {plain(' '.join(v['words']))}", ""]
        if v["sec"] in eng:
            md += [f"*{eng[v['sec']]}*", ""]
        for it in items.get(v["sec"], []):
            md += [f"Apparatus: {it}", ""]
        for nt in lake.get(v["sec"], []):
            md += [f"Lake's note: {nt}", ""]
    (out / "appendix.md").write_text("\n".join(md).rstrip() + "\n", encoding="utf-8")
    return len(text["verses"])


INTRO_APPENDIX = """
Manuscript A, the only Greek manuscript that runs so far, breaks off after Similitude 9.30.2: its
last leaf is lost. From there to the end Lake prints the Latin version (the Vulgate, L₁), and the
Greek where the papyri preserve it (Similitude 9.30.3-4 and 9.31.5-6 from the Amherst papyrus;
10.3.2-5 from Oxyrhynchus papyrus 404). Lake's note at 9.30.3: “At this point A ends, as the last
leaf is missing. The Latin text which follows is that of L₁. The few verses in Greek are from Pᵃᵐ.”
The text below follows his pages section by section, each with his translation beneath it; it is
not annotated word by word.
"""


# --- Taylor ---------------------------------------------------------------------------------------

_TAYLOR_HEAD = re.compile(r"^##\s+(Vision|Mandate|Similitude)\s+(\d+)\.(\d+)(?:\.(\d+))?(?:\s*[-–]\s*(\d+))?\s*$")


def taylor_ref(heading: str) -> str | None:
    """'## Mandate 4.1.2' -> '9.1.2'; '## Mandate 1.3' (a book of one chapter) -> '6.1.3'."""
    m = _TAYLOR_HEAD.match(heading)
    if not m:
        return None
    kind, k, a, bb = m.group(1), int(m.group(2)), int(m.group(3)), m.group(4)
    book = BOOK_NAMES.index(f"{kind} {k}") + 1 if f"{kind} {k}" in BOOK_NAMES else None
    if book is None:
        return None
    return f"{book}.{a}.{bb}" if bb is not None else f"{book}.1.{a}"


def taylor_notes_and_introduction(play, tdir: Path, out: Path, have_n: set[str], problems: list[str]) -> None:
    from .drama_prose import merge_kind

    def checked(kind: str) -> bool:
        files = sorted(tdir.glob(f"{kind}-*.md"))
        return bool(files) and not any(re.search(r"(?m)^\d+ .*→\s*$", f.read_text(encoding="utf-8")) for f in files)

    paras = merge_kind(tdir, "notes") if checked("notes") else []
    if paras:
        placed: list[tuple[str, list[str]]] = []
        latin_notes: list[tuple[str, list[str]]] = []
        cur: list[str] | None = None
        for p in paras:
            if p.startswith("##"):
                ref = taylor_ref(p)
                if ref is None:
                    problems.append(f"taylor: heading “{p}” not understood")
                    cur = None
                    continue
                target = latin_notes if sec_key(ref) > sec_key(LAST_GREEK) else placed
                if ref not in have_n and target is placed:
                    problems.append(f"taylor: note on {p[3:]} ({ref}): no such verse")
                if target and target[-1][0] == ref:
                    cur = target[-1][1]
                else:
                    target.append((ref, []))
                    cur = target[-1][1]
            elif p.startswith("# "):
                continue
            elif cur is None:
                problems.append(f"taylor: a paragraph before the first note: {p[:60]}")
            else:
                cur.append(p)
        md = _meta_lines({
            "title": f"Commentary ({play.notes_editor_name})", "author": play.notes_editor_name, "lang": "eng",
            "source": f"{play.notes_edition}: the notes to his translation; transcribed from the Internet Archive "
                      f"scans {', '.join(s for s, _r in play.notes_sources.get('notes', [])) or play.notes_scan}",
            "license": TRANSCRIPTION_LICENSE,
        }) + [""]
        for ref, body in sorted(placed, key=lambda x: sec_key(x[0])):
            md += [f"## {ref}", "\n\n".join(body), ""]
        (out / f"commentary-{play.notes_editor}.md").write_text("\n".join(md) + "\n", encoding="utf-8")
        print(f"wrote commentary-{play.notes_editor}.md: {sum(len(b) for _r, b in placed)} paragraphs under {len(placed)} verses; "
              f"{len(latin_notes)} on the Latin end (in the appendix)")
        if latin_notes and (out / "appendix.md").exists():
            app = (out / "appendix.md").read_text(encoding="utf-8").rstrip()
            app += "\n\n# Taylor's notes on the Latin end\n\n" + "\n\n".join(
                f"**{cite(ref)}** " + "\n\n".join(body) for ref, body in latin_notes) + "\n"
            (out / "appendix.md").write_text(app, encoding="utf-8")
    paras = merge_kind(tdir, "intro") if checked("intro") else []
    if paras:
        md = _meta_lines({
            "title": "Introduction", "author": f"Kirsopp Lake; {play.notes_editor_name}",
            "source": f"{play.edition}, the introduction to the Shepherd (pp. 2-5); {play.notes_edition}, the introduction "
                      "(vol. I) and the appendix on Hermas and the Gospels (vol. II); transcribed from the Internet Archive scans",
            "license": TRANSCRIPTION_LICENSE,
        }) + [""] + ["\n\n".join(paras)]
        (out / "introduction.md").write_text("\n".join(md).rstrip() + "\n", encoding="utf-8")
        print(f"wrote introduction.md: {sum(1 for p in paras if p.startswith('#'))} headings")


def main(slug: str = "hermas") -> int:
    return merge(slug, PIPELINE / "sources", ROOT / "texts", PIPELINE / "build", ROOT / "data" / "lexicon.sqlite")
