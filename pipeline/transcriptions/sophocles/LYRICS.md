# Jebb's Sophocles: the division of the lyric verses

The first pass (INSTRUCTIONS.md) checked the words of the text and Jebb's printed line numbers.
In the lyric passages (choral odes, kommoi, some anapaests) Jebb often divides the words into
verses otherwise than our text, which came from Perseus; then his line numbers cannot fall on
the lines they belong to. This second pass makes our division follow the print, page by page.

Compare the Greek text at the top of each page in your task (left-hand pages: header
ΣΟΦΟΚΛΕΟΥΣ) with our text as imported after the first pass, `texts/<play>/grc.txt`. Each of
its lines is `number<TAB>text`; it already has Jebb's readings, and his numbers wherever the
margin prints one. Look only at the division into verses: where it agrees, write nothing.

## The differences

Write them in the format of the first pass, under our line numbers in `texts/<play>/grc.txt`,
quoting our words exactly as they stand there (ʼ for the elision), enough of them to be found
in the line:

* A printed verse that ends inside one of our lines: split our line with ` | ` where the print
  begins the new verse:
  `414: ours «πάραλά τʼ ἄντρα καὶ νέμος ἐπάκτιον,» print «πάραλά τʼ ἄντρα | καὶ νέμος ἐπάκτιον,»`
* Two of our lines that the print sets as one verse: delete the second, quoting it whole,
  `415: ours «κατείχετʼ ἀμφὶ Τροίαν» print «»`, then add its words to the first,
  `414: ours «δὴ» print «δὴ κατείχετʼ ἀμφὶ Τροίαν»`. Write the deletion first.
* A word that the print divides between two verses: split it as printed, with the hyphen:
  `609: ours «μανίας ξύνεστιν» print «μανί- | ας ξύνεστιν»`.
* A verse split between two speakers (our lettered lines, 591 and 591a) stays as it is.

Change nothing but the division. If you notice a word, accent or stop that still differs from
the print, say so in your reply; do not write it as a difference.

## Numbers that two printed lines share

Jebb sometimes gives one number to two short printed lines (a verse whose second part is
indented, or two short cola counted as one), so that our lines, numbered one by one, run ahead
of his. His note headings and the margin show where. Give such places as fixed points under
`--- numbers` in your block, the number with a letter for the later line, followed by its first
word, as in the first pass: `401a ἀλκίμα` (his 401 is ἀλλά μʼ ἁ Διὸς with ἀλκίμα θεὸς); and give
any other number you can establish for a line our numbering misplaces (`354 οἴμʼ`). The import
then numbers the lines between the fixed points.

A long verse that wraps onto an indented second line usually covers two or more of the
traditional numbers, and Jebb prints the margin number beside the line where that number falls,
often the wrapped end (`ἄφρακτος | φίλων· 910`). His note headings show which number each part
of the verse has (908 ὤ μοι, 909 οἶος, 910 ἄφρακτος): give the verse's FIRST number as a fixed
point with its first two words where one is not enough to find it (`908 ὤμοι ἐμᾶς`). Our line
then carries the first number, and the numbers it covers are skipped, as in the print.

## Output

One file per task, `transcriptions/sophocles/<play>/lines-NN.md` (the name is in your task),
a block per page that has changes:

    === p-0156
    --- differences
    414: ours «…» print «… | …»
    --- notes
    (anything uncertain)

## Checking

From `pipeline/`:

    .venv/bin/python -m anagnosis_pipeline check-sophocles-lines <play> transcriptions/sophocles/<play>/lines-NN.md

It applies your differences to our text and prints, for each page, our lines as they become (a
verse split off is numbered `z` for now; the import gives it its number). Compare that with the
print: the verses must now be the printed verses, one for one. Fix and run it again; a warning
"not found" means the quoted words are not in that line (or near it).
