"""The author's list of short definitions to choose from, and the pairs he chose.

A word shows a short definition only if Logeion's list has that very word (build.resolve_short_
definition). Some words therefore show none although the list has an entry that may well be
theirs: one spelt with another capital or accent (Ἔρως, the god, beside ἔρως "love"; σάββατον
beside Σάββατον), or the headword under which the dictionaries file the word (νοῦσος under
νόσος). No rule can tell the right ones from the wrong ones (καλῶς "well" beside κάλως "a reefing
rope"), and no agent is to choose: the author does.

`shortdef-choices list` writes one line per such pair for the texts on offer (on sale or free),
each with a box to tick. `shortdef-choices apply` reads the ticked lines and writes
pipeline/shortdef-pairs.tsv, which the build reads (build.read_shortdef_pairs): exactly the pairs
he ticked, and no others."""
from __future__ import annotations

import collections
import csv
import re
from pathlib import Path

from . import greek
from .build import (SHORTDEF_PAIRS, Homographs, _cased_key, capitalised_lemmas, load_logeion_shortdefs,
                    pair_definition, read_aliases, read_catalog_entry, read_shortdef_pairs, short_definition_of)

LINE = re.compile(r"^- \[(?P<tick>[ xX])\] (?P<lemma>\S+) → (?P<entry>\S+): ")


def offered(texts: Path) -> list[Path]:
    """The texts on offer: on sale (`# google_play: yes`) or free (`# free: yes`)."""
    out = []
    for work_dir in sorted(p for p in texts.iterdir() if p.is_dir() and (p / "grc.txt").exists()):
        entry = read_catalog_entry(work_dir)
        if "yes" in (str(entry.get("google_play", "")).lower(), str(entry.get("free", "")).lower()):
            out.append(work_dir)
    return out


def candidates(texts: Path, sources: Path) -> dict[tuple[str, str], dict]:
    """(lemma as the text spells it, Logeion's entry as Logeion spells it) -> the definition, the
    kind of pair ("spelling" or "headword") and the number of words per text."""
    exact, loose = load_logeion_shortdefs(sources)
    homographs = Homographs.load(sources)
    out: dict[tuple[str, str], dict] = {}
    for work_dir in offered(texts):
        with (work_dir / "tokens.tsv").open(encoding="utf-8", newline="") as f:
            tokens = [(r["form"], r["lemma"]) for r in csv.DictReader(f, delimiter="\t", quoting=csv.QUOTE_NONE) if r["lemma"]]
        capitals = capitalised_lemmas(tokens)
        counts = collections.Counter(_cased_key(lemma) for _form, lemma in tokens)
        aliases = read_aliases(work_dir / "aliases.tsv")
        title = read_catalog_entry(work_dir).get("title_en") or work_dir.name
        for lemma, n in counts.items():
            if short_definition_of(lemma, exact, loose, capitals, {}, homographs) is not None:
                continue
            found: list[tuple[str, str]] = [(e, "spelling") for e in loose.get(greek.strip_diacritics(lemma), [])]
            headword = aliases.get(greek.lemma_key(lemma))
            if headword:
                found += [(e, "headword") for e in loose.get(greek.strip_diacritics(headword), []) if e.lower() == headword]
            for entry, kind in found:
                definition = pair_definition(entry, exact, loose)
                if definition is None:
                    continue
                row = out.setdefault((lemma, entry), {"definition": definition, "kind": kind, "texts": {}})
                row["texts"][title] = n
    return out


HEAD = """# Short definitions for you to choose

Each line below is a word that shows **no short definition** now, with an entry of the short
dictionary (Logeion) that may be its own. Tick the box of each pair you want shown: change
`[ ]` to `[x]`. Leave the others as they are. Then tell Claude; exactly the ticked pairs are
entered (`shortdef-choices apply`), and no others. The definitions are Logeion's own words.

How to read a line: **word in the text → entry in the short dictionary: that entry's
definition** · where the word stands, and how many times.

Lines already ticked are the pairs you chose before.
"""

SECTIONS = [
    ("spelling", "## A. The same letters, with another capital or accent\n\n"
                 "The short dictionary has an entry with the same letters, but spelt otherwise. Often it "
                 "is the same word (Ἔρως, the god, and ἔρως; σάββατον and Σάββατον); often it is another "
                 "word altogether (καλῶς \"well\" and κάλως \"a reefing rope\"; a man's name and a common "
                 "word).\n"),
    ("headword", "## B. Filed in the dictionaries under another headword\n\n"
                 "The word has no entry of its own in the short dictionary, but the large dictionaries "
                 "list it under the headword shown. Until now the word borrowed that headword's "
                 "definition. Sometimes it fits (νοῦσος under νόσος); sometimes it does not fit the form "
                 "(πορεύομαι \"go\" under πορεύω \"to make to go\").\n"),
]


def write_list(texts: Path, sources: Path, path: Path) -> str:
    rows = candidates(texts, sources)
    chosen = read_shortdef_pairs(SHORTDEF_PAIRS)
    if path.exists():   # ticks made in the file and not yet applied are kept
        chosen.update(read_ticks(path))
    out = [HEAD]
    for kind, heading in SECTIONS:
        mine = [(k, v) for k, v in rows.items() if v["kind"] == kind]
        mine.sort(key=lambda kv: (-sum(kv[1]["texts"].values()), greek.strip_diacritics(kv[0][0]), kv[0]))
        out.append(heading)
        out.append(f"{len(mine)} pairs, the most frequent first.\n")
        for (lemma, entry), row in mine:
            tick = "x" if chosen.get(lemma) == entry else " "
            where = ", ".join(f"{t} {n}" for t, n in sorted(row["texts"].items(), key=lambda x: -x[1]))
            out.append(f"- [{tick}] {lemma} → {entry}: {row['definition']} · {where}")
        out.append("")
    path.write_text("\n".join(out), encoding="utf-8")
    by_kind = collections.Counter(v["kind"] for v in rows.values())
    return f"wrote {path}: {by_kind['spelling']} pairs by spelling, {by_kind['headword']} by headword"


def read_ticks(path: Path) -> dict[str, str]:
    """lemma -> entry for the ticked lines. A word ticked twice (two entries) is an error."""
    out: dict[str, str] = {}
    for raw in path.read_text(encoding="utf-8").splitlines():
        m = LINE.match(raw)
        if m and m["tick"] != " ":
            lemma, entry = _cased_key(m["lemma"]), _cased_key(m["entry"])
            if out.get(lemma, entry) != entry:
                raise SystemExit(f"{m['lemma']} is ticked for two entries ({out[lemma]}, {entry}): keep one")
            out[lemma] = entry
    return out


def apply(path: Path, pairs_path: Path = SHORTDEF_PAIRS) -> str:
    ticks = read_ticks(path)
    lines = ["# lemma as the text spells it\tLogeion's entry whose short definition it shows",
             "# The author's own choices (private list, `shortdef-choices apply`). No rule, agent or importer adds a line."]
    lines += [f"{lemma}\t{entry}" for lemma, entry in sorted(ticks.items(), key=lambda x: (greek.strip_diacritics(x[0]), x[0]))]
    pairs_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return f"wrote {pairs_path}: {len(ticks)} pairs"
