"""Download the upstream sources into pipeline/sources/."""
from __future__ import annotations

import re
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
    # Burnet's Oxford Plato, vol. III (the Gorgias) is fetched leaf by leaf by gorgias_pages.py
    # Burnet's Oxford Plato, vol. II (the Symposium): a reprint of about 1935 with a good Greek
    # OCR, and the 1910 printing the Perseus text follows, whose OCR reads the Latin
    **{
        f"scans/{ident}{suffix}": f"https://archive.org/download/{ident}/{ident}{suffix}"
        for ident in ("platonisopera02platuoft", "operarecognovitb02platuoft")
        for suffix in (".pdf", "_djvu.txt")
    },
    # Autenrieth's Homeric Dictionary (tr. Keep, rev. Flagg, 1891), PIMS Toronto scan with a Greek
    # OCR: the page images the reader's Autenrieth is transcribed from (autenrieth_pages.py)
    "scans/homericdictiona00aute.pdf": "https://archive.org/download/homericdictiona00aute/homericdictiona00aute.pdf",
    # Woodhouse's English-Greek Dictionary (1910): the OCR by Akemdwr (woodhouse.py), and the
    # 1910 scan (from Google, 600 ppi) its corrections are checked against (woodhouse_pages.py)
    "woodhouse/Woodhouse.dsl": "https://archive.org/download/Woodhouse/Woodhouse.dsl",
    "scans/woodhouse-1910-english-attic-greek-dictionary.pdf":
        "https://archive.org/download/woodhouse-1910-english-attic-greek-dictionary/Woodhouse_1910_English_Attic-Greek_Dictionary.pdf",
    # GLAUx (CC BY-SA 4.0): automatic lemmas, morphology and syntax of the Symposium
    "glaux/0059-011.xml": f"{RAW}/alekkeersmaekers/glaux/main/xml/0059-011.xml",
    # ... and of the Gorgias (gorgias_merge.py)
    "glaux/0059-023.xml": f"{RAW}/alekkeersmaekers/glaux/main/xml/0059-023.xml",
    # Jowett's Gorgias: the Wikisource text, and the OCR of the 1892 printing whose margin gives
    # the Stephanus pages that text lacks (gorgias.py)
    "jowett/gorgias.wiki": "https://en.wikisource.org/w/index.php?title=Gorgias_(Jowett)&action=raw",
    "jowett/gorgias-1892-scan.txt": "https://archive.org/download/b24750189_0002/b24750189_0002_djvu.txt",
    # ... and of the two Sophocles plays the treebank lacks (sophocles.py)
    "glaux/0011-006.xml": f"{RAW}/alekkeersmaekers/glaux/main/xml/0011-006.xml",
    "glaux/0011-007.xml": f"{RAW}/alekkeersmaekers/glaux/main/xml/0011-007.xml",
    # Jebb's translations of the other Sophocles plays, modernized by Perseus (sophocles.py)
    **{
        f"{slug}.{eng}.xml": f"{RAW}/PerseusDL/canonical-greekLit/master/data/tlg0011/{tlg}/tlg0011.{tlg}.{eng}.xml"
        for slug, tlg, eng in (("ajax", "tlg003", "perseus-eng2"), ("electra", "tlg005", "perseus-eng2"),
                               ("oedipustyrannus", "tlg004", "perseus-eng2"), ("oedipuscoloneus", "tlg007", "perseus-eng2"),
                               ("philoctetes", "tlg006", "perseus-eng2"), ("trachiniae", "tlg001", "perseus-eng3"))
    },
    **{
        f"lsj/grc.lsj.perseus-eng{i}.xml": f"{RAW}/PerseusDL/lexica/master/CTS_XML_TEI/perseus/pdllex/grc/lsj/grc.lsj.perseus-eng{i}.xml"
        for i in range(1, 28)
    },
    # The nine plays (pipeline/PLAN-drama.md, drama.py): the Perseus Greek texts the OCR of each
    # edition is checked against (never shipped), and the Perseus translations used
    **{
        f"drama/{urn}.xml": f"{RAW}/PerseusDL/canonical-greekLit/master/data/{urn.split('.')[0]}/{urn.split('.')[1]}/{urn}.xml"
        for urn in (
            "tlg0085.tlg005.perseus-grc2", "tlg0085.tlg006.perseus-grc2", "tlg0085.tlg007.perseus-grc2",
            "tlg0019.tlg003.perseus-grc2", "tlg0019.tlg007.perseus-grc2", "tlg0019.tlg009.perseus-grc2",
            "tlg0006.tlg002.perseus-grc2", "tlg0006.tlg003.perseus-grc2", "tlg0006.tlg017.perseus-grc2",
            # Smyth's Aeschylus (Loeb 1926), Coleridge's Alcestis and Medea, Buckley's Bacchae (fallback)
            "tlg0085.tlg005.perseus-eng3", "tlg0085.tlg006.perseus-eng2", "tlg0085.tlg007.perseus-eng2",
            "tlg0006.tlg002.perseus-eng2", "tlg0006.tlg003.perseus-eng2", "tlg0006.tlg017.perseus-eng2",
            # Hesiod's Theogony (pipeline/PLAN-theogony.md): Evelyn-White's Loeb text and translation
            "tlg0020.tlg001.perseus-grc2", "tlg0020.tlg001.perseus-eng2",
            # Lucian's A True Story (pipeline/PLAN-true-story.md): Harmon's Loeb text (the check
            # text, never shipped) and his translation
            "tlg0062.tlg012.perseus-grc2", "tlg0062.tlg012.perseus-eng2",
            # The Shepherd of Hermas (pipeline/PLAN-hermas.md): Lake's translation and his notes
            "tlg1419.tlg001.perseus-eng1",
        )
    },
    # The Shepherd of Hermas: Tauber and Macdonald's text of Lake (the check text, never shipped),
    # First1KGreek's edition of Lake (its apparatus notes are the check of ours), GLAUx
    "hermas/013-shepherd.txt": f"{RAW}/jtauber/apostolic-fathers/master/texts/013-shepherd.txt",
    "hermas/013-shepherd_COMPARE_JT3vsSM2_notes.txt": f"{RAW}/jtauber/apostolic-fathers/master/comparison/013-shepherd_COMPARE_JT3vsSM2_notes.txt",
    "hermas/tlg1419.tlg001.1st1K-grc1.xml": f"{RAW}/OpenGreekAndLatin/First1KGreek/master/data/tlg1419/tlg001/tlg1419.tlg001.1st1K-grc1.xml",
    "glaux/1419-001.xml": f"{RAW}/alekkeersmaekers/glaux/main/xml/1419-001.xml",
    # GLAUx for the six plays the AGDT lacks (the Aeschylus treebanks are in treebanks/)
    **{f"glaux/{n}.xml": f"{RAW}/alekkeersmaekers/glaux/main/xml/{n}.xml"
       for n in ("0019-003", "0019-007", "0019-009", "0006-002", "0006-003", "0006-017")},
    # GLAUx for Lucian's A True Story (automatic syntax, aligned to Nilén's words)
    "glaux/0062-012.xml": f"{RAW}/alekkeersmaekers/glaux/main/xml/0062-012.xml",
    # The Athenian Society's Aristophanes (1912): Lysistrata, Frogs
    **{f"gutenberg/pg{n}.txt": f"https://www.gutenberg.org/cache/epub/{n}/pg{n}.txt" for n in (8688, 8689)},
}
GUTENBERG_MIRROR = "https://gutenberg.pglaf.org/{a}/{b}/{c}/{n}/{n}.txt"
# Coleridge's Bacchantes (The Plays of Euripides, vol. 2, 1913), proofread on Wikisource
COLERIDGE = "https://en.wikisource.org/w/index.php?title=Page:The_Plays_of_Euripides_Vol._2-_Edward_P._Coleridge_(1913).djvu/{n}&action=raw"
COLERIDGE_PAGES = range(99, 142)
HOPPER = "https://www.perseus.tufts.edu/hopper/opensource/downloads/texts/hopper-texts-GreekRoman.tar.gz"
HOPPER_FILES = {
    "Classics/LSJ/opensource/ml.xml": "middle-liddell.xml",
    "Classics/Sophocles/opensource/jebb.soph.ant_eng.xml": "jebb-antigone-commentary.xml",
    "Classics/Homer/opensource/hom.od_gk.xml": "odyssey.perseus-gk.xml",
    "Classics/Homer/opensource/hom.od_eng.xml": "odyssey.murray-eng.xml",
    "Classics/Homer/opensource/monro.hom.od_eng.xml": "odyssey-merry-monro-commentary.xml",
    "Classics/Plato/opensource/bury.symp.xml": "symposium-bury-commentary.xml",
    "Classics/Plato/opensource/lodge.plat.gorg_eng.xml": "gorgias-lodge-commentary.xml",
    # Jebb's Greek text of the other Sophocles plays, and his commentaries (none for the Philoctetes)
    **{f"Classics/Sophocles/opensource/soph.{code}_gk.xml": f"{slug}.perseus-gk.xml"
       for slug, code in (("ajax", "aj"), ("electra", "el"), ("oedipustyrannus", "ot"), ("oedipuscoloneus", "oc"),
                          ("philoctetes", "phil"), ("trachiniae", "trach"))},
    **{f"Classics/Sophocles/opensource/jebb.soph.{code}_eng.xml": f"jebb-{slug}-commentary.xml"
       for slug, code in (("ajax", "aj"), ("electra", "el"), ("oedipustyrannus", "ot"), ("oedipuscoloneus", "oc"),
                          ("trachiniae", "trach"))},
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
        try:
            _download(url, sources / name)
        except OSError:
            if not name.startswith("gutenberg/"):
                raise
            n = re.search(r"\d+", name).group()
            print(f"Gutenberg refused {url}; trying the mirror", file=sys.stderr)
            _download(GUTENBERG_MIRROR.format(a=n[0], b=n[1], c=n[2], n=n), sources / name)
    for n in COLERIDGE_PAGES:
        _download(COLERIDGE.format(n=n), sources / "coleridge" / f"bacchantes-{n}.wiki")
    # Morpheus (MPL-2.0), built here and run by build-morpheus-forms
    morpheus = sources / "morpheus"
    if not morpheus.exists():
        import subprocess

        subprocess.run(["git", "clone", "--depth", "1", "https://github.com/perseids-tools/morpheus.git", str(morpheus)], check=True)
        print("Morpheus cloned; build it: cd pipeline/sources/morpheus/src && CFLAGS='-std=gnu89 -fcommon' make && make install", file=sys.stderr)
    # Abbott-Smith's New Testament lexicon (public domain TEI), for the shared dictionaries
    if not (sources / "abbott-smith").exists():
        import subprocess

        subprocess.run(["git", "clone", "--depth", "1", "https://github.com/translatable-exegetical-tools/Abbott-Smith.git",
                        str(sources / "abbott-smith")], check=True)
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
