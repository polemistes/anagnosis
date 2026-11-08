"""The digital texts of the Shepherd of Hermas that the build of Lake's edition reads
(pipeline/PLAN-hermas.md): none of them ships as text; each is a check or a source of Lake's own
words.

* tauber_text(): Tauber and Macdonald's Open Apostolic Fathers text (Lake's Greek, proofread twice
  against scans of the print), `texts/013-shepherd.txt`, one line per verse `book.chapter.verse
  text`, headings as `N.0.0`. The check text of the OCR: tokens as lucian_pages.perseus_prose gives
  them, with the verse ('sec', "1.1.2") and whether a verse or a chapter begins at a word.
* first1k_marks(): First1KGreek's edition of the same Loeb (Beta code in the notes): where Lake's
  footnote marks stand (the apparatus) and his margin references (<bibl> in a note), each as the
  index of the Tauber word it follows, with the note's text converted from Beta code.
* lake_translation(), lake_notes(): Lake's translation (Perseus tlg1419.tlg001.perseus-eng1) by
  verse, and his footnotes and marginal side-headings to it.

The numbering is that of the digital texts: 27 books (1-5 the Visions, 6-17 the Mandates, 18-27
the Similitudes), chapter and verse within each.
"""
from __future__ import annotations

import difflib
import re
import unicodedata
from pathlib import Path

from . import greek
from .drama import APOS, skel

ROOT = Path(__file__).resolve().parent.parent.parent
SOURCES = ROOT / "pipeline" / "sources"
TAUBER = SOURCES / "hermas" / "013-shepherd.txt"
FIRST1K = SOURCES / "hermas" / "tlg1419.tlg001.1st1K-grc1.xml"
PERSEUS_ENG = SOURCES / "drama" / "tlg1419.tlg001.perseus-eng1.xml"
TEI = "{http://www.tei-c.org/ns/1.0}"
# the last verse of manuscript A; from here Lake prints the Latin version (L1) with the papyri's Greek
LAST_GREEK = "26.30.2"
_ELISION = re.compile(r"(?<=[Ͱ-Ͽἀ-῿])['’᾽](?=\s|$|[,.;·:!?)\]⟩—])")

# the traditional name of each of the 27 books, and Lake's Greek heading for it (as Tauber has
# them: Lake's own headings; checked on the page at step 2)
BOOK_NAMES = ([f"Vision {k}" for k in range(1, 6)] + [f"Mandate {k}" for k in range(1, 13)]
              + [f"Similitude {k}" for k in range(1, 11)])
# the continuous chapter numbers (Whittaker-Joly, 1-114): the first continuous number of each book
FIRST_CHAPTER = [1, 5, 9, 22, 25, 26, 27, 28, 29, 33, 35, 37, 38, 39, 40, 43, 44, 50, 51, 52, 53, 54, 61, 66, 67, 78, 111]


def sec_key(sec: str) -> tuple[int, int, int]:
    b, c, v = (re.sub(r"[a-z+]$", "", x) for x in sec.split("."))
    return int(b), int(c), int(v)


def book_name(book: int) -> str:
    return BOOK_NAMES[book - 1]


def continuous_chapter(book: int, chapter: int) -> int:
    return FIRST_CHAPTER[book - 1] + chapter - 1


def cite(sec: str) -> str:
    """'26.30.2' -> 'Similitude 9.30.2'."""
    b, c, v = sec_key(sec)
    return f"{book_name(b)}.{c}.{v}"


# --- Tauber ----------------------------------------------------------------------------------

def tauber_lines(path: Path = TAUBER) -> list[tuple[str, str]]:
    """[(ref, text)], headings included (`1.0.0`), the text NFC with elision ʼ."""
    out = []
    for raw in path.read_text(encoding="utf-8").splitlines():
        if not raw.strip():
            continue
        ref, _, text = raw.partition(" ")
        text = _ELISION.sub(APOS, greek.nfc(text.strip()))
        out.append((ref, text))
    return out


