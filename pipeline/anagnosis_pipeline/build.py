"""Build the SQLite bundle from texts/ and the lexica.

Conventions inside texts/<slug>/:
    grc.txt               the Greek text
    tokens.tsv            per-word lemma and morphology, aligned to grc.txt
    <lang>-<name>.txt     a translation (e.g. eng-jebb.txt)
    commentary-<name>.md  a commentary
"""
from __future__ import annotations

import html
import json
import re
import sqlite3
import sys
from pathlib import Path

from . import greek
from .commentary import parse_commentary_md
from .import_perseus import read_syntax_nodes, read_tokens
from .lexicon import Entry, parse_lsj, parse_middle_liddell
from .linenum import STEPHANUS, VERSE
from .textfmt import Line, Section, Speaker, Stage, parse_file

SCHEMA_VERSION = 1

TEXT_SCHEMA = """
CREATE TABLE meta (key TEXT PRIMARY KEY, value TEXT NOT NULL);

CREATE TABLE works (
    id INTEGER PRIMARY KEY, slug TEXT NOT NULL UNIQUE, title TEXT NOT NULL, author TEXT,
    lang TEXT NOT NULL, source TEXT, edition TEXT, license TEXT
);
CREATE TABLE sections (
    id INTEGER PRIMARY KEY, work_id INTEGER NOT NULL REFERENCES works(id), ord INTEGER NOT NULL,
    level INTEGER NOT NULL, kind TEXT NOT NULL, label TEXT, first_line_id INTEGER
);
CREATE TABLE lines (
    id INTEGER PRIMARY KEY, work_id INTEGER NOT NULL REFERENCES works(id), ord INTEGER NOT NULL,
    n TEXT NOT NULL, n_int INTEGER NOT NULL, n_sub TEXT NOT NULL DEFAULT '',
    section_id INTEGER REFERENCES sections(id), speaker TEXT, speech_start INTEGER NOT NULL DEFAULT 0,
    text TEXT NOT NULL
);
CREATE INDEX lines_work_n ON lines(work_id, n_int, n_sub);
CREATE TABLE tokens (
    id INTEGER PRIMARY KEY, line_id INTEGER NOT NULL REFERENCES lines(id), ord INTEGER NOT NULL,
    start INTEGER NOT NULL, end INTEGER NOT NULL, form TEXT NOT NULL,
    lemma TEXT NOT NULL, lemma_key TEXT NOT NULL, postag TEXT NOT NULL DEFAULT '',
    relation TEXT, head INTEGER, sentence TEXT, word_id TEXT
);
CREATE INDEX tokens_line ON tokens(line_id, ord);
CREATE INDEX tokens_lemma ON tokens(lemma_key);
-- Treebank nodes that are not words of the text: punctuation and artificial (elliptic) nodes.
-- Together with tokens they make up the dependency tree of a sentence; head refers to a
-- word_id within the sentence, 0 being the sentence root.
CREATE TABLE sentence_nodes (
    id INTEGER PRIMARY KEY, work_id INTEGER NOT NULL REFERENCES works(id), sentence TEXT NOT NULL,
    word_id INTEGER NOT NULL, form TEXT NOT NULL, lemma TEXT, postag TEXT NOT NULL DEFAULT '',
    relation TEXT, head INTEGER, artificial INTEGER NOT NULL DEFAULT 0
);
CREATE INDEX sentence_nodes_sentence ON sentence_nodes(work_id, sentence);

CREATE TABLE translations (
    id INTEGER PRIMARY KEY, work_id INTEGER NOT NULL REFERENCES works(id), slug TEXT NOT NULL,
    title TEXT, translator TEXT, lang TEXT NOT NULL, source TEXT, edition TEXT, license TEXT
);
CREATE TABLE translation_segments (
    id INTEGER PRIMARY KEY, translation_id INTEGER NOT NULL REFERENCES translations(id),
    ord INTEGER NOT NULL, kind TEXT NOT NULL, speaker TEXT, speech_start INTEGER NOT NULL DEFAULT 0,
    from_n_int INTEGER NOT NULL, from_n_sub TEXT NOT NULL DEFAULT '',
    to_n_int INTEGER NOT NULL, to_n_sub TEXT NOT NULL DEFAULT '', text TEXT NOT NULL
);
CREATE INDEX translation_segments_range ON translation_segments(translation_id, from_n_int);

CREATE TABLE commentaries (
    id INTEGER PRIMARY KEY, work_id INTEGER NOT NULL REFERENCES works(id), slug TEXT NOT NULL,
    title TEXT, author TEXT, lang TEXT, source TEXT, license TEXT
);
CREATE TABLE commentary_notes (
    id INTEGER PRIMARY KEY, commentary_id INTEGER NOT NULL REFERENCES commentaries(id),
    ord INTEGER NOT NULL, n TEXT NOT NULL, from_n_int INTEGER NOT NULL, to_n_int INTEGER NOT NULL,
    html TEXT NOT NULL
);
CREATE INDEX commentary_notes_range ON commentary_notes(commentary_id, from_n_int);

-- A lemma the dictionaries list under another headword (Homeric ἠέλιος under ἥλιος):
-- the word sheet shows the target's entries and short definition.
CREATE TABLE lemma_aliases (lemma_key TEXT PRIMARY KEY, target_key TEXT NOT NULL);

CREATE TABLE documents (
    id INTEGER PRIMARY KEY, work_id INTEGER NOT NULL REFERENCES works(id), slug TEXT NOT NULL,
    title TEXT NOT NULL, source TEXT, license TEXT, html TEXT NOT NULL
);

-- Per-text lexicon material: the glossary of names and the short definitions of the text's lemmas.
CREATE TABLE lexicons (
    id INTEGER PRIMARY KEY, slug TEXT NOT NULL UNIQUE, title TEXT NOT NULL, source TEXT, license TEXT
);
CREATE TABLE lexicon_entries (
    id INTEGER PRIMARY KEY, lexicon_id INTEGER NOT NULL REFERENCES lexicons(id), key TEXT NOT NULL,
    headword TEXT NOT NULL, homograph INTEGER NOT NULL DEFAULT 0, lemma_key TEXT NOT NULL,
    loose_key TEXT NOT NULL, sort_key TEXT NOT NULL, html TEXT NOT NULL
);
CREATE INDEX lexicon_entries_key ON lexicon_entries(lemma_key);
CREATE INDEX lexicon_entries_loose ON lexicon_entries(loose_key);
CREATE TABLE short_definitions (
    lemma_key TEXT NOT NULL PRIMARY KEY, source TEXT NOT NULL, definition TEXT NOT NULL
);
"""

