"""Compile the data of the reader's voice: eSpeak NG's phoneme tables with the Ancient Greek
table of Anagnosis (app/espeak/phsource/ph_grc), the two voices (app/espeak/voices: grc for
Homeric and Attic, grc-koine for Koine) and the (empty) grc dictionary.

eSpeak NG's sources are fetched by app/espeak/fetch-espeak.sh (the same release the app is built
against, with its patches); the compiler is that checkout built for this computer, in
app/espeak/espeak-ng/build-host (built here when missing). The compiled files go to
app/espeak/src/main/assets/espeak-ng-data/, which is committed, with a 'version' file that
tells the app when to copy them to its files again. See app/PLAN-speech.md, section 3.
"""
from __future__ import annotations

import hashlib
import shutil
import subprocess
import sys
from pathlib import Path

# the compiled files the app needs (all languages' phonemes are in phondata; it is small)
DATA_FILES = ["phontab", "phonindex", "phondata", "intonations", "grc_dict"]
VOICES = {name: f"lang/grk/{name}" for name in ("grc", "grc-koine", "grc-f", "grc-koine-f", "grc-klatt", "grc-koine-klatt", "grc-f-klatt", "grc-koine-f-klatt")}


def _host_espeak(clone: Path) -> Path:
    exe = clone / "build-host" / "src" / "espeak-ng"
    if exe.exists():
        return exe
    print("building eSpeak NG for this computer (build-host)", file=sys.stderr)
    subprocess.run(["cmake", "-B", "build-host", "-DUSE_MBROLA=OFF", "-DUSE_LIBSONIC=OFF", "-DUSE_LIBPCAUDIO=OFF",
                    "-DUSE_KLATT=ON", "-DUSE_SPEECHPLAYER=OFF", "-DUSE_ASYNC=OFF", "-DESPEAK_BUILD_MANPAGES=OFF",
                    "-DBUILD_TESTING=OFF", "-DEXTRA_ru=OFF", "-DEXTRA_cmn=OFF", "-DEXTRA_yue=OFF"], cwd=clone, check=True)
    subprocess.run(["cmake", "--build", "build-host", "--target", "espeak-ng-bin", "-j8"], cwd=clone, check=True)
    return exe


def build_data_dir(root: Path, work: Path) -> Path:
    """Compile everything into work/espeak-ng-data (work is wiped first); returns that directory.
    root is the repository; the result can be used at once with ESPEAK_DATA_PATH=work."""
    espeak_dir = root / "app" / "espeak"
    clone = espeak_dir / "espeak-ng"
    if not (clone / "phsource" / "phonemes").exists():
        raise SystemExit(f"{clone} is missing: run app/espeak/fetch-espeak.sh first")
    exe = _host_espeak(clone)
    if work.exists():
        shutil.rmtree(work)
    data = work / "espeak-ng-data"
    shutil.copytree(clone / "phsource", work / "phsource")
    shutil.copy(espeak_dir / "phsource" / "ph_grc", work / "phsource" / "ph_grc")
    master = work / "phsource" / "phonemes"
    text = master.read_text(encoding="utf-8")
    old = "phonemetable grc base2\ninclude ph_greek_ancient"
    if old not in text:
        raise SystemExit("eSpeak's phonemes file has changed: 'phonemetable grc base2 / include ph_greek_ancient' not found")
    master.write_text(text.replace(old, "phonemetable grc base2\ninclude ph_grc"), encoding="utf-8")
    shutil.copytree(clone / "espeak-ng-data" / "lang", data / "lang")
    for name, rel in VOICES.items():
        shutil.copy(espeak_dir / "voices" / name, data / rel)
    (data / "voices").mkdir(parents=True, exist_ok=True)
    env = {"ESPEAK_DATA_PATH": str(work), "PATH": "/usr/bin:/bin"}
    subprocess.run([str(exe), "--compile-intonations"], cwd=work / "phsource", env=env, check=True, stdout=subprocess.DEVNULL)
    res = subprocess.run([str(exe), "--compile-phonemes"], cwd=work / "phsource", env=env, capture_output=True, text=True)
    if res.returncode != 0 or "error" in (res.stdout + res.stderr).lower():
        print(res.stdout[-3000:], res.stderr[-3000:], file=sys.stderr)
        if res.returncode != 0:
            raise SystemExit("compiling the phonemes failed")
    dsrc = work / "dictsource"
    dsrc.mkdir()
    for f in ("grc_rules", "grc_list"):
        shutil.copy(espeak_dir / "dictsource" / f, dsrc / f)
    subprocess.run([str(exe), "--compile=grc"], cwd=dsrc, env=env, check=True, stdout=subprocess.DEVNULL)
    return data


def build(root: Path) -> None:
    work = root / "pipeline" / "build" / "espeak"
    data = build_data_dir(root, work)
    out = root / "app" / "espeak" / "src" / "main" / "assets" / "espeak-ng-data"
    if out.exists():
        shutil.rmtree(out)
    digest = hashlib.sha256()
    for rel in DATA_FILES + list(VOICES.values()):
        src = data / rel
        dst = out / rel
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy(src, dst)
        digest.update(rel.encode())
        digest.update(src.read_bytes())
    (out / "version").write_text(digest.hexdigest()[:16] + "\n", encoding="utf-8")
    total = sum(p.stat().st_size for p in out.rglob("*") if p.is_file())
    print(f"wrote {out}: {total / 1e6:.1f} MB, version {digest.hexdigest()[:16]}")
