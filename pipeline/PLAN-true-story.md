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
* **Misprints in Nilén's text**: 144.3 σκοκῶν (for σκοπῶν, 1.18), 144.7 μεγέθος (for μέγεθος) and
  probably 144.21 ἐξώγρησαν (for ἐζώγρησαν)
  are kept as printed, with the right analysis on the word sheet; say if you want them corrected
  in the text (with a note in the apparatus).
* **Short definitions folded by case (all texts)**: `build.load_logeion_shortdefs` keeps the first
  of a capitalised and a lower-case Logeion entry, so ὕλη shows "Hyle, a town in Boeotia" and
  Ὅμηρος "hostage"; the True Story overrides its cases in shortdefs.tsv. Fixing the loader would
  mend every text; say if you want it done.
* **Release**: the text is built and in the catalogue after step 10; a reader release with it is
  yours to decide (play/README.md: build the bundle, upload, create and activate the product
  `lucian_truestory_nilen`, name "A True Story", €3).

## Progress

- [x] Step 1: modules, tests, CLI (2026-11-08): `lucian_pages.py`, `lucian_merge.py`, `tests/test_lucian.py`, CLI `lucian-pages`, `check-lucian-batch`, `merge-lucian`; `transcriptions/lucian/INSTRUCTIONS.md`
- [x] Step 2: leaves (2026-11-08): Nilén text leaves 196-275, sigla 10, 11, 13, 16, title 4; Jerram notes 81-100, introduction 15-29, his text 31-79
- [x] Step 3: draft (2026-11-08): 80 pages, 1480 lines, 220 flagged (14 %), all 89 sections placed, apparatus and short rule found on all 80 pages; 14 batches
- [x] Step 4: text and apparatus batches, residuals (2026-11-08): 14 batches checked and independently reviewed (workflows, 7 at a time), residual pass (433 items, 7 agents); every checker remark explained
- [x] Step 5: merge, lemma check, Harmon checklist, review (2026-11-08): 104 lines (89 sections), 1660 apparatus items, 11176 words; 26 Harmon notes and 96 lemma misses settled, ten sections by eye; one slip fixed (144.21)
- [x] Step 6: Jerram's notes (2026-11-08): 20 pages in 3 batches checked and reviewed; 261 notes under 78 sections, placed by his own line numbers mapped to ours
- [x] Step 7: introduction (2026-11-08): Jerram's introduction (pp. ix-xxiii), 2 batches checked and reviewed
- [x] Step 8: DCC notes (2026-11-08): 86 pages (89 sections; 2.7-2.10 one page), 1798 paragraphs; twenty notes compared with the site, all agree
- [x] Step 9: translation, sigla, glossary, about, READMEs (2026-11-08): eng-harmon.txt 89 sections (no problems); sigla.md from the praefatio; glossary 79, short definitions 106, aliases 26, 16 lemma fixes and 12 hand analyses; lexicon coverage complete
- [ ] Step 10: build, pack, catalogue, emulator check

## Decisions

(append dated entries: what was open, what was chosen, why, which pages were looked at)