def headings(path: Path = TAUBER) -> dict[int, str]:
    """Each book's heading as Tauber has it (Lake's): {1: 'Ὅρασις αʹ', …, 27: 'Similitudo X'}."""
    return {int(r.split(".")[0]): t for r, t in tauber_lines(path) if r.endswith(".0.0")}


def _is_latin(word: str) -> bool:
    return bool(re.search(r"[A-Za-z]", word)) and not re.search(r"[Ͱ-Ͽἀ-῿]", word)


def tauber_text(path: Path = TAUBER, part: str = "greek") -> list[dict]:
    """The words of the verses in order: {'t', 'skel', 'sec', 'newsec', 'newchapter', 'para',
    'glued', 'verse', 'inverse', 'gap', 'label', 'latin'}. part 'greek': the verses to 26.30.2
    (manuscript A); 'latin': those after it, in which most words are Latin ('latin' True)."""
    out: list[dict] = []
    chapter = None
    for ref, text in tauber_lines(path):
        if ref.endswith(".0.0"):
            continue
        after = sec_key(ref) > sec_key(LAST_GREEK)
        if (part == "greek") == after:
            continue
        b, c, _v = ref.split(".")
        newchapter = (b, c) != chapter
        chapter = (b, c)
        first = True
        for raw in text.split():
            pieces = re.split(r"(?<=[^\s—])—(?=[^\s—])", raw)
            for k, piece in enumerate(pieces):
                piece = piece + ("—" if k + 1 < len(pieces) else "")
                s = skel(piece)
                if not s:
                    if out and not first:
                        out[-1]["t"] += piece
                    continue
                out.append({"t": piece, "skel": s, "sec": ref, "newsec": first, "newchapter": newchapter and first,
                            "para": False, "glued": k > 0, "verse": False, "inverse": False, "gap": False,
                            "label": False, "latin": _is_latin(piece)})
                first = False
    return out


def tauber_sections(path: Path = TAUBER, part: str = "greek") -> dict[str, list[str]]:
    out: dict[str, list[str]] = {}
    for t in tauber_text(path, part):
        out.setdefault(t["sec"], []).append(t["t"])
    return out


# --- First1KGreek: Lake's apparatus notes and margin references --------------------------------

SIGLA_BETA = [  # First1K's spelling of Lake's sigla -> as printed
    (r"N%2", "ℵ*"), (r"Nc", "ℵᶜ"), (r"Na", "ℵᵃ"), (r"\bN\b", "ℵ"), (r"Pam", "Pᵃᵐ"), (r"Pox", "Pᵒˣ"),
    (r"Pber", "Pᵇᵉʳ"), (r"L1", "L₁"), (r"L2", "L₂"),
]


def beta_item(text: str) -> str:
    """A First1K apparatus note in Beta code, the Greek words converted (a word is Greek if it holds
    a Beta accent or breathing sign, begins with * (a capital), or stands between Greek words and
    has no capital Latin letter); sigla as Lake prints them."""
    toks = text.split()
    # an accent, an iota subscript, a capital's star, or a breathing followed by more of the word
    # (a closing parenthesis after a Latin word is not a breathing: "(Cumae)")
    marks = re.compile(r"[/\\=|]|^\(?\*|[aehiouwr][()][a-z/\\=|]|^\(?[aehiouwr]{1,2}[()]$")
    greekish = [bool(marks.search(t)) for t in toks]
    for i, t in enumerate(toks):
        core = t.strip(",.;:()")
        if greekish[i] or not core.isalpha() or not core.islower():
            continue
        if (i > 0 and greekish[i - 1]) and (i + 1 < len(toks) and greekish[i + 1]):
            greekish[i] = True
    out = []
    for t, g in zip(toks, greekish):
        if g:
            lead = re.match(r"^[,.;:]*", t).group(0)
            trail = re.search(r"[,.;:]*$", t).group(0)
            core = t[len(lead):len(t) - len(trail)] if trail else t[len(lead):]
            out.append(lead + greek.betacode_to_unicode(core).replace("’", APOS) + trail)
        else:
            for pat, rep in SIGLA_BETA:
                t = re.sub(pat, rep, t)
            out.append(t)
    return " ".join(out)


