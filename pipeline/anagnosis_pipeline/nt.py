"""The Greek New Testament: the SBL edition's text and apparatus, MACULA's lemmas and morphology,
Dodson's lexicon for the words the dictionaries lack, and the Berean Standard Bible.

Sources (pipeline/sources/nt/, see fetch_nt):
    sblgnt/   github.com/LogosBible/SBLGNT: data/sblgnt/xml (text) and data/sblgntapp/xml (apparatus)
    macula/   github.com/Clear-Bible/macula-greek: SBLGNT/tsv/macula-greek-SBLGNT.tsv, one row per word
    dodson/   github.com/biblicalhumanities/Dodson-Greek-Lexicon: dodson.csv (Strong's number, gloss)
    bsb.txt   bereanbible.com/bsb.txt: the Berean Standard Bible, one verse per line

A line of grc.txt is a verse, numbered book.chapter.verse (1.5.3). A paragraph of the SBLGNT
that begins inside a verse makes the rest of the verse a second line with a letter (1.5.3b).
The SBLGNT marks the places its apparatus discusses with signs (⸀ ⸂ ⸃ ...); they are left out
of the text and of the apparatus, whose notes are keyed to the verse.
"""
from __future__ import annotations

import collections
import csv
import json
import re
import subprocess
from pathlib import Path

from . import greek

# (SBLGNT file, English name, BSB name): the canonical order gives the book numbers 1-27.
BOOKS = [
    ("Matt", "Matthew"), ("Mark", "Mark"), ("Luke", "Luke"), ("John", "John"), ("Acts", "Acts"),
    ("Rom", "Romans"), ("1Cor", "1 Corinthians"), ("2Cor", "2 Corinthians"), ("Gal", "Galatians"),
    ("Eph", "Ephesians"), ("Phil", "Philippians"), ("Col", "Colossians"), ("1Thess", "1 Thessalonians"),
    ("2Thess", "2 Thessalonians"), ("1Tim", "1 Timothy"), ("2Tim", "2 Timothy"), ("Titus", "Titus"),
    ("Phlm", "Philemon"), ("Heb", "Hebrews"), ("Jas", "James"), ("1Pet", "1 Peter"), ("2Pet", "2 Peter"),
    ("1John", "1 John"), ("2John", "2 John"), ("3John", "3 John"), ("Jude", "Jude"), ("Rev", "Revelation"),
]
ENGLISH_NUMBER = {name: i + 1 for i, (_f, name) in enumerate(BOOKS)}

# The signs with which the SBLGNT marks a variation unit; a digit after one counts occurrences.
CRITICAL_SIGNS = re.compile(r"[⸀⸁⸂⸃⸄⸅]\d?")

GREEK_META = {
    "title": "Ἡ Καινὴ Διαθήκη",
    "author": "",
    "lang": "grc",
    "source": "The Greek New Testament: SBL Edition (github.com/LogosBible/SBLGNT, version 1.2, 2023); lemmas and morphology from MACULA Greek (github.com/Clear-Bible/macula-greek)",
    "edition": "The Greek New Testament: SBL Edition, ed. Michael W. Holmes, Society of Biblical Literature and Logos Bible Software 2010",
    "license": "CC BY 4.0: text and apparatus © 2010 Society of Biblical Literature and Logos Bible Software; MACULA Greek Linguistic Datasets © 2022-2024 Biblica, Inc.",
    "layout": "prose",
}
APPARATUS_META = {
    "title": "Apparatus (SBL Greek New Testament)",
    "author": "Michael W. Holmes",
    "lang": "grc",
    "source": "The Greek New Testament: SBL Edition, apparatus (github.com/LogosBible/SBLGNT, data/sblgntapp)",
    "license": "CC BY 4.0, © 2010 Society of Biblical Literature and Logos Bible Software",
}
BSB_META = {
    "title": "Berean Standard Bible",
    "translator": "Berean Bible Translation Committee",
    "lang": "en",
    "source": "Berean Standard Bible, bereanbible.com/bsb.txt",
    "edition": "The Holy Bible, Berean Standard Bible (2023)",
    "license": "Public domain (dedicated to the public domain on 30 April 2023)",
}
GLOSSARY_META = {
    "title": "Glossary of names and words of the New Testament (Dodson)",
    "lang": "eng",
    "source": "John Jeffrey Dodson, A Lexicon of the Greek New Testament, as published by biblicalhumanities.org (github.com/biblicalhumanities/Dodson-Greek-Lexicon)",
    "license": "CC0 1.0 (public domain)",
}

