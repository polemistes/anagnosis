"""Download the upstream sources into pipeline/sources/."""
from __future__ import annotations

import sys
import tarfile
import urllib.request
from pathlib import Path

RAW = "https://raw.githubusercontent.com"
FILES = {
    "antigone.grc2.xml": f"{RAW}/PerseusDL/canonical-greekLit/master/data/tlg0011/tlg002/tlg0011.tlg002.perseus-grc2.xml",
    "antigone.eng2.xml": f"{RAW}/PerseusDL/canonical-greekLit/master/data/tlg0011/tlg002/tlg0011.tlg002.perseus-eng2.xml",
    "scans/sophocles03soph_djvu.txt": "https://archive.org/download/sophocles03soph/sophocles03soph_djvu.txt",
    # the open Greek corpus whose word forms Morpheus analyses for the word analyser (morpheus_forms.py)
    "corpora/canonical-greekLit.tar.gz": "https://codeload.github.com/PerseusDL/canonical-greekLit/tar.gz/refs/heads/master",
    "logeion-shortdefs.txt": f"{RAW}/helmadik/shortdefs/master/shortdefsGreekEnglishLogeion",
    "antigone.tb.xml": f"{RAW}/PerseusDL/treebank_data/master/v2.1/Greek/texts/tlg0011.tlg002.perseus-grc2.tb.xml",
    # Allen's Oxford Odyssey, second edition (1917, 1919), in two printings; archive.org dates
    # them 1908 and 1912, but both title pages read "editio altera". The UConn copy is clean;
    # the Toronto copy has a student's notes on a few pages but an OCR that reads the Latin.
    **{
        f"scans/{ident}.{ext}": f"https://archive.org/download/{ident}/{ident}{suffix}"
        for ident in ("homeriopera03home", "homeriopera04home", "homerioperarecog03homeuoft", "homerioperarecog04homeuoft")
        for ext, suffix in (("pdf", ".pdf"), ("txt", "_djvu.txt"))
    },
    # Burnet's Oxford Plato, vol. II (the Symposium): a reprint of about 1935 with a good Greek
    # OCR, and the 1910 printing the Perseus text follows, whose OCR reads the Latin
    **{
        f"scans/{ident}{suffix}": f"https://archive.org/download/{ident}/{ident}{suffix}"
        for ident in ("platonisopera02platuoft", "operarecognovitb02platuoft")
        for suffix in (".pdf", "_djvu.txt")
    },
    # GLAUx (CC BY-SA 4.0): automatic lemmas, morphology and syntax of the Symposium
    "glaux/0059-011.xml": f"{RAW}/alekkeersmaekers/glaux/main/xml/0059-011.xml",
    **{
        f"lsj/grc.lsj.perseus-eng{i}.xml": f"{RAW}/PerseusDL/lexica/master/CTS_XML_TEI/perseus/pdllex/grc/lsj/grc.lsj.perseus-eng{i}.xml"
        for i in range(1, 28)
    },
}
HOPPER = "https://www.perseus.tufts.edu/hopper/opensource/downloads/texts/hopper-texts-GreekRoman.tar.gz"
HOPPER_FILES = {
    "Classics/LSJ/opensource/ml.xml": "middle-liddell.xml",
    "Classics/Sophocles/opensource/jebb.soph.ant_eng.xml": "jebb-antigone-commentary.xml",
    "Classics/Homer/opensource/hom.od_gk.xml": "odyssey.perseus-gk.xml",
    "Classics/Homer/opensource/hom.od_eng.xml": "odyssey.murray-eng.xml",
    "Classics/Homer/opensource/monro.hom.od_eng.xml": "odyssey-merry-monro-commentary.xml",
    "Classics/Plato/opensource/bury.symp.xml": "symposium-bury-commentary.xml",
}
# Jowett's Symposium (The Dialogues of Plato, 3rd ed., 1892, vol. I), as proofread on Wikisource
JOWETT = "https://en.wikisource.org/w/index.php?title=Page:The_Dialogues_of_Plato_v._1.djvu/{n}&action=raw"
JOWETT_PAGES = range(580, 634)


def _download(url: str, dest: Path) -> None:
    dest.parent.mkdir(parents=True, exist_ok=True)
    if dest.exists():
        return
    print(f"fetching {url}", file=sys.stderr)
    tmp = dest.with_suffix(dest.suffix + ".part")
    # Wikimedia refuses the default Python user agent
    req = urllib.request.Request(url, headers={"User-Agent": "anagnosis-pipeline/1.0 (https://github.com/anagnosis)"})
    with urllib.request.urlopen(req) as r, open(tmp, "wb") as f:
        while chunk := r.read(1 << 20):
            f.write(chunk)
    tmp.rename(dest)


TREEBANKS_API = "https://api.github.com/repos/PerseusDL/treebank_data/contents/v2.1/Greek/texts"


def fetch(sources: Path) -> None:
    for name, url in FILES.items():
        _download(url, sources / name)
    # Morpheus (MPL-2.0), built here and run by build-morpheus-forms
    morpheus = sources / "morpheus"
    if not morpheus.exists():
        import subprocess

        subprocess.run(["git", "clone", "--depth", "1", "https://github.com/perseids-tools/morpheus.git", str(morpheus)], check=True)
        print("Morpheus cloned; build it: cd pipeline/sources/morpheus/src && CFLAGS='-std=gnu89 -fcommon' make && make install", file=sys.stderr)
    import json

    tb_dir = sources / "treebanks"
    if not tb_dir.exists() or not any(tb_dir.glob("*.xml")):
        with urllib.request.urlopen(TREEBANKS_API) as r:
            for entry in json.load(r):
                if entry["name"].endswith(".xml"):
                    _download(entry["download_url"], tb_dir / entry["name"])
    for n in JOWETT_PAGES:
        _download(JOWETT.format(n=n), sources / "jowett" / f"{n}.wiki")
    if not all((sources / v).exists() for v in HOPPER_FILES.values()):
        tarball = sources / "hopper-texts-GreekRoman.tar.gz"
        _download(HOPPER, tarball)
        with tarfile.open(tarball) as tf:
            for member, out in HOPPER_FILES.items():
                if (sources / out).exists():
                    continue
                f = tf.extractfile(member)
                if f is None:
                    raise SystemExit(f"{member} not found in {tarball}")
                (sources / out).write_bytes(f.read())
                print(f"extracted {out}", file=sys.stderr)
    print("sources are complete")
