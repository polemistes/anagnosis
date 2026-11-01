"""Nine plays in editions of 1880-1911, one text each (texts/<slug>/): pipeline/PLAN-drama.md.

Aeschylus' Oresteia (Sidgwick, Clarendon Press), Aristophanes' Clouds (Starkie), Frogs (Tucker)
and Lysistrata (Hall-Geldart, Oxford, with Rogers's notes), Euripides' Medea (Earle), Bacchae
(Sandys) and Alcestis (Hayley). For each play the edition's Greek text and critical apparatus
are read from an Internet Archive scan by OCR (drama_pages.py), matched word by word to the
Perseus text (a different edition: the check text, never shipped), and checked by agents
against the page images where the two disagree; the editor's notes and introduction (and
Starkie's translation) are read by OCR and checked word by word where the OCR doubts
(drama_prose.py). merge_play() writes texts/<slug>/ from the checked batch files in
pipeline/transcriptions/drama/<slug>/, the treebank (AGDT, or GLAUx) aligned to the edition's
words, and the translation.

PLAYS holds what each play needs; the leaves of each scan are filled in at step 2 of the brief.
Leaves are the numbers of the scan's JPEG 2000 files (<scan>_jp2.zip: <scan>_0042.jp2); the
Archive's page images (/page/n<N>_w700.jpg) count the pages shown, which for most scans is the
leaf minus one.
"""
from __future__ import annotations

import difflib
import json
import re
import sys
import unicodedata
from dataclasses import dataclass, field
from pathlib import Path

from . import greek

ROOT = Path(__file__).resolve().parent.parent.parent
PIPELINE = ROOT / "pipeline"
TEI = "{http://www.tei-c.org/ns/1.0}"

TRANSCRIPTION_LICENSE = "CC BY-SA 4.0 (transcription; the edition is in the public domain)"


@dataclass
class Play:
    slug: str
    title: str                   # Greek title, as Perseus
    title_en: str
    author: str                  # Greek
    author_en: str
    tlg: str                     # tlg0085.tlg005
    edition: str                 # the edition of text and apparatus, as the title page gives it
    scan: str                    # Internet Archive identifier of the text's scan
    app_editor: str              # file name key of the apparatus: commentary-<app_editor>-apparatus.md
    app_editor_name: str         # "A. Sidgwick"
    product_id: str
    treebank: str = ""           # AGDT file in sources/treebanks/
    glaux: str = ""              # GLAUx file in sources/glaux/
    # the translation: "perseus" (TEI with line numbers), "gutenberg" (the Athenian Society: speeches),
    # "wikisource" (Coleridge's Bacchantes: speeches), "starkie" (transcribed from the scan: trans-NN.md)
    translation: str = "perseus"
    trans_file: str = ""         # under sources/
    translator: str = ""
    trans_key: str = ""          # eng-<trans_key>.txt
    trans_edition: str = ""
    trans_license: str = "Public domain"
    gutenberg_title: str = ""    # the play's heading in the Gutenberg volume (THE FROGS)
    # the commentary and introduction
    notes_editor: str = ""       # commentary-<notes_editor>.md
    notes_editor_name: str = ""
    notes_edition: str = ""
    notes_scan: str = ""         # "" = scan
    # leaves (jp2 numbers) as ranges, filled in at step 2
    text_leaves: list[tuple[int, int]] = field(default_factory=list)
    notes_leaves: list[tuple[int, int]] = field(default_factory=list)
    intro_leaves: list[tuple[int, int]] = field(default_factory=list)
    trans_leaves: list[tuple[int, int]] = field(default_factory=list)
    sigla_leaves: list[int] = field(default_factory=list)
    # the page: "foot" = text, then the apparatus at the foot of the page; "jebb" = the text at the
    # top of the left-hand page with the apparatus under it, continued on the facing page
    layout: str = "foot"
    margin_numbers: str = "right"
    adscript: bool = False       # the edition prints the iota adscript (τῶι): shipped as subscript
    app_langs: tuple[str, str] = ("grc+lat", "lat+grc")
    # how a note begins in the commentary: the line number (group 1), a range end (group 2)
    note_start: str = r"^(?:l{1,2}\.\s*)?(\d{1,4})(?:\s*[-–—]\s*(\d{1,4}))?(?:\s*f{1,2}\.|\s*sqq?\.)?[.,:]?(?=\s|$)"
    speakers: dict[str, str] = field(default_factory=dict)   # the translation's names -> Greek (Perseus) names
    hand_analyses: dict[str, tuple[str, str]] = field(default_factory=dict)  # "line form" -> (lemma, postag)
    lemma_fixes: dict[str, str] = field(default_factory=dict)

    @property
    def perseus(self) -> str:
        return f"drama/{self.tlg}.perseus-grc2.xml"

    @property
    def syntax_automatic(self) -> bool:
        return not self.treebank

    def leaves(self, kind: str) -> list[int]:
        ranges = {"text": self.text_leaves, "notes": self.notes_leaves, "intro": self.intro_leaves,
                  "trans": self.trans_leaves}[kind]
        out: list[int] = []
        for a, b in ranges:
            out += list(range(a, b + 1))
        if kind == "text" and self.layout == "jebb":
            # the Greek on the left-hand pages only, the translation or commentary facing it
            out = [l for l in out if (l - self.text_leaves[0][0]) % 2 == 0]
        return out

    def visible(self, kind: str) -> list[int]:
        """The kind's leaves without those the scan hides (scandata.xml: a leaf the Archive left
        out of its page images, a duplicate or an interleaved sheet). For a Jebb-layout volume the
        text is on every other shown leaf from the first, the translation on the leaves facing it."""
        hidden = hidden_leaves(self.scan_for(kind))
        if self.layout == "jebb" and kind in ("text", "trans"):
            shown = [l for a, b in (self.text_leaves if kind == "text" else self.trans_leaves)
                     for l in range(a, b + 1) if l not in hidden]
            return shown[0::2]
        return [l for l in self.leaves(kind) if l not in hidden]

    def facing(self, leaf: int) -> int:
        """The shown leaf after `leaf` (the right-hand page of its spread)."""
        hidden = hidden_leaves(self.scan)
        nxt = leaf + 1
        while nxt in hidden:
            nxt += 1
        return nxt

    def scan_for(self, kind: str) -> str:
        return self.scan if kind == "text" else (self.notes_scan or self.scan)


def _scandata(scan: str) -> list[tuple[int, bool]]:
    """(leaf number, shown) for every leaf of a scan, from its scandata.xml, cached in
    pipeline/sources/scans/<scan>/scandata.xml. The jp2 files are numbered by these leaf numbers
    (from 0 or from 1, as the scan has it); the page images /page/n<N> count only the leaves shown."""
    import subprocess

    path = PIPELINE / "sources" / "scans" / scan / "scandata.xml"
    if not path.exists():
        path.parent.mkdir(parents=True, exist_ok=True)
        tmp = path.with_suffix(".part")
        r = subprocess.run(["curl", "-sfL", "--retry", "5", "--max-time", "120", "-o", str(tmp),
                            f"https://archive.org/download/{scan}/{scan}_scandata.xml"])
        if r.returncode != 0 or not tmp.exists() or tmp.stat().st_size < 1000:
            # older scans keep it in scandata.zip
            import zipfile

            z = path.with_name("scandata.zip")
            r = subprocess.run(["curl", "-sfL", "--retry", "5", "--max-time", "120", "-o", str(z),
                                f"https://archive.org/download/{scan}/scandata.zip"])
            if r.returncode != 0 or not z.exists():
                raise SystemExit(f"{scan}: neither {scan}_scandata.xml nor scandata.zip could be fetched; try again")
            with zipfile.ZipFile(z) as zf:
                name = next(n for n in zf.namelist() if n.endswith("scandata.xml"))
                tmp.write_bytes(zf.read(name))
        tmp.rename(path)
    t = path.read_text(encoding="utf-8", errors="replace")
    return [(int(n), not re.search(r"<addToAccessFormats>\s*false", body))
            for n, body in re.findall(r'<page leafNum="(\d+)">(.*?)</page>', t, re.S)]


