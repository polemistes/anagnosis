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
    sub.add_parser("check", help="validate texts/ (line numbers, token alignment, lexicon coverage)")
    m = sub.add_parser("merge-apparatus", help="merge transcription batches into texts/antigone/commentary-jebb-apparatus.md")
    m.add_argument("--batches", default=str(ROOT / "pipeline" / "build" / "apparatus"))
    v = sub.add_parser("verify-apparatus", help="check apparatus lemmas against the Greek text")
    b = sub.add_parser("build", help="build the SQLite bundle in data/")
    b.add_argument("--out", default=str(DATA / "antigone.sqlite"))
    args = ap.parse_args(argv)

    if args.cmd == "fetch":
        from .fetch import fetch
        fetch(SOURCES)
    elif args.cmd == "import":
        from .import_perseus import import_antigone
        import_antigone(SOURCES, TEXTS)
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
    elif args.cmd == "verify-apparatus":
        from .apparatus import verify
        return 1 if verify(TEXTS / "antigone" / "commentary-jebb-apparatus.md", TEXTS / "antigone" / "grc.txt") else 0
    elif args.cmd == "build":
        from .build import build
        build(TEXTS, SOURCES, Path(args.out))
    return 0


if __name__ == "__main__":
    sys.exit(main())
