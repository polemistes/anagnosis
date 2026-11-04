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
* For a translation batch (`trans-NN.md`) the crops are named `trans-p-0251-flags.png` and so on.

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

## Each edition's pages

**Sidgwick's Aeschylus (notes and introduction).** The English OCR of these students' copies is
weaker than its flags show (quotation marks read as ¢ “ © *, "l." read as "1." or "11.", Greek
read as Latin letters, lines garbled under pencil underlining): read each page's column image
through once and correct what the print shows, not only the flagged words; ignore all
handwriting. Each note begins "l. 1." / "ll. 1345-51." (heading `## 1`, `## 1345-1351`); bold
(or spaced) Greek is `**…**` wherever Sidgwick prints it, at the head of a note or inside it;
quotation marks are his single ‘ ’ (double “ ” only where he prints them inside). His bracketed
summary that opens a scene or song ("[Prologue. … (ll. 1-39.) …]") is a note of its own headed by
the range it names (`## 1-39`), kept where it is printed, in its brackets, in plain type. A
page that begins with a new indented paragraph of the note before gets no `+ ` (the merge files
it under that note); `+ ` only where a paragraph runs on. Where Sidgwick numbers a note by a
line our text (texts/<play>/grc.txt) numbers otherwise, keep his number and say under notes
which of our lines it is.

**Starkie's Clouds (commentary, introduction, translation).** Clean print, no handwriting.
* *Commentary* (`notes-NN.md`): on every page of the play, in two columns under a rule: on the
  Greek (even) pages under the second rule (above it are the verses and the apparatus, not
  yours), on the translation (odd) pages under the rule below the translation (where a page has
  two rules there, the band between them is the apparatus run on, not yours). A note begins with
  the line number and a stop in bold, then the lemma in bold Greek and a colon ("5. **οἰκέται**:
  schol. V (int.) …"): heading `## 5`, the lemma `**οἰκέται**:`. A further lemma without a
  number ("**οὐκ ἄν**: schol. V …") is a new paragraph under the same heading. Ranges ("1345-1451.
  Agon II.", "119 sq.") become `## 1345-1451`, `## 119`. He quotes the scholia at length in
  Greek, with his signs: keep `[ ]`, `⟨ ⟩` (printed < >), `R`, `V`, `(int.)`, `(ext.)`,
  `Su.`, `cp.`, as printed; references (Ach. 412 n., Kühner-Gerth, Gram. § 398. 4) exactly.
  The draft's structure needs checking on every page: a bold line number misread at a note's
  start ("δ. οἰκέται" for "5. **οἰκέται**") is a missed heading; a number at the start of a
  printed line inside running text ("1265" continuing "cp. 12, 720, | 1265, 1407") made into a
  heading is false: put it back in the text; a sentence that runs from the foot of the left
  column to the top of the right one is one paragraph: join it.
* *Introduction* (`intro-NN.md`): numbered chapters ("I. THE DATE OF THE CLOUDS" → `# I. The
  Date of the Clouds`), sections and footnotes by the introduction rules above; Greek
  quotations of several verses on their own lines with ` | `. The Greek hypotheses (leaves
  101-106) are Greek prose and verse: each hypothesis `# Hypothesis I` and so on, the Greek
  exactly as printed, Starkie's footnotes as `[Note: …]`. The list of persons (leaf 107) as one
  paragraph of names separated by ` · `.
* *Translation* (`trans-NN.md`): one column above the rule on each odd page. Speakers are
  printed in small capitals with a stop at the start of a speech (STREPS., PHID., SOCR., DISC.,
  CHOR., STUD.); the stage directions are in italics in parentheses inside the speeches: keep
  them in parentheses in the text, without the italics marks. The line number of each speech is
  the Greek verse where the speech begins on the facing page (its draft:
  `pipeline/build/drama-pages/clouds/p-NNNN.md`, the page number one less than the translation
  page's); the margin numbers of the facing page fix it.

**Paley's Hesiod (notes on the Theogony, the Epitome).** Clean print, no handwriting. Each
page of the Theogony has, from the top: Paley's Greek text (a few verses), a short rule, a
centred band of his digamma readings ("40. ϝίσασιν"), a band of manuscript readings in small type
("36. δίκῃσιν A. 37. ἐδασσάμεθα K, …"), another short rule, and then his commentary in two
columns. **Only the two columns are yours**; the draft cuts the page under the bands. Where a
line of the bands slipped into the draft (a short centred digamma line, the last line of the
readings), delete it and say so under notes; where the draft lost the first lines of the
columns, add them from the column image.
* A note begins with the line number and a stop: "37. ἤδη μὲν κ.τ.λ. ‘For we had …’" →
  `## 37` and `**ἤδη μὲν κ.τ.λ.**` (Paley prints the lemma in ordinary Greek type; the Greek
  that opens the note, up to its stop, is the lemma all the same, κ.τ.λ. included).
  "40—1." and "40, 41." → `## 40-41`; "116—132." → `## 116-132`. A note with no lemma ("3. The
  combinations …") has none. "Ibid." opening a paragraph begins a further note on the same line:
  a new paragraph under the same heading, "Ibid." kept.
* His references (inf. v. 356, sup. 221, Cf. Il. xi. 270, Opp. 286, Schol., Gaisf., Goettl.,
  Van Lennep, Schoem.) are copied as printed; "Opp." and "Opp." with a line number mean his
  Works and Days. Quotation marks are his ‘ ’, “ ”.
* Where Paley's lemma reads otherwise than Rzach's text (he prints a digamma, ϝ, or another
  reading), copy Paley's Greek as printed; the merge files the note under the line he numbers.
* **Check the structure on every page against the column images**: the draft makes a false
  heading wherever a printed line inside running text begins with a number ("… or with v. |
  74 …" became `## 22-74`, "… tertia usque ad v. | 115 …" became `## 115`): put the number back
  into the text, joined to the paragraph it belongs to. A real note begins a paragraph with the
  number and a stop at the left edge of the column. Check too that the paragraphs stand in the
  print's order (left column top to bottom, then right column) and that a paragraph running
  from the foot of the left column to the top of the right is one paragraph.
* Paley's Greek in small type is often read as Latin letters by Tesseract (kal for καὶ, 6 for ὁ,
  k.T.A. for κ.τ.λ.): correct every such word from the image even if it is not flagged.
* The *Preface* (`intro-NN.md`, pp. v-xliv): heading `# Preface`; Paley's own section headings,
  if any, as `## …`; footnotes `[Note: ¹ …]`; his quotations of Greek verse on their own lines
  with ` | `. Keep his digamma signs as printed (ϝ, written with the Greek digamma, or F where
  he prints a Latin F).
* The *Epitome* (`intro-NN.md`, pp. 167-170): one paragraph per printed paragraph; the ranges
  ("1—115. Introduction. 1—35. The Muses …") stay in the running text with plain hyphens
  (1-115); the essay that follows is ordinary paragraphs; footnotes as `[Note: ¹ …]`. Heading:
  `# Epitome of the Theogony`.

**Your own files.** Scripts, enlarged crops and other helpers go only in a folder of your own,
named after your batch file, under the session's scratchpad folder (e.g.
`<scratchpad>/agamemnon-notes-03/`); other agents work beside you at the same time and use the
same scratchpad, so never write a file directly in the scratchpad or in another agent's folder.

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
