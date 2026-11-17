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

from . import greek
from .drama import PLAYS, TRANSCRIPTION_LICENSE, _meta_lines
from .hude_pages import APP_KEY, HYPOTHESIS, KEY, LABEL, SPEECHES, TITLE, check_tokens, is_numeral, out_dir, read_batches, transcriptions_dir
from .lucian_merge import LETTERS, _LOWER_GREEK, _find, _sk, greek_runs, lemma_of, split_long
from .lucian_pages import SECTION_MARK

ROOT = Path(__file__).resolve().parent.parent.parent
PIPELINE = ROOT / "pipeline"
# Evident misprints in Hude's print (the author's rule: keep to the printed edition; correct
# evident misprints everywhere, the apparatus too, each with a note). The batches keep what is
# printed; the merge puts the right reading in and says so in the apparatus of the section.
# Text: (leaf.line, the printed words, the right words; the same number of words).
MISPRINTS: dict[str, list[tuple[str, str, str]]] = {
    "lysias": [
        ("89.22", "ἔλεγετʼ,", "ἐλέγετʼ,"),                    # 8.8: the accent on the wrong syllable; his apparatus has ἐλέγετʼ
        ("100.16", "Αυσιθέῳ", "Λυσιθέῳ"),                    # 10.12: a capital alpha for the lambda; his apparatus has Λυσιθέῳ
        ("184.15", "πεπιστευμενους", "πεπιστευμένους"),      # 19.13: no accent (the word divided at the line's end)
        ("202.2", "εστιν,", "ἐστιν,"),                        # 20.28: no breathing
        ("205.21", "ἐνίκων καὶ,", "ἐνίκων, καὶ"),             # 21.4: the comma set after καὶ instead of before it
        ("229.27", "ὀλιγαοχικὸς", "ὀλιγαρχικὸς"),            # 25.8: an omicron for the rho
    ],
}
# Apparatus items whose first reading is not the text's, each looked at on the page image
# (2026-11-16): the batch has the line and the item as printed; the item reports a variant, a
# conjecture or the manuscripts' reading first (Hude's apparatus is largely negative). The lemma
# check does not list these again. Key: "leaf.number: the item's first words".
SETTLED: dict[str, set[str]] = {
    "lysias": {
        "32.5: δὲ μὴ γενομένων", "35.13: εἰς", "44.11: τῆς τούτων", "68.19: οὐδὲν χαρισ. αὐτῶ", "72.23: εἰς δημοκρατίαν",
        "139.5: μὴ", "161.6: διὰ τὴν δύναμιν, ὅτε", "186.23: μάρτυρες", "199.15: δὲ [ἐν", "210.2: τοσοῦτ", "212.4: ἀξιοῖς ἢ",
        "219.5: ἀντιγρᾱ", "226.24: ⟨περὶ⟩ ἁπάντων", "233.23: ἐκ τοῦ ἄστεος", "239.8: τῇ αὐτῇ", "258.23: ὑπὸ λόγον",
        "278.1: δικασταί", "279.20: αὐτῷ οὐδεὶς", "286.19: ὦ Ἀθηναῖοι",
    },
}
# Apparatus: (leaf.number of the item as the batch has it, the printed word, the right word).
APPARATUS_MISPRINTS: dict[str, list[tuple[str, str, str]]] = {
    "lysias": [
        ("45.19", "προτερον", "πρότερον"),            # no accent
        ("76.26", "συμβαλόμενυς", "συμβαλόμενος"),    # an upsilon for the omicron
        ("77.3", "ἐφʼ ᾖ", "ἐφʼ ᾗ"),                   # a smooth breathing for the rough
        ("146.27", "οὑτυσὶ", "οὑτοσὶ"),               # an upsilon for the omicron
        ("211.16", "ούνεκα", "οὔνεκα"),               # no breathing (οὔνεκα L on leaves 213 and 215)
        ("238.25", "ούνεκα", "οὔνεκα"),
    ],
}
# The speeches' names for the book chooser: Hude's printed title (capitals without accents in
# the print) in lower case with accents and breathings, the first word capitalised, his brackets
# kept (the author, 2026-11-16); the accents are those of the Perseus files' titles where the
# words agree. The merge compares each with the title lines of the batches by letters and reports
# a difference. The second name is the customary English one (for the introduction's chapters).
SPEECH_NAMES: dict[int, tuple[str, str]] = {
    1: ("Ὑπὲρ τοῦ Ἐρατοσθένους φόνου ἀπολογία", "On the Murder of Eratosthenes"),
    2: ("Ἐπιτάφιος τοῖς Κορινθίων βοηθοῖς", "Funeral Oration"),
    3: ("Πρὸς Σίμωνα ἀπολογία", "Against Simon"),
    4: ("Περὶ τραύματος ἐκ προνοίας, ὑπὲρ οὗ καὶ πρὸς ὃν ⟨ἄδηλον⟩", "On a Wound by Premeditation"),
    5: ("Ὑπὲρ Καλλίου ἱεροσυλίας ἀπολογία", "For Callias"),
    6: ("Κατὰ Ἀνδοκίδου ἀσεβείας", "Against Andocides"),
    7: ("Ἀρεοπαγιτικὸς περὶ τοῦ σηκοῦ ἀπολογία", "On the Olive Stump"),
    8: ("Κατηγορία πρὸς τοὺς συνουσιαστὰς κακολογιῶν", "Accusation of Calumny"),
    9: ("Ὑπὲρ τοῦ στρατιώτου", "For the Soldier"),
    10: ("Κατὰ Θεομνήστου", "Against Theomnestus I"),
    11: ("Κατὰ Θεομνήστου Β", "Against Theomnestus II"),
    12: ("Κατὰ Ἐρατοσθένους τοῦ γενομένου τῶν τριάκοντα, ὃν αὐτὸς εἶπε Λυσίας", "Against Eratosthenes"),
    13: ("Κατὰ Ἀγοράτου ἐνδείξεως", "Against Agoratus"),
    14: ("Κατὰ Ἀλκιβιάδου λιποταξίου", "Against Alcibiades I"),
    15: ("Κατὰ Ἀλκιβιάδου ἀστρατείας", "Against Alcibiades II"),
    16: ("Ἐν βουλῇ Μαντιθέῳ δοκιμαζομένῳ ἀπολογία", "For Mantitheus"),
    17: ("Δημοσίων ἀδικημάτων", "On the Property of Eraton"),
    18: ("Περὶ τῆς δημεύσεως ⟨τῶν⟩ τοῦ Νικίου ἀδελφοῦ ἐπίλογος", "On the Property of the Brother of Nicias"),
    19: ("Ὑπὲρ τῶν Ἀριστοφάνους χρημάτων, πρὸς τὸ δημόσιον", "On the Property of Aristophanes"),
    20: ("Ὑπὲρ Πολυστράτου δήμου καταλύσεως ἀπολογία", "For Polystratus"),
    21: ("Ἀπολογία δωροδοκίας ἀπαράσημος", "Defence against a Charge of Taking Bribes"),
    22: ("Κατὰ τῶν σιτοπωλῶν", "Against the Grain Dealers"),
    23: ("Κατὰ Παγκλέωνος ὅτι οὐκ ἦν Πλαταιεύς", "Against Pancleon"),
    24: ("[Πρὸς τὴν εἰσαγγελίαν] περὶ τοῦ μὴ δίδοσθαι τῷ ἀδυνάτῳ ἀργύριον", "For the Cripple"),
    25: ("Δήμου καταλύσεως ἀπολογία", "Defence against a Charge of Subverting the Democracy"),
    26: ("⟨Περὶ τῆς Εὐάνδρου δοκιμασίας⟩", "On the Scrutiny of Evander"),
    27: ("Κατὰ Ἐπικράτους καὶ τῶν συμπρεσβευτῶν ἐπίλογος [ὡς Θεόδωρος]", "Against Epicrates"),
    28: ("Κατὰ Ἐργοκλέους ἐπίλογος", "Against Ergocles"),
    29: ("Κατὰ Φιλοκράτους ἐπίλογος", "Against Philocrates"),
    30: ("Κατὰ Νικομάχου γραμματέως εὐθυνῶν κατηγορία", "Against Nicomachus"),
    31: ("Κατὰ Φίλωνος δοκιμασίας", "Against Philon"),
    32: ("Κατὰ Διογείτονος", "Against Diogeiton"),
    33: ("Ὀλυμπικός", "Olympic Oration"),
    34: ("Περὶ τοῦ μὴ καταλῦσαι τὴν πάτριον πολιτείαν Ἀθήνησι", "On the Constitution"),
}
# Where the trees of each speech come from (PLAN-lysias.md, "Syntax"): the AGDT's hand-made trees
# (pipeline/sources/treebanks, CC BY-SA 3.0), GLAUx's file (hand-made for 24: the Pedalion trees;
# automatic for the rest, CC BY-SA 4.0), or none (12, 13, 19: the only trees are under a
# non-commercial licence; the author, 2026-11-16: shipped without syntax).
AGDT = {1, 14, 15, 23}
MANUAL = AGDT | {24}
NO_SYNTAX = {12, 13, 19}
# the anonymous literal translation of 1898 (Project Gutenberg #6969): its twenty speeches
TRANSLATED_1898 = (2, 5, 7, 9, 10, 12, 13, 14, 16, 17, 19, 22, 23, 24, 25, 28, 30, 31, 32, 33)
STATIC = PIPELINE / "transcriptions" / "lysias" / "static"
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
    labels: dict[str, str] = {}
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
                    if pending_labels and units:
                        # a heading after a speech's last words (14.47: the laws, oaths and indictment read at the end)
                        units[-1].setdefault("after", []).extend(pending_labels)
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
                labels[key] = text[len(LABEL):].strip()
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
    if pending_labels and units:
        units[-1].setdefault("after", []).extend(pending_labels)
    # long sections divided at sentence ends; the headings stay before the part they stood before
    # (after the last part, for a heading that ends a speech)
    before = {id(u): u["before"] for u in units}
    firsts = [(ui, u["words"][0][1]) for ui, u in enumerate(units) if u["words"] and u["before"]]
    lasts = [(ui, u["words"][-1][1], len(u["words"]) - 1, u["after"]) for ui, u in enumerate(units) if u["words"] and u.get("after")]
    old_lines = lines
    new_units, lines = split_long(units, old_lines)
    for u in new_units:
        u["before"] = []
    for ui, key in firsts:
        k = next(i for i, (a, b, _w) in enumerate(old_lines[key]) if a == ui and b == 0)
        new_units[lines[key][k][0]]["before"] = before[id(units[ui])]
    for ui, key, wi, after in lasts:
        k = next(i for i, (a, b, _w) in enumerate(old_lines[key]) if a == ui and b == wi)
        new_units[lines[key][k][0]]["after"] = after
    return {"units": new_units, "lines": lines, "titles": titles, "labels": labels, "problems": problems}


