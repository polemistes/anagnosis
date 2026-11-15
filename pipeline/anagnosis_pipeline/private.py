"""Texts kept off the public repository until their release date (pipeline/PLAN-euripides.md).

Gilbert Murray's Oxford text of Euripides (Murray died 1957) is protected in Norway and the UK
until the end of 2027. The Euripides plays are made from it now and offered from 1 January 2028;
until then nothing of Murray's text or apparatus may reach the public repository, a release
bundle of the app, or the shop. Their files live in `private/` at the repository root (its own
git repository, ignored by the public one); the pipeline finds them at its usual paths through
symbolic links:

    texts/<slug>                          -> ../private/texts/<slug>
    pipeline/transcriptions/drama/<slug>  -> ../../../private/transcriptions/drama/<slug>

`PRIVATE_SLUGS` is the one list of these texts; the public .gitignore, the pre-push hook
(pipeline/tools/pre-push), `check` and `catalog` all read it from here. This module uses the
standard library only, so that the hook can load it with any Python 3.

    python -m anagnosis_pipeline private-setup <slug>   the folders and links for a slug
"""
from __future__ import annotations

import datetime as _dt
import os
import re
import shutil
import subprocess
from pathlib import Path
from typing import Iterable

ROOT = Path(__file__).resolve().parent.parent.parent

# the nineteen plays of Euripides in Murray's Oxford text, in the order of the ranking in
# pipeline/research/euripides-plays.md (texts/electra is Sophocles': Euripides' is euripideselectra)
PRIVATE_SLUGS: tuple[str, ...] = (
    "alcestis", "medea", "heraclidae", "helen", "bacchae", "hecuba", "troades", "cyclops", "heracles",
    "iphigeniataurica", "orestes", "phoenissae", "iphigeniaaulidensis", "ion", "hippolytus", "andromache",
    "euripideselectra", "rhesus", "supplices",
)

# the earliest day any of them may be offered: Murray's text is free in Norway and the UK from then
PRIVATE_RELEASE = "2028-01-01"

PRIVATE = "private"                        # the private folder, at the repository root
AUTHOR_CATALOG = "data/catalog-author.json"  # every text, held-back ones too: for the author's own builds

# where the public repository's paths point, per slug: (public path, path inside private/)
LINKS = (("texts/{slug}", "texts/{slug}"),
         ("pipeline/transcriptions/drama/{slug}", "transcriptions/drama/{slug}"))

# the public files that list the reader's asset packs
PACK_LISTS = ("app/settings.gradle.kts", "app/androidApp/build.gradle.kts")


def public_patterns(slug: str) -> list[str]:
    """The public repository's paths that belong to a private slug (as .gitignore lines)."""
    return [f"/texts/{slug}", f"/pipeline/transcriptions/drama/{slug}", f"/data/{slug}.*", f"/app/packs/{slug}"]


def gitignore_lines(slugs: Iterable[str] = PRIVATE_SLUGS) -> list[str]:
    """Every line the public .gitignore must hold for the private texts."""
    out = [f"/{PRIVATE}/", f"/{AUTHOR_CATALOG}"]
    for slug in slugs:
        out += public_patterns(slug)
    return out


def private_slug_of(path: str, slugs: Iterable[str] = PRIVATE_SLUGS) -> str | None:
    """The private slug a repository-relative path belongs to ("private" for the private folder
    itself, "catalog" for the author's catalogue), or None for a public path."""
    p = path.strip().lstrip("/")
    if p == PRIVATE or p.startswith(PRIVATE + "/"):
        return PRIVATE
    if p == AUTHOR_CATALOG:
        return "catalog"
    for slug in slugs:
        for prefix in (f"texts/{slug}", f"pipeline/transcriptions/drama/{slug}", f"app/packs/{slug}"):
            if p == prefix or p.startswith(prefix + "/"):
                return slug
        if p.startswith(f"data/{slug}."):
            return slug
    return None


def find_private(paths: Iterable[str], slugs: Iterable[str] = PRIVATE_SLUGS) -> list[str]:
    """The paths among `paths` that lie under a private slug's paths or under private/."""
    slugs = tuple(slugs)
    return sorted({p for p in paths if p and private_slug_of(p, slugs)})


def _git(root: Path, *args: str) -> str:
    r = subprocess.run(["git", *args], cwd=root, capture_output=True, text=True)
    if r.returncode != 0:
        raise RuntimeError(f"git {' '.join(args)}: {r.stderr.strip()}")
    return r.stdout


def tracked_files(root: Path = ROOT) -> list[str]:
    """The files git tracks in the repository at `root` (git ls-files; reading only)."""
    return [p for p in _git(root, "ls-files", "-z").split("\0") if p]


