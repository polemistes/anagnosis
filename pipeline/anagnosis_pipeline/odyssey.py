"""Import Homer's Odyssey into texts/odyssey/.

Sources (pipeline/sources/, see fetch.py):
    odyssey.perseus-gk.xml              Perseus Greek text (Murray's Loeb, 1919), TEI P4, Beta Code
    odyssey.murray-eng.xml              Murray's translation (Loeb, 1919), TEI P4
    odyssey-merry-monro-commentary.xml  Merry & Riddell (books 1-12, 1886) and Monro (13-24, 1901)
    treebanks/tlg0012.tlg002.perseus-grc1.tb.xml   Ancient Greek Dependency Treebank 2.1

The Greek text of the edition is Allen's second Oxford edition (1917, 1919). It is not
available digitally, so `import-odyssey` writes the Perseus text as a draft, and
`merge-odyssey` replaces it with the page-by-page transcription of Allen's text and
apparatus (pipeline/transcriptions/odyssey/), re-aligning the treebank to the new text.

Line numbers are book.line (1.1 ... 24.548).
"""
from __future__ import annotations

import csv
import difflib
import re
import sys
from pathlib import Path

from . import greek
from .tei_p4 import load as load_p4
from .textfmt import Document, Line, Section, Speaker, write_file

BOOK_LETTERS = "ΑΒΓΔΕΖΗΘΙΚΛΜΝΞΟΠΡΣΤΥΦΧΨΩ"

GREEK_META = {
    "title": "Ὀδύσσεια",
    "author": "Ὅμηρος",
    "lang": "grc",
    "source": "Homeri Opera, recognovit brevique adnotatione critica instruxit Thomas W. Allen, tomi III-IV, "
    "editio altera, Oxford 1917, 1919; transcribed from the Internet Archive scans homeriopera03home, "
    "homeriopera04home (with homerioperarecog03homeuoft, homerioperarecog04homeuoft)",
    "edition": "Homeri Opera III-IV, ed. T. W. Allen, 2nd ed., Oxford 1917-1919",
    "license": "CC BY-SA 4.0 (transcription; the edition is in the public domain)",
}

DRAFT_META = {
    **GREEK_META,
    "source": "Perseus Digital Library, hom.od_gk.xml (Murray's Loeb text, 1919); draft until merge-odyssey",
    "edition": "The Odyssey, ed. A. T. Murray, Loeb 1919 (Perseus Digital Library)",
    "license": "CC BY-SA 3.0 US",
}


def section_for(book: int) -> Section:
    return Section(1, "book", f"{book} · {BOOK_LETTERS[book - 1]}")


# ---------------------------------------------------------------- Greek (Perseus draft)

def _text_of(el) -> str:
    parts = [el.text or ""]
    for child in el:
        if isinstance(child.tag, str):
            parts.append(_text_of(child))
        parts.append(child.tail or "")
    return "".join(parts)


def clean_greek(raw: str) -> str:
    """A Perseus Beta Code line as Unicode, without the Loeb's quotation marks."""
    raw = re.sub(r"[“”‘’]", "", raw)
    raw = raw.replace("[", "⟦").replace("]", "⟧")
    text = greek.betacode_to_unicode(re.sub(r"\s+", " ", raw).strip())
    text = text.replace("⟦", "[").replace("⟧", "]").replace("'", greek.APOSTROPHE)
    text = re.sub(r"\s+([,.;·])", r"\1", text)
    return re.sub(r"\s+", " ", text).strip()


def perseus_greek(path: Path) -> Document:
    """The Perseus text, one section per book; lines numbered book.line.

    The file states the number of every fifth line. Between two stated numbers a and b the
    lines are counted from a; when there are more lines than numbers (a plus-verse), the
    extra ones take a letter after the last number (1.93a); when there are fewer (a line
    the file lacks), the numbers before b are skipped.
    """
    root = load_p4(path)
    doc = Document(meta=dict(DRAFT_META))
    for div in root.iter("div1"):
        book = int(div.get("n"))
        doc.items.append(section_for(book))
        raw = [(l.get("n"), clean_greek(_text_of(l))) for l in div.iter("l")]
        stated = [i for i, (n, _) in enumerate(raw) if n and n.isdigit()]
        numbers: list[str] = [""] * len(raw)
        anchors = [(0, 0)] + [(i, int(raw[i][0])) for i in stated] + [(len(raw), None)]
        if not stated or stated[0] != 0:
            anchors[0] = (0, 1)
        else:
            anchors = anchors[1:]
        for (i, a), (j, b) in zip(anchors, anchors[1:]):
            count = j - i
            slots = (b - a) if b is not None else count
            for k in range(count):
                if k < slots:
                    numbers[i + k] = str(a + k)
                else:
                    numbers[i + k] = f"{a + slots - 1}{'abcdefgh'[k - slots]}"
        for number, (_n, text) in zip(numbers, raw):
            doc.items.append(Line(f"{book}.{number}", text))
    return doc