def _letters(s: str) -> str:
    """A title's letters alone (no accents, brackets or hyphens of a divided word; an iota
    adscript of the capitals counts as the subscript of the lower case: ΒΟΥΛΗΙ, βουλῇ)."""
    from .drama import skel

    return skel(s.replace("- ", ""), adscript=True)


def speech_title(lines: list[str]) -> tuple[str, str]:
    """(the speech's number as printed, its title) from the [title] lines: the Roman numeral
    stands first; a hypothesis's own heading (ΥΠΟΘΕΣΙΣ …) is not part of the title."""
    numeral = lines[0] if lines and is_numeral(lines[0]) else ""
    rest = [l for l in (lines[1:] if numeral else lines) if not l.startswith("ΥΠΟΘΕΣΙΣ")]
    return numeral, " ".join(rest)


def correct_misprints(slug: str, text: dict, problems: list[str]) -> list[tuple[int, str]]:
    """The right reading in the text where the edition misprints (MISPRINTS), and for each an
    apparatus note on its section, marked as this edition's: [(unit index, note)]."""
    notes: list[tuple[int, str]] = []
    for key, printed, right in MISPRINTS.get(slug, []):
        want, new = printed.split(), right.split()
        entries = text["lines"].get(key, [])
        at = next((i for i in range(len(entries) - len(want) + 1) if [e[2] for e in entries[i:i + len(want)]] == want), None)
        if at is None or len(want) != len(new):
            problems.append(f"misprint {key}: “{printed}” not found on the line")
            continue
        for k, w in enumerate(new):
            u, wi, _old = entries[at + k]
            entries[at + k] = (u, wi, w)
            text["units"][u]["words"][wi] = (w, text["units"][u]["words"][wi][1])
        bare = lambda x: x.strip(",.·;")  # noqa: E731
        if len(want) == 1:
            notes.append((entries[at][0], f"{bare(right)}: Hude prints {bare(printed)}, a misprint; corrected in this edition."))
        else:
            notes.append((entries[at][0], f"{right}: Hude prints {printed}, a misprint; corrected in this edition."))
    return notes


