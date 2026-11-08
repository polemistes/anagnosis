# Checking Lake's Shepherd of Hermas: the Greek text, the critical apparatus, the margin

This folder holds the page-by-page transcription of the Shepherd of Hermas (Ποιμήν) in Kirsopp
Lake's Loeb edition (*The Apostolic Fathers*, vol. II, London 1913, the 1917 reprint), from the
Internet Archive scan `apostolicfathers02lakeuoft`: the Greek text verse by verse, Lake's critical
apparatus, and the Bible references he prints in the margin. `merge-hermas` turns the batch files
into `texts/hermas/grc.txt` (one line per verse) and `texts/hermas/commentary-lake-apparatus.md`.
The edition is in the public domain; the transcription is published under CC BY-SA 4.0. The brief
for the whole text is `pipeline/PLAN-hermas.md`.

**What ships is Lake's text with Lake's apparatus.** The text is not typed: `lake-pages hermas
draft` read every page with Tesseract and matched its words to J. Tauber and S. Macdonald's
digital text **of this same edition** (proofread twice against scans of the print). So the draft
and the page should agree almost everywhere: most flags are Tesseract's errors. But Tauber silently
corrected some of Lake's misprints (Vis. 2.2.5: Lake prints μενανοίας, Tauber has μετανοίας), and
may have erred elsewhere. **The page wins every time**: write what Lake prints, even a misprint,
and say so under notes (`2.2.5	μενανοίας as printed: a misprint`); misprints are corrected at the
merge, with a note in the apparatus.

Your work on each page:

1. **Check the flags** against the image and correct the batch file where it is wrong.
2. **Check every footnote mark** in the text (the draft placed them from another digital edition of
   Lake: confirm each on the page, its place and its number).
3. **Write the apparatus** from the image. Tesseract's two readings of it are a help, not a draft.
4. **Check the margin references** (pre-filled) against the left margin.

Do not re-read or retype unflagged verses word by word; do look at them in the crop as you check
the marks. Do not change anything you have not checked on the image. Never guess: where something
is unreadable, write `[illegible]` and say so under notes.

## Files

