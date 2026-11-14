"""Convert Perseus lexica (LSJ, Middle Liddell) to a list of entries with HTML bodies.

The HTML uses only <p>, <b>, <i>, <span>, <a> and <br> so that the app can render it with
a minimal HTML-to-styled-text converter.

The first paragraph of an entry (class "head") holds the headword and, in LSJ, the forms section:
its lines are separated by <br>, with an empty line before a new voice. Tense labels carry the
classes "gram tns" and voice labels "gram voice", so that the app can show the structure.
"""
from __future__ import annotations

import collections
import html
import re
import unicodedata
from dataclasses import dataclass
from pathlib import Path

from lxml import etree

from . import greek
from .tei_p4 import load as load_p4

GRAM_TAGS = {"gramGrp", "pos", "gen", "itype", "tns", "mood", "per", "num", "number", "pron", "case", "gram"}
SKIP_TAGS = {"pb", "milestone", "index"}


@dataclass
class Entry:
    lexicon: str
    key: str          # raw betacode key from the source, e.g. "a)gaqo/s" or "a)1"
    headword: str     # Unicode headword, without homograph number
    homograph: int    # 0 if none
    html: str
    sort_key: str     # for alphabetical ordering


_VOWELS = "aehiouw"
_BRACKETED = re.compile(r"(\(*)(.*?)(\)*)([,.;:]*)", re.S)


def _greek(s: str) -> str:
    """Betacode to Unicode, keeping the brackets that stand inside Greek text ("(ai)/qw)").

    The converter reads every bracket as a breathing. A breathing follows its vowel, so a bracket
    before a word opens a parenthesis; and one after a word closes it when the word has its
    breathing already or, starting with a consonant, takes none.
    """
    def word(t: str) -> str:
        opening, body, closing, stops = _BRACKETED.fullmatch(t).groups()
        if not opening and not closing:
            return greek.betacode_to_unicode(t)
        first = body.lstrip("*")[:1].lower()
        if closing and first and first in _VOWELS and "(" not in body and ")" not in body:
            body, closing = body + ")", closing[1:]     # the word's own breathing
        return opening + greek.betacode_to_unicode(body) + closing + greek.betacode_to_unicode(stops)

    return "".join(t if t.isspace() or not t else word(t) for t in re.split(r"(\s+)", s))


def _text(s: str | None, grk: bool) -> str:
    if not s:
        return ""
    if grk:
        s = _greek(s)
    return html.escape(s, quote=False)


def _render(el, grk: bool, out: list[str]) -> None:
    """Append the HTML rendering of `el` (children and tails handled here) to out."""
    tag = etree.QName(el).localname
    grk = grk or el.get("lang") == "greek"
    if tag in SKIP_TAGS:
        return
    if tag == "sense":
        _sense(el, grk, out)
        return
    open_, close = "", ""
    if tag in ("orth",):
        open_, close = '<b class="orth">', "</b>"
    elif tag in ("tr", "trans"):
        open_, close = '<i class="tr">' if tag == "tr" else "", "</i>" if tag == "tr" else ""
    elif tag in ("foreign", "quote", "lemma"):
        open_, close = f'<span class="{tag}">', "</span>"
    elif tag == "cit":
        open_, close = '<span class="cit">', "</span>"
    elif tag == "bibl":
        n = el.get("n")
        attr = f' data-ref="{html.escape(n, quote=True)}"' if n else ""
        open_, close = f'<span class="bibl"{attr}>', "</span>"
    elif tag == "ref":
        target = el.get("target") or ""
        attr = f' data-ref="{html.escape(target, quote=True)}"' if target else ""
        open_, close = f'<span class="ref"{attr}>', "</span>"
    elif tag in GRAM_TAGS:
        cls = ("gram tns" if tag == "tns" else "gram mood" if tag == "mood"
               else "gram voice" if tag == "gram" and el.get("type") == "voice" else "gram")
        open_, close = f'<span class="{cls}">', "</span>"
    elif tag in ("usg", "etym", "note", "xr", "abbr", "lbl", "date", "placeName", "author", "title", "biblScope", "hi", "emph"):
        cls = "i" if tag in ("hi", "emph", "title") else "span"
        open_, close = f'<{cls} class="{tag}">', f"</{cls}>"
    elif tag in ("entryFree", "entry", "form", "item", "list", "p", "div", "num", "date", "term"):
        pass
    else:
        open_, close = f'<span class="{tag}">', "</span>"
    out.append(open_)
    _children(el, grk, out)
    out.append(close)


def _sense(el, grk: bool, out: list[str], labels: list[str] | None = None, content: str | None = None) -> None:
    """A sense as a paragraph: its number in bold (or `labels`, each in bold), then its content
    (or `content`, already rendered)."""
    level = int(el.get("level") or 1)
    n = el.get("n") or ""
    indent = " " * max(level - 1, 0)
    out.append(f'<p class="sense">{indent}')
    if labels is None:
        labels = [n] if n and not n.startswith("0") else []    # "0", "0-0": a section without a number
    for label in labels:
        out.append(f"<b>{html.escape(label)}.</b> ")
    if content is None:
        _children(el, grk, out)
    else:
        out.append(content)
    out.append("</p>")


def _children(el, grk: bool, out: list[str]) -> None:
    out.append(_text(el.text, grk))
    for child in el:
        if isinstance(child.tag, str):  # skip comments and processing instructions
            _render(child, grk, out)
        # the tail belongs to the parent's language, not the child's
        out.append(_text(child.tail, grk))


_WS = re.compile(r"\s+")
# a line that opens with a label: the space inside its tags would indent the line by a letter
_BR_SPACE = re.compile(r"<br>((?:<(?!/)[^>]*>)+)\s+")


# Metrical schemes in the English text of the lexica, written with the signs of a typewriter:
# "^—^^", "_ _ ^", "(scanned - ^)", "˘ ˘ ¯". They become the metrical signs, ⏑ for a short and –
# for a long syllable. A run counts as a scheme when it holds a sign that is never anything else
# (^ _ ˘ ¯ ⏑); a dash or hyphen alone stays what it is.
_METRE = re.compile(r"(?<![\wͰ-Ͽἀ-῿̀-ͯ\-—])"
                    r"((?:[\^_˘¯⏑—\-–×|\[\]] ?)*[\^_˘¯⏑](?: ?[\^_˘¯⏑—\-–×|\[\]])*)"
                    r"(?![\wͰ-Ͽἀ-῿\-—])")
_METRE_SIGNS = str.maketrans({"^": "⏑", "˘": "⏑", "_": "–", "¯": "–", "—": "–", "-": "–"})


