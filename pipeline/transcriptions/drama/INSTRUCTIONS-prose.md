# The plays: the commentaries, introductions, appendices and Starkie's translation, from OCR

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

The batch file (`notes-NN.md`, `intro-NN.md`, `trans-NN.md` or `appendix-NN.md`, eight pages each) has a block
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

**Jerram's Lucian, A True Story (notes and introduction).** C. S. Jerram, *Luciani Vera
Historia*, Oxford 1879, scan `lucianiverahisto00luci`; the batches are in
`pipeline/transcriptions/lucian/truestory/` (`notes-NN.md`, `intro-NN.md`), the crops in
`pipeline/build/drama-prose/truestory/`. Clean print, one column, no handwriting.
* *Notes* (pp. 51-70, leaves 81-100): the page title NOTES is left out; the headings BOOK I. and
  BOOK II. become `# Book I` and `# Book II` (a paragraph of their own). Each note begins with
  the line number of **Jerram's own text** (not ours: the merge maps his lines to our sections),
  printed "Line 4.", "l. 17.", "ll. 26, 27.": heading `## 4`, `## 17`, `## 26-27`; he counts his
  lines afresh in each book. Tesseract reads "l." as 1, I, | or _ and then misses the heading ("1 7.
  σπουδαιοτέρων" is `## 7`, "| 1. 25. Nothing …" is `## 25`): mend every such note from the image,
  and take the number from the print, not from the draft. A further note on the same line without
  a number is a new paragraph under the same heading.
* The lemma: the Greek that opens a note, up to the comma or stop after it, printed in ordinary
  Greek type, is the lemma: `**μέρος γοῦν**, etc., a parenthesis …`, `**ψιλὴν**, etc., …` (the
  "etc." outside the bold). A note that opens in English has none. Where the draft has lost the
  lemma ("## 159 / etc. Lucian has been …"), restore it from the image.
* His references to his own text ("cp. ll. 13, 19, 28", "i. 32", "ii. 87, 438", "l. 170
  onwards") and to other works (Virg. Ecl. vii. 17, Od. vii. 114, Thuc. i. 1, Phaedo, ch. 29) are
  copied as printed; Latin and English quotations set on their own lines are paragraphs of their
  own. Quotation marks are his ‘ ’ (“ ” where he prints them). Greek in Unicode polytonic with
  every accent and breathing (Tesseract misreads ξ as ἐ, χ as x, ι with its accent as 1).
* *Introduction* (pp. ix-xxiii, leaves 15-29): heading `# Introduction`; no numbered sections;
  footnotes `[Note: ¹ …]` after the paragraph where the mark stands; run-ons `+ `; titles of books
  in italics `*…*`. Keep everything, the paragraph on translations and editions included (it is
  prose, not a list).

**Taylor's Shepherd of Hermas (notes, introduction, appendix), and Lake's introduction.**
Charles Taylor, *The Shepherd of Hermas*, Early Church Classics, SPCK, vol. I 1903 (scan
`shepherdofhermas0000herm`), vol. II 1906 (scan `shepherdofhermas02hermuoft`); K. Lake, *The
Apostolic Fathers* II (Loeb 1913, scan `apostolicfathers02lakeuoft`). The batches are in
`pipeline/transcriptions/hermas/` (`notes-NN.md`, `intro-NN.md`). The pages come from more than one
scan, so a page's stem carries the scan's place in the list as its first digit: `p-10061` is leaf
61 of the first scan, `p-20013` leaf 13 of the second. For the notes the first scan is Taylor I and
the second Taylor II; for the introduction the first is Lake, the second Taylor I, the third Taylor
II (`p-30139`). The crops are in a folder per scan, `pipeline/build/drama-prose/hermas/<scan>/`
(`p-10061-flags.png`, `p-10061-col-l.png`, `pages/leaf_0061.png`); the index of the pages is
`pipeline/build/drama-prose/hermas/notes.json` (`intro.json`). Clean print, one column.
* *Taylor's page*: the running head (THE SHEPHERD on the left-hand page, the book on the right:
  FIRST VISION, TWELFTH MANDATE, SECOND SIMILITUDE) and the page number; his **translation**, with
  the book's title where a book begins (FIRST VISION), CHAPTER 2 headings, and **the verse numbers
  in the text** ("2. After a while I saw her bathing"); under it, in small type, his **footnotes**,
  each beginning with a mark (* † ‡ § ‖ ¶) that answers a mark after a word of the translation above.
* *Notes* (`notes-NN.md`): **keep only the footnotes, and leave the translation out** (it is not
  used; delete the draft's paragraphs of translation). Head each footnote with the place of its
  mark in the translation, in the traditional reference: book, chapter, verse, as
  `## Vision 1.1.2`, `## Mandate 4.3.1`, `## Similitude 9.30.2`. The book is the running head's (or
  the title on the page); the chapter is the last CHAPTER heading before the mark (a book without
  CHAPTER headings, as most Mandates and the first Similitudes, is chapter 1: `## Mandate 1.1.3`,
  or, as Taylor prints such places, `## Mandate 1.3`, which the merge reads as chapter 1); the
  verse is the last verse number printed before the mark (the first verse of a chapter, before
  any number is printed, is verse 1). Then the footnote's text as printed, **without its mark**,
  as one paragraph, opened by the English words just before the mark in bold, up to about five
  words from the start of their clause: `**sold me to a lady**: …` (none if the mark stands after
  a heading). Two footnotes on the same verse: the same heading twice is fine, or one heading
  and two paragraphs.
* *Taylor's printing slips*: a wrong or dropped letter that makes no word ("Gosbels", "he Gospel",
  *Mana.* for *Mand.*), and a footnote that ends with a printed comma where nothing follows (worn
  type), are corrected, with a line under `--- notes` saying what is printed; anything
  that could be his own spelling or wording stays as printed.
* A footnote that runs over to the next page: its rest is the first paragraph of the next page's
  block, marked `+ ` (and nothing else on that page is so marked).
