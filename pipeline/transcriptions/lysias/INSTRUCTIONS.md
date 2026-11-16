# Checking Hude's Lysias: the Greek text and the critical apparatus

This folder holds the page-by-page transcription of the thirty-four speeches of Lysias in Karl
Hude's Oxford text (*Lysiae orationes*, Oxford Classical Texts, 1912), from the Internet Archive
scan `orationesrecogno00lysi` (leaves 19–287): the Greek text line by line, and Hude's critical
apparatus. `merge-lysias` turns the batch files into `texts/lysias/grc.txt` (one line per
section, 12.7 = speech 12, § 7) and `texts/lysias/commentary-hude-apparatus.md`. The edition is in
the public domain; the transcription is published under CC BY-SA 4.0. The brief for the whole
text is `pipeline/PLAN-lysias.md`.

**What ships is Hude's text with Hude's apparatus. Nothing of any other edition's Greek ships.**
The text is not typed: `hude-pages lysias draft` read every page with Tesseract and matched its
lines word by word to the Perseus text of the speeches. That text is **Lamb's Loeb (1930), a
different edition** ("the check text"): it has the same words almost everywhere, but not all
(Lamb adopts other conjectures, brackets other words, punctuates and capitalises in his own
way). Where the OCR and the check text agreed, the line is taken as right. Where they did not,
the line is **flagged**. Your work on each page:

1. **Check the flagged lines** against the image and correct the batch file where it is wrong.
   **Hude's page wins every time**: where the page prints another word, spelling, accent, stop
   or bracket than the check text, write what the page prints.
2. **Write the apparatus** from the image. Tesseract's reading of it is a help, not a draft: it
   garbles the sigla, the line numbers and small Greek words.

