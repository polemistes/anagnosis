"""A built database's version comes from its content, not from the bytes of its file.

The reader fetches a text's pack again when the catalogue's version of the text differs from the
one it holds. The version used to be a hash of the database file, and the file changes with
things that are not the text: the SQLite library stamps its own number into the header, and
pages can be laid out otherwise. So a rebuild with nothing changed gave a new version, and every
phone would have fetched an identical pack again.

**The content digest** (`content_digest`): SHA-256 over the schema number (PRAGMA user_version)
and, for every table in the order of their names, the table's name, its columns' names in their
order, and the digests of its rows sorted. A row's digest is the SHA-256 of its values, each
written with a letter for its type and its length (NULL, integer, real, text as UTF-8, bytes); a
value of bytes that is zlib-compressed text (the dictionaries' html) is hashed as the text it
holds, so that the compressing library does not matter either. Indexes, the order of rows on
the pages, the page size, the library and the file's times do not enter. The same content gives
the same digest; one changed cell gives another.

**The rule** (`version_for`): a text's version stays what it is as long as its content digest
stays what it is; when the content changes, the new version is the first sixteen hex digits of
the new digest. The versions the phones already hold therefore stay valid: the records began on
2026-11-17 with the digests of the databases then installed, each beside the version it had.

**The records**: `data/versions.json` (tracked): {slug: {"version", "digest"}} for the texts of
the public catalogue and the lexicon; `data/versions-author.json` (not tracked) for the texts
held back, of which nothing stands in a tracked file. The catalogue's own format is unchanged
(the reader's parser reads named keys of flat objects; the digests are kept out of it all the
same, since readers already installed parse it too). Only a build into `data/` writes the
records; a build into another folder (`build --out`) reads them and changes nothing.
"""
from __future__ import annotations

import hashlib
import json
import sqlite3
import zlib
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
DATA = ROOT / "data"
RECORDS = "versions.json"
AUTHOR_RECORDS = "versions-author.json"


def _value(v) -> bytes:
    if v is None:
        return b"N"
    if isinstance(v, bool):
        v = int(v)
    if isinstance(v, int):
        return b"I" + str(v).encode()
    if isinstance(v, float):
        return b"F" + repr(v).encode()
    if isinstance(v, str):
        b = v.encode("utf-8")
        return b"T" + str(len(b)).encode() + b":" + b
    b = bytes(v)
    try:
        text = zlib.decompress(b)
        return b"Z" + str(len(text)).encode() + b":" + text
    except zlib.error:
        return b"B" + str(len(b)).encode() + b":" + b


def table_digests(path: Path) -> dict[str, str]:
    """Each table's digest (see the module's text), by name."""
    db = sqlite3.connect(f"file:{path}?mode=ro", uri=True)
    try:
        out = {}
        tables = [r[0] for r in db.execute("SELECT name FROM sqlite_master WHERE type = 'table' AND name NOT LIKE 'sqlite_%' ORDER BY name")]
        for table in tables:
            columns = [r[1] for r in db.execute(f'PRAGMA table_info("{table}")')]
            rows = []
            for row in db.execute(f'SELECT * FROM "{table}"'):
                h = hashlib.sha256()
                for v in row:
                    h.update(_value(v))
                    h.update(b"\x1f")
                rows.append(h.digest())
            rows.sort()
            h = hashlib.sha256()
            h.update(("\x1e".join([table, *columns]) + "\x1d").encode("utf-8"))
            h.update(str(len(rows)).encode() + b"\x1d")
            for r in rows:
                h.update(r)
            out[table] = h.hexdigest()
        out["(schema number)"] = str(db.execute("PRAGMA user_version").fetchone()[0])
        return out
    finally:
        db.close()


def content_digest(path: Path) -> str:
    tables = table_digests(path)
    h = hashlib.sha256()
    for name in sorted(tables):
        h.update(f"{name}={tables[name]}\n".encode("utf-8"))
    return h.hexdigest()


def load(data: Path = DATA) -> dict[str, dict[str, str]]:
    """The records of both files together: slug -> {"version", "digest"}."""
    out: dict[str, dict[str, str]] = {}
    for name in (RECORDS, AUTHOR_RECORDS):
        f = data / name
        if f.exists():
            out.update(json.loads(f.read_text(encoding="utf-8")))
    return out