_LATIN_LENGTH = re.compile(r"(?<=[A-Za-z])?([aeiouyAEIOUY])([\^_])(?=[a-z])|(?<=[a-z])([aeiouy])([\^_])")


def _latin_length(m: re.Match) -> str:
    vowel, mark = (m.group(1), m.group(2)) if m.group(1) else (m.group(3), m.group(4))
    return unicodedata.normalize("NFC", vowel + ("\u0306" if mark == "^" else "\u0304"))


def _metre(html_text: str) -> str:
    """The metrical schemes of an entry's HTML in metrical signs, and the length marks of Latin
    words over their vowel ("balsa^mum" gives balsămum), outside the tags."""
    def fix(text: str) -> str:
        text = text.replace("Ae_r.", "Aër.")  # Hippocrates' De aëre, whose diaeresis the file writes so
        return _METRE.sub(lambda m: m.group(1).translate(_METRE_SIGNS), _LATIN_LENGTH.sub(_latin_length, text))
    return "".join(p if p.startswith("<") else fix(p) for p in re.split(r"(<[^>]+>)", html_text))


def render_entry(el) -> str:
    """A Middle Liddell entry as HTML.

    Before the senses the file holds the forms and the derivation as separate notes, without the
    stops of the printed book: each gets a line of its own. A note of machine stem codes
    ("diakwlu_s is_ews fem") is no part of the dictionary and is left out.
    """
    out: list[str] = [_text(el.text, False)]
    head = True
    for child in el:
        if isinstance(child.tag, str):
            head = head and child.tag != "sense"
            if child.tag == "gramGrp" and child.find("note") is not None:
                pass
            else:
                if head and child.tag in ("note", "etym"):
                    out.append("<br>")
                _render(child, False, out)
        out.append(_text(child.tail, False))
    s = "".join(out)
    s = _WS.sub(" ", s)
    s = _BR_SPACE.sub(r"<br>\1", re.sub(r" ?<br> ?", "<br>", s))
    s = s.replace(" </p>", "</p>").replace("<p class=\"sense\"> ", "<p class=\"sense\">")
    # the head matter (before the first sense) becomes its own paragraph
    if not s.startswith("<p"):
        i = s.find("<p")
        head, rest = (s, "") if i < 0 else (s[:i], s[i:])
        s = f"<p class=\"head\">{head.strip()}</p>{rest}"
    return _metre(s).strip()


# ---------------------------------------------------------------- LSJ: the forms section
#
# In the printed lexicon an entry is one paragraph: the headword, its forms (tenses, cases, dialect
# forms, each with its authority), then the meanings. The Perseus file gives every entry a section
# "A", and opens it by rule: after the last headword form, at the first quoted form, and so on.
# Where a quoted form comes first, "A." lands inside the forms ("impf. | A. ἠρχόμην"); where a
# derived word is marked as a headword, it lands after that word, past the entry's own meaning
# ("Κελτοί, οἱ, Celts … hence Κελτικός, | A. Celtic"). The repair below takes the forms back into
# the head paragraph and puts "A." where the meanings start. The letter itself is shown only in
# the entries that go on to a "B.": elsewhere it is the file's addition, and print has none.


@dataclass
class _Frag:
    """A piece of an element's content at its top level: a run of text, or a child rendered."""
    kind: str   # text, tr, greek, tns, voice, label, infl, xr, other
    html: str


def _kind(el) -> str:
    tag = el.tag
    if tag in ("tr", "title"):
        return "tr"     # italics; outside the senses the file marks them as titles ("Celts")
    if tag == "tns":
        return "tns"
    if tag == "gram" and el.get("type") == "voice":
        return "voice"
    if tag == "gramGrp":
        kids = [k for k in el if isinstance(k.tag, str)]
        return "voice" if len(kids) == 1 and _kind(kids[0]) == "voice" else "label"
    if tag in ("gen", "itype", "pos"):
        return "infl"   # ὁ, εος, ή όν: what follows a headword
    if tag in GRAM_TAGS or tag in ("usg", "lbl", "abbr"):
        return "label"
    if tag in ("foreign", "quote", "cit", "orth"):
        return "greek"
    if tag == "xr":
        return "xr"
    return "other"


def _frags(text: str | None, nodes: list) -> list[_Frag]:
    """The content of an element as fragments. A quotation with its citation (<cit>) is taken
    apart into its pieces: the file wraps whole stretches in one ("ἀφίημι) one who lets off a
    military engine, Plb. 4.56.3"), and a divider may stand inside."""
    frags = []
    if text:
        frags.append(_Frag("text", _text(text, False)))
    for k in nodes:
        if isinstance(k.tag, str) and k.tag == "cit":
            frags.extend(_frags(k.text, list(k)))
        elif isinstance(k.tag, str) and k.tag not in SKIP_TAGS:
            out: list[str] = []
            _render(k, False, out)
            frags.append(_Frag(_kind(k), "".join(out)))
        if k.tail:
            frags.append(_Frag("text", _text(k.tail, False)))
    return frags


def _blank(f: _Frag) -> bool:
    return f.kind == "text" and not f.html.strip()


def _plain(html_text: str) -> str:
    return re.sub(r"<[^>]+>", "", html_text)


def _plain_len(html_text: str) -> int:
    return len(_WS.sub(" ", _plain(html_text)).strip())


def _brackets(text: str, depth: int = 0) -> int:
    """How many brackets stand open after `text`, with `depth` open before it."""
    for ch in text:
        if ch in "([":
            depth += 1
        elif ch in ")]":
            depth = max(depth - 1, 0)
    return depth


def _matched(frags: list[_Frag]) -> list[str]:
    """The text of each fragment (of a run of text as it stands, of a child without its tags),
    with every bracket that has no partner blanked out.

    The file has brackets that are never closed ("fut. ἀκούσομαι ( Act. ἀκούσω first in …"):
    counted, such a bracket would hold everything after it for a parenthesis.
    """
    texts = [f.html if f.kind == "text" else _plain(f.html) for f in frags]
    open_: list[tuple[int, int, str]] = []
    paired = set()
    for i, text in enumerate(texts):
        for pos, ch in enumerate(text):
            if ch in "([":
                open_.append((i, pos, ch))
            elif ch in ")]":
                partner = "(" if ch == ")" else "["
                for n in range(len(open_) - 1, -1, -1):
                    if open_[n][2] == partner:
                        paired.update((open_[n][:2], (i, pos)))
                        del open_[n:]
                        break
    return ["".join(ch if ch not in "()[]" or (i, pos) in paired else " " for pos, ch in enumerate(text))
            for i, text in enumerate(texts)]