# ---------------------------------------------------------------- Murray's translation

MURRAY_META = {
    "title": "The Odyssey",
    "translator": "A. T. Murray",
    "lang": "eng",
    "source": "Perseus Digital Library, hom.od_eng.xml",
    "edition": "Homer, The Odyssey, with an English translation by A. T. Murray, Loeb Classical Library, 1919",
    "license": "CC BY-SA 3.0 US",
}


def murray_translation(path: Path) -> Document:
    """Murray's prose, cut at his line markers (every fifth line).

    Each piece is anchored to the Greek line its marker names. A line break in the source
    starts a new paragraph (written as an empty speaker, '@'); a paragraph that begins between
    two markers is anchored to a line estimated from its position in the text between them.
    """
    root = load_p4(path)
    doc = Document(meta=dict(MURRAY_META))
    for div in root.iter("div1"):
        book = int(div.get("n"))
        doc.items.append(section_for(book))
        # flatten to a stream of text and line markers
        stream: list[tuple[str, str]] = []  # ("text", s) | ("line", n)

        def walk(node):
            if node.text:
                stream.append(("text", node.text))
            for child in node:
                if isinstance(child.tag, str):
                    if child.tag == "milestone":
                        if child.get("unit") == "line":
                            stream.append(("line", child.get("n")))
                    elif child.tag == "note":
                        pass
                    else:
                        walk(child)
                if child.tail:
                    stream.append(("text", child.tail))

        walk(div)
        # pieces between markers: (anchor line, text)
        pieces: list[tuple[int, str]] = []
        current, buf = 1, []
        for kind, value in stream:
            if kind == "line":
                if buf:
                    pieces.append((current, "".join(buf)))
                current, buf = int(value), []
            else:
                buf.append(value)
        if buf:
            pieces.append((current, "".join(buf)))
        new_para = True
        last = 0
        for i, (anchor, text) in enumerate(pieces):
            nxt = pieces[i + 1][0] if i + 1 < len(pieces) else anchor + 5
            parts = text.split("\n")
            total = max(1, len(text))
            pos = 0
            for k, part in enumerate(parts):
                if k > 0:
                    new_para = True  # a line break in the source is a paragraph break
                body = re.sub(r"\s+", " ", part).strip()
                start_pos, pos = pos, pos + len(part) + 1
                if not body:
                    continue
                if start_pos == 0:
                    n = anchor
                else:
                    n = anchor + round((nxt - anchor) * start_pos / total)
                    n = max(n, last + 1)
                    if n >= nxt:
                        n = max(last, anchor)
                prev = doc.items[-1] if doc.items else None
                if not new_para and isinstance(prev, Line) and prev.n == f"{book}.{n}":
                    doc.items[-1] = Line(prev.n, prev.text + " " + body)
                    continue
                if new_para:
                    doc.items.append(Speaker(""))
                    new_para = False
                doc.items.append(Line(f"{book}.{n}", body))
                last = n
    return doc


# ---------------------------------------------------------------- commentary

COMMENTARY_META = {
    "title": "Commentary on the Odyssey",
    "author": "W. W. Merry and J. Riddell (books 1-12); D. B. Monro (books 13-24)",
    "lang": "eng",
    "source": "Perseus Digital Library, monro.hom.od_eng.xml: Homer's Odyssey, Books I-XII, ed. Merry and Riddell, "
    "2nd ed., Oxford 1886; Books XIII-XXIV, ed. Monro, Oxford 1901",
    "license": "CC BY-SA 3.0 US",
}

_SUP = str.maketrans("0123456789", "⁰¹²³⁴⁵⁶⁷⁸⁹")


