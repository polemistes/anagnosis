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
                text = _inline_text(child)
                if not text.strip() and child.find(f"{TEI}gap") is not None:
                    text = "…"  # a verse lost in the Greek (<gap reason="lost"/>)
                doc.items.append(Line(child.get("n"), text))
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
                # "161.1" is the treebank's spelling of the extra line 161b
                m = re.match(r"^(\d+)\.(\d+)$", current_line)
                if m:
                    current_line = m.group(1) + "abcdefgh"[int(m.group(2))]
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
    "εἰ+τε": "εἴτε", "ἐάν+τε": "ἐάν",  # GLAUx splits εἴτε and ἐάντε (LSJ has ἐάντε under ἐάν)
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
    # slips in the Ajax treebank
    "πρήν": "φρήν",
    "τεῦκρος": "Τεῦκρος",
    "Ατρείδης": "Ἀτρείδης",
    "Ἐριβοία": "Ἐρίβοια",
    "ἀπαίσσω": "ἀπαΐσσω",
    "εἴσειδον": "εἰσεῖδον",
    "οἰ": "οἴ",
}

# Hand annotations for words the treebank does not cover (Storr's text differs from the
# text the treebank was made from). Keyed by (line, word index in line).
# Jebb reads βρέμουσι δʼ where the treebank's text has βρέμουσιν: the verb takes the treebank's
# word 21 and the particle a new id, so that the sentence's syntax tree is complete.
TOKEN_FIXES = {
    ("591", 2): {"lemma": "βρέμω", "postag": "v3ppia---", "relation": "PRED_CO", "head": "18", "sentence": "2900392", "word_id": "21"},
    ("591", 3): {"lemma": "δέ", "postag": "g--------", "relation": "AuxY", "head": "21", "sentence": "2900392", "word_id": "26"},
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
            # the merged word takes the syntax of the part that is not a mere particle: the τε of
            # οὔτε is the coordinator (COORD), the οὔ only an AuxZ on a member
            main = next((x for x in ws if x["relation"] not in ("AuxZ", "AuxY", "")), ws[0])
            postag, relation, head = main["postag"], main["relation"], main["head"]
            sentence, word_id = w["sentence"], "+".join(x["word_id"] for x in ws)
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


# ---------------------------------------------------------------- syntax nodes

# Tokens of the treebank that are not words of the text, yet take part in the syntax: the
# punctuation (a comma often heads a coordination) and the artificial nodes that stand for
# an omitted word (an elided verb, "[0]"). They complete the trees drawn from tokens.tsv.
SYNTAX_NODE_COLUMNS = ["sentence", "word_id", "form", "lemma", "postag", "relation", "head", "artificial"]


def read_treebank_nodes(path: Path) -> list[dict]:
    """The treebank's punctuation and artificial nodes, in document order."""
    tree = etree.parse(str(path))
    out = []
    for sent in tree.iter("sentence"):
        for w in sent.iter("word"):
            form = greek.nfc(w.get("form", ""))
            artificial = bool(w.get("artificial") or w.get("insertion_id"))
            if not artificial and greek.is_word(form):
                continue
            out.append(
                {
                    "sentence": sent.get("id"),
                    "word_id": w.get("id"),
                    "form": form,
                    "lemma": greek.nfc(w.get("lemma", "")) if not artificial else "",
                    "postag": w.get("postag", "") if not artificial else "",
                    "relation": w.get("relation", ""),
                    "head": w.get("head", ""),
                    "artificial": "1" if artificial else "",
                }
            )
    return out


def write_syntax_nodes(path: Path, rows: list[dict]) -> None:
    with path.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=SYNTAX_NODE_COLUMNS, delimiter="\t", lineterminator="\n")
        w.writeheader()
        w.writerows(rows)


def read_syntax_nodes(path: Path) -> list[dict]:
    if not path.exists():
        return []
    with path.open(encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f, delimiter="\t"))


def import_syntax_nodes(sources: Path, texts: Path) -> None:
    """Write texts/antigone/syntax-nodes.tsv alone; it touches no hand-edited file."""
    out = texts / "antigone" / "syntax-nodes.tsv"
    rows = read_treebank_nodes(sources / "antigone.tb.xml")
    write_syntax_nodes(out, rows)
    print(f"wrote {out}: {len(rows)} nodes ({sum(1 for r in rows if r['artificial'])} artificial)")


# ---------------------------------------------------------------- entry point