# The shared dictionary database: full LSJ and Middle Liddell.
LEXICON_SCHEMA = """
CREATE TABLE meta (key TEXT PRIMARY KEY, value TEXT NOT NULL);
CREATE TABLE lexicons (
    id INTEGER PRIMARY KEY, slug TEXT NOT NULL UNIQUE, title TEXT NOT NULL, source TEXT, license TEXT
);
CREATE TABLE lexicon_entries (
    id INTEGER PRIMARY KEY, lexicon_id INTEGER NOT NULL REFERENCES lexicons(id), key TEXT NOT NULL,
    headword TEXT NOT NULL, homograph INTEGER NOT NULL DEFAULT 0, lemma_key TEXT NOT NULL,
    loose_key TEXT NOT NULL, sort_key TEXT NOT NULL, html BLOB NOT NULL
);
CREATE INDEX lexicon_entries_key ON lexicon_entries(lemma_key);
CREATE INDEX lexicon_entries_loose ON lexicon_entries(loose_key);
CREATE INDEX lexicon_entries_sort ON lexicon_entries(lexicon_id, sort_key);
CREATE TABLE short_definitions (
    lemma_key TEXT NOT NULL PRIMARY KEY, source TEXT NOT NULL, definition TEXT NOT NULL
);
"""
# In the shared database the html column holds zlib-compressed UTF-8 (BLOB); see meta html_encoding.

