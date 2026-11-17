"""Authors' names that dropped out of Perseus's files of Jebb's commentaries.

In Perseus's files of the commentary on the Antigone and the Ajax an author's abbreviation is
missing before many titles: Jebb prints "Then in Plat. Phaedr. 272 B", the file has
"Then in  <title>Phaedr.</title> 272 B" (often a double space where the word stood). Which
places lack a word cannot be told from the file: "Aesch. Ag. 1148 …: Th. 683" is right without a
second "Aesch.". So every place where it may have happened is read on Jebb's page:

* `places(slug, sources)`: the commentary imported with a mark (MARK) at each such place: a
  citation of an author other than Sophocles and Homer that begins with its title and has no
  author's name just before it, and a bare title after a gap;
* `make_jobs`: job files `pipeline/transcriptions/sophocles/<slug>/authors-NN.tsv`, each place
  with its note, the words around it and the pages of the scan on which the note stands;
* `check_job`: the agents' checker;
* `restored(slug)`: (wrong, right) pairs for the answered places, applied after the play's
  COMMENTARY_FIXES (sophocles.write_commentary).

The brief for the agents is pipeline/transcriptions/sophocles/AUTHORS.md.
"""
from __future__ import annotations

import json
import re
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DIR = ROOT / "transcriptions" / "sophocles"
MARK = "⟦A⟧"
JOB_SIZE = 40
# words with a capital that stand before a citation and are no author
NOT_AUTHORS = {"Cp", "See", "So", "In", "Thus", "Also", "But", "And", "Then", "Cf", "Compare", "As", "For", "Here",
               "The", "Similarly", "Yet", "Or", "On", "Thus", "Add", "Contrast", "Hence", "Not", "With", "From", "It"}
# titles Jebb cites without an author: Sophocles' own plays and Homer
OWN_TITLES = {"O. T.", "O. C.", "Ant.", "Tr.", "Ph.", "El.", "Ai.", "Aj.", "Il.", "Od.", "Phil.", "Trach."}

_BIBL = re.compile(r'<bibl n="([A-Z][A-Za-z]*)\.? [^"]*">\s*(?=<title>)')
_TITLE = re.compile(r"(?<=[^\s>])( {2,})(?=<title>([^<]*)</title>)")


def _before(xml: str, at: int) -> str:
    """The text just before a place, tags and entities taken out."""
    s = re.sub(r"<[^>]*>", " ", xml[max(0, at - 200):at])
    return re.sub(r"&[a-z]+;", " ", s)


def mark_places(xml: str) -> str:
    """The file's text with MARK set where an author's name may have dropped out."""
    start = xml.find('type="commentary"')
    head, body = (xml[:start], xml[start:]) if start >= 0 else ("", xml)

    def bibl(m: re.Match) -> str:
        if m.group(1) in ("Soph", "Hom"):
            return m.group(0)
        last = re.findall(r"([A-Z][A-Za-zé]+)(?:'s)?[.,]?\s*\(?\s*$", _before(body, m.start()))
        if last and last[0] not in NOT_AUTHORS:
            return m.group(0)  # an author's name stands before the citation
        return f" {MARK} " + m.group(0)

    def title(m: re.Match) -> str:
        if m.group(2).strip() in OWN_TITLES:
            return m.group(0)
        return f" {MARK} "

    return head + _TITLE.sub(title, _BIBL.sub(bibl, body))


def marked_commentary(slug: str, sources: Path) -> str:
    """The play's commentary as write_commentary makes it (import, range headings, the play's
    fix table), with the marks standing in it."""
    from . import sophocles
    from .commentary import import_jebb_commentary

    play = sophocles.PLAYS[slug]
    src = sources / sophocles.sources_for(play)["commentary"]
    with tempfile.TemporaryDirectory() as d:
        marked = Path(d) / src.name
        marked.write_text(mark_places(src.read_text(encoding="utf-8")), encoding="utf-8")
        out = Path(d) / "commentary.md"
        # the same options as write_commentary gives the importer (the play's switches, if any)
        options = getattr(sophocles, "import_options", lambda _play: {})(play)
        import_jebb_commentary(marked, out, {"title": "x"}, **options)
        text = sophocles.range_headings(out.read_text(encoding="utf-8"))
    for wrong, right in sophocles.COMMENTARY_FIXES.get(slug, []):
        if wrong in text:
            text = text.replace(wrong, right)
        else:
            # a fix whose words a mark now divides: apply it across the mark, which stays
            pattern = r"\s*".join(re.escape(w) for w in wrong.split())
            pattern = pattern.replace(r"\s*", rf"\s*(?:{re.escape(MARK)}\s*)?")
            text = re.sub(pattern, lambda _m: right, text)
    return re.sub(r" +", " ", text)


def places(slug: str, sources: Path) -> list[dict]:
    """Each marked place: its note's heading, the words before and after it."""
    out = []
    note = ""
    for line in marked_commentary(slug, sources).splitlines():
        if line.startswith("## "):
            note = line[3:].strip()
            continue
        for m in re.finditer(re.escape(MARK), line):
            before = line[max(0, m.start() - 110):m.start()].replace(MARK, "").strip()
            after = line[m.end():m.end() + 60].replace(MARK, "").strip()
            out.append({"note": note, "before": re.sub(r" +", " ", before), "after": re.sub(r" +", " ", after)})
    return out