_GLOSS = re.compile(r"[A-Za-z][A-Za-z ,;:.'’()-]*")
_ABBREVIATION = re.compile(r"[A-Z][a-z]{0,5}\.+")
_TR = re.compile(r'<i class="tr">(.*?)</i>', re.S)


def _is_gloss(tr_text: str) -> bool:
    """Whether an italic phrase reads as an English translation.

    The file marks every italic as a translation: also a lone letter ("the a is short"), a stem
    ("nar-"), the title of a work ("Ep.", "V A"), which define nothing.
    """
    text = _plain(tr_text).rpartition("—")[2].strip()
    if _ABBREVIATION.fullmatch(text):
        return False
    if re.search(r"\.\S", text) or (text.endswith(".") and text.split()[-1][:1].isupper()):
        return False    # "Fr.anon.", "Acut.(Sp.", "Bis Acc.", "D Mort."
    text = text.strip(" ,;:.")
    if not _GLOSS.fullmatch(text) or text.endswith("-"):
        return False
    return bool(re.search(r"[a-z]{2}", text)) or text == "I" or bool(re.fullmatch(r"[A-Z][a-z]", text))


_ITALIC = re.compile(r"(<i[^>]*>)(.*)(</i>)", re.S)


def _split_italics(frags: list[_Frag]) -> list[_Frag]:
    """The same fragments, with the italics cut where a divider stands inside them: a dash
    ("serpo):—move slowly"), or the bracket that closes an etymology ("ibo) withdraw, retreat").
    The dash becomes text, so that it divides like any other."""
    out = []
    for f in frags:
        m = _ITALIC.fullmatch(f.html) if f.kind == "tr" else None
        if m is None or "<" in m.group(2):
            out.append(f)
            continue
        open_, text, close = m.groups()
        pieces = [text]
        dash = re.fullmatch(r"(.*?)(:?\s*—)(.*)", text, re.S)
        if dash:
            pieces = [dash.group(1), None, dash.group(3)]
            out_dash = dash.group(2)
        cut: list[_Frag] = []
        for piece in pieces:
            if piece is None:
                cut.append(_Frag("text", out_dash))
                continue
            depth = 0
            for pos, ch in enumerate(piece):
                if ch in "([":
                    depth += 1
                elif ch in ")]":
                    depth -= 1
                    if depth < 0 and piece[pos + 1:].strip():
                        cut.append(_Frag("tr", open_ + piece[:pos + 1] + close))
                        piece = piece[pos + 1:]
                        break
            if piece.strip() or not cut:
                cut.append(_Frag("tr", open_ + piece + close))
            elif piece:
                cut.append(_Frag("text", piece))
        out.extend(cut)
    return out


# what may stand between a divider and the meaning it opens: words, labels, a Greek word without citation
_LIGHT = {"text", "label", "infl", "tns", "voice"}
# the longest such run that still belongs to the meaning ("an umbelliferous plant growing in Crete, Athamanta")
_LEAD_IN = 60
_CLAUSE_END = (",", ";", ":", ".", "·", ";")


@dataclass
class _Segment:
    """A stretch of a section between two dashes outside brackets."""
    start: tuple[int, int]          # the fragment and the offset in its text where it starts
    opens: str | None = None        # the kind of its first fragment
    strong: int | None = None       # its first translation that stands on its own
    clause: int | None = None       # its first translation that opens a clause (": scratch, gash")
    weak: int | None = None         # its first Greek phrase with a translation
    tenses: int = 0                 # the tenses and moods named before its first translation


def _segments(frags: list[_Frag], texts: list[str], depth: int) -> list[_Segment]:
    """The section cut at its dashes, with what each stretch holds. `texts` are the fragments'
    texts with their brackets matched and `depth` brackets are open before the section; what
    stands in brackets (an etymology: "cf. Skt. nar-") is no translation."""
    segs = [_Segment((0, 0))]
    prev = None     # the fragment before, blanks aside
    for i, f in enumerate(frags):
        seg = segs[-1]
        before = depth
        if f.kind == "text":
            for pos, ch in enumerate(texts[i]):
                if ch in "([":
                    depth += 1
                elif ch in ")]":
                    depth = max(depth - 1, 0)
                elif ch == "—" and depth == 0:
                    seg = _Segment((i, pos + 1))
                    segs.append(seg)
                elif not ch.isspace() and seg.opens is None:
                    seg.opens = "text"
            if _blank(f):
                continue
        else:
            depth = _brackets(texts[i], depth)
            if seg.opens is None:
                seg.opens = f.kind
            if (f.kind == "tns" or 'class="gram mood"' in f.html) and seg.clause is None and seg.weak is None:
                seg.tenses += 1
            if before == 0 and f.kind == "tr" and _is_gloss(f.html):
                p = frags[prev] if prev is not None else None
                cited = p is not None and p.kind != "text" and 'class="bibl"' in p.html
                if cited:
                    pass                    # italics straight after a citation are the title of a work
                elif p is not None and p.kind == "greek" and not _plain(p.html).rstrip().endswith(_CLAUSE_END):
                    if seg.weak is None:
                        seg.weak = prev     # the Greek phrase it translates
                else:
                    if seg.strong is None:
                        seg.strong = i
                    # a full stop does not count: it closes every abbreviation ("in signf. fly")
                    if seg.clause is None and (p is None or _plain(p.html).rstrip().endswith((":", ";", ",", "—"))):
                        seg.clause = i
            elif before == 0 and f.kind == "greek" and seg.weak is None and any(_is_gloss(t) for t in _TR.findall(f.html)):
                seg.weak = i                # a quotation and its translation, marked up as one
        prev = i
    return segs


# what may lead up to the "for" or "of" of a definition by reference: abbreviations and a few plain words
_REFERENCE = re.compile(r"(?:(?:[A-Za-z]+\.|\d|form|forms|later|late|rarer|rare|older|old|another|Verb|Noun|word),? )*(?:for|of|=)")
_FOREGOING = re.compile(r"(?:\b(?:for|of)|=)\s*(?:foreg|sq)\.")


