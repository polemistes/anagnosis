"""The commentaries and introductions on Lysias (pipeline/PLAN-lysias.md, step 9): the checked
prose batches of the three school editions, filed under Hude's sections.

One commentary to a speech (drama.LYSIAS_NOTES): Adams (12, 16, 19, 22, 24, 25, 32, 34) and
Morgan (7, 23, 31) print their notes under their text by section number; Shuckburgh (5, 9, 10,
13, 14, 17, 28, 30) prints his at the back by the line numbers of his own text. Each speech is an
entry of the prose route (drama-prose lysias-12 notes|intro …), its batches in
pipeline/transcriptions/drama/lysias-NN/. From the checked batches this module makes

* commentary-adams.md, commentary-morgan.md, commentary-shuckburgh.md: every note under a
  heading `## 12.7` (speech.section of Hude's text), its lemma in bold;
* introduction.md: Adams's general introduction, then a chapter for each speech that has one
  (`# 12. Against Eratosthenes`, with its commentator named), in the order of the speeches;
* appendix.md: Adams's Appendix I-V (his notes cite its paragraphs: "App. § 57. 3").

Where a note goes. The commentator's number names a section (Adams, Morgan) or a line of his own
text (Shuckburgh: `shuckburgh_lines` reads his text pages, matches them to the check text and so
knows the section of each of his lines). His section is not always Hude's: Hude marks the line
where a section begins, the school editions follow the vulgate division, and the two differ by a
few words at many section starts. So the note's lemma is looked for in Hude's text: in the
section named, then in the sections beside it; the note is filed where the lemma stands. A lemma
that is not in Hude's text at all (the commentator reads otherwise than Hude, or the lemma is
abbreviated) stays under the section the commentator names, the lemma as he prints it, and is
listed in the log (`<slug>-notes.log`) for a reader to look at: the note as a rule discusses that
very reading.
"""
from __future__ import annotations

import re
from collections import Counter
from pathlib import Path

from .drama import LYSIAS_EDITORS, LYSIAS_NOTES, LYSIAS_PROSE, PLAYS, TRANSCRIPTION_LICENSE, _meta_lines, skel

ROOT = Path(__file__).resolve().parent.parent.parent
PIPELINE = ROOT / "pipeline"
DRAMA = PIPELINE / "transcriptions" / "drama"
REACH = 2  # how many sections either side of the one named a lemma is looked for
# Where Hude numbers the sections otherwise than the check text (he prints 13.65-66 of the vulgate
# after 13.67-68 and numbers the four in his own order): the check text's section -> Hude's
CHECK_TO_HUDE = {13: {65: 67, 66: 68, 67: 65, 68: 66}}


def entry(speech: int) -> str:
    return f"lysias-{speech:02d}"


# --- reading the batches ----------------------------------------------------------------------

def unanswered(directory: Path, kind: str) -> list[str]:
    """The flags of a kind's batches that have no answer yet (the merge takes checked batches only)."""
    from .drama_prose import read_prose_batches

    out = []
    for stem, block in read_prose_batches(directory, kind).items():
        for raw in block["flags"]:
            m = re.match(r"^\d+ .*→\s*(.*)$", raw)
            if raw.strip() and (not m or not m.group(1).strip()):
                out.append(f"{block['batch']} {stem}")
                break
    return out


def paragraphs(speech_or_slug: int | str, kind: str, drafts: bool = False) -> list[str] | None:
    """The paragraphs of an entry's checked batches in page order (drama_prose.merge_kind); None
    if it has no batches, or flags not yet answered (unless `drafts`: a trial merge)."""
    from .drama_prose import merge_kind

    slug = entry(speech_or_slug) if isinstance(speech_or_slug, int) else speech_or_slug
    d = DRAMA / slug
    if not any(d.glob(f"{kind}-*.md")):
        return None
    if not drafts and unanswered(d, kind):
        return None
    return merge_kind(d, kind)


def split_notes(paras: list[str]) -> tuple[list[str], list[tuple[str, list[str]]]]:
    """(the paragraphs before the first note: Shuckburgh's introduction to the speech under
    `# Introduction`; the notes as (number or range as headed, paragraphs))."""
    intro: list[str] = []
    notes: list[tuple[str, list[str]]] = []
    for p in paras:
        m = re.match(r"^## (\d+)(?:-(\d+))?$", p)
        if m:
            notes.append((p[3:], []))
        elif p.startswith("#"):
            continue  # "# Introduction"
        elif notes:
            notes[-1][1].append(p)
        else:
            intro.append(p)
    return intro, notes


# --- the lemma in Hude's text --------------------------------------------------------------------

