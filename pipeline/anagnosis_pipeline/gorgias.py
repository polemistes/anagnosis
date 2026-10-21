"""Plato's Gorgias: Jowett's translation and Lodge's commentary, fitted to Burnet's lines
(texts/gorgias/grc.txt, from the transcription).

Jowett: the Wikisource text "Gorgias (Jowett)" is the third edition's (The Dialogues of Plato,
1892, vol. II; its wording agrees with the 1892 scan), with the Stephanus pages marked by
{{verse}} templates for 447-500 and 523-524 only. The other pages are placed from the 1892 scan
(Internet Archive b24750189_0002), whose margin prints them: the words beside each margin number
are found in the Wikisource text. A page the scan's OCR lost is placed in proportion between its
neighbours. Within a page the text is cut as for the Symposium (symposium.jowett_segments).

Lodge: Gonzalez Lodge, Plato, Gorgias (Boston: Ginn, 1891), the commentary from Perseus
(lodge.plat.gorg_eng.xml, CC BY-SA 3.0 US), notes filed by section and placed on a line by
their lemma, as Bury's on the Symposium.
"""
from __future__ import annotations

import difflib
import re
from collections import defaultdict
from pathlib import Path

from . import greek
from .symposium import _bury_md, _clean_md, _locate, _sec_ord, _skel, section_of, _wiki_to_text

JOWETT_META = {
    "title": "Gorgias",
    "translator": "Benjamin Jowett",
    "lang": "eng",
    "source": "Wikisource, Gorgias (Jowett), the text of The Dialogues of Plato, third edition, vol. II; Stephanus pages missing there placed from the 1892 scan (Internet Archive b24750189_0002)",
    "edition": "The Dialogues of Plato, translated by B. Jowett, third edition, Oxford, 1892",
    "license": "Public domain (Jowett died 1893); Wikisource transcription CC BY-SA 4.0",
}
LODGE_META = {
    "title": "Commentary on the Gorgias",
    "author": "Gonzalez Lodge",
    "lang": "eng",
    "source": "Perseus Digital Library, lodge.plat.gorg_eng.xml: Plato, Gorgias, edited on the basis of Deuschle-Cron's edition by Gonzalez Lodge, Boston: Ginn & Company, 1891",
    "license": "CC BY-SA 3.0 US",
}

FIRST_PAGE, LAST_PAGE = 447, 527


# ---------------------------------------------------------------- Jowett

def _words(s: str) -> list[str]:
    return re.findall(r"[a-z]+", s.lower())


def _scan_marks(scan_text: str) -> dict[int, list[str]]:
    """Stephanus pages in the margin of the 1892 scan's OCR, with the words of the line they
    stand beside: {page: words}. A number begins or ends the line it stands beside."""
    start = scan_text.find("late  for  a")
    if start < 0:
        start = scan_text.find("late for a")
    end = scan_text.find("Plato are the following", start)
    body = scan_text[start - 400 : end if end > 0 else None]
    marks: dict[int, list[str]] = {}
    for line in body.splitlines():
        line = line.strip()
        m = re.match(r"^(\d{3})\s+(.*)$", line) or re.match(r"^(.*?)\s+(\d{3})$", line)
        if not m:
            continue
        num, words = (m.group(1), m.group(2)) if m.group(1).isdigit() else (m.group(2), m.group(1))
        n = int(num)
        if FIRST_PAGE <= n <= LAST_PAGE and n not in marks:
            w = _words(words)
            if len(w) >= 4:
                marks[n] = w[:10]
    return marks