def _reference_at(frags: list[_Frag], start: tuple[int, int], equations: bool = True) -> bool:
    """Whether a definition by reference to another word opens at `start`: "poet. for τέκνον",
    "collat. form of κτείνω", "pf. 2 of ὁράω", "Ep. for sq.", and with `equations` also
    "= σπίζα", "poet. Verb, = κτερεΐζω"; not a remark that happens to end so ("perhaps by error
    for ῥᾳδιέστερος"), nor a pointer among the forms ("ἀμφ-εληλεύθεν, v. ἀμφέρχομαι")."""
    i, off = start
    words = ""
    while i < len(frags) and len(words) <= 40:
        f = frags[i]
        if f.kind == "text":
            words += f.html[off:]
        elif f.kind in ("label", "tns", "voice"):
            words += _plain(f.html)
        else:
            break
        words = _WS.sub(" ", words).lstrip()
        i, off = i + 1, 0
    words = words.strip()
    if _FOREGOING.match(words) or re.match(_REFERENCE.pattern + r"\s*(?:foreg|sq)\.", words):
        return True
    if len(words) > 40 or i >= len(frags):
        return False
    f = frags[i]
    if f.kind == "xr" and _plain(f.html).lstrip().startswith("="):
        return equations and (not words or bool(re.fullmatch(r"(?:(?:[A-Za-z]+\.|Verb|Noun|form|word),? ?)*", words)))
    return (f.kind == "xr" or f.html.startswith('<span class="foreign">')) and bool(_REFERENCE.fullmatch(words))


def _first_reference(frags: list[_Frag], texts: list[str], depth: int = 0, equations: bool = True) -> tuple[int, int] | None:
    """Where the first definition by reference opens, at the start of a clause outside brackets."""
    for i, f in enumerate(frags):
        if f.kind != "text":
            depth = _brackets(texts[i], depth)
            continue
        for pos, ch in enumerate(texts[i]):
            if ch in "([":
                depth += 1
            elif ch in ")]":
                depth = max(depth - 1, 0)
            elif ch in ",;:—" and depth == 0:
                at = _skip_stops(frags, (i, pos + 1))
                if _reference_at(frags, at, equations):
                    return at
    return None


def _lead_in(frags: list[_Frag], t: int) -> tuple[int, int]:
    """Where the meaning that holds the translation at `t` starts, as (fragment, offset in its
    text): after the inflection, the closing bracket or the citation before it, when only a short
    description stands between ("τό, indecl., | the Hebrew Passover"); else at the translation."""
    length = 0
    j = t - 1
    cut = None
    while j >= 0 and cut is None:
        f = frags[j]
        if (f.kind == "infl" or (f.kind not in _LIGHT and f.kind != "tr" and not f.html.startswith('<span class="foreign">'))
                or (f.kind != "text" and re.search(r"[)\]]", _plain(f.html)))):
            cut = (j + 1, 0)
        elif f.kind == "text" and re.search(r"[)\]—]", f.html):
            off = max(f.html.rfind(c) for c in ")]—") + 1
            cut = (j, off) if length + _plain_len(f.html[off:]) <= _LEAD_IN else (t, 0)
        else:
            length += _plain_len(f.html)
            if length > _LEAD_IN:
                cut = (t, 0)
            j -= 1
    return _skip_stops(frags, cut or (0, 0), t)


def _skip_stops(frags: list[_Frag], at: tuple[int, int], limit: int | None = None) -> tuple[int, int]:
    """The place after the stops, spaces and inflection that follow `at`: they stay with what
    comes before a divider ("(…)), ἡ, | feast")."""
    i, off = at
    limit = len(frags) if limit is None else limit
    while i < limit:
        f = frags[i]
        if f.kind == "infl" and off == 0:
            i += 1
            continue
        if f.kind != "text":
            break
        rest = f.html[off:]
        off += len(rest) - len(rest.lstrip(" \t\r\n,;:"))
        if off < len(f.html):
            break
        i, off = i + 1, 0
    return i, off


def _clause_start(frags: list[_Frag], t: int) -> tuple[int, int]:
    """Where the clause that opens with the translation at `t` starts: after the stop before it."""
    if t > 0 and frags[t - 1].kind == "text":
        text = frags[t - 1].html
        off = max(text.rfind(c) for c in ":;,—") + 1
        if 0 < off and text[off:].strip():
            return t - 1, off
    return t, 0


def _cut(frags: list[_Frag], at: tuple[int, int]) -> tuple[list[_Frag], list[_Frag]]:
    i, off = at
    if off == 0:
        return frags[:i], frags[i:]
    text = frags[i].html
    return frags[:i] + [_Frag("text", text[:off])], [_Frag("text", text[off:])] + frags[i + 1:]


def _bracket_closes(frags: list[_Frag], texts: list[str], depth: int) -> tuple[int, int] | None:
    """The place after the bracket that closes the `depth` brackets open before the fragments."""
    for i, f in enumerate(frags):
        if f.kind == "text":
            for pos, ch in enumerate(texts[i]):
                if ch in "([":
                    depth += 1
                elif ch in ")]":
                    depth -= 1
                    if depth == 0:
                        return i, pos + 1
        else:
            depth = _brackets(texts[i], depth)
            if depth == 0:
                return i + 1, 0
    return None


# words that carry on a citation or a remark on the forms, and open no meaning
_CARRIES_ON = {"etc", "cf", "codd", "cod", "al", "ib", "ibid", "v", "vv", "sq", "s", "l", "dub", "prob", "perh", "and", "but",
               "also", "or", "in", "ap", "acc", "nom", "gen", "dat", "voc", "sg", "pl", "dual", "id", "fut", "aor", "pf", "impf",
               "later", "hence", "so", "the", "of", "these", "this", "written", "found", "freq", "rarely", "rare", "more", "not",
               "never", "always", "only", "for", "from", "poet", "fem", "masc", "neut", "adj", "adv", "comp", "sup", "dim",
               "patron", "med", "pass", "act", "ep", "ion", "dor", "att", "aeol", "it", "there", "on", "with", "as",
               # remarks that say there is no meaning to give, or where the word comes from
               "sine", "sens", "cj", "coined", "corrupt", "formed", "composed", "mostly", "opp", "expl"}


def _reads_as_meaning(frags: list[_Frag], at: tuple[int, int]) -> bool:
    """Whether the meaning opens at `at`, after an etymology in brackets: with a translation, a
    reference, or plain words ("(ἀφίημι) one who lets off a military engine"); not with a
    citation, a form, or a remark on the forms."""
    rest = _cut(frags, at)[1]
    seg = _segments(rest, _matched(rest), 0)[0]
    first = next((i for i, f in enumerate(rest) if not _blank(f)), None)
    if first is None or seg.tenses:
        return False
    f = rest[first]
    if f.kind == "xr" or _reference_at(rest, (first, 0)):
        return True
    if f.kind == "greek":
        return seg.weak == first
    if f.kind in ("text", "tr"):
        word = re.match(r"\s*([A-Za-z]+)", _plain(f.html))
        return word is not None and word.group(1).lower() not in _CARRIES_ON and (len(word.group(1)) > 1 or word.group(1) in "aI")
    return False


