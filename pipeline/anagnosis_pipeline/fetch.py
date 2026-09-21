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
    "MorpheusUnicode.xml.zip": f"{RAW}/gcelano/LemmatizedAncientGreekXML/master/Morpheus/MorpheusUnicode.xml.zip",
    "logeion-shortdefs.txt": f"{RAW}/helmadik/shortdefs/master/shortdefsGreekEnglishLogeion",
    "antigone.tb.xml": f"{RAW}/PerseusDL/treebank_data/master/v2.1/Greek/texts/tlg0011.tlg002.perseus-grc2.tb.xml",
    **{
        f"lsj/grc.lsj.perseus-eng{i}.xml": f"{RAW}/PerseusDL/lexica/master/CTS_XML_TEI/perseus/pdllex/grc/lsj/grc.lsj.perseus-eng{i}.xml"
        for i in range(1, 28)
    },
}
HOPPER = "https://www.perseus.tufts.edu/hopper/opensource/downloads/texts/hopper-texts-GreekRoman.tar.gz"
HOPPER_FILES = {
    "Classics/LSJ/opensource/ml.xml": "middle-liddell.xml",
    "Classics/Sophocles/opensource/jebb.soph.ant_eng.xml": "jebb-antigone-commentary.xml",
}


def _download(url: str, dest: Path) -> None:
    dest.parent.mkdir(parents=True, exist_ok=True)
    if dest.exists():
        return
    print(f"fetching {url}", file=sys.stderr)
    tmp = dest.with_suffix(dest.suffix + ".part")
    urllib.request.urlretrieve(url, tmp)
    tmp.rename(dest)


TREEBANKS_API = "https://api.github.com/repos/PerseusDL/treebank_data/contents/v2.1/Greek/texts"


def fetch(sources: Path) -> None:
    for name, url in FILES.items():
        _download(url, sources / name)
    import json

    tb_dir = sources / "treebanks"
    if not tb_dir.exists() or not any(tb_dir.glob("*.xml")):
        with urllib.request.urlopen(TREEBANKS_API) as r:
            for entry in json.load(r):
                if entry["name"].endswith(".xml"):
                    _download(entry["download_url"], tb_dir / entry["name"])
    if not all((sources / v).exists() for v in HOPPER_FILES.values()):
        tarball = sources / "hopper-texts-GreekRoman.tar.gz"
        _download(HOPPER, tarball)
        with tarfile.open(tarball) as tf:
            for member, out in HOPPER_FILES.items():
                f = tf.extractfile(member)
                if f is None:
                    raise SystemExit(f"{member} not found in {tarball}")
                (sources / out).write_bytes(f.read())
                print(f"extracted {out}", file=sys.stderr)
    print("sources are complete")
