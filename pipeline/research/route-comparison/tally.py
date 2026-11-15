#!/usr/bin/env python3
"""Route comparison, the tally: the adjudicators' verdicts against the key.

    pipeline/.venv/bin/python research/route-comparison/tally.py \
        --items DIR/items.jsonl --key DIR/key.jsonl --verdicts DIR/verdicts-*.jsonl [--out DIR/tally.md]

A verdict line: {"id": …, "verdict": "1" | "2" | "neither" | "both", "printed": "…", "note": …}.
"1"/"2" name the reading the page prints; "both" = both readings are what the page prints (the
difference does not matter on the page); "neither" = the page prints something else.

Per route and per kind: disagreements where the route was right, where it was wrong, and of the
wrong ones how many were a difference from the reference that it missed (its reading = reference,
the other route's = the print) and how many an error it introduced (its reading ≠ reference and
≠ print). For the apparatus there is no reference: wrong ones are not split. "neither" and "both"
are counted apart (with the same split for "neither"). Where several verdict files judge the same
item and disagree, the item is listed as disputed and left out of the counts.
"""
from __future__ import annotations

import argparse
import json
import sys
import unicodedata
from collections import Counter, defaultdict
from pathlib import Path

ELISION = "’᾽ʼ'᾿"


def load(path: Path) -> list[dict]:
    out = []
    for n, raw in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        if raw.strip():
            try:
                out.append(json.loads(raw))
            except json.JSONDecodeError as e:
                sys.exit(f"{path}:{n}: {e}")
    return out


def norm(s: str | None) -> str:
    s = unicodedata.normalize("NFC", s or "")
    for c in ELISION:
        s = s.replace(c, "ʼ")
    return " ".join(s.replace("*", "").split())


def part(kind: str) -> str:
    return "text" if kind.startswith("text") else "apparatus"


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--items", required=True, type=Path)
    ap.add_argument("--key", required=True, type=Path)
    ap.add_argument("--verdicts", required=True, type=Path, nargs="+")
    ap.add_argument("--out", type=Path, help="write the Markdown here as well as to stdout")
    args = ap.parse_args()

    items = {it["id"]: it for it in load(args.items)}
    key = {k["id"]: k for k in load(args.key)}
    verdicts: dict[str, list[tuple[str, dict]]] = defaultdict(list)
    problems = []
    for path in args.verdicts:
        for v in load(path):
            if v.get("id") not in items:
                problems.append(f"{path.name}: unknown id {v.get('id')!r}")
                continue
            if str(v.get("verdict")) not in ("1", "2", "neither", "both"):
                problems.append(f"{path.name}: {v['id']}: verdict {v.get('verdict')!r} not understood")
                continue
            verdicts[v["id"]].append((path.name, v))

    final: dict[str, dict] = {}
    disputed = []
    for iid, vs in verdicts.items():
        kinds = {str(v["verdict"]) for _, v in vs}
        if len(kinds) > 1:
            disputed.append((iid, [(name, v["verdict"], v.get("printed", "")) for name, v in vs]))
            continue
        final[iid] = vs[0][1]
    missing = [iid for iid in items if iid not in verdicts]

    # (route, kind) -> Counter
    t: dict[tuple[str, str], Counter] = defaultdict(Counter)
    inconsistent = []
    for iid, v in final.items():
        it, k = items[iid], key[iid]
        kind = it["kind"]
        verdict = str(v["verdict"])
        printed = norm(v.get("printed"))
        # does the adjudicator's "printed" agree with the reading chosen?
        if verdict in ("1", "2") and printed and printed != norm(it[f"reading_{verdict}"]):
            inconsistent.append((iid, verdict, it[f"reading_{verdict}"], v.get("printed")))
        for route in ("E", "O"):
            other = "O" if route == "E" else "E"
            mine = "1" if k["reading_1"] == route else "2"
            rel = k[route]["vs_reference"]
            orel = k[other]["vs_reference"]
            c = t[(route, kind)]
            c["items"] += 1
            if verdict == "both":
                c["both"] += 1
            elif verdict == "neither":
                c["neither"] += 1
                if rel == "= reference":
                    c["neither: = reference"] += 1
                elif rel:
                    c["neither: changed"] += 1
            elif verdict == mine:
                c["right"] += 1
            else:
                c["wrong"] += 1
                if rel is None:
                    pass
                elif rel == "= reference" and orel != "= reference":
                    c["wrong: missed"] += 1
                elif rel != "= reference":
                    c["wrong: introduced"] += 1
                else:
                    c["wrong: other"] += 1

    cols = ["items", "right", "wrong", "wrong: missed", "wrong: introduced", "neither", "neither: = reference",
            "neither: changed", "both"]
    head = ["route", "kind"] + cols
    out = ["# Route comparison: tally", "",
           f"Items {len(items)}; judged {len(final)}; disputed {len(disputed)}; without a verdict {len(missing)}; "
           f"verdict files: {', '.join(p.name for p in args.verdicts)}.", "",
           "*right* = the route's reading is what the page prints; *wrong* = the other route's is. Of the wrong ones "
           "(text only): *missed* = its reading is the reference's and the print differs from the reference; "
           "*introduced* = its reading is neither the reference's nor the print. *neither* = the page prints "
           "neither reading (split by the route's relation to the reference); *both* = the two readings are the same "
           "on the page.", ""]

    def cell(kind, col, c):
        apparatus_only = kind == "all apparatus" or (kind.startswith("apparatus") or kind == "missing-note")
        if apparatus_only and (col.startswith("wrong:") or col.startswith("neither:")):
            return "–"
        return str(c.get(col, 0))

    def table(rows):
        lines = ["| " + " | ".join(head) + " |", "|" + "---|" * len(head)]
        for route, kind, c in rows:
            lines.append("| " + " | ".join([route, kind] + [cell(kind, col, c) for col in cols]) + " |")
        return lines

    for route in ("E", "O"):
        out.append(f"## Route {route}")
        out.append("")
        rows = []
        totals = {"text": Counter(), "apparatus": Counter()}
        for (r, kind), c in sorted(t.items()):
            if r != route:
                continue
            rows.append((route, kind, c))
            totals[part(kind)].update(c)
        rows.append((route, "all text", totals["text"]))
        rows.append((route, "all apparatus", totals["apparatus"]))
        allc = Counter()
        allc.update(totals["text"])
        allc.update(totals["apparatus"])
        rows.append((route, "**all**", allc))
        out += table(rows) + [""]
    if disputed:
        out += ["## Disputed (verdict files disagree; not counted)", ""]
        out += [f"* {iid}: " + "; ".join(f"{n} → {v} ({p})" for n, v, p in vs) for iid, vs in disputed] + [""]
    if inconsistent:
        out += ["## Verdicts whose \"printed\" differs from the reading chosen (check them)", ""]
        out += [f"* {iid}: verdict {v} = «{r}», printed «{p}»" for iid, v, r, p in inconsistent] + [""]
    if missing:
        out += ["## Items without a verdict", "", ", ".join(missing), ""]
    if problems:
        out += ["## Problems in the verdict files", ""] + [f"* {p}" for p in problems] + [""]
    text = "\n".join(out)
    print(text)
    if args.out:
        args.out.write_text(text + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
