"""Lysias: the checking pass over the word analyses of the speeches without trees (12, 13, 19).

There every word has the lemma and form the analyser gives the word by itself (hude_merge.tokens).
Measured against the hand-made trees of other speeches that reading differs from the trees' in
about six words of a hundred, nearly always where the spelling allows several readings (a neuter
that is nominative or accusative, a form two verbs share). In the pass an agent sees each such
word in its sentence with the analyser's readings and chooses one (pipeline/PLAN-lysias.md,
"The words without trees"; the brief transcriptions/lysias/ANALYSES.md).

  jobs     the job files transcriptions/lysias/analyses/job-NN.tsv: the words to decide, by
           section, each with its readings; an existing file is never written again.
           Jobs 91 and 92 are the control: stretches of speeches 1 and 24, which HAVE hand-made
           trees, given to the agents as if they had none
  check    a job file after the agent: every word answered, the answers well formed, nothing
           but the answers changed
  measure  the control jobs against the trees: how many words differed before the pass and how
           many after; the evidence by which the pass is judged
  answers  the table the merge reads: (section, word number) -> (form, lemma, tag) from the
           finished job files of 12, 13, 19 (hude_merge.tokens applies it; tokens.tsv is never
           edited by hand)
"""
from __future__ import annotations

import re
import subprocess
from pathlib import Path

from . import greek

ROOT = Path(__file__).resolve().parent.parent.parent
PIPELINE = ROOT / "pipeline"
DIR = PIPELINE / "transcriptions" / "lysias" / "analyses"

NO_TREES = (12, 13, 19)
CONTROL = {91: 1, 92: 24}  # job number -> the speech with hand-made trees its stretch is taken from
JOB_SIZE = 150             # words to decide in a job (a section is never divided)
MOST = 8                   # readings shown for a word at most

# the commonest words: only their own lemma's readings are offered (the article's case, not
# whether καί might be a form of καίω)
STOP = set("ὁ καί δέ ἄν γάρ μέν τε οὐ ὡς ὅς εἰμί ἐγώ σύ αὐτός οὗτος ἐν εἰς ἐπί διά παρά ἤ μή ἀλλά γε δή οὖν ὅτι πᾶς "
           "οὐδέ μήτε οὔτε καίτοι οὕτως ἅπας ἐάν ἑαυτοῦ πρός περί ἐκ ἀπό κατά μετά ὑπό ὑπέρ τίς τις ἐκεῖνος οὐδείς "
           "μηδείς ἀντί ἡμεῖς ὦ εἰ ἐπειδή ὅτε ὥστε ἵνα πρό σύν νῦν ἔτι πολύς ἄλλος".split())

TAG = re.compile(r"[nvadlgcrpmiexu-][123-][sdp-][pirlatf-][ismonpdg-][ampe-][mfnc-][nvgda-][cs-]")
_ITEM = re.compile(r"^(\d+\.\d+[a-z]?):(\d+)\t([^\t]*)\t([^\t]*)\t→ ?(.*)$")
_READING = re.compile(r"^(\d+) (\S+) (\S{9}) ")

_POS = {"n": "noun", "v": "verb", "a": "adjective", "d": "adverb", "l": "article", "g": "particle", "c": "conjunction",
        "r": "preposition", "p": "pronoun", "m": "numeral", "i": "interjection", "e": "exclamation", "x": "other", "u": "punctuation"}
_NUMBER = {"s": "singular", "d": "dual", "p": "plural"}
_TENSE = {"p": "present", "i": "imperfect", "r": "perfect", "l": "pluperfect", "a": "aorist", "f": "future", "t": "future perfect"}
_MOOD = {"i": "indicative", "s": "subjunctive", "o": "optative", "m": "imperative", "n": "infinitive", "p": "participle",
         "d": "gerund", "g": "gerundive"}
_VOICE = {"a": "active", "m": "middle", "p": "passive", "e": "middle or passive"}
_GENDER = {"m": "masculine", "f": "feminine", "n": "neuter", "c": "common"}
_CASE = {"n": "nominative", "v": "vocative", "g": "genitive", "d": "dative", "a": "accusative"}
_DEGREE = {"c": "comparative", "s": "superlative"}


