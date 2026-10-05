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


def add_transcribed_introduction(path: Path, checked: Path, play: Play) -> None:
    """The chapters of Jebb's Introduction that Perseus lacks (the manuscripts, the ancient
    argument, the persons, the structure; for some plays the whole), transcribed page by page
    (introduction-*.md, brief INTRODUCTION.md), after those from Perseus."""
    from .sophocles_pages import SCAN_EDITIONS, merge_pages

    paras = merge_pages(checked, "introduction-") if checked.exists() else []
    if not paras:
        return
    slug = checked.name
    transcribed = (f"Sophocles: The Plays and Fragments, {PART_ROMAN[play.part]}: The {play.title_en}, "
                   f"Cambridge University Press, {SCAN_EDITIONS[slug]}, transcribed page by page")
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
    print(f"added to {path}: {sum(1 for p in paras if p.startswith('#'))} transcribed headings")


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
