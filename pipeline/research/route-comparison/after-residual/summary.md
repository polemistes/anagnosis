# Route comparison, Trachiniae pp. 80-143: route E vs route O (state `37b78c0`)

Text: verses 1-440 (pages 80-142); words: reference 2602, route E 2604, route O 2604.
Apparatus: route E 258 notes (pages 80-143), route O 258 notes (pages 80-142 with the facing pages); plus the sigla paragraph.

## Disagreements for adjudication (items.jsonl)

| kind | items |
|---|---|
| apparatus-greek | 27 |
| apparatus-other | 1 |
| text-accent | 4 |
| text-punctuation | 13 |
| **total** | **45** |

Not adjudicated: 25 words where the verse division or numbering differs (verse-division.md). Speaker labels are not compared.

## Convention differences excluded (normalised before comparing)

Occurrences normalised in each route's files (not all of them differ from the other route).

| part | rule | route E | route O |
|---|---|---|---|
| apparatus | angle brackets < > written ⟨ ⟩ (pairs ×2) | 2 | 0 |
| apparatus | bold lemma markers ** (route E) | 86 | 0 |
| apparatus | elision / apostrophe mark ’ ᾽ ' written ʼ | 226 | 16 |
| apparatus | ellipsis character … written ... | 2 | 0 |
| apparatus | italics markers *…* (route E) | 43 | 0 |
| apparatus | look-alike characters (Latin XO for Greek ΧΟ; ʽ for ῾) | 2 | 0 |
| apparatus | superscript figure (V² written V2 by route E) | 0 | 9 |
| apparatus | the note's line number repeated at the start of its text | 0 | 1 |
| text | angle brackets < > written ⟨ ⟩ (pairs ×2) | 2 | 0 |
| text | asterisk before a conjecture (route O leaves it out by rule) | 7 | 0 |
| text | elision / apostrophe mark ’ ᾽ ' written ʼ | 24 | 0 |

Also by rule, not counted: spacing (whitespace collapsed; spaces around punctuation, dashes and the upright stroke | ignored in the apparatus, which is compared as words and single marks); "f."/"ff." after a note number (both routes drop it); the sigla note (route E `*Sigla.*` paragraph, route O `Sigla:` under notes) compared as a note of its own; Unicode NFC.

## Files

* `items.jsonl`: for the adjudicators (readings shuffled per item, fixed seed)
* `key.jsonl`: which reading is which route, and its relation to the reference (not for the adjudicators)
* `verse-division.md`: verse division and numbering differences (not adjudicated)
* `streams/`: the normalised texts of both routes and the reference, and the paired apparatus notes

Made with: `pipeline/.venv/bin/python research/route-comparison/compare.py --state 37b78c0 --out research/route-comparison/after-residual` (from pipeline/).
