"""Import Perseus TEI texts and the treebank into the editable files under texts/<slug>/.

This is run once (or when upstream changes); afterwards the files in texts/ are the
source of truth and may be edited by hand.
"""
from __future__ import annotations

import csv
import re
import sys
from pathlib import Path

from lxml import etree

from . import greek
from .textfmt import Document, Line, Section, Speaker, Stage, write_file

TEI = "{http://www.tei-c.org/ns/1.0}"


def _local(el) -> str:
    return etree.QName(el).localname


def _inline_text(el) -> str:
    """Flatten an <l>/<stage>/<speaker> element to plain text with light editorial marks."""
    parts: list[str] = []

    def walk(node):
        if node.text:
            parts.append(node.text)
        for child in node:
            tag = _local(child)
            if tag == "add":
                parts.append("⟨")
                walk(child)
                parts.append("⟩")
            elif tag == "del":
                parts.append("[")
                walk(child)
                parts.append("]")
            elif tag == "q":
                parts.append("“")
                walk(child)
                parts.append("”")
            elif tag in ("milestone", "pb", "note"):
                pass
            else:
                walk(child)
            if child.tail:
                parts.append(child.tail)

    walk(el)
    return greek.nfc(re.sub(r"\s+", " ", "".join(parts))).strip()


def tei_to_document(path: Path, meta: dict[str, str]) -> Document:
    tree = etree.parse(str(path))
    body = tree.find(f".//{TEI}body")
    doc = Document(meta=dict(meta))

    def walk(node, depth: int):
        for child in node:
            tag = _local(child)
            if tag == "div":
                if child.get("type") == "textpart":
                    kind = child.get("subtype", "div")
                    doc.items.append(Section(depth, kind, child.get("n", "")))
                    walk(child, depth + 1)
                else:
                    walk(child, depth)
            elif tag == "sp":
                sp = child.find(f"{TEI}speaker")
                doc.items.append(Speaker(_inline_text(sp) if sp is not None else ""))
                walk(child, depth)
            elif tag == "l":
                doc.items.append(Line(child.get("n"), _inline_text(child)))
            elif tag == "stage":
                doc.items.append(Stage(_inline_text(child)))
            elif tag in ("speaker", "milestone", "pb", "head"):
                pass
            else:
                walk(child, depth)

    walk(body, 1)
    return doc


# ---------------------------------------------------------------- treebank

def read_treebank(path: Path) -> list[dict]:
    """All real (non-artificial) tokens in document order, with their cited line number."""
    tree = etree.parse(str(path))
    out = []
    for sent in tree.iter("sentence"):
        current_line = None
        for w in sent.iter("word"):
            if w.get("artificial") or w.get("insertion_id"):
                continue
            cite = w.get("cite", "")
            if cite:
                current_line = cite.rsplit(":", 1)[-1]
            form = greek.nfc(w.get("form", ""))
            out.append(
                {
                    "sentence": sent.get("id"),
                    "word_id": w.get("id"),
                    "line": current_line,
                    "form": form,
                    "lemma": greek.nfc(w.get("lemma", "")),
                    "postag": w.get("postag", ""),
                    "head": w.get("head", ""),
                    "relation": w.get("relation", ""),
                    "is_word": greek.is_word(form),
                }
            )
    return out


# Treebank lemmas for compounds the treebank splits into two tokens (οὔτʼ -> οὔ + τ̓).
MERGED_LEMMAS = {
    "οὐ+τε": "οὔτε", "οὐ+δέ": "οὐδέ", "μή+τε": "μήτε", "μή+δέ": "μηδέ",
    "οὐ+δείς": "οὐδείς", "μή+δείς": "μηδείς", "οὐ+τις": "οὔτις", "μή+τις": "μήτις",
    "οὐ+ποτε": "οὔποτε", "μή+ποτε": "μήποτε", "οὐ+πω": "οὔπω", "μή+πω": "μήπω",
    "οὐ+κοῦν": "οὐκοῦν", "οὐ+κέτι": "οὐκέτι", "μή+κέτι": "μηκέτι", "οὐ+δαμοῦ": "οὐδαμοῦ",
    "οὐ+τοι": "οὔτοι", "μή+τοι": "μήτοι", "οὐ+πως": "οὔπως", "οὐ+δαμῶς": "οὐδαμῶς",
    "μή+δαμῶς": "μηδαμῶς", "οὐ+δέποτε": "οὐδέποτε", "μή+δέποτε": "μηδέποτε",
}