def import_antigone(sources: Path, texts: Path) -> None:
    out = texts / "antigone"
    out.mkdir(parents=True, exist_ok=True)

    tb = read_treebank(sources / "antigone.tb.xml")
    grc = p4_text_to_document(
        sources / "antigone.perseus-gk.xml",
        {
            "title": "Ἀντιγόνη",
            "author": "Σοφοκλῆς",
            "lang": "grc",
            "source": "Perseus Digital Library, soph.ant_gk.xml",
            "edition": "The Antigone of Sophocles, ed. R. C. Jebb, Cambridge University Press, 1891 (Perseus Digital Library)",
            "license": "CC BY-SA 3.0 US",
        },
    )
    for w in renumber_from_treebank(grc, tb):
        print("  numbering: " + w, file=sys.stderr)
    label_sections(grc, ANTIGONE_SECTIONS)
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

    rows, warnings = align_tokens(grc, tb)
    write_tokens(out / "tokens.tsv", rows)
    missing = sum(1 for r in rows if not r["lemma"])
    print(f"wrote {out/'tokens.tsv'}: {len(rows)} words, {missing} without lemma, {len(warnings)} warnings")
    for w in warnings:
        print("  " + w, file=sys.stderr)
    import_syntax_nodes(sources, texts)

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
    from .introduction import import_introduction

    n = import_introduction(
        sources / "jebb-antigone-commentary.xml",
        out / "introduction.md",
        {
            "title": "Introduction",
            "author": "Richard C. Jebb",
            "source": "Perseus Digital Library, jebb.soph.ant_eng.xml (Sophocles: The Plays and Fragments, part III, Cambridge University Press, 1900)",
            "license": "CC BY-SA 3.0 US",
        },
    )
    print(f"wrote {out/'introduction.md'}: {n} sections")
    ocr = sources / "scans" / "sophocles03soph_djvu.txt"
    if ocr.exists():
        from .ffmarks import apply_ff_marks

        print(f"  f./ff. marks from OCR: {apply_ff_marks(out / 'commentary-jebb.md', ocr)} headings")


# ---------------------------------------------------------------- Perseus P4 Greek editions (betacode)

def p4_text_to_document(path: Path, meta: dict[str, str], split_verses: bool = False) -> Document:
    """Older Perseus Greek editions: TEI P4, betacode, <l> mostly without n (only every fifth line).

    With `split_verses`, the later parts of a verse shared between speakers (<l part="M|F">)
    keep the verse's number, and their indices are listed in meta["_parts"]."""
    from .tei_p4 import load as load_p4

    root = load_p4(path)
    body = root.find(".//body")
    doc = Document(meta=dict(meta))
    counter = 0
    explicit: set[int] = set()  # indices (in doc.lines) of lines whose number the file states
    continued: set[int] = set()  # indices of the later parts of a shared verse

    def text_of(el) -> str:
        parts = [el.text or ""]
        for child in el:
            if isinstance(child.tag, str):
                parts.append(text_of(child))
            parts.append(child.tail or "")
        return "".join(parts)

    def walk(node, depth: int):
        nonlocal counter
        for child in node:
            if not isinstance(child.tag, str):
                continue
            tag = child.tag
            if tag in ("div1", "div2", "div3"):
                doc.items.append(Section(depth, child.get("type", "div"), child.get("n", "")))
                walk(child, depth + 1)
            elif tag == "sp":
                sp = child.find("speaker")
                doc.items.append(Speaker(greek.betacode_to_unicode(text_of(sp).strip()) if sp is not None else ""))
                walk(child, depth)
            elif tag == "l":
                n = child.get("n")
                if split_verses and child.get("part") in ("M", "F") and doc.lines:
                    continued.add(len(doc.lines))
                    label = str(counter)
                    if n:  # the verse's number, written on its later part
                        explicit.add(len(doc.lines))
                        counter = int(re.match(r"^(\d+)", n).group(1))
                        label = n
                elif n:
                    m = re.match(r"^(\d+)([a-z]?)$", n)
                    counter = int(m.group(1))
                    label = n
                    explicit.add(len(doc.lines))
                else:
                    counter += 1
                    label = str(counter)
                raw = text_of(child)
                raw = raw.replace("[", "⟦").replace("]", "⟧")  # keep brackets out of betacode's way
                text = greek.betacode_to_unicode(re.sub(r"\s+", " ", raw).strip())
                text = text.replace("⟦", "[").replace("⟧", "]").replace("'", greek.APOSTROPHE)
                text = re.sub(r"\s+([,.;·])", r"\1", text)
                if text in P4_DROP_DUPLICATE_LINES and doc.lines and doc.lines[-1].text == text:
                    counter -= 1
                    explicit.discard(len(doc.lines))
                    continue
                doc.items.append(Line(label, text))
            elif tag in ("speaker", "milestone", "pb", "head"):
                pass
            else:
                walk(child, depth)

    walk(body, 1)
    doc.meta["_explicit"] = ",".join(str(i) for i in sorted(explicit))
    if split_verses:
        doc.meta["_parts"] = ",".join(str(i) for i in sorted(continued))
    return doc