def describe(tag: str) -> str:
    """The nine letters of a tag in words: "verb, 3rd singular aorist indicative active"."""
    parts = [_POS.get(tag[0], "?")]
    participle = tag[4] == "p"
    verb = " ".join(x for x in ({"1": "1st", "2": "2nd", "3": "3rd"}.get(tag[1], ""), "" if participle else _NUMBER.get(tag[2], ""),
                                _TENSE.get(tag[3], ""), _MOOD.get(tag[4], ""), _VOICE.get(tag[5], "")) if x) if tag[0] == "v" else ""
    noun = " ".join(x for x in (_NUMBER.get(tag[2], "") if tag[0] != "v" or participle else "", _GENDER.get(tag[6], ""),
                                _CASE.get(tag[7], "")) if x)
    parts += [x for x in (verb, noun, _DEGREE.get(tag[8], "")) if x]
    return ", ".join(parts)


def _fixes() -> dict[str, str]:
    from .drama_fixes import LEMMA_FIXES as text_fixes
    from .import_perseus import LEMMA_FIXES

    return {**LEMMA_FIXES, **text_fixes.get("lysias", {})}


def signature(lemma: str, tag: str, fixes: dict[str, str] | None = None) -> tuple:
    """What two readings must share to be the same reading for a learner: the lemma (after the
    lemma fixes), person (of a verb), number, tense, mood, voice (middle and passive are one, as
    the trees do not agree on them), case. Not the gender (a genitive plural's), not the part of
    speech (pronoun or adjective, particle or adverb: the trees' conventions differ)."""
    from .odyssey import fix_lemma

    lemma = fix_lemma(lemma)
    lemma = (fixes if fixes is not None else _fixes()).get(lemma, lemma)
    voice = "m" if tag[5] in "mep" else tag[5]
    return (greek.lemma_key(lemma), tag[1] if tag[0] == "v" else "-", tag[2], tag[3], tag[4], voice, tag[7])


class Reader:
    """The analyser with the treebank frequencies, as the merge uses them."""

    def __init__(self, sources: Path, lexicon: Path):
        from .odyssey_merge import Analyser, Frequencies

        self.analyse = Analyser(lexicon)
        self.freq = Frequencies(sources / "treebanks")
        keys = {k for (k,) in self.analyse.db.execute("SELECT DISTINCT lemma_key FROM lexicon_entries")}
        self.known = lambda lemma: greek.lemma_key(lemma) in keys
        self.fixes = _fixes()

    def alone(self, forms: list[str]) -> list[tuple[str, str]]:
        """Each word's reading by the analyser alone, as hude_merge.tokens reads a speech without
        trees: the analyser's choice, a compound verb from its simple verb, the address after ὦ,
        the relative and the article before an enclitic. ("", "") where it has none."""
        from .hude_merge import compound_analysis, relatives_and_articles, vocatives
        from .odyssey import fix_lemma
        from .odyssey_merge import choose_analysis

        rows = []
        for form in forms:
            chosen = choose_analysis(form, self.analyse(form), "", "", self.freq, "")
            if chosen is not None:
                chosen = (fix_lemma(chosen[0]), chosen[1])
            else:
                chosen = compound_analysis(form, self.analyse, self.known,
                                           pick=lambda f, found: choose_analysis(f, found, freq=self.freq)) or ("", "")
            rows.append({"form": form, "lemma": chosen[0], "postag": chosen[1], "sentence": ""})
        vocatives(rows, self.analyse)
        relatives_and_articles(rows)
        return [(self.fixes.get(r["lemma"], r["lemma"]), r["postag"]) for r in rows]

    def readings(self, form: str, now: tuple[str, str]) -> list[tuple[str, str]]:
        """The readings to choose among: the present one first, then the analyser's other readings
        of exactly this spelling (accent and breathing), one for each signature, the commoner
        first; for the commonest words only readings of the same lemma. At most MOST."""
        from .odyssey_merge import _accent_key

        found = [a for a in self.analyse(form) if len(a) > 2 and TAG.fullmatch(a[2])]
        key = _accent_key(form)
        found = [a for a in found if _accent_key(a[0]) == key] or found
        mine = signature(*now, self.fixes) if now[1] else None
        # a tag with letters missing where another reading of the same lemma has them is no reading
        # of its own ("l--------" beside "l-s---na-"); of the commonest words only the readings
        # the treebanks know (the analyser's list holds a dative τὸ)
        whole = [(a[1], a[2]) for a in found] + ([now] if now[1] else [])
        found = [a for a in found if not any(l == a[1] and t != a[2] and all(x in ("-", y) for x, y in zip(a[2], t)) for l, t in whole)]
        if now[0] in STOP:
            found = [a for a in found if self.freq.analysis[(key, greek.nfc(a[1]), a[2])]]
        best: dict[tuple, tuple[int, str, str]] = {}
        for _form, lemma, tag, *_ in found:
            sig = signature(lemma, tag, self.fixes)
            if sig == mine or (now[0] in STOP and sig[0] != (mine[0] if mine else "")):
                continue
            n = self.freq.analysis[(key, greek.nfc(lemma), tag)] * 1000 + self.freq.lemma[greek.nfc(lemma)]
            if sig not in best or n > best[sig][0]:
                best[sig] = (n, self.fixes.get(lemma, lemma), tag)
        others = [(lemma, tag) for _n, lemma, tag in sorted(best.values(), key=lambda x: (-x[0], x[1], x[2]))]
        return ([now] if now[1] else []) + others[:MOST - 1]