def hidden_leaves(scan: str) -> set[int]:
    """The leaves a scan's scandata.xml marks as not shown (a duplicate, an interleaved sheet)."""
    return {n for n, shown in _scandata(scan) if not shown}


def leaf_of(scan: str, n: int) -> int:
    """The leaf (jp2 number) of the Archive's page image n<N>."""
    shown = [leaf for leaf, ok in _scandata(scan) if ok]
    return shown[n]


SIDGWICK_NOTE = r"^[lI1|]{1,2}\.\s*(\d{1,4})(?:\s*[-–—]\s*(\d{1,4}))?(?:\s*f{1,2}\.|\s*sqq?\.)?[.,:]?(?=\s|$)"

PLAYS: dict[str, Play] = {p.slug: p for p in [
    Play("agamemnon", "Ἀγαμέμνων", "Agamemnon", "Αἰσχύλος", "Aeschylus", "tlg0085.tlg005",
         "Aeschylus: Agamemnon, with introduction and notes by A. Sidgwick, third edition, revised, Oxford, Clarendon Press, 1887",
         "agamemnonwithint00aescuoft", "sidgwick", "A. Sidgwick", "aeschylus_agamemnon_sidgwick",
         treebank="tlg0085.tlg005.perseus-grc1.tb.xml",
         # text pp. 1-61 (leaves 47-48, the title of Part II, are bound in after p. 16); notes pp. 3-79 (Part II); introduction pp. vii-xxiii and the persons;
         # the manuscripts, the editors' abbreviations and the signs of the text: pp. xix-xxii
         text_leaves=[(31, 46), (49, 91)], notes_leaves=[(93, 169)], intro_leaves=[(11, 27), (30, 30)], sigla_leaves=[23, 24, 25, 26],
         trans_file="drama/tlg0085.tlg005.perseus-eng3.xml", translator="Herbert Weir Smyth", trans_key="smyth",
         trans_edition="Aeschylus, with an English translation by Herbert Weir Smyth, vol. II, Loeb Classical Library, 1926",
         trans_license="CC BY-SA 4.0 (Perseus Digital Library, modernized by Perseus)",
         notes_editor="sidgwick", notes_editor_name="Arthur Sidgwick", note_start=SIDGWICK_NOTE),
    Play("choephoroi", "Χοηφόροι", "Choephoroi", "Αἰσχύλος", "Aeschylus", "tlg0085.tlg006",
         "Aeschylus: Choephoroi, with introduction and notes by A. Sidgwick, Oxford, Clarendon Press, 1884",
         "choephoroiwithin00aescuoft", "sidgwick", "A. Sidgwick", "aeschylus_choephoroi_sidgwick",
         treebank="tlg0085.tlg006.perseus-grc2.tb.xml",
         # text pp. 3-43, notes pp. 45-121, introduction pp. vii-xxvii and the persons; the leaves
         # the scan hides (28-29, 52-53, 62-63, 70-71, 92-93) are skipped (Play.visible)
         text_leaves=[(37, 83)], notes_leaves=[(85, 163)], intro_leaves=[(11, 33), (36, 36)],
         sigla_leaves=[26, 27, 30, 31, 32, 33],
         trans_file="drama/tlg0085.tlg006.perseus-eng2.xml", translator="Herbert Weir Smyth", trans_key="smyth",
         trans_edition="Aeschylus, with an English translation by Herbert Weir Smyth, vol. II, Loeb Classical Library, 1926",
         trans_license="CC BY-SA 4.0 (Perseus Digital Library, modernized by Perseus)",
         notes_editor="sidgwick", notes_editor_name="Arthur Sidgwick", note_start=SIDGWICK_NOTE),
    Play("eumenides", "Εὐμενίδες", "Eumenides", "Αἰσχύλος", "Aeschylus", "tlg0085.tlg007",
         "Aeschylus: Eumenides, with introduction and notes by A. Sidgwick, vol. I, introduction and text, Oxford, Clarendon Press, 1887",
         "eumenideswithint01aescuoft", "sidgwick", "A. Sidgwick", "aeschylus_eumenides_sidgwick",
         treebank="tlg0085.tlg007.perseus-grc1.tb.xml",
         # Vol. I only (introduction and text): the notes volume was never scanned (PLAN-drama.md,
         # Decisions); text pp. 35-74, introduction pp. 7-31 and the persons, sigla pp. 25-30
         text_leaves=[(37, 76)], intro_leaves=[(9, 33), (36, 36)], sigla_leaves=[27, 28, 29, 30, 31, 32],
         trans_file="drama/tlg0085.tlg007.perseus-eng2.xml", translator="Herbert Weir Smyth", trans_key="smyth",
         trans_edition="Aeschylus, with an English translation by Herbert Weir Smyth, vol. II, Loeb Classical Library, 1926",
         trans_license="CC BY-SA 4.0 (Perseus Digital Library, modernized by Perseus)",
         notes_editor="sidgwick", notes_editor_name="Arthur Sidgwick", note_start=SIDGWICK_NOTE),
    Play("clouds", "Νεφέλαι", "Clouds", "Ἀριστοφάνης", "Aristophanes", "tlg0019.tlg003",
         "The Clouds of Aristophanes, with introduction, English prose translation, critical notes and commentary by W. J. M. Starkie, London, Macmillan, 1911",
         "cloudsofaristoph00aris_0", "starkie", "W. J. M. Starkie", "aristophanes_clouds_starkie",
         glaux="0019-003.xml", translation="starkie", translator="W. J. M. Starkie", trans_key="starkie",
         notes_editor="starkie", notes_editor_name="W. J. M. Starkie", layout="jebb",
         text_leaves=[(108, 414)], trans_leaves=[(109, 415)], notes_leaves=[(108, 415)],
         intro_leaves=[(19, 98), (101, 107)], sigla_leaves=[67, 68, 69, 70]),
    Play("medea", "Μήδεια", "Medea", "Εὐριπίδης", "Euripides", "tlg0006.tlg003",
         "The Medea of Euripides, with introduction and notes by Mortimer Lamson Earle, New York, American Book Company, 1904",
         "cu31924079583609", "earle", "M. L. Earle", "euripides_medea_earle",
         glaux="0006-003.xml",
         trans_file="drama/tlg0006.tlg003.perseus-eng2.xml", translator="E. P. Coleridge", trans_key="coleridge",
         trans_edition="The Plays of Euripides, translated by E. P. Coleridge, London, George Bell and Sons, 1891",
         trans_license="CC BY-SA 4.0 (Perseus Digital Library)",
         notes_editor="earle", notes_editor_name="Mortimer Lamson Earle", layout="jebb"),
    Play("frogs", "Βάτραχοι", "Frogs", "Ἀριστοφάνης", "Aristophanes", "tlg0019.tlg009",
         "The Frogs of Aristophanes, with introduction and commentary by T. G. Tucker, London, Macmillan, 1906",
         "frogsofaristopha00arisrich", "tucker", "T. G. Tucker", "aristophanes_frogs_tucker",
         glaux="0019-009.xml", translation="gutenberg", trans_file="gutenberg/pg8689.txt",
         gutenberg_title="THE FROGS", translator="The Athenian Society", trans_key="athenian",
         trans_edition="The Eleven Comedies, literally and completely translated from the Greek tongue into English, London, The Athenian Society, 1912, vol. II (Project Gutenberg #8689)",
         notes_editor="tucker", notes_editor_name="T. G. Tucker",
         app_langs=("grc+eng", "eng+grc")),
    Play("bacchae", "Βάκχαι", "Bacchae", "Εὐριπίδης", "Euripides", "tlg0006.tlg017",
         "The Bacchae of Euripides, with critical and explanatory notes by John Edwin Sandys, third edition, Cambridge, University Press, 1892",
         "BacchaeOfEuripides_680", "sandys", "J. E. Sandys", "euripides_bacchae_sandys",
         glaux="0006-017.xml", translation="wikisource", trans_file="coleridge",
         translator="E. P. Coleridge", trans_key="coleridge",
         trans_edition="The Plays of Euripides, translated by E. P. Coleridge, vol. II, London, G. Bell and Sons, 1913 (Wikisource)",
         trans_license="Public domain; Wikisource transcription CC BY-SA 4.0",
         notes_editor="sandys", notes_editor_name="John Edwin Sandys"),
    Play("alcestis", "Ἄλκηστις", "Alcestis", "Εὐριπίδης", "Euripides", "tlg0006.tlg002",
         "The Alcestis of Euripides, edited with an introduction and critical and exegetical notes by H. W. Hayley, Boston, Ginn & Company, 1898",
         "alcestisofeuripi00euriuoft", "hayley", "H. W. Hayley", "euripides_alcestis_hayley",
         glaux="0006-002.xml",
         trans_file="drama/tlg0006.tlg002.perseus-eng2.xml", translator="E. P. Coleridge", trans_key="coleridge",
         trans_edition="The Plays of Euripides, translated by E. P. Coleridge, London, George Bell and Sons, 1891",
         trans_license="CC BY-SA 4.0 (Perseus Digital Library)",
         notes_editor="hayley", notes_editor_name="Harry Wilson Hayley",
         app_langs=("grc+eng", "eng+grc")),
    Play("lysistrata", "Λυσιστράτη", "Lysistrata", "Ἀριστοφάνης", "Aristophanes", "tlg0019.tlg007",
         "Aristophanis Comoediae, recognoverunt brevique adnotatione critica instruxerunt F. W. Hall et W. M. Geldart, tomus II, Oxford, Clarendon Press, 1907",
         "aristophaniscomo02arisuoft", "hall-geldart", "F. W. Hall and W. M. Geldart", "aristophanes_lysistrata_hall_geldart",
         glaux="0019-007.xml", translation="gutenberg", trans_file="gutenberg/pg8688.txt",
         gutenberg_title="LYSISTRATA", translator="The Athenian Society", trans_key="athenian",
         trans_edition="The Eleven Comedies, literally and completely translated from the Greek tongue into English, London, The Athenian Society, 1912, vol. I (Project Gutenberg #8688)",
         notes_editor="rogers", notes_editor_name="Benjamin Bickley Rogers",
         notes_edition="The Lysistrata of Aristophanes, with a translation into corresponding metres, introduction and commentary by Benjamin Bickley Rogers, London, George Bell and Sons, 1911",
         notes_scan="aristophaniscomo04aris"),
]}