def correct_apparatus(slug: str, pages: dict[str, dict], problems: list[str]) -> int:
    """The right word in an apparatus item where Hude's apparatus misprints one
    (APPARATUS_MISPRINTS), with the note in brackets after the item. Returns how many."""
    done = 0
    for key, printed, right in APPARATUS_MISPRINTS.get(slug, []):
        leaf, _, number = key.partition(".")
        block = pages.get(f"p-{int(leaf):04d}")
        hit = False
        for k, (n, item) in enumerate(block["apparatus"] if block else []):
            if n == number and printed in item:
                block["apparatus"][k] = (n, item.replace(printed, right, 1)
                                         + f" [{right}: Hude's apparatus prints {printed}, a misprint; corrected in this edition.]")
                hit = True
                done += 1
                break
        if not hit:
            problems.append(f"apparatus misprint {key}: “{printed}” not found in an item numbered {number}")
    return done


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
        noted = {m_.group(1) for x in block["notes"] if (m_ := re.match(r"^(\d+\.\d+)", x))}
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
            # Hude writes a lemma's range with dots ("τούτῳ . . . εἰ] οὐδὲ C")
            first, last = lemma_of(re.sub(r"\s*\.\s\.\s\.\s*", " — ", rest))
            runs = greek_runs(rest)
            where = f"{leaf}.{n}"
            if not own and first and ka in text.get("labels", {}) and _sk(" ".join(first)) in _sk(text["labels"][ka]):
                # an item on a heading (μάρτυρες] spatium X): the part the heading stands before
                u = next((lines[k][0][0] for k in ordered[ia:] if lines[k]), None)
                if u is not None:
                    placed.append((u, item))
                    last_unit = u
                    continue
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
                # the hands of one manuscript are given in their order, the first hand's reading
                # first ("κοινὰ X¹: κοινὴ Xˢ"): there the text has the later reading by rule
                hands = re.match(r"^[^:]*?\s[A-Za-z]¹(?:\s[A-Za-z]¹?)*\s*:", rest) is not None
                if last and hit is not None and bracket:
                    bracket = False  # a range whose first word stands on the line
                if not exact and not hands and (bracket or (later and ":" in rest)) \
                        and f"{where}: {' '.join(first)}" not in SETTLED.get("lysias", ()):
                    why = "the lemma] is not in the text" if bracket else "a later reading of the item stands in the text"
                    mark = " (the line is noted in the batch)" if any(k in noted for k in ordered[ia: ib + 1]) else ""
                    misses.append(f"SERIOUS {where}{mark}: Hude's reading “{' '.join(first)}” is not on the line as written ({why}) "
                                  f"(the line: {' '.join(c[2] for c in own)}): {item}")
                elif hit is None:
                    misses.append(f"WEAK {where}: “{' '.join(first)}” matches nothing on the line: {item}")
                    if len({c[0] for c in own}) > 1:
                        # a variant without its lemma, on a line that holds the end of one section
                        # and the start of the next: the section of the word most like it
                        # (ᾔδειν beside the text's ᾔδη, οἷς beside οὓς)
                        best = max(((difflib.SequenceMatcher(None, _sk(c[2]), _sk(w)).ratio(), -k, c) for k, c in enumerate(own)
                                    for w in first if _sk(w)), default=(0, 0, None))
                        if best[0] >= 0.5:
                            hit = best[2]
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


# --- words and syntax --------------------------------------------------------------------------

def syntax_kind(speech: int) -> str:
    return "none" if speech in NO_SYNTAX else "manual" if speech in MANUAL else "automatic"


