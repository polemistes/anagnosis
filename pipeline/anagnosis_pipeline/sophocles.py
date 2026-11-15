"""Sophocles' plays in Jebb's edition, one text each (texts/<slug>/), as Antigone was made.

For every play: Jebb's Greek text (Perseus P4, soph.<code>_gk.xml), numbered with the line
numbers a treebank cites; Jebb's translation (Perseus, modernized); lemmas, morphology and
syntax from the Ancient Greek Dependency Treebank where it has the play, else from GLAUx
(automatic); Jebb's commentary and introduction from Perseus where it has them. Words the
treebank does not cover get the word analyser's analysis. The critical notes are transcribed
from the scans (pipeline/transcriptions/sophocles/<slug>/) and merged by merge-apparatus.
"""
from __future__ import annotations

import re
import sys
from dataclasses import dataclass, field
from pathlib import Path

from . import greek


@dataclass
class Play:
    slug: str
    code: str              # Perseus file code: soph.<code>_gk.xml
    tlg: str               # tlg0011.<tlg>
    title: str             # Greek title
    title_en: str
    part: str              # Jebb's part number
    edition: str           # the edition Perseus's text and our apparatus follow
    treebank: str = ""     # AGDT file in sources/treebanks/
    glaux: str = ""        # GLAUx file in sources/glaux/ when there is no AGDT
    eng: str = "perseus-eng2"
    commentary: bool = True
    parts: list[tuple[int, str]] = field(default_factory=list)  # Jebb's divisions: (first line, name)


PLAYS = {p.slug: p for p in [
    Play("ajax", "aj", "tlg003", "Αἴας", "Ajax", "VII", "1896",
         treebank="tlg0011.tlg003.perseus-grc1.tb.xml",
         parts=[(1, "Prologue"), (134, "Parodos"), (201, "First episode"), (596, "First stasimon"),
                (646, "Second episode"), (693, "Second stasimon"), (719, "Third episode"),
                (866, "Epiparodos"), (879, "Kommos"), (974, "Fourth episode"), (1185, "Third stasimon"),
                (1223, "Exodos")]),
    Play("electra", "el", "tlg005", "Ἠλέκτρα", "Electra", "VI", "1894",
         treebank="tlg0011.tlg005.perseus-grc2.tb.xml",
         parts=[(1, "Prologue"), (121, "Parodos"), (251, "First episode"), (472, "First stasimon"),
                (516, "Second episode"), (1058, "Second stasimon"), (1098, "Third episode"),
                (1384, "Third stasimon"), (1398, "Exodos")]),
    Play("oedipustyrannus", "ot", "tlg004", "Οἰδίπους Τύραννος", "Oedipus Tyrannus", "I", "1893",
         treebank="tlg0011.tlg004.perseus-grc1.tb.xml",
         parts=[(1, "Prologue"), (151, "Parodos"), (216, "First episode"), (463, "First stasimon"),
                (513, "Second episode"), (863, "Second stasimon"), (911, "Third episode"),
                (1086, "Third stasimon"), (1110, "Fourth episode"), (1186, "Fourth stasimon"),
                (1223, "Exodos")]),
    Play("oedipuscoloneus", "oc", "tlg007", "Οἰδίπους ἐπὶ Κολωνῷ", "Oedipus at Colonus", "II", "1889",
         glaux="0011-007.xml",
         parts=[(1, "Prologue"), (117, "Parodos"), (254, "First episode"), (668, "First stasimon"),
                (720, "Second episode"), (1044, "Second stasimon"), (1096, "Third episode"),
                (1211, "Third stasimon"), (1249, "Fourth episode"), (1556, "Fourth stasimon"),
                (1579, "Exodos")]),
    Play("philoctetes", "phil", "tlg006", "Φιλοκτήτης", "Philoctetes", "IV", "1898",
         glaux="0011-006.xml", commentary=False,
         parts=[(1, "Prologue"), (135, "Parodos"), (219, "First episode"), (676, "Stasimon"),
                (730, "Second episode"), (865, "Third episode"), (1081, "Kommos"), (1218, "Exodos")]),
    Play("trachiniae", "trach", "tlg001", "Τραχίνιαι", "Trachiniae", "V", "1892",
         treebank="tlg0011.tlg001.perseus-grc2.tb.xml", eng="perseus-eng3",
         parts=[(1, "Prologue"), (94, "Parodos"), (141, "First episode"), (497, "First stasimon"),
                (531, "Second episode"), (633, "Second stasimon"), (663, "Third episode"),
                (821, "Third stasimon"), (863, "Fourth episode"), (947, "Fourth stasimon"),
                (971, "Exodos")]),
]}

PART_ROMAN = {"I": "Part I", "II": "Part II", "III": "Part III", "IV": "Part IV", "V": "Part V", "VI": "Part VI", "VII": "Part VII"}


def sources_for(play: Play) -> dict[str, str]:
    """Local file names in pipeline/sources/ (made by fetch)."""
    return {
        "greek": f"{play.slug}.perseus-gk.xml",
        "eng": f"{play.slug}.{play.eng}.xml",
        "commentary": f"jebb-{play.slug}-commentary.xml",
    }


# Jebb's readings that neither the treebank nor the analyser knows: form -> (lemma, postag)
FORM_FIXES = {
    "ἀνστάσεις": ("ἀνίστημι", "v2sfia---"),  # El. 138, apocope for ἀναστήσεις
    "διαίτᾳ": ("δίαιτα", "n-s---fd-"),  # El. 1073, where the treebank has διά+δίαιτα, a preposition
}
WRONG_LEMMAS = {"διά+δίαιτα"}


def read_agdt(path: Path, book_cites: bool = False) -> list[dict]:
    """An AGDT treebank: every word (artificial nodes and punctuation included, is_word False),
    with the line it cites (the last citation carried forward). A citation "15.2" is part 2 of
    line 15 (Sophocles); with `book_cites` it is line 2 of book 15 (Hesiod's "1.120": line 120)."""
    from lxml import etree

    out = []
    for sent in etree.parse(str(path)).iter("sentence"):
        current = None
        for w in sent.iter("word"):
            artificial = bool(w.get("artificial") or w.get("insertion_id"))
            cite = w.get("cite", "")
            if cite:
                current = cite.rsplit(":", 1)[-1]
                m = re.match(r"^(\d+)\.(\d+)$", current)
                if m:
                    current = m.group(2) if book_cites else m.group(1) + "abcdefgh"[int(m.group(2))]
            form = greek.nfc(w.get("form", ""))
            out.append({
                "sentence": sent.get("id"), "word_id": w.get("id"), "form": form,
                "lemma": greek.nfc(w.get("lemma", "")), "postag": w.get("postag", ""),
                "head": w.get("head", ""), "relation": w.get("relation", ""),
                "line": None if artificial else current, "cite": current or "",
                "artificial": artificial, "is_word": not artificial and greek.is_word(form),
            })
    return out


def read_glaux_lines(path: Path) -> list[dict]:
    """GLAUx in the same shape, with the line each word stands in."""
    from lxml import etree

    from .symposium_merge import read_glaux

    rows = read_glaux(path)
    lines = []
    for sent in etree.parse(str(path)).iter("sentence"):
        for w in sent.iter("word"):
            lines.append(w.get("line") or None)
    for r, line in zip(rows, lines):
        r["line"] = None if r["artificial"] else line
        r["cite"] = line or ""
        # crasis: GLAUx gives the first word its own node (κα- = καί, το- = τό) before the
        # whole form (κἀξίδρυσον); that node belongs to the tree, not to the words of the text
        if len(r["form"]) > 1 and r["form"].endswith("-"):
            r["form"] = r["lemma"] or r["form"].rstrip("-")
            r["is_word"] = False
            r["line"] = None
    return rows