def import_commentary(source: Path, out: Path) -> int:
    from .commentary import _md

    root = load_p4(source)
    lines = [f"# {k}: {v}" for k, v in COMMENTARY_META.items()]
    lines.append("")
    count = 0

    def clean(md: str) -> str:
        md = re.sub(r"\^\{(\d+)\}", lambda m: m.group(1).translate(_SUP), md)
        md = re.sub(r"[ \t]+\n", "\n", md)
        md = re.sub(r"\n{3,}", "\n\n", md).strip()
        return re.sub(r" +", " ", md)

    for div1 in root.iter("div1"):
        book = int(div1.get("n"))
        for d2 in div1.iter("div2"):
            n = int(d2.get("n"))
            paras = [c for c in d2 if isinstance(c.tag, str) and c.tag != "head"]
            body = "\n\n".join(clean(_md(p, False)) for p in paras)
            # a note that opens with "5-6." covers a range of lines
            heading = f"{book}.{n}"
            m = re.match(r"^(\d+)\s*[-–]\s*(\d+)\.\s", body)
            if m and int(m.group(1)) == n and int(m.group(2)) > n:
                heading = f"{book}.{n}-{book}.{int(m.group(2))}"
            # cross references to other notes: <ref target="cb13l5"> -> (#13.5)
            body = re.sub(r"\]\(#cb(\d+)l(\d+)\)", r"](#\1.\2)", body)
            lines.append(f"## {heading}")
            lines.append(body)
            lines.append("")
            count += 1
    out.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return count


# ---------------------------------------------------------------- treebank

TREEBANK = "treebanks/tlg0012.tlg002.perseus-grc1.tb.xml"


def read_treebank(path: Path) -> list[dict]:
    """Treebank words in the order of the poem.

    The file stores the books in string order (1, 10, 11 ... 19, 2, 20 ...); sentences are
    sorted by book and by the first line cited. Artificial (elliptic) nodes and punctuation
    are included with is_word False.
    """
    from lxml import etree

    tree = etree.parse(str(path))
    sentences = []
    for sent in tree.iter("sentence"):
        cites = [w.get("cite", "") for w in sent.iter("word") if w.get("cite")]
        first = cites[0].rsplit(":", 1)[-1] if cites else (sent.get("subdoc") or "0.0").split("-")[0]
        m = re.match(r"^(\d+)\.(\d+)", first)
        key = (int(m.group(1)), int(m.group(2))) if m else (999, 0)
        sentences.append((key, int(sent.get("id")), sent))
    sentences.sort(key=lambda t: (t[0], t[1]))
    out = []
    for _key, _id, sent in sentences:
        for w in sent.iter("word"):
            form = greek.nfc(w.get("form", ""))
            artificial = bool(w.get("artificial") or w.get("insertion_id"))
            out.append(
                {
                    "sentence": sent.get("id"),
                    "word_id": w.get("id"),
                    "form": form,
                    "lemma": greek.nfc(w.get("lemma", "")),
                    "postag": w.get("postag", ""),
                    "head": w.get("head", ""),
                    "relation": w.get("relation", ""),
                    "cite": (w.get("cite") or "").rsplit(":", 1)[-1],
                    "artificial": artificial,
                    "is_word": not artificial and greek.is_word(form),
                }
            )
    return out


def _skeleton(s: str) -> str:
    return greek.strip_diacritics(s).replace("ς", "σ")


