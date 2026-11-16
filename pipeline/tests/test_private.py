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
from anagnosis_pipeline.private import (PRIVATE_SLUGS, check_private, exclude_lines, find_private, gitignore_lines,
                                        held_back, pack_names, pre_push, private_slugs, release_of, setup)

ROOT = Path(__file__).resolve().parent.parent.parent
TODAY = dt.date(2026, 11, 16)


# made-up slugs: the public repository names no private text (private/slugs.txt holds the list)
HELD = ("heldback", "later")


class Slugs(unittest.TestCase):
    def test_read_from_the_private_folder(self):
        with tempfile.TemporaryDirectory() as t:
            root = Path(t)
            self.assertEqual(private_slugs(root), ())  # a public checkout: no private folder
            (root / "private" / "texts" / "later").mkdir(parents=True)
            (root / "private" / "slugs.txt").write_text("# the private texts\nheldback\n\nlater  # also a folder\n")
            self.assertEqual(private_slugs(root), ("heldback", "later"))

    def test_plain_slugs_and_no_public_text_among_them(self):
        from anagnosis_pipeline.sophocles import PLAYS as SOPHOCLES

        for s in PRIVATE_SLUGS:
            self.assertRegex(s, r"^[a-z]+$")
        self.assertNotIn("electra", PRIVATE_SLUGS)  # Sophocles' Electra is public
        self.assertFalse(set(SOPHOCLES) & set(PRIVATE_SLUGS))
        for d in (ROOT / "texts").iterdir():
            if d.name in PRIVATE_SLUGS:
                self.assertTrue(d.is_symlink(), f"texts/{d.name} must be a link into private/")


class Paths(unittest.TestCase):
    def test_find_private(self):
        paths = ["texts/heldback/grc.txt", "texts/heldback", "texts/electra/grc.txt", "texts/heldbackX/grc.txt",
                 "pipeline/transcriptions/drama/heldback/batch-01.md", "pipeline/transcriptions/drama/clouds/batch-01.md",
                 "data/heldback.sqlite", "data/heldback.catalog.json", "data/ion.sqlite.version", "data/ionic.sqlite",
                 "app/packs/later/build.gradle.kts", "app/packs/gorgias/build.gradle.kts", "private/README.md",
                 "privateer.txt", "data/catalog-author.json", "data/catalog.json", "pipeline/PLAN-euripides.md",
                 "app/author-packs.txt", "app/settings.gradle.kts"]
        self.assertEqual(find_private(paths, ("heldback", "ion", "later")), sorted([
            "texts/heldback/grc.txt", "texts/heldback", "pipeline/transcriptions/drama/heldback/batch-01.md",
            "data/heldback.sqlite", "data/heldback.catalog.json", "data/ion.sqlite.version",
            "app/packs/later/build.gradle.kts", "private/README.md", "data/catalog-author.json",
            "app/author-packs.txt"]))

    def test_gitignore_and_exclude_lines(self):
        self.assertEqual(gitignore_lines(), ["/private/", "/data/catalog-author.json", "/app/author-packs.txt"])
        self.assertEqual(exclude_lines(["heldback"]), ["/texts/heldback", "/pipeline/transcriptions/drama/heldback",
                                                       "/data/heldback.*", "/app/packs/heldback"])

    def test_real_gitignore_and_pack_lists(self):
        have = {l.strip() for l in (ROOT / ".gitignore").read_text(encoding="utf-8").splitlines()}
        self.assertEqual([l for l in gitignore_lines() if l not in have], [])
        # the tracked .gitignore names no private text: their lines are in .git/info/exclude
        self.assertEqual([l for l in exclude_lines() if l in have], [])
        for rel in private.PACK_LISTS:
            names = pack_names((ROOT / rel).read_text(encoding="utf-8"))
            self.assertIn("antigone", names)
            self.assertFalse(set(names) & set(PRIVATE_SLUGS), rel)

    def test_pack_names(self):
        text = 'for (slug in listOf("antigone", "ajax")) {\n    include(":packs:$slug")\n}\ninclude(":packs:heldback")\n' \
               'assetPacks += listOf("gorgias").map { ":packs:$it" }'
        self.assertEqual(sorted(pack_names(text)), ["ajax", "antigone", "gorgias", "heldback"])


