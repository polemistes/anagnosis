"""The version of a built database follows its content (versions.py)."""
import sqlite3
import tempfile
import unittest
import zlib
from pathlib import Path

from anagnosis_pipeline import versions


def make(path: Path, rows, page_size=4096, reverse=False, vacuum=True, html=b"", level=9):
    db = sqlite3.connect(path)
    db.execute(f"PRAGMA page_size = {page_size}")
    db.execute("CREATE TABLE lines (id INTEGER PRIMARY KEY, n TEXT NOT NULL, text TEXT, extra BLOB)")
    db.execute("CREATE TABLE meta (key TEXT PRIMARY KEY, value TEXT)")
    db.execute("CREATE INDEX lines_n ON lines(n)")
    for r in (reversed(rows) if reverse else rows):
        db.execute("INSERT INTO lines VALUES (?,?,?,?)", (*r, zlib.compress(html, level) if html else None))
    db.execute("INSERT INTO meta VALUES ('kind', 'text')")
    db.execute("PRAGMA user_version = 1")
    db.commit()
    if vacuum:
        db.execute("VACUUM")
    db.close()


ROWS = [(1, "1.1", "Περὶ πολλοῦ"), (2, "1.2", "ἂν ποιησαίμην"), (3, "1.3", None)]


class Digest(unittest.TestCase):
    def test_same_content_same_digest(self):
        with tempfile.TemporaryDirectory() as d:
            d = Path(d)
            make(d / "a.sqlite", ROWS)
            make(d / "b.sqlite", ROWS)
            # the rows written in another order, on pages of another size, the file not compacted,
            # the html compressed otherwise: the files differ, the content does not
            make(d / "c.sqlite", ROWS, page_size=8192, reverse=True, vacuum=False)
            make(d / "h1.sqlite", ROWS, html=b"<p>entry</p>" * 50, level=9)
            make(d / "h2.sqlite", ROWS, html=b"<p>entry</p>" * 50, level=1)
            self.assertEqual(versions.content_digest(d / "a.sqlite"), versions.content_digest(d / "b.sqlite"))
            self.assertNotEqual((d / "a.sqlite").read_bytes(), (d / "c.sqlite").read_bytes())
            self.assertEqual(versions.content_digest(d / "a.sqlite"), versions.content_digest(d / "c.sqlite"))
            self.assertNotEqual((d / "h1.sqlite").read_bytes(), (d / "h2.sqlite").read_bytes())
            self.assertEqual(versions.content_digest(d / "h1.sqlite"), versions.content_digest(d / "h2.sqlite"))

    def test_one_changed_cell(self):
        with tempfile.TemporaryDirectory() as d:
            d = Path(d)
            make(d / "a.sqlite", ROWS)
            make(d / "b.sqlite", ROWS[:2] + [(3, "1.3", "")])        # NULL is not the empty text
            make(d / "c.sqlite", ROWS[:1] + [(2, "1.2", "ἂν ποιησαίμην,")] + ROWS[2:])
            make(d / "e.sqlite", ROWS[:2])                            # a row fewer
            got = {versions.content_digest(d / f"{x}.sqlite") for x in "abce"}
            self.assertEqual(len(got), 4)
            tables = versions.table_digests(d / "a.sqlite"), versions.table_digests(d / "c.sqlite")
            self.assertEqual(tables[0]["meta"], tables[1]["meta"])
            self.assertNotEqual(tables[0]["lines"], tables[1]["lines"])

    def test_the_version_stays_with_the_content(self):
        with tempfile.TemporaryDirectory() as d:
            data = Path(d)
            make(data / "text.sqlite", ROWS)
            (data / "text.sqlite.version").write_text("0123456789abcdef\n", encoding="utf-8")  # the old hash of the file
            self.assertEqual(len(versions.seed(data)), 1)
            self.assertEqual(versions.seed(data), [])  # a record is never made twice
            old = versions.load(data)["text"]
            self.assertEqual(old["version"], "0123456789abcdef")
            # built again with the same content (another page size): the version stays
            (data / "text.sqlite").unlink()
            make(data / "text.sqlite", ROWS, page_size=8192)
            self.assertEqual(versions.stamp(data / "text.sqlite", data), ("0123456789abcdef", old["digest"]))
            # a build elsewhere reads the records and writes none
            other = data / "scratch"
            other.mkdir()
            make(other / "text.sqlite", ROWS)
            self.assertEqual(versions.stamp(other / "text.sqlite", data)[0], "0123456789abcdef")
            self.assertFalse((other / versions.RECORDS).exists())
            # the content changes: the new version is the digest's beginning, and it is recorded
            (data / "text.sqlite").unlink()
            make(data / "text.sqlite", ROWS + [(4, "1.4", "new")])
            version, digest = versions.stamp(data / "text.sqlite", data)
            self.assertEqual(version, digest[:16])
            self.assertNotEqual(version, "0123456789abcdef")
            self.assertEqual(versions.load(data)["text"], {"version": version, "digest": digest})
            self.assertEqual((data / "text.sqlite.version").read_text(encoding="utf-8").strip(), version)


if __name__ == "__main__":
    unittest.main()