def speech_treebank(speech: int, sources: Path) -> list[dict]:
    """The trees of a speech as drama._tokens takes them (sophocles.read_agdt / read_glaux_lines),
    the sentence ids made the text's own by the speech's number in front ("12.34"); [] for a
    speech shipped without syntax."""
    from .sophocles import read_agdt, read_glaux_lines

    if speech in NO_SYNTAX:
        return []
    if speech in AGDT:
        tb = read_agdt(sources / "treebanks" / f"tlg0540.tlg{speech:03d}.perseus-grc1.tb.xml")
    else:
        tb = read_glaux_lines(sources / "glaux" / f"0540-{speech:03d}.xml")
    for w in tb:
        w["sentence"] = f"{speech}.{w['sentence']}"
    return tb


# a verb's prefixes as they stand before the stem (elided, assimilated, aspirated) and as the
# dictionary writes them
PREFIXES = {"ανα": "ἀνα", "αν": "ἀνα", "αντι": "ἀντι", "αντ": "ἀντι", "ανθ": "ἀντι", "απο": "ἀπο", "απ": "ἀπο", "αφ": "ἀπο",
            "δια": "δια", "δι": "δια", "εισ": "εἰσ", "εκ": "ἐκ", "εξ": "ἐκ", "εν": "ἐν", "εμ": "ἐν", "εγ": "ἐν",
            "επι": "ἐπι", "επ": "ἐπι", "εφ": "ἐπι", "κατα": "κατα", "κατ": "κατα", "καθ": "κατα", "μετα": "μετα", "μετ": "μετα",
            "μεθ": "μετα", "παρα": "παρα", "παρ": "παρα", "περι": "περι", "προ": "προ", "προσ": "προσ", "συν": "συν", "συμ": "συν",
            "συγ": "συν", "συλ": "συν", "υπερ": "ὑπερ", "υπο": "ὑπο", "υπ": "ὑπο", "υφ": "ὑπο"}
_ASPIRATE = {"π": "φ", "τ": "θ", "κ": "χ"}


def _join_prefix(prefix: str, lemma: str) -> str:
    """A dictionary prefix before a verb's lemma: ἀπο + γράφω = ἀπογράφω; before a vowel the
    prefix's last vowel goes (ἀπο + ἄγω = ἀπάγω; not περι, προ), and a rough breathing aspirates
    it (κατα + ἕζομαι = καθέζομαι); συν takes the stem's first consonant (συλλέγω, συμβάλλω,
    συγγράφω); ἐκ is ἐξ before a vowel. The lemma's breathing goes."""
    import unicodedata

    d = unicodedata.normalize("NFD", lemma)
    rough = "\u0314" in d[:4]
    vowel = d[0] in "αεηιουω"
    bare = unicodedata.normalize("NFC", d.replace("\u0313", "", 1).replace("\u0314", "", 1)) if vowel else lemma
    if vowel:
        if prefix == "ἐκ":
            prefix = "ἐξ"
        elif prefix[-1] in "αοι" and prefix not in ("περι", "προ"):
            prefix = prefix[:-1]
            if rough and prefix[-1] in _ASPIRATE:
                prefix = prefix[:-1] + _ASPIRATE[prefix[-1]]
    elif prefix in ("συν", "ἐν"):
        first = greek.strip_diacritics(bare)[0]
        last = "μ" if first in "πβφμψ" else "γ" if first in "κγχξ" else "λ" if first == "λ" and prefix == "συν" else "ρ" if first == "ρ" and prefix == "συν" else "ν"
        prefix = prefix[:-1] + last
    return prefix + bare


def _rough(form: str) -> bool:
    import unicodedata

    return "\u0314" in unicodedata.normalize("NFD", form)[:4]


def compound_analysis(form: str, analyse, known, depth: int = 2, pick=None) -> tuple[str, str] | None:
    """(lemma, postag) of a compound verb the analyser does not know, from its simple verb:
    κατεχορήγησε = κατ + ἐχορήγησε (χορηγέω, aorist) gives καταχορηγέω; with two prefixes,
    συνεκπλευσεῖσθαι. Taken only if the dictionaries have the compound (`known(lemma)`)."""
    key = greek.strip_diacritics(form.replace(greek.APOSTROPHE, "")).lower()
    for i in range(5, 1, -1):
        prefix = PREFIXES.get(key[:i])
        rest = form[i:] if len(form) > i + 2 else ""
        if not prefix or not rest:
            continue
        found = [a for a in analyse(rest) if len(a) >= 3 and a[2].startswith("v")]
        if rest[0] in "αεηιουω":
            # the stem's breathing shows in the prefix: ἀπ-ιέναι is from εἶμι, ἀφ-ιέναι from ἵημι
            aspirated = key[:i][-1] in "φθχ"
            if key[:i][-1] in "πτκφθχ":
                found = [a for a in found if _rough(a[0]) == aspirated]
        chosen = pick(rest, found) if pick and found else None   # the commonest reading of the simple form
        cands = ([chosen] if chosen else []) + [(a[1], a[2]) for a in found if (a[1], a[2]) != chosen]
        if not cands and depth > 1:
            inner = compound_analysis(rest, analyse, lambda _l: True, depth - 1, pick)
            cands = [inner] if inner else []
        for lemma, postag in cands:
            whole = _join_prefix(prefix, re.sub(r"\d+$", "", lemma))
            if known(whole):
                return whole, postag
    return None


_ARTICLE_BEFORE_ENCLITIC = {"ὅ": "l-s---mn-", "ἥ": "l-s---fn-", "οἵ": "l-p---mn-", "αἵ": "l-p---fn-"}