def pack_names(text: str) -> list[str]:
    """The pack names a Gradle file lists: the strings of its listOf(...) and every :packs:<name>."""
    names: list[str] = []
    for m in re.finditer(r"listOf\(([^)]*)\)", text):
        names += re.findall(r'"([A-Za-z0-9_]+)"', m.group(1))
    names += re.findall(r":packs:([A-Za-z0-9_]+)", text)
    return names


def about_headers(work_dir: Path) -> dict[str, str]:
    """The `# key: value` headers at the top of a text's about.md."""
    out: dict[str, str] = {}
    about = work_dir / "about.md"
    if not about.exists():
        return out
    for raw in about.read_text(encoding="utf-8").splitlines():
        m = re.match(r"^# ([a-z_]+):\s*(.*)$", raw)
        if not m:
            if raw.strip():
                break
            continue
        out[m.group(1)] = m.group(2).strip()
    return out


def parse_date(value: str) -> _dt.date | None:
    try:
        return _dt.date.fromisoformat(value.strip()) if re.fullmatch(r"\d{4}-\d{2}-\d{2}", value.strip()) else None
    except ValueError:
        return None


def release_of(slug: str, release: str | None) -> tuple[_dt.date | None, str | None]:
    """The day a text may be offered, and a complaint where the about.md's `release` is wrong.
    None = no release date (offered now). A private slug is never offered before PRIVATE_RELEASE,
    whatever its about.md says; a release value that is not a date holds the text back for good."""
    floor = parse_date(PRIVATE_RELEASE) if slug in PRIVATE_SLUGS else None
    if release is None or not release.strip():
        if floor:
            return floor, f"{slug}: a private text without `# release:` in about.md (held back until {PRIVATE_RELEASE})"
        return None, None
    day = parse_date(release)
    if day is None:
        return _dt.date.max, f"{slug}: `# release: {release}` is not a date YYYY-MM-DD (held back)"
    if floor and day < floor:
        return floor, f"{slug}: `# release: {release}` is before {PRIVATE_RELEASE}, the earliest day for a private text (held back until then)"
    return day, None


def held_back(slug: str, release: str | None, today: _dt.date | None = None) -> bool:
    """True while a text's release date lies in the future: `catalog` leaves it out of the public
    catalogue."""
    day, _ = release_of(slug, release)
    return day is not None and day > (today or _dt.date.today())


def check_private(root: Path = ROOT, tracked: list[str] | None = None, today: _dt.date | None = None) -> tuple[list[str], list[str]]:
    """(errors, notes) for `check`: a private slug's file that git tracks in the public repository,
    a private slug in the public pack lists, marked for sale or in the public catalogue while held
    back, a .gitignore line missing; and which texts are held back and until when."""
    import json

    errors: list[str] = []
    notes: list[str] = []
    today = today or _dt.date.today()
    if tracked is None:
        try:
            tracked = tracked_files(root)
        except (RuntimeError, OSError) as e:
            errors.append(f"cannot list the files git tracks ({e}): the private texts were not checked")
            tracked = []
    for p in find_private(tracked):
        errors.append(f"{p}: a private text's file is tracked in the public repository (git rm --cached it)")
    for rel in PACK_LISTS:
        f = root / rel
        if f.exists():
            for name in sorted(set(pack_names(f.read_text(encoding="utf-8"))) & set(PRIVATE_SLUGS)):
                errors.append(f"{rel}: lists the private text {name} as an asset pack")
    gi = root / ".gitignore"
    have = {l.strip() for l in gi.read_text(encoding="utf-8").splitlines()} if gi.exists() else set()
    missing = [l for l in gitignore_lines() if l not in have]
    if missing:
        errors.append(f".gitignore lacks {len(missing)} line(s) for the private texts: {', '.join(missing[:6])}"
                      + (" …" if len(missing) > 6 else ""))
    texts = root / "texts"
    public_catalog: set[str] = set()
    cat = root / "data" / "catalog.json"
    if cat.exists():
        try:
            public_catalog = {e.get("slug", "") for e in json.loads(cat.read_text(encoding="utf-8"))}
        except ValueError:
            errors.append("data/catalog.json is not valid JSON")
    if texts.is_dir():
        for d in sorted(p for p in texts.iterdir() if p.is_dir()):
            h = about_headers(d)
            slug = d.name
            if slug in PRIVATE_SLUGS and not (d.is_symlink() and (root / PRIVATE).resolve() in d.resolve().parents):
                errors.append(f"texts/{slug}: a private text outside private/ (run private-setup {slug})")
            if slug in PRIVATE_SLUGS and h.get("google_play", "").lower() == "yes":
                errors.append(f"texts/{slug}/about.md: a private text marked `google_play: yes`")
            if not h and slug not in PRIVATE_SLUGS:
                continue
            day, complaint = release_of(slug, h.get("release"))
            if complaint and (d / "grc.txt").exists():
                errors.append(complaint)
            if day is not None and day > today:
                notes.append(f"{slug}: held back until {day.isoformat() if day != _dt.date.max else 'a valid release date'}"
                             " (in the author's catalogue only)")
                if slug in public_catalog:
                    errors.append(f"data/catalog.json names {slug}, which is held back: run `catalog`")
    for slug in sorted(public_catalog & set(PRIVATE_SLUGS)):
        if not (texts / slug).exists():
            errors.append(f"data/catalog.json names the private text {slug}")
    return errors, notes


