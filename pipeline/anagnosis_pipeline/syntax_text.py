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
           "difference", "extent", "misprint"]
PASSAGE = 3  # so many absent or unprinted words in a row are a passage

SCHEMA = """
-- What a word of the text is to the text the syntax trees were made on, where it is not simply
-- the trees' own word (syntax_text.py). kind: unit, reading, absent (token_id set), unprinted
-- (sentence and word_id of the node in sentence_nodes; no token).
CREATE TABLE syntax_text_words (
    id INTEGER PRIMARY KEY, kind TEXT NOT NULL, token_id INTEGER REFERENCES tokens(id),
    sentence TEXT, word_id INTEGER, tree_form TEXT, tree_lemma TEXT, tree_postag TEXT,
    same_construction INTEGER, difference TEXT, extent TEXT,
    misprint INTEGER  -- 1 on a reading where the trees' word is an evident misprint of the text the trees were made on
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


def differences(rows: list[dict], record: list[dict], known=None) -> dict[str, int]:
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
        tree_tag = rec.get("tree_postag") or ""
        # what the analyser knows of our spelling (`known`), where the word wears the trees' analysis
        mine = known(rec["form"]) if known and same_lemma and same_tag else None
        if mine:
            under = [t for l, t in mine if greek.lemma_key(l) == greek.lemma_key(fix_lemma(rec.get("tree_lemma", "")))]
            same_lemma = bool(under)
            if not under:
                # known only under other lemmas: another word, unless a lemma is the trees' lemma
                # spelled otherwise (ἐπιμέλομαι, ἐπιμελέομαι)
                tree_lemma = _bare(rec.get("tree_lemma", ""))
                alike = len(tree_lemma) >= 8 and any(difflib.SequenceMatcher(None, _bare(l), tree_lemma, autojunk=False).ratio() >= 0.9 for l, _t in mine)
            same_tag = any(t[1:6] == tree_tag[1:6] and t[7:8] == tree_tag[7:8] for t in under) if under else \
                any(t[1:6] == tree_tag[1:6] and t[7:8] == tree_tag[7:8] for _l, t in mine)
        if known and not same_lemma and not mine:
            # two words of their own (a pair made by one word in two forms): a spelling only where
            # the lemmas are one lemma spelled otherwise
            a, b = _bare(row["lemma"]), _bare(rec.get("tree_lemma", ""))
            alike = alike and min(len(a), len(b)) >= 6 and difflib.SequenceMatcher(None, a, b, autojunk=False).ratio() >= 0.85
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
                   "difference, extent, misprint) VALUES (?,?,?,?,?,?,?,?,?,?,?)",
                   (r["kind"], tid, r["sentence"] or None, int(word) if word.isdigit() else None, r["tree_form"] or None,
                    r["tree_lemma"] or None, r.get("tree_postag") or None,
                    int(r["same_construction"]) if r.get("same_construction") in ("0", "1") else None,
                    r.get("difference") or None, r["extent"] or None, 1 if r.get("misprint") == "1" else None))
    db.execute("INSERT OR REPLACE INTO meta VALUES ('syntax_text_words', ?)", (str(len(rows)),))
    return len(rows)


# --- the record made from a text's files as they stand ------------------------------------------
#
# For a text that is on sale nothing but the syntax record may change. Its merge or import is
# therefore not run again: the record is worked out from texts/<slug>/grc.txt, tokens.tsv and
# syntax-nodes.tsv and the trees, and only the rows it concerns are rewritten, line by line.

def _book(line: str) -> str:
    return line.split(".")[0] if "." in line else ""


FAR = 400  # tree words: how far from its neighbours' place a run of words may be tied elsewhere


def _greek(form: str) -> str:
    """A tree word without the marks that are not of the text (GLAUx's "G?" at a gap, the
    treebank's "κ-" for the καί of a crasis)."""
    return "".join(c for c in form if not (c.isascii() and (c.isalpha() or c in "?-")))


def _main(ws: list[dict], by_id: dict | None = None) -> dict:
    """Of the tree words one word of ours joins, the one whose syntax the word carries: the
    topmost (import_perseus.joined_main)."""
    from .import_perseus import joined_main

    return joined_main(ws, by_id)


def mend_joined(rows: list[dict], by_id: dict) -> list[str]:
    """A word that joins several tree words must carry the relation and head of its topmost
    part. The older merges gave some the relation and head of a part that hangs on another part
    (οὐδέ: the δέ that GLAUx ties to the οὐ; εἴτε; ἐϋφρονέων) or on a word under another part
    (οὔτε: the οὔ on a member of the coordination the τε heads): in the tree such a word hangs
    on itself, or on a word that hangs on it. Those get the topmost part's relation and head.
    A word that already carries its topmost part's, or whose relation and head are no part's
    (set by hand), is left. Returns what was mended."""
    done = []
    for r in rows:
        ids = r["word_id"].split("+")
        if len(ids) < 2 or r["word_id"].startswith("="):
            continue
        ws = [by_id.get((r["sentence"], x)) for x in ids]
        if any(w is None for w in ws):
            continue
        m = _main(ws, by_id)
        carried = [w for w in ws if (w["relation"], str(w["head"])) == (r["relation"], r["head"])]
        if not carried or m in carried or _main([m] + carried, by_id) is not m or len({id(w) for w in [m] + carried}) < 2:
            continue
        # only where the part carried is under the topmost one: else the choice was a fair one
        from .import_perseus import joined_main
        if joined_main([carried[0], m], by_id) is not m or joined_main([m, carried[0]], by_id) is not m:
            continue
        done.append(f"{r['line']} {r['form']}: {r['relation']} on {r['head']} -> {m['relation']} on {m['head']}")
        r["relation"], r["head"] = m["relation"], str(m["head"])
    return done


def mend_joined_file(work_dir: Path, tb: list[dict]) -> list[str]:
    """mend_joined on a text's tokens.tsv, only the lines concerned (for a text without a record)."""
    path = work_dir / "tokens.tsv"
    raw = path.read_text(encoding="utf-8").split("\n")
    head = raw[0].split("\t")
    col = {k: i for i, k in enumerate(head)}
    body = [(i, l.split("\t")) for i, l in enumerate(raw) if i and l]
    rows = [{k: f[col[k]] for k in head} for _i, f in body]
    done = mend_joined(rows, {(w["sentence"], w["word_id"]): w for w in tb})
    for (at, f), r in zip(body, rows):
        if (f[col["relation"]], f[col["head"]]) != (r["relation"], r["head"]):
            f[col["relation"]], f[col["head"]] = r["relation"], r["head"]
            raw[at] = "\t".join(f)
    if done:
        path.write_text("\n".join(raw), encoding="utf-8")
    return done


def _joined(forms: list[str], ours: str) -> bool:
    """Whether the tree words, written together, are our word: in their order, or the enclitic
    first as the treebank has it (μήτε: "-τε", "μή")."""
    from .odyssey import _bare

    parts = [_bare(_greek(f)) for f in forms]
    return "".join(parts) == ours or (len(parts) == 2 and parts[1] + parts[0] == ours)


# A word of ours that differs from the trees' word by an iota subscript wears the analysis of the
# trees' word; where the analyser cannot give ours by rule (no reading of our spelling under the
# trees' lemma), it is set here: slug -> "line form" -> (lemma, tag). An entry that repeats the
# trees' analysis says that it is right as it stands. Also here: a reading in other letters that
# was left wearing the analysis of the trees' word because the analyser cannot read ours.
OWN_ANALYSES: dict[str, dict[str, tuple[str, str]]] = {
    "lysias": {
        "6.20 δέη": ("δέος", "n-p---na-"),          # δέη πολλὰ καὶ κινδύνους ὁ θεὸς ἐπιπέμπει; the trees' δέῃ a verb
        "6.21 ᾔδει": ("οἶδα", "v3slia---"),         # the trees' ἤδει read as a dative of ἦδος
        "6.34 πραότητα": ("πραότης", "n-s---fa-"),
        "7.19 ᾤχετο": ("οἴχομαι", "v3siim---"),     # the trees' ὤχετο read as a form of ἀχεύω
        "7.22 φής": ("φημί", "v2spia---"),
        "10.4 ἀπέθνῃσκε": ("ἀποθνῄσκω", "v3siia---"),
        "14.38 Θρᾴκης": ("Θρᾴκη", "n-s---fg-"),
        "14.43 ᾔσθησθε": ("αἰσθάνομαι", "v2plie---"),  # the trees' ἤσθησθε read as a form of ἐσθέω
        "18.9 ᾤχετο": ("οἴχομαι", "v3siim---"),
        "18.13 Ἀθήνησι": ("Ἀθήνη", "n-p---fd-"),
        "22.13 δέῃ": ("δέω", "v3spsa---"),          # ὅταν μὲν εἰσφορὰν εἰσενεγκεῖν δέῃ; the trees' δέη a noun
        "30.31 σῴζειν": ("σῴζω", "v--pna---"),
        "32.10 ᾤχοντο": ("οἴχομαι", "v3piim---"),
        "18.20 πίθησθε": ("πείθω", "v2pasm---"),    # the trees' πείθησθε a present; ours wore an aorist active
        "34.4 πίθησθε": ("πείθω", "v2pasm---"),
        "34.5 πίθησθε": ("πείθω", "v2pasm---"),
        "24.13 ἐλεήσαντας": ("ἐλεέω", "v-papama-"),  # wore the analysis of the trees' πάντας
        "28.6 ἐνέπληντο": ("ἐμπίμπλημι", "v3paim---"),  # the trees' ἐνεπέπληντο, given to ἐμπελάζω
        "33.7 καινομένην": ("καίνω", "v-sppmfa-"),  # Hude's own conjecture; wore the καίω of the trees' καομένην
    },
    "ajax": {
        # words the importer left wearing the analysis of the trees' word
        "178 ἐλαφαβολίαις": ("ἐλαφηβολία", "n-p---fd-"),   # the trees' ἐλαφαβολίας, a genitive
        "1184 μεληθεὶς": ("ἐπιμελέομαι", "v-sapemn-"),     # the trees' μεληθῶ, a subjunctive
        "1230 ἐφώνεις": ("φωνέω", "v2siia---"),            # the trees' ἐκόμπεις
        "1404 ταχύνετε": ("ταχύνω", "v2ppma---"),          # the trees' ταχύνατε, an aorist
    },
    "electra": {
        "1486 τοῦ": ("ὁ", "l-s---mg-"),                    # τοῦ χρόνου; the trees read οὐ
    },
    "odyssey": {
        "5.243 ἤνυτο": ("ἀνύω", "v3siie---"),       # θοῶς δέ οἱ ἤνυτο ἔργον; the trees' ᾔνυτο given to αἴνυμαι
        "1.29 μνῄσατο": ("μιμνήσκω", "v3sai----"),
        "8.113 Πρῳρεύς": ("Πρωρεύς", "n-s---mn-"),
        "8.526 θνῄσκοντα": ("θνήσκω", "v-sppama-"),
        "18.137 ἄγῃσι": ("ἄγω", "v3spsa---"),
        "19.115 τῶ": ("τῷ", "d--------"),
        "19.526 δμῳάς": ("δμώς", "n-p---ma-"),
        "21.362 πῇ": ("πη", "g--------"),
        "21.394 πάντῃ": ("πάντῃ", "d--------"),
        "21.405 πάντῃ": ("πάντῃ", "d--------"),
        "24.208 πάντῃ": ("πάντῃ", "d--------"),
        "24.355 πάντῃ": ("πάντῃ", "d--------"),
        "24.413 πάντῃ": ("πάντῃ", "d--------"),
    },
}


# Readings where the trees' word is an evident misprint of the text the trees were made on (the
# author, 2026-11-17: "a misprint in the trees' text is mentioned where that text is shown, and
# nowhere else"). The reader treats such a reading as a real difference whatever its kind and
# says that the trees' text has a misprint there. slug -> "line form" -> (the trees' word, why).
MISPRINTS: dict[str, dict[str, tuple[str, str]]] = {
    "hermas": {  # First1KGreek's digital text of the same edition: its own slips
        "11.2.6 ἀσύμφορα": ("ἀσύμποφα", "no word; π for φ and φ for ρ"),
        "14.1.10 αὐτῆς": ("αὐτῇς", "no form; an iota subscript put in"),
        "25.6.3 μετανοήσωσι": ("μενανοήσωσι", "no word; ν for τ"),
        "26.11.2 ἀποκριθεῖσαι": ("ἀκοκριθεῖσαι", "no word; κ for π"),
        "26.11.7 παρθένων": ("παρθένον", "τῶν παρθένων in the edition; ο for ω"),
        "26.23.5 μετανοήσατε": ("μετανήσατε", "no word; an ο dropped"),
    },
    "lysias": {  # Perseus's digital text of Lamb
        "6.20 τούτῳ": ("τούτω", "Perseus's file has τούτω τῷ χρόνῳ; the iota subscript dropped"),
        "7.20 ἔπραττες": ("ἔραττες", "no word; a π dropped"),
        "8.3 ἐπιχειρεῖτε": ("χειρεῖτε", "no word; the ἐπι- lost"),
        "8.15 ἐβάδιζε": ("ἐβάδιξε", "no form; ξ for ζ"),
        "14.7 ἐξῆλθε": ("ἐξῆθε", "no form; a λ dropped"),
        "23.13 ἔπραξε": ("ἔραξε", "a π dropped, as at 7.20"),
    },
    "odyssey": {  # Perseus's digital text of Murray, as the treebank had it
        "3.74 φέροντες": ("πέροντες", "no sense; π for φ"),
        "3.435 ἐργάζετο": ("εἰργάξετο", "no form; ξ for ζ"),
        "4.270 οἷον": ("οἷν", "no word; an ο dropped"),
        "4.332 προσέφη": ("προσέθη", "no form; θ for φ"),
    },
}


# Words of ours that the trees' text has not and that were given a node by hand in the text's
# importer (import_perseus.TOKEN_FIXES): absent from the trees' text, the node kept.
HAND_NODES: dict[str, set[str]] = {
    "antigone": {"591 δʼ"},  # the trees read βρέμουσιν, without the δʼ
}


def record_from_files(work_dir: Path, tb: list[dict], name: str, write: bool = True, reader=None,
                      hand: dict | None = None, answers: dict | None = None) -> dict:
    """Work out the record of a text from its files and its trees (`tb`: the treebank words as
    the text's merge reads them, sentence ids as in tokens.tsv), and write it. Nothing of the
    text is made again: only the words concerned change.

    * A word that is linked already stays as it is. It is recorded as a unit where its word id
      joins several tree words, or where the trees write it as two words of which it carries one
      (κἀγὼ: "κ-" and "ἀγὼ"; the other stays a node of the tree and is no unprinted word); as a
      reading where the tree word has other letters or another iota subscript. An iota subscript
      is a letter of the form (ναυμαχία a nominative, ναυμαχίᾳ a dative): such a word wears the
      analysis of the trees' word and gets its own, the analyser's reading of exactly our
      spelling under the trees' lemma, or the one set by hand (`hand`: "line form" -> (lemma, tag)).
    * The words without a link are looked at between their linked neighbours, against the tree
      words there that no word of ours uses: two to four of ours that are one tree word when
      joined become a unit (the first carries the node; in a crasis with καί the second); one of
      ours that is two or three tree words joined becomes a unit with all their ids; one word in
      two forms becomes a reading (the token gets the sentence, the tree word stays a node of its
      own); three or more words that stand word for word elsewhere among the tree words left
      over are linked there.
    * What is left gets the sentence it stands in ("absent"), in a book that has trees at all.
    * The tree words no word of ours uses are "unprinted".

    Run on its own result it gives the same again. `answers`: (line, ord) -> (our word, the
    trees' word, difference), the checked kinds of difference of the readings.

    Changed: tokens.tsv (only the lines of the words concerned), syntax-nodes.tsv (the nodes a
    word of ours now carries are taken out), syntax-text.tsv, grc.txt (the header line
    `# syntax-text:`). Returns counts and what to look at by hand."""
    from .odyssey import _bare, _subscripts, _two_forms
    from .textfmt import parse_file

    doc = parse_file(work_dir / "grc.txt")
    lines = [(line.n, line.text) for line in doc.lines]
    tok_path = work_dir / "tokens.tsv"
    raw = tok_path.read_text(encoding="utf-8").split("\n")
    head = raw[0].split("\t")
    col = {k: i for i, k in enumerate(head)}
    body = [(i, l.split("\t")) for i, l in enumerate(raw) if i and l]
    rows = [{k: f[col[k]] for k in head} for _i, f in body]
    index = {(r["line"], int(r["ord"])): i for i, r in enumerate(rows)}
    # run again on its own result: the words that had only a sentence (absent words, readings
    # whose tree word stays a node of its own) are as they were before
    record_path = work_dir / "syntax-text.tsv"
    if record_path.exists():
        for old in read_record(record_path):
            i = index.get((old["line"], int(old["ord"]))) if old["line"] else None
            if i is not None and old["kind"] in ("absent", "reading") and not rows[i]["word_id"]:
                rows[i]["sentence"] = ""
    words = [w for w in tb if w["is_word"] and not w["artificial"] and _bare(_greek(w["form"]))]
    place = {(w["sentence"], w["word_id"]): k for k, w in enumerate(words)}
    by_id = {(w["sentence"], w["word_id"]): w for w in tb}
    used: set[tuple[str, str]] = set()
    for r in rows:
        if r["sentence"]:
            for w in r["word_id"].lstrip("=").split("+"):
                if w:
                    used.add((r["sentence"], w))
    carriers = {(r["sentence"], r["word_id"][1:]) for r in rows if r["word_id"].startswith("=")}
    accounted: set[tuple[str, str]] = set()  # tree words that are half of a word of ours and stay nodes
    record: list[dict] = []
    look: list[str] = []
    reanalysed: list[str] = []
    hand = hand or {}
    mended = mend_joined(rows, by_id)

    def note(i: int, kind: str, w: dict | None, sentence: str = "", word_id: str = "", form: str = "", lemma: str = "", tag: str = "") -> None:
        r = rows[i]
        record.append({"line": r["line"], "ord": int(r["ord"]), "form": r["form"], "kind": kind,
                       "tree_form": form or (w["form"] if w else ""), "tree_lemma": lemma or (w["lemma"] if w else ""),
                       "tree_postag": tag or (w["postag"] if w else ""), "sentence": sentence or r["sentence"], "word_id": word_id or r["word_id"]})

    def halves(i: int, w: dict) -> list[dict] | None:
        """The tree words next to `w` that, joined with it, are our word (κ- ἀγὼ; οὐ δὲ)."""
        k = place.get((w["sentence"], w["word_id"]))
        if k is None:
            return None
        ours = _bare(rows[i]["form"])
        for a, b in ((k - 1, k + 1), (k, k + 2), (k - 2, k + 1), (k, k + 3), (k - 1, k + 2)):
            if a < 0 or b > len(words) or any(words[x]["sentence"] != w["sentence"] for x in range(a, b)):
                continue
            if any(x != k and (words[x]["sentence"], words[x]["word_id"]) in used for x in range(a, b)):
                continue
            if _joined([words[x]["form"] for x in range(a, b)], ours):
                return words[a:b]
        return None

    # 1. the words that are linked
    for i, r in enumerate(rows):
        if not r["sentence"] or not r["word_id"]:
            continue
        ids = r["word_id"].lstrip("=").split("+")
        ws = [by_id.get((r["sentence"], x)) for x in ids]
        if any(w is None for w in ws):
            if f"{r['line']} {r['form']}" in HAND_NODES.get(work_dir.name, ()):
                note(i, "absent", None)  # it keeps the node made for it by hand
            else:
                look.append(f"{r['line']} {r['form']}: its word id {r['word_id']} is not in the trees")
            continue
        if any(w["artificial"] for w in ws):
            continue  # a node the treebank itself put in for a word its text lacks: nothing to compare
        theirs = _greek(ws[0]["form"])
        if r["word_id"].startswith("=") or len(ws) > 1 or (r["sentence"], r["word_id"]) in carriers:
            note(i, "unit", None, form=" ".join(w["form"] for w in ws), lemma=" ".join(w["lemma"] for w in ws), tag=_main(ws, by_id)["postag"])
        elif _bare(theirs) != _bare(r["form"]):
            both = halves(i, ws[0])
            if both:
                accounted.update((w["sentence"], w["word_id"]) for w in both)
                note(i, "unit", None, form=" ".join(w["form"] for w in both), lemma=" ".join(w["lemma"] for w in both), tag=ws[0]["postag"])
            else:
                note(i, "reading", ws[0])
                key = f"{r['line']} {r['form']}"
                if key in hand and tuple(hand[key]) != (r["lemma"], r["postag"]):
                    reanalysed.append(f"{key}: {r['lemma']} {r['postag']} -> {hand[key][0]} {hand[key][1]} (the trees: {ws[0]['form']})")
                    r["lemma"], r["postag"] = hand[key]
        elif _subscripts(theirs) != _subscripts(r["form"]):
            note(i, "reading", ws[0])
            key = f"{r['line']} {r['form']}"
            mine = hand.get(key) or (reader(r["form"], ws[0]["lemma"], ws[0]["postag"]) if reader else None)
            if mine is None:
                look.append(f"{key}: differs from the trees' {ws[0]['form']} by an iota subscript and wears its analysis "
                            f"({r['lemma']} {r['postag']}); the analyser has no reading of our spelling under that lemma: set it by hand")
            elif tuple(mine) != (r["lemma"], r["postag"]):
                reanalysed.append(f"{key}: {r['lemma']} {r['postag']} -> {mine[0]} {mine[1]} (the trees: {ws[0]['form']})")
                r["lemma"], r["postag"] = mine

    # 2. the words without a link, between their linked neighbours
    linked = [bool(r["sentence"]) for r in rows]
    where = {i: place.get((r["sentence"], r["word_id"].lstrip("=").split("+")[0])) for i, r in enumerate(rows) if r["sentence"] and r["word_id"]}
    has_trees = {_book(r["line"]) for r in rows if r["sentence"]}
    free_set = {k for k, w in enumerate(words) if (w["sentence"], w["word_id"]) not in used and (w["sentence"], w["word_id"]) not in accounted}

    def link(i: int, w: dict, node: bool, word_id: str | None = None) -> None:
        r = rows[i]
        r["sentence"] = w["sentence"]
        if node:
            r["word_id"], r["relation"], r["head"] = (word_id or w["word_id"]), w["relation"], w["head"]
            used.add((w["sentence"], w["word_id"]))
            free_set.discard(place[(w["sentence"], w["word_id"])])
        elif word_id:
            r["word_id"] = word_id
        linked[i] = True

    paired: set[int] = set()  # the tree words a reading of ours is paired with
    i = 0
    while i < len(rows):
        if linked[i]:
            i += 1
            continue
        a = i
        while i < len(rows) and not linked[i]:
            i += 1
        b = i
        before = next((where[k] for k in range(a - 1, max(-1, a - 6), -1) if where.get(k) is not None), None)
        after = next((where[k] for k in range(b, min(len(rows), b + 6)) if where.get(k) is not None), None)
        if before is None or after is None or not 0 < after - before <= (b - a) + 12:
            continue
        local = [k for k in range(before + 1, after) if k in free_set]
        settled: set[int] = set()
        # first the units, through the whole run: a tree word that is one of ours written
        # otherwise is no reading of a neighbour
        j = a
        while j < b:
            done = False
            # two to four of our words are one tree word (the same letters, or καί in crasis)
            for size in (2, 3, 4):
                if j + size > b or done:
                    break
                joined = "".join(_bare(rows[x]["form"]) for x in range(j, j + size))
                for k in local:
                    if k not in free_set:
                        continue
                    theirs = _bare(_greek(words[k]["form"]))
                    crasis = (size == 2 and _bare(rows[j]["form"]) == "και" and _bare(rows[j + 1]["form"])[:1] in "αεηιουω"
                              and "κα" + _bare(rows[j + 1]["form"])[1:] == theirs)
                    if joined == theirs or crasis:
                        w = words[k]
                        carrier = j + size - 1 if crasis else j
                        for x in range(j, j + size):
                            link(x, w, node=(x == carrier), word_id=None if x == carrier else "=" + w["word_id"])
                            note(x, "unit", w)
                            settled.add(x)
                        j += size
                        done = True
                        break
            if done:
                continue
            # the other way: our one word is two or three tree words in a row (μήτε: μή, τε)
            ours = _bare(rows[j]["form"])
            for k in local:
                for size in (2, 3):
                    part = list(range(k, k + size))
                    if all(x in free_set and x in local and words[x]["sentence"] == words[k]["sentence"] for x in part) \
                            and _joined([words[x]["form"] for x in part], ours):
                        ws = [words[x] for x in part]
                        main = _main(ws, by_id)
                        r = rows[j]
                        r["sentence"], r["word_id"], r["relation"], r["head"] = main["sentence"], "+".join(w["word_id"] for w in ws), main["relation"], main["head"]
                        for w in ws:
                            used.add((w["sentence"], w["word_id"]))
                            free_set.discard(place[(w["sentence"], w["word_id"])])
                        linked[j] = True
                        settled.add(j)
                        note(j, "unit", None, form=" ".join(w["form"] for w in ws), lemma=" ".join(w["lemma"] for w in ws), tag=main["postag"])
                        done = True
                        break
                if done:
                    break
            j += 1
        # then one word in two forms: a reading; the tree word stays a node of its own
        for j in range(a, b):
            if j in settled:
                continue
            for k in local:
                if k in free_set and k not in paired and not words[k]["form"].endswith("-") and _two_forms(rows[j]["form"], _greek(words[k]["form"])):
                    w = words[k]
                    paired.add(k)
                    link(j, w, node=False)
                    note(j, "reading", w, sentence=w["sentence"], word_id=w["word_id"])
                    break

    # 3. three or more words that stand word for word elsewhere among the tree words left over
    read = {(r["sentence"], str(r["word_id"])) for r in record if r["kind"] == "reading"}
    left = [k for k in sorted(free_set) if (words[k]["sentence"], words[k]["word_id"]) not in read]
    runs: list[list[int]] = []
    for k in left:
        if runs and runs[-1][-1] == k - 1:
            runs[-1].append(k)
        else:
            runs.append([k])
    i = 0
    while i < len(rows):
        if linked[i]:
            i += 1
            continue
        a = i
        while i < len(rows) and not linked[i]:
            i += 1
        ours = [_bare(rows[x]["form"]) for x in range(a, i)]
        if len(ours) < 3:
            continue
        # not far from where the words around them stand in the trees (a verse that recurs in
        # the poem is not tied to its twin in another book): near in the trees' order, or in a
        # sentence numbered between the sentences around (the Odyssey's treebank cites the last
        # verse of some books by the book alone, and it is read after all the rest)
        near = next((where[k] for k in list(range(a - 1, max(-1, a - 40), -1)) + list(range(i, min(len(rows), i + 40))) if where.get(k) is not None), None)
        lo = next((rows[k]["sentence"] for k in range(a - 1, max(-1, a - 40), -1) if rows[k]["sentence"] and rows[k]["word_id"]), "")
        hi = next((rows[k]["sentence"] for k in range(i, min(len(rows), i + 40)) if rows[k]["sentence"] and rows[k]["word_id"]), "")

        def close(k: int) -> bool:
            sentence = words[k]["sentence"]
            if near is not None and abs(k - near) <= FAR:
                return True
            return lo.isdigit() and hi.isdigit() and sentence.isdigit() and int(lo) <= int(sentence) <= int(hi)
        for run in runs:
            theirs = [_bare(_greek(words[k]["form"])) for k in run]
            at = next((s for s in range(len(theirs) - len(ours) + 1) if theirs[s:s + len(ours)] == ours), None)
            if at is not None and all(k in free_set for k in run[at:at + len(ours)]) and close(run[at]):
                for m, x in enumerate(range(a, i)):
                    link(x, words[run[at + m]], node=True)
                break

    # GLAUx writes a crasis as a mark and the whole word ("τα-", "ταὐτόν"): the mark is its device,
    # no word of the trees' text, and so no unprinted word
    accounted.update((w["sentence"], w["word_id"]) for w in words if w["form"].endswith("-") and (w["sentence"], w["word_id"]) not in used)

    # 4. what is left: the sentence it stands in, in a book that has trees
    for i, r in enumerate(rows):
        if not linked[i] and _book(r["line"]) in has_trees:
            note(i, "absent", None)
    given, without = give_sentences(lines, rows, record)
    # the checked kinds of difference (syntax_differences.py), where both words are still the
    # ones the answer was given for
    checked = 0
    for rec in record:
        a = answers.get((rec["line"], int(rec["ord"]))) if answers and rec["kind"] == "reading" else None
        if a and a[0] == rec["form"] and a[1] == rec["tree_form"]:
            rec["difference"] = a[2]
            checked += 1
    counts_diff = differences(rows, record, reader.known if reader else None)
    # the trees' words that are evident misprints of the text the trees were made on (MISPRINTS)
    marks = MISPRINTS.get(work_dir.name, {})
    marked = set()
    for rec in record:
        m = marks.get(f"{rec['line']} {rec['form']}") if rec["kind"] == "reading" else None
        if m and m[0] == rec["tree_form"]:
            rec["misprint"] = "1"
            marked.add(f"{rec['line']} {rec['form']}")
    look += [f"{k}: the misprint {v[0]} is not a reading of the record any more (MISPRINTS)" for k, v in marks.items() if k not in marked]

    lengths: dict[str, int] = {}
    for r in rows:
        lengths[r["line"]] = lengths.get(r["line"], 0) + 1
    fields = ("lemma", "postag", "relation", "head", "sentence", "word_id")
    changed = [i for i, (_at, f) in enumerate(body) if any(f[col[k]] != rows[i][k] for k in fields)]
    out = {"changed tokens": len(changed), "look": look, "given their own analysis": reanalysed, "joined words mended": mended, "difference": counts_diff,
           "absent with a sentence": given, "absent without": without, "differences checked": checked}
    words_only = [w for w in tb if _bare(_greek(w["form"]))]
    if not write:
        import tempfile
        with tempfile.TemporaryDirectory() as d:
            out["kinds"] = write_record(Path(d) / "x.tsv", record, words_only, used | accounted, lengths)
            out["rows"] = read_record(Path(d) / "x.tsv")
        return out
    out["kinds"] = write_record(record_path, record, words_only, used | accounted, lengths)
    out["rows"] = read_record(record_path)
    # tokens.tsv: only the changed lines
    for i in changed:
        at, f = body[i]
        for k in fields:
            f[col[k]] = rows[i][k]
        raw[at] = "\t".join(f)
    if changed:
        tok_path.write_text("\n".join(raw), encoding="utf-8")
    # syntax-nodes.tsv: the nodes a word of ours now carries are no extra nodes any more
    nodes_path = work_dir / "syntax-nodes.tsv"
    node_lines = nodes_path.read_text(encoding="utf-8").split("\n")
    keep = [node_lines[0]] + [l for l in node_lines[1:] if not l or tuple(l.split("\t")[:2]) not in used]
    out["nodes taken out"] = len(node_lines) - len(keep)
    if len(keep) != len(node_lines):
        nodes_path.write_text("\n".join(keep), encoding="utf-8")
    # grc.txt: the header names the trees' text
    old = (work_dir / "grc.txt").read_text(encoding="utf-8")
    grc = [l for l in old.split("\n") if not l.startswith("# syntax-text:")]
    last = max(k for k, l in enumerate(grc[:40]) if l.startswith("# "))
    if name:  # a text whose trees' text is its own edition in a digital copy is not named (the Shepherd)
        grc.insert(last + 1, f"# syntax-text: {name}")
    if "\n".join(grc) != old:
        (work_dir / "grc.txt").write_text("\n".join(grc), encoding="utf-8")
    return out


def really_differing(rows: list[dict], tokens: list[dict] | None = None) -> int:
    """How many sentences have a real difference: a reading in another form or another word, a
    word of ours the trees' text has not, a tree word not printed (not a unit, an elision, a
    movable ν or a spelling). Only sentences that have a word of ours (`tokens`: the token rows)
    count: the tree of another is never shown."""
    ours = {t["sentence"] for t in tokens if t["sentence"]} if tokens is not None else None
    real = set()
    for r in rows:
        if r["kind"] in ("absent", "unprinted") or (r["kind"] == "reading" and r.get("difference") in ("form", "word")):
            if r["sentence"] and (ours is None or r["sentence"] in ours):
                real.add(r["sentence"])
    return len(real)


def _lysias_trees(sources: Path) -> list[dict]:
    from .hude_merge import speech_treebank
    from .hude_pages import SPEECHES

    out: list[dict] = []
    for speech in range(1, SPEECHES + 1):
        out += speech_treebank(speech, sources)
    return out


def _play_trees(slug: str):
    """The trees of a text of the drama route (drama.PLAYS), as its merge reads them."""
    def load(sources: Path) -> list[dict]:
        from .drama import PLAYS
        from .sophocles import read_agdt, read_glaux_lines

        play = PLAYS[slug]
        if play.treebank:
            return read_agdt(sources / "treebanks" / play.treebank, play.treebank.startswith("tlg0020."))
        return read_glaux_lines(sources / "glaux" / play.glaux)
    return load


def _odyssey_trees(sources: Path) -> list[dict]:
    from .odyssey import TREEBANK, read_treebank

    return read_treebank(sources / TREEBANK)


def _glaux_trees(module: str):
    """GLAUx's trees of a text whose merge names its file (symposium_merge.GLAUX, gorgias_merge.GLAUX)."""
    def load(sources: Path) -> list[dict]:
        import importlib

        from .symposium_merge import read_glaux

        return read_glaux(sources / importlib.import_module(f"anagnosis_pipeline.{module}").GLAUX)
    return load


def _antigone_trees(sources: Path) -> list[dict]:
    from .import_perseus import read_treebank

    from .import_perseus import read_treebank_nodes

    # the importer reads the real words and the other nodes apart
    words = [dict(w, artificial=False) for w in read_treebank(sources / "antigone.tb.xml")]
    nodes = [dict(w, artificial=bool(w["artificial"]), is_word=False) for w in read_treebank_nodes(sources / "antigone.tb.xml")]
    return words + nodes


def _sophocles_trees(slug: str):
    """The treebank of a play of the Perseus importer (sophocles.PLAYS), as it reads it."""
    def load(sources: Path) -> list[dict]:
        from .sophocles import PLAYS, read_agdt

        return read_agdt(sources / "treebanks" / PLAYS[slug].treebank)
    return load


# The texts whose record is made from their files (record_from_files): how their trees are read
# and what the trees' text is called. A text is added here only when its trees' text has been
# confirmed from its sources (the plan of each text says how).
FROM_FILES: dict[str, tuple] = {
    "lysias": (_lysias_trees, "the Perseus Digital Library's text of the speeches (W. R. M. Lamb's Loeb edition, 1930)"),
    "odyssey": (_odyssey_trees, "the Perseus Digital Library's text of the poem (A. T. Murray's Loeb edition, 1919)"),
    "gorgias": (_glaux_trees("gorgias_merge"), "the Perseus Digital Library's text of this edition, without the words Burnet brackets"),
    "antigone": (_antigone_trees, "the Perseus Digital Library's text of the play as the treebank's annotators had it"),
    "ajax": (_sophocles_trees("ajax"), "the Perseus Digital Library's text of the play (F. Storr's Loeb edition, 1913)"),
    "electra": (_sophocles_trees("electra"), "the Perseus Digital Library's text of the play (F. Storr's Loeb edition, 1913)"),
    # the Shepherd's trees were made on First1KGreek's digital text of this same edition, which
    # misprints six words: the record is kept, the reader is not told of another text (the author,
    # 2026-11-17), so no name
    "hermas": (_play_trees("hermas"), ""),
}


def exact_reader(sources: Path, lexicon: Path):
    """read(form, lemma, tag): the analyser's reading of exactly this spelling (accents and iota
    subscripts as written) under the lemma named, the one whose tag agrees best with `tag`:
    (lemma, tag), or None where it has none under that lemma. read.known(form): all its readings
    of exactly this spelling, [(lemma, tag)]."""
    from . import greek
    from .odyssey import fix_lemma
    from .odyssey_merge import Analyser, Frequencies, _accent_key

    analyse, freq = Analyser(lexicon), Frequencies(sources / "treebanks")

    def known(form: str) -> list[tuple[str, str]]:
        key = _accent_key(form)
        return [(fix_lemma(a[1]), a[2][:9]) for a in analyse(form) if len(a) > 2 and len(a[2]) >= 9 and _accent_key(a[0]) == key]

    def read(form: str, lemma: str, tag: str = "") -> tuple[str, str] | None:
        key = _accent_key(form)
        want = greek.lemma_key(fix_lemma(lemma))
        same = [a for a in known(form) if greek.lemma_key(a[0]) == want and greek.nfc(a[0])[:1].isupper() == greek.nfc(fix_lemma(lemma))[:1].isupper()]
        if not same:
            return None
        best = max(same, key=lambda a: (sum(1 for x, y in zip(a[1], tag.ljust(9, "-")) if x == y), freq.analysis[(key, greek.nfc(a[0]), a[1])]))
        return fix_lemma(lemma), best[1]
    read.known = known
    return read


def difference_answers(slug: str) -> dict[tuple[str, int], tuple[str, str, str]]:
    """The checked kinds of difference of a text's readings: (line, ord) -> (our word, the trees'
    word, difference)."""
    from .syntax_differences import answers

    return answers(slug)


# Texts without a record (their trees were made on the very text printed) whose trees the step
# still reads, to mend their joined words (mend_joined).
NO_RECORD: dict[str, object] = {
    "symposium": _glaux_trees("symposium_merge"),
}


def run(slug: str, texts: Path, sources: Path, write: bool, lexicon: Path | None = None) -> dict:
    if slug in NO_RECORD:
        tb = NO_RECORD[slug](sources)
        if write:
            mended = mend_joined_file(texts / slug, tb)
        else:
            with (texts / slug / "tokens.tsv").open(encoding="utf-8", newline="") as f:
                mended = mend_joined(list(csv.DictReader(f, delimiter="\t", quoting=csv.QUOTE_NONE)), {(w["sentence"], w["word_id"]): w for w in tb})
        return {"changed tokens": len(mended), "joined words mended": mended, "look": [], "kinds": {}, "sentences": 0, "sentences that really differ": 0, "rows": []}
    loader, name = FROM_FILES[slug]
    out = record_from_files(texts / slug, loader(sources), name, write, exact_reader(sources, lexicon or texts.parent / "data" / "lexicon.sqlite"),
                            OWN_ANALYSES.get(slug, {}), difference_answers(slug))
    with (texts / slug / "tokens.tsv").open(encoding="utf-8", newline="") as f:
        tokens = list(csv.DictReader(f, delimiter="\t", quoting=csv.QUOTE_NONE))
    if not write:  # the sentences of the words that would get one
        given = {(r["line"], str(r["ord"])): r["sentence"] for r in out["rows"] if r["line"] and r["sentence"]}
        for t in tokens:
            t["sentence"] = t["sentence"] or given.get((t["line"], t["ord"]), "")
    out["sentences"] = len({t["sentence"] for t in tokens if t["sentence"]})
    out["sentences that really differ"] = really_differing(out["rows"], tokens)
    return out


def after_merge(slug: str, texts: Path, sources: Path, lexicon: Path | None = None) -> list[str]:
    """For the end of a text's merge: the record made again from the files just written (so
    that a merge run again leaves the text as it is). Returns what is to be looked at by hand,
    as lines for the merge's problems."""
    if slug in NO_RECORD:
        got = run(slug, texts, sources, True, lexicon)
        print(f"trees' text: none (the trees were made on the text printed); joined words mended: {len(got['joined words mended'])}")
        return []
    if slug not in FROM_FILES:
        return []
    got = run(slug, texts, sources, True, lexicon)
    print("trees' text: " + ", ".join(f"{k} {v}" for k, v in got["kinds"].items()) + f"; {got['sentences that really differ']} of "
          f"{got['sentences']} sentences really differ; {len(got['look'])} to look at")
    return [f"trees' text: {x}" for x in got["look"]]
