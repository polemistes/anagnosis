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
    # the Antigone: made by import_perseus.import_antigone (the first text), now re-established from
    # Jebb's page by the drama route (drama.PLAYS["antigone"]); here for the drama route's merge and
    # sophocles-prose; the old by-eye commands leave it out (OLD_ROUTE_EXCLUDED); its divisions are
    # set when the merge is planned
    Play("antigone", "ant", "tlg002", "Ἀντιγόνη", "Antigone", "III", "1891",
         treebank="tlg0011.tlg002.perseus-grc2.tb.xml", eng="eng2",
         # Jebb's "Structure of the play" (introduction § 5): "ἐπεισόδιον τέταρτον 806-943, beginning
         # with a κομμός, 806-882", "ὑπόρχημα 1115-1154, taking the place of a fifth stasimon",
         # "ἔξοδος 1155-1352, including a κομμός, 1261-1347": the kommoi named as parts of the
         # fourth episode and the exodos (label_parts: "Fourth episode (continued)" after it)
         parts=[(1, "Prologue"), (100, "Parodos"), (162, "First episode"), (332, "First stasimon"),
                (384, "Second episode"), (582, "Second stasimon"), (631, "Third episode"),
                (781, "Third stasimon"), (806, "Fourth episode: kommos"), (883, "Fourth episode"),
                (944, "Fourth stasimon"), (988, "Fifth episode"), (1115, "Hyporcheme"), (1155, "Exodos"),
                # 1347, not his list's 1348: his own text begins the Chorus's closing anapests with
                # the verse numbered 1347 (πολλῷ τὸ φρονεῖν), so the exodos is taken up there
                (1261, "Exodos: kommos"), (1347, "Exodos")]),
    Play("ajax", "aj", "tlg003", "Αἴας", "Ajax", "VII", "1896",
         treebank="tlg0011.tlg003.perseus-grc1.tb.xml",
         # Jebb's "Structure of the play" (introduction): "ἐπεισόδιον πρῶτον, 201—595 (including two
         # κομμοί, 201—262, and 348—429)", "ἐπιπάροδος (866—878), followed by a κομμός (879—973)",
         # "ἐπεισόδιον τέταρτον, 974—1184"
         parts=[(1, "Prologue"), (134, "Parodos"), (201, "First episode: kommos"), (263, "First episode"),
                (348, "First episode: second kommos"), (430, "First episode"), (596, "First stasimon"),
                (646, "Second episode"), (693, "Second stasimon"), (719, "Third episode"),
                (866, "Epiparodos"), (879, "Kommos"), (974, "Fourth episode"), (1185, "Third stasimon"),
                (1223, "Exodos")]),
    Play("electra", "el", "tlg005", "Ἠλέκτρα", "Electra", "VI", "1894",
         treebank="tlg0011.tlg005.perseus-grc2.tb.xml",
         # Jebb's "Structure of the play" (introduction): "ἐπεισόδιον δεύτερον, 516—1057, including a
         # κομμός, 823—870", "ἐπεισόδιον τρίτον, 1098—1383, including a μέλος ἀπὸ σκηνῆς, 1232—1286",
         # "ἔξοδος, 1398—1510, including a κομμός, 1398—1441"
         parts=[(1, "Prologue"), (121, "Parodos"), (251, "First episode"), (472, "First stasimon"),
                (516, "Second episode"), (823, "Second episode: kommos"), (871, "Second episode"),
                (1058, "Second stasimon"), (1098, "Third episode"), (1232, "Third episode: song from the stage"),
                # 1288, not his 1287: his own text gives 1287 (ἇς ἐγὼ … λαθοίμαν) to Electra's song
                (1288, "Third episode"), (1384, "Third stasimon"), (1398, "Exodos: kommos"), (1442, "Exodos")]),
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
                (730, "Second episode"), (827, "Kommos"), (865, "Third episode"), (1081, "Second kommos"),
                (1218, "Exodos")]),
    Play("trachiniae", "trach", "tlg001", "Τραχίνιαι", "Trachiniae", "V", "1892",
         treebank="tlg0011.tlg001.perseus-grc2.tb.xml", eng="perseus-eng3",
         parts=[(1, "Prologue"), (94, "Parodos"), (141, "First episode"), (497, "First stasimon"),
                (531, "Second episode"), (633, "Second stasimon"), (663, "Third episode"),
                (821, "Third stasimon"), (863, "Fourth episode"), (947, "Fourth stasimon"),
                (971, "Exodos")]),
]}

# plays made outside import_play / the old by-eye batches: the default lists of import-sophocles,
# merge-sophocles-apparatus, merge-sophocles-appendix and prepare-sophocles-pages leave them out
OLD_ROUTE_EXCLUDED = {"antigone", "ajax", "electra"}  # Ajax, Electra: the drama route since 2026-11-17

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


def align_part_starts(doc, play: Play, window: int = 6) -> list[str]:
    """Begin each of Jebb's divisions (play.parts) exactly at its first verse: a top-level section
    of the check text's division that begins up to `window` verses before or after the division's
    first verse (the nearest such section, and only where no section begins at that verse already)
    is moved to stand before that verse, with the speaker and stage directions just before it (so
    the lyric sub-section before it ends there too); a section that would then start with a verse
    and no speaker gets the speaker of that verse. Run by merge-drama before label_parts. Returns
    one line per section moved."""
    from .textfmt import Line, Section, Speaker, Stage

    moves: list[str] = []

    def base(n: str) -> int:
        return int(re.match(r"\d+", n).group())

    def first_line(i: int):
        for item in doc.items[i + 1:]:
            if isinstance(item, Line):
                return item
            if isinstance(item, Section) and item.level == 1:
                return None
        return None

    for start, _label in play.parts[1:]:
        items = doc.items
        tops = [(i, first_line(i)) for i, it in enumerate(items) if isinstance(it, Section) and it.level == 1]
        tops = [(i, l) for i, l in tops if l is not None]
        if any(base(l.n) == start for _i, l in tops):
            continue
        # a section that already begins exactly at another division is that division's: never
        # taken (the Ajax: the kommos's section at 879 is not the epiparodos's at 866)
        starts = {s for s, _l in play.parts}
        near = [(abs(base(l.n) - start), i, l) for i, l in tops
                if abs(base(l.n) - start) <= window and base(l.n) not in starts]
        if not near:
            # no top-level section near, but a lyric sub-section of the check text begins at the
            # division's first verse (the Alcestis: the third stasimon 962 inside Perseus's choral
            # section from 861): a top-level section of the enclosing kind begins there
            target = next((k for k, it in enumerate(items) if isinstance(it, Line) and base(it.n) == start), None)
            if target is None:
                continue
            k = target
            while k > 0 and isinstance(items[k - 1], (Speaker, Stage)):
                k -= 1
            enclosing = next((it for it in reversed(items[:k]) if isinstance(it, Section) and it.level == 1), None)
            if enclosing is not None:
                if k > 0 and isinstance(items[k - 1], Section) and items[k - 1].level > 1:
                    k -= 1
                # also where no sub-section begins there (the Ajax's epiparodos 866: the check text's
                # "=== kommos" there is not Jebb's)
                items.insert(k, Section(1, enclosing.kind, ""))
                moves.append(f"section {enclosing.kind} begun at {start} (Jebb's {_label})")
            continue
        _d, si, sline = min(near, key=lambda x: x[0])
        target = next((k for k, it in enumerate(items) if isinstance(it, Line) and base(it.n) == start), None)
        if target is None:
            continue
        # the speaker of the target verse, and where its heading block begins
        speaker = None
        for it in items[:target]:
            if isinstance(it, Speaker):
                speaker = it
        k = target
        # before the speaker and stage lines just before the verse, and before a lyric
        # sub-section that begins at that verse (Medea 131: "=== lyric" opens the parodos)
        while k > 0 and (isinstance(items[k - 1], (Speaker, Stage))
                         or isinstance(items[k - 1], Section) and items[k - 1].level > 1):
            k -= 1
        section = items.pop(si)
        if si < k:
            k -= 1
        items.insert(k, section)
        nxt = k + 1
        while nxt < len(items) and isinstance(items[nxt], Stage):
            nxt += 1
        if nxt < len(items) and isinstance(items[nxt], Line) and speaker is not None:
            items.insert(nxt, Speaker(speaker.name))
        moves.append(f"section {section.kind} moved from {sline.n} to {start} (Jebb's {_label})")
    return moves