LEXICONS = {
    "lsj": {
        "title": "Liddell, Scott, Jones: A Greek-English Lexicon (1940)",
        "source": "Perseus Digital Library, https://github.com/PerseusDL/lexica",
        "license": "CC BY-SA 4.0",
    },
    "ml": {
        "title": "Liddell & Scott: An Intermediate Greek-English Lexicon (1889)",
        "source": "Perseus Digital Library, hopper-texts-GreekRoman",
        "license": "CC BY-SA 3.0 US",
    },
}


def line_n_parts(n: str) -> tuple[int, str]:
    from .linenum import parts

    return parts(n)


# ------------------------------------------------------------------ markdown

def md_to_html(md: str) -> str:
    paras = [p.strip() for p in re.split(r"\n\s*\n", md) if p.strip()]
    out = []
    for p in paras:
        m = re.match(r"^(#{1,3}) (.+)$", p)
        if m:
            level = len(m.group(1))
            out.append(f"<h{level}>{html.escape(m.group(2).strip(), quote=False)}</h{level}>")
            continue
        s = html.escape(p, quote=False)
        s = re.sub(r"\[([^\]]+)\]\(#([0-9a-z.-]+)\)", r'<a href="note:\2">\1</a>', s)
        s = re.sub(r"(?<!\\)\*\*(.+?)(?<!\\)\*\*", r"<b>\1</b>", s)
        s = re.sub(r"(?<!\\)\*(.+?)(?<!\\)\*", r"<i>\1</i>", s)
        s = s.replace("\\*", "*").replace("\\_", "_")
        s = re.sub(r"\s*\n\s*", " ", s)
        out.append(f"<p>{s}</p>")
    return "".join(out)


# ------------------------------------------------------------------ lexica cache

def load_lexica(sources: Path, cache_dir: Path) -> dict[str, list[Entry]]:
    cache_dir.mkdir(parents=True, exist_ok=True)
    result = {}
    for slug, fn in (("lsj", parse_lsj), ("ml", parse_middle_liddell)):
        cache = cache_dir / f"{slug}.jsonl"
        if cache.exists():
            entries = [Entry(**json.loads(l)) for l in cache.open(encoding="utf-8")]
        else:
            print(f"parsing {slug} (cached afterwards in {cache}) ...", file=sys.stderr)
            entries = fn(sources)
            with cache.open("w", encoding="utf-8") as f:
                for e in entries:
                    f.write(json.dumps(e.__dict__, ensure_ascii=False) + "\n")
        result[slug] = entries
    return result


# ------------------------------------------------------------------ build

def _finish(db: sqlite3.Connection, out: Path) -> None:
    db.execute("PRAGMA user_version = %d" % SCHEMA_VERSION)
    db.commit()
    db.execute("VACUUM")
    db.close()
    import hashlib
    digest = hashlib.sha256(out.read_bytes()).hexdigest()[:16]
    out.with_suffix(out.suffix + ".version").write_text(digest + "\n", encoding="utf-8")
    print(f"wrote {out} ({out.stat().st_size / 1e6:.1f} MB), version {digest}")


def build(texts: Path, sources: Path, out_dir: Path, only: str | None = None) -> None:
    """Write data/lexicon.sqlite (LSJ + Middle Liddell, shared) and data/<slug>.sqlite per text.

    With `only`, rebuild just that text's database (and the catalog), keeping the lexicon.
    """
    out_dir.mkdir(parents=True, exist_ok=True)
    if only is None:
        build_lexicon(sources, out_dir)
    build_texts(texts, sources, out_dir, only)