# ---------------------------------------------------------------- the Perseus text

APOS = "ʼ"
_ELISION = re.compile(r"(?<=[Ͱ-Ͽἀ-῿])['’᾽](?=\s|$|[,.;·:!?)\]⟩—])")


def skel(s: str, adscript: bool = False) -> str:
    """A word's letters, lower case, without accents, breathings or punctuation; with `adscript`,
    an iota subscript counts as an iota (the edition prints it beside the letter: τῶι)."""
    s = unicodedata.normalize("NFD", s.lower())
    if adscript:
        s = s.replace("ͅ", "ι")
    s = "".join(c for c in s if unicodedata.category(c) in ("Ll", "Lu", "Lo"))
    return unicodedata.normalize("NFC", s).replace("ς", "σ")


def base(n: str) -> int:
    m = re.match(r"\d+", n)
    return int(m.group()) if m else -1


def _flatten(el, parts: list[str], gaps: list[int]) -> None:
    """The text of a verse: <del> in [ ], <add> in ⟨ ⟩, <q> without marks (the editions print
    none), notes left out, a <gap> as the mark \x00."""
    from lxml import etree

    if el.text:
        parts.append(el.text)
    for child in el:
        if not isinstance(child.tag, str):
            if child.tail:
                parts.append(child.tail)
            continue
        tag = etree.QName(child).localname
        if tag in ("note", "milestone", "pb", "lb"):
            pass
        elif tag == "gap":
            parts.append(" \x00 ")
        elif tag == "del":
            parts.append("[")
            _flatten(child, parts, gaps)
            parts.append("]")
        elif tag == "add":
            parts.append("⟨")
            _flatten(child, parts, gaps)
            parts.append("⟩")
        elif tag == "stage":
            parts.append("(")
            _flatten(child, parts, gaps)
            parts.append(")")
        else:
            _flatten(child, parts, gaps)
        if child.tail:
            parts.append(child.tail)


def _words_of(text: str) -> list[tuple[str, bool]]:
    """(word, a gap follows) for the words of a verse; punctuation standing alone joins the word
    before; brackets opened or closed beside a space join the word beside them."""
    text = greek.nfc(re.sub(r"\s+", " ", text))
    text = _ELISION.sub(APOS, text)
    text = re.sub(r"(?<=[Ͱ-Ͽἀ-῿][.,;·])(?=[Ͱ-Ͽἀ-῿])", " ", text)  # a space Perseus lost: στρατωθέν.οἴκτῳ
    text = re.sub(r"([⟨\[(])\s+", r"\1", text)
    text = re.sub(r"\s+([⟩\])])", r"\1", text)
    out: list[list] = []
    for raw in text.split():
        if raw == "\x00":
            if out:
                out[-1][1] = True
            continue
        gap = "\x00" in raw
        raw = raw.replace("\x00", "")
        if not skel(raw):
            if out and raw:
                out[-1][0] += raw
            continue
        out.append([raw, gap])
    return [(w, g) for w, g in out]


def perseus_play(path: Path) -> dict:
    """The Perseus text of a play as the drama route uses it:

    tokens: the words in order, {'t', 'skel', 'n' (the Perseus line's number, '15b'), 'base' (15),
        'li' (index into lines), 'first' (the line's first word), 'speaker', 'newsp' (a new speaker
        begins at this word), 'gap' (Perseus marks lost text after it), 'si' (index into speeches)};
        a word divided at the end of a verse (ὀρχη- | σμοῖς) is one word, on the first verse;
    lines: {'n', 'base', 'words': [token indexes], 'gap'} for every <l> (a lost verse has no words);
    sections: (index into lines of the section's first verse, level, kind, label);
    stages: (index into tokens of the word the direction follows, -1 before all; text);
    speakers: the names in order of appearance."""
    from lxml import etree

    root = etree.parse(str(path)).getroot()
    body = root.find(f".//{TEI}body")
    tokens: list[dict] = []
    lines: list[dict] = []
    sections: list[tuple[int, int, str, str]] = []
    stages: list[tuple[int, str]] = []
    speakers: list[str] = []
    state = {"speaker": "", "last": None, "pending": False, "si": -1}

    def add_line(el) -> None:
        n = (el.get("n") or "").strip()
        if n == "0":
            return  # a speaker's name repeated for display
        parts: list[str] = []
        _flatten(el, parts, [])
        words = _words_of("".join(parts))
        li = len(lines)
        # a lost verse: Perseus marks a <gap>, or prints only metrical signs or nothing (Eum. 353-359)
        line = {"n": n, "base": base(n), "words": [], "gap": not words and ("\x00" in "".join(parts) or not skel("".join(parts)))}
        lines.append(line)
        if line["gap"] and tokens:
            tokens[-1]["gap"] = True
        for k, (w, gap) in enumerate(words):
            # the second half of a word divided at the end of the verse before
            if k == 0 and tokens and tokens[-1]["t"].endswith("-") and re.search(r"[Ͱ-Ͽἀ-῿]-$", tokens[-1]["t"]) \
                    and tokens[-1]["li"] == li - 1 and not state["pending"]:
                prev = tokens[-1]
                prev["t"] = prev["t"][:-1] + w
                prev["skel"] = skel(prev["t"])
                prev["gap"] = prev["gap"] or gap
                prev["joined"] = True
                continue
            tok = {"t": w, "skel": skel(w), "n": n, "base": line["base"], "li": li, "first": not line["words"],
                   "speaker": state["speaker"], "newsp": state["pending"], "gap": gap, "si": state["si"]}
            state["pending"] = False
            line["words"].append(len(tokens))
            tokens.append(tok)

    def walk(node, depth: int) -> None:
        for child in node:
            if not isinstance(child.tag, str):
                continue
            tag = etree.QName(child).localname
            if tag == "div":
                if child.get("type") == "textpart" and (child.get("subtype") or "").lower() not in ("cast_list",):
                    kind = (child.get("subtype") or "div").rstrip(".").lower()
                    sections.append((len(lines), depth, kind, child.get("n") or ""))
                    walk(child, depth + 1)
                elif child.get("type") != "textpart":
                    walk(child, depth)
            elif tag == "sp":
                sp = child.find(f"{TEI}speaker")
                name = re.sub(r"\s+", " ", "".join(sp.itertext())).strip().rstrip(".") if sp is not None else ""
                name = greek.nfc(name)
                if name and name != state["last"]:
                    state["pending"] = True
                    state["si"] += 1
                    if name not in speakers:
                        speakers.append(name)
                    state["last"] = name
                state["speaker"] = name or state["speaker"]
                walk(child, depth)
            elif tag == "l":
                add_line(child)
            elif tag == "stage":
                text = greek.nfc(re.sub(r"\s+", " ", "".join(child.itertext())).strip())
                if text:
                    stages.append((len(tokens) - 1, text))
            elif tag in ("speaker", "milestone", "pb", "note", "head", "listPerson", "p"):
                pass
            else:
                walk(child, depth)

    walk(body, 1)
    # sections that hold no verse of their own (a heading div around others) begin with the next
    return {"tokens": tokens, "lines": lines, "sections": sections, "stages": stages, "speakers": speakers}