def version_for(slug: str, digest: str, records: dict[str, dict[str, str]]) -> str:
    """The version of a database with this content: the recorded one while the content is the
    recorded content, else the first sixteen hex digits of the new digest."""
    r = records.get(slug)
    return r["version"] if r and r.get("digest") == digest else digest[:16]


def _held(slug: str, texts: Path) -> bool:
    """Whether a text is held back from the public catalogue (private.held_back): its record
    then goes into the file that is not tracked."""
    from .build import read_catalog_entry
    from .private import held_back

    work = texts / slug
    if not (work / "grc.txt").exists():
        return False  # the lexicon
    return held_back(slug, read_catalog_entry(work).get("release"))


def record(slug: str, version: str, digest: str, data: Path = DATA, texts: Path = ROOT / "texts") -> None:
    """Write a text's version and digest into the records (the tracked file, or the author's for
    a text held back; never both)."""
    held = _held(slug, texts)
    for name, mine in ((RECORDS, not held), (AUTHOR_RECORDS, held)):
        f = data / name
        recs = json.loads(f.read_text(encoding="utf-8")) if f.exists() else {}
        if mine:
            recs[slug] = {"version": version, "digest": digest}
        elif slug in recs:
            del recs[slug]
        else:
            continue
        f.write_text(json.dumps(dict(sorted(recs.items())), ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def stamp(path: Path, data: Path = DATA) -> tuple[str, str]:
    """(version, digest) of a database just built; writes <file>.version beside it, and the
    record if the database stands in `data`."""
    digest = content_digest(path)
    version = version_for(path.stem, digest, load(data))
    path.with_suffix(path.suffix + ".version").write_text(version + "\n", encoding="utf-8")
    if path.parent.resolve() == data.resolve():
        record(path.stem, version, digest, data)
    return version, digest


def seed(data: Path = DATA) -> list[str]:
    """The starting point: for every database in `data` that has no record yet, its digest beside
    the version in its .version file (the version the catalogue and the phones have)."""
    recs = load(data)
    out = []
    for db in sorted(data.glob("*.sqlite")):
        v = db.with_suffix(".sqlite.version")
        if db.stem in recs or not v.exists():
            continue
        version, digest = v.read_text(encoding="utf-8").strip(), content_digest(db)
        record(db.stem, version, digest, data)
        out.append(f"{db.stem}: version {version}, content {digest[:16]}…")
    return out


def check(data: Path = DATA) -> tuple[list[str], list[str]]:
    """(errors, notes) for `check`: a database whose content is not the recorded content, or whose
    .version file or catalogue entry gives another version than the record; a recorded version
    that differs from the last commit's though the content digest is the same."""
    import subprocess

    errors, notes = [], []
    recs = load(data)
    catalogue = {}
    for name in ("catalog-author.json", "catalog.json"):
        f = data / name
        if f.exists():
            catalogue.update({e["slug"]: e.get("version", "") for e in json.loads(f.read_text(encoding="utf-8"))})
    got = subprocess.run(["git", "-C", str(ROOT), "show", f"HEAD:data/{RECORDS}"], capture_output=True, text=True)
    committed = json.loads(got.stdout) if got.returncode == 0 and got.stdout.strip() else {}
    for db in sorted(data.glob("*.sqlite")):
        slug = db.stem
        r = recs.get(slug)
        if r is None:
            errors.append(f"{slug}: no version record (run `catalog`, which records what is installed)")
            continue
        digest = content_digest(db)
        if digest != r["digest"]:
            errors.append(f"{slug}: the database's content ({digest[:16]}…) is not the recorded content ({r['digest'][:16]}…): "
                          "build it again, or the record is stale")
        v = db.with_suffix(".sqlite.version")
        if v.exists() and v.read_text(encoding="utf-8").strip() != r["version"]:
            errors.append(f"{slug}: {v.name} says {v.read_text(encoding='utf-8').strip()}, the record {r['version']}")
        if slug in catalogue and catalogue[slug] != r["version"]:
            errors.append(f"{slug}: the catalogue says version {catalogue[slug]}, the record {r['version']}")
        c = committed.get(slug)
        if c and c["digest"] == r["digest"] and c["version"] != r["version"]:
            errors.append(f"{slug}: the version changed ({c['version']} to {r['version']}) though the content did not")
        elif c and c["digest"] != r["digest"]:
            notes.append(f"{slug}: content changed since the last commit: version {c['version']} becomes {r['version']}")
    return errors, notes
