"""Burnet's Symposium from the page-by-page transcription (pipeline/transcriptions/symposium/).

read_batches() reads the batch files; check_batch() checks one batch against the Perseus text
of Burnet's edition (which has his words but not his lines) and the OCR drafts.
"""
from __future__ import annotations

import difflib
import json
import re
import unicodedata
from pathlib import Path

from . import greek
from .linenum import STEPHANUS, SECTIONS

ITEM_N = re.compile(r"^(\d+)([a-e])(\d+)(?:-(?:(\d+)([a-e]))?(\d+))?$")


def read_batches(directory: Path) -> dict[str, dict]:
    """Page blocks by stem: {'text': [(n, line)], 'apparatus': [(n, item)], 'notes': [str], 'batch': name}.
    A '¶' line (a new paragraph) is kept in the text as ('¶', '')."""
    pages: dict[str, dict] = {}
    for path in sorted(directory.glob("batch-*.md")):
        stem, section = None, None
        for raw in path.read_text(encoding="utf-8").splitlines():
            m = re.match(r"^=== (s-\d{4})\s*$", raw)
            if m:
                stem = m.group(1)
                pages[stem] = {"text": [], "apparatus": [], "notes": [], "batch": path.name}
                section = None
                continue
            m = re.match(r"^--- (text|apparatus|notes)\s*$", raw)
            if m:
                section = m.group(1)
                continue
            if stem is None or section is None or not raw.strip():
                continue
            if section == "notes":
                pages[stem]["notes"].append(raw.strip())
                continue
            if section == "text" and raw.strip() == "¶":
                pages[stem]["text"].append(("¶", ""))
                continue
            n, sep, body = raw.partition("\t")
            if not sep:
                pages[stem].setdefault("errors", []).append(f"no TAB: {raw[:60]!r}")
                continue
            pages[stem][section].append((n.strip(), unicodedata.normalize("NFC", body.strip())))
    return pages


def _skel(s: str) -> str:
    return greek.strip_diacritics(s).replace("ς", "σ").lower()


def _words(text: str) -> list[str]:
    text = re.sub(r"\{[^}]*\}", " ", text)
    return [_skel(w) for w, _s, _e in greek.words(text)]


def perseus_sections(pages_dir: Path, sources: Path) -> list[tuple[str, str]]:
    cache = pages_dir / "perseus-sections.json"
    if cache.exists():
        return [tuple(x) for x in json.loads(cache.read_text(encoding="utf-8"))]
    from .symposium_pages import perseus_sections as read

    sections = read(sources)
    cache.write_text(json.dumps(sections, ensure_ascii=False), encoding="utf-8")
    return sections


def _key(n: str) -> tuple[int, int, int] | None:
    m = STEPHANUS.match(n)
    return (int(m.group(1)), SECTIONS.index(m.group(2)), int(m.group(3))) if m else None


def _follows(prev: tuple[int, int, int], cur: tuple[int, int, int]) -> bool:
    """Whether line cur may follow line prev: the next line, the first line of the next section,
    or the first line of the next Stephanus page."""
    return (cur == (prev[0], prev[1], prev[2] + 1) or cur == (prev[0], prev[1] + 1, 1)
            or cur == (prev[0] + 1, 0, 1))


def check_batch(path: Path, pages_dir: Path, sources: Path) -> list[str]:
    """Problems in one batch file: format, numbering, line counts against the OCR, apparatus
    numbers, and differences in wording from the Perseus text of the sections the batch covers."""
    import tempfile

    out: list[str] = []
    with tempfile.TemporaryDirectory() as tmp:
        (Path(tmp) / "batch-x.md").write_text(path.read_text(encoding="utf-8"), encoding="utf-8")
        pages = read_batches(Path(tmp))
    index = {p["stem"]: p for p in json.loads((pages_dir / "pages.json").read_text(encoding="utf-8"))}
    prev = None
    words: list[tuple[str, str, str]] = []  # (skeleton, word as written, line number)
    numbers: set[str] = set()
    for stem, block in pages.items():
        for e in block.get("errors", []):
            out.append(f"{stem}: {e}")
        if stem not in index:
            out.append(f"{stem}: unknown page")
            continue
        lines = [(n, t) for n, t in block["text"] if n != "¶"]
        draft_n = index[stem]["lines"]
        if abs(len(lines) - draft_n) > 2:
            out.append(f"{stem}: {len(lines)} lines, the OCR has {draft_n}")
        if not block["apparatus"]:
            out.append(f"{stem}: no apparatus")
        for n, text in lines:
            numbers.add(n)
            if text != unicodedata.normalize("NFC", text):
                out.append(f"{stem} {n}: not NFC")
            if re.search(r"['᾽]", text) or re.search(r"[Ͱ-Ͽἀ-῿]’", text):
                out.append(f"{stem} {n}: elision written other than ʼ")
            if re.search(r"(?<!\w)-|-$", text) or re.search(r"\w-\s*$", text):
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
    # the wording against Perseus, over the sections the batch covers
    sections = perseus_sections(pages_dir, sources)
    keys = [STEPHANUS.match(w[2]) for w in words]
    secs = {f"{m.group(1)}{m.group(2)}" for m in keys if m}
    pw: list[str] = []
    for sec, text in sections:
        if sec in secs:
            pw.extend(_words(text))
    ours = [w[0] for w in words]
    sm = difflib.SequenceMatcher(None, ours, pw, autojunk=False)
    for op, a0, a1, b0, b1 in sm.get_opcodes():
        if op == "equal":
            continue
        if op == "insert" and (a0 == 0 or a0 == len(ours)):
            continue  # the batch begins or ends inside a section
        where = words[a0][2] if a0 < len(words) else words[-1][2]
        if op == "replace" and a1 - a0 == b1 - b0 == 1 and words[a0][1][:1].isupper():
            continue  # a capital may differ only in its accent or breathing mark
        mine = " ".join(w[1] for w in words[a0:a1]) or "(nothing)"
        theirs = " ".join(pw[b0:b1]) or "(nothing)"
        out.append(f"{where}: written {mine!s} | Perseus has {theirs}")
    return out