def pages_of(slug: str, note: str, build: Path) -> str:
    """The leaves of the scan on which a note stands: the text page that holds its first verse
    and the page facing it (the commentary runs under both); a long note may run on."""
    index = json.loads((build / "drama-pages" / slug / "pages.json").read_text(encoding="utf-8"))
    first = int(re.match(r"\d+", note).group()) if re.match(r"\d+", note) else 0
    leaf = None
    for p in index:
        a, b = re.match(r"\d+", str(p["first"])), re.match(r"\d+", str(p["last"]))
        if a and b and int(a.group()) <= first <= int(b.group()):
            leaf = p["leaf"]
            break
    if leaf is None:
        later = [p["leaf"] for p in index if re.match(r"\d+", str(p["first"])) and int(re.match(r"\d+", str(p["first"])).group()) > first]
        leaf = (min(later) - 2) if later else index[-1]["leaf"]
    return f"{leaf}, {leaf + 1}"


def job_text(name: str, slug: str, items: list[dict], build: Path) -> str:
    lines = [f"# Authors' names before titles · job {name} · {slug} · {len(items)} places",
             "# Write after the arrow what the page prints at ⟦A⟧: the author's name or abbreviation as printed, or - for nothing: transcriptions/sophocles/AUTHORS.md",
             ""]
    for i, it in enumerate(items, 1):
        lines.append(f"== {i} · note {it['note']} · leaves {pages_of(slug, it['note'], build)}")
        lines.append(f"{it['before']} {MARK} {it['after']}")
        lines.append("→ ")
        lines.append("")
    return "\n".join(lines)


def make_jobs(slug: str, sources: Path, build: Path) -> list[str]:
    folder = DIR / slug
    if list(folder.glob("authors-*.tsv")):
        return [f"{slug}: job files exist already; none written"]
    items = places(slug, sources)
    names = []
    for n, at in enumerate(range(0, len(items), JOB_SIZE), 1):
        name = f"authors-{n:02d}"
        (folder / f"{name}.tsv").write_text(job_text(name, slug, items[at:at + JOB_SIZE], build), encoding="utf-8")
        names.append(name)
    return [f"{slug}: {len(items)} places in {len(names)} job files"]


def read_job(path: Path) -> list[dict]:
    items = []
    lines = path.read_text(encoding="utf-8").splitlines()
    for i, line in enumerate(lines):
        m = re.match(r"== (\d+) · note (.+?) · leaves (.+)$", line)
        if m and i + 2 < len(lines):
            before, _, after = lines[i + 1].partition(f" {MARK} ")
            answer = lines[i + 2][1:].strip() if lines[i + 2].startswith("→") else None
            items.append({"n": int(m.group(1)), "note": m.group(2), "before": before, "after": after, "answer": answer})
    return items


def check_job(path: Path) -> list[str]:
    """Remarks on an answered job file: a place without an answer, an answer that is no name."""
    problems = []
    for it in read_job(path):
        a = it["answer"]
        where = f"{path.name} {it['n']} (note {it['note']})"
        if a is None:
            problems.append(f"{where}: the arrow line is missing")
        elif not a:
            problems.append(f"{where}: not answered")
        elif a != "-" and not a.startswith("?") and not re.fullmatch(r"[A-Za-zÀ-ÿ.' ]{2,30}", a):
            problems.append(f"{where}: not understood: {a!r} (an author's name as printed, - for nothing, or ? and a reason)")
    return problems


def restored(slug: str, sources: Path) -> list[tuple[str, str]]:
    """(wrong, right) for each place where the page has an author's name: the shortest run of
    words round the place that stands once in the commentary, without the name and with it."""
    folder = DIR / slug
    answers = {}
    for path in sorted(folder.glob("authors-*.tsv")):
        if check_job(path):
            continue
        for it in read_job(path):
            answers[(it["note"], it["before"][-40:], it["after"][:25])] = it["answer"]
    if not answers:
        return []
    text = marked_commentary(slug, sources)
    plain = text.replace(f" {MARK} ", " ").replace(MARK, "")
    plain = re.sub(r" +", " ", plain)
    pairs = []
    for it in places(slug, sources):
        answer = answers.get((it["note"], it["before"][-40:], it["after"][:25]))
        if not answer or answer == "-" or answer.startswith("?"):
            continue
        before, after = it["before"].split(" "), it["after"].split(" ")
        for k in range(2, 12):
            left, right = " ".join(before[-k:]), " ".join(after[:max(2, k // 2)])
            wrong = f"{left} {right}"
            if plain.count(wrong) == 1:
                pairs.append((wrong, f"{left} {answer} {right}"))
                break
        else:
            print(f"{slug}: note {it['note']}: no words that stand once round the place ({it['before'][-30:]} | {it['after'][:20]})")
    return pairs