def merge_repeated_subsections(doc) -> int:
    """One heading per strophe, antistrophe or epode: Perseus puts each speaker's part of a lyric
    stanza in a division of its own (Philoctetes 1169-1217: "epode" six times), which the check
    text keeps; a sub-section with the same kind and number as the sub-section before it, with no
    other section between, is dropped (its verses stay, under the first). Run by merge-drama with
    label_parts. Returns the number of headings dropped."""
    from .textfmt import Section

    out: list = []
    last = None          # (kind, label) of the last sub-section since the last top-level one
    dropped = 0
    for item in doc.items:
        if isinstance(item, Section):
            if item.level == 1:
                last = None
            elif (item.kind, item.label) == last:
                dropped += 1
                continue
            else:
                last = (item.kind, item.label)
        out.append(item)
    doc.items[:] = out
    return dropped


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
    # a division that simply goes on in the next top-level section (Perseus begins a choral section
    # inside Jebb's parodos at the strophe, the Ajax 172): one section, not a second heading with
    # "(continued)"; its kind is that of the part with more verses, its sub-headings stay
    order = sorted(chosen)
    drop = [b for a, b in zip(order, order[1:]) if chosen[a] == chosen[b]]
    for b in drop:
        a = max(i for i in order if i < b and i not in drop)
        if counts[b][chosen[b]] > counts[a][chosen[a]]:
            doc.items[a].kind = doc.items[b].kind
        counts[a][chosen[a]] += counts[b][chosen[b]]
    for b in drop:
        del chosen[b]
    seen: set[str] = set()
    for i, k in chosen.items():
        # "Exodos: kommos" (a lyric part named inside its division) counts as the division
        # "Exodos" begun, so the episode after it is "Exodos (continued)"
        name = play.parts[k][1]
        base = name.split(":")[0]
        doc.items[i].label = f"{name} (continued)" if name in seen or (":" not in name and base in seen) else name
        seen.update({name, base})
    for b in sorted(drop, reverse=True):
        del doc.items[b]


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
    # the record of the text the trees were made on (syntax_text.py): from the files just written
    from . import syntax_text

    for line in syntax_text.after_merge(slug, texts, sources, lexicon):
        print(line)
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
    return join_footnote_rests([plain_heading(p) if p.startswith("#") else escape_jebb_asterisks(p) for p in paras])


_GREEK_LETTER = re.compile(r"[Ͱ-Ͽἀ-῿]")


def escape_jebb_asterisks(para: str) -> str:
    """Jebb marks a conjecture with an asterisk before the word (*θεῶν, *οὑκ); in the batches'
    markdown `*…*` is italics, so such a mark left bare opens italics that run on to the next
    asterisk ("… Ant.* 360"). A single asterisk directly before a Greek letter that does not
    close an italics span (an even number of single asterisks before it) is Jebb's mark and is
    written \\*; one already escaped, and bold `**`, are left alone."""
    out: list[str] = []
    singles = 0
    pos = 0
    for m in re.finditer(r"\\\*|\*\*|\*", para):
        out.append(para[pos:m.start()])
        tok = m.group()
        if tok == "*":
            if singles % 2 == 0 and _GREEK_LETTER.match(para, m.end()):
                tok = "\\*"
            else:
                singles += 1
        out.append(tok)
        pos = m.end()
    out.append(para[pos:])
    return "".join(out)


_FOOTNOTE_OPEN = re.compile(r"[.!?;:)\]\u2019\u201d]\s*$")


def join_footnote_rests(paras: list[str]) -> list[str]:
    """A footnote run over to the next page stands at that page's foot as a footnote of its own,
    "[Note: sail with Philoctetes, \u2026]": a footnote that begins with a small letter, where the
    footnote before it ends without a stop ("\u2026 And Neoptolemus can propose to]"), is that
    footnote's rest and is joined to it (a divided word joined again)."""
    from .sophocles_pages import join_run_on

    out: list[str] = []
    last: int | None = None      # index in out of the last footnote
    for p in paras:
        if (p.startswith("[Note: ") and p.endswith("]") and re.match(r"\[Note: [a-z]", p) and last is not None
                and not _FOOTNOTE_OPEN.search(out[last][:-1])):
            out[last] = join_run_on(out[last][:-1], p[len("[Note: "):])
            continue
        if p.startswith("[Note:"):
            last = len(out)
        out.append(p)
    return out


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
                text = tmp.read_text(encoding="utf-8")
                for wrong, right in INTRODUCTION_FIXES.get(slug, []):
                    if wrong not in text:
                        print(f"{path.name}: fix not applied, not found: {wrong}")
                    text = text.replace(wrong, right)
                tmp.write_text(range_dash(text), encoding="utf-8")
                print(f"{slug}: {n} sections of the introduction from Perseus")
        add_transcribed_introduction(tmp, transcriptions, play, paras=paras, how=PROSE_HOW)
        os.replace(tmp, path)
    def ff_marks() -> None:
        # Perseus, and the batches, drop Jebb's "f." / "ff." after a note's number; where the
        # scan's own OCR text is at hand (sophocles03soph_djvu.txt) they are put back from it, as
        # the Antigone's old import did (ffmarks.py), before the notes are re-filed
        from .drama import PLAYS as DRAMA
        from .ffmarks import apply_ff_marks
        ocr = sources / "scans" / f"{DRAMA[slug].scan}_djvu.txt" if slug in DRAMA else None
        if ocr is not None and ocr.exists():
            print(f"{slug} commentary: f./ff. marks from the scan's OCR text: "
                  f"{apply_ff_marks(out / 'commentary-jebb.md', ocr)} headings")

    # a play whose commentary is read from Jebb's page (COMMENTARY_FROM_PAGE): the checked notes
    # batches make commentary-jebb.md once they are all checked; until then Perseus's stays
    from_page = slug in COMMENTARY_FROM_PAGE and write_transcribed_commentary(slug, texts, transcriptions, index_dir) > 0
    if from_page:
        ff_marks()
        # what the scan's OCR text did not give, from our own OCR of the commentary's pages
        from .drama import PLAYS as DRAMA
        from .drama_pages import scan_dirs
        from .ffmarks import apply_hocr_marks
        _src, build = scan_dirs(DRAMA[slug].scan)
        hocr = [build / "hocr" / f"leaf_{leaf:04d}.eng.hocr" for a, b in DRAMA[slug].notes_leaves
                for leaf in range(a, b + 1)]
        print(f"{slug} commentary: f./ff. marks from the pages' own OCR: "
              f"{apply_hocr_marks(out / 'commentary-jebb.md', [h for h in hocr if h.exists()])} headings")
    elif write_commentary(slug, sources, texts):
        ff_marks()
    elif not play.commentary:
        # Perseus has no commentary for this play (the Philoctetes): Jebb's, read by OCR
        if write_transcribed_commentary(slug, texts, transcriptions, index_dir) < 0:
            skipped += 1
    refile_commentary(out)
    if from_page:
        file_at_half_lines(out)
    write_translation(slug, sources, texts)
    return skipped


# Plays on sale whose commentary is read whole from Jebb's page by the prose route (kind notes),
# because Perseus's digitisation of it is not his page (authors and titles added or respelt,
# slips): sophocles-prose writes commentary-jebb.md from the notes batches once every one is
# checked, and Perseus's (write_commentary, COMMENTARY_FIXES, jebb_authors.restored) until then
COMMENTARY_FROM_PAGE = {"antigone", "ajax", "electra"}
# how a commentary read from the page was made, for its header, where more is to be said than
# PROSE_HOW
COMMENTARY_HOW = {
    "antigone": "read by OCR and checked against the page images by AI agents, in two readings (2026)",
}