def build_lexicon(sources: Path, out_dir: Path) -> None:
    # the shared dictionaries
    lex_path = out_dir / "lexicon.sqlite"
    if lex_path.exists():
        lex_path.unlink()
    db = sqlite3.connect(lex_path)
    db.executescript(LEXICON_SCHEMA)
    db.executemany("INSERT INTO meta VALUES (?, ?)", [("schema_version", str(SCHEMA_VERSION)), ("kind", "lexicon"), ("html_encoding", "zlib")])
    lexica = load_lexica(sources, sources.parent / "build")
    import zlib

    def pack(html_text: str) -> bytes:
        # citation targets are not used by the app; dropping them saves a third of the size
        html_text = re.sub(r' data-ref="[^"]*"', "", html_text)
        return zlib.compress(html_text.encode("utf-8"), 9)

    for slug, entries in lexica.items():
        info = LEXICONS[slug]
        cur = db.execute(
            "INSERT INTO lexicons (slug, title, source, license) VALUES (?, ?, ?, ?)",
            (slug, info["title"], info["source"], info["license"]),
        )
        lex_id = cur.lastrowid
        rows = [
            (lex_id, e.key, e.headword, e.homograph, greek.lemma_key(e.headword), greek.strip_diacritics(e.headword), e.sort_key, pack(e.html))
            for e in entries
        ]
        db.executemany(
            "INSERT INTO lexicon_entries (lexicon_id, key, headword, homograph, lemma_key, loose_key, sort_key, html) VALUES (?,?,?,?,?,?,?,?)",
            rows,
        )
        print(f"lexicon {slug}: {len(rows)} entries")
    from .forms import build_forms

    build_forms(db, sources)
    # Logeion's short definitions for every headword that has one, for the dictionary search
    exact, _loose = load_logeion_shortdefs(sources)
    headword_keys = {greek.lemma_key(e.headword) for entries in lexica.values() for e in entries}
    rows = [(k, "logeion", d) for k, d in exact.items() if k in headword_keys]
    db.executemany("INSERT OR IGNORE INTO short_definitions (lemma_key, source, definition) VALUES (?,?,?)", rows)
    print(f"short definitions in lexicon: {len(rows)}")
    _finish(db, lex_path)