_BOLD = re.compile(r"^\*\*(.+?)\*\*")
_OMISSION = re.compile(r"\s*(?:\.(?:\s?\.)+|…|κτλ\.?|κ\.τ\.λ\.?)\s*")  # Shuckburgh prints two dots


def lemma_parts(paragraph: str) -> list[list[str]]:
    """The skeletons of a note's lemma, in the runs its dots of omission divide it into:
    "**κινδυνεύειν ἐδόκει, ὡς . . . ὑπάρχοντος**: …" gives [[κινδυνευειν, εδοκει, ως],
    [υπαρχοντος]]; [] for a paragraph without a bold lemma in Greek."""
    m = _BOLD.match(paragraph)
    if not m or not re.search(r"[Ͱ-Ͽἀ-῿]", m.group(1)):
        return []
    runs = []
    for piece in _OMISSION.split(m.group(1)):
        ws = [skel(w) for w in piece.split()]
        ws = [w for w in ws if w]
        if ws:
            runs.append(ws)
    return runs


def _has_run(words: list[str], run: list[str], start: int = 0) -> int | None:
    """Where `run` stands in `words` from `start` on (a final sigma and an elided ending count as
    the word: τοῦτʼ for τοῦτο is looked for by its letters)."""
    n = len(run)
    for i in range(start, len(words) - n + 1):
        if all(words[i + k] == run[k] or (len(run[k]) >= 3 and (words[i + k].startswith(run[k]) or run[k].startswith(words[i + k]))
                                          and abs(len(words[i + k]) - len(run[k])) <= 1) for k in range(n)):
            return i
    return None


def find_lemma(runs: list[list[str]], words: list[str]) -> bool:
    """Whether the lemma's runs stand in the section's words, in order."""
    at = 0
    for run in runs:
        i = _has_run(words, run, at)
        if i is None:
            return False
        at = i + len(run)
    return True


def hude_sections(grc: Path) -> dict[str, list[str]]:
    """Each section's words as skeletons, from grc.txt (the parts 12.7b, 12.7c joined)."""
    out: dict[str, list[str]] = {}
    for raw in grc.read_text(encoding="utf-8").splitlines():
        m = re.match(r"^(\d+\.\d+)[a-z]?\t(.*)$", raw)
        if m:
            out.setdefault(m.group(1), []).extend(w for w in (skel(x) for x in m.group(2).split()) if w)
    return out


def place(speech: int, named: list[int], paragraph: str, sections: dict[str, list[str]]) -> tuple[str, str]:
    """(the section of Hude's text a note's paragraph belongs to, how it was found: 'lemma',
    'near' (the lemma stands in a section beside the one named), 'none' (no Greek lemma), 'miss'
    (the lemma is not in Hude's text near there)). `named`: the sections the commentator's number
    names, the likeliest first."""
    last = max((int(k.split(".")[1]) for k in sections if k.startswith(f"{speech}.")), default=0)
    first = min((int(k.split(".")[1]) for k in sections if k.startswith(f"{speech}.")), default=1)
    named = [min(max(n, first), last) for n in named] or [first]
    home = f"{speech}.{named[0]}"
    runs = lemma_parts(paragraph)
    if not runs:
        return home, "none"
    for n in named:
        if find_lemma(runs, sections.get(f"{speech}.{n}", [])):
            return f"{speech}.{n}", "lemma"
    for d in range(1, REACH + 1):
        for n in (named[0] - d, named[0] + d):
            if find_lemma(runs, sections.get(f"{speech}.{n}", [])):
                return f"{speech}.{n}", "near"
    # a lemma that runs over a section's end: its first run in one section, the rest in the next
    for n in named:
        if find_lemma(runs[:1], sections.get(f"{speech}.{n}", []) + sections.get(f"{speech}.{n + 1}", [])):
            return f"{speech}.{n}", "lemma"
    return home, "miss"


# --- Shuckburgh's own lines -----------------------------------------------------------------------

