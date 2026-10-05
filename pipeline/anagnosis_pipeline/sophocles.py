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


def read_agdt(path: Path) -> list[dict]:
    """An AGDT treebank: every word (artificial nodes and punctuation included, is_word False),
    with the line it cites (the last citation carried forward)."""
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
                    current = m.group(1) + "abcdefgh"[int(m.group(2))]
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
    used = {l.n for l in merged.lines}
    for members, verse in zip(groups, merged.lines):
        lines[members[0]].n = verse.n
        base = re.match(r"^\d+", verse.n).group()
        letters = iter(c for c in "abcdefghijklmnop" if base + c not in used)
        for i in members[1:]:
            lines[i].n = base + next(letters)
            used.add(lines[i].n)
    return warnings


def _skel(s: str) -> str:
    return re.sub(r"[^α-ω]", "", greek.strip_diacritics(s).replace("ς", "σ"))


def apply_text_check(doc, anchors: list[tuple[str, str]], diffs: list, parts: set[int]) -> tuple[dict[int, str], set[int], list[str]]:
    """Jebb's printed text: the differences the transcribers found (keyed by our current line
    numbers) applied, and the printed line numbers placed on our lines as fixed points.
    Returns (fixed points by line index, the later parts of shared verses by index, warnings)."""
    from .textfmt import Line

    warnings = []
    cont = {id(l) for i, l in enumerate(doc.lines) if i in parts}
    by_n = {l.n: l for l in doc.lines}
    for n, insert, ours, printed in diffs:
        line = by_n.get(n)
        if line is None:
            warnings.append(f"difference at {n}: no such line")
            continue
        if insert:
            new = Line(n + "z", printed)
            doc.items.insert(doc.items.index(line) + 1, new)
        elif not printed and ours and ours.strip() == line.text.strip():
            doc.items.remove(line)
        elif ours and line.text.count(ours) >= 1:
            line.text = line.text.replace(ours, printed, 1)
        elif not ours and printed:
            line.text = (line.text + " " + printed).strip()
        else:
            warnings.append(f"difference at {n}: «{ours}» not in «{line.text}»")
    lines = doc.lines
    explicit: dict[int, str] = {}
    current = {l.n: i for i, l in enumerate(lines)}
    for n, word in anchors:
        guess = current.get(n)
        if guess is None:
            near = [i for i, l in enumerate(lines) if re.match(r"\d+", l.n) and abs(int(re.match(r"\d+", l.n).group()) - int(n)) <= 3]
            guess = near[0] if near else None
        if guess is None:
            warnings.append(f"printed {n} {word}: no line near it")
            continue
        found = [i for i in range(max(0, guess - 8), min(len(lines), guess + 9))
                 if lines[i].text.split() and _skel(lines[i].text.split()[0]) == _skel(word) and id(lines[i]) not in cont]
        if not found:
            warnings.append(f"printed {n} {word}: no line begins so near our {n}")
            continue
        explicit[min(found, key=lambda i: abs(i - guess))] = n
    new_parts = {i for i, l in enumerate(lines) if id(l) in cont}
    return explicit, new_parts, warnings


def label_parts(doc, play: Play) -> None:
    """Name each top-level section by Jebb's division its first line falls in."""
    from .textfmt import Line, Section

    if not play.parts:
        return
    seen: set[str] = set()
    current = None
    first_line: dict[int, str] = {}
    for i, item in enumerate(doc.items):
        if isinstance(item, Section) and item.level == 1:
            current = i
        elif isinstance(item, Line) and current is not None and current not in first_line:
            first_line[current] = item.n
    for i, n in first_line.items():
        num = int(re.match(r"\d+", n).group())
        name = [label for start, label in play.parts if start <= num][-1]
        doc.items[i].label = name if name not in seen else f"{name} (continued)"
        seen.add(name)


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
        from .sophocles_pages import text_check

        anchors, diffs = text_check(checked)
        explicit, parts, warnings = apply_text_check(grc, anchors, diffs, parts)
        for w in warnings:
            print("  text check: " + w, file=sys.stderr)
        for w in renumber_verses(grc, tb, parts, explicit):
            print("  numbering (printed): " + w, file=sys.stderr)
        print(f"  text check: {len(diffs)} differences applied, {len(explicit)} printed numbers placed")
    label_parts(grc, play)
    write_file(out / "grc.txt", grc)
    print(f"wrote {out / 'grc.txt'}: {len(grc.lines)} lines")

    eng = tei_to_document(sources / files["eng"], {
        "title": play.title_en, "translator": "Richard C. Jebb", "lang": "eng",
        "source": f"urn:cts:greekLit:tlg0011.{play.tlg}.{play.eng}",
        "edition": f"Sophocles: The Plays and Fragments, {PART_ROMAN[play.part]}: The {play.title_en}, tr. R. C. Jebb, Cambridge; modernized by Perseus",
        "license": "CC BY-SA 4.0",
    })
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
        print(f"wrote {out / 'introduction.md'}: {n} sections")
