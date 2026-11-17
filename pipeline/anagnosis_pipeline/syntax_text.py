"""What each word of a text is to the text its syntax trees were made on.

The trees of a text are the treebank's, made on the Perseus Digital Library's text of the work,
which is often another edition than the one printed here (the Theogony: Evelyn-White's Loeb for
the trees, Rzach's Teubner in the reader). The merge lines our words up with the trees' words
(odyssey.align). Most are the same words. The others are recorded, so that the reader can be
told (pipeline/PLAN-theogony.md, "The trees' text"):

  unit       our word is a part of a tree word (αἵ θʼ for αἵθʼ), or several tree words joined
  reading    the trees' text has another word here (`tree_form`, `tree_lemma`, `tree_postag`):
             ours is paired with it, the row naming the tree word's node. The tree is shown with
             the word it was made for; the relation and head are that word's, not ours.
             `same_construction` (TREE_READINGS) says whether our word stands in the same
             construction (1: its token then carries the node in its own columns too, as a word
             of the trees does) or in another (0: the token has the sentence but no node of its
             own, so that nothing but this row gives it the tree word's role)
  absent     the trees' text has no word for it (no node). It has the `sentence` it stands in
             (give_sentences), so that the tree can be opened from it; none where it is part of a
             passage that makes sentences of its own, for which there is no tree
  unprinted  a tree word our edition does not print (kept as a node so that the tree stays whole)

`extent` says of an absent or unprinted word whether it stands alone ("word") or in a run of
three or more such words ("passage": a verse or more that one of the two texts lacks).

The record is the file texts/<slug>/syntax-text.tsv, written by the text's merge; the build
makes the table `syntax_text_words` of it (only for a text that has the file) and the meta keys
`syntax_text` (the trees' text named, from grc.txt's header `# syntax-text:`) and
`syntax_text_words` (the number of rows).
"""
from __future__ import annotations

import csv
import sqlite3
from pathlib import Path

COLUMNS = ["kind", "line", "ord", "form", "sentence", "word_id", "tree_form", "tree_lemma", "tree_postag", "same_construction",
           "difference", "extent"]
PASSAGE = 3  # so many absent or unprinted words in a row are a passage

SCHEMA = """
-- What a word of the text is to the text the syntax trees were made on, where it is not simply
-- the trees' own word (syntax_text.py). kind: unit, reading, absent (token_id set), unprinted
-- (sentence and word_id of the node in sentence_nodes; no token).
CREATE TABLE syntax_text_words (
    id INTEGER PRIMARY KEY, kind TEXT NOT NULL, token_id INTEGER REFERENCES tokens(id),
    sentence TEXT, word_id INTEGER, tree_form TEXT, tree_lemma TEXT, tree_postag TEXT,
    same_construction INTEGER, difference TEXT, extent TEXT
);
CREATE INDEX syntax_text_words_token ON syntax_text_words(token_id);
CREATE INDEX syntax_text_words_node ON syntax_text_words(sentence, word_id);
"""


def settle(slug: str, rows: list[dict], record: list[dict]) -> list[str]:
    """Add the judgement on each reading (drama_fixes.TREE_READINGS: "line form" -> ("keep" or
    "drop", reason)) as `same_construction`: 1 where our word stands in the trees' word's
    construction, 0 where it does not. The row keeps the tree word's node either way. A word in
    another construction does not carry the node in its own token columns (relation, head and
    word id are emptied; the sentence stays, so that the tree can be opened from the word): the
    tree word is then a node of its own, shown as the trees have it, and only the record ties
    our word to it. Returns the readings that have no decision (left as paired)."""
    from .drama_fixes import TREE_READINGS

    decisions = TREE_READINGS.get(slug, {})
    by = {(r["line"], int(r["ord"])): r for r in rows}
    undecided = []
    for rec in record:
        if rec["kind"] != "reading":
            continue
        key = f"{rec['line']} {rec['form']}"
        decision = decisions.get(key)
        if decision is None:
            undecided.append(key)
            continue
        rec["same_construction"] = "1" if decision[0] == "keep" else "0"
        if len(decision) > 2:
            rec["difference"] = decision[2]  # by hand, where the letters and tags would mislead
        if decision[0] == "drop":
            by[(rec["line"], int(rec["ord"]))].update(relation="", head="", word_id="")
    return undecided