def _meaning_start(frags: list[_Frag], before: list[_Frag], in_forms: bool) -> tuple[list[_Frag], list[_Frag], str, str] | None:
    """Split the file's section "A" where the meanings of the headword start: what comes before,
    the meaning, the divider that was used, and a note (or "") when the split rests on a
    judgment. None when no meaning is found, or nothing shows that forms stand before it.

    `before` is the head: a bracket opened there may close in the section, and what follows such
    a bracket (an etymology) is the meaning when it reads as one. Else the lexicon's dashes
    divide: forms, ":—Med., …", ":—Pass., …", then the meaning, which is the first stretch after
    a dash that holds a translation of its own or opens with a reference ("= ἀρτύω", "poet. for
    τέκνον"), from its dash on. A Greek phrase with its translation counts only where no tense is
    named: among the forms it glosses another word ("were replaced by forms of εἶμι ibo").
    `in_forms` says that the section opens after a label of a form; then a translation that opens
    a clause before the first dash starts the meaning ("fut. -ιοῦμαι Luc. Alex. 1; reckon").
    """
    texts = _matched(list(before) + frags)
    depth = _brackets("".join(texts[:len(before)]))
    texts = texts[len(before):]
    if depth:
        closes = _bracket_closes(frags, texts, depth)
        if closes is not None:
            at = _skip_stops(frags, closes)
            if _reads_as_meaning(frags, at):
                return *_cut(frags, at), "bracket", ""
    forms = in_forms or depth > 0     # something shows that forms stand before the meaning
    segs = _segments(frags, texts, depth)
    for n, seg in enumerate(segs):
        if n == 0:
            if in_forms and seg.clause is not None:
                return *_cut(frags, _clause_start(frags, seg.clause)), "clause", ""
        elif seg.opens in ("voice", "tns") and seg.tenses:
            # the forms of a voice or tense: they hold the meaning only where it follows them
            # without a dash, as a clause of its own (":—Pass., aor. ἐκνίσθην E. Andr. 209: scratch, gash")
            if seg.clause is not None:
                return *_cut(frags, _clause_start(frags, seg.clause)), "clause", "the forms of a voice run on into the first translation without a dash"
        elif seg.strong is not None or seg.opens == "xr" or (seg.weak is not None and seg.tenses == 0) or _reference_at(frags, seg.start):
            if not forms:
                return None
            weak_only = seg.strong is None and seg.opens != "xr" and not _reference_at(frags, seg.start)
            return *_cut(frags, seg.start), "dash", "the first translation is that of a Greek phrase" if weak_only else ""
        forms = forms or seg.tenses > 0 or seg.opens in ("voice", "tns")
    return None


def _plain_words_after_dash(frags: list[_Frag], before: list[_Frag]) -> tuple[list[_Frag], list[_Frag]] | None:
    """Split a section that holds no translation and no reference at the first dash after which
    plain words open: there the meaning may stand unmarked ("…voc. Ἰοῖ A. Pr. 635, etc.:—Io,
    daughter of Inachus")."""
    texts = _matched(list(before) + frags)
    depth = _brackets("".join(texts[:len(before)]))
    for seg in _segments(frags, texts[len(before):], depth)[1:]:
        if seg.opens in ("text", "tr") and _reads_as_meaning(frags, _skip_stops(frags, seg.start)):
            return _cut(frags, seg.start)
    return None


def _plain_words_in_head(head: list[_Frag]) -> tuple[int, int] | None:
    """Where the head gives the meaning in plain, unmarked words, if it does: straight after the
    headword with its inflection, or after the etymology in brackets that follows them
    ("Ὑδατοσύδνη, ἡ, | name of a Nereïd", "μέλινος …, η, ον, (μελία) | ashen")."""
    last = max((i for i, f in enumerate(head) if f.kind == "infl" or f.html.startswith('<b class="orth">')), default=None)
    if last is None:
        return None
    at = _skip_stops(head, (last + 1, 0))
    texts = _matched(head)
    i, off = at
    if i < len(head) and head[i].kind == "text" and texts[i][off:off + 1] == "(":
        closes = _bracket_closes(head[i:], [texts[i][off + 1:]] + texts[i + 1:], 1)
        if closes is None:
            return None
        j, pos = closes
        at = _skip_stops(head, (i + j, pos + (off + 1 if j == 0 else 0)))
    return at if at[0] < len(head) and _reads_as_meaning(head, at) else None


def _meaning_in_head(head: list[_Frag], references: bool, following: list[_Frag] = ()) -> tuple[int, int] | None:
    """Where the head itself starts to give the meaning, if it does: at its first translation
    ("Κελτοί, οἱ, | Celts, Hdt. 2.33 …"), with the short description that leads up to it; and,
    with `references`, at a definition by reference ("κτίννυμι, | collat. form of κτείνω"), whose
    other word may be the first of `following`, the section ("Dim. of | πλινθίς 11").
    The file sets "A." past such a meaning when a derived word or a quoted form follows it."""
    texts = _matched(head)
    found = []
    for seg in _segments(head, texts, 0):
        if seg.strong is not None:
            found.append(_lead_in(head, seg.strong))
            break
    if references:
        first = next((f for f in following if not _blank(f)), None)
        other = [_Frag("greek", '<span class="foreign">' + _plain(first.html) + "</span>")] if first is not None and first.kind == "greek" else []
        at = _first_reference(head + other, texts + [""] * len(other))
        if at is not None and at[0] < len(head):
            found.append(at)
    return min(found) if found else None


_FORM_LABEL = re.compile(r"(?:\b(?:sg|pl|nom|gen|dat|acc|voc|inf|part|subj|opt|imper|ind|indic|aor|fut|pf|impf|pres|plpf)\.|\bdual|\d)\s*[-(]?\s*$")


def _in_forms(head: list[_Frag]) -> bool:
    """Whether the head breaks off among the forms: after a grammatical label."""
    last = next((f for f in reversed(head) if not (f.kind == "text" and not f.html.strip(" \t\r\n-("))), None)
    if last is None:
        return False
    if last.kind in ("tns", "voice", "label"):
        return True
    return last.kind == "text" and bool(_FORM_LABEL.search(_plain(last.html)))


_COMMA_QUOTE = re.compile(r'<span class="quote">\s*,\s*(\([^()<>]*\))?\s*(.*)</span>', re.S)