# ---------------------------------------------------------------- numbering the printed verses

LETTERS = "abcdefghijklmnopqrstuvwxyz"


def number_verses(verses: list[list[int]], toks: list[dict]) -> list[tuple[str, list[str]]]:
    """The edition's verses numbered by the rule of the brief: a printed verse (a list of token
    indexes, in order) takes the number of the Perseus line its first word stands in; a second
    printed verse that begins in the same Perseus line gets a letter (401a, 401b); a verse that
    covers several Perseus lines carries the first number, and the numbers it covers are skipped.
    Perseus's own letters (15b for the second part of a shared verse) count as their line's
    number (15). Numbers never go back: a verse whose first word stands in an earlier line than
    the verse before takes that verse's number with a letter, and is flagged. Returns
    (number, flags) per verse."""
    out: list[tuple[str, list[str]]] = []
    last = -1
    used = 0
    for words in verses:
        flags: list[str] = []
        if not words:
            out.append((f"{last}{LETTERS[used]}" if last >= 0 else "0", ["a verse without words"]))
            used += 1
            continue
        t = toks[words[0]]
        b = t["base"]
        if b > last:
            n, last, used = str(b), b, 0
        else:
            if b < last:
                flags.append(f"the Perseus line numbers go back here (the first word stands in Perseus line {t['n']}, "
                             f"the verse before is numbered {last}): check the print's numbering")
            n = f"{last}{LETTERS[used]}"
            used += 1
            if b == last:
                flags.append(f"lettered: a second verse in Perseus line {t['n']}")
        out.append((n, flags))
    return out


# ---------------------------------------------------------------- the batch files

def read_text_batches(directory: Path, files: list[Path] | None = None) -> dict[str, dict]:
    """The text batches' page blocks by stem: {'items': [('@', name) | ('!', text) | (n, text)],
    'apparatus': [(n, item)], 'notes': [str], 'batch': name, 'errors': [str]}."""
    pages: dict[str, dict] = {}
    for path in files if files is not None else sorted(directory.glob("batch-*.md")):
        stem, section = None, None
        for k, raw in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
            m = re.match(r"^=== (p-\d{4})\s*$", raw)
            if m:
                stem = m.group(1)
                pages[stem] = {"items": [], "apparatus": [], "notes": [], "batch": path.name, "errors": []}
                section = None
                continue
            m = re.match(r"^--- (text|apparatus|notes)\s*$", raw)
            if m:
                section = m.group(1)
                continue
            if stem is None or section is None or not raw.strip():
                continue
            block = pages[stem]
            if section == "notes":
                block["notes"].append(raw.strip())
                continue
            if section == "text":
                if raw.startswith("@"):
                    block["items"].append(("@", greek.nfc(raw[1:].strip())))
                    continue
                if raw.startswith("!"):
                    block["items"].append(("!", greek.nfc(raw[1:].strip())))
                    continue
            n, sep, body = raw.partition("\t")
            if not sep:
                block["errors"].append(f"line {k}: no TAB: {raw[:60]!r}")
                continue
            block["items" if section == "text" else "apparatus"].append((n.strip(), greek.nfc(body.strip())))
    return pages


LINE_N = re.compile(r"^(\d+)([a-z]?)$")
APP_N = re.compile(r"^(\d+)([a-z]?)(?:-(\d+)([a-z]?))?$")


def line_key(n: str) -> tuple[int, str] | None:
    m = LINE_N.match(n)
    return (int(m.group(1)), m.group(2)) if m else None


# ---------------------------------------------------------------- the edition's lines against Perseus

def perseus_map(lines: list[tuple[str, str]], pers: dict) -> dict[int, int]:
    """For each Perseus line (index into pers['lines']), the index of our line that holds its first
    word, by a word alignment of the two texts; a Perseus line whose words were not found goes
    with the line of the next word that was."""
    ours: list[tuple[str, int]] = []
    for i, (_n, text) in enumerate(lines):
        for w, _s, _e in greek.words(text):
            ours.append((skel(w), i))
    toks = pers["tokens"]
    sm = difflib.SequenceMatcher(None, [s for s, _i in ours], [t["skel"] for t in toks], autojunk=False)
    at: list[int | None] = [None] * len(toks)
    for a, b, size in sm.get_matching_blocks():
        for k in range(size):
            at[b + k] = ours[a + k][1]
    # unmatched words take the line of the next matched word (or the last line)
    nxt = len(lines) - 1 if lines else 0
    for j in range(len(toks) - 1, -1, -1):
        if at[j] is None:
            at[j] = nxt
        else:
            nxt = at[j]
    # never back
    best = 0
    for j in range(len(toks)):
        best = max(best, at[j])
        at[j] = best
    out: dict[int, int] = {}
    for li, line in enumerate(pers["lines"]):
        if line["words"]:
            out[li] = at[line["words"][0]]
    # a verse without words (lost) goes with the next verse that has words
    following = len(lines)
    for li in range(len(pers["lines"]) - 1, -1, -1):
        if li in out:
            following = out[li]
        else:
            out[li] = following
    return out


def perseus_number_map(lines: list[tuple[str, str]], pers: dict) -> dict[str, str]:
    """Perseus line number (as the translations cite it) -> our line number."""
    idx = perseus_map(lines, pers)
    out: dict[str, str] = {}
    for li, line in enumerate(pers["lines"]):
        i = idx.get(li, len(lines))
        if i < len(lines):
            out.setdefault(line["n"], lines[i][0])
    return out


# ---------------------------------------------------------------- translations

