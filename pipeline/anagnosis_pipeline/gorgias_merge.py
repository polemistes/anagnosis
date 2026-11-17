"""Burnet's Gorgias from the checked transcription (pipeline/transcriptions/gorgias/).

check_batch() checks one batch file: format, numbering, apparatus numbers, and every difference in
wording from the Perseus text (the draft is the Perseus text, so each difference is a change made
on checking). merge() writes texts/gorgias/: the text, the apparatus, GLAUx's annotation aligned
to Burnet's lines, Jowett and Lodge.
"""
from __future__ import annotations

import difflib
import json
import re
import unicodedata
from pathlib import Path

from . import greek
from .linenum import SECTIONS, STEPHANUS
from .symposium_merge import ITEM_N, _follows, _key, read_batches, read_glaux

GREEK_META = {
    "title": "Γοργίας",
    "author": "Πλάτων",
    "lang": "grc",
    "source": "Platonis Opera, recognovit brevique adnotatione critica instruxit Ioannes Burnet, tomus III, Oxford; read from the Internet Archive scan platonisopera03platuoft by OCR, matched line by line to the Perseus Digital Library text (tlg0059.tlg023.perseus-grc2), and checked against the scan where the two disagreed",
    "edition": "Platonis Opera III, ed. J. Burnet, Oxford 1903",
    "license": "CC BY-SA 4.0 (transcription; the edition is in the public domain)",
    "layout": "prose",
    "syntax": "automatic",
    "dashes": "closed",
}
APPARATUS_META = {
    "title": "Critical apparatus (J. Burnet)",
    "author": "John Burnet",
    "lang": "lat",
    "source": "Platonis Opera III, ed. J. Burnet, Oxford 1903; transcribed from the Internet Archive scan platonisopera03platuoft",
    "license": "CC BY-SA 4.0 (transcription; the edition is in the public domain)",
}
GLAUX = "glaux/0059-023.xml"
# GLAUx lemmas that are wrong or spelled otherwise than the dictionaries' headwords
LEMMA_FIXES = {
    # a slip of the lemma: πρώην in the Ionic spelling (the enclitic νυν keeps its own lemma νύν, set by
    # hand)
    "πρῴην": "πρώην",
    "ἁσθιͅω": "ᾄδω", "κατέρδω": "καθείργνυμι", "διαβιάω": "διαβιόω", "διαπορρήγνυμι": "διαπράσσω",
    "προσαπολόω": "προσαπόλλυμι", "ἐπιτηδευτέος": "ἐπιτηδευτέον", "ἐγχειρίδιον": "ἐγχειρίδιος",
    "ἀμφιαμφισβητέω": "ἀμφισβητέω", "οπροῗδα": "πρόοιδα", "ἐπανεράομαι": "ἐπανέρομαι", "κατοράω": "καθοράω",
    "ὀψοποιϊκός": "ὀψοποιικός", "μιμνῄσκω": "μιμνήσκω", "ἀναμιμνῄσκω": "ἀναμιμνήσκω", "ὅπῃ": "ὅπη",
    "ἀνδριαντοποιία": "ἀνδριαντοποιΐα", "νυν": "νύν", "Ἀλκέτας": "Ἀλκέτης", "Κλεοπάτρη": "Κλεοπάτρα",
    "Σκέλλιος": "Σκελλίας", "Κλείνιος": "Κλεινίας", "Μέλητος": "Μέλης", "ᾁδω": "ᾄδω", "ᾁσμα": "ᾆσμα",
    "ὑπομιμνῄσκω": "ὑπομιμνήσκω", "κατάσσω": "κατάγνυμι", "παντοδαπής": "παντοδαπός", "αἰνίζω": "αἰνίσσομαι",
    "διανοέω": "διανοέομαι", "Σήραμβος": "Σάραμβος", "ἀιδής": "ἀϊδής", "Ἡρακλέης": "Ἡρακλῆς",
    "φιλονεικέω": "φιλονικέω", "Αἰγίνη": "Αἴγινα",
}
# words GLAUx misreads, by "line form": (lemma, tag)
HAND_ANALYSES = {
    "522e8 πέρανον": ("περαίνω", "v2sama---"),  # "finish!", taken for an indicative of a verb περιάνω
    "479a7 διαπράξαιτο": ("διαπράσσω", "v3saom---"),
}


def _skel(s: str) -> str:
    return greek.strip_diacritics(s).replace("ς", "σ").lower()


def _perseus_by_section(sources: Path) -> dict[str, list[str]]:
    from .gorgias_pages import perseus_tokens

    out: dict[str, list[str]] = {}
    for t in perseus_tokens(sources):
        if t["label"]:
            continue
        for w, _s, _e in greek.words(t["t"]):
            out.setdefault(t["sec"], []).append(_skel(w))
    return out


