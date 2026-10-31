# The plays: checking the Greek text and writing the critical apparatus

This folder holds the page-by-page work on the printed editions of nine plays (see
pipeline/PLAN-drama.md for which edition each play uses). Each play has a folder
(`agamemnon/`, `choephoroi/`, `eumenides/`, `clouds/`, `medea/`, `frogs/`, `bacchae/`,
`alcestis/`, `lysistrata/`) with batch files. The editions are in the public domain; the
transcription is published under CC BY-SA 4.0. `merge-drama <play>` turns the batch files into
`texts/<play>/grc.txt` and `texts/<play>/commentary-<editor>-apparatus.md`.

**The text is already there.** Nobody types the Greek. `drama-pages <play> draft` read every
text page with Tesseract, matched its lines word by word to the Perseus text of the play (a
different edition, which has the words but divides the lyric verses otherwise and reads
differently here and there), numbered the printed verses from that match and checked the
numbers against those printed in the margin. Where everything agreed, the line is taken as
right. Where it did not, the line is **flagged**. Your work on each page:

1. **Check the flagged lines** against the image, and correct the batch file where it is wrong.
2. **Write the apparatus** from the image. Tesseract's reading of it is a help, not a draft: it
   garbles the sigla, the line numbers and small Greek words.

Do not re-read or retype unflagged lines. Do not change anything you have not checked on the
image. Never guess: where something is unreadable, write `[illegible]` and say so under notes.

## Files

For each page `p-0042` (leaf 42 of the scan), in `pipeline/build/drama-pages/<play>/`:

* `p-0042.md`: the check sheet: the flags, line by line; every line of the draft beside
  Tesseract's reading of it; Tesseract's readings of the apparatus.
* `p-0042-lines.png`: the flagged lines cut out of the page, one under another, each labelled
  with its line number. Look here first.
* `p-0042-app-l.png`, `p-0042-app-r.png`: the apparatus block, left and right halves, enlarged
  (they overlap a little). Read the apparatus from these. Where an edition continues the
  apparatus on the facing page (Starkie), that part follows as `-app2-l.png`, `-app2-r.png`.
* `pages/leaf_0042.png`: the whole page, when you need more (the margin numbers, a line that is
  not in the flagged strip, a speaker abbreviation).

**Keep image requests light**: open the lines image and the apparatus halves for each page; open
the whole page only when a flag needs it.

The batch file `pipeline/transcriptions/drama/<play>/batch-NN.md` holds six pages:

```
=== p-0042
--- text
@ Χορός
104	κύριός εἰμι θροεῖν ὅδιον κράτος αἴσιον ἀνδρῶν
105	ἐκτελέων· ἔτι γὰρ θεόθεν καταπνεύει
...
!	(Μυγμός.)
--- apparatus
104	κύριος] κύριον MSS. corr. Pal.
--- notes
104	(optional: what you checked and decided, one remark per line, starting with the line number)
```

The number and the text are separated by a single TAB. Edit the file in place, page by page,
and **save after each page**, so that nothing is lost if you are interrupted.

## The text: what the draft does, and what the flags mean

* Every printed verse is one line of the file. Its number is the traditional number of the
  verse: the number of the Perseus line in which the verse's first word stands. A second
  printed verse that begins in the same Perseus line has a letter (`401a`); a printed verse
  that runs over two or more Perseus lines carries the first number, and the numbers it covers
  are skipped. The margin numbers of the print (every fifth verse, beside the verse where that
  number falls) are the check.
* Speakers are lines `@ Name`, the name as Perseus has it (Χορός, Κλυταιμήστρα), placed where
  the print changes speaker (ΧΟ., ΚΛ. in the margin, or a centred heading such as ΧΟΡΟΣ.).
  A stage direction printed in the text ((Μυγμός.), (ὠγμός.)) is a `!` line with the words as
  printed, brackets included.
* The words, accents and punctuation of a confirmed line are the print's as Perseus spells them;
  capitals from the OCR. Elision is ʼ (U+02BC), never ’ or ᾽; the raised stop is ·; brackets as
  printed (`[ ]`, `⟨ ⟩`, †). An asterisk before a word (Sidgwick's mark of a conjecture) is left
  out. An iota adscript (τῶι, χώραι) is written as the subscript (τῷ, χώρᾳ).
* A word divided at the end of a verse and finished on the next (lyrics: εὐδαί- | μων) is
  written whole at the end of the first verse and left out of the second.

The flags, and what to do:

* **"X: the OCR reads “Y”"**: Perseus and the OCR differ. Look at the crop: if the page prints
  what Perseus has, leave it; if the page prints something else (another word, accent,
  breathing, stop, a bracket), write what the page prints, and say so under notes. Editions
  differ from Perseus often in these plays: a difference is a real reading as often as an OCR
  error. Tesseract confuses ἂν/ἃν, ἡ/ἣ, ὢν/ὧν, smooth and rough breathings, and iota subscripts
  constantly: on these, trust the page only when the crop is clear.
* **"X: not found in the OCR; check it is printed on this line"**, **"which line it stands on
  is a guess"**: check that the word stands on this verse and not the one before or after; move
  it if not. Check too that the verse division is the print's (where the print begins a new
  verse inside our line, split the line with the number rule above; where it joins two of ours,
  join them and note it).
