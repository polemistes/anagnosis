# Lucian, A True Story (Ἀληθῶν διηγημάτων α´ β´), from Nilén's Teubner edition

Decided with the author on 2026-11-08 after an assessment of Lucian's corpus (see the memory
note "lucian-sources" and, for the pipeline's rules, `pipeline/PLAN-drama.md`, whose rules hold
here unless this file says otherwise; the prose route is the Gorgias's,
`pipeline/transcriptions/gorgias/INSTRUCTIONS.md`). This file is the brief: follow it step by
step in the order given, tick the steps off under **Progress**, write every choice the brief
does not settle under **Decisions** (dated, with the pages looked at), and commit after each
step, this file with it. Where the brief leaves something open, take the choice that keeps the
data closest to the printed page, write it under Decisions and go on; the questions that only
the author can answer are collected under **For the author** and never block the next step.
The work may be cut off at any moment: every step saves to disk as it goes and can be run again
from where it stopped (`git status`, `git log -5`, Progress and Decisions here, then
`grep '^=== ' ` on the batch file being written shows the first missing page).

## What ships, and the one rule behind it

**Nilén's text with Nilén's apparatus.** Nothing of Harmon's Greek ships. The Perseus text
(Harmon's Loeb, 1913) is the *check text*: Tesseract reads Nilén's pages, the OCR is matched
word by word to Harmon to find where Tesseract erred, and every disagreement is decided by an
agent from the page image, Nilén's reading winning. Where Nilén and Harmon differ (θαλάσσης
against θαλάττης, 1.7), Nilén's word stands and his apparatus item under it records the
variants. An apparatus that belongs to another text would make us the editor; the same-edition
rule of PLAN-drama.md forbids it. The author's words: a matched apparatus "will no longer be
Nilén's apparatus, but an altered one, which will make you the editor".

## Decisions already taken (do not reopen)

