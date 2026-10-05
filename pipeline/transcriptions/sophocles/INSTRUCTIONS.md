# Jebb's Sophocles: critical notes and text check

This directory holds the page-by-page work on R. C. Jebb's editions of Sophocles (*The Plays and
Fragments*, Cambridge University Press) for the reader's six further plays: Ajax, Electra,
Oedipus Tyrannus, Oedipus at Colonus, Philoctetes, Trachiniae. The editions are in the public
domain; the transcription is published under CC BY-SA 4.0. Each play has a folder
(`ajax/`, `electra/`, `oedipustyrannus/`, `oedipuscoloneus/`, `philoctetes/`, `trachiniae/`) with
batch files.

Page images: `pipeline/build/sophocles-pages/<play>/p-NNNN.png`, the PDF page number zero padded
to four digits (made by `prepare-sophocles-pages`). Read them with the Read tool, one at a time,
in order.

## The page

Jebb's pages come in pairs. A left-hand page (header ΣΟΦΟΚΛΕΟΥΣ) has the **Greek text** at the
top, with the line numbers in the margin every fifth line; a right-hand page (header with the
play's Greek name) has the **English translation** at the top. Under the text or the translation
there is a block in SMALL type set full width: the **critical notes**. Each note begins with a
bold line number ("1", "4 ff.", "5 f.", "12—14") and usually a Greek lemma. Under them, in two
columns, the commentary: do NOT transcribe the commentary or the translation.

Pages before the play begins (introduction, arguments, list of persons) and pages without
critical notes need no block, except that a left-hand page with Greek text always gets one.

## Your two jobs on each page

1. **Critical notes**: transcribe the small full-width block exactly.
2. **Text check** (left-hand pages only): compare the Greek text printed at the top with our text
   of the play, `transcriptions/sophocles/<play>/reference-grc.txt` (the Perseus text as first
   imported, kept fixed while the batches are made, because the import that applies the check
   renumbers `texts/<play>/grc.txt`; each line is `number<TAB>text`; a verse shared between
   speakers has its later parts lettered: `591`, `591a`; speakers are lines beginning `@`).
   * Under `--- numbers`, list every line number printed in the margin, with the first word of
     that printed line: `5 ὅθεν`.
   * Under `--- differences`, list every place where the printed text differs from ours, word,
     accent, breathing, punctuation, a bracket, a missing or extra word or line:
     `12: ours «πόλει» print «πόλις»`. Use our line number; for a line we lack, write the number
     of our line it should follow with `+`: `554+: ours «» print «τὸ μὴ φρονεῖν γὰρ …»`.
     Leave out differences of apostrophe shape (ʼ ’ ᾽) and of the spacing around punctuation.
     Where Jebb divides a lyric passage into verses differently, report the moved words as
     differences on both lines, and a line of ours that the print joins to the one before as
     `N: ours «…» print «»`, so that the text can follow the print.

## Output format

One file per batch (path given in your task), with a block per page in page order:

    === p-0110
    --- numbers
    5 ὅθεν
    10 ἱκτηρίοις
    --- differences
    12: ours «πόλει» print «πόλις»
    --- apparatus
    ## 1
    **νέα**] νέαι Blaydes.

    ## 2
    **θοάζετε** L: θοάζεται A.
    --- notes
    (anything uncertain, one remark per line)

Rules for the critical notes (as for the Antigone):

* The heading is `## ` plus the FIRST line number of the note's label only: "4 ff." → `## 4`,
  "5 f." → `## 5`, "12—14" → `## 12-14` (a range with a plain hyphen). A lettered number keeps its
  letter (`## 161b`).
* Each Greek lemma (the word(s) Jebb prints in bold) is wrapped in `**...**`; keep the `]` that
  follows it OUTSIDE the bold, as printed: `**κοινὸν**] κλεινὸν`.
* Keep Jebb's wording, punctuation, abbreviations, sigla (L, A, B, Γ, L², r, MSS., cod. etc.) and
  dashes exactly. Book titles Jebb prints in italics go in `*...*`. Do not modernise.
* Greek in Unicode polytonic, precomposed characters, with every breathing and accent; ’
  (U+2019) for elision. Watch iota subscripts and circumflexes.
* Superscript hands like L² are written L2; "1st hand" as printed.
* A note that runs on from the previous page: the page's apparatus begins with a line
  `+ ` followed by the rest of that note (no heading). A note that runs on to the next page simply
  stops at the foot of the page; the next page's `+ ` line continues it. So every page is
  transcribed on its own, and nothing is written twice.
* If the same line number gets a second note (e.g. on the facing page), write the heading again.
* The first page with critical notes also has a note on the manuscripts ("L = cod. Laur. 32. 9 …"):
  put it first under `--- apparatus`, as a paragraph beginning `*Sigla.*`, before the first heading.
* Where something is genuinely illegible, write `[illegible]` and say so under `--- notes`; never
  guess silently. Where the Greek of the printed text and the line numbers are hard to read,
  say so under `--- notes` rather than inventing a difference.
* Nothing of your own: no comments or translations in the apparatus.

## Checking

From `pipeline/`:

    .venv/bin/python -m anagnosis_pipeline check-sophocles-batch <play> transcriptions/sophocles/<play>/batch-NN.md

It checks the format, the order of the notes, and the printed line numbers you listed against our
text (reference-grc.txt): a remark "numbering differs" means the printed line N begins with another word than our
line N. Look again at the image: if you misread, fix it; if the print really is so, leave it (and
it is a numbering difference we will correct) and say so under `--- notes`.