_GREEK_TO_BETA = str.maketrans("αβγδεζηθικλμνξοπρσςτυφχψω", "abgdezhqiklmncoprsstufxyw")


def compare_form(item: str, beta: bool = False) -> str:
    """An apparatus item reduced for comparison with the other edition's: Greek letters as Beta
    letters without accents, sigla as First1K writes them, lower case, letters and digits only."""
    s = item
    if beta:
        s = re.sub(r"%\d*", "", s)  # %2 is Beta code's asterisk (ℵ* = N%2)
        s = re.sub(r"[/\\=()|+*]", "", s)
    else:
        s = unicodedata.normalize("NFD", s.lower())
        s = "".join(c for c in s if not unicodedata.combining(c))
        s = s.replace("ℵ", "n").replace("ᶜ", "c").replace("ᵃᵐ", "am").replace("ᵒˣ", "ox").replace("ᵃ", "a")
        s = s.replace("₁", "1").replace("₂", "2").replace("*", "").translate(_GREEK_TO_BETA)
    return re.sub(r"[^a-z0-9]", "", s.lower())


def first1k_marks(f1k: Path = FIRST1K, tauber: Path = TAUBER) -> list[dict]:
    """Lake's footnote marks and margin references as First1K places them, in order: {'kind'
    ('app' or 'bibl'), 'sec' (the verse), 'after' (the index in tauber_text('greek') of the word
    the mark follows; -1 if it could not be placed), 'n' (First1K's number: the footnote's number
    on Lake's page), 'beta' (the note as First1K has it), 'text' (converted)}. Only the verses to
    26.30.2: First1K's Latin pages are garbled into Greek letters."""
    from lxml import etree

    toks = tauber_text(tauber, "greek")
    by_sec: dict[str, list[int]] = {}
    for i, t in enumerate(toks):
        by_sec.setdefault(t["sec"], []).append(i)
    root = etree.parse(str(f1k)).getroot()
    body = root.find(f".//{TEI}body")
    out: list[dict] = []
    for sec_div in body.iter(f"{TEI}div"):
        if sec_div.get("subtype") != "section":
            continue
        anc = [a for a in sec_div.iterancestors(f"{TEI}div") if a.get("subtype") in ("book", "chapter")]
        nums = {a.get("subtype"): a.get("n") for a in anc}
        if "book" not in nums or "chapter" not in nums:
            continue
        sec = f"{nums['book']}.{nums['chapter']}.{sec_div.get('n')}"
        if sec not in by_sec:
            continue
        # the section's words with the notes between them
        words: list[str] = []
        notes: list[tuple[int, etree._Element]] = []

        def walk(el) -> None:
            for child in el:
                if etree.QName(child).localname == "note":
                    notes.append((len(words), child))
                elif etree.QName(child).localname not in ("bibl", "pb", "milestone", "head"):
                    if child.text:
                        words.extend(child.text.split())
                    walk(child)
                if child.tail:
                    words.extend(child.tail.split())

        if sec_div.text:
            words.extend(sec_div.text.split())
        walk(sec_div)
        ws = [skel(w) for w in words]
        ours = by_sec[sec]
        sm = difflib.SequenceMatcher(None, ws, [toks[i]["skel"] for i in ours], autojunk=False)
        pos: dict[int, int] = {}
        for a, b, size in sm.get_matching_blocks():
            for k in range(size):
                pos[a + k] = ours[b + k]
        for at, el in notes:
            # the word before the mark: the nearest First1K word before it that Tauber has
            after = -1
            k = at - 1
            while k >= 0:
                if k in pos:
                    after = pos[k]
                    break
                if ws[k]:
                    break
                k -= 1
            if after == -1 and at == 0:
                after = ours[0] - 1
            bibl = el.find(f"{TEI}bibl")
            beta = " ".join("".join(el.itertext()).split())
            kind = "bibl" if bibl is not None else "app"
            out.append({"kind": kind, "sec": sec, "after": after, "n": el.get("n", ""), "beta": beta,
                        "text": beta if kind == "bibl" else beta_item(beta)})
    return out