* His references (*Sim.* i. 1—3, *Mand.* xi. 18 n., Lev. xxv. 23, Clem. *Strom.* vii. 12, P. 877)
  and Greek, Latin and Hebrew words as printed; italics `*…*`; Greek in Unicode polytonic with
  every accent and breathing, his transliterations in italics as printed (*paroikia*, *xenen*).
* *Introduction* (`intro-NN.md`): first Lake's four pages (p-1…: THE APOSTOLIC FATHERS / THE
  SHEPHERD OF HERMAS heading becomes `# Lake's introduction (1913)`; his list of the manuscripts,
  versions and papyri as paragraphs, one witness each, ℵ written as U+2135, sigla as he prints them:
  L₁, L₂, Pᵃᵐ, Pᵒˣ), then Taylor's (p-2…: the page's title INTRODUCTION becomes
  `# Taylor's introduction (1903)`, his numbered chapters "1. AUTHORSHIP AND DATE." `## 1.
  Authorship and Date`, his lettered parts "A. *Rhoda and the Church.*" `### A. Rhoda and the
  Church`), then Taylor's appendix (p-3…: `# Taylor: Hermas and the Gospels (1906)`, his heading
  APPENDIX left out as part of it; his signature "C. TAYLOR. Cambridge, August 1906." as the last
  paragraph). Footnotes `[Note: * …]` after the paragraph where the mark stands; run-ons `+ `.
  Keep everything, the paragraphs on editions and translations included (they are prose).

## Jebb's Sophocles: the Appendix and the chapters before the text

R. C. Jebb, *Sophocles: The Plays and Fragments* (Cambridge). Perseus has his text, translation,
commentary and most of his introduction; what it lacks is read here: his chapter **Manuscripts,
editions, etc.**, the **pages before the text** (the ancient argument or, for the Trachiniae,
his note in its place; the persons of the drama; the structure of the play), for the Oedipus
Tyrannus **the whole introduction**, and his **Appendix** (longer notes on particular lines, at
the end of the volume). The batches are `pipeline/transcriptions/drama/<play>/intro-NN.md` (the
chapters before the text) and `appendix-NN.md` (the Appendix), the crops in
`pipeline/build/drama-prose/<play>/`. `sophocles-prose <play>` turns the checked batches into
`texts/<play>/introduction.md` (after the chapters from Perseus) and `texts/<play>/appendix.md`;
the result must look exactly like `texts/electra/appendix.md` and the last two chapters of
`texts/electra/introduction.md` (look at them before you start). Everything you need is in this
section; do not open `pipeline/transcriptions/sophocles/` (another route's material).

**Read each page's image through once** (`<stem>-col-l.png`, or `pages/leaf_NNNN.png`), not
only the flagged words: the OCR knows no italics, and it garbles Jebb's italic words (*Trachiniae*
read as "Zrachiniae", *Il.* as "ZZ", *Hist.* as "Aist.") and his old-style figures (1 read as I,
l or ι; 0 as o; 6 as b or 0; "8o f." for "80 f.") without always flagging them. Line and page
numbers, references and Greek must be exactly the print's.

**What the draft already does** (check each, mend what is wrong): it leaves out the running head
(page number, APPENDIX., MANUSCRIPTS, EDITIONS, ETC., ΣΟΦΟΚΛΕΟΥΣ), the signature at the foot and
the large titles APPENDIX. and ΣΟΦΟΚΛΕΟΥΣ ΤΡΑΧΙΝΙΑΙ; it writes the headings below in their forms,
with the section and line numbers as it could read them (often wrongly: take every number from
the image); it puts the margin notes after their section's heading or at the start of their
paragraph; it joins the lines of a paragraph, writes the persons on one line, joins quoted verses
with ` | `, puts an Appendix note's lemma in bold, and marks a paragraph run on from the page before
with `+ `. Flags on words of lines the draft left out (a running head, a title) are answered
`omitted`.

**The Appendix** (`appendix-NN.md`):

* Each note begins with Jebb's line number in bold and, mostly, his lemma. The number becomes a
  heading of its own: `## Line 70`; with "f." or "ff." as printed, `## Line 29 f.`,
  `## Line 853 ff.`; a range with an **en dash** (–), `## Lines 11–14`, `## Lines 1264–1278`.
  Nothing else on the heading line.
