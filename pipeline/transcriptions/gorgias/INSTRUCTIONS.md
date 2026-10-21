# Checking Burnet's Gorgias

This directory holds the transcription of John Burnet's Oxford text of Plato's Gorgias
(*Platonis Opera* III, Oxford 1903), page by page from the Internet Archive scan
`platonisopera03platuoft` (leaves 261-377): the Greek text line by line with Burnet's line
numbers, and his critical apparatus. `merge-gorgias` turns the batch files into
`texts/gorgias/grc.txt` and `texts/gorgias/commentary-burnet-apparatus.md`. The edition is in the
public domain; the transcription is published under CC BY-SA 4.0.

**The text is already there.** Unlike the Symposium, nobody types the Greek. `gorgias-pages draft`
read every page with Tesseract, matched its lines word by word to the Perseus text of Burnet's
edition (which has his words but not his lines), numbered the lines from the Stephanus sections
and checked the numbers against those printed in the margin. Where all of this agreed, the line is
taken as right. Where it did not, the line is **flagged**. Your work on each page is:

1. **Check the flagged lines** against the image, and correct the batch file where it is wrong.
2. **Write the apparatus** from the image. Tesseract's reading of it is a help, not a draft: it
   garbles the sigla, the line references and small Greek words.

Do not re-read or retype unflagged lines. Do not change anything you have not checked on the
image.

## Files

For each page `g-0263` (leaf 263), in `pipeline/build/gorgias-pages/`:

* `g-0263.md`: the check sheet: the flags, line by line; every line of the draft beside
  Tesseract's reading of it; Tesseract's two readings of the apparatus.
* `g-0263-lines.png`: the flagged lines cut out of the page, one under another, each labelled
  with its line number. Look here first.
* `g-0263-app.png`: the apparatus, the whole width; `g-0263-app-l.png` and `g-0263-app-r.png`:
  its left and right halves, enlarged (they overlap a little in the middle). Read the
  apparatus from the halves.
* `pages/leaf_0263.png`: the whole page, when you need to see more (the margin numbers, a line
  that is not in the flagged strip). It is 1735 × 2702 pixels.

**Keep image requests light**: open the lines image and the two apparatus halves for each page;
open the whole page only when a flag needs it.

The batch file `pipeline/transcriptions/gorgias/batch-NN.md` holds six pages:

```
=== g-0263
--- text
448b5	τῆς τέχνης ἧσπερ ὁ ἀδελφὸς αὐτοῦ Ἡρόδικος, τί ἂν αὐτὸν
448b6	ὠνομάζομεν δικαίως; οὐχ ὅπερ ἐκεῖνον;
¶
448b7	{ΠΩΛ.} Πάνυ γε.
...
--- apparatus
448b5	Ἡρόδικος B T P: πρόδικος F
...
--- notes
448b5	(optional: what you checked and decided, one remark per line, starting with the line number)
```

The number and the text are separated by a single TAB. Edit the file in place, page by page,
and **save after each page** (so that nothing is lost if you are interrupted).

## The text: what the draft does, and what the flags mean

* Every printed line is one line of the file, numbered by Stephanus page, section letter and
  line within the section: `448b5`. Burnet prints the section letters b–e in the margin and every
  fifth line number; a new Stephanus page shows its number (e.g. `449`) instead of the letter a:
  that line is `449a1`. Lines are counted afresh in each section.
* **A word divided at the end of a line is written whole on the line where it begins**, and left
  out of the next line (`παρεσκευά-` / `σθαι` → `παρεσκευάσθαι` at the end of the first line).
  Only when the second line would be left without a word of its own does the whole word stand
  there.
* **Speakers' names** are written in braces where they stand: `{ΣΩ.} Καλῶς γε`. In quick
  exchanges Burnet runs the speeches on, separated by a dash: write `Ναί.—{ΣΩ.} Δεύτερον`, and
  where such a speech begins a line, the dash ends the line before (`… τοῦ κακοῦ;—` then
  `{ΠΩΛ.} Ναί.—{ΣΩ.} …`).
* **A new paragraph** (a line Burnet indents: a new speech, or a new paragraph within a long one)
  has a line with only `¶` before it.
* **Verse** set off on lines of its own (Pindar at 484b, Euripides, Homer) begins with `| `
  after the TAB.
