# The four remaining Sophocles plays (Jebb): Trachiniae, Oedipus Tyrannus, Oedipus at Colonus, Philoctetes

The author asked on 2026-11-15: finish the Sophocles plays, **one at a time** (limits are short:
one play finished is worth more than four half done), in the order of least work left:
**Trachiniae → Oedipus Tyrannus → Oedipus at Colonus → Philoctetes**. Delegate to cheaper models
where quality does not suffer; the author finds Opus the best reader of page images.
Building a play is not putting it on sale: never write `google_play: yes`; give the play a
`product_id` (`sophocles_trachiniae_jebb`, `sophocles_oedipustyrannus_jebb`,
`sophocles_oedipuscoloneus_jebb`, `sophocles_philoctetes_jebb`) and stop there.

A session that picks this up: read **Progress** below, `git status`, `git log -5`, then
`grep -c '^=== p-' transcriptions/sophocles/<play>/*.md` to see which pages are on disk.
Commit after every verified stage. The method is the one Ajax and Electra were made with
(texts/README.md, "Sophocles' other plays"; the briefs in `transcriptions/sophocles/`).

## The route: the drama pipeline (OCR, flags, residuals), not the old by-eye batches

**The author, 2026-11-15: "follow the paths that have already been proven to be most efficient
and least prone to error."** That is the route of `PLAN-drama.md` (read its "How to work from
this brief", "Steps for each play" and Decisions before anything else), by which every text
since the Gorgias was made, the Clouds on pages laid out like Jebb's (`layout="jebb"`):
Tesseract reads the page, the OCR is matched to the check text, agents decide only the flagged
places and copy the apparatus from crops, a residual pass settles what flags do not see
(punctuation, brackets, low-confidence words), and the print's own verse division and margin
numbers come from the page, so no separate lyric pass is needed. The old Sophocles briefs
(INSTRUCTIONS.md, LYRICS.md: agents read whole pages by eye) are NOT to be used for new pages.

What has to be set up once for the Sophocles plays (then each play is a `drama.PLAYS` entry):

1. **A `Play` entry** per play in drama.py: scan (`SCANS` in sophocles_pages.py), `layout="jebb"`,
   the AGDT treebank (Trachiniae, OT) or GLAUx (OC, Philoctetes) as `sophocles.PLAYS` names them,
   Jebb's translation from Perseus, product id, `text_leaves` (the PDF page numbers in
   build/sophocles-pages/pages.json are not leaf numbers: convert with the scan's scandata.xml,
   `leaf_of`, and look at the first and last text page).
2. **The check text is Jebb's own text from Perseus** (`sources/<play>.perseus-gk.xml`, TEI P4,
   read today by sophocles.py / tei_p4.py), not the canonical grc2 file `load_perseus` expects:
   give `load_perseus` a P4 reader that returns the same structure as `perseus_play` (tokens,
   lines, sections, stage directions, speakers), with a test.
3. `drama-pages <play> fetch | ocr | draft` in the background; read the summary. More than 70 %
   of the lines flagged on clean print = the matching or the layout is wrong: fix the module
   first (the rough test of 2026-10-23 flagged 53 % of Jebb's lines, with a cruder
   normalisation than drama_pages has; the Agamemnon had 26 %).
4. Text batches (`transcriptions/drama/<play>/batch-NN.md`, INSTRUCTIONS-text.md, six pages
   each, Opus, at most 10 at once, by workflow), checker, then `drama-residuals` and its pass
   (RESIDUALS.md); the Clouds also had a review agent per batch (REVIEW.md): use it only if
   the author asks.
5. `merge-drama <play>`. **What Perseus already gives stays**: Jebb's commentary
   (`commentary-jebb.md`) and his introduction, made by `import-sophocles`; make sure the merge
   keeps them (the commentary is keyed to Jebb's line numbers, which the merged text now
   carries) and that `import-sophocles` is no longer run for a play once it is on this route.