def renumber_verses(doc, tb: list[dict], parts: set[int], explicit: dict[int, str]) -> list[str]:
    """Jebb's line numbers from the treebank's citations, between fixed points (`explicit`: line
    index -> number), a verse shared between speakers counted once: its parts (`parts`, the
    indices of the later parts) are joined for the numbering, then each later part takes the
    verse's number with a letter (591, 591a, 591b), as the text format writes lines that share
    a number."""
    from .import_perseus import renumber_from_treebank
    from .textfmt import Document, Line

    lines = doc.lines
    groups: list[list[int]] = []
    for i in range(len(lines)):
        if i in parts and groups:
            groups[-1].append(i)
        else:
            groups.append([i])
    merged = Document(meta={})
    explicit_groups = []
    for g, members in enumerate(groups):
        stated = [explicit[i] for i in members if i in explicit]
        merged.items.append(Line(stated[-1] if stated else lines[members[0]].n, " ".join(lines[i].text for i in members)))
        if stated:
            explicit_groups.append(g)
    merged.meta["_explicit"] = ",".join(map(str, explicit_groups))
    warnings = renumber_from_treebank(merged, tb)
    for members, verse in zip(groups, merged.lines):
        for i in members:
            lines[i].n = re.match(r"^\d+", verse.n).group()
    # the lines that share a number (the parts of a shared verse, the short lines Jebb counts as
    # one) lettered in the order they stand: 591, 591a, 591b
    seen: dict[str, int] = {}
    for line in lines:
        k = seen.get(line.n, 0)
        seen[line.n] = k + 1
        if k:
            line.n += "abcdefghijklmnop"[k - 1]
    return warnings


def _skel(s: str) -> str:
    return re.sub(r"[^α-ω]", "", greek.strip_diacritics(s).replace("ς", "σ"))


def _printed(text: str) -> str:
    """Jebb's printed words in the text's conventions: ʼ for the elision, ⟨ ⟩ for his additions,
    and without the asterisk that marks his own emendations (his notes say so)."""
    text = text.replace("\u2019", "\u02bc").replace("<", "\u27e8").replace(">", "\u27e9")
    return re.sub(r"\*(?=[\u0370-\u03ff\u1f00-\u1fff])", "", text)


def apply_text_check(doc, anchors: list[tuple[str, str]], diffs: list, parts: set[int],
                     reference: dict[str, str] | None = None,
                     lyrics: list | None = None) -> tuple[dict[int, str], set[int], list[str]]:
    """Jebb's printed text: the differences the transcribers found applied, and the printed line
    numbers placed on our lines as fixed points.

    A difference is keyed by the line number of the text the transcribers compared
    (`reference`, number -> text: the play's reference-grc.txt), which may number a line
    otherwise than this import does, and a transcriber may have used the printed number; so it
    goes to the line near that number which holds the quoted words, the one whose words are the
    reference line's first; an inserted line follows the line whose words are the reference
    line's. `lyrics`, the second pass over the lyric verses, are keyed by the numbers of the
    text as imported with the first and applied after it, by their words alone; there ` | ` in
    the printed words begins a new verse. Returns (fixed points by line index, the later parts
    of shared verses by index, warnings)."""
    from .textfmt import Line

    warnings = []
    reference = reference or {}
    cont = {id(l) for i, l in enumerate(doc.lines) if i in parts}

    def num(n: str) -> int:
        m = re.match(r"\d+", n)
        return int(m.group()) if m else -1

    def locate(n: str, ours: str | None) -> int | None:
        lines = doc.lines
        guess = next((i for i, l in enumerate(lines) if l.n == n), None)
        if guess is None:
            near = [i for i, l in enumerate(lines) if num(l.n) >= 0]
            if not near:
                return None
            guess = min(near, key=lambda i: abs(num(lines[i].n) - num(n)))
        window = sorted(range(max(0, guess - 8), min(len(lines), guess + 9)), key=lambda i: abs(i - guess))
        ref = reference.get(n)
        same = [i for i in window if ref is not None and _skel(lines[i].text) == _skel(ref)]
        if ours is None:
            return same[0] if same else guess
        hits = [i for i in window if ours in lines[i].text]
        return next((i for i in same if i in hits), hits[0] if hits else None)

    last: tuple[str, object] | None = None  # (number, line) of the difference applied last
    for k, (n, insert, ours, printed) in enumerate(diffs + (lyrics or [])):
        if k == len(diffs):
            reference = {}  # the lyrics are keyed by the first pass's numbers
        printed = _printed(printed)
        if ours and not any(ours in l.text for l in doc.lines):
            ours = ours.replace("\u2019", "\u02bc")
        if insert and last is not None and last[0] == n and last[1] in doc.lines:
            i = doc.lines.index(last[1])  # a verse split off the line just changed
        else:
            i = locate(n, None if insert or not ours else ours)
        if i is None:
            warnings.append(f"difference at {n}: «{ours}» not found near it")
            continue
        line = doc.lines[i]
        if insert:
            new = Line(line.n + "z", printed)
            doc.items.insert(doc.items.index(line) + 1, new)
            line = new
        elif not printed and ours and ours.strip() == line.text.strip():
            doc.items.remove(line)
        elif ours:
            line.text = line.text.replace(ours, printed, 1)
        elif printed:
            line.text = (line.text + " " + printed).strip()
        if " | " in line.text and line in doc.lines:
            first, *rest = [part.strip() for part in line.text.split(" | ")]
            line.text = first
            at = doc.items.index(line)
            for j, part in enumerate(rest, 1):
                doc.items.insert(at + j, Line(line.n + "z", part))
        last = (n, line)
    lines = doc.lines
    orig = list(lines)
    explicit: dict[int, str] = {}
    current = {l.n: i for i, l in enumerate(lines)}
    for n, word in anchors:
        guess = current.get(n)
        if guess is None:
            near = [i for i, l in enumerate(lines) if re.match(r"\d+", l.n) and abs(num(l.n) - num(n)) <= 3]
            guess = near[0] if near else None
        if guess is None:
            warnings.append(f"printed {n} {word}: no line near it")
            continue
        window = range(max(0, guess - 8), min(len(lines), guess + 9))
        words = [_skel(w) for w in word.split()]
        begins = [i for i in window if [_skel(w) for w in lines[i].text.split()[:len(words)]] == words]
        found = [i for i in begins if id(lines[i]) not in cont]
        if not found and begins:
            # a number printed on the later part of what our text has as a shared verse: Jebb
            # counts that part as a verse of its own (El. 1280 τί μὴν οὔ;)
            found = begins
            cont.discard(id(lines[min(found, key=lambda i: abs(i - guess))]))
        if not found:
            # Jebb prints a number beside the wrapped end of a long lyric verse (ἄφρακτος |
            # φίλων· 910): the verse ends there, so the next line takes the next number, and the
            # verse is numbered by count from the lines before it
            inside = [i for i in window if id(lines[i]) not in cont
                      and words[0] in [_skel(w) for w in lines[i].text.split()[1:]]]
            if inside:
                i = min(inside, key=lambda i: abs(i - guess)) + 1
                while i < len(lines) and id(lines[i]) in cont:
                    i += 1
                if i < len(lines):
                    explicit.setdefault(i, str(num(n) + 1))
                continue
            warnings.append(f"printed {n} {word}: no line begins so near our {n}")
            continue
        explicit[min(found, key=lambda i: abs(i - guess))] = n
    # A word Jebb divides between two lyric verses (εὐδαί- | μων) is written whole at the end of
    # the first, so that it can be looked up and parsed; the verses and their numbers stay.
    for i in range(len(lines) - 1):
        m = re.search(r"(\S*[\u0370-\u03ff\u1f00-\u1fff])-$", lines[i].text)
        nxt = lines[i + 1].text.split(maxsplit=1)
        if m and nxt and re.match(r"[\u0370-\u03ff\u1f00-\u1fff]", nxt[0]):
            lines[i].text = lines[i].text[:-1] + nxt[0]
            lines[i + 1].text = nxt[1] if len(nxt) > 1 else ""
    for line in [l for l in lines if not l.text.strip()]:
        doc.items.remove(line)  # a verse that was only the end of a word
    lines = doc.lines
    new_parts = {i for i, l in enumerate(lines) if id(l) in cont}
    explicit = {lines.index(l): n for l, n in ((orig[i], n) for i, n in explicit.items()) if l in lines}
    return explicit, new_parts, warnings