def build_texts(texts: Path, sources: Path, out_dir: Path, only: str | None = None) -> None:
    # one database per text, and a catalog of them for the app's library
    catalog = []
    for work_dir in sorted(p for p in texts.iterdir() if p.is_dir() and (p / "grc.txt").exists()):
        catalog.append(read_catalog_entry(work_dir))
        if only is not None and work_dir.name != only:
            continue
        path = out_dir / f"{work_dir.name}.sqlite"
        if path.exists():
            path.unlink()
        db = sqlite3.connect(path)
        db.executescript(TEXT_SCHEMA)
        db.executemany("INSERT INTO meta VALUES (?, ?)", [("schema_version", str(SCHEMA_VERSION)), ("kind", "text")])
        keys, lemmas = build_work(db, work_dir)
        overrides = read_shortdef_overrides(work_dir / "shortdefs.tsv")
        aliases = read_aliases(work_dir / "aliases.tsv")
        db.executemany("INSERT INTO lemma_aliases VALUES (?, ?)", sorted(aliases.items()))
        build_short_definitions(db, sources, lemmas, overrides, aliases)
        _finish(db, path)
    (out_dir / "catalog.json").write_text(json.dumps(catalog, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    # each text's own entry, for the app that sells it to hand to the reader
    for entry in catalog:
        (out_dir / f"{entry['slug']}.catalog.json").write_text(json.dumps([entry], ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"wrote {out_dir / 'catalog.json'}: {len(catalog)} texts")


def read_catalog_entry(work_dir: Path) -> dict:
    """texts/<slug>/catalog.toml-like header in about.md, or defaults from grc.txt."""
    from .textfmt import parse_file as _parse

    meta = _parse(work_dir / "grc.txt").meta
    entry = {"slug": work_dir.name, "title": meta.get("title", work_dir.name), "author": meta.get("author", ""),
             "title_en": "", "author_en": "", "description": "", "edition": meta.get("edition", "")}
    about = work_dir / "about.md"
    if about.exists():
        body = []
        for raw in about.read_text(encoding="utf-8").splitlines():
            m = re.match(r"^# ([a-z_]+): (.*)$", raw)
            if m and not body:
                entry[m.group(1)] = m.group(2).strip()
            elif body or raw.strip():
                body.append(raw)
        entry["description"] = "\n".join(body).strip()
    return entry


def build_work(db: sqlite3.Connection, work_dir: Path) -> set[str]:
    slug = work_dir.name
    doc = parse_file(work_dir / "grc.txt")
    m = doc.meta
    cur = db.execute(
        "INSERT INTO works (slug, title, author, lang, source, edition, license) VALUES (?,?,?,?,?,?,?)",
        (slug, m.get("title", slug), m.get("author"), m.get("lang", "grc"), m.get("source"), m.get("edition"), m.get("license")),
    )
    work_id = cur.lastrowid

    # sections, speakers and lines
    section_stack: list[tuple[int, int]] = []  # (level, section_id)
    speaker = None
    speech_start = 0
    line_ids: dict[str, int] = {}
    line_texts: dict[str, str] = {}
    ord_line = ord_section = 0
    pending_section_ids: list[int] = []
    for item in doc.items:
        if isinstance(item, Section):
            while section_stack and section_stack[-1][0] >= item.level:
                section_stack.pop()
            ord_section += 1
            cur = db.execute(
                "INSERT INTO sections (work_id, ord, level, kind, label) VALUES (?,?,?,?,?)",
                (work_id, ord_section, item.level, item.kind, item.label or None),
            )
            section_stack.append((item.level, cur.lastrowid))
            pending_section_ids.append(cur.lastrowid)
        elif isinstance(item, Speaker):
            speaker = item.name or None
            speech_start = 1
        elif isinstance(item, Stage):
            pass  # stage directions are not part of the Greek text as transmitted
        elif isinstance(item, Line):
            n_int, n_sub = line_n_parts(item.n)
            ord_line += 1
            cur = db.execute(
                "INSERT INTO lines (work_id, ord, n, n_int, n_sub, section_id, speaker, speech_start, text) VALUES (?,?,?,?,?,?,?,?,?)",
                (work_id, ord_line, item.n, n_int, n_sub, section_stack[-1][1] if section_stack else None, speaker, speech_start, item.text),
            )
            speech_start = 0
            if item.n in line_ids:
                raise SystemExit(f"{slug}: duplicate line number {item.n}")
            line_ids[item.n] = cur.lastrowid
            line_texts[item.n] = item.text
            for sid in pending_section_ids:
                db.execute("UPDATE sections SET first_line_id = ? WHERE id = ?", (cur.lastrowid, sid))
            pending_section_ids = []

    # tokens
    lemma_keys: set[str] = set()
    lemmas: dict[str, str] = {}
    tokens_by_line: dict[str, list[dict]] = {}
    for row in read_tokens(work_dir / "tokens.tsv"):
        tokens_by_line.setdefault(row["line"], []).append(row)
    for n, rows in tokens_by_line.items():
        if n not in line_ids:
            raise SystemExit(f"{slug}: tokens.tsv refers to unknown line {n}")
        words = greek.words(line_texts[n])
        if len(words) != len(rows):
            raise SystemExit(f"{slug}: line {n}: {len(words)} words in text but {len(rows)} in tokens.tsv (run 'check')")
        for row, (form, start, end) in zip(rows, words):
            lemma = row["lemma"]
            key = greek.lemma_key(lemma)
            lemma_keys.add(key)
            lemmas[key] = lemma
            db.execute(
                "INSERT INTO tokens (line_id, ord, start, end, form, lemma, lemma_key, postag, relation, head, sentence, word_id) VALUES (?,?,?,?,?,?,?,?,?,?,?,?)",
                (line_ids[n], int(row["ord"]), start, end, form, lemma, key, row["postag"], row["relation"] or None,
                 int(row["head"]) if row["head"].isdigit() else None, row["sentence"] or None, row.get("word_id") or None),
            )
    nodes = read_syntax_nodes(work_dir / "syntax-nodes.tsv")
    for row in nodes:
        db.execute(
            "INSERT INTO sentence_nodes (work_id, sentence, word_id, form, lemma, postag, relation, head, artificial) VALUES (?,?,?,?,?,?,?,?,?)",
            (work_id, row["sentence"], int(row["word_id"]), row["form"], row["lemma"] or None, row["postag"],
             row["relation"] or None, int(row["head"]) if row["head"].isdigit() else None, 1 if row["artificial"] else 0),
        )
    print(f"work {slug}: {len(line_ids)} lines, {sum(len(r) for r in tokens_by_line.values())} tokens, {len(lemma_keys)} lemmas, {len(nodes)} syntax nodes")
    # an epic is cited by book and line; the app shows the line within the book
    if any(n.count(".") == 1 for n in line_ids):
        db.execute("INSERT OR REPLACE INTO meta VALUES ('line_numbers', 'book.line')")
    # the New Testament is cited by book, chapter and verse (1.5.3; the app shows 5:3)
    elif line_ids and all(VERSE.match(n) for n in line_ids):
        db.execute("INSERT OR REPLACE INTO meta VALUES ('line_numbers', 'verse')")
    # prose is cited by Stephanus page, section and line (172a1)
    elif line_ids and all(STEPHANUS.match(n) for n in line_ids):
        db.execute("INSERT OR REPLACE INTO meta VALUES ('line_numbers', 'stephanus')")
    # prose is shown as paragraphs; an automatic syntax is labelled as such
    for key in ("layout", "syntax"):
        if m.get(key):
            db.execute("INSERT OR REPLACE INTO meta VALUES (?, ?)", (key, m[key]))

    last_line = max(line_ids, key=lambda n: line_n_parts(n))
    last_int, last_sub = line_n_parts(last_line)

    # translations
    for path in sorted(work_dir.glob("*-*.txt")):
        if path.name.startswith("commentary-"):
            continue
        build_translation(db, work_id, path, (last_int, last_sub))

    # commentaries
    for path in sorted(work_dir.glob("commentary-*.md")):
        build_commentary(db, work_id, path)

    # free-standing documents: manuscripts and sigla, later perhaps introductions
    preferred = ["introduction", "preface", "appendix", "sigla"]
    docs = [p for p in work_dir.glob("*.md") if not p.name.startswith("commentary-") and p.name not in ("glossary.md", "about.md")]
    for path in sorted(docs, key=lambda p: (preferred.index(p.stem) if p.stem in preferred else len(preferred), p.stem)):
        build_document(db, work_id, path)

    # glossary (hand-written entries, e.g. proper names missing from the lexica)
    if (work_dir / "glossary.md").exists():
        build_glossary(db, slug, work_dir / "glossary.md")

    return lemma_keys, lemmas


def read_shortdef_overrides(path: Path) -> dict[str, str]:
    """texts/<work>/shortdefs.tsv: 'lemma<TAB>definition' lines; '#' comments."""
    out: dict[str, str] = {}
    if not path.exists():
        return out
    for raw in path.read_text(encoding="utf-8").splitlines():
        if not raw.strip() or raw.startswith("#"):
            continue
        lemma, _, definition = raw.partition("\t")
        if definition.strip():
            out[greek.lemma_key(lemma)] = definition.strip()
    return out


def load_logeion_shortdefs(sources: Path) -> tuple[dict[str, str], dict[str, list[str]]]:
    """Logeion short definitions: exact key -> definition, and loose key -> [exact keys]."""
    exact: dict[str, str] = {}
    loose: dict[str, list[str]] = {}
    path = sources / "logeion-shortdefs.txt"
    if not path.exists():
        print(f"warning: {path} missing, no short definitions (run 'fetch')", file=sys.stderr)
        return exact, loose
    for raw in path.read_text(encoding="utf-8").splitlines():
        lemma, _, definition = raw.partition("\t")
        lemma, definition = lemma.strip(), definition.strip()
        if not lemma or not definition or definition.isdigit():
            continue
        key = greek.lemma_key(lemma)
        if key in exact:
            continue
        exact[key] = definition
        loose.setdefault(greek.strip_diacritics(lemma), []).append(key)
    return exact, loose


def resolve_short_definition(lemma: str, exact: dict[str, str], loose: dict[str, list[str]]) -> str | None:
    key = greek.lemma_key(lemma)
    if key in exact:
        return exact[key]
    candidates = loose.get(greek.strip_diacritics(lemma), [])
    if len(candidates) == 1:
        return exact[candidates[0]]
    return None


def read_aliases(path: Path) -> dict[str, str]:
    """texts/<work>/aliases.tsv: 'lemma<TAB>headword' lines ('#' comments); lemma key -> headword key."""
    out: dict[str, str] = {}
    if not path.exists():
        return out
    for raw in path.read_text(encoding="utf-8").splitlines():
        if not raw.strip() or raw.startswith("#"):
            continue
        lemma, _, target = raw.partition("\t")
        if target.strip():
            out[greek.lemma_key(lemma)] = greek.lemma_key(target.strip())
    return out


def build_short_definitions(db: sqlite3.Connection, sources: Path, lemmas: dict[str, str], overrides: dict[str, str],
                            aliases: dict[str, str] | None = None) -> None:
    exact, loose = load_logeion_shortdefs(sources)
    aliases = aliases or {}
    rows = []
    missing = []
    for key, lemma in sorted(lemmas.items()):
        if key in overrides:
            rows.append((key, "override", overrides[key]))
            continue
        definition = resolve_short_definition(lemma, exact, loose)
        if definition is None and key in aliases:
            definition = overrides.get(aliases[key]) or exact.get(aliases[key])
        if definition is None:
            missing.append(lemma)
        else:
            rows.append((key, "logeion", definition))
    db.executemany("INSERT INTO short_definitions (lemma_key, source, definition) VALUES (?,?,?)", rows)
    print(f"short definitions: {len(rows)} of {len(lemmas)} lemmas ({len(missing)} missing; 'check' lists them)")


def build_document(db: sqlite3.Connection, work_id: int, path: Path) -> None:
    meta: dict[str, str] = {}
    body: list[str] = []
    for raw in path.read_text(encoding="utf-8").splitlines():
        if not body and re.match(r"^# [a-z]+: ", raw):
            k, _, v = raw[2:].partition(":")
            meta[k.strip()] = v.strip()
        elif body or raw.strip():
            body.append(raw)
    db.execute(
        "INSERT INTO documents (work_id, slug, title, source, license, html) VALUES (?,?,?,?,?,?)",
        (work_id, path.stem, meta.get("title", path.stem), meta.get("source"), meta.get("license"), md_to_html("\n".join(body))),
    )
    print(f"document {path.stem}: {meta.get('title')}")


def build_glossary(db: sqlite3.Connection, slug: str, path: Path) -> None:
    meta: dict[str, str] = {}
    entries: list[tuple[str, list[str]]] = []
    for raw in path.read_text(encoding="utf-8").splitlines():
        if not entries and raw.startswith("#") and not raw.startswith("##"):
            k, _, v = raw[1:].partition(":")
            meta[k.strip()] = v.strip()
        elif raw.startswith("## "):
            entries.append((raw[3:].strip(), []))
        elif entries:
            entries[-1][1].append(raw)
    cur = db.execute(
        "INSERT INTO lexicons (slug, title, source, license) VALUES (?,?,?,?)",
        (f"{slug}-glossary", meta.get("title", "Glossary"), None, meta.get("license")),
    )
    lex_id = cur.lastrowid
    for headword, body in entries:
        db.execute(
            "INSERT INTO lexicon_entries (lexicon_id, key, headword, homograph, lemma_key, loose_key, sort_key, html) VALUES (?,?,?,?,?,?,?,?)",
            (lex_id, headword, headword, 0, greek.lemma_key(headword), greek.strip_diacritics(headword),
             greek.strip_diacritics(headword), md_to_html("\n".join(body))),
        )
    print(f"glossary {path}: {len(entries)} entries")


def build_translation(db: sqlite3.Connection, work_id: int, path: Path, last: tuple[int, str]) -> None:
    doc = parse_file(path)
    m = doc.meta
    lang, _, name = path.stem.partition("-")
    cur = db.execute(
        "INSERT INTO translations (work_id, slug, title, translator, lang, source, edition, license) VALUES (?,?,?,?,?,?,?,?)",
        (work_id, path.stem, m.get("title"), m.get("translator"), m.get("lang", lang), m.get("source"), m.get("edition"), m.get("license")),
    )
    tr_id = cur.lastrowid
    # collect segments in order, then compute ranges from the next speech segment's start
    segs: list[dict] = []
    speaker = None
    speech_start = 0
    for item in doc.items:
        if isinstance(item, Speaker):
            speaker = item.name or None
            speech_start = 1
        elif isinstance(item, Stage):
            segs.append({"kind": "stage", "speaker": None, "n": None, "text": item.text, "speech_start": 0})
        elif isinstance(item, Line):
            segs.append({"kind": "speech", "speaker": speaker, "n": item.n, "text": item.text, "speech_start": speech_start})
            speech_start = 0
    # stage directions take the start of the next speech segment (or the previous one at the end)
    next_n = None
    for s in reversed(segs):
        if s["n"] is not None:
            next_n = s["n"]
        else:
            s["n"] = next_n
    prev_n = None
    for s in segs:
        if s["n"] is None:
            s["n"] = prev_n or "1"
        prev_n = s["n"]
    starts = [line_n_parts(s["n"]) for s in segs]
    count = 0
    for i, s in enumerate(segs):
        frm = starts[i]
        to = last
        for j in range(i + 1, len(segs)):
            if segs[j]["kind"] == "speech" and starts[j] > frm:
                nxt = starts[j]
                to = (nxt[0] - 1, "") if nxt[1] == "" else (nxt[0], "")
                break
        if to < frm:
            to = frm
        db.execute(
            "INSERT INTO translation_segments (translation_id, ord, kind, speaker, speech_start, from_n_int, from_n_sub, to_n_int, to_n_sub, text) VALUES (?,?,?,?,?,?,?,?,?,?)",
            (tr_id, i + 1, s["kind"], s["speaker"], s["speech_start"], frm[0], frm[1], to[0], to[1], s["text"]),
        )
        count += 1
    print(f"translation {path.stem}: {count} segments")


def build_commentary(db: sqlite3.Connection, work_id: int, path: Path) -> None:
    meta, notes = parse_commentary_md(path)
    cur = db.execute(
        "INSERT INTO commentaries (work_id, slug, title, author, lang, source, license) VALUES (?,?,?,?,?,?,?)",
        (work_id, path.stem, meta.get("title"), meta.get("author"), meta.get("lang"), meta.get("source"), meta.get("license")),
    )
    c_id = cur.lastrowid
    for i, note in enumerate(notes):
        db.execute(
            "INSERT INTO commentary_notes (commentary_id, ord, n, from_n_int, to_n_int, html) VALUES (?,?,?,?,?,?)",
            (c_id, i + 1, note["n"], line_n_parts(note["from"])[0], line_n_parts(note["to"])[0], md_to_html(note["body"])),
        )
    print(f"commentary {path.stem}: {len(notes)} notes")
