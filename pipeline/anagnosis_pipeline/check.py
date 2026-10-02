"""Validate the editable files in texts/ and report lexicon coverage."""
from __future__ import annotations

import collections
import re
import sys
from pathlib import Path

from . import greek
from .commentary import parse_commentary_md
from .import_perseus import read_syntax_nodes, read_tokens
from .textfmt import Line, parse_file


def _n_parts(n: str) -> tuple[int, str]:
    from .linenum import parts

    try:
        return parts(n)
    except ValueError:
        return (-1, n)


def check_work(work_dir: Path, lexicon_keys: dict[str, set[str]] | None, sources: Path) -> tuple[int, int]:
    errors = 0
    warnings = 0
    slug = work_dir.name
    doc = parse_file(work_dir / "grc.txt")
    lines = doc.lines
    print(f"== {slug}: {len(lines)} lines")

    # line numbers unique and increasing
    seen = set()
    prev = (0, "")
    for l in lines:
        k = _n_parts(l.n)
        if l.n in seen:
            print(f"  ERROR duplicate line number {l.n}"); errors += 1
        if k <= prev:
            print(f"  WARN line {l.n} does not follow {prev[0]}{prev[1]}"); warnings += 1
        seen.add(l.n)
        prev = k

    # tokens aligned to text
    tokens = read_tokens(work_dir / "tokens.tsv")
    by_line: dict[str, list[dict]] = collections.defaultdict(list)
    for t in tokens:
        by_line[t["line"]].append(t)
    for n in by_line:
        if n not in seen:
            print(f"  ERROR tokens.tsv: unknown line {n}"); errors += 1
    no_lemma = 0
    for l in lines:
        words = [w for w, _, _ in greek.words(l.text)]
        rows = by_line.get(l.n, [])
        forms = [r["form"] for r in rows]
        if words != forms:
            print(f"  ERROR line {l.n}: text words {words} != tokens.tsv {forms}"); errors += 1
        for r in rows:
            if not r["lemma"]:
                no_lemma += 1
    if no_lemma:
        print(f"  WARN {no_lemma} tokens without lemma"); warnings += 1

    # syntax: every head points at a word of its sentence or at a node of syntax-nodes.tsv
    nodes = read_syntax_nodes(work_dir / "syntax-nodes.tsv")
    ids: dict[str, set[str]] = collections.defaultdict(set)
    for t in tokens:
        for i in t.get("word_id", "").split("+"):
            if i:
                ids[t["sentence"]].add(i)
    for nd in nodes:
        ids[nd["sentence"]].add(nd["word_id"])
    dangling = [t for t in tokens if t.get("head") not in ("", "0") and t["head"] not in ids[t["sentence"]]]
    dangling += [nd for nd in nodes if nd["head"] not in ("", "0") and nd["head"] not in ids[nd["sentence"]]]
    if dangling:
        print(f"  WARN {len(dangling)} syntax heads point at no word of their sentence, e.g. "
              + ", ".join(f"{t.get('line', 'node')}:{t['form']}" for t in dangling[:8])); warnings += 1
    print(f"  syntax: {len(nodes)} nodes beyond the words (punctuation, omitted words)")

    # translations
    for path in sorted(work_dir.glob("*-*.txt")):
        if path.name.startswith("commentary-"):
            continue
        tdoc = parse_file(path)
        bad = [l.n for l in tdoc.lines if l.n not in seen]
        print(f"  translation {path.name}: {len(tdoc.lines)} segments" + (f", {len(bad)} start at line numbers absent from grc.txt (attach to the next line): {bad[:10]}" if bad else ""))

    # commentaries
    for path in sorted(work_dir.glob("commentary-*.md")):
        _, notes = parse_commentary_md(path)
        bad = [n["n"] for n in notes if n["from"] not in seen or n["to"] not in seen]
        print(f"  commentary {path.name}: {len(notes)} notes" + (f", {len(bad)} refer to line numbers absent from grc.txt (attach to the next line): {bad[:10]}" if bad else ""))

    # lexicon coverage (the work's own glossary counts as a lexicon)
    if lexicon_keys is not None and not isinstance(lexicon_keys, dict):
        lexicon_keys = None
    if lexicon_keys is not None:
        glossary = work_dir / "glossary.md"
        if glossary.exists():
            for raw in glossary.read_text(encoding="utf-8").splitlines():
                if raw.startswith("## "):
                    hw = raw[3:].strip()
                    lexicon_keys["exact"].add(greek.lemma_key(hw))
                    lexicon_keys["loose"].add(greek.strip_diacritics(hw))
        from .build import read_aliases
        aliases = read_aliases(work_dir / "aliases.tsv")
        for k, target in aliases.items():
            if target in lexicon_keys["exact"]:
                lexicon_keys["exact"].add(k)
                lexicon_keys["loose"].add(greek.strip_diacritics(k))
        counts = collections.Counter(t["lemma"] for t in tokens if t["lemma"])
        missing_exact = {lem: c for lem, c in counts.items() if greek.lemma_key(lem) not in lexicon_keys["exact"]}
        missing_loose = {lem: c for lem, c in missing_exact.items() if greek.strip_diacritics(lem) not in lexicon_keys["loose"]}
        tok_total = sum(counts.values())
        print(f"  lexicon coverage: {len(counts)} lemmas; {len(missing_exact)} not found exactly "
              f"({sum(missing_exact.values())}/{tok_total} tokens), {len(missing_loose)} not found even loosely "
              f"({sum(missing_loose.values())} tokens)")
        for lem, c in sorted(missing_loose.items(), key=lambda x: -x[1])[:60]:
            print(f"    {lem}\t{c}")
        for lem, c in sorted((x for x in missing_exact.items() if x[0] not in missing_loose), key=lambda x: -x[1])[:25]:
            print(f"    (loose only) {lem}\t{c}")
    # short definitions
    from .build import load_logeion_shortdefs, read_shortdef_overrides, resolve_short_definition
    exact, loose = load_logeion_shortdefs(sources)
    overrides = read_shortdef_overrides(work_dir / "shortdefs.tsv")
    from .build import read_aliases
    aliases = read_aliases(work_dir / "aliases.tsv")
    counts = collections.Counter(t["lemma"] for t in tokens if t["lemma"])
    no_short = {l: c for l, c in counts.items()
                if greek.lemma_key(l) not in overrides and resolve_short_definition(l, exact, loose) is None
                and not (greek.lemma_key(l) in aliases and (aliases[greek.lemma_key(l)] in exact or aliases[greek.lemma_key(l)] in overrides))}
    print(f"  short definitions: {len(counts) - len(no_short)}/{len(counts)} lemmas covered; "
          f"{len(no_short)} without ({sum(no_short.values())} tokens) - add them to shortdefs.tsv:")
    for lem, c in sorted(no_short.items(), key=lambda x: -x[1])[:60]:
        print(f"    {lem}\t{c}")
    return errors, warnings


def check_all(texts: Path, sources: Path) -> int:
    lexicon_keys = None
    cache = sources.parent / "build"
    if (cache / "lsj.jsonl").exists() and (cache / "ml.jsonl").exists():
        from .build import load_lexica
        lex = load_lexica(sources, cache)
        exact = {greek.lemma_key(e.headword) for es in lex.values() for e in es}
        loose = {greek.strip_diacritics(e.headword) for es in lex.values() for e in es}
        lexicon_keys = {"exact": exact, "loose": loose}
    else:
        print("(lexicon cache not built yet; run 'build' first for coverage figures)")
    errors = warnings = 0
    for work_dir in sorted(p for p in texts.iterdir() if p.is_dir() and (p / "grc.txt").exists()):
        e, w = check_work(work_dir, lexicon_keys, sources)
        errors += e
        warnings += w
    print(f"{errors} errors, {warnings} warnings")
    return 1 if errors else 0