6. **The English prose Perseus lacks** by the prose OCR route (`drama-prose`, word flags,
   INSTRUCTIONS-prose.md, eight pages per agent): the manuscripts chapter and the pages before
   the text (kind `intro`, added after Perseus's chapters as `import-sophocles` does today),
   and Jebb's Appendix (a new kind `appendix`, written as `appendix.md` in the format of
   texts/electra/appendix.md; APPENDIX.md and INTRODUCTION.md keep their format rules). For
   the Oedipus Tyrannus and the Philoctetes the whole introduction, for the Philoctetes the
   whole commentary (kind `notes`), come this way too.
7. `sigla.md`, `glossary.md`, `shortdefs.tsv`, review list, `about.md` with its `product_id`
   (no sale mark), `build --only <play>`, `check`, `catalog`, the asset pack, play/README.md
   row, texts/README.md, emulator check: as PLAN-drama.md steps 8–10.

## Which model reads

Page agents on Opus (PLAN-drama.md; the author finds Opus the best reader). A blind test was
started 2026-11-15: Sonnet re-transcribed Electra pp. 150–153 and 301–302 without seeing
Opus's batches; result under Progress when it is in. Sonnet is for code written to a contract,
tests and mechanical checks.

## What each play still needs

| play | text pages | appendix | front matter to transcribe | other |
|---|---|---|---|---|
| trachiniae | 80–257 | 259–284 | MSS chapter 55–58; Jebb's note in place of the argument, persons, structure 77–79 (rendered) | — |
| oedipustyrannus | 110–300 (110–133 done: batch-01, 01b, 02) | 301–334 | whole introduction PDF 15–66 (Perseus lacks it; MSS ~57–61), arguments 104–107 | Perseus has the 1887 text, the scan is the 1893 third edition: the text follows the scan |
| oedipuscoloneus | 100–363 | 365–388 | MSS ~53–57, persons ~97 | GLAUx syntax (automatic) |
| philoctetes | 76–297 | 299–324 | whole introduction 11–49 (MSS ~47–49), 73–75 | GLAUx syntax; the whole commentary from the column crops (`prepare_commentary`, build/sophocles-pages/philoctetes-commentary): Perseus lacks it. OCR (egt_ocr.py route) helps most for these English parts |

The metrical analyses are not transcribed (as for Ajax and Electra).

## Progress

* **2026-11-15, Trachiniae.** Before the author's word on the route, eight by-eye batches of
  the old kind were started (transcriptions/sophocles/trachiniae/batch-01…08, pages 80–143,
  Opus). They are let finish and kept **only as an audit**: once the drama route has merged the
  text, compare its verses and apparatus for those pages with these batches and look at every
  disagreement on the page. Nothing else of the old route is run. Next: set-up items 1–3 above
  for the Trachiniae. PDF pages 77–79 rendered (build/sophocles-pages/trachiniae).
* **2026-11-15, set-up items 1–2 done** (commit a41903c): `Play.check_text` and
  `drama.textfile_play` (the check text read from `sophocles/<play>/reference-grc.txt`, Jebb's
  Perseus text as first imported: 7,294 words, 1,248 lines for the Trachiniae), and the
  `trachiniae` entry (leaf = PDF page; text leaves 80–257, the Greek on the even ones).
  Item 3 started: `drama-pages trachiniae fetch`, `ocr`, `draft`, log in
  `build/logs/trachiniae-pages.log` (idempotent: run again if cut off). **Next**: read the
  draft's summary (share of flagged lines), look at two drafted pages against the images, then
  the text batches (item 4). **Before `merge-drama trachiniae`** (item 5) the merge needs:
  a translation mode that leaves `eng-jebb.txt` alone (today `translation="perseus"` reads a
  canonical TEI file; Jebb's is P4, already imported), and nothing that overwrites
  `commentary-jebb.md` or `introduction.md` unless prose batches exist (drama.py lines
  ~1340–1360 write them only then: check); the `source` line of grc.txt names the check text.

## Decisions

* 2026-11-15: order by least work left (Trachiniae first).
* 2026-11-15: the drama pipeline's OCR route for all four plays (the author's word; see "The
  route"). My first choice that day, to go on with the old by-eye batches, was wrong: it
  ignored that the route had been replaced after the Gorgias and the Agamemnon showed what a
  reader's eye misses (PLAN-drama.md, Decisions, "Agamemnon step 4: a second pass").
