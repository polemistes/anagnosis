# Transcribing Allen's Odyssey

This directory holds the transcription of T. W. Allen's Oxford text of the Odyssey (*Homeri
Opera* III–IV, *editio altera*, 1917 and 1919), page by page from the Internet Archive scans
`homeriopera03home` and `homeriopera04home`: the Greek text and the critical apparatus at the
foot of each page. `merge-odyssey` turns the batch files here into `texts/odyssey/grc.txt` and
`texts/odyssey/commentary-allen-apparatus.md`. The edition is in the public domain; the
transcription is published under CC BY-SA 4.0.

The page images and drafts are made by `prepare-odyssey-pages` in `pipeline/build/odyssey-pages/`:

* `<stem>.png`: the whole page; `<stem>-v1.png` and `<stem>-v2.png`: the upper and lower half of
  the text, enlarged; `<stem>-app.png`: the apparatus, enlarged. Read the text from the enlarged
  halves; use the whole page to see where the page begins and ends.
* `<stem>.md`: a draft. For every line it gives **D**, the Perseus text (from another edition,
  Murray's Loeb, so it differs from Allen in places), and two OCR readings of Allen's line:
  **A** from this scan and **B** from another printing of the same edition. Then an OCR of the
  apparatus from the other printing: its Latin is mostly right, its Greek, sigla and numbers
  are often wrong.

**The image is the authority.** The draft only helps you read it. Where the image is clear,
write what Allen prints even if D, A and B all say otherwise.

## Output format

One file per batch, `batch-NN.md`, with a block per page in page order:

```
=== p3-0021
--- text
1.1	Ἄνδρα μοι ἔννεπε, Μοῦσα, πολύτροπον, ὃς μάλα πολλὰ
1.2	πλάγχθη, ἐπεὶ Τροίης ἱερὸν πτολίεθρον ἔπερσε·
...
--- apparatus
1.1	πολύκροτον quidam ap. schol. Ar. Nub. 260, Eust.; υἱὸς Λαέρταο πολύκροτα μήδεα εἰδώς Hes. fr. 94. 22
1.1	πολλὰ] πάντων **c**
1.3	νόμον Zen.
...
--- notes
(optional: anything uncertain, one remark per line, starting with the line number)
```

The number and the text are separated by a single TAB.

## The text

* The draft's division into pages can be off by a line or two. Transcribe exactly the lines
  printed on the page image, no more and no fewer.
* Every verse line on the page, in order, numbered `book.line`. Allen prints a number every
  fifth line; count the lines in between. The draft's numbers can be wrong; follow Allen's.
* Copy Allen exactly: words, accents and breathings, iota subscript, diaeresis, capitals
  (he capitalises proper names and the first word of a paragraph), punctuation.
* Elision mark: ʼ (U+02BC MODIFIER LETTER APOSTROPHE), as in δʼ, ἀλλʼ, ἔνθʼ.
  Raised stop: · (U+00B7 MIDDLE DOT).
* Allen marks direct speech with quotation marks: copy them as printed, “ where a speech
  opens and ” where it closes (also ‘ ’ for a speech within a speech).
* Words or lines that Allen sets in square brackets keep their brackets.
* A line Allen prints that is missing from the draft (16.101, for instance) goes in with its
  number. A draft line Allen does not print is simply left out.
* Leave out the book title (ΟΔΥΣΣΕΙΑΣ Α), running heads, page numbers and line numbers.
* Where the image is genuinely unclear, keep D's reading if it fits the letters you can see,
  and say so under `--- notes`.

## The apparatus

* One output line per item: the line number it refers to (`book.line`), a TAB, the item.
  Allen prints a line's number once before all its items, which are separated by a wider space;
  repeat the number on each item's line. An item for a range of lines: `1.26-27`.
* Copy each item as printed: lemma, the bracket `]`, readings, sigla, authorities, Latin.
  Greek with full accents.
* Manuscript family sigla are printed in **bold** lower-case letters: write `**a**`, `**cd**`.
  Other sigla as printed, with superscript digits as Unicode superscripts: H³, L⁴, U⁵, p¹⁰
  (write the Gothic papyrus 𝔭 as a plain p).
* References: Iliad books are Greek capitals (`Ζ 154`), Odyssey books small letters
  (`ε 408`); keep them as printed. Keep Latin abbreviations as printed (`coni.`, `om.`,
  `add.`, `cf.`, `schol.`, `Zen.`, `Ar.`, `gl.`, `γρ.`, `ss.`, `uv.`). Write a colon or semicolon
  without the space Allen sets before it (`οἷς ἑτάροισι **be**: ...`).
* Lines Allen quotes as additions (plus-verses) are items of the line they follow, numbered with
  a letter as he does: `1.93a`, or `1.93a-b` for two.
* Ignore italics (the apparatus prints its Greek in italic). Keep spaced dots `. . .` as `...`.
* An item running over to the next page continues there; finish it on the page where it
  starts, under its own number.

## Before you write

Count the text lines you wrote for each page against the lines printed on the page, and
check that the numbers run on without a gap from the previous page (a gap is only right
where Allen's numbering itself skips).