MAX_MERGE = 4

# Corrections to treebank lemmas (typos, wrong accents, inflected forms used as lemma).
LEMMA_FIXES = {
    "??": "δέ",
    "ἀνιτλογέω": "ἀντιλογέω",
    "Λαδβακίδης": "Λαβδακίδης",
    "Ἀντιγόνην": "Ἀντιγόνη",
    "Τειρεσίης": "Τειρεσίας",
    "ὁ͂ι": "οἷ",
    "ὐπέρτατος": "ὑπέρτατος",
    "Οιδίπους": "Οἰδίπους",
    "πάτηρ": "πατήρ",
    "ὁμοῖος": "ὅμοιος",
    "πλήσιος": "πλησίος",
    "ἀμφικεῖμαι": "ἀμφίκειμαι",
    "σαυτοῦ": "σεαυτοῦ",
}

# Hand annotations for words the treebank does not cover (Storr's text differs from the
# text the treebank was made from). Keyed by (line, word index in line).
TOKEN_FIXES = {
    ("591", 2): {"lemma": "βρέμω", "postag": "v3ppia---"},
    ("591", 3): {"lemma": "δέ", "postag": "g--------"},
    ("1321", 2): {"lemma": "ὅς", "postag": "p-s---na-"},
    ("1321", 3): {"lemma": "τις", "postag": "p-s---na-"},
}


def _merge_lemma(form: str, ws: list[dict]) -> str:
    """Lemma for a text word that the treebank split into several tokens.

    Usually the first token already carries the compound lemma (οὔ -> οὔτε); otherwise
    look the combination up in MERGED_LEMMAS, else join with '+' so that 'check' reports it.
    """
    first = ws[0]["lemma"]
    if greek.strip_diacritics(first).startswith(greek.strip_diacritics(form)):
        return first
    key = "+".join(w["lemma"] for w in ws)
    return MERGED_LEMMAS.get(key, key)


def align_tokens(doc: Document, tb: list[dict]) -> tuple[list[dict], list[str]]:
    """Match the words of the text, in document order, to the treebank words in document order.

    Line numbers are deliberately ignored: the treebank's citations drift by a line in
    lyric passages. A text word may correspond to 1..MAX_MERGE consecutive treebank words
    (the treebank splits οὔτε, οὐδέ, μηδέ ...). Text forms win; the treebank contributes
    lemma and morphology. Unmatched stretches are reported and left without a lemma.
    """
    text_words: list[tuple[str, int, str]] = []  # (line n, ord, form)
    for line in doc.lines:
        for ord_, (form, _s, _e) in enumerate(greek.words(line.text)):
            text_words.append((line.n, ord_, form))
    tb_words = [w for w in tb if w["is_word"]]
    ta = [greek.strip_diacritics(f) for _, _, f in text_words]
    tb_sk = [greek.strip_diacritics(w["form"]) for w in tb_words]

    matched: dict[int, list[dict]] = {}
    warnings: list[str] = []
    i = j = 0
    while i < len(ta) and j < len(tb_sk):
        hit = 0
        acc = ""
        for k in range(1, MAX_MERGE + 1):
            if j + k > len(tb_sk):
                break
            acc += tb_sk[j + k - 1]
            if acc == ta[i]:
                hit = k
                break
            if len(acc) >= len(ta[i]):
                break
        if hit:
            matched[i] = tb_words[j : j + hit]
            i += 1
            j += hit
            continue
        # Resynchronise: find the nearest (di, dj) where three consecutive skeletons agree.
        best = None
        for di in range(0, 12):
            for dj in range(0, 12):
                ii, jj = i + di, j + dj
                if ii + 3 <= len(ta) and jj + 3 <= len(tb_sk) and ta[ii : ii + 3] == tb_sk[jj : jj + 3]:
                    if best is None or di + dj < best[0] + best[1]:
                        best = (di, dj)
        if best is None:
            warnings.append(f"line {text_words[i][0]}: lost synchronisation at {text_words[i][2]!r}")
            break
        di, dj = best
        skipped_t = text_words[i : i + di]
        skipped_b = tb_words[j : j + dj]
        if di == dj:
            for k in range(di):
                matched[i + k] = [tb_words[j + k]]
                warnings.append(
                    f"line {text_words[i + k][0]}: paired {text_words[i + k][2]!r} with treebank {tb_words[j + k]['form']!r}"
                )
        else:
            warnings.append(
                f"line {skipped_t[0][0] if skipped_t else text_words[i][0]}: unmatched text={[f for _, _, f in skipped_t]} treebank={[w['form'] for w in skipped_b]}"
            )
        i += di
        j += dj
    if i < len(ta):
        warnings.append(f"{len(ta) - i} text words after last match are unmatched (from line {text_words[i][0]})")
    if j < len(tb_sk):
        warnings.append(f"{len(tb_sk) - j} treebank words left over after the text ended")

    rows: list[dict] = []
    for idx, (n, ord_, form) in enumerate(text_words):
        ws = matched.get(idx)
        if ws and len(ws) == 1:
            w = ws[0]
            lemma, postag, relation, head, sentence, word_id = (
                w["lemma"], w["postag"], w["relation"], w["head"], w["sentence"], w["word_id"],
            )
        elif ws:
            w = ws[0]
            lemma = _merge_lemma(form, ws)
            postag, relation, head, sentence, word_id = "", "", "", w["sentence"], "+".join(x["word_id"] for x in ws)
        else:
            lemma = postag = relation = head = sentence = word_id = ""
        row = {"line": n, "ord": ord_, "form": form, "lemma": lemma, "postag": postag,
               "relation": relation, "head": head, "sentence": sentence, "word_id": word_id}
        row.update(TOKEN_FIXES.get((n, ord_), {}))
        row["lemma"] = LEMMA_FIXES.get(row["lemma"], row["lemma"])
        rows.append(row)
    return rows, warnings


