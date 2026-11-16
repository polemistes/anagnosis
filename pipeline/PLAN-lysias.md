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
| syntax | **GLAUx `0540-001.xml` … `0540-034.xml`** (CC BY-SA 4.0), one file per speech, aligned to Hude's words; fetched to `pipeline/sources/glaux/`. GLAUx marks every sentence `analysis="manual"` or `"auto"`: speeches **1, 12, 13, 14, 15, 19, 23, 24 are manual** in GLAUx (1, 14, 15, 23 are the AGDT's hand-made trees, also in `pipeline/sources/treebanks/tlg0540.tlg0NN.perseus-grc1.tb.xml`; where GLAUx took 12, 13, 19 and 24 from is to be found out before they are shown as hand-made), the other 26 automatic. Automatic syntax is always shown as automatic. See "Syntax" below |
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
307 are hidden by the scan's own page list (36–37 and 44–45 are openings photographed twice; the
text runs on without them). The page image the Archive serves as `page/n<N>` is leaf N+1 up to
leaf 35, leaf N+3 for 38–43, leaf N+5 from 46.

| part | leaves | |
|---|---|---|
| series title, title page (no date; verso "Excudebat Horatius Hart") | 5, 7 | |
| Praefatio, pp. iii–x | 9–16 | Latin: the manuscripts (the Palatinus X of the 12th century, the source of all others for speeches 3–31; speeches 1–2 also in other families: H, P, and F V for 2), the first hand's index of X, the editions used; pp. viii–ix a list of spellings adopted, with references; signed "Scribebam Romae Kal. Dec. MCMXI" |
| SIGLA | 18 | three lists: speeches 1–31 (X and its correcting hands X¹ Xᶜ Xᶜ(1) Xʳ Xˢ, C D E F f G g H h I K M N O P Q q R S U V W, L = consensus codicum, Aldus, marg. Ald., Turr., the signs + / [X]); speeches 32–34 (the manuscripts of Dionysius of Halicarnassus F G M T); speech 35 (Plato's B T W) |
| **Speeches I–XXXIV** | **19–287** | **265 pages** (269 leaves less the four hidden); every speech begins on a fresh page |
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

GLAUx has all 34 speeches, tokenised with `div_section` on every word, so each word's section is
known and the alignment (`odyssey.align`, as for every GLAUx text) runs speech by speech. What the
merge needs that the other texts do not: `Play.glaux` names one file, here there are 34 (the
token step takes the speech's file by number); and **the label is per speech**, not per text:
GLAUx's `analysis="manual"` on every sentence of speeches 1, 12, 13, 14, 15, 19, 23, 24, `"auto"`
on the rest. The text files carry one `# syntax: automatic` line for the whole text today, and
the reader shows one label per text. Until the author decides (For the author), the plan is: one
GLAUx source for all speeches; the label "automatic" for the whole text unless the reader learns
a per-book label (a `# syntax-manual: 1 12 13 14 15 19 23 24` header key read by the build into
the sections table would be the small change); the AGDT files for 1, 14, 15, 23 are kept as the
check of GLAUx's manual trees for those speeches (the same trees, converted), not as a second
source. Not built in this stage.

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
8. **Translations.** The 1898 version from the Gutenberg text by speech and section (its
   headings are "ORATION II." … with the OCR's slips "XXXL", "XXXIL"; sections are numbered in
   the text); Gillies's speeches by the prose route from the scan (long s; a free version
   without section numbers: how it is laid beside the Greek is a question for the author).
9. **Commentaries and introductions.** Adams, Morgan, Shuckburgh by the prose route
   (`drama-prose`, a section per editor in `INSTRUCTIONS-prose.md`; each has a general
   introduction and one to each speech); notes keyed `## 12.7`.
10. **sigla.md, glossary.md, shortdefs.tsv, aliases.tsv, about.md** (no `google_play`; a
    `product_id` only once the author has confirmed it), the texts/README.md section.
11. **Build and emulator check** (`build --only lysias`, `check`, `catalog`, the pack; the
    emulator check of PLAN-drama.md step 10: a book chooser of 34 speeches, a heading inside a
    speech, a hypothesis, a speech without English, the apparatus, the syntax label). Memory
    rules as PLAN-hermas.md.

## Hand-over: the agents' runs

(filled in at the end of the set-up stage: see Progress)

## For the author

(filled in at the end of the set-up stage)

## Progress

- [x] Step 1: modules, tests, CLI (2026-11-16): `hude_pages.py` (layout, margins, draft, checker, residuals), `hude_merge.py` (text, apparatus, lemma check), `tests/test_lysias.py`; `lucian_pages.perseus_prose` takes a speech's number, quotations and headings; `Play.unhide`; CLI `hude-pages`, `check-lysias-batch`, `lysias-residuals`, `merge-lysias`; the briefs and workflow scripts in `transcriptions/lysias/`; the 34 Perseus files, the 34 GLAUx files and Gutenberg #6969 in `fetch.py` and fetched
- [x] Step 2: leaves and layout (2026-11-16): text leaves 19–287 (269 pages, with the four leaves the scan hides), SIGLA 18, praefatio 9–16; the tables above
- [ ] Step 3: OCR and draft
- [ ] Pilot: one batch checked by the set-up session
- [ ] Step 4: text and apparatus batches, first pass
- [ ] Step 5: second passes
- [ ] Step 6: merge and the checks
- [ ] Step 7: words and syntax
- [ ] Step 8: translations
- [ ] Step 9: commentaries and introductions
- [ ] Step 10: sigla, glossary, about
- [ ] Step 11: build and emulator check

## Decisions

(append dated entries: what was open, what was chosen, why, which pages were looked at)

## Sizes, for planning

34 speeches, 1,116 sections, 56,162 Greek words in the check text; 265 pages of Hude; 45 text
batches of six pages (the last of one).