For each page `p-0020` (leaf 20 of the scan = Lake's p. 8; the page is the leaf less 12), in
`pipeline/build/lake-pages/hermas/`:

* `p-0020.md`: the check sheet: the flags, verse by verse; the page's lines as Tesseract read them;
  the margin as read; Tesseract's two readings of the apparatus (Greek first, English first).
* `p-0020-lines.png`: the flagged verses cut out of the page (each verse's printed lines), one
  under another, each labelled with its key. Look here first.
* `p-0020-app-l.png`, `p-0020-app-r.png`: the apparatus, left and right halves, enlarged (they
  overlap a little). Read the apparatus from these.
* `p-0020-margin.png`: the left margin, enlarged (the Bible references).
* `pages/leaf_0020.png`: the whole page (about 1780 pixels wide). You will need it for the
  footnote marks, which are small: open it for every page that has marks.

**Keep image requests light**: the lines image, the apparatus halves, the margin crop, and the
whole page once per page.

The batch file `pipeline/transcriptions/hermas/batch-NN.md` holds six pages:

```
=== p-0020
--- text
1.1.3+	ὑδάτων. διαβὰς οὖν τὸν ποταμὸν ἐκεῖνον ἦλθον εἰς τὰ ὁμαλὰ …
1.1.4	προσευχομένου δέ μου ἠνοίγη ὁ οὐρανός, …
1.1.7	ἀποκριθεὶς αὐτῇ λέγω· Εἰς σὲ ἥμαρτον; ποίῳ τόπῳ¹ ἢ πότε σοι αἰσχρὸν ῥῆμα ἐλάλησα; οὐ πάντοτέ σε ὡς θεὰν² ἡγησάμην; …
[chapter]	II
¶
1.2.1	Μετὰ τὸ λαλῆσαι αὐτὴν τὰ ῥήματα ταῦτα …
--- apparatus
1	τόπῳ ℵ* L₁, τρόπῳ ℵᶜAL₂(E).
2	θυγατέρα A, dominam E.
--- margin
1.1.6	Ps. 2, 4; 123, 1;
1.1.6	Gen. 1, 28; 8, 17; 9, 1; 28, 3 etc.
--- notes
1.1.7	(optional: what you checked and decided, one remark per line, starting with the verse)
```

The key and the text are separated by a single TAB. Edit the file in place, page by page, and
**save after each page**, so that nothing is lost if you are interrupted.

## Lake's page

The Greek stands on the left-hand (even) pages; the English translation faces it on the next leaf
and is **not** transcribed (it comes from elsewhere). On each Greek page:

* At the top the running head "THE APOSTOLIC FATHERS"; at the foot the page number (and on some
  pages a printer's signature, "B 2"): not text.
* **Headings**: where a book begins, Lake prints its title centred (ΠΟΙΜΗΝ on p. 6, over the whole
  work; Ὅρασις βʹ, Ἐντολὴ αʹ …), and **each chapter's number as a centred Roman numeral** (I, II,
  … XXXIII). These are `[title]<TAB>…` and `[chapter]<TAB>…` lines, as printed (the numeral in
  Latin capitals: `[chapter]<TAB>XXIX`). The draft wrote the numeral of the chapter that begins
  below it, and Tauber's heading for a title it could read: check both against the page.
* **The verses run on in paragraphs**, each begun by its number in the text ("2. μετὰ χρόνον …").
  A chapter's first verse ("1.") begins a new, indented line. **Lake's verse number is not
  copied**: the key carries it. The draft flags a verse whose number it did not read where Tauber
  begins it, or a number read where Tauber begins none: look whether the verse really begins there.
* **Footnote marks**: small raised numerals after a word (after its stop, if any): `τόπῳ¹`,
  `καταφθαρῆναι,¹`. They are **numbered afresh on each page** (1, 2, 3 …) and answer the apparatus
  items at the foot, which begin with the same raised numeral.
* **The apparatus** at the foot, in small type, the items running on: "¹ τόπῳ ℵ* L₁, τρόπῳ
  ℵᶜAL₂(E). ² θυγατέρα A, dominam E." Some items are long English remarks of Lake's.
* **The margin**: Bible references in small type in the left margin beside the line they belong
  to ("Ps. 2, 4; 123, 1;", "Deut. 30, 3 cf. Jer. 3, 22", "Mt. 18, 3", "Ps. 58, 6; etc.").

## The text: what the draft does, and what the flags mean

* **The key** is the verse: `book.chapter.verse` in the numbering of the digital texts, 27 books:
  1-5 the Visions (Vision 1 = book 1), 6-17 the Mandates (Mandate 1 = book 6, Mandate 4 = book 9),
  18-27 the Similitudes (Similitude 1 = 18, Similitude 9 = 26). `1.2.1` is Vision 1, chapter II,
  verse 1. You do not renumber; the keys follow Tauber's verses, which are Lake's.
* **A verse is on one line of the batch**, however many printed lines it takes on the page. **A
  verse that runs over to the next page is divided at the page break**: its part on the next page
  is keyed `1.1.3+` and is the first verse of that page's block. The words are where they are
  printed; **a word divided across the page break is written whole on the page where it begins**
  (and left out of the next page's `+` line). Within a page, a word divided at a line's end is
  simply written whole.
* **`¶`** on a line of its own before a verse Lake begins on a new, indented line (every chapter's
  first verse; sometimes another, before a speech or a letter). The draft put one where it saw an
  indent: check them.
* **Footnote marks** as raised digits, U+00B9 ¹, U+00B2 ², U+00B3 ³, U+2074 ⁴ …, directly after the
  word and its punctuation as printed, no space: `αὐτῇ,¹`. The draft placed each mark where the
  other digital edition (First1KGreek) has its note, numbered by the page as the draft divided the
  pages; **every mark is flagged**: look at the place on the page, move the mark to the word where
  Lake prints it, renumber if the page numbers it otherwise, add a mark the draft lacks, delete one
  the page does not print. The marks on a page must run 1, 2, 3 … and answer the apparatus items
  one for one.
* **Spelling and signs as Lake prints them**: elision ʼ (U+02BC), never ’ or ' or ᾽; the raised
  stop ·; the iota subscript as printed; brackets as printed (⟨ ⟩, [ ]); quotation marks as Lake
  prints them in the Greek (he prints none as a rule); capitals as printed (Lake capitalises the
  first word of direct speech after a raised stop: λέγων· Μακάριος ἤμην).

The flags, and what to do:

* **"X: the OCR reads “Y”"**: Tauber and the OCR differ. Almost always Tesseract's error (it reads
  Lake's ζ as ξ, χ as κ, loses a capital's breathing, reads ὦ as ὅ); change the text only where
  the print clearly shows something else than X, and then note it: that is a misprint of Lake's,
  or Tauber's error.
* **"X: not found in the OCR"**, **"which line it stands on is a guess"**: check the word is
  printed in this verse on this page (the page break: it may belong to the next page's `+` line).
* **"the OCR reads “Y” on a line of this verse, which Tauber does not have here"**: a word the page
  prints that the text lacks (add it), a margin reference read into the line, or noise.
* **"no verse number … read"**, **"the verse number … is read …"**, **"a verse number … where
  Tauber begins no verse"**: find the printed number; if Lake divides the verses otherwise than the
  keys, say so under notes with what the page shows (do not renumber on your own).
* **Chapter and title flags**: the numeral or title as printed; a `[chapter]` line stands directly
  above the chapter's first verse (with `¶` between them).

## The apparatus

* **One output line per item**: the footnote's number as printed (`1`, `2`, `3`), a TAB, the item
  without its raised numeral. Each raised numeral at the foot begins a new item.
* **An item belongs to the page where its mark stands in the text.** An item that runs over from
  the page before to the foot of this page belongs to the page before (rare). On p. 290 (leaf 302,
  where the Greek ends and the Latin begins) the page is shared by two blocks, `p-0302` in the last
  Greek batch and `l-0302` in `batch-latin.md`: each item goes in the block whose text holds its
  mark.
* **Copy each item exactly as printed**: the lemma, the readings, the sigla, Lake's Latin and
  English. Greek with full accents and breathings as printed; Latin and English as printed
  (italics ignored).
* **The sigla** (Lake's introduction, pp. 3-5): ℵ (Codex Sinaiticus; U+2135), with its hands ℵ*
  (the first hand), ℵᶜ, ℵᵃ (correctors: raised small letters ᶜ ᵃ); A (Codex Athous); H (the Hamburg
  fragment); the papyri Pᵃᵐ (Amherst), Pᵒˣ (Oxyrhynchus), Pᵇᵉʳ (Berlin), written with raised
  small letters as printed; the versions L₁ (Vulgate), L₂ (Palatine) with subscript digits
  (U+2081 ₁, U+2082 ₂), L (both), E (Ethiopic), C (Coptic); the Fathers Clem., Athan., Ant. (as
  printed). Sigla run together as printed (`ℵᶜAL₂(E)`, `AL₁`), a space where Lake leaves one.
  Parentheses around a siglum (`A(L)`, `(E)`) as printed: they mean the witness supports the
  reading loosely.
* **Abbreviations** as printed: om., add., cf., al., etc.; editors' names as printed (Hilgenfeld,
  Gebhardt, Harnack, Funk, Zahn …).
* Where Lake prints a dash between two ends of a long lemma ("ἁμαρτίας μου—ἁμαρτίας μου om. per
  homoiot. ℵL₂") write it as printed, with an em dash.

## The margin

The draft pre-filled the `--- margin` section from the other digital edition: one line per
reference, `verse<TAB>reference`, keyed by the verse beside whose line it stands (when the line
holds the end of one verse and the start of the next, the verse whose words stand nearest the
reference; if unclear, the verse that begins on the line). Check each against `p-NNNN-margin.png`:
the reference copied as printed (Lake writes "Ps. 2, 4; 123, 1;" with a comma between chapter and
verse, "cf." in small letters, "etc."), the verse key right; add any the page prints that the
draft lacks, delete any it does not print. A reference that runs over two printed lines is one
line of the batch.

## Checking

Run, from `pipeline/`:

    .venv/bin/python -m anagnosis_pipeline check-hermas-batch transcriptions/hermas/batch-NN.md

It reports pages missing, keys malformed or out of order, a `+` line not first on its page,
chapters without a `[chapter]` line or a numeral that does not match, footnote marks that do not
run 1, 2, 3 … or do not answer the apparatus numbers, margin references keyed to a verse not on the
page, elision written with ’ or ', a space before a stop, Latin letters in the Greek, and **every
place where the words now differ from Tauber's** (every change of wording you made: each must be
one the image shows; a remark is marked “(noted)” when your notes name its verse). Remarks on
Lake's own readings that you noted are expected and stay.

**Your own files.** Scripts, enlarged crops and other helpers go only in a folder of your own,
named after your batch file, under the session's scratchpad folder (e.g.
`<scratchpad>/hermas-batch-03/`); other agents work beside you at the same time and use the same
scratchpad, so never write a file directly in the scratchpad or in another agent's folder. Do not
commit.

## Before you finish

For each page: every flag looked at; every footnote mark checked on the page; the apparatus
complete, every item with its number; the margin references checked; the `[chapter]`, `[title]`
and `¶` lines against the page; the checker run clean or each remark explained (a noted reading of
Lake's is an explanation). Then say in your reply, for each page, how many flags you checked, what
you changed, how many marks and apparatus items the page has, and how many margin references.

## The Latin pages (`batch-latin.md`)

From p. 290 (leaf 302: after Sim. 9.30.2, where manuscript A ends) to p. 304 (leaf 316) Lake prints
the Latin version, with Greek where the papyri preserve it (Sim. 9.30.3-4, 9.31.5-6, 10.3.2-5).
The blocks are `=== l-0302` … `=== l-0316`, in the same format; the check text is Tauber's Latin
(the same edition), read by Tesseract with its Latin and Greek models, and the images are
`l-NNNN-lines.png`, `l-NNNN-app-l.png`, `l-NNNN-app-r.png`. Copy the Latin as printed (Lake's
spelling: "paenitentiam", "quodsi", u and v as printed, his punctuation and capitals), the Greek
with accents and breathings, and Lake's dots of omission as printed (`. . . .`). The book's title
on p. 298 is `[title]<TAB>Similitudo X` as printed. The Latin pages have few footnotes (Lake's
remarks in English: "At this point A ends …"; "The Greek which follows is a quotation preserved in
Antiochus"): each under its number, as on the Greek pages. The checker does not flag Latin letters
in this file.