def read_tokens(texts: Path) -> list[dict]:
    import csv

    with (texts / "lysias" / "tokens.tsv").open(encoding="utf-8") as f:
        return list(csv.DictReader(f, delimiter="\t", quoting=csv.QUOTE_NONE))


def _sections(texts: Path) -> dict[str, str]:
    out = {}
    for raw in (texts / "lysias" / "grc.txt").read_text(encoding="utf-8").splitlines():
        n, tab, text = raw.partition("\t")
        if tab and re.fullmatch(r"\d+\.\d+[a-z]?", n):
            out[n] = text
    return out


def _speech(line: str) -> int:
    return int(line.split(".")[0])


def stretch(tokens: list[dict], speech: int, reader: Reader, control: bool) -> list[dict]:
    """A speech's words with the present reading of each and the readings to choose among (none
    where there is nothing to choose). For the control the present reading is the analyser's
    alone, whatever the trees say; a word settled by hand is not asked about."""
    from .drama_fixes import HAND_ANALYSES

    hands = HAND_ANALYSES.get("lysias", {})
    rows = [t for t in tokens if _speech(t["line"]) == speech]
    now = reader.alone([t["form"] for t in rows]) if control else [(t["lemma"], t["postag"]) for t in rows]
    out = []
    for t, reading in zip(rows, now):
        by_hand = not control and (f"{t['line']} {t['form']}" in hands or f"{re.sub(r'[a-z]$', '', t['line'])} {t['form']}" in hands)
        choices = [] if by_hand or not reading[1] else reader.readings(t["form"], reading)
        out.append({"line": t["line"], "ord": int(t["ord"]), "form": t["form"], "now": reading,
                    "readings": choices if len(choices) > 1 else []})
    return out


def _context(words: list[dict], i: int) -> str:
    a = " ".join(w["form"] for w in words[max(0, i - 4):i])
    b = " ".join(w["form"] for w in words[i + 1:i + 5])
    return f"{'… ' if i > 4 else ''}{a} [{words[i]['form']}] {b}{' …' if i + 5 < len(words) else ''}".replace("  ", " ").strip()


def job_text(number: int, speech: int, words: list[dict], sections: dict[str, str]) -> str:
    lines_ = list(dict.fromkeys(w["line"] for w in words))
    n = sum(1 for w in words if w["readings"])
    out = [f"# Lysias, word analyses · job {number:02d} · speech {speech}, sections {lines_[0]}–{lines_[-1]} · {n} words to decide",
           "# Write your answer after the arrow of each line: transcriptions/lysias/ANALYSES.md"]
    for line in lines_:
        here = [w for w in words if w["line"] == line]
        if not any(w["readings"] for w in here):
            continue
        out += ["", f"== {line}", sections.get(line, " ".join(w["form"] for w in here)), ""]
        for i, w in enumerate(here):
            if w["readings"]:
                shown = " ‖ ".join(f"{k} {lemma} {tag} {describe(tag)}" for k, (lemma, tag) in enumerate(w["readings"], 1))
                out.append(f"{line}:{w['ord']}\t{_context(here, i)}\t{shown}\t→ ")
    return "\n".join(out) + "\n"