# MACULA's word classes and features as the nine letters of a Perseus tag
POS = {"noun": "n", "verb": "v", "det": "l", "conj": "c", "pron": "p", "prep": "r", "adj": "a",
       "adv": "d", "ptcl": "g", "num": "m", "intj": "i"}
PERSON = {"first": "1", "second": "2", "third": "3"}
NUMBER = {"singular": "s", "plural": "p"}
TENSE = {"present": "p", "imperfect": "i", "future": "f", "aorist": "a", "perfect": "r", "pluperfect": "l"}
MOOD = {"indicative": "i", "subjunctive": "s", "optative": "o", "imperative": "m", "infinitive": "n", "participle": "p"}
VOICE = {"active": "a", "middle": "m", "passive": "p"}
GENDER = {"masculine": "m", "feminine": "f", "neuter": "n"}
CASE = {"nominative": "n", "genitive": "g", "dative": "d", "accusative": "a", "vocative": "v"}
DEGREE = {"comparative": "c", "superlative": "s"}

# Lemmas Dodson lacks (forms MACULA lemmatises apart from their headword), with short glosses.
HAND_GLOSSES = {
    "ἱνατί": "why? for what reason?",
    "περισσότερον": "more, all the more, the more abundantly",
    "ἐκπερισσῶς": "beyond measure, vehemently",
    "καταβαρύνομαι": "to be weighed down, be heavy",
    "Ἀρνί": "Arni, an ancestor of Jesus in Luke's genealogy",
    "Ζηλωτής": "the Zealot, surname of Simon the apostle",
    "βασίλειον": "palace, royal residence; (as adj.) royal",
    "Σαλείμ": "Salim, a place near Aenon",
    "ἀκριβέστερον": "more accurately, more exactly",
    "Καλός": "Fair (Καλοὶ Λιμένες, Fair Havens, a harbour of Crete)",
    "πώς": "somehow, in some way, perhaps",
    "μήτιγε": "how much more (then), not to speak of",
    "περισσοτέρως": "more abundantly, all the more, especially",
    "ὑπερεκπερισσοῦ": "beyond all measure, most earnestly",
    "ἄγε": "come now! (interjection)",
    "μέγιστος": "greatest, very great",
    "ἱππικόν": "cavalry, horsemen",
    "δισμυριάς": "twenty thousand",
    "ἄμωμον": "amomum, an Indian spice plant",
    "φαρμακός": "sorcerer, magician",
}


def fetch_nt(sources: Path) -> None:
    """Clone or download the sources into pipeline/sources/nt/ (skipping what is there)."""
    nt = sources / "nt"
    nt.mkdir(parents=True, exist_ok=True)

    def git(url: str, dest: str, sparse: list[str] | None = None) -> None:
        if (nt / dest).exists():
            return
        if sparse:
            subprocess.run(["git", "clone", "-q", "--depth", "1", "--filter=blob:none", "--sparse", url, dest], cwd=nt, check=True)
            subprocess.run(["git", "sparse-checkout", "set", "--no-cone", *sparse], cwd=nt / dest, check=True)
        else:
            subprocess.run(["git", "clone", "-q", "--depth", "1", url, dest], cwd=nt, check=True)

    git("https://github.com/LogosBible/SBLGNT.git", "sblgnt")
    git("https://github.com/Clear-Bible/macula-greek.git", "macula", ["/SBLGNT/tsv/", "/LICENSE.md", "/README.md"])
    git("https://github.com/biblicalhumanities/Dodson-Greek-Lexicon.git", "dodson")
    if not (nt / "bsb.txt").exists():
        subprocess.run(["curl", "-sSL", "-o", str(nt / "bsb.txt"), "https://bereanbible.com/bsb.txt"], check=True)