def write_transcribed_commentary(slug: str, texts: Path, transcriptions: Path, index_dir: Path | None = None) -> int:
    """texts/<slug>/commentary-jebb.md from the checked notes batches of the prose OCR route
    (transcriptions/drama/<slug>/notes-NN.md: `## 12` headings, the bold lemma, '+ ' for a note run
    on from the page before), for a play whose commentary Perseus lacks (the Philoctetes), with
    the header lines of the other plays' commentary-jebb.md (title, author, lang, source,
    license); the metrical schemes in metrical signs as write_commentary writes them. Notes on
    lines our numbering lacks are re-filed afterwards by refile_commentary, as for the others.
    Returns the number of notes; 0 when there are no batches, -1 when they are not all checked
    (the file is then left alone)."""
    import os

    from .drama import notes_from_paragraphs
    from .lexicon import _METRE, _METRE_SIGNS
    from .sophocles_pages import SCAN_EDITIONS

    if not any(transcriptions.glob("notes-*.md")):
        print(f"{slug} notes: no batches")
        return 0
    why = unchecked_prose(transcriptions, "notes", index_dir / "notes.json" if index_dir else None)
    if why:
        print(f"{slug} notes: not merged, the batches are not all checked:\n  " + "\n  ".join(why[:20])
              + (f"\n  … and {len(why) - 20} more" if len(why) > 20 else ""))
        return -1
    play = PLAYS[slug]
    notes = notes_from_paragraphs(prose_paragraphs(transcriptions, "notes"))
    md = [f"# title: Commentary on Sophocles: {play.title_en}", "# author: Richard C. Jebb", "# lang: eng",
          f"# source: Sophocles: The Plays and Fragments, {PART_ROMAN[play.part]}: The {play.title_en}, ed. R. C. Jebb, "
          f"Cambridge University Press, {SCAN_EDITIONS[slug]}, {COMMENTARY_HOW.get(slug, PROSE_HOW)}",
          "# license: CC BY-SA 4.0 (transcription; the edition is in the public domain)", ""]
    if len(notes) > 1 and not notes[0][0]:
        # what Jebb prints before the first note's number (the Philoctetes: "Scene:—A lonely place
        # …" before "1—134 Prologue."), under the first heading, as Perseus files the Trachiniae's
        print(f"{slug} notes: put under ## {notes[1][0]}, before its note: {' '.join(notes[0][1])[:80]}")
        notes = [(notes[1][0], notes[0][1] + notes[1][1])] + notes[2:]
    joined: list[tuple[str, list[str]]] = []
    for heading, body in notes:
        # Jebb's "927 ff." (a general note) and "927 πῦρ" next to it are both `## 927`: one note,
        # its paragraphs in the print's order (as further lemmas on one verse are)
        if joined and heading and joined[-1][0] == heading:
            joined[-1] = (heading, joined[-1][1] + body)
        else:
            joined.append((heading, body))
    notes = joined
    count = 0
    for heading, body in notes:
        if not heading:
            print(f"{slug} notes: text without a heading, left out: {' '.join(body)[:80]}")
            continue
        md += [f"## {heading}"] + [x for p in body for x in (p, "")]
        if not body:
            md.append("")
        count += 1
    text = _METRE.sub(lambda m: m.group(1).translate(_METRE_SIGNS), "\n".join(md).rstrip("\n") + "\n")
    # the OCR's ᾽ (koronis sign) for Jebb's elision and prodelision mark: ’, as the brief says
    text = text.replace("\u1fbd", "\u2019")
    path = texts / slug / "commentary-jebb.md"
    tmp = path.with_name(path.name + ".part")
    tmp.write_text(text, encoding="utf-8")
    os.replace(tmp, path)
    print(f"wrote {path}: {count} notes from the transcribed batches")
    return count


def jebb_translation(play: Play, sources: Path):
    """Jebb's translation from Perseus as a Document (the eng-jebb.txt import_play writes), with
    the stage directions Perseus sets inside a verse's <l> made stage directions of their own
    (after the segment), the space Perseus's <milestone/> stood for kept, and TRANSLATION_FIXES."""
    from .import_perseus import tei_to_document

    path = sources / sources_for(play)["eng"]
    doc = tei_to_document(path, {
        "title": play.title_en, "translator": "Richard C. Jebb", "lang": "eng",
        "source": f"urn:cts:greekLit:tlg0011.{play.tlg}.{play.eng}",
        "edition": f"Sophocles: The Plays and Fragments, {PART_ROMAN[play.part]}: The {play.title_en}, tr. R. C. Jebb, Cambridge; modernized by Perseus",
        "license": "CC BY-SA 4.0",
    })
    split_translation_stages(doc, path)
    fixes = TRANSLATION_FIXES.get(play.slug, [])
    from .textfmt import Line
    for it in doc.items:
        if isinstance(it, Line):
            for wrong, right in fixes:
                it.text = it.text.replace(wrong, right)
    return doc


# Perseus's English: words run together in its own file (no space after the comma)
TRANSLATION_FIXES: dict[str, list[tuple[str, str]]] = {
    "philoctetes": [("Hush,boy!", "Hush, boy!"), ("the pain,the misery", "the pain, the misery"),
                    ("will help,then", "will help, then")],
}


