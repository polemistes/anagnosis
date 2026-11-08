# Lake's Shepherd: the second pass (residuals, paragraphs, marks)

The batch files `pipeline/transcriptions/hermas/batch-NN.md` have been checked once, by the flags,
and reviewed (INSTRUCTIONS.md, which still holds: read it). The flags compared the OCR with
Tauber's text by letters only; the print may differ also in punctuation, accents and brackets, and
Tesseract read some words rightly without being sure of them. The residual pass compared every
checked verse with Tesseract's reading of the page, word by word with its punctuation. What still
disagrees is listed per page; your work is to settle each item against the print.

## Files

For each page `p-0020` that has residuals, in `pipeline/build/lake-pages/hermas/residuals/`:

* `r-p-0020.md`: the numbered items, each with the verse, the text's word and the OCR's.
* `r-p-0020.png`: the printed lines concerned, each labelled with its verse. Look here.
* the whole page: `pipeline/build/lake-pages/hermas/pages/leaf_0020.png`.

## Each item

* **word / accents / punctuation / brackets**: look at the word in the crop. If the print has what
  the OCR read, change the batch text to the print (the word, its accents and breathings, its
  punctuation: comma, full stop, raised stop ·, question mark ;, a bracket). If the print has what
  the text has, leave it. Tesseract misreads a raised stop as a full stop or a quotation mark, adds
  commas from specks, and confuses grave and acute, smooth and rough breathings, ζ and ξ: change
  only what the print clearly shows. A footnote mark is not a difference.
* **"the OCR reads … here, the text has nothing"**: a word on the printed line that the text lacks
  (add it where printed), a verse number, a margin reference, a footnote numeral, or noise (leave
  it).
* Write one line under `--- notes` for each change: `1.1.4 res: raised stop after αὐτῇ, as
  printed`. Items you leave need no note.

## Paragraphs and marks

On every page of your batches, against the whole page image: each verse Lake begins on a new,
indented line must have a `¶` line before it, and no other verse; each raised footnote numeral of
the Greek must be in the text after its word, and the apparatus items must answer them. Correct and
note what is wrong.

**Your own files.** Scripts, enlarged crops and other helpers go only in a folder of your own,
named after your batch file, under the session's scratchpad folder; never write a file directly in
the scratchpad or in another agent's folder. Do not commit.

## Checking

From `pipeline/`, for each of your batch files:

    .venv/bin/python -m anagnosis_pipeline check-hermas-batch transcriptions/hermas/batch-NN.md

Each remark must be a change you or the first pass made and noted. Save after each page. Reply,
per page: items settled, changes made.
