"""The plays' English pages by OCR: the editors' notes and introductions, and Starkie's
translation of the Clouds (pipeline/PLAN-drama.md, steps 6-7), by the route of the Expositor's
Greek Testament (egt_ocr.py): Tesseract with the English and Greek models, Greek words read again
with the Greek model, and every word the OCR doubts flagged for an agent to check against a crop.

    python -m anagnosis_pipeline drama-prose <play> notes|intro|trans|appendix fetch|ocr|draft

The draft of each page is written into the batch files pipeline/transcriptions/drama/<play>/
notes-NN.md, intro-NN.md, trans-NN.md or appendix-NN.md (eight pages each; a file that exists is
never overwritten) as a block

    === p-0250
    ## 779
    **ὁ δῆμος**: as if there was an ἐκκλησία in Hades.
    --- flags
    1 ἐκκλησία [greek] →
    --- notes

and the crops under pipeline/build/drama-prose/<play>/: p-0250-flags.png (the lines that hold a
flagged word, numbered, the word boxed), p-0250-col-l.png and -col-r.png (the columns; one
column: -col-l.png only). merge_kind() and merge_translation() read the checked batches for
drama.merge_play.

Jebb's Sophocles (layout "jebb"): the chapters before the text (kind intro) and the Appendix (kind
appendix) are full-width pages, the manuscripts chapter with notes in the outer margin; the draft
writes them as the briefs sophocles/INTRODUCTION.md and APPENDIX.md want (_jebb_markdown): the
margin note after the section's heading (`## § 3 — Scholia.`) or in italics at the start of its
paragraph, `# Manuscripts, editions, etc.`, `# The ancient argument`, `## The persons of the
drama` (the names in one line), `## Structure of the play`, the Appendix's notes headed
`## Line 15`, `## Lines 11–14`, `## Line 29 f.` with the lemma in bold; the section and line
numbers, which the OCR often garbles, are settled over the pages in order (_resolve_headings).
sophocles.write_prose (sophocles-prose) reads the checked batches.
"""
from __future__ import annotations

import json
import os
import re
import sys
import unicodedata
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from . import greek
from .drama import PLAYS, Play, bold_lemma, note_heading
from .drama_pages import fetch_leaf, route_dir, scan_dirs

ROOT = Path(__file__).resolve().parent.parent.parent
PIPELINE = ROOT / "pipeline"
PAGES_PER_BATCH = 8
KINDS = ("notes", "intro", "trans", "appendix")


# --- fetch and OCR -----------------------------------------------------------------------------

def ocr_leaf(scan: str, leaf: int) -> Path:
    from .egt_ocr import tesseract

    _, build = scan_dirs(scan)
    hocr = build / "hocr" / f"leaf_{leaf:04d}.eng.hocr"
    if hocr.exists():
        return hocr
    png = fetch_leaf(scan, leaf)
    part = build / "hocr" / f"leaf_{leaf:04d}.eng.part"
    tesseract(png, part, "eng+grc", 3)
    os.replace(str(part) + ".hocr", hocr)
    return hocr


def run(slug: str, kind: str, step: str, workers: int = 4) -> None:
    play = PLAYS[slug]
    sources = play.sources_for(kind)
    if not any(leaves for _scan, leaves in sources):
        raise SystemExit(f"{slug}: no {kind} leaves in drama.PLAYS yet (step 2)")
    if step == "draft":
        index = write_draft(slug, kind)
        print(f"{slug} {kind}: {len(index)} pages, {sum(p['flags'] for p in index)} flags")
        missing = [p["stem"] for p in index if p.get("no_rule")]
        if missing:
            print(f"{slug} {kind}: no rule found, nothing drafted (to be read from the image): {', '.join(missing)}")
        return
    for k, (scan, leaves) in enumerate(sources, 1):
        prose_dir(play, kind, scan)
        if step == "fetch":
            with ThreadPoolExecutor(workers) as ex:
                list(ex.map(lambda l: fetch_leaf(scan, l), leaves))
        elif step == "ocr":
            with ThreadPoolExecutor(workers) as ex:
                list(ex.map(lambda l: ocr_leaf(scan, l), leaves))
        else:
            raise SystemExit(f"unknown step {step!r}")
        print(f"{slug} {kind}: {step} done for {len(leaves)} leaves of {scan}")


def prose_dir(play: Play, kind: str, scan: str) -> Path:
    """Where a kind's crops go: build/drama-prose/<slug>/ (with `pages` linked to the scan's
    images), or, for a kind read from several scans (Play.notes_sources), a folder per scan under it."""
    if kind not in play.notes_sources:
        return route_dir("drama-prose", play.slug, scan)
    d = PIPELINE / "build" / "drama-prose" / play.slug / scan
    d.mkdir(parents=True, exist_ok=True)
    link = d / "pages"
    if not link.exists() and not link.is_symlink():
        link.symlink_to(Path("..") / ".." / ".." / "drama-scans" / scan / "pages")
    return d


def page_stem(play: Play, kind: str, scan: str, leaf: int) -> str:
    """p-0250; p-10250 / p-20250 for a kind read from several scans (the place in the list of the
    entry that holds the leaf: a scan may stand in the list twice, as Earle's volume does for the
    Medea's introduction, before and after Murray's hypotheses, and the pages are merged in the
    order of their stems)."""
    if kind not in play.notes_sources:
        return f"p-{leaf:04d}"
    entries = play.notes_sources[kind]
    k = next((i for i, (s, ranges) in enumerate(entries, 1) if s == scan and any(a <= leaf <= b for a, b in ranges)), None)
    if k is None:
        k = [s for s, _r in entries].index(scan) + 1
    return f"p-{k}{leaf:04d}"


# --- the page --------------------------------------------------------------------------------

