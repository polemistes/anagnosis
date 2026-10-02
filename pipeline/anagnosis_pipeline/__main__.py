"""CLI: python -m anagnosis_pipeline <command>"""
from __future__ import annotations

import argparse
import sys
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
    return 0


if __name__ == "__main__":
    sys.exit(main())