# ---------------------------------------------------------------- the text

def _clean(s: str) -> str:
    return CRITICAL_SIGNS.sub("", s or "")


def read_book(path: Path, book: int) -> tuple[str, list[dict]]:
    """A book of the SBLGNT: its title and its lines in order. A line is a dict with n, text,
    para (a paragraph begins with it) and words (the forms of its <w> elements)."""
    from lxml import etree

    root = etree.parse(str(path)).getroot()
    title = " ".join((root.findtext("title") or "").split())
    lines: list[dict] = []
    current: dict | None = None
    parts: list[str] = []
    split_count: dict[str, int] = collections.Counter()

    def close() -> None:
        if current is not None:
            current["text"] = re.sub(r"\s+", " ", "".join(parts)).strip()
            lines.append(current)

    for p in root.iter("p"):
        first = True
        for el in p:
            if not isinstance(el.tag, str):
                continue
            if el.tag == "verse-number":
                close()
                chapter, verse = re.search(r"(\d+):(\d+)$", el.get("id")).groups()
                current = {"n": f"{book}.{int(chapter)}.{int(verse)}", "para": first, "words": []}
                parts = []
            else:
                if first and current is not None:
                    # a paragraph begins inside the verse: the rest of it is a line of its own
                    close()
                    base = re.sub(r"[a-z]$", "", current["n"])
                    split_count[base] += 1
                    current = {"n": base + "bcdefgh"[split_count[base] - 1], "para": True, "words": []}
                    parts = []
                if current is None:
                    raise SystemExit(f"{path}: text before the first verse")
                if el.tag == "w":
                    form = greek.nfc(el.text or "")
                    current["words"].append(form)
                    parts.append(form)
                elif el.tag == "prefix":
                    parts.append(_clean(el.text))
                elif el.tag == "suffix":
                    # an empty suffix is the space between two words
                    parts.append(_clean(el.text) or " ")
            first = False
    close()
    return title, lines


def read_text(sources: Path) -> list[tuple[str, str, list[dict]]]:
    """The 27 books: (English name, Greek title, lines)."""
    xml = sources / "nt" / "sblgnt" / "data" / "sblgnt" / "xml"
    out = []
    for i, (stem, name) in enumerate(BOOKS):
        title, lines = read_book(xml / f"{stem}.xml", i + 1)
        out.append((name, title, lines))
    return out


# ---------------------------------------------------------------- MACULA

def read_macula(sources: Path) -> list[dict]:
    path = sources / "nt" / "macula" / "SBLGNT" / "tsv" / "macula-greek-SBLGNT.tsv"
    with path.open(encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f, delimiter="\t", quoting=csv.QUOTE_NONE))


def postag(r: dict) -> str:
    """MACULA's analysis of a word as a Perseus tag: pos, person, number, tense, mood, voice, gender, case, degree."""
    return "".join([
        POS.get(r["class"], "x"), PERSON.get(r["person"], "-"), NUMBER.get(r["number"], "-"),
        TENSE.get(r["tense"], "-"), MOOD.get(r["mood"], "-"), VOICE.get(r["voice"], "-"),
        GENDER.get(r["gender"], "-"), CASE.get(r["case"], "-"), DEGREE.get(r["degree"], "-"),
    ])


# ---------------------------------------------------------------- the dictionaries

