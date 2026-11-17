"""Nine plays in editions of 1880-1911, one text each (texts/<slug>/): pipeline/PLAN-drama.md.

Aeschylus' Oresteia (Sidgwick, Clarendon Press), Aristophanes' Clouds (Starkie), Frogs (Tucker)
and Lysistrata (Hall-Geldart, Oxford, with Rogers's notes), Euripides' Medea (since 2026-11-16
Murray's Oxford text with Earle's notes, private until 2028: PLAN-euripides.md), Bacchae (Sandys)
and Alcestis (Hayley; both to move to Murray's text by PLAN-euripides.md). For each play the edition's Greek text and critical apparatus
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
    # "wikisource" (Coleridge's Bacchantes: speeches), "starkie" (transcribed from the scan: trans-NN.md),
    # "kept" (made by another command and left as it is: Jebb's Sophocles, eng-jebb.txt from
    # Perseus by import-sophocles; the merge writes no translation)
    translation: str = "perseus"
    trans_file: str = ""         # under sources/
    translator: str = ""
    trans_key: str = ""          # eng-<trans_key>.txt
    trans_edition: str = ""
    trans_license: str = "Public domain"
    # a stage direction inside a verse of Perseus's translation set apart from the speech (before
    # the verse when it stands before its words, else after it) instead of in parentheses within
    # it (the Medea; the plays made earlier keep theirs inline)
    trans_stages_apart: bool = False
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
    # an appendix of longer notes in prose (Jebb's Sophocles: the Appendix after the commentary),
    # read like an introduction (drama_prose kind "appendix") and written as appendix.md
    appendix_leaves: list[tuple[int, int]] = field(default_factory=list)
    sigla_leaves: list[int] = field(default_factory=list)
    # critical notes printed apart from the text pages (Earle's "Notes on the text", an appendix)
    app_leaves: list[tuple[int, int]] = field(default_factory=list)
    # the page: "foot" = text, then the apparatus at the foot of the page; "jebb" = the text at the
    # top of the left-hand page with the apparatus under it, continued on the facing page;
    # "earle" = the text at the top of every page, the commentary under it in two columns in
    # smaller type, no rule, no apparatus (the critical notes are in app_leaves)
    layout: str = "foot"
    margin_numbers: str = "right"
    adscript: bool = False       # the edition prints the iota adscript (τῶι): shipped as subscript
    app_langs: tuple[str, str] = ("grc+lat", "lat+grc")
    # the apparatus items' numbers stand without a stop (Rzach: "215 ἧς scripsi")
    app_bare_numbers: bool = False
    # the apparatus crop runs to the foot of the page (Rzach: a last line Tesseract reads too badly
    # to count as print would otherwise fall outside it)
    app_to_foot: bool = False
    # the commentary's region on a page of the notes scan: "" = as the layout says; "paley" = the
    # two columns under the text and Paley's bands (everything below the last line that crosses
    # the page's middle); "earle" = everything under the verses at the top of the page, found by
    # the two columns of small type (drama_prose.earle_top); "hayley" = Hayley's notes at the back of
    # his book: one column, every note an indented paragraph opened by its bold number, further
    # bold lemmas run on inside the paragraph after a sentence's end ("… ἑστίαν. **αἰνέσαι** : …")
    # "college" = the college editions of Lysias (Adams, Morgan): the text at the top of the page,
    # the notes under it in two columns in smaller type, no rule; a note opens an indented paragraph
    # with its section number, further lemmas follow after a dash (read as Jebb's commentary);
    # "back" = Shuckburgh's Lysias: notes at the back of the book in one column, numbered by the
    # lines of his own text, each speech's under a heading "ORATION IV. [10.]" with his introduction
    notes_layout: str = ""
    # the highest number a note can carry (a speech's last section, or the last line of the
    # commentator's own text) where no text of this slug exists to take it from
    last_note: int = 0
    # the introduction's footnotes stand in two columns under its text (Morgan's Lysias)
    intro_foot_columns: bool = False
    # an eighteenth-century print with the long s (Gillies's Lysias, 1778): written s
    long_s: bool = False
    # words the text prints apart and the treebank as one (αἵ θʼ for αἵθʼ) form a unit on the
    # treebank word's node (odyssey.align, units): a change of tokens, so a text's own choice
    tree_units: bool = False
    # the text the syntax trees were made on, where it is another than the printed edition (the
    # Perseus text of another editor): named in grc.txt's header ("syntax-text") and so in the
    # database, and what each word is to that text recorded in syntax-text.tsv (syntax_text.py)
    syntax_text: str = ""
    # leaves of the notes scan read with another kind (the introduction) that are laid out as the
    # notes pages and take their region (Earle's notes on the hypothesis under his Greek, "earle")
    notes_region_leaves: list[tuple[int, int]] = field(default_factory=list)
    # a note on a verse our numbering lacks, filed under the nearest earlier verse (place_notes),
    # keeps the printed number in front ("[1056] **…**"), as the apparatus always does (Earle's
    # notes on Murray's text, whose numbering differs from Earle's in places)
    notes_refile_mark: bool = False
    # a paragraph of a note whose bold lemma is not in the verse (or range) the note is filed under
    # but in a verse up to three lines away goes to that verse, the printed number in front
    # (follow_lemmas; Hayley's Alcestis, whose numbering differs from Murray's in places)
    notes_follow_lemma: bool = False
    # letters the edition's typeface makes Tesseract read otherwise (Rzach's Teubner: ϑ for θ),
    # put right in the OCR before it is matched; letters counted as one in the matching (Tesseract
    # reads the Teubner κ as χ): pairs "χκ" = χ counts as κ
    ocr_fold: dict[str, str] = field(default_factory=dict)
    skel_fold: str = ""
    # "numeric": the check text's verses put in the order of their numbers (Evelyn-White moves
    # Theogony 214 before 213 and 434 before 430; Rzach prints them in their order)
    perseus_order: str = ""
    # check-text verses the edition does not print in its text (the Metis fragment, Theogony
    # 929a-929t, which Rzach keeps among the fragments): left out of the check text
    perseus_drop: tuple[str, ...] = ()
    # the reading voice's pronunciation (grc.txt's "pronunciation" key: homeric, attic, koine);
    # "" = the reader's default (Attic for every author but Homer)
    pronunciation: str = ""
    # how a note begins in the commentary: the line number (group 1), a range end (group 2)
    note_start: str = r"^(?:l{1,2}\.\s*)?(\d{1,4})(?:\s*[-–—]\s*(\d{1,4}))?(?:\s*f{1,2}\.|\s*sqq?\.)?[.,:]?(?=\s|$)"
    speakers: dict[str, str] = field(default_factory=dict)   # the translation's names -> Greek (Perseus) names
    hand_analyses: dict[str, tuple[str, str]] = field(default_factory=dict)  # "line form" -> (lemma, postag)
    lemma_fixes: dict[str, str] = field(default_factory=dict)
    # a prose text read by lucian_pages.py (pipeline/PLAN-true-story.md): the printed page is
    # leaf - page_offset (Nilén's Lucian: p. 133 = leaf 200); the apparatus is what stands under
    # the short rule below the text ("short") rather than the small type found from the foot up
    page_offset: int = 0
    # "under" (Jebb's Sophocles, layout "jebb"): no rule between the verses and the apparatus;
    # the apparatus is the small type directly above the one rule that heads the commentary
    app_rule: str = ""
    # the running head: lines that end above this share of the page's height (Jebb's head stands lower)
    head_frac: float = 0.075
    # the verse's type size is this quantile of the sizes of the lines in the page's upper 70 %
    # (0.5, the median; Murray's Euripides 0.75: a long apparatus reaches up into that part of
    # the page and would pull the median down to its own smaller type)
    verse_size_q: float = 0.5
    # the printer's signature at the foot of some pages ("EUR. I. 6", a lone "6*" at the right)
    # is not part of the apparatus (Murray's Oxford text)
    foot_signature: bool = False
    # the apparatus block found from the foot up ends where the step to the next line up is wider
    # than the apparatus's own line pitch allows (Murray: the last verse, whose type Tesseract
    # sometimes sizes as small as the apparatus's, stands a verse's pitch above it)
    app_pitch_cut: bool = False
    # the edition prints metrical labels at the right of a strophe's first verse ("[στρ.", "[ἀντ.",
    # Murray): not a bracket of the text
    metre_labels: bool = False
    # the check text is the same editor's text (Jebb's, from Perseus): where it changes speaker
    # and the print has something in the left margin that Tesseract garbles, the change counts
    # as printed and is not flagged
    speaker_trust: bool = False
    # the commentary's own text (Jerram's Greek, whose line numbers his notes cite), read only to
    # map those line numbers to ours
    notes_text_leaves: list[tuple[int, int]] = field(default_factory=list)
    # the text on every other leaf of its ranges, from the first (Lake's Loeb: the Greek on the
    # left-hand pages, his translation facing it)
    leaf_step: int = 1
    # pages of the text read apart from the rest (the Latin end of the Shepherd: Lake prints the
    # Latin version where manuscript A breaks off), as leaf ranges with the same step
    latin_leaves: list[tuple[int, int]] = field(default_factory=list)
    # the commentary and introduction from more than one scan (Taylor's Shepherd of Hermas, two
    # volumes): [(scan, [(first leaf, last leaf)])] per kind; when set it replaces notes_scan and
    # notes_leaves / intro_leaves for that kind. Each page's stem carries its volume (p-1NNNN for
    # the first scan, p-2NNNN for the second) so that leaves of two scans never meet
    notes_sources: dict[str, list[tuple[str, list[tuple[int, int]]]]] = field(default_factory=dict)
    # stretches of a prose page left out by rule (a list of editions inside a chapter of the
    # introduction, the commentator's own Greek hypothesis): (scan, leaf, first line, last line,
    # marker): the lines from the first that matches `first` ("" = the page's first) to the last that
    # matches `last` ("" = the page's end, footnotes included) are not read; `marker` ("" = none) is
    # written as a paragraph where they stood (drama_prose.analyse_page)
    prose_omit: list[tuple[str, int, str, str, str]] = field(default_factory=list)
    # the module that reads the text pages: "" (drama_pages, or lucian_pages when page_offset is set),
    # "lake" (lake_pages: the batches in transcriptions/<slug>/, notes headed by the traditional
    # reference, ## Mandate 4.1.2)
    route: str = ""
    # the check text from a file in our own text format (under pipeline/transcriptions/) instead
    # of the canonical Perseus TEI: Jebb's Sophocles, whose Perseus text (TEI P4, Jebb's own) was
    # imported by sophocles.py and frozen as sophocles/<slug>/reference-grc.txt
    check_text: str = ""
    # the divisions of the play as the commentator gives them, (first verse, name): the top-level
    # sections are moved to begin at these verses and named after them (sophocles.align_part_starts,
    # label_parts, merge_repeated_subsections, as for Jebb's Sophocles); parts_window = how far
    # (in verses) a check-text section may lie from a division's first verse to be moved there
    # (Earle's Medea: Perseus begins the parodos with the anapaests at 96, Earle at 131)
    parts: list[tuple[int, str]] = field(default_factory=list)
    parts_window: int = 6
    # the licence line of the files that hold the edition's text or apparatus, where "the edition
    # is in the public domain" would not be true everywhere (Murray's Oxford text: free in the
    # United States, protected in Norway, the EU and the UK until the end of 2027); "" = the
    # usual TRANSCRIPTION_LICENSE
    edition_license: str = ""
    # grc.txt's `syntax:` line when the trees are hand-made but are not the AGDT's on this
    # edition (the Medea: the Pedalion trees, made on a later text); "" = "automatic" for GLAUx,
    # nothing for an AGDT treebank
    syntax_note: str = ""
    # leaves the scan's own page list hides (scandata: "Delete") that are pages of the text all
    # the same (Hude's Lysias: two openings exist only as the camera's uncropped frames, leaves
    # 36-37 and 44-45, which the Archive's reader therefore lacks): kept by visible()
    unhide: tuple[int, ...] = ()

    @property
    def perseus(self) -> str:
        return f"drama/{self.tlg}.perseus-grc2.xml"

    @property
    def syntax_automatic(self) -> bool:
        return not self.treebank and not self.syntax_note

    @property
    def text_license(self) -> str:
        return self.edition_license or TRANSCRIPTION_LICENSE

    def leaves(self, kind: str) -> list[int]:
        ranges = {"text": self.text_leaves, "notes": self.notes_leaves, "intro": self.intro_leaves,
                  "trans": self.trans_leaves, "latin": self.latin_leaves, "appendix": self.appendix_leaves}[kind]
        out: list[int] = []
        for a, b in ranges:
            out += list(range(a, b + 1, self.leaf_step if kind in ("text", "latin") else 1))
        if kind == "text" and self.layout == "jebb":
            # the Greek on the left-hand pages only, the translation or commentary facing it
            out = [l for l in out if (l - self.text_leaves[0][0]) % 2 == 0]
        return out

    def visible(self, kind: str) -> list[int]:
        """The kind's leaves without those the scan hides (scandata.xml: a leaf the Archive left
        out of its page images, a duplicate or an interleaved sheet). For a Jebb-layout volume the
        text is on every other shown leaf from the first, the translation on the leaves facing it."""
        hidden = hidden_leaves(self.scan_for(kind)) - set(self.unhide)
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
        if kind in self.notes_sources:
            return self.notes_sources[kind][0][0]
        return self.scan if kind in ("text", "latin") else (self.notes_scan or self.scan)

    def sources_for(self, kind: str) -> list[tuple[str, list[int]]]:
        """The scans and shown leaves of a prose kind: [(scan, leaves)], one entry unless the kind
        has notes_sources."""
        if kind in self.notes_sources:
            out = []
            for scan, ranges in self.notes_sources[kind]:
                hidden = hidden_leaves(scan)
                out.append((scan, [l for a, b in ranges for l in range(a, b + 1) if l not in hidden]))
            return out
        return [(self.scan_for(kind), self.visible(kind))]


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


# Hayley's Alcestis: "Verse 1." opens his first note, then "2.", "28-37.", "86 ff."
HAYLEY_NOTE = r"^(?:Verses?\s+|Vss?\.\s*)?(\d{1,4})(?:\s*[-–—]\s*(\d{1,4}))?(?:\s*f{1,2}\.|\s*sqq?\.)?[.,:]?(?=\s|$)"
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
    # Euripides in Murray's Oxford text (pipeline/PLAN-euripides.md): PRIVATE until 2028-01-01
    # (private.py; texts/medea and pipeline/transcriptions/drama/medea are links into private/).
    # Murray's text and apparatus; the check text is Perseus's grc2 file, which is Murray's own
    # text (the same scan), so the two are one edition; Earle's notes and introduction beside it
    Play("medea", "Μήδεια", "Medea", "Εὐριπίδης", "Euripides", "tlg0006.tlg003",
         "Euripidis Fabulae, recognovit brevique adnotatione critica instruxit Gilbertus Murray, tomus I, Oxford, Clarendon Press, 1902",
         "euripidisfabulae01euriuoft", "murray", "G. Murray", "euripides_medea_murray",
         glaux="0006-003.xml",
         trans_file="drama/tlg0006.tlg003.perseus-eng2.xml", translator="E. P. Coleridge", trans_key="coleridge",
         trans_edition="The Plays of Euripides, translated by E. P. Coleridge, London, George Bell and Sons, 1891",
         trans_license="CC BY-SA 4.0 (Perseus Digital Library)", trans_stages_apart=True,
         # Murray died in 1957: his edition is free in the United States (published before 1931),
         # and in Norway, the EU and the UK only from 2028 (pipeline/PLAN-euripides.md)
         edition_license="CC BY-SA 4.0 (transcription); Murray's edition is in the public domain in the United States, "
                         "and in Norway, the EU and the UK from 1 January 2028",
         # the hand-made Pedalion trees (GLAUx 0006-003, all sentences manual), made on a later text
         syntax_note="hand-made (Pedalion trees, with GLAUx), made on a later edition of the text than Murray's",
         notes_editor="earle", notes_editor_name="Mortimer Lamson Earle",
         notes_edition="The Medea of Euripides, edited by Mortimer Lamson Earle, New York, Cincinnati, Chicago, American Book Company, 1904",
         notes_scan="cu31924079583609", notes_layout="earle",
         # the check text is Murray's own: where it changes speaker and the margin holds something
         # Tesseract garbles, the change counts as printed (as for Jebb's Sophocles)
         speaker_trust=True,
         # the apparatus items' numbers stand without a stop (the verse number, then the lemma); a long
         # apparatus reaches high up the page; the printer's signature under it on some pages
         app_bare_numbers=True, verse_size_q=0.75, foot_signature=True, app_pitch_cut=True,
         head_frac=0.065,  # the running head ends above 0.060 of the page, the first verse below 0.072
         metre_labels=True,
         # Murray (euripidisfabulae01euriuoft; leaf = page image n + 1; leaves 0 and 381-385
         # hidden): title page leaf 9 (Tomus I; the verso, leaf 10, "Excudebat Horatius Hart"),
         # Praefatio pp. iii-xi = leaves 11-19, Fabularum ordo 20, Codicum catalogus 21-23, Sigla
         # leaf 24. The Medea: half-title with the ΥΠΟΘΕΣΙΣ ΜΗΔΕΙΑΣ leaf 102 and the
         # hypotheses' end (Aristophanes') leaf 103, both with their Latin apparatus and line
         # numbers at the left; ΤΑ ΤΟΥ ΔΡΑΜΑΤΟΣ ΠΡΟΣΩΠΑ with Murray's notes on the persons and the
         # codices leaf 104; the text vv. 1-1419 leaves 105-161 (162 blank, the Heraclidae from 163).
         # Earle (notes scan cu31924079583609; p = leaf - 7 throughout, no hidden leaves): his
         # text with the commentary under it in two columns pp. 73-247 = leaves 80-254 (the notes
         # run on inside paragraphs: "— 20. **ἡ δύστηνος**: …"); introduction pp. 7-64 = leaves
         # 14-71 (title page leaf 8); the half-title leaf 72, his Greek hypothesis with his notes on
         # it in two columns under it pp. 66-71 = leaves 73-78 (his Greek not used, Murray's is; his
         # notes are, in the introduction), his persons p. 72 = leaf 79 (not used: Murray's are);
         # the codices pp. 255-259 and his "Notes on the text of this edition" pp. 267-294
         # = leaves 274-301 (not used: Murray's apparatus is the apparatus). OCR of Earle's
         # leaves is on disk (pipeline/build/drama-scans/cu31924079583609/).
         text_leaves=[(105, 161)], sigla_leaves=[24], notes_leaves=[(80, 254)], intro_leaves=[(14, 71)],
         # the introduction document (pipeline/PLAN-euripides.md, "Medea: the introduction"): Earle's
         # introduction (leaves 14-71, pp. 7-64), then Murray's ancient hypotheses with his apparatus
         # (vol. I leaves 102-103), then Earle's notes on the hypothesis (leaves 73-78, pp. 66-71,
         # the two columns under his Greek, which is not used), then Murray's persons page (leaf 104);
         # merged in this order (the stems p-1…, p-2…, p-3…, p-4…)
         notes_sources={"intro": [("cu31924079583609", [(14, 71)]), ("euripidisfabulae01euriuoft", [(102, 103)]),
                                  ("cu31924079583609", [(73, 78)]), ("euripidisfabulae01euriuoft", [(104, 104)])]},
         notes_region_leaves=[(73, 78)], notes_refile_mark=True,
         # Earle's "Divisions of the play" (introduction § 32, after Aristotle's Poetics ch. 12)
         parts=[(1, "Prologue"), (131, "Parodos"), (214, "First episode"), (410, "First stasimon"),
                (446, "Second episode"), (627, "Second stasimon"), (663, "Third episode"),
                (824, "Third stasimon"), (866, "Fourth episode"), (976, "Fourth stasimon"),
                (1002, "Fifth episode"), (1251, "Fifth stasimon"), (1293, "Exodos")],
         parts_window=40),
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
    # Euripides from Murray's Oxford text (pipeline/PLAN-euripides.md; private until 2028-01-01):
    # the Alcestis's text and apparatus are Murray's, vol. I, the same scan and page as the Medea;
    # Hayley (Ginn 1898) is the commentary and introduction beside it
    Play("alcestis", "Ἄλκηστις", "Alcestis", "Εὐριπίδης", "Euripides", "tlg0006.tlg002",
         "Euripidis Fabulae, recognovit brevique adnotatione critica instruxit Gilbertus Murray, tomus I, Oxford, Clarendon Press, 1902",
         "euripidisfabulae01euriuoft", "murray", "G. Murray", "euripides_alcestis_murray",
         glaux="0006-002.xml",
         trans_file="drama/tlg0006.tlg002.perseus-eng2.xml", translator="E. P. Coleridge", trans_key="coleridge",
         trans_edition="The Plays of Euripides, translated by E. P. Coleridge, London, George Bell and Sons, 1891",
         trans_license="CC BY-SA 4.0 (Perseus Digital Library)",
         notes_editor="hayley", notes_editor_name="Harry Wilson Hayley",
         notes_edition="The Alcestis of Euripides, edited with an introduction and critical and exegetical notes by H. W. Hayley, Boston, Ginn & Company, 1898",
         notes_scan="alcestisofeuripi00euriuoft", notes_layout="hayley", note_start=HAYLEY_NOTE,
         # a note on a verse Murray's numbering lacks keeps Hayley's number in front (as the Medea's);
         # a paragraph whose lemma stands in a neighbouring verse goes there (Hayley numbers some
         # lyric and dialogue stretches otherwise than Murray)
         notes_refile_mark=True, notes_follow_lemma=True,
         # Hayley's divisions of the play (introduction, chapter B)
         parts=[(1, "Prologue"), (77, "Parodos"), (136, "First episode"), (435, "First stasimon"),
                (476, "Second episode"), (568, "Second stasimon"), (606, "Third episode"),
                (962, "Third stasimon"), (1006, "Exodos")],
         trans_stages_apart=True,
         # Murray died in 1957 (as the Medea's entry): the licence line of the files that hold his
         # text or apparatus (introduction.md too: his hypotheses and persons stand in it)
         edition_license="CC BY-SA 4.0 (transcription); Murray's edition is in the public domain in the United States, "
                         "and in Norway, the EU and the UK from 1 January 2028",
         # Murray's page, as for the Medea (see that entry for what each option answers)
         speaker_trust=True, app_bare_numbers=True, verse_size_q=0.75, foot_signature=True, app_pitch_cut=True,
         head_frac=0.065, metre_labels=True,
         # Murray's scan: the hypotheses with their apparatus leaves 54-55, the persons with his
         # note leaf 56, the text leaves 57-101 (seen 2026-11-16), the volume's Sigla leaf 24.
         # Hayley (notes scan alcestisofeuripi00euriuoft; 294 leaves, hidden 0, 8-9, 18-19, 172-173,
         # 278-279, 289-293; p = leaf - 98 to leaf 171, leaf - 100 from leaf 174): title leaf 7,
         # contents leaf 17; Introduction pp. xi-lxxxvii = leaves 21-97: A. The Myth of Alcestis (21),
         # B. The Euripidean Play (29), C. The Critical Basis for the Text (43; from "The editions of
         # the Alcestis are very numerous" on leaf 53 to the end of the list of editions, translations
         # and critical essays on leaf 58 a list: left out, leaves 54-57 not read), D. Questions
         # concerning the Scenic Representation (58), E. The Myth of Alcestis in Ancient Art, by James
         # M. Paton (61-95; Paton believed to have died in 1944, so free in Norway since 2015:
         # unverified, the author to confirm), F. Hypotheses of the Play (95-96: his own Greek after Schwartz, not used:
         # Murray's are; no notes on them), Critical Signs and Abbreviations (97: his apparatus's, not
         # used); half-title 99, his persons 100, his text with his apparatus pp. 3-52 = leaves 101-150
         # and Select Conjectures pp. 53-60 = leaves 151-157 (not used); Critical and Exegetical Notes
         # pp. 61-167 = leaves 159-267 (one column; critical and exegetical notes mixed; "Verse 1.",
         # then a bold figure opening an indented paragraph, further bold lemmas run on inside it);
         # Metrical Appendix from p. 169 = leaf 269 (not transcribed).
         text_leaves=[(57, 101)], sigla_leaves=[24], notes_leaves=[(159, 267)], intro_leaves=[(21, 53), (58, 95)],
         # the introduction document, as the Medea's: Hayley's introduction, then Murray's ancient
         # hypotheses with his apparatus (vol. I leaves 54-55), then Murray's persons page (leaf 56);
         # merged in this order (the stems p-1…, p-2…, p-3…)
         notes_sources={"intro": [("alcestisofeuripi00euriuoft", [(21, 53), (58, 95)]),
                                  ("euripidisfabulae01euriuoft", [(54, 55)]),
                                  ("euripidisfabulae01euriuoft", [(56, 56)])]},
         # the list of essays on the play at the end of chapter B (leaves 42-43), the list of
         # editions, translations and essays in chapter C (leaves 53-58; the lines as the OCR reads
         # them) and Hayley's own Greek of the hypotheses (leaf 95 from his heading F) left out
         prose_omit=[("alcestisofeuripi00euriuoft", 42, r"^I append a partial list of the essays", "", ""),
                     ("alcestisofeuripi00euriuoft", 43, "", r"^hand\.$", "[Bibliography omitted]"),
                     ("alcestisofeuripi00euriuoft", 53, r"^The editions of the Alcestis are very numerous",
                      r"^Barnes.{0,3} comments may still be consulted", ""),
                     ("alcestisofeuripi00euriuoft", 58, "", r"^ed\. IV\. p\. 70", "[list of editions omitted]"),
                     ("alcestisofeuripi00euriuoft", 95, r"^F\. HYPOTHESES OF THE PLAY", "", "")]),
    Play("lysistrata", "Λυσιστράτη", "Lysistrata", "Ἀριστοφάνης", "Aristophanes", "tlg0019.tlg007",
         "Aristophanis Comoediae, recognoverunt brevique adnotatione critica instruxerunt F. W. Hall et W. M. Geldart, tomus II, Oxford, Clarendon Press, 1907",
         "aristophaniscomo02arisuoft", "hall-geldart", "F. W. Hall and W. M. Geldart", "aristophanes_lysistrata_hall_geldart",
         glaux="0019-007.xml", translation="gutenberg", trans_file="gutenberg/pg8688.txt",
         gutenberg_title="LYSISTRATA", translator="The Athenian Society", trans_key="athenian",
         trans_edition="The Eleven Comedies, literally and completely translated from the Greek tongue into English, London, The Athenian Society, 1912, vol. I (Project Gutenberg #8688)",
         notes_editor="rogers", notes_editor_name="Benjamin Bickley Rogers",
         notes_edition="The Lysistrata of Aristophanes, with a translation into corresponding metres, introduction and commentary by Benjamin Bickley Rogers, London, George Bell and Sons, 1911",
         notes_scan="aristophaniscomo04aris"),
    # Sophocles in Jebb's edition (pipeline/PLAN-sophocles.md): text and apparatus by this route;
    # Jebb's commentary, introduction and translation are Perseus's, made by sophocles.py
    # Jebb's Antigone (on sale since reader 0.3.0): its text from Perseus (soph.ant_gk.xml) proved to
    # differ from Jebb's printed page in about one verse in three (2026-11-17, PLAN-sophocles.md), so
    # it is established again by this route; the check text is the text as it stood
    Play("antigone", "Ἀντιγόνη", "Antigone", "Σοφοκλῆς", "Sophocles", "tlg0011.tlg002",
         "Sophocles: The Plays and Fragments, Part III: The Antigone, ed. R. C. Jebb, second edition, Cambridge University Press, 1891",
         "sophocles03soph", "jebb", "R. C. Jebb", "sophocles_antigone_jebb",
         treebank="tlg0011.tlg002.perseus-grc2.tb.xml", translation="kept", translator="Richard C. Jebb", trans_key="jebb", layout="jebb", app_rule="under", head_frac=0.095, speaker_trust=True, app_langs=("eng+grc", "grc+eng"),
         check_text="sophocles/antigone/reference-grc.txt",
         # leaf = PDF page (leaves 0 and 365 hidden; Boston College, grey ground, a reader's pencil and
         # ink notes and underlining on some pages): the Greek on the even leaves 76-306 (pp. 8-238),
         # Jebb's translation facing it; the Appendix from leaf 310 (p. 242; 308 blank, 309 its
         # first page to be confirmed); the introduction pp. ix ff. from leaf 15; the argument and the
         # persons before the text (leaves 73-75). appendix_leaves: only the pages of the Appendix's
         # note "Lines 904-920" (pp. 258-263), which the published appendix had as raw OCR: read by
         # the prose route into appendix-01.md, checked, spliced into texts/antigone/appendix.md
         # and the batch kept in appendix-904-920/ (out of sophocles-prose's way, which would
         # otherwise write the whole appendix.md from this one batch)
         # notes_leaves: Jebb's commentary (kind notes), under the rule of every leaf 76-307, both
         # pages of each spread, two columns, as the Philoctetes's: Perseus's digitisation of it is
         # not his page (authors and titles added or respelt, slips), so it is read from the page
         # (2026-11-17; written by sophocles-prose once every notes batch is checked)
         text_leaves=[(76, 307)], appendix_leaves=[(326, 331)],
         notes_leaves=[(76, 307)], notes_editor="jebb", notes_editor_name="Richard C. Jebb"),
    # Jebb's Ajax and Electra (on sale; typed by eye from Perseus's text and checked against the scans
    # by the older route): re-read from Jebb's page by this route at the author's word (2026-11-17);
    # the check text is the text as it stood
    Play("ajax", "Αἴας", "Ajax", "Σοφοκλῆς", "Sophocles", "tlg0011.tlg003",
         "Sophocles: The Plays and Fragments, Part VII: The Ajax, ed. R. C. Jebb, Cambridge University Press, 1896",
         "playsfragmentswi07sophuoft", "jebb", "R. C. Jebb", "sophocles_ajax_jebb",
         treebank="tlg0011.tlg003.perseus-grc1.tb.xml", translation="kept", translator="Richard C. Jebb", trans_key="jebb", layout="jebb", app_rule="under", head_frac=0.095, speaker_trust=True, app_langs=("eng+grc", "grc+eng"),
         check_text="sophocles/ajax/reference-grc.txt",
         # the fourth episode (974) begins 13 verses after the check text's section (961: Tecmessa's
         # speech, which Jebb counts in the kommos 879-973)
         parts_window=14,
         # leaf = PDF page (Toronto, reprint 1914 of the 1896 edition; leaves 352-355 hidden): the Greek
         # on the even leaves 94-294 (pp. 10-210), Jebb's translation facing it; the Appendix from 298.
         # notes_leaves: Jebb's commentary (kind notes) under the rule of every leaf 94-295, both pages,
         # two columns, read from the page as the Antigone's (Perseus's digitisation is not his page)
         text_leaves=[(94, 295)],
         notes_leaves=[(94, 295)], notes_editor="jebb", notes_editor_name="Richard C. Jebb"),
    Play("electra", "Ἠλέκτρα", "Electra", "Σοφοκλῆς", "Sophocles", "tlg0011.tlg005",
         "Sophocles: The Plays and Fragments, Part VI: The Electra, ed. R. C. Jebb, Cambridge University Press, 1894",
         "sophoclesplaysfr06soph", "jebb", "R. C. Jebb", "sophocles_electra_jebb",
         treebank="tlg0011.tlg005.perseus-grc2.tb.xml", translation="kept", translator="Richard C. Jebb", trans_key="jebb", layout="jebb", app_rule="under", head_frac=0.095, speaker_trust=True, app_langs=("eng+grc", "grc+eng"),
         check_text="sophocles/electra/reference-grc.txt",
         # leaf = PDF page (University of Florida, reprint 1907 of the 1894 edition; leaves 0 and 345-349
         # hidden): the Greek on the even leaves 102-298 (pp. 6-202), the translation facing it.
         # notes_leaves: Jebb's commentary (kind notes) under the rule of every leaf 102-299, both
         # pages, two columns, read from the page as the Antigone's (Perseus's is not his page)
         text_leaves=[(102, 299)],
         notes_leaves=[(102, 299)], notes_editor="jebb", notes_editor_name="Richard C. Jebb"),
    Play("trachiniae", "Τραχίνιαι", "Trachiniae", "Σοφοκλῆς", "Sophocles", "tlg0011.tlg001",
         "Sophocles: The Plays and Fragments, Part V: The Trachiniae, ed. R. C. Jebb, Cambridge University Press, 1892",
         "sophocles05soph", "jebb", "R. C. Jebb", "sophocles_trachiniae_jebb",
         treebank="tlg0011.tlg001.perseus-grc2.tb.xml", translation="kept", translator="Richard C. Jebb", trans_key="jebb", layout="jebb", app_rule="under", head_frac=0.095, speaker_trust=True, app_langs=("eng+grc", "grc+eng"),
         check_text="sophocles/trachiniae/reference-grc.txt",
         # leaf = PDF page (leaf 0 is hidden): the Greek on the even leaves 80-256, Jebb's
         # translation facing it; the Appendix 259-281 (282 blank, the indices from 283);
         # "Manuscripts, editions, etc." 55-58; Jebb's note in place of an ancient argument, the
         # persons and the structure 77-79
         text_leaves=[(80, 257)], intro_leaves=[(55, 58), (77, 79)], appendix_leaves=[(259, 281)]),
    Play("oedipustyrannus", "Οἰδίπους Τύραννος", "Oedipus Tyrannus", "Σοφοκλῆς", "Sophocles", "tlg0011.tlg004",
         "Sophocles: The Plays and Fragments, Part I: The Oedipus Tyrannus, ed. R. C. Jebb, third edition, Cambridge University Press, 1893",
         "playsfragmentswi01sophuoft", "jebb", "R. C. Jebb", "sophocles_oedipustyrannus_jebb",
         treebank="tlg0011.tlg004.perseus-grc1.tb.xml", translation="kept", translator="Richard C. Jebb", trans_key="jebb", layout="jebb", app_rule="under", head_frac=0.095, speaker_trust=True, app_langs=("eng+grc", "grc+eng"),
         check_text="sophocles/oedipustyrannus/reference-grc.txt",
         # leaf = PDF page (leaves from 1; 358-361 hidden): the Greek on the even leaves 110-298
         # (leaf 300, p. 200, holds only the end of the commentary; the Appendix 301-334); the
         # introduction 15-66 (67 ff. the metrical analysis) and the pages before the text 103-109
         # (title and arguments 103-106, persons 107, structure 108-109), which Perseus lacks
         text_leaves=[(110, 299)], intro_leaves=[(15, 66), (103, 109)], appendix_leaves=[(301, 334)]),
    Play("oedipuscoloneus", "Οἰδίπους ἐπὶ Κολωνῷ", "Oedipus at Colonus", "Σοφοκλῆς", "Sophocles", "tlg0011.tlg007",
         "Sophocles: The Plays and Fragments, Part II: The Oedipus Coloneus, ed. R. C. Jebb, second edition, Cambridge University Press, 1889",
         "sophocles02soph_0", "jebb", "R. C. Jebb", "sophocles_oedipuscoloneus_jebb",
         glaux="0011-007.xml", translation="kept", translator="Richard C. Jebb", trans_key="jebb", layout="jebb", app_rule="under", head_frac=0.095, speaker_trust=True, app_langs=("eng+grc", "grc+eng"),
         check_text="sophocles/oedipuscoloneus/reference-grc.txt",
         # twelve leaves are hidden (0, 25, 26, 77, 78, 83, 84, 147, 148, 387, 388, 421), so a leaf
         # is not its PDF page: PDF 100-363 (the text) = leaves 106-371, the Greek on every other
         # shown leaf from 106; the Appendix PDF 365-388 = leaves 373-398; "Manuscripts,
         # editions, etc." about PDF 53-57 = leaves 55-59; the persons about PDF 97 = leaf 103
         # prose leaves (PDF page in brackets): "Manuscripts, editions, etc." 55-66 [53-64]; the
         # arguments, persons and structure before the text 99-105 [93-99]; the Appendix 373-397
         # [365-387]
         text_leaves=[(106, 371)], intro_leaves=[(55, 66), (99, 105)], appendix_leaves=[(373, 397)]),
    Play("philoctetes", "Φιλοκτήτης", "Philoctetes", "Σοφοκλῆς", "Sophocles", "tlg0011.tlg006",
         "Sophocles: The Plays and Fragments, Part IV: The Philoctetes, ed. R. C. Jebb, second edition, Cambridge University Press, 1898",
         "playsfragmentswi04sophuoft", "jebb", "R. C. Jebb", "sophocles_philoctetes_jebb",
         glaux="0011-006.xml", translation="kept", translator="Richard C. Jebb", trans_key="jebb", layout="jebb", app_rule="under", head_frac=0.095, speaker_trust=True, app_langs=("eng+grc", "grc+eng"),
         check_text="sophocles/philoctetes/reference-grc.txt",
         # leaf = PDF page (leaves from 1; 344-347 hidden): the Greek on the even leaves 76-296;
         # the Appendix 299-324; the introduction 11-49 and 73-75, and the whole commentary
         # (under the text, two columns), which Perseus lacks
         # prose leaves: the introduction 11-46 and "Manuscripts, editions, etc." 47-49 (the
         # metrical analysis 50-70 is not transcribed); the arguments, persons and structure
         # 73-75; the Appendix 299-324. The commentary (kind notes): under the rule of every
         # leaf 76-297, both pages of each spread, two columns (drama_prose._region_under_rule);
         # written by sophocles-prose as commentary-jebb.md (Perseus has none for this play)
         text_leaves=[(76, 297)], intro_leaves=[(11, 49), (73, 75)], appendix_leaves=[(299, 324)],
         notes_leaves=[(76, 297)], notes_editor="jebb", notes_editor_name="Richard C. Jebb"),
    # Hesiod's Theogony (pipeline/PLAN-theogony.md): Rzach's Teubner text and apparatus, Paley's
    # commentary (his own text and critical notes on the same pages are not used)
    Play("theogony", "Θεογονία", "Theogony", "Ἡσίοδος", "Hesiod", "tlg0020.tlg001",
         "Hesiodi carmina, recensuit Aloisius Rzach, Leipzig, B. G. Teubner, 1908",
         "hesiodicarminare00hesi", "rzach", "A. Rzach", "hesiod_theogony_rzach",
         treebank="tlg0020.tlg001.perseus-grc1.tb.xml", tree_units=True,
         syntax_text="the Perseus Digital Library's text of the poem (H. G. Evelyn-White's Loeb edition, 1914)",
         trans_file="drama/tlg0020.tlg001.perseus-eng2.xml", translator="Hugh G. Evelyn-White", trans_key="evelyn-white",
         trans_edition="Hesiod, the Homeric Hymns and Homerica, with an English translation by Hugh G. Evelyn-White, Loeb Classical Library, London, Heinemann, 1914",
         trans_license="CC BY-SA 4.0 (Perseus Digital Library)",
         notes_editor="paley", notes_editor_name="F. A. Paley",
         notes_edition="The Epics of Hesiod, with an English commentary by F. A. Paley, second edition, revised, London, Whittaker, 1883",
         notes_scan="epicsofhesiodwit00hesiuoft", notes_layout="paley", app_bare_numbers=True, app_to_foot=True,
         ocr_fold={"ϑ": "θ", "ϱ": "ρ", "ϐ": "β", "ϰ": "κ"}, skel_fold="χκ", perseus_order="numeric",
         perseus_drop=tuple(f"929{c}" for c in "abcdefghijklmnopqrst"),
         pronunciation="homeric",  # Hesiod's epic Ionic, as the Odyssey
         # Rzach: p = leaf - 10; the half-title p. 1 (leaf 11), the sigla ("Notae librorum") p. 2,
         # text pp. 3-50. Paley (notes scan, hidden leaves 118-119 and 272-273): the Theogony with
         # his commentary pp. 171-276 = leaves 223-328; the preface pp. v-xliv = leaves 11-50 and
         # the "Epitome of the Theogony" pp. 167-170 = leaves 219-222
         text_leaves=[(13, 60)], sigla_leaves=[12], notes_leaves=[(223, 328)], intro_leaves=[(11, 50), (219, 222)]),
    # Lucian's A True Story (pipeline/PLAN-true-story.md): Nilén's Teubner text and apparatus, read
    # by lucian_pages.py (prose, by printed line; the unit of grc.txt is the book.section), GLAUx,
    # Harmon's translation, Jerram's commentary and introduction
    Play("truestory", "Ἀληθῶν διηγημάτων", "A True Story", "Λουκιανός", "Lucian", "tlg0062.tlg012",
         "Lucianus, edidit Nils Nilén, vol. I fasc. I: libelli I–XIV, Leipzig, B. G. Teubner, 1906",
         "bub_gb_RYepnZKT1OwC", "nilen", "N. Nilén", "lucian_truestory_nilen",
         glaux="0062-012.xml",
         trans_file="drama/tlg0062.tlg012.perseus-eng2.xml", translator="A. M. Harmon", trans_key="harmon",
         trans_edition="Lucian, with an English translation by A. M. Harmon, vol. I, Loeb Classical Library, London, Heinemann, 1913",
         trans_license="CC BY-SA 4.0 (Perseus Digital Library)",
         notes_editor="jerram", notes_editor_name="C. S. Jerram",
         notes_edition="Luciani Vera Historia, edited with introduction and notes for the use of middle forms in schools by C. S. Jerram, Oxford, Clarendon Press, 1879",
         notes_scan="lucianiverahisto00luci", app_bare_numbers=True, app_rule="short",
         ocr_fold={"ϑ": "θ", "ϱ": "ρ", "ϐ": "β", "ϰ": "κ"}, skel_fold="χκξζ",  # Nilén's ζ is read as ξ
         pronunciation="attic",  # the author (2026-11-08): Lucian strove for a learned, Attic sound
         page_offset=67,
         # Jerram: "Line 4. μέρος γοῦν", "l. 17.", "ll. 26, 27." (his own lines, per book); the OCR
         # reads l. as 1. or I.
         note_start=r"^(?:Line\s+|L\.\s*|[lI1|]{1,2}\.\s*)(\d{1,4})(?:\s*[-–—,]\s*(\d{1,4}))?(?:\s*f{1,2}\.|\s*sqq?\.)?[.,:]?(?=\s|$)",
         # Nilén (scan leaf n = page image n): title page leaf 4, praefatio pp. III-XVI = leaves 6-19,
         # the witnesses (pp. VII, VIII, X, XIII) leaves 10, 11, 13, 16; text pp. 129-208 = leaves
         # 196-275 (book I 196-233, book II 234-275). Jerram (leaf 0 hidden, leaf = image n + 1):
         # title leaf 9, preface pp. v-vii = leaves 11-13, introduction pp. ix-xxiii = leaves 15-29,
         # his text pp. 1-49 = leaves 31-79, notes pp. 51-70 = leaves 81-100, index pp. 71-73
         text_leaves=[(196, 275)], sigla_leaves=[10, 11, 13, 16], notes_leaves=[(81, 100)],
         intro_leaves=[(15, 29)], notes_text_leaves=[(31, 79)]),
    # The Shepherd of Hermas (pipeline/PLAN-hermas.md): Lake's Loeb text, apparatus, translation and
    # notes; read by lake_pages.py (prose, by verse: book.chapter.verse of the 27 digital books),
    # Tauber's text as the check text, GLAUx, Taylor's notes and introduction from two volumes
    Play("hermas", "Ποιμήν", "The Shepherd", "Ἑρμᾶς", "Hermas", "tlg1419.tlg001",
         "The Apostolic Fathers, with an English translation by Kirsopp Lake, vol. II, Loeb Classical Library, "
         "London, William Heinemann, and New York, The Macmillan Co., 1913 (reprinted 1917)",
         "apostolicfathers02lakeuoft", "lake", "K. Lake", "hermas_shepherd_lake",
         glaux="1419-001.xml",
         trans_file="drama/tlg1419.tlg001.perseus-eng1.xml", translator="Kirsopp Lake", trans_key="lake",
         trans_edition="The Apostolic Fathers, with an English translation by Kirsopp Lake, vol. II, Loeb Classical Library, London, Heinemann, 1913",
         trans_license="CC BY-SA 4.0 (Perseus Digital Library)",
         notes_editor="taylor", notes_editor_name="Charles Taylor",
         notes_edition="The Shepherd of Hermas, translated into English with an introduction and notes by Charles Taylor, "
                       "Early Church Classics, London, SPCK, vol. I 1903, vol. II 1906",
         notes_scan="shepherdofhermas0000herm", app_bare_numbers=True, pronunciation="koine",
         page_offset=12, leaf_step=2, skel_fold="ξζ", route="lake",  # Tesseract reads Lake's ζ as ξ
         app_langs=("grc+eng", "eng+grc"),  # the apparatus is Greek with Latin readings and English remarks
         # Lake (leaf = page + 12; the scan hides leaves 0-2, so page image n = leaf - 3): half-title
         # p. 1 = leaf 13, his introduction pp. 2-5 = leaves 14-17, the Greek on the even pages
         # 6-290 = leaves 18-302 (his translation on the odd pages facing it); A ends on p. 290 after
         # Sim. 9.30.2, and the Latin end runs from there to p. 304 = leaf 316
         text_leaves=[(18, 302)], latin_leaves=[(302, 316)], sigla_leaves=[15, 16, 17],
         # Taylor I (shepherdofhermas0000herm; scandata hides leaf 0, page image n = leaf - 1; leaf =
         # page + 4): introduction pp. 9-54 = leaves 13-58, the Visions and Mandates with his
         # footnotes pp. 57-164 = leaves 61-168 (p. 55 the half-title "Visions I-IV", the index p. 165).
         # Taylor II (shepherdofhermas02hermuoft; jp2 from _0001, page image n = leaf - 1; leaf = page
         # + 4): the Similitudes pp. 9-131 = leaves 13-135, the Appendix (Hermas and the Gospels)
         # pp. 135-139 = leaves 139-143 (half-title p. 133), the index p. 141.
         notes_sources={
             "notes": [("shepherdofhermas0000herm", [(61, 168)]), ("shepherdofhermas02hermuoft", [(13, 135)])],
             "intro": [("apostolicfathers02lakeuoft", [(14, 17)]), ("shepherdofhermas0000herm", [(13, 58)]),
                       ("shepherdofhermas02hermuoft", [(139, 143)])],
         }),
    # Lysias, the 34 speeches as one text (pipeline/PLAN-lysias.md): Hude's Oxford text and critical
    # apparatus, read by hude_pages.py (prose, by printed line; the unit of grc.txt is the
    # speech.section, the speeches being the text's books). The check text is the 34 Perseus files
    # tlg0540.tlg001-034 (Lamb's Loeb Greek, never shipped); `tlg` names the author only.
    Play("lysias", "Λόγοι", "Speeches", "Λυσίας", "Lysias", "tlg0540",
         "Lysiae orationes, recognovit brevique adnotatione critica instruxit Carolus Hude, Oxford, Clarendon Press, 1912",
         "orationesrecogno00lysi", "hude", "C. Hude", "lysias_speeches_hude",
         route="hude", pronunciation="attic",
         # the Oxford page, as Murray's: the apparatus items' numbers without a stop, a long
         # apparatus reaching high up the page, the printer's signature under it ("LYS. 1", "1*")
         app_bare_numbers=True, verse_size_q=0.75, foot_signature=True, app_pitch_cut=True,
         # Hude prints no page numbers in the text. Scan orationesrecogno00lysi: 308 leaves (0-307),
         # hidden 0, 36, 37, 44, 45 and 307. Leaves 36-37 and 44-45 are pages of speech 2 that the
         # scan keeps only as uncropped camera frames marked "Delete" (the Archive's reader skips
         # them): they are used (unhide; cut to the page by hude_pages.FRAMES). Page image n = leaf
         # - 1 up to leaf 35, leaf - 3 for 38-43, leaf - 5 from 46. Series title leaf 5, title page leaf 7,
         # praefatio pp. iii-x = leaves 9-16 (signed Rome, 1 December 1911), SIGLA leaf 18, speeches
         # I-XXXIV leaves 19-287 (each speech begins on a fresh page), XXXV (the Eroticus, from
         # Plato's Phaedrus; not part of this text) leaves 288-292, Index nominum 293-296, the
         # publisher's list (dated August 1914) from 297
         text_leaves=[(19, 287)], sigla_leaves=[18], intro_leaves=[(9, 16)], unhide=(36, 37, 44, 45)),
]}


# ---------------------------------------------------------------- the commentaries on Lysias

# One commentary to a speech, from three school editions (pipeline/PLAN-lysias.md): the leaves of
# each speech's introduction and of its notes. Each speech is an entry of its own for the prose
# route (drama-prose lysias-12 notes|intro fetch|ocr|draft; batches in transcriptions/drama/
# lysias-12/): the notes of a speech are numbered from 1 again, as a play's are, so the route's
# checks of the numbers' order hold within an entry. hude_notes.py files the checked notes under
# Hude's sections. `last` is the speech's last section (Adams, Morgan: notes by section) or the
# last line of the commentator's own text (Shuckburgh: notes by his lines).
#
# Adams (lysiasselectedsp0000char; leaf = page + 8): introduction pp. 9-42, each speech with its
# introduction, then the text with the notes under it in two columns; Appendix pp. 327-362
# (I Chronological outline, II Athenian legal procedure, III Rhetorical terms, IV Money and prices,
# V The manuscripts; VI Bibliography and VII Critical notes on his own text are not taken).
# Morgan (eightorations00lysi, the 1900 printing; leaf = page + 64): the same page; his
# introduction to a speech stands before its text.
# Shuckburgh (orationes16witha00lysiuoft; leaf = page + 38): his text pp. 1-190 with English
# summaries, the notes at the back pp. 193 ff. by the lines of his text, each speech's under
# "ORATION IV. [10.]" with his introduction to it; his own numbers I-XVI are not ours.
LYSIAS_EDITORS = {
    "adams": ("lysiasselectedsp0000char", "Charles Darwin Adams", "college",
              "Lysias: Selected Speeches, XII, XVI, XIX, XXII, XXIV, XXV, XXXII, XXXIV, edited with introduction, notes, and "
              "appendices by Charles Darwin Adams, New York, Cincinnati, Chicago, American Book Company, 1905"),
    "morgan": ("eightorations00lysi", "Morris H. Morgan", "college",
               "Eight Orations of Lysias, edited with introduction, notes, and appendices by Morris H. Morgan, "
               "Boston, Ginn and Company, 1895"),
    "shuckburgh": ("orationes16witha00lysiuoft", "Evelyn S. Shuckburgh", "back",
                   "Lysiae Orationes XVI, with analysis, notes, appendices, and indices by Evelyn S. Shuckburgh, "
                   "London, Macmillan and Co., 1882"),
}
# speech: (editor, introduction leaves, notes leaves, last note number, the commentator's text leaves)
LYSIAS_NOTES: dict[int, tuple[str, list[tuple[int, int]], list[tuple[int, int]], int, list[tuple[int, int]]]] = {
    12: ("adams", [(51, 67)], [(69, 137)], 100, []),
    16: ("adams", [(138, 149)], [(150, 167)], 21, []),
    19: ("adams", [(168, 183)], [(184, 220)], 64, []),
    22: ("adams", [(221, 227)], [(228, 238)], 22, []),
    24: ("adams", [(239, 246)], [(247, 260)], 27, []),
    25: ("adams", [(261, 268)], [(269, 290)], 35, []),
    32: ("adams", [(291, 300)], [(301, 320)], 29, []),
    34: ("adams", [(321, 327)], [(328, 334)], 11, []),
    7: ("morgan", [(65, 70)], [(71, 87)], 43, []),
    23: ("morgan", [(168, 171)], [(172, 179)], 16, []),
    31: ("morgan", [(197, 199)], [(200, 215)], 34, []),
    # Shuckburgh: no introduction pages of its own (it stands at the head of the notes); the
    # notes' leaves (a leaf shared with the next speech is cut at its heading), his text's leaves
    5: ("shuckburgh", [], [(231, 235)], 0, [(39, 41)]),
    9: ("shuckburgh", [], [(249, 258)], 0, [(54, 60)]),
    10: ("shuckburgh", [], [(258, 268)], 0, [(60, 68)]),
    13: ("shuckburgh", [], [(290, 310)], 0, [(96, 130)]),
    14: ("shuckburgh", [], [(310, 323)], 0, [(128, 146)]),
    17: ("shuckburgh", [], [(330, 336)], 0, [(151, 160)]),
    28: ("shuckburgh", [], [(368, 374)], 0, [(196, 206)]),
    30: ("shuckburgh", [], [(374, 384)], 0, [(205, 218)]),
}
# entries without notes: Adams's general introduction, and his Appendix I-V
LYSIAS_PROSE = {
    "lysias-intro": ("adams", [(17, 50)]),
    "lysias-appendix": ("adams", [(335, 370)]),
}
# John Gillies, The Orations of Lysias and Isocrates, London 1778 (scan
# bim_eighteenth-century_the-orations-of-lysias-a_lysias_1778: 676 leaves, a bitonal film scan,
# long s; leaf = page + 175 up to p. 350, page + 174 from p. 419): the six speeches the 1898
# translation lacks, each from the first page of the oration to its last (Gillies's own
# introduction before each and the title leaf of the next are not taken; the last pages were
# settled on the drafts). He has eighteen speeches of Lysias in all, in this
# order: 2, 14, 13, 12, 25, 34, 21, 26, 31, 16, 7, 17, 19, 1, 4, 3, 32, 10.
GILLIES_SCAN = "bim_eighteenth-century_the-orations-of-lysias-a_lysias_1778"
GILLIES_EDITION = ("The Orations of Lysias and Isocrates, translated from the Greek, with some account of their lives, "
                   "by John Gillies, London, J. Murray, 1778")
LYSIAS_GILLIES: dict[int, list[tuple[int, int]]] = {
    1: [(593, 602)], 3: [(613, 623)], 4: [(607, 612)], 21: [(504, 511)], 26: [(516, 522)], 34: [(494, 496)],
}


def _lysias_entries() -> list[Play]:
    out = []
    for slug, (editor, intro) in LYSIAS_PROSE.items():
        scan, name, _layout, edition = LYSIAS_EDITORS[editor]
        out.append(Play(slug, "Λόγοι", "Speeches", "Λυσίας", "Lysias", "tlg0540", "", scan, "hude", "C. Hude", "",
                        route="hude-notes", notes_editor=editor, notes_editor_name=name, notes_edition=edition,
                        notes_scan=scan, intro_leaves=intro,
                        # Adams's Appendix VI (Bibliography) begins on the page where V ends: left out
                        prose_omit=[(scan, 370, r"BIBLIOGRAPHY", "", "")] if slug == "lysias-appendix" else []))
    for speech, leaves in LYSIAS_GILLIES.items():
        out.append(Play(f"lysias-gillies-{speech:02d}", "Λόγοι", "Speeches", "Λυσίας", "Lysias", f"tlg0540.tlg{speech:03d}", "",
                        GILLIES_SCAN, "hude", "C. Hude", "", route="hude-notes", notes_editor="gillies",
                        notes_editor_name="John Gillies", notes_edition=GILLIES_EDITION, notes_scan=GILLIES_SCAN,
                        intro_leaves=leaves, long_s=True))
    for speech, (editor, intro, notes, last, text) in LYSIAS_NOTES.items():
        scan, name, layout, edition = LYSIAS_EDITORS[editor]
        out.append(Play(f"lysias-{speech:02d}", "Λόγοι", "Speeches", "Λυσίας", "Lysias", f"tlg0540.tlg{speech:03d}", "", scan,
                        "hude", "C. Hude", "", route="hude-notes", notes_editor=editor, notes_editor_name=name,
                        notes_edition=edition, notes_scan=scan, notes_layout=layout, intro_leaves=intro, notes_leaves=notes,
                        last_note=last, notes_text_leaves=text, intro_foot_columns=editor == "morgan"))
    return out


PLAYS.update({p.slug: p for p in _lysias_entries()})


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


def textfile_play(path: Path) -> dict:
    """A check text kept in our text format (grc.txt: sections, speakers, stage directions,
    `number<TAB>verse`) in the structure of perseus_play."""
    from .textfmt import Line, Section, Speaker, Stage, parse_file

    tokens: list[dict] = []
    lines: list[dict] = []
    sections: list[tuple[int, int, str, str]] = []
    stages: list[tuple[int, str]] = []
    speakers: list[str] = []
    speaker, last, pending, si = "", None, False, -1
    for item in parse_file(path).items:
        if isinstance(item, Section):
            sections.append((len(lines), item.level, item.kind, item.label))
        elif isinstance(item, Speaker):
            name = greek.nfc(item.name)
            if name and name != last:
                pending, si, last = True, si + 1, name
                if name not in speakers:
                    speakers.append(name)
            speaker = name or speaker
        elif isinstance(item, Stage):
            stages.append((len(tokens) - 1, greek.nfc(item.text)))
        elif isinstance(item, Line):
            words = _words_of(item.text)
            li = len(lines)
            line = {"n": item.n, "base": base(item.n), "words": [], "gap": not words}
            lines.append(line)
            if line["gap"] and tokens:
                tokens[-1]["gap"] = True
            for k, (w, gap) in enumerate(words):
                # the second half of a word divided at the end of the verse before
                if k == 0 and tokens and re.search(r"[Ͱ-Ͽἀ-῿]-$", tokens[-1]["t"]) and tokens[-1]["li"] == li - 1 and not pending:
                    prev = tokens[-1]
                    prev["t"] = prev["t"][:-1] + w
                    prev["skel"] = skel(prev["t"])
                    prev["gap"] = prev["gap"] or gap
                    prev["joined"] = True
                    continue
                tokens.append({"t": w, "skel": skel(w), "n": item.n, "base": line["base"], "li": li,
                               "first": not line["words"], "speaker": speaker, "newsp": pending, "gap": gap, "si": si})
                pending = False
                line["words"].append(len(tokens) - 1)
    return {"tokens": tokens, "lines": lines, "sections": sections, "stages": stages, "speakers": speakers}


def load_perseus(play: "Play", sources: Path) -> dict:
    """The play's check text (perseus_play), its verses in the order of their numbers where the
    play asks for it (Play.perseus_order), and its skeletons folded (Play.skel_fold)."""
    pers = textfile_play(PIPELINE / "transcriptions" / play.check_text) if play.check_text else perseus_play(sources / play.perseus)
    if play.perseus_order == "numeric" or play.perseus_drop:
        pers = numeric_order(pers, set(play.perseus_drop), play.perseus_order == "numeric")
    if play.skel_fold:
        tr = str.maketrans(play.skel_fold[0::2], play.skel_fold[1::2])
        for t in pers["tokens"]:
            t["skel"] = t["skel"].translate(tr)
    return pers


def numeric_order(pers: dict, drop: set[str] = frozenset(), sort: bool = True) -> dict:
    """The check text with its verses sorted by number (929, 929a … 929t, 930) and the verses in
    `drop` left out, the tokens with them; for a text without speakers, sections or stage
    directions."""
    lines = pers["lines"]
    order = list(range(len(lines)))
    if sort:
        order.sort(key=lambda i: (lines[i]["base"], re.sub(r"\d", "", lines[i]["n"]), i))
    order = [i for i in order if lines[i]["n"] not in drop]
    if order == list(range(len(lines))):
        return pers
    tokens: list[dict] = []
    new_lines: list[dict] = []
    for li in order:
        line = dict(lines[li])
        idx = []
        for j in line["words"]:
            t = dict(pers["tokens"][j])
            t["li"] = len(new_lines)
            idx.append(len(tokens))
            tokens.append(t)
        line["words"] = idx
        new_lines.append(line)
    return {**pers, "tokens": tokens, "lines": new_lines, "stages": [], "sections": []}


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

# a stage direction of the translation this short, before the words of a verse or a speech, says
# how the speaker speaks and stays with the speech (perseus_translation, stages_apart)
SPEAKER_DIRECTION_WORDS = 4


def _stage_text(text: str) -> str:
    """A stage direction set apart: without the parentheses or the opening bracket Perseus keeps
    round it ("(within)." -> "within.", "[Exit Attendant …" -> "Exit Attendant …")."""
    t = re.sub(r"\s+", " ", text).strip()
    t = re.sub(r"^\[\s*", "", t)
    m = re.fullmatch(r"\((.*)\)([.,;:]?)", t)
    if m and "(" not in m.group(1) and ")" not in m.group(1):
        t = m.group(1).strip() + m.group(2)
    return t.strip()


def perseus_translation(path: Path, stages_apart: bool = False) -> list[tuple[str, str, str]]:
    """A Perseus translation in verse-numbered TEI: (Perseus line number, speaker, text) for each
    <l>, and ("!", "", text) for a stage direction between verses; the display line n="0" left out;
    a stage direction inside a verse kept in parentheses, or with `stages_apart` (Play.
    trans_stages_apart) set apart as a ("!", "", text) row of its own, after the verse (before it
    when it stands before the verse's words); but a short direction before the words of a verse
    or a speech (Coleridge's "MEDEA (within)."; "(To the Nurse.)"), which says how the speaker
    speaks, stays at the head of the verse's text in parentheses, "(within) Ah, me!", as the
    Clouds' and the Agamemnon's translations show such directions, and a short one in
    parentheses among the words stays where it stands ("… hearth. (To a Servant) Go before …")."""
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
                    # a footnote between two words (quick-glancing<note/>Aphrodite) leaves a space
                    if re.match(r"\w", child.tail or "") and not parts[-1][-1:].isspace():
                        parts.append(" ")
                elif tag == "del":
                    parts.append("[" + text_of(child) + "]")
                else:
                    parts.append(text_of(child))
            parts.append(child.tail or "")
        return "".join(parts)

    head: list[str] = []  # short directions waiting for the words of the speech (stages_apart)
    carry: list[str] = []  # words after a direction set apart, waiting for the speech's next verse
    SPLIT = "\ue000"  # a private-use character: lxml refuses control characters

    def short(st: str) -> bool:
        return len(st.split()) <= SPEAKER_DIRECTION_WORDS and not st.startswith("[")

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
                before: list[str] = []
                after: list[str] = []
                if stages_apart:
                    seen_words = bool((child.text or "").strip())
                    for sub in list(child):
                        if isinstance(sub.tag, str) and etree.QName(sub).localname == "stage":
                            raw = re.sub(r"\s+", " ", "".join(sub.itertext())).strip()
                            st = _stage_text(raw)
                            inline = ""
                            if st and not seen_words and short(raw):
                                head.append(st.rstrip(".").strip())
                            elif st and short(raw) and raw.startswith("(") and not re.match(r"\(\s*(?:Exit|Exeunt|Enter)\b", raw):
                                # a short direction in parentheses among the words ("… hearth.
                                # (To a Servant.) Go before …") stays where it stands
                                inline = f" ({st.rstrip('.').strip()}) "
                            elif st:
                                (after if seen_words else before).append(st)
                                if seen_words:
                                    inline = SPLIT  # where the verse's words may be cut (below)
                            # the stage's place keeps a space between the words round it
                            prev = sub.getprevious()
                            tail = inline + (sub.tail or "")
                            if prev is not None:
                                prev.tail = (prev.tail or "") + " " + tail
                            else:
                                child.text = (child.text or "") + " " + tail
                            child.remove(sub)
                        elif (isinstance(sub.tag, str) and "".join(sub.itertext()).strip()) or (sub.tail or "").strip():
                            seen_words = True
                text = re.sub(r"\s+", " ", text_of(child)).strip()
                text = re.sub(r"\(\s+", "(", re.sub(r"\s+\)", ")", text))
                if carry:
                    text = (carry.pop() + " " + text).strip()
                if SPLIT in text:
                    # a direction set apart among the words: what follows it begins the next verse of
                    # the same speech ("… disowned it. [Exit Pheres.] Now, since we must bear …"),
                    # so that the direction stands where Perseus has it; with no next verse in the
                    # speech, the words stay and the direction follows them
                    first, _, rest = text.partition(SPLIT)
                    rest = rest.replace(SPLIT, " ").strip()
                    nxt = next((sib for sib in child.itersiblings() if isinstance(sib.tag, str)
                                and etree.QName(sib).localname == "l"), None)
                    if rest and nxt is not None:
                        carry.append(rest)
                        text = first.strip()
                    else:
                        text = (first + " " + rest).strip()
                    text = re.sub(r"\s+", " ", text)
                out.extend(("!", "", st) for st in before)
                if text and head:
                    text = "".join(f"({h}) " for h in head) + text
                    head.clear()
                if text:
                    out.append((n, speaker[0], text))
                out.extend(("!", "", st) for st in after)
            elif tag == "stage":
                st = re.sub(r"\s+", " ", "".join(child.itertext())).strip()
                if st and stages_apart and etree.QName(node).localname == "sp" and short(st) \
                        and child.getprevious() is not None and etree.QName(child.getprevious()).localname == "speaker":
                    # a direction between the speaker's name and the speech's first verse
                    head.append(_stage_text(st).rstrip(".").strip())
                elif st:
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


def escape_apparatus_asterisks(bold, text: str) -> str:
    """The apparatus lines of the batches are plain text, so every asterisk in them is printed
    (Jebb's mark of a conjecture, *θεῶν; an erased letter, ὧ* L): written \\* so that it cannot
    open italics in the markdown. `bold` (sophocles_pages.bold_lemmas) puts the lemmas in bold
    first, a starred lemma (*λόγων]) too."""
    return bold(text.replace("*", "\x00")).replace("\x00", "\\*")


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


_ELIDED = "ʼ’᾽'"


def _lemma_words(paragraph: str) -> list[str] | None:
    """The letters of the words of a paragraph's bold lemma (up to its first "…", "..." or "|"),
    those of three letters or more; None when it has no bold lemma or no word of four letters."""
    m = re.match(r"^(?:\[\d+[a-z]?(?:-\d+[a-z]?)?\]\s*)?\*\*([^*]+)\*\*", paragraph)
    if not m:
        return None
    first = re.split(r"\.\s*\.\s*\.|…|\|", m.group(1))[0]
    words = [w for w, _s, _e in greek.words(first)]
    keys = [skel(w) + ("ʼ" if w[-1:] in _ELIDED else "") for w in words]
    keys = [k for k in keys if len(k.rstrip("ʼ")) >= 3]
    return keys if any(len(k.rstrip("ʼ")) >= 4 for k in keys) else None


def _holds(keys: list[str], verse: str) -> bool:
    """Whether every lemma word stands in the verse (an elided word matches its full form)."""
    have = [skel(w) + ("ʼ" if w[-1:] in _ELIDED else "") for w, _s, _e in greek.words(verse)]

    def match(k: str, v: str) -> bool:
        a, b = k.rstrip("ʼ"), v.rstrip("ʼ")
        if a == b:
            return True
        if v.endswith("ʼ") and a.startswith(b) and len(a) - len(b) <= 1:
            return True
        return k.endswith("ʼ") and b.startswith(a) and len(b) - len(a) <= 1

    return all(any(match(k, v) for v in have) for k in keys)


def follow_lemmas(notes: list[tuple[str, list[str]]], lines: list[tuple[str, str]],
                  reach: int = 3) -> tuple[list[tuple[str, list[str]]], list[str]]:
    """Play.notes_follow_lemma: a paragraph of a note filed under one of our verses whose bold
    lemma (a word of four letters at least) stands neither in that verse nor in the note's range
    but in a verse up to `reach` lines away goes to the nearest such verse as a note of its own,
    the printed number in front ("[575] **συρίζων**: …"), right after the note it comes from.
    Returns the notes and one remark per paragraph moved."""
    numbers = [n for n, _t in lines]
    index = {n: i for i, n in enumerate(numbers)}
    out: list[tuple[str, list[str]]] = []
    moves: list[str] = []
    for heading, body in notes:
        a, _, b = heading.partition("-")
        if a not in index:
            # a number our text lacks: the whole note goes to the verse near it that holds its
            # lemma, where place_notes would take the nearest earlier verse
            keys = _lemma_words(body[0]) if body and heading else None
            near = sorted((abs(base(n) - base(a)), k) for k, n in enumerate(numbers)
                          if keys and abs(base(n) - base(a)) <= reach and _holds(keys, lines[k][1]))
            if near:
                target = numbers[near[0][1]]
                moves.append(f"notes: the note on {heading} goes to {target}, which holds its lemma")
                heading = target + (f"-{b}" if b and base(b) > base(target) else "")
            out.append((heading, body))
            continue
        i = index[a]
        j = index.get(b, i) if b else i
        if b and b not in index:
            later = [k for k, n in enumerate(numbers) if base(a) < base(n) <= base(b)]
            j = later[-1] if later else i
        # a note on a verse covers its lettered parts (219 and 219a: one verse of the tradition)
        while j + 1 < len(numbers) and base(numbers[j + 1]) == base(numbers[j]) and numbers[j + 1] != str(base(numbers[j + 1])):
            j += 1
        stay: list[str] = []
        moved: list[tuple[str, list[str]]] = []
        for para in body:
            keys = _lemma_words(para)
            if not keys or any(_holds(keys, lines[k][1]) for k in range(i, j + 1)):
                stay.append(para)
                continue
            near = sorted((abs(k - i), k) for k in range(max(0, i - reach), min(len(lines), j + reach + 1))
                          if not i <= k <= j and _holds(keys, lines[k][1]))
            if not near:
                stay.append(para)
                continue
            target = numbers[near[0][1]]
            text = para if para.startswith("[") else f"[{heading}] {para}"
            if moved and moved[-1][0] == target:
                moved[-1][1].append(text)
            else:
                moved.append((target, [text]))
            moves.append(f"notes: the paragraph of the note on {heading} on {para.split('**')[1]!r} goes to {target}, "
                         "which holds its lemma")
        if stay:
            out.append((heading, stay))
        out += moved
    return out, moves


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


def check_text_name(play: Play) -> str:
    """The check text as grc.txt's source line names it."""
    if play.check_text:
        from .sophocles import PLAYS as SOPHOCLES

        # sophocles/<slug>/reference-grc.txt was imported from Jebb's own text on Perseus (TEI P4)
        return f"Jebb's text in the Perseus Digital Library (soph.{SOPHOCLES[play.slug].code}_gk.xml)"
    return f"the Perseus Digital Library text ({play.tlg}.perseus-grc2)"


def apparatus_meta(play: Play) -> dict[str, str]:
    """The header of commentary-<app_editor>-apparatus.md; for Jebb's Sophocles that of the plays
    made earlier (texts/electra/commentary-jebb-apparatus.md)."""
    if play.check_text:
        from .sophocles import PART_ROMAN, PLAYS as SOPHOCLES
        from .sophocles_pages import SCAN_EDITIONS

        s = SOPHOCLES[play.slug]
        return {"title": "Critical apparatus", "author": "Richard C. Jebb", "lang": "eng",
                "source": f"Sophocles, The Plays and Fragments, {PART_ROMAN[s.part]}: The {s.title_en}, Cambridge University "
                          f"Press, {SCAN_EDITIONS[play.slug]} (critical apparatus), read by OCR and checked against the scan",
                "license": TRANSCRIPTION_LICENSE}
    return {
        "title": f"Critical apparatus ({play.app_editor_name})",
        "author": play.app_editor_name,
        "lang": "eng" if play.app_langs[1].startswith("eng") else "lat",
        "source": f"{play.edition}; transcribed from the Internet Archive scan {play.scan}",
        "license": play.text_license,
    }


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
    pers = load_perseus(play, sources)
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
        "source": f"{play.edition}; read from the Internet Archive scan {play.scan} by OCR, matched word by word to "
                  f"{check_text_name(play)}, and checked against the scan where the two disagreed",
        "edition": play.edition,
        "license": play.text_license,
    }
    if play.syntax_note:
        meta["syntax"] = play.syntax_note
    elif play.syntax_automatic:
        meta["syntax"] = "automatic"
    if play.pronunciation:
        meta["pronunciation"] = play.pronunciation
    if play.syntax_text:
        meta["syntax-text"] = play.syntax_text
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
    if play.check_text:
        # Jebb's Sophocles: the sections named by the divisions of the play (sophocles.PLAYS) in
        # which most of their verses fall, by our final numbering
        from . import sophocles

        if slug in sophocles.PLAYS:
            for m in sophocles.align_part_starts(doc, sophocles.PLAYS[slug], window=play.parts_window):
                print(m)
            sophocles.label_parts(doc, sophocles.PLAYS[slug])
            print(f"lyric sub-headings repeated within a stanza dropped: {sophocles.merge_repeated_subsections(doc)}")
    elif play.parts:
        # the commentator's divisions (Earle's Medea), by the same rules as Jebb's
        from . import sophocles

        for m in sophocles.align_part_starts(doc, play, window=play.parts_window):
            print(m)
        sophocles.label_parts(doc, play)
        print(f"lyric sub-headings repeated within a stanza dropped: {sophocles.merge_repeated_subsections(doc)}")
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
    md = _meta_lines(apparatus_meta(play)) + [""]
    for heading, body in notes:
        md.append(f"## {heading}")
        md.append(escape_apparatus_asterisks(bold_lemmas, "\n\n".join(body)))
        md.append("")
    (out / f"commentary-{play.app_editor}-apparatus.md").write_text("\n".join(md) + "\n", encoding="utf-8")
    print(f"wrote commentary-{play.app_editor}-apparatus.md: {len(notes)} notes, {sum(len(b) for _h, b in notes)} items")

    # lemmas, morphology, syntax
    review = _tokens(play, doc, sources, out, lexicon, build)
    print(f"review list: {review} words in {build / f'{slug}-review.tsv'}")

    # the translation
    _translation(play, sources, out, lines, items, pers, problems, transcriptions)

    # the commentary and the introduction
    if play.check_text:
        # Jebb's Sophocles: commentary-jebb.md and introduction.md are Perseus's (import-sophocles),
        # the transcribed chapters and the Appendix are added by sophocles-prose; never touched here
        print("commentary and introduction: left as they are (sophocles-prose writes the transcribed parts)")
    else:
        write_prose_documents(play, transcriptions, out, lines, build, problems)

    log = build / f"{slug}-merge.log"
    log.write_text("\n".join(problems) + "\n", encoding="utf-8")
    print(f"{len(problems)} problems ({log})")
    return len(problems)


def escape_footnote_marks(paragraph: str) -> str:
    """A footnote mark printed as an asterisk ("[Note: * See …]", "tragedies,* though") written \\*,
    so that build.md_to_html cannot pair it with the next italics mark. Walking the paragraph:
    an escaped \\* is kept; ** is bold and skipped; a * not after a letter, a digit or closing
    punctuation and before a word, while no italics are open, opens them ("Wecklein*) … no *certain*":
    the first is a mark); a * preceded by a non-space while italics are open closes them; any
    other single * is a mark, and so is an opener left unclosed at the end. Headings are left."""
    if paragraph.startswith("#") or "*" not in paragraph:
        return paragraph
    chars = list(paragraph)
    marks: list[int] = []
    opened = None
    i = 0
    while i < len(chars):
        c = chars[i]
        if c == "\\" and i + 1 < len(chars) and chars[i + 1] == "*":
            i += 2
            continue
        if c == "*" and i + 1 < len(chars) and chars[i + 1] == "*":
            i += 2
            continue
        if c == "*":
            before = chars[i - 1] if i else " "
            after = chars[i + 1] if i + 1 < len(chars) else " "
            if opened is None and not (before.isalnum() or before in ".,;:!?)]”’") and not after.isspace() \
                    and after not in ")]:;,.":
                opened = i
            elif opened is not None and not before.isspace():
                opened = None
            else:
                marks.append(i)
        i += 1
    if opened is not None:
        marks.append(opened)
    for k in sorted(marks, reverse=True):
        chars[k] = "\\*"
    return "".join(chars)


def write_prose_documents(play: Play, transcriptions: Path, out: Path, lines: list[tuple[str, str]], build: Path,
                          problems: list[str]) -> None:
    """commentary-<notes_editor>.md and introduction.md from the checked notes and intro batches
    (drama_prose: notes-NN.md, intro-NN.md), each only when its batches are all checked (every
    flag answered, every page of build/drama-prose/<slug>/<kind>.json there), so that a draft
    nobody has checked never becomes a text. Notes go under our line numbers (place_notes); with
    Play.notes_refile_mark a note moved off a number our text lacks keeps that number in front.
    The introduction's pages are merged in the order of their stems (with notes_sources: the
    entries' order). Remarks are added to `problems`."""
    from .drama_prose import merge_kind
    from .sophocles import unchecked_prose

    slug = play.slug
    have = {n for n, _t in lines}

    def checked(kind: str) -> bool:
        why = unchecked_prose(transcriptions, kind, build / "drama-prose" / slug / f"{kind}.json")
        if why:
            problems.append(f"{kind}: not merged, the batches are not all checked ({len(why)}): {why[0]}")
            print(f"{kind}: not merged, the batches are not all checked ({len(why)} pages), e.g. {why[0]}")
        return not why

    paras = merge_kind(transcriptions, "notes") if any(transcriptions.glob("notes-*.md")) and checked("notes") else []
    if paras:
        raw = notes_from_paragraphs(paras)
        if play.notes_refile_mark:
            raw = [(h, body if not h or h.split("-")[0] in have else
                    ([f"[{h}] {body[0]}"] + body[1:] if body else [f"[{h}]"])) for h, body in raw]
        if play.notes_follow_lemma:
            raw, moves = follow_lemmas(raw, lines)
            problems += moves
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
            md.append("\n\n".join(escape_footnote_marks(b) for b in body))
            md.append("")
        (out / f"commentary-{play.notes_editor}.md").write_text("\n".join(md) + "\n", encoding="utf-8")
        print(f"wrote commentary-{play.notes_editor}.md: {len(placed)} notes")
    paras = merge_kind(transcriptions, "intro") if any(transcriptions.glob("intro-*.md")) and checked("intro") else []
    if paras:
        author, source = play.notes_editor_name, (f"{play.notes_edition or play.edition}, the introduction; transcribed from "
                                                  f"the Internet Archive scan {play.scan_for('intro')}")
        if "intro" in play.notes_sources and play.scan in [s for s, _r in play.notes_sources["intro"]]:
            # the commentator's introduction with the text's edition's hypotheses and persons (the
            # Medea, the Alcestis); the commentator's notes on the hypothesis where his volume is read
            # twice (Earle's)
            author = f"{play.notes_editor_name}; {play.app_editor_name} (the ancient hypotheses and the persons)"
            twice = sum(1 for s, _r in play.notes_sources["intro"] if s == play.notes_scan) > 1
            source = (f"{play.notes_edition}, the introduction{' and the notes on the hypothesis' if twice else ''} (Internet Archive scan "
                      f"{play.notes_scan}); {play.edition}, the ancient hypotheses with the critical apparatus and the "
                      f"persons of the drama (scan {play.scan}); transcribed from the scans")
        license = TRANSCRIPTION_LICENSE
        if author != play.notes_editor_name and play.edition_license:
            # the text's edition's hypotheses and persons stand in it too (the Medea: Murray's)
            tail = re.sub(r"^.*?\bis\b", "which is", play.edition_license.split("; ", 1)[-1], count=1)
            license = (f"CC BY-SA 4.0 (transcription); {play.notes_editor_name}'s edition is free of copyright; the "
                       f"ancient hypotheses with their apparatus and the persons are from {play.app_editor_name}'s "
                       f"edition, {tail}")
        md = _meta_lines({
            "title": "Introduction", "author": author, "source": source,
            "license": license,
        }) + [""] + ["\n\n".join(escape_footnote_marks(p) for p in paras)]
        (out / "introduction.md").write_text("\n".join(md).rstrip() + "\n", encoding="utf-8")
        print(f"wrote introduction.md: {sum(1 for p in paras if p.startswith('#'))} headings")


def _tokens(play: Play, doc, sources: Path, out: Path, lexicon: Path, build: Path) -> int:
    from .import_perseus import LEMMA_FIXES, write_syntax_nodes, write_tokens
    from .odyssey import align, fix_lemma, syntax_nodes
    from .odyssey_merge import Analyser, Frequencies, choose_analysis
    from .sophocles import read_agdt, read_glaux_lines

    tb = read_agdt(sources / "treebanks" / play.treebank, play.treebank.startswith("tlg0020.")) if play.treebank else read_glaux_lines(sources / "glaux" / play.glaux)
    record: list[dict] | None = [] if play.syntax_text else None
    rows, _warnings = align(doc, tb, keep_tb_form=True, units=play.tree_units, record=record)
    analyse = Analyser(lexicon)
    freq = Frequencies(sources / "treebanks")
    review = []
    for r in rows:
        tb_form = r.pop("tb_form", "")
        same = tb_form and greek.strip_diacritics(tb_form) == greek.strip_diacritics(r["form"])
        if same and play.syntax_text:
            # an iota subscript is a letter of the form: παιπαλοέσσης is not the trees' παιπαλοέσσῃς,
            # and our word wants its own analysis
            from .odyssey import _subscripts
            same = _subscripts(tb_form) == _subscripts(r["form"])
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
    if record is not None:
        from .syntax_text import differences, give_sentences, settle, shift_repeats, write_record
        undecided = settle(play.slug, rows, record)
        print("readings by their difference: " + ", ".join(f"{n} {k}" for k, n in sorted(differences(rows, record).items())))
        greek_lines = [(line.n, line.text) for line in doc.lines]
        shift_repeats(greek_lines, rows, record)
        given, left = give_sentences(greek_lines, rows, record)
        print(f"words the trees' text has not: {given} given the sentence they stand in, {left} in passages without a tree")
    write_tokens(out / "tokens.tsv", rows)
    used = {(r["sentence"], w) for r in rows for w in r["word_id"].split("+") if r["sentence"]}
    write_syntax_nodes(out / "syntax-nodes.tsv", syntax_nodes(tb, used))
    if record is not None:
        lengths: dict[str, int] = {}
        for r in rows:
            lengths[r["line"]] = lengths.get(r["line"], 0) + 1
        counts = write_record(out / "syntax-text.tsv", record, tb, used, lengths)
        print("wrote syntax-text.tsv: " + ", ".join(f"{v} {k}" for k, v in counts.items())
              + (f"; {len(undecided)} readings without a decision (kept): {', '.join(undecided[:8])}" if undecided else ""))
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
    if play.translation == "kept":
        print(f"translation: eng-{play.trans_key}.txt left as it is")
        return
    if play.translation == "perseus":
        # verses the edition does not print (Play.perseus_drop) have no translation either
        rows = [r for r in perseus_translation(sources / play.trans_file, play.trans_stages_apart)
                if r[0] not in play.perseus_drop]
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
