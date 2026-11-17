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
  absent     the trees' text has no word for it (no node)
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

COLUMNS = ["kind", "line", "ord", "form", "sentence", "word_id", "tree_form", "tree_lemma", "tree_postag", "same_construction", "extent"]
PASSAGE = 3  # so many absent or unprinted words in a row are a passage

SCHEMA = """
-- What a word of the text is to the text the syntax trees were made on, where it is not simply
-- the trees' own word (syntax_text.py). kind: unit, reading, absent (token_id set), unprinted
-- (sentence and word_id of the node in sentence_nodes; no token).
CREATE TABLE syntax_text_words (
    id INTEGER PRIMARY KEY, kind TEXT NOT NULL, token_id INTEGER REFERENCES tokens(id),
    sentence TEXT, word_id INTEGER, tree_form TEXT, tree_lemma TEXT, tree_postag TEXT,
    same_construction INTEGER, extent TEXT
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
        if decision[0] == "drop":
            by[(rec["line"], int(rec["ord"]))].update(relation="", head="", word_id="")
    return undecided


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
    rows = [dict(r, extent="") for r in record]
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
        db.execute("INSERT INTO syntax_text_words (kind, token_id, sentence, word_id, tree_form, tree_lemma, tree_postag, same_construction, extent) "
                   "VALUES (?,?,?,?,?,?,?,?,?)",
                   (r["kind"], tid, r["sentence"] or None, int(word) if word.isdigit() else None, r["tree_form"] or None,
                    r["tree_lemma"] or None, r.get("tree_postag") or None,
                    int(r["same_construction"]) if r.get("same_construction") in ("0", "1") else None, r["extent"] or None))
    db.execute("INSERT OR REPLACE INTO meta VALUES ('syntax_text_words', ?)", (str(len(rows)),))
    return len(rows)
