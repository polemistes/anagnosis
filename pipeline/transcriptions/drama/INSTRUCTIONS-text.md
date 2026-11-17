# The plays: checking the Greek text and writing the critical apparatus

This folder holds the page-by-page work on the printed editions of nine plays and of Hesiod's
Theogony (see pipeline/PLAN-drama.md and pipeline/PLAN-theogony.md for which edition each uses). Each play has a folder
(`agamemnon/`, `choephoroi/`, `eumenides/`, `clouds/`, `medea/`, `frogs/`, `bacchae/`,
`alcestis/`, `lysistrata/`, and for Jebb's Sophocles `trachiniae/`, `oedipustyrannus/`) with batch files. The editions are in the public domain; the
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
  apparatus on the facing page, that part follows as `-app2-l.png`, `-app2-r.png`.
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

**Starkie's Clouds.** Each spread has the Greek on the left-hand (even) page and Starkie's
translation with his commentary on the right-hand page; only the left-hand pages are yours (the
translation and the commentary are done separately). On a text page: the verses, then a rule,
the critical apparatus, a second rule, and the commentary in two columns. The apparatus is only
what stands **between the two rules**; everything under the second rule is commentary: leave it.
On some spreads the apparatus runs on to the facing page, between two rules under the
translation (crops `-app2-l.png`, `-app2-r.png`): write it with the text page.
The speakers' abbreviations (ΣΤΡ., ΦΕΙ., ΣΩΚ., ΜΑ., ΧΟ., ΔΙ. Λ., ΑΔ. Λ.) stand in the left
margin; the margin numbers every fifth verse are at the right.
* **Turnovers.** Many verses (the anapaests, the long tetrameters of the agon) are longer than
  the printed line: Starkie prints the end of the verse on the next line, set in further, often
  after a divided word ("ἔλθετε δῆτʼ … εἰς ἐπί- | δειξιν·", "… τὸν κακοδαίμονʼ | ἔχοντα."). That
  indented end is part of the verse above, not a verse of its own. The draft joins such lines and
  flags each join ("the indented line … was joined to this verse as its turnover"): confirm it
  on the image, or, where the print really begins a new verse there (a short lyric verse set in
  for its metre, not for lack of room), split it off with the number rule above and note it. A
  lettered verse in the draft (`271a Νύμφαις,`) that is such a turnover is joined to the verse
  above, even when it is not flagged; note it.
* **The apparatus.** Each item begins with the line number in bold ("92 θυρίδιον RV etc., a
  common error (Ach. 777 crit. n.)"); several items on one line are divided by `||`: write each
  as its own output line with that line's number. The items run on in the paragraph, so a new
  number inside the paragraph begins a new item. Copy the sigla as printed (R, V, U, A, M, Θ,
  codd., al., Ald., Su., schol. R, dett.) and Starkie's words, references and Greek as printed.
* Ignore pencil and ink notes on the pages.

**Rzach's Theogony (Teubner 1908).** One poem, no speakers: the check sheet names none, and the
file has no `@` lines. The margin numbers every fifth verse are at the right. Rzach sets the
verses in paragraphs divided by a blank line; the blank lines are not recorded. The Teubner type
prints θ as ϑ, ρ often as ϱ and β inside a word as ϐ: write θ, ρ, β (the check sheet's Perseus
spelling already does); his elision mark is ʼ, his raised stop ·. Lines he holds to be
interpolated stand in square brackets, which may open on one verse and close several verses
later ([ἔνθα σφιν … ἱεῖσαι.] 63-67): keep the brackets exactly where printed. Asterisks
(* * * * *) between verses mark a gap he assumes: a `!` line `* * * * *`. Where Perseus has
verses Rzach does not print in his text (the Metis fragment after 929, which Perseus numbers
929a-929t), the draft cannot match them: follow the page, and note what Rzach prints there.
* **The apparatus** is under a short rule at the foot of the page, in Latin, with no stop after
  the line numbers: "215 ἧς scripsi, αἷς libri   post 216 olim nomina … censuit Muetzell" —
  each item begins with the number of its line (a range "215—217 et 220—222", "18 sq.", or a
  "post 26" that names the line it follows: write `26` and keep "post 26" in the item). Items run
  on in the paragraph, separated by wider spaces: a new number begins a new item. A note on two
  lines ("218 sq. neglexit Stobaeus") is filed under the first, with "sq." kept in the item.
* Copy the sigla exactly: the papyri A B R, the codices C D E F G H I K L, the classes and
  families Ω Ψ Φ, Ωa Ωb Ωc Ωbc (write Ωbc as printed, letters on the line), m¹ m² (first and
  second hand: superscript digits), m. rec., γρ. (a variant noted in a manuscript), superscr.,
  in marg., in ras., e corr., ///  (erased letters: three slashes as printed), codd., libri,
  schol., Tzetzes, the scholars' names (Goettling, Hermann, Guyet, Peppmüller, Paley …). Where
  Rzach prints a papyrus's letters in capitals with restored letters in brackets
  (ΑΜΦΙΛΛ⟨Ο⟩ΓΙΑC B), copy the capitals as printed, lunate sigma C included, and his brackets.
* Greek words in the apparatus have full accents as printed; references (Hom. Β 305, Priscianus
  Inst. XIV 34, Aristides XXVIII 20, Mor. 747 f) are copied as printed.

**Jebb's Sophocles (Trachiniae, Oedipus Tyrannus, Oedipus at Colonus, Philoctetes).** Each
spread has the Greek on the left-hand (even) page and Jebb's translation on the right-hand page;
only the left-hand pages have verses. On a text page: the verses; under them, after a wider
space but **with no rule**, the critical apparatus in small type set to the full width; then a
rule, and under the rule the commentary in two columns: leave the commentary. The apparatus
usually runs on to the facing page, where it stands in the same small type between the
translation and the rule (crops `-app2-l.png`, `-app2-r.png`): write it with the text page.
* **The text.** The speakers' abbreviations (ΔΗ., ΥΛ., ΧΟ., ΑΓ., ΛΙ., ΤΡ., ΠΡ., ΗΡ., ΘΕ.; ΟΙ.,
  ΙΕ., ΚΡ., ΤΕ., ΙΟ.) stand in the left margin; a character's name is printed in capitals,
  centred, above the first speech (ΔΗΙΑΝΕΙΡΑ.); the margin numbers every fifth verse are at the
  right. In the lyrics Jebb prints small numerals before the verses of a strophe (2, 3, 4 …) and
  labels in the left margin (στρ. α΄., ἀντ. α΄., ἐπ.): neither is part of the text. A verse too
  long for the line ends on the next line, set in to the right: it is one verse (the draft joins
  it and flags the join; confirm it). Jebb marks a conjecture admitted into the text with an
  asterisk (*τό): leave the asterisk out. His supplements stand in angle brackets, printed
  < >: write ⟨ ⟩; words he holds spurious in square brackets; a dagger † stays. Words printed
  outside the metre on a verse's line (ναί· before 425) stay on that line, as printed.
  The play's opening words, printed in capitals, are written as the check text spells them
  (ὦ τέκνα, not Ὦ Τέκνα or Ὦ ΤΕΚΝΑ).
* **The apparatus.** Each note begins with the line number in bold ("16", "12 f.", "94—102"),
  usually followed by a lemma that ends in a square bracket; a note on one line may hold several
  remarks divided by ".—": the whole note is ONE output line, `16<TAB>ἀεὶ] αἰεὶ L. Cp. cr. n. on
  Ant. 76.—ἐπηυχόμην] ἐπευχόμην L. Cp. Ant. 1164 (comment.).` The number is the first line
  number alone: "12 f." and "4 ff." give `12` and `4` (leave "f."/"ff." out); a range
  "94—102" gives `94-102`. A second note with the same number (often on the facing page) is a
  further output line with that number. Copy Jebb's English, his sigla (L, A, B, K, T, V, V²,
  Vat., Harl., r, MSS., schol., the hands "1st hand", S, corrector), names and references as
  printed; a manuscript's spelling he quotes without accents or with the final σ (ἀλκμήνησ,
  δόμοισ) is copied as printed; a superscript letter or figure as a Unicode superscript (V²).
  The verse division he reports with upright strokes (ὃν— | τίκτει— | ἅλιον) keeps its strokes.
