# The plays: the second pass (residuals and numbering)

The batch files `pipeline/transcriptions/drama/<play>/batch-NN.md` have been checked once, by
the flags (INSTRUCTIONS-text.md, which still holds; read it). The flags compared the OCR with
Perseus by letters only; the edition differs from Perseus also in punctuation, accents,
brackets and daggers, and Tesseract read some words rightly without being sure of them. The
residual pass compared every checked verse with Tesseract's reading of its printed line, word
by word with its punctuation. What still disagrees is listed per page; your work is to settle
each item against the print, and to make the numbering follow the print.

## Files

For each page `p-0042` that has residuals, in `pipeline/build/drama-pages/<play>/residuals/`:

* `r-0042.md`: the numbered items, each with the verse number, the text's word and the OCR's.
* `r-0042.png`: the printed lines concerned, each labelled with the verse number. Look here.
* the whole page: `pipeline/build/drama-pages/<play>/pages/leaf_0042.png`.

## Each item

* **word / accents / punctuation / brackets or dagger**: look at the word in the crop. If the
  print has what the OCR read, change the batch text to the print (the word, its accents and
  breathings, its punctuation: comma, full stop, raised stop ·, question mark ;, a dagger †, a
  bracket). If the print has what the text has, leave it. Tesseract misreads a raised stop as
  a full stop or a quotation mark, adds commas from specks and pencil, and confuses grave and
  acute, smooth and rough: change only what the print clearly shows. A diaeresis (ἀΐων,
  Ἀχαιϊκοῦ) is written as printed.
* **"the OCR reads … here, the text has nothing"**: a word on the printed line that the text
  lacks (add it if it is printed in the verse), or the apparatus, a margin number, a metrical
  label (στρ. α΄.), handwriting or noise (leave it).
* Write one line under `--- notes` for each change: `1234 res: comma after X, as printed`.
  Items you leave need no note.

## Numbering: the print's numbers win

The margin numbers printed every fifth verse are the edition's; where they differ from ours,
renumber to the print, and copy the apparatus numbers as printed:

* A verse the draft lettered (`49a`, `223a`) that the print counts as a verse of its own (the
  margin number falls so that it must be counted) takes the print's number (`50`, `224`).
* Where the print counts a stretch otherwise than Perseus (a verse more or fewer), the verses
  between two margin numbers run on from the first: renumber them so that every margin number
  stands on the verse that bears it, and the numbers still increase. Where two margin numbers
  cannot both be met without letters, keep the numbers that meet the later one and say so.
* Where the print transposes verses (prints Perseus's 1304 before 1303), keep each verse's own
  number (the number of the Perseus line its words are) in the print's order: `1304` then
  `1303`. The checker will remark that the numbering does not run on: note it.
* Your task lists the numbering questions the first pass left open on your pages; check every
  page's margin numbers against the batch as well.

## Checking

From `pipeline/`, for each of your batch files:

    .venv/bin/python -m anagnosis_pipeline check-drama-batch <play> transcriptions/drama/<play>/batch-NN.md

Each remark must be a change you or the first pass made and noted. Save after each page.
Reply, per page: items settled, changes made, verses renumbered.
