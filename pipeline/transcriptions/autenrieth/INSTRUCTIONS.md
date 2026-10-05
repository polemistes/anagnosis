# Transcribing Autenrieth's Homeric Dictionary

This directory holds the transcription of G. Autenrieth, *A Homeric Dictionary for Schools and
Colleges*, translated by R. P. Keep and revised by Isaac Flagg (New York: Harper, 1891), page by
page from the Internet Archive scan `homericdictiona00aute`. The book is in the public domain;
the transcription is published under CC BY-SA 4.0. The pipeline builds the reader's Autenrieth
dictionary from the batch files.

The page images and drafts are made by `prepare-autenrieth-pages` in
`pipeline/build/autenrieth-pages/`:

* `<stem>.png`: the whole page; `<stem>-l1.png`, `<stem>-l2.png`: the left column, enlarged,
  upper and lower half; `<stem>-r1.png`, `<stem>-r2.png`: the right column likewise. Read the
  text from the enlarged halves; the halves overlap by a line or so, so do not write a line
  twice. Use the whole page to see where columns begin and end.
* `<stem>.md`: an OCR draft of the running head and of each column. Its English is mostly right;
  its Greek accents, breathings, italics and the Greek letters that number Homer's books are
  often wrong.

**The image is the authority.** The draft only helps you read it.

## Output format

One file per batch, `batch-NNN.md`, with a block per page in page order:

```
=== a-0037
--- head
ἁμαρτέω | ἀμητήρ
--- left
+ *to hit*, τινός, and abs., ἤμβροτες, οὐδʼ ἔτυχες, Ε 287; met., ‘mistake,’ ‘fail of,’ …
**ἁμαρτέω**: see ὁμαρτέω.
**ἁμαρτῇ**, **ἁμαρτῆ** (ἅμα, root αρ): *at once, together.*
…
--- right
+ *dreadful;* voc. as term of reproach, *miserable*, ρ 219.
**ἀμείβω**, fut. ἀμείψω, -ομαι, aor. ἠμείψατο, ἀμείψατο: I. act., *change, exchange;* …
…
--- notes
(optional: anything uncertain, one remark per line)
```

* `--- head`: the two headwords of the running head at the top of the page, separated by ` | `
  (leave out the page number).
* `--- left` and `--- right`: the columns, top to bottom, **one line per entry**: join the
  printed lines of an entry into one line.
* An entry begins with its headword in bold, `**ἀμείβω**`, as printed (with the hyphens that
  mark a compound: `**ἀ-μείλικτος**`). Where two headwords are printed in bold at the start, both
  are bold: `**ἁμαρτῇ**, **ἁμαρτῆ**`. A numbered homograph keeps its number before the bold:
  `1. **ἀ-μέρδω** (μέρος): …`, `2. **ἀ-μέρδω** …`.
* **The first line of a column** that continues an entry from the end of the previous column
  or page begins with `+ ` (a plus and a space). Only the first line of a column can be a
  continuation; every other line begins with a headword.
* **A new letter beginning halfway down a page** (its heading across both columns, the old
  letter above it in both columns): write each column top to bottom as usual, the old letter's
  part and then the new letter's. The checker reports the first headword of the right column as
  out of order; say under `--- notes` that the letter changes there.

## The text

* Copy exactly: words, accents and breathings, iota subscript, diaeresis, capitals,
  punctuation, the dagger † (which marks that all the passages are cited), the equals sign =,
  dashes —, and the single quotation marks ‘ ’ around translations.
* **Italics**: the English meanings printed in italics are written in single asterisks:
  `*change, exchange;*`. Mark only italic English (and italic Latin). The Greek in the running
  text is printed in sloping type throughout: do not mark it. A semicolon or full stop printed
  in italics after the meaning goes inside the asterisks (`*at once, together.*`); a comma goes
  outside (`*miserable*, ρ 219`).
* **Bold**: headwords only, as above (and any other bold Greek or numeral, in `**…**`).
* **A word divided at the end of a printed line** is written whole: `ἠμεί-` / `ψατο` becomes
  `ἠμείψατο`; `ex-` / `change` becomes `exchange`. A hyphen that belongs to the word (the hyphen
  of a compound headword `ἀ-μέρδω`, English `rash-speaking`) stays. Where you cannot tell, keep
  the word whole without the hyphen if it is a single English or Greek word.
* **A word divided between two columns or pages** (`ἀν-` at the foot of a page, `τιάσειας` at
  the top of the next) is written whole at the foot of the earlier column; the next column's
  `+ ` line begins with what follows the word. Note it under `--- notes`.
* **References to Homer** are a book letter and a line number: the Iliad's books are the Greek
  capitals Α Β Γ Δ Ε Ζ Η Θ Ι Κ Λ Μ Ν Ξ Ο Π Ρ Σ Τ Υ Φ Χ Ψ Ω, the Odyssey's the small letters
  α β γ δ ε ζ η θ ι κ λ μ ν ξ ο π ρ σ τ υ φ χ ψ ω. **Always write them as Greek characters**,
  never as the Latin look-alikes (Ε 287 with a Greek Epsilon, not E; ρ 219 with a Greek rho,
  not p; Ω, not Q; Λ, not A). Read each letter from the image: the OCR gets most of them wrong
  (it prints a for α, n for η, x for χ, Q for Ω, 8 for δ, ἃ or ἂ for λ). (Il.) and (Od.) stay
  as printed.
* The digamma (Ϝ, ϝ) appears in etymologies: `(Ϝέπος)`.
* Leave out the marks of vowel quantity on Greek (the short lines and curves over α ι υ: write
  ἄμεναι for ᾱ̆μεναι). English names keep theirs as printed (Diōres). Where the book marks
  with a quantity mark, and no diaeresis, that α ι are two syllables (ᾱισσω), write the
  diaeresis of the Homeric word: ἀΐσσω.
* Where a breathing or accent is at the limit of what the scan shows, take the reading that is
  right for the Homeric word, and note it.
* The book has a few misprints (a wrong book letter, a slip in a Greek word). Copy them as
  printed and note them under `--- notes` with what is meant: `left 17: Η 369 printed; the
  passage is Ε 369`.
* Spaced hyphens are plain hyphens (`deep-fetched`); no space before a colon or inside
  parentheses.
* Elision mark: ʼ (U+02BC): `οὐδʼ`, `ἀπʼ`. The closing single quotation mark is ’ (U+2019).
* Leave out the running head's page number, the large letter at the head of each letter's
  section, and the woodcuts with their captions and numbers ("No. 12" and the like inside an
  entry stays).
* Where the image is genuinely unclear, write your best reading and say so under `--- notes`.

## Checking

Run `check-autenrieth-batch` on your file (from `pipeline/`:
`.venv/bin/python -m anagnosis_pipeline check-autenrieth-batch ../pipeline/transcriptions/autenrieth/batch-NNN.md`).
It reports format errors, headwords out of alphabetical order (usually a misread letter, or a
line written twice or left out), a running head that does not match the first and last
headwords, Latin letters used as book letters, words that mix Greek and Latin letters, and
columns much shorter than the OCR (a part left out). Look at each remark in the image: fix your
slips; where the page really is so, say so under `--- notes`.

## Before you write

Check for each column that you have every entry from the top of the column to the bottom, that
the halves' overlap is not written twice, and that the last entry of the left column flows
into the first line of the right column (`+ `) when the entry continues.