def _alias_candidates(lemma: str) -> list[str]:
    """Headwords under which LSJ may list a New Testament lemma: οὕτω(ς) as οὕτως or οὕτω, a
    middle deponent under its active (ἀποκρίνομαι, ἀποκρίνω), γινώσκω as γιγνώσκω, ἀνοίγω as
    ἀνοίγνυμι, and the like."""
    out: list[str] = []
    m = re.fullmatch(r"(.*)\((.+)\)", lemma)
    if m:
        out += [m.group(1) + m.group(2), m.group(1)]
    for b in [lemma] + list(out):
        if "γιν" in b:
            out.append(b.replace("γιν", "γιγν"))
        for end, repl in (("ομαι", "ω"), ("έομαι", "έω"), ("άομαι", "άω"), ("όομαι", "όω"), ("αμαι", "ημι"),
                          ("ίζω", "ίζομαι"), ("ω", "ομαι"), ("ύω", "υμι"), ("γω", "γνυμι")):
            if b.endswith(end):
                out.append(b[: -len(end)] + repl)
    for b in list(out):
        if "γιν" in b:
            out.append(b.replace("γιν", "γιγν"))
    return out


def resolve_lemmas(lemmas: list[str], headwords: set[str]) -> tuple[dict[str, str], list[str]]:
    """(aliases: lemma -> headword, lemmas still not found). A lemma found under an alias
    candidate, or under exactly one headword that differs from it only in accents, breathing or
    iota subscript (never in capitals: Ἠλίας is not ἡλιάς), gets an alias."""
    keys = {greek.lemma_key(h): h for h in headwords}
    loose: dict[str, set[str]] = collections.defaultdict(set)
    for h in headwords:
        loose[greek.strip_diacritics(h)].add(h)
    aliases: dict[str, str] = {}
    missing: list[str] = []
    for lemma in lemmas:
        if greek.lemma_key(lemma) in keys:
            continue
        hit = next((keys[greek.lemma_key(c)] for c in _alias_candidates(lemma) if greek.lemma_key(c) in keys), None)
        if hit is None:
            same_case = [h for h in loose.get(greek.strip_diacritics(lemma), ()) if h[:1].isupper() == lemma[:1].isupper()]
            if len(same_case) == 1:
                hit = same_case[0]
        if hit is None:
            missing.append(lemma)
        else:
            aliases[lemma] = hit
    return aliases, missing


def read_dodson(sources: Path) -> dict[int, dict]:
    """Dodson's entries by Strong's number: headword (with its article or endings), brief and full gloss."""
    out: dict[int, dict] = {}
    path = sources / "nt" / "dodson" / "dodson.csv"
    with path.open(encoding="utf-8", newline="") as f:
        for r in csv.reader(f, delimiter="\t"):
            if len(r) >= 5 and r[0].isdigit():
                out[int(r[0])] = {"orth": greek.betacode_to_unicode(r[2]), "brief": r[3].strip(), "full": r[4].strip()}
    return out


# ---------------------------------------------------------------- the apparatus

SIGLA = re.compile(r"\s(?=(?:WH|Treg|NIV|RP|NA2[78]|Holmes|TR|SBL|Greeven)[A-Za-z]*\b)")
NOTE_REF = re.compile(r"^\s*(?:•\s*|(?:(\d+):)?(\d+)(?:[–-](?:(\d+):)?(\d+))?\s+)")


def read_apparatus(sources: Path) -> list[tuple[str, list[str]]]:
    """The apparatus as (heading, notes): a heading is a verse (1.1.5) or a range (1.1.7-8)."""
    from lxml import etree

    xml = sources / "nt" / "sblgnt" / "data" / "sblgntapp" / "xml"
    out: list[tuple[str, list[str]]] = []
    for i, (stem, _name) in enumerate(BOOKS):
        book = i + 1
        root = etree.parse(str(xml / f"{stem}.xml")).getroot()
        verse = None
        for el in root:
            if el.tag == "verse":
                chapter, v = re.search(r"(\d+):(\d+)$", el.text.strip()).groups()
                verse = (int(chapter), int(v))
            elif el.tag == "note" and verse is not None:
                text = " ".join((el.text or "").split())
                m = NOTE_REF.match(text)
                heading = f"{book}.{verse[0]}.{verse[1]}"
                if m and m.group(4):
                    to_chapter = int(m.group(3)) if m.group(3) else verse[0]
                    to = m.group(4) if to_chapter == verse[0] else f"{to_chapter}.{m.group(4)}"
                    heading += f"-{to}"
                body = _clean(text[m.end():] if m else text).strip()
                parts = SIGLA.split(body, maxsplit=1)
                if len(parts) == 2 and parts[0].strip() and "]" not in parts[0]:
                    body = f"**{parts[0].strip()}** {parts[1].strip()}"
                if out and out[-1][0] == heading:
                    out[-1][1].append(body)
                else:
                    out.append((heading, [body]))
    return out


