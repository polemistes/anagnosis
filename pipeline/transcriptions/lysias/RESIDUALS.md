# Hude's Lysias: the second pass (residuals, sections, paragraphs)

The batch files `pipeline/transcriptions/lysias/batch-NN.md` have been checked once, by the flags
(INSTRUCTIONS.md, which still holds: read it). The flags compared the OCR with the check text
(Lamb's Loeb) by letters only; Hude differs from Lamb also in punctuation, accents, capitals and
brackets, and Tesseract read some words rightly without being sure of them. The residual pass
(`lysias-residuals`) compared every checked line with Tesseract's reading of it, word by word
with its punctuation. What still disagrees is listed per page; your work is to settle each item
against the print.

## Files

For each page `p-0028` that has residuals, in `pipeline/build/hude-pages/lysias/residuals/`:

* `r-0028.md`: the numbered items, each with the line's key, the text's word and the OCR's.
* `r-0028.png`: the printed lines concerned, each labelled with its key. Look here.
* the whole page: `pipeline/build/drama-scans/orationesrecogno00lysi/pages/leaf_0028.png`.

## Each item

* **word / accents / punctuation / brackets**: look at the word in the crop. If the print has
  what the OCR read, change the batch text to the print (the word, its accents and breathings,
  its punctuation: comma, full stop, raised stop ·, question mark ;, a bracket). If the print
  has what the text has, leave it. Tesseract misreads a raised stop as a full stop, a colon or a
  quotation mark, adds commas from specks, and confuses grave and acute, smooth and rough
  breathings, ἦν and ἣν, ἂν and ἃν: change only what the print clearly shows.
* **"the OCR reads … here, the text has nothing"**: a word on the printed line that the text
  lacks (add it where printed), a margin number, or noise (leave it).
* **Capitals and quotation marks**: the residuals do not compare them. While you look at each
  crop, make the first letters of the words you see follow the print (Hude begins a new train of
  thought with a capital, also inside a line), and the quotation marks ‘ ’ stand where he prints
  them.
* Write one line under `--- notes` for each change: `28.4 res: raised stop after ἄνδρες, as
  printed`. Items you leave need no note.

## Sections, paragraphs, headings

On every page of your batches, against the whole page image: each section number in the outer
margin must have its `§speech.section` mark on that line, before the word where the section
begins (after the wider space, where it begins inside the line); each line Hude indents must have
a `¶` line before it, and no other line; each heading inside a speech must be a `[label]` line of
its own, counted in the keys. Correct and note what is wrong.

**Your own files.** Scripts, enlarged crops and other helpers go only in the folder you were
given (`pipeline/build/agent-scratch/lysias-res-<job>/`), never under `/tmp`; delete your crops
when you are done. Do not commit.

## Checking

From `pipeline/`, for each of your batch files:

    .venv/bin/python -m anagnosis_pipeline check-lysias-batch transcriptions/lysias/batch-NN.md

Each remark must be a change you or the first pass made and noted. Save after each page. Reply,
per page: items settled, changes made.