def relatives_and_articles(rows: list[dict]) -> int:
    """Two things the analyser cannot tell without the next word, in the words it read by itself
    (those outside the trees): ὃ with the grave, and ὅ before τι, is the relative, not the
    article; ἥ τε, οἵ τε, αἵ τε, ὅ τε is the article with the enclitic's accent, not the
    relative. Returns how many were changed."""
    changed = 0
    for r, nxt in zip(rows, rows[1:]):
        if r.get("sentence"):
            continue
        if (r["form"] == "ὃ" or (r["form"] == "ὅ" and nxt["form"] in ("τι", "τί"))) and r["lemma"] == "ὁ":
            r["lemma"], r["postag"] = "ὅς", "p-s---na-"
            changed += 1
        elif r["form"] in _ARTICLE_BEFORE_ENCLITIC and nxt["form"] == "τε" and r["lemma"] == "ὅς":
            r["lemma"], r["postag"] = "ὁ", _ARTICLE_BEFORE_ENCLITIC[r["form"]]
            changed += 1
    return changed


ADDRESSED = {"δικαστής", "βουλευτής", "πολίτης"}


def vocatives(rows: list[dict], analyse) -> int:
    """In a speech without trees the analyser reads each word by itself and calls the address
    after ὦ a nominative (ὦ ἄνδρες δικασταί, ὦ Ἀθηναῖοι, ὦ βουλή). The words that follow ὦ, as
    far as each has a vocative of the same lemma and number among its analyses, are made
    vocative: the first word whatever it is, after it only the court's names and proper names.
    Returns how many were changed."""
    changed = 0
    for i, r in enumerate(rows):
        if r["form"].lower() != "ὦ":
            continue
        for k, t in enumerate(rows[i + 1:i + 4]):
            tag = t["postag"]
            if len(tag) != 9 or tag[7] not in "nv":
                break
            if k and t["lemma"] not in ADDRESSED and not t["lemma"][:1].isupper():
                break  # the address is over: ὦ ἄνδρες δικασταί, τέτταρες ἀδελφοί
            want = tag[:7] + "v" + tag[8]
            if tag[7] == "n":
                if not any(a[1] == t["lemma"] and a[2] == want for a in analyse(t["form"])):
                    break
                t["postag"] = want
                changed += 1
    return changed


def tokens(slug: str, doc, sources: Path, out: Path, lexicon: Path, build: Path) -> int:
    """tokens.tsv and syntax-nodes.tsv: each speech's words aligned to its own trees (the words
    alone decide: neither source knows Hude's lines), the analyser for the words the trees lack
    or read otherwise, and for the whole of the speeches without trees; the review list
    build/<slug>-review.tsv. As drama._tokens, speech by speech."""
    from . import greek
    from .drama_fixes import HAND_ANALYSES, LEMMA_FIXES as TEXT_LEMMA_FIXES
    from .import_perseus import LEMMA_FIXES, write_syntax_nodes, write_tokens
    from .odyssey import align, fix_lemma, syntax_nodes
    from .odyssey_merge import Analyser, Frequencies, choose_analysis
    from .textfmt import Document

    analyse = Analyser(lexicon)
    freq = Frequencies(sources / "treebanks")
    known_keys = {k for (k,) in analyse.db.execute("SELECT DISTINCT lemma_key FROM lexicon_entries")}
    known = lambda lemma: greek.lemma_key(lemma) in known_keys  # noqa: E731
    by_speech: dict[int, Document] = {}
    for line in doc.lines:
        by_speech.setdefault(int(line.n.split(".")[0]), Document(meta={})).items.append(line)
    rows: list[dict] = []
    nodes: list[dict] = []
    review: list[dict] = []
    for speech in sorted(by_speech):
        tb = speech_treebank(speech, sources)
        who = "the treebank" if speech in AGDT else "GLAUx"
        got, _warnings = align(by_speech[speech], tb, keep_tb_form=True)
        for r in got:
            tb_form = r.pop("tb_form", "")
            same = tb_form and greek.strip_diacritics(tb_form) == greek.strip_diacritics(r["form"])
            if r["lemma"] and r["postag"] and (same or not tb_form):
                continue
            chosen = choose_analysis(r["form"], analyse(r["form"]), r["postag"], r["lemma"], freq, tb_form)
            if chosen is not None:
                r["lemma"], r["postag"] = fix_lemma(chosen[0]), chosen[1]
            elif not r["lemma"]:
                compound = compound_analysis(r["form"], analyse, known, pick=lambda f, found: choose_analysis(f, found, freq=freq))
                if compound:
                    r["lemma"], r["postag"] = compound
                    review.append({"line": r["line"], "form": r["form"], "lemma": r["lemma"], "postag": r["postag"],
                                   "reason": "a compound verb read from its simple verb"})
                    continue
            if not tb:
                if not r["lemma"]:
                    review.append({"line": r["line"], "form": r["form"], "lemma": "", "postag": r["postag"], "reason": "no trees for this speech; the analyser has no reading"})
                continue  # a speech without trees: every word is the analyser's, only the unread ones are listed
            reason = (f"no lemma or parse in {who}" if same else f"reads {r['form']} where {who} has {tb_form}" if tb_form
                      else f"a word {who} splits" if "+" in r["word_id"] else f"not in {who}")
            review.append({"line": r["line"], "form": r["form"], "lemma": r["lemma"], "postag": r["postag"], "reason": reason})
        if not tb:
            vocatives(got, analyse)
        used = {(r["sentence"], w) for r in got for w in r["word_id"].split("+") if r["sentence"]}
        nodes += syntax_nodes(tb, used)
        rows += got
    relatives_and_articles(rows)
    # the checking pass over the speeches without trees (hude_analyses.py): the agents' choices
    from .hude_analyses import answers as checked_analyses
    table = checked_analyses() if slug == "lysias" else {}
    applied = 0
    for r in rows:
        a = table.get((r["line"], int(r["ord"])))
        if a is None or r.get("sentence"):
            continue
        if a[0] != r["form"]:
            review.append({"line": r["line"], "form": r["form"], "lemma": r["lemma"], "postag": r["postag"],
                           "reason": f"the checked analysis was made for {a[0]}: the text has changed"})
            continue
        if (r["lemma"], r["postag"]) != (a[1], a[2]):
            applied += 1
        r["lemma"], r["postag"] = a[1], a[2]
    if table:
        print(f"checked analyses (speeches without trees): {len(table)} words in the table, {applied} readings changed by it")
    hands = HAND_ANALYSES.get(slug, {})
    fixes = TEXT_LEMMA_FIXES.get(slug, {})
    for r in rows:
        hand = hands.get(f"{r['line']} {r['form']}") or hands.get(f"{base(r['line'])} {r['form']}")
        if hand:
            r["lemma"], r["postag"] = hand
        r["lemma"] = LEMMA_FIXES.get(r["lemma"], r["lemma"])
        r["lemma"] = fixes.get(r["lemma"], r["lemma"])
    write_tokens(out / "tokens.tsv", rows)
    write_syntax_nodes(out / "syntax-nodes.tsv", nodes)
    print(f"wrote tokens.tsv: {len(rows)} words, {sum(1 for r in rows if not r['lemma'])} without lemma; "
          f"syntax-nodes.tsv: {len(nodes)} nodes")
    with (build / f"{slug}-review.tsv").open("w", encoding="utf-8") as f:
        f.write("line\tform\tlemma\tpostag\treason\n")
        for r in review:
            f.write(f"{r['line']}\t{r['form']}\t{r['lemma']}\t{r['postag']}\t{r['reason']}\n")
    return len(review)


