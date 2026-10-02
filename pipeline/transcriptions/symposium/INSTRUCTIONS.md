# Transcribing Burnet's Symposium

This directory holds the transcription of John Burnet's Oxford text of Plato's Symposium
(*Platonis Opera* II, Oxford), page by page from the Internet Archive scan
`platonisopera02platuoft`: the Greek text line by line, with Burnet's line numbers, and his
critical apparatus. `merge-symposium` turns the batch files into `texts/symposium/grc.txt` and
`texts/symposium/commentary-burnet-apparatus.md`. The edition is in the public domain; the
transcription is published under CC BY-SA 4.0.

The page images and drafts are made by `prepare-symposium-pages` in
`pipeline/build/symposium-pages/`:

* `<stem>.png`: the whole page; `<stem>-v1.png` and `<stem>-v2.png`: the upper and lower half of
  the text, enlarged; `<stem>-app.png`: the apparatus, enlarged. Read the text from the enlarged
  halves; use the whole page to see where the page begins and ends.
* `<stem>.md`: a draft. **D** is the Perseus text of Burnet's edition, section by section
  (`[172a] ...`), without his line breaks, with lower-case first letters and without some of his
  brackets; **A** is an OCR of the page's lines (with the margin letters and numbers); then OCR
  readings of the apparatus from this printing (Greek mostly right) and from the 1910 printing
  (Latin and sigla right, Greek garbled).

**The image is the authority.** The draft only helps you read it.

## Line numbers

Burnet prints the Stephanus page at the head of the page and in the margin ("St. III p. 172",
then "173" where a new Stephanus page begins), the section letters b–e in the margin, and every
fifth line number. Lines are counted afresh in each section: the line beside the letter **b** is
b1, the next b2, and so on; "5" and "10" in the margin confirm the count. Where a new Stephanus
page begins, the margin shows the page number (e.g. "173") instead of the letter a: that line is
`173a1`. A line is written with its Stephanus page, section letter and line: `172a1`, `172b5`,
`173a1`. Every printed line counts, verse lines included.

## Output format

One file per batch, `batch-NN.md`, with a block per page in page order:

```
=== s-0165
--- text
172a1	{ΑΠΟΛ.} Δοκῶ μοι περὶ ὧν πυνθάνεσθε οὐκ ἀμελέτητος
172a2	εἶναι. καὶ γὰρ ἐτύγχανον πρῴην εἰς ἄστυ οἴκοθεν ἀνιὼν Φαληρόθεν·
...
--- apparatus
172a1	οὐκ B T W: νῦν οὐκ Methodius al.
172a4	ὦ B T W: ὁ al.
...
--- notes
(optional: anything uncertain, one remark per line, starting with the line number)
```

The number and the text are separated by a single TAB.

## The text

* Every printed line of the page, in order, with its number.
* **A word divided at the end of a line is written whole on the line where it begins**, and
  left out of the next line: Burnet's `Φαλη-` / `ρόθεν` becomes `Φαληρόθεν` at the end of the
  first line.
* Copy Burnet exactly: words, accents and breathings, iota subscript, diaeresis, capitals,
  punctuation, quotation marks, dashes (—), and his brackets ⟨ ⟩ for additions and [ ] for
  deletions. This printing marks speeches with quotation marks (“ ” and, inside a speech, ‘ ’):
  copy them where they stand, opening and closing, even across pages. The Perseus text (D) has
  no quotation marks and lower-case first letters; follow the page.
* Elision mark: ʼ (U+02BC MODIFIER LETTER APOSTROPHE), not ’ or ᾽: `δʼ`, `ἀλλʼ`. ’ (U+2019) is
  only the closing single quotation mark. Raised stop: · (U+00B7 MIDDLE DOT).
* **Speaker names** printed in the text (ΑΠΟΛ., ΕΤ., ΕΤΑΙ.) are written in braces where they
  stand: `{ΑΠΟΛ.} Δοκῶ μοι …`, also in the middle of a line.
* **A new paragraph** (a line Burnet indents) is marked by a line with only `¶` before it. In
  the reported dialogues (Diotima and Socrates, Socrates and Agathon) each reply begins a new
  indented line: each gets its `¶`.
* **Verse** quoted and set off on lines of its own (Homer, Agathon's hexameters) is written with
  `| ` (a bar and a space) at the start of each verse line, after the TAB:
  `196c1	| τῆς μένθʼ ἁπαλοὶ πόδες· οὐ γὰρ ἐπʼ οὔδει`. Verse run on inside a prose line is not marked.
* Leave out the title (ΣΥΜΠΟΣΙΟΝ), "St. III", the list of persons, running heads, page
  numbers, and the margin letters and numbers.
* Where the image is genuinely unclear, keep D's reading if it fits the letters you can see,
  and say so under `--- notes`.

## The apparatus

* One output line per item: the full line number it refers to (`172a4`), a TAB, the item.
  Burnet gives the section letter and line ("a 4", "b 2"); within a section he gives only the
  next line number; take the Stephanus page from the text on the page (where the page holds the
  end of one Stephanus page and the start of the next, "a 2" after the change belongs to the new
  page). An item for several lines: `172a4-5`.
* Copy each item as printed: lemma, readings, sigla (B T W and others, as printed; small
  letters for later hands, as printed: `Tb`, `W t`; superscripts as Unicode superscripts),
  authorities, Latin. Greek with full accents. Ignore italics.
* Items follow one another on a line separated by wide spaces; each starts with its section
  letter and line number in bold ("a 2", "b 7"), or, for a further item on the same line, with
  its lemma alone (it belongs to the line of the item before it).
* A colon or semicolon is written without a space before it.

## Checking

Run `check-symposium-batch` on your file (see below). It reports numbering that does not run
on, apparatus numbers naming lines you did not write, divided words, elision written with ’,
and every place where your words differ from the Perseus text (Burnet's words without his
lines). Burnet and Perseus agree almost everywhere, so each difference must be looked at in
the image: fix your slips; keep what the page shows and say so under `--- notes`. A remark on
’ that is a closing quotation mark is fine.

## Before you write

Count the text lines you wrote for each page against the printed lines, check that the line
numbers run on and restart at each new section letter, and that the apparatus numbers match
lines you wrote.
