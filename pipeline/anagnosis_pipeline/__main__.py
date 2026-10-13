"""CLI: python -m anagnosis_pipeline <command>"""
from __future__ import annotations

import argparse
import sys
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent  # repo root
SOURCES = ROOT / "pipeline" / "sources"
TEXTS = ROOT / "texts"
DATA = ROOT / "data"


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(prog="anagnosis_pipeline")
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("fetch", help="download upstream sources into pipeline/sources/")
    sub.add_parser("import", help="convert upstream sources into the editable files in texts/")
    sub.add_parser("import-odyssey", help="(re)generate texts/odyssey/ from Perseus and the treebank; overwrites hand edits")
    sub.add_parser("prepare-odyssey-pages", help="page images and drafts for transcribing Allen's Odyssey (pipeline/build/odyssey-pages/)")
    sub.add_parser("merge-odyssey", help="build texts/odyssey/ grc.txt, apparatus and tokens from the transcription of Allen's text")
    cb = sub.add_parser("check-odyssey-batch", help="check transcription batch files")
    cb.add_argument("files", nargs="+")
    sub.add_parser("build-morpheus-forms", help="run Morpheus over the open corpora: pipeline/build/morpheus-analyses.tsv.gz for the analyser")
    sub.add_parser("prepare-symposium-pages", help="page images and drafts for transcribing Burnet's Symposium (pipeline/build/symposium-pages/)")
    sub.add_parser("merge-symposium", help="texts/symposium/ from the transcription (pipeline/transcriptions/symposium/), GLAUx, Jowett and Bury")
    csb = sub.add_parser("check-symposium-batch", help="check Symposium transcription batch files")
    csb.add_argument("files", nargs="+")
    psp = sub.add_parser("prepare-sophocles-pages", help="page images of Jebb's Sophocles scans for the critical notes and the text check (pipeline/build/sophocles-pages/)")
    psp.add_argument("plays", nargs="*")
    csp = sub.add_parser("check-sophocles-batch", help="check transcription batches of a Sophocles play")
    csp.add_argument("play")
    csp.add_argument("files", nargs="+")
    clp = sub.add_parser("check-sophocles-lines", help="apply a lyric-pass file (lines-NN.md) to texts/<play>/grc.txt and show the verses it makes")
    clp.add_argument("play")
    clp.add_argument("file")
    msp = sub.add_parser("merge-sophocles-apparatus", help="texts/<play>/commentary-jebb-apparatus.md from the batches")
    msp.add_argument("plays", nargs="*")
    map_ = sub.add_parser("merge-sophocles-appendix", help="texts/<play>/appendix.md from the appendix batches")
    map_.add_argument("plays", nargs="*")
    isp = sub.add_parser("import-sophocles", help="texts/<play>/ for Sophocles' plays in Jebb's edition (sophocles.py): text, translation, tokens, syntax, commentary")
    isp.add_argument("plays", nargs="*", help="slugs (default: all): ajax electra oedipustyrannus oedipuscoloneus philoctetes trachiniae")
    sub.add_parser("fetch-nt", help="download the New Testament sources into pipeline/sources/nt/ (SBLGNT, MACULA, Dodson, BSB)")
    sub.add_parser("import-nt", help="texts/newtestament/ from the SBLGNT, MACULA, Dodson and the Berean Standard Bible")
    sub.add_parser("prepare-autenrieth-pages", help="page images and OCR drafts for transcribing Autenrieth's Homeric Dictionary (pipeline/build/autenrieth-pages/)")
    cab = sub.add_parser("check-autenrieth-batch", help="check Autenrieth transcription batch files")
    cab.add_argument("files", nargs="+")
    sub.add_parser("check-autenrieth", help="check the whole Autenrieth transcription: pages missing or twice, order and seams between batches")
    sub.add_parser("import-syntax", help="regenerate texts/antigone/syntax-nodes.tsv (treebank punctuation and elliptic nodes) without touching the other files")
    sub.add_parser("check", help="validate texts/ (line numbers, token alignment, lexicon coverage)")
    m = sub.add_parser("merge-apparatus", help="merge transcription batches into texts/antigone/commentary-jebb-apparatus.md")
    m.add_argument("--batches", default=str(ROOT / "pipeline" / "build" / "apparatus"))
    v = sub.add_parser("verify-apparatus", help="check apparatus lemmas against the Greek text")
    ma = sub.add_parser("merge-appendix", help="merge appendix transcription batches into texts/antigone/appendix.md")
    ma.add_argument("--batches", default=str(ROOT / "pipeline" / "build" / "apparatus"))
    b = sub.add_parser("build", help="build data/lexicon.sqlite and one data/<text>.sqlite per text")
    b.add_argument("--out", default=str(DATA))
    b.add_argument("--only", help="rebuild only this text's database (and the catalog), keeping the lexicon")
    c = sub.add_parser("catalog", help="write data/catalog.json alone, from the about.md headers and the built databases")
    c.add_argument("--out", default=str(DATA))
    args = ap.parse_args(argv)

    if args.cmd == "fetch":
        from .fetch import fetch
        fetch(SOURCES)
    elif args.cmd == "import":
        from .import_perseus import import_antigone
        import_antigone(SOURCES, TEXTS)
    elif args.cmd == "import-odyssey":
        from .odyssey import import_odyssey
        import_odyssey(SOURCES, TEXTS)
    elif args.cmd == "prepare-odyssey-pages":
        from .odyssey_pages import prepare
        index = prepare(SOURCES, TEXTS, ROOT / "pipeline" / "build" / "odyssey-pages", refresh_crops=True)
        print(f"{len(index)} pages; {sum(1 for p in index if not p['apparatus_found'])} without a detected apparatus")
    elif args.cmd == "merge-odyssey":
        from .odyssey_merge import merge
        merge(ROOT / "pipeline" / "transcriptions" / "odyssey", ROOT / "pipeline" / "build" / "odyssey-pages", TEXTS, SOURCES,
              DATA / "lexicon.sqlite", ROOT / "pipeline" / "build")
    elif args.cmd == "check-odyssey-batch":
        from .odyssey_merge import check_batch
        bad = 0
        for f in args.files:
            problems = check_batch(Path(f), ROOT / "pipeline" / "build" / "odyssey-pages")
            print(f"{f}: {len(problems)} remarks")
            for p in problems:
                print("  " + p)
            bad += len(problems)
        return 1 if bad else 0
    elif args.cmd == "merge-symposium":
        from .symposium_merge import merge as merge_symposium
        return 1 if merge_symposium(ROOT / "pipeline" / "transcriptions" / "symposium", ROOT / "pipeline" / "build" / "symposium-pages",
                                    TEXTS, SOURCES, DATA / "lexicon.sqlite", ROOT / "pipeline" / "build") else 0
    elif args.cmd == "check-symposium-batch":
        from .symposium_merge import check_batch as check_symposium
        bad = 0
        for f in args.files:
            problems = check_symposium(Path(f), ROOT / "pipeline" / "build" / "symposium-pages", SOURCES)
            print(f"{f}: {len(problems)} remarks")
            for p in problems:
                print("  " + p)
            bad += len(problems)
        return 1 if bad else 0
    elif args.cmd == "build-morpheus-forms":
        from .morpheus_forms import build as build_morpheus
        build_morpheus(SOURCES, TEXTS, ROOT / "pipeline" / "build" / "morpheus-analyses.tsv.gz")
    elif args.cmd == "prepare-symposium-pages":
        from .symposium_pages import prepare as prepare_symposium
        index = prepare_symposium(SOURCES, ROOT / "pipeline" / "build" / "symposium-pages")
        print(f"{len(index)} pages")
    elif args.cmd == "fetch-nt":
        from .nt import fetch_nt
        fetch_nt(SOURCES)
    elif args.cmd == "import-nt":
        from .nt import import_nt
        return 1 if import_nt(SOURCES, TEXTS, ROOT / "pipeline" / "build") else 0
    elif args.cmd == "prepare-autenrieth-pages":
        from .autenrieth_pages import prepare as prepare_autenrieth
        index = prepare_autenrieth(SOURCES, ROOT / "pipeline" / "build" / "autenrieth-pages")
        print(f"{len(index)} pages")
    elif args.cmd == "check-autenrieth-batch":
        from .autenrieth import check_batch as check_autenrieth
        bad = 0
        for f in args.files:
            problems = check_autenrieth(Path(f), ROOT / "pipeline" / "build" / "autenrieth-pages")
            print(f"{f}: {len(problems)} remarks")
            for p in problems:
                print("  " + p)
            bad += len(problems)
        return 1 if bad else 0
    elif args.cmd == "prepare-sophocles-pages":
        from .sophocles import PLAYS
        from .sophocles_pages import prepare as prepare_sophocles
        index = prepare_sophocles(SOURCES, ROOT / "pipeline" / "build" / "sophocles-pages", args.plays or list(PLAYS))
        print(json.dumps(index, indent=1))
    elif args.cmd == "check-sophocles-lines":
        from .sophocles import apply_text_check
        from .sophocles_pages import DIFF, read_batches
        from .textfmt import parse_file
        doc = parse_file(TEXTS / args.play / "grc.txt")
        path = Path(args.file)
        pages = read_batches(path.parent, files=[path])
        for stem, block in pages.items():
            diffs = [(m.group(1), bool(m.group(2)), m.group(3), m.group(4)) for raw in block["differences"] if (m := DIFF.match(raw))]
            bad = [raw for raw in block["differences"] if not DIFF.match(raw)]
            for raw in bad:
                print(f"{stem}: '{raw}' is not 'N: ours «…» print «…»'")
            touched = {d[0] for d in diffs}
            before = [l.n for l in doc.lines]
            _, _, warnings = apply_text_check(doc, [], [], set(), None, diffs)
            for w in warnings:
                print(f"{stem}: {w}")
            nums = [int(re.match(r"\d+", n).group()) for n in touched if re.match(r"\d+", n)]
            if not nums:
                continue
            lo, hi = min(nums) - 2, max(nums) + 2
            print(f"== {stem}: our lines {lo}-{hi} after the changes (z = a verse split off; the import numbers them)")
            for l in doc.lines:
                m = re.match(r"\d+", l.n)
                if m and lo <= int(m.group()) <= hi:
                    print(f"  {l.n}\t{l.text}")
    elif args.cmd == "check-sophocles-batch":
        from .sophocles_pages import check_batch as check_sophocles
        bad = 0
        for f in args.files:
            problems = check_sophocles(Path(f), TEXTS, args.play)
            print(f"{f}: {len(problems)} remarks")
            for p in problems:
                print("  " + p)
            bad += len(problems)
        return 1 if bad else 0
    elif args.cmd == "merge-sophocles-apparatus":
        from .sophocles import PLAYS, PART_ROMAN
        from .sophocles_pages import SCAN_EDITIONS, merge as merge_sophocles
        for slug in args.plays or list(PLAYS):
            play = PLAYS[slug]
            header = (f"# title: Critical notes\n# author: Richard C. Jebb\n# lang: eng\n"
                      f"# source: Sophocles, The Plays and Fragments, {PART_ROMAN[play.part]}: The {play.title_en}, Cambridge University Press, "
                      f"{SCAN_EDITIONS[slug]} (critical notes), transcribed page by page\n"
                      f"# license: CC BY-SA 4.0 (transcription; the edition is in the public domain)\n")
            d = ROOT / "pipeline" / "transcriptions" / "sophocles" / slug
            n, sigla = merge_sophocles(d, TEXTS / slug / "commentary-jebb-apparatus.md", header)
            print(f"{slug}: {n} notes" + (f"; sigla: {sigla[:80]}" if sigla else ""))
    elif args.cmd == "merge-sophocles-appendix":
        from .sophocles import PLAYS, PART_ROMAN
        from .sophocles_pages import SCAN_EDITIONS, merge_appendix
        for slug in args.plays or list(PLAYS):
            play = PLAYS[slug]
            d = ROOT / "pipeline" / "transcriptions" / "sophocles" / slug
            if not any(d.glob("appendix-*.md")):
                continue
            header = (f"# title: Appendix\n# author: Richard C. Jebb\n"
                      f"# source: Sophocles, The Plays and Fragments, {PART_ROMAN[play.part]}: The {play.title_en}, Cambridge University Press, "
                      f"{SCAN_EDITIONS[slug]} (Appendix), transcribed page by page\n"
                      f"# license: CC BY-SA 4.0 (transcription; the edition is in the public domain)\n")
            n = merge_appendix(d, TEXTS / slug / "appendix.md", header)
            print(f"{slug}: {n} notes")
    elif args.cmd == "import-sophocles":
        from .sophocles import PLAYS, import_play
        for slug in args.plays or list(PLAYS):
            print(f"== {slug}")
            import_play(slug, SOURCES, TEXTS, ROOT / "pipeline" / "build", DATA / "lexicon.sqlite")
    elif args.cmd == "check-autenrieth":
        from .autenrieth import check_all as check_autenrieth_all
        problems = check_autenrieth_all(ROOT / "pipeline" / "transcriptions" / "autenrieth", ROOT / "pipeline" / "build" / "autenrieth-pages")
        print(f"{len(problems)} remarks")
        for p in problems:
            print("  " + p)
        return 1 if problems else 0
    elif args.cmd == "import-syntax":
        from .import_perseus import import_syntax_nodes
        import_syntax_nodes(SOURCES, TEXTS)
    elif args.cmd == "check":
        from .check import check_all
        return check_all(TEXTS, SOURCES)
    elif args.cmd == "merge-apparatus":
        from .apparatus import merge
        out = TEXTS / "antigone" / "commentary-jebb-apparatus.md"
        n = merge(Path(args.batches), out)
        print(f"wrote {out}: {n} entries")
        ocr = SOURCES / "scans" / "sophocles03soph_djvu.txt"
        if ocr.exists():
            from .ffmarks import apply_ff_marks

            print(f"f./ff. marks from OCR: {apply_ff_marks(out, ocr)} headings")
    elif args.cmd == "merge-appendix":
        from .apparatus import merge_appendix
        out = TEXTS / "antigone" / "appendix.md"
        print(f"wrote {out}: {merge_appendix(Path(args.batches), out)} entries")
    elif args.cmd == "verify-apparatus":
        from .apparatus import verify
        return 1 if verify(TEXTS / "antigone" / "commentary-jebb-apparatus.md", TEXTS / "antigone" / "grc.txt") else 0
    elif args.cmd == "build":
        from .build import build
        build(TEXTS, SOURCES, Path(args.out), only=args.only)
    elif args.cmd == "catalog":
        from .build import build_catalog
        build_catalog(TEXTS, Path(args.out))
    return 0


if __name__ == "__main__":
    sys.exit(main())
