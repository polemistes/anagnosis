"""The checking pass over the kinds of difference between our words and the trees' words.

Where the syntax trees of a text were made on another text than the one printed, each word of
ours that the trees' text reads otherwise is a "reading" of the record (syntax_text.py), and the
record says how the two differ (`difference`): elision, nu, spelling, form, word. The reader
marks a sentence as differing only for the last two. The value is set by rule
(syntax_text.differences), and the rule is wrong in about one case of six (measured on the
Theogony, whose 62 readings were set by hand). In the pass an agent sees each reading in its
sentence, with both words and their analyses and the rule's value, and confirms or corrects the
value (the brief: transcriptions/syntax-text/DIFFERENCES.md; pipeline/PLAN-syntax-text.md).

  jobs     the job files transcriptions/syntax-text/<slug>-NN.tsv: the readings of a text in
           its order, about sixty to a file; an existing file is never written again.
           control-01.tsv and control-02.tsv are the control: the Theogony's 62 readings, whose
           values are known, shown with the rule's values as if they were not
  check    a job file after the agent: every reading answered with one of the five values (or
           "?" and a reason), nothing but the answers changed
  measure  the control files against the Theogony's record: how many values the rule had right
           and how many the agents have; the evidence by which the pass is judged
  answers  the table the record step reads: (line, word number) -> (our word, the trees' word,
           value), from the finished, committed job files of a text (syntax_text.record_from_files
           applies it where both words are still the ones the answer was given for)
"""
from __future__ import annotations

import csv
import re
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
PIPELINE = ROOT / "pipeline"
DIR = PIPELINE / "transcriptions" / "syntax-text"

VALUES = ("elision", "nu", "spelling", "form", "word")
JOB_SIZE = 60        # readings in a job
CONTROL = "theogony"  # the text whose values are known: its readings are the control
_ITEM = re.compile(r"^([^\t:]+):(\d+)\t([^\t]*)\t([^\t]*)\t([^\t]*)\trule: (\w+)\t→ ?(.*)$")


def _read_tsv(path: Path) -> list[dict]:
    with path.open(encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f, delimiter="\t", quoting=csv.QUOTE_NONE))


def readings(texts: Path, slug: str, by_rule: bool = False) -> list[dict]:
    """The readings of a text in its order, each with its token, its place among the tokens and
    its value. `by_rule`: the value the rule alone gives (for the control: the values set by
    hand are not shown)."""
    from .syntax_text import differences, read_record

    tokens = _read_tsv(texts / slug / "tokens.tsv")
    place = {(t["line"], t["ord"]): i for i, t in enumerate(tokens)}
    rows = [r for r in read_record(texts / slug / "syntax-text.tsv") if r["kind"] == "reading"]
    if by_rule:
        bare = [dict(r, ord=int(r["ord"]), difference="") for r in rows]
        differences(tokens, bare)
        rows = [dict(r, rule=b["difference"]) for r, b in zip(rows, bare)]
    else:
        rows = [dict(r, rule=r["difference"]) for r in rows]
    out = []
    for r in rows:
        i = place.get((r["line"], r["ord"]))
        if i is None:
            continue
        out.append(dict(r, at=i, token=tokens[i]))
    out.sort(key=lambda r: r["at"])
    for r in out:
        a = " ".join(t["form"] for t in tokens[max(0, r["at"] - 10):r["at"]])
        b = " ".join(t["form"] for t in tokens[r["at"] + 1:r["at"] + 9])
        r["context"] = f"… {a} «{r['form']}» {b} …"
    return out


def job_text(name: str, title: str, items: list[dict]) -> str:
    from .hude_analyses import describe

    out = [f"# The trees' text, kinds of difference · job {name} · {title} · {len(items)} readings",
           "# Write your answer after the arrow of each line: transcriptions/syntax-text/DIFFERENCES.md"]
    for r in items:
        t = r["token"]
        ours = f"{t['lemma']} {t['postag']} {describe(t['postag'])}"
        theirs = f"{r['tree_lemma']} {r['tree_postag']} {describe(r['tree_postag'])}"
        out += ["", f"== {r['line']}", r["context"], f"   ours:  {r['form']}  ({ours})", f"   trees: {r['tree_form']}  ({theirs})",
                f"{r['line']}:{r['ord']}\t{r['form']}\t{r['tree_form']}\t{t['lemma']} {t['postag']} | {r['tree_lemma']} {r['tree_postag']}\trule: {r['rule']}\t→ "]
    return "\n".join(out) + "\n"


def make_jobs(texts: Path, slugs: list[str], directory: Path = DIR) -> list[str]:
    """Write the job files of the texts named (and of the control); returns what was done."""
    directory.mkdir(parents=True, exist_ok=True)
    done = []
    for slug in slugs:
        control = slug == CONTROL
        items = readings(texts, slug, by_rule=control)
        prefix = "control" if control else slug
        if list(directory.glob(f"{prefix}-*.tsv")):
            done.append(f"{prefix}: job files exist already; none written")
            continue
        size = (len(items) + 1) // 2 if control else JOB_SIZE
        # a file is never nearly empty: the last short piece joins the one before
        pieces = [items[i:i + size] for i in range(0, len(items), size)]
        if len(pieces) > 1 and len(pieces[-1]) < size // 3:
            pieces[-2] += pieces.pop()
        for n, piece in enumerate(pieces, 1):
            name = f"{prefix}-{n:02d}"
            title = f"{piece[0]['line']}–{piece[-1]['line']}" if control else f"{slug}, {piece[0]['line']}–{piece[-1]['line']}"
            (directory / f"{name}.tsv").write_text(job_text(name, title, piece), encoding="utf-8")
        done.append(f"{prefix}: {len(items)} readings in {len(pieces)} job files")
    return done