def differences(rows: list[dict], record: list[dict]) -> dict[str, int]:
    """How each reading differs from the trees' word (`difference`), so that the reader can leave
    the slightest unmarked if the author wishes:

      elision   one of the two is the other elided (μʼ / μοι, ταῦτά / ταῦτʼ)
      nu        the same form with and without the movable ν (τέκε / τέκεν)
      spelling  the same word in the same form, spelled otherwise (μειχθεὶς / μιχθεὶς; a name)
      form      the same word in another form (νύκτας / νυκτὸς; παιπαλοέσσης / παιπαλοέσσῃς)
      word      another word

    Returns the count of each."""
    import difflib

    from . import greek
    from .odyssey import _bare, fix_lemma

    by = {(r["line"], int(r["ord"])): r for r in rows}
    counts: dict[str, int] = {}
    for rec in record:
        if rec["kind"] != "reading":
            continue
        row = by[(rec["line"], int(rec["ord"]))]
        ours, theirs = _bare(rec["form"]), _bare(rec["tree_form"])
        short, long_ = sorted((ours, theirs), key=len)
        elided = any(greek.nfd(x).rstrip()[-1:] in "ʼ’\u0313\u1fbd\u02bc" for x in (rec["form"], rec["tree_form"]))
        same_lemma = greek.lemma_key(fix_lemma(rec.get("tree_lemma", ""))) == greek.lemma_key(row["lemma"])
        same_tag = (rec.get("tree_postag") or "")[1:6] == row["postag"][1:6] and (rec.get("tree_postag") or "")[7:8] == row["postag"][7:8]
        alike = difflib.SequenceMatcher(None, ours, theirs, autojunk=False).ratio() >= 0.75
        if rec.get("difference"):
            kind = rec["difference"]
        elif elided and long_.startswith(short) and len(long_) - len(short) <= 2:
            kind = "elision"
        elif short + "ν" == long_ and (same_lemma or same_tag):
            kind = "nu"
        elif same_tag and (same_lemma or alike):
            kind = "spelling"
        elif same_lemma or (alike and (rec.get("tree_postag") or "")[:1] == row["postag"][:1]):
            kind = "form"
        else:
            kind = "word"
        rec["difference"] = kind
        counts[kind] = counts.get(kind, 0) + 1
    return counts


STOPS = ".;·"  # the marks that end a sentence in our text (the full stop, the question mark, the raised stop)


def stops_before(lines: list[tuple[str, str]], words: int) -> list[bool]:
    """For every word of the text, whether a sentence-ending stop stands between it and the word
    before it."""
    from . import greek

    out: list[bool] = []
    tail = ""
    for _n, text in lines:
        at = 0
        for _form, start, end in greek.words(text):
            out.append(any(c in STOPS for c in tail + text[at:start]))
            tail, at = "", end
        tail = text[at:] + " "
    if len(out) != words:
        raise SystemExit(f"syntax_text: {len(out)} words in the text, {words} token rows")
    return out


def shift_repeats(lines: list[tuple[str, str]], rows: list[dict], record: list[dict]) -> int:
    """Where our text has a passage the trees' text lacks, and the passage begins with the same
    words as the sentence after it (Theogony 576-577, "[ἀμφὶ δέ οἱ στεφάνους … Παλλὰς Ἀθήνη.]"
    before 578 "ἀμφὶ δέ οἱ στεφάνην …"), the alignment gives the trees' words to their first
    occurrence, and the passage's rest with the true sentence's opening is left over. If both
    occurrences begin after a stop, the trees' words belong to the second: the annotation of the
    two is exchanged, so that the passage is whole and the sentence after it too. Returns the
    number of words moved."""
    from .odyssey import _bare

    stop_before = stops_before(lines, len(rows))
    place = {(r["line"], int(r["ord"])): i for i, r in enumerate(rows)}
    recs = {place[(r["line"], int(r["ord"]))]: r for r in record}
    moved = 0
    i = 0
    while i < len(rows):
        if not (i in recs and recs[i]["kind"] == "absent"):
            i += 1
            continue
        a = i
        while i < len(rows) and i in recs and recs[i]["kind"] == "absent":
            i += 1
        b = i  # rows[a:b]: a run of words the trees' text has not
        for k in range(min(6, b - a, a), 1, -1):
            first, second = range(a - k, a), range(b - k, b)
            if (all(rows[x]["sentence"] and x not in recs for x in first)
                    and [_bare(rows[x]["form"]) for x in first] == [_bare(rows[x]["form"]) for x in second]
                    and stop_before[a - k] and stop_before[b - k]):
                for x, y in zip(first, second):
                    for key in ("lemma", "postag", "relation", "head", "sentence", "word_id"):
                        rows[x][key], rows[y][key] = rows[y][key], rows[x][key]
                    rec = recs.pop(y)
                    rec.update(line=rows[x]["line"], ord=rows[x]["ord"], form=rows[x]["form"])
                    recs[x] = rec
                moved += k
                break
    return moved