# Lines in the Perseus P4 Jebb text that are data errors (a line printed twice); matched by text.
P4_DROP_DUPLICATE_LINES = {"ξύν θʼ ἱπποκόμοις κορύθεσσιν."}


def renumber_from_treebank(doc: Document, tb: list[dict]) -> list[str]:
    """Give each line the number the treebank cites for most of its words.

    The treebank was annotated on Jebb's text and carries Jebb's traditional numbering, which
    the Perseus P4 file only marks every fifth line. Lines that share a number get letter
    suffixes (323, 323a). Returns warnings.
    """
    from collections import Counter

    rows, warnings = align_tokens(doc, tb)
    by_line: dict[str, Counter] = {}
    tb_by_id = {(w["sentence"], w["word_id"]): w for w in tb}
    for r in rows:
        if not r["word_id"] or "+" in r["word_id"]:
            continue
        w = tb_by_id.get((r["sentence"], r["word_id"]))
        if w and w["line"]:
            by_line.setdefault(r["line"], Counter())[w["line"]] += 1

    lines = doc.lines
    explicit = sorted(int(i) for i in doc.meta.pop("_explicit", "").split(",") if i)

    def vote_for(idx: int) -> str | None:
        votes = by_line.get(lines[idx].n)
        return votes.most_common(1)[0][0] if votes else None

    def n_int(n: str) -> int:
        return int(re.match(r"\d+", n).group())

    new_numbers: list[str] = [""] * len(lines)
    for i in explicit:
        new_numbers[i] = lines[i].n
    # Number the lines between consecutive anchors. When the count of lines equals the count of
    # free numbers, count; otherwise let the treebank's citations decide which numbers are
    # skipped (lyric numbering) or shared (short lines), keeping the sequence monotonic.
    bounds = [-1] + explicit + [len(lines)]
    for a, b in zip(bounds, bounds[1:]):
        lo = n_int(new_numbers[a]) if a >= 0 else 0
        hi = n_int(new_numbers[b]) if b < len(lines) else 10**9
        if b < len(lines) and re.search(r"[a-z]$", new_numbers[b]):
            hi += 1  # an anchor like 161b leaves room for a plain 161 before it
        idxs = list(range(a + 1, b))
        free = hi - lo - 1
        if not idxs:
            continue
        if len(idxs) == free or hi == 10**9 and all(vote_for(i) is None for i in idxs):
            for k, i in enumerate(idxs):
                new_numbers[i] = str(lo + 1 + k)
            continue
        prev = lo
        for pos, i in enumerate(idxs):
            remaining = len(idxs) - pos  # lines still to number, this one included
            vote = vote_for(i)
            v = n_int(vote) if vote else None
            if v is not None and prev < v < hi and (hi - v) >= 1 and (v + remaining - 1) < hi + remaining:
                n = vote
            elif prev + 1 < hi:
                n = str(prev + 1)
            else:
                n = str(prev)
                warnings.append(f"line {lines[i].n}: shares number {prev} (no room before {hi})")
            new_numbers[i] = n
            prev = n_int(n)
    # letter suffixes for lines sharing a number
    seen: dict[str, int] = {}
    final: list[str] = []
    explicit_set = set(explicit)
    for idx, n in enumerate(new_numbers):
        base = re.match(r"^\d+", n).group()
        count = seen.get(base, 0)
        if idx in explicit_set:
            final.append(n)  # keep the file's own label, e.g. 161b
        else:
            final.append(base if count == 0 else base + "abcdefgh"[count - 1])
        seen[base] = count + 1
    for line, n in zip(lines, final):
        line.n = n
    return warnings


# Names for the top-level sections (Perseus marks them only as episode/choral), in order.
ANTIGONE_SECTIONS = [
    "Prologue", "Parodos", "First episode", "First stasimon", "Second episode", "Second stasimon",
    "Third episode", "Third stasimon", "Kommos", "Fourth episode", "Fourth stasimon",
    "Fifth episode", "Fifth stasimon", "Exodos", "Kommos", "Exodos (continued)",
]


def label_sections(doc: Document, names: list[str]) -> None:
    tops = [i for i in doc.items if isinstance(i, Section) and i.level == 1]
    if len(tops) != len(names):
        print(f"  warning: {len(tops)} top-level sections but {len(names)} names; labels not applied", file=sys.stderr)
        return
    for sec, name in zip(tops, names):
        sec.label = name