# --- the translation of 1898 -------------------------------------------------------------------

_ROMAN = {"I": 1, "V": 5, "X": 10, "L": 50}


def _roman(s: str) -> int:
    total = 0
    for a, b in zip(s, s[1:] + " "):
        total += -_ROMAN[a] if b in _ROMAN and _ROMAN[b] > _ROMAN[a] else _ROMAN[a]
    return total


def translation_1898(path: Path) -> tuple[dict[int, list[tuple[int, str]]], list[str]]:
    """The anonymous literal translation of 1898 (Project Gutenberg #6969) by speech and section:
    {speech: [(section, text)]} and problems. The speeches are headed "ORATION XII." (the
    transcription has "XXXL." and "XXXIL." for XXXI and XXXII); the section numbers stand in the
    text ("… for time to fail. 2. But I think …"), most of them, not all: a segment runs from one
    printed number to the next and is filed under its first section. The speech's title line is
    left out; the headings inside a speech (WITNESSES., LAW.) stay in the text; _italics_ are
    written *italics*."""
    t = path.read_text(encoding="utf-8").replace("\r", "")
    t = t.split("*** END OF THE PROJECT GUTENBERG")[0]
    heads = list(re.finditer(r"^ORATION ([IVXL]+)\.\s*$", t, re.M))
    out: dict[int, list[tuple[int, str]]] = {}
    problems: list[str] = []
    for k, h in enumerate(heads):
        numeral = h.group(1)
        if numeral not in ("L", "XL") and numeral.endswith("L"):
            numeral = numeral[:-1] + "I"  # XXXL, XXXIL: an I read as L
        speech = _roman(numeral)
        if speech != TRANSLATED_1898[k]:
            problems.append(f"translation 1898: heading {h.group(0).strip()} read as speech {speech}, expected {TRANSLATED_1898[k]}")
            speech = TRANSLATED_1898[k]
        block = t[h.end(): heads[k + 1].start() if k + 1 < len(heads) else len(t)]
        text = " ".join(block.split())
        segs: list[tuple[int, str]] = []
        cur, pos, start = 0, 0, None
        for m in re.finditer(r"(?:^|(?<=\s))(\d{1,3})\. (?=[\"“‘'(\[A-Z_])", text):
            n = int(m.group(1))
            if not (cur < n <= cur + 6):
                continue  # a figure in the text, not a section's number
            if start is not None:
                segs.append((cur, text[start:m.start()].strip()))
            elif text[:m.start()].strip() and n != 1:
                problems.append(f"translation 1898: speech {speech} begins with section {n}")
            cur, start = n, m.end()
        if start is not None:
            segs.append((cur, text[start:].strip()))
        out[speech] = [(n, re.sub(r"_([^_]+)_", r"*\1*", s_)) for n, s_ in segs]
    return out, problems


def write_translation(slug: str, sources: Path, out: Path, units: list[dict], problems: list[str]) -> int:
    play = PLAYS[slug]
    by_speech, probs = translation_1898(sources / "gutenberg" / "pg6969.txt")
    problems += probs
    have = {base(u["n"]) for u in units}
    rows = []
    for speech in sorted(by_speech):
        for n, text in by_speech[speech]:
            if f"{speech}.{n}" not in have:
                problems.append(f"translation 1898: section {speech}.{n} is not in the Greek")
                continue
            rows.append(f"{speech}.{n}\t{plain(text)}")
    meta = {"title": play.title_en, "translator": "Anonymous (1898)", "lang": "eng",
            "source": "The Orations of Lysias, literally translated, Handy Literal Translations, New York, 1898 (speeches "
                      + ", ".join(str(x) for x in TRANSLATED_1898) + "); from the Project Gutenberg text, ebook 6969",
            "license": "Public domain"}
    (out / "eng-1898.txt").write_text("\n".join(_meta_lines(meta) + [""] + rows) + "\n", encoding="utf-8")
    print(f"wrote eng-1898.txt: {len(rows)} segments of {len(by_speech)} speeches")
    return len(rows)