class Release(unittest.TestCase):
    def test_release_of(self):
        self.assertEqual(release_of("antigone", None), (None, None))
        self.assertEqual(release_of("antigone", "2027-03-01"), (dt.date(2027, 3, 1), None))
        day, complaint = release_of("heldback", None, HELD)
        self.assertEqual(day, dt.date(2028, 1, 1))
        self.assertIn("without", complaint)
        day, complaint = release_of("heldback", "2027-06-01", HELD)  # never before Murray is free
        self.assertEqual(day, dt.date(2028, 1, 1))
        self.assertIn("before", complaint)
        self.assertEqual(release_of("heldback", "2028-01-01", HELD), (dt.date(2028, 1, 1), None))
        day, complaint = release_of("antigone", "soon")
        self.assertEqual(day, dt.date.max)
        self.assertIn("not a date", complaint)

    def test_held_back(self):
        self.assertTrue(held_back("heldback", "2028-01-01", TODAY, HELD))
        self.assertFalse(held_back("heldback", "2028-01-01", dt.date(2028, 1, 1), HELD))
        self.assertTrue(held_back("heldback", None, TODAY, HELD))
        self.assertFalse(held_back("antigone", None, TODAY))
        self.assertTrue(held_back("antigone", "2026-12-24", TODAY))
        self.assertFalse(held_back("antigone", "2026-11-16", TODAY))

    def test_write_catalog(self):
        with tempfile.TemporaryDirectory() as t:
            out = Path(t)
            (out / "antigone.sqlite.version").write_text("abc\n")
            cat = [{"slug": "antigone", "title": "Ἀντιγόνη"},
                   {"slug": "heldback", "title": "Τέξτ", "release": "2028-01-01"},
                   {"slug": "theogony", "title": "Θεογονία", "release": "2026-12-01"}]
            write_catalog(cat, out, today=TODAY)
            public = json.loads((out / "catalog.json").read_text())
            author = json.loads((out / "catalog-author.json").read_text())
            self.assertEqual([e["slug"] for e in public], ["antigone"])
            self.assertEqual(public[0]["version"], "abc")
            self.assertEqual([e["slug"] for e in author], ["antigone", "heldback", "theogony"])
            self.assertTrue((out / "heldback.catalog.json").exists())
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
    (root / "private").mkdir()
    (root / "private" / "slugs.txt").write_text("\n".join(HELD) + "\n")
    (root / "data").mkdir()
    (root / "data" / "catalog.json").write_text('[{"slug": "antigone"}]')
    (root / "pipeline" / "transcriptions" / "drama").mkdir(parents=True)
    return root


class Setup(unittest.TestCase):
    def test_links_and_moves(self):
        with tempfile.TemporaryDirectory() as t:
            root = _fake_root(t)
            # an empty folder at a public path (as pipeline/transcriptions/drama/heldback was) and a
            # folder with an untracked file
            (root / "pipeline" / "transcriptions" / "drama" / "heldback").mkdir()
            (root / "texts" / "heldback").mkdir()
            (root / "texts" / "heldback" / "notes.md").write_text("x")
            setup("heldback", root, git=False)
            link = root / "texts" / "heldback"
            self.assertTrue(link.is_symlink())
            self.assertEqual(os.readlink(link), "../private/texts/heldback")
            self.assertEqual(os.readlink(root / "pipeline" / "transcriptions" / "drama" / "heldback"),
                             "../../../private/transcriptions/drama/heldback")
            self.assertEqual((root / "private" / "texts" / "heldback" / "notes.md").read_text(), "x")
            self.assertTrue((root / "private" / "README.md").exists())
            said = setup("heldback", root, git=False)  # a second run changes nothing
            self.assertTrue(all("already there" in s for s in said if "->" in s))
            with self.assertRaises(SystemExit):
                setup("antigone", root, git=False)

    def test_pack(self):
        # the asset pack of the author's own builds: its build file in private/, a link from app/packs
        with tempfile.TemporaryDirectory() as t:
            root = _fake_root(t)
            setup("heldback", root, git=False, pack=True)
            link = root / "app" / "packs" / "heldback"
            self.assertTrue(link.is_symlink())
            self.assertEqual(os.readlink(link), "../../private/app/packs/heldback")
            gradle = (link / "build.gradle.kts").read_text()
            self.assertIn('packName.set("heldback")', gradle)
            self.assertIn('include("heldback.sqlite", "heldback.sqlite.version")', gradle)
            (link / "build.gradle.kts").write_text(gradle + "// edited\n")
            setup("heldback", root, git=False, pack=True)  # a second run keeps the file
            self.assertTrue((link / "build.gradle.kts").read_text().endswith("// edited\n"))
            errors, _notes = check_private(root, tracked=["texts/antigone/grc.txt"], today=TODAY)
            self.assertEqual(errors, [])