def jowett_paragraphs(sources: Path) -> list[str]:
    """Jowett's Gorgias as paragraphs (a speech each), with Stephanus page marks written ⟦447⟧."""
    raw = (sources / "jowett" / "gorgias.wiki").read_text(encoding="utf-8")
    raw = raw[raw.index("{{verse|chapter=Gorgias|verse=447}}") :]
    raw = raw[: raw.index("==Notes==")] if "==Notes==" in raw else raw
    raw = re.sub(r"\{\{verse\|chapter=Gorgias\|verse=(\d+)\}\}", r" ⟦\1⟧ ", raw)
    raw = re.sub(r"'''([A-Z][a-z]+)\.?'''\.?", r"\1.", raw)  # '''Callicles.''' -> Callicles.
    text = _wiki_to_text(raw)
    paras = [re.sub(r"\s+", " ", p).strip() for p in re.split(r"\n\s*\n", text)]
    paras = [p for p in paras if p]
    # the pages the Wikisource text lacks, from the scan
    have = {int(n) for p in paras for n in re.findall(r"⟦(\d{3})⟧", p)}
    marks = _scan_marks((sources / "jowett" / "gorgias-1892-scan.txt").read_text(encoding="utf-8"))
    flat: list[tuple[int, int, str]] = []  # (paragraph, offset, word) for every word
    for i, p in enumerate(paras):
        for m in re.finditer(r"[A-Za-z]+", p):
            flat.append((i, m.start(), m.group(0).lower()))
    words = [w for _i, _o, w in flat]
    placed: dict[int, int] = {}  # page -> index into flat
    from_scan: list[int] = []
    from_speech: list[int] = []
    # where the pages Wikisource marks fall
    for i, p in enumerate(paras):
        for m in re.finditer(r"⟦(\d{3})⟧", p):
            k = next((x for x, (pi, off, _w) in enumerate(flat) if pi == i and off >= m.end()), None)
            if k is not None:
                placed[int(m.group(1))] = k
    for page in range(FIRST_PAGE, LAST_PAGE + 1):
        if page in have or page not in marks:
            continue
        lo = max((placed[p] for p in placed if p < page), default=0)
        hi = min((placed[p] for p in placed if p > page), default=len(words))
        anchor = marks[page]
        best, best_k = 0.0, None
        for k in range(lo, max(lo, hi - len(anchor)) + 1):
            r = difflib.SequenceMatcher(None, anchor, words[k : k + len(anchor)], autojunk=False).ratio()
            if r > best:
                best, best_k = r, k
        if best_k is not None and best >= 0.6:
            placed[page] = best_k
            from_scan.append(page)
    # pages still missing: in the speech of Jowett's that answers to the Greek speech the page
    # begins in, in proportion within it
    by_speech = _speech_places(paras, sources)
    for page in range(FIRST_PAGE, LAST_PAGE + 1):
        if page in placed or page not in by_speech:
            continue
        i, frac = by_speech[page]
        ks = [x for x, (pi, _o, _w) in enumerate(flat) if pi == i]
        if ks:
            placed[page] = ks[min(len(ks) - 1, int(frac * len(ks)))]
            from_speech.append(page)
    # and if that fails, in proportion between their neighbours
    for page in range(FIRST_PAGE, LAST_PAGE + 1):
        if page in placed:
            continue
        before = max((p for p in placed if p < page), default=None)
        after = min((p for p in placed if p > page), default=None)
        if before is None:
            continue
        if after is None:  # the last pages: an average page's length on
            known = sorted(placed)
            avg = (placed[known[-1]] - placed[known[0]]) // max(1, known[-1] - known[0])
            placed[page] = min(len(words) - 1, placed[before] + avg * (page - before))
            continue
        span = after - before
        placed[page] = placed[before] + (placed[after] - placed[before]) * (page - before) // span
    # write the new marks into the paragraphs
    inserts: dict[int, list[tuple[int, int]]] = defaultdict(list)
    for page, k in placed.items():
        if page in have:
            continue
        i, off, _w = flat[k]
        inserts[i].append((off, page))
    for i, items in inserts.items():
        p = paras[i]
        for off, page in sorted(items, reverse=True):
            p = p[:off] + f"⟦{page}⟧ " + p[off:]
        paras[i] = p
    guessed = [p for p in range(FIRST_PAGE, LAST_PAGE + 1) if p not in have and p not in from_scan and p not in from_speech]
    print(f"Jowett: Stephanus pages from Wikisource {len(have)}, from the 1892 scan {sorted(from_scan)}, "
          f"by the speeches {sorted(from_speech)}, by proportion {guessed}")
    missing = [p for p in range(FIRST_PAGE, LAST_PAGE + 1) if not any(f"⟦{p}⟧" in q for q in paras)]
    if missing:
        raise SystemExit(f"Jowett: no place for Stephanus pages {missing}")
    return paras


SPEAKERS = {"Socrates": "ΣΩ", "Callicles": "ΚΑΛ", "Polus": "ΠΩΛ", "Gorgias": "ΓΟΡ", "Chaerephon": "ΧΑΙ"}