def split_translation_stages(doc, path: Path) -> list[str]:
    """In Perseus's TEI a stage direction may stand inside the verse's <l> after the words ("…
    nothing anymore! <stage>Exit Philoctetes into the cave.</stage>"), which tei_to_document runs
    into the segment; and a <milestone/> between two sentences is dropped without the space it
    stood for ("worse.Why"). Each such stage direction becomes a Stage after its segment; the
    space is put back. Changes the Document in place; returns one line per change."""
    from lxml import etree

    from .import_perseus import _inline_text, _local
    from .textfmt import Line, Stage

    stages: dict[str, list[str]] = {}
    joins: dict[str, list[tuple[str, str]]] = {}
    for el in etree.parse(str(path)).iter():
        if not isinstance(el.tag, str) or _local(el) != "l":
            continue
        n = el.get("n")
        for child in el:
            if not isinstance(child.tag, str):
                continue
            if _local(child) == "stage":
                stages.setdefault(n, []).append(_inline_text(child))
            elif _local(child) == "milestone":
                prev = child.getprevious()
                before = (prev.tail if prev is not None else el.text) or ""
                after = child.tail or ""
                if before and after and not before[-1].isspace() and not after[0].isspace():
                    joins.setdefault(n, []).append((before.split()[-1], after.split()[0]))
    changes: list[str] = []
    out: list = []
    for it in doc.items:
        out.append(it)
        if not isinstance(it, Line):
            continue
        for a, b in joins.get(it.n, []):
            if a + b in it.text:
                it.text = it.text.replace(a + b, f"{a} {b}", 1)
                changes.append(f"translation {it.n}: space put back in {a}{b}")
        for text in stages.get(it.n, []):
            if text and it.text.rstrip().endswith(text):
                it.text = it.text.rstrip()[:-len(text)].rstrip()
                out.append(Stage(text))
                changes.append(f"translation {it.n}: stage direction set apart: {text}")
    doc.items[:] = out
    return changes


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
    # the Chorus's κέρδη παραινεῖς … 1326 (Perseus 1325; the rule had given it Creon's 1324)
    "antigone": {"1325": "1326"},
    # Tecmessa's ὤμοι· κεῖθεν κεῖθεν … 233 (Perseus 231, a verse of the Chorus in Jebb's numbering)
    "ajax": {"231": "233"},
    "electra": {
        # read beside the Greek, each segment to the verse its speaker's words begin (2026-11-17):
        # ἀπολεῖς 831 (Electra), πῶς; 831a (Chorus)
        "830a": "831", "831": "831a",
        # the recognition: ψεῦδος οὐδὲν 1220a, ἦ ζῇ γὰρ ἁνήρ; 1221, εἴπερ ἔμψυχος 1221a, ἦ γὰρ σὺ
        # κεῖνος; 1222, τήνδε προσβλέψασα 1222a (Perseus counts each half a verse late)
        "1221": "1220a", "1221a": "1221", "1222": "1221a", "1222a": "1222", "1223": "1222a",
        # the second speaker's part of a shared verse (the rule would take the plain number)
        "1323a": "1323a", "1477a": "1477a", "1483a": "1483a", "1502a": "1502a", "1502b": "1502b",
        # the murder and the kommos: Jebb's lines here cover two of Perseus's numbers
        "1408": "1409", "1409": "1410", "1410": "1410a", "1411a": "1411a", "1417": "1416a",
        "1418": "1417", "1420": "1419", "1427": "1426a", "1429": "1428", "1431": "1431a",
        "1436": "1435a", "1437": "1436", "1438": "1436a", "1439": "1437", "1440": "1439",
        "1442": "1442",
    },
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
    "philoctetes": {
        # parodos: λέγʼ ὅ τι 210a (Neoptolemus), φροντίδας νέας· ὡς οὐκ ἔξεδρος … 210b (Perseus
        # counts the parts of the shared verse 210, 211, 212)
        "211": "210a", "212": "210b",
        # ποίου δὲ τούτου … Ὀδυσσέως ἐρεῖς; is 441, Philoctetes's answer 442 (Perseus 440, 441)
        "440": "441", "441": "442",
        # the second speaker's part of a shared verse whose first part Perseus files under the
        # segment before (so no plain number, and the rule would take "a" for the first part):
        # καὶ σέ γʼ εἰσάξω 674a, πῶς οὐκ οἶσθα 754a, ἰὼ ἰὼ δύστηνε σύ 759a, τὴν ἁμαρτίαν 1248a,
        # παῦε, μὴ λέξῃς πέρα 1275a, πάντα γὰρ φράσεις μάτην 1280a, μὴ ʼπεύξῃ πέρα 1286a, σάφʼ
        # ἴσθι 1296a
        "674a": "674a", "754a": "754a", "759a": "759a", "1248a": "1248a", "1275a": "1275a",
        "1280a": "1280a", "1286a": "1286a", "1296a": "1296a",
        # ἆ ἆ ἆ ἆ 732 (Philoctetes), τί ⟨δʼ⟩ ἔστιν; 733, οὐδὲν δεινόν 733a (Perseus 731-733)
        "731": "732", "732": "733", "733": "733a",
        # λεύσσων δʼ ὅπου … προσενώμα ("but ever directed his path …") is 716
        "715": "716",
        # πότμος, ⟨πότμος⟩ σε δαιμόνων 1116 (the Chorus; Perseus 1115)
        "1115": "1116",
        # epode of the second kommos: τί τοῦτʼ ἔλεξας; 1173, εἰ σὺ τὰν ἐμοὶ 1173a; ὦ ξένοι, μείνατε
        # 1185, τί θροεῖς; 1185a; ποῖον ἐρεῖς τόδʼ ἔπος; 1204, ξίφος 1204a; τί ποτε; 1210, πατέρα
        # ματεύων 1210a (Perseus counts each a verse earlier)
        "1172": "1173", "1173": "1173a", "1184": "1185", "1185": "1185a",
        "1203": "1204", "1204": "1204a", "1209": "1210", "1210": "1210a",
        # Odysseus's "…" for the verse lost after 1251 (Jebb prints no verse)
        "1251a": None,
        # Heracles's μήπω γε 1409 (Perseus 1408)
        "1408": "1409",
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


# Plays whose commentary gives Jebb's italics to the Latin Perseus marks (commentary._latin;
# 2026-11-17, the three on sale, their fix tables written against the italics); the others get it
# at their next merge (their fix tables match the text as imported without it)
LATIN_ITALICS = {"ajax", "electra"}  # the Antigone: read from the page, its batches carry the italics


def import_options(play: Play) -> dict:
    """The switches write_commentary gives commentary.import_jebb_commentary for a play."""
    return {"latin_italics": play.slug in LATIN_ITALICS}


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
            "source": perseus_source(play), "license": "CC BY-SA 3.0 US"}, **import_options(play))
    except SystemExit as e:  # the file holds no commentary
        tmp.unlink(missing_ok=True)
        print(f"{src.name}: {e}; {path.name} left as it is")
        return 0
    text = range_headings(tmp.read_text(encoding="utf-8"))
    for wrong, right in COMMENTARY_FIXES.get(slug, []):
        if wrong not in text:
            print(f"{path.name}: fix not applied, not found: {wrong}")
        text = text.replace(wrong, right)
    # the authors' names that dropped out of Perseus's file before titles, read on Jebb's page
    # (jebb_authors.py: the answered job files transcriptions/sophocles/<slug>/authors-NN.tsv)
    from .jebb_authors import restored
    # the authors' names restored on Perseus's text (jebb_authors); not reached for a play whose
    # commentary is read from the page once its batches are checked (write_prose)
    names = restored(slug, sources)
    for wrong, right in names:
        if text.count(wrong) != 1:
            print(f"{path.name}: author's name not restored, the words stand {text.count(wrong)} times: {wrong}")
            continue
        text = text.replace(wrong, right)
    if names:
        print(f"{path.name}: {len(names)} authors' names restored before titles")
    text = length_signs_over(range_dash(text))
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


_RANGE_DASH = re.compile(r"(\d)([—–]) (\d)")


def range_dash(text: str) -> str:
    """No space after the dash of a range of numbers (Perseus: "1670— 1750", Jebb: 1670—1750)."""
    return _RANGE_DASH.sub(r"\1\2\3", text)


# Perseus's introduction (import_introduction) where it is not what the page prints
INTRODUCTION_FIXES: dict[str, list[tuple[str, str]]] = {
    "trachiniae": [
        # Perseus's "<*>" (imported as "[?]"): Plutarch's εἶτα … εἶδος (De prof. in virt. 7), and two
        # English places whose letters the sense leaves no doubt about
        ("ε[?]τα τὸ πικρὸν", "εἶτα τὸ πικρὸν"), ("ε[?]δος ὅπερ", "εἶδος ὅπερ"),
        ("some epic[?] which", "some epic in which"), ("mind of Heracle[?]. The", "mind of Heracles. The"),
    ],
}