def perseus_anchors(lines, stated: dict[int, str], printed: dict[int, str], reach: int = 10) -> dict[int, str]:
    """The numbers the Perseus file states (`stated`: id of the line -> number) as fixed points
    where no printed number is near (pages not yet checked), in order with the printed ones."""
    import bisect

    def num(n: str) -> int:
        return int(re.match(r"\d+", n).group())

    fixed = sorted(printed)
    out: dict[int, str] = {}
    for i, line in enumerate(lines):
        n = stated.get(id(line))
        if n is None:
            continue
        k = bisect.bisect_left(fixed, i)
        before = fixed[k - 1] if k else None
        after = fixed[k] if k < len(fixed) else None
        if (before is not None and i - before <= reach) or (after is not None and after - i <= reach):
            continue
        if (before is not None and num(printed[before]) >= num(n)) or (after is not None and num(printed[after]) <= num(n)):
            continue
        out[i] = n
    return out


def label_parts(doc, play: Play) -> None:
    """Name each top-level section by Jebb's division (play.parts) in which most of its verses
    fall; a later section of a division already named is "(continued)" (a lyric part inside an
    episode, or the episode again after it). By the majority, not the first line: Perseus's
    section boundaries often lie a verse before Jebb's division (512 for 513), and the first
    line would then name the whole episode after the stasimon before it."""
    import collections

    from .textfmt import Line, Section

    if not play.parts:
        return
    counts: dict[int, collections.Counter] = {}
    current = None
    for i, item in enumerate(doc.items):
        if isinstance(item, Section) and item.level == 1:
            current = i
            counts[i] = collections.Counter()
        elif isinstance(item, Line) and current is not None:
            num = int(re.match(r"\d+", item.n).group())
            division = [k for k, (start, _label) in enumerate(play.parts) if start <= num]
            counts[current][division[-1] if division else 0] += 1
    # the most verses; between equal counts the earlier division
    chosen = {i: min(c, key=lambda d: (-c[d], d)) for i, c in counts.items() if c}
    # but a division that would be named nowhere keeps the section its first verses begin, if it
    # has more than one verse there (Electra 1384-1441: the stasimon 1384-1397 and the kommos of
    # the exodos in one Perseus section)
    named = set(chosen.values())
    for i, c in counts.items():
        if i in chosen:
            first = min(c)
            if first not in named and c[first] > 1:
                chosen[i] = first
                named = set(chosen.values())
    seen: set[str] = set()
    for i, k in chosen.items():
        name = play.parts[k][1]
        doc.items[i].label = name if name not in seen else f"{name} (continued)"
        seen.add(name)


def add_transcribed_introduction(path: Path, checked: Path, play: Play, paras: list[str] | None = None,
                                 how: str = "transcribed page by page") -> None:
    """The chapters of Jebb's Introduction that Perseus lacks (the manuscripts, the ancient
    argument, the persons, the structure; for some plays the whole), transcribed page by page
    (introduction-*.md, brief INTRODUCTION.md), after those from Perseus. `paras`: the chapters'
    paragraphs already merged (sophocles-prose: from the prose OCR batches), `how` they were read."""
    from .sophocles_pages import SCAN_EDITIONS, merge_pages

    if paras is None:
        paras = merge_pages(checked, "introduction-") if checked.exists() else []
    if not paras:
        return
    slug = play.slug
    transcribed = (f"Sophocles: The Plays and Fragments, {PART_ROMAN[play.part]}: The {play.title_en}, "
                   f"Cambridge University Press, {SCAN_EDITIONS[slug]}, {how}")
    if path.exists():
        head, _, body = path.read_text(encoding="utf-8").partition("\n\n")
        head = re.sub(r"^# source: (.*)$", lambda m: f"# source: {m.group(1)}; the chapters after § "
                      f"{sum(1 for l in body.splitlines() if l.startswith('## '))} from {transcribed}", head, flags=re.M)
        head = re.sub(r"^# license: .*$", "# license: CC BY-SA 3.0 US (Perseus); the transcribed chapters CC BY-SA 4.0",
                      head, flags=re.M)
        text = head + "\n\n" + body.rstrip("\n") + "\n\n" + "\n\n".join(paras) + "\n"
    else:
        text = (f"# title: Introduction\n# author: Richard C. Jebb\n# source: {transcribed}\n"
                f"# license: CC BY-SA 4.0 (transcription; the edition is in the public domain)\n\n"
                + "\n\n".join(paras) + "\n")
    path.write_text(text, encoding="utf-8")
    shown = path.with_suffix("") if path.suffix == ".part" else path
    print(f"added to {shown}: {sum(1 for p in paras if p.startswith('#'))} transcribed headings")


