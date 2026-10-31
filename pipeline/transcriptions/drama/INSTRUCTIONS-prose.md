# The plays: the commentaries, introductions and Starkie's translation, from OCR

The English pages of the editions (the editor's notes, his introduction, and for the Clouds
Starkie's translation) are read by Tesseract with the English and Greek models and turned into
a draft in the batch file. English is read well; Greek inside English is read less well and
is re-read with the Greek model; the draft marks every word it doubts with a **flag**. Your
work on each page:

1. **Answer every flag** against its crop: correct the word, or confirm it.
2. **Check the structure**: that each note begins where the print begins one, with the right
   line number and lemma; that paragraphs and headings are the print's; that a note running on
   from the page before is marked.

Do not re-read or retype unflagged text. Read the whole page image only when a flag or the
structure needs it. Never guess: `[illegible]`, and a remark, where you cannot read it.

## Files

For each page `p-0250`, in `pipeline/build/drama-prose/<play>/`:

* `p-0250-flags.png`: the lines that hold flagged words, cut out and numbered, the flagged word
  marked. Look here first.
* `p-0250-col-l.png`, `p-0250-col-r.png`: the columns (or the whole block) enlarged, for a
  structure question or a flag whose line crop is not enough.
* `pages/leaf_0250.png`: the whole page.

The batch file (`notes-NN.md`, `intro-NN.md` or `trans-NN.md`, eight pages each) has a block
per page:

```
=== p-0250
## 779
**ὁ δῆμος**: as if there was an ἐκκλησία in Hades.

**κρίσιν ποεῖν**: not = κρίνειν (which would require ποιεῖσθαι), but ‘to institute (arrange)
a trial.’ Cf. 785 and ἐκκλησίαν ποιεῖν )( ποιεῖσθαι.

## 781
**οὐράνιόν γ’ ὅσον**: sc. ἀνεβόα. …
--- flags
1 ἐκκλησία [greek] →
2 ποεῖν [accent] →
--- notes
```

Each flag line is the crop's number, the word as the OCR read it and the kind of doubt; write
after the arrow the word as printed (or `ok` when the OCR was right), and correct the word in
the text above. Edit in place and **save after each page**.

## The notes (`notes-NN.md`)

* A note begins with the line number the editor prints before it: heading `## 779`; a range
  `## 1345-1451` (plain hyphen); "215 f." and "215 ff." become `## 215`; "1058, 1059" becomes
  `## 1058-1059`. A further note on the same line without a number, or a note that begins with
  a lemma alone (Tucker: "κρίσιν ποεῖν :" under 779), is a new paragraph under the same heading.
* The lemma (the Greek the editor prints in bold or spaced type at the start of the note) goes
  in `**…**`; the stop, colon or bracket after it stays outside: `**ὁ δῆμος**:`. Where the
  draft has split a note wrongly, or missed a note's beginning, mend it.
* Paragraphs as printed, separated by a blank line; lines joined into running text; a word
  divided at a line end written whole. Italics `*…*`, bold `**…**`; small capitals (MSS., B.C.)
  as ordinary capitals. Quotation marks, dashes and abbreviations as printed. Greek in Unicode
  polytonic, precomposed, with every breathing and accent.
* A note that runs on to the next page simply stops at the foot; the next page's block begins
  with `+ ` and the rest of it. A word divided between two pages is written whole at the end of
  the first page.
* The running head (page number, NOTES, the line range) is left out. A footnote is written as
  `[Note: ¹ …]` after the paragraph where its mark stands.
* Structural headings the editor prints inside the notes (Starkie's "1345-1451. Agon II.")
  are notes like any other, under their range.

## The introduction (`intro-NN.md`)

The rules of `pipeline/transcriptions/sophocles/INTRODUCTION.md` and `APPENDIX.md` hold:
chapters `# Title` as printed (small capitals as ordinary capitals and small letters), numbered
sections `## § 3`, a margin note after a dash in the heading, paragraphs separated by a blank
line, Greek verses quoted on their own lines separated by ` | `, footnotes as `[Note: ¹ …]`,
run-ons with `+ `. Lists of editions and bibliographies are left out (write `[list of editions
omitted]` as a paragraph where one stood); everything else stays, tables included (as
paragraphs, one row each).

## Starkie's translation (`trans-NN.md`)

* A speech is `@ Speaker` (the name in full as the Greek text has it: Στρεψιάδης becomes
  `@ Strepsiades`; the draft lists the names) and then `N<TAB>text`, N being the Greek line
  where the speech begins, taken from the facing Greek page; a long speech that the facing page
  shows to cross a margin number may be split there into a second `N<TAB>` segment at a sentence
  end. Stage directions in italics are kept in the text in parentheses as printed.
* Structural headings (AGON II, ODE, CATACELEUSMUS) are left out: the Greek text carries the
  sections.
* Check the speaker of every speech and the line numbers of the segments against the facing
  page (its draft is in `pipeline/build/drama-pages/<play>/p-NNNN.md`).

## Checking

From `pipeline/`:

    .venv/bin/python -m anagnosis_pipeline check-drama-prose <play> transcriptions/drama/<play>/notes-NN.md

It checks that the blocks are complete and in page order, the headings well formed and
increasing, the run-on markers consistent, every flag answered, the Greek precomposed with
breathings on initial vowels, and (for the notes) that each heading's number exists in
`texts/<play>/grc.txt` or is noted. Fix what it reports, or explain under notes.

## Before you finish

Read each page's block through once against the column images, above all the Greek accents and
breathings (in small type a rough breathing is easily misread as smooth) and the scholars' names.
Then say in your reply, per page, how many flags you answered, how many words you changed, and
what you changed in the structure.