def perseus_translation(path: Path) -> list[tuple[str, str, str]]:
    """A Perseus translation in verse-numbered TEI: (Perseus line number, speaker, text) for each
    <l>, and ("!", "", text) for a stage direction between verses; the display line n="0" left out;
    a stage direction inside a verse kept in parentheses."""
    from lxml import etree

    root = etree.parse(str(path)).getroot()
    body = root.find(f".//{TEI}body")
    out: list[tuple[str, str, str]] = []
    speaker = [""]

    def text_of(el) -> str:
        parts = [el.text or ""]
        for child in el:
            if isinstance(child.tag, str):
                tag = etree.QName(child).localname
                if tag == "stage":
                    parts.append(" (" + re.sub(r"\s+", " ", "".join(child.itertext())).strip() + ") ")
                elif tag == "note":
                    pass
                elif tag == "del":
                    parts.append("[" + text_of(child) + "]")
                else:
                    parts.append(text_of(child))
            parts.append(child.tail or "")
        return "".join(parts)

    def walk(node) -> None:
        for child in node:
            if not isinstance(child.tag, str):
                continue
            tag = etree.QName(child).localname
            if tag == "sp":
                sp = child.find(f"{TEI}speaker")
                speaker[0] = re.sub(r"\s+", " ", "".join(sp.itertext())).strip().rstrip(".") if sp is not None else ""
                walk(child)
            elif tag == "l":
                n = (child.get("n") or "").strip()
                if n == "0" or not n:
                    continue
                text = re.sub(r"\s+", " ", text_of(child)).strip()
                text = re.sub(r"\(\s+", "(", re.sub(r"\s+\)", ")", text))
                if text:
                    out.append((n, speaker[0], text))
            elif tag == "stage":
                st = re.sub(r"\s+", " ", "".join(child.itertext())).strip()
                if st:
                    out.append(("!", "", st))
            elif tag in ("speaker", "note", "head", "milestone", "pb"):
                pass
            else:
                walk(child)

    walk(body)
    return out


def gutenberg_speeches(path: Path, title: str) -> list[tuple[str, str]]:
    """The Athenian Society's translation of one play from its Gutenberg volume: (speaker as
    printed, text) for each speech; a stage direction between speeches is a speech of speaker ''."""
    text = path.read_text(encoding="utf-8").replace("\r\n", "\n")
    # the play: after its title, its introduction and its dramatis personae, the title again
    # follows a row of asterisks; it ends at the next row of asterisks with a title, or the notes
    starts = [m.end() for m in re.finditer(rf"\*\s+\*\s+\*\s+\*\s+\*\s*\n+\s*{re.escape(title)}\s*\n", text)]
    if len(starts) < 2:
        raise SystemExit(f"{path}: the play {title} not found")
    body = text[starts[1]:]
    end = re.search(r"\n\s*\*\s+\*\s+\*\s+\*\s+\*\s*\n|\n[A-Z][A-Z ]{3,}\n\n\n|\nFOOTNOTES", body)
    body = body[: end.start()] if end else body
    paras = [re.sub(r"\s+", " ", p).strip() for p in re.split(r"\n\s*\n", body)]
    out: list[tuple[str, str]] = []
    speech = re.compile(r"^((?:[A-ZÉÈÂ][A-Za-zÉÈÂéèâ'\-]*\.?\s)*?[A-ZÉÈÂ][A-ZÉÈÂ'\-]+)(\s*\(_[^)]*_\))?\.\s+(.*)$")
    for p in paras:
        if not p:
            continue
        p = re.sub(r"\[\d+\]", "", p)  # footnote numbers
        p = re.sub(r"_([^_]+)_", r"*\1*", p)
        m = speech.match(p)
        if m and m.group(1).upper() == m.group(1):
            who = m.group(1).strip()
            rest = ((m.group(2) or "").strip() + " " + m.group(3)).strip()
            out.append((who, rest))
        elif out and out[-1][0]:
            out[-1] = (out[-1][0], out[-1][1] + " " + p)
        else:
            out.append(("", p))
    return out


def wikisource_speeches(directory: Path, pages: range = range(99, 142)) -> list[tuple[str, str]]:
    """Coleridge's Bacchantes from the Wikisource pages (sources/coleridge/bacchantes-NN.wiki):
    (speaker as printed, text) for each speech."""
    from .symposium import _wiki_to_text

    raw = ""
    for n in pages:
        p = directory / f"bacchantes-{n}.wiki"
        t = p.read_text(encoding="utf-8")
        t = re.sub(r"<noinclude>.*?</noinclude>", "", t, flags=re.S)
        raw += t.rstrip() + ("\n" if t.rstrip().endswith((".", "!", "?", "”", "’")) else " ")
    raw = re.sub(r"\{\{sc\|([^}]*)\}\}", lambda m: m.group(1).upper(), raw)
    raw = re.sub(r"''([^']+)''", r"*\1*", raw)
    text = _wiki_to_text(raw)
    paras = [re.sub(r"\s+", " ", p).strip() for p in re.split(r"\n\s*\n|\n(?=[A-Z][A-Z]+\.\s)", text)]
    out: list[tuple[str, str]] = []
    for p in paras:
        m = re.match(r"^([A-Z][A-Z]+(?:\s+[A-Z]+)?)\.\s+(.*)$", p)
        if m:
            out.append((m.group(1), m.group(2)))
        elif out:
            out[-1] = (out[-1][0], out[-1][1] + " " + p)
    return out


_SENT = re.compile(r"(?<=[.?!;:])(?:['’\"”)*]*)\s+(?=\S)")


def greek_speeches(items: list) -> list[dict]:
    """The speeches of our Greek text: {'speaker', 'lines': [(n, chars)], 'chars'}."""
    out: list[dict] = []
    for kind, a, b in items:
        if kind == "@":
            out.append({"speaker": a, "lines": [], "chars": 0})
        elif kind == "line":
            if not out:
                out.append({"speaker": "", "lines": [], "chars": 0})
            out[-1]["lines"].append((a, len(b)))
            out[-1]["chars"] += len(b) + 1
    return [s for s in out if s["lines"]]


def align_speeches(eng: list[tuple[str, str]], grc: list[dict], names: dict[str, str]) -> dict[int, int]:
    """Pair the translation's speeches with the Greek ones (as gorgias._speech_places does): by
    speaker (the translation's names mapped by `names`) and length. Returns Greek speech ->
    English speech."""
    import math

    def who(name: str) -> str:
        key = re.sub(r"\s+", " ", name.upper().strip().rstrip("."))
        return names.get(key, names.get(name, ""))

    js = [(who(s), len(t)) for s, t in eng]
    gs = [(g["speaker"], g["chars"]) for g in grc]
    ratio = sum(x[1] for x in js) / max(1, sum(x[1] for x in gs))
    n, m = len(js), len(gs)
    NEG = -1e18
    score = [[NEG] * (m + 1) for _ in range(n + 1)]
    back = [[0] * (m + 1) for _ in range(n + 1)]
    score[0][0] = 0.0
    for i in range(n + 1):
        for j in range(m + 1):
            if i == 0 and j == 0:
                continue
            best, how = NEG, 0
            if i > 0 and j > 0 and score[i - 1][j - 1] > NEG:
                same = js[i - 1][0] == gs[j - 1][0] and js[i - 1][0] != ""
                d = abs(math.log((js[i - 1][1] + 20) / (gs[j - 1][1] * ratio + 20)))
                v = score[i - 1][j - 1] + (2.0 - d if same else -1.0 - d)
                if v > best:
                    best, how = v, 3
            if i > 0 and score[i - 1][j] > NEG and score[i - 1][j] - 1.2 > best:
                best, how = score[i - 1][j] - 1.2, 1  # an English speech (or stage direction) without a Greek one
            if j > 0 and score[i][j - 1] > NEG and score[i][j - 1] - 1.5 > best:
                best, how = score[i][j - 1] - 1.5, 2  # a Greek speech the translation joins to another
            score[i][j], back[i][j] = best, how
    pair: dict[int, int] = {}
    i, j = n, m
    while i > 0 or j > 0:
        how = back[i][j]
        if how == 3:
            pair[j - 1] = i - 1
            i, j = i - 1, j - 1
        elif how == 1:
            i -= 1
        else:
            j -= 1
    return pair