* The lemma (the Greek words after the number) goes in bold at the start of the first paragraph,
  its stop inside the bold: `**ἔλειπε.** This imperfect has been explained …`. A lemma that
  stands alone on its line (often a verse or two, set to the right) is a paragraph of its own,
  its verses separated by ` | `: `**νὺξ γὰρ εἰσάγει | καὶ νὺξ ἀπωθεῖ διαδεδεγμένη πόνον.**`.
  English after the Greek, "(So the MSS.)", stays outside the bold. A note with no lemma ("11—14
  As to the coins …") has none.
* A heading inside a note, in capitals or small capitals ("I. NOTE ON THE CONSTRUCTION.", "THE
  ORACLE AT DODONA."), is `### ` and the words in ordinary capitals and small letters, the stop
  kept: `### I. Note on the Construction.` A title printed above a note's number goes **after**
  the note's heading (`## Line 1166`, then `### The Oracle at Dodona.`).
* A numbered list (1. Bothe: … 2. Hermann: …; I. … II. …) is a paragraph per item when each
  item begins a printed line; numbers inside running text stay in it.
* An essay of the Appendix that is not on one line (the Oedipus Tyrannus: "*The Oedipus Tyrannus
  at Harvard.*", in numbered sections "§ 1. *Opening Scene.*") is headed `## ` and its title
  (`## The Oedipus Tyrannus at Harvard`), its sections `### § 1. Opening Scene.`; the line notes
  after it are headed as above. The Oedipus Tyrannus prints a stop after a note's number
  ("1526. οὔ τις …"): the heading is `## Line 1526` all the same.

**The chapters before the text** (`intro-NN.md`):

* A chapter begins with `# ` and its title as printed, small capitals as ordinary capitals and
  small letters: `# Manuscripts, editions, etc.`, `# Introduction`.
* A numbered section (§ 1, § 2 …) begins with a heading `## § 1`; if Jebb prints a note in the
  margin beside the section's first line, it follows after a spaced em dash, as printed with its
  stop: `## § 3 — Scholia.`, `## § 5 — The theory of two recensions.` A margin note beside a later
  paragraph of the section goes at the start of that paragraph in italics: `*Editions.* The
  complete editions …`. Margin notes are small and the OCR garbles them ("of tw oe"): read each
  from the image.
* The pages before the text: `# The ancient argument` once, then `## The argument`, or, where
  Jebb numbers several (the Oedipus Tyrannus: I., II., III.), `## I. The argument`,
  `## II. The argument`, `## III. The argument` (the draft makes these from the numerals), then
  `## The persons of the drama` and `## Structure of the play`. For the Trachiniae, which has no
  ancient argument, Jebb's note in its place ("THE *Trachiniae*, alone among the seven plays, has
  no ancient ὑπόθεσις …") stands under `## The argument`.
* The persons: the Greek names as printed, in one paragraph, separated by ` · `, the left column
  first, then the right: `ΔΗΙΑΝΕΙΡΑ. · ΔΟΥΛΗ ΤΡΟΦΟΣ. · ΥΛΛΟΣ. · …`. The OCR reads these capitals
  as Latin letters (AHIANEIPA): write them in Greek. Jebb's remarks after them (on the persons and
  on the actors' parts) are ordinary paragraphs.
* The structure of the play: a paragraph per numbered part, as printed: `1. πρόλογος, 1—93.`,
  `3. ἐπεισόδιον πρῶτον, 141—496, including a short ὑπόρχημα, or ‘dance-song,’ 205—224.` (ranges
  in the running text keep Jebb's —). Leave out stray pencil marks (~, -) at the ends of lines.
* An argument in Greek (the Oedipus Tyrannus): paragraphs as printed, without the line numbers
  in its margin; its heading in Greek capitals begins its first paragraph in bold:
  `**ΥΠΟΘΕΣΙΣ.** Τὸ δρᾶμα …`. Jebb's critical apparatus on it (the small full-width block)
  follows as one paragraph beginning `*Critical apparatus.*` (our label: never "Critical notes"),
  each note with its line number:
  `*Critical apparatus.* 2 **ἐπιγράφουσιν**] So Dindorf with L: vulg. ἐπέγραφον. 4 …`. His commentary
  on it (the two columns below) is a paragraph per note, the lemma in bold followed by `]`:
  `2 **τύραννον...ἐπιγράφουσιν**] …`. Where the text, the critical notes and the commentary all
  run on to the next page, the text continues there after `+ `, the critical apparatus after
  `+notes `, the commentary after `+comm `, in that order. Each further heading in Greek capitals
  (ΑΛΛΩΣ., ΧΡΗΣΜΟΣ …, ΤΟ ΑΙΝΙΓΜΑ ΤΗΣ ΣΦΙΓΓΟΣ., ΛΥΣΙΣ ΤΟΥ ΑΙΝΙΓΜΑΤΟΣ.) begins its paragraph in
  bold, as the draft writes it (in Greek letters: the OCR reads them as Latin, XPH3MOS). The OCR of
  these Greek pages is weak (accents read as separate marks: `\ ~ ε ’ ’ /`, `Ν ’ 3`): delete
  such debris and read every verse from the image. On these pages the draft does not tell the
  critical apparatus from the commentary (it may wrap the commentary in `[Note: …]`): give
  each its form as above.
* The list of suspected verses ("black list") and other lists of verses in the manuscripts
  chapter are kept, as printed, as one paragraph. A list of editions or of subsidia (the Oedipus
  Tyrannus, "Editions and commentaries", § 12-13) is left out as the general rule says: one
  paragraph `[list of editions omitted]` where it stood; Jebb's prose before and after it stays.
* In the Oedipus Tyrannus the persons are followed by the actors' parts, set as a table with
  braces (OEDIPUS, πρωταγωνιστής. / IOCASTA, PRIEST OF ZEUS, … } δευτεραγωνιστής.): one paragraph
  per actor, the names as printed (small capitals as capitals and small letters), then his Greek
  word: `Oedipus, πρωταγωνιστής.`, `Iocasta, Priest of Zeus, Messenger from the house
  (ἐξάγγελος), Servant of Laïus, δευτεραγωνιστής.`, and so on.

**For both**:

* Paragraphs as printed, separated by a blank line; headings too. A paragraph that runs on to the
  next page stops at the foot; the next page's block begins with `+ ` and the rest (only the
  page's first paragraph may begin so). A word divided between two pages is written whole at the
  end of the first page and left out on the next; a word divided at a line end is written whole
  (a hyphen only in a word that has one, as *man-headed*).
* A footnote (small type at the foot, marked ¹ ² or * †): the mark stays in the text where it
  stands, and the note is a paragraph `[Note: ¹ …]` directly after the paragraph in which its
  mark stands.
* Greek verses quoted on lines of their own: one paragraph, the lines separated by ` | `.
* Jebb's wording, spelling and punctuation exactly; his quotation marks are mostly single ‘ ’
  (the OCR often reads the closing ’ as ” and the opening ‘ as ¢ or ‘ followed by a space:
  check every one); the dash is —. Italics `*…*` wherever he prints italics: titles of books
  (*Adversaria*, *Hist. Numorum*), the abbreviated works he cites (*Il.*, *Od.*, *O. T.*, *Ai.*,
  *Ph.*), Latin words and phrases (*editio princeps*, *ad loc.*, *i.e.*), the italic heads of
  numbered paragraphs (`1. *Site.* Dodona stood …`) and words in italics for emphasis (*after*).
  Small capitals as ordinary capitals: MSS., MS., B.C., A.D., S.W. (the OCR reads them as small
  letters: "mss.", "Ms." become `MSS.`, `MS.`); the figures of a manuscript's page as printed
  (p. 64 B). Sigla as printed: L, L², Lc, V², V³ (superscript figures as ² ³, the OCR reads them
  as ?, *, 2).
* Greek in Unicode polytonic, precomposed, with every breathing and accent; elision ’ (the OCR's
  ᾽ is also accepted and made ’ at the merge). The OCR reads short Greek words in Latin letters
  (yap for γὰρ, ov for οὐ, Tov for τὸν, dpa for ἅμα): correct them wherever they stand.
* "critical notes" stays where Jebb writes it in his prose; it is his wording.
* Check with `check-drama-prose <play> transcriptions/drama/<play>/appendix-NN.md` (or
  `intro-NN.md`): for the Appendix it wants the headings above, increasing line numbers, and each
  line in `texts/<play>/grc.txt` (where it is not, say why under notes: Jebb may number a verse
  otherwise than our text).

## Jebb's Sophocles: the commentary

For the **Philoctetes** Perseus has no commentary, so Jebb's whole commentary (R. C. Jebb,
*Sophocles: The Plays and Fragments, Part IV: The Philoctetes*, second edition, Cambridge 1898;
scan `playsfragmentswi04sophuoft`) is read here. The batches are
`pipeline/transcriptions/drama/philoctetes/notes-NN.md` (eight pages each), the crops in
`pipeline/build/drama-prose/philoctetes/` (`p-0121-flags.png`, `p-0121-col-l.png`,
`p-0121-col-r.png`, `pages/leaf_0121.png`). `sophocles-prose philoctetes` turns the checked
batches into `texts/philoctetes/commentary-jebb.md`, which must look like
`texts/trachiniae/commentary-jebb.md` or `texts/oedipuscoloneus/commentary-jebb.md` (look at a
screenful of one before you start). Everything you need is in this section and in "The notes"
above; do not open `pipeline/transcriptions/sophocles/`.

**The page and what is yours.** Each spread has the Greek verses on the left-hand (even) page
and Jebb's translation on the right-hand (odd) page; under them, full width in small type, the
critical apparatus; then a rule; and **under the rule, on both pages, the commentary in two
columns. Only the commentary under the rule is yours.** The verses, the translation and the
apparatus above the rule belong to other batches: if a line of them slipped into the draft (an
apparatus note such as "1151 πρόσθεν r: πρόσθε L.—", a line of the translation), delete it and
say so under notes. The draft also leaves out the running head (page number, ΣΟΦΟΚΛΕΟΥΣ,
ΦΙΛΟΚΤΗΤΗΣ) and the signature at the foot ("4—2", "15—2"); a flag on such a word is answered
`omitted`.

**The order.** The commentary reads down the left column of the left-hand page, then its right
column, then the left and right columns of the right-hand page, and runs on to the next spread;
the pages stand in the batches in that order (p-0120 left page, p-0121 right page). The draft has
put each page's lines in this order and joined a paragraph that runs from the foot of the left
column to the top of the right one; check it on the column images. A paragraph that runs on from
the page before (also from the left-hand page to the right-hand page of one spread) begins the
page's block with `+ `; a page whose first line is a new, indented paragraph gets no `+ `.

**The notes.**

* A note begins a new, indented paragraph with the verse number in bold, mostly followed by the
  lemma in bold Greek: "**12 f.** **ἀκμὴ** …". The number becomes the heading: `## 12`; "12 f."
  and "12 ff." are `## 12`; a range "50—53" is `## 50-53` (plain hyphen); "1081—1217" over a
  whole lyric part is a note like any other. Nothing else on the heading line.
* The draft took the numbers as the OCR read them and kept a heading only where its number
  follows the last one (not lower, at most 60 higher); **take every number from the image**: the
  bold old-style figures are often misread (1 as I, l or ι; 0 as o; 6 as b; "255 f." as "2555.",
  where the draft has already tried a figure fewer). A heading the draft could not settle is left
  as text at the start of its paragraph ("1760 w…"): make it the heading from the image. A number
  at the start of a printed line inside running text ("Thuc. 4. | 117", "cp. | 1095") is a
  reference, never a heading.
* The lemma: the Greek in bold after the number, in `**…**`; its colon, comma or stop stays
  outside, as does "κ.τ.λ." after it: `**ἔα κακῶς** κ.τ.λ.`, `**πότμος...δαιμόνων**: Ant. 157`.
  The OCR reads bold Greek worst of all: read every lemma from the image.
* **Further lemmas on the same verse** run on inside Jebb's paragraph after a dash: "…the
  repeated σε, cp. *Ant.* 790.—**ἐμᾶς**, Bergk's correction…". As in the other plays' files, each
  such lemma begins a **new paragraph under the same heading**, the dash dropped:
  `**ἐμᾶς**, Bergk's correction…`. The draft has already cut the paragraph at **every** dash
  followed by Greek and put the Greek in bold: check each cut against the image; where the Greek
  after the dash is not bold (a quotation or a word in plain type), join the pieces again with
  the dash (`…the gloss,—κατέχεται…`) and take the bold away. A dash followed by English ("—For
  που, Blaydes gives πω") stays in the paragraph. A further lemma that Jebb begins on a new
  indented line without a number is also a new paragraph under the same heading.
* Bold Greek **inside** a paragraph, not after a dash ("…the bravest of the Greeks.'
  **πατρὸς** is not a gen. of agency"), stays in its paragraph, in bold.
* The OCR reads Jebb's "=" as "--", so the draft may have cut "τολμήστατε=τολμηέστατε" at it:
  join it again with "=". A paragraph that begins indented without a number begins with a bold
  lemma in the draft: take the bold away where the print has none.
* Before the first note Jebb describes the scene ("Scene:—*A lonely place on the N.E. coast of
  Lemnos* …"), and a range note opens each part of the play ("1—134 Prologue. Odysseus tells
  …"): keep the scene as the first paragraph of p-0076 (the merge files it under `## 1-134`, as
  the Trachiniae's) and the range notes as notes (`## 1-134`), in italics where Jebb prints them.
* Jebb's dash is —, in ranges too ("vv. 264—269"; the draft wrote the OCR's -- and --- so);
  only the heading's range has a hyphen.
* Jebb's printed asterisk before a word (his mark of a conjecture: \*θεῶν, \*οὑκ, in the text,
  the commentary, the introduction and the Appendix) is written `\*`: a bare `*` is italics
  markup and would run the italics on to the next asterisk. (`sophocles-prose` also escapes a
  bare `*` directly before a Greek letter that does not close italics.)

**Jebb's references and abbreviations**, copied exactly as printed, italics as printed:
Sophocles' plays *Ai.*, *Ant.*, *El.*, *O. T.*, *O. C.*, *Tr.*, *Ph.* and other works (*Il.*,
*Od.*, Aesch. *Pers.*, Eur. *H. F.*, Ar. *Pax*, Plut. *Mor.*, Thuc. 4. 117, Lys. or. 12 § 23);
"n." is a note: "170 n." his note on v. 170 of this play, "*O. C.* 1019 n." his note in his
Oedipus Coloneus (another volume of the same edition), "cr. n." his critical note (the
apparatus); "see Appendix" is the Appendix of this volume, "Introd." his introduction; cp., sc.,
*i.e.*, *v. l.*, schol., Herm. (Hermann), Nauck, Blaydes, Bergk, Wecklein as printed. Small
capitals as ordinary capitals (MSS., MS., B.C.; the OCR reads "Mss."): `MSS.`. Sigla as printed
(L, A, r, L², V³). Quotation marks are mostly his single ‘ ’ (the OCR reads ’ as ” and ‘ as ¢:
check every one). Metrical schemes in the signs he prints (– ⏑ ×).

**Greek**: Unicode polytonic, precomposed, every breathing and accent; elision ’ (the OCR's ᾽ is
accepted and made ’ at the merge). Jebb quotes much Greek in his notes; the OCR reads short Greek
words in Latin letters (yap γὰρ, ov οὐ, Tov τὸν, kal καί) and garbles bold Greek: correct every
such word you see, flagged or not, but do not retype Greek that is right. **Read each column
image through once**, as for the Appendix: the OCR knows no italics, and the figures of verse
references must be exactly the print's.

**Check** with `check-drama-prose philoctetes transcriptions/drama/philoctetes/notes-NN.md`: it
wants `## N` or `## N-M` headings, rising numbers, each in `texts/philoctetes/grc.txt` (where Jebb
numbers a verse our text lacks, which happens in the lyrics, keep his number and say under notes
"## 1100: Jebb's number; our text has no 1100"), every flag answered, `+ ` only at a page's start.

## Earle's Medea: the commentary and the introduction

M. L. Earle, *The Medea of Euripides*, New York, American Book Company, 1904 (scan
`cu31924079583609`). The play's Greek text and apparatus in the app are another edition's
(Gilbert Murray's Oxford text); Earle supplies the **commentary** (`notes-NN.md`) and the
**introduction** (`intro-NN.md`). The play is **private until 2028-01-01**
(pipeline/PLAN-euripides.md): its batch files live in `private/` (the play's folder under
`pipeline/transcriptions/drama/` is a link into it). Never copy anything of these batches, or
of Murray's pages, into another file, a message to another agent, or anything outside the batch
file and your own scratch folder. Everything you need is in this section and in "The notes" and
"The introduction" above.

**Earle's page (the notes).** At the top the running head and page number; then Earle's own
Greek verses in large type with his margin numbers (**not yours**: they are his edition's text,
which is not used); then, **without a rule**, his commentary in smaller type in **two columns**.
Only the commentary is yours. The draft took everything under the verses (the crops are
`pipeline/build/drama-prose/medea/p-0140-flags.png`, `p-0140-col-l.png`, `p-0140-col-r.png`, the
page `pages/leaf_0140.png`); if a verse, a margin number or the printer's signature at the foot
of a left column ("MEDEA — 13") slipped in, delete it and say so under notes; if the first
line of a column is missing, add it from the image. The order is the left column top to bottom,
then the right column, then the next page; a paragraph running from the foot of the left column
to the top of the right one is one paragraph (the draft joined them: check); a note running on
from the page before begins the page's block with `+ `.

**Notes run on inside paragraphs.** Earle does not begin each note on a new line. A note begins
with the verse number in **bold old-style figures and a stop**, followed by the lemma in bold
Greek and a spaced colon, or by English: "**458.** **τυράννους** : apparently with the same
reference as βασιλέων, v. 455." — "**452.** The prolepsis is like that in v. 447." The number
may stand at the start of an indented paragraph, at the start of a line, or **in the middle of
a line after a sentence** ("… where we have ὡς with οὐδέν. **453.** Of course the μέν clause …").
Forms: "21 f." and "21 ff." → `## 21`; "455–458." → `## 455-458` (plain hyphen); "Vv. 1–48."
(a note on a whole scene) → `## 1-48`. The draft cut the paragraph before every such number and
made it the heading; it kept only numbers that rise through the commentary, so:
* **Take every heading's number from the image.** Old-style figures are misread: 1 as I or l,
  3/8, 0/9 or o, 2 as "ἡ" or "z", the bold "f." as "£." or "1."; the draft has tried such
  readings. A bold number the draft left in the text (it could not fit it into the sequence)
  becomes a heading: cut the paragraph there. A number the draft made a heading that is not
  bold in the print (a reference: "v. 450.", "cp. 1345 f.", "Pyth. 4. 209", "Il. 9. 63.") goes
  back into the text where it stood, joined to its paragraph.
* **Earle's order is his text's order.** Where his text moves verses (p-0111/0112 and
  p-0200/0201 at least) his notes go back in number (… 217, 222, 223, 224, then 219–221 …): keep
  his order and his numbers; `check-drama-prose` then says "note N comes after M": write under
  notes "Earle's order (his text moves the verses)".
* **The lemma** is the bold Greek after the number, ending at his spaced colon (or at the first
  plain word): write `**τυράννους**:` (colon outside the bold, no space before it). A lemma may
  bridge a gap with dots: `**ἀμφιλόγους . . . νείκη**:`. Where the print sets two bold
  stretches with plain words between ("**αἰθερία** (= πρὸς αἰθέρα) **ἀνέπτα** :", "**πατρὸς
  δόμοι** and **λέκτρων δόμοισιν** are contrasted"), bold each as printed (the draft bolds only
  the first). A note that begins in English has no lemma.
* **Further lemmas on the same verse** follow a dash inside the note: "… with the gen. —
  **τοιγάρ** : *i.e.* …". As in every play's commentary, each begins a **new paragraph under
  the same heading**, the dash dropped: `**τοιγάρ**: *i.e.* ἐπεὶ …`. The draft cut at every dash
  followed by Greek and bolded the Greek: check each cut on the image; where the Greek after the
  dash is not bold (a quotation), join the pieces again with " — " and take the bold away.
  Where the OCR read the bold Greek after a dash in Latin letters, the draft could not cut: do it
  yourself ("— obras : aeque" is "— **οὕτως** : aeque"; "—alel δ᾽" is "**αἰεὶ δ᾽**";
  "—"Apyois σκάφος" is "**Ἀργοῦς σκάφος**"). A dash followed by English ("— The dramatic
  excellence of this πρόλογος …") stays in its paragraph as " — ".
* Earle's dash is spaced: " — ". His quotation marks are single ‘ ’ (double “ ” for a quotation
  inside a quotation and for some longer quotations): the OCR reads ‘ as ¢ (the draft has
  changed those) and ’ as ” or ’: check them. Verses he quotes run on in his text with " | "
  between them, as printed.

**His abbreviations and references**, copied as printed: v., vv., cp., cf., sc., *i.e.*, *e.g.*
(italic; the OCR reads *i.e.* as "2.6.", "Ze.", "Z.e.": the draft has made most of them
`*i.e.*`), κτέ. (his "etc." after Greek), Introd. (his introduction, by page: "Introd. p. 34"),
"see on v. 3 f." (his note on 3), Schol. (the scholia), Mss.; the grammars HA. (Hadley-Allen),
G. (Goodwin), GMT. (Goodwin's Moods and Tenses), with their section numbers ("HA. 871 a, G. 1513,
GMT. 734"); L. and S. (Liddell and Scott). Other plays and authors with italic titles: *Alc.*,
*Hipp.*, *Androm.*, *Heracl.*, *Hec.*, *I.T.*, *Suppl.*, *Bacch.*, Soph. *Ant.*, *El.*, *O.C.*,
Aesch., Aristoph. *Ach.*, *Clouds*, Hdt., Thuc., Plato's *Protagoras*, Hesiod *Op.*; Homer by
the book's Greek letter (ε 264, Ω 545: the OCR reads Ω as Q). Latin and German quoted in
italics (*aeque*, *qui facit per alium facit per se*, *Griechenland*), names as printed
(Hölderlin, Wecklein, Verrall, Headlam). The OCR knows no italics: **read each column image
through once** and set the italics (`*…*`) where Earle prints them, as for the Philoctetes.

**Greek**: Unicode polytonic, precomposed, every breathing and accent; elision ’ (the OCR's ᾽
is accepted). The OCR reads short Greek words in Latin letters and does **not** always flag them
("sc. poi" for sc. μοί, kal for καί, yap for γάρ, ols for οἷς): correct every such word you see
on the read-through; do not retype Greek that is right.

**Headings that our text lacks.** Earle numbers some lyric verses otherwise than the play's
text in the app (`texts/medea/grc.txt`): keep Earle's number; `check-drama-prose` says "no
line N": write under notes "## 134: Earle's number; our text has no 134" (the merge files the
note under the nearest earlier verse with "[134]" in front).

**The introduction (`intro-NN.md`)** holds four parts, in the order of their page names (the
first figure after `p-` is the part; the crops are in `pipeline/build/drama-prose/medea/<scan>/`,
`p-10014-flags.png` and so on, the page in that folder's `pages/leaf_0014.png`):

1. **Earle's Introduction** (`p-1…`, his pp. 7-64, scan `cu31924079583609`). The title
   INTRODUCTION → `# Introduction`; his chapter titles in capitals (EURIPIDES'S LIFE, THE MEDEA
   and the others) → `# Euripides's Life` (capitals and small letters, apostrophe as printed).
   He numbers his paragraphs through the whole introduction ("**1.** Of the facts of
   Euripides's personal life …"): each is a section `## § 1` (the draft has done this where it
   saw the number; the numbers run on across chapters; `check-drama-prose` checks the sequence).
   **His notes in the margin** (small bold words in a space beside two or three shortened lines,
   at the outer edge: "Sources", "Birth and death", "Parentage"): after a dash in the section's
   heading, `## § 2 — Birth and death`; a margin note beside a paragraph that opens no section
   in italics at the paragraph's start, `*Parentage* …`. The draft has taken out the margin notes
   it found: check every one against the page (the OCR reads "Birth" as "girth"; a margin word
   left inside a sentence must be moved out of it; a note's words split between lines joined).
   Verses he quotes (Greek, Latin, English, French) are set in: one paragraph, the printed lines
   separated by " | " (the draft has done this; check where a quotation begins and ends; the
   accents of Greek verses that Tesseract read as a line of their own are dropped, the rest of
   such noise you delete). The English translations he prints after them are ordinary
   paragraphs. His bracketed **bibliographies** at the end of chapters ("[BIBLIOGRAPHY. — …]"):
   left out by the brief's rule, each replaced by the paragraph `[Bibliography omitted]`. A
   table (the plays with their dates) as paragraphs, one row each. Footnotes `[Note: …]`. The
   printer's signature at the foot ("MEDEA — 3") is left out.
2. **The ancient hypotheses in Murray's edition** (`p-2…`, scan `euripidisfabulae01euriuoft`,
   leaves 102-103: the half-title, then the hypotheses in Greek prose with line numbers in the
   left margin and Murray's Latin apparatus in small type at the foot). Write: on the first page
   `# The ancient hypotheses`; each hypothesis `## ` and its heading as printed (Greek
   capitals, in brackets where printed); its Greek as one paragraph per printed paragraph,
   without the margin line numbers, exactly as printed (brackets, daggers, sigla in the text);
   then the apparatus of that page as one paragraph beginning `*Critical apparatus.* `, its
   items with Murray's line numbers as printed and in the form the play's apparatus uses
   (INSTRUCTIONS-text.md, "Murray's Euripides": his sigla, hands, Σ). The draft has given the
   foot's small type as `[Note: …]` paragraphs and the margin numbers inside the Greek: rewrite
   both. Murray's half-title (the play's name) is left out.
3. **Earle's notes on the hypothesis** (`p-3…`, scan `cu31924079583609`, leaves 73-78, his
   pp. 66-71). Each page has Earle's Greek of the hypothesis at the top (not used, and left out
   by the draft) and his notes under it in two columns, run on as in the commentary. On the first
   page begin with `## Earle's notes on the hypothesis (by the lines of his printing)`. Each note
   is a paragraph that begins with his line number and stop, then the bold lemma: `8.
   **δρακόντων πτερωτῶν**: *i.e.* drawn by them.` (the draft has made such paragraphs where it
   saw a number); a further lemma after a dash is a paragraph of its own without a number. His
   line numbers are those of his own printing of the hypothesis: keep them as printed.
4. **The persons of the drama in Murray's edition** (`p-4…`, leaf 104): `# The persons of the
   drama`; the names in one paragraph separated by " · " as printed (Greek, in the case
   printed); Murray's note under the list (Latin: the first performance and the codices) as one
   paragraph, exactly as printed.

Check with `check-drama-prose medea transcriptions/drama/medea/intro-NN.md` as for the notes.

## Hayley's Alcestis: the commentary and the introduction

H. W. Hayley, *The Alcestis of Euripides*, Boston, Ginn & Company, 1898 (scan
`alcestisofeuripi00euriuoft`). As for the Medea, the play's Greek text and apparatus in the app
are Gilbert Murray's; Hayley supplies the **commentary** (`notes-NN.md`, his "Critical and
Exegetical Notes" at the back of his book, pp. 61-167) and the **introduction** (`intro-NN.md`).
His own Greek text, apparatus, select conjectures and metrical appendix are not used. The play is
**private until 2028-01-01**: what "Earle's Medea" says above about private files holds here word
for word (the batches live in `private/`; nothing of them, or of Murray's pages, goes anywhere but
the batch file and your own scratch folder).

**Hayley's notes page.** One column, clean print, no handwriting. At the top the running head
CRITICAL AND EXEGETICAL NOTES and the page number (left out by the draft). Every note is an
**indented paragraph opened by the verse number in bold figures and a stop**: "**2.**", "**28-37.**"
(printed with an en dash: `## 28-37`), "**700 f.**" and "**1132 ff.**" (`## 700`, `## 1132`); his first
note is headed "Verse 1." (`## 1`). Then, mostly, the **lemma in bold Greek with a spaced colon**
("**φλόγα** : here unqualified …"): write `**φλόγα**: here …` (colon outside the bold, no space
before it). A note may begin in English ("**8.** Wakefield and Earle read …"): no lemma.
* **Further lemmas run on inside the paragraph.** Hayley does not start a new line for a further
  lemma on the same verse: "… so *El.* 205 θῆσσαν ἑστίαν. **αἰνέσαι** : Schol. …". As in every
  play's commentary, each further lemma **begins a new paragraph under the same heading**. The
  draft cut the paragraph wherever a sentence ended and Greek followed before a colon, and bolded
  that Greek: check every cut on the image. **Only what the print sets in the bold lemma type is
  bold** (a heavier, plainer Greek face than the Greek of his quotations): where the cut Greek is
  in the ordinary Greek type (a quotation, or the opening words of the play quoted inside his note
  on verse 1), take the bold away and join the pieces again into one paragraph. Where the print
  has a bold lemma the draft did not cut (it is followed by a comma or by English instead of a
  colon: "**τοῖς μὴ θέλουσι**, “any who are unwilling” …", "**πλείω** will then mean …", or its Greek
  was read in Latin letters), cut it yourself. A lemma may bridge a gap with dots:
  `**εἰ τὴν παροῦσαν . . . γυναῖχ’**:` (dots as printed, spaced).
* **Take every heading's number from the image.** A bold number the draft left in the text
  becomes a heading; a number the draft made a heading that is not a bold number at the start of
  an indented paragraph goes back into its paragraph. Hayley's notes go back a little in places
  (a range note after the single notes it covers, "**1132 ff.**" after 1140; "**381.**" after 384): keep his
  order and his numbers; `check-drama-prose` then says "note N comes after M": write under notes
  "Hayley's order".
* **Critical and exegetical notes are mixed**; keep them all, his discussion of readings and
  manuscripts included (sigla in italics as printed: *B*, *L*, *P*, *a*, *b*; "MSS.", "Sel.
  Conj." for his Select Conjectures, "App. Crit." for his apparatus: copy as printed). His bracketed
  list of the editions he cites the other dramatists from, at the head of the first page, is left
  out (the draft has dropped it).
* **His references**, copied as printed: plays in italics (*El.*, *Hippol.*, *Or.*, *Phoen.*, *Hec.*,
  Soph. *Aj.*, *O. C.*, Aristoph. *Thesm.*, *Nub.*), the grammars (Goodwin *M. and T.* 38, Kühner,
  G.), scholars and their works with their titles in italics (Wecklein, Prinz, Nauck *Eur. Stud.*,
  Kviçala, Earle, Weil, Monk, Wuestemann). German, Latin and French quotations are frequent and
  long: read them on the image; the OCR loses umlauts and ç ("niichtern" is "nüchtern", "Kvigala"
  "Kviçala") and garbles quotation marks (he uses “ ” for quotations and ‘ ’ inside them or for
  a meaning: check every one). **Homer**: Hayley cites the books by **roman numerals with a
  stop** (*Il.* XXII. 386, *Od.* XI. 253), in Latin letters; the OCR reads them now as Greek
  capitals ("ΧΙ.") or garbles them ("XVIIL" for XVIII, "1." for I.): write the Latin numeral as
  printed (`check-drama-prose` reports a run of Greek Ι/Χ standing as such a numeral). Where a
  book of Homer is cited by its **letter** instead (a quotation from another scholar, a note of
  Earle's kind: Α 282, ε 264), the letter is **Greek**, never a Latin look-alike (A, B, E, Z, H, I,
  K, M, N, O, P, T, Y, X; Ω read as Q); `check-drama-prose` reports a Latin capital standing as a
  book letter after Hom., Il. or Od.
* The OCR joins a word divided at a line's end even where the hyphen belongs to it
  ("palacedoor" for "palace-door"): put the hyphen back where the print has a compound. "?" is
  sometimes read as ὃ, "El." as "Kl.", "so" as "50", "I" as "1": the read-through finds them.
* His footnotes (a few pages, marked *) are written `[Note: * …]` after the paragraph where the
  mark stands.

**The introduction (`intro-NN.md`)** holds three parts, in the order of their page names (the
crops in `pipeline/build/drama-prose/alcestis/<scan>/`, `p-10021-flags.png` and so on):

1. **Hayley's Introduction** (`p-1…`, pp. xi-lxxxv, scan `alcestisofeuripi00euriuoft`). One column,
   footnotes marked * (`[Note: * …]`). Headings: the title INTRODUCTION → `# Introduction`; his
   lettered chapters → `# A. The Myth of Alcestis`, `# B. The Euripidean Play`, `# C. The Critical
   Basis for the Text`, `# D. Questions Concerning the Scenic Representation of the Play`,
   `# E. The Myth of Alcestis in Ancient Art` (capitals and small letters as in these examples);
   the italic subtitle under a chapter ("Its History and Literary Treatment.", "The Manuscripts,
   Scholia, Editions, etc.") and the numbered parts of D (I., II., III.) → `## …` (no stop at the
   end). Chapter E is by James M. Paton: the line under its title (BY JAMES M. PATON, PH.D.) is
   the paragraph `By James M. Paton, Ph.D.` The draft has made the headings: check them (the
   OCR garbles his small capitals: "Tue EuripipEaN Pray" is THE EURIPIDEAN PLAY). **Left out**:
   the list of essays on the nature of the play that ends chapter B (from "I append a partial
   list of the essays" on p-10042 to "… unable to consult at first hand." on p-10043; the draft
   has written `[Bibliography omitted]` at the head of p-10043); the list of editions,
   translations and critical essays in chapter C (from "The editions
   of the Alcestis are very numerous" on p-10053 to "… Dobree, *Adversaria Critica* …" on p-10058;
   the draft has left it out and written `[list of editions omitted]` at the head of p-10058:
   check that nothing of the list is left and nothing else is lost; the prose on the scholia
   before it on p-10053 stays), and his chapter F with his own Greek of the hypotheses (p-10095
   from its heading on; the draft has left it out: Murray's hypotheses follow instead). Greek
   verses he quotes on lines of their own (chapter A) are one paragraph with " | " between the
   printed lines. **Kept, though dense**: in chapter C the table of the variants of *L* and *P*
   in the first 300 lines (from the foot of p-10047 over p-10048 into p-10049; two columns, "26
   συμμέτρως *L*, | σύμμετρος *P*."): one paragraph per printed row, the two columns in one line as
   printed (`26 συμμέτρως *L*, σύμμετρος *P*.`, the first row with its "v."), read row by row from the image (the OCR
   of this table is poor and partly out of order: rewrite it, do not mend it).
2. **The ancient hypotheses in Murray's edition** (`p-2…`, scan `euripidisfabulae01euriuoft`,
   leaves 54-55): exactly as part 2 of the Medea's introduction above (`# The ancient
   hypotheses`; each hypothesis `## ` with its heading as printed, in Greek capitals and in
   brackets where printed; its Greek one paragraph per printed paragraph, without the margin line
   numbers; then the page's apparatus as one paragraph beginning `*Critical apparatus.* `, in the
   form INSTRUCTIONS-text.md, "Murray's Euripides", gives). These two pages are **dense Greek and
   Latin in small type: read them from the page image line by line**, not from the draft (which
   gives the foot's small type as `[Note: …]` paragraphs and the margin numbers inside the Greek,
   and garbles the headings); the flags are only a help. Murray's half-title (the play's name) is
   left out.
3. **The persons of the drama in Murray's edition** (`p-3…`, leaf 56): `# The persons of the
   drama`; the names in one paragraph separated by " · ", **read down each column** of the list as
   printed (the left column top to bottom, then the right one; not across the columns: that
   mistake was made on the Medea's page), in the printed capitals; then, each as a paragraph of
   its own and exactly as printed, read from the image: the line of Greek in ordinary type under
   the names; Murray's note on the list in small type (Latin with Greek words and sigla, in the
   form INSTRUCTIONS-text.md gives for his apparatus: hands as superscripts, the small letters of
   the later hands, Σ); and his note at the foot of the page (the year of the performance and the
   codices). No `*Critical apparatus.*` label on this page (as the Medea's).

Check with `check-drama-prose alcestis transcriptions/drama/alcestis/notes-NN.md` (or `intro-NN.md`).

## Your own files

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