* The words, accents, punctuation, brackets ⟨ ⟩ [ ] and quotation marks “ ” come from Perseus,
  and the capitals from the OCR. Elision is ʼ (U+02BC), never ’ or ᾽; the raised stop is ·.

The flags, and what to do:

* **"X: the OCR reads “Y”"**: the word differs between Perseus and the OCR. Almost always the
  OCR is wrong; look at the image, and change the word only if the page clearly prints something
  else (then say so under `--- notes`). Accents: Tesseract confuses ἂν/ἃν, ἡ/ἣ, ὢν/ὧν and the
  like constantly; trust Perseus unless the page is clear.
* **"X: not found in the OCR; check it is printed on this line"**: the OCR lost the word, so its
  line is not confirmed. Check that it stands on this line (and not on the next or the one
  before); move it if not.
* **"X: which line it stands on is a guess"**: the same; check the line break.
* **Speakers' names**: "Perseus has this speaker's name here, the OCR shows none: left out" —
  Perseus adds names where Burnet prints none (often at a new Stephanus page in a long speech).
  If the page does print it, add it. "the OCR reads “ΔΛ.” here; check the name is printed" —
  the name was kept; remove it if the page has none.
* **"the OCR reads “Y” on this line, which Perseus does not have here"**: a word on the page
  that is missing from the line, or OCR noise. Add it only if it is really printed.
* **Margin flags** ("the margin reads “5” here, but the line is numbered 490d4", "no number or
  letter found in the margin, though 490d5 should have one"): the line numbering may be off
  (a line lost or doubled near here). Look at the whole page: count the lines from the nearest
  margin number or letter, and **renumber** what is wrong — a line missing from the file must be
  added (with its words taken out of the line where the draft put them), a line split in two
  must be joined. Often the margin number was simply not read: then nothing is wrong.
* **"section X begins inside the line"**: Perseus marks the section at a word that is not the
  first of the line; see whether the margin letter stands at this line or the next and number
  accordingly.
* **"the line is indented, but Perseus begins no speech or paragraph here"**: if the page indents
  it, put `¶` before it (or it is verse: `| `); otherwise leave it.
* **"the next printed line, read as “…”, matched no Perseus words"**: a line the draft may have
  lost, or a smudge. Check the page.
* **"Perseus marks a gap"**: copy what Burnet prints there (e.g. asterisks) and note it.

## The apparatus

* One output line per item: the full line number it refers to (`448b5`), a TAB, the item.
  Burnet gives the section letter and line ("b 5", "c 3"); within a section he gives only the
  next line number; take the Stephanus page from the text on the page (where the page holds the
  end of one Stephanus page and the start of the next, "a 2" after the change belongs to the new
  page). An item for several lines: `448b5-6`.
* Copy each item as printed: lemma, readings, sigla (B T W P F f and others, as printed; small
  letters for later hands, as printed: `b`, `t`, `f`; superscripts as Unicode superscripts:
  `B²`, `T²`), authorities, Latin. Greek with full accents. Ignore italics.
* Where Burnet says it in words, copy his words: `(suprascr. ὧν f)` stays as printed. Where he
  prints letters small above a word without words (a variant spelling in a manuscript), write
  them in parentheses with ss. after the word: `τοτὲ (π ss.) T`.
* A further item on the same line begins with its lemma alone; it belongs to the line of the
  item before it: give it that line's number.
* A colon or semicolon is written without a space before it (`B T P: πρόδικος F`).
* An item that runs on from the previous page belongs to the line it names; write it on the
  page where it begins. Leave out the signature at the foot of some pages ("PLATO, VOL. III. 17").
* Keep Burnet's line number even where it seems off by one, and say so under `--- notes`.

## Checking

Run, from `pipeline/`:

    .venv/bin/python -m anagnosis_pipeline check-gorgias-batch transcriptions/gorgias/batch-NN.md

It reports numbering that does not run on, apparatus numbers that name a line not on the page,
pages without an apparatus, elision written with ’ or ᾽, divided words, and every place where
the words now differ from Perseus (that is, every change of wording you made: each must be one
the image shows, and noted). It does not see a word moved to another line or a speaker's name
added or removed: note those under `--- notes` yourself. Fix what it reports, or explain under `--- notes`.

## Before you finish

For each page: every flag looked at; the apparatus complete, every item with a full line
number; the checker run clean (or each remark explained). Then say in your reply, for each page,
how many flags you checked, what you changed, and how many apparatus items you wrote.