# The translations are shown as plain text (no other text's translation has markup): italics
# marks are taken out, and so are the raised letters of Gillies's footnotes, which are not shipped
_ITALICS = re.compile(r"\*([^*\n]+)\*")
_FOOTNOTE_LETTER = re.compile(r"(?<=\S)[ᵃᵇᶜᵈᵉᶠᵍʰⁱʲᵏˡᵐⁿᵒᵖ]")


def plain(text: str) -> str:
    return _ITALICS.sub(r"\1", text)


GILLIES_MARK = re.compile(r"(?:^|(?<=\s))§(\d+)\s+")


def gillies_segments(paras: list[str]) -> tuple[list[tuple[int, str]], list[str]]:
    """Gillies's paragraphs as (section, text) segments, and what is wrong with the marks. A mark
    `§7 ` stands at the head of a paragraph, or inside one before a sentence; the text from one
    mark to the next is one segment, filed under that section. A paragraph without a mark, and
    the part of a paragraph before its first mark, run on in the segment before. Headings and
    footnotes ([Note: …]) are not his translation and are left out."""
    segs: list[list] = []
    wrong: list[str] = []

    def add(text: str, new_paragraph: bool) -> None:
        text = text.strip()
        if not text:
            return
        if not segs:
            wrong.append(f"text before the first mark: {text[:40]}")
        elif segs[-1][1]:
            segs[-1][1] += ("\n\n" if new_paragraph else " ") + text  # a paragraph of his own inside the segment
        else:
            segs[-1][1] = text

    for p_ in paras:
        if p_.startswith("#") or p_.startswith("[Note:"):
            continue
        at = 0
        for m in GILLIES_MARK.finditer(p_):
            add(p_[at:m.start()], at == 0)
            n = int(m.group(1))
            if segs and n <= segs[-1][0]:
                wrong.append(f"§{n} after §{segs[-1][0]}: the marks must rise")
            segs.append([n, ""])
            at = m.end()
        add(p_[at:], at == 0)
    return [(n, t) for n, t in segs], wrong


def write_gillies(slug: str, out: Path, units: list[dict], problems: list[str], drafts: bool = False) -> int:
    """eng-gillies.txt: Gillies's version (1778) of the speeches the 1898 translation lacks, from
    the checked batches of the entries lysias-gillies-NN (kind intro). It is a free version without
    section numbers: each of his paragraphs is filed under the section of Hude's text where it
    begins, which an alignment pass writes at the paragraph's head as `§7 `
    (transcriptions/lysias/GILLIES-ALIGN.md; gillies_segments); his footnotes ([Note: …]) and
    the oration's heading are not shipped. A speech whose paragraphs carry no marks yet is left
    out and named."""
    from .drama import GILLIES_EDITION, LYSIAS_GILLIES
    from .hude_notes import english_stops, paragraphs

    have = {base(u["n"]) for u in units}
    rows: list[str] = []
    done = []
    for speech in sorted(LYSIAS_GILLIES):
        paras = paragraphs(f"lysias-gillies-{speech:02d}", "intro", drafts)
        if paras is None:
            continue
        segs, wrong = gillies_segments(paras)
        if not segs:
            problems.append(f"Gillies, speech {speech}: transcribed, but its paragraphs are not yet placed (§N at each paragraph's head)")
            continue
        problems += [f"Gillies, speech {speech}: {w}" for w in wrong]
        for n, text in segs:
            if f"{speech}.{n}" not in have:
                problems.append(f"Gillies: section {speech}.{n} is not in the Greek")
            rows.append(f"{speech}.{n}\t" + plain(_FOOTNOTE_LETTER.sub("", english_stops(" ".join(text.split())))))
        done.append(speech)
    if rows:
        meta = {"title": PLAYS[slug].title_en, "translator": "John Gillies (1778)", "lang": "eng",
                "source": f"{GILLIES_EDITION} (speeches {', '.join(str(x) for x in done)}); transcribed from the Internet Archive scan "
                          "bim_eighteenth-century_the-orations-of-lysias-a_lysias_1778; a free version, laid beside the Greek by paragraphs",
                "license": "Public domain"}
        (out / "eng-gillies.txt").write_text("\n".join(_meta_lines(meta) + [""] + rows) + "\n", encoding="utf-8")
        print(f"wrote eng-gillies.txt: {len(rows)} paragraphs of speeches {done}")
    return len(rows)


def _batch_text(content: str) -> list[str]:
    """The text lines of a prose batch file (not its flags and notes), the marks taken out."""
    lines, on = [], True
    for raw in content.splitlines():
        if raw.startswith("=== "):
            on = True
        elif raw.startswith("--- "):
            on = False
        if on:
            lines.append(GILLIES_MARK.sub("", raw).rstrip())
    return lines