# ---------------------------------------------------------------- merge

GREEK_META = {
    "title": "Συμπόσιον",
    "author": "Πλάτων",
    "lang": "grc",
    "source": "Platonis Opera, recognovit brevique adnotatione critica instruxit Ioannes Burnet, tomus II, Oxford; transcribed from the Internet Archive scans platonisopera02platuoft (with operarecognovitb02platuoft, the 1910 printing) and checked against the Perseus Digital Library text (tlg0059.tlg011.perseus-grc2)",
    "edition": "Platonis Opera II, ed. J. Burnet, Oxford 1901 (corrected printing 1910)",
    "license": "CC BY-SA 4.0 (transcription; the edition is in the public domain)",
    "layout": "prose",
    "syntax": "automatic",
}
APPARATUS_META = {
    "title": "Critical apparatus (J. Burnet)",
    "author": "John Burnet",
    "lang": "lat",
    "source": "Platonis Opera II, ed. J. Burnet, Oxford; transcribed from the Internet Archive scan platonisopera02platuoft",
    "license": "CC BY-SA 4.0 (transcription; the edition is in the public domain)",
}
GLAUX = "glaux/0059-011.xml"
# GLAUx lemmas that are wrong or spelled otherwise than the dictionaries' headwords
LEMMA_FIXES = {
    "κατοράω": "καθοράω", "σι—ληνός": "Σιληνός", "μοῦσαι": "Μοῦσα", "μεταπέμπομαι": "μεταπέμπω",
    "Φαῖδρας": "Φαῖδρος", "ἔπιπνος": "ἐπίπνοος", "πταίρω%": "πταίρω", "ὄον": "ὄα",
    "καταδεδαρθάω": "καταδαρθάνω", "λίσπη": "λίσπος", "πός": "πότερος", "ᾀζω": "ᾄδω",
    "ἀνέζομαι": "ἀνίημι", "φύζω": "φύω", "ἐγχύνω": "ἐγχέω", "διανοέω": "διανοέομαι",
    "ᾁδω": "ᾄδω", "Μαντινέη": "Μαντινικός",
}
# words GLAUx misreads, by "line form": (lemma, tag)
HAND_ANALYSES = {
    "207c2 Διανοῇ": ("διανοέομαι", "v2spie---"),  # "you think", taken for a noun
    "213b4 Ὑπολύετε": ("ὑπολύω", "v2ppma---"),  # "take off (his shoes)", taken for a name
    "217c2 περανῶν": ("περαίνω", "v-sfpamn-"),
}


def read_glaux(path: Path) -> list[dict]:
    """GLAUx's words in the order of the text, in the shape odyssey.read_treebank gives: ids made
    local to the sentence (1, 2, ...), heads likewise, 0 for the root."""
    from lxml import etree

    out = []
    for sent in etree.parse(str(path)).iter("sentence"):
        words = list(sent.iter("word"))
        local = {w.get("id"): str(k + 1) for k, w in enumerate(words)}
        sid = sent.get("struct_id") or sent.get("id")
        for w in words:
            # GLAUx writes the second piece of a word it splits with a hyphen (οὔ, -τε) and
            # elision with ’
            form = greek.nfc(w.get("form", "")).replace("’", greek.APOSTROPHE)
            if len(form) > 1 and form.startswith("-"):
                form = form[1:]
            if greek.is_word(form):
                form = re.sub(r"^[;·.,]+", "", form)  # a stop glued to the word (;τί)
            artificial = bool(w.get("artificial"))
            head = w.get("head", "")
            out.append({
                "sentence": sid,
                "word_id": local[w.get("id")],
                "form": form,
                "lemma": re.sub(r"^[;·.,]+(?=\w)", "", greek.nfc(w.get("lemma", ""))),
                "postag": w.get("postag", ""),
                "head": "0" if head in ("0", "") else local.get(head, "0"),
                "relation": w.get("relation", ""),
                "cite": w.get("div_stephanus_section", ""),
                "artificial": artificial,
                "is_word": not artificial and greek.is_word(form),
            })
    return out


