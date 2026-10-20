"""Listening samples of the reading voice, for checking it by ear.

    speech-samples prepare   pipeline/build/speech-samples/input.tsv: the opening lines of every
                             built text, each word with its place and length-marked form (the same
                             choice as the app's VowelLength)
    (then)   cd app && ./gradlew :shared:testAndroidHostTest --tests '*SpeechSampleDump*'
             which writes pipeline/build/speech-samples/<text>.txt: the eSpeak phonemes of each
             line in the text's pronunciation (and Attic, Homeric, Koine for the Odyssey's first lines)
    speech-samples render    one WAV per text from those files, with the speech data of
                             build-speech-data, into pipeline/build/speech-samples/
"""
from __future__ import annotations

import sqlite3
import subprocess
import sys
import unicodedata
import zlib
from pathlib import Path

from . import greek

SAMPLES = {  # text: number of opening lines (prose: lines of the edition)
    "odyssey": 10, "antigone": 10, "ajax": 6, "symposium": 6, "newtestament": 6,
}


def _analyses(lex: sqlite3.Connection, form: str):
    key = greek.strip_diacritics(form.rstrip("ʼ’"))
    row = lex.execute("SELECT analyses FROM forms WHERE form_key=?", (key,)).fetchone()
    if not row:
        return []
    out = []
    for line in zlib.decompress(row[0]).decode("utf-8").split("\n"):
        f = line.split("\t")
        if len(f) >= 4:
            out.append((f[0], f[1].lower(), f[2], f[4] if len(f) > 4 and f[4] else None))
    return out


def _letters(s: str) -> str:
    return "".join(c for c in unicodedata.normalize("NFD", s) if not unicodedata.combining(c)).lower().replace("ς", "σ")


def _choose(form: str, lemma_key: str, postag: str, analyses) -> str | None:
    """As the app's VowelLength.choose: the parse decides, else the lemma, when they agree.
    A marked form of other letters than the token's counts as none."""
    def pattern(a):
        m = a[3]
        if not m or _letters(m) != _letters(form.rstrip("ʼ’")):
            return ""
        return m

    def decide(cands):
        if not cands:
            return None
        pats = {pattern(a) for a in cands}
        return pats.pop() if len(pats) == 1 else None

    r = decide([a for a in analyses if a[1] == lemma_key and a[2] == postag])
    if r is not None:
        return r or None
    r = decide([a for a in analyses if a[1] == lemma_key])
    return r or None


def prepare(root: Path) -> None:
    data = root / "data"
    out = root / "pipeline" / "build" / "speech-samples"
    out.mkdir(parents=True, exist_ok=True)
    lex = sqlite3.connect(data / "lexicon.sqlite")
    rows = []
    for slug, n in SAMPLES.items():
        path = data / f"{slug}.sqlite"
        if not path.exists():
            continue
        db = sqlite3.connect(path)
        lines = db.execute("SELECT id, text FROM lines ORDER BY ord LIMIT ?", (n,)).fetchall()
        prose = (db.execute("SELECT value FROM meta WHERE key='layout'").fetchone() or [""])[0] == "prose"
        pron = (db.execute("SELECT value FROM meta WHERE key='pronunciation'").fetchone() or [None])[0]
        for line_id, text in lines:
            words = []
            for tid, start, end, form, lemma_key, postag in db.execute(
                    "SELECT id, start, end, form, lemma_key, postag FROM tokens WHERE line_id=? ORDER BY ord", (line_id,)):
                words.append([tid, start, end, form, _choose(form, lemma_key, postag, _analyses(lex, form)) or ""])
            rows.append({"slug": slug, "prose": prose, "pronunciation": pron, "line": line_id, "text": text, "words": words})
    # slug, prose (0/1), pronunciation, line id, text, words as id|start|end|form|marked separated by spaces
    with (out / "input.tsv").open("w", encoding="utf-8") as f:
        for r in rows:
            words = " ".join("|".join(str(x) for x in w) for w in r["words"])
            f.write(f"{r['slug']}\t{int(r['prose'])}\t{r['pronunciation'] or ''}\t{r['line']}\t{r['text']}\t{words}\n")
    print(f"wrote {out / 'input.tsv'}: {len(rows)} lines")


def render(root: Path) -> None:
    out = root / "pipeline" / "build" / "speech-samples"
    exe = root / "app" / "espeak" / "espeak-ng" / "build-host" / "src" / "espeak-ng"
    env = {"ESPEAK_DATA_PATH": str(root / "pipeline" / "build" / "espeak"), "PATH": "/usr/bin:/bin"}
    for txt in sorted(out.glob("*.txt")):
        lines = [l.split("\t") for l in txt.read_text(encoding="utf-8").splitlines() if l.strip()]
        # file lines: voice <TAB> phonemes
        voice = lines[0][0]
        phon = " ".join(l[1] for l in lines)
        wav = txt.with_suffix(".wav")
        subprocess.run([str(exe), "-v", voice, "-s", "140", "-w", str(wav), phon], env=env, check=True)
        print(f"wrote {wav}")
