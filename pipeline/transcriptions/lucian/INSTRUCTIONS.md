# Checking Nilén's Lucian: the Greek text and the critical apparatus

This folder holds the page-by-page transcription of Lucian's *A True Story* (Ἀληθῶν διηγημάτων
α´ β´) in Nils Nilén's Teubner edition (*Luciani Samosatensis libelli*, vol. I fasc. 1, Leipzig
1906), from the Internet Archive scan `bub_gb_RYepnZKT1OwC` (leaves 196-275 = Nilén's pp.
129-208): the Greek text line by line with Nilén's page and line, and his critical apparatus.
`merge-lucian truestory` turns the batch files into `texts/truestory/grc.txt` (one line per
section, 1.7) and `texts/truestory/commentary-nilen-apparatus.md`. The edition is in the public
domain; the transcription is published under CC BY-SA 4.0. The brief for the whole text is
`pipeline/PLAN-true-story.md`.

**What ships is Nilén's text with Nilén's apparatus. Nothing of Harmon's Greek ships.** The
text is not typed: `lucian-pages truestory draft` read every page with Tesseract and matched its
lines word by word to the Perseus text of A True Story. That text is **Harmon's Loeb (1913), a
different edition**: it has the same words almost everywhere, but not all (Harmon adds αὐτοὺς
with Schwartz at 1.2, where Nilén prints nothing; Nilén prints συγγεγραφότας where Harmon has
συγγεγραφότων; θαλάσσης and θαλάττης, γίνομαι and γίγνομαι, ἐς and εἰς differ from place to
place). Where the OCR and Harmon agreed, the line is taken as right. Where they did not, the
line is **flagged**. Your work on each page:

1. **Check the flagged lines** against the image and correct the batch file where it is wrong.
   **Nilén's page wins every time**: where the page prints another word, spelling, accent or
   stop than Harmon, write what the page prints.
2. **Write the apparatus** from the image. Tesseract's reading of it is a help, not a draft: it
   garbles the sigla, the line numbers and small Greek words.

Do not re-read or retype unflagged lines. Do not change anything you have not checked on the
image. Never guess: where something is unreadable, write `[illegible]` and say so under notes.

## Files