def import_play(slug: str, sources: Path, texts: Path, build: Path, lexicon: Path) -> None:
    from .import_perseus import (LEMMA_FIXES, p4_text_to_document, renumber_from_treebank, tei_to_document,
                                 write_syntax_nodes, write_tokens)
    from .odyssey import align, fix_lemma, syntax_nodes
    from .odyssey_merge import Analyser, Frequencies, choose_analysis
    from .textfmt import write_file

    play = PLAYS[slug]
    files = sources_for(play)
    out = texts / slug
    out.mkdir(parents=True, exist_ok=True)

    tb = read_agdt(sources / "treebanks" / play.treebank) if play.treebank else read_glaux_lines(sources / "glaux" / play.glaux)
    edition = f"Sophocles: The Plays and Fragments, {PART_ROMAN[play.part]}: The {play.title_en}, ed. R. C. Jebb, Cambridge University Press, {play.edition}"
    grc = p4_text_to_document(sources / files["greek"], {
        "title": play.title, "author": "Σοφοκλῆς", "lang": "grc",
        "source": f"Perseus Digital Library, soph.{play.code}_gk.xml",
        "edition": edition + " (Perseus Digital Library)",
        "license": "CC BY-SA 3.0 US",
        **({"syntax": "automatic"} if play.glaux else {}),
    }, split_verses=True)
    parts = {int(i) for i in grc.meta.pop("_parts", "").split(",") if i}
    stated = {int(i) for i in grc.meta.pop("_explicit", "").split(",") if i}
    for w in renumber_verses(grc, tb, parts, {i: grc.lines[i].n for i in stated}):
        print("  numbering: " + w, file=sys.stderr)
    # Jebb's printed page, where the transcribers have checked it: his readings and his numbers
    checked = sources.parent / "transcriptions" / "sophocles" / slug
    if any(checked.glob("batch-*.md")):
        from .sophocles_pages import read_reference, text_check

        anchors, diffs = text_check(checked)
        lyric_anchors, lyrics = text_check(checked, "lines-")
        stated_ids = {id(grc.lines[i]): grc.lines[i].n for i in stated}
        explicit, parts, warnings = apply_text_check(grc, anchors + lyric_anchors, diffs, parts,
                                                     read_reference(checked), lyrics)
        explicit.update(perseus_anchors(grc.lines, stated_ids, explicit))
        for w in warnings:
            print("  text check: " + w, file=sys.stderr)
        for w in renumber_verses(grc, tb, parts, explicit):
            print("  numbering (printed): " + w, file=sys.stderr)
        print(f"  text check: {len(diffs)} differences applied, {len(explicit)} printed numbers placed")
    label_parts(grc, play)
    write_file(out / "grc.txt", grc)
    print(f"wrote {out / 'grc.txt'}: {len(grc.lines)} lines")

    eng = jebb_translation(play, sources)
    write_file(out / "eng-jebb.txt", eng)
    print(f"wrote {out / 'eng-jebb.txt'}: {len(eng.lines)} paragraphs")

    # lemmas, morphology and syntax; the analyser for words the treebank lacks or reads otherwise
    rows, _warnings = align(grc, tb, keep_tb_form=True)
    analyse = Analyser(lexicon)
    freq = Frequencies(sources / "treebanks")
    review = []
    for r in rows:
        tb_form = r.pop("tb_form", "")
        same = tb_form and greek.strip_diacritics(tb_form) == greek.strip_diacritics(r["form"])
        if r["lemma"] and r["postag"] and (same or not tb_form):
            continue
        chosen = choose_analysis(r["form"], analyse(r["form"]), r["postag"], r["lemma"], freq, tb_form)
        reason = ("no lemma or parse in the treebank" if same
                  else f"reads {r['form']} where the treebank has {tb_form}" if tb_form
                  else "not in the treebank")
        if chosen is not None:
            r["lemma"], r["postag"] = fix_lemma(chosen[0]), chosen[1]
        review.append({"line": r["line"], "form": r["form"], "lemma": r["lemma"], "postag": r["postag"], "reason": reason})
    for r in rows:
        r["lemma"] = LEMMA_FIXES.get(r["lemma"], r["lemma"])
        if (not r["lemma"] or r["lemma"] in WRONG_LEMMAS) and r["form"] in FORM_FIXES:
            r["lemma"], r["postag"] = FORM_FIXES[r["form"]]
    write_tokens(out / "tokens.tsv", rows)
    used = {(r["sentence"], w) for r in rows for w in r["word_id"].split("+") if r["sentence"]}
    write_syntax_nodes(out / "syntax-nodes.tsv", syntax_nodes(tb, used))
    missing = sum(1 for r in rows if not r["lemma"])
    print(f"wrote {out / 'tokens.tsv'}: {len(rows)} words, {missing} without lemma, {len(review)} for review")
    build.mkdir(parents=True, exist_ok=True)
    with (build / f"{slug}-review.tsv").open("w", encoding="utf-8") as f:
        f.write("line\tform\tlemma\tpostag\treason\n")
        for r in review:
            f.write(f"{r['line']}\t{r['form']}\t{r['lemma']}\t{r['postag']}\t{r['reason']}\n")

    if play.commentary and (sources / files["commentary"]).exists():
        from .commentary import import_jebb_commentary
        from .introduction import import_introduction

        source = f"Perseus Digital Library, jebb.soph.{play.code}_eng.xml ({edition})"
        n = import_jebb_commentary(sources / files["commentary"], out / "commentary-jebb.md", {
            "title": f"Commentary on Sophocles: {play.title_en}", "author": "Richard C. Jebb", "lang": "eng",
            "source": source, "license": "CC BY-SA 3.0 US"})
        print(f"wrote {out / 'commentary-jebb.md'}: {n} notes")
        n = import_introduction(sources / files["commentary"], out / "introduction.md", {
            "title": "Introduction", "author": "Richard C. Jebb", "source": source, "license": "CC BY-SA 3.0 US"})
        if n:
            print(f"wrote {out / 'introduction.md'}: {n} sections")
        else:
            # Perseus lacks this play's introduction (the Oedipus Tyrannus): it is transcribed instead
            (out / "introduction.md").unlink()
            print(f"no introduction in {files['commentary']}")
    add_transcribed_introduction(out / "introduction.md", checked, play)


# ---------------------------------------------------------------- the prose OCR route

PROSE_HOW = "read by OCR and checked against the page images"


def prose_paragraphs(directory: Path, kind: str) -> list[str]:
    """The paragraphs of a play's checked prose batches (drama_prose: <kind>-NN.md, the page's
    Markdown without its flags and notes), merged as the page-by-page transcriptions are
    (sophocles_pages.merge_page_blocks: '+ ' runs on, footnotes stay after their paragraph); the
    OCR's elision mark (᾽, ʼ) after a Greek letter written ’ as in the other plays' documents."""
    from .drama_prose import read_prose_batches
    from .sophocles_pages import merge_page_blocks

    pages = {stem: block["md"] for stem, block in read_prose_batches(directory, kind).items()}
    paras = [re.sub(r"(?<=[\u0370-\u03ff\u1f00-\u1fff])[\u1fbd\u02bc]", "\u2019", p) for p in merge_page_blocks(pages)]
    return [plain_heading(p) if p.startswith("#") else p for p in paras]


def plain_heading(heading: str) -> str:
    """A Markdown heading without italics markers or backslashes: the reader shows a heading as
    plain text (and lists it in the contents), so "## § 18 — The *Oedipus* of Seneca." would show
    its asterisks."""
    marks, _, text = heading.partition(" ")
    return f"{marks} " + re.sub(r"\s+", " ", re.sub(r"[*_\\]", "", text)).strip()


def unchecked_prose(directory: Path, kind: str, index: Path | None = None) -> list[str]:
    """Why the batches of a kind cannot be merged yet: a flag not answered, a page of the draft's
    index (build/drama-prose/<slug>/<kind>.json) missing. Empty when they can."""
    import json

    from .drama_prose import read_prose_batches

    pages = read_prose_batches(directory, kind)
    out = []
    for stem, block in pages.items():
        n = sum(1 for raw in block["flags"] if re.match(r"^\d+ .*→\s*$", raw))
        if n:
            out.append(f"{block['batch']} {stem}: {n} flags not answered")
    if index is not None and index.exists():
        for p in json.loads(index.read_text(encoding="utf-8")):
            if p["stem"] not in pages:
                out.append(f"{p['stem']}: not in the {kind} batches")
    return out