def check_gillies_marks(speech: int, texts: Path) -> list[str]:
    """After the alignment pass on a speech of Gillies: nothing but the marks may differ from the
    committed (checked) transcription; the marks name sections of the Greek and rise. Prints each
    mark with the first words of the English and of the Greek section, to read down by eye."""
    import subprocess

    from .hude_notes import paragraphs

    slug = f"lysias-gillies-{speech:02d}"
    directory = PIPELINE / "transcriptions" / "drama" / slug
    problems: list[str] = []
    for f in sorted(directory.glob("intro-*.md")):
        rel = f.relative_to(ROOT).as_posix()
        got = subprocess.run(["git", "-C", str(ROOT), "show", f"HEAD:{rel}"], capture_output=True, text=True)
        if got.returncode:
            problems.append(f"{f.name}: not committed yet: commit the checked transcription before the alignment pass")
            continue
        was, now = _batch_text(got.stdout), _batch_text(f.read_text(encoding="utf-8"))
        for d in difflib.unified_diff(was, now, lineterm="", n=0):
            if d[:1] in "+-" and d[:3] not in ("+++", "---"):
                problems.append(f"{f.name}: the text is changed, not only marked: {d[:90]}")
    paras = paragraphs(slug, "intro", True)
    if paras is None:
        return problems + [f"{slug}: no batch file"]
    segs, wrong = gillies_segments(paras)
    problems += wrong
    grc = {}
    for raw in (texts / "lysias" / "grc.txt").read_text(encoding="utf-8").splitlines():
        n, tab, text = raw.partition("\t")
        if tab and n.startswith(f"{speech}.") and n[-1].isdigit():
            grc[int(n.split(".")[1])] = text
    for n, text in segs:
        if n not in grc:
            problems.append(f"§{n}: speech {speech} has no such section")
        print(f"  {speech}.{n:<3} {' '.join(text.split()[:9]):<60} | {' '.join(grc.get(n, '?').split()[:7])}")
    unmarked = [n for n in sorted(grc) if n and n not in {k for k, _ in segs}]
    print(f"speech {speech}: {len(segs)} marks for {len([n for n in grc if n])} sections; sections with no mark of their own: "
          f"{' '.join(str(n) for n in unmarked) or 'none'}")
    return problems


# --- merge -----------------------------------------------------------------------------------

def base(n: str) -> str:
    return re.sub(r"[a-z]$", "", n)


def merge(slug: str, sources: Path, texts: Path, build: Path, lexicon: Path | None = None, drafts: bool = False,
          notes: bool = True) -> int:
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
    correct_apparatus(slug, pages, problems)
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

    by_kind: dict[str, list[int]] = {}
    for k in range(1, SPEECHES + 1):
        by_kind.setdefault(syntax_kind(k), []).append(k)
    meta = {
        "title": play.title, "author": play.author, "lang": "grc",
        "source": f"{play.edition}; read from the Internet Archive scan {play.scan} by OCR, matched word by word to the "
                  f"Perseus Digital Library text ({play.tlg}.tlg001-{SPEECHES:03d}.perseus-grc2, Lamb's Loeb), and checked "
                  "against the scan where the two disagreed",
        "edition": play.edition,
        "license": TRANSCRIPTION_LICENSE,
        "layout": "prose",
        # the text's label, and the speeches that differ from it: hand-made trees, or none
        "syntax": "automatic",
        "syntax-by-book": " ".join(f"{k}={kind}" for kind in ("manual", "none") for k in by_kind.get(kind, [])),
        "pronunciation": play.pronunciation,
    }
    doc = Document(meta=meta)
    book = None
    for u in units:
        b = u["n"].split(".")[0]
        if b != book:
            book = b
            _numeral, title = speech_title(text["titles"].get(int(b), []))
            name = SPEECH_NAMES[int(b)][0]
            if title and _letters(name) != _letters(title):
                problems.append(f"speech {b}: the name “{name}” has other letters than Hude's title “{title}”")
            doc.items.append(Section(1, "book", f"{b} · {name}"))
        # a heading inside a speech (ΜΑΡΤΥΡΕΣ. ΝΟΜΟΣ.) is a section of the second level without a
        # number: the reader shows a section's label on a line of its own before the section's
        # first line, as it shows a play's strophes. A heading after a speech's last line has no
        # line to stand before: its kind is heading-after, and the build ties it to the line before
        for heading in u["before"]:
            doc.items.append(Section(2, "heading", heading))
        if u["para"]:
            doc.items.append(Speaker(""))
        doc.items.append(Line(u["n"], " ".join(w for w, _k in u["words"])))
        for heading in u.get("after", []):
            doc.items.append(Section(2, "heading-after", heading))
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

    # words and syntax, the translation, the commentaries and introduction, the hand-written files
    if lexicon is not None:
        n = tokens(slug, doc, sources, out, lexicon, build)
        print(f"review list: {n} words in {build / f'{slug}-review.tsv'}")
        write_translation(slug, sources, out, units, problems)
        if notes:
            # (left out while the commentary batches are with their checking agents: a batch whose
            # flags are answered may still be waiting for its second reading)
            write_gillies(slug, out, units, problems, drafts)
            from . import hude_notes

            hude_notes.write(texts, slug, sources, build, drafts)
        for path in sorted(STATIC.glob("*")):
            (out / path.name).write_bytes(path.read_bytes())
    log = [f"# merge-lysias {slug}", "", f"## Problems ({len(problems)})", ""] + [f"* {x}" for x in problems]
    log += ["", f"## Apparatus lemmas not found on their lines ({len(misses)})", "",
            "SERIOUS: the text may have slipped to the check text's reading; look at the page. WEAK: a conjecture, a "
            "variant in another order, a note in Latin; read through once.", ""] + [f"* {x}" for x in sorted(misses)]
    (build / f"{slug}-merge.log").write_text("\n".join(log) + "\n", encoding="utf-8")
    print(f"{len(problems)} problems; log in {build / f'{slug}-merge.log'}")
    return len(problems)