def _comma_first(head: list[_Frag], body: list[_Frag]) -> bool:
    """A quotation that opens the section with a comma (", (ὄρρος) pertaining to the rump"): the
    comma, and with it an etymology in brackets, go back to the head. Says whether it did so."""
    first = next((i for i, f in enumerate(body) if not _blank(f)), None)
    m = _COMMA_QUOTE.fullmatch(body[first].html) if first is not None else None
    if m is None:
        return False
    etymology, rest = m.groups()
    while head and _blank(head[-1]):
        del head[-1]
    if head and head[-1].kind == "text":
        head[-1] = _Frag("text", head[-1].html.rstrip())
    head.append(_Frag("text", ", "))
    if etymology:
        head.append(_Frag("other", f'<span class="foreign">{etymology}</span>'))
        head.append(_Frag("text", " "))
    if _plain(rest).strip() in ("ὁ", "ἡ", "τό", "οἱ", "αἱ", "τά"):
        # ", ἡ an adept in polite learning": the second gender of the headword, not a quotation
        head.append(_Frag("infl", f'<span class="gram">{_plain(rest).strip()}</span>'))
        head.append(_Frag("text", ", "))
        del body[first]
    elif rest.strip():
        body[first] = _Frag("greek", '<span class="quote">' + rest + "</span>")
    else:
        del body[first]
    return True


def _find_words(frags: list[_Frag], words: str) -> tuple[int, int] | None:
    """The place where `words` start in the fragments, spaces aside: in a run of text, or at the
    start of a child."""
    target = _WS.sub("", html.escape(words, quote=False))
    chars: list[str] = []
    where: list[tuple[int, int]] = []
    for i, f in enumerate(frags):
        for pos, ch in enumerate(f.html if f.kind == "text" else _plain(f.html)):
            if not ch.isspace():
                chars.append(ch)
                where.append((i, pos))
    k = "".join(chars).find(target)
    if k < 0 or not target:
        return None
    i, pos = where[k]
    if frags[i].kind == "text":
        return i, pos
    return (i, 0) if k == 0 or where[k - 1][0] != i else None


def _repair_section_a(head: list[_Frag], senses: list, over: dict, decision: str | None = None) -> tuple[str, str] | None:
    """Put the file's "A." where the meanings start: take back into `head` the forms that the
    file put under it, or take into the section the meaning that the file left in the head.

    `over` says how the senses concerned are rendered instead: None to leave one out, else its
    labels (None for its own) and its content (None for its own). `decision` is the editor's own
    for the entry (lsj-forms.tsv): the first words of the meaning, "-" for no "A." at all, "="
    to leave the entry as the file has it. Returns the rule that was used, and a note (or "")
    when the repair rests on a judgment and wants looking at; None when nothing was done.
    """
    def html_of(frags: list[_Frag]) -> str:
        return "".join(f.html for f in frags).lstrip()

    s0 = senses[0]
    body = _split_italics(_frags(s0.text, list(s0)))
    first = next((f for f in body if not _blank(f)), None)
    if first is None or decision == "=":
        return None
    if decision == "-":
        head.extend(body)
        over[s0] = None
        return "decided", ""
    if decision:
        at = _find_words(head + body, decision)
        if at is None:
            raise ValueError(f"lsj-forms.tsv: the words {decision!r} do not stand before the second section of the entry")
        keep, meaning = _cut(head + body, at)
        head[:] = keep
        over[s0] = (None, html_of(meaning))
        return "decided", ""
    if any(s.get("n") == "A" and s.get("level") == "1" for s in senses[1:]):
        # the lexicon prints an "A." of its own further down: the file's is no section at all
        head.extend(body)
        over[s0] = None
        return "printed A.", ""
    # the file's "A." opens at a quoted form, inside a citation ("Hsch. | s.v. κιμβεία") or inside
    # a remark on the forms ("formed | like ἵστημι"): placed by rule, not at a meaning
    opening = _plain(first.html) if first.kind == "xr" else ""
    aside = re.match(r"\s*s\.\s?v\.\s", opening) is not None
    if re.match(r"\s*like\s", opening):
        # "like ῥάζω, growl, snarl" defines; "apocop. acc. αἰῶ, like Ποσειδῶ, restored by …:—lifetime" is a remark
        before_dash = _segments(body, _matched(body), 0)[0]
        aside = before_dash.strong is None or before_dash.tenses > 0
    quoted = first.kind == "greek" or aside
    done = None
    if _comma_first(head, body):
        over[s0] = (None, html_of(body))
        done = "comma", ""
    at = _meaning_in_head(head, references=quoted, following=body)
    if at is not None:
        keep, meaning = _cut(head, at)
        head[:] = keep
        over[s0] = (None, html_of(meaning + body))
        return "head", ""
    open_ = _brackets("".join(_matched(head + body)[:len(head)]))     # brackets open where "A." stands
    if not (quoted or (first.kind == "xr" and open_)):
        return done     # "A." opens at a translation, or the entry is defined by a reference ("= κάππαρις")
    in_forms = _in_forms(head)
    found = _meaning_start(body, head, in_forms)
    if found is not None:
        forms, meaning, divider, note = found
        if not any(not _blank(f) for f in forms):
            return done     # the meaning opens the section: "A." stands where it should
        head.extend(forms)
        over[s0] = (None, html_of(meaning))
        return divider, note
    if not (in_forms or open_ or aside or any(f.kind == "tns" for f in body)):
        return done     # no forms in sight: quotations for a meaning that the head gives in plain words
    plain = _plain_words_after_dash(body, head)
    if plain is not None:
        forms, meaning = plain
        head.extend(forms)
        over[s0] = (None, html_of(meaning))
        return "plain words", "the meaning is not marked as a translation: taken to start at the plain words after a dash"
    at = _plain_words_in_head(head)
    if at is not None:
        keep, meaning = _cut(head, at)
        head[:] = keep
        over[s0] = (None, html_of(meaning + body))
        return "plain words", "the meaning is not marked as a translation: taken to start at the plain words after the headword"
    # forms, and no meaning among them
    head.extend(body)
    over[s0] = None
    s1 = senses[1] if len(senses) > 1 else None
    if s1 is None:
        return "no A.", "the entry holds no translation: all of it taken into the head, A. left out"
    if (s1.get("n"), s1.get("level")) in (("I", "2"), ("1", "3"), ("a", "4")):
        # a numbered series opens: all of the file's "A." comes before the first meaning
        nxt = _frags(s1.text, list(s1))
        segs = _segments(nxt, _matched(nxt), 0)
        meaning = any(s.strong is not None or s.weak is not None or s.opens == "xr" for s in segs)
        if not meaning and any(f.kind == "greek" for f in nxt):
            return "no A.", "numbered sections of forms follow, so A. has no place and is left out"
        over[s1] = (["A", s1.get("n")], None)
        return "next section", ""
    return "no A.", "the unnumbered first section holds no translation: taken into the head, A. left out"