def make_jobs(texts: Path, sources: Path, lexicon: Path, directory: Path = DIR) -> list[str]:
    """Write the job files that do not exist yet; returns a line for each job."""
    reader = Reader(sources, lexicon)
    tokens = read_tokens(texts)
    sections = _sections(texts)
    directory.mkdir(parents=True, exist_ok=True)
    report = []

    def write(number: int, speech: int, words: list[dict]) -> None:
        path = directory / f"job-{number:02d}.tsv"
        lines_ = list(dict.fromkeys(w["line"] for w in words))
        n = sum(1 for w in words if w["readings"])
        state = "exists, left as it is" if path.exists() else "written"
        if not path.exists():
            path.write_text(job_text(number, speech, words, sections), encoding="utf-8")
        report.append(f"job-{number:02d}: speech {speech}, {lines_[0]}–{lines_[-1]}, {len(words)} words, {n} to decide ({state})")

    number = 0
    for speech in NO_TREES:
        batch: list[dict] = []
        words = stretch(tokens, speech, reader, control=False)
        for line in dict.fromkeys(w["line"] for w in words):
            batch += [w for w in words if w["line"] == line]
            if sum(1 for w in batch if w["readings"]) >= JOB_SIZE:
                number += 1
                write(number, speech, batch)
                batch = []
        if batch:
            number += 1
            write(number, speech, batch)
    for number, speech in CONTROL.items():
        batch = []
        words = stretch(tokens, speech, reader, control=True)
        for line in dict.fromkeys(w["line"] for w in words):
            batch += [w for w in words if w["line"] == line]
            if sum(1 for w in batch if w["readings"]) >= JOB_SIZE:
                break
        write(number, speech, batch)
    return report


def read_job(path: Path) -> list[dict]:
    """The items of a job file: line, ord, form, readings [(lemma, tag)], answer (the text after
    the arrow), and what the answer chooses: `chosen` (lemma, tag), None while unanswered or
    undecided ("?")."""
    items = []
    for raw in path.read_text(encoding="utf-8").splitlines():
        m = _ITEM.match(raw)
        if not m:
            continue
        readings = []
        for part in m.group(4).split(" ‖ "):
            r = _READING.match(part + " ")
            if r:
                readings.append((r.group(2), r.group(3)))
        form = re.search(r"\[([^\]]+)\]", m.group(3))
        answer = m.group(5).strip()
        chosen = None
        if re.fullmatch(r"\d+", answer) and 1 <= int(answer) <= len(readings):
            chosen = readings[int(answer) - 1]
        else:
            o = re.match(r"^other:\s*(\S+)\s+(\S{9})(?=\s|$)", answer)
            if o and TAG.fullmatch(o.group(2)):
                chosen = (o.group(1), o.group(2))
        items.append({"line": m.group(1), "ord": int(m.group(2)), "form": form.group(1) if form else "", "readings": readings,
                      "answer": answer, "chosen": chosen})
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
        key, a = f"{it['line']}:{it['ord']} [{it['form']}]", it["answer"]
        if not a:
            problems.append(f"{key}: not answered")
        elif re.fullmatch(r"\d+", a):
            if not 1 <= int(a) <= len(it["readings"]):
                problems.append(f"{key}: answer {a}, but the readings are 1–{len(it['readings'])}")
        elif a.startswith("other:"):
            o = re.match(r"^other:\s*(\S+)\s+(\S+)\s*(.*)$", a)
            if not o or not TAG.fullmatch(o.group(2)):
                problems.append(f"{key}: `other:` wants a lemma, a nine-letter tag and a reason (other: λέγω v3saia--- the aorist of λέγω)")
            elif not re.search(r"[Ͱ-Ͽἀ-῿]", o.group(1)):
                problems.append(f"{key}: the lemma of `other:` is not Greek")
            elif len(o.group(3).strip(" —-")) < 4:
                problems.append(f"{key}: `other:` without a reason")
        elif a.startswith("?"):
            if len(a.strip("? —-")) < 4:
                problems.append(f"{key}: `?` without a reason")
        else:
            problems.append(f"{key}: answer not understood: {a[:40]}")
    return problems