def shuckburgh_lines(speech: int, sources: Path) -> dict[int, list[int]]:
    """Shuckburgh's line numbers for a speech, each with the sections (of the check text) of the
    words on it: his text pages are read by Tesseract and matched word by word to the check text
    of the speech; a line counts as a line of the speech if half its words are matched (his
    English summaries in italics, the running head and the lines of a neighbouring speech are
    not); the lines are counted from 1, and the numbers he prints every fifth line in the margin
    put the count right where Tesseract lost or doubled a line."""
    from PIL import Image

    from .drama_pages import DASHES, ocr_leaf, ocr_norm, read_lines, scan_dirs
    from .gorgias_pages import align
    from .hude_pages import check_file
    from .lucian_pages import perseus_prose

    play = PLAYS[entry(speech)]
    scan = play.notes_scan
    _, sbuild = scan_dirs(scan)
    plines: list[dict] = []
    ocr: list[dict] = []
    for a, b in play.notes_text_leaves:
        for leaf in range(a, b + 1):
            with Image.open(sbuild / "pages" / f"leaf_{leaf:04d}.png") as im:
                W, H = im.size
            for l in read_lines(ocr_leaf(scan, leaf)):
                if l["bbox"][3] < 0.075 * H or l["bbox"][3] - l["bbox"][1] < 0.012 * H:
                    continue  # the running head; the accents Tesseract reads as a line of their own
                ws = sorted(l["words"], key=lambda w: w["bbox"][0])
                nums = []
                for w in (ws[:1] + ws[-1:]) if len(ws) > 1 else ws:
                    t = w["text"].strip("._,:;")
                    if re.fullmatch(r"\d{1,3}", t) and (w["bbox"][2] < 0.3 * W or w["bbox"][0] > 0.7 * W):
                        nums.append(int(t))
                ws = [w for w in ws if not re.fullmatch(r"\d{1,3}", w["text"].strip("._,:;"))]
                li = len(plines)
                plines.append({"leaf": leaf, "nums": nums})
                for w in ws:
                    for piece in DASHES.split(ocr_norm(w["text"])):
                        if skel(piece):
                            ocr.append({"t": piece, "skel": skel(piece), "line": li, "conf": w["conf"]})
    toks, _notes = perseus_prose(check_file(PLAYS["lysias"], sources, speech), book=str(speech), quotes=True, headings=True)
    match = align(ocr, toks)
    by_line: dict[int, list[int]] = {}
    for j, o in enumerate(match):
        if o is not None:
            by_line.setdefault(ocr[o]["line"], []).append(j)
    count = Counter(t["line"] for t in ocr)
    out: dict[int, list[int]] = {}
    n = 0
    for li, pl in enumerate(plines):
        hits = by_line.get(li, [])
        if not count[li] or len(hits) < count[li] / 2 or sum(1 for j in hits if len(toks[j]["skel"]) >= 3) < 2:
            # a divided word's second half alone on a line still counts when the lines beside it do
            if not (hits and count[li] <= 2 and li - 1 in by_line and li + 1 in by_line):
                continue
        n += 1
        for m in pl["nums"]:
            if m % 5 == 0 and m != n and abs(m - n) <= 6:
                n = m
        renumber = CHECK_TO_HUDE.get(speech, {})
        out[n] = [renumber.get(x, x) for x in (int(toks[j]["sec"].split(".")[1]) for j in sorted(hits))]
    return out


def line_sections(lines: dict[int, list[int]], a: int, b: int | None = None) -> list[int]:
    """The sections that lines a-b of Shuckburgh's text hold, the commonest first; if the lines
    are not known, those of the nearest line before."""
    secs: list[int] = []
    for n in range(a, (b or a) + 1):
        secs += lines.get(n, [])
    if not secs:
        k = max((x for x in lines if x <= a), default=None)
        secs = lines.get(k, []) if k is not None else []
    return [s for s, _c in Counter(secs).most_common()]


# --- writing ------------------------------------------------------------------------------------

def speech_notes(speech: int, sections: dict[str, list[str]], sources: Path, drafts: bool = False) -> tuple[list[tuple[str, str]], list[str], list[str]] | None:
    """A speech's notes placed: ([(section, paragraph)] in the commentator's order, the
    paragraphs of his introduction that stand at the head of the notes (Shuckburgh), log lines);
    None while the batches are not checked."""
    paras = paragraphs(speech, "notes", drafts)
    if paras is None:
        return None
    editor = LYSIAS_NOTES[speech][0]
    intro, notes = split_notes(paras)
    by_line = LYSIAS_EDITORS[editor][2] == "back"
    lines = shuckburgh_lines(speech, sources) if by_line else {}
    placed: list[tuple[str, str]] = []
    log: list[str] = []
    for head, ps in notes:
        m = re.match(r"^(\d+)(?:-(\d+))?$", head)
        a, b = int(m.group(1)), int(m.group(2)) if m.group(2) else None
        named = line_sections(lines, a, b) if by_line else [a]
        if by_line and not named:
            log.append(f"{speech}: note on line {head}: the line is not in the line map; filed under the speech's first section")
        prev = None
        for p in ps:
            sec, how = place(speech, named, p, sections)
            if how == "none" and prev is not None:
                sec = prev  # a further paragraph of the note before
            elif how == "near":
                log.append(f"NEAR {speech} note {head}: the lemma stands in {sec}, not in "
                           f"{speech}.{named[0] if named else '?'}: {p[:70]}")
            elif how == "miss":
                log.append(f"MISS {speech} note {head}: the lemma is not in Hude's text at {sec} (another reading, or abbreviated): {p[:70]}")
            placed.append((sec, p))
            prev = sec
    return placed, intro, log