def _lines(frags: list[_Frag]) -> str:
    """The head paragraph with the lexicon's own dividers shown as lines.

    A new line after a colon and before a dash, outside brackets; an empty line before a dash that
    opens a new voice. A verb whose first tense follows the headword at once gets the headword on
    a line of its own, when there are other lines.
    """
    tokens: list[tuple[str, object]] = []
    for f, text in zip(frags, _matched(frags)):
        if f.kind == "text":
            # a bracket without a partner counts as none: blanked in `text`, kept in the output
            tokens.extend(("ch", c) if c == m else ("lone", c) for c, m in zip(f.html, text))
        else:
            tokens.append(("el", (f, text)))

    def following(k: int) -> int | None:
        while k < len(tokens):
            if not (tokens[k][0] == "ch" and tokens[k][1].isspace()):
                return k
            k += 1
        return None

    def voice_at(k: int) -> bool:
        kind, value = tokens[k]
        if kind == "el":
            return value[0].kind == "voice"
        word = "".join(v for t, v in tokens[k:k + 5] if t == "ch")
        return word.startswith(("Med.", "Pass.", "Act."))

    # "λαμβάνω, fut. λήψομαι": the place after the comma
    solid = [i for i, f in enumerate(frags) if not _blank(f)][:3]
    headword_comma = (len(solid) == 3 and frags[solid[0]].html.startswith('<b class="orth">')
                      and frags[solid[1]].kind == "text" and frags[solid[1]].html.strip() == ","
                      and frags[solid[2]].kind == "tns")
    headword_break = None
    out: list[str] = []
    depth = 0
    k = 0
    while k < len(tokens):
        kind, value = tokens[k]
        k += 1
        if kind == "el":
            out.append(value[0].html)
            depth = _brackets(value[1], depth)
            continue
        if kind == "lone":
            out.append(value)
            continue
        if value in "([":
            depth += 1
        elif value in ")]":
            depth = max(depth - 1, 0)
        elif value == "," and headword_comma and headword_break is None:
            out.append(value)
            headword_break = len(out)
            continue
        elif depth == 0 and value in ":—":
            nxt = following(k)
            if nxt is not None and any(o.strip() for o in out):
                if value == "—":
                    out.append("<br><br>—" if voice_at(nxt) else "<br>—")
                    continue
                if tokens[nxt] != ("ch", "—"):
                    out.append(":<br>")
                    k = nxt
                    continue
        out.append(value)
    if headword_break is not None and any("<br>" in o for o in out):
        out.insert(headword_break, "<br>")
    return "".join(out)


def render_lsj_entry(el, decision: str | None = None) -> tuple[str, tuple[str, str] | None]:
    """An LSJ entry as HTML, and how its "A." was put right, if it was: the rule used, and a note
    (or "") when that rests on a judgment. `decision` is the editor's own for the entry."""
    kids = list(el)
    first = next((i for i, k in enumerate(kids) if k.tag == "sense"), len(kids))
    head = _frags(el.text, kids[:first])
    senses = [k for k in kids[first:] if k.tag == "sense"]
    over: dict = {}
    repair = None
    if senses and senses[0].get("n") == "A" and senses[0].get("level") == "1":
        repair = _repair_section_a(head, senses, over, decision)
    elif decision:
        raise ValueError("lsj-forms.tsv: the entry has no section A to decide on")
    # "A." is the file's own addition where the lexicon has no "B.": print has no letter there
    lettered = any(k.get("level") == "1" and (k.get("n") or "0")[0] not in "A0" for k in senses)

    def labels_of(k, labels: list[str] | None) -> list[str] | None:
        if lettered:
            return labels
        if labels is None:
            return [] if k.get("level") == "1" and k.get("n") == "A" else None
        return [label for label in labels if label != "A"]

    rest: list[str] = []
    for k in kids[first:]:
        if k in over:
            if over[k] is not None:
                _sense(k, False, rest, labels=labels_of(k, over[k][0]), content=over[k][1])
        elif isinstance(k.tag, str) and k.tag == "sense":
            _sense(k, False, rest, labels=labels_of(k, None))
        elif isinstance(k.tag, str):
            _render(k, False, rest)
        rest.append(_text(k.tail, False))
    s = _WS.sub(" ", _lines(head)).strip()
    s = (f'<p class="head">{s}</p>' if s else "") + _WS.sub(" ", "".join(rest))
    s = _BR_SPACE.sub(r"<br>\1", re.sub(r" ?<br> ?", "<br>", s))
    s = s.replace(" </p>", "</p>").replace("<p class=\"sense\"> ", "<p class=\"sense\">")
    return _metre(s).strip(), repair


def _split_key(key: str) -> tuple[str, int]:
    m = re.match(r"^(.*?)(\d+)$", key)
    if m:
        return m.group(1), int(m.group(2))
    return key, 0


def parse_lexicon(path: Path, lexicon: str, p4: bool, repairs: list[tuple[str, str, str]] | None = None,
                  decisions: dict[str, str] | None = None) -> list[Entry]:
    """The entries of one file. For LSJ, `repairs` collects (key, rule, note) for the entries
    whose "A." was put right, and `decisions` are the editor's own, by key (read_lsj_decisions)."""
    if p4:
        root = load_p4(path)
    else:
        parser = etree.XMLParser(load_dtd=False, resolve_entities=False, huge_tree=True)
        root = etree.parse(str(path), parser).getroot()
    entries: list[Entry] = []
    for el in root.iter("entryFree", "entry"):
        key = el.get("key") or ""
        if not key:
            continue
        base, homograph = _split_key(key)
        headword = greek.betacode_to_unicode(base)
        if lexicon == "lsj":
            try:
                entry_html, repair = render_lsj_entry(el, (decisions or {}).get(key))
            except ValueError as e:
                raise ValueError(f"{key}: {e}") from None
            if repair and repairs is not None:
                repairs.append((key, *repair))
        else:
            entry_html = render_entry(el)
        entries.append(
            Entry(
                lexicon=lexicon,
                key=key,
                headword=headword,
                homograph=homograph,
                html=entry_html,
                sort_key=greek.strip_diacritics(headword),
            )
        )
    return entries


LSJ_DECISIONS = "lsj-forms.tsv"


def read_lsj_decisions(path: Path) -> dict[str, str]:
    """The editor's decisions on where the meanings of an LSJ entry start, for the entries where
    the rules go wrong: tab-separated lines of key, decision, comment. The decision is the first
    words of the meaning ("A." is set before them), "-" for no "A." at all, or "=" to leave the
    entry as the file has it. Lines starting with # are comments."""
    decisions = {}
    if path.exists():
        for line in path.read_text(encoding="utf-8").splitlines():
            if line.strip() and not line.startswith("#"):
                key, decision = line.split("\t")[:2]
                decisions[key] = decision.strip()
    return decisions