def write_prose(slug: str, sources: Path, texts: Path, transcriptions: Path, index_dir: Path | None = None) -> int:
    """sophocles-prose: from the checked prose batches of a play on the drama route
    (transcriptions/drama/<slug>/intro-NN.md, appendix-NN.md) texts/<slug>/introduction.md (the
    chapters from Perseus, made afresh from sources/jebb-<slug>-commentary.xml as import-sophocles
    makes them, then the transcribed chapters) and texts/<slug>/appendix.md (as
    merge-sophocles-appendix); a kind whose batches are not all checked is left alone. Then
    Jebb's commentary from Perseus (commentary-jebb.md) made afresh (write_commentary) and its notes
    on lines our numbering lacks re-filed (refile_commentary); Jebb's translation (eng-jebb.txt)
    made afresh and its segments at numbers our text lacks re-filed (write_translation). Nothing
    else in texts/<slug>/ is touched. Safe to run again. Returns the number of kinds left alone."""
    import os

    from .introduction import import_introduction
    from .sophocles_pages import appendix_header

    play = PLAYS[slug]
    out = texts / slug
    out.mkdir(parents=True, exist_ok=True)
    skipped = 0
    for kind in ("intro", "appendix"):
        if not any(transcriptions.glob(f"{kind}-*.md")):
            print(f"{slug} {kind}: no batches")
            continue
        why = unchecked_prose(transcriptions, kind, index_dir / f"{kind}.json" if index_dir else None)
        if why:
            print(f"{slug} {kind}: not merged, the batches are not all checked:\n  " + "\n  ".join(why[:20])
                  + (f"\n  … and {len(why) - 20} more" if len(why) > 20 else ""))
            skipped += 1
            continue
        paras = prose_paragraphs(transcriptions, kind)
        if kind == "appendix":
            path = out / "appendix.md"
            tmp = path.with_name(path.name + ".part")
            tmp.write_text(appendix_header(slug, PROSE_HOW).rstrip("\n") + "\n\n" + "\n\n".join(paras) + "\n", encoding="utf-8")
            os.replace(tmp, path)
            print(f"wrote {path}: {sum(1 for p in paras if p.startswith('## '))} notes")
            continue
        path = out / "introduction.md"
        tmp = path.with_name(path.name + ".part")
        tmp.unlink(missing_ok=True)
        commentary = sources / sources_for(play)["commentary"]
        if play.commentary and commentary.exists():
            n = import_introduction(commentary, tmp, {
                "title": "Introduction", "author": "Richard C. Jebb", "source": perseus_source(play),
                "license": "CC BY-SA 3.0 US"})
            if not n:
                tmp.unlink()  # Perseus lacks this play's introduction (the Oedipus Tyrannus)
            else:
                print(f"{slug}: {n} sections of the introduction from Perseus")
        add_transcribed_introduction(tmp, transcriptions, play, paras=paras, how=PROSE_HOW)
        os.replace(tmp, path)
    write_commentary(slug, sources, texts)
    refile_commentary(out)
    write_translation(slug, sources, texts)
    return skipped


def jebb_translation(play: Play, sources: Path):
    """Jebb's translation from Perseus as a Document (the eng-jebb.txt import_play writes)."""
    from .import_perseus import tei_to_document

    return tei_to_document(sources / sources_for(play)["eng"], {
        "title": play.title_en, "translator": "Richard C. Jebb", "lang": "eng",
        "source": f"urn:cts:greekLit:tlg0011.{play.tlg}.{play.eng}",
        "edition": f"Sophocles: The Plays and Fragments, {PART_ROMAN[play.part]}: The {play.title_en}, tr. R. C. Jebb, Cambridge; modernized by Perseus",
        "license": "CC BY-SA 4.0",
    })


def refile_translation(doc, numbers: list[str], speech_starts: set[str] | None = None,
                       word_map=None, fixed: dict[str, str | None] | None = None) -> tuple[list[str], list[str]]:
    """Jebb's translation from Perseus (a Document) put with the verses of grc.txt (`numbers`, in
    order). The segments' numbers are Jebb's verse numbers as Perseus's English cites them, which
    are ours except where his longer lyric verse covers a number, and except in a few places where
    Perseus's count drifts from his print. So, segment by segment, in order:
      * a lettered number is Perseus's way of dividing a verse shared by speakers (whether
        grc.txt has the number or not): 876a is the first speaker's part, 876b the second's (409b
        alone: the second part, the first being in the segment before; if the file also has a plain
        876, a is the second part). Our text numbers the parts 876, 876a …: the k-th part goes to
        the k-th of these that grc.txt has; when it has fewer (Jebb prints the second speaker's
        words as the next verse) the number is left as it is and the build shows the segment from
        the next verse;
      * a plain number our text has stays; one that Jebb's longer verse covers goes to the nearest
        earlier verse;
      * where the segment begins a new speaker but that verse does not (`speech_starts`: the
        verses of grc.txt that begin a speech), the word map is asked (`word_map(n)`: the verse of
        ours that holds the first word of Perseus's verse n, drama.perseus_number_map): its verse
        is taken if it begins a speech and keeps the order (Perseus 886 = our 887);
      * a segment that lands on the verse of the segment before is joined to it (one space), unless
        a change of speaker, a stage direction or a section lies between: then, as one that would
        land before it, it takes the next verse after it, so that the print's order stays.
    `fixed` (TRANSLATION_NUMBERS) overrides all of this for the segments it names, where
    Perseus's English counts a stretch otherwise than the print (its number -> ours, or None: a
    "…" for a lost verse our text has no line for, dropped with its speaker).
    Changes the Document in place; returns (moves, notes on the segments left or forced on)."""
    from .linenum import parts as n_parts
    from .textfmt import Line

    have = set(numbers)
    order = {n: i for i, n in enumerate(numbers)}
    keys = sorted((n_parts(n), n) for n in numbers)
    items = doc.items
    original = {it.n for it in items if isinstance(it, Line)}
    moves: list[str] = []
    left: list[str] = []

    def default(n: str) -> tuple[str | None, str]:
        num, letter = n_parts(n)
        if letter:
            k = (1 if str(num) in original else 0) + ord(letter) - ord("a")
            ours = [x for x in [str(num)] + [f"{num}{chr(ord('a') + j)}" for j in range(26)] if x in have]
            if k < len(ours):
                return ours[k], f"part {k + 1} of the shared verse {num}"
            return None, f"grc.txt has {len(ours)} part(s) of verse {num}"
        if n in have:
            return n, ""
        earlier = [x for key, x in keys if key < (num, letter)]
        return (earlier[-1], "covered by the verse") if earlier else (None, "no earlier verse")

    out: list = []
    prev: int | None = None      # order index of the last placed segment
    prev_line = None
    blocked = False              # a speaker, stage direction or section since the last segment
    new_speaker = False
    for it in items:
        if not isinstance(it, Line):
            out.append(it)
            blocked = True
            if type(it).__name__ == "Speaker":
                new_speaker = True
            continue
        n = it.n
        if fixed and n in fixed:
            target, how = fixed[n], "Jebb's verse (TRANSLATION_NUMBERS)"
            if target is None:
                moves.append(f"translation: {n} dropped ({it.text.strip()[:30]}: no verse of ours)")
                if out and type(out[-1]).__name__ == "Speaker":
                    out.pop()
                continue
        else:
            target, how = default(n)
        if (not (fixed and n in fixed) and new_speaker and speech_starts is not None and word_map is not None
                and target is not None and target not in speech_starts):
            m = word_map(n)
            if m in speech_starts and (prev is None or order[m] > prev):
                target, how = m, "its words begin a speech there (word map)"
        if target is None:
            left.append(f"translation: {n} left as it is ({how})")
        else:
            if prev is not None and order[target] <= prev:
                if order[target] == prev and not blocked and prev_line is not None:
                    prev_line.text = prev_line.text.rstrip() + " " + it.text.lstrip()
                    moves.append(f"translation: {n} joined to the segment of {target} ({how or 'same verse'})")
                    new_speaker = False
                    continue
                if prev + 1 >= len(numbers):
                    left.append(f"translation: {n} left as it is (no verse after {numbers[prev]})")
                    target = None
                else:
                    forced = numbers[prev + 1]
                    left.append(f"translation: {n} would go to {target}, before the segment before it: "
                                f"takes the next verse, {forced}")
                    target = forced
            elif target != n:
                moves.append(f"translation: {n} → {target}" + (f" ({how})" if how else ""))
            if target is not None:
                it.n = target
                prev = order[target]
        out.append(it)
        prev_line = it
        blocked = new_speaker = False
    items[:] = out
    return moves, left