def answers(directory: Path = DIR) -> dict[tuple[str, int], tuple[str, str, str]]:
    """The table for the merge: (section, word number) -> (form, lemma, tag), from the job files
    of the speeches without trees in which every word is answered and the checker finds nothing
    (a half-done file is not used; the control jobs never)."""
    table: dict[tuple[str, int], tuple[str, str, str]] = {}
    for path in sorted(directory.glob("job-*.tsv")):
        number = int(path.stem.split("-")[1])
        if number in CONTROL:
            continue
        items = read_job(path)
        if any(not it["answer"] for it in items) or any("not understood" in p or "wants" in p or "readings are" in p for p in check_job(path)):
            continue
        for it in items:
            if it["chosen"]:
                table[(it["line"], it["ord"])] = (it["form"], *it["chosen"])
    return table


def measure(texts: Path, sources: Path, lexicon: Path, directory: Path = DIR) -> list[str]:
    """The control jobs against the hand-made trees. For every word of the control stretches:
    does the reading agree with the trees' (by `signature`) before the pass (the analyser alone)
    and after it (the agent's choice where it made one)?"""
    reader = Reader(sources, lexicon)
    tokens = read_tokens(texts)
    out = []
    total = [0, 0, 0, 0, 0, 0]  # words, shown, differing before, after, corrected, spoiled
    for number, speech in CONTROL.items():
        path = directory / f"job-{number:02d}.tsv"
        if not path.exists():
            out.append(f"job-{number:02d}: no file")
            continue
        items = {(it["line"], it["ord"]): it for it in read_job(path)}
        open_ = sum(1 for it in items.values() if not it["answer"])
        lines_ = {k[0] for k in items}
        last = max(lines_, key=lambda n: [int(x) for x in re.sub(r"[a-z]$", "", n).split(".")] + [n])
        rows = [t for t in tokens if _speech(t["line"]) == speech]
        # the stretch ends with the job's last section
        end = max(i for i, t in enumerate(rows) if t["line"] == last)
        rows = rows[:end + 1]
        alone = reader.alone([t["form"] for t in rows])
        n = shown = before = after = corrected = spoiled = 0
        notes = []
        for t, reading in zip(rows, alone):
            if not t["sentence"] or not TAG.fullmatch(t["postag"]) or not reading[1]:
                continue
            n += 1
            tree = signature(t["lemma"], t["postag"], reader.fixes)
            was = signature(*reading, reader.fixes) == tree
            it = items.get((t["line"], int(t["ord"])))
            chosen = it["chosen"] if it and it["chosen"] else reading
            shown += bool(it)
            is_ = signature(*chosen, reader.fixes) == tree
            before += not was
            after += not is_
            corrected += (not was) and is_
            spoiled += was and not is_
            if was and not is_:
                notes.append(f"    spoiled {t['line']}:{t['ord']} {t['form']}: trees {t['lemma']} {t['postag']}, chosen {chosen[0]} {chosen[1]}")
            elif not was and not is_ and it:
                on_offer = any(signature(*r, reader.fixes) == tree for r in it["readings"])
                notes.append(f"    still differs {t['line']}:{t['ord']} {t['form']}: trees {t['lemma']} {t['postag']}, chosen {chosen[0]} {chosen[1]}"
                             + ("" if on_offer else " (the trees' reading was not on offer)"))
        out.append(f"job-{number:02d} (speech {speech}, to {last}): {n} words, {shown} shown to the agent"
                   + (f", {open_} NOT YET ANSWERED" if open_ else "")
                   + f"; differing from the trees before {before} ({100 * before / max(n, 1):.1f} %), after {after} "
                     f"({100 * after / max(n, 1):.1f} %); corrected {corrected}, spoiled {spoiled}")
        out += notes
        for k, v in enumerate((n, shown, before, after, corrected, spoiled)):
            total[k] += v
    n, shown, before, after, corrected, spoiled = total
    if n:
        out.append(f"control in all: {n} words, {shown} shown; differing from the trees before {before} ({100 * before / n:.1f} %), "
                   f"after {after} ({100 * after / n:.1f} %); corrected {corrected}, spoiled {spoiled}")
    return out
