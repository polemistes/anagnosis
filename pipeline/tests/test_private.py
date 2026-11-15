"""Private texts and release dates (private.py; build.write_catalog): pipeline/PLAN-euripides.md.

Nothing here touches the real repository's state: the set-up, the catalogue and the hook are tried
in temporary folders (the hook in a throw-away git repository); the real .gitignore and pack lists
are only read."""
import datetime as dt
import json
import os
import subprocess
import tempfile
import unittest
from pathlib import Path

from anagnosis_pipeline import private
from anagnosis_pipeline.build import write_catalog
from anagnosis_pipeline.private import (PRIVATE_SLUGS, check_private, find_private, gitignore_lines, held_back,
                                        pack_names, pre_push, release_of, setup)

ROOT = Path(__file__).resolve().parent.parent.parent
TODAY = dt.date(2026, 11, 16)


class Slugs(unittest.TestCase):
    def test_nineteen_plain_slugs(self):
        self.assertEqual(len(PRIVATE_SLUGS), 19)
        self.assertEqual(len(set(PRIVATE_SLUGS)), 19)
        for s in PRIVATE_SLUGS:
            self.assertRegex(s, r"^[a-z]+$")
        self.assertNotIn("electra", PRIVATE_SLUGS)  # Sophocles' Electra is public
        self.assertIn("euripideselectra", PRIVATE_SLUGS)

    def test_no_public_text_has_a_private_slug(self):
        from anagnosis_pipeline.sophocles import PLAYS as SOPHOCLES

        self.assertFalse(set(SOPHOCLES) & set(PRIVATE_SLUGS))
        for d in (ROOT / "texts").iterdir():
            if d.name in PRIVATE_SLUGS:
                self.assertTrue(d.is_symlink(), f"texts/{d.name} must be a link into private/")


class Paths(unittest.TestCase):
    def test_find_private(self):
        paths = ["texts/medea/grc.txt", "texts/medea", "texts/electra/grc.txt", "texts/medeaX/grc.txt",
                 "pipeline/transcriptions/drama/medea/batch-01.md", "pipeline/transcriptions/drama/clouds/batch-01.md",
                 "data/medea.sqlite", "data/medea.catalog.json", "data/ion.sqlite.version", "data/ionic.sqlite",
                 "app/packs/helen/build.gradle.kts", "app/packs/gorgias/build.gradle.kts", "private/README.md",
                 "privateer.txt", "data/catalog-author.json", "data/catalog.json", "pipeline/PLAN-euripides.md"]
        self.assertEqual(find_private(paths), sorted([
            "texts/medea/grc.txt", "texts/medea", "pipeline/transcriptions/drama/medea/batch-01.md",
            "data/medea.sqlite", "data/medea.catalog.json", "data/ion.sqlite.version",
            "app/packs/helen/build.gradle.kts", "private/README.md", "data/catalog-author.json"]))

    def test_gitignore_lines(self):
        lines = gitignore_lines(["medea"])
        self.assertEqual(lines, ["/private/", "/data/catalog-author.json", "/texts/medea",
                                 "/pipeline/transcriptions/drama/medea", "/data/medea.*", "/app/packs/medea"])

    def test_real_gitignore_and_pack_lists(self):
        have = {l.strip() for l in (ROOT / ".gitignore").read_text(encoding="utf-8").splitlines()}
        self.assertEqual([l for l in gitignore_lines() if l not in have], [])
        for rel in private.PACK_LISTS:
            names = pack_names((ROOT / rel).read_text(encoding="utf-8"))
            self.assertIn("antigone", names)
            self.assertFalse(set(names) & set(PRIVATE_SLUGS), rel)

    def test_pack_names(self):
        text = 'for (slug in listOf("antigone", "ajax")) {\n    include(":packs:$slug")\n}\ninclude(":packs:medea")\n' \
               'assetPacks += listOf("gorgias").map { ":packs:$it" }'
        self.assertEqual(sorted(pack_names(text)), ["ajax", "antigone", "gorgias", "medea"])