# --- Lake's translation and notes (Perseus) ---------------------------------------------------

def _perseus_eng(path: Path):
    from lxml import etree

    root = etree.parse(str(path)).getroot()
    body = root.find(f".//{TEI}body")
    for bk in body.iter(f"{TEI}div"):
        if bk.get("subtype") != "book":
            continue
        for ch in bk.iter(f"{TEI}div"):
            if ch.get("subtype") != "chapter":
                continue
            for sc in ch.iter(f"{TEI}div"):
                if sc.get("subtype") == "section":
                    yield f"{bk.get('n')}.{ch.get('n')}.{sc.get('n')}", sc, bk


def _flat(el, keep_notes: bool = False) -> str:
    from lxml import etree

    bits: list[str] = []

    def w(e) -> None:
        tag = etree.QName(e).localname
        if tag in ("note", "head", "bibl") and not keep_notes:
            return
        if tag == "q":
            bits.append("“")
        if e.text:
            bits.append(e.text)
        for c in e:
            w(c)
            if c.tail:
                bits.append(c.tail)
        if tag == "q":
            bits.append("”")
        if tag in ("l", "p"):
            bits.append(" ")

    w(el)
    s = " ".join("".join(bits).split())
    return re.sub(r"\s+([,.;:!?”])", r"\1", s.replace("“ ", "“"))


def lake_translation(path: Path = PERSEUS_ENG) -> list[tuple[str, str]]:
    """Lake's translation by verse: [('1.1.1', text)], his notes left out. Perseus marks quoted
    speech with <q>; it is written with quotation marks as Lake prints them."""
    return [(sec, _flat(sc)) for sec, sc, _bk in _perseus_eng(path)]


def lake_book_titles(path: Path = PERSEUS_ENG) -> dict[int, str]:
    from lxml import etree

    root = etree.parse(str(path)).getroot()
    out = {}
    for bk in root.find(f".//{TEI}body").iter(f"{TEI}div"):
        if bk.get("subtype") == "book":
            h = bk.find(f"{TEI}head")
            out[int(bk.get("n"))] = " ".join("".join(h.itertext()).split()) if h is not None else ""
    return out


def lake_notes(path: Path = PERSEUS_ENG) -> list[dict]:
    """Lake's notes to his translation: {'sec', 'kind' ('footnote' or 'marginal'), 'text',
    'after' (the English words before the mark, for the lemma)}. A note in a book's heading goes
    to the book's first verse."""
    from lxml import etree

    root = etree.parse(str(path)).getroot()
    out: list[dict] = []
    for bk in root.find(f".//{TEI}body").iter(f"{TEI}div"):
        if bk.get("subtype") != "book":
            continue
        # a note in the book's heading, or between it and the first verse
        first = next((s for s, _sc, b in _perseus_eng(path) if b is bk), f"{bk.get('n')}.1.1")
        for n in bk.iter(f"{TEI}note"):
            if any(a.get("subtype") == "section" for a in n.iterancestors(f"{TEI}div")):
                continue
            out.append({"sec": first, "kind": n.get("type", "footnote"), "text": _flat(n, keep_notes=True),
                        "after": "(the heading)"})
    for sec, sc, _bk in _perseus_eng(path):
        for n in sc.iter(f"{TEI}note"):
            # the words just before the note
            prev = n.getprevious()
            text_before = (prev.tail if prev is not None else n.getparent().text) or ""
            out.append({"sec": sec, "kind": n.get("type", "footnote"), "text": _flat(n, keep_notes=True),
                        "after": " ".join(text_before.split()[-4:])})
    return out