def give_sentences(lines: list[tuple[str, str]], rows: list[dict], record: list[dict]) -> tuple[int, int]:
    """A word of ours that the trees' text has not ("absent") still stands in a sentence, and
    pressing it must open that sentence's tree. Each such word gets the sentence it stands in
    (in its token row and in the record), with no node of its own (the word id stays empty):

    * between two words of the same tree sentence: that sentence;
    * at the seam of two sentences: the sentence of the words before it, unless one of our
      sentence-ending stops (. ; ·) stands between them and the word; then the sentence of the
      words after it, unless a stop stands between the word and them;
    * cut off by stops on both sides (a sentence of its own that the trees' text lacks: verses
      576-577 of the Theogony): no sentence.

    `lines`: (number, text) of the Greek in order; `rows`: the token rows in the same order.
    Returns (words given a sentence, words left without)."""
    stop_before = stops_before(lines, len(rows))
    absent = {(r["line"], int(r["ord"])): r for r in record if r["kind"] == "absent"}
    linked = [bool(r["sentence"]) for r in rows]
    given = left = 0
    for i, r in enumerate(rows):
        rec = absent.get((r["line"], int(r["ord"])))
        if rec is None:
            continue
        p = next((k for k in range(i - 1, -1, -1) if linked[k]), None)
        n = next((k for k in range(i + 1, len(rows)) if linked[k]), None)
        before = rows[p]["sentence"] if p is not None else ""
        after = rows[n]["sentence"] if n is not None else ""
        cut_before = p is None or any(stop_before[p + 1:i + 1])
        cut_after = n is None or any(stop_before[i + 1:n + 1])
        sentence = before if before and before == after else before if not cut_before else after if not cut_after else ""
        if sentence:
            rec["sentence"] = sentence
            r["sentence"] = sentence  # no node: relation, head and word id stay empty
            given += 1
        else:
            left += 1
    return given, left


def _runs(flags: list[bool]) -> list[int]:
    """For each place, the length of the run of true flags it stands in (0 where false)."""
    out = [0] * len(flags)
    i = 0
    while i < len(flags):
        if not flags[i]:
            i += 1
            continue
        j = i
        while j < len(flags) and flags[j]:
            j += 1
        for k in range(i, j):
            out[k] = j - i
        i = j
    return out