* **2026-11-08, step 1: modules.** Looked at leaves 196-202, 233, 234, 275 (pp. 129-135, 166,
  167, 208).
  * `drama.Play` gained `page_offset` (printed page = leaf − 67) and `app_rule = "short"`;
    `drama_pages.page_layout` takes an optional `app_y` (default unchanged for the plays). The
    apparatus is everything under Nilén's short rule (`lucian_pages.short_rule`: a band ≤ 10 px
    high, 8-40 % of the page wide, ≥ 30 % inked, blank 28 rows above and below; the rule is
    faint and broken on many pages, so two thresholds). Found on all nine pages tried.
  * Margins: on an odd page the line numbers and the Vulgate pages are left and the chapter
    numbers right, on an even page the reverse (p. 130: chapter 3 left, line numbers right).
    Each margin is cut beyond the column (the median end of the lines' last words) and read
    four ways (psm 7, 8, 10, 13), the commonest reading kept. Tesseract reads Nilén's hooked 5 as
    3 and his chapter 2 as 9: a line mark at a fifth line confirms it whatever it reads, a
    chapter mark at a line where a section begins confirms the place whatever it reads; only a
    plausible misnumbering is flagged.
  * A book's title counts as line 1 of its page (p. 129: the 5 stands at the fifth line counting
    the title); its spaced capitals are read with low confidence and dropped as noise by the
    drama layout, so `page_layout` puts it back. Batch line `129.1	[title] ΑΛΗΘΩΝ ΔΙΗΓΗΜΑΤΩΝ Α`.
  * Batch conventions (not settled by the brief): `§1.7 ` before the word where a section
    begins (also mid-line), `¶` before an indented line, `| ` for verse, apparatus numbers as
    printed (`5`, `1/2`) with the page known from the block, `-` for a note on no line ("Libri:
    …" at the head of each book's apparatus, the subscriptions at the end of each book; filed
    under the section of the page's first line, or of the item before).
  * A paragraph Nilén begins inside a section (p. 208: "Ταῦτα μὲν οὖν", 2.47) continues the
    section on a line of its own lettered `2.47b` after `@ `, as the New Testament does with a
    verse a paragraph divides.
  * Verse inside a section (the epigram, 2.28) is joined into the section's line: one line per
    section leaves no room for verse lines.
  * `skel_fold` "χκξζ": Tesseract reads the Teubner ζ as ξ throughout (ζόφος, ζάλης,
    ἐχειμαζόμεθα on p. 133); ξ counts as ζ in the matching, as χ counts as κ (the Theogony's
    rule). A real ξ/ζ difference between Nilén and Harmon would go unflagged: a risk accepted.
  * Case: the draft takes the case of a word's first letter from the OCR both ways where the
    OCR is sure (Perseus capitalises "Ἄχρι" in the inscription at 1.7, Nilén does not).
  * Harmon's check text has 26 footnotes, as the brief says; `perseus_prose` returns them with
    their section and the word they follow (the note on the title goes to 1.1).
  * A trial draft of pp. 129-135 flagged 22 of 129 lines (17 %): `αὐτοὺς` (1.2, Harmon's
    supplement, absent in Nilén), `ἔμελλον` (Perseus's gap, Nilén's `***`), and OCR errors.
  * The Jerram section of `INSTRUCTIONS-prose.md` is written at step 6, when his notes' keying
    is known (step 2 finds it).
* **2026-11-08, step 2: leaves.** Pages looked at: Nilén leaves 0-72 (OCR of each, images of 4,
  10, 11, 13, 16), 196-202, 215-279 (running heads by OCR; images of 232-234, 275); Jerram leaves
  7-15, 28-31, 35, 80-81, 101-104.
  * **Nilén**: the scan numbers its leaves from 0 with none hidden, so leaf = page image n;
    page = leaf − 67 throughout the text (p. 129 = leaf 196, p. 133 = leaf 200, p. 208 = leaf 275:
    checked at both ends and in the middle). Book I: pp. 129-166 = leaves 196-233 (the title on
    p. 129 below a blank upper half; p. 166 ends after six lines, with the subscription
    "διώρθωσα …" in the apparatus). Book II: pp. 167-208 = leaves 234-275 (title on p. 167; p.
    208 ends with the subscription and Nilén's note "ascribam adnotationem finalem
    scholiastarum …"). 80 pages, as the brief expected. Leaves 276-279: blank and the library's.
  * Title page (leaf 4): "LUCIANUS | edidit | NILS NILÉN | VOL. I. FASC. I | LIBELLI I—XIV |
    MCMVI | LIPSIAE | IN AEDIBUS B. G. TEUBNERI" ("Samosatensis" is a reader's pencil): the
    edition is written "Lucianus, edidit Nils Nilén, vol. I fasc. I: libelli I–XIV, Leipzig, B. G.
    Teubner, 1906" (not "Luciani Samosatensis libelli", as the brief had it).
  * There is no conspectus siglorum of the usual kind: the praefatio (pp. III-XVI, leaves 6-19)
    holds tables. p. VII (leaf 10): every witness used by the editors with its date class (aᵃ-aᵘ
    = 9th/10th-12th c., r = later) and its name (Γ Vaticanus 90, Ω Marcianus 434, S Mutinensis
    193, Z Vaticanus 1323, P Vaticanus 76, N Parisinus 2957, F Guelferbytanus fol., I Urbinas 118,
    B Vindobonensis 123, U Vaticanus 1324, v the Amsterdam edition of 1743 …); p. VIII (leaf
    11): Jacobitz's witnesses, and the note on the date classes; p. X (leaf 13): "Ego hos testes
    adhibui in libellorum 1—14 apparatu": for libelli 13 and 14 (the two books) Γ Ω F N P (*P in
    13: lost at the beginning, "periit in P libelli initium usque ad c. 14 med.") S Z, with
    Nilén's explanation of the asterisks and dashes in the table; p. XIII (leaf 16): further
    codices. The hands (Γᵃ, Γˣ, Γ*, S²) are not explained in what was seen: sigla.md (step 9) says
    what the pages show and reads the rest of the praefatio for it. The appendix apparatus (pp.
    XVII ff., leaves 20 ff.) covers libelli 1-12 only, not ours.
  * Six text pages (pp. 129, 130, 132, 133, 166, 167) and p. 208: 12-21 lines of text (20-21 on a
    full page, fewer above a long apparatus); the margins as recorded at step 1; the short rule;
    the apparatus in Latin with every item headed by its line number (repeated for each item on
    the same line), ranges "1/2", "12/13", "13/14", "12/15"; above the first items of each book a
    paragraph "Libri: ΓΩSZPNF …" naming the witnesses; Nilén's text prints `***` for the lacuna
    at 1.2 (p. 130 l. 12, "ἔμελλον *** Κτησίας") and lacks Harmon's αὐτοὺς (p. 130 l. 3).
  * **Jerram** (scan lucianiverahisto00luci; scandata hides leaf 0, so leaf = page image n + 1;
    its own page numbers: leaf = page + 30, leaf = roman + 6): **1879** (title page "M DCCC
    LXXIX", preface signed January 1879; the brief's date stands). Title leaf 9, preface pp. v-vii
    leaves 11-13, introduction pp. ix-xxiii leaves 15-29 (15 pages, not 23), his text with the
    English summaries pp. 1-49 leaves 31-79 (p. 50 blank), **notes pp. 51-70 leaves 81-100** (20
    pages, not 50), index pp. 71-73 leaves 101-103. The introduction ends: "The text of the present
    edition is that of the Tauchnitz Classics, by C. H. Weise".
  * **How Jerram keys his notes**: under the headings BOOK I and BOOK II, each note begins with
    the line number of **his own text** ("Line 4. μέρος γοῦν, etc., …", "l. 17. σπουδαιοτέρων …",
    "ll. 26, 27. …"), counted from the start of each book and printed every fifth line in the right
    margin of his text pages, which print no chapter numbers and set his English summaries in
    italics between the paragraphs (not counted). So the brief's second case holds: the note's
    section is found from the line. Decided: his text pages (leaves 31-79, `Play.notes_text_leaves`)
    are read by Tesseract and matched to the Perseus words (as the drama route matches a text),
    which gives each of his lines its book.section; the lemma search in Nilén's section is the
    check, `_locate_fuzzy` the fallback. Built at step 6.
* **2026-11-08, step 3: draft.** First run: 1479 lines, 219 flagged (14 %), but the short rule
  missed on 8 pages (leaves 199, 210, 214, 256, 259, 262, 269, 273): there the rule stands only
  16-20 rows below the last line's descenders, and on leaf 259 the rule is 13 px thick. On leaf
  262 (p. 195) the drama fallback then put the last text line into the apparatus. The rule test
  was relaxed (12 blank rows above, 20 below, a band up to 14 px) and checked on all 80 pages: the
  rule is now found on every page, and no rule found before moved by more than 3 px. Those 8
  pages were drafted again (their margin and apparatus caches deleted) and the batches written
  afresh (no agent had touched them). Result: 1480 lines, 220 flagged (14 %), within the brief's
  10-25 %. Of the flags, 181 are "the OCR reads …" (mostly OCR errors on Nilén's δ, ὁ, Δ, μ),
  32 words not found in the OCR, 13 lines guessed, 13 fifth lines whose margin number was not read,
  2 chapter numbers not read. The draft capitalises the first word of every paragraph, as Nilén
  does (the OCR loses the breathing on Ὥσπερ and the like; 60 lines).
* **2026-11-08, step 4: batches.** Ultracode is on, so the batches ran as workflows: per batch a
  checking agent, then an independent reviewer (`transcriptions/lucian/REVIEW.md`), in two waves of
  seven (batches 1-7, 8-14), at most seven agents at once; then the residual pass
  (`lucian-residuals`, `transcriptions/lucian/RESIDUALS.md`): 433 items (128 accent, 119 word, 108
  punctuation, 76 OCR-only, 2 brackets), seven agents with two batches each. The reviewers
  corrected mostly the apparatus (breathings, iota subscripts, a lemma in Latin A, an οἱ/οἳ) and
  two divided words left on the next line (177.3 φυτοῖς, 178.1 συμπόσιον; a scan of every hyphen
  the OCR read found no other); the residual pass changed four things (144.7 μεγέθος, 199.8 a
  comma, 202.4 a dash, the siglum below). Every checker remark left is one of Nilén's own readings
  against Harmon's, noted (αὐτοὺς absent 130.3, συγγεγραφότας 130.10, κατετέθημεν 154.2, [καὶ]
  161.16 and 180.9, [λέγων] 182.8, no καὶ 173.11, no τὸν 186.10, ἀπενενέκρωτο 168.1, …).
  * Conventions settled on the way (INSTRUCTIONS.md updated): Nilén's black blocks (a printed sort
    for letters lost in a manuscript) are written ■, one per block; apparatus numbers may be
    `18 sq.` and `8 et 9` (the checker and the merge accept them; three items written "sq." at
    the start of the item were moved into the number); a range printed "13—16" is written 13/16;
    the raised sign after Γ at pp. 143, 201, 202 is read Γ³ (a flat-topped 3; the reviewer of
    batch 3 compared the three places), not Γˢ.
  * **Paragraph capitals**: the brief said Nilén capitalises the first word of a paragraph and the
    draft did so (60 lines); the pages show that he does so only at the start of a book and in two
    places (Ὁρμηθεὶς 1.5, Ταῦτα 2.47; Τὸ 2.1), and begins the other paragraphs with a small letter.
    The agents followed the print, and the residual pass checked the first word of every ¶ line.
  * Misprints in Nilén's Greek text are kept as printed (the brief's rule: closest to the page),
    each noted in its batch: 144.3 σκοκῶν (for σκοπῶν), 144.7 μεγέθος (for μέγεθος). In the apparatus
    likewise (ἀλκίνουυ p. 131, ΓFSN p. 185). Listed for the author.