def setup(slug: str, root: Path = ROOT, git: bool = True) -> list[str]:
    """The private folders of a slug and the links to them from the public paths; private/ gets
    its own git repository the first time. An empty folder at a public path is replaced by the
    link; a folder with files that git does not track is moved into private/ first; a tracked
    file there stops the set-up."""
    if slug not in PRIVATE_SLUGS:
        raise SystemExit(f"{slug}: not a private text (anagnosis_pipeline/private.py, PRIVATE_SLUGS)")
    said: list[str] = []
    priv = root / PRIVATE
    priv.mkdir(exist_ok=True)
    if git and not (priv / ".git").exists():
        subprocess.run(["git", "init", "-q"], cwd=priv, check=True)
        said.append(f"{priv}: a git repository of its own (never push it to the public one)")
    readme = priv / "README.md"
    if not readme.exists():
        readme.write_text(
            "# Private texts (never public before their release date)\n\n"
            "Files of texts that may not be published yet (Murray's Euripides: not before 2028-01-01),\n"
            "kept out of the public repository: see pipeline/PLAN-euripides.md and\n"
            "pipeline/anagnosis_pipeline/private.py in the public repository. This folder has its own\n"
            "git history; it has no remote. The public paths texts/<slug> and\n"
            "pipeline/transcriptions/drama/<slug> are symbolic links into it.\n", encoding="utf-8")
    for public_rel, private_rel in LINKS:
        target = priv / private_rel.format(slug=slug)
        target.mkdir(parents=True, exist_ok=True)
        link = root / public_rel.format(slug=slug)
        rel = os.path.relpath(target, link.parent)
        if link.is_symlink():
            if os.readlink(link) == rel:
                said.append(f"{link.relative_to(root)} -> {rel} (already there)")
                continue
            raise SystemExit(f"{link}: a link to {os.readlink(link)}, not to {rel}: look at it by hand")
        if link.exists():
            if not link.is_dir():
                raise SystemExit(f"{link}: a file, not a folder: look at it by hand")
            if git:
                try:
                    tracked = _git(root, "ls-files", "--", str(link.relative_to(root))).split()
                except RuntimeError:
                    tracked = []
                if tracked:
                    raise SystemExit(f"{link}: git tracks {len(tracked)} file(s) there; they must leave the public "
                                     "repository first (by the main session)")
            inside = list(link.iterdir())
            if inside:
                if any(target.iterdir()):
                    raise SystemExit(f"{link} and {target} both hold files: merge them by hand")
                for p in inside:
                    shutil.move(str(p), str(target / p.name))
                said.append(f"{len(inside)} file(s) moved from {link.relative_to(root)} into {target.relative_to(root)}")
            link.rmdir()
        link.parent.mkdir(parents=True, exist_ok=True)
        link.symlink_to(rel)
        said.append(f"{link.relative_to(root)} -> {rel}")
    return said


ZERO = "0" * 40


def pre_push(lines: Iterable[str], root: Path = ROOT) -> list[str]:
    """The pre-push hook's test: the paths under a private slug's paths or under private/ that
    the push would carry, in any commit pushed or in the tree of a pushed tip. `lines` are the
    hook's standard input (<local ref> <local sha> <remote ref> <remote sha>). Any git error
    counts as a problem: the hook refuses rather than lets a private file through."""
    problems: list[str] = []
    for raw in lines:
        parts = raw.split()
        if len(parts) != 4:
            continue
        local_ref, local_sha, remote_ref, remote_sha = parts
        if set(local_sha) == {"0"}:
            continue  # deleting a remote branch carries no files
        try:
            paths = set(_git(root, "ls-tree", "-r", "--name-only", "-z", local_sha).split("\0"))
            if set(remote_sha) != {"0"} and subprocess.run(["git", "cat-file", "-e", remote_sha], cwd=root,
                                                          capture_output=True).returncode == 0:
                rng = [f"{remote_sha}..{local_sha}"]
            else:
                rng = [local_sha, "--not", "--remotes"]
            paths |= set(_git(root, "log", "--no-renames", "--format=", "--name-only", "-z", *rng).replace("\n", "\0").split("\0"))
        except RuntimeError as e:
            problems.append(f"{local_ref}: {e}")
            continue
        for p in find_private(paths):
            problems.append(f"{local_ref} -> {remote_ref}: {p}")
    return problems