* A note that runs on beyond the spread (from the foot of the right-hand page to the top of the
  next left-hand page's apparatus, where it goes on without a number): write the whole note on
  the page where it begins, taking its end from the next page's `-app-l.png`, `-app-r.png`
  (open them even if that page is in another batch), and do not write that end again on the next
  page. If your first page's apparatus begins with such an end, leave it to the batch before.
* The first text page's apparatus begins with Jebb's note on his symbols ("L = cod. Laur. 32. 9
  … r = one or more of the later MSS. … MSS., after a reading, means …"): it is not an item.
  Copy it under `--- notes` in one line beginning `Sigla:`.

**Jebb's Antigone (Part III, second edition 1891; scan sophocles03soph).** Everything above for
Jebb's Sophocles holds, with these differences:
* **The check text is NOT Jebb's.** It is the text we published, from Perseus's file, which proved to
  differ from this page in about one verse in three: words (195 δόρει for δορί, 198 Πολυνείκη for
  Πολυνείκην, 213 που πάρεστί for πού γʼ ἔνεστί, 424 ἐς for ὡς, 803 δάκρυ for δακρύων, 1136 πᾶσαι for
  πασᾶν), accents (42 εἰ for εἶ, 44 ἢ for ἦ, 45 ἐμὸν for ἐμόν) and above all punctuation (commas and
  colons lost or added: 11, 24, 25, 45, 49, 191 …). The draft flags only some of this, because its
  rules trust a check text of the same edition. So **read every verse of your pages word by word and
  sign by sign against the page** (letters, accents, breathings, iota subscripts, every comma, colon,
  raised stop, question mark and full stop, brackets, daggers), not only the flagged ones, and correct
  the batch to what Jebb prints. A list of what the OCR and the draft disagree on is ready for each page,
  `build/drama-pages/antigone/residuals/r-NNNN.md` (with an image of each line): go through it as well;
  it is a help (much of it is OCR noise), not a substitute for reading the verses.
* **Numbering by Jebb's margins and his notes**, not by the draft: the draft numbered by the check text,
  whose numbers follow the treebank and run a verse apart from Jebb's in some lyrics (591-593, 799-800
  were seen). Jebb prints a number at odd places too (593, 799 …); where his margin or his apparatus
  names a number, that number stands, and the verses between are counted from it.
* The scan is a library copy with a reader's pencil and ink: underlining, upright strokes inside the
  verses, words in the margins (stage notes). None of it is print: ignore it, and be careful where a
  stroke falls on a letter or a stop.
* The first text page (p-0076) holds Jebb's note on his symbols at the head of the apparatus ("L = cod.
  Laur. 32. 9 …"): `Sigla:` under `--- notes`, as above.

**Jebb's Ajax (Part VII, 1896, scan playsfragmentswi07sophuoft) and Electra (Part VI, 1894, scan
sophoclesplaysfr06soph).** Everything above for Jebb's Sophocles holds. The check text is the text we
published; in the samples read against the page its words, accents and stops agree with Jebb's, but
it was typed by eye: check the flags, go through the page's residual list
(`build/drama-pages/<play>/residuals/r-NNNN.md`: mostly OCR noise; a real difference is what you must
find), and look over every verse for brackets, daggers and stops. **Numbering**: the check text's
numbers follow the treebank and in the lyrics run one behind Jebb's margins in places (Electra
249-250, 473-485, 504-515, 1249-1250, 1419-1420, 1439-1440, 1160/1162 were seen; the Ajax agreed where
seen): number by Jebb's margin and his apparatus, as the brief says above. The critical apparatus is
written fresh from the crops, as for every play.

