"""Analyses for the word analyser, made with Morpheus itself.

Morpheus (github.com/perseids-tools/morpheus, Mozilla Public License 2.0) is built in
pipeline/sources/morpheus (see fetch.py) and run over every distinct word form of open texts:
the Perseus canonical Greek corpus (CC BY-SA 4.0), the Perseus treebanks and the texts in
texts/. Its analyses are converted to the nine-position Perseus treebank tags and written to
pipeline/build/morpheus-analyses.tsv.gz ("form<TAB>lemma<TAB>postag<TAB>dialects" lines), which
forms.py puts into data/lexicon.sqlite.

(The analyser earlier used a Morpheus dump from a repository licensed CC BY-NC, which a paid
app may not use; this replaces it.)
"""
from __future__ import annotations

import gzip
import itertools
import os
import re
import subprocess
import sys
import tarfile
import unicodedata
from collections import Counter
from pathlib import Path

import beta_code
from lxml import etree

from . import greek

TENSE = {"pres": "p", "imperf": "i", "perf": "r", "plup": "l", "futperf": "t", "fut_perf": "t", "fut": "f", "aor": "a"}
MOOD = {"ind": "i", "subj": "s", "opt": "o", "inf": "n", "imperat": "m", "part": "p"}
VOICE = {"act": "a", "mid": "m", "pass": "p", "mp": "e"}
PERSON = {"1st": "1", "2nd": "2", "3rd": "3"}
NUMBER = {"sg": "s", "pl": "p", "dual": "d"}
GENDER = {"masc": "m", "fem": "f", "neut": "n"}
CASE = {"nom": "n", "gen": "g", "dat": "d", "acc": "a", "voc": "v"}
DEGREE = {"comp": "c", "superl": "s"}
# Morpheus stem types of the indeclinable and pronominal words, and the part of speech they mean
STEMTYPE_POS = {
    "conj": "c", "prep": "r", "adverb": "d", "article": "l", "particle": "g", "exclam": "i",
    "numeral": "m", "pron1": "p", "pron2": "p", "pron3": "p", "relative": "p", "indef": "p",
    "interrog": "p", "demonstr": "p", "indecl": "p", "art_adj": "p", "pron_adj1": "p", "pron_adj2": "p",
}
# Stem types of two-termination adjectives (masc/fem and neuter), told apart from nouns
TWO_TERMINATION = {"os_on", "hs_es", "wn_on", "us_u", "ws_wn", "hn_en", "ous_oun", "is_i", "wn_ousa_on",
                   "eis_essa_en", "as_asa_an", "us_usa_un", "ws_uia_os"}


def _to_unicode(beta: str) -> str:
    beta = beta.replace("_", "").replace("^", "")
    beta = re.sub(r"#\d+$", "", beta)
    beta = re.sub(r"\d+$", "", beta)
    return greek.nfc(beta_code.beta_code_to_greek(beta))


def _to_beta(form: str) -> str:
    """A Unicode word as Morpheus input: Beta Code, grave read as acute, elision as '."""
    s = unicodedata.normalize("NFD", form.replace(greek.APOSTROPHE, "'").replace("’", "'"))
    s = s.replace("̀", "́")
    s = unicodedata.normalize("NFC", s)
    return beta_code.greek_to_beta_code(s)


def tags(letter: str, features: list[str], stemtypes: list[str], flags: list[str] | None = None) -> list[str]:
    """Nine-position tags for one Morpheus analysis (several where it names alternatives,
    e.g. masc/neut or nom/voc/acc)."""
    f = set()
    genders, cases = [None], [None]
    for t in features:
        if "/" in t and all(x in GENDER for x in t.split("/")):
            genders = t.split("/")
        elif "/" in t and all(x in CASE for x in t.split("/")):
            cases = t.split("/")
        elif t in GENDER:
            genders = [t]
        elif t in CASE:
            cases = [t]
        else:
            f.add(t)
    tense = next((TENSE[t] for t in f if t in TENSE), "-")
    mood = next((MOOD[t] for t in f if t in MOOD), "-")
    voice = next((VOICE[t] for t in f if t in VOICE), "-")
    person = next((PERSON[t] for t in f if t in PERSON), "-")
    number = next((NUMBER[t] for t in f if t in NUMBER), "-")
    degree = next((DEGREE[t] for t in f if t in DEGREE), "-")
    if degree == "-" and flags:  # irregular comparison is a flag: irreg_comp, irreg_superl
        degree = "s" if "irreg_superl" in flags else "c" if "irreg_comp" in flags else "-"
    if letter == "V":
        pos = "v"
    elif letter == "P":
        pos, mood = "v", "p"
    else:
        known = [STEMTYPE_POS[s] for s in stemtypes if s in STEMTYPE_POS]
        if "adverbial" in f:
            pos = "d"
        elif known:
            pos = known[0]
        elif degree != "-" or any(s.count("_") >= 2 or s in TWO_TERMINATION or "adj" in s for s in stemtypes):
            pos = "a"
        else:
            pos = "n"
    out = []
    for g, c in itertools.product(genders, cases):
        gc = GENDER.get(g, "-") if g else "-"
        cc = CASE.get(c, "-") if c else "-"
        out.append(pos + person + number + tense + mood + voice + gc + cc + degree)
    return out


