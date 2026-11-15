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

## Steps for each play

Page ranges (PDF pages = image numbers) are in `build/sophocles-pages/pages.json`.

1. **First pass** (INSTRUCTIONS.md): critical apparatus and text check, 8 pages per agent,
   files `batch-NN.md`, numbered in page order. Agents: general-purpose, **Opus**, at most 10
   at once, each appending page by page and running `check-sophocles-batch`. Run them with the
   workflow `transcriptions/sophocles/sophocles.workflow.js` (args in its header; `kind: batch`),
   ten jobs at a time. Do NOT run `import-sophocles <play>` while first-pass agents work
   (they compare with the frozen `reference-grc.txt`, but the lyric pass reads `texts/<play>/grc.txt`).
2. **Appendix** (APPENDIX.md, `appendix-NN.md`, ~7 pages per agent) and **front matter**
   (INTRODUCTION.md, `introduction-NN.md`): independent of step 1, can run beside it.
   Front-matter pages may have to be rendered first (pdftoppm, width 1600, as `_render` in
   sophocles_pages.py); find them with `pdftotext -f N -l N`.
3. `check-sophocles-batch <play> <all batch files>`; look at the agents' `--- notes`; then
   `merge-sophocles-apparatus <play>`, `import-sophocles <play>`; commit.
4. **Lyric pass** (LYRICS.md, `lines-NN.md`, `kind: lines`): the pages where the first pass
   reported "numbering differs" or moved words between verses (odes, kommoi): list them from
   the batches' differences and notes, about 5–6 pages per agent. Then `import-sophocles` again;
   aim, as for Electra: nearly every apparatus lemma stands in the line that carries its number.
5. `merge-sophocles-appendix <play>`; `sigla.md` (Jebb's note on his symbols, from the first
   apparatus page, as texts/electra/sigla.md); `glossary.md` (names the dictionaries lack) and
   `shortdefs.tsv`; lemma slips listed by `check` and `build/<play>-review.tsv` corrected in the
   importer; `about.md` gets its `product_id`.
6. `build --only <play>`, `check`, `catalog`; asset pack `app/packs/<play>` registered in
   `app/settings.gradle.kts` and `app/androidApp/build.gradle.kts`; a row in `play/README.md`;
   the "Done so far" line of texts/README.md. Emulator check (free RAM first; no Gradle build
   beside two emulators; stop Gradle and close the emulator afterwards). Commit; update Progress.

## Which model reads

Blind test 2026-11-15: Sonnet re-transcribed Electra pp. 150–153 (text pages) and 301–302
(appendix) without seeing Opus's batches; results under Progress. Until it says otherwise:
Greek text check and apparatus on Opus.

## What each play still needs

| play | text pages | appendix | front matter to transcribe | other |
|---|---|---|---|---|
| trachiniae | 80–257 | 259–284 | MSS chapter 55–58; Jebb's note in place of the argument, persons, structure 77–79 (rendered) | — |
| oedipustyrannus | 110–300 (110–133 done: batch-01, 01b, 02) | 301–334 | whole introduction PDF 15–66 (Perseus lacks it; MSS ~57–61), arguments 104–107 | Perseus has the 1887 text, the scan is the 1893 third edition: the text follows the scan |
| oedipuscoloneus | 100–363 | 365–388 | MSS ~53–57, persons ~97 | GLAUx syntax (automatic) |
| philoctetes | 76–297 | 299–324 | whole introduction 11–49 (MSS ~47–49), 73–75 | GLAUx syntax; the whole commentary from the column crops (`prepare_commentary`, build/sophocles-pages/philoctetes-commentary): Perseus lacks it. OCR (egt_ocr.py route) helps most for these English parts |

The metrical analyses are not transcribed (as for Ajax and Electra).

## Progress

* **2026-11-15, Trachiniae.** First pass: batches 01–08 (pages 80–143) started on Opus;
  09–22 (144–257, the last one 248–257) to follow, then appendix 259–284 and front matter
  55–58, 77–79. Pages 77–79 rendered.

## Decisions

* 2026-11-15: order by least work left (Trachiniae first); 8 pages per agent; the old route
  (agents read the page images) kept rather than building an OCR route for Jebb's text pages:
  the OCR test of 2026-10-23 flagged over half the lines, so it would save little there.