def speech_segments(eng: list[tuple[str, str]], grc: list[dict], names: dict[str, str],
                    every: int = 10) -> tuple[list[tuple[str, str, str]], list[str]]:
    """The translation as (first Greek line, speaker, text) segments: each English speech at the
    first line of its Greek speech, a long speech cut at sentence ends about every `every` Greek
    lines, in proportion to the Greek. An English speech without a Greek partner joins the
    segment before (a stage direction: as its own paragraph). Returns segments and problems."""
    pair = align_speeches(eng, grc, names)
    by_eng = {e: g for g, e in pair.items()}
    problems: list[str] = []
    segs: list[tuple[str, str, str]] = []
    for e, (speaker, text) in enumerate(eng):
        g = by_eng.get(e)
        if g is None:
            if segs:
                n, sp, t = segs[-1]
                segs[-1] = (n, sp, t + " " + (f"{speaker.title()}: " if speaker else "") + text)
            else:
                problems.append(f"translation: no Greek speech for the first speech ({speaker}: {text[:50]})")
            continue
        lines = grc[g]["lines"]
        if len(lines) <= every * 1.5:
            segs.append((lines[0][0], speaker, text))
            continue
        # cut points: every `every` lines, at the sentence end nearest to the proportional place
        total = sum(c for _n, c in lines)
        ends = sorted({0} | {m.end() for m in _SENT.finditer(text)})
        cuts = [(0, lines[0][0])]
        acc = 0
        for k, (n, c) in enumerate(lines):
            if k and k % every == 0 and len(lines) - k >= every // 2:
                target = int(len(text) * acc / total)
                pos = min(ends, key=lambda e: abs(e - target))
                if pos > cuts[-1][0] and pos < len(text):
                    cuts.append((pos, n))
            acc += c
        for k, (pos, n) in enumerate(cuts):
            end = cuts[k + 1][0] if k + 1 < len(cuts) else len(text)
            piece = text[pos:end].strip()
            if piece:
                segs.append((n, speaker if k == 0 else "", piece))
    unpaired = [grc[g]["lines"][0][0] for g in range(len(grc)) if g not in pair]
    if unpaired:
        problems.append(f"translation: {len(unpaired)} Greek speeches without an English speech of their own "
                        f"(joined to the one before): {', '.join(unpaired[:40])}")
    # keep the anchors increasing and unique
    out: list[tuple[str, str, str]] = []
    for n, sp, t in segs:
        if out and _ord(n) <= _ord(out[-1][0]):
            pn, psp, pt = out[-1]
            out[-1] = (pn, psp, pt + " " + (f"{sp.title()}: " if sp else "") + t)
            continue
        out.append((n, sp, t))
    return out, problems


def _ord(n: str) -> tuple[int, str]:
    m = LINE_N.match(n)
    return (int(m.group(1)), m.group(2)) if m else (-1, "")


# ---------------------------------------------------------------- the commentary

def note_heading(raw: str, regex: str) -> tuple[str, int] | None:
    """A note's heading from the start of its paragraph: ('779', length of the label) or
    ('1345-1451', …); "215 f." and "215 ff." give 215; "1058, 1059" gives 1058-1059."""
    m2 = re.match(r"^(?:[lI1|]{1,2}\.\s*)?(\d{1,4}),\s*(\d{1,4})[.,:]?(?=\s)", raw)
    if m2 and int(m2.group(2)) == int(m2.group(1)) + 1 and re.match(regex, raw):
        return f"{m2.group(1)}-{m2.group(2)}", m2.end()
    m = re.match(regex, raw)
    if not m:
        return None
    a, b = m.group(1), m.group(2) if m.lastindex and m.lastindex >= 2 else None
    if b and len(b) < len(a):  # 1345-51
        b = a[: len(a) - len(b)] + b
    if b and int(b) <= int(a):
        b = None
    return (f"{a}-{b}" if b else a), m.end()


_GREEK_WORD = r"[Ͱ-Ͽἀ-῿ʼ’᾽]+"


def bold_lemma(text: str) -> str:
    """The Greek at the start of a note, up to its colon, comma, bracket, stop or the first word
    in Latin letters, in bold: "κρίσιν ποεῖν: not = …" -> "**κρίσιν ποεῖν**: not = …"."""
    if text.startswith("**"):
        return text
    m = re.match(rf"^((?:[‘“(\[]?{_GREEK_WORD}[’”)\]]?(?:\s*(?:\.\.\.|…|—)\s*|\s+)?)+?)(?=[,:;.\]]|\s+[A-Za-z(‘“]|$)", text)
    if not m or not re.search(r"[Ͱ-Ͽἀ-῿]", m.group(1)):
        return text
    lemma = m.group(1).strip()
    return f"**{lemma}**" + text[len(m.group(1).rstrip()):]


def split_notes(paragraphs: list[str], regex: str) -> list[tuple[str, list[str]]]:
    """Paragraphs of the notes (in page order; a page's run-on paragraph already joined) as notes:
    a paragraph that begins with a line number begins a note; its lemma in bold; a paragraph
    without a number belongs to the note before."""
    notes: list[tuple[str, list[str]]] = []
    for p in paragraphs:
        h = note_heading(p, regex)
        if h:
            heading, end = h
            body = bold_lemma(p[end:].strip())
            notes.append((heading, [body] if body else []))
        elif notes:
            notes[-1][1].append(p)
        else:
            notes.append(("", [p]))
    return notes


def notes_from_paragraphs(paras: list[str]) -> list[tuple[str, list[str]]]:
    """The checked notes (paragraphs, with headings '## 779' or '## 1345-1451') as notes."""
    notes: list[tuple[str, list[str]]] = []
    for p in paras:
        m = re.match(r"^##\s+(\d+[a-z]?(?:-\d+[a-z]?)?)\s*$", p)
        if m:
            notes.append((m.group(1), []))
        elif notes:
            notes[-1][1].append(p)
        else:
            notes.append(("", [p]))
    return notes


def _lemma_line(body: list[str], n: int, lines: dict[str, str]) -> str | None:
    """The line near n (n-4 … n+3) that holds the first word of the note's bold lemma."""
    m = re.match(r"^(?:\[\d+[a-z]?\]\s*)?\*\*([^*]+)\*\*", body[0]) if body else None
    if not m:
        return None
    words = [skel(w) for w, _s, _e in greek.words(m.group(1))]
    if not words or not words[0]:
        return None
    near = [(abs(base(k) - n), k) for k in lines if n - 4 <= base(k) <= n + 3
            and words[0] in [skel(w) for w, _s, _e in greek.words(lines[k])]]
    return min(near)[1] if near else None


def place_notes(notes: list[tuple[str, list[str]]], numbers: list[str],
                texts: dict[str, str] | None = None) -> tuple[list[tuple[str, list[str]]], list[str]]:
    """Notes under our line numbers: a heading names a line we have (1234 or 1234a) or a range; a
    note on a line our numbering skips goes to the nearest earlier line. Returns the notes (those
    on the same heading merged) and problems."""
    have = set(numbers)
    bases = sorted({base(n) for n in numbers if base(n) >= 0})
    problems: list[str] = []
    out: list[tuple[str, list[str]]] = []
    for heading, body in notes:
        if not heading:
            problems.append(f"notes: a note without a line number before the first note: {(body[0] if body else '')[:60]}")
            continue
        a, _, b = heading.partition("-")
        found = _lemma_line(body, base(a), texts) if a not in have and texts else None
        if found:
            problems.append(f"notes: line {a} is not in our numbering; the note goes to {found}, which holds its lemma")
            a = found
        if a not in have:
            earlier = [x for x in bases if x <= base(a)]
            if not earlier:
                problems.append(f"notes: no line for the note on {heading}")
                continue
            new = str(earlier[-1])
            problems.append(f"notes: line {a} is not in our numbering; the note goes to {new}")
            a = new
        if b and (b not in have or base(b) <= base(a)):
            later = [x for x in bases if base(a) < x <= base(b)]
            b = str(later[-1]) if later else ""
        h = f"{a}-{b}" if b else a
        if out and out[-1][0] == h:
            out[-1][1].extend(body)
        else:
            out.append((h, list(body)))
    return out, problems


