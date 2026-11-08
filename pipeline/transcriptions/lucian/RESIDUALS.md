# Nilén's Lucian: the second pass (residuals, sections, paragraphs)

The batch files `pipeline/transcriptions/lucian/truestory/batch-NN.md` have been checked once, by
the flags, and reviewed (INSTRUCTIONS.md, which still holds: read it). The flags compared the OCR
with Harmon's text by letters only; Nilén differs from Harmon also in punctuation, accents and
brackets, and Tesseract read some words rightly without being sure of them. The residual pass
compared every checked line with Tesseract's reading of it, word by word with its punctuation.
What still disagrees is listed per page; your work is to settle each item against the print.

## Files

For each page `p-0200` that has residuals, in `pipeline/build/lucian-pages/truestory/residuals/`:

* `r-0200.md`: the numbered items, each with the line's key, the text's word and the OCR's.
* `r-0200.png`: the printed lines concerned, each labelled with its key. Look here.
* the whole page: `pipeline/build/lucian-pages/truestory/pages/leaf_0200.png`.

## Each item

* **word / accents / punctuation / brackets or asterisk**: look at the word in the crop. If the
  print has what the OCR read, change the batch text to the print (the word, its accents and
  breathings, its punctuation: comma, full stop, raised stop ·, question mark ;, an asterisk, a
  bracket). If the print has what the text has, leave it. Tesseract misreads a raised stop as a
  full stop or a quotation mark, adds commas from specks, and confuses grave and acute, smooth
  and rough breathings, ζ and ξ, κ and χ (Nilén's ϰ): change only what the print clearly shows.
  Nilén's stop set off by a space ("ἦν .") is written without the space; that is not a
  difference.
* **"the OCR reads … here, the text has nothing"**: a word on the printed line that the text
  lacks (add it where printed), a margin number, a chapter number, or noise (leave it).
* **Capitals**: the residuals do not compare case. While you look at each crop, make the first
  letters of the words you see follow the print (Nilén capitalises proper names and the first
  word of a paragraph only).
* Write one line under `--- notes` for each change: `133.4 res: raised stop after ἦν, as
  printed`. Items you leave need no note.

## Sections and paragraphs

On every page of your batch, against the whole page image: each chapter number in the margin
must have its `§book.section` mark on that line, before the word where the chapter begins; each
line Nilén indents must have a `¶` line before it, and no other line. Correct and note what is
wrong.

**Your own files.** Scripts, enlarged crops and other helpers go only in a folder of your own,
named after your batch file, under the session's scratchpad folder; never write a file directly
in the scratchpad or in another agent's folder. Do not commit.

## Checking

From `pipeline/`, for each of your batch files:

    .venv/bin/python -m anagnosis_pipeline check-lucian-batch transcriptions/lucian/truestory/batch-NN.md

Each remark must be a change you or the first pass made and noted. Save after each page. Reply,
per page: items settled, changes made.