def translation_word_map(slug: str, sources: Path, lines: list[tuple[str, str]], translation_numbers: set[str]):
    """word_map for refile_translation: Perseus's verse n (a lettered part: the k-th part of that
    verse in the reference text, plain, a, b …) -> the verse of ours that holds its first word."""
    from . import drama
    from .linenum import parts as n_parts

    pers = drama.load_perseus(drama.PLAYS[slug], sources)
    nmap = drama.perseus_number_map(lines, pers)
    ref = {l["n"] for l in pers["lines"]}

    def word_map(n: str) -> str | None:
        num, letter = n_parts(n)
        if letter:
            k = (1 if str(num) in translation_numbers else 0) + ord(letter) - ord("a")
            parts = [x for x in [str(num)] + [f"{num}{chr(ord('a') + j)}" for j in range(26)] if x in ref]
            n = parts[k] if k < len(parts) else ""
        return nmap.get(n) if n in ref else None
    return word_map


def write_translation(slug: str, sources: Path, texts: Path) -> list[str]:
    """texts/<slug>/eng-jebb.txt afresh from Perseus (as import_play makes it), then
    refile_translation against grc.txt, with the word map of the play's check text where the drama
    route has one (sophocles-prose); safe to run again. Returns the moves."""
    import os

    from . import drama
    from .textfmt import Line, Speaker, parse_file, write_file

    play = PLAYS[slug]
    src = sources / sources_for(play)["eng"]
    grc = texts / slug / "grc.txt"
    if not src.exists() or not grc.exists():
        return []
    doc = jebb_translation(play, sources)
    gdoc = parse_file(grc)
    lines = [(l.n, l.text) for l in gdoc.lines]
    starts: set[str] = set()
    pending = True
    for it in gdoc.items:
        if isinstance(it, Speaker):
            pending = True
        elif isinstance(it, Line):
            if pending:
                starts.add(it.n)
            pending = False
    word_map = None
    if slug in drama.PLAYS and drama.PLAYS[slug].check_text:
        word_map = translation_word_map(slug, sources, lines, {it.n for it in doc.items if isinstance(it, Line)})
    moves, left = refile_translation(doc, [n for n, _t in lines], starts, word_map,
                                     TRANSLATION_NUMBERS.get(slug))
    path = texts / slug / "eng-jebb.txt"
    tmp = path.with_name(path.name + ".part")
    write_file(tmp, doc)
    os.replace(tmp, path)
    for m in moves + left:
        print(m)
    print(f"wrote {path}: {len(moves)} segments moved or joined, {len(left)} left or forced on")
    return moves


# Perseus's English where its numbers in a stretch follow neither Jebb's print nor the rules of
# refile_translation (read beside the Greek): Perseus's number -> our verse, None = a "…" standing
# for a verse lost in the MSS. (Jebb prints a line of metrical signs, our text no verse)
TRANSLATION_NUMBERS: dict[str, dict[str, str | None]] = {
    "oedipuscoloneus": {
        # parodos: the lost verses after 181 and 182; 193 (οὕτως;) is Jebb's 194; Perseus counts
        # 197-199 one ahead; τί τόδʼ … τέκνον, ὤμοι, τί γεγώνω; are Jebb's 212-212c (Perseus 211-214)
        "181a": None, "181b": None, "181c": "182", "183": None, "193": "194", "193a": "194a",
        "198": "197", "199": "198", "200": "199",
        "211": "212", "212": "212a", "213": "212b", "214": "212c",
        # first kommos: πῶς φῄς; 531, παῖδε, δύο δʼ ἄτα 532, ὦ Ζεῦ 532a, ματρὸς 533; τί γάρ; 538b,
        # ἐδεξάμην δῶρον 538c
        "530": "531", "530a": "532", "531": "532a", "532": "533", "539": "538b", "539a": "538c",
        # δοκῶ 879, τάνδʼ ἄρʼ 879a; Creon's Ζεύς γʼ ἂν εἰδείη 882a (882 is Jebb's supplement)
        "878": "879", "879": "879a", "882a": "882a",
        # Perseus's misprint for 1099a (ὦ πάτερ πάτερ)
        "1009a": "1099a",
        # the second speaker's part of a shared verse whose first part Perseus files under the
        # verse before (so no plain number): τί δρᾷς, ξένε; 829a, ὦ τάλαινʼ ἐγώ 1438a, ταῦτα δʼ ἐν
        # τῷ δαίμονι 1443a, μηδέ γε μάτευε 1743a
        "829a": "829a", "1438a": "1438a", "1443a": "1443a", "1743a": "1743a",
        # segments (Perseus's five-verse chunks in the lyrics) put with the verse that holds their
        # first words: ὅρα 117, ἃς τρέμομεν 127, ἐή· ἀλαῶν ὀμμάτων 149, μετάσταθʼ 161, ἀβάτων ἀποβάς
        # 167, πρός νυν θεῶν 49, μὴ ʼπίτασσʼ 839a, πώλοισιν 1062, καὶ τὸν ἀγρευτὰν Ἀπόλλω 1091, τίς
        # πλαγὰ 1231, αἱ δʼ ἀνατέλλοντος 1246, νέα τάδε 1447, μέγας, ἴδε 1462, τάλαιναν 1691, ὦ
        # τάλαινα (Ismene) 1715, ἐπαμμένει 1717
        "118": "117", "130": "127", "148": "149", "160": "161", "165": "167", "48": "49",
        "839": "839a", "1060": "1062", "1090": "1091", "1230": "1231", "1245": "1246",
        "1448": "1447", "1463": "1462", "1690": "1691", "1714": "1715", "1715": "1717",
    },
}


# Perseus's commentary where it is of another edition than the volume scanned (play.edition): the
# Oedipus Tyrannus on Perseus is the second edition (its note numbers are not always the third's)
PERSEUS_EDITION = {"oedipustyrannus": "second edition, 1887"}


def perseus_source(play: Play) -> str:
    """The source line of the documents made from Perseus's commentary file (import_play)."""
    edition = (f"Sophocles: The Plays and Fragments, {PART_ROMAN[play.part]}: The {play.title_en}, ed. R. C. Jebb, "
               f"Cambridge University Press, {PERSEUS_EDITION.get(play.slug, play.edition)}")
    return f"Perseus Digital Library, jebb.soph.{play.code}_eng.xml ({edition})"


def write_commentary(slug: str, sources: Path, texts: Path) -> int:
    """texts/<slug>/commentary-jebb.md afresh from sources/jebb-<slug>-commentary.xml, with the
    header import_play gives it, and the metrical schemes Perseus writes with breves and macrons
    (¯˘˘¯) in metrical signs (–⏑⏑–), as in the files of the plays made earlier. Run by
    sophocles-prose before refile_commentary re-files the notes on lines our numbering lacks, so
    a change of the numbering or of the importer reaches the file; safe to run again. Returns the
    number of notes (0 when Perseus has no commentary for the play: the file is left alone)."""
    import os

    from .commentary import import_jebb_commentary
    from .greek import length_signs_over
    from .lexicon import _METRE, _METRE_SIGNS

    play = PLAYS[slug]
    src = sources / sources_for(play)["commentary"]
    if not play.commentary or not src.exists():
        return 0
    path = texts / slug / "commentary-jebb.md"
    tmp = path.with_name(path.name + ".part")
    try:
        n = import_jebb_commentary(src, tmp, {
            "title": f"Commentary on Sophocles: {play.title_en}", "author": "Richard C. Jebb", "lang": "eng",
            "source": perseus_source(play), "license": "CC BY-SA 3.0 US"})
    except SystemExit as e:  # the file holds no commentary
        tmp.unlink(missing_ok=True)
        print(f"{src.name}: {e}; {path.name} left as it is")
        return 0
    text = range_headings(tmp.read_text(encoding="utf-8"))
    for wrong, right in COMMENTARY_FIXES.get(slug, []):
        if wrong not in text:
            print(f"{path.name}: fix not applied, not found: {wrong}")
        text = text.replace(wrong, right)
    text = length_signs_over(text)
    tmp.write_text(_METRE.sub(lambda m: m.group(1).translate(_METRE_SIGNS), text), encoding="utf-8")
    os.replace(tmp, path)
    print(f"wrote {path}: {n} notes from Perseus")
    return n