# Treebank lemmas to correct (spelling, or a form used as lemma). Applied after alignment, after
# a stray breathing mark at the start of a lemma (̓ὀδυσσεύς) has been removed.
LEMMA_FIXES: dict[str, str] = {
    "ὀδυσσεύς": "Ὀδυσσεύς", "ἀθήνη": "Ἀθήνη", "ὠγυγία": "Ὠγυγία",
    "πάτηρ": "πατήρ", "ἤτορ": "ἦτορ", "παίς": "παῖς", "ὁμοῖος": "ὅμοιος",
    "Ποσειδεών": "Ποσειδῶν",  # the month, for Poseidon
    # forms or fragments used as lemmas, and misspellings (found while writing the glossary)
    "δέ+οὐ": "οὐδέ", "+δέ": "οὐδέ", "καθέζετο": "καθέζομαι", "τοιοῦτον": "τοιοῦτος", "Ἠοῦς": "ἠώς",
    "Πηληι": "Πηληιάδης", "Νηληι": "Νηληιάδης", "Τυδει": "Τυδείδης", "Βοηθοί": "Βοηθοΐδης", "Δηί": "Δηΐφοβος",
    "Π́ερση": "Πέρση", "Πάνδαρος": "Πανδάρεος", "Διοκλής": "Διοκλῆς",
    "δουλίχιος": "Δουλίχιον", "δουλικίον": "Δουλίχιον", "δουλιχίον": "Δουλίχιον", "Δουλιχιόν": "Δουλίχιον",
    "Δουλίχιόδε": "Δουλίχιον", "ʽἑρμῆς": "Ἑρμῆς", "χαρίες": "χαρίεις", "ἀγήρωρ": "ἀγήνωρ", "τεύκω": "τεύχω",
    "πάροιθεϝ": "πάροιθε", "ὀ͂νοψ": "οἶνοψ", "πημί": "φημί", "θυμαλέων": "θυμολέων", "ἀγριοώτης": "ἀγροιώτης",
    "πολυμενθης": "πολυπενθής", "δασυπλῆτις": "δασπλῆτις", "ἀγκυλχείλης": "ἀγκυλοχείλης",
    "ἠ~μος": "ἦμος", "δι~ος": "δῖος", "πα~ς": "πᾶς", "γλαυκω~πις": "γλαυκῶπις",
    "Ἀι": "ᾍδης", "Ἄι": "ᾍδης", "κάλη": "καλός", "μάκαρος": "μάκαρ", "ἱερή": "ἱερός", "κάτος": "κατά",
    "ἐγώγε": "ἐγώ", "δαί̓ς": "δαίς",
    # from merging Allen's text, where he joins or divides words differently from the treebank
    "ὣς": "ὡς", "δ̓": "δέ", "ἀλλ̓": "ἀλλά", "κ̓": "κε", "εὖ+φρονέω": "εὐφρονέω", "τρίς+μάκαρ": "τρισμάκαρ",
    "εὐρύς+κρείων": "εὐρυκρείων", "εἰ+ποτέ": "εἰ", "πᾶς+μέλω": "πασιμέλουσα", "τὸν": "ὁ", "Χρομίος": "Χρόμιος",
    "καλλιγύναικα": "καλλιγύναιξ", "ὕπερθε": "ὕπερθεν", "πολύ": "πολύς", "ἠδή": "ἤδη", "ἐνειμί": "ἔνειμι",
}


def fix_lemma(lemma: str) -> str:
    lemma = lemma.lstrip("\u0313\u0314'’ʼ᾿ʽ῎῾῞῍῏")
    return LEMMA_FIXES.get(lemma, lemma)