**Murray's Euripides (Oxford text).** G. Murray, Euripidis Fabulae, Oxford (vol. I 1902:
Cyclops, Alcestis, Medea, Heraclidae, Hippolytus, Andromache, Hecuba; vols. II-III the other
plays). These plays are **private until 2028-01-01** (pipeline/PLAN-euripides.md): their batch
files live in `private/` (the play's folder here is a link into it). Never copy any of their
text or apparatus into another file, a message to another agent, or anything outside the batch
file and your own scratch folder. Every page is a text page; there is no facing translation.
* **What stands on the page.** At the top the running head (ΕΥΡΙΠΙΔΟΥ on the left-hand pages,
  the play's title, e.g. ΜΗΔΕΙΑ, on the right-hand ones): not text. Then 20-29 verses; the
  margin numbers every fifth verse stand at the **right** on both pages. Under the verses, with
  a wider space and **no rule**, the apparatus in small type, Latin, set to the full width. At
  the foot of some pages, under the apparatus, the printer's signature: "EUR. I." with a
  sheet number at the right, or the number alone with an asterisk (7*): not apparatus, leave
  it out (the crops stop above it; if a crop shows it, ignore it). The first page of a play has
  the play's title above the text.
* **Speakers.** The speaker's abbreviation stands in the left margin before the verse where
  the speaker begins, the name's first two letters: in the Medea Τρ. (Τροφός), Πα.
  (Παιδαγωγός), Μη., Χο., Κρ., Ια., Αι. (Αἰγεύς); in the Alcestis Χο., Αδ., Ηρ. and the
  others of the play's persons page (the check sheet lists the check text's names). The same abbreviation can mean two persons (in the Medea, Πα. is the
  Paedagogus early in the play, the children, Παῖδες, at 1271 ff.): take the name the check
  text gives there unless the page plainly says otherwise. A character's first entry is
  announced by the name in capitals on a line of its own above the speech (ΙΑΣΩΝ, ΑΓΓΕΛΟΣ):
  that heading is not text, it is the `@ Name` line. Words printed with the heading in brackets
  ((ἔνδοθεν), "within") are a stage direction: a `!` line with the words as printed, before
  the verse. A change of speaker **inside** a printed line is printed with the next speaker's
  abbreviation in the line itself (Ια. … Μη. …): the line is split at that point into lettered
  verses as the draft does it (the second part `1397a`), each part after its own `@` line.
  Within the chorus or a group a change of voice is printed as a dash — before the words: the
  dash is part of the verse as printed (Perseus has it too); it is not a new `@` line.
* **Metrical labels and turnovers.** At the right of a strophe's first verse Murray prints
  `[στρ.`, `[ἀντ.` (and `[ἐπῳδ.`): not text, not a bracket of the text; leave them out. A
  lyric verse too long for the measure ends on the next printed line, set in, often after a
  divided word (σε- | βίζουσʼ); the margin number may stand beside that turnover. It is one
  verse: the word is written whole and the margin number belongs to the verse it ends (the
  draft joins such lines and flags the join: confirm it on the image).
* **The check text is Murray's own text** (Perseus digitised this very edition by OCR). So a
  flag is almost always an OCR slip on one side: Tesseract's (δʼ read as ὃ, ἂν as ἃν, a lost
  breathing) or Perseus's (a garbled word, a wrong accent, a lost stop). Decide from the crop
  which: where the page agrees with the check text, leave the line; where the page prints
  something else, write what the page prints and say under notes "Perseus has X". A real
  difference of reading between the print and the check text is rare: when you find one, look
  twice and note it.