SIGLA_DOC = """# title: Editions cited in the apparatus
# source: The Greek New Testament: SBL Edition, apparatus
# license: CC BY-SA 4.0 (this explanation); the apparatus is CC BY 4.0, © 2010 Society of Biblical Literature and Logos Bible Software

The SBL Greek New Testament was edited by Michael W. Holmes. Its apparatus does not report manuscripts: it records where the SBL text differs from four other editions of the Greek New Testament, and from a few more in particular places. Each note gives the SBL reading first, with the editions that agree with it, then a square bracket, then the other readings with their editions.

**WH** = B. F. Westcott and F. J. A. Hort, *The New Testament in the Original Greek* (1881). **WHmarg** is a reading in their margin, **WHapp** one in their appendix.

**Treg** = S. P. Tregelles, *The Greek New Testament* (1857–1879). **Tregmarg** is a reading in his margin.

**NIV** = the Greek text behind the New International Version, as published by R. J. Goodrich and A. L. Lukaszewski, *A Reader's Greek New Testament* (2003).

**RP** = M. A. Robinson and W. G. Pierpont, *The New Testament in the Original Greek: Byzantine Textform* (2005).

**NA28**, **NA27** = Nestle–Aland, *Novum Testamentum Graece*, 28th edition (2012) and 27th edition (1993).

**Holmes** = a reading the editor adopted although none of the four editions above prints it.

**TR** = the Textus Receptus; **Greeven** = H. Greeven's edition of Huck's *Synopsis of the First Three Gospels* (1981).

*Signs*

**]** separates the reading of the SBL text, on the left, from the other readings.

**+** a word or words added by the edition named; **–** omitted by it.

**…** stands for the words between the first and the last word of a longer reading.

*In the printed SBL text small signs (⸀ ⸂ ⸃) mark the places the apparatus discusses. They are left out here: every note is shown with the verse it belongs to.*
"""

ABOUT = """# title_en: New Testament
# app_id: no.anagnosis.newtestament

The Greek New Testament in the SBL edition of Michael W. Holmes with its apparatus, the Berean Standard Bible, and the Liddell–Scott dictionaries with Dodson's lexicon of the New Testament for the names and words they lack. Tap any word for its meaning and form; the lemmas and morphology are those of the MACULA Greek project.
"""


# ---------------------------------------------------------------- the translation

# Where the BSB numbers verses otherwise than the SBL text: (SBL verse, whether the English is
# appended to it). The English Acts 19:41 is the end of the Greek 19:40; the English
# 2 Corinthians 13:12-13 are the Greek 13:12 and the English 13:14 the Greek 13:13.
VERSIFICATION = {"5.19.41": ("5.19.40", True), "8.13.13": ("8.13.12", True), "8.13.14": ("8.13.13", False)}


def read_bsb(sources: Path) -> dict[str, str]:
    """The Berean Standard Bible's New Testament verses by our verse number (1.5.3)."""
    out: dict[str, str] = {}
    for raw in (sources / "nt" / "bsb.txt").read_text(encoding="utf-8-sig").splitlines():
        ref, sep, text = raw.partition("\t")
        m = re.fullmatch(r"(.+) (\d+):(\d+)", ref.strip())
        if not sep or not m or m.group(1) not in ENGLISH_NUMBER or not text.strip():
            continue  # the BSB keeps a verse the critical texts omit (Matthew 17:21) as an empty line
        n = f"{ENGLISH_NUMBER[m.group(1)]}.{int(m.group(2))}.{int(m.group(3))}"
        text = " ".join(text.split())
        if n in VERSIFICATION:
            n, append = VERSIFICATION[n]
            if append:
                text = f"{out[n]} {text}"
        out[n] = text
    return out