TOKEN_COLUMNS = ["line", "ord", "form", "lemma", "postag", "relation", "head", "sentence", "word_id"]


def write_tokens(path: Path, rows: list[dict]) -> None:
    with path.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=TOKEN_COLUMNS, delimiter="\t", lineterminator="\n")
        w.writeheader()
        w.writerows(rows)


def read_tokens(path: Path) -> list[dict]:
    with path.open(encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f, delimiter="\t"))


# ---------------------------------------------------------------- entry point

def import_antigone(sources: Path, texts: Path) -> None:
    out = texts / "antigone"
    out.mkdir(parents=True, exist_ok=True)

    grc = tei_to_document(
        sources / "antigone.grc2.xml",
        {
            "title": "Ἀντιγόνη",
            "author": "Σοφοκλῆς",
            "lang": "grc",
            "source": "urn:cts:greekLit:tlg0011.tlg002.perseus-grc2",
            "edition": "Sophocles, vol. 1, ed. Francis Storr, Loeb Classical Library, 1912 (Perseus Digital Library)",
            "license": "CC BY-SA 4.0",
        },
    )
    write_file(out / "grc.txt", grc)
    print(f"wrote {out/'grc.txt'}: {len(grc.lines)} lines")

    eng = tei_to_document(
        sources / "antigone.eng2.xml",
        {
            "title": "Antigone",
            "translator": "Richard C. Jebb",
            "lang": "eng",
            "source": "urn:cts:greekLit:tlg0011.tlg002.perseus-eng2",
            "edition": "Sophocles: The Plays and Fragments, part III: The Antigone, tr. R. C. Jebb, Cambridge 1891; modernized by Perseus",
            "license": "CC BY-SA 4.0",
        },
    )
    write_file(out / "eng-jebb.txt", eng)
    print(f"wrote {out/'eng-jebb.txt'}: {len(eng.lines)} paragraphs")

    tb = read_treebank(sources / "antigone.tb.xml")
    rows, warnings = align_tokens(grc, tb)
    write_tokens(out / "tokens.tsv", rows)
    missing = sum(1 for r in rows if not r["lemma"])
    print(f"wrote {out/'tokens.tsv'}: {len(rows)} words, {missing} without lemma, {len(warnings)} warnings")
    for w in warnings:
        print("  " + w, file=sys.stderr)

    from .commentary import import_jebb_commentary

    n = import_jebb_commentary(
        sources / "jebb-antigone-commentary.xml",
        out / "commentary-jebb.md",
        {
            "title": "Commentary on Sophocles: Antigone",
            "author": "Richard C. Jebb",
            "lang": "eng",
            "source": "Perseus Digital Library, jebb.soph.ant_eng.xml (Sophocles: The Plays and Fragments, part III, Cambridge University Press, 1900)",
            "license": "CC BY-SA 3.0 US",
        },
    )
    print(f"wrote {out/'commentary-jebb.md'}: {n} notes")