* **Signs in the text**, written as printed: square brackets [ ] round words or verses Murray
  deletes (a deleted verse stays a verse, in its brackets); his additions in angle brackets,
  printed ⟨ ⟩ (also round a whole supplied cry with its speaker's heading: the `@` line, then
  the verse in ⟨ ⟩, and say under notes where the bracket opens); daggers † round corrupt words,
  exactly where they stand; a lacuna he marks with a row of asterisks or dots between verses is
  a `!` line with the row as printed (`* * * * *`). The play's opening words, if printed in
  capitals, are written as the check text spells them. Otherwise a verse's first word has a
  capital only where the print has one in its ordinary type (a proper name, a speech's first
  word where Murray prints one): Murray does not capitalise verse beginnings.
* **Numbering** (what the Sophocles plays taught): the verses carry **Murray's** numbers. His
  witnesses are the margin numbers and the numbers of his apparatus (an item numbered 634 names
  the verse that holds its lemma). The check text's numbers, from which the draft numbered the
  verses, run in lyric passages at times one behind or ahead of his, where the traditional
  numbering skips or doubles a number (in the Medea's second stasimon Perseus numbers ἱμέρῳ …
  633 where Murray's apparatus shows 634). The margin check sees only every fifth number, so
  in lyrics compare every apparatus number on the page with the verse that holds its lemma, and
  renumber the verses (and the following ones up to the next margin number) where they
  disagree; note each renumbering. A verse that covers two traditional numbers carries the
  first, and the second is skipped. A line Murray prints as one, shared between speakers, is one
  printed line split into lettered verses at the change of speaker (above). Where Murray prints
  verses out of the order of their numbers (the Medea 1271-1272 after 1273-1274, with his
  margin numbers beside them), write them in his order with his numbers and explain the
  checker's "does not run on" remark under notes.
* **The apparatus.** Each item begins with the line number, **without a stop**, then the lemma
  (often closed by a square bracket) and the readings with their sigla. Items run on in the
  paragraph, separated by wider spaces; a new number begins a new item. Several items for one
  line, the second printed without the number (a second lemma after a wider space), are separate
  output lines with the same number; where you cannot tell, keep them in one item. Two
  consecutive lines named together ("21, 22", "38-43") are a range `21-22`, `38-43`; lines not
  consecutive ("1125, 1129, 1136 …") go under the first number, and the item keeps the further
  numbers as printed at its start. "Post 1056 …" goes under 1056 with "Post 1056" kept in the
  item. A remark printed without a number after the last item of the play ("In fine …", the
  manuscripts' subscriptions) goes under the play's last verse. An item that runs on to the
  next page (rare: each page's apparatus treats that page's verses) is written whole on the page
  where it begins.
* **Sigla**, copied exactly as on Murray's Sigla page: the manuscripts M A B V L P (O D F N, Nap.,
  Haun., Apogr. Par. rarely), the papyri Π, the fragments K, H, Ambr.; Σ for the scholia (Σ B,
  Σ V for a scholion in one manuscript, as printed); a manuscript's first and second hand as
  Unicode superscripts (L¹, V², B¹, A¹); the later correcting hands as the small letters l, p, v,
  b (his Sigla page: "litteris minusculis"; write the small letter, italics are ignored); γρ.
  (a variant noted in a manuscript), codd., rell., corr., suprascr., om., cf., fortasse, sic,
  and the scholars' names (Elmsley, Porson, Nauck, Wilamowitz, Verrall …) and references as
  printed. Greek in the apparatus with full accents and breathings as printed.
* Format, as everywhere: one output line per item, `N<TAB>item` (a range `N-M`); no space
  before a colon or semicolon; save after each page.
* **Keep to the flags and the apparatus.** A review pass follows every batch: it reads every
  verse against the whole page for stops, accents, breathings, iota subscripts, brackets and
  daggers, and compares the apparatus's breathings at enlargement with certain ones on the same
  page. So do not re-read unflagged verses word by word; spend the care on the flags, the
  numbering in the lyrics and a complete apparatus.

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
