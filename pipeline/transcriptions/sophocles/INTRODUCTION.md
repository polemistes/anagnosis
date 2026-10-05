# Jebb's Sophocles: introduction chapters, the ancient argument, persons and structure

Perseus has Jebb's Introduction for most plays but not his chapter on the manuscripts, nor the
ancient argument (ὑπόθεσις), the list of persons and the structure of the play that stand before
the text; for the Oedipus Tyrannus and the Philoctetes it has no introduction at all. These
pages are transcribed into `introduction-NN.md` files in the play's folder, and
`import-sophocles` adds them to `texts/<play>/introduction.md`, a document of the app, after the
chapters from Perseus. Look at `texts/antigone/introduction.md` (its last two chapters) for the
result. The edition is in the public domain; the transcription is published under CC BY-SA 4.0.

All the rules of APPENDIX.md (same folder) hold here: read it first. The differences:

## Headings

* Each chapter begins with `# ` and its title as printed, small capitals written as ordinary
  capitals and small letters: `# Manuscripts, editions, etc.`, `# Introduction`.
* Each numbered section of a chapter (§ 1, § 2 …) begins with a heading `## § 1`, followed, after
  a dash, by the note Jebb prints in the margin beside it if there is one: `## § 3 — Scholia.`
  A margin note beside a later paragraph of the section goes at the start of that paragraph in
  italics: `*Editions.* The complete editions …`.
* The pages before the text: `# The ancient argument` once, then `## The argument` (the
  ὑπόθεσις; with Roman numerals if there are several: `## I. The argument of Aristophanes`, as
  headed in the print), `## The persons of the drama`, `## Structure of the play`.

## The Greek of the argument and the persons

* The Greek text of an argument: paragraphs as printed; leave out the line numbers in its margin.
  The heading in Greek capitals (ΥΠΟΘΕΣΙΣ, ΑΡΙΣΤΟΦΑΝΟΥΣ ΓΡΑΜΜΑΤΙΚΟΥ ΥΠΟΘΕΣΙΣ) begins its
  first paragraph in bold: `**ΥΠΟΘΕΣΙΣ.** Τὸ δρᾶμα …`.
* Jebb's critical notes on it (the small full-width block) follow it as one paragraph beginning
  `*Critical notes.*`, the notes in print order, each with its line number: `*Critical notes.*
  2 **ἐπιγράφουσιν**] So Dindorf with L: vulg. ἐπέγραφον. 4 …`.
* His commentary on it (the two columns below): a paragraph per note, the lemma in bold, as in
  `texts/antigone/introduction.md`: `**ΑΡΙΣΤΟΦΑΝΟΥΣ ΓΡΑΜΜΑΤΙΚΟΥ**] The first of the three …`
  (keep the line number before the lemma if printed: `2 **τύραννον...ἐπιγράφουσιν**] …`).
* The persons: the Greek names as printed, one paragraph, separated by ` · `; Jebb's remarks
  after them (on the actors' parts) as ordinary paragraphs.
* The structure of the play: a paragraph per numbered part, as printed (`1. πρόλογος, verses
  1—133.`).

## Output

One block per page, `=== p-NNNN`, in the file your task names; a paragraph that runs on to the
next page continues there after `+ `, as in APPENDIX.md. Read the file through once against the
images when you have finished, above all the Greek accents and breathings.