_RANGE_LOST = re.compile(r"^## (\d+)\n(\n?)— ?\*(\d+)\* ?", re.M)


def range_headings(text: str) -> str:
    """Perseus's commentary keeps only the first number of some of Jebb's range headings and puts
    the rest in front of the note as an italic number ("982—984 He has just said" comes as
    "## 982" + "—*984* He has just said"): the heading is made the range again (## 982-984)."""
    return _RANGE_LOST.sub(lambda m: f"## {m.group(1)}-{m.group(3)}\n{m.group(2)}", text)


# Perseus's commentary where it is not what the page prints, put right before the vowel-length and
# metrical signs are converted (write_commentary): (Perseus's text as imported, the page's)
COMMENTARY_FIXES: dict[str, list[tuple[str, str]]] = {
    "oedipustyrannus": [
        # leaf 191, note on 640 (synizesis of υ): the bar stands over both vowels (υ͞ω), not
        # over the υ as a macron (Perseus: genu/&macr;wn)
        ("γενύ¯ων", "γενύ͞ων"), ("ἡδύ¯οσμον", "ἡδύ͞οσμον"), ("Ἐρινύ¯ων", "Ἐρινύ͞ων"),
        ("Ἠλεκτρύ¯ωνος", "Ἠλεκτρύ͞ωνος"),
        # leaf 127, note on 118 f.: "χωρὶς τοῦ ῑ...ἡ μέντοι παράδοσις ἔχει τὸ ῑ." (Perseus: the
        # second ῑ without its mark)
        ("ἡ μέντοι παράδοσις ἔχει τὸ ι.", "ἡ μέντοι παράδοσις ἔχει τὸ ῑ."),
    ],
    "oedipuscoloneus": [
        # Perseus's Betacode v (digamma) where the page has another letter: leaf 155 (note 307)
        # υἱέος, leaf 285 (1181) νέα, leaf 232 (805) "√ΛΥ, another form of √ΛΟϜ", leaf 334 (1533)
        # √ΔΑϜ
        ("vἱέος", "υἱέος"), ("**vέα**", "**νέα**"),
        ("√ΛΓ, another form of √ΛΟv", "√ΛΥ, another form of √ΛΟϜ"), ("√ΔΑv", "√ΔΑϜ"),
        # leaf 155, note 310: "τί λέξω" (Perseus ti/le/cw)
        ("**τίλέξω**", "**τί λέξω**"),
        # note 49: a space lost after "προστρέπω),"; leaf 155, note 309: "ἀνδρί [γ'] ἐσθλὰ",
        # "pseudo-Philem."
        ("προστρέπω),φράσαι", "προστρέπω), φράσαι"), ("ἀνδρί [ γ' ] ἐσθλὰ", "ἀνδρί [γ'] ἐσθλὰ"),
        ("pseudo - Philem.", "pseudo-Philem."),
    ],
}


# Perseus's commentary: notes whose printed heading (and the first word of the lemma) Perseus lost,
# put right from the page: "number lemma-start" -> (Jebb's heading, Jebb's lemma)
NOTE_HEADING_FIXES: dict[str, dict[str, tuple[str, str]]] = {
    "trachiniae": {
        # leaf 172: "633—639 ὦ ναύλοχα κ.τ.λ." (Perseus: 639, the ὦ lost)
        "639 **<*> ναύλοχα**": ("633-639", "**ὦ ναύλοχα**"),
    },
}

_NOTE_HEAD = re.compile(r"^## (\d+[a-z]?)(?:-(\d+[a-z]?))?(?:\s+(ff?\.))?\s*$")


def _skel(word: str) -> str:
    from .drama import skel

    return skel(word)


def refile_notes(text: str, lines: dict[str, str],
                 heading_fixes: dict[str, tuple[str, str]] | None = None) -> tuple[str, list[str]]:
    """Jebb's notes (a commentary-jebb.md text) on verses our numbering lacks, filed as merge-drama
    files the apparatus (drama.place_notes): his longer printed verse covers the traditional
    numbers after its own (his 98 holds 98-99), so a note on 99 goes to the line that holds the
    first words of its bold lemma if they stand in the nearest earlier line or the next line of
    grc.txt (`lines`: number -> verse), else to the nearest earlier line; the printed number is
    kept in front of the note (`[99] **…**`), and a note filed under the heading just before it
    is joined to that note. A range's end our numbering lacks becomes the last line we have
    inside the range. Notes on lines we have are left exactly as they are, so running it again
    changes nothing. `heading_fixes` ("639 **<*> ναύλοχα**" -> ("633-639", "**ὦ ναύλοχα**"))
    first puts right a note whose heading and lemma Perseus lost or misread (NOTE_HEADING_FIXES).
    Returns the text and one line per note moved."""
    from .drama import base
    from .linenum import complete

    numbers = list(lines)
    have = set(numbers)
    raw = text.split("\n")
    head: list[str] = []
    blocks: list[list] = []  # [heading line, body lines]
    for line in raw:
        if line.startswith("## "):
            blocks.append([line, []])
        elif blocks:
            blocks[-1][1].append(line)
        else:
            head.append(line)
    moves: list[str] = []
    out: list[list] = []
    for heading, body in blocks:
        i = next((k for k, l in enumerate(body) if l.strip()), None)
        if heading_fixes and i is not None and _NOTE_HEAD.match(heading):
            pm = re.match(r"^\[(\S+)\] (.*)$", body[i])
            num, rest = (pm.group(1), pm.group(2)) if pm else (heading[3:].strip(), body[i])
            for key, (new_n, new_lemma) in heading_fixes.items():
                knum, _, klemma = key.partition(" ")
                if num == knum and rest.startswith(klemma):
                    moves.append(f"commentary: the note on {num} ({klemma}) is Jebb's note on {new_n} ({new_lemma})")
                    heading = f"## {new_n}"
                    body = body[:i] + [new_lemma + rest[len(klemma):]] + body[i + 1:]
        m = _NOTE_HEAD.match(heading)
        if not m or not numbers:
            out.append([heading, body])
            continue
        a, b, ff = m.group(1), m.group(2), m.group(3)
        b_full = complete(b, a) if b else ""
        if a in have and (not b or b_full in have):
            out.append([heading, body])
            continue
        printed = a + (f"-{b}" if b else "")
        new_a = a
        if a not in have:
            earlier = [n for n in numbers if 0 <= base(n) <= base(a)]
            later = [n for n in numbers if base(n) > base(a)]
            candidates = [c for c in (earlier[-1] if earlier else None, later[0] if later else None) if c]
            first = next((l for l in body if l.strip()), "")
            lm = re.match(r"^\*\*([^*]+)\*\*", first)
            words = [s for s in (_skel(w) for w, _s, _e in greek.words(lm.group(1))) if s][:3] if lm else []
            found = None
            if words:
                best = 0
                for c in candidates:  # the earlier line first: it wins a tie
                    verse = {_skel(w) for w, _s, _e in greek.words(lines[c])}
                    if words[0] not in verse:
                        continue
                    score = sum(1 for w in words if w in verse)
                    if score > best:
                        best, found = score, c
            if found:
                new_a = found
                how = "which holds its lemma"
            elif earlier:
                new_a = earlier[-1]
                how = "the nearest earlier line"
            else:
                out.append([heading, body])
                moves.append(f"commentary: no line for the note on {printed}")
                continue
        new_b = ""
        if b:
            new_b = b_full if b_full in have else ""
            if not new_b:
                inside = [n for n in numbers if base(new_a) < base(n) <= base(b_full)]
                new_b = inside[-1] if inside else ""
            if new_b and base(new_b) <= base(new_a):
                new_b = ""
        new_heading = f"## {new_a}" + (f"-{new_b}" if new_b else "") + (f" {ff}" if ff and not new_b else "")
        if new_a != a:
            # the printed number in front of the note, as in the apparatus
            i = next((k for k, l in enumerate(body) if l.strip()), None)
            if i is not None:
                body = body[:i] + [f"[{printed}] {body[i]}"] + body[i + 1:]
            moves.append(f"commentary: line {a} is not in our numbering; the note on {printed} goes to "
                         f"{new_heading[3:]} ({how})")
        else:
            moves.append(f"commentary: the note on {printed} now ends at {new_b or a}")
        if out and out[-1][0] == new_heading:
            prev = out[-1][1]
            while prev and not prev[-1].strip():
                prev.pop()
            prev.append("")
            prev.extend(body)
        else:
            out.append([new_heading, body])
    lines_out = head + [l for heading, body in out for l in [heading, *body]]
    return "\n".join(lines_out), moves