* **"this printed line matched no Perseus words"**: a verse the edition prints that Perseus
  lacks (a restored line, a line Perseus deletes), a stage direction, or OCR noise. Add it with
  the letter number that follows the line before (1329a), or as a `!` line, or remove it; say
  which under notes.
* **"the margin reads N at a line numbered M"**: the numbering may be off here (a verse
  skipped or doubled, a printed number the edition places otherwise). Look at the whole page,
  count from the nearest margin number, and renumber what is wrong: the printed numbering wins;
  lines between two margin numbers run on from the first. Often the margin number was simply
  misread: then nothing is wrong.
* **"a speaker change in the print that Perseus does not have here"** / **"Perseus changes
  speaker here, the print shows none"**: the print wins. Add `@ Name` (the Perseus name of the
  speaker the abbreviation means; the names are listed at the top of the check sheet) or remove
  it, and note it.
* **"a bracketed line: a stage direction?"**: if the print sets it as a direction, make it a
  `!` line; if it is a bracketed verse (deleted by the editor), keep it as a verse with its
  brackets.
* **"Perseus marks a gap"**: copy what the edition prints there (asterisks, a row of dots, a
  note "lacuna") as a `!` line, and note it.

## The apparatus

* One output line per item: the line number it refers to, a TAB, the item. The editions
  print the number at the start of each item (Sidgwick "103. ὅρα δὲ MSS. corr. Pal.", Tucker
  "970 Κῷος Aristarchus in schol.", Sandys "252. οὐκ ἔχον P", Hayley "546 τῷδε d] τῶδε a τῶνδε r."):
  that number, even where it does not match our numbering exactly (say so under notes). An
  item for several lines: `104-105`. A further item on the same line, printed without a number,
  gets the number of the item before it.
* Copy each item as printed: lemma, readings, sigla as printed (M, G, V, Fl., Fa., R, V, P, C, L, B, a, d, r,
  codd., MSS.; later hands and superscripts as Unicode superscripts: M², P¹), scholars' names
  and abbreviations (Pal., Turn., Herm., Dindf., Herwerden), Latin and English words. Greek
  with full accents. Italics are ignored; bold lemmas are written plain (the merge marks them).
  A square bracket after the lemma stays: `κύριος] κύριον`.
* Where the editor says it in words, copy his words. A colon or semicolon is written without a
  space before it. Keep "corr.", "conj.", "om.", "del." as printed.
* An item that runs on from the previous page belongs to the line it names: write it on the
  page where it begins. Leave out signatures and catchwords at the foot of a page.
* Where the text page has no apparatus (an edition that prints critical notes elsewhere), the
  section stays empty, and the first page's notes say "no apparatus on the text pages".

## Each edition's page

**Sidgwick's Aeschylus (Agamemnon, Choephoroi, Eumenides).** The speakers' abbreviations
(ΚΛ., ΧΟ., ΑΓ., ΚΑ., ΚΗ., ΑΙ.) stand in the left margin; a new character's name is printed in
capitals centred above the first speech (ΦΥΛΑΞ.); the margin numbers every fifth verse are at the
right. The labels Sidgwick prints in the right margin of the lyrics (στρ. α΄., ἀντ. β΄., μεσῳδ.,
ἐπῳδ.) are not part of the text: leave them out (the sections come from elsewhere). The scans
are of students' copies: pencil notes in English between and beside the lines, underlinings,
and in the Eumenides writing over the text. Ignore all handwriting; where it hides a word, look
at the whole page, and if the print is still unreadable keep the draft's word and say so under
notes. The apparatus is at the foot of the page, its items begin with the line number and a
stop ("850. πήματος τρέψαι νόσον MSS. corr. Pors."): write `850<TAB>πήματος τρέψαι νόσον MSS.
corr. Pors.`. Items in English ("7. Probably spurious.") are copied as printed. Sidgwick marks
his own and others' conjectures in the text with an asterisk (*καλῶς): leave the asterisk out of
the text (it stays in the apparatus if printed there). Where Perseus has an empty verse (a
lacuna Smyth marks), the draft has nothing; if Sidgwick prints a verse there, add it with the
number of the empty Perseus verse (the check sheet's flags say where).

**Your own files.** Scripts, enlarged crops and other helpers go only in a folder of your own,
named after your batch file, under the session's scratchpad folder (e.g.
`<scratchpad>/agamemnon-notes-03/`); other agents work beside you at the same time and use the
same scratchpad, so never write a file directly in the scratchpad or in another agent's folder.

## Checking

Run, from `pipeline/`:

    .venv/bin/python -m anagnosis_pipeline check-drama-batch <play> transcriptions/drama/<play>/batch-NN.md

It reports numbering that does not run on, apparatus numbers that name a line not on the page,
pages without an apparatus, elision written with ’ or ᾽, divided words, and every place where
the words now differ from Perseus (that is, every change of wording you made: each must be one
the image shows, and noted). It does not see a word moved to another line or a speaker added or
removed: note those yourself. Fix what it reports, or explain under notes.

## Before you finish

For each page: every flag looked at; the apparatus complete, every item with a line number;
the checker run clean or each remark explained. Then say in your reply, for each page, how many
flags you checked, what you changed, and how many apparatus items you wrote.