def check_batch(path: Path, pages_dir: Path, sources: Path) -> list[str]:
    import tempfile

    out: list[str] = []
    with tempfile.TemporaryDirectory() as tmp:
        (Path(tmp) / "batch-x.md").write_text(path.read_text(encoding="utf-8"), encoding="utf-8")
        pages = read_batches(Path(tmp))
    index = {p["stem"]: p for p in json.loads((pages_dir / "pages.json").read_text(encoding="utf-8"))}
    prev = None
    words: list[tuple[str, str, str]] = []
    for stem, block in pages.items():
        for e in block.get("errors", []):
            out.append(f"{stem}: {e}")
        if stem not in index:
            out.append(f"{stem}: unknown page")
            continue
        numbers: set[str] = set()
        lines = [(n, t) for n, t in block["text"] if n != "¶"]
        if abs(len(lines) - index[stem]["lines"]) > 2:
            out.append(f"{stem}: {len(lines)} lines, the draft had {index[stem]['lines']}")
        if not block["apparatus"] and index[stem]["lines"]:
            out.append(f"{stem}: no apparatus")
        for n, text in lines:
            numbers.add(n)
            if text != unicodedata.normalize("NFC", text):
                out.append(f"{stem} {n}: not NFC")
            if re.search(r"[᾽']", text) or re.search(r"[Ͱ-Ͽἀ-῿]’", text):
                out.append(f"{stem} {n}: elision written other than ʼ")
            if re.search(r"\w-\s*$", text):
                out.append(f"{stem} {n}: a divided word? write it whole on the line where it begins")
            for label in re.findall(r"\{([^}]*)\}", text):
                if not re.fullmatch(r"[Α-ΩΆ-Ώ]+\.", label):
                    out.append(f"{stem} {n}: odd speaker label {{{label}}}")
            cur = _key(n)
            if cur is None:
                out.append(f"{stem}: bad number {n!r}")
                continue
            if prev is not None and not _follows(prev, cur):
                out.append(f"{stem}: {n} follows {prev[0]}{SECTIONS[prev[1]]}{prev[2]}")
            prev = cur
            for w, _s, _e in greek.words(re.sub(r"\{[^}]*\}", " ", text)):
                words.append((_skel(w), w, n))
        for n, item in block["apparatus"]:
            m = ITEM_N.match(n)
            if not m:
                out.append(f"{stem}: bad apparatus number {n!r}")
                continue
            first = f"{m.group(1)}{m.group(2)}{m.group(3)}"
            if first not in numbers:
                out.append(f"{stem}: apparatus {n} names a line not on this page")
            if re.search(r"\s[:;]", item):
                out.append(f"{stem} {n}: a space before a colon or semicolon")
    by_sec = _perseus_by_section(sources)
    secs = []
    for _sk, _w, n in words:
        m = STEPHANUS.match(n)
        s = f"{m.group(1)}{m.group(2)}"
        if not secs or secs[-1] != s:
            secs.append(s)
    pw: list[str] = []
    for s in secs:
        pw.extend(by_sec.get(s, []))
    ours = [w[0] for w in words]
    sm = difflib.SequenceMatcher(None, ours, pw, autojunk=False)
    for op, a0, a1, b0, b1 in sm.get_opcodes():
        if op == "equal":
            continue
        if op == "insert" and (a0 == 0 or a0 == len(ours)):
            continue  # the batch begins or ends inside a section
        where = words[a0][2] if a0 < len(words) else words[-1][2]
        mine = " ".join(w[1] for w in words[a0:a1]) or "(nothing)"
        theirs = " ".join(pw[b0:b1]) or "(nothing)"
        out.append(f"{where}: written {mine} | Perseus has {theirs}")
    return out


# ---------------------------------------------------------------- merge