def align(doc: Document, tb: list[dict], keep_tb_form: bool = False) -> tuple[list[dict], list[str]]:
    """Pair the words of the text with treebank words, in order.

    A difflib alignment of skeletons (no diacritics) finds the stretches that agree; inside a
    stretch that differs, a text word may equal 2-4 consecutive treebank words joined
    (the treebank splits οὔτε, κἀγώ ...), or be paired one to one when the counts agree.
    Words left over get no annotation here; merge-odyssey and the analyser fill them in.
    """
    text_words: list[tuple[str, int, str]] = []
    for line in doc.lines:
        for ord_, (form, _s, _e) in enumerate(greek.words(line.text)):
            text_words.append((line.n, ord_, form))
    tb_words = [w for w in tb if w["is_word"]]
    ta = [_skeleton(f) for _, _, f in text_words]
    tbs = [_skeleton(w["form"]) for w in tb_words]
    matched: dict[int, list[dict]] = {}
    warnings: list[str] = []
    sm = difflib.SequenceMatcher(None, ta, tbs, autojunk=False)
    for op, i1, i2, j1, j2 in sm.get_opcodes():
        if op == "equal":
            for k in range(i2 - i1):
                matched[i1 + k] = [tb_words[j1 + k]]
            continue
        # try merges inside the block: text word = several treebank words
        i, j = i1, j1
        while i < i2 and j < j2:
            acc, hit = "", 0
            for k in range(1, 5):
                if j + k > j2:
                    break
                acc += tbs[j + k - 1]
                if acc == ta[i]:
                    hit = k
                    break
                if len(acc) >= len(ta[i]):
                    break
            if hit:
                matched[i] = tb_words[j : j + hit]
                i += 1
                j += hit
            else:
                break
        rest_t, rest_b = i2 - i, j2 - j
        if rest_t and rest_t == rest_b:
            for k in range(rest_t):  # a variant reading: same number of words, paired in order
                matched[i + k] = [tb_words[j + k]]
                warnings.append(f"{text_words[i + k][0]}: paired {text_words[i + k][2]!r} with treebank {tb_words[j + k]['form']!r}")
        elif rest_t:
            warnings.append(
                f"{text_words[i][0]}: no treebank words for {[f for _, _, f in text_words[i:i2]]}"
                + (f" (treebank has {[w['form'] for w in tb_words[j:j2]]})" if rest_b else "")
            )
    rows: list[dict] = []
    for idx, (n, ord_, form) in enumerate(text_words):
        ws = matched.get(idx)
        row = {"line": n, "ord": ord_, "form": form, "lemma": "", "postag": "", "relation": "", "head": "", "sentence": "", "word_id": ""}
        if ws and len(ws) == 1:
            w = ws[0]
            row.update(lemma=w["lemma"], postag=w["postag"], relation=w["relation"], head=w["head"], sentence=w["sentence"], word_id=w["word_id"])
            if keep_tb_form:
                row["tb_form"] = w["form"]
        elif ws:
            from .import_perseus import _merge_lemma

            w = ws[0]
            row.update(lemma=_merge_lemma(form, ws), sentence=w["sentence"], word_id="+".join(x["word_id"] for x in ws),
                       relation=w["relation"], head=w["head"])
            # the first part's tag fits when the merge is a crasis or compound of it
            row["postag"] = w["postag"] if _skeleton(ws[0]["lemma"]).startswith(_skeleton(form)[:2]) else ""
        row["lemma"] = fix_lemma(row["lemma"])
        rows.append(row)
    return rows, warnings


def syntax_nodes(tb: list[dict], used: set[tuple[str, str]]) -> list[dict]:
    """Treebank nodes that are not words of the text: punctuation, omitted words, and words
    the edition does not print (so that the trees stay whole)."""
    out = []
    for w in tb:
        if w["is_word"] and (w["sentence"], w["word_id"]) in used:
            continue
        out.append(
            {
                "sentence": w["sentence"], "word_id": w["word_id"], "form": w["form"],
                "lemma": w["lemma"] if not w["artificial"] else "",
                "postag": w["postag"] if not w["artificial"] else "",
                "relation": w["relation"], "head": w["head"], "artificial": "1" if w["artificial"] else "",
            }
        )
    return out


# ---------------------------------------------------------------- entry point

def import_odyssey(sources: Path, texts: Path) -> None:
    from .import_perseus import SYNTAX_NODE_COLUMNS, write_syntax_nodes, write_tokens

    out = texts / "odyssey"
    out.mkdir(parents=True, exist_ok=True)

    doc = perseus_greek(sources / "odyssey.perseus-gk.xml")
    write_file(out / "grc.txt", doc)
    print(f"wrote {out / 'grc.txt'}: {len(doc.lines)} lines (Perseus draft)")

    eng = murray_translation(sources / "odyssey.murray-eng.xml")
    write_file(out / "eng-murray.txt", eng)
    print(f"wrote {out / 'eng-murray.txt'}: {len(eng.lines)} segments")

    n = import_commentary(sources / "odyssey-merry-monro-commentary.xml", out / "commentary-merry-monro.md")
    print(f"wrote {out / 'commentary-merry-monro.md'}: {n} notes")

    tb = read_treebank(sources / TREEBANK)
    rows, warnings = align(doc, tb)
    write_tokens(out / "tokens.tsv", rows)
    used = set()
    for r in rows:
        for wid in r["word_id"].split("+"):
            if wid:
                used.add((r["sentence"], wid))
    nodes = syntax_nodes(tb, used)
    write_syntax_nodes(out / "syntax-nodes.tsv", nodes)
    missing = sum(1 for r in rows if not r["lemma"])
    print(f"wrote {out / 'tokens.tsv'}: {len(rows)} words, {missing} without lemma, {len(warnings)} warnings")
    print(f"wrote {out / 'syntax-nodes.tsv'}: {len(nodes)} nodes")
    (sources.parent / "build").mkdir(exist_ok=True)
    (sources.parent / "build" / "odyssey-align.log").write_text("\n".join(warnings) + "\n", encoding="utf-8")