class Check(unittest.TestCase):
    def test_clean(self):
        with tempfile.TemporaryDirectory() as t:
            root = _fake_root(t)
            setup("heldback", root, git=False)
            errors, notes = check_private(root, tracked=["texts/antigone/grc.txt"], today=TODAY)
            self.assertEqual(errors, [])
            self.assertEqual(notes, ["heldback: held back until 2028-01-01 (in the author's catalogue only)"])

    def test_errors(self):
        with tempfile.TemporaryDirectory() as t:
            root = _fake_root(t)
            setup("heldback", root, git=False)
            (root / "texts" / "heldback" / "grc.txt").write_text("# title: Τέξτ\n")
            (root / "texts" / "heldback" / "about.md").write_text("# google_play: yes\n# release: 2027-01-01\n\nText.\n")
            (root / "app" / "settings.gradle.kts").write_text('for (slug in listOf("antigone", "heldback")) {}\n')
            (root / "data" / "catalog.json").write_text('[{"slug": "antigone"}, {"slug": "heldback"}]')
            (root / ".gitignore").write_text("/private/\n")
            (root / "texts" / "later").mkdir()  # a private slug as a plain folder
            errors, notes = check_private(root, tracked=["texts/antigone/grc.txt", "texts/heldback/grc.txt",
                                                         "private/texts/heldback/grc.txt"], today=TODAY)
            text = "\n".join(errors)
            for part in ("texts/heldback/grc.txt: a private text's file is tracked", "private/texts/heldback/grc.txt",
                         "settings.gradle.kts: lists the private text heldback", ".gitignore lacks",
                         "google_play: yes", "before 2028-01-01", "data/catalog.json names heldback",
                         "texts/later: a private text outside private/"):
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
            self.assertEqual(pre_push([f"refs/heads/main {clean} refs/heads/main {zero}"], repo, HELD), [])
            # a private file added and removed again: still in the pushed history
            (repo / "texts" / "heldback").mkdir()
            (repo / "texts" / "heldback" / "grc.txt").write_text("m")
            _git(repo, "add", "-A")
            _git(repo, "commit", "-q", "-m", "oops")
            _git(repo, "rm", "-q", "-r", "texts/heldback")
            _git(repo, "commit", "-q", "-m", "removed")
            tip = _git(repo, "rev-parse", "HEAD")
            problems = pre_push([f"refs/heads/main {tip} refs/heads/main {clean}"], repo, HELD)
            self.assertEqual(len(problems), 1)
            self.assertIn("texts/heldback/grc.txt", problems[0])
            problems = pre_push([f"refs/heads/main {tip} refs/heads/main {zero}"], repo, HELD)
            self.assertIn("texts/heldback/grc.txt", problems[0])
            # deleting a remote branch carries nothing; a bad sha refuses
            self.assertEqual(pre_push([f"(delete) {zero} refs/heads/old {clean}"], repo, HELD), [])
            self.assertTrue(pre_push([f"refs/heads/main {'1' * 40} refs/heads/main {zero}"], repo, HELD))


if __name__ == "__main__":
    unittest.main()