def parse_nl(nl: str) -> list[tuple[str, str, str]]:
    """(lemma, tag, dialects) from one '<NL>...</NL>' analysis; dialects is Morpheus's
    space-separated list ('attic epic ionic', 'doric aeolic'), empty for all dialects."""
    fields = nl.split("\t")
    head = fields[0]
    m = re.match(r"^([A-Z])\s+(\S+)\s*(.*)$", head)
    if not m:
        return []
    letter, lemma, feats = m.group(1), m.group(2), m.group(3).split()
    stemtypes, flags, dialects = [], [], ""
    if len(fields) >= 4:
        stemtypes = [s for s in fields[3].split(",") if s]
        flags = fields[2].split()
        dialects = " ".join(fields[1].split())
    elif len(fields) >= 2:
        stemtypes = [s for s in fields[-1].split(",") if s]
    lemma = lemma.split(",")[-1]
    lemma = re.sub(r"-pl$", "", lemma)
    try:
        lem = _to_unicode(lemma)
    except Exception:
        return []
    return [(lem, t, dialects) for t in tags(letter, feats, stemtypes, flags)]


def _crunch(part: list[str], morpheus: Path) -> dict[str, list[tuple[str, str, str]]]:
    env = dict(os.environ, MORPHLIB=str(morpheus / "stemlib"))
    betas = [_to_beta(f) for f in part]
    res = subprocess.run([str(morpheus / "bin" / "cruncher"), "-S"], input="\n".join(betas) + "\n",
                         capture_output=True, text=True, env=env)
    lines = res.stdout.splitlines()
    # The output echoes each input word that has analyses, followed by a line of <NL>
    # analyses; words Morpheus does not know are left out altogether.
    found: dict[str, str] = {}
    for k, line in enumerate(lines):
        if k + 1 < len(lines) and not line.startswith("<NL>") and lines[k + 1].startswith("<NL>"):
            found[line.strip()] = lines[k + 1]
    out: dict[str, list[tuple[str, str, str]]] = {}
    for form, beta in zip(part, betas):
        nl_line = found.get(beta.strip())
        if not nl_line:
            continue
        analyses: list[tuple[str, str, str]] = []
        for nl in re.findall(r"<NL>(.*?)</NL>", nl_line):
            analyses.extend(parse_nl(nl))
        if analyses:
            out[form] = list(dict.fromkeys(analyses))
    return out


def run_morpheus(forms: list[str], morpheus: Path, chunk: int = 4000, workers: int = 12) -> dict[str, list[tuple[str, str, str]]]:
    """Analyses of each form, by running cruncher over the forms in chunks, several at a time."""
    from concurrent.futures import ThreadPoolExecutor

    out: dict[str, list[tuple[str, str, str]]] = {}
    parts = [forms[i : i + chunk] for i in range(0, len(forms), chunk)]
    with ThreadPoolExecutor(max_workers=workers) as pool:
        for k, res in enumerate(pool.map(lambda part: _crunch(part, morpheus), parts)):
            out.update(res)
            if k % 10 == 9 or k == len(parts) - 1:
                print(f"  morpheus: {min((k + 1) * chunk, len(forms))}/{len(forms)} forms, {len(out)} analysed", file=sys.stderr)
    return out


def corpus_forms(sources: Path, texts: Path) -> Counter:
    """Distinct Greek word forms (NFC) of the open corpora, treebanks and our texts, with counts."""
    words: Counter = Counter()
    tarball = sources / "corpora" / "canonical-greekLit.tar.gz"
    with tarfile.open(tarball) as tf:
        for member in tf:
            if not re.search(r"grc\d*\.xml$", member.name):
                continue
            data = tf.extractfile(member).read()
            try:
                root = etree.fromstring(data, etree.XMLParser(recover=True, huge_tree=True))
            except Exception:
                continue
            if root is None:
                continue
            body = root.find(".//{http://www.tei-c.org/ns/1.0}body")
            if body is None:
                continue
            for el in body.iter("{http://www.tei-c.org/ns/1.0}note"):
                el.clear()  # editors' notes are not Greek text
            text = " ".join(body.itertext())
            for w, _s, _e in greek.words(text):
                words[greek.nfc(w)] += 1
    for path in sorted((sources / "treebanks").glob("*.xml")):
        for m in re.finditer(r'form="([^"]+)"', path.read_text(encoding="utf-8")):
            f = greek.nfc(m.group(1))
            if greek.is_word(f):
                words[f] += 1
    for grc in texts.glob("*/grc.txt"):
        for raw in grc.read_text(encoding="utf-8").splitlines():
            _n, sep, body = raw.partition("\t")
            if sep and not raw.startswith("#"):
                for w, _s, _e in greek.words(body):
                    words[greek.nfc(w)] += 1
    return words


def build(sources: Path, texts: Path, out: Path) -> int:
    morpheus = sources / "morpheus"
    if not (morpheus / "bin" / "cruncher").exists():
        raise SystemExit(f"Morpheus is not built: see {morpheus}/README.md (cd src; CFLAGS='-std=gnu89 -fcommon' make; make install)")
    words = corpus_forms(sources, texts)
    # Greek letters only; the analyser keys forms without diacritics, so one form per spelling suffices
    forms = sorted(w for w in words if re.fullmatch(r"[Ͱ-Ͽἀ-῿ʼ’̀-ͯ]+", w))
    print(f"morpheus: {len(forms)} distinct forms from {sum(words.values())} words", file=sys.stderr)
    analyses = run_morpheus(forms, morpheus)
    out.parent.mkdir(parents=True, exist_ok=True)
    with gzip.open(out, "wt", encoding="utf-8") as f:
        for form in forms:
            for lemma, tag, dialects in analyses.get(form, []):
                f.write(f"{form}\t{lemma}\t{tag}\t{dialects}\n")
    print(f"wrote {out}: {len(analyses)} of {len(forms)} forms analysed")
    return len(analyses)