class Release(unittest.TestCase):
    def test_release_of(self):
        self.assertEqual(release_of("antigone", None), (None, None))
        self.assertEqual(release_of("antigone", "2027-03-01"), (dt.date(2027, 3, 1), None))
        day, complaint = release_of("medea", None)
        self.assertEqual(day, dt.date(2028, 1, 1))
        self.assertIn("without", complaint)
        day, complaint = release_of("medea", "2027-06-01")  # never before Murray is free
        self.assertEqual(day, dt.date(2028, 1, 1))
        self.assertIn("before", complaint)
        self.assertEqual(release_of("medea", "2028-01-01"), (dt.date(2028, 1, 1), None))
        day, complaint = release_of("antigone", "soon")
        self.assertEqual(day, dt.date.max)
        self.assertIn("not a date", complaint)

    def test_held_back(self):
        self.assertTrue(held_back("medea", "2028-01-01", TODAY))
        self.assertFalse(held_back("medea", "2028-01-01", dt.date(2028, 1, 1)))
        self.assertTrue(held_back("medea", None, TODAY))
        self.assertFalse(held_back("antigone", None, TODAY))
        self.assertTrue(held_back("antigone", "2026-12-24", TODAY))
        self.assertFalse(held_back("antigone", "2026-11-16", TODAY))

    def test_write_catalog(self):
        with tempfile.TemporaryDirectory() as t:
            out = Path(t)
            (out / "antigone.sqlite.version").write_text("abc\n")
            cat = [{"slug": "antigone", "title": "Ἀντιγόνη"},
                   {"slug": "medea", "title": "Μήδεια", "release": "2028-01-01"},
                   {"slug": "theogony", "title": "Θεογονία", "release": "2026-12-01"}]
            write_catalog(cat, out, today=TODAY)
            public = json.loads((out / "catalog.json").read_text())
            author = json.loads((out / "catalog-author.json").read_text())
            self.assertEqual([e["slug"] for e in public], ["antigone"])
            self.assertEqual(public[0]["version"], "abc")
            self.assertEqual([e["slug"] for e in author], ["antigone", "medea", "theogony"])
            self.assertTrue((out / "medea.catalog.json").exists())
            write_catalog([dict(e) for e in cat], out, today=dt.date(2028, 1, 1))
            self.assertEqual(len(json.loads((out / "catalog.json").read_text())), 3)


def _fake_root(t: str) -> Path:
    root = Path(t)
    (root / "texts" / "antigone").mkdir(parents=True)
    (root / "texts" / "antigone" / "grc.txt").write_text("# title: Ἀντιγόνη\n")
    (root / "app" / "androidApp").mkdir(parents=True)
    (root / "app" / "settings.gradle.kts").write_text('for (slug in listOf("antigone")) {\n    include(":packs:$slug")\n}\n')
    (root / "app" / "androidApp" / "build.gradle.kts").write_text('assetPacks += listOf("antigone").map { ":packs:$it" }\n')
    (root / ".gitignore").write_text("\n".join(gitignore_lines()) + "\n")
    (root / "data").mkdir()
    (root / "data" / "catalog.json").write_text('[{"slug": "antigone"}]')
    (root / "pipeline" / "transcriptions" / "drama").mkdir(parents=True)
    return root


class Setup(unittest.TestCase):
    def test_links_and_moves(self):
        with tempfile.TemporaryDirectory() as t:
            root = _fake_root(t)
            # an empty folder at a public path (as pipeline/transcriptions/drama/medea was) and a
            # folder with an untracked file
            (root / "pipeline" / "transcriptions" / "drama" / "medea").mkdir()
            (root / "texts" / "medea").mkdir()
            (root / "texts" / "medea" / "notes.md").write_text("x")
            setup("medea", root, git=False)
            link = root / "texts" / "medea"
            self.assertTrue(link.is_symlink())
            self.assertEqual(os.readlink(link), "../private/texts/medea")
            self.assertEqual(os.readlink(root / "pipeline" / "transcriptions" / "drama" / "medea"),
                             "../../../private/transcriptions/drama/medea")
            self.assertEqual((root / "private" / "texts" / "medea" / "notes.md").read_text(), "x")
            self.assertTrue((root / "private" / "README.md").exists())
            said = setup("medea", root, git=False)  # a second run changes nothing
            self.assertTrue(all("already there" in s for s in said if "->" in s))
            with self.assertRaises(SystemExit):
                setup("antigone", root, git=False)