def merge(transcriptions: Path, pages_dir: Path, texts: Path, sources: Path, lexicon: Path, build: Path) -> int:
    from .gorgias import JOWETT_META, import_lodge, jowett_paragraphs
    from .import_perseus import write_syntax_nodes, write_tokens
    from .odyssey import align, fix_lemma, syntax_nodes
    from .odyssey_merge import Analyser, Frequencies, choose_analysis
    from .symposium import jowett_segments
    from .symposium_merge import _lines
    from .textfmt import Document, Line

    pages = read_batches(transcriptions)
    index = json.loads((pages_dir / "pages.json").read_text(encoding="utf-8"))
    lines, para, problems = _lines(pages, index)
    out = texts / "gorgias"
    out.mkdir(parents=True, exist_ok=True)

    txt = [f"# {k}: {v}" for k, v in GREEK_META.items()] + [""]
    for n, text in lines:
        if n in para:
            txt.append("@ ")
        txt.append(f"{n}\t{text}")
    (out / "grc.txt").write_text("\n".join(txt) + "\n", encoding="utf-8")
    print(f"wrote {out / 'grc.txt'}: {len(lines)} lines, {len(para)} paragraphs, from {len(pages)} pages")

    notes: list[tuple[str, list[str]]] = []
    for p in index:
        block = pages.get(p["stem"])
        if block is None:
            continue
        for n, item in block["apparatus"]:
            m = ITEM_N.match(n)
            if not m:
                problems.append(f"{p['stem']}: bad apparatus number {n!r}")
                continue
            page, letter, line, _el, end_letter, end_n = m.groups()
            heading = f"{page}{letter}{line}"
            if end_n:
                heading += f"-{page}{end_letter or letter}{end_n}"
            if notes and notes[-1][0] == heading:
                notes[-1][1].append(item)
            else:
                notes.append((heading, [item]))
    md = [f"# {k}: {v}" for k, v in APPARATUS_META.items()] + [""]
    for heading, items in notes:
        md.append(f"## {heading}")
        # every asterisk of the apparatus is Burnet's sign for an erased letter and is printed:
        # it is written \* so that two in one item cannot become italics (build.md_to_html)
        md.append("\n\n".join(items).replace("*", "\\*"))
        md.append("")
    (out / "commentary-burnet-apparatus.md").write_text("\n".join(md) + "\n", encoding="utf-8")
    print(f"wrote {out / 'commentary-burnet-apparatus.md'}: {len(notes)} notes, {sum(len(i) for _, i in notes)} items")

    # GLAUx, aligned to Burnet's lines; words it lacks get the analyser's analysis
    doc = Document(items=[Line(n=n, text=text) for n, text in lines])
    tb = read_glaux(sources / GLAUX)
    rows, _warnings = align(doc, tb, keep_tb_form=True)
    analyse = Analyser(lexicon)
    freq = Frequencies(sources / "treebanks")
    review = []
    for r in rows:
        tb_form = r.pop("tb_form", "")
        same = tb_form and _skel(tb_form) == _skel(r["form"])
        if r["lemma"] and r["postag"] and same:
            continue
        if r["lemma"] and r["postag"] and not tb_form:
            continue
        chosen = choose_analysis(r["form"], analyse(r["form"]), r["postag"], r["lemma"], freq, tb_form)
        reason = ("GLAUx leaves it without lemma or parse" if same
                  else f"reads {r['form']} where GLAUx has {tb_form}" if tb_form
                  else "a word GLAUx splits" if "+" in r["word_id"] else "not in GLAUx")
        if chosen is not None:
            r["lemma"], r["postag"] = fix_lemma(chosen[0]), chosen[1]
        review.append({"line": r["line"], "form": r["form"], "lemma": r["lemma"], "postag": r["postag"], "reason": reason})
    for r in rows:
        hand = HAND_ANALYSES.get(f"{r['line']} {r['form']}")
        if hand:
            r["lemma"], r["postag"] = hand
        r["lemma"] = LEMMA_FIXES.get(r["lemma"], r["lemma"])
    write_tokens(out / "tokens.tsv", rows)
    used = {(r["sentence"], w) for r in rows for w in r["word_id"].split("+") if r["sentence"]}
    write_syntax_nodes(out / "syntax-nodes.tsv", syntax_nodes(tb, used))
    missing = sum(1 for r in rows if not r["lemma"])
    print(f"wrote {out / 'tokens.tsv'}: {len(rows)} words, {missing} without lemma; {len(review)} for review")
    with (build / "gorgias-review.tsv").open("w", encoding="utf-8") as f:
        f.write("line\tform\tlemma\tpostag\treason\n")
        for r in review:
            f.write(f"{r['line']}\t{r['form']}\t{r['lemma']}\t{r['postag']}\t{r['reason']}\n")

    # Jowett, Lodge
    segs = jowett_segments(jowett_paragraphs(sources), lines, para)
    eng = [f"# {k}: {v}" for k, v in JOWETT_META.items()] + [""]
    for n, text, starts in segs:
        if starts:
            eng.append("@ ")
        eng.append(f"{n}\t{text}")
    (out / "eng-jowett.txt").write_text("\n".join(eng) + "\n", encoding="utf-8")
    print(f"wrote {out / 'eng-jowett.txt'}: {len(segs)} segments")
    n_notes, lost = import_lodge(sources / "gorgias-lodge-commentary.xml", lines, out / "commentary-lodge.md")
    print(f"wrote {out / 'commentary-lodge.md'}: {n_notes} notes ({lost} lemmas not found in Burnet's text: filed under their section)")

    from .lodge_intro import assemble as lodge_introduction

    n_pages = lodge_introduction(transcriptions.parent / "gorgias-lodge-intro", out / "introduction.md")
    print(f"wrote {out / 'introduction.md'}: Lodge's preface and introduction from {n_pages} pages")

    # the record of the text the trees were made on (syntax_text.py): from the files just written
    # (nothing for a text whose trees were made on the very text printed)
    from . import syntax_text

    problems += syntax_text.after_merge("gorgias", texts, sources, lexicon)

    log = build / "gorgias-merge.log"
    log.write_text("\n".join(problems) + "\n", encoding="utf-8")
    print(f"{len(problems)} problems ({log}); review list in {build / 'gorgias-review.tsv'}")
    return len(problems)