* **2026-11-08, step 5: merge and the two checks.** `merge-lucian truestory`: grc.txt 104 lines
  (89 sections, 15 continued after a paragraph inside a section, 2.47b and the like), 46
  paragraphs; 1660 apparatus items under 103 lines (the brief guessed 1,500); tokens 11,176 words,
  all with a lemma; 0 problems (every Perseus section once, in order). `check`: 0 errors.
  * The lemma check was sharpened before it was used: fuzzy matching would have accepted a slip
    (θαλάττης for θαλάσσης), so a lemma counts as found only when it is in the text exactly; and a
    **slip** is told by its shape: Nilén's first reading missing from the text while a later reading
    of the same item stands there, or an explicit `lemma]` not found ("SERIOUS", 22). Variants that
    match nothing (Nilén's negative items: additions, omissions, word order, manuscripts' spellings)
    and items without a Greek lemma are listed apart ("WEAK", 74). A merge guard: Jerram's notes and
    introduction are merged only once every flag in their batches is answered.
  * Three agents (a workflow): (1) the 22 serious misses and Harmon's 26 footnotes
    (`build/truestory-harmon-notes.md`): every one already Nilén's reading: the 22 are manuscripts'
    readings and corrections (Γ*ᵃ, spscr., γρ mg.) or conjectures (Lehmann's Ἀεροσκόρδακες), and
    Nilén writes Schwartz's numerals ϛ (2.2) and ⟨ε⟩ (2.11) only in the apparatus, printing ἐς ἓξ
    and ⟨πέντε⟩ in the text; at the 26 Harmon places the text has Nilén's reading (αὐτοὺς absent
    1.2, συγγεγραφότας, *** 1.2, οὐδὲ ὀλίγον 1.16, [καὶ οὗτοι] 1.16, no με 1.21, ἔντερον δὲ οὐδὲ ἧπαρ
    and ῥῖγος ᾖ 1.24, κατετέθημεν 1.29, ⟨μεγάλοι καὶ⟩ 1.31, ἀπενενέκρωτο 2.1, ⟨πέντε⟩ 2.11, [λέγων]
    2.20, Κάρανος 2.22, ἐπεσκόπουν 2.42, …). (2) the 74 weak misses: **one slip**, 144.21 (1.18):
    the text kept Harmon's ἐζώγρησαν where Nilén prints ἐξώγρησαν (a ξ, compared with δεξάμενον and
    πεζομαχίας on the same pages): the ξ/ζ fold of step 1 hid it from the flags, the risk accepted
    then; and one apparatus letter (177.12/13 ζ for ξ). (3) ten sections chosen at random (1.2, 1.11,
    1.29, 1.39, 1.42, 2.8, 2.13, 2.16, 2.29, 2.44), text and apparatus against the page: all agree.
  * The review list (23 words): three analyses set by hand in `drama_fixes.HAND_ANALYSES["truestory"]`
    (κατετέθημεν from κατατίθημι, ἀπενενέκρωτο pluperfect, Ἐκβαλοῦσα the island's name); the
    others were right (σκοκῶν and μεγέθος, Nilén's misprints, have σκοπός and μέγεθος).
  * Nilén's black blocks in "ἔμελλ■ ambig. Z" (p. 130) are two small blocks stacked in one letter's
    width; written as one ■.
* **2026-11-08, steps 6-7: Jerram.** `drama-prose truestory notes|intro fetch|ocr|draft` (the
  batches now go to `transcriptions/lucian/truestory/`, `drama_prose.transcriptions_for`); 571 and
  132 flags. `Play.note_start` for Jerram: "Line 4.", "l. 17.", "ll. 26, 27." and the OCR's 1./I./|
  for l.; headings `## N` under `# Book I` / `# Book II` (the prose checker resets the order at a
  Book heading and does not compare his numbers with ours). Five batches, each checked and
  independently reviewed (a workflow of 10 agents), every checker remark explained. The section
  of each note: `lucian_merge.jerram_line_map` reads his Greek text pages (leaves 31-79) and matches
  them to the Perseus words, numbering his lines from the numbers printed every fifth line (in the
  outer margin: right on right-hand pages, left on left-hand pages, where Tesseract reads them as
  the line's first word); a page's lines are numbered from the nearest number above them; a line
  counts only if half its words and two of three letters or more are matched (lines of loose
  accents and his italic English summaries do not). Built in three rounds: the first read the
  right margin only and drifted 2-6 lines by book I line 150; the last leaves 17 notes whose lemma
  stands a line away (a word divided at the line end, or Jerram's misprint: "l. 247" for 237, "607"
  for 617, both found by the lemma), and the note goes under the section of the word its lemma
  names, searched up to 12 lines either way. Lemmas that follow Weise's Tauchnitz text where it
  differs from the Perseus words (αὑτοὺς 1.72, Ἀεροκόρακες, Κοττυφίων, ἀπενενέκρωτο …: 13 notes) are
  filed by the line. Result: 261 notes (paragraphs) under 78 sections. Jerram's line numbers are
  not kept in the notes (they refer to his text); the bold lemma identifies the word.
* **2026-11-08, step 8: DCC.** The site's pages are `https://dcc.dickinson.edu/lucian-true/book-1/1-7`
  (the brief's base URL redirects to the front page); 2.7-2.10 is one page (`2-7-2-10`), filed
  under 2.7; the introduction page saved too (not used). Saved in `pipeline/sources/dcc/lucian-true/`
  (ignored by git, as all sources). `lucian_merge.write_dcc`: the notes field of each page (the
  vocabulary tab and the "VERB LIST" link left out), the italic summary as *…*, the lemma (the
  words before the first colon, or the Greek that opens a note without one) in bold, the grammar
  links kept as text ("(S. 1328, 1356; G. 511c)"). Licence (terms-use page): "Creative Commons
  Attribution-ShareAlike License". Twenty notes chosen at random were compared with the pages'
  text programmatically, word for word: all twenty agree.
* **2026-11-08, step 9.** The translation: `eng-harmon.txt`, one segment per section, the merge
  log reports none missing. Two agents (a workflow): (1) `sigla.md` from Nilén's praefatio (pp. III-
  XVI): the seven witnesses of libelli 13-14 (Γ Ω S Z P N F) with their date classes (p. VII),
  the occasional ones (I, i, A, O, ε, v), Nilén's own key to the correctors' marks (p. XI: ¹, *,
  ², ³, ˢ/ᵃ, ᵛ/ˣ …), the editors named in the apparatus, and the signs and abbreviations (Nilén
  gives no key for these: the page says they are read as usual in a Teubner apparatus). Two
  scholars' particulars the agent gave from memory (Belin de Ballu's date, Schmieder's place) were
  cut to their names. (2) `glossary.md` (79 names and coinages, glossed from Harmon's English and
  the parts of the compounds), `shortdefs.tsv` (106), `aliases.tsv` (26), and lemma fixes applied
  in `drama_fixes.py` (`LEMMA_FIXES["truestory"]` 16: GLAUx's garbled πηρεληλύθειμνυμι for
  παρεληλύθειμεν, ἀπoβρέχω with a Latin o, Λουκιάν, Ὕλη for Hylas, Ἶρις for the rainbow …;
  `HAND_ANALYSES` 9 more: cases and genders of names). `check`: every lemma found in a dictionary,
  the glossary or the short definitions.
  * The glossary agent found that `build.load_logeion_shortdefs` folds capitals, so a common word
    can get a name's definition and a name a common word's (ὕλη "Hyle, a town in Boeotia", Ὅμηρος
    "hostage", Πλάτων "ladle"); `shortdefs.tsv` overrides the cases in this text (41 lines). Other
    texts are likely affected: recorded for the author, not changed here (shared code).
  * `about.md` as the Gorgias's (GLAUx, machine-made syntax); "A Lucian" section in texts/README.md;
    the row in play/README.md.

## Sizes, for planning

A True Story: 11,200 Greek words (book 1 sections 1-42, book 2 sections 1-47), about 80 Nilén
pages, about 1,500 apparatus items; Jerram's notes about 50 pages, his introduction 23 pages.
The Theogony (48 pages, 642 items) took one day of agent batches; expect two to three days and
roughly twice its token cost, most of it on the apparatus.
