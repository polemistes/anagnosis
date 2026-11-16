# Lysias, the thirty-four speeches (Λυσίου λόγοι), from Hude's Oxford text

Decided with the author on 2026-11-16 after two assessments of the sources (memory note
"lysias-sources"). The pipeline's rules are those of `pipeline/PLAN-drama.md` and, for a prose
text read by OCR against a check text, `pipeline/PLAN-true-story.md` (read both first: this brief
names what differs). This file is the brief: follow it step by step in the order given, tick the
steps off under **Progress**, write every choice the brief does not settle under **Decisions**
(dated, with the pages looked at), and commit after each step, this file with it. Where the
brief leaves something open, take the choice that keeps the data closest to the printed page,
write it under Decisions and go on; the questions that only the author can answer are collected
under **For the author** and never block the next step. The work may be cut off at any moment:
every step saves to disk as it goes and can be run again from where it stopped (`git status`,
`git log -5`, Progress and Decisions here, then `grep -c '^=== ' pipeline/transcriptions/lysias/batch-*.md`
and the notes sections of the batch files show which pages an agent has finished).

## What ships, and the one rule behind it

**Hude's text with Hude's critical apparatus, all thirty-four speeches as one text.** Nothing of
Lamb's Greek ships. The Perseus text (Lamb's Loeb, 1930) is the *check text*: Tesseract reads
Hude's pages, the reading is matched word by word to Lamb to find where Tesseract erred, and
every disagreement is decided by an agent from the page image, Hude's reading winning. Where
Hude and Lamb differ (Lamb adopts other conjectures in places), Hude's word stands and his
apparatus under it records the variants. An apparatus that belongs to another text would make us
the editor; the same-edition rule of PLAN-drama.md forbids it. **We keep to the printed edition
and correct only evident misprints, each with a note** (`MISPRINTS` in `hude_merge.py`: the
batches keep what is printed, the text shows the right reading, and an apparatus note says "X:
Hude prints Y, a misprint; corrected in this edition").

The text is **not marked for sale**: no `google_play` line, nothing announced, no reader release.
Lysias is wholly in the public domain (Hude died in 1936), so its files are ordinary public files.

## Decisions already taken (do not reopen)

| what | source |
|---|---|
| Greek text and critical apparatus (one edition) | C. Hude, *Lysiae orationes*, Oxford Classical Texts, Clarendon Press, 1912 (the praefatio is signed Rome, 1 December 1911; Karl Hude 1860–1936). Scan **orationesrecogno00lysi** (Toronto, PIMS copy; 308 leaves, jp2 112 MB, 2306 × 3598 pixels a page, very clean; the publisher's list bound in at the end is dated August 1914, so the copy is a later issue from the same plates). The Archive's own OCR of this item is useless for the Greek; ours is run as always |
| check text (never shipped) | Perseus canonical-greekLit `tlg0540.tlg001` … `tlg034` `.perseus-grc2.xml` = W. R. M. Lamb's Loeb (1930), one file per speech, sections as `div subtype="section"`, with Lamb's 845 critical footnotes as `<note>` elements (stripped from the check text), 74 headings (`<label>`: Μάρτυρες, Νόμος, Ψήφισμα …) and 41 quotations (`<q>`). 56,162 words, 1,116 sections. Fetched to `pipeline/sources/drama/` |
| translation | **Twenty speeches** (2, 5, 7, 9, 10, 12, 13, 14, 16, 17, 19, 22, 23, 24, 25, 28, 30, 31, 32, 33): the anonymous literal translation of 1898 (*The Orations of Lysias*, Handy Literal Translations; Project Gutenberg #6969, sections numbered; `pipeline/sources/gutenberg/pg6969.txt`). **Four or five more** (1, 3, 26, 34, probably 21): John Gillies, *The Orations of Lysias and Isocrates*, London 1778 (scan `bim_eighteenth-century_the-orations-of-lysias-a_lysias_1778`, long-s print): where both exist the 1898 version is used. **Nine speeches go in without English** (4, 6, 8, 11, 15, 18, 20, 27, 29): no public-domain translation was found. Lamb's translation (Perseus) is protected until the end of 2031: never used. Nothing is ever translated by us or by a model |
| commentary, one per speech (read from scans, a later step) | C. D. Adams, *Lysias: Selected Speeches*, 1905 (scan `lysiasselectedsp0000char`) for 12, 16, 19, 22, 24, 25, 32, 34; M. H. Morgan, *Eight Orations of Lysias*, 1895 (`eightorations00lysi`) for 7, 23, 31; E. S. Shuckburgh, *Lysiae orationes XVI*, 1882 (`orationes16witha00lysiuoft`) for 5, 9, 10, 13, 14, 17, 28, 30. Fourteen speeches (1, 2, 3, 4, 6, 8, 11, 15, 18, 20, 21, 26, 27, 29, 33) have none of the three |
| syntax | Three sources, by speech (see "Syntax" below; **one question is open, for the author**): the AGDT's hand-made trees for **1, 14, 15, 23** (`pipeline/sources/treebanks/tlg0540.tlg0NN.perseus-grc1.tb.xml`, release 2.1 of 2015, CC BY-SA 3.0; annotated by Vanessa Gorman); **GLAUx `0540-0NN.xml`** (CC BY-SA 4.0; fetched to `pipeline/sources/glaux/`) for the rest: hand-made for **24** (the Pedalion trees, CC BY-SA 4.0), automatic for 26 speeches. **Speeches 12, 13 and 19** are in GLAUx only with Gorman's own later trees, which GLAUx's README lists as CC BY-NC-SA 4.0: not usable in an app that is sold, and GLAUx has no automatic trees for them. Automatic syntax is always shown as automatic |
| sigla | `sigla.md` written by hand from Hude's SIGLA page (leaf 18) and what the praefatio says of the manuscripts |
| slug, titles, product | `lysias`; the speeches are the text's books; product id proposed `lysias_speeches_hude` (see For the author); no `google_play` |
| pronunciation | `# pronunciation: attic` |

* **The unit of the text is the section**: one line of grc.txt per `speech.section` (`12.7` =
  speech 12, § 7: the reference everyone uses for Lysias), with `# layout: prose`. The speeches
  are books: `== book 12 · ΚΑΤΑ ΕΡΑΤΟΣΘΕΝΟΥΣ …` with Hude's title as printed. A section number
  is at most 100 and there are 34 speeches, so the reader's `book.line` numbering (book × 1000 +
  line) holds it, as it holds the True Story's two books. Paragraphs (`@ `) where Hude indents;
  a paragraph or a heading he sets inside a section continues the section on a line of its own
  with a letter (`1.30b`), and a section too long for a phone's page is divided at sentence ends
  in the same way (the True Story's `split_long`: the reader joins the parts and shows the
  number once).
* **The batch files the agents check are per printed line**, because Hude's apparatus cites the
  lines of his page. **Hude prints no page numbers**, so a line's key is the scan's leaf and the
  line's place on that page: `28.5` is line 5 of leaf 28, whose image is `p-0028`. The merge joins
  the lines into sections.
* **Apparatus items** go under the section that holds the lemma, copied as printed (Greek,
  Latin, sigla, the scholars' names), **without Hude's line number in front**: it refers to his
  page, which the reader does not see; the lemma identifies the word. In the batch every item
  has its line number (Hude prints the number once and runs the further items of the same line
  on without it: each gets the number of the item before it, as in the Gorgias). The merge finds
  the lemma's words on the line named; where a line holds the end of one section and the start
  of the next, the lemma decides ("alt. τὴν" is the second τὴν of the line).
* **Two checks at the merge** (step 6): (a) every item's lemma is looked for on its line; a miss
  is SERIOUS where the text may have slipped to Lamb's reading (a `lemma]` not in the text; or
  Hude's first reading missing while a later reading of the same item stands in the text) and
  WEAK otherwise (a conjecture, a note in Latin); an agent settles the serious ones from the
  page. (b) Every section of the check text once and in order, every speech with its title.
* **Not usable, ever**: Lamb's translation and notes; Thalheim's Teubner as text (another
  edition: it may be cited by nobody here); Carey's Oxford text (2007); Todd's commentary and
  translation; Edwards and Usher; the Perseus English of any speech.
* **Agents**: page agents on Opus (PLAN-sophocles.md, "Which model reads"), one per batch of six
  pages, at most ten at once and fewer while the author works at the laptop, as workflows; every
  agent saves its batch file after each page and keeps its helper files in a folder of its own
  under `pipeline/build/agent-scratch/` (on disk; the session scratchpad and `/tmp` are RAM disks:
  nothing large goes there). Heavy local jobs (OCR, drafts) run with `nice -n 19` and at most six
  workers; `free -g` first.

## Hude's book

308 leaves in the scan (0–307; the jp2 files carry these numbers). Leaves 0, 36, 37, 44, 45 and
307 are hidden by the scan's own page list. **Leaves 36–37 and 44–45 are four pages of speech 2
(2.23–2.30 and 2.59–2.66)** that the scan holds only as the camera's uncropped frames, marked
"Delete": the Archive's online reader and its page images skip them, the jp2 files have them, and
they are used here (Decisions). The page image the Archive serves as `page/n<N>` is leaf N+1 up
to leaf 35, leaf N+3 for 38–43, leaf N+5 from 46.

| part | leaves | |
|---|---|---|
| series title, title page (no date; verso "Excudebat Horatius Hart") | 5, 7 | |
| Praefatio, pp. iii–x | 9–16 | Latin: the manuscripts (the Palatinus X of the 12th century, the source of all others for speeches 3–31; speeches 1–2 also in other families: H, P, and F V for 2), the first hand's index of X, the editions used; pp. viii–ix a list of spellings adopted, with references; signed "Scribebam Romae Kal. Dec. MCMXI" |
| SIGLA | 18 | three lists: speeches 1–31 (X and its correcting hands X¹ Xᶜ Xᶜ(1) Xʳ Xˢ, C D E F f G g H h I K M N O P Q q R S U V W, L = consensus codicum, Aldus, marg. Ald., Turr., the signs + / [X]); speeches 32–34 (the manuscripts of Dionysius of Halicarnassus F G M T); speech 35 (Plato's B T W) |
| **Speeches I–XXXIV** | **19–287** | **269 pages**, none missing; every speech begins on a fresh page (the page after the last of the speech before, left or right) |
| XXXV, the Eroticus (Plato, *Phaedrus* 230e–234c) | 288–292 | not part of this text: see For the author |
| Index nominum | 293–296 | not shipped |
| the publisher's list, August 1914 | 297– | |

Speeches 32, 33 and 34 survive only as quotations in Dionysius of Halicarnassus; Hude prints
Dionysius's introductory words before each as ΥΠΟΘΕΣΙΣ ΔΙΟΝΥΣΙΟΥ in smaller type, with the
Dionysius page numbers in the margin, and ends the fragment with a row of dots. Speech 2 (the
Funeral Oration) has the fullest apparatus (more manuscripts: F V f g and others).

## Hude's page

Looked at: leaves 19, 20, 21, 28, 29, 30, 284 and the first and last leaves of the parts (page
images at full size), 2026-11-16.

* **The running head** (left-hand page: the Stephanus page in brackets, ΛΥΣΙΟΥ, the speech's
  number; right-hand page: the number, the speech's short title, the Stephanus page): not text.
* **A speech's first page** begins lower down: the number as a Roman numeral, the title in
  capitals on one to three lines ("Steph." and the first Stephanus page beside it for speech 1);
  for speeches 32–34 the heading ΥΠΟΘΕΣΙΣ ΔΙΟΝΥΣΙΟΥ. and the hypothesis in smaller type. The
  numeral, the title and the hypothesis's heading are **not counted as lines**; the lines of the
  hypothesis are (p-0284: the 5 and 10 stand in the hypothesis, the 15 at the speech's second
  line).
* **The text**: 27–28 lines on a full page. **Line numbers** by fives (5, 10, 15 …), beginning
  anew on every page, in the **inner** margin: at the left on a right-hand page (an odd leaf), at
  the right on a left-hand page (an even leaf). **Section numbers** in the **outer** margin
  beside the line where the section begins; a section begins at the start of a line or, more
  often, inside one after a wider space. **Stephanus pages** stand in square brackets in the
  outer margin too ([92]); where both fall on one line the section number is set above or below
  the bracket. The Stephanus pages are not recorded (see Decisions).
* **Headings inside a speech** (ΜΑΡΤΥΡΕΣ. ΝΟΜΟΣ. ΨΗΦΙΣΜΑ.), centred in small capitals with a
  full stop, **count as lines** (p-0028: ΜΑΡΤΥΡΕΣ. is line 3; the 5 stands two lines below it).
* A new paragraph is indented; Hude also begins a new train of thought inside a line with a
  capital after a wider space ("αὐτήν.   Πρῶτον μὲν οὖν"): the capital is kept, nothing else.
  Direct speech stands in single quotation marks (‘ἵνα σύ γε’ ἔφη ‘πειρᾷς …’). Elision is
  printed as an apostrophe; a lacuna as three spaced dots; deletions in [ ], additions in ⟨ ⟩.
* **The apparatus** at the foot in small type, no rule above it, the items run on and
  separated by wider spaces: the line number, the lemma, the reading's authority, then after a
  colon the other readings ("3 εἴητε marg. Ald. : εἰ ἦτε C H X   6 τὰς ⟨μεγίστας⟩ Reiske   7
  μικρὰς Xᶜ (1) : μακρὰς C H P X¹"); further items on the same line follow without a number
  ("18 ἀποδεῖξαι Herwerden   ἐμοίχευσεν Contius"); ranges "22-23"; an item on a speech's title
  has no number ("Λυσίου ἐπιτάφιος F V", p-0030). Latin throughout, scholars' names in full or
  shortened (Bekk., Turr.). Raised letters and digits on the sigla (X¹, Xᶜ, Mᶜ, P¹, Fˢ).
* At the foot of some pages the printer's signature ("LYS. 1", "1*"): not text.

## The reference system

`speech.section`: `1.1` … `34.11`, 1,116 sections. The reader's citation is "Lysias 12.7"; the
book chooser lists the 34 speeches. Hypotheses (speeches 32–34) are proposed as section 0 of
their speech (`34.0`; see For the author). Notes and translations are keyed by section
(`## 12.7`), as the True Story's.

## Syntax

GLAUx has all 34 speeches (one file each, `div_section` on every word, so each word's section is
known and the alignment, `odyssey.align` as for every GLAUx text, runs speech by speech). It
marks every sentence `analysis="manual"` or `"auto"`, and its `metadata.txt` names where the
manual trees come from (looked up 2026-11-16):

| speeches | in GLAUx | source of the trees | usable |
|---|---|---|---|
| 1, 14, 15, 23 | manual | "Vanessa Gorman's Ancient Greek Prose Dependency Treebanks" (GLAUx's README: CC BY-NC-SA 4.0) | not from GLAUx; **but the same speeches are in the AGDT release 2.1** (2015, CC BY-SA 3.0, annotator Vanessa Gorman, in `pipeline/sources/treebanks/`): use those |
| 12, 13, 19 | manual | Gorman's treebanks only | **no**: non-commercial licence, and no automatic trees exist in GLAUx for them |
| 24 | manual | the Pedalion trees (CC BY-SA 4.0) | yes, hand-made |
| the other 26 | automatic | GLAUx's parser | yes, shown as automatic |

So five speeches have hand-made trees we may use, 26 automatic ones, and **three (12, 13, 19:
14,000 words, among them the two longest and best-known speeches) have none we may use** until
the author decides (For the author): ask Vanessa Gorman for leave; ship those three without
syntax (lemmas and forms from the analyser, as for words the treebanks lack); or wait for a
GLAUx release that offers automatic trees for them.

What the merge needs that the other texts do not: `Play.glaux` and `Play.treebank` name one file
each, here the source is chosen per speech (a table in `hude_merge.py`); and **the label is per
speech**, not per text. The text files carry one `# syntax: automatic` line for the whole text
today and the reader shows one label per text: a per-book label (for instance a header key
`# syntax-manual: 1 14 15 23 24` that the build reads into the sections table) is a small change
to the build and the reader, to be made at step 7 if the author agrees; until then the whole
text would be labelled automatic. The AGDT files were made on Lamb's text, like GLAUx's: both
are aligned to Hude's words, and a word Hude has otherwise gets the analyser's reading. Not
built in this stage.

## Steps

1. **Module work** (tests with each change; `cd pipeline && .venv/bin/python -m unittest discover -s tests`). Done: see Progress.
2. **Leaves and layout.** Done: the tables above.
3. **OCR and draft.** `hude-pages lysias fetch | ocr | draft` in the background at low priority
   (`TMPDIR=pipeline/build/tmp DRAMA_WORKERS=5 nice -n 19 …`); read the summary. More than a
   quarter of the lines flagged on this clean print means the matching or the layout is wrong:
   fix the module, do not send it to agents.
4. **Text and apparatus batches, first pass.** One agent per batch
   (`pipeline/transcriptions/lysias/batch-NN.md`, six pages each, 45 batches) with
   `pipeline/transcriptions/lysias/INSTRUCTIONS.md`; the workflow
   `pipeline/transcriptions/lysias/lysias-text.workflow.js` (args under "Hand-over"); the checker
   on every returned file (`check-lysias-batch`); unresolved remarks to a fresh agent; commit
   every few batches.
5. **Second passes.** `lysias-residuals` lists what the checked lines and the OCR still disagree
   on (punctuation, accents, brackets, words read without confidence): the residual pass
   (`RESIDUALS.md`, two batches per agent). Then the independent review (`REVIEW.md`, one agent
   per batch) with the reading task of the Sophocles reviews. The author's rule decides how far
   each goes: **a pass stays only if it catches errors that would otherwise remain.** Run both
   on the first eight batches (speeches 1–3), count what each changed, and write the result
   under Decisions before running them on the rest. (For the plays from an Oxford text whose
   check text was the same edition the residual pass found almost nothing and was dropped; here
   the check text is another edition, with its own punctuation, so the residual pass is expected
   to earn its place.)
6. **Merge and the checks.** `merge-lysias` (first into a scratch folder: `--out
   pipeline/build/agent-scratch/lysias/texts`); read `pipeline/build/lysias-merge.log`: the
   problems, the SERIOUS lemma misses (an agent with the page crops fixes the text where it
   slipped and writes each case under Decisions), the WEAK ones read through once; ten sections
   chosen at random compared with the page by eye; the misprints found by the agents (their
   notes say "as printed") put before the author, then into `MISPRINTS`.
7. **Words and syntax.** The token step for 34 GLAUx files (see "Syntax"), the analyser for the
   rest, the review list `pipeline/build/lysias-review.tsv`, `HAND_ANALYSES` / `LEMMA_FIXES` in
   drama_fixes.py.
8. **Translations.** (a) The 1898 version: `hude_merge.translation_1898` reads the Gutenberg
   text by speech and section (headings "ORATION II." …, with the transcription's "XXXL." and
   "XXXIL."; most section numbers stand in the text, a segment runs from one printed number to
   the next): `eng-1898.txt`. At 13.65–68 it follows the same order as Hude, so nothing is
   re-filed. (b) Gillies (1778) for the six speeches the 1898 version lacks: see "Gillies"
   below: transcribed by the prose route, then laid beside the Greek by paragraphs
   (the alignment pass, `transcriptions/lysias/GILLIES-ALIGN.md`; `hude_merge.write_gillies`:
   `eng-gillies.txt`).
9. **Commentaries and introductions.** See "The commentaries" below: every speech's commentary
   an entry of the prose route, 74 batches; first check and second reading by agents
   (`lysias-prose.workflow.js`); `merge-lysias` then writes `commentary-adams.md`,
   `commentary-morgan.md`, `commentary-shuckburgh.md`, `introduction.md` and `appendix.md`
   (`hude_notes.py`) and the log `pipeline/build/lysias-notes.log`.
10. **sigla.md, glossary.md, shortdefs.tsv, aliases.tsv, about.md** (no `google_play`; a
    `product_id` only once the author has confirmed it), the texts/README.md section.
11. **Build and emulator check** (`build --only lysias`, `check`, `catalog`, the pack; the
    emulator check of PLAN-drama.md step 10: a book chooser of 34 speeches, a heading inside a
    speech, a hypothesis, a speech without English, the apparatus, the syntax label). Memory
    rules as PLAN-hermas.md.

## The commentaries (step 9)

One commentary to a speech, from three school editions; nineteen speeches have one. Each speech
is **an entry of the prose route of its own** (`drama.LYSIAS_NOTES`; `drama-prose lysias-12
notes|intro fetch|ocr|draft`; batches `pipeline/transcriptions/drama/lysias-12/notes-NN.md`,
`intro-NN.md`; crops `pipeline/build/drama-prose/lysias-12/`; checker `check-drama-prose
lysias-12 <file>`), because the prose route's checks expect a note's numbers to run upwards
within an entry, as a play's do. The agents' brief is the section "Lysias: the three
commentaries, their introductions, and Gillies's translation" of
`pipeline/transcriptions/drama/INSTRUCTIONS-prose.md`.

| book | scan (leaf = page + …) | what ships | what is left out |
|---|---|---|---|
| **Adams**, *Lysias: Selected Speeches*, 1905 | `lysiasselectedsp0000char` (416 leaves, + 8) | his general introduction pp. 9–42 (leaves 17–50: life, works, style, the revolutions of 411 and 404); for 12, 16, 19, 22, 24, 25, 32, 34 the introduction before each speech (with its outline and "Comments on argument and style") and the notes under his text; Appendix I–V pp. 327–362 (leaves 335–370: Chronological outline, Athenian legal procedure, Rhetorical terms, Money and prices at Athens, The manuscripts): his notes cite its numbered paragraphs ("App. § 57. 3") | his Greek text; Appendix VI Bibliography; VII Critical notes (pp. 363–389: on his own text); the indices; the preface |
| **Morgan**, *Eight Orations*, 1895 (the scan is the 1900 printing) | `eightorations00lysi` (296 leaves, + 64) | for 7, 23, 31 the introduction before each speech and the notes under his text | his general introduction (pp. vii–lii), his other five speeches (12, 16, 22, 24, 32: Adams's are used), his Greek text, the appendices and indices |
| **Shuckburgh**, *Lysiae Orationes XVI*, 1882 | `orationes16witha00lysiuoft` (430 leaves, + 38) | for 5, 9, 10, 13, 14, 17, 28, 30 the notes at the back (pp. 193 ff.), with his introduction to each speech, which stands in square brackets at the head of its notes | his general introduction, his Greek text with its English summaries (read only to map his line numbers), his other eight speeches, the appendices and indices |

Leaves of each speech's parts: `drama.LYSIAS_NOTES` (speech: editor, introduction leaves, notes
leaves, last section, the commentator's text leaves). Sizes: Adams 353 pages in 51 batches,
3,888 flags; Morgan 54 pages, 9 batches, 898 flags; Shuckburgh 86 pages, 14 batches, 1,011
flags: 493 pages, 74 batches, 5,797 flags (12 a page).

**The pages.** Adams and Morgan (`notes_layout="college"`): the editor's Greek at the top of the
page in large type, the notes under it in two columns in small type, no rule; found as the
earlier two-column commentary under verses is (the first three rows where a left and a right
column stand side by side). A note opens an indented paragraph with its **section number**;
further lemmas follow after a dash, each made a paragraph of its own; the lemma runs to its
colon (`college_lemma`). Morgan's footnotes to his introductions stand in two columns under the
text (`intro_foot_columns`). Shuckburgh (`notes_layout="back"`): one column; a speech's notes
begin under "ORATION IV. [10.]" (his number, then the usual one), on a page that may also hold
the end of the speech before: only this speech's part is taken (`_own_oration`); the figures in
the outer margin are the pages of his text and are dropped; a note opens with **the line number
of his own text**, counted through the speech.

**Every note ends on a reference speech.section with its lemma** (`hude_notes.py`, run by
`merge-lysias`). Adams's and Morgan's numbers are sections. Shuckburgh's are lines of his own
text: his text pages (leaves in `LYSIAS_NOTES`) are read by Tesseract and matched to the check
text, which gives the sections of the words on each of his lines (`shuckburgh_lines`; for speech
10: 212 lines, the printed fives agreeing with the count; 13.65–68 renumbered to Hude's order).
Then, for all three, **the lemma decides**: it is looked for in the section named, then in the two
sections either side (Hude marks the line where a section begins, the school editions follow the
vulgate division, and the two differ by some words at many section starts), and the note is
filed where its lemma stands. **A lemma that is not in Hude's text** (the commentator reads
otherwise than Hude, or abbreviates) keeps the section the commentator names and its lemma as he
prints it; it is listed in `pipeline/build/lysias-notes.log` (`MISS`), as are the notes moved to
a neighbouring section (`NEAR`), for one reader to go through after the batches are checked. The
trial merge on the unchecked drafts: 2,761 paragraphs under 641 sections; 192 moved by their
lemma, 309 lemmas not found (most of them OCR damage in the draft's lemma; the number to look at
is the one after the check).

**The introduction** (`introduction.md`): Adams's general introduction, then a chapter for each
of the nineteen speeches that has one, in the order of the speeches, headed with the speech's
number, English name and commentator ("# 12. Against Eratosthenes (Charles Darwin Adams)").
**The appendix** (`appendix.md`): Adams's Appendix I–V.

**Pilot** (four pages checked by the brief by the set-up session; their batch files carry the
answers): Adams p-0069 and p-0078 (speech 12), Morgan p-0172 (speech 23), Shuckburgh p-0259
(speech 10). What they showed, all now in the brief or the tool: the OCR knows no italics and
misreads italic words ("7 am guilty", "20 go", "27 seemed"): the columns must be read through,
not only the flags; Adams's braced displays and spaced colons; a page that opens with a dash and
a lemma opens a paragraph of the note before, not a run-on; figures of references misread (GMT.
592 as 502, § 8 as "καὶ ὃ", 16. 8 as "τό. 8"); a bold lemma read in Latin letters is not cut
("— kal: αἴϑ8ο." for — **καί**: *also*.); Shuckburgh's margin figures, his two dots of omission,
his bracketed introduction, his bold Greek inside a note.

## Gillies (step 8)

John Gillies, *The Orations of Lysias and Isocrates*, London 1778 (scan
`bim_eighteenth-century_the-orations-of-lysias-a_lysias_1778`, 676 leaves, a bitonal film scan
at 800 ppi, clean; the jp2 zip is 8 GB, so leaves are fetched one by one). **What he really has**
(his table of contents, and the first pages of six orations looked at on the page images): of
Lysias eighteen speeches, in this order: 2 (p. 81), 14 (195), 13 (233), 12 (257), 25 (285),
34 (319), 21 (329), 26 (341), 31 (353), 16 (365), 7 (377), 17 (389), 19 (399), 1 (419), 4 (433),
3 (439), 32 (453), 10 (465); each has an introduction of his own before it (not taken). Twelve of
them the 1898 version covers; **Gillies is needed for six: 1, 3, 4, 21, 26, 34**. So speech 21 is
his "Defence of a Citizen accused of receiving a Bribe" (confirmed: it opens "I had no sooner
become of age, under the archonship …"), and **speech 4 has a translation after all** (his
"Defence … of a Citizen accused of giving a Wound from Malice aforethought"): the speeches
without English are eight, not nine: 6, 8, 11, 15, 18, 20, 27, 29. Leaves (page + 175 up to
p. 350, + 174 from p. 419): 1: 593–602; 3: 613–623; 4: 607–612; 21: 504–511; 26: 516–522;
34: 494–496 (`drama.LYSIAS_GILLIES`; entries `lysias-gillies-NN`, kind `intro`).

**The sample**: speech 4 (six pages) fetched, read and drafted by the prose route
(`transcriptions/drama/lysias-gillies-04/intro-01.md`, 93 flags). The print has the long s:
`drama_prose.long_s` writes it s wherever that turns a non-word into an English word ("fhould",
"poffeffion", "impoflible"); a word that is English both ways (same/fame, so/fo, sight/fight) it
cannot decide, and the draft lists those per page for the agent. Tesseract garbles the spaced
capitals of the title and the ct ligature; the body reads well.

**How it is laid beside the Greek** (proposed; For the author). Gillies is a free version without
section numbers, in long paragraphs, and he recasts sentences; the 1898 version by contrast
follows the sections. So: by paragraph. After the transcription is checked, **an alignment
pass** (one agent per speech, with Hude's Greek of that speech and the checked English; proper
names, numbers and the order of events fix the places) writes at the head of each of Gillies's
paragraphs the section of Hude's text where it begins (`§7 `); a paragraph that begins in the
middle of a section takes that section; the merge files each paragraph under its section
(`eng-gillies.txt`) and the reader shows it beside the Greek from that section on. Nothing is
cut, reordered or reworded; where Gillies leaves something out or adds, the paragraph simply
runs on. `about.md` says that these six are in a free eighteenth-century version.

**The other five speeches** (1, 3, 21, 26, 34) are fetched, read and drafted (2026-11-16):
entries `lysias-gillies-01`, `-03`, `-21`, `-26`, `-34` beside the sample `-04`. On the drafts the
last page of each oration was found (the ranges first given ran on into the title leaf and the
introduction of the next oration) and the ranges cut back to the oration itself: 1: leaves
593–602; 3: 613–623; 4: 607–612; 21: 504–511; 26: 516–522; 34: 494–496
(`drama.LYSIAS_GILLIES`). In all **45 pages in 8 batch files, 1,726 flags**: speech 1: 438 (10
pages, two files); 3: 288 (11 pages, two files); 4: 93 (6 pages); 21: 620 (8 pages); 26: 237
(7 pages); 34: 50 (3 pages). The flags are many for two reasons, both in the brief: the long s,
and, on this film, the print of the other side showing through the paper, which Tesseract reads
as lines of stray letters (one page of speech 21 has 136 flags, most of them such noise; the
agent deletes the lines and answers their flags `noise` after seeing on the image that nothing
is printed there). The oration's heading in widely spaced capitals is read badly or not at all
and is typed from the image.

**The alignment pass, as written** (`transcriptions/lysias/GILLIES-ALIGN.md`, the script
`lysias-gillies-align.workflow.js`; nothing started). It runs on a speech only after its
transcription has had its check and second reading and **is committed**. The agent writes one
thing into the text: the mark `§N ` (the number of a section of Hude's Greek). A mark stands at
the head of every paragraph of Gillies; and, so that a long paragraph does not sit beside one
section while the next five have nothing beside them, also inside a paragraph before a sentence
of his that plainly begins where a section of the Greek begins. The marks rise; what he leaves
out has no mark; what he transposes stays where he put it, unmarked, with a remark. The agent
does not translate and may not open another translation. Two guards: the brief's single rule
(marks only), and the checker `check-gillies-marks N`, which compares the marked file with the
committed transcription (any difference that is not a mark is reported), checks that the marks
are sections of the speech and rise, and lists each mark with the first words of the English and
of the Greek for the eye. A second agent then checks the places (the script's `review`). The
merge takes the text from one mark to the next as one segment under that section
(`hude_merge.gillies_segments`); a speech without marks is left out and named in the log. The
prose checker (`check-drama-prose`) gives the same output with the marks as without.

## The words without trees: the checking pass (speeches 12, 13, 19)

**Why.** In these speeches every word has the lemma and form the analyser gives the word by
itself. Against the hand-made trees of speeches 1, 14, 15, 23, 24 (7,590 words, each given to
the analyser alone) that reading differs from the trees' in 5.8 words of a hundred: the case in
214 words, the lemma in 190, the number in 73, mood, tense, person, voice in fewer. Counted as
the same reading: gender, pronoun or adjective, particle or adverb, middle or passive, which the
trees themselves do not treat alike (`hude_analyses.signature`).

**What the agent does.** It sees a section's Greek and, for each word whose spelling allows more
than one reading, the readings (lemma, tag, the tag in words; the present reading first), and
writes the number of the one that is right in the sentence. A reading that is not offered can
only be given as `other: lemma tag reason`; `? reason` keeps the present reading. It translates
nothing and may not open the trees, the tokens or a translation. Brief:
`transcriptions/lysias/ANALYSES.md`.

**Which words.** Those where the analyser's readings of exactly this spelling differ in lemma,
person, number, tense, mood, voice or case; for the commonest words (the article, καί, οὗτος …:
`STOP`) only readings of their own lemma that the treebanks know (the case of τὸ, not whether
καί is a form of καίω); a tag with letters missing beside a fuller one is dropped; at most eight
readings. On the speeches with trees this shows 37 % of the words and holds 83 % of the
differences. Words settled by hand (`HAND_ANALYSES`) are not asked about.

**The jobs** (`lysias-analyses jobs`; an existing file is never written again):
`transcriptions/lysias/analyses/job-01.tsv` … `job-28.tsv`, about 160 words to decide each (a
run of whole sections, about 400 words of text): speech 12 in jobs 01–10, 13 in 11–21, 19 in
22–28; 4,214 words to decide in all. **Jobs 91 and 92 are the control**: speech 1, 1.1–1.10
(154 words to decide) and speech 24, 24.1–24.10 (164), which have hand-made trees (by two
different annotators) and are set exactly as the others, from the analyser alone; the agents are
not told.

**The checker**: `lysias-analyses check FILE…`: every word answered, the number within the
list, `other:` with a lemma, a well-formed tag and a reason, and nothing but the answers changed
(compared with the committed file).

**How the answers enter the build.** The finished job files are the table:
`hude_analyses.answers()` reads every job of 12, 13, 19 in which all words are answered, and
`hude_merge.tokens` gives each word its chosen lemma and tag (after the rules, before the hand
analyses and the lemma fixes; a word whose form no longer matches the file goes to the review
list). `tokens.tsv` is never edited by hand; `merge-lysias` prints how many readings the table
changed. The control jobs never reach the merge.

**The measurement** (`lysias-analyses measure`): for every word of the two control stretches
(985 words) it compares the reading with the trees' before the pass (the analyser alone) and
after it (the agent's choice where it made one), and prints the words differing before and
after, those corrected and those spoiled, with each spoiled word and each word still differing.
Before: 56 words differ (5.7 %: 3.6 % in speech 1, 7.6 % in speech 24). With every choice right
the pass would leave 14 (1.4 %: nine words it does not show, five where the trees' reading is not
among the analyser's). **The rule for going on**: run the two control jobs first; the pass goes
on to jobs 01–28 if it removes at least half of the differences (56 down to 28 or fewer) and
spoils no more than one word for every ten it corrects, the spoiled words read by eye first (a
few are the trees' own slips or conventions). If a cheaper model fails that, the control files
are restored from git and run again with the stronger model; if that fails too, the pass is
dropped and the speeches stay as they are, with the line in about.md.

## The reader (the change is made: commit 757b603, by the reader's own session)

**Made on 2026-11-16 (757b603)**, as described below and a little more: the syntax label goes by
speech (`WorkData.syntaxByBook`, `automaticSyntaxAt`, `automaticSyntaxOfSentence`, read from the
meta key `syntax_by_book`: the word sheet's "(automatic)" and the syntax view's banner follow the
speech in view; a text without the key is as before); the chooser offers the speeches by number
and name (`Book.hasTitle`: a label "12 · Κατὰ Ἐρατοσθένους …" makes the book named, two lines at
most; an epic's "1 · Α" stays "Book 1 · Α"); the English column of a speech that has no
translation says so; a section 0 (the hypotheses) carries no number; the asset pack
`app/packs/lysias` with its entries in the Gradle files; unit tests `SpeechesTest`. Left as it
is: the page range at the foot reads "§§ 0–…" on a page that begins with a hypothesis. Two lines
the app shows once for the whole text cannot follow the speech, so they are worded for the mixed
sources in about.md: the shop's "Syntax:" line (`# syntax:`) and the credits' "Lemmas,
morphology and syntax:" line (`# syntax_source:`). What follows is the description the change
was made from.

Two things the reader needs for this text; both are small and neither changes another text.
The files are all under `app/shared/src/commonMain/kotlin/no/anagnosis/`: `data/Models.kt`
(both changes), `data/AnagnosisRepository.kt` and `ui/ReaderScreen.kt` (the label); line numbers
as on 2026-11-16. Until it is made, the reader shows Lysias with every speech's syntax called
automatic (also the five hand-made ones) and a chooser of bare numbers 1–34; nothing breaks.
The built database carries what is needed: checked in `data/lysias.sqlite`: meta
`syntax_by_book = 1=manual 14=manual 15=manual 23=manual 24=manual 12=none 13=none 19=none`,
34 level-1 sections labelled "1 · Ὑπὲρ τοῦ Ἐρατοσθένους φόνου ἀπολογία" and so on.

1. **The syntax label by speech.** Today `AnagnosisRepository` reads the meta key `syntax` once
   (`automaticSyntax = selectMeta("syntax") == "automatic"`, AnagnosisRepository.kt line 136) and
   uses it in three places: the word sheet's role line ("… (automatic)", line 169), the syntax
   screen (`SyntaxScreen(…, automatic = data.automaticSyntax)`, ReaderScreen.kt line 979) and the
   search screen's remark on lemma search (SearchScreen.kt line 390). The built database now also
   carries the meta key **`syntax_by_book`** for a text that has one: `"1=manual 14=manual
   15=manual 23=manual 24=manual 12=none 13=none 19=none"` (the books that differ from the
   text's own `syntax` value). The change: `WorkData` gets `syntaxByBook: Map<Int, String>`
   (parsed from that key; empty for every other text) and a function `automaticSyntaxAt(nInt:
   Long): Boolean` = `when (syntaxByBook[bookOf(nInt)]) { "manual" -> false; "none" -> false;
   null -> automaticSyntax; else -> true }`; the word sheet and the syntax screen call it with
   the token's line instead of reading `automaticSyntax`; the search remark stays as it is (the
   text as a whole is mostly automatic). A speech marked `none` has no sentence ids on its
   tokens, so the reader already offers no syntax there (the Syntax button is shown only for a
   token with a sentence): nothing to do but check it on the emulator. The pipeline side is
   done: `hude_merge.merge` writes `# syntax-by-book: …` into grc.txt and `build.build_work`
   copies it into `meta` (other texts have no such line and get no such key).
2. **The chooser of 34 speeches.** `WorkData.books` (Models.kt line 100) already builds the
   list from the level-1 sections, with each section's label (`"12 · Κατὰ Ἐρατοσθένους τοῦ
   γενομένου …"`), but marks a book `named` only for a verse-numbered text (the New Testament);
   for a text numbered book.line the chooser shows the number alone, as for the Odyssey's
   books (`Book.name`, `Book.title`, Models.kt lines 162–167: a named book is called by its
   label, another "Book" and its number). The change (Models.kt line 103): `named = verses || label is not just the number` (or: `named` when the
   section's label holds " · " and a name after it), so that the chooser lists "12 · Κατὰ
   Ἐρατοσθένους …"; the list must scroll (34 rows; the New Testament's 27 already do) and a
   long name must wrap or be cut with an ellipsis (the longest is 67 letters). The True Story's
   two books ("1 · Α") would then show their label too, which is what its section label says.
   To check on the emulator with the rest of step 11: the `!` lines (headings inside a speech)
   in prose, a hypothesis (section 0, shown as "§ 0": perhaps better without a number), a speech
   without English, a speech without syntax.

## Hand-over: the agents' runs

Everything the agents read is in `pipeline/transcriptions/lysias/`: `INSTRUCTIONS.md` (the
first pass), `RESIDUALS.md`, `REVIEW.md`; the scripts `lysias-text.workflow.js` and
`lysias-pass.workflow.js`. Their crops and check sheets are in `pipeline/build/hude-pages/lysias/`
(git-ignored; made again by `hude-pages lysias draft`, which never overwrites a batch file),
the whole pages in `pipeline/build/drama-scans/orationesrecogno00lysi/pages/`. Scratch for the
agents: `pipeline/build/agent-scratch/` (on disk). **Batch 01 is done (the pilot): the first run
begins with batch 02.**

**First pass** (`lysias-text.workflow.js`; model opus, general-purpose; ten at once at most,
fewer while the laptop is in use):

```json
{ "scratch": "/home/proteus/koding/anagnosis/pipeline/build/agent-scratch", "atOnce": 8,
  "batches": [
    {"id": "02", "first": "p-0025", "last": "p-0030"}, {"id": "03", "first": "p-0031", "last": "p-0036"},
    {"id": "04", "first": "p-0037", "last": "p-0042"}, {"id": "05", "first": "p-0043", "last": "p-0048"},
    {"id": "06", "first": "p-0049", "last": "p-0054"}, {"id": "07", "first": "p-0055", "last": "p-0060"},
    {"id": "08", "first": "p-0061", "last": "p-0066"}, {"id": "09", "first": "p-0067", "last": "p-0072"},
    {"id": "10", "first": "p-0073", "last": "p-0078"}, {"id": "11", "first": "p-0079", "last": "p-0084"},
    {"id": "12", "first": "p-0085", "last": "p-0090"}, {"id": "13", "first": "p-0091", "last": "p-0096"},
    {"id": "14", "first": "p-0097", "last": "p-0102"}, {"id": "15", "first": "p-0103", "last": "p-0108"},
    {"id": "16", "first": "p-0109", "last": "p-0114"}, {"id": "17", "first": "p-0115", "last": "p-0120"},
    {"id": "18", "first": "p-0121", "last": "p-0126"}, {"id": "19", "first": "p-0127", "last": "p-0132"},
    {"id": "20", "first": "p-0133", "last": "p-0138"}, {"id": "21", "first": "p-0139", "last": "p-0144"},
    {"id": "22", "first": "p-0145", "last": "p-0150"}, {"id": "23", "first": "p-0151", "last": "p-0156"},
    {"id": "24", "first": "p-0157", "last": "p-0162"}, {"id": "25", "first": "p-0163", "last": "p-0168"},
    {"id": "26", "first": "p-0169", "last": "p-0174"}, {"id": "27", "first": "p-0175", "last": "p-0180"},
    {"id": "28", "first": "p-0181", "last": "p-0186"}, {"id": "29", "first": "p-0187", "last": "p-0192"},
    {"id": "30", "first": "p-0193", "last": "p-0198"}, {"id": "31", "first": "p-0199", "last": "p-0204"},
    {"id": "32", "first": "p-0205", "last": "p-0210"}, {"id": "33", "first": "p-0211", "last": "p-0216"},
    {"id": "34", "first": "p-0217", "last": "p-0222"}, {"id": "35", "first": "p-0223", "last": "p-0228"},
    {"id": "36", "first": "p-0229", "last": "p-0234"}, {"id": "37", "first": "p-0235", "last": "p-0240"},
    {"id": "38", "first": "p-0241", "last": "p-0246"}, {"id": "39", "first": "p-0247", "last": "p-0252"},
    {"id": "40", "first": "p-0253", "last": "p-0258"}, {"id": "41", "first": "p-0259", "last": "p-0264"},
    {"id": "42", "first": "p-0265", "last": "p-0270"}, {"id": "43", "first": "p-0271", "last": "p-0276"},
    {"id": "44", "first": "p-0277", "last": "p-0282"}, {"id": "45", "first": "p-0283", "last": "p-0287"}
  ] }
```

Economy first (one text at a time, about ten agents): start with **batches 02–08** (speeches 1–5:
the end of speech 1, the Funeral Oration with the two cut openings in batches 03 and 05, and the
first pages with a one-line apparatus), read their replies and run the checker
(`.venv/bin/python -m anagnosis_pipeline check-lysias-batch transcriptions/lysias/batch-0[2-8].md`)
before the rest go out; commit every wave (`git commit pipeline/transcriptions/lysias`). Pages
that will want a second look whatever the agent says: p-0143/p-0144 (13.65–66 printed after
13.68, Hude's own section numbers), p-0163/p-0164 (a heading of the check text at the end of
speech 14 that fell on speech 15's title), p-0106, p-0153, p-0272 (the line count), p-0272,
p-0281, p-0284 (the hypotheses, typed from the image).

**Residual pass** (after a wave's first pass is back and committed):
`.venv/bin/python -m anagnosis_pipeline lysias-residuals` (all batch files, or name some) writes
`pipeline/build/hude-pages/lysias/residuals/r-NNNN.md` and `.png`; then `lysias-pass.workflow.js`
with `{ "scratch": "…/pipeline/build/agent-scratch", "kind": "residuals", "atOnce": 8, "jobs":
[{ "id": "01", "batches": ["01", "02"], "pages": "p-0019, p-0020, …" }, …] }` (two batches a
job; `pages` = the pages of those batches that have an `r-NNNN.md`).

**Review** (one batch a job): the same script with `"kind": "review"` and `"jobs": [{ "id":
"01", "batches": ["01"] }, …]`; REVIEW.md already holds the reading task (its point 4), so no
`extra` is needed; give one only for something found on the way. Batch 01, the pilot, is
reviewed with the others: it has had no second reader.

How far the two second passes go is step 5's decision: both on batches 01–08 first, their
yield written under Decisions.

**The commentaries and introductions** (`pipeline/transcriptions/lysias/lysias-prose.workflow.js`;
model opus, general-purpose; a first check and, by the experience of the two earlier
commentaries, **a second reading of every batch**: `"review": true`). One run per editor keeps
the waves small:

```json
{ "scratch": "/home/proteus/koding/anagnosis/pipeline/build/agent-scratch", "atOnce": 8, "review": true,
  "jobs": [
    {"entry": "lysias-07", "file": "intro-01"}, {"entry": "lysias-07", "file": "notes-01"}, {"entry": "lysias-07", "file": "notes-02"},
    {"entry": "lysias-07", "file": "notes-03"}, {"entry": "lysias-23", "file": "intro-01"}, {"entry": "lysias-23", "file": "notes-01"},
    {"entry": "lysias-31", "file": "intro-01"}, {"entry": "lysias-31", "file": "notes-01"}, {"entry": "lysias-31", "file": "notes-02"}
  ] }
```

(Morgan: 9 batches: the first run, the smallest, to see the brief work.) Shuckburgh, 14 batches:

```json
{ "scratch": "/home/proteus/koding/anagnosis/pipeline/build/agent-scratch", "atOnce": 8, "review": true,
  "jobs": [
    {"entry": "lysias-05", "file": "notes-01"}, {"entry": "lysias-09", "file": "notes-01"}, {"entry": "lysias-09", "file": "notes-02"},
    {"entry": "lysias-10", "file": "notes-01"}, {"entry": "lysias-10", "file": "notes-02"}, {"entry": "lysias-13", "file": "notes-01"},
    {"entry": "lysias-13", "file": "notes-02"}, {"entry": "lysias-13", "file": "notes-03"}, {"entry": "lysias-14", "file": "notes-01"},
    {"entry": "lysias-14", "file": "notes-02"}, {"entry": "lysias-17", "file": "notes-01"}, {"entry": "lysias-28", "file": "notes-01"},
    {"entry": "lysias-30", "file": "notes-01"}, {"entry": "lysias-30", "file": "notes-02"}
  ] }
```

Adams, 51 batches, the same arguments with these jobs (entry: files): `lysias-12`: intro-01…03,
notes-01…09; `lysias-16`: intro-01, 02, notes-01…03; `lysias-19`: intro-01, 02, notes-01…05;
`lysias-22`: intro-01, notes-01, 02; `lysias-24`: intro-01, notes-01, 02; `lysias-25`: intro-01,
notes-01…03; `lysias-32`: intro-01, 02, notes-01…03; `lysias-34`: intro-01, notes-01;
`lysias-appendix`: intro-01…05; `lysias-intro`: intro-01…05. The pilot pages (p-0069 in
lysias-12/notes-01, p-0078 in notes-02, p-0172 in lysias-23/notes-01, p-0259 in
lysias-10/notes-01) are already answered; the agent of the batch does the other pages and the
second reader reads all.

**Gillies, the transcription** (the same script and brief section; the speech-4 sample batch is
one of the jobs: its flags are not answered; `"review": true` as for the commentaries):

```json
{ "scratch": "/home/proteus/koding/anagnosis/pipeline/build/agent-scratch", "atOnce": 6, "review": true,
  "jobs": [
    {"entry": "lysias-gillies-01", "file": "intro-01"}, {"entry": "lysias-gillies-01", "file": "intro-02"},
    {"entry": "lysias-gillies-03", "file": "intro-01"}, {"entry": "lysias-gillies-03", "file": "intro-02"},
    {"entry": "lysias-gillies-04", "file": "intro-01"}, {"entry": "lysias-gillies-21", "file": "intro-01"},
    {"entry": "lysias-gillies-26", "file": "intro-01"}, {"entry": "lysias-gillies-34", "file": "intro-01"}
  ] }
```

**Gillies, the alignment pass** (`pipeline/transcriptions/lysias/lysias-gillies-align.workflow.js`,
brief `GILLIES-ALIGN.md`; model opus, general-purpose; one agent per speech and a second look):
only after the transcription batches above are checked, read a second time **and committed**
(`git commit pipeline/transcriptions/drama/lysias-gillies-NN`; the checker compares with HEAD):

```json
{ "atOnce": 6, "review": true, "speeches": [1, 3, 4, 21, 26, 34] }
```

Then `.venv/bin/python -m anagnosis_pipeline check-gillies-marks 1 3 4 21 26 34` (0 remarks; its
listing read down once), commit, and `merge-lysias` writes `eng-gillies.txt`.

**The words without trees** (`pipeline/transcriptions/lysias/lysias-analyses.workflow.js`, brief
`ANALYSES.md`; general-purpose; the model is an argument). First the control:

```json
{ "atOnce": 2, "model": "sonnet", "jobs": ["91", "92"] }
```

then `.venv/bin/python -m anagnosis_pipeline lysias-analyses check transcriptions/lysias/analyses/job-9*.tsv`
and `… lysias-analyses measure`, and the rule above. If the pass goes on:

```json
{ "atOnce": 8, "model": "sonnet", "jobs": ["01", "02", "03", "04", "05", "06", "07", "08", "09", "10", "11", "12", "13", "14",
  "15", "16", "17", "18", "19", "20", "21", "22", "23", "24", "25", "26", "27", "28"] }
```

then the checker on every file (`job-[0-2]*.tsv`), commit `pipeline/transcriptions/lysias/analyses`,
`merge-lysias` (it prints "checked analyses: … words in the table, … readings changed"), build.

After each wave: `check-drama-prose <entry> <file>` on every file, commit
(`git commit pipeline/transcriptions/drama/lysias-NN`), and at the end `merge-lysias`, then read
`pipeline/build/lysias-notes.log`.

## For the author

**Answered on 2026-11-16 (the questions that follow, from the merge, the words and the build):**
speeches 12, 13, 19: **the checking pass**, judged by a measurement ("The words without trees"
below), and about.md says in one line that their word analyses are automatic; Gillies: **marks
inside his paragraphs where the place can be told, at the paragraph's head otherwise**; the two
words cut by a supplement **stay two tappable halves**; the catalogue entry is fine, nothing is
released before the commentaries and Gillies are in. **Still open: the glossary** (whether
every party to a speech should have an entry; no more entries for now).

**The questions as they were put:**

* **Speeches 12, 13 and 19 have no trees, so every word there (12,860, a quarter of the text)
  has the lemma and form the analyser gives the word by itself.** Measured on the speeches with
  hand-made trees that is right for the lemma 97 times in 100; the case is wrong for about two
  words in a hundred (a neuter called accusative where it is nominative), the number for fewer
  than one. Three ways: (a) leave it, as the words outside the trees are left in the other
  texts, with a sentence in about.md; (b) a checking pass by agents over the 811 word forms in
  these speeches whose spelling allows more than one lemma (the list is made:
  `pipeline/build/agent-scratch/lysias/notree-ambiguous.txt`; the agent chooses among the
  analyser's readings, it does not write any), about a dozen small batches for a cheaper model;
  (c) a reader change that shows every possible form for a word without trees. Proposed: (b).
* **Gillies beside the Greek: marks inside his paragraphs too.** The alignment pass as written
  puts a section mark at the head of each of his paragraphs and also, inside a long paragraph,
  before a sentence that plainly begins a new section, so the reader shows his English in
  smaller pieces beside the sections they render. His words and their order are untouched, but
  his long paragraphs are shown divided. Say if you want marks at his paragraph heads only.
* **Two words cut by a supplement** (25.35 ὑπο⟨ψίαν καταστήσετε⟩, 33.9 ⟨ἀγανακτήσει⟩εν): the
  reader divides a word at such a bracket, so each is two tappable halves; both halves give
  the whole word (ὑποψία, ἀγανακτέω). Making them one word would need a change to the word
  division that the pipeline and the reader share; not made.
* **The glossary of 188 names** says who each person is in the speeches, with the places. What
  it adds from outside the speeches is little and worth your eye: the archons' years, "the
  Phaedrus of Plato's dialogues" (19.15), Cinesias "the dithyrambic poet", Cephisodorus "the
  comic poet", Antiphon "the orator", the year of a battle. Names the dictionaries already have
  as bare names (Διόδοτος "Diodotus", Σίμων "Simon") got no entry: say if every party to a
  speech should have one.
* **The catalogue.** Lysias now stands in `data/catalog.json` (not for sale). Its description
  comes from about.md, which describes the finished text (commentaries, Gillies). Nothing is
  pushed; the catalogue reaches users only with a reader release.

**Questions from the commentaries, translations and merge stage (2026-11-16):**

* **Adams's appendices.** Proposed: his Appendix I–V ships as the text's appendix (Chronological
  outline, Athenian legal procedure, Rhetorical terms, Money and prices, The manuscripts: 36
  pages), because his notes cite its numbered paragraphs all the time ("App. § 57. 3"). His
  Bibliography and his Critical Notes (27 pages on his own text against Thalheim's) are left out,
  so his "See Crit. Note" in a note leads nowhere: say if the Critical Notes should ship too, or
  if the appendix should not.
* **Gillies has speech 4**, so only eight speeches are without English (6, 8, 11, 15, 18, 20, 27,
  29). His version is free and has no section numbers: proposed to lay it beside the Greek by
  his paragraphs, each filed under the section where it begins, the places set by an alignment
  pass after the transcription is checked. The alternative is to show Gillies's speeches as
  running text apart from the Greek (as an appendix), not beside it.
* **The chooser's names** are Hude's titles as he prints them, in lower case with accents. Three
  are odd because the print is: speech 17 is headed Δημοσίων ἀδικημάτων (the manuscripts' wrong
  title, which Hude keeps; the speech is the one usually called "On the property of Eraton"),
  and 4, 18, 24, 26, 27 carry his brackets (⟨ἄδηλον⟩, ⟨τῶν⟩, [Πρὸς τὴν εἰσαγγελίαν], ⟨…⟩, [ὡς
  Θεόδωρος]). Kept as printed; say if the brackets should go from the chooser, or 17 take the
  usual title.
* **The hypotheses** of 32–34 are section 0 of their speech; the reader would label them "§ 0".
  A label without a number ("Hypothesis") needs a line in the reader; say if wanted.
* **Notes whose lemma is not in Hude's text** stay under the section their commentator names,
  with his lemma, unmarked. They could instead carry a mark ("Adams reads …"); the number to
  judge by comes after the batches are checked (the log lists them).
* **Misprints corrected** (each with a note in the apparatus; the batches keep the print): text:
  ἔλεγετʼ → ἐλέγετʼ (8.8), Αυσιθέῳ → Λυσιθέῳ (10.12), πεπιστευμενους → πεπιστευμένους (19.13),
  εστιν → ἐστιν (20.28), "ἐνίκων καὶ," → "ἐνίκων, καὶ" (21.4, the comma misplaced), ὀλιγαοχικὸς →
  ὀλιγαρχικὸς (25.8); apparatus: προτερον, συμβαλόμενυς, ἐφʼ ᾖ, οὑτυσὶ, and ούνεκα twice
  (printed οὔνεκα on two other pages). Left as printed: ἑβδομήκοντα at 19.47 (a damaged ν, not a
  misprint). Say if any should stand as printed.

**Answered by the author on 2026-11-16** (these settle the matching questions below):

* Syntax for speeches 12, 13 and 19: **ship them without syntax** (the only trees are under a
  non-commercial licence).
* The syntax label: **per speech** (hand-made or automatic), with the small build and reader
  change that needs.
* The speeches' names in the chooser: **lower-case Greek with accents, with the speech's number**.
* The product id: **`lysias_speeches_hude`**.
* Settled as proposed, the author not objecting: Hude's Latin praefatio is not shipped, his sigla
  are; the introduction is Adams's general one plus each commentator's introduction to his speech;
  13.65-68 follow Hude's own order and numbers.
* The Eroticus (XXXV, from Plato's Phaedrus): **left out** (it survives only in Plato's dialogue
  and belongs there; whether it is Lysias's own is an old open question).


Nothing here blocks the text batches. In the order in which an answer is needed:

1. **Syntax for speeches 12, 13 and 19** (needed at step 7). GLAUx's trees for seven speeches
   are Vanessa Gorman's, which GLAUx lists as CC BY-NC-SA 4.0: not usable in an app that is
   sold. For four of them (1, 14, 15, 23) the same annotator's trees were released in the AGDT
   in 2015 under CC BY-SA 3.0, and we have those files; for 12 (Against Eratosthenes), 13
   (Against Agoratus) and 19 (On the Property of Aristophanes) there is nothing else, and GLAUx
   has no automatic trees for them. Choose: (a) write to Vanessa Gorman for leave to use her
   trees of the three speeches in the reader; (b) ship the three without syntax trees (lemmas
   and forms from the analyser; the Syntax button absent there); (c) wait for GLAUx. Speech 24
   has hand-made trees we may use (Pedalion).
2. **How the syntax is labelled** (step 7). Five speeches hand-made (1, 14, 15, 23, 24), 26
   automatic, three perhaps none. The reader shows one label for a whole text today. Either the
   whole text is called automatic (safe, but understates five speeches), or the label goes by
   speech (a small change to the build and the reader: proposed).
3. **The product id**, which can never be changed once it exists in the Play Console: proposed
   **`lysias_speeches_hude`** (the pattern of `plato_gorgias_burnet`, `lucian_truestory_nilen`;
   "orations" would be the other word: `lysias_orations_hude`). It stands in `drama.PLAYS` only;
   no about.md and no `google_play` line exists.
4. **Titles.** The text's Greek title (now Λόγοι; Hude's title page reads LYSIAE ORATIONES) and
   English title (now "Speeches"); and **the names of the 34 speeches in the book chooser**: the
   merge writes the speech's number and Hude's Greek title as printed, in capitals without
   accents ("1 · ΥΠΕΡ ΤΟΥ ΕΡΑΤΟΣΘΕΝΟΥΣ ΦΟΝΟΥ ΑΠΟΛΟΓΙΑ"; some run to three lines of print: "12 ·
   ΚΑΤΑ ΕΡΑΤΟΣΘΕΝΟΥΣ ΤΟΥ ΓΕΝΟΜΕΝΟΥ ΤΩΝ ΤΡΙΑΚΟΝΤΑ, ΟΝ ΑΥΤΟΣ ΕΙΠΕ ΛΥΣΙΑΣ"). Would you rather
   have them in lower case with accents (not in the print: taken from the Perseus headers), or
   with the usual English names beside the number ("12 · Against Eratosthenes")?
5. **Hude's Latin praefatio** (eight pages: the manuscripts, the editions he used, two pages of
   spellings adopted). The other editions' prefaces in Latin were not shipped (Nilén's); the
   English introductions were. Proposed: not shipped as an introduction; `sigla.md` is written
   from his SIGLA page and from what the praefatio says of the manuscripts. Say if you want the
   praefatio transcribed as it stands.
6. **The introductions of the three commentators.** Adams, Morgan and Shuckburgh each have a
   general introduction (Lysias's life, style, the courts) and an introduction to every speech
   they edit; the reader has one introduction per text. Proposed: one `introduction.md` whose
   first part is one general introduction (Adams's, the fullest and latest), followed by a
   chapter per speech with that speech's introduction by its commentator, named ("Speech 12,
   Against Eratosthenes · C. D. Adams"); the other two general introductions left out. The
   alternative is to keep all three general introductions as three parts.
7. **Where a section begins.** Hude's section numbers stand in the margin beside a line; he
   does not mark the word. Lamb's text (and with it Perseus, GLAUx and the 1898 translation)
   begins some sections a line or two earlier or later than Hude's number stands (five of the
   28 sections on the pilot pages; about ninety flagged in the whole text), and begins about
   150 sections in mid-sentence after a comma. The rule the agents work by: the section begins
   on the line Hude's number marks; if Lamb's word is on that line it is kept (so most sections
   begin exactly where every digital Lysias begins them); otherwise the section begins at the
   first sentence break of Hude's line. The other possible rule, to begin every section at the
   sentence break of Hude's line, would read better and depart further from the digital texts.
   Say if you want that.
8. **Speech 13, sections 65–68.** Hude prints the passage Lamb numbers 65–66 after 67–68 and
   numbers the four in his own order. The print's numbers are followed; the translation and the
   syntax are re-filed for these four sections. (Only place of the kind.)
9. **The Dionysius hypotheses** before speeches 32, 33 and 34 (Hude prints them in smaller
   type). Proposed: shipped as the speech's section 0 (`34.0`), words tappable, lemmas from the
   analyser, no syntax (GLAUx has not got them), no translation unless the 1898 version gives
   one. The alternative is to leave them to the commentary.
10. **The headings inside a speech** (ΜΑΡΤΥΡΕΣ. ΝΟΜΟΣ. ΨΗΦΙΣΜΑ.): proposed as lines of their
    own without a number, as stage directions are in the plays; how the reader shows such a line
    in prose is looked at on the emulator at step 11.
11. **Speech 35, the Eroticus** (Plato, *Phaedrus* 230e–234c, five pages, with Hude's apparatus
    from Plato's manuscripts): left out, as you said thirty-four. It could be added later as a
    35th book (check text: Burnet's Phaedrus on Perseus; Stephanus numbering). The **Index
    nominum** is not shipped.
12. **The Stephanus pages** in Hude's margin are not recorded (he marks the line, not the word;
    Lysias is cited by speech and section). Say if you want them.
13. **Gillies's translation** (1778) for speeches 1, 3, 26, 34 and perhaps 21 is a free version
    without section numbers in long-s print. It will come by the prose route from the scan; how
    it is laid beside the Greek (by paragraphs placed at the nearest section, as Jowett's
    Symposium was) is settled at step 8, with a sample put before you first.
14. **The missing pages in the Archive's reader.** Anyone who opens the scan online will not
    find pages 2.23–2.30 and 2.59–2.66: they are in our text from the scan's own files. Worth a
    sentence in about.md.

## Progress

- [x] Step 1: modules, tests, CLI (2026-11-16): `hude_pages.py` (layout, margins, draft, checker, residuals), `hude_merge.py` (text, apparatus, lemma check), `tests/test_lysias.py`; `lucian_pages.perseus_prose` takes a speech's number, quotations and headings; `Play.unhide`; CLI `hude-pages`, `check-lysias-batch`, `lysias-residuals`, `merge-lysias`; the briefs and workflow scripts in `transcriptions/lysias/`; the 34 Perseus files, the 34 GLAUx files and Gutenberg #6969 in `fetch.py` and fetched
- [x] Step 2: leaves and layout (2026-11-16): text leaves 19–287 (269 pages, with the four leaves the scan hides), SIGLA 18, praefatio 9–16; the tables above
- [x] Step 3: OCR and draft (2026-11-16): 269 pages fetched, cut (the four frames) and read; draft: 6,798 lines (6,698 of text, 67 headings, 26 hypothesis lines, 7 lines the check text lacks) and 82 title lines; 1,242 text lines flagged (18 %), 1,681 flags in all (6.2 a page; 11 pages with none; the most 34); the apparatus found on all 269 pages, a title on 34; 45 batch files `transcriptions/lysias/batch-NN.md`
- [x] Pilot (2026-11-16): batch 01 (leaves 19–24, 1.1–1.28) checked by the set-up session by the brief: 56 flags, 21 changes to the text, 85 apparatus items, checker 8 remarks all noted; the brief, the flags and the tools mended from it (Decisions); `lysias-residuals` on it: 27 items; a scratch merge of the draft runs (`--out pipeline/build/agent-scratch/lysias/texts`)
- [x] Step 4: text and apparatus batches, first pass (2026-11-16, run by the main session): all 45 batches checked by agents against the crops
- [x] Step 5: second passes (2026-11-16, the main session): the residual pass on all 45 batches (71 corrections) and the independent review of all 45 (35 corrections); commit 1e8aef8. Both stayed for the whole text: each caught errors the pass before had left
- [x] Step 6: merge and the checks (2026-11-16): `merge-lysias`: 1,145 lines (1,116 sections of 1,116), 34 speeches, 280 paragraphs, from 269 pages; 4,091 apparatus items under 1,061 sections; 0 problems. The 19 serious lemma misses looked up on the page and settled (none a slip of the text: `SETTLED`), 568 weak ones sampled (no class of fault); the pages flagged at set-up looked at; the misprint tables (6 in the text, 6 in the apparatus). See Decisions
- [x] Step 7: words and syntax (2026-11-16): each speech aligned to its own trees (AGDT 1, 14, 15, 23; GLAUx for the rest, hand-made for 24; none for 12, 13, 19); the label by speech (`# syntax-by-book`, `syntax_by_book` in the built meta table); 56,484 words, none without a lemma; 6,923 syntax nodes; the review list (830 words) gone through: what it was and what was done under Decisions. The reader's change is described under "The reader" and not made. The checking pass over the words of 12, 13, 19 is done and applied: 591 readings changed (Decisions)
- [x] Step 8: translations (2026-11-16): `eng-1898.txt`: 699 segments of 20 speeches, every one under a section of Hude's text; `eng-gillies.txt`: Gillies's six speeches (1, 3, 4, 21, 26, 34), transcribed and read a second time (91798f7), laid beside the Greek by the alignment pass (57a1545; `check-gillies-marks`: 0 remarks; 157 marks for 178 sections: 43 of 50, 44 of 48, 17 of 20, 19 of 25, 23 of 24, 11 of 11), merged as 157 segments; looked at beside the Greek at the start and end of speeches, at a marked section and at one that runs on under the mark before
- [x] Step 9: commentaries and introductions (2026-11-16): 21 entries, 493 pages, 74 batches, checked and read a second time by the main session's agents (a412f1e, 62bce24, 364f4a2, a38cf55); merged: `commentary-adams.md` (308 notes, 1,616 paragraphs), `commentary-morgan.md` (90 notes, 432 paragraphs), `commentary-shuckburgh.md` (573 notes, 631 paragraphs under 253 sections), `introduction.md` (Adams's general introduction and a chapter for each of the nineteen speeches), `appendix.md` (Adams's Appendix I–V); the notes log settled (Decisions)
- [x] Step 10: sigla, glossary, about (2026-11-16): `sigla.md` and `about.md` (`transcriptions/lysias/static/`, copied by the merge); the book names in lower-case Greek with numbers (`hude_merge.SPEECH_NAMES`); `glossary.md` (188 names), `shortdefs.tsv` (21 ordinary words, 185 names, one line for δῆμος), `aliases.tsv` (13), written by hand in `texts/lysias/` (the merge does not touch them); `check`: 2,801 lemmas, none missing from the dictionaries and the glossary, none without a short definition; the texts/README.md section
- [ ] Step 11: build and emulator check: the final merge and build on 2026-11-16 with everything in (1,116 sections in 34 speeches, 56,484 words, 6,923 syntax nodes, 4,091 apparatus items under 1,061 sections, Adams 308 notes, Morgan 90, Shuckburgh 253, the 1898 translation 699 segments, Gillies 157, the introduction, the appendix, the sigla, 188 glossary entries; `data/lysias.sqlite` 9.6 MB, version 5897863ec0a34c22, the same in the catalogue); `catalog` (no `google_play`), `check` (0 errors; no warning in Lysias), the tests; the reader's change made (757b603) with the asset pack. Still to do: the emulator check (the main session)

## Decisions

(append dated entries: what was open, what was chosen, why, which pages were looked at)

* **2026-11-16, steps 1–2: the book, the page, the modules.** Pages looked at: leaves 5–18 (front
  matter), 19–21, 26, 28–30, 35–38, 43–46, 143, 284, 287–297, and the OCR of every text leaf.
  * **Four pages of speech 2 are missing from the Archive's reader but not from the scan.**
    The scan's page list marks leaves 36, 37, 44 and 45 "Delete" (hidden). They are not
    duplicates: the visible leaves run from 2.22 (leaf 35) straight to 2.31 (leaf 38), and from
    2.58 (leaf 43) to 2.67 (leaf 46); the two openings between exist only as the camera's whole
    frames (the book on its mat between two rulers, 3744 × 5616 pixels), which the hidden leaves
    are. `Play.unhide = (36, 37, 44, 45)` keeps them; `hude_pages.FRAMES` holds each page's
    rectangle in its frame and `hude-pages lysias fetch` cuts the page image to it once. So the
    text is 269 pages, leaves 19–287 without a gap, and a reader who looks a place up in the
    Archive's online reader will not find these four pages there.
  * **Keys by leaf.** Hude prints no page numbers; a line is `leaf.line` (`28.5`), the page's
    files `p-0028…`. A right-hand page is an odd leaf (line numbers left, section numbers
    right), a left-hand page an even leaf (the other way round); this holds through the four
    cut pages.
  * **What counts as a line** (settled from the margin numbers and the apparatus's references on
    leaves 19, 28, 284): not the running head, not a speech's number and title, not the heading
    ΥΠΟΘΕΣΙΣ ΔΙΟΝΥΣΙΟΥ; but every line of a hypothesis and every heading inside a speech
    (ΜΑΡΤΥΡΕΣ.).
  * **The running head and the apparatus are found on each page by itself** (`head_bottom`,
    `apparatus_top`). The scan's pages are not cut alike (the head ends between 1.4 % and 8.2 % of
    the page's height), so no fixed share works. The apparatus has no rule above it and
    Tesseract's type sizes are not sure (it sizes a last line of text as small as the apparatus
    on some pages), but the apparatus's lines stand at two thirds of the text's pitch and the
    text ends a line and a half above it: the block is taken from the foot upwards by pitch and
    size together. A one-line apparatus under the last lines of a speech (leaves 59, 64) and a
    stray stamp under the apparatus (leaf 55) are provided for. The shared drama layout is used
    with the head and the apparatus handed to it; lines it drops as noise (a short last line of
    a paragraph read with little confidence, a speech's numeral) are put back, and a line
    Tesseract read twice is left out.
  * **Margin numbers by their place.** Each margin is cut into its clusters of ink, each read
    by Tesseract (digits). Hude's old-style figures are misread often (10 as 1, 3 as 8), so a
    number confirms a fifth line, or the line where a section begins, by standing beside it,
    whatever it was read as. A Stephanus page is told from a section number by its brackets,
    which stand taller than any figure. The Stephanus pages (and for speeches 32–34 the
    Dionysius pages) are **not recorded**: Lysias is cited by speech and section, and Hude marks
    only the line, not the word, where a page begins (as Nilén's Vulgate pages in the True Story).
  * **The check text.** `perseus_prose` gained three options, all off by default (the True
    Story's output is unchanged: a scratch merge gave byte-identical files): `book` (the speech's
    number for a file without book divisions), `quotes` (a `<q>` written ‘ ’: Hude's single
    marks; the closing mark is kept apart from the elision sign ʼ), `headings` (the words of a
    `<label>` marked, and the section that Perseus begins with its label begun at the first word
    after it, where Hude's margin number stands).
  * **Three things Tesseract does on this print, and what the draft does about them.** It reads
    δʼ as ὃ (the check word δʼ is paired with such a reading standing free in its place: no
    flag; a risk accepted, as the ζ/ξ fold of the True Story: a real ὃ against δʼ between the
    editions would go unflagged). It runs two words together (ὑπὸτῶν: both words paired, no
    flag). It reads Hude's angle brackets ⟨ ⟩ as round ones: round and angle brackets are
    counted together when the OCR is compared with the check text, so a ⟨ ⟩ that Hude prints as
    ( ) or the reverse is not flagged; the review's reading task covers the brackets' kind.
  * **Where the editions differ in order or extent.** A run of eight or more check words that
    the page does not show is left out of the draft with one flag (a passage Hude deletes). A
    passage of fifteen words or more that the print has in another place is moved in the check
    text before the matching (`transposed`): one case, 13.65–66, which Hude prints after 13.68
    and whose sections he numbers in his own order (his 65–68 are Lamb's 67, 68, 65, 66). **The
    print's numbers win**: the agents number the sections as Hude's margin does; the merge's
    "every section once, in order" check then holds, and the translation and GLAUx, which follow
    Lamb's numbers there, are re-filed for these four sections at steps 7–8.
  * **Where a section begins.** Hude's number stands beside the line; inside the line the section
    begins after a wider space. Lamb begins some sections a few words earlier or later (1.33:
    Hude's 33 stands at the line "βην, ἡγούμενος τοὺς μὲν …", Lamb begins at "τοὺς δὲ
    πείσαντας" a line below). Rule for the agents (INSTRUCTIONS.md): the mark goes on Hude's
    line; there after the wider space, else at Lamb's word if it is on that line, else after the
    line's first stop. About 80 places are flagged for it (see For the author).
  * **Batch conventions** (not settled by the brief): `[title]<TAB>…` lines without a key for a
    speech's number and title (one per printed line; the numeral is written from the speech's
    number, since Tesseract reads the Roman numerals badly); `[label] ` after the TAB for a
    heading inside a speech; `[hypothesis] ` for a hypothesis's lines; `§12.7 ` before the word
    where a section begins; `¶` before an indented line; apparatus numbers as printed (`3`,
    `22-23`), an item printed without a number given the number of the item before it, `-` for
    an item on a speech's title. Quotations ‘ ’ (U+2018, U+2019), elision ʼ (U+02BC): the checker
    takes a ’ for a closing mark only while a quotation is open.
  * **In grc.txt** (`hude_merge.py`): a heading inside a speech is a `!` line (the format's
    stage direction: a line without a number and without words to tap); a hypothesis is the
    speech's section 0 (`34.0`); the book's label is the speech's number and Hude's title as
    printed, in capitals without accents (`== book 1 · ΥΠΕΡ ΤΟΥ ΕΡΑΤΟΣΘΕΝΟΥΣ ΦΟΝΟΥ ΑΠΟΛΟΓΙΑ`).
    How the reader shows each of these is checked at step 11; the three are listed under For the
    author.
  * **The Murray options.** Hude's page shares `app_bare_numbers`, `verse_size_q`,
    `foot_signature` and `app_pitch_cut` with Murray's Oxford text; `tests/test_murray_layout.py`
    allowed them for that editor only and now allows the route `hude` too.
  * **Texts verified unchanged**: the True Story (a scratch merge into
    `pipeline/build/agent-scratch/lysias/verify/`, run twice, after the first and after the last
    change to `perseus_prose`: grc.txt, the apparatus, tokens, syntax, translation, both
    commentaries and the introduction byte-identical to `texts/truestory/`; `check-lucian-batch`
    gives the same remarks). No other text reads through the changed code (`perseus_prose` is
    the True Story's alone; `Play.unhide` is empty for every other entry; the fetch list only
    grew; the test that allowed the Oxford page's options for one editor only now allows the
    route `hude` too). Nothing was rebuilt.
* **2026-11-16, step 3: the draft.** `hude-pages lysias fetch | ocr | draft`
  (`TMPDIR=pipeline/build/tmp DRAMA_WORKERS=5 nice -n 19`; the jp2 files were taken from the
  scan's zip in one download, the per-leaf route being slow that day). Tesseract's reading of
  this print is very good: of 56,424 words read, 387 matched no word of the check text, and of
  the check text's 56,162 words 118 were not found. The first draft flagged 19 % of the lines
  with 2,700 flags; what was wrong was the page, not the print: the four hidden leaves, the
  running head taken for a line where the page is cut lower, the last line of text taken into
  the apparatus (or the apparatus into the text), a ghost line. After the layout was mended:
  1,239 flags; after the pilot widened the flags (below): **1,681 flags on 269 pages**: 441 words
  that differ, 243 that differ where Tesseract was unsure, 190 printed words the check text
  lacks, 118 check words not found, 156 brackets, 106 accents only, 180 for 90 sections whose
  number stands beside another line (each such place flags both lines), 82 title lines, 60
  quotation marks, 26 hypothesis lines, 28 line numbers, 17 gaps of the check text, 11 lines of
  the moved passage, 7 lines the check text lacks, a dozen others.
* **2026-11-16, the pilot: batch 01 (leaves 19–24, 1.1–1.28), checked by the brief.** 56 flags
  on six pages; 21 changes to the text: five section marks moved to Hude's line (1.7, 1.16,
  1.20, 1.23, 1.26); seven of Hude's own readings against Lamb's (ἑαυτοῦ 21.4, ἑορακυῖα 21.12,
  πεύσει 22.10, τέτταρες 23.18, ἐπιμέλεσθαι 23.28, ⟨οὐκ⟩ … οὐδʼ 24.2, ἣ added 20.16), each
  borne out by his apparatus on the line; two lacunae written as printed; quotation marks
  corrected in four places; a capital, three stops and an accent seen on flagged lines. 85
  apparatus items written. What it taught, and what was changed:
  * Two of Hude's readings had not been flagged: ἑορακυῖα (Tesseract was unsure of the word, and
    the True Story's rule passed over unsure readings) and ἣ (a word of one letter). **For a
    check text of another edition the flags must be wider**: a differing word is now flagged
    whatever Tesseract's confidence (243 more flags), and a short printed word the check text
    lacks is flagged where Tesseract is sure of it (about 100 more).
  * Section numbers: where Hude's number stands beside another line than the check text's
    section start, the flag now names that line, and both lines are in the lines image (in the
    pilot each case needed a crop of the page to find the number).
  * In the apparatus the breathings and iota subscripts of the small Greek cannot be read at
    the crops' size where they matter most ("ἣ πάντων H P (ἢ)", "θέλη rell.", "πεύση L"): the
    brief tells the agent to enlarge such words and to copy a form without its subscript as
    printed; the review repeats it.
  * Quotation marks: Lamb's are not Hude's (no marks where a quotation runs on after ἔφη-less
    breaks; a second opening mark before a new sentence; the closing mark before the stop). The
    checker now asks only whether a quotation is open when a ’ comes.
  * Punctuation, accents and capitals are not compared by the flags; on the six pages four such
    differences were seen by chance on flagged lines. `lysias-residuals` on the checked batch
    lists 27 items (19 accents, 6 words, 2 stops) after Tesseract's standing misreadings on
    this print are taken out (the raised stop read as an apostrophe, δʼ as ὃ, ⟨ ⟩ as ( )): so a
    residual pass is expected to be needed, as the brief said for an Oxford text whose check
    text is another edition.
  * Small faults of the draft mended: a paragraph mark before a line that begins with a
    one-letter word; the check text's "ἄνδρες,(δεῖ" and "πέντε,ὡς" (no space in the Perseus
    file); speech numerals written from the speech's number (Tesseract reads them as ΙΠ, ΧΧῚΙ).
  * The merge was run on the draft into a scratch folder: 1,116 sections of 1,116, 34 speeches,
    the 85 pilot items filed under their sections, no serious lemma miss, 15 weak (all
    manuscripts' spellings and conjectures); its four problems are the draft's open places named
    under "Hand-over".

* **2026-11-16, the merge of the checked text (step 6).** `merge-lysias` on the 45 batches after
  their three passes; the log `pipeline/build/lysias-merge.log`.
  * **The 19 serious lemma misses** (an apparatus item whose lemma is neither on its line nor
    beside it): each looked up on the page (crop sheets of the 19 text lines with their apparatus).
    In every one the batch's text agrees with the print, and the item is a reading Hude reports
    without the word of his own text in front (his apparatus is largely negative: "δὲ μὴ
    γενομένων C", "εἰς δημοκρατίαν L", "ἐκ τοῦ ἄστεος X"), a variant in another word order, or a
    supplement quoted with its neighbour ("⟨περὶ⟩ ἁπάντων"). None is a slip of the text and
    none a wrong lemma in a batch, so no batch file was changed; the 19 are recorded as printed
    in `hude_merge.SETTLED` (key `leaf.line: lemma`: 32.5, 35.13, 44.11, 68.19, 72.23, 139.5,
    161.6, 186.23, 199.15, 210.2, 212.4, 219.5, 226.24, 233.23, 239.8, 258.23, 278.1, 279.20,
    286.19) and the log now shows 0 serious. At 72.23 the text's ἐπὶ δημοκρατίας is Dobree's
    reading, which Hude adopts; the agents had noted it.
  * **The weak ones** (568): 503 are items whose first words match nothing on the line (readings
    of the manuscripts and conjectures given without a lemma: ἤδειν L, τοι C, οὔσης ⟨οὐ μᾶλλον⟩
    Canter), 62 name a word that stands on the line beside (Hude counts a broken line with the
    one before, or cites the line where a longer lemma begins), 3 are ranges whose last word was
    not found (an omission that runs into the next section). A hundred read through: no class
    of fault, nothing to change in the batches. One thing mended in the tool from it: a variant
    without a lemma on a line that holds the end of one section and the beginning of the next
    was filed under the first; it now goes under the section whose words it is most like.
  * **The pages flagged at set-up.** p-0143/0144: 13.65–68 stand in Hude's order with his
    numbers (the batch notes say so; grc.txt has 65 Τἆλλα τοίνυν … 67 Ἦσαν τοίνυν οὗτοι … in
    his sequence). p-0163/0164: the heading ΝΟΜΟΙ. ΟΡΚΟΙ. ΓΡΑΦΗ. closes speech 14 (a `!` line
    after 14.47; the merge kept a heading only before a section and now keeps one at a speech's
    end too). p-0106, p-0153, p-0272: the line counts agree with the margin numbers after the
    agents' check (no problem in the log). p-0272, p-0281, p-0284: the three hypotheses are
    sections 32.0, 33.0, 34.0 (34.0 in two paragraphs).
  * **Misprints** (the reviewers' `misprint:` notes, all twelve in the tables; the batches keep
    the print, each correction has a note in the apparatus): text, `MISPRINTS`: ἔλεγετʼ (89.22),
    Αυσιθέῳ (100.16), πεπιστευμενους (184.15), εστιν (202.2), the comma of "ἐνίκων καὶ,"
    (205.21), ὀλιγαοχικὸς (229.27); apparatus, `APPARATUS_MISPRINTS`: προτερον (45.19),
    συμβαλόμενυς (76.26), ἐφʼ ᾖ (77.3), οὑτυσὶ (146.27), ούνεκα without a breathing (211.16 and
    238.25; printed οὔνεκα on two other pages). Not corrected: ἑβδομήκοντα at 191.17 (a damaged
    ν), Ἱππαρμόδωρον in the apparatus at 218.9 (the reviewer withdrew the note).
* **2026-11-16, the words (step 7).** What the review list of 830 words was, and what was done.
  * **What it held.** 550 words that are **not in the trees** (283 of them the three hypotheses
    of 32–34, which GLAUx has not got; the rest Hude's supplements and the places where he has
    more words than Lamb); 209 where **Hude reads another word than the trees' text**; 39 words
    in the speeches without trees that **the analyser could not read**; 32 compound verbs read
    by a rule. Names: 45 of the 830. So about 760 are words the analyser read by itself, and the
    71 words that had no lemma at all were the 39 and the 32.
  * **By rule first.** (1) A compound verb the analyser lacks is read from its simple verb and
    its prefix where the joined lemma is a dictionary headword (`compound_analysis`): 32.
    (2) In a speech without trees the address after ὦ is a vocative (`vocatives`: ὦ ἄνδρες
    δικασταί; 60 words). (3) ὃ and ὅ τι are the relative, ἥ τε / αἵ τε the article
    (`relatives_and_articles`: 25 words outside the trees). (4) Garbled and variant lemmas of
    the trees go to the dictionaries' headword (`LEMMA_FIXES["lysias"]`, 72 lemmas: οὐτε,
    κατά-καθεύδω, ἀμφιαμφισβητέω, ξηαριξλες for Χαρικλῆς, καταλιμπάνω for καταλείπω, ἔχθρη …).
  * **Then by hand** (`HAND_ANALYSES["lysias"]`, 104 words, keyed by section and form): the 39
    unread words of 12, 13, 19; the names the trees or the analyser read as the common word they
    are spelled like, or the reverse (Δάμνιππος as "horse-taming", Πολέμαρχος as the polemarch,
    Φυλῇ as Φυλεύς, Παιανιεῖ as παιανίζω, Ἑρμᾶς, φυλὴν as Phyle); the two words a supplement
    cuts in two (25.35 ὑπο⟨ψίαν, 33.9 ⟨ἀγανακτήσει⟩εν: the reader's word division makes two
    words of each, and both halves carry the whole word's lemma and form); and 15 words where
    the analyser's choice among the readings of a form was wrong for the place (ἀξιῶ as ἄξιος,
    θεωρῶν as θεωρέω, οὐδʼ as οὐδός, κακῶς and ὁμοίως as adjectives, Πλαταιῶν as the town).
    For that last group the 441 review words whose spelling allows more than one lemma were
    listed with their context and read through (`build/agent-scratch/lysias/review-ambiguous.txt`).
  * **How good the analyser's reading is where nothing checks it** (measured on the 7,607 words
    of the speeches with hand-made trees, by giving the analyser each word alone): the lemma is
    the trees' in 97.1 % (the rest mostly another headword for the same word: μᾶλλον/μάλα,
    δεῖ/δέω); the case differs in 2.5 % of the words (most of them the vocative after ὦ, now a
    rule), the number in 0.7 %; the other differences are conventions (particle or adverb,
    pronoun or adjective, middle or middle-passive). **Speeches 12, 13 and 19 (12,860 words)
    stand on that reading alone**: For the author.
  * **The dictionaries.** After the fixes 165 lemmas were in no dictionary, nearly all names,
    and 90 had no short definition. `glossary.md`: 188 entries (the 165, and 23 names the
    dictionaries know only as common words: Βάτραχος "frog", Φείδων "oil-can", Αἴσιμος
    "fated"), each saying who the person is in the speech, with the places; several men of one
    name in one entry. `shortdefs.tsv`: 21 ordinary words Logeion's list lacks, the names (a
    name spelled like a common word that the speeches do not use takes that word's place, since
    lemma keys are lower-cased; δῆμος has one line for the people and for Demus; Φυλή and
    Πολέμαρχος keep Logeion's own capitalised lines). `aliases.tsv`: 13 spellings the
    dictionaries list otherwise (μιμνῄσκω, πρῴην, εὔνους, Χερρόνησος, ἀκληρωτί …). The sources
    of the two hand files are kept beside their small generator in
    `build/agent-scratch/lysias/glossary/` (not in the repository; the files in texts/lysias/
    are the ones to edit).
* **2026-11-16, the build without the commentaries (step 11, the pipeline's part).** `merge-lysias
  lysias --without-notes` (the option leaves the commentaries, the introduction, the appendix
  and Gillies out while their batches are with the agents), `build --only lysias`: 1,145 lines,
  56,484 tokens, 2,797 lemmas, 6,923 syntax nodes, 699 translation segments, 1,061 apparatus
  notes, the sigla, 188 glossary entries, 8.3 MB; `catalog`: 19 texts in the public catalogue,
  Lysias without `google_play`; `check`: 0 errors, 8 warnings, none of them in Lysias. The
  catalogue's description is about.md's and already speaks of the commentaries and Gillies: they
  are to be merged before any reader release carries the catalogue. Other texts verified
  unchanged: data/lexicon.sqlite and the databases of three other texts by checksum before and
  after; the tests (277).

* **2026-11-16, the space before ; : ? ! in the English prose.** The old prints set a space
  before these stops and the agents who read the pages did not all keep it. The merge of the
  Lysias prose (the three commentaries, the introduction, the appendix: `hude_notes.write`;
  Gillies: `write_gillies`) now writes it without the space (`hude_notes.english_stops`; the
  batch files keep what their reader typed). Only English is touched: where the last letter
  before the stop is Greek, the space before ; ? ! stays (a ; there may be the Greek question
  mark); a colon is no Greek stop and loses its space after a Greek lemma too ("**κινδυνεύειν** :"),
  but not where Greek stands on both sides of it; the raised stop is never touched. Test:
  `test_english_stops`. **The other texts' prose merges do not do this**: nothing in
  `drama_prose.py` or the older merges touches the space; their output is as the readers typed
  it, without the space throughout in three commentaries looked at (Jerram, Taylor, Jebb's
  Trachiniae: no line with it) and with it here and there in three others (Sidgwick's Agamemnon
  70 lines of 2,664, Starkie 53 of 6,900, Paley 15 of 1,516). They were not changed.
* **2026-11-16, the words without trees: the checking pass prepared** (the author's answer; the
  section of that name): the module `hude_analyses.py`, the CLI `lysias-analyses jobs | check |
  measure`, 28 job files and two control jobs, the brief, the workflow script; the merge reads
  the answers as a table. Nothing is answered yet, so tokens.tsv is unchanged by it. about.md
  now says that the word analyses of the three speeches are automatic.

* **2026-11-16, the commentaries merged; the notes log settled** (`pipeline/build/lysias-notes.log`,
  which ends each speech with a `COUNT` line).
  * **How the paragraphs found their sections** (a note's every lemma is a paragraph): Adams
    1,616 paragraphs: 1,510 by their lemma in the section he names, 13 by their lemma in a
    section beside it, 60 without a Greek lemma (kept with their note), 25 on another reading
    than Hude's, 8 not found. Morgan 432: 412, 3, 4, 11, 2. Shuckburgh 631: 474, 75, 48, 27, 7.
  * **The lemma search widened** after the first run showed 242 lemmas "not found", 150 of them
    only because the lemma names words that stand apart ("ἐπιβουλεύετε, ἀφῆτε"; "τῇ ἀρετῇ" for
    τῇ τούτων ἀρετῇ): a lemma is also found where every one of its words is in the section;
    where its letters are there divided otherwise (δή που / δήπου); δέ in a lemma for the text's
    δʼ; a dash or κτέ. as dots of omission.
  * **Shuckburgh numbers by the lines of his own text**, which the merge maps to sections through
    an OCR of his text pages. The map runs a section or two ahead in stretches (the end of speech
    13), so his lemma is looked for four sections either side (two for the others), and a note
    without a lemma to be found by goes with the drift of the notes before it (`DRIFT`, 5 notes).
  * **A note on a reading that is not Hude's** (63): each looked up in Hude's section; the note
    stays under the section where Hude's own words stand, with its lemma as printed, and is
    followed by a line in square brackets: "[Morgan's text reads otherwise here; the text shown
    has δωρεὰν.]" (`hude_notes.OTHER_READINGS`: the lemma, Hude's words; the merge checks that
    Hude's words are in the section and says so if a table entry is not used). Only where it is
    certain: not a lemma in its dictionary form (χιτωνίσκος), not a heading (ΜΑΡΤΥΡΕΣ).
  * **Left at the commentator's number, unmarked** (17): lemmas in the dictionary form (ὑγιὴς,
    χιτωνίσκος, ἀνδραποδιστὴς, εὐήθειαν), abbreviated (τῶν ἄλλων Ἑ. πλεῖστα, τί δʼ ἂν κ.τ.λ., ἦ που
    κτλ., the display at 24.8), the heading ΜΑΡΤΥΡΕΣ, words in two sections (αὖ, ἡνίκα; ἄριστοι δὲ
    γεγενημένοι), Hude's capital with iota adscript (Ὤιμην), and five where the counterpart in
    Hude is not plain (αὐτῶν 7.40, ἦ πού γε 13.69, ἀλλʼ οὐκ 19.23, ὅτου 22.22, οἷοί περ 30.28).
  * **The checker's last remarks in Adams's files**: lysias-19/notes-04 "note 48 comes after 52":
    Adams prints § 52 after § 47 and his notes follow his order; the merge files each note by
    its number and lemma, so the note on 52 stands at 19.52. The word endings without a breathing
    (-ῃ, -ει and the like) are endings he discusses, as printed. Nothing changed.
  * **Footnotes that run over a page** stood in the batches as two `[Note: …]` paragraphs, the
    second without a mark at the head of the next page's block: joined again where the first
    ends without a stop (`join_footnotes`; five in the introduction: "three brothers, Pole-" +
    "marchus, …").
  * **Elisions** in quoted Greek typed with the closing quotation mark (δ’ ἐστὶ) are written
    with the Greek's apostrophe (`greek_elisions`); a quotation's closing mark stays.
  * **The commentators' misprints** corrected by the readers of the pages in the batch files,
    each with its note there: 51 notes, listed by the merge in
    `pipeline/build/lysias-commentary-misprints.log` (wrong accents and breathings in quoted
    Greek, ἐκφέρετο for ἐξεφέρετο, "Nor further" for "No further", a broken letter). All are
    evident; two doubtful places were left as printed by the readers (τὰ κείνων in a quotation of
    Demosthenes, γεμοὶ in one of Andocides).
  * **No batch file was changed** in settling the log: the placing, the bracketed lines, the
    footnotes and the elisions are the merge's.
  * Built with the commentaries: 9.5 MB; `check`: 0 errors, no warning in Lysias; the HTML of
    notes of each commentator, of the introduction and the appendix looked at (bold lemmas,
    italics, the bracketed lines, headings in two levels, footnotes as `[Note: …]` paragraphs
    as in the other texts). Gillies is not merged: his marks do not exist yet (the merge names
    speeches 3 and 4 as transcribed but not placed).

* **2026-11-16, the checking pass applied** (the 28 jobs answered by Sonnet agents, checked and
  committed by the main session, 09546b6; the control: 32 of 56 differing words corrected, the
  "spoiled" ones differences of convention). The merge reads 4,213 answers and changes the
  reading of **591 words** of speeches 12, 13, 19 (4.6 % of their 12,860; 203, 205 and 179): the
  case in 356, the number in 187, the mood in 95, the lemma in 80, the person in 72, the tense
  in 71, the voice in 46 (a word can change in several); 11 answers were `other:`, one `?`.
  **A sample read for a class of fault** (all 108 lemma changes; nine of each other kind in their
  sentences): the choices are right (τὰ ἔργα … γεγένηται nominative, τῆς κατηγορίας genitive
  singular for the accusative plural, ἐβάδιζον third plural, ἐρωτῶσιν the verb for the
  participle, σώσω future, τιμωρήσασθε imperative, πλεῖν "more", ἔδει from δεῖ, Ἦ "I was").
  One class of fault, not the agents' but the list's: seven lemmas among the analyser's readings
  are no dictionary headword (πρὶν, πλὴν, εἰτε with the wrong accent, epic ἀέκων, the adverbs
  πρότερον, πότερον, θᾶττον): the reading chosen is right, the lemma is sent to its headword
  (`LEMMA_FIXES["lysias"]`; 28 words; `Reader.readings` applies the fixes, so a job made again
  would not offer them). Three short definitions added (πρῶτον, φίλτατος, ὕστατος) and one made
  to fit (προσδέω, "need besides"). `check`: 2,799 lemmas, none missing, none without a short
  definition. The merge uses a job file only when it is committed and unchanged.

## Sizes, for planning

34 speeches, 1,116 sections, 56,162 Greek words in the check text; 269 pages of Hude, 6,798
printed lines (25 to a page on average, 27–30 on a full one), about 4,100 apparatus items (1,878
printed lines of apparatus; 85 items on the six pilot pages; speech 2 has a third more to the
page than the rest); 45 text batches (44 of six pages, the last of five).

| speech | words | leaves | | speech | words | leaves |
|---|---|---|---|---|---|---|
| 1 | 2,413 | 19–29 | | 18 | 1,346 | 176–181 |
| 2 | 4,067 | 30–49 | | 19 | 3,120 | 182–195 |
| 3 | 2,184 | 50–59 | | 20 | 1,920 | 196–204 |
| 4 | 950 | 60–64 | | 21 | 1,297 | 205–210 |
| 5 | 278 | 65–66 | | 22 | 1,125 | 211–216 |
| 6 | 2,615 | 67–78 | | 23 | 777 | 217–220 |
| 7 | 2,030 | 79–87 | | 24 | 1,432 | 221–227 |
| 8 | 1,039 | 88–92 | | 25 | 2,022 | 228–236 |
| 9 | 880 | 93–97 | | 26 | 1,386 | 237–243 |
| 10 | 1,498 | 98–104 | | 27 | 749 | 244–247 |
| 11 | 549 | 105–107 | | 28 | 911 | 248–251 |
| 12 | 4,859 | 108–129 | | 29 | 664 | 252–254 |
| 13 | 4,882 | 130–152 | | 30 | 1,887 | 255–263 |
| 14 | 2,426 | 153–163 | | 31 | 1,826 | 264–271 |
| 15 | 602 | 164–166 | | 32 | 1,703 | 272–280 |
| 16 | 1,151 | 167–172 | | 33 | 432 | 281–283 |
| 17 | 588 | 173–175 | | 34 | 554 | 284–287 |

Agent cost, from the texts made by the same route: a first-pass batch of six pages took about
0.13–0.15 M tokens for the plays (the Sophocles plays: 19 batches 2.9 M; the first Oxford-text
play: 10 batches 1.3 M); 45 batches would be about 6–7 M for the first pass, the residual pass
about half of that, a review of every batch as much as the first pass again. At ten agents at
once the first pass is five waves.