For each page `p-0200` (leaf 200 of the scan = Nilén's p. 133; the page is the leaf less 67),
in `pipeline/build/lucian-pages/truestory/`:

* `p-0200.md`: the check sheet: the flags, line by line; every line of the draft beside
  Tesseract's reading of it and the margin numbers read beside it; Tesseract's two readings of
  the apparatus.
* `p-0200-lines.png`: the flagged lines cut out of the page, one under another, each labelled
  with its key. Look here first.
* `p-0200-app-l.png`, `p-0200-app-r.png`: the apparatus, left and right halves, enlarged (they
  overlap a little). Read the apparatus from these.
* `pages/leaf_0200.png`: the whole page (2500 pixels wide), when you need more: the margin
  numbers, a line that is not in the flagged strip, an indentation.

**Keep image requests light**: open the lines image and the two apparatus halves for each page;
open the whole page only when a flag needs it.

The batch file `pipeline/transcriptions/lucian/truestory/batch-NN.md` holds six pages:

```
=== p-0200
--- text
133.1	ὑποφαινομένης οὐ σφόδρα βιαίως ἀνηγόμεθα, τῆς ἐπιούσης
133.2	δὲ ἅμα ἡλίῳ ἀνίσχοντι ὅ τε ἄνεμος ἐπεδίδου
...
133.14	ἀνελθεῖν ἐπὶ κατασκοπῇ τῶν ἐν τῇ νήσῳ. §1.7 προελθόντες
--- apparatus
1/2	τῆς ἐπιούσης ΓΩIS τῇ ἐπιούσῃ Γ*ˣZNFv γρ mg. S
3	ἐπεγίνετο ΓΩIS ἐνεγίνετο ZF ἐγίγνετο N
3	οὐκέτι F
5	πνέοντι ΓΩS πνεύματι ZNFI ex corr. Ωˣ
--- notes
133.14	(optional: what you checked and decided, one remark per line, starting with the key)
```

The key and the text are separated by a single TAB. Edit the file in place, page by page, and
**save after each page**, so that nothing is lost if you are interrupted.

## Nilén's page

* At the top the running head ("13. VERAE NARRATIONES. I. VULG. 26" and the page number on a
  right-hand page, "ΑΛΗΘΩΝ ΔΙΗΓΗΜΑΤΩΝ Α" and the page number on a left-hand one): not text.
* The text, about 20 lines (fewer on a page whose apparatus is long). On an **odd** page Nilén's
  line numbers (5, 10, 15, 20) and the Vulgate page numbers (Hemsterhuis's pages, two or three
  digits: 70, 75, 105, 141) stand in the **left** margin and his **chapter numbers** (1-42 in
  book I, 1-47 in book II: Perseus's sections) in the **right** margin; on an **even** page the
  other way round. The Vulgate numbers are not recorded. Teubner digits: the 5 has a hook and
  is easily taken for a 3.
* A short rule, then the apparatus in small type, keyed by line number.
* At the foot of some pages a signature ("LUCIANUS, ed. Nilén. I." and a number): leave it out.
* A book begins on a fresh page with its title in capitals (ΑΛΗΘΩΝ ΔΙΗΓΗΜΑΤΩΝ Α on p. 129,
  … Β on p. 167), and **the title counts as line 1** of that page (the 5 in the margin stands at
  the fifth line counting the title). The draft writes it as `129.1<TAB>[title] ΑΛΗΘΩΝ
  ΔΙΗΓΗΜΑΤΩΝ Α`: correct the letters to the print, keep `[title]`.

## The text: what the draft does, and what the flags mean

* **The key** is `page.line`: Nilén's page and the line's place on it, counted from the top of
  the text (the title included). Lines run 1, 2, 3 … on every page without a gap. The margin
  numbers are the check.
* **A word divided at the end of a line is written whole on the line where it begins**, and
  left out of the next line (`και-` / `ρὸν` → `καιρὸν` at the end of the first line). Only when
  the second line would be left without a word of its own does the whole word stand there.
  Across a page break likewise: the whole word at the foot of the first page.
* **`§1.7`** stands, followed by a space, before the word where a section (Nilén's chapter)
  begins: at the start of the line or inside it (`… νήσῳ. §1.7 προελθόντες`). The draft puts it
  where Harmon begins the section; Nilén's chapter number in the margin stands beside the line
  where the chapter begins. Every section of the book once, in order (book I: 1.1-1.42; book II:
  2.1-2.47).
* **A new paragraph** (a line Nilén indents) has a line with only `¶` before it. Paragraphs
  begin at the start of a line; most begin with a section, some inside one (2.47 "Ταῦτα μὲν
  οὖν"): put `¶` where Nilén indents, whatever the section.
* **Verse** set off on lines of its own (the epigram at 2.28, quotations of Homer) begins with
  `| ` after the TAB.
* **Spelling and signs as Nilén prints them**, with these rules: his ϑ, ϱ, ϐ, ϰ are written θ,
  ρ, β, κ; elision ʼ (U+02BC), never ’ or ' or ᾽; the raised stop ·; the iota subscript as he
  prints it (ἡλίῳ); his spacing before a stop ("ἦν . ἐπιτρέψαντες", "παρασκευάζειν . γένοιτο")
  is a printing convention: **no space before a stop** (`ἦν. ἐπιτρέψαντες`); dashes with a space
  on either side (`ἀνέσεως — μέρος`). His signs are kept as printed: three asterisks for a
  lacuna (`ἔμελλον *** Κτησίας`), an asterisk inside a word (`προ*ελθεῖν`), angle brackets
  ⟨ ⟩ for words he adds, square brackets [ ] for words he deletes, †. Capitals as printed:
  Nilén capitalises proper names and the first word of a paragraph, not the first word after a
  full stop, and not the inscription at 1.7 ("ἄχρι τούτων").

The flags, and what to do:

* **"X: the OCR reads “Y”"**: Harmon and the OCR differ. Look at the crop. Most are OCR errors
  (Tesseract reads Nilén's δ as ὃ, ὁ as δ or υ, Δ as Ζ, μ as ω or υ), but some are Nilén's own
  readings: if the page prints something other than X, write what it prints, and say so under
  notes (`133.15	θαλάσσης as printed`). Accents and breathings: Tesseract confuses ἂν/ἃν,
  ἡ/ἣ, ὢν/ὧν constantly; change an accent only where the crop is clear.
* **"X: not found in the OCR; check it is printed on this line"**, **"which line it stands on
  is a guess"**: check that the word stands on this line and not the next or the one before;
  move it if not. **A word Harmon has that Nilén does not print** (αὐτοὺς at 1.2, Harmon's
  supplements) is deleted, with a note.
* **"the OCR reads “Y” on this line, which Perseus does not have here"**: a word Nilén prints
  that Harmon lacks (add it where printed), a margin number, or OCR noise.
* **"the next printed line, read as “…”, matched no Perseus words"**: a line the draft lost
  (then add it with its key and renumber the page's lines after it), or a smudge.
* **Margin flags**: "the margin reads line N here, but the line is K", "no line number read in
  the margin, though K should have one": count the lines of the page on the whole page image
  (the title counts) and **renumber** what is wrong: a line missing from the file is added (its
  words taken out of the line where the draft put them), a line split in two is joined. Often
  the number was simply misread: then nothing is wrong. "no chapter number read in the margin,
  though section S begins on this line", "the margin has a chapter number … but Perseus begins no
  section here": look where Nilén's chapter number stands and **move `§S` to the line it
  marks**, before the word where the chapter begins (the first word after the full stop on that
  line, as a rule). Write the change under notes.
* **"Perseus marks a gap"**: copy what Nilén prints there (`***`).
* **"the OCR reads an asterisk on this line"**: Nilén's asterisks, as above.

## The apparatus

* **One output line per item**: the line number as printed (`5`, a range `1/2`, `20/22`), a
  TAB, the item. Nilén prints the number before every item, items separated by wider spaces
  ("5 πνέοντι ΓΩS πνεύματι ZNFI ex corr. Ωˣ   5 αὐτοὺς F   5 τῇ τύχῃ, post ἑαυτοὺς add. Z"):
  each number begins a new item, even where the number repeats. The number refers to the line
  of this page; keep it as printed even where it seems off, and say so under notes.
* A note that names no line (the paragraph "Libri: ΓΩSZPNF … textus natura." at the head of each
  book's apparatus, the subscriptions "διώρθωσα … subscr. Γᵃ in mg." at the end of a book) gets
  `-` as its number.
* **Copy each item exactly as printed**: the lemma, the readings, the sigla, Nilén's Latin and
  abbreviations. Greek with full accents and breathings, as printed (the variants he reports
  are often unaccented or oddly accented in the manuscripts: copy what he prints, ϑ written θ).
* **The sigla**: manuscripts Γ Ω S Z P N F I B U (and others where printed), v (the vulgate);
  hands and corrections as printed with Unicode superscripts: Γᵃ Γᶜ Γˣ Ωˣ Sˣ Pˣ (small raised
  letters ᵃ ᶜ ˣ, and others: ᵇ ᵈ ᵉ ᵐ ᵛ), S¹ S² Γ¹ (raised digits ¹ ² ³), the asterisk for the first
  hand (Γ*, Γ*ᵃ, Γ*ˣ, Ω*ˣ). Sigla run together as printed (`ΓΩIS`, `ZNFv`); a space where Nilén
  leaves one (`ZN Fv` at a line break is one group: write `ZNFv`).
* **Abbreviations and words** as printed: corr., ex corr., spscr., mg., in mg., γρ (γράφεται),
  ras., om., add., del., coni., prob., probant, cfr., ut vid., fort., sic, rell., ambig.,
  litterarum, inter … et …, ante, post, compend.; the editors Ibtz (Jacobitz), Dind, Bekk, Sbdt
  (Sommerbrodt), Schw (Schwartz), Schmieder, du Soul, Guyet, Rothst, Voss, Photius cod. 166 and
  the like; references (cfr. 144, 9—11) as printed. Italics are ignored. Brackets and signs as
  printed: `]` after a lemma (`τοὺς λόγους] ΓΩIS λόγους ZNFv`), ⟨ ⟩, [ ], *, ‖, a dash between
  the ends of a lemma range (`12/13 ἔμελλον — ὃς] multiplex locus`).
* An item that runs over to the next page is written on the page where it begins.

## Checking

Run, from `pipeline/`:

    .venv/bin/python -m anagnosis_pipeline check-lucian-batch transcriptions/lucian/truestory/batch-NN.md

It reports pages missing, keys that do not run on (1, 2, 3 … on each page), section marks out of
order, apparatus numbers that name no line of the page, pages without an apparatus, elision
written with ’ or ', a space before a stop, divided words, and **every place where the words now
differ from Harmon's** (every change of wording you made: each must be one the image shows; a
remark is marked “(noted)” when your notes name its line). Remarks on Nilén's own readings that
you noted are expected and stay. It does not see a word moved to another line, a ¶ added, or a
§ mark moved within its line: note those yourself.

**Your own files.** Scripts, enlarged crops and other helpers go only in a folder of your own,
named after your batch file, under the session's scratchpad folder (e.g.
`<scratchpad>/truestory-batch-03/`); other agents work beside you at the same time and use the
same scratchpad, so never write a file directly in the scratchpad or in another agent's folder.
Do not commit.

## Before you finish

For each page: every flag looked at; the § marks and ¶ against the page; the apparatus complete,
every item with its number; the checker run clean or each remark explained (a noted reading of
Nilén's is an explanation). Then say in your reply, for each page, how many flags you checked,
what you changed, and how many apparatus items you wrote.