# ---------------------------------------------------------------- merge

def _meta_lines(meta: dict[str, str]) -> list[str]:
    return [f"# {k}: {v}" for k, v in meta.items() if v]


def merge_play(slug: str, sources: Path, texts: Path, build: Path, lexicon: Path,
               transcriptions: Path | None = None) -> int:
    """texts/<slug>/ from the checked batch files; safe to run again at any time. Writes what its
    inputs allow (the text and apparatus once text batches exist; the notes, introduction and a
    transcribed translation once theirs do) and pipeline/build/<slug>-merge.log. Returns the number
    of problems."""
    from .textfmt import Document, Line, Section, Speaker, Stage, write_file

    play = PLAYS[slug]
    transcriptions = transcriptions or PIPELINE / "transcriptions" / "drama" / slug
    pages_dir = build / "drama-pages" / slug
    out = texts / slug
    problems: list[str] = []
    index_path = pages_dir / "pages.json"
    if not index_path.exists() or not any(transcriptions.glob("batch-*.md")):
        print(f"{slug}: no text batches yet")
        return 0
    index = json.loads(index_path.read_text(encoding="utf-8"))
    pages = read_text_batches(transcriptions)
    pers = perseus_play(sources / play.perseus)
    speakers = set(pers["speakers"])

    # the text, page by page
    items: list[tuple[str, str, str]] = []  # ('@', name, '') | ('!', text, '') | ('line', n, text)
    seen: set[str] = set()
    last_key: tuple[int, str] | None = None
    for p in index:
        block = pages.get(p["stem"])
        if block is None:
            problems.append(f"{p['stem']}: not transcribed")
            continue
        for e in block["errors"]:
            problems.append(f"{p['stem']}: {e}")
        for a, b in block["items"]:
            if a == "@":
                if b not in speakers:
                    problems.append(f"{p['stem']}: speaker {b!r} is not one of Perseus's names")
                items.append(("@", b, ""))
            elif a == "!":
                items.append(("!", b, ""))
            else:
                key = line_key(a)
                if key is None:
                    problems.append(f"{p['stem']}: bad line number {a!r}")
                    continue
                if a in seen:
                    problems.append(f"{p['stem']}: line {a} twice; the second left out")
                    continue
                if last_key is not None and key <= last_key:
                    problems.append(f"{p['stem']}: line {a} follows {last_key[0]}{last_key[1]}")
                seen.add(a)
                last_key = key
                items.append(("line", a, b.replace("’", APOS)))
    lines = [(a, b) for kind, a, b in items if kind == "line"]
    if not lines:
        print(f"{slug}: the batches hold no lines")
        return 0

    # sections from the Perseus TEI, re-attached by words
    pmap = perseus_map(lines, pers)
    line_pos = {}
    k = 0
    for i, (kind, a, _b) in enumerate(items):
        if kind == "line":
            line_pos[k] = i
            k += 1
    before: dict[int, list[Section]] = {}
    for li, level, kind, label in pers["sections"]:
        target = pmap.get(li, len(lines))
        if target >= len(lines):
            problems.append(f"section {kind} {label} (Perseus line {pers['lines'][li]['n'] if li < len(pers['lines']) else 'end'}): no line after it")
            continue
        at = line_pos[target]
        # before the speaker and stage lines that directly precede the line
        while at > 0 and items[at - 1][0] in ("@", "!"):
            at -= 1
        before.setdefault(at, []).append(Section(level, kind, label))
    meta = {
        "title": play.title, "author": play.author, "lang": "grc",
        "source": f"{play.edition}; read from the Internet Archive scan {play.scan} by OCR, matched word by word to the "
                  f"Perseus Digital Library text ({play.tlg}.perseus-grc2), and checked against the scan where the two disagreed",
        "edition": play.edition,
        "license": TRANSCRIPTION_LICENSE,
    }
    if play.syntax_automatic:
        meta["syntax"] = "automatic"
    doc = Document(meta=meta)
    for i, (kind, a, b) in enumerate(items):
        for s in before.get(i, []):
            doc.items.append(s)
        if kind == "@":
            doc.items.append(Speaker(a))
        elif kind == "!":
            doc.items.append(Stage(a))
        else:
            doc.items.append(Line(a, b))
    out.mkdir(parents=True, exist_ok=True)
    write_file(out / "grc.txt", doc)
    print(f"wrote {out / 'grc.txt'}: {len(lines)} lines from {len(pages)} pages")

    # the critical apparatus
    have = {n for n, _t in lines}
    notes: list[tuple[str, list[str]]] = []
    for p in index:
        block = pages.get(p["stem"])
        if block is None:
            continue
        for n, item in block["apparatus"]:
            m = APP_N.match(n)
            if not m:
                problems.append(f"{p['stem']}: bad apparatus number {n!r}")
                continue
            heading = n
            if notes and notes[-1][0] == heading:
                notes[-1][1].append(item)
            else:
                notes.append((heading, [item]))
    from .sophocles_pages import bold_lemmas

    # an item numbered as the edition numbers a verse our text lacks goes to the nearest earlier
    # line, its printed number kept in front of it
    placed, probs = place_notes([(h, [b if APP_N.match(h) and h.split("-")[0] in have else f"[{h}] {b}" for b in body])
                                 for h, body in notes], [n for n, _t in lines], dict(lines))
    problems += [p.replace("notes:", "apparatus:") for p in probs]
    notes = placed
    md = _meta_lines({
        "title": f"Critical apparatus ({play.app_editor_name})",
        "author": play.app_editor_name,
        "lang": "eng" if play.app_langs[1].startswith("eng") else "lat",
        "source": f"{play.edition}; transcribed from the Internet Archive scan {play.scan}",
        "license": TRANSCRIPTION_LICENSE,
    }) + [""]
    for heading, body in notes:
        md.append(f"## {heading}")
        md.append(bold_lemmas("\n\n".join(body)))
        md.append("")
    (out / f"commentary-{play.app_editor}-apparatus.md").write_text("\n".join(md) + "\n", encoding="utf-8")
    print(f"wrote commentary-{play.app_editor}-apparatus.md: {len(notes)} notes, {sum(len(b) for _h, b in notes)} items")

    # lemmas, morphology, syntax
    review = _tokens(play, doc, sources, out, lexicon, build)
    print(f"review list: {review} words in {build / f'{slug}-review.tsv'}")

    # the translation
    _translation(play, sources, out, lines, items, pers, problems, transcriptions)

    # the commentary
    from .drama_prose import merge_kind

    paras = merge_kind(transcriptions, "notes")
    if paras:
        raw = notes_from_paragraphs(paras)
        placed, probs = place_notes(raw, [n for n, _t in lines], dict(lines))
        problems += probs
        md = _meta_lines({
            "title": f"Commentary ({play.notes_editor_name})",
            "author": play.notes_editor_name, "lang": "eng",
            "source": f"{play.notes_edition or play.edition}, the notes; transcribed from the Internet Archive scan {play.scan_for('notes')}",
            "license": TRANSCRIPTION_LICENSE,
        }) + [""]
        for heading, body in placed:
            md.append(f"## {heading}")
            md.append("\n\n".join(body))
            md.append("")
        (out / f"commentary-{play.notes_editor}.md").write_text("\n".join(md) + "\n", encoding="utf-8")
        print(f"wrote commentary-{play.notes_editor}.md: {len(placed)} notes")
    paras = merge_kind(transcriptions, "intro")
    if paras:
        md = _meta_lines({
            "title": "Introduction", "author": play.notes_editor_name,
            "source": f"{play.notes_edition or play.edition}, the introduction; transcribed from the Internet Archive scan {play.scan_for('intro')}",
            "license": TRANSCRIPTION_LICENSE,
        }) + [""] + ["\n\n".join(paras)]
        (out / "introduction.md").write_text("\n".join(md).rstrip() + "\n", encoding="utf-8")
        print(f"wrote introduction.md: {sum(1 for p in paras if p.startswith('#'))} headings")

    log = build / f"{slug}-merge.log"
    log.write_text("\n".join(problems) + "\n", encoding="utf-8")
    print(f"{len(problems)} problems ({log})")
    return len(problems)


