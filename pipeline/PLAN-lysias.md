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

## For the author

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
* Still open: whether the Eroticus (XXXV, from Plato's Phaedrus) goes in.


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