def write_record(path: Path, record: list[dict], tb: list[dict], used: set[tuple[str, str]], lengths: dict[str, int] | None = None) -> dict[str, int]:
    """syntax-text.tsv from the aligner's record and the tree words no word of ours uses; returns
    the number of rows by kind."""
    rows = sorted((dict(r, extent="") for r in record), key=lambda r: (_line_key(r["line"]), int(r["ord"])))
    # our words without a tree word: alone, or a run (a verse the trees' text lacks). A run is
    # counted among the words of the text in their order, whatever stands between in the record
    order = sorted(range(len(rows)), key=lambda i: (_line_key(rows[i]["line"]), int(rows[i]["ord"])))
    absent = [i for i in order if rows[i]["kind"] == "absent"]
    for a, b in _adjacent(absent, rows, lengths or {}):
        for i in absent[a:b]:
            rows[i]["extent"] = "passage" if b - a >= PASSAGE else "word"
    # the tree's words that our edition does not print, in the treebank's order
    # (a tree word that a reading of ours is tied to by the record is not one of them)
    read = {(r["sentence"], str(r["word_id"])) for r in rows if r["kind"] == "reading"}
    words = [w for w in tb if w["is_word"] and not w["artificial"]]
    flags = [(w["sentence"], w["word_id"]) not in used and (w["sentence"], w["word_id"]) not in read for w in words]
    for w, flag, run in zip(words, flags, _runs(flags)):
        if flag:
            rows.append({"kind": "unprinted", "line": "", "ord": "", "form": "", "sentence": w["sentence"], "word_id": w["word_id"],
                         "tree_form": w["form"], "tree_lemma": w["lemma"], "tree_postag": w["postag"],
                         "extent": "passage" if run >= PASSAGE else "word"})
    with path.open("w", encoding="utf-8", newline="") as f:
        out = csv.DictWriter(f, fieldnames=COLUMNS, delimiter="\t", lineterminator="\n", quoting=csv.QUOTE_NONE, quotechar=None, escapechar=None)
        out.writeheader()
        out.writerows({k: r.get(k, "") for k in COLUMNS} for r in rows)
    counts: dict[str, int] = {}
    for r in rows:
        counts[r["kind"]] = counts.get(r["kind"], 0) + 1
    return counts


def _line_key(n: str) -> tuple:
    import re
    return tuple(int(x) if x.isdigit() else x for x in re.findall(r"\d+|[a-z]+", n))


def _adjacent(absent: list[int], rows: list[dict], lengths: dict[str, int]) -> list[tuple[int, int]]:
    """The runs of absent words that follow one another in the text (the next word of the same
    line, or the last word of a line and the first of the next): (from, to) places in `absent`.
    `lengths`: the number of words of each line, the lines in the text's order."""
    place = {n: i for i, n in enumerate(lengths)}

    def follows(x: dict, y: dict) -> bool:
        if x["line"] == y["line"]:
            return int(y["ord"]) == int(x["ord"]) + 1
        return (int(y["ord"]) == 0 and int(x["ord"]) == lengths.get(x["line"], -1) - 1
                and place.get(y["line"], -9) == place.get(x["line"], -1) + 1)

    runs, a = [], 0
    for k in range(1, len(absent) + 1):
        if k == len(absent) or not follows(rows[absent[k - 1]], rows[absent[k]]):
            runs.append((a, k))
            a = k
    return runs


def read_record(path: Path) -> list[dict]:
    with path.open(encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f, delimiter="\t", quoting=csv.QUOTE_NONE))


def build_table(db: sqlite3.Connection, work_dir: Path) -> int:
    """The table syntax_text_words and the meta key syntax_text_words, for a text that has
    syntax-text.tsv (no table otherwise: a text without the record is built as before)."""
    path = work_dir / "syntax-text.tsv"
    if not path.exists():
        return 0
    db.executescript(SCHEMA)
    token = {(n, o): i for i, n, o in db.execute("SELECT t.id, l.n, t.ord FROM tokens t JOIN lines l ON l.id = t.line_id")}
    rows = read_record(path)
    for r in rows:
        tid = token.get((r["line"], int(r["ord"]))) if r["line"] else None
        if r["line"] and tid is None:
            raise SystemExit(f"{work_dir.name}: syntax-text.tsv names the word {r['line']}:{r['ord']} {r['form']}, which the text has not")
        word = r["word_id"].lstrip("=").split("+")[0]
        db.execute("INSERT INTO syntax_text_words (kind, token_id, sentence, word_id, tree_form, tree_lemma, tree_postag, same_construction, "
                   "difference, extent) VALUES (?,?,?,?,?,?,?,?,?,?)",
                   (r["kind"], tid, r["sentence"] or None, int(word) if word.isdigit() else None, r["tree_form"] or None,
                    r["tree_lemma"] or None, r.get("tree_postag") or None,
                    int(r["same_construction"]) if r.get("same_construction") in ("0", "1") else None,
                    r.get("difference") or None, r["extent"] or None))
    db.execute("INSERT OR REPLACE INTO meta VALUES ('syntax_text_words', ?)", (str(len(rows)),))
    return len(rows)