def _tokens(play: Play, doc, sources: Path, out: Path, lexicon: Path, build: Path) -> int:
    from .import_perseus import LEMMA_FIXES, write_syntax_nodes, write_tokens
    from .odyssey import align, fix_lemma, syntax_nodes
    from .odyssey_merge import Analyser, Frequencies, choose_analysis
    from .sophocles import read_agdt, read_glaux_lines

    tb = read_agdt(sources / "treebanks" / play.treebank) if play.treebank else read_glaux_lines(sources / "glaux" / play.glaux)
    rows, _warnings = align(doc, tb, keep_tb_form=True)
    analyse = Analyser(lexicon)
    freq = Frequencies(sources / "treebanks")
    review = []
    for r in rows:
        tb_form = r.pop("tb_form", "")
        same = tb_form and greek.strip_diacritics(tb_form) == greek.strip_diacritics(r["form"])
        if r["lemma"] and r["postag"] and (same or not tb_form):
            continue
        chosen = choose_analysis(r["form"], analyse(r["form"]), r["postag"], r["lemma"], freq, tb_form)
        who = "the treebank" if play.treebank else "GLAUx"
        reason = (f"no lemma or parse in {who}" if same
                  else f"reads {r['form']} where {who} has {tb_form}" if tb_form
                  else f"a word {who} splits" if "+" in r["word_id"] else f"not in {who}")
        if chosen is not None:
            r["lemma"], r["postag"] = fix_lemma(chosen[0]), chosen[1]
        review.append({"line": r["line"], "form": r["form"], "lemma": r["lemma"], "postag": r["postag"], "reason": reason})
    # a word Perseus (and so the treebank) divides between two verses is whole in ours: the
    # treebank's two halves give "+κνεφάζω", "θυτήρ+θυτήρ", "τρία+τριακτήρ"; the second half's
    # lemma is the word's where it continues the first's letters
    for r in rows:
        if "+" in r["lemma"] and "+" in r["word_id"]:
            parts = r["lemma"].split("+")
            first, last = parts[0], parts[-1]
            if len(parts) == 2 and (not first or greek.strip_diacritics(last).lower().startswith(greek.strip_diacritics(first).lower()[:3])):
                r["lemma"] = last
    from .drama_fixes import HAND_ANALYSES, LEMMA_FIXES as PLAY_LEMMA_FIXES

    hands = {**play.hand_analyses, **HAND_ANALYSES.get(play.slug, {})}
    fixes = {**play.lemma_fixes, **PLAY_LEMMA_FIXES.get(play.slug, {})}
    for r in rows:
        hand = hands.get(f"{r['line']} {r['form']}")
        if hand:
            r["lemma"], r["postag"] = hand
        r["lemma"] = LEMMA_FIXES.get(r["lemma"], r["lemma"])
        r["lemma"] = fixes.get(r["lemma"], r["lemma"])
    write_tokens(out / "tokens.tsv", rows)
    used = {(r["sentence"], w) for r in rows for w in r["word_id"].split("+") if r["sentence"]}
    write_syntax_nodes(out / "syntax-nodes.tsv", syntax_nodes(tb, used))
    missing = sum(1 for r in rows if not r["lemma"])
    print(f"wrote tokens.tsv: {len(rows)} words, {missing} without lemma")
    build.mkdir(parents=True, exist_ok=True)
    with (build / f"{play.slug}-review.tsv").open("w", encoding="utf-8") as f:
        f.write("line\tform\tlemma\tpostag\treason\n")
        for r in review:
            f.write(f"{r['line']}\t{r['form']}\t{r['lemma']}\t{r['postag']}\t{r['reason']}\n")
    return len(review)


def _translation(play: Play, sources: Path, out: Path, lines: list[tuple[str, str]], items: list,
                 pers: dict, problems: list[str], transcriptions: Path) -> None:
    meta = {"title": play.title_en, "translator": play.translator, "lang": "eng",
            "source": play.trans_edition, "license": play.trans_license}
    eng: list[str] = []
    if play.translation == "perseus":
        rows = perseus_translation(sources / play.trans_file)
        nmap = perseus_number_map(lines, pers)
        order = {n: i for i, (n, _t) in enumerate(lines)}
        meta["source"] = f"Perseus Digital Library, {Path(play.trans_file).stem}: {play.trans_edition}; its line numbers mapped to the edition's"
        segs: list[list] = []  # [our n, speaker, text, stage directions before it]
        speaker = None
        stages: list[str] = []
        for n, sp, text in rows:
            if n == "!":
                stages.append(text)
                continue
            ours = nmap.get(n)
            if ours is None:
                m = re.match(r"\d+", n)
                cands = [x for x in nmap if re.match(r"\d+", x) and int(re.match(r"\d+", x).group()) <= int(m.group())] if m else []
                ours = nmap[max(cands, key=lambda x: (base(x), x))] if cands else lines[0][0]
                problems.append(f"translation: Perseus line {n} not in the Greek; placed at {ours}")
            new_speaker = sp != speaker
            if segs and order[ours] <= order[segs[-1][0]]:
                segs[-1][2] += "".join(f" ({x})" for x in stages) + " " + (f"{sp}: " if new_speaker and sp else "") + text
            else:
                segs.append([ours, sp if new_speaker else "", text, stages])
            stages = []
            speaker = sp
        for n, sp, text, before in segs:
            for x in before:
                eng.append(f"!\t{x}")
            if sp:
                eng.append(f"@ {sp}")
            eng.append(f"{n}\t{text}")
        for x in stages:
            eng.append(f"!\t{x}")
    elif play.translation in ("gutenberg", "wikisource"):
        speeches = (gutenberg_speeches(sources / play.trans_file, play.gutenberg_title) if play.translation == "gutenberg"
                    else wikisource_speeches(sources / play.trans_file))
        grc = greek_speeches(items)
        segs3, probs = speech_segments(speeches, grc, {k.upper(): v for k, v in play.speakers.items()})
        problems += probs
        unknown = sorted({s for s, _t in speeches if s and s.upper() not in {k.upper() for k in play.speakers}})
        if unknown:
            problems.append(f"translation: speakers not in SPEAKERS: {', '.join(unknown)}")
        for n, sp, text in segs3:
            if sp:
                eng.append(f"@ {sp.title()}")
            eng.append(f"{n}\t{text}")
    elif play.translation == "starkie":
        from .drama_prose import merge_translation

        segs4 = merge_translation(transcriptions)
        meta["source"] = f"{play.edition}, the translation; transcribed from the Internet Archive scan {play.scan}"
        meta["license"] = TRANSCRIPTION_LICENSE
        have = {n for n, _t in lines}
        for sp, n, text in segs4:
            if n not in have:
                problems.append(f"translation: line {n} not in the Greek")
            if sp:
                eng.append(f"@ {sp}")
            eng.append(f"{n}\t{text}")
    if not eng:
        return
    path = out / f"eng-{play.trans_key}.txt"
    path.write_text("\n".join(_meta_lines(meta) + [""] + eng) + "\n", encoding="utf-8")
    print(f"wrote {path.name}: {sum(1 for l in eng if not l.startswith('@'))} segments")


def main_merge(slug: str) -> int:
    return merge_play(slug, PIPELINE / "sources", ROOT / "texts", PIPELINE / "build", ROOT / "data" / "lexicon.sqlite")


if __name__ == "__main__":
    sys.exit(main_merge(sys.argv[1]))