# ---------------------------------------------------------------- import

def import_nt(sources: Path, texts: Path, build: Path, slug: str = "newtestament") -> int:
    from .build import load_lexica, load_logeion_shortdefs, resolve_short_definition
    from .import_perseus import write_tokens

    out = texts / slug
    out.mkdir(parents=True, exist_ok=True)
    problems: list[str] = []

    # --- the text
    books = read_text(sources)
    txt = [f"# {k}: {v}" for k, v in GREEK_META.items()] + [""]
    for name, title, lines in books:
        txt.append(f"== book {name} · {title}")
        for line in lines:
            if line["para"]:
                txt.append("@ ")
            txt.append(f"{line['n']}\t{line['text']}")
        txt.append("")
    (out / "grc.txt").write_text("\n".join(txt), encoding="utf-8")
    all_lines = [l for _n, _t, ls in books for l in ls]
    print(f"wrote {out / 'grc.txt'}: {len(books)} books, {len(all_lines)} lines, "
          f"{sum(1 for l in all_lines if l['para'])} paragraphs, {sum(1 for l in all_lines if l['n'][-1].isalpha())} verses divided by a paragraph")

    # --- lemmas and morphology, word by word from MACULA
    macula = read_macula(sources)
    forms = [w for l in all_lines for w in l["words"]]
    if len(forms) != len(macula):
        raise SystemExit(f"the SBLGNT has {len(forms)} words, MACULA {len(macula)}")
    rows: list[dict] = []
    k = 0
    for line in all_lines:
        words = [w for w, _s, _e in greek.words(line["text"])]
        if words != line["words"]:
            problems.append(f"{line['n']}: the text's words {words} are not the SBLGNT's {line['words']}")
        for ord_, form in enumerate(line["words"]):
            r = macula[k]
            k += 1
            letters = lambda w: "".join(c for c in greek.strip_diacritics(w) if c.isalpha())
            # MACULA writes Moses Μωϋσῆς where the SBLGNT has Μωσῆς (John 8:5)
            if letters(r["text"]) != letters(form) and not (form == "Μωσῆς" and r["text"] == "Μωϋσῆς"):
                problems.append(f"{line['n']}: {form} is {r['text']} in MACULA ({r['xml:id']})")
            rows.append({"line": line["n"], "ord": str(ord_), "form": form, "lemma": greek.nfc(r["lemma"]),
                         "postag": postag(r), "relation": "", "head": "", "sentence": "", "word_id": ""})
    write_tokens(out / "tokens.tsv", rows)
    print(f"wrote {out / 'tokens.tsv'}: {len(rows)} words, {len({r['lemma'] for r in rows})} lemmas")

    # --- the dictionaries: aliases for New Testament spellings, Dodson for what they lack
    lexica = load_lexica(sources, build)
    headwords = {e.headword for entries in lexica.values() for e in entries}
    counts = collections.Counter(r["lemma"] for r in rows)
    aliases, missing = resolve_lemmas(sorted(counts), headwords)
    strong: dict[str, collections.Counter] = collections.defaultdict(collections.Counter)
    for r in macula:
        if r["strong"].isdigit():
            strong[greek.nfc(r["lemma"])][int(r["strong"])] += 1
    dodson = read_dodson(sources)

    def dodson_of(lemma: str) -> dict | None:
        for number, _c in strong[lemma].most_common():
            if number in dodson:
                return dodson[number]
        return None

    with (out / "aliases.tsv").open("w", encoding="utf-8") as f:
        f.write("# lemma\theadword under which LSJ / Middle Liddell list it (made by 'import-nt')\n")
        for lemma in sorted(aliases):
            f.write(f"{lemma}\t{aliases[lemma]}\n")
    glossary = [f"# {k}: {v}" for k, v in GLOSSARY_META.items()] + [""]
    no_entry = []
    for lemma in sorted(missing, key=lambda l: (-counts[l], l)):
        d = dodson_of(lemma)
        if d is not None:
            body = f"**{d['orth']}** {d['full']}"
        elif lemma in HAND_GLOSSES:
            body = f"**{lemma}** {HAND_GLOSSES[lemma]}"
        else:
            no_entry.append(lemma)
            continue
        glossary += [f"## {lemma}", body, ""]
    (out / "glossary.md").write_text("\n".join(glossary), encoding="utf-8")
    exact, loose = load_logeion_shortdefs(sources)
    shortdefs = ["# Short definitions for lemmas missing from Logeion's list, from Dodson's lexicon (made by 'import-nt'). lemma\tdefinition"]
    missing_set = set(missing)
    for lemma in sorted(counts):
        if lemma in missing_set:
            continue  # its glossary entry is shown
        if resolve_short_definition(lemma, exact, loose) is not None:
            continue
        if lemma in aliases and resolve_short_definition(aliases[lemma], exact, loose) is not None:
            continue
        d = dodson_of(lemma)
        gloss = d["brief"] if d is not None else HAND_GLOSSES.get(lemma)
        if gloss:
            shortdefs.append(f"{lemma}\t{gloss}")
        else:
            no_entry.append(lemma)
    (out / "shortdefs.tsv").write_text("\n".join(shortdefs) + "\n", encoding="utf-8")
    print(f"lemmas: {len(counts)}; {len(aliases)} found under another headword (aliases.tsv), "
          f"{len(missing)} not in LSJ or Middle Liddell (glossary.md, {sum(counts[l] for l in missing)} words), "
          f"{len(shortdefs) - 1} short definitions from Dodson (shortdefs.tsv), {len(no_entry)} with nothing: {no_entry[:20]}")
    problems += [f"no definition for {l}" for l in no_entry]

    # --- the apparatus and its sigla
    notes = read_apparatus(sources)
    md = [f"# {k}: {v}" for k, v in APPARATUS_META.items()] + [""]
    for heading, items in notes:
        md += [f"## {heading}", "\n\n".join(items), ""]
    (out / "commentary-sbl-apparatus.md").write_text("\n".join(md), encoding="utf-8")
    print(f"wrote {out / 'commentary-sbl-apparatus.md'}: {len(notes)} verses, {sum(len(i) for _, i in notes)} notes")
    (out / "sigla.md").write_text(SIGLA_DOC, encoding="utf-8")
    (out / "about.md").write_text(ABOUT, encoding="utf-8")

    # --- the Berean Standard Bible, a paragraph wherever the Greek begins one
    bsb = read_bsb(sources)
    greek_verses = {re.sub(r"[a-z]$", "", l["n"]) for l in all_lines}
    para = {l["n"] for l in all_lines if l["para"] and not l["n"][-1].isalpha()}
    eng = [f"# {k}: {v}" for k, v in BSB_META.items()] + [""]
    from .linenum import parts as n_parts
    for n in sorted(bsb, key=n_parts):
        if n in para:
            eng.append("@ ")
        # a verse the SBL text leaves out (Matthew 17:21): bracketed, as not in the Greek beside it
        eng.append(f"{n}\t{bsb[n]}" if n in greek_verses else f"{n}\t[{bsb[n]}]")
    (out / "eng-bsb.txt").write_text("\n".join(eng) + "\n", encoding="utf-8")
    only_greek = sorted(greek_verses - set(bsb), key=n_parts)
    only_english = sorted(set(bsb) - greek_verses, key=n_parts)
    print(f"wrote {out / 'eng-bsb.txt'}: {len(bsb)} verses; {len(only_english)} not in the SBL text "
          f"({only_english[:12]}), {len(only_greek)} missing in the BSB ({only_greek[:12]})")

    log = build / "nt-import.log"
    log.write_text("\n".join(problems) + "\n", encoding="utf-8")
    print(f"{len(problems)} problems ({log})")
    return len(problems)