def _speech_places(paras: list[str], sources: Path) -> dict[int, tuple[int, float]]:
    """For each Stephanus page, Jowett's paragraph it begins in and how far into it, found by
    matching Jowett's speeches to the Greek ones (by speaker and length)."""
    import math

    from .gorgias_pages import perseus_tokens

    # Jowett's speeches: [speaker, [paragraph indexes], characters]
    js: list[list] = []
    for i, p in enumerate(paras):
        m = re.match(r"^(?:⟦\d{3}⟧\s*)?([A-Z][a-z]+)\.", p)
        if m and m.group(1) in SPEAKERS:
            js.append([SPEAKERS[m.group(1)], [i], len(p)])
        elif js:
            js[-1][1].append(i)
            js[-1][2] += len(p)
    # the Greek speeches: [speaker, first token, last token, characters]; a name Perseus repeats
    # for the same speaker does not begin a new speech
    toks = perseus_tokens(sources)
    gs: list[list] = []
    for k, t in enumerate(toks):
        if t["label"]:
            who = t["t"].strip("{}.")
            if gs and gs[-1][0] == who:
                continue
            gs.append([who, k, k, 0])
        elif gs:
            gs[-1][2] = k
            gs[-1][3] += len(t["t"]) + 1
    ratio = sum(x[2] for x in js) / max(1, sum(x[3] for x in gs))
    n, m = len(js), len(gs)
    NEG = -1e9
    score = [[NEG] * (m + 1) for _ in range(n + 1)]
    back = [[0] * (m + 1) for _ in range(n + 1)]
    score[0][0] = 0.0
    for i in range(n + 1):
        for j in range(m + 1):
            if i == 0 and j == 0:
                continue
            best, how = NEG, 0
            if i > 0 and j > 0:
                same = js[i - 1][0] == gs[j - 1][0]
                d = abs(math.log((js[i - 1][2] + 20) / (gs[j - 1][3] * ratio + 20)))
                v = score[i - 1][j - 1] + (2.0 - d if same else -3.0)
                if v > best:
                    best, how = v, 3
            if i > 0 and score[i - 1][j] - 1.5 > best:
                best, how = score[i - 1][j] - 1.5, 1
            if j > 0 and score[i][j - 1] - 1.5 > best:
                best, how = score[i][j - 1] - 1.5, 2
            score[i][j], back[i][j] = best, how
    pair: dict[int, int] = {}  # Greek speech -> Jowett speech
    i, j = n, m
    while i > 0 or j > 0:
        how = back[i][j]
        if how == 3:
            if js[i - 1][0] == gs[j - 1][0]:
                pair[j - 1] = i - 1
            i, j = i - 1, j - 1
        elif how == 1:
            i -= 1
        else:
            j -= 1
    out: dict[int, tuple[int, float]] = {}
    for k, t in enumerate(toks):
        if not (t["newsec"] and t["sec"].endswith("a")):
            continue
        page = int(t["sec"][:-1])
        g = next((x for x, sp in enumerate(gs) if sp[1] <= k <= sp[2]), None)
        if g is None or g not in pair:
            continue
        sp = gs[g]
        before = sum(len(toks[x]["t"]) + 1 for x in range(sp[1] + 1, k))
        frac = before / max(1, sp[3])
        jp = js[pair[g]]
        # the paragraph of the speech, and how far into it, by the speech's characters
        target = frac * jp[2]
        acc = 0
        for pi in jp[1]:
            if acc + len(paras[pi]) >= target:
                out[page] = (pi, (target - acc) / max(1, len(paras[pi])))
                break
            acc += len(paras[pi])
    return out


# ---------------------------------------------------------------- Lodge

def _word_sim(a: str, b: str) -> float:
    if a == b:
        return 1.0
    if a and b and (a.startswith(b) or b.startswith(a)) and min(len(a), len(b)) >= 1 and abs(len(a) - len(b)) <= 2:
        return 0.9  # elision: γʼ for γε, δʼ for δέ
    r = difflib.SequenceMatcher(None, a, b).ratio()
    return r if r >= 0.75 else 0.0


def _find(seq: list[str], skels: list[str], frm: int, hint: int) -> tuple[float, int] | None:
    """The best place for a run of words: (score per word, index), preferring places after the hint."""
    best = None
    for i in range(frm, len(skels) - len(seq) + 1):
        sc = sum(_word_sim(a, skels[i + k]) for k, a in enumerate(seq)) / len(seq)
        key = (sc, i >= hint, -abs(i - hint))
        if best is None or key > best[0]:
            best = (key, i)
    if best is None or best[0][0] < (0.8 if len(seq) == 1 else 0.6):
        return None
    return best[0][0], best[1]