| what | source |
|---|---|
| Greek text and critical apparatus (one edition) | N. Nilén, *Luciani Samosatensis libelli*, vol. I fasc. 1, Leipzig, Teubner, 1906 (libelli I-XIV; Nils Nilén 1851-1930/31). Scan **bub_gb_RYepnZKT1OwC** (Google/Michigan, 280 page images, jp2 240 MB, about 2500 px across a page, clean on the pages seen). Running heads "13. VERAE NARRATIONES. I. VULG. 26" and the page number; text in Teubner type (ϑ for θ) with line numbers every fifth line in the left margin, the Vulgate (Hemsterhuis) page numbers also in the left margin (2-3 digits, e.g. 75, 203), the **chapter numbers in the right margin** (7, 21), a rule, then the apparatus keyed by line number ("5 πνέοντι ΓΩS πνεύματι ZNF"). About 20 lines of text and 20 apparatus items per page; A True Story about 80 pages, so about 1,500 items. The Archive's own OCR of this item is useless (wrong language); ours is run as always |
| check text (never shipped) | Perseus canonical-greekLit `tlg0062.tlg012.perseus-grc2.xml` = Harmon's Loeb vol. I (1913), book.section numbering (`div subtype="book"` / `"section"`), with Harmon's 26 critical footnotes as `<note>` elements (strip them from the check text; keep them as the checklist of step 5) |
| translation | A. M. Harmon (Loeb 1913; d. 1950), Perseus `tlg0062.tlg012.perseus-eng2.xml`, CC BY-SA 4.0, by book.section; his footnotes left out as for every Perseus translation. Not the Fowlers (eng4): they cut 1.22 and 2.19 |
| commentary 1 | C. S. Jerram (d. 1914), *Luciani Vera Historia*, Oxford, Clarendon Press, 1879: introduction, text with English summaries, **notes at the back**. Scan **lucianiverahisto00luci** (UC, 114 images, jp2); spares lucianiverahisto0000csje (114, jp2), lucianiverahist00lucigoog (125, jp2) |
| commentary 2 | Dickinson College Commentaries, *Lucian, True History* (Eric Casey, Evan Hayes, Stephen Nimis, 2023), https://dcc.dickinson.edu/lucian-true/ : notes on 1.1-1.42 and book 2, text based on Harmon. Licence: "Dickinson College Commentaries by Dickinson College is licensed under a Creative Commons Attribution-ShareAlike License" (https://dcc.dickinson.edu/terms-use). Notes only; their running vocabulary is not taken (the reader has the dictionaries). The Faenum/Hayes-Nimis reader it grew from is CC BY-NC-SA: never use it |
| introduction | Jerram's introduction in full (the prose route, kind `intro`), with the heading rules of `pipeline/transcriptions/sophocles/INTRODUCTION.md`; lists of editions left out. The DCC introduction is left out (one introduction per text; the author may add it later) |
| syntax | **GLAUx 0062-012.xml throughout** (automatic, CC BY-SA 4.0), aligned to Nilén's words. The Harrington trees (perseids-publications/harrington-trees, grctb.5279 = 1.1-1.4, grctb.5280 = 1.5-1.42, CC BY-SA 4.0, hand-made) cover exactly book 1 but use their own set of 133 relation labels ("N-SUBJ", "A-DO", "CP-TEMPOR_SBJ"), not the treebank's; mapping them is judgment work and would give the text two kinds of tree. Not used now; recorded under For the author as a later upgrade for book 1 |
| sigla | `sigla.md` written by hand from Nilén's list of manuscripts and signs (his praefatio or conspectus siglorum in the scan: find it at step 2; if the scan has none, from Harmon's Loeb vol. I introduction "The manuscripts", scan lucianha01luciuoft, which follows Nilén's sigla). Seen on the pages: manuscripts Γ Ω Z S B P U N F I, v = vulgate, editors Ibtz (Jacobitz), Dind, Bekk, Sbdt (Sommerbrodt), Schw (Schwartz), du Soul, Guyet; mg., ras., spscr., corr., "ex corr." |
| slug, titles, product | `truestory`; Greek title Ἀληθῶν διηγημάτων (Perseus's; Nilén prints VERAE NARRATIONES), English "A True Story"; author Λουκιανός / Lucian; product id `lucian_truestory_nilen`, €3, `google_play: yes` |
| pronunciation | `# pronunciation: koine` in grc.txt (second century AD); the author may switch it to attic |

* **The unit of the text is the section**: one line of grc.txt per book.section (`1.7`), the
  reference everyone uses, with `# layout: prose` and `# syntax: automatic`. Paragraphs (`@ `)
  where Nilén indents; where he prints none across a whole section, none are added. The batch
  files the agents check are still **per printed line** with Nilén's page and line as the key
  (`133.5`), as the Gorgias batches are per Burnet line, because the apparatus cites his lines;
  the merge joins the lines into sections. A chapter number that begins inside a printed line
  (1.7 at "προελθόντες" on p. 133 line 14) is placed from the Perseus token where the section
  changes, and the margin number is the check.
* **Apparatus items** go under the section that holds the lemma, copied as printed (Greek,
  Latin, sigla, the editors' abbreviations), **without Nilén's page-line number in front**: it
  refers to his page, which the reader does not see; the lemma identifies the word. An item on
  a range ("20/22 ἄν — διπλασιάσαντος]") keeps the lemma range. An item whose lemma is not in
  the text (an addition: "5 τῇ τύχῃ, post ἑαυτοὺς add. Z") goes under the section of the word
  it names. Nilén's typographical signs (the asterisk in προ*ελθεῖν, ‖, —) are kept as printed;
  sigla.md explains them.
* **Nilén's spacing before punctuation** ("ἦν . ἐπιτρέψαντες", "ὀφθαλμῶν . ἀκούετε") is a
  printing convention: written without the space. His raised stop is ·, elision ʼ (U+02BC),
  ϑ ϱ ϐ ϰ written θ ρ β κ (the Theogony's `ocr_fold`), iota subscript as he prints it.
* **Two checks that this edition makes possible and the brief requires** (step 5): (a) every
  apparatus item's lemma must be found in its section's text (skeleton match); a miss is listed
  and an agent decides from the page: either the lemma is a variant Nilén rejects (fine) or
  the text has slipped to Harmon's reading (fix it). (b) Harmon's 26 footnotes name the places
  where his text departs from the manuscripts or adopts a conjecture; each is looked up in
  Nilén's page and the text's reading confirmed from the crop. These two checks are what makes
  "matched to Harmon" safe: they catch the one case the flags cannot, an OCR error that lands
  exactly on Harmon's reading.
* **Not usable, ever**: Macleod's and Kilburn's Loebs and the OCT, Harmon's vol. V (1936) for
  any other Lucian, the Faenum readers (NC), Yates's Bell edition (death year unknown), Helm's
  revisions of Sommerbrodt's school edition.
* **Agents**: one agent per batch of six pages, the checker on every returned file, unresolved
  remarks to a fresh agent, then the residual pass (`pipeline/transcriptions/drama/RESIDUALS.md`,
  adapted to prose: punctuation, accents, the asterisks and brackets, the chapter boundaries).
  If the author has turned "ultracode" (workflows) on, run the batches as workflows with an
  independent review agent per batch (`REVIEW.md`), at most 10 agents at once; otherwise the
  brief's route. Every agent keeps its helper files in a folder of its own.

## Steps

1. **Module work** (tests with each change; `cd pipeline && .venv/bin/python -m unittest discover -s tests`).
   * `fetch.py`: `drama/tlg0062.tlg012.perseus-grc2.xml`, `drama/tlg0062.tlg012.perseus-eng2.xml`
     (the canonical-greekLit raw pattern already there), `glaux/0062-012.xml`.
   * A reader for a Perseus **prose** P5 file: tokens with their `book.section`, `<note>`
     elements stripped and returned separately (Harmon's footnotes, for step 5). The drama
     `load_perseus` is verse-shaped; the NT importer and `tei_to_document` are the models.
   * `lucian_pages.py` from `gorgias_pages.py` (copy and generalise; do not break the Gorgias):
     the scan and leaves from a `Play` entry in drama.py (`PLAYS["truestory"]`, with `scan`,
     `text_leaves`, `sigla_leaves`, `notes_scan`, `notes_leaves`, `intro_leaves`, `ocr_fold`,
     `skel_fold` as the Theogony's), the Perseus tokens from the prose reader, the margin marks
     of Nilén's page: line numbers every fifth line at the left (digits, multiples of 5), the
     Vulgate page numbers at the left (2-3 digits, not multiples of 5 as a rule; recorded but not
     used), the chapter numbers at the right (the anchors to Perseus sections). `number_lines`
     gives each printed line its key `page.line` and the section it begins in. The apparatus
     block under the rule as the Gorgias's (`apparatus_top`, full-width and two enlarged halves).
     Commands `lucian-pages fetch|ocr|draft`, `check-lucian-batch FILE...`, `merge-lucian` in
     `__main__.py`.
   * `merge-lucian`: grc.txt (one line per section, paragraphs, header keys incl. pronunciation),
     `commentary-nilen-apparatus.md` (`## 1.7` headings, items under their section), the lemma-in-
     section check (a report in `pipeline/build/truestory-merge.log`), the Harmon checklist
     (`pipeline/build/truestory-harmon-notes.md`: each note with its section and Nilén's reading
     to confirm), tokens from GLAUx aligned by words (`align`, the analyser for the rest), the
     review list `pipeline/build/truestory-review.tsv`, `HAND_ANALYSES`/`LEMMA_FIXES` in
     drama_fixes.py, the translation from Perseus by section, Jerram's and the DCC notes placed
     by section.
   * `pipeline/transcriptions/lucian/INSTRUCTIONS.md` from the Gorgias brief with a Nilén section
     (the page, the margin numbers, the apparatus format and abbreviations, the spacing rule, the
     asterisks), and the prose brief for Jerram's notes and introduction (`INSTRUCTIONS-prose.md`
     gets a Jerram section: how his notes are keyed, see step 6).
2. **Leaves.** From the scan's page images (`https://archive.org/download/bub_gb_RYepnZKT1OwC/page/n<N>_w700.jpg`;
   p. 133 = image n200, so image n = page + 67 there; check at both ends, Google scans can skip
   pages): the first and last pages of Verae narrationes I and II (running head "13." / "14."),
   the praefatio or conspectus siglorum, the title page (the edition's full title for the header
   and about.md). Write them into `PLAYS["truestory"]`. Look at six text pages and note the layout
   under Decisions. Commit.
3. **OCR and draft.** `lucian-pages truestory fetch`, `ocr`, `draft` in the background; read the
   summary (pages, lines, flagged). Expect 10-25 % flagged after the folding (the Theogony: 19 %);
   over 50 % means the matching or the layout reading is wrong: fix the module, do not send it
   to agents. Nilén's and Harmon's texts are close (Harmon called Nilén's "the only satisfactory
   critical edition" and used it), so most flags will be OCR errors.
4. **Text and apparatus batches.** Agents on `pipeline/transcriptions/lucian/truestory/batch-NN.md`,
   six pages each, with INSTRUCTIONS.md; checker on every file; commit every few batches; then
   the residual pass. About 14 batches.
5. **Merge and the two checks.** `merge-lucian truestory`; read the merge log: the lemma misses
   and the Harmon checklist go to one agent with the page crops, who fixes the text where it
   slipped and writes under Decisions what each case was; the review list to one agent (lemma
   empty or wrong); `check`; ten random sections compared with the page by eye. Commit.
6. **Jerram's notes.** `drama-prose truestory notes fetch|ocr|draft` on scan lucianiverahisto00luci
   (notes at the back; find at step 2 how he keys them, by his page and line or by chapter, and set
   `note_start` and the Jerram section of INSTRUCTIONS-prose.md so that each note gets its
   book.section; where he keys by page and line, the merge finds the section by the lemma in the
   Greek, `_locate_fuzzy` as for Lodge). Agents on `notes-NN.md`, eight pages each; checker; merge
   again; read the log (notes it could not place).
7. **Introduction.** Jerram's, the same route with `intro`.
8. **The DCC notes.** Fetch the commentary pages of https://dcc.dickinson.edu/lucian-true/ (find
   the page per section range from the site's navigation; keep the HTML in
   `pipeline/sources/dcc/`), convert the notes to `commentary-dcc.md` (`## 1.7` headings, the
   lemma in bold, the note's text; vocabulary lists and images left out), header `# license:
   CC BY-SA (Dickinson College Commentaries)` with the editors' names and the URL. Read twenty
   notes against the site by eye. Commit.
9. **Translation, sigla, glossary, short definitions, about.md, README.** The merge writes
   `eng-harmon.txt`; read its log. sigla.md from Nilén's page (step 2). glossary.md for the
   names (Endymion, Phaethon, Rhadamanthus, the Islands of the Blest, the Moonites and
   Sunites: expect many coinages; the analyser will miss Lucian's invented words, which go to
   shortdefs.tsv or the glossary with a gloss from Harmon's translation). about.md as
   texts/gorgias/about.md, with `ref_edition`, `ref_translation`, `ref_commentary` (Jerram and
   DCC), `syntax` "machine-made (GLAUx), not checked by hand", `google_play: yes`,
   `product_id`. A "Lucian" section in texts/README.md, the row in play/README.md. Commit.
10. **Build.** `build --only truestory`; `check`; the pack: copy app/packs/theogony/build.gradle.kts
    to app/packs/truestory/ with the slug changed, add `truestory` to the list in
    app/settings.gradle.kts and to `assetPacks` in app/androidApp/build.gradle.kts; `catalog`.
    Then the emulator check of PLAN-drama.md step 10 for this one text: buy it in the debug shop,
    open it, read a section, open the apparatus, a Jerram note, a DCC note, the introduction, the
    sigla, the syntax of one sentence, play a line aloud; fix what is wrong; `adb emu kill`,
    `./gradlew --stop`. A reader release is the author's call.

## For the author

* **Pronunciation**: set to koine; say if you want attic.
* **Harrington's hand-made trees for book 1**: usable later if their 133 relation labels are
  mapped to the treebank's; the text would then have hand trees for book 1 and GLAUx for book 2.
* **The DCC introduction**: left out; say if you want it after Jerram's.
* **Nilén's fasc. 2 (1923)** holds five more works with his apparatus but has no scan on the
  Archive; the Symposium and the Judgement of the Vowels among them have Pedalion hand trees.
* **Release**: the text is built and in the catalogue after step 10; a reader release with it is
  yours to decide (play/README.md: build the bundle, upload, create and activate the product
  `lucian_truestory_nilen`, name "A True Story", €3).

## Progress

- [ ] Step 1: modules, tests, CLI
- [ ] Step 2: leaves
- [ ] Step 3: draft
- [ ] Step 4: text and apparatus batches, residuals
- [ ] Step 5: merge, lemma check, Harmon checklist, review
- [ ] Step 6: Jerram's notes
- [ ] Step 7: introduction
- [ ] Step 8: DCC notes
- [ ] Step 9: translation, sigla, glossary, about, READMEs
- [ ] Step 10: build, pack, catalogue, emulator check

## Decisions

(append dated entries: what was open, what was chosen, why, which pages were looked at)

## Sizes, for planning

A True Story: 11,200 Greek words (book 1 sections 1-42, book 2 sections 1-47), about 80 Nilén
pages, about 1,500 apparatus items; Jerram's notes about 50 pages, his introduction 23 pages.
The Theogony (48 pages, 642 items) took one day of agent batches; expect two to three days and
roughly twice its token cost, most of it on the apparatus.