def refile_commentary(work_dir: Path) -> list[str]:
    """refile_notes on texts/<slug>/commentary-jebb.md against its grc.txt (sophocles-prose);
    writes the file only when a note moved. Returns the moves (also printed)."""
    from .textfmt import parse_file

    path, grc = work_dir / "commentary-jebb.md", work_dir / "grc.txt"
    if not path.exists() or not grc.exists():
        return []
    lines = {l.n: l.text for l in parse_file(grc).lines}
    text = path.read_text(encoding="utf-8")
    new, moves = refile_notes(text, lines, NOTE_HEADING_FIXES.get(work_dir.name))
    if new != text:
        tmp = path.with_name(path.name + ".part")
        tmp.write_text(new, encoding="utf-8")
        tmp.replace(path)
    for m in moves:
        print(m)
    print(f"{path}: {len(moves)} notes on lines our numbering lacks re-filed")
    return moves


# ---------------------------------------------------------------- numbering check (sophocles-numbering)

_APP_LEMMA = re.compile(r"^(?:\[[^\]]+\]\s*)?\*\*([^*]+)\*\*")
_APP_PRINTED = re.compile(r"^\[(\d+[a-z]?(?:-\d+[a-z]?)?)\]\s")


def _letters(s: str) -> str:
    """The letters of a text, accents, breathings, case and spaces ignored; an iota subscript
    counts as an iota (the apparatus quotes L's λαμπρᾶι for the text's λαμπρᾷ)."""
    from .drama import skel

    return "".join(skel(w, adscript=True) for w, _s, _e in greek.words(s))


def numbering_suspects(lines: list[tuple[str, str]], apparatus: str, reach: int = 3) -> list[dict]:
    """Where our verse numbers may not be Jebb's (lyric verses his longer verse covers, numbered
    on from the last margin number): from grc.txt's verses (`lines`: (number, verse) in order)
    and the merged apparatus (commentary-jebb-apparatus.md text). A note's lemma stands in the
    verse that bears the note's number, so two kinds are listed:
      * "lemma": a note whose bold lemma (`**…**` at its start, up to the first `...`, `…` or
        `|`) is not in the verse it is filed under but in a verse within `reach` lines of it;
      * "printed": a note whose printed number was kept in front (`[99] …`) because our
        numbering lacks it.
    Each item: kind, note (the note's number), lemma, filed (the number it is filed under),
    found (the number of the verse that holds the lemma, or None), context (the verses from
    `reach` lines before to `reach` after, as (number, verse))."""
    numbers = [n for n, _t in lines]
    index = {n: i for i, n in enumerate(numbers)}
    letters = [_letters(t) for _n, t in lines]
    out: list[dict] = []
    heading = None
    for para in re.split(r"\n\s*\n", apparatus):
        para = para.strip()
        m = re.match(r"^## (\S+)(?:[ \t]+ff?\.)?[ \t]*(?:\n(.*))?$", para, re.S)
        if m:
            heading, para = m.group(1), (m.group(2) or "").strip()
        elif para.startswith("#") or heading is None:
            continue
        if not para:
            continue
        filed = heading.split("-")[0]
        if filed not in index:
            continue
        i = index[filed]
        pm = _APP_PRINTED.match(para)
        note = pm.group(1) if pm else heading
        lm = _APP_LEMMA.match(para)
        lemma = re.split(r"\.\.\.|…|\|", lm.group(1))[0].strip() if lm else ""
        key = _letters(lemma)
        near = range(max(0, i - reach), min(len(lines), i + reach + 1))
        found = None
        if key:
            hits = [j for j in near if key in letters[j]]
            found = numbers[min(hits, key=lambda j: (abs(j - i), j))] if hits else None
        context = [lines[j] for j in near]
        if key and key not in letters[i] and found:
            out.append({"kind": "lemma", "note": note, "lemma": lemma, "filed": filed, "found": found, "context": context})
        elif pm:
            if not key:
                # no bold lemma: the words before a "]", else the first two Greek words
                rest = para[len(pm.group(0)):]
                bm = re.match(r"^([^\]:]{1,60})\]", rest)
                if bm:
                    lemma = bm.group(1).strip()
                else:
                    run = []
                    for w, _s, _e in greek.words(rest):
                        if not re.search(r"[\u0370-\u03ff\u1f00-\u1fff]", w) or len(run) == 2:
                            break
                        run.append(w)
                    lemma = " ".join(run)
                key = _letters(lemma)
                hits = [j for j in near if key and key in letters[j]]
                found = numbers[min(hits, key=lambda j: (abs(j - i), j))] if hits else None
            out.append({"kind": "printed", "note": note, "lemma": lemma, "filed": filed, "found": found,
                        "context": context})
    return out


def report_numbering(work_dir: Path, reach: int = 3) -> int:
    """sophocles-numbering: print numbering_suspects for texts/<slug>/ from the apparatus
    (commentary-jebb-apparatus.md); returns how many. (Jebb's commentary from Perseus is not
    scanned: Perseus drops the "f." of its headings, so a note on two verses whose lemma stands in
    the second would be listed everywhere; look at its numbers by hand in a suspect stretch.)"""
    from .textfmt import parse_file

    grc, app = work_dir / "grc.txt", work_dir / "commentary-jebb-apparatus.md"
    if not grc.exists() or not app.exists():
        print(f"{work_dir}: no grc.txt or commentary-jebb-apparatus.md")
        return 0
    lines = [(l.n, l.text) for l in parse_file(grc).lines]
    total = 0
    for path in (app,):
        label = "apparatus"
        items = numbering_suspects(lines, path.read_text(encoding="utf-8"), reach)
        for it in items:
            what = ("the lemma is not in the verse it is filed under" if it["kind"] == "lemma"
                    else "printed number kept in front: our numbering lacks it")
            where = f"; the lemma stands in {it['found']}" if it["found"] else ""
            print(f"{label} note {it['note']} ({it['lemma']}): filed under {it['filed']}{where} [{what}]")
            for n, t in it["context"]:
                mark = ">" if n == it["filed"] else ("*" if n == it["found"] else " ")
                print(f"  {mark} {n}\t{t}")
        lem = sum(1 for it in items if it["kind"] == "lemma")
        print(f"{work_dir.name} {label}: {lem} notes whose lemma stands in another verse, "
              f"{len(items) - lem} notes with the printed number in front")
        total += len(items)
    return total