# Perseus's commentary where it is not what the page prints, put right before the vowel-length and
# metrical signs are converted (write_commentary): (Perseus's text as imported, the page's)
COMMENTARY_FIXES: dict[str, list[tuple[str, str]]] = {
    "trachiniae": [
        # Perseus's "<*>" (imported as "[?]"): what its keyers could not read, every one read on the
        # page (leaves 81-253, two columns under the rule), with the other slips of the same notes
        # (zerb, inder, cioth, ἱεροί, dial gue, ναιετάονρες, προv-ι for verb, under, cloth, ἱεροῦ,
        # dialogue, ναιετάοντες, προϝ-ι) and the run of tags Perseus left as text in the note on 143
        ('α[?]νός τις', 'αἶνός τις'),
        ('**[?]λγιστον**', '**ἄλγιστον**'),
        ('Ἀχελῷοσ[?] δὲ', 'Ἀχελῷος δὲ'),
        ('οὐδέ π[?] λήξαντʼ', 'οὐδέ πω λήξαντʼ'),
        ('πλὴν [?] κύριος | Θησε[?] παρέστω', 'πλὴν ὁ κύριος | Θησεὺς παρέστω'),
        ('*ὠδῖνας*: cp. [?]25.', '*ὠδῖνας*: cp. 325.'),
        ('**αὑτοῦ**, [?]ctive gen.', '**αὑτοῦ**, objective gen.'),
        ('πατρὸς...ο[?]κτο[?] (', 'πατρὸς...οἶκτον ('),
        ('*[?]οῦ* is clearly right: the h[?]shness of **αὐτ[?]**', '*αὐτοῦ* is clearly right: the harshness of **αὐτοῦ**'),
        ('supposing that, [?]stead of it', 'supposing that, instead of it'),
        ('ἄλλοις [?]έντε**', 'ἄλλοις πέντε**'),
        ('the [?]acle at Dodona had told Heracles th[?]. at the end', 'the oracle at Dodona had told Heracles that, at the end'),
        ('he [?]ould have rest. Fifteen months befo[?] this', 'he should have rest. Fifteen months before this'),
        ('given Deian[?] the δέλτος on which h[?] had written [?]own that', 'given Deianeira the δέλτος on which he had written down that'),
        ('[?]e had then to[?] her', 'He had then told her'),
        ('return at the [?] of fifteen', 'return at the end of fifteen'),
        ('assume th[?] he was dead (164 ff.)[?]', 'assume that he was dead (164 ff.).'),
        ('to announ[?] his approach', 'to announce his approach'),
        ('tidings of [?]im.', 'tidings of him.'),
        ('ponders the [?]cle, her grave misgiving (43) becomes [?]rtitude.', 'ponders the oracle, her grave misgiving (43) becomes certitude.'),
        ('in dial gue without', 'in dialogue without'),
        ('rejection of vv[?] 44—48', 'rejection of vv. 44—48'),
        ('conjecture [?].—', 'conjecture σοί.—'),
        ('**ἀγεννή[?]ων**', '**ἀγεννήτων**'),
        ('**πα[?]ς** is that', '**παῖς** is that'),
        ('(1) **[?]ν**, not **ἂν**', '(1) **ἐν**, not **ἂν**'),
        ('σφραγῖδα φύλασ[?] [?]ν ἐπὶ δέλτῳ', 'σφραγῖδα φύλασσʼ, ἣν ἐπὶ δέλτῳ'),
        ('ἐπεικάζω is [?] to ‘enter upon’', 'ἐπεικάζω is strictly, to ‘enter upon’'),
        ('ἐπινοῶ: [?] ἀπεικάζω', 'ἐπινοῶ: while ἀπεικάζω'),
        ('is rath[?] throw off,’', 'is rather ‘to throw off,’'),
        ('a guess,—ἀπ[?] [?]ing used', 'a guess,—ἀπό being used'),
        ('**θυμοφ[?]**, from', '**θυμοφθορῶ**, from'),
        ("**μήτ' [?]θοις … νῦν δʼ ἄπειρος εἶ**: i.e., ‘mayest [?] remain ignorant,—as thou now art [?] the combination of a wish with a fact [?] 582 ff.", "**μήτ' ἐκμάθοις … νῦν δʼ ἄπειρος εἶ**: i.e., ‘mayest thou remain ignorant,—as thou now art.’ For the combination of a wish with a fact, cp. 582 ff."),
        ('has [?] authority than', 'has better authority than'),
        ('Greek express[?] had a pervading bent towards antith[?] and this tendency sometimes asserted [?] after a sentence had begun in the [?]actic’ form.', 'Greek expression had a pervading bent towards antithesis, and this tendency sometimes asserted itself after a sentence had begun in the ‘paratactic’ form.'),
        ('sprang [?] the thought, ‘you may, indeed, know [?] the future', 'sprang from the thought, ‘you may, indeed, know in the future'),
        ('you do [?]’ I therefore', 'you do not.’ I therefore'),
        ('Each trad[?]nal instance', 'Each traditional instance'),
        ('should be care[?] weighed', 'should be carefully weighed'),
        ('**τ[?] νεάζον** κ.τ.λ.', '**τὸ γὰρ νεάζον** κ.τ.λ.'),
        ('before changing δέ to τε. [?] 285 f. Ant., 333 f. Ant., 1151 ff.: *Ant.* 1096, *P*<*\\*>12 f.*<*\\*> and for the negative*<*quote lang=greek>mh/te*<*/quote> followed by*<*quote lang=greek>de/*<*/quote>,*<*title>O. C.* 421 f.', 'before changing δέ to τε. Cp. 285 f., 333 f., 1151 ff.: *Ant.* 1096, *Ph.* 1312 f.: and for the negative μήτε followed by δέ, *O. C.* 421 f.'),
        ('simple and clear[?] but', 'simple and clear; but'),
        ('etc., [?]σχω is more usual', 'etc., ἀνίσχω is more usual'),
        ('καὶ καρπ[?] τούτων', 'καὶ καρπῶν τούτων'),
        ('πρόσοδος ἀναλ[?] σκηται', 'πρόσοδος ἀναλίσκηται'),
        ('συντελουμέν[?] θυσίας', 'συντελουμένας θυσίας'),
        ('τοῦ ἱεροί συντείνοντα', 'τοῦ ἱεροῦ συντείνοντα'),
        ('μαντείας**: [?] may have vowed', 'μαντείας**: he may have vowed'),
        ('bright praise[?] seen', 'bright praises seen'),
        ('cp. 1127 [?] *O. C.* 332 f.', 'cp. 1127: *O. C.* 332 f.'),
        ('cp. *O. C.* 35 [?]', 'cp. *O. C.* 35 n.'),
        ('*Ant.* 764 ἐν [?] ὁρῶν', '*Ant.* 764 ἐν ὀφθαλμοῖς ὁρῶν'),
        ('schol. [?] εἰσὶ δεσπότου', 'schol. ἀντὶ τίνος εἰσὶ δεσπότου'),
        ('*sc.* τὸ [?] χαίρειν', '*sc.* τὸ ἐμὲ χαίρειν'),
        ('sense of the zerb', 'sense of the verb'),
        ('Not (as [?]ood)', 'Not (as Linwood)'),
        ('but [?]ls a certain sadness', 'but feels a certain sadness'),
        ("δέδοικ' [?]γὼ", "δέδοικ' ἐγὼ"),
        ('makest me to [?]lt', 'makest me to halt'),
        ('602 ο[?]δεν τό γʼ α[?]σχρὸν', '602 οἶδεν τό γʼ αἰσχρὸν'),
        ('[?]κείνης διδακτά', '| κείνης διδακτά'),
        ('ἐστίν, [?] ἰοὺς ὕδρα', 'ἐστίν, ᾧ ἰοὺς ὕδρα'),
        ('blood with a cioth', 'blood with a cloth'),
        ('πολιουρκούμενοι...ε[?]τα', 'πολιουρκούμενοι...εἶτα'),
        ('all that he said’[?] as if', 'all that he said’: as if'),
        ('is rather an a[?].): but *Phaedr.*', 'is rather an aor.): but Plat. *Phaedr.*'),
        ('‘too soon[?] ( Aesch.', '‘too soon’ (Aesch.'),
        ('πρω-ί is prob. for προv-ι', 'πρω-ί is prob. for προϝ-ι'),
        ('Second στ[?]ον.', 'Second στάσιμον.'),
        ('1st an[?] 640', '1st antistr., 640'),
        ('For the [?]res see', 'For the metres see'),
        ('will presen[?] be heard by the dwellers around Tr[?]s. The victorious Heracles will soon [?]rn, filled with new love for Deianeira, inder the spell', 'will presently be heard by the dwellers around Trachis. The victorious Heracles will soon return, filled with new love for Deianeira, under the spell'),
        ('highlands ([?]ους Οἴτας)', 'highlands (πάγους Οἴτας)'),
        ('the wa[?]m springs', 'the warm springs'),
        ('(**να[?]λοχα**)', '(**ναύλοχα**)'),
        ('locally called χ[?]ροι', 'locally called χύτροι'),
        ('*sc.* ναιετάονρες', '*sc.* ναιετάοντες'),
        ('οἱ ἄλλοι [?]ρσαι', 'οἱ ἄλλοι Πέρσαι'),
        ('λί[?]ναν*', 'λίμναν*'),
        ('the deep [?] which it forms', 'the deep recess which it forms'),
        ('*O.* 2. 13 [?] Κρόνιε', '*O.* 2. 13 ὦ Κρόνιε'),
        ('*Pers.* 25 σοῦν[?] ται', '*Pers.* 25 σοῦνται'),
        ('no nearer [?]arallel', 'no nearer parallel'),
        ('(like [?]θλα)', '(like ἆθλα)'),
        ('As γένοιτο [?]=‘it might', 'As γένοιτο ἂν=‘it might'),
        ('μὴ ματαία [?]ν γένοιτο', 'μὴ ματαία ἂν γένοιτο'),
        ('τὴν ἐξ ἐμο[?] δυσβουλίαν', 'τὴν ἐξ ἐμοῦ δυσβουλίαν'),
        ('Here [?]ὰ ἐκεῖθεν is not merely τ[?] ἐκεῖ', 'Here τὰ ἐκεῖθεν is not merely τὰ ἐκεῖ'),
        ('*from* (or [?]) his side', '*from* (or *on*) his side'),
        ('ἐμοῦ.—*[?]θούμεθα*', 'ἐμοῦ.—*ποθούμεθα*'),
        ('οἰστρηθε[?]ς Διονύσῳ', 'οἰστρηθεὶς Διονύσῳ'),
        ('τὰ ὀχήματα, τά τ[?] πεζὰ', 'τὰ ὀχήματα, τά τε πεζὰ'),
        ('ὥσπερ [?]ν=*dummodo*', 'ὥσπερ ἂν=*dummodo*'),
        ('ἀμφίθρεπτον α[?]μα', 'ἀμφίθρεπτον αἷμα'),
        ('Ἀχελῷος καὶ Ἡρ[?]κλῆς', 'Ἀχελῷος καὶ Ἡρακλῆς'),
        ('Then Heracles, [?]ning to', 'Then Heracles, turning to'),
        ('**δν οὐχ ο[?]όν τε**', '**ὃν οὐχ οἷόν τε**'),
        ('Σοφοκλῆς (fr. 822)[?] λύσω', 'Σοφοκλῆς (fr. 822)· λύσω'),
        ('γνώμας μολόν[?]) [?]ought', 'γνώμας μολόντʼ ought'),
        ('the secre[?] villainy', 'the secret villainy'),
        ('in the [?]eadly grip', 'in the deadly grip'),
        ('the robe. Thi[?] very trait', 'the robe. This very trait'),
        ('κινεῖ γὰρ ἁνὴρ [?] κἀνάγει κάρα.—Wecklein, omitting [?] takes', 'κινεῖ γὰρ ἁνὴρ ὄμμα κἀνάγει κάρα.—Wecklein, omitting **θʼ**, takes'),
        ('a certain standard, [?]s with εἰς', 'a certain standard, is with εἰς'),
        ('gain to seafarers. [?] I hesitate', 'gain to seafarers. I hesitate'),
        ('protasis is εἰ μὴ [?]ης', 'protasis is εἰ μὴ δοίης'),
        ('*O.T.* 13[?] n.', '*O.T.* 1376 n.'),
        ('on a[?] count of', 'on account of'),
        ('εὐτυχὴς δοκεῖ ε[?]ναι', 'εὐτυχὴς δοκεῖ εἶναι'),
        ('in accor[?]nce with', 'in accordance with'),
        ('ἐναριζο[?]ένα', 'ἐναριζομένα'),
        ('ὦ χρόνιος ἐ[?]θὼν', 'ὦ χρόνιος ἐλθὼν'),
        ('prose-write[?] would', 'prose-writer would'),
        ('Heracleid [?]escent', 'Heracleid descent'),
        ('(τ[?] ἐμῆς φρενός', '(τῆς ἐμῆς φρενός'),
        ('παρελθὼν [?]μματος', 'παρελθὼν ὄμματος'),
        ('λελωφήκα[?]εν', 'λελωφήκαμεν'),
        ('my father[?]s,’', "my father's,’"),
        ('φύλασσʼ, [?]ν ἐπὶ δέλτῳ', 'φύλασσʼ, ἣν ἐπὶ δέλτῳ'),
        ("οἷός τ' ε[?]ναι", "οἷός τ' εἶναι"),
        ("(L's re[?]ding)", "(L's reading)"),
        ('Ἀχαιῶν, ο[?]δα,', 'Ἀχαιῶν, οἶδα,'),
        ('ἐν κακοῖσιν ο[?]δὲν', 'ἐν κακοῖσιν οὐδὲν'),
        ('gloss on το[?]ε.', 'gloss on τοῦδε.'),
        ('adjecti[?] which', 'adjectives which'),
        ('καθέλοι νιν α[?]ν πότμον', 'καθέλοι νιν αἰὼν πότμον'),
        ('ταλαιπ[?]ρῶν', 'ταλαιπωρῶν'),
        ('**θ[?]μα**', '**θαῦμα**'),
        ('Dindo[?]f formerly', 'Dindorf formerly'),
        ('ἐκνενε[?] μένος', 'ἐκνενευρισμένος'),
        ('ἀνῇ νό[?]ος', 'ἀνῇ νόσος'),
        ('only i[?] he abhors', 'only if he abhors'),
        ('βουκ[?]λήσας', 'βουκολήσας'),
        ('441 [?]αῦτʼ ὀνείδιζʼ', '441 τοιαῦτʼ ὀνείδιζʼ'),
        ('πε[?]σομαι δέ', 'πείσομαι δέ'),
        ('εἰσιέν[?].', 'εἰσιέναι.'),
        ('thou comest [?]hither', 'thou comest thither'),
        ('*γεν[?]ῦ*', '*γενοῦ*'),
        ('τὸ σὸν ἔ[?]ον', 'τὸ σὸν ἔργον'),
        # note 418: the italics of the conjecture "κάτοισθα δῆτʼ;—οὔ φημί" doubled into "**" (a stray
        # asterisk that ran the italics on)
        ("*δῆτʼ**;*—*οὔ*", "*δῆτʼ;*—*οὔ*"),
    ],
    "oedipustyrannus": [
        # leaf 191, note on 640 (synizesis of υ): the bar stands over both vowels (υ͞ω), not
        # over the υ as a macron (Perseus: genu/&macr;wn)
        ("γενύ¯ων", "γενύ͞ων"), ("ἡδύ¯οσμον", "ἡδύ͞οσμον"), ("Ἐρινύ¯ων", "Ἐρινύ͞ων"),
        ("Ἠλεκτρύ¯ωνος", "Ἠλεκτρύ͞ωνος"),
        # leaf 127, note on 118 f.: "χωρὶς τοῦ ῑ...ἡ μέντοι παράδοσις ἔχει τὸ ῑ." (Perseus: the
        # second ῑ without its mark)
        ("ἡ μέντοι παράδοσις ἔχει τὸ ι.", "ἡ μέντοι παράδοσις ἔχει τὸ ῑ."),
        # Perseus's Betacode read wrongly, leaving a stray asterisk that opens italics: its "(" and
        # ")" (Jebb's brackets) taken for breathings and "*" (a capital) left bare: note 472 Hes.
        # Th. 217 "(Νὺξ) καὶ Μοίρας"; 1463 Arndt's ἄλλη for ἡμή "(Λ for Μ)"; 1525 "Kontos (Λόγιος
        # Ἑρμῆς p. 61)", "(or ᾔδειν)"; and two words broken: 510 Plat. Theaet. 179 D "ὦ φίλε
        # Θεόδωρε", 772 Dem. 19. 248 "τῆς πόλεως"
        ("*ʽνὺξʼ καὶ Μοίρας", "(Νὺξ) καὶ Μοίρας"), ("*ʽλΛ for M)", "(Λ for Μ)"),
        ("Kontos *ʽλόγιος Ἑρμῆς p. 61)", "Kontos (Λόγιος Ἑρμῆς p. 61)"), ("(or ᾔδεινʼ.", "(or ᾔδειν)."),
        ("ὦ φλ* ́ʼε Θεόδωρε", "ὦ φίλε Θεόδωρε"), ("τῆς π*|ολεως", "τῆς πόλεως"),
    ],
    "electra": [
        # a breathing Perseus left out (note on 1485): ἐξ ἀρχῆς
        ('κακὸν ὲξ ἀρχῆς', 'κακὸν ἐξ ἀρχῆς'),
        # Pind. P. 3. 24 (note on 1427): Jebb prints the digamma, ἀϝάταν (leaf 286, read 2026-11-17)
        ('μεγάλαν ἀvάταν', 'μεγάλαν ἀϝάταν'),
        # Perseus's o=io/llusai (the lemma of 141) for dio/llusai
        ('**ο ͂ιόλλυσαι**', '**διόλλυσαι**'),
        # Perseus's "<*>" (imported as "[?]"), read on Jebb's page (1894, scan sophoclesplaysfr06soph;
        # 2026-11-17): 51 of the 76; the rest still to read (build/logs/sophocles-on-sale-fixes.md)
        ('... [?]λευθέρωσε ...', '... ἠλευθέρωσε ...'),
        ('τὰ παρόν[?]) have prompted', 'τὰ παρόντʼ have prompted'),
        ('οὐ λανθάνε[?] με ἀλλʼ', 'οὐ λανθάνει με ἀλλʼ'),
        ("οὐ λάθει μ' [?]ν δεῖ", "οὐ λάθει μ' ὧν δεῖ"),
        ('παῦσαι· κρα[?]εῖς τοι', 'παῦσαι· κρατεῖς τοι'),
        ('(*sc.* [?]ησι)', '(*sc.* ἔῃσι)'),
        ('τόνδε to π[?]λιν', 'τόνδε to πόλιν'),
        ('fr. 658 [?] πρῷρα', 'fr. 658 ὦ πρῷρα'),
        ('αὐθέντης, u[?]ed by', 'αὐθέντης, used by'),
        ('**ἦ τ[?]ν**, or', '**ἦ τἂν**, or'),
        ('μηδὲν α[?]τόν:', 'μηδὲν αὐτόν:'),
        ('*Ph.* 565 η[?] ταῦτα', '*Ph.* 565 ἦ ταῦτα'),
        ('**τίνα … τόνδʼ**[?] cp.', '**τίνα … τόνδʼ**: cp.'),
        ('τίνʼ εἶπας, [?] γεραιέ', 'τίνʼ εἶπας, ὦ γεραιέ'),
        ('ὀρύγματα ο[?] ͂νον', 'ὀρύγματα οἶνον'),
        ('=σῳζόμενα [?].', '=σῳζόμενα ἦ.'),
        ('κεφαλῇ [?]ναμάξεις', 'κεφαλῇ ἀναμάξεις'),
        ('Ἄτην τʼ, [?]ρινύν', 'Ἄτην τʼ, Ἐρινύν'),
        ('τὸν ο[?]κον (*i.e.*', 'τὸν οἶκον (*i.e.*'),
        ('τῶν ἐμ[?]ν, and', 'τῶν ἐμῶν, and'),
        ('instead of [?]δʼ εἶχε', 'instead of ὧδʼ εἶχε'),
        ('*Ph.* 243 [?] τοῦ γέροντος', '*Ph.* 243 ὦ τοῦ γέροντος'),
        ('*Ant.* 488 οὐ[?] ἀλύξετον', '*Ant.* 488 οὐκ ἀλύξετον'),
        ('kinds), ο[?] μὲν παλαιοὶ', 'kinds), οἱ μὲν παλαιοὶ'),
        ('(for κακά) ο[?]ς ἐγὼ', '(for κακά) οἷς ἐγὼ'),
        ('offspring o[?] her', 'offspring of her'),
        ('**πρέπ[?] γὰρ**', '**πρέπει γὰρ**'),
        ('συλλαβὼν [?]ρῶ:', 'συλλαβὼν ἐρῶ:'),
        ('πῶς ε[?]πας which', 'πῶς εἶπας which'),
        ('ἤδη Λά[?]ον πάλαι', 'ἤδη Λάιον πάλαι'),
        ('*Achaeans*’[?] *Il.* 2. 684)', '*Achaeans*’ (*Il.* 2. 684)'),
        ('τελοῦντ[?]ες (‘doing’)', 'τελοῦντες (‘doing’)'),
        ('αὖ ο[?]τως ἄπορος', 'αὖ οὕτως ἄπορος'),
        ("ὄλετ' ἐ[?] Θήβῃσι", "ὄλετ' ἐν Θήβῃσι"),
        ('νῦ[?] δέ μιν', 'νῦν δέ μιν'),
        ('ἔρχεται [?]να ἴδῃ', 'ἔρχεται ἵνα ἴδῃ'),
        ('σμικρὸς [?] καιρός', 'σμικρὸς ὁ καιρός'),
        ('δὲ φρά[?] [?]ράς τʼ', 'δὲ φράστοράς τʼ'),
        ('τοῖς [?]λλοις ἡμῖν', 'τοῖς ἄλλοις ἡμῖν'),
        ('ἦμαρ, [?]διστος', 'ἦμαρ, ἥδιστος'),
        ('258 [?]γʼ ἔχοντες', '258 σῖγʼ ἔχοντες'),
        ('σῴζε[?]θαί σ`ʼ ἐκέλευσʼ', 'σῴζεσθαί σʼ ἐκέλευσʼ'),
        ('1040 μ[?] τεῖνε', '1040 μὴ τεῖνε'),
        ('**[?]δε**, as thou', '**ὧδε**, as thou'),
        ('sense of [?]δε for', 'sense of ὧδε for'),
        ('274 ε[?] ξυντυχόντων', '274 εὖ ξυντυχόντων'),
        ('80 [?]ξεδροι', '80 ἔξεδροι'),
        ('οὐκ [?]παμβλυνεῖς', 'οὐκ ἀπαμβλυνεῖς'),
        ('ἔκλυες, [?], |', 'ἔκλυες, ὦ, |'),
        ('γαίης | [?]χετʼ', 'γαίης | ᾤχετʼ'),
        ('etc.), [?]ντιθυρὼν', 'etc.), ἀντιθυρὼν'),
        # the rest, read on the page (leaves 131-295); the note on 603 (Whitelaw's version, ‘O[?]) stays
        # unread: the letter after O is cut off at the page's edge in this scan (leaf 184)
        ('*Hipp.* 337 ο[?]ον, μῆτερ', '*Hipp.* 337 οἷον, μῆτερ'),
        ('δαίμων was there, wor[?]ng out', 'δαίμων was there, working out'),
        ('*M.* 1. 3. 9 ε[?]ναι τῶν', '*M.* 1. 3. 9 εἶναι τῶν'),
        ('rash, then, to asser[?] that', 'rash, then, to assert that'),
        ('in the vault (3[?]1).', 'in the vault (381).'),
        ('κλύουσαν ο[?]κτον.', 'κλύουσαν οἶκτον.'),
        ('τοὺς πέλας ψ[?]γε ἡμᾶς', 'τοὺς πέλας ψέγε ἡμᾶς'),
        ('Cp. *[?]r.* 1236 f.', 'Cp. *Tr.* 1236 f.'),
        ('calls u[?]n the virgin', 'calls upon the virgin'),
        ('as guilty [?] unmaidenly', 'as guilty of unmaidenly'),
        ('As Arist. say[?] ( Arist. *Rhet.*', 'As Arist. says (*Rhet.*'),
        ('Cp. 13 [?] τὸν ἄσκοπον', 'Cp. 1315: *Tr.* 246 τὸν ἄσκοπον'),
        ('οὐ φαι[?]νετο πάσης', 'οὐ φαίνετο πάσης'),
        ('57 πυρὰ[?] τάφον', '57 πυρὰν τάφον'),
        ('*Ph.* 442, ο[?] τοῦτον', '*Ph.* 442, οὐ τοῦτον'),
        ("ὅτ' ο[?]ν ἐκεῖνοι", "ὅτ' οὖν ἐκεῖνοι"),
        ('**μ[?] ʼξέλη**', '**μὴ ʼξέλη**'),
        ('part of an [?]ξάγγελος', 'part of an ἐξάγγελος'),
        ('| [?]ζηλα νίκης', '| ἄζηλα νίκης'),
        ('οὐκ ἐκτὸς ἄψο[?]ρον [?]κνεμεῖ πόδα', 'οὐκ ἐκτὸς ἄψορρον ἐκνεμεῖ πόδα'),
        ('Clytaemnestra[?]s death', 'Clytaemnestra’s death'),
        ('οὐδ[?] θανόντι', 'οὐδὲ θανόντι'),
        # Jebb's asterisk before a conjecture (686, Musgrave's τἀφέσει): printed, not italics
        ('**ἰσώσας * τἀφέσει**', '**ἰσώσας \\* τἀφέσει**'),
        # Perseus's Betacode v left a Latin v: the digamma (ϝ, Ϝ; read on the page: Ajax leaves 139, 265, 293;
        # Electra 137) or a mistyped ν (the word is plain)
        ('being vεκ,', 'being ϝεκ,'),
        ('for ἐvέκηλος, ἔvκηλος', 'for ἐϝέκηλος, ἔϝκηλος'),
        ('(for ἔκηvα)', '(for ἔκηϝα)'),
    ],
    "ajax": [
        # Perseus's e)=nai for ei)=nai (a circumflex over nothing)
        ('ellipse of ἐ ͂ναι', 'ellipse of εἶναι'),
        # Perseus's "<*>" (imported as "[?]") and capital rho keyed *(p, read on Jebb's page (1896, scan
        # playsfragmentswi07sophuoft; 2026-11-17): all 20
        ('εἱλόμη[?] ἄν', 'εἱλόμην ἄν'),
        ('Menander *ʽπαπιζομένης', 'Menander Ῥαπιζομένης'),
        ('γυμνικὸν [?]ιὰ πάσης', 'γυμνικὸν διὰ πάσης'),
        ('in which Soph [?]es has used', 'in which Sophocles has used'),
        ('**ἐπεντύνον[?]**', '**ἐπεντύνοντʼ**'),
        ('the fore[?]st thought', 'the foremost thought'),
        ('τῶν τρ[?]άκοντα', 'τῶν τριάκοντα'),
        ('κανόνητα σ[?]ματα', 'κανόνητα σώματα'),
        ('stem the [?]de.', 'stem the tide.'),
        ('ἀτρύτ [?]τιν |', 'ἀτρύτοισιν |'),
        ('ὁ ἀεὶ as=[?] ἀεὶ ὤν', 'ὁ ἀεὶ as=ὁ ἀεὶ ὤν'),
        ('διαφέρε[?]ν τὸν', 'διαφέρειν τὸν'),
        ('ᾧ καὶ Ζ[?]ὺς', 'ᾧ καὶ Ζεὺς'),
        ('τῷ *ʽποιτείῳ', 'τῷ Ῥοιτείῳ'),
        ('fairly wo[?] The fut.', 'fairly won. The fut.'),
        ('ἐμβρόντητε, ε[?] ͂τα νῦν', 'ἐμβρόντητε, εἶτα νῦν'),
        # the last four (68 leaf 106, 500 leaf 167, 797 leaf 208, 977 leaf 233)
        ('εἰ[?]ιδεῖν**', 'εἰσιδεῖν**'), ('the Lat. *[?]a-c* is', 'the Lat. *ja-c* is'),
        ('*Ph.* 174 [?]λύει δʼ', '*Ph.* 174 ἀλύει δʼ'),
        ('For ξύναιμον, cp. [?] σοπη. *αντ.* αὐτάδελφον..κάρα, Soph. *O. C.*', 'For ξύναιμον, cp. *Ant.* 1 αὐτάδελφον..κάρα, *O. C.*'),
        # Perseus's Betacode v left a Latin v: the digamma (ϝ, Ϝ; read on the page: Ajax leaves 139, 265, 293;
        # Electra 137) or a mistyped ν (the word is plain)
        ('**vαὸς ἀρωγοὶ**', '**ναὸς ἀρωγοὶ**'),
        ('= ἀv-vέρυσαν', '= ἀϝ-ϝέρυσαν'),
        ('for ἀν-vερ,', 'for ἀν-ϝερ,'),
        ('form was Αἴvας', 'form was ΑἴϜας'),
        ('root (vεργ)', 'root (ϝεργ)'),
        ('the rt. ἀv (ἄω)', 'the rt. ἀϝ (ἄω)'),
        ('a rt. ἀvες', 'a rt. ἀϝες'),
        ('rt. vελ, εἴλω', 'rt. ϝελ, εἴλω'),
        ('**vαύταις**', '**ναύταις**'),
    ],
    # the Antigone: none since its commentary is read from Jebb's page (COMMENTARY_FROM_PAGE,
    # 2026-11-17); the fixes to Perseus's digitisation it had are in git history (before be034e2)
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
        # note 1248: Ῥιπᾶν, Ῥῖπαι (Perseus's Betacode *(ripa=n read as a bare asterisk and a breathing)
        ("***ʽπιπᾶν**", "**Ῥιπᾶν**"), ("*ʽπῖπαι", "Ῥῖπαι"),
        # the same note, leaf 294 (read 2026-11-17): Alcman's Ῥίπας and Damastes' Ῥίπαια, which
        # had paired into italics over the passage
        ("*ʽπίπας", "Ῥίπας"), ("*ʽπίπαια", "Ῥίπαια"), ("ὑπὲρτὰ Ῥίπαια", "ὑπὲρ τὰ Ῥίπαια"),
    ],
}