def parse_lsj(sources: Path, repairs: list[tuple[str, str, str]] | None = None) -> list[Entry]:
    decisions = read_lsj_decisions(sources.parent / LSJ_DECISIONS)
    entries: list[Entry] = []
    for path in sorted((sources / "lsj").glob("grc.lsj.perseus-eng*.xml"), key=lambda p: int(re.search(r"eng(\d+)", p.name).group(1))):
        entries.extend(parse_lexicon(path, "lsj", p4=False, repairs=repairs, decisions=decisions))
    unknown = set(decisions) - {e.key for e in entries}
    if unknown:
        raise ValueError(f"{LSJ_DECISIONS}: no such entries: {sorted(unknown)}")
    return entries


def parse_middle_liddell(sources: Path) -> list[Entry]:
    return parse_lexicon(sources / "middle-liddell.xml", "ml", p4=True)


# ---------------------------------------------------------------- Abbott-Smith

ABBOTT_SMITH_NS = "{http://www.crosswire.org/2013/TEIOSIS/namespace}"
# OCR left Latin letters inside some Greek words (πoρνεύω): in a word that mixes the scripts,
# the Latin look-alikes are Greek
_LOOKALIKE = str.maketrans({"o": "ο", "n": "ν", "a": "α", "i": "ι", "k": "κ", "t": "τ", "u": "υ", "v": "ν", "x": "χ", "e": "ε", "y": "γ"})
_GREEK = re.compile(r"[Ͱ-Ͽἀ-῿]")
_LATIN = re.compile(r"[A-Za-z]")


def _fix_mixed(text: str) -> str:
    def fix(m):
        w = m.group(0)
        return w.translate(_LOOKALIKE) if _GREEK.search(w) and _LATIN.search(w) else w
    return re.sub(r"\S+", fix, text)


def _as_text(s: str | None) -> str:
    return html.escape(_fix_mixed(s), quote=False) if s else ""


def _as_render(el, out: list[str]) -> None:
    tag = etree.QName(el).localname
    if tag in ("pb", "lb"):
        return
    if tag == "note" and el.get("type") == "occurrencesNT":
        return  # shown at the end of the entry
    open_, close = "", ""
    if tag == "orth":
        open_, close = '<b class="orth">', "</b>"
    elif tag == "gloss":
        open_, close = '<i class="tr">', "</i>"
    elif tag == "ref" and el.get("osisRef"):
        open_, close = '<span class="bibl">', "</span>"  # a passage; a ref to another entry is plain Greek
    elif tag in ("etym", "seg"):
        open_, close = '<span class="etym">', "</span>"
    elif tag in ("emph", "hi"):
        open_, close = "<i>", "</i>"
    elif tag in ("gramGrp", "pos"):
        open_, close = '<span class="gram">', "</span>"
    elif tag == "sense":
        n = (el.get("n") or "").strip()
        out.append('<p class="sense">' + (f"<b>{html.escape(n)}</b> " if n else ""))
        _as_children(el, out)
        out.append("</p>")
        return
    elif tag == "re":
        out.append('<p class="re">')
        _as_children(el, out)
        out.append("</p>")
        return
    out.append(open_)
    _as_children(el, out)
    out.append(close)


def _as_children(el, out: list[str]) -> None:
    out.append(_as_text(el.text))
    for child in el:
        if isinstance(child.tag, str):
            _as_render(child, out)
        out.append(_as_text(child.tail))


def render_abbott_smith(entry) -> str:
    """An entry as HTML: the head (form and Septuagint note) as a paragraph, each sense a
    paragraph (nested senses flattened in order), the synonyms last, then the count of NT
    occurrences the edition prints in the margin."""
    out: list[str] = []
    head: list[str] = []
    body: list[str] = []
    for child in entry:
        if not isinstance(child.tag, str):
            continue
        tag = etree.QName(child).localname
        target = body if tag in ("sense", "re") else head
        _as_render(child, target)
        target.append(_as_text(child.tail))
    s_head = _WS.sub(" ", "".join(head)).strip()
    if s_head:
        out.append(f'<p class="head">{s_head}</p>')
    s_body = _WS.sub(" ", "".join(body)).strip()
    # a sense holding senses: its own paragraph is empty but for the inner ones
    s_body = re.sub(r'<p class="sense">\s*(<p class="sense">)', r"\1", s_body)
    s_body = re.sub(r"</p>\s*</p>", "</p>", s_body)
    out.append(s_body)
    occ = entry.find(f"{ABBOTT_SMITH_NS}note[@type='occurrencesNT']")
    if occ is not None and (occ.text or "").strip().isdigit():
        n = int(occ.text.strip())
        out.append(f'<p class="note"><span class="gram">{n} occurrence{"s" if n != 1 else ""} in the New Testament</span></p>')
    s = "".join(out)
    s = s.replace(" </p>", "</p>").replace("<p class=\"sense\"> ", "<p class=\"sense\">")
    return s.strip()


def parse_abbott_smith(sources: Path) -> list[Entry]:
    """G. Abbott-Smith, A Manual Greek Lexicon of the New Testament (1922), from the TEI of
    github.com/translatable-exegetical-tools/Abbott-Smith. The key is "headword|G<Strong>"."""
    parser = etree.XMLParser(load_dtd=False, resolve_entities=False, huge_tree=True)
    root = etree.parse(str(sources / "abbott-smith" / "abbott-smith.tei.xml"), parser).getroot()
    entries: list[Entry] = []
    seen: collections.Counter = collections.Counter()
    for el in root.iter(f"{ABBOTT_SMITH_NS}entry"):
        n = el.get("n") or ""
        headword = n.partition("|")[0].strip()
        if not headword:
            orth = el.find(f".//{ABBOTT_SMITH_NS}orth")
            headword = "".join(orth.itertext()) if orth is not None else ""
        headword = greek.nfc(_fix_mixed(re.sub(r"[-\s,.*†]", "", headword)))
        if not headword or not _GREEK.search(headword):
            continue
        seen[headword] += 1
        entries.append(Entry(
            lexicon="abbott-smith",
            key=n or headword,
            headword=headword,
            homograph=seen[headword] if seen[headword] > 1 else 0,
            html=render_abbott_smith(el),
            sort_key=greek.strip_diacritics(headword),
        ))
    # a headword printed more than once is numbered from the first
    firsts = {e.headword for e in entries if e.homograph == 2}
    for e in entries:
        if e.headword in firsts and e.homograph == 0:
            e.homograph = 1
    return entries


def strong_numbers(entry: Entry) -> list[int]:
    return [int(g) for g in re.findall(r"G(\d+)", entry.key)]