def read_job(path: Path) -> list[dict]:
    """The items of a job file: line, ord, form, tree_form, rule, answer (the text after the
    arrow) and `value` (the kind it names; None while unanswered or undecided)."""
    items = []
    for raw in path.read_text(encoding="utf-8").splitlines():
        m = _ITEM.match(raw)
        if not m:
            continue
        answer = m.group(7).strip()
        first = answer.split()[0].rstrip(".,:;") if answer else ""
        items.append({"line": m.group(1), "ord": int(m.group(2)), "form": m.group(3), "tree_form": m.group(4), "rule": m.group(6),
                      "answer": answer, "value": first if first in VALUES else None})
    return items


def _frame(content: str) -> list[str]:
    """A job file without its answers: what the agent may not change."""
    return [re.sub(r"\t→.*$", "\t→", raw).rstrip() for raw in content.splitlines()]


def check_job(path: Path) -> list[str]:
    problems = []
    items = read_job(path)
    if not items:
        return [f"{path.name}: no items"]
    rel = path.resolve().relative_to(ROOT).as_posix() if ROOT in path.resolve().parents else None
    if rel:
        got = subprocess.run(["git", "-C", str(ROOT), "show", f"HEAD:{rel}"], capture_output=True, text=True)
        if got.returncode == 0:
            was, now = _frame(got.stdout), _frame(path.read_text(encoding="utf-8"))
            if was != now:
                diff = next((f"line {i + 1}" for i, (a, b) in enumerate(zip(was, now)) if a != b), "the number of lines")
                problems.append(f"{path.name}: something other than the answers is changed ({diff}): restore it from git")
    for it in items:
        key, a = f"{it['line']}:{it['ord']} {it['form']} / {it['tree_form']}", it["answer"]
        if not a:
            problems.append(f"{key}: not answered")
        elif a.startswith("?"):
            if len(a.strip("? —-")) < 4:
                problems.append(f"{key}: `?` without a reason")
        elif it["value"] is None:
            problems.append(f"{key}: answer not understood: {a[:40]} (one of: {', '.join(VALUES)}; or ? and a reason)")
        elif it["value"] != it["rule"] and len(a.split(None, 1)) < 2:
            problems.append(f"{key}: the rule's value is changed ({it['rule']} to {it['value']}) without a reason after it")
    return problems


def _uncommitted(path: Path) -> bool:
    """Is this file of the repository changed since its last commit (or not committed at all)?
    False for a file outside the repository (the tests')."""
    if ROOT not in path.resolve().parents:
        return False
    got = subprocess.run(["git", "-C", str(ROOT), "status", "--porcelain", "--", str(path.resolve())], capture_output=True, text=True)
    return got.returncode == 0 and bool(got.stdout.strip())


def answers(slug: str, directory: Path = DIR) -> dict[tuple[str, int], tuple[str, str, str]]:
    """The table for the record step: (line, word number) -> (our word, the trees' word, value),
    from the job files of the text in which every reading is answered and the checker finds
    nothing ill formed (a half-done file is not used, nor one changed since its last commit;
    the control files never: the Theogony's values are set in drama_fixes.TREE_READINGS)."""
    table: dict[tuple[str, int], tuple[str, str, str]] = {}
    if slug == CONTROL or not directory.is_dir():
        return table
    for path in sorted(directory.glob(f"{slug}-*.tsv")):
        if _uncommitted(path):
            continue  # an agent may still be at work on it: only what is checked and committed counts
        items = read_job(path)
        if any(not it["answer"] for it in items) or any("not understood" in p for p in check_job(path)):
            continue
        for it in items:
            if it["value"]:
                table[(it["line"], it["ord"])] = (it["form"], it["tree_form"], it["value"])
    return table


def measure(texts: Path, directory: Path = DIR) -> list[str]:
    """The control files against the Theogony's record."""
    from .syntax_text import read_record

    truth = {(r["line"], int(r["ord"])): r["difference"] for r in read_record(texts / CONTROL / "syntax-text.tsv") if r["kind"] == "reading"}
    real = ("form", "word")
    out, n, rule_ok, agent_ok, rule_band, agent_band, answered = [], 0, 0, 0, 0, 0, 0
    for path in sorted(directory.glob("control-*.tsv")):
        for it in read_job(path):
            want = truth.get((it["line"], it["ord"]))
            if want is None:
                out.append(f"{path.name} {it['line']}:{it['ord']}: not a reading of the record any more")
                continue
            n += 1
            rule_ok += it["rule"] == want
            rule_band += (it["rule"] in real) == (want in real)
            if it["value"] is None:
                out.append(f"{path.name} {it['line']}:{it['ord']} {it['form']} / {it['tree_form']}: {'not answered' if not it['answer'] else it['answer'][:60]} (by hand: {want})")
                continue
            answered += 1
            agent_ok += it["value"] == want
            agent_band += (it["value"] in real) == (want in real)
            if it["value"] != want:
                out.append(f"{path.name} {it['line']}:{it['ord']} {it['form']} / {it['tree_form']}: the agent {it['value']}, by hand {want}"
                           f" (the rule: {it['rule']}){'' if (it['value'] in real) == (want in real) else '  <- changes whether the sentence is marked'}")
    out.append(f"{n} readings of the control; the rule alone: {rule_ok} values right, {rule_band} right as to whether the sentence is marked "
               f"(form or word against the rest)")
    out.append(f"answered: {answered}; the agents: {agent_ok} values right, {agent_band} right as to whether the sentence is marked")
    return out