class Check(unittest.TestCase):
    def test_clean(self):
        with tempfile.TemporaryDirectory() as t:
            root = _fake_root(t)
            setup("medea", root, git=False)
            errors, notes = check_private(root, tracked=["texts/antigone/grc.txt"], today=TODAY)
            self.assertEqual(errors, [])
            self.assertEqual(notes, ["medea: held back until 2028-01-01 (in the author's catalogue only)"])

    def test_errors(self):
        with tempfile.TemporaryDirectory() as t:
            root = _fake_root(t)
            setup("medea", root, git=False)
            (root / "texts" / "medea" / "grc.txt").write_text("# title: Μήδεια\n")
            (root / "texts" / "medea" / "about.md").write_text("# google_play: yes\n# release: 2027-01-01\n\nText.\n")
            (root / "app" / "settings.gradle.kts").write_text('for (slug in listOf("antigone", "medea")) {}\n')
            (root / "data" / "catalog.json").write_text('[{"slug": "antigone"}, {"slug": "medea"}]')
            (root / ".gitignore").write_text("/private/\n")
            (root / "texts" / "helen").mkdir()  # a private slug as a plain folder
            errors, notes = check_private(root, tracked=["texts/antigone/grc.txt", "texts/medea/grc.txt",
                                                         "private/texts/medea/grc.txt"], today=TODAY)
            text = "\n".join(errors)
            for part in ("texts/medea/grc.txt: a private text's file is tracked", "private/texts/medea/grc.txt",
                         "settings.gradle.kts: lists the private text medea", ".gitignore lacks",
                         "google_play: yes", "before 2028-01-01", "data/catalog.json names medea",
                         "texts/helen: a private text outside private/"):
                self.assertIn(part, text)


def _git(cwd: Path, *args: str) -> str:
    return subprocess.run(["git", "-c", "user.name=t", "-c", "user.email=t@example.invalid", *args], cwd=cwd,
                          capture_output=True, text=True, check=True).stdout.strip()


class Hook(unittest.TestCase):
    def test_pre_push(self):
        with tempfile.TemporaryDirectory() as t:
            repo = Path(t)
            _git(repo, "init", "-q")
            (repo / "texts" / "antigone").mkdir(parents=True)
            (repo / "texts" / "antigone" / "grc.txt").write_text("a")
            _git(repo, "add", "-A")
            _git(repo, "commit", "-q", "-m", "public")
            clean = _git(repo, "rev-parse", "HEAD")
            zero = "0" * 40
            self.assertEqual(pre_push([f"refs/heads/main {clean} refs/heads/main {zero}"], repo), [])
            # a private file added and removed again: still in the pushed history
            (repo / "texts" / "medea").mkdir()
            (repo / "texts" / "medea" / "grc.txt").write_text("m")
            _git(repo, "add", "-A")
            _git(repo, "commit", "-q", "-m", "oops")
            _git(repo, "rm", "-q", "-r", "texts/medea")
            _git(repo, "commit", "-q", "-m", "removed")
            tip = _git(repo, "rev-parse", "HEAD")
            problems = pre_push([f"refs/heads/main {tip} refs/heads/main {clean}"], repo)
            self.assertEqual(len(problems), 1)
            self.assertIn("texts/medea/grc.txt", problems[0])
            problems = pre_push([f"refs/heads/main {tip} refs/heads/main {zero}"], repo)
            self.assertIn("texts/medea/grc.txt", problems[0])
            # deleting a remote branch carries nothing; a bad sha refuses
            self.assertEqual(pre_push([f"(delete) {zero} refs/heads/old {clean}"], repo), [])
            self.assertTrue(pre_push([f"refs/heads/main {'1' * 40} refs/heads/main {zero}"], repo))


if __name__ == "__main__":
    unittest.main()