def _region(play: Play, kind: str, leaf: int, lines: list[dict], size: tuple[int, int],
            scan: str | None = None) -> tuple[list[dict], float]:
    """The lines of the page that hold the notes (introduction, translation), each marked with its
    column ('left', 'right' or 'one'), without the running head, page number and signature, in
    reading order. Returns them and the gutter's x (0 for one column)."""
    from .drama_pages import _rule_below

    W, H = size
    body = [l for l in lines if l["bbox"][3] > 0.065 * H]
    # the running head (NOTES. LINES 412-450. / AGAMEMNON. / INTRODUCTION.) a little lower down
    body = [l for l in body if not (l["bbox"][1] < 0.1 * H and len(l["words"]) <= 5
                                    and _capitals(" ".join(w["text"] for w in l["words"])))]
    if play.layout == "jebb" and kind in ("intro", "appendix"):
        # Jebb's head with its page number in small roman figures (EDITIONS, ETC. lii), and his
        # signature at the foot (J. S. V., I—2): no word of three small letters
        body = [l for l in body if not (l["bbox"][1] < 0.1 * H and len(l["words"]) <= 6 and _capitals(" ".join(
            w["text"] for w in l["words"] if not re.fullmatch(r"[ivxlcIl1\d]{1,6}[.,]?", w["text"]))))]
        body = [l for l in body if not (l["bbox"][1] > 0.88 * H and len(" ".join(w["text"] for w in l["words"])) <= 12
                                        and not re.search(r"[a-z]{3}", " ".join(w["text"] for w in l["words"])))]
    # a page number or signature alone at the foot
    body = [l for l in body if not (l["bbox"][1] > 0.88 * H and len(l["words"]) <= 2
                                    and len(" ".join(w["text"] for w in l["words"])) <= 7
                                    and re.search(r"\d", " ".join(w["text"] for w in l["words"])))]
    if play.notes_layout == "earle" and (scan or play.scan_for(kind)) == play.notes_scan:
        # Earle's volume: the printer's signature at the foot of every eighth page ("MEDEA — 13",
        # under the left column on the notes pages)
        body = [l for l in body if not (l["bbox"][1] > 0.75 * H and re.fullmatch(
            r"MEDEA\s*[—–-]*\s*[\dIl|§]{0,3}\.?", " ".join(w["text"] for w in l["words"]).strip()))]
    if play.notes_layout == "hayley" and (scan or play.scan_for(kind)) == play.notes_scan:
        # specks read as a tiny line of a figure or two (a "9" under the running head of p. 62,
        # which became a note's number)
        body = [l for l in body if not (l["bbox"][3] - l["bbox"][1] < 26
                                        and len(" ".join(w["text"] for w in l["words"])) <= 4)]
        # the running head of the introduction with its page number in small roman figures
        # ("INTRODUCTION. xiii", "lxxxvi INTRODUCTION."), which is not all capitals
        body = [l for l in body if not (l["bbox"][1] < 0.1 * H and re.fullmatch(
            r"(?:\S{1,9}\s+)?INTRODUCTION\.?(?:\s+\S{1,9})?", " ".join(w["text"] for w in l["words"]).strip()))]
        # the accents of quoted Greek verses read as a line of their own (tiny type, few letters)
        def letters(t: str) -> float:
            t = t.replace(" ", "")
            return sum(c.isalpha() for c in t) / len(t) if t else 0.0
        body = [l for l in body if not ((l.get("x_size") or 99) < 26
                                        and letters(" ".join(w["text"] for w in l["words"])) < 0.6)]
    top = 0
    if play.notes_layout == "college" and kind == "notes":
        # the college editions of Lysias (Adams, Morgan): the printer's signature under the left
        # column of every eighth or sixteenth page ("LYSIAS — 5")
        body = [l for l in body if not (l["bbox"][1] > 0.75 * H and re.fullmatch(
            r"[A-Z]{4,}\.?\s*[—–-]*\s*[\dIl|§]{0,3}\.?", " ".join(w["text"] for w in l["words"]).strip()))]
        return _region_earle(play, leaf, body, size)
    if play.notes_layout == "back" and kind == "notes":
        # Shuckburgh's running head on a right-hand page: the speech's numeral and the page number ("IV. 221")
        body = [l for l in body if not (l["bbox"][1] < 0.1 * H and len(l["words"]) <= 3
                                        and re.search(r"\d{3}", " ".join(w["text"] for w in l["words"])))]
        # the pages of his text, printed in the outer margin beside the notes ("22", "23"): a figure
        # standing beyond the column's edge at a line's end or start
        if body:
            ends = sorted(l["bbox"][2] for l in body if not re.fullmatch(r"\d{1,3}", l["words"][-1]["text"]))
            starts = sorted(l["bbox"][0] for l in body if not re.fullmatch(r"\d{1,3}", l["words"][0]["text"]))
            right = ends[int(0.9 * len(ends))] if ends else W
            left = starts[len(starts) // 10] if starts else 0
            for l in body:
                ws = l["words"]
                if len(ws) > 1 and re.fullmatch(r"\d{1,3}", ws[-1]["text"]) and ws[-1]["bbox"][0] > right - 5:
                    l["words"] = ws[:-1]
                elif len(ws) > 1 and re.fullmatch(r"\d{1,3}", ws[0]["text"]) and ws[0]["bbox"][2] < left + 5:
                    l["words"] = ws[1:]
            body = [l for l in body if not (len(l["words"]) == 1 and re.fullmatch(r"\d{1,3}", l["words"][0]["text"])
                                            and (l["bbox"][0] > right - 5 or l["bbox"][2] < left + 5))]
        body = _own_oration(play, leaf, body)
    if play.intro_foot_columns and kind == "intro":
        # Morgan's introductions: the text in one column, his footnotes under it in two (found as
        # Earle's commentary is, by the rows of two columns): the text first, then the footnotes'
        # left column, then their right one
        cut = earle_top(body, W)
        if cut > 0.3 * H:
            main = sorted((l for l in body if (l["bbox"][1] + l["bbox"][3]) / 2 <= cut), key=lambda l: l["bbox"][1])
            for l in main:
                l["region"] = "one"
            feet, _mid = _two_columns([l for l in body if (l["bbox"][1] + l["bbox"][3]) / 2 > cut], H, signature=False)
            return main + feet, 0
    if play.layout == "jebb" and kind == "notes" and play.app_rule == "under":
        return _region_under_rule(play, leaf, body, size)
    if play.notes_layout == "earle" and (kind == "notes" or earle_notes_page(play, kind, leaf, scan)):
        return _region_earle(play, leaf, body, size)
    if play.layout == "jebb" and kind in ("notes", "trans"):
        from .drama_pages import rules as _rules

        png = scan_dirs(play.scan_for(kind))[1] / "pages" / f"leaf_{leaf:04d}.png"
        found = _rules(png, int(0.1 * H))
        if kind == "notes":
            top = (found[-1] + 5) if found else 0  # the commentary: under the last rule
        else:
            body = [l for l in body if not found or l["bbox"][3] < found[0]]  # the translation: above the first
    if play.notes_layout == "paley" and kind == "notes" and body:
        # Paley: his text and his bands (digamma, MSS readings) run across the page; the
        # commentary's two columns under them never cross the middle
        mid0 = W / 2
        def crosses(l: dict) -> bool:
            return l["bbox"][0] < mid0 - 0.04 * W and l["bbox"][2] > mid0 + 0.04 * W

        found = short_rules(scan_dirs(play.scan_for(kind))[1] / "pages" / f"leaf_{leaf:04d}.png")
        seq = sorted(body, key=lambda l: l["bbox"][1])
        start = next((i for i in range(len(seq)) if not any(crosses(l) for l in seq[i:i + 4])
                      and len(seq[i:i + 4]) == 4), None)
        limit = seq[start]["bbox"][1] if start is not None else H
        cross = [l for l in seq if crosses(l) and l["bbox"][1] < limit]
        top = (max(l["bbox"][3] for l in cross) + 2) if cross else 0
        if found:
            top = max(top, found[-1] + 5)  # under Paley's last short rule, and under his bands
    body = [l for l in body if l["bbox"][1] >= top]
    if not body:
        return [], 0
    x0 = min(l["bbox"][0] for l in body)
    x1 = max(l["bbox"][2] for l in body)
    width = x1 - x0
    xs = range(int(x0 + width * 0.4), int(x0 + width * 0.6), 4)
    cover = [(sum(1 for l in body if l["bbox"][0] < x < l["bbox"][2]), abs(x - (x0 + x1) / 2), x) for x in xs]
    best = min(cover) if cover else (len(body), 0, 0)
    two = best[0] <= max(1, len(body) // 12) and len(body) >= 8
    if kind == "trans" and play.layout == "jebb":
        # Starkie's translation is one column; Tesseract splits a justified line at a wide space
        # into pieces that look like two columns: put the pieces of one printed line together
        two = False
        body.sort(key=lambda l: (l["bbox"][1] + l["bbox"][3]) / 2)
        merged: list[dict] = []
        for l in body:
            m = merged[-1] if merged else None
            if m is not None:
                ov = min(m["bbox"][3], l["bbox"][3]) - max(m["bbox"][1], l["bbox"][1])
                if ov > 0.5 * min(m["bbox"][3] - m["bbox"][1], l["bbox"][3] - l["bbox"][1]):
                    a, b = (m, l) if m["bbox"][0] <= l["bbox"][0] else (l, m)
                    m["words"] = a["words"] + b["words"]
                    m["bbox"] = [min(a["bbox"][0], b["bbox"][0]), min(a["bbox"][1], b["bbox"][1]),
                                 max(a["bbox"][2], b["bbox"][2]), max(a["bbox"][3], b["bbox"][3])]
                    continue
            merged.append(l)
        body = merged
    mid = best[2] if two else 0
    for l in body:
        l["region"] = ("left" if (l["bbox"][0] + l["bbox"][2]) / 2 < mid else "right") if two else "one"
    order = sorted(body, key=lambda l: ({"left": 0, "one": 0, "right": 1}[l["region"]], l["bbox"][1]))
    return order, mid


NO_RULE = -1  # _region's gutter when the page has no rule to take the commentary from
ORATION_HEAD = re.compile(r"^ORATION\s+[IVXLl1]+\b")


def _own_oration(play: Play, leaf: int, body: list[dict]) -> list[dict]:
    """Shuckburgh's Lysias (notes_layout "back"): the notes stand at the back of the book, each
    speech's under a heading "ORATION IV. [10.]" with his introduction to the speech, and the
    next speech's heading may stand on the page where this one's notes end. Of the first leaf of
    the speech's notes only what stands from its heading down is the speech's; of a later leaf,
    only what stands above the next speech's heading."""
    leaves = play.leaves("notes")
    heads = sorted((l for l in body if ORATION_HEAD.match(" ".join(w["text"] for w in l["words"]).strip())),
                   key=lambda l: l["bbox"][1])
    if not heads or not leaves:
        return body
    if leaf == leaves[0]:
        body = [l for l in body if l["bbox"][1] >= heads[0]["bbox"][1] - 2]
        heads = heads[1:]
    if heads:
        body = [l for l in body if l["bbox"][3] <= heads[0]["bbox"][1] + 2]
    return body


def _region_under_rule(play: Play, leaf: int, body: list[dict], size: tuple[int, int]) -> tuple[list[dict], float]:
    """Jebb's Sophocles (app_rule "under"), kind notes: the commentary is everything under the
    rule page_layout finds (drama_pages.head_rule: above it stand the verses or the translation
    and the apparatus, which are not the commentary), in two columns on both pages of a spread:
    the left column read first, then the right. A line Tesseract ran across the gutter is cut
    there into its two columns' lines; the signature at the foot (J. S. IV., 3) is left out. A
    page where no rule is found gives no lines and the gutter NO_RULE (the draft says so on the
    page: nothing is taken from the whole page silently)."""
    from .drama_pages import head_rule

    W, H = size
    png = scan_dirs(play.scan_for("notes"))[1] / "pages" / f"leaf_{leaf:04d}.png"
    rule = head_rule(play, png, H)
    if rule is None:
        return [], NO_RULE
    body = [l for l in body if (l["bbox"][1] + l["bbox"][3]) / 2 > rule + 4]
    # the signature (J. S. IV. 3, or a lone figure) at the foot
    body = [l for l in body if not (l["bbox"][1] > 0.9 * H and len(" ".join(w["text"] for w in l["words"])) <= 14
                                    and not re.search(r"[a-z]{3}|[Ͱ-Ͽἀ-῿]{3}", " ".join(w["text"] for w in l["words"])))]
    return _two_columns(body, H)


def _gutter(lines: list[dict], lo: float = 0.38, hi: float = 0.62) -> tuple[int, float, int]:
    """The gutter between two columns: (words crossing it, distance from the middle, x) for the x
    between `lo` and `hi` of the lines' width that the fewest words cross."""
    x0 = min(l["bbox"][0] for l in lines)
    x1 = max(l["bbox"][2] for l in lines)
    words = [w for l in lines for w in l["words"]]
    cover = [(sum(1 for w in words if w["bbox"][0] - 4 < x < w["bbox"][2] + 4), abs(x - (x0 + x1) / 2), x)
             for x in range(int(x0 + lo * (x1 - x0)), int(x0 + hi * (x1 - x0)), 3)]
    return min(cover) if cover else (len(words), 0, 0)


def _two_columns(body: list[dict], H: int, signature: bool = True) -> tuple[list[dict], float]:
    """The commentary's lines in two columns (Jebb's under the rule, Earle's under the verses): the
    left column read first, then the right; a line Tesseract ran across the gutter cut there; with
    `signature` a short line without a word at a column's foot (J. S. IV.) left out. One column
    (gutter 0) where no gutter is found."""
    if not body:
        return [], 0
    words = [w for l in body for w in l["words"]]
    best = _gutter(body)
    mid = best[2]
    left_n = sum(1 for w in words if w["bbox"][2] <= mid)
    right_n = sum(1 for w in words if w["bbox"][0] >= mid)
    if best[0] > max(2, len(words) // 40) or min(left_n, right_n) < 3:
        # one column only (the end of the commentary, or a page Tesseract read as one block)
        for l in body:
            l["region"] = "one"
        return sorted(body, key=lambda l: l["bbox"][1]), 0
    out: list[dict] = []
    for l in body:
        parts = {"left": [w for w in l["words"] if (w["bbox"][0] + w["bbox"][2]) / 2 < mid],
                 "right": [w for w in l["words"] if (w["bbox"][0] + w["bbox"][2]) / 2 >= mid]}
        for region, ws in parts.items():
            if not ws:
                continue
            if len(ws) == len(l["words"]):
                piece = l
            else:
                piece = dict(l, words=ws, bbox=[min(w["bbox"][0] for w in ws), min(w["bbox"][1] for w in ws),
                                                max(w["bbox"][2] for w in ws), max(w["bbox"][3] for w in ws)])
            piece["region"] = region
            out.append(piece)
    # pieces of one printed line that Tesseract read as lines of their own ("983 ἅμ’ αὐτοῖς, sc.
    # τοῖς τόξοις." and "So in"): put together, so that the second piece does not look indented
    merged: list[dict] = []
    for region in ("left", "right"):
        col = sorted((l for l in out if l["region"] == region), key=lambda l: (l["bbox"][1] + l["bbox"][3]) / 2)
        row: list[dict] = []
        for l in col:
            m = row[-1] if row else None
            if m is not None:
                ov = min(m["bbox"][3], l["bbox"][3]) - max(m["bbox"][1], l["bbox"][1])
                if ov > 0.5 * min(m["bbox"][3] - m["bbox"][1], l["bbox"][3] - l["bbox"][1]):
                    ws = sorted(m["words"] + l["words"], key=lambda w: w["bbox"][0])
                    row[-1] = dict(m, words=ws, bbox=[min(m["bbox"][0], l["bbox"][0]), min(m["bbox"][1], l["bbox"][1]),
                                                       max(m["bbox"][2], l["bbox"][2]), max(m["bbox"][3], l["bbox"][3])],
                                   x_size=max(m.get("x_size") or 0, l.get("x_size") or 0))
                    continue
            row.append(l)
        merged += row
    out = merged
    # the signature (J. S. IV., read "7.5. IV.") at the foot of a column: a short line without a
    # word in it, the column's last, set off from the line above by more than the usual space
    for region in ("left", "right") if signature else ():
        col = sorted((l for l in out if l["region"] == region), key=lambda l: l["bbox"][1])
        if len(col) < 4:
            continue
        pitch = sorted(b["bbox"][1] - a["bbox"][1] for a, b in zip(col, col[1:]))[(len(col) - 1) // 2]
        last = col[-1]
        text = " ".join(w["text"] for w in last["words"])
        if (last["bbox"][1] > 0.75 * H and len(text) <= 14 and not re.search(r"[a-z]{3}|[Ͱ-Ͽἀ-῿]{3}", text)
                and last["bbox"][1] - col[-2]["bbox"][1] > 1.5 * pitch):
            out.remove(last)
    order = sorted(out, key=lambda l: ({"left": 0, "right": 1}[l["region"]], l["bbox"][1]))
    return order, mid


def earle_top(body: list[dict], W: int) -> int:
    """Earle's Medea (notes_layout "earle"): the y where his commentary begins, under the block of
    verses in larger type at the top of the page, with no rule between. The commentary is found
    by its two columns: the first of three rows, one under the other at the small type's pitch,
    where a line of the left column and a line of the right one stand side by side (a verse
    crosses the gutter; a verse that Tesseract cut at a wide space, or its margin number, makes no
    run of three such rows). From that row up, lines in the small type directly above it are taken
    too (a first row that Tesseract read across the gutter as one line). 0 where the page has no
    such rows (the whole page is then taken, as for a page without verses)."""
    if not body:
        return 0
    lines = [l for l in body if l["bbox"][3] - l["bbox"][1] >= 18 and l["x_size"] >= 20]  # not the verses' accents read as a line
    lower = [l for l in lines if l["bbox"][1] > 0.35 * max(x["bbox"][3] for x in lines)] or lines
    mid = _gutter(lower, 0.4, 0.6)[2] if lower else W / 2
    def side(l: dict) -> str:
        if l["bbox"][2] <= mid + 8:
            return "L"
        if l["bbox"][0] >= mid - 8:
            return "R"
        return "X"
    col_w = max(1, mid - min(l["bbox"][0] for l in lines))
    def real(l: dict) -> bool:  # not a margin number, a speaker's abbreviation or a speck
        return len(l["words"]) >= 2 and (l["bbox"][2] - l["bbox"][0]) > 0.25 * col_w
    left = [l for l in lines if side(l) == "L" and real(l)]
    right = [l for l in lines if side(l) == "R" and real(l)]
    rows: list[tuple[int, int, float]] = []  # (top, bottom, x_size) of the rows of two columns
    for a in left:
        for b in right:
            ov = min(a["bbox"][3], b["bbox"][3]) - max(a["bbox"][1], b["bbox"][1])
            if ov > 0.5 * min(a["bbox"][3] - a["bbox"][1], b["bbox"][3] - b["bbox"][1]):
                rows.append((min(a["bbox"][1], b["bbox"][1]), max(a["bbox"][3], b["bbox"][3]),
                             max(a["x_size"], b["x_size"])))
                break
    rows.sort()
    if len(rows) < 3:
        return 0
    pitches = sorted(b[0] - a[0] for a, b in zip(rows, rows[1:]) if b[0] - a[0] > 10)
    pitch = pitches[len(pitches) // 2] if pitches else 45
    start = next((i for i in range(len(rows) - 2)
                  if rows[i + 1][0] - rows[i][0] <= 1.6 * pitch and rows[i + 2][0] - rows[i + 1][0] <= 1.6 * pitch), None)
    if start is None:
        return 0
    small = sorted(r[2] for r in rows[start:])[len(rows[start:]) // 2]
    hs = sorted(r[1] - r[0] for r in rows[start:])
    h = hs[len(hs) // 2]
    top = rows[start][0]
    margin = sorted(l["bbox"][0] for l in left if l["bbox"][1] >= top)
    margin = margin[len(margin) // 5] if margin else 0
    for l in sorted((l for l in lines if l["bbox"][1] < top), key=lambda l: -l["bbox"][1]):
        if top - l["bbox"][1] > 1.6 * pitch:
            break
        if l["bbox"][3] - l["bbox"][1] > 1.35 * h or (side(l) == "X" and l["x_size"] > 1.15 * small):
            break  # a verse (Tesseract's size of a short line in one column, "(302-306).", is no guide)
        if side(l) == "L" and l["bbox"][0] > margin + 2.5 * h:
            break  # a short verse, set in from the left column's edge
        if side(l) == "R" and not real(l):
            continue  # a verse's margin number
        top = l["bbox"][1]
    return top - 2


def earle_notes_page(play: Play, kind: str, leaf: int, scan: str | None) -> bool:
    """A page of another kind laid out as Earle's notes pages (Play.notes_region_leaves of the
    notes scan: his notes on the hypothesis, under his Greek, read with the introduction)."""
    return (kind != "notes" and (scan or play.scan_for(kind)) == play.notes_scan
            and any(a <= leaf <= b for a, b in play.notes_region_leaves))


def _region_earle(play: Play, leaf: int, body: list[dict], size: tuple[int, int]) -> tuple[list[dict], float]:
    """Earle's Medea, kind notes: everything under the verses (earle_top), in two columns, the left
    column read first; the page number at the foot is already gone (_region)."""
    W, H = size
    top = earle_top(body, W)
    return _two_columns([l for l in body if (l["bbox"][1] + l["bbox"][3]) / 2 > top], H, signature=False)


def jebb_dashes(text: str) -> str:
    """The OCR's dashes in Jebb's commentary as he prints them: '---', '--', '-—' are his dash (—);
    κ.τ.λ. as the OCR reads it (κιτ.λ., k.T.\\.) written so;
    and his commonest references, which the OCR reads "O. 7." and "0. C.", as *O. T.*, *O. C.*"""
    text = re.sub(r"\s?(?:-{2,4}|-—|—-)\s?", "—", text)
    text = re.sub(r"(?<!\w)(?:κ[.,ι:]\s?τ[.,]\s?λ|k\.\s?T\.\s?[\\λA])[.,]", "κ.τ.λ.", text)  # κιτ.λ., k.T.\.
    text = re.sub(r"(?<=\s)ὃ(?=\s\d)", "§", text)  # "De Igne § 37" read "ὃ 37"
    text = re.sub(r"(?<![\w*])[OΟ0]\.\s?[7T]\.", "*O. T.*", text)
    return re.sub(r"(?<![\w*])[OΟ0]\.\s?[CС]\.", "*O. C.*", text)


_BOLD_F = re.compile(r"^(\d{1,4}(?:\s*—\s*\d{1,4})?)\s*(?:£f|££|ff|£|f|ΣΦ|ΖΦ|Φ|Ζ|Ξ|Ο|2(?=[.,]\s*[‘“(]?[Ͱ-Ͽἀ-῿]))[.,](?=\s)")


def jebb_f(text: str) -> str:
    """The bold "f." or "ff." after a note's number as the OCR misreads it ("£.", "£f.", "ΖΦ.",
    "Φ.", "2." before Greek) written "f." / "ff.", so that the number is read as the heading."""
    return _BOLD_F.sub(lambda m: m.group(1) + (" ff." if m.group(0).rstrip(".,").endswith(("£f", "££", "ff")) else " f."), text)


_LEMMA_DASH = re.compile(r"\s*—\s*(?=[‘“(\[]?[Ͱ-Ͽἀ-῿])")


_GWORD = r"[‘“(\[]?[Ͱ-Ͽἀ-῿][Ͱ-Ͽἀ-῿ʼ’᾽]*[’”)\]]?"
_LEAD_GREEK = re.compile(rf"^{_GWORD}(?:(?:\s*(?:\.{{2,3}}|…)\s*|\s+){_GWORD})*")


def jebb_lemma(text: str) -> str:
    """The Greek words at the start of a note of Jebb's in bold, as drama.bold_lemma, up to the
    first word that is not Greek, with his 'κ.τ.λ.' left out of the bold (**ἔα κακῶς** κ.τ.λ.).
    (Not bold_lemma itself: its pattern, whose word separators are optional, backtracks for
    minutes on a long run of Greek that ends otherwise than it expects.)"""
    if text.startswith("**"):
        return text
    m = _LEAD_GREEK.match(text)
    if not m:
        return text
    lemma = m.group(0)
    if re.search(r"\sκ$", lemma) and text[len(lemma):].startswith(".τ.λ."):
        lemma = lemma[:-2]
    lemma = lemma.rstrip()
    rest = text[len(lemma):]
    return f"**{re.sub(r'(?<=[^.])\.\.(?=[^.])', '...', lemma)}**" + rest  # the OCR's '..' for Jebb's '...' 


_COLLEGE_LEMMA = re.compile(rf"^({_GWORD}(?:(?:\s*[,;]?\s*\.(?:\s?\.){{1,3}}\s*|\s*…\s*|[,;]?\s+){_GWORD})*(?:\s+κτλ\.)?)\s?:(?=\s|$)")


def college_lemma(text: str) -> str:
    """The lemma of a note in the college editions of Lysias (Adams, Morgan): the bold Greek up to
    the colon that follows it (Adams sets a space before the colon), commas and dots of omission
    included ("κινδυνεύειν ἐδόκει, ὡς . . . ὑπάρχοντος : it seemed …"); written `**lemma**: `.
    Where no colon follows the leading Greek, as jebb_lemma."""
    if text.startswith("**"):
        return text
    m = _COLLEGE_LEMMA.match(text)
    if not m:
        return jebb_lemma(text)
    lemma = re.sub(r"\s*\.(?:\s?\.){1,3}\s*", " . . . ", m.group(1)).strip()
    return f"**{lemma}**:" + text[m.end():]


_BACK_LEMMA = re.compile(rf"^{_GWORD}(?:(?:\s*[,;]?\s*\.(?:\s?\.){{1,3}}\s*|\s*…\s*|[,;]?\s+){_GWORD})*")


def back_lemma(text: str) -> str:
    """The lemma of a note of Shuckburgh's: the bold Greek that opens it, with its dots of
    omission (he prints two: "εἰσήγγελλε . . δημηγορεῖν ‘was impeaching …’"), up to the first
    word that is not Greek; no colon follows. The dots are written as he prints them, spaced."""
    if text.startswith("**"):
        return text
    m = _BACK_LEMMA.match(text)
    if not m:
        return text
    lemma = re.sub(r"\s*\.(?:\s?\.)+\s*", lambda d: " " + " ".join("." * d.group(0).count(".")) + " ", m.group(0)).strip()
    return f"**{lemma.rstrip(' .,;')}**" + (text[m.end():] if not lemma.endswith((".", ",", ";")) else lemma[len(lemma.rstrip(' .,;')):] + text[m.end():])


def split_lemmas(text: str, first: bool = False, lemma=None) -> list[str]:
    """A paragraph of Jebb's commentary cut where a dash is followed by Greek (in the print a
    further lemma in bold: "…cp. 1095 n.—**ἐμᾶς**, Bergk's correction"), each piece after a cut
    with its lemma in bold, as Perseus's files of the other plays give them; with `first` the
    first piece too (the text after a note's number). Pieces that are not a lemma (Greek after a
    dash in plain type) are for the agent to join again."""
    lemma = lemma or jebb_lemma
    parts = _LEMMA_DASH.split(text)
    out = [lemma(parts[0].strip()) if first else parts[0].strip()]
    out += [lemma(x.strip()) for x in parts[1:] if x.strip()]
    return [x for x in out if x] or [""]


def earle_clean(text: str) -> str:
    """The OCR of Earle's commentary as he prints it: '---', '--', '-—' are his dash (—); a range
    divided at a line's end ("455- 458.") joined; the OCR's ¢ for his opening quotation mark ‘;
    the space he sets before a lemma's colon ("τυράννους :") is kept for the lemma rule."""
    text = re.sub(r"\s?(?:-{2,4}|-—|—-)\s?", " — ", text)
    text = re.sub(r"(?<=\d)\s?[-–]\s+(?=\d)", "-", text)
    text = text.replace("¢", "‘")
    # his italic i.e., which the OCR reads "2.6.", "Ze.", "Z.e.", "7.e."; sc. read "56." or "SC."
    text = re.sub(r"(?<![\w.])(?:2\.[26]|1\.6|Z\.?e|ze|ie|7\.?\s?e|fe)\.(?=\s)", "*i.e.*", text)
    text = re.sub(r"(?<![\w.])(?:56|SC)\.(?=\s[Ͱ-Ͽἀ-῿])", "sc.", text)
    return re.sub(r"\s{2,}", " ", text).strip()


# a note's number in Earle's commentary, wherever it stands in the paragraph: bold old-style
# figures with a stop, "21 f.", "455-458.", "Vv. 1-48."; the OCR reads old-style 1 as I or l, 0 as
# o, and the figure 2 as "ἡ" or "z"; the bold "f." as "£." or "Φ."
_EARLE_CAND = re.compile(r"(?<![^\s—])(?:(?:Vv?\.)\s*)?([0-9IlΙ|oOοΟ]{1,4}|ἡ|z)(?:\s*[-–]\s*([0-9IlΙ|oOοΟ]{1,4}))?"
                         r"(?:\s*(?:ff|f|£f|££|£|ΖΦ|ΣΦ|Φ))?\.(?=\s|$)")
_EARLE_DIGITS = str.maketrans({"I": "1", "l": "1", "Ι": "1", "|": "1", "o": "0", "O": "0", "ο": "0", "Ο": "0"})
# the word before a number that makes it a reference, not a note's number: v. 450, cp. 1345, p. 36,
# HA. 871, Soph. Ant. 173 f.
_EARLE_REF = re.compile(r"^\(?(?:[vV]v?|[cC]p|[cC]f|pp?|ll?|nn?|sqq?|sc|ch|no|vol|ed|al|ib|ibid|ss?|[A-Z][A-Za-z]{0,3}"
                        r"|Soph|Aesch|Aeschin|Hipp|Suppl|Supp|Thuc|Androm|Heracl|Herc|Introd|Bacch|Phoen|Troad|Cycl|Rhes"
                        r"|Iph|Taur|Aul|Hom|Aristoph|Plat|Pind|Theocr|Verg|Hor|Carm|Georg|Ecl|Aen|Symp|Phaed|Prot|Gorg"
                        r"|Isocr|Plut|Anth|Schol|Hist|Pyth|Nem|Isth|Prom|Sept|Pers|Alcest|Elect|Lycurg|Andoc|Lysias)\.$")
EARLE_WINDOW = 60  # how far one of Earle's notes may run ahead of the one before
# Earle's lemma may span a gap marked with spaced dots ("ἀμφιλόγους . . . νείκη :", "κοὐκ.... ἔκβασις")
_EARLE_LEAD = re.compile(rf"^{_GWORD}(?:(?:\s*\.(?:\s?\.){{1,3}}\s*|\s*…\s*|\s+){_GWORD})*")


def earle_lemma(text: str) -> str:
    """The Greek at the start of a piece of Earle's notes in bold (as jebb_lemma), a gap marked by
    dots inside it included as printed."""
    if text.startswith("**"):
        return text
    m = _EARLE_LEAD.match(text)
    if not m:
        return text
    lemma = m.group(0).rstrip()
    return f"**{lemma}**" + text[len(lemma):]


def earle_markdown(text: str, cands: list[dict], lead: str = "") -> list[str]:
    """One paragraph of Earle's commentary (earle_clean'd) as draft lines: the paragraph is cut
    before every number that may begin a note (_EARLE_CAND, after a sentence's end or a dash, not
    after a reference word), each such number a placeholder for _resolve_note_headings (which
    keeps those in a sequence as `## N` headings and joins the rest back); every piece is cut
    again at a dash followed by Greek (a further lemma on the verse, as split_lemmas), and the
    Greek after a number or a dash goes in bold, its colon outside (`**τυράννους**:`). `lead` is
    put before the paragraph's first piece ("+ " for a paragraph run on from the page before)."""
    starts = []
    for m in _EARLE_CAND.finditer(text):
        a, b = m.group(1), m.group(2)
        if not (re.search(r"\d", a) or a in ("ἡ", "z")) or (b and not re.search(r"\d", b)):
            continue
        if re.match(r"\s*[\d)\]]", text[m.end():]):
            continue  # a reference's book or chapter ("Pyth. 4. 209)")
        before = text[:m.start()].rstrip()
        prev = before.split()[-1] if before.split() else ""
        if prev and not (re.search(r"[.;:!?’'”)\]—]$", prev)):
            continue
        if prev and _EARLE_REF.match(prev):
            continue
        a = "2" if a in ("ἡ", "z") else a.translate(_EARLE_DIGITS)
        b = b.translate(_EARLE_DIGITS) if b else ""
        if a.startswith("0") and len(a) == 1:
            continue
        starts.append((m.start(), m.end(), a + (f"-{b}" if b else "")))
    def colon(piece: str) -> str:
        return re.sub(r"^(\*\*[^*]+\*\*)\s+([:;,])", r"\1\2", piece)
    out: list[str] = []
    pre = text[: starts[0][0]].strip() if starts else text
    if pre:
        pieces = [colon(x) for x in split_lemmas(pre, lemma=earle_lemma)]
        pieces[0] = lead + pieces[0]
        for x in pieces:
            out += [x, ""]
    for k, (s, e, n) in enumerate(starts):
        end = starts[k + 1][0] if k + 1 < len(starts) else len(text)
        rest = text[e:end].strip()
        # a number inside the paragraph that is not kept goes back into it; one at its start stays
        # at the start of its paragraph
        cands.append({"kind": "note", "n": n, "label": text[s:e].strip(), "join": bool(pre) or k > 0,
                      "alone": lead if k == 0 and not pre else "",
                      "bonus": 3 if k == 0 and not pre and not lead else 0,  # a number opening an indented paragraph
                      "body": [colon(x) for x in split_lemmas(rest, first=True, lemma=earle_lemma)] if rest else [],
                      "orig": [colon(x) for x in split_lemmas(text[s:end].strip(), lemma=earle_lemma)]})
        out += [f"\x00{len(cands) - 1}", ""]
    return out


def hayley_clean(text: str) -> str:
    """The OCR of Hayley's notes as he prints them: '---', '--', '-—' his spaced dash; the OCR's ¢ for
    his opening quotation mark ‘."""
    text = re.sub(r"\s?(?:-{2,4}|-—|—-)\s?", " — ", text)
    text = text.replace("¢", "‘")
    text = re.sub(r"\s?:\s?:(?=\s)", " :", text)  # the colon read twice
    return re.sub(r"\s{2,}", " ", text).strip()


# a further lemma of Hayley's (not after the dots of a gap, "εἰ τὴν παροῦσαν . . . γυναῖχ᾽ :", nor after
# sc., cf., i.e., e.g., v.: "πολλή μ᾽ ἀνάγκη : sc. μητέρα γενέσθαι : μ᾽ is …") inside a note's paragraph: bold Greek after a sentence's end, before
# his spaced colon ("… θῆσσαν ἑστίαν. αἰνέσαι : Schol. …"); Greek quoted after a reference's figure
# ("Phoen. 425 οὐ μεμπτὸς … ἡμέρας :") is no lemma
_HAYLEY_CUT = re.compile(rf"(?<=[.;!?’”)\]])(?<!\.\.)(?<!\.\s\.)(?<![\s(]sc\.)(?<![\s(][cC]f\.)(?<!i\.e\.)(?<!e\.g\.)(?<![\s(]v\.)(?<![\s(]vv\.)\s+(?={_GWORD}(?:(?:\s*\.(?:\s?\.){{1,3}}\s*|\s*…\s*|\s+){_GWORD})*\s?:)")
_HAYLEY_LEMMA = re.compile(rf"^({_GWORD}(?:(?:\s*\.(?:\s?\.){{1,3}}\s*|\s*…\s*|\s+){_GWORD})*)\s?:")


def hayley_lemma(text: str) -> str:
    """The Greek before Hayley's colon at the start of a piece in bold, the colon outside it without
    the space he sets before it ("φλόγα : here" -> "**φλόγα**: here"); a piece that does not begin
    with Greek and a colon is left as it is."""
    if text.startswith("**"):
        return text
    m = _HAYLEY_LEMMA.match(text)
    if not m:
        return text
    return f"**{m.group(1).rstrip()}**:" + text[m.end():]


def hayley_split(text: str, first: bool = False) -> list[str]:
    """A paragraph of Hayley's notes cut before every further lemma (_HAYLEY_CUT), each piece after
    a cut a paragraph of its own with its lemma in bold, as the other commentaries' further lemmas
    are written; with `first` the first piece's lemma too (the text after a note's number)."""
    parts = [x.strip() for x in _HAYLEY_CUT.split(text) if x.strip()]
    if not parts:
        return [""]
    return [hayley_lemma(parts[0]) if first else parts[0]] + [hayley_lemma(x) for x in parts[1:]]


HAYLEY_BACK = 15   # how far one of Hayley's notes may stand below the one before it (his order going back)
NOTE_WINDOW = 100  # how far one note's number may run ahead of the one before (Jebb's notes)
NOTE_REACH = 80    # how many headings back a note's predecessor in the sequence is looked for
_DIGIT_LIKE = {"3": "8", "8": "3", "1": "7", "7": "1", "5": "6", "6": "5", "0": "9", "9": "0"}


def _note_options(a: str) -> list[tuple[int, int]]:
    """The readings of a note's number as the OCR gave it, with their cost: as read (0); with a
    figure fewer (1: "255 f." read "2555.", "1153" for "153"); with one old-style figure read as
    its look-alike (2: 3/8, 1/7, 5/6, 0/9: "30" read "80")."""
    out = {int(a): 0}
    if len(a) >= 3:
        for i in range(len(a)):
            x = a[:i] + a[i + 1:]
            if x and not x.startswith("0"):
                out.setdefault(int(x), 1)
    for i, c in enumerate(a):
        if c in _DIGIT_LIKE:
            x = a[:i] + _DIGIT_LIKE[c] + a[i + 1:]
            if not x.startswith("0"):
                out.setdefault(int(x), 2)
    return sorted(out.items(), key=lambda t: t[1])


def _resolve_note_headings(pages: list[dict], last_line: int = 2000, window: int = NOTE_WINDOW) -> None:
    """The note headings of Jebb's commentary (placeholders of analyse_page) settled over all the
    pages at once: of the numbers as read (or a reading of _note_options), the longest sequence
    that never falls and never leaps more than NOTE_WINDOW nor beyond the play's last line is
    kept as headings, the cheaper readings preferred; a candidate outside it (a reference at the
    start of a paragraph, a number misread past mending) goes back into the text as read, for
    the agent. One misread number thus cannot shut out the notes after it. A candidate marked
    `join` (Earle's notes, which run on inside a paragraph) goes back into the paragraph it was
    cut from: its first piece joined to the text before it on the page (or, if nothing stands
    before it, written with its `alone` prefix, the page's run-on mark). A candidate marked `back`
    (Hayley's notes, every one opening an indented paragraph) whose number as read lies a little
    below the heading before it (at most `back` lower) is kept as a heading too: the editor's own
    order going back ("384. … 381. …", a range note after its single notes)."""
    cands = []  # (page, candidate)
    for page in pages:
        for raw in page["md"].split("\n"):
            m = re.fullmatch("\x00(\\d+)", raw)
            if m and page["cands"][int(m.group(1))].get("kind") == "note":
                cands.append(page["cands"][int(m.group(1))])
    opts = [[(v, c) for v, c in _note_options(x["n"].partition("-")[0]) if 1 <= v <= last_line] for x in cands]
    # best[i][j]: (score, previous (i, j)) of the best sequence ending in option j of candidate i
    best: list[list[tuple[int, tuple[int, int] | None]]] = []
    for i, oi in enumerate(opts):
        row = []
        for v, cost in oi:
            gain = 10 - cost + cands[i].get("bonus", 0)
            score, prev = gain, None
            for k in range(max(0, i - NOTE_REACH), i):
                for j2, (v2, _c2) in enumerate(opts[k]):
                    if v2 <= v <= v2 + window and best[k][j2][0] + gain > score:
                        score, prev = best[k][j2][0] + gain, (k, j2)
            row.append((score, prev))
        best.append(row)
    chosen: dict[int, int] = {}
    ends = [(best[i][j][0], i, j) for i in range(len(best)) for j in range(len(best[i]))]
    if ends:
        _s, i, j = max(ends)
        node: tuple[int, int] | None = (i, j)
        while node is not None:
            chosen[id(cands[node[0]])] = opts[node[0]][node[1]][0]
            node = best[node[0]][node[1]][1]
    last = 0
    for page in pages:
        out: list[str] = []
        for raw in page["md"].split("\n"):
            m = re.fullmatch("\x00(\\d+)", raw)
            c = page["cands"][int(m.group(1))] if m else None
            if c is None or c.get("kind") != "note":
                out.append(raw)
                continue
            if id(c) not in chosen and c.get("back"):
                read = c["n"].partition("-")[0]
                if read.isdigit() and last - c["back"] <= int(read) <= last:
                    chosen[id(c)] = int(read)
                    n = int(read)
                    b = c["n"].partition("-")[2]
                    out += [f"## {n}" + (f"-{b}" if b and int(b) > n else "")] + [x for piece in c["body"] if piece for x in (piece, "")]
                    if out[-1] != "":
                        out.append("")
                    continue
            if id(c) not in chosen:
                pieces = list(c["orig"])
                k = len(out) - 1
                while k >= 0 and out[k] == "":
                    k -= 1
                if c.get("join") and pieces and k >= 0 and not out[k].startswith("#"):
                    out[k] = out[k] + " " + pieces.pop(0)
                    del out[k + 1:]
                    out.append("")
                elif pieces:
                    pieces[0] = c.get("alone", "") + pieces[0]
                for piece in pieces:
                    out += [piece, ""]
                continue
            n = chosen[id(c)]
            last = max(last, n)
            b = c["n"].partition("-")[2]
            out += [f"## {n}" + (f"-{b}" if b and int(b) > n else "")] + [x for piece in c["body"] if piece for x in (piece, "")]
            if out[-1] != "":
                out.append("")
        page["md"] = re.sub(r"\n{3,}", "\n\n", "\n".join(out)).strip()


def short_rules(png: Path, upto: float = 0.8) -> list[int]:
    """The short rules centred on the page (Paley's, under his text and under his bands), as the
    y of each: a row whose ink is one dense run between 5 % and 30 % of the page's width, its
    middle within a tenth of the page's middle, in the upper part of the page."""
    from PIL import Image

    with Image.open(png) as im:
        g = im.convert("L")
        W, H = g.size
        px = g.load()
        out: list[int] = []
        for y in range(int(0.05 * H), int(upto * H)):
            xs = [x for x in range(0, W, 2) if px[x, y] < 170]
            if not xs:
                continue
            span = xs[-1] - xs[0]
            if 0.05 * W < span < 0.3 * W and len(xs) * 2 > 0.8 * span \
                    and abs((xs[0] + xs[-1]) / 2 - W / 2) < 0.1 * W:
                if not out or y - out[-1] > 8:
                    out.append(y)
        return out


def _join_lines(texts: list[str]) -> str:
    """Printed lines joined into running text; a word divided at a line's end written whole."""
    out = ""
    for t in texts:
        t = t.strip()
        if not t:
            continue
        if out.endswith("-") and re.search(r"[^\W\d_]-$", out) and re.match(r"[^\W\d_]", t) and t[:1].islower():
            out = out[:-1] + t
        elif out:
            out += " " + t
        else:
            out = t
    return out


SMALL_WORDS = {"a", "an", "and", "as", "at", "but", "by", "for", "from", "in", "into", "of", "on", "or", "the", "to", "with"}


def title_case(text: str) -> str:
    """A heading printed in capitals, as ordinary capitals and small letters: THE STORY AND THE
    PLOT OF THE AGAMEMNON -> The Story and the Plot of the Agamemnon."""
    out = []
    for k, w in enumerate(text.strip(" .,").split()):
        core = w.strip("().,;:—-")
        if re.fullmatch(r"[IVXLC]+", core) and len(core) <= 5 and k > 0:
            out.append(w)
        elif k > 0 and core.lower() in SMALL_WORDS:
            out.append(w.lower())
        else:
            out.append(w[:1].upper() + w[1:].lower())
    return " ".join(out)


def _capitals(text: str) -> bool:
    letters = [c for c in text if c.isalpha()]
    return len(letters) >= 4 and sum(c.isupper() for c in letters) >= 0.8 * len(letters)


def _reread_strip(scan: str, leaf: int, box: tuple[int, int, int, int]) -> list[dict]:
    """The lines Tesseract (eng+grc) finds in a part of the page read on its own (cached)."""
    import tempfile

    from .drama_pages import read_lines
    from .egt_ocr import tesseract

    _, sbuild = scan_dirs(scan)
    x0, y0, x1, y1 = box
    cache = sbuild / "hocr" / f"leaf_{leaf:04d}.eng-strip-{x0}-{y0}-{x1}-{y1}.hocr"
    if not cache.exists():
        from PIL import Image

        with Image.open(sbuild / "pages" / f"leaf_{leaf:04d}.png") as im, tempfile.TemporaryDirectory() as t:
            im.crop(box).save(Path(t) / "s.png")
            tesseract(Path(t) / "s.png", Path(t) / "s", "eng+grc", 6)
            cache.write_text((Path(t) / "s.hocr").read_text(encoding="utf-8"), encoding="utf-8")
    out = []
    for l in read_lines(cache):
        for w in l["words"]:
            w["bbox"] = [w["bbox"][0] + x0, w["bbox"][1] + y0, w["bbox"][2] + x0, w["bbox"][3] + y0]
        l["bbox"] = [l["bbox"][0] + x0, l["bbox"][1] + y0, l["bbox"][2] + x0, l["bbox"][3] + y0]
        out.append(l)
    return out


def long_s(word: str, english: set[str]) -> str:
    """A word of an eighteenth-century print as we write it: the long s (ſ), which Tesseract
    reads as ſ or as f, written s ("fhould", "ſhould" → should; "poſſeſſion" → possession). An f
    becomes an s only where the word as read is no English word and the word with s is one (the
    first such reading, the fewest letters changed); the ligatures ct and st are plain letters."""
    w = word.replace("ſ", "s").replace("ﬅ", "st").replace("ﬆ", "st").replace("\ueada", "ct")
    w = re.sub(r"^\{(?=[a-z])", "s", w)  # a long s at a word's head read as a brace ("{trumpet")
    m = re.match(r"^([^A-Za-z]*)([A-Za-z]+(?:[-'’][A-Za-z]+)*)([^A-Za-z]*)$", w)
    if not m or "f" not in m.group(2).lower():
        return w
    core = m.group(2)
    if core.lower() in english:
        return w
    if "fl" in core:
        # the double long s before i, read as the ligature fl ("impoflible", "poflefs")
        double = long_s(m.group(1) + core.replace("fl", "ff") + m.group(3), english)
        if re.sub(r"[^A-Za-z]", "", double).lower() in english:
            return double
    spots = [i for i, c in enumerate(core) if c == "f"]
    if len(spots) > 4:
        return w
    from itertools import combinations

    for k in range(1, len(spots) + 1):
        for combo in combinations(spots, k):
            cand = "".join("s" if i in combo else c for i, c in enumerate(core))
            if cand.lower() in english:
                return m.group(1) + cand + m.group(3)
    return w


def _omit(play: Play, scan: str, leaf: int, order: list[dict], spans: list | None = None) -> list[dict]:
    """The page's lines without a stretch Play.prose_omit leaves out; the line after the stretch
    (or, at the page's end, the line before it) carries the marker to write in its place. The
    stretch's (top, bottom) is added to `spans` (where the page is not read again for lines the
    OCR missed)."""
    for oscan, oleaf, first, last, marker in play.prose_omit:
        if oscan != scan or oleaf != leaf or not order:
            continue
        texts = [" ".join(w["text"] for w in l["words"]) for l in order]
        a = 0 if not first else next((i for i, t in enumerate(texts) if re.search(first, t)), None)
        b = len(order) - 1 if not last else next((i for i, t in enumerate(texts) if re.search(last, t) and i >= (a or 0)), None)
        if a is None or b is None:
            print(f"{play.slug}: leaf {leaf}: the stretch to leave out was not found ({first!r} … {last!r})")
            continue
        if spans is not None:
            spans.append((min(l["bbox"][1] for l in order[a:b + 1]), max(l["bbox"][3] for l in order[a:b + 1])))
        order = order[:a] + order[b + 1:]
        if marker and order:
            if a < len(order):
                order[a]["omit_before"] = marker
            else:
                order[-1]["omit_after"] = marker
    return order


def analyse_page(play: Play, kind: str, leaf: int, voc, names: set[str], scan: str | None = None) -> dict:
    """The page's text in Markdown with the flagged words, and the data for its crops."""
    from PIL import Image

    from .drama_pages import read_lines
    from .egt_ocr import check_words

    scan = scan or play.scan_for(kind)
    _, sbuild = scan_dirs(scan)
    img = Image.open(sbuild / "pages" / f"leaf_{leaf:04d}.png").convert("L")
    lines = read_lines(ocr_leaf(scan, leaf))
    doubtful: list[str] = []
    if play.long_s:
        for l in lines:
            for w in l["words"]:
                w["text"] = long_s(w["text"], voc[2])
                core = re.sub(r"[^A-Za-z]", "", w["text"]).lower()
                # a word that is English with f and with s (fame / same, fight / sight): the OCR cannot tell
                # (the long s never ends a word; "for", "from", "after", "before" are too common to list)
                if "f" in core and core in voc[2] and core not in ("for", "from", "after", "before", "few", "fell") and any(
                        (core[:i] + "s" + core[i + 1:]) in voc[2] for i, c in enumerate(core[:-1]) if c == "f"):
                    doubtful.append(core)
    order, mid = _region(play, kind, leaf, lines, img.size, scan)
    omitted: list[tuple[int, int]] = []
    order = _omit(play, scan, leaf, order, omitted)
    no_rule = mid == NO_RULE
    if no_rule:
        mid = 0
    ids = {id(x) for x in lines}
    lines.extend(l for l in order if id(l) not in ids)  # a line cut at the gutter: its pieces
    jebb =play.layout == "jebb" and kind in ("intro", "appendix")
    earle_page = earle_notes_page(play, kind, leaf, scan)  # Earle's notes on the hypothesis (intro)
    if jebb:
        order = _jebb_margins(order, img.size)
    # Earle's introduction (his volume's pages read as kind intro, not his notes on the hypothesis):
    # his notes in the outer margin, the verses he quotes, the accents Tesseract reads as a line
    earle_intro = (kind == "intro" and play.notes_layout == "earle" and scan == play.notes_scan and not earle_page)
    # Hayley's introduction: Greek verses he quotes set in on lines of their own
    hayley_intro = kind == "intro" and play.notes_layout == "hayley" and scan == play.notes_scan
    if earle_intro:
        order = _earle_margins(order, img.size)
    cols: dict[str, list[dict]] = {}
    for l in order:
        cols.setdefault(l["region"], []).append(l)
    # a printed line Tesseract skipped: where two lines of a column stand a line too far apart,
    # the strip between them is read again on its own
    for region, col in cols.items():
        if len(col) < 4:
            continue
        tops = [l["bbox"][1] for l in col]
        pitch = sorted(b - a for a, b in zip(tops, tops[1:]))[len(tops) // 2]
        h = sorted(l["bbox"][3] - l["bbox"][1] for l in col)[len(col) // 2]
        x0 = min(l["bbox"][0] for l in col) - 10
        x1 = max(l["bbox"][2] for l in col) + 10
        extra = []
        for a, b in zip(col, col[1:]):
            if b["bbox"][1] - a["bbox"][1] > 1.75 * pitch and not any(
                    y0 < b["bbox"][1] and a["bbox"][3] < y1 for y0, y1 in omitted):  # not a stretch left out
                near = {w["text"] for w in a["words"] + b["words"]}
                strip = (max(0, x0), a["bbox"][1] + int(0.7 * pitch), min(img.width, x1), b["bbox"][1] + int(0.25 * pitch))
                for l in _reread_strip(scan, leaf, strip):
                    sure = [w for w in l["words"] if w["conf"] >= 60 and len(w["text"]) >= 3]
                    if len(sure) >= 2 and sum(1 for w in sure if w["text"] in near) < 0.5 * len(sure):
                        l["region"] = region
                        l["reread"] = True
                        extra.append(l)
        if extra:
            lines.extend(extra)
            col.extend(extra)
            col.sort(key=lambda l: l["bbox"][1])
    order = [l for region in cols for l in cols[region]]
    # footnotes: lines in smaller type at the foot of the column, after a gap
    foot: dict[str, list[dict]] = {}
    for region, col in cols.items():
        sizes = sorted(l["x_size"] for l in col if l["x_size"])
        if len(col) < 6 or not sizes or (kind == "notes" and play.notes_layout in ("earle", "college", "back")) or earle_page:
            continue  # (Earle's notes have no footnotes; Tesseract's size of a short last line is no guide)
        xs = sizes[len(sizes) // 2]
        h = sorted(l["bbox"][3] - l["bbox"][1] for l in col)[len(col) // 2]
        k = len(col)
        while k > 0 and col[k - 1]["x_size"] and col[k - 1]["x_size"] <= 0.85 * xs:
            k -= 1
        if 0 < k < len(col) and col[k]["bbox"][1] - col[k - 1]["bbox"][3] > 0.35 * h:
            foot[region] = col[k:]
            cols[region] = col[:k]
            continue
        # or after a wider gap than the lines', beginning with a note's mark, in the lower part
        gaps = sorted(b["bbox"][1] - a["bbox"][3] for a, b in zip(col, col[1:]))
        usual = gaps[len(gaps) // 2] if gaps else 0
        for k in range(len(col) - 1, max(0, len(col) - 8), -1):
            first = " ".join(w["text"] for w in col[k]["words"])
            if (col[k]["bbox"][1] > 0.6 * img.height and col[k]["bbox"][1] - col[k - 1]["bbox"][3] > usual + 0.5 * h
                    and re.match(r"^[\d¹²³⁴⁵⁶⁷⁸⁹*†‡!]{1,2}\s", first)):
                foot[region] = col[k:]
                cols[region] = col[:k]
                break
    if kind == "intro" and play.intro_foot_columns and "one" in cols:
        # the two columns under the text are its footnotes
        for region in ("left", "right"):
            if region in cols:
                foot.setdefault("one", []).extend(cols.pop(region))
    idx = [lines.index(l) for l in order]
    flags = check_words(lines, idx, img, voc, names, leaf)
    # paragraphs: a line indented by about an em, a centred line, a line in capitals, or a line
    # beginning with a note's number begins one; so does a line after a short line that ends a
    # sentence
    paras: list[dict] = []
    # Jebb's Sophocles: the commentary under the rule; the college editions of Lysias (Adams,
    # Morgan: notes_layout "college") print their notes the same way under the text: a note opens
    # an indented paragraph with its number, further lemmas follow after a dash
    under = kind == "notes" and (play.app_rule == "under" or play.notes_layout == "college")
    back = kind == "notes" and play.notes_layout == "back"  # Shuckburgh's Lysias: notes at the back by his own lines
    earle = kind == "notes" and play.notes_layout == "earle"  # Earle's Medea: notes run on inside paragraphs
    hayley = kind == "notes" and play.notes_layout == "hayley"  # Hayley's Alcestis: further lemmas run on
    for region, col in cols.items():
        lefts = sorted(l["bbox"][0] for l in col)
        left = lefts[len(lefts) // 5] if lefts else 0
        rights = sorted(l["bbox"][2] for l in col)
        right = rights[int(len(rights) * 0.8)] if rights else 0
        h = sorted(l["bbox"][3] - l["bbox"][1] for l in col)[len(col) // 2] if col else 30
        prev = None
        for l in col:
            text = " ".join(w["text"] for w in l["words"])
            indent = l["bbox"][0] - left
            centred = (abs((l["bbox"][0] + l["bbox"][2]) / 2 - (left + right) / 2) < 2 * h
                       and (l["bbox"][2] - l["bbox"][0]) < 0.6 * (right - left))
            caps = _capitals(text) and len(text) < 90
            # (Earle's numbers are found inside the paragraph by earle_markdown; a paragraph begins
            # with an indented line)
            numbered = kind == "notes" and not earle and note_heading(text, play.note_start) is not None
            short_end = prev is not None and prev["bbox"][2] < right - 3 * h and re.search(r"[.?!:]['’”)]?$", prev["text"])
            if jebb and prev is not None and prev["bbox"][2] < right - 1.5 * h and re.match(r"^(?:\d{1,2}|[IlΙ1]{1,2})\.\s", text):
                short_end = True  # an item of a numbered list (the structure of the play) after a short line
            if (under or hayley) and numbered and indent <= 0.8 * h:
                # Jebb begins every note with an indented line: a figure at the start of a line
                # flush with the column is a reference run on (Thuc. 4. | 117; "7. 110" at the
                # top of a column; Hayley's "O. C. 1138." read "0. C.")
                numbered = False
            verse = (earle_intro and not caps and indent > 3 * h and l["bbox"][2] < right - 1.5 * h)
            if hayley_intro:
                verse = not caps and indent > 3 * h and l["bbox"][2] < right - 1.5 * h and _greek_share(text) >= 0.5
                # (his chapter titles are long: "C. THE CRITICAL BASIS FOR THE TEXT." fills 0.63 of the line)
                centred = (abs((l["bbox"][0] + l["bbox"][2]) / 2 - (left + right) / 2) < 2 * h
                           and (l["bbox"][2] - l["bbox"][0]) < 0.75 * (right - left))
                centred = centred and not verse and (caps or _greek_share(text) < 0.3)
            if earle_intro:
                centred = centred and caps  # Earle centres only his headings; the verses he quotes are set in
            new = (prev is None or indent > 0.8 * h or centred or caps or numbered or bool(short_end)
                   or (prev is not None and prev["caps"]))
            if earle_intro and not verse and not caps and indent > 3 * h and prev is not None and not short_end:
                new = False  # a line shortened beside a note in the left margin, not a paragraph's start
            if (earle_intro or hayley_intro) and prev is not None and (verse or prev.get("verse")):
                # the verses he quotes: one paragraph, its lines separated by " | "
                new = verse != bool(prev.get("verse")) or (not verse and new)
            if (under or earle or earle_page) and prev is None and region == "right" and paras and not (indent > 0.8 * h or numbered or centred):
                new = False  # the paragraph runs on from the foot of the left column
            entry = {"text": text, "bbox": l["bbox"], "centred": centred, "caps": caps, "margin": l.get("margin"),
                     "words": l["words"], "verse": verse, "omit_before": l.get("omit_before"), "omit_after": l.get("omit_after")}
            if new or not paras:
                paras.append({"lines": [entry], "region": region, "indent": indent > 0.8 * h})
            else:
                paras[-1]["lines"].append(entry)
            prev = entry
        for l in foot.get(region, []):
            text = " ".join(w["text"] for w in l["words"])
            if paras and paras[-1].get("foot") and not re.match(r"^[\d¹²³⁴⁵⁶⁷⁸⁹*†‡!]", text):
                paras[-1]["lines"].append({"text": text})
            else:
                paras.append({"lines": [{"text": text}], "region": region, "indent": False, "foot": True})
    md: list[str] = []
    cands: list[dict] = []
    if jebb:
        md = _jebb_markdown(paras, kind, cands)
    for k, p in enumerate([] if jebb else paras):
        text = _join_lines([x["text"] for x in p["lines"]])
        before = next((x["omit_before"] for x in p["lines"] if x.get("omit_before")), None)
        if before:
            md += [before, ""]  # a stretch left out by rule (Play.prose_omit) stood here
        if p.get("foot"):
            if hayley and not re.search(r"[A-Za-zͰ-Ͽἀ-῿]{4}", text):
                continue  # specks at the foot of Hayley's page read as a footnote ("A hd", "».»»")
            md.append(f"[Note: {text}]")
            md.append("")
            continue
        heading = len(p["lines"]) == 1 and (p["lines"][0]["caps"] or (p["lines"][0]["centred"] and len(text) < 80))
        if earle:
            md += earle_markdown(earle_clean(text), cands, "+ " if k == 0 and not p["indent"] else "")
            continue
        if earle_page:
            # his notes on the hypothesis, keyed to the lines of his printing of it: each note a
            # paragraph of its own, its number kept in the text ("8. **δρακόντων πτερωτῶν**: …")
            local: list[dict] = []
            for x in earle_markdown(earle_clean(text), local, "+ " if k == 0 and not p["indent"] else ""):
                mm = re.fullmatch("\x00(\\d+)", x)
                if not mm:
                    md.append(x)
                    continue
                c = local[int(mm.group(1))]
                body = c["body"] or [""]
                md += [(c["alone"] + c["label"] + " " + body[0]).rstrip()] + [y for piece in body[1:] for y in ("", piece)]
            continue
        if hayley:
            # Hayley's notes: the title over the first page (CRITICAL AND EXEGETICAL NOTES.) and his
            # bracketed list of the editions he cites from under it are left out (PLAN-drama.md: lists of
            # editions are not transcribed); the heading is settled over the pages
            # (_resolve_note_headings); a further lemma inside the paragraph begins one of its own
            if p["lines"][0]["caps"] and len(p["lines"]) == 1:
                continue
            if text.startswith("[") and text.rstrip().endswith("]") and not cands and re.search(r"edition", text):
                continue
            text = hayley_clean(text)
            h = note_heading(text, play.note_start)
            if h and p["indent"]:
                cands.append({"kind": "note", "n": h[0], "body": hayley_split(text[h[1]:].strip(), first=True),
                              "orig": hayley_split(text), "back": HAYLEY_BACK})
                md += [f"\x00{len(cands) - 1}", ""]
                continue
            pieces = hayley_split(text)
            if k == 0 and not p["indent"]:
                pieces[0] = "+ " + pieces[0]  # the note runs on from the page before
            for piece in pieces:
                md += [piece, ""]
            continue
        if under:
            # Jebb's Sophocles: the heading is settled over the pages (_resolve_note_headings);
            # a further bold lemma after a dash begins a paragraph of its own, as in Perseus's files
            text = jebb_f(jebb_dashes(text))
            lem = college_lemma if play.notes_layout == "college" else None
            h = note_heading(text, play.note_start)
            if h:
                cands.append({"kind": "note", "n": h[0], "body": split_lemmas(text[h[1]:].strip(), first=True, lemma=lem),
                              "orig": split_lemmas(text, lemma=lem)})
                md += [f"\x00{len(cands) - 1}", ""]
                continue
            pieces = split_lemmas(text, first=p["indent"], lemma=lem)  # an indented paragraph begins with a lemma
            if k == 0 and not p["indent"] and not (lem and text.lstrip().startswith("—")):
                # the note runs on from the page before (but a page of a college edition that opens
                # with a dash and a lemma opens a new paragraph of the note before: no run-on mark)
                pieces[0] = "+ " + pieces[0]
            for piece in pieces:
                md += [piece, ""]
            continue
        if back and len(p["lines"]) == 1 and ORATION_HEAD.match(text.strip()):
            md += ["# Introduction", ""]  # the speech's heading: his introduction to it follows, then the notes
            continue
        if kind == "notes":
            h = note_heading(text, play.note_start)
            if back and h and not p["indent"]:
                h = None  # a figure at the start of a line flush with the column is a reference run on
            if h:
                n, end = h
                md.append(f"## {n}")
                body = back_lemma(text[end:].strip()) if back else bold_lemma(text[end:].strip())
                if body:
                    md.append(body)
                md.append("")
                continue
            if k == 0 and not p["indent"]:
                text = "+ " + text  # the note runs on from the page before
            elif back and p["indent"] and "# Introduction" not in md[-12:] and any(x.startswith("## ") for x in md):
                text = back_lemma(text)  # a further note on the same line: an indented paragraph that opens with its lemma
        elif kind == "intro":
            if p["lines"][0].get("verse"):
                text = " | ".join(x["text"].strip() for x in p["lines"])
            margins = [x["margin"] for x in p["lines"] if x.get("margin")]
            m = re.match(r"^§\s*(\d+)\.?\s*(.*)$", text)
            if not m and play.notes_layout == "earle" and scan == play.notes_scan and p["indent"]:
                # Earle numbers the paragraphs of his introduction through all its chapters ("1. Of the
                # facts of Euripides's personal life …"): each a section, `## § 1`
                m = re.match(r"^(\d{1,2})\.\s+(?=[A-Z‘“(])(.*)$", text)
            if m:
                # a note in the margin beside the section's paragraph after a dash, as Jebb's
                md.append(f"## § {m.group(1)}" + (" — " + "; ".join(margins) if margins else ""))
                md.append("")
                text = m.group(2)
                if not text:
                    continue
                margins = []
            elif heading and play.notes_layout == "hayley" and scan == play.notes_scan:
                # Hayley's introduction: its title and his lettered chapters (A. THE MYTH OF ALCESTIS.)
                # `# `, the subtitles and numbered parts under them (Its History and Literary
                # Treatment., I. The Alcestis and the Stage-question.) `## `; the line naming the
                # chapter's author (BY JAMES M. PATON, PH.D.) a paragraph
                if re.match(r"^BY\s", text):
                    md += [text, ""]
                    continue
                top = re.match(r"^(?:[A-F]\.\s|INTRODUCTION\b)", text)
                words = title_case(text) if _capitals(text) else text.strip(" .")
                words = re.sub(r"^([A-F]\. )(\w)", lambda mm: mm.group(1) + mm.group(2).upper(), words)  # A. The Myth
                last_md = next((x for x in reversed(md) if x), "")
                if not top and _capitals(text) and last_md.startswith("# ") and md and md[-1] == "" \
                        and p["lines"][0].get("caps") and k > 0 and paras[k - 1]["lines"][-1].get("caps"):
                    # a chapter's title in capitals turned over to a second line (… REPRESENTATION OF | THE PLAY.)
                    md[-2] = last_md + " " + title_case(text)[:1].lower() + title_case(text)[1:]
                    continue
                md += [("# " if top else "## ") + words, ""]
                continue
            elif heading:
                md.append("# " + (title_case(text) if _capitals(text) else text.strip(" .")))
                md.append("")
                continue
            elif k == 0 and not p["indent"]:
                text = "+ " + text
            if margins:
                # a note in the margin beside a paragraph that opens no section: in italics before it
                text = re.sub(r"^(\+ )?", lambda mm: (mm.group(1) or "") + f"*{'; '.join(margins)}* ", text, count=1)
        elif kind == "trans":
            m = re.match(r"^([A-Z][A-Za-z]+(?:\s[A-Z][A-Za-z]+)?)\.\s+(.*)$", text)
            if m:
                md.append(f"@ {m.group(1).title()}")
                text = "N\t" + m.group(2)
            elif heading:
                continue  # AGON II, ODE: the Greek text carries the sections
            elif k == 0 and not p["indent"]:
                text = "+ " + text
        md.append(text)
        md.append("")
        after = next((x["omit_after"] for x in p["lines"] if x.get("omit_after")), None)
        if after:
            md += [after, ""]
    return {"leaf": leaf, "md": "\n".join(md).strip(), "flags": flags, "lines": lines, "mid": mid,
            "order": idx, "size": list(img.size), "scan": scan, "cands": cands, "no_rule": no_rule,
            "long_s": sorted(set(doubtful))}


def _crops(play: Play, kind: str, page: dict, out_dir: Path, stem: str) -> None:
    """p-NNNN-flags.png: each line with a flagged word, numbered, the word boxed; the columns."""
    from PIL import Image, ImageDraw, ImageFont

    _, sbuild = scan_dirs(page.get("scan") or play.scan_for(kind))
    img = Image.open(sbuild / "pages" / f"leaf_{page['leaf']:04d}.png").convert("L")
    lines = page["lines"]
    try:
        font = ImageFont.truetype("DejaVuSans-Bold.ttf", 30)
    except OSError:
        font = ImageFont.load_default()
    by_line: dict[int, list[tuple[int, dict]]] = {}
    for k, f in enumerate(page["flags"], 1):
        by_line.setdefault(f["line"], []).append((k, f))
    crops = []
    for li in sorted(by_line, key=lambda li: page["order"].index(li) if li in page["order"] else li):
        x0, y0, x1, y1 = lines[li]["bbox"]
        h = y1 - y0
        cx, cy = max(0, x0 - 20), max(0, y0 - h // 2)
        c = img.crop((cx, cy, min(img.width, x1 + 20), min(img.height, y1 + h // 2))).convert("RGB")
        d = ImageDraw.Draw(c)
        for k, f in by_line[li]:
            w = lines[li]["words"][f["word"]]
            d.rectangle([w["bbox"][0] - cx - 3, w["bbox"][1] - cy - 3, w["bbox"][2] - cx + 3, w["bbox"][3] - cy + 3],
                        outline=(220, 0, 0), width=3)
        crops.append((",".join(str(k) for k, _f in by_line[li]), c))
    if crops:
        label_w = 130
        sheet = Image.new("RGB", (label_w + max(c.width for _n, c in crops), sum(c.height + 8 for _n, c in crops)), (255, 255, 255))
        dr = ImageDraw.Draw(sheet)
        y = 0
        for n, c in crops:
            sheet.paste(c, (label_w, y))
            dr.text((6, y + c.height // 2 - 16), n, fill=(0, 0, 0), font=font)
            dr.line((0, y + c.height + 3, sheet.width, y + c.height + 3), fill=(170, 170, 170), width=2)
            y += c.height + 8
        sheet.save(out_dir / f"{stem}-flags.png", optimize=True)
    regions: dict[str, list[list[int]]] = {}
    for li in page["order"]:
        regions.setdefault(lines[li].get("region", "one"), []).append(lines[li]["bbox"])
    for region, boxes in regions.items():
        x0 = min(b[0] for b in boxes) - 15
        y0 = min(b[1] for b in boxes) - 15
        x1 = max(b[2] for b in boxes) + 15
        y1 = max(b[3] for b in boxes) + 15
        c = img.crop((max(0, x0), max(0, y0), min(img.width, x1), min(img.height, y1)))
        if region != "one":
            c = c.resize((int(c.width * 1.4), int(c.height * 1.4)), Image.LANCZOS)
        c.save(out_dir / f"{stem}-col-{'r' if region == 'right' else 'l'}.png", optimize=True)


def transcriptions_for(play: Play) -> Path:
    """Where a text's batch files are: transcriptions/drama/<slug>, or transcriptions/lucian/<slug>
    for a text read by lucian_pages.py (Play.page_offset set)."""
    if play.route == "lake":
        return PIPELINE / "transcriptions" / play.slug
    return PIPELINE / "transcriptions" / ("lucian" if play.page_offset else "drama") / play.slug


def write_draft(slug: str, kind: str) -> list[dict]:
    from .egt_ocr import FLAG_KINDS, vocabularies

    play = PLAYS[slug]
    voc = vocabularies()
    pages: list[dict] = []
    for scan, leaves in play.sources_for(kind):
        names = _names(scan, leaves, voc)
        with ThreadPoolExecutor(int(os.environ.get("DRAMA_WORKERS", "4"))) as ex:
            pages += list(ex.map(lambda l: analyse_page(play, kind, l, voc, names, scan), leaves))
    if play.layout == "jebb" and kind in ("intro", "appendix"):
        _resolve_headings(pages, kind, last_line(play))
    if kind == "notes" and (play.app_rule == "under" or play.notes_layout == "college"):
        _resolve_note_headings(pages, last_line(play))
    if kind == "notes" and play.notes_layout == "earle":
        _resolve_note_headings(pages, last_line(play), EARLE_WINDOW)
    if kind == "notes" and play.notes_layout == "hayley":
        _resolve_note_headings(pages, last_line(play))
    top = route_dir("drama-prose", slug, play.scan_for(kind)) if kind not in play.notes_sources else prose_dir(play, kind, play.scan_for(kind)).parent
    index = []
    trans_starts = _greek_speech_starts(slug) if kind == "trans" else {}
    for b, page in enumerate(pages):
        stem = page_stem(play, kind, page["scan"], page["leaf"])
        page["stem"] = stem
        out_dir = prose_dir(play, kind, page["scan"])
        # the translation's pages are also the commentary's (Starkie): its crops get their own names
        _crops(play, kind, page, out_dir, f"trans-{stem}" if kind == "trans" else stem)
        if kind == "trans":
            page["md"] = _number_speeches(page["md"], trans_starts.get(page["leaf"] - 1, []), play)
        index.append({"stem": stem, "leaf": page["leaf"], "batch": b // PAGES_PER_BATCH + 1, "flags": len(page["flags"]),
                      "scan": page["scan"], "dir": str(out_dir.relative_to(PIPELINE))})
        if page.get("no_rule"):
            index[-1]["no_rule"] = True
    (top / f"{kind}.json").write_text(json.dumps(index, indent=1), encoding="utf-8")
    out_dir = top
    tdir = transcriptions_for(play)
    tdir.mkdir(parents=True, exist_ok=True)
    for b in range(0, len(pages), PAGES_PER_BATCH):
        path = tdir / f"{kind}-{b // PAGES_PER_BATCH + 1:02d}.md"
        if path.exists():
            continue
        out = []
        for page in pages[b : b + PAGES_PER_BATCH]:
            out.append(f"=== {page['stem']}")
            out.append(page["md"])
            out.append("--- flags")
            for k, f in enumerate(page["flags"], 1):
                alt = f" (Greek model: {f['alt']})" if f.get("alt") and f["alt"] != f["text"] else ""
                out.append(f"{k} {f['token']} [{f['kind']}]{alt} →")
            out.append("--- notes")
            if page.get("long_s"):
                out.append("DRAFT: long s. These words on the page are English with f and with s; read each on the image "
                           "(the long s has no cross-stroke, or one on the left only): " + ", ".join(page["long_s"]))
            if page.get("no_rule"):
                out.append("DRAFT: no rule was found on this page, so the commentary's region is unknown and nothing "
                           "was drafted: transcribe the commentary under the rule from the page image, and say so here.")
            out.append("")
        path.write_text("\n".join(out), encoding="utf-8")
    (out_dir / "FLAG_KINDS.md").write_text("\n".join(f"* **{k}**: {v}" for k, v in FLAG_KINDS.items()) + "\n", encoding="utf-8")
    return index


def _names(scan: str, leaves: list[int], voc) -> set[str]:
    """Capitalised words in Latin letters that the OCR read with confidence at least three times
    (the scholars' names: Hermann, Wecklein, Paley), taken as known."""
    from collections import Counter

    from .egt_ocr import TOKEN, _script
    from .gorgias_pages import read_hocr

    _, sbuild = scan_dirs(scan)
    _, _, english = voc
    seen: Counter[str] = Counter()
    for leaf in leaves:
        p = sbuild / "hocr" / f"leaf_{leaf:04d}.eng.hocr"
        if not p.exists():
            continue
        for l in read_hocr(p):
            for w in l["words"]:
                for tok in TOKEN.findall(w["text"]):
                    if tok[:1].isupper() and not tok.isupper() and _script(tok) == "latin" and w["conf"] >= 90 and tok.lower() not in english:
                        seen[tok] += 1
    return {t for t, n in seen.items() if n >= 3}


# --- Jebb's Sophocles: the chapters before the text and the Appendix -------------------------------

_GREEK_LETTER = re.compile(r"[Ͱ-Ͽἀ-῿]")
_DIGITS = str.maketrans({"I": "1", "l": "1", "Ι": "1", "ι": "1", "|": "1", "o": "0", "O": "0", "ο": "0", "Ο": "0"})


def _jebb_margins(order: list[dict], size: tuple[int, int]) -> list[dict]:
    """Jebb's notes in the outer margin of the manuscripts chapter (MSS., Scholia., The theory of
    two recensions.): the words beyond the edge of the justified lines, taken out of their lines
    and attached, as l["margin"], to the line of the text beside which the note begins. Specks at
    the page's edge and tall boxes (the binding, a library stamp) are dropped. Returns the lines
    left."""
    W, _H = size
    if not order:
        return order
    hs = sorted(l["bbox"][3] - l["bbox"][1] for l in order)
    h = hs[len(hs) // 2]
    keep = [l for l in order if not (l["bbox"][0] > 0.94 * W or l["bbox"][2] < 0.06 * W or l["bbox"][3] - l["bbox"][1] > 3 * h)]
    # a column of numbers that Tesseract took for one tall line (5. 6. 7. 8. 9. of the structure
    # of the play): each word put back at the start of the line it stands beside
    for tall in [l for l in order if l["bbox"][3] - l["bbox"][1] > 3 * h and 0.06 * W < l["bbox"][0] < 0.94 * W]:
        for w in tall["words"]:
            y = (w["bbox"][1] + w["bbox"][3]) / 2
            beside = [l for l in keep if l["bbox"][1] <= y <= l["bbox"][3] and l["bbox"][0] > w["bbox"][2]]
            if beside:
                beside[0]["words"].insert(0, w)
                beside[0]["bbox"] = [w["bbox"][0]] + beside[0]["bbox"][1:]
    full = [l for l in keep if len(l["words"]) >= 5]

    def edge(values: list[int]) -> int | None:
        # the x at which most lines begin (end), if at least five lines share it
        best: list[int] = []
        for v in values:
            near = [u for u in values if abs(u - v) <= 0.006 * W]
            if len(near) > len(best):
                best = near
        return sorted(best)[len(best) // 2] if len(best) >= 5 else None

    right = edge([l["bbox"][2] for l in full])
    left = edge([l["bbox"][0] for l in full])
    # the edge must bound the bulk of the page's text (verses set in, or a list, share an edge
    # too, with the wider lines of a note or of prose beyond it: not margin notes)
    x1s = sorted(l["bbox"][2] for l in full)
    x0s = sorted(l["bbox"][0] for l in full)
    if right is not None and right < x1s[int(0.75 * len(x1s))] - 0.01 * W:
        right = None
    if left is not None and left > x0s[int(0.25 * len(x0s))] + 0.01 * W:
        left = None
    found: list[tuple[int, dict]] = []  # (y, word)
    body: list[dict] = []
    for l in keep:
        out = [w for w in l["words"] if (right is not None and w["bbox"][0] > right + 0.1 * h)
               or (left is not None and w["bbox"][2] < left - 0.1 * h)]
        if out and (len(out) > 4 or max(w["bbox"][2] for w in out) - min(w["bbox"][0] for w in out) > 0.15 * W):
            out = []  # too much for a margin note
        if out and all(re.fullmatch(r"[\dIlΙ|oOο]{1,4}", w["text"]) for w in out):
            # the line numbers in the margin of an argument's Greek text: left out
            l["words"] = [w for w in l["words"] if w not in out]
            if not l["words"]:
                continue
            out = []
        if out:
            found += [(w["bbox"][1], w) for w in out]
            l["words"] = [w for w in l["words"] if w not in out]
            if not l["words"]:
                continue
            l["bbox"] = [min(w["bbox"][0] for w in l["words"]), min(w["bbox"][1] for w in l["words"]),
                         max(w["bbox"][2] for w in l["words"]), max(w["bbox"][3] for w in l["words"])]
        body.append(l)
    found.sort(key=lambda t: (t[0], t[1]["bbox"][0]))
    notes: list[list[dict]] = []  # a note's lines follow one another closely
    for y, w in found:
        if notes and y - notes[-1][-1]["bbox"][1] < 2.0 * h:
            notes[-1].append(w)
        else:
            notes.append([w])
    for note in notes:
        # the words of the note's lines in reading order, a word divided at a line end joined
        lines_of: list[list[dict]] = []
        for w in sorted(note, key=lambda w: w["bbox"][1]):
            if lines_of and abs(w["bbox"][1] - lines_of[-1][0]["bbox"][1]) < 0.5 * h:
                lines_of[-1].append(w)
            else:
                lines_of.append([w])
        text = _join_lines([" ".join(x["text"] for x in sorted(ws, key=lambda w: w["bbox"][0])) for ws in lines_of])
        y = (note[0]["bbox"][1] + note[0]["bbox"][3]) / 2
        if body:
            near = min(body, key=lambda l: abs((l["bbox"][1] + l["bbox"][3]) / 2 - y))
            near["margin"] = (near["margin"] + " " + text) if near.get("margin") else text
    return body


def _earle_margins(order: list[dict], size: tuple[int, int]) -> list[dict]:
    """Earle's introduction: his notes in the outer margin ("Sources", "Birth and death",
    "Parentage"), set in smaller bold type into a space left beside two or three shortened lines
    (at the right of a right-hand page, the left of a left-hand page), taken out and attached, as
    l["margin"], to the nearest line of the text; Tesseract reads such a note as a line of its own
    (smaller type, three words at most, in the outer fifth of the page) or as the last (first)
    words of a shortened line after a wide space. The accents of quoted Greek verses that
    Tesseract reads as a line of their own (tiny type) are dropped."""
    W, _H = size
    if not order:
        return order
    sizes = sorted(l["x_size"] for l in order if len(l["words"]) >= 4 and l["x_size"])
    med = sizes[len(sizes) // 2] if sizes else 0
    hs = sorted(l["bbox"][3] - l["bbox"][1] for l in order if len(l["words"]) >= 4)
    h = hs[len(hs) // 2] if hs else 30
    right = max((l["bbox"][2] for l in order if len(l["words"]) >= 4), default=W)
    keep = [l for l in order if not (med and l["x_size"] < 0.6 * med and l["bbox"][3] - l["bbox"][1] < 0.6 * h)
            and (re.search(r"[A-Za-zͰ-Ͽἀ-῿]{3}|\d{2}", " ".join(w["text"] for w in l["words"])) or len(l["words"]) < 2)]
    found: list[tuple[float, str]] = []
    body: list[dict] = []
    for l in keep:
        ws = l["words"]
        text = " ".join(w["text"] for w in ws)
        if (len(ws) <= 3 and med and l["x_size"] <= 0.85 * med and re.search(r"[A-Za-z]{3}", text)
                and (l["bbox"][0] >= 0.76 * W or l["bbox"][2] <= 0.24 * W)):
            found.append(((l["bbox"][1] + l["bbox"][3]) / 2, text))
            continue
        out: list[dict] = []
        wh = sorted(w["bbox"][3] - w["bbox"][1] for w in ws)
        for i in range(len(ws) - 1):
            gap = ws[i + 1]["bbox"][0] - ws[i]["bbox"][2]
            after, before = ws[i + 1:], ws[: i + 1]
            # (at the right only: on a left-hand page Tesseract reads the note as a line of its own)
            if (gap >= 25 and len(after) <= 3 and len(before) >= 3 and after[0]["bbox"][0] >= 0.76 * W
                    and before[-1]["bbox"][2] <= 0.81 * W and after[-1]["bbox"][2] <= right - 12
                    and max(w["bbox"][3] - w["bbox"][1] for w in after) <= 0.85 * wh[len(wh) // 2]):
                out = after
                break
        if out and re.search(r"[A-Za-z]{3}", " ".join(w["text"] for w in out)):
            found.append(((out[0]["bbox"][1] + out[0]["bbox"][3]) / 2, " ".join(w["text"] for w in out)))
            rest = [w for w in ws if w not in out]
            l["words"] = rest
            l["bbox"] = [min(w["bbox"][0] for w in rest), l["bbox"][1], max(w["bbox"][2] for w in rest), l["bbox"][3]]
        body.append(l)
    # the lines of one note (Birth | and death) follow one another closely
    notes: list[list[tuple[float, str]]] = []
    for y, t in sorted(found):
        if notes and y - notes[-1][-1][0] < 1.6 * h:
            notes[-1].append((y, t))
        else:
            notes.append([(y, t)])
    for note in notes:
        text = _join_lines([t for _y, t in note])
        y = note[0][0]
        if body:
            near = min(body, key=lambda l: abs((l["bbox"][1] + l["bbox"][3]) / 2 - y))
            near["margin"] = (near["margin"] + " " + text) if near.get("margin") else text
    return body


def _greek_share(text: str) -> float:
    letters = [c for c in text if c.isalpha()]
    return sum(1 for c in letters if _GREEK_LETTER.match(c)) / len(letters) if letters else 0.0


def _greek_caps(text: str) -> bool:
    """A line in Greek capitals, though the English model may have read it in Latin letters that
    look alike (ΔΙΑ ΤΙ ΤΥΡΑΝΝΟΣ read as ATA TI TYPANNOS; Σ as S or 3, Ω as Q, Π as II)."""
    letters = [c for c in text if c.isalpha()]
    like = sum(1 for c in letters if _GREEK_LETTER.match(c) or c in "ABEHIKMNOPTXYZQS")
    return len(letters) >= 4 and like >= 0.85 * len(letters)


def _bold_lemma_lead(text: str) -> tuple[str, str]:
    """An Appendix note's lemma: the Greek at the start of the text up to where Jebb's English
    begins (a word in Latin letters of four letters or more, or two such words in a row; the OCR
    reads short Greek words as Latin: yap, ov). Returns (lemma, the rest); ('', text) if none."""
    words = text.split(" ")
    end = len(words)
    for i, w in enumerate(words):
        core = re.sub(r"[^A-Za-z]", "", w)
        if not core:
            continue
        nxt = re.sub(r"[^A-Za-z]", "", words[i + 1]) if i + 1 < len(words) else ""
        if len(core) >= 4 or (nxt and not _GREEK_LETTER.search(words[i + 1])):
            end = i
            break
    lemma = " ".join(words[:end]).strip()
    if not re.search(r"[Ͱ-Ͽἀ-῿]{2}", lemma):
        return "", text
    return lemma, " ".join(words[end:]).strip()


def _jebb_markdown(paras: list[dict], kind: str, cands: list[dict]) -> list[str]:
    """The Markdown of a page of Jebb's chapters before the text (intro) or of his Appendix: see
    the module's docstring. A paragraph that may begin a numbered section or an Appendix note is
    written as a placeholder line (\x00k, cands[k]) that _resolve_headings settles."""
    # verses quoted on lines of their own (short lines in Greek): one paragraph, lines joined by |
    merged: list[dict] = []
    for p in paras:
        one = len(p["lines"]) == 1 and not p.get("foot")
        verse = (one and _greek_share(p["lines"][0]["text"]) >= 0.7 and not p["lines"][0]["caps"]
                 and not re.match(r"^\S{1,3}\.\s", p["lines"][0]["text"]))
        if verse and merged and merged[-1].get("verse"):
            merged[-1]["lines"][0]["text"] += " | " + p["lines"][0]["text"]
            continue
        if verse:
            p = dict(p, verse=True, lines=[dict(p["lines"][0])])
        merged.append(p)
    md: list[str] = []
    persons: tuple[list[str], list[str]] | None = None
    title = argument = args = False  # args: on the pages of the ancient arguments
    bold_next = ""
    k = 0
    while k < len(merged):
        p = merged[k]
        first = k == 0
        k += 1
        text = _join_lines([x["text"] for x in p["lines"]])
        if p.get("foot") and not args:
            md += [f"[Note: {text}]", ""]
            continue
        line0 = p["lines"][0]
        heading = len(p["lines"]) == 1 and (line0["caps"] or (line0["centred"] and len(text) < 80)) and not p.get("verse")
        if heading and sum(c.isalpha() for c in text) < 0.5 * len(text.replace(" ", "")) \
                and not re.fullmatch(r"[IVXlΙ1T]{1,4}[.,]?", text.strip()):
            heading = False  # the accents of a Greek line read as a line of their own: no heading
        if persons is not None:
            letters = [c for c in text if c.isalpha()]
            if len(p["lines"]) == 1 and letters and sum(c.isupper() for c in letters) >= 0.6 * len(letters):
                # ΔΗΙΑΝΕΙΡΑ.   ΑΓΓΕΛΟΣ.: the names in two columns, the left one read first
                ws = line0["words"]
                h = max(1, line0["bbox"][3] - line0["bbox"][1])
                cut = next((i for i in range(1, len(ws)) if ws[i]["bbox"][0] - ws[i - 1]["bbox"][2] > 3 * h), len(ws))
                persons[0].append(" ".join(w["text"] for w in ws[:cut]))
                if cut < len(ws):
                    persons[1].append(" ".join(w["text"] for w in ws[cut:]))
                continue
            md += [" · ".join(persons[0] + persons[1]), ""]
            persons = None
        if re.search(r"[ΣΞ]ΟΦΟΚΛ|ΟΦΟΚΛΕ", text) and len(p["lines"]) <= 3 and len(text) < 80:
            # the play's title over the pages before the text (ΣΟΦΟΚΛΕΟΥΣ | ΤΡΑΧΙΝΙΑΙ): not written;
            # the ancient argument (or Jebb's note in its place) follows
            md += ["# The ancient argument", ""]
            title, argument, args = len(p["lines"]) == 1, True, True
            continue
        if title:
            title = False
            if heading and _greek_share(text) >= 0.5 and not re.search(r"ΥΠΟΘΕΣ|ΠΡΟΣ|IIPO", text):
                continue  # the play's name, on a line of its own
        if heading and re.search(r"ΠΡΟΣ|IIPO|ΙΙΡΟ", text):  # ΤΑ ΤΟΥ ΔΡΑΜΑΤΟΣ ΠΡΟΣΩΠΑ, read as Latin too
            md += ["## The persons of the drama", ""]
            persons = ([], [])
            argument = False
            continue
        if heading and re.search(r"STRUCTURE", text, re.I):
            md += ["## Structure of the play", ""]
            argument = False
            continue
        if heading and kind == "intro" and re.fullmatch(r"[IVXlΙ1T]{1,4}[.,]?", text.strip()):
            # I. II. III. over the arguments of the Oedipus Tyrannus
            roman = re.sub(r"[lΙ1T]", "I", text.strip().rstrip(".,"))
            md += [f"## {roman}. The argument", ""]
            argument = False
            continue
        if heading and kind == "intro" and (args or _greek_caps(text) or re.search(r"ΥΠΟΘΕΣ|YIIO", greek.strip_diacritics(text).upper())) and (
                _capitals(text) or re.search(r"ΥΠΟΘΕΣ", greek.strip_diacritics(text).upper())):
            # a heading in Greek capitals (ΥΠΟΘΕΣΙΣ, ΑΛΛΩΣ., ΧΡΗΣΜΟΣ …): its paragraph's first words, in bold
            if argument:
                md += ["## The argument", ""]
                argument = False
            bold_next = (bold_next + " " if bold_next else "") + f"**{text.strip()}**"
            continue
        if heading and _capitals(text) and kind == "appendix":
            if re.fullmatch(r"\W*APPENDIX\W*", text):
                continue
            md += ["### " + title_case(text) + ("." if text.rstrip().endswith(".") else ""), ""]
            continue
        if heading and _capitals(text):
            words = text.strip().lower()
            words = words if words.endswith("etc.") else words.rstrip(" .")
            md += ["# " + words[:1].upper() + words[1:], ""]
            continue
        if argument:
            md += ["## The argument", ""]
            argument = False
        if bold_next:
            text = bold_next + " " + text
            bold_next = ""
        margin = next((x["margin"] for x in p["lines"] if x.get("margin")), None)
        prefix = "+ " if first and not p["indent"] else ""
        if kind == "intro" and (p["indent"] or first):
            # § 1. read as "§ I.", "δι.", "56.", "8.7.": a sign before the number (a numbered list
            # without one, 1. πρόλογος, is no section)
            m1 = re.match(r"^(§|δ|S|s|8|5)\s*\.?\s*([0-9IlΙι|oOοΟ]{1,2})\s*\.\s+", text)
            nums = []
            if m1 and m1.group(2).translate(_DIGITS).isdigit():
                nums.append((int(m1.group(2).translate(_DIGITS)), m1.end()))
            if nums:
                cands.append({"kind": "sec", "nums": [n for n, _e in nums], "explicit": bool(m1 and m1.group(1) == "§"),
                              "margin": margin, "bodies": [text[e:] for _n, e in nums],
                              "orig": prefix + (f"*{margin}* " if margin else "") + text})
                md += [f"\x00{len(cands) - 1}", ""]
                continue
        if kind == "appendix" and (p["indent"] or first):
            # "11—14 As to", "29 f. νὺξ", "1526. οὔ τις" (the Oedipus Tyrannus prints a stop)
            m = re.match(r"^([0-9IlΙ|oOο]{1,4})(?:\s*[-—–]+\s*([0-9IlΙ|oOο]{1,4}))?(?:\s*([fἢἔ]{1,2})[.,]|\.)?(?=\s|$)", text)
            if m and m.group(1).translate(_DIGITS).isdigit() and (not m.group(2) or m.group(2).translate(_DIGITS).isdigit()):
                read = m.group(1).translate(_DIGITS)
                b = int(m.group(2).translate(_DIGITS)) if m.group(2) else None
                suffix = {1: " f.", 2: " ff."}.get(len(m.group(3) or ""), "")
                # the number as read; "190 f." read as "1901."; an extra figure read (8563 for 853)
                options = [(int(read), f"## Lines {read}–{b}" if b and b > int(read) else f"## Line {int(read)}{suffix}")]
                if not b and not suffix and len(read) >= 3 and read.endswith("1") and m.group(0).endswith("."):
                    options.append((int(read[:-1]), f"## Line {int(read[:-1])} f."))
                if len(read) >= 3:
                    options += [(a, f"## Lines {a}–{b}" if b and b > a else f"## Line {a}{suffix}")
                                for a in sorted({int(read[:i] + read[i + 1:]) for i in range(len(read))})]
                lemma, rest = _bold_lemma_lead(text[m.end():].strip())
                if (len(p["lines"]) == 1 or p.get("verse")) and _greek_share(text[m.end():]) >= 0.6:
                    lemma, rest = text[m.end():].strip(), ""  # the lemma alone on its line(s), Greek misread as Latin and all
                if lemma and not rest and k < len(merged) and merged[k].get("verse"):
                    lemma += " | " + merged[k]["lines"][0]["text"]  # the lemma's verses run on below
                    k += 1
                # Jebb's English after the lemma's Greek ("(So the MSS.)", "(1)", an opening quote) not in bold
                tail = re.search(r"\s*(\([^()]*[A-Za-z0-9][^()]*\)|[‘“]|—\S*)$", lemma) if lemma else None
                if tail and tail.start() > 0:
                    rest = (tail.group(1) + " " + rest).strip()
                    lemma = lemma[:tail.start()].rstrip()
                body = f"**{lemma}** {rest}" if lemma else rest
                cands.append({"kind": "line", "options": options, "body": body.strip(), "orig": prefix + text})
                md += [f"\x00{len(cands) - 1}", ""]
                continue
        if margin:
            text = f"*{margin}* " + text
        md += [prefix + text, ""]
    if persons is not None:
        md += [" · ".join(persons[0] + persons[1]), ""]
    return md


def last_line(play: Play) -> int:
    """The highest line number of the check text (the bound of an Appendix note's number), or of
    texts/<slug>/grc.txt for a play merged without one (Earle's notes on Murray's Medea), or before
    that play's text is merged, of its text draft (build/drama-pages/<slug>/draft.json: Hayley's
    notes on Murray's Alcestis)."""
    if play.last_note:
        return play.last_note
    if not play.check_text and play.notes_layout in ("earle", "hayley"):
        path = ROOT / "texts" / play.slug / "grc.txt"
        if path.exists():
            found = [int(m.group(1)) for m in re.finditer(r"^(\d+)[a-z]?\t", path.read_text(encoding="utf-8"), re.M)]
            if found:
                return max(found)
        draft = PIPELINE / "build" / "drama-pages" / play.slug / "draft.json"
        if play.notes_layout == "hayley" and draft.exists():
            found = [int(m.group(1)) for v in json.loads(draft.read_text(encoding="utf-8"))
                     if (m := re.match(r"^(\d+)", str(v.get("n", ""))))]
            if found:
                return max(found)
    if play.check_text:
        path = PIPELINE / "transcriptions" / play.check_text
        if path.exists():
            found = [int(m.group(1)) for m in re.finditer(r"^(\d+)[a-z]?\t", path.read_text(encoding="utf-8"), re.M)]
            if found:
                return max(found)
    return 2000


def _resolve_headings(pages: list[dict], kind: str, last_line: int = 2000) -> None:
    """The placeholders of _jebb_markdown settled over the pages in order: a section heading where
    its number (one of the readings the OCR allows) follows the last section's (or Jebb prints §
    clearly), counted afresh in each chapter; an Appendix note where its line number is higher
    than the last note's. Anything else goes back into the text as read."""
    last = 0
    for page in pages:
        out: list[str] = []
        for raw in page["md"].split("\n"):
            if raw.startswith("# "):
                last = 0
            m = re.fullmatch("\x00(\\d+)", raw)
            if not m:
                out.append(raw)
                continue
            c = page["cands"][int(m.group(1))]
            if c["kind"] == "sec":
                pick = next((i for i, n in enumerate(c["nums"]) if n == last + 1), None)
                if pick is None and c["explicit"]:
                    pick = 0
                if pick is None:
                    out.append(c["orig"])
                    continue
                last = c["nums"][pick]
                out += [f"## § {last}" + (f" — {c['margin']}" if c["margin"] else ""), ""]
                if c["bodies"][pick].strip():
                    out.append(c["bodies"][pick].strip())
                elif out[-1] == "":
                    out.pop()
            else:
                pick = next(((a, h) for a, h in c["options"] if last < a <= last_line), None)
                if pick is None:
                    out.append(c["orig"])
                    continue
                last = pick[0]
                out += [pick[1], ""]
                if c["body"]:
                    out.append(c["body"])
                elif out[-1] == "":
                    out.pop()
        md = re.sub(r"\n{3,}", "\n\n", "\n".join(out)).strip()
        # a title printed above an Appendix note (THE ORACLE AT DODONA. over 1166) goes under the
        # note's heading, so that it belongs to that note and not to the one before
        page["md"] = re.sub(r"^(### [^\n]+)\n\n(## Lines? [^\n]+)$", r"\2\n\n\1", md, flags=re.M)


# --- Starkie's translation ---------------------------------------------------------------------

def _greek_speech_starts(slug: str) -> dict[int, list[tuple[str, str]]]:
    """From the text draft: for each Greek page (leaf), the speeches that begin on it: (line, speaker)."""
    path = PIPELINE / "build" / "drama-pages" / slug / "draft.json"
    if not path.exists():
        return {}
    out: dict[int, list[tuple[str, str]]] = {}
    for v in json.loads(path.read_text(encoding="utf-8")):
        if v.get("speaker"):
            out.setdefault(v["leaf"], []).append((v["n"], v["speaker"]))
    return out


def _number_speeches(md: str, starts: list[tuple[str, str]], play: Play) -> str:
    """Each speech of a translation page (`@ Name` then `N<TAB>…`) given the line of the k-th
    speech that begins on the facing Greek page, and the Greek speaker's English name."""
    english = {v: k.title() for k, v in play.speakers.items()}
    out = []
    k = 0
    pending = None
    for line in md.split("\n"):
        if line.startswith("@ "):
            pending = line
            continue
        if line.startswith("N\t"):
            if k < len(starts):
                n, sp = starts[k]
                out.append(f"@ {english.get(sp, pending[2:] if pending else sp)}")
                out.append(f"{n}\t{line[2:]}")
            else:
                out.append(pending or "@ ?")
                out.append(f"?\t{line[2:]}")
            k += 1
            pending = None
            continue
        out.append(line)
    return "\n".join(out)


# --- reading the checked batches ----------------------------------------------------------------

def read_prose_batches(directory: Path, kind: str, files: list[Path] | None = None) -> dict[str, dict]:
    """Page blocks: {'md': [lines], 'flags': [lines], 'notes': [lines], 'batch': name}."""
    pages: dict[str, dict] = {}
    for path in files if files is not None else sorted(directory.glob(f"{kind}-*.md")):
        stem, section = None, None
        for raw in path.read_text(encoding="utf-8").splitlines():
            m = re.match(r"^=== (p-\d{4,5})\s*$", raw)
            if m:
                stem = m.group(1)
                pages[stem] = {"md": [], "flags": [], "notes": [], "batch": path.name}
                section = "md"
                continue
            m = re.match(r"^--- (flags|notes)\s*$", raw)
            if m and stem is not None:
                section = m.group(1)
                continue
            if stem is not None:
                pages[stem][section].append(raw.rstrip())
    return pages


def _paragraphs(md_lines: list[str]) -> list[str]:
    out: list[str] = []
    for block in re.split(r"\n\s*\n", "\n".join(md_lines)):
        rows = [r.strip() for r in block.splitlines() if r.strip()]
        while rows and rows[0].startswith("#"):
            out.append(rows.pop(0))
        if rows:
            # elision as in the texts (ʼ); the OCR's ᾽ is never a quotation mark
            out.append(greek.nfc(" ".join(rows)).replace("᾽", "ʼ"))
    return out


def merge_kind(directory: Path, kind: str) -> list[str]:
    """The checked notes or introduction as paragraphs in page order (headings as paragraphs of
    their own); a page's paragraph that begins '+ ' joined to the last paragraph of the page
    before (not to a footnote after it)."""
    from .sophocles_pages import join_run_on

    pages = read_prose_batches(directory, kind)
    paras: list[str] = []
    for stem in sorted(pages):
        for p in _paragraphs(pages[stem]["md"]):
            if p.startswith("+ ") and paras:
                k = len(paras) - 1
                while k > 0 and paras[k].startswith("[Note:"):
                    k -= 1
                paras[k] = join_run_on(paras[k], p[2:])
            elif p.startswith("+ "):
                paras.append(p[2:])
            else:
                paras.append(p)
    return paras


def merge_translation(directory: Path) -> list[tuple[str, str, str]]:
    """Starkie's translation from trans-NN.md: (speaker or '', line, text) segments; '+ ' continues
    the segment before."""
    from .sophocles_pages import join_run_on

    pages = read_prose_batches(directory, "trans")
    segs: list[list[str]] = []
    speaker = ""
    for stem in sorted(pages):
        for raw in pages[stem]["md"]:
            if not raw.strip():
                continue
            if raw.startswith("@ "):
                speaker = raw[2:].strip()
                continue
            if raw.startswith("+ ") and segs:
                segs[-1][2] = join_run_on(segs[-1][2], raw[2:])
                continue
            n, sep, text = raw.partition("\t")
            if sep and re.fullmatch(r"\d+[a-z]?", n.strip()):
                segs.append([speaker, n.strip(), greek.nfc(text.strip())])
                speaker = ""
            elif segs:
                segs[-1][2] = join_run_on(segs[-1][2], raw)
    return [tuple(s) for s in segs]


# --- the checker --------------------------------------------------------------------------------

_GREEK = re.compile(r"[Ͱ-Ͽἀ-῿][Ͱ-Ͽἀ-῿ʼ’᾽]*")
_VOWEL_START = re.compile(r"^[αεηιουωρ]", re.I)
# a reference to Homer by the book's letter: "Hom. Α 282", "Il. Ζ 146, Ι 63", "Od. ε 264"; the
# letters (and the numbers) that follow the author's or the poem's name
_HOMER_REF = re.compile(r"(?<![A-Za-z])(?:Hom(?:er)?\.?|Il\.|Od\.)\s*"
                        r"((?:[A-Za-zͰ-Ͽ]\s*\d{1,3}(?:\s*f{1,2}\.)?(?:\s*[-–]\s*\d{1,3})?\s*[,;]?\s*(?:and\s+)?)+)")
_HOMER_BOOK = re.compile(r"(?<![A-Za-zͰ-Ͽ])([A-Za-zͰ-Ͽ])\s*(?=\d)")


_HOMER_ROMAN_GREEK = re.compile(r"(?<![A-Za-z])(?:Hom(?:er)?\.?|Il\.|Od\.)\s*(?:[IVXL]*[ΙΧ][IVXLΙΧ]*)(?=\.?\s*\d)")


def homer_greek_numerals(text: str) -> list[str]:
    """References to Homer by a roman numeral (Hayley: "Od. XI. 253") in which the numeral holds
    Greek capitals Ι or Χ (the OCR's reading of the Latin letters), two letters or more: each as
    read ("Od. ΧΙ")."""
    return [m.group(0) for m in _HOMER_ROMAN_GREEK.finditer(text) if len(m.group(0).split()[-1]) >= 2]


def homer_latin_letters(text: str) -> list[str]:
    """The references to Homer by book letter in which a book letter is a Latin capital (the OCR's
    look-alike of the Greek capital: "Hom. A 282" with a Latin A for Α): each as "A 282"."""
    out = []
    for m in _HOMER_REF.finditer(text):
        for b in _HOMER_BOOK.finditer(m.group(1)):
            if "A" <= b.group(1) <= "Z":
                num = re.match(r"\s*(\d+)", m.group(1)[b.end(1):])
                out.append(f"{b.group(1)} {num.group(1) if num else ''}".strip())
    return out


def check_prose(slug: str, kind: str, path: Path, texts: Path) -> list[str]:
    """Remarks on one checked prose batch: pages missing or out of order, headings, run-on marks,
    flags not answered, Greek not precomposed or without a breathing on an initial vowel or rho,
    and (notes, translation, appendix) line numbers that grc.txt lacks."""
    out_dir = PIPELINE / "build" / "drama-prose" / slug
    index = json.loads((out_dir / f"{kind}.json").read_text(encoding="utf-8"))
    pages = read_prose_batches(path.parent, kind, files=[path])
    m = re.search(rf"{kind}-(\d+)", path.name)
    expected = [p["stem"] for p in index if m and p["batch"] == int(m.group(1))]
    remarks: list[str] = []
    if list(pages) != [s for s in expected if s in pages]:
        remarks.append("the pages are not in page order")
    for stem in expected:
        if stem not in pages:
            remarks.append(f"{stem}: missing from the batch")
    for stem in pages:
        if stem not in expected:
            remarks.append(f"{stem}: not a page of this batch")
    numbers: set[str] = set()
    grc = texts / slug / "grc.txt"
    if grc.exists():
        for raw in grc.read_text(encoding="utf-8").splitlines():
            mm = re.match(r"^(\d+[a-z]?|\d+\.\d+\.\d+[a-z]?)\t", raw)
            if mm:
                numbers.add(mm.group(1))
    prev_note = -1
    prev_sec = 0
    prev_ref: str | None = None
    for stem, block in pages.items():
        noted = " ".join(block["notes"])
        md = [l for l in block["md"] if l.strip()]
        if not md:
            if "blank" not in noted.lower() and "no text" not in noted.lower():
                remarks.append(f"{stem}: empty page (say so under notes if the page is blank)")
            continue
        first = md[0]
        college = PLAYS[slug].notes_layout in ("college", "back")
        # a page that begins with a new paragraph of the note before (a further lemma, "(1) If …",
        # Jebb's scene before the first note) is right when the batch's notes say so
        said = re.search(r"new,? (?:indented )?paragraph|further lemma|new lemma|scene description", noted, re.I)
        if kind == "notes" and not (first.startswith("## ") or first.startswith("+ ") or first == "# Introduction"
                                    or (college and first.startswith("**")) or said):  # a further lemma of the note before
            remarks.append(f"{stem}: the page begins neither with a note's heading nor with '+ ' (a note run on)")
        for k, raw in enumerate(md):
            if raw.startswith("+ ") and k > 0:
                remarks.append(f"{stem}: '+ ' inside the page (only the page's first paragraph may run on)")
            if raw.startswith("#"):
                if kind == "notes" and re.match(r"^# (?:Book [IVX]+|Introduction)$", raw):
                    prev_note = -1  # Jerram counts his lines afresh in each book; Shuckburgh's introduction to a speech stands at the head of its notes
                    continue
                if kind == "notes" and PLAYS[slug].route == "lake":
                    # Taylor: ## Vision 1.1.2, ## Mandate 1.3 (a book of one chapter), ## Similitude 9.30.2
                    from .hermas_text import LAST_GREEK, sec_key
                    from .lake_merge import taylor_ref

                    ref = taylor_ref(raw)
                    if ref is None:
                        remarks.append(f"{stem}: heading “{raw}” is not '## Vision|Mandate|Similitude N.chapter.verse'")
                        continue
                    if prev_ref is not None and sec_key(ref) < sec_key(prev_ref):
                        remarks.append(f"{stem}: note {raw[3:]} comes after {prev_ref}")
                    prev_ref = ref
                    if numbers and ref not in numbers and sec_key(ref) <= sec_key(LAST_GREEK) and raw[3:] not in noted:
                        remarks.append(f"{stem}: note {raw[3:]}: no verse {ref} in texts/{slug}/grc.txt (say why under notes)")
                    continue
                if kind == "notes":
                    mm = re.match(r"^## (\d+)([a-z]?)(?:-(\d+)([a-z]?))?$", raw)
                    if not mm:
                        remarks.append(f"{stem}: heading “{raw}” is not '## N' or '## N-M'")
                        continue
                    n = int(mm.group(1))
                    if n < prev_note:
                        remarks.append(f"{stem}: note {raw[3:]} comes after {prev_note}")
                    prev_note = n
                    if PLAYS[slug].notes_text_leaves:
                        continue  # keyed by the commentary's own lines (Jerram), mapped to ours at the merge
                    if numbers and mm.group(1) + mm.group(2) not in numbers and raw[3:] not in noted and mm.group(1) not in noted:
                        remarks.append(f"{stem}: note {raw[3:]}: no line {mm.group(1)}{mm.group(2)} in texts/{slug}/grc.txt (say why under notes)")
                elif kind == "intro":
                    mm = re.match(r"^## § (\d+)(?: — .+)?$", raw)
                    if mm:
                        n = int(mm.group(1))
                        if n != prev_sec + 1 and n != 1:
                            remarks.append(f"{stem}: § {n} after § {prev_sec}")
                        prev_sec = n
                    elif not re.match(r"^#{1,3} \S", raw):
                        remarks.append(f"{stem}: heading “{raw}” is not well formed")
                elif kind == "appendix":
                    # Jebb's Appendix (sophocles/APPENDIX.md): ## Line 15, ## Line 29 f., ## Lines 11–14, ### I. Note on …
                    if raw.startswith("### ") and len(raw) > 4:
                        continue
                    if re.match(r"^## (?!Lines? \d)\S", raw):
                        continue  # an essay of the Appendix not on one line (## The Oedipus Tyrannus at Harvard)
                    mm = re.match(r"^## Lines? (\d+)(?:–(\d+))?(?: (ff?)\.)?$", raw)
                    if not mm or (raw.startswith("## Lines ") != bool(mm.group(2))) or (mm.group(2) and mm.group(3)):
                        remarks.append(f"{stem}: heading “{raw}” is not '## Line N', '## Line N f.', '## Line N ff.', "
                                       f"'## Lines N–M' (en dash), '## Title' or '### …'")
                        continue
                    n = int(mm.group(1))
                    if n <= prev_note:
                        remarks.append(f"{stem}: note {raw[3:]} comes after line {prev_note}")
                    prev_note = n
                    if numbers and mm.group(1) not in numbers and mm.group(1) not in noted:
                        remarks.append(f"{stem}: note {raw[3:]}: no line {n} in texts/{slug}/grc.txt (say why under notes)")
            if kind == "trans":
                if not (raw.startswith("@ ") or raw.startswith("+ ") or re.match(r"^\d+[a-z]?\t", raw)):
                    remarks.append(f"{stem}: “{raw[:50]}” is neither '@ Speaker', 'N<TAB>text' nor a run-on '+ '")
                mm = re.match(r"^(\d+[a-z]?)\t", raw)
                if mm and numbers and mm.group(1) not in numbers:
                    remarks.append(f"{stem}: translation line {mm.group(1)} is not a line of grc.txt")
            if raw != unicodedata.normalize("NFC", raw):
                remarks.append(f"{stem}: not NFC: “{raw[:40]}”")
            for ref in homer_latin_letters(raw):
                remarks.append(f"{stem}: Homer's book letter in “{ref}” is a Latin capital: write the Greek letter")
            for ref in homer_greek_numerals(raw):
                remarks.append(f"{stem}: Homer's book in “{ref}” is a roman numeral with Greek capitals: write it in Latin letters")
            for g in _GREEK.findall(raw):
                letters = unicodedata.normalize("NFD", g)
                if _VOWEL_START.match(letters) and letters[0].islower() and not re.search("[̓̔]", letters[:4]):
                    at = raw.find(g)
                    if at > 0 and raw[at - 1] in "ʼ’᾽'":
                        continue  # prodelision: ʼκεῖνος
                    remarks.append(f"{stem}: “{g}” begins with a vowel or rho but has no breathing")
        for raw in block["flags"]:
            if not raw.strip():
                continue
            mm = re.match(r"^\d+ .*→\s*(.*)$", raw)
            if not mm:
                remarks.append(f"{stem}: flag line “{raw[:50]}” is not 'k word [kind] → answer'")
            elif not mm.group(1).strip():
                remarks.append(f"{stem}: flag not answered: “{raw[:50]}”")
    return remarks


def main(argv: list[str]) -> None:
    run(argv[0], argv[1], argv[2])


if __name__ == "__main__":
    main(sys.argv[1:])