def _lines(pages: dict[str, dict], index: list[dict]) -> tuple[list[tuple[str, str]], set[str], list[str]]:
    """Burnet's lines in order, the lines that begin a paragraph, and problems."""
    lines: list[tuple[str, str]] = []
    para: set[str] = set()
    problems: list[str] = []
    pending = True  # the dialogue begins a paragraph
    seen: set[str] = set()
    for p in index:
        block = pages.get(p["stem"])
        if block is None:
            problems.append(f"{p['stem']}: not transcribed")
            continue
        for n, text in block["text"]:
            if n == "¶":
                pending = True
                continue
            if n in seen:
                problems.append(f"{p['stem']}: {n} twice")
                continue
            seen.add(n)
            lines.append((n, text))
            if pending:
                para.add(n)
                pending = False
    return lines, para, problems


def merge(transcriptions: Path, pages_dir: Path, texts: Path, sources: Path, lexicon: Path, build: Path) -> int:
    from .import_perseus import write_syntax_nodes, write_tokens
    from .odyssey import align, fix_lemma, syntax_nodes
    from .odyssey_merge import Analyser, Frequencies, choose_analysis
    from .symposium import import_bury, import_bury_introduction, jowett_paragraphs, jowett_segments
    from .textfmt import Document, Line

    pages = read_batches(transcriptions)
    index = json.loads((pages_dir / "pages.json").read_text(encoding="utf-8"))
    lines, para, problems = _lines(pages, index)
    out = texts / "symposium"
    out.mkdir(parents=True, exist_ok=True)

    # --- the text: '@ ' (no speaker) before a line that begins a paragraph
    txt = [f"# {k}: {v}" for k, v in GREEK_META.items()] + [""]
    for n, text in lines:
        if n in para:
            txt.append("@ ")
        txt.append(f"{n}\t{text}")
    (out / "grc.txt").write_text("\n".join(txt) + "\n", encoding="utf-8")
    print(f"wrote {out / 'grc.txt'}: {len(lines)} lines, {len(para)} paragraphs, from {len(pages)} pages")

    # --- the apparatus
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
            page, letter, line, end_line, end_letter, end_n = m.groups()
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
        md.append("\n\n".join(items))
        md.append("")
    (out / "commentary-burnet-apparatus.md").write_text("\n".join(md) + "\n", encoding="utf-8")
    print(f"wrote {out / 'commentary-burnet-apparatus.md'}: {len(notes)} notes, {sum(len(i) for _, i in notes)} items")

    # --- GLAUx, aligned to Burnet's lines; words it lacks get the analyser's analysis
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
            continue  # a word GLAUx splits in two, annotated from its parts
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
    nodes = syntax_nodes(tb, used)
    write_syntax_nodes(out / "syntax-nodes.tsv", nodes)
    missing = sum(1 for r in rows if not r["lemma"])
    print(f"wrote {out / 'tokens.tsv'}: {len(rows)} words, {missing} without lemma; {len(review)} for review")
    with (build / "symposium-review.tsv").open("w", encoding="utf-8") as f:
        f.write("line\tform\tlemma\tpostag\treason\n")
        for r in review:
            f.write(f"{r['line']}\t{r['form']}\t{r['lemma']}\t{r['postag']}\t{r['reason']}\n")

    # --- Jowett, Bury
    from .symposium import JOWETT_META

    segs = jowett_segments(jowett_paragraphs(sources), lines)
    eng = [f"# {k}: {v}" for k, v in JOWETT_META.items()] + [""]
    for n, text, starts in segs:
        if starts:
            eng.append("@ ")
        eng.append(f"{n}\t{text}")
    (out / "eng-jowett.txt").write_text("\n".join(eng) + "\n", encoding="utf-8")
    print(f"wrote {out / 'eng-jowett.txt'}: {len(segs)} segments")
    n_notes, lost = import_bury(sources / "symposium-bury-commentary.xml", lines, out / "commentary-bury.md")
    print(f"wrote {out / 'commentary-bury.md'}: {n_notes} notes ({lost} lemmas not found in Burnet's text: filed under their section)")
    n_heads = import_bury_introduction(sources / "symposium-bury-commentary.xml", out / "introduction.md")
    print(f"wrote {out / 'introduction.md'}: {n_heads} headings")

    log = build / "symposium-merge.log"
    log.write_text("\n".join(problems) + "\n", encoding="utf-8")
    print(f"{len(problems)} problems ({log}); review list in {build / 'symposium-review.tsv'}")
    return len(problems)