def write(texts: Path, slug: str, sources: Path, build: Path, drafts: bool = False) -> list[str]:
    """commentary-<editor>.md for the three commentators, introduction.md and appendix.md, from
    the checked batches (with `drafts`, from the batches as they are: a trial). Returns the log."""
    out = texts / slug
    sections = hude_sections(out / "grc.txt")
    order = sorted(sections, key=lambda k: [int(x) for x in k.split(".")])
    log: list[str] = []
    by_editor: dict[str, dict[str, list[str]]] = {}
    speech_intros: dict[int, list[str]] = {}
    for speech in sorted(LYSIAS_NOTES):
        editor = LYSIAS_NOTES[speech][0]
        res = speech_notes(speech, sections, sources, drafts)
        if res is None:
            log.append(f"speech {speech} ({editor}): notes not merged: no batches, or flags not answered")
        else:
            placed, intro, lg = res
            log += lg
            for sec, p in placed:
                by_editor.setdefault(editor, {}).setdefault(sec, []).append(p)
            if intro:
                speech_intros[speech] = intro
        own = paragraphs(speech, "intro", drafts)
        if own:
            speech_intros[speech] = own + speech_intros.get(speech, [])
    for editor, by_sec in by_editor.items():
        scan, name, _layout, edition = LYSIAS_EDITORS[editor]
        md = _meta_lines({"title": f"Commentary ({name})", "author": name, "lang": "eng",
                          "source": f"{edition}, the notes; transcribed from the Internet Archive scan {scan}",
                          "license": TRANSCRIPTION_LICENSE}) + [""]
        for sec in order:
            if sec in by_sec:
                md += [f"## {sec}", "\n\n".join(by_sec[sec]), ""]
        (out / f"commentary-{editor}.md").write_text("\n".join(md) + "\n", encoding="utf-8")
        print(f"wrote commentary-{editor}.md: {sum(len(v) for v in by_sec.values())} paragraphs under {len(by_sec)} sections")
    # the introduction: Adams's general one, then the speeches'
    general = paragraphs("lysias-intro", "intro", drafts)
    if general or speech_intros:
        from .hude_merge import SPEECH_NAMES

        md = _meta_lines({"title": "Introduction", "author": "Charles Darwin Adams; Morris H. Morgan; Evelyn S. Shuckburgh",
                          "source": "; ".join(f"{LYSIAS_EDITORS[e][3]} (scan {LYSIAS_EDITORS[e][0]})" for e in LYSIAS_EDITORS)
                                    + ": Adams's general introduction and each editor's introduction to his speeches",
                          "license": TRANSCRIPTION_LICENSE}) + [""]
        for p in general or []:
            md += [p, ""]
        for speech in sorted(speech_intros):
            name = LYSIAS_EDITORS[LYSIAS_NOTES[speech][0]][1]
            md += [f"# {speech}. {SPEECH_NAMES[speech][1]} ({name})", ""]
            for p in speech_intros[speech]:
                # the speech's own title at the head of its introduction is the chapter's; its parts one level down
                if re.match(r"^# ", p):
                    if re.fullmatch(r"# (?:Introduction|[IVXL]+)\.?", p) or len(skel(p)) == 0 and False:
                        continue
                    p = "#" + p
                md += [p, ""]
        (out / "introduction.md").write_text("\n".join(md).rstrip() + "\n", encoding="utf-8")
        print(f"wrote introduction.md: the general introduction {'present' if general else 'MISSING'}, {len(speech_intros)} speeches")
    appendix = paragraphs("lysias-appendix", "intro", drafts)
    if appendix:
        scan, name, _layout, edition = LYSIAS_EDITORS[LYSIAS_PROSE["lysias-appendix"][0]]
        md = _meta_lines({"title": "Appendix", "author": name,
                          "source": f"{edition}, Appendix I-V; transcribed from the Internet Archive scan {scan}",
                          "license": TRANSCRIPTION_LICENSE}) + [""]
        for p in appendix:
            md += [p, ""]
        (out / "appendix.md").write_text("\n".join(md).rstrip() + "\n", encoding="utf-8")
        print(f"wrote appendix.md: {len(appendix)} paragraphs")
    (build / f"{slug}-notes.log").write_text("\n".join(log) + "\n", encoding="utf-8")
    near = sum(1 for x in log if x.startswith("NEAR"))
    miss = sum(1 for x in log if x.startswith("MISS"))
    print(f"notes: {near} filed under a neighbouring section by their lemma, {miss} lemmas not in Hude's text (log {build / f'{slug}-notes.log'})")
    return log