Do not re-read or retype unflagged lines. Do not change anything you have not checked on the
image. Never guess: where something is unreadable, write `[illegible]` and say so under notes.
An evident misprint of Hude's is **copied as printed** and noted (`28.7	misprint: σκοκῶν for
σκοπῶν, as printed`); it is corrected later, by rule, with a note in the apparatus.

## Files

Hude prints no page numbers, so a page is named by its leaf in the scan: `p-0028` is leaf 28. For
each page, in `pipeline/build/hude-pages/lysias/`:

* `p-0028.md`: the check sheet: the flags, line by line; every line of the draft beside
  Tesseract's reading of it and the margin numbers found beside it; Tesseract's two readings of
  the apparatus.
* `p-0028-lines.png`: the flagged lines cut out of the page, one under another, each labelled
  with its key. Look here first.
* `p-0028-app-l.png`, `p-0028-app-r.png`: the apparatus, left and right halves, enlarged (they
  overlap a little in the middle). Read the apparatus from these.
* `pages/leaf_0028.png`: the whole page (2300 pixels wide), when you need more: the margin
  numbers, a line that is not in the flagged strip, an indentation.

**Keep image requests light**: open the lines image and the two apparatus halves for each page;
open the whole page only when a flag needs it (crop the part you need rather than opening all of
it, where you can).

The batch file `pipeline/transcriptions/lysias/batch-NN.md` holds six pages:

```
=== p-0028
--- text
28.1	τῶν ἐσομένων ἐκείνῃ τῇ νυκτί, οὓς οἷός τε ἦ παρέλαβον. Καί
28.2	μοι ἀνάβητε τούτων μάρτυρες.
28.3	[label] ΜΑΡΤΥΡΕΣ.
¶
28.4	§1.43 Τῶν μὲν μαρτύρων ἀκηκόατε, ὦ ἄνδρες· σκέψασθε δὲ
28.5	παρʼ ὑμῖν αὐτοῖς οὕτως περὶ τούτου τοῦ πράγματος, ζητοῦντες
...
28.7	ταύτης. §1.44 οὐδεμίαν γὰρ εὑρήσετε. οὔτε γὰρ συκοφαντῶν
--- apparatus
1	ἦν L
10	⟨ἂν⟩ αὐτὸν Francken
11	διαπραξαίμην Lipsius: διεπραξάμην L
11	ποθεν Emperius: μὲν L (om. P, del. Mᶜ)
--- notes
28.7	(optional: what you checked and decided, one remark per line, starting with the key)
```

The key and the text are separated by a single TAB. Edit the file in place, page by page, and
**save after each page**, so that nothing is lost if you are interrupted.

## Hude's page

* At the top the running head (a Stephanus page in square brackets, ΛΥΣΙΟΥ or the speech's short
  title, the speech's number): not text.
* The text, 27 or 28 lines on a full page. **Line numbers** every fifth line (5, 10, 15 …),
  beginning anew on every page, in the **inner** margin: at the **left** on a right-hand page (an
  odd leaf: p-0019, p-0021), at the **right** on a left-hand page (an even leaf). **Section
  numbers** in the **outer** margin, beside the line in which the section begins. In the outer
  margin too, in square brackets, the **Stephanus pages** ([92], [93]): they are not recorded;
  where one falls on the same line as a section number, the section number is set a little above
  or below it. The check sheet names the side for each page. Hude's figures are old-style (the 1
  looks like a small capital I, 3 4 5 7 9 hang below the line).
* The apparatus at the foot in small type (no rule above it), keyed by line number.
* At the foot of some pages a printer's signature ("LYS. 1", "1*", "2"): leave it out.
* **A speech begins on a fresh page**, lower down, without a running head: its number as a Roman
  numeral, then its title in capitals on one to three lines. These are **not counted as lines**.
  The draft writes each printed line of them as `[title]<TAB>…` (no key): `[title]	I`,
  `[title]	ΥΠΕΡ ΤΟΥ ΕΡΑΤΟΣΘΕΝΟΥΣ ΦΟΝΟΥ`, `[title]	ΑΠΟΛΟΓΙΑ`. The numeral comes from the speech's
  number, not from the OCR; the title's letters are Tesseract's and often wrong. Correct them to
  the print: capitals without accents or breathings, exactly the words of each printed line,
  brackets and stops as printed, a word divided at the line's end as printed (with its hyphen:
  a title is copied line by line), the numeral in Latin capitals (I, V, X). If the draft has no
  numeral line, add it as the first `[title]` line. "Steph." and the bracketed number beside the
  title of speech 1 are not part of it.
* **Speeches 32, 33 and 34** have, under the title, the heading ΥΠΟΘΕΣΙΣ ΔΙΟΝΥΣΙΟΥ. (a `[title]`
  line, not counted) and Dionysius's hypothesis in smaller type, whose lines **are counted**.
  The check text does not have the hypothesis, so the draft holds only Tesseract's reading of
  it: **type every line of the hypothesis from the image**, keeping `[hypothesis] ` after the TAB
  (`284.1	[hypothesis] Τοῦ δήμου κατελθόντος ἐκ Πειραιῶς καὶ ψηφισαμένου διαλύσασθαι`). The
  speech's first section follows it (`§34.1`).

## The text: what the draft does, and what the flags mean

* **The key** is `leaf.line`: the page's leaf and the line's place on the page, counted from the
  top of the text. Lines run 1, 2, 3 … on every page without a gap. **Counted**: every line of
  the text, every line of a hypothesis, and every heading inside a speech. **Not counted**: the
  running head, a speech's number and title, ΥΠΟΘΕΣΙΣ ΔΙΟΝΥΣΙΟΥ. Hude's margin numbers are the
  check: the 5 must stand beside line 5 by your count.
* **A word divided at the end of a line is written whole on the line where it begins**, and
  left out of the next line (`ἐπε-` / `χείρησεν` → `ἐπεχείρησεν` at the end of the first line).
  Only when the second line would be left without a word of its own does the whole word stand
  there. Across a page break likewise: the whole word at the foot of the first page.
* **`§1.44`** (speech.section) stands, followed by a space, before the word where a section
  begins: at the start of the line or inside it (`ταύτης. §1.44 οὐδεμίαν γὰρ`). The draft puts it
  where the check text begins the section. **Hude's number in the outer margin is the
  authority for the line**: the mark belongs on the line beside which his number stands (where
  the number is set above or below a Stephanus page, the line of the two it belongs to is the
  one the check text's section begins on, if that is one of them).
  * If the check text's word stands on Hude's line, **leave the mark where it is** (also where
    that is after a comma: Hude marks the line, not the word).
  * If Hude's number stands beside another line (about one section in twelve, more in some speeches: Lamb begins many
    sections a line or two earlier or later), **move the mark to Hude's line**: before the first
    word after a full stop, raised stop or question mark inside that line (Hude leaves a wider
    space after a full stop); if the line has none, after a comma inside it; if it has no stop
    inside it at all, before its first word. Note it (`22.4	§1.16 moved to Hude's line, after
    the full stop; the check text begins it at ὁ γὰρ on 22.6`).
  * Every section of a speech once, in order, the speech's first being `§N.1` on its first line
    (Hude prints a 1 beside it). Where Hude's numbers differ from the check text's (he prints a
    passage in another place, or leaves one out), **number the sections as his margin does** and
    note it.
* **A new paragraph** (a line Hude indents) has a line with only `¶` before it. A speech's first
  line is indented: it has one.
* **A heading inside a speech** (ΜΑΡΤΥΡΕΣ. ΜΑΡΤΥΡΙΑ. ΝΟΜΟΣ. ΝΟΜΟΙ. ΨΗΦΙΣΜΑ. ΟΡΚΟΙ. and the
  like, centred, in small capitals, with its full stop) is a line of its own, **counted**, written
  `28.3<TAB>[label] ΜΑΡΤΥΡΕΣ.`: capitals without accents, as printed, brackets as printed
  (`[label] ⟨ΜΑΡΤΥΡΕΣ.⟩`). No `¶` before a heading; a section mark never stands on a heading's
  line but before the first word after it. The check text has most of these headings but not
  always where Hude prints them: follow the print (delete a `[label]` line that is not printed,
  add one that is, and renumber the page's lines).
* **Spelling and signs as Hude prints them**: elision ʼ (U+02BC), never ’ or ' or ᾽; the raised
  stop ·; the question mark ;; the iota subscript as he prints it. **Quotation marks**: Hude sets
  direct speech in single marks: write ‘ (U+2018) where one opens and ’ (U+2019) where one
  closes (`ἀπιέναι, ‘ἵνα σύ γε’ ἔφη ‘πειρᾷς ἐνταῦθα τὴν παιδίσκην·`); do not confuse the closing
  mark with the elision sign (`ἔστι δʼ’ ἔφη`: elision, then the closing mark). The check text's
  marks are Lamb's and often not Hude's: copy exactly what is printed: no mark where a quotation
  simply runs on (`πρὸς σέ· ὁ γὰρ ἀνὴρ`), a second ‘ where Hude sets one before a new sentence
  inside a quotation (`πεύσει. ‘ἔστι δʼ’ ἔφη ‘Ἐρατοσθένης`), the closing mark before or after
  the stop as printed (`εἶναι’.`). A lacuna is three dots with spaces between, as printed (`. . .`),
  with a space before and after. Square brackets [ ] for words Hude deletes, angle brackets ⟨ ⟩
  (U+27E8, U+27E9) for words he adds, an obelus † where he prints one. **Capitals as printed**:
  Hude begins a new train of thought with a capital, also in the middle of a line after a wider
  space (`αὐτήν. Πρῶτον μὲν οὖν`), and proper names; he does not capitalise after every full
  stop. The draft took the capitals from the OCR where it was sure.

**While you look at a flagged line, make the whole line follow the print**: its punctuation
(comma, full stop, raised stop, question mark), accents, capitals and marks too, not only the
flagged word; the flags compare letters only, and a later pass looks at the punctuation of the
unflagged lines. Note what you change.

The flags, and what to do:

* **"X: the OCR reads “Y”"**, **"X: the OCR, unsure, reads “Y”"**: the check text and the OCR
  differ. Look at the crop. Most are OCR errors, but about one in eight is Hude's own reading
  (ἑαυτοῦ for ἐμαυτοῦ, ἑορακυῖα for ἑωρακυῖα, τέτταρες for τέσσαρες, πεύσει for πεύσῃ,
  ἐπιμέλεσθαι for ἐπιμελεῖσθαι on the first six pages): if the page prints something other than
  X, write what it prints, and say so under notes (`21.12	ἑορακυῖα as printed`). Hude's
  apparatus on the same line often confirms it ("12 ἑωρ. L"). **"(accents)"**: the
  letters agree, the accents or breathings do not: Tesseract confuses ἂν/ἃν, ἡ/ἣ/ἢ, ἦν/ἣν,
  ὢν/ὧν, αὐτ-/αὑτ- constantly; change an accent only where the crop is clear.
* **"X: not found in the OCR; check it is printed on this line"** (or "…, and on which
  line"), **"which line it stands on is a guess"**: check that the word is printed, and on this
  line and not the next or the one before; move it if not. **A word the check text has that Hude
  does not print** is deleted, with a note (Lamb's supplements in ⟨ ⟩ are often not Hude's).
* **"N words of the check text (“…”) are not on the page here and were left out of the
  draft"**: a passage Lamb has and Hude does not print here (he deletes it, or prints it
  elsewhere: his apparatus says which, "§§ 65-66 del. Hamaker"). Look at the page: if the words
  are printed there after all, type them from the image; if not, nothing is to be added. Note
  it.
* **"these words stand in another place in the check text"**: Hude prints a passage where the
  check text does not; the draft has put the check text's words there. Check the lines like any
  other and give the sections the numbers Hude's margin gives them.
* **"the OCR reads “Y” on this line, which the check text does not have here"**: a word Hude
  prints that the check text lacks (add it where printed, with a note: `20.16	ἣ added before
  πάντων, as printed`), a margin number, or OCR noise.
* **"this printed line matched no words of the check text"**, **"a line of the hypothesis"**:
  the draft holds only what Tesseract read; type the line from the image (or delete it and
  renumber, if it is no line of the text).
* **"below this line the OCR read “…”, which was passed over"**: a line the draft may have lost
  (then add it with its key and renumber the page's lines after it), or a smudge.
* **Margin flags: line numbers.** "no line number read in the margin, though K should have
  one", "the margin has a line number at this line, which is K by the count": count the lines of
  the page on the whole page image and **renumber** what is wrong: a line missing from the file
  is added (its words taken out of the line where the draft put them), a line split in two is
  joined (Tesseract now and then reads the end of a line a second time as a line of its own).
  Often the number was simply not read: then nothing is wrong.
* **Margin flags: sections.** "the check text begins section S on this line, but Hude's section
  number seems to stand beside K" (and on line K: "Hude's section number seems to stand beside
  this line"): both lines are in the lines image; if Hude's number does stand beside K, move the
  mark there by the rule above. "no section number read in the margin, though section S begins
  on this line", "the margin has a section number … but the check text begins no section here":
  look where Hude's number stands (the whole page) and do the same. A number in square brackets
  is a Stephanus page, not a section number. Write every move under notes.
* **"the check text marks a gap"**, **"the OCR reads a row of dots"**: copy what Hude prints
  there (`. . .`, or nothing).
* **Brackets**: "the OCR shows square brackets on this line, the check text has none", "the OCR
  shows more round or angle brackets … than the check text has", or the other way round: Hude's
  brackets are often not Lamb's. Write the brackets the page prints, around exactly the words it
  brackets, and remove those it does not print. Tesseract reads Hude's angle brackets ⟨ ⟩ as
  round ones: look at the shape (angle brackets are pointed, around a word Hude adds; round
  ones enclose a parenthesis of the speaker's, "(δεῖ γὰρ καὶ ταῦθʼ ὑμῖν διηγήσασθαι)").
* **"the check text has quotation marks on this line"**: write Hude's marks where he prints
  them (‘ ’), none where he prints none.
* **"the speech's number"**, **"the speech's title"**: check every letter of the `[title]`
  lines.

## The apparatus

* **One output line per item**: the line number, a TAB, the item. Hude prints the number once,
  before the first item on a line of the text, and runs the further items on that line on after
  a wider space, without a number ("18 ἀποδεῖξαι Herwerden   ἐμοίχευσεν Contius"): **each item
  is a line of the file, and an item printed without a number gets the number of the item
  before it** (`18	ἀποδεῖξαι Herwerden` and `18	ἐμοίχευσεν Contius`). A new item begins at
  every number and at every wider space that is followed by a new lemma; the readings of one
  item are joined by colons ("μικρὰς Xᶜ (1): μακρὰς C H P X¹" is one item).
* The number is that of the line on this page, as printed; a range as printed, `22-23`. Keep
  the number even where it seems off by a line, and say so under notes. An item on the title of a
  speech, printed before the first number ("Λυσίου ἐπιτάφιος F V"), and any other note that names
  no line, gets `-` as its number.
* **Copy each item exactly as printed**: the lemma, the readings, the sigla, Hude's Latin and the
  scholars' names. Greek with full accents and breathings, as printed (the manuscripts' readings
  he reports are sometimes abbreviated or oddly spelt, "ἐγίν.", "συνοιθ.", "ποδηγεὶσ": copy what
  he prints). **The small Greek of the apparatus is where a breathing, an accent or an iota
  subscript is most easily misread, and often it is the whole point of the item** ("16 ἣ πάντων
  H P (ἢ)": the manuscripts' breathing against the text's; "θέλη rell.", "πεύση L", "αὐτῆ H N
  X" printed without the subscript that the text's form has): cut such a word out of the page
  image at four to six times its size, compare the mark with a certain one beside it, and copy
  what is printed, not what the form "should" be.
  Italics are ignored. A colon between readings is written without a space before it (`εἴητε
  marg. Ald.: εἰ ἦτε C H X`). Brackets and signs as printed: `]` after a lemma (`εἰπὼν] ὑπονοῶν
  Hirschig`), ⟨ ⟩, [ ], round brackets, the dots of a lemma range (`εἴπερ . . . μοι om. C`),
  `+` for an erased letter (`+ πάντων Xᶜ`), `/`, †.
* **The sigla** (the SIGLA page, leaf 18): for speeches 1–31 the manuscripts X C D E F f G g H h
  I K M N O P Q q R S U V W (capital and small letters are different manuscripts: copy the case
  exactly), L (the consensus), Aldus, marg. Ald., Turr.; for speeches 32–34 F G M T and L.
  Sigla stand apart with spaces as printed (`C H P X¹`). **Raised letters and digits** as Unicode
  superscripts: X¹ P¹ M¹ F² (¹ ² ³), Xᶜ Mᶜ Hᶜ (ᶜ, the corrected reading), Xʳ (ʳ, a later hand), Xˢ
  Fˢ (ˢ, written above); `Xᶜ (1)` or `Xᶜ(1)` with or without the space, as printed (the figure
  is a 1, Hude's old-style one, not the letter I).
* **Abbreviations and words** as printed: om., add., del., corr., ex … corr., suprascr., supra
  v., in ras., transp., coni., lac., lacunam statuit, post, ante, alt., pr., it. (item), cf.,
  rell., all., soli, vulg., comp., marg., lex. Vindob.; the scholars as printed (Reiske, Dobree,
  Bekker or Bekk., Sauppe, Scheibe, Herwerden, Cobet, Markland, Taylor, Stephanus, Contius,
  Emperius, Rauchenstein, Frohberger, Thalheim, Weidner, Fuhr …); references as printed
  ("Bekk. Anecd. i 169", "(item infra §§ 11, 14)").
* An item that runs over to the next page is written on the page where it begins.
* A page without an apparatus (the last lines of a speech): write `no apparatus on this page`
  under notes.

## Checking

Run, from `pipeline/`:

    .venv/bin/python -m anagnosis_pipeline check-lysias-batch transcriptions/lysias/batch-NN.md

It reports pages missing, keys that do not run on (1, 2, 3 … on each page), section marks out
of order, apparatus numbers that name no line of the page or stand out of order, pages without
an apparatus, elision and quotation marks, a space before a stop, divided words, and **every
place where the words now differ from the check text** (every change of wording you made: each
must be one the image shows; a remark is marked “(noted)” when your notes name its line).
Remarks on Hude's own readings that you noted are expected and stay. It does not see a word
moved to another line, a `¶` added, a § mark moved within its line, or an accent changed: note
those yourself.

**Your own files.** Scripts, enlarged crops and other helpers go only in the folder you were
given for them (`pipeline/build/agent-scratch/lysias-batch-NN/`), never under `/tmp` and never in
another agent's folder; other agents work beside you. Delete your crops when you are done. Do
not commit, and do not open any other batch file.

## Before you finish

For each page: every flag looked at; the § marks, `¶` and headings against the page; the
apparatus complete, every item with its number; the checker run clean or each remark explained
(a noted reading of Hude's is an explanation). Then say in your reply, for each page, how many
flags you checked, what you changed, and how many apparatus items you wrote; and the checker's
last line.