def _locate_fuzzy(lemma: str, words: list[tuple[str, str]], hint: int) -> tuple[str, str, int] | None:
    """(first line, last line, index) of a lemma ("καὶ μάλα γʼ ἀστείας", "ἐὰν ... λέγῃς") among the
    words of a passage, by the best match of its words, allowing for elision and misprints."""
    parts = [p for p in re.split(r"\s*(?:\.\s*\.\s*\.|…|κτλ\.?)\s*", lemma) if p.strip()]
    if not parts:
        return None
    first = [_skel(w) for w, _s, _e in greek.words(parts[0])]
    last = [_skel(w) for w, _s, _e in greek.words(parts[-1])] if len(parts) > 1 else []
    if not first:
        return None
    skels = [w for w, _n in words]
    found = _find(first, skels, 0, hint)
    if found is None:
        return None
    i = found[1]
    end = i + len(first) - 1
    if last:
        f2 = _find(last, skels, i + len(first), i + len(first))
        if f2 is not None and f2[1] - i < 120:
            end = f2[1] + len(last) - 1
    return words[i][1], words[min(end, len(words) - 1)][1], i


def import_lodge(source: Path, lines: list[tuple[str, str]], out: Path) -> tuple[int, int]:
    """Lodge's commentary, each note under the line its lemma is on (the first line of its section
    where the lemma is not found). Returns (notes, notes not located)."""
    from .commentary import _md
    from .tei_p4 import load as load_p4

    root = load_p4(source)
    body = root.find(".//body")
    by_section: dict[str, list[tuple[str, str]]] = defaultdict(list)
    first_line: dict[str, str] = {}
    for n, text in lines:
        sec = section_of(n)
        first_line.setdefault(sec, n)
        for w, _s, _e in greek.words(re.sub(r"\{[^}]*\}", " ", text)):
            by_section[sec].append((_skel(w), n))
    sections = list(first_line)
    notes: list[list] = []
    lost = 0
    for div in body.iter("div1"):
        sec = (div.get("n") or "").lower()
        if sec not in first_line:
            earlier = [s for s in sections if _sec_ord(s) <= _sec_ord(sec)] if re.fullmatch(r"\d{3}[a-e]", sec) else []
            sec = earlier[-1] if earlier else sections[0]
        k = sections.index(sec)
        words = by_section[sec] + (by_section[sections[k + 1]] if k + 1 < len(sections) else [])
        hint = 0
        for p in div:
            if not isinstance(p.tag, str) or p.tag != "p":
                continue
            # links to other places in the Gorgias
            for bibl in list(p.iter("bibl")):
                m = re.match(r"^Plat\. Gorg\.\s*(\d{3})\s*([a-e])\b", bibl.get("n") or "", re.I)
                if m:
                    target = f"{m.group(1)}{m.group(2).lower()}1"
                    text = "".join(bibl.itertext()).strip()
                    for child in list(bibl):
                        bibl.remove(child)
                    bibl.tag = "seg"
                    bibl.attrib.clear()
                    bibl.text = f"⟦{target}|{text}⟧"
            lemma_el = p.find("lemma")
            starts_with_lemma = lemma_el is not None and not (p.text or "").strip()
            if starts_with_lemma and re.fullmatch(r"\s*\d+\s*", "".join(lemma_el.itertext())) \
                    and re.fullmatch(r"\s*f+\.?\s*", "".join(p.itertext())[len("".join(lemma_el.itertext())):]):
                continue  # "8 f.": a reference to the lines of Lodge's own text
            md = _bury_md(p)
            md = re.sub(r"⟦(\d{3}[a-e]1)\|([^⟧]*)⟧", r"[\2](#\1)", md)
            if not md or re.fullmatch(r"[IVXLC]+\.", md.strip()):
                continue  # Lodge's chapter numbers ("I.")
            md = re.sub(r"(?<=[\u0370-\u03ff\u1f00-\u1fff])'", "ʼ", md)  # elision in the Greek
            if starts_with_lemma:
                lemma = re.sub(r"[*\\]", "", _md(lemma_el, True)).strip()
                found = _locate_fuzzy(lemma, words, hint)
                if found is None:
                    lost += 1
                    # where the note before was, or the section's first line
                    heading = notes[-1][0].split("-")[0] if notes and section_of(notes[-1][0].split("-")[0]) == sec else first_line[sec]
                else:
                    a, b, hint = found
                    heading = a if a == b else f"{a}-{b}"
                notes.append([heading, [md]])
            elif notes and section_of(notes[-1][0].split("-")[0]) == sec:
                notes[-1][1].append(md)
            else:
                notes.append([first_line[sec], [md]])
    merged: list[list] = []
    for heading, body_ in notes:
        if merged and merged[-1][0] == heading:
            merged[-1][1].extend(body_)
        else:
            merged.append([heading, list(body_)])
    md_out = [f"# {k}: {v}" for k, v in LODGE_META.items()] + [""]
    for heading, body_ in merged:
        md_out.append(f"## {heading}")
        md_out.append("\n\n".join(body_))
        md_out.append("")
    out.write_text("\n".join(md_out) + "\n", encoding="utf-8")
    return len(merged), lost