# Perseus's commentary: notes whose printed heading (and the first word of the lemma) Perseus lost,
# put right from the page: "number lemma-start" -> (Jebb's heading, Jebb's lemma)
NOTE_HEADING_FIXES: dict[str, dict[str, tuple[str, str]]] = {
    "trachiniae": {
        # leaf 172: "633—639 ὦ ναύλοχα κ.τ.λ." (Perseus: 639, the ὦ unread, "<*>", imported as "[?]")
        "639 **[?] ναύλοχα**": ("633-639", "**ὦ ναύλοχα**"),
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
    changes nothing. `heading_fixes` ("639 **[?] ναύλοχα**" -> ("633-639", "**ὦ ναύλοχα**"))
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
        new_heading = f"## {new_a}" + (f"-{new_b}" if new_b else "") + (f" {ff}" if ff and not new_b and new_a == a else "")
        if new_a != a:
            # the printed number in front of the note, as in the apparatus, with Jebb's "f."/"ff."
            # (they belong to his number, not to the line the note is filed under)
            i = next((k for k, l in enumerate(body) if l.strip()), None)
            if i is not None:
                body = body[:i] + [f"[{printed}{' ' + ff if ff else ''}] {body[i]}"] + body[i + 1:]
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


def file_at_half_lines(work_dir: Path) -> list[str]:
    """Jebb's notes on a verse our text divides between two speakers (981 and 981a): his heading
    carries no letter, so a note "## 982" may hold lemmas of the second part. Each paragraph that
    begins with a bold lemma whose first word stands in Na and not in N goes, with the paragraphs
    after it that have no lemma, under a heading `## Na` after the note; run by sophocles-prose
    for a commentary read from the page (COMMENTARY_FROM_PAGE). Returns one line per note split."""
    from .textfmt import parse_file

    path, grc = work_dir / "commentary-jebb.md", work_dir / "grc.txt"
    if not path.exists() or not grc.exists():
        return []
    lines = {l.n: l.text for l in parse_file(grc).lines}

    def words(t: str) -> set[str]:
        return {_skel(w) for w, _s, _e in greek.words(t)}

    text = path.read_text(encoding="utf-8")
    blocks = re.split(r"(?m)^(?=## )", text)
    moves = []
    for k, blk in enumerate(blocks):
        m = re.match(r"^## (\d+)( ff?\.)?\n(.*)$", blk, re.S)
        if not m or m.group(1) + "a" not in lines:
            continue
        n = m.group(1)
        here, there = words(lines[n]), words(lines[n + "a"])
        paras = [p for p in m.group(3).split("\n\n")]
        stay, go, current = [], [], None
        for para in paras:
            lm = re.match(r"^(?:\[[^\]]+\]\s*)?\*\*([^*]+)\*\*", para.strip())
            if lm:
                first = [_skel(w) for w, _s, _e in greek.words(lm.group(1))][:1]
                current = "go" if first and first[0] in there and first[0] not in here else "stay"
            (go if current == "go" else stay).append(para)
        if not go:
            continue
        body_stay = "\n\n".join(p for p in stay if p.strip())
        body_go = "\n\n".join(p.strip("\n") for p in go if p.strip())
        if not body_stay.strip():
            blocks[k] = f"## {n}a\n{body_go}\n\n"
        else:
            blocks[k] = f"## {n}{m.group(2) or ''}\n{body_stay.rstrip()}\n\n## {n}a\n{body_go}\n\n"
        moves.append(f"commentary: {len(go)} paragraph(s) of the note on {n} filed at {n}a (their lemma stands there)")
    new = "".join(blocks)
    if new != text:
        tmp = path.with_name(path.name + ".part")
        tmp.write_text(new, encoding="utf-8")
        tmp.replace(path)
    for mv in moves:
        print(mv)
    return moves


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


def numbering_suspects(lines: list[tuple[str, str]], apparatus: str, reach: int = 3, unbolded: bool = False) -> list[dict]:
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
    `reach` lines before to `reach` after, as (number, verse)).
    `unbolded` (Murray's Euripides, whose items mostly have no "]" and give the text's reading
    first, "<reading> L: <variant> rell."): an item without a bold lemma takes its first one or
    two Greek words, up to the first word in Latin letters, as its lemma."""
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
        if unbolded and not lm:
            lemma = _first_greek(para[len(pm.group(0)):] if pm else para)
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
                lemma = bm.group(1).strip() if bm else _first_greek(rest)
                key = _letters(lemma)
                hits = [j for j in near if key and key in letters[j]]
                found = numbers[min(hits, key=lambda j: (abs(j - i), j))] if hits else None
            out.append({"kind": "printed", "note": note, "lemma": lemma, "filed": filed, "found": found,
                        "context": context})
    return out


def _first_greek(text: str, most: int = 2) -> str:
    """The first one or two Greek words of an apparatus item, up to the first word in Latin
    letters (a siglum, "om.", a scholar's name)."""
    run = []
    for w, _s, _e in greek.words(text):
        if not re.search(r"[\u0370-\u03ff\u1f00-\u1fff]", w) or len(run) == most:
            break
        run.append(w)
    return " ".join(run)


def report_numbering(work_dir: Path, reach: int = 3, apparatus: str = "commentary-jebb-apparatus.md",
                     unbolded: bool = False) -> int:
    """sophocles-numbering: print numbering_suspects for texts/<slug>/ from the apparatus
    (commentary-jebb-apparatus.md); returns how many. (Jebb's commentary from Perseus is not
    scanned: Perseus drops the "f." of its headings, so a note on two verses whose lemma stands in
    the second would be listed everywhere; look at its numbers by hand in a suspect stretch.)"""
    from .textfmt import parse_file

    grc, app = work_dir / "grc.txt", work_dir / apparatus
    if not grc.exists() or not app.exists():
        print(f"{work_dir}: no grc.txt or {apparatus}")
        return 0
    lines = [(l.n, l.text) for l in parse_file(grc).lines]
    total = 0
    for path in (app,):
        label = "apparatus"
        items = numbering_suspects(lines, path.read_text(encoding="utf-8"), reach, unbolded)
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
