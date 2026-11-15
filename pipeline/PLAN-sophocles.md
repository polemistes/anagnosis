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
run 2026-11-15: Sonnet re-transcribed Electra pp. 150–153 without seeing Opus's batches. On
four pages it missed one difference of the text (353 γόων;), reported one that is not there
(373 τὼν), and misread three places in the apparatus (βʼ for βʹ, the impossible τὀυ for τὸν,
τοὔμε for τοῦμε). **Sonnet does not read Greek pages**; page agents stay on Opus. Sonnet is for code written to a contract,
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

* **2026-11-15, set-up item 3 done for both plays; Trachiniae item 4 running.** The first
  draft showed Jebb's page read wrongly; fixed in drama_pages.py / drama.py (commit "Drama
  pipeline for Jebb's Sophocles", tests in tests/test_drama.py): `app_rule="under"` (the
  apparatus is the small type above the commentary's one rule, found by the line pitch of the
  commentary), `_rule_sloping` (a rule askew or thin), `GREY_GROUND` + `whiten` (the Boston
  College scans photograph grey paper; the module's ink tests want white: **add
  `sophocles02soph_0`, the Oedipus at Colonus, to GREY_GROUND if its pages are grey**),
  `head_frac=0.095`, `speaker_trust=True`, `app_langs=("eng+grc", "grc+eng")`. Drafts:
  Trachiniae 89 pages, 1,242 verses, 150 flagged (12 %), 15 batches; Oedipus Tyrannus 96 pages,
  1,482 verses, 287 flagged (19 %), 16 batches (its last page, leaf 300, has no verses in the
  draft and leaves 163, 217 no apparatus crop: look before sending agents). INSTRUCTIONS-text.md
  has a section "Jebb's Sophocles". The workflow script is
  `transcriptions/drama/drama-text.workflow.js` (args in its header). **Trachiniae text
  batches 01–15 were started** (Opus, eight at once). When they are back: checker on every
  file, commit, `drama-residuals trachiniae` and its pass (RESIDUALS.md), then item 5.
* **The comparison the author asked for (2026-11-15)**: "how much better/worse the two ways of
  reading are". Material: the by-eye batches `transcriptions/sophocles/trachiniae/batch-01…08`
  (pages 80–143; 1.34 M agent tokens for 64 pages, 10 agents incl. two test agents) against
  the OCR route's batches 01–06 for the same pages (text after flags, and again after the
  residual pass). Compare (a) the text: every difference from the check text each route
  reports; (b) the apparatus, note by note. Every disagreement is settled on the page image by
  an Opus agent that is not told which route said what; report per route: real differences
  missed, errors introduced, tokens per page. The Oedipus Tyrannus has 24 by-eye pages
  (110–133, transcriptions/sophocles/oedipustyrannus) for the same. The agents of the OCR route
  are told not to open transcriptions/sophocles/.

* **2026-11-15, afternoon (the author: use what is left of the limit before it resets;
  "ultracode").** Trachiniae: first pass back and committed (854a0cb: 15 agents, 2.47 M
  tokens, 178 leaves); `drama-residuals trachiniae` gave 387 residuals on 81 pages; the
  residual pass runs (15 agents, one batch each; script
  `transcriptions/drama/drama-pass.workflow.js`, kind `residuals`). After it: checker, commit,
  then a review agent per batch (same script, kind `review`; the author's "ultracode" covers
  the Clouds-level checking), then `merge-drama trachiniae`. Oedipus Tyrannus: text batches
  restarted with 16 at once (workflow run wf_e4ae76bf-010). Oedipus at Colonus and
  Philoctetes: `Play` entries added (OC: twelve hidden leaves, leaf ≠ PDF page, text leaves
  106–371; its scan is in GREY_GROUND; Philoctetes text leaves 76–297, to verify against
  build/sophocles-pages/philoctetes/p-0076.png once fetched); `drama-pages <play> fetch`,
  `ocr`, `draft` started with nohup, logs build/logs/<play>-pages.log (run again if cut off;
  check the draft's summary and two pages before sending agents). An Opus agent extends the
  prose route (kind `appendix`, command `sophocles-prose`; its notes in
  build/logs/sophocles-prose-agent.md); another builds the comparison lists in
  pipeline/research/route-comparison/ (compare.py, tally.py; blind adjudication to follow).

* **2026-11-15, later.** Trachiniae: residual pass back and committed (37b78c0; 15 agents,
  1.28 M tokens, 8 minutes); the review pass runs (kind `review`, with the extra task of
  reading every verse against the page for stops, accents, breathings and brackets: a residual
  agent had found seven such places that neither flags nor residuals caught; use the same
  `extra` text for the other plays, it is in the workflow call of this session and repeated
  here: "read every verse of the batch against the whole page image … for its punctuation,
  accents, breathings, iota subscripts, brackets and daggers; change only what the print
  clearly shows, with a `rev:` note"). Trachiniae prose: drafts made (introduction 7 pages,
  158 flags; appendix 23 pages, leaves 259–281, 556 flags); check + review agents run
  (`transcriptions/drama/drama-prose.workflow.js`); then `sophocles-prose trachiniae`.
  Oedipus Tyrannus: first pass back and committed (6743722; 16 agents, 2.0 M tokens); 599
  residuals; the residual pass runs; its prose OCR (`drama-prose oedipustyrannus intro|appendix
  fetch|ocr|draft`, log build/logs/oedipustyrannus-prose.log; pages before the text are leaves
  103–109) runs. Philoctetes and Oedipus at Colonus: leaf numbering verified against the old
  page images; OCR and drafts under way.
* **Route comparison**: pipeline/research/route-comparison/ (compare.py, tally.py; states
  after-flags = 854a0cb, after-residual = 37b78c0; adjudication/items.jsonl = the 67 places
  of both states, map.json ties them to the states' items). Blind adjudication by workflow
  (two readers per item, a third where they differ); its result must be written to
  adjudication/verdicts.json and tallied per state; an after-review state is to follow.
* Open with the author: the label "*Critical notes.*" over an argument's notes in
  texts/electra/introduction.md and sophocles/INTRODUCTION.md (the new pages say "*Critical
  apparatus.*"); changing the Electra means rebuilding a text on sale.

* **STOPPED 2026-11-15 about 13:55 at the author's word ("stop the work now, but do not lose
  work that has been done").** All workflows were stopped; no agent and no local job is
  running; everything on disk is committed (afc7300). Agents edit their batch file in place
  and save after each page, so a batch that was in work is partly done: a new agent on the same
  file goes on from what is there (the first-pass brief and the review brief both say so).
  **Do not start anything until the author says so.** State, and what to run then (scripts in
  `transcriptions/drama/`: `drama-text.workflow.js`, `drama-pass.workflow.js`,
  `drama-prose.workflow.js`; their args are in each header and in this log):
  * **Trachiniae.** Text: first pass ✓, residual pass ✓ (37b78c0). Review (kind `review` with
    the `extra` text above): batches 03, 04, 08, 09, 14, 15 finished; **01, 02, 05, 06, 07,
    10, 11, 12, 13 to run again** (they may hold some `rev:` notes already). Prose
    (`drama-prose.workflow.js`, review: true): intro-01 checked (its review not done);
    appendix-01, -02 have every flag answered but their agents had not reported; appendix-03
    has 10 flags open: run the workflow again on intro-01, appendix-01…03 (a checking agent
    finds little left, the reviewer then reads the pages). Then `sophocles-prose trachiniae`,
    `merge-drama trachiniae`, review list, sigla, glossary, shortdefs, about.md (product id,
    no sale mark), build, pack, emulator.
  * **Oedipus Tyrannus.** Text: first pass ✓, residual pass ✓ (d36e3c7). Review: started on
    all 16 batches, none finished: run all 16 again. Prose: introduction intro-01…08 (59
    pages, 1065 flags): intro-08 checked, the others in work (open flags: 01 55, 02 18, 03 92,
    04 195, 05 17, 06 64, 07 243); Appendix drafted (appendix-01…05, 34 pages, 804 flags),
    no agent yet. Run the prose workflow on all thirteen files.
  * **Philoctetes.** Draft ✓ (111 pages, 1,469 verses, 216 flagged, 19 batches). First pass
    started on all 19, none finished (batches 05 and 15–19 have no apparatus yet): run
    `drama-text.workflow.js` on all 19 again; then residuals, review. Its prose: the whole
    introduction (leaves 11–49, 73–75), the Appendix (299–324) and the **whole commentary**
    (kind `notes`: two columns under the rule on both pages of every spread; needs
    `notes_leaves`, `notes_editor="jebb"` and a look at `_region` for this layout) are not
    set up yet.
  * **Oedipus at Colonus.** Draft ✓ (132 pages, 1,802 verses, 401 flagged = 22 %, 22
    batches); not yet looked at (flag kinds, apparatus found on every page, two pages against
    the images), no agent yet. Prose leaves: see the comment at its `Play` entry (leaf ≠ PDF
    page).
  * **Route comparison.** The adjudication was stopped after part 4 of 4 (both readers,
    15 and 16 verdicts, agreeing on all 15 they share: adjudication/verdicts-partial.json).
    Parts 1–3 (51 items) to adjudicate: the workflow script is in this session's folder only;
    its prompt is easy to rebuild from adjudication/items.jsonl (two blind readers per part,
    a third where they differ; readers must not open map.json, key.jsonl, after-*/,
    transcriptions/, texts/). Then write verdicts per state through map.json and run tally.py;
    an after-review state is to be compared when the Trachiniae's review is complete.
  * **Module gap to fix** (reported by the residual agents): `drama_residuals` misses
    punctuation that follows an elided word (δʼ, τοῦτʼ); until it is fixed the review's extra
    task (reading every verse for stops) covers it.
  * Token use this day, for the record: Trachiniae by-eye round 1.34 M (64 pages); OCR route
    first pass 2.47 M (Trachiniae, 178 leaves) and 2.02 M (Oedipus Tyrannus, 190 leaves);
    residual passes 1.28 M and 1.44 M; prose-route agent 0.34 M; comparison lists 0.17 M.

* **RESTARTED 2026-11-15 at the author's word: "take it play by play again, and go back to
  doing it the most economical way that produces the best quality, and after that you can
  think about efficiency."** So: the Trachiniae alone until it is finished (then Oedipus
  Tyrannus, Philoctetes or Oedipus at Colonus only when their turn comes; their half-done
  batches wait); at most ten agents at once; no pass run twice; the passes kept are those that
  were seen to catch errors: flags, residuals, and one review per batch with the verse-reading
  task (text) or one second reading (prose). Running: the review of Trachiniae batches 01, 02,
  05, 06, 07, 10, 11, 12, 13 (six at once) and the prose (appendix-03 check, then a review of
  intro-01, appendix-01…03). Then: the comparison's parts 1–3 with ONE blind reader each (the
  two readers of part 4 agreed on everything; a second reader only for a "neither" or an
  unclear scan), `sophocles-prose trachiniae`, `merge-drama trachiniae` and the steps after it.

* **2026-11-15, evening. Trachiniae: everything but the emulator check done and committed
  (b38fb8f).** Review of all 15 text batches (five corrections in the whole play); prose
  checked and read a second time (`sophocles-prose trachiniae`: introduction = Perseus's 22
  sections + 12 transcribed headings, appendix 29 notes); `merge-drama trachiniae` (1,242
  verses, 692 apparatus notes; the 25 remarks in build/trachiniae-merge.log are apparatus
  notes on lyric verses Jebb's longer verse covers, filed under the earlier line with the
  printed number in front); six analyses fixed from the review list (`HAND_ANALYSES`), twelve
  lemma slips (`LEMMA_FIXES`); glossary (21 names), shortdefs (25), sigla; `sophocles-prose`
  now also re-files Jebb's commentary notes on verses our numbering lacks (19 here);
  product id, pack, catalogue, play/README row, texts/README. `check`: 0 errors, nothing for
  the Trachiniae but the 17 translation segments at absent numbers (as Ajax and Electra).
  An Opus agent does the emulator check (PLAN-drama step 10; it must close the emulator and
  stop Gradle). **The order of the last steps, for the next plays**: review → prose check +
  second reading → `sophocles-prose` → `merge-drama` → review list → lemma fixes, glossary,
  shortdefs, sigla, about → `sophocles-prose` again (re-files the commentary) → `build --only`,
  `catalog`, pack → emulator.
* **The comparison is finished**: research/route-comparison/RESULTS.md. In short: by eye 15
  errors in 2,600 words of text and 22 in 258 apparatus notes; OCR route after flags and
  residuals 2 and 4, after the review and a targeted settling of six doubtful breathings no
  known error. The apparatus's breathings in the small type are the commonest error of every
  reader: the review's `extra` text for the next plays now tells the reviewer to enlarge and
  compare each breathing that matters with certain ones on the same page (see the Oedipus
  Tyrannus review call).
* **Oedipus Tyrannus resumed** (the Trachiniae waits only for its emulator check): review of
  the 16 text batches (six at once) and the prose (intro-01…08, appendix-01…05; three at once,
  check then second reading). Then the same last steps. Its introduction comes wholly from
  the prose batches (Perseus has none).
* The checker's glossary bug was fixed (it counted an earlier text's glossary for later
  texts); it now shows names without a dictionary entry in the Choephoroi, Clouds, Electra and
  one word in the Eumenides: small glossary additions, not done.

* **2026-11-15, Trachiniae emulator check and what it led to** (508573f). The check (Opus
  agent; commands in its report: from app/ with JAVA_HOME=/opt/android-studio/jbr,
  `./gradlew :androidApp:bundleDebug`, `./gradlew --stop`, bundletool 1.18.1 `build-apks
  --local-testing`, `install-apks`, `emulator -avd anagnosis -no-snapshot-save -no-boot-anim
  -no-audio`; the unmarked text is not in the shop, so the sale mark is added to a scratch
  copy of the bundle's catalogue only) found the app working and three things in the data:
  * **`merge-drama` exits with the number of its log remarks**: never chain it with `&&`
    (my chain stopped and the build stayed stale). Run merge, `sophocles-prose`,
    `build --only`, `catalog`, `check` as separate commands.
  * **Lyric numbering.** After a long verse that covers two traditional numbers, the numbering
    pass's "run on from the margin number" leaves our numbers one behind Jebb's until the
    next margin number, and his notes then sit under the wrong verse. New command
    **`sophocles-numbering <play>`** lists the suspects (apparatus notes whose lemma stands in
    a neighbouring verse; notes with the printed number in front). For the Trachiniae an agent
    renumbered five stretches by Jebb's note numbers and the pages (parodos, 205–215, 633–644,
    839–864, 1015–1040); three lemma suspects are left on purpose (658, 977, 981: explained in
    build/logs/trachiniae-numbering-agent.md); undecided and left: the epode 131–140 (margin
    135 on χαίρειν against note 132 and the introduction's "epode 132–140") and 1029/1030.
    **For the next plays: run `sophocles-numbering` after the first merge and give its list to
    one agent with the pages, before the last build.**
  * **Lost spaces in Jebb's commentary from Perseus** ("*Ai.*664ἡ βροτῶν"): the importer
    joined pieces at tag boundaries without a space; fixed in commentary.py (`_join`,
    `_needs_space`, tests). `sophocles-prose` now makes commentary-jebb.md again from the
    Perseus source with the fixed importer, then re-files the notes. The published plays were
    NOT regenerated; the fix would add 321 spaces in the Antigone (259 notes), 1,341 in the
    Ajax (915 notes, 28 in the introduction), 1,121 in the Electra (772 notes, 14 in the
    introduction): **the author decides whether to rebuild them.** For the Oedipus Tyrannus
    the regeneration would also turn 7 places like Ἐρινύ–ων back to Ἐρινύ¯ων (the vowel-length
    correction of commit a369d68 was made in the files, not in the importer): look at this
    when that play reaches `sophocles-prose`.
  * Being done by the same agent: the 25 translation segments that start at numbers we lack
    are to stand with the earlier verse that covers them (in `sophocles-prose`, eng-jebb.txt
    made again from Perseus first). After that the Trachiniae is finished; a second emulator
    run is not planned (the app's behaviour was seen; what changed since is data, checked in
    the files).

* **2026-11-15: THE TRACHINIAE IS FINISHED** (built, in the catalogue as
  `sophocles_trachiniae_jebb`, no sale mark; putting it on sale is the author's word and
  needs the product in the Console and a reader release). Last step: the translation's
  segments re-filed in `sophocles-prose` (eng-jebb.txt made again from Perseus each run; a
  lettered part goes to the matching part of our verse, a number a longer verse covers to the
  nearest earlier verse; the word map only where a segment begins a speech and its default
  verse does not; 30 segments moved). The word map could NOT be the main rule: the
  translation's numbers follow neither reference-grc.txt nor the Perseus Greek's own count
  (it misplaced the English at 103, 115, 190–195, 505–517, 863, 955, 971, 974). Two
  segments stay one verse late (132 at the epode's disputed number; "Oh! Oh!" at 1015 for
  ἒ ἔ, our 1014a); `check`: one segment at an absent number (881b, shown at 882, right).
* **Oedipus Tyrannus**: review back (16 agents, 2.6 M tokens, 28 corrections) and committed;
  `merge-drama oedipustyrannus`: 1,485 verses, 319 apparatus notes, 9 log remarks (covered
  verses), 2 words without lemma, review list 126 words; `sophocles-numbering`: 3 lemma
  suspects, 9 notes with the number in front. Prose check + second reading running. Then, in
  this order: `sophocles-prose oedipustyrannus` (look at the 7 vowel-length places first),
  one agent for the numbering suspects with the pages, the finishing agent (review list,
  lemma fixes, glossary, shortdefs, sigla from the first apparatus page, about.md product id
  `sophocles_oedipustyrannus_jebb`, pack, catalogue, README rows), separate commands for
  merge / sophocles-prose / build / catalog / check, then the emulator check (points 3–11 of
  the Trachiniae's list; point 1 is known: an unmarked text is not in the shop).

* **2026-11-15, later evening.** Oedipus Tyrannus prose back (25 agents, 3.9 M tokens: check
  and second reading of intro-01…08 and appendix-01…05) and committed; an Opus agent does the
  finishing (log: build/logs/oedipustyrannus-finish-agent.md): vowel-length marks in the
  commentary, `sophocles-prose`, lyric numbering in every lyric passage, review list, lemma
  fixes, glossary, shortdefs, sigla, about, build, pack, README rows. Then the emulator check.
* **What the prose second reading finds** (the author's rule: a pass stays only if it catches
  real errors): Trachiniae 30 pages: 6 corrections, 5 of them breathings in the Appendix;
  Oedipus Tyrannus 93 pages: 4 (two accents, a bolding, an escaped asterisk). Nearly all in
  the Greek of the Appendix. Proposed to the author for the next plays (no answer yet; until
  then keep the full second reading): second reading for the Appendix and the argument pages
  only; English introduction pages get the first check alone.
* **Oedipus at Colonus prepared, NOT started.** Its 1889 printing has the rule above the
  commentary as a hairline: `_rule_hairline` in drama_pages.py (agrees with the other
  detectors on all 264 leaves, finds the rule where they missed it; leaf 225 has none). Draft
  made again: 132 pages, 1,801 verses, 396 flagged (22 %), 22 batches, committed (8525ba7).
  A start beside the Oedipus Tyrannus's finishing agent was first refused as against "play by
  play"; the author then allowed it ("Do it."): **the next play's first pass may overlap the
  previous play's finishing steps, within ten agents; no more than that.** First pass started
  2026-11-15 (22 batches, nine at once). The Philoctetes (first pass half done) comes after it.

* **2026-11-15, the author: "We will not go further with Philoctetes for now."** The
  Philoctetes is PARKED: do not continue it (first pass, prose, commentary) until the author
  says so. What is on disk stays: the `Play` entry, scan, OCR, draft (111 pages, 1,469
  verses, 216 flagged), 19 batch files of which 13 hold partial first-pass work. The work
  ends with the Oedipus at Colonus.

* **2026-11-15: THE OEDIPUS TYRANNUS IS FINISHED** (c4f67ea; built, catalogue, pack,
  `sophocles_oedipustyrannus_jebb`, no sale mark). Finishing: introduction (§§ 1–30,
  manuscripts chapter, arguments, persons, structure) and Appendix (18 notes) joined; lyric
  numbering (kommos 649–699, second and fourth stasimon); 22 hand analyses, 11 lemma fixes;
  glossary 15, shortdefs 29, sigla. Perseus's commentary and translation for this play are
  the SECOND edition (1887): `PERSEUS_EDITION` in sophocles.py, said in about.md. The
  emulator check (Opus agent) then found, and the same agent fixed, in shared code so that
  the next play gets them too: sections named by the division holding most of their verses
  (`label_parts`; applied by merge-drama to plays with a check text); the opening words
  printed in capitals written as the check text has them (INSTRUCTIONS-text.md); a line the
  print sets as one shared verse is one lettered verse (683/683a/683b), whatever number a
  note gives a part of it; Perseus's `<gap/>` = Jebb's "…" kept in the commentary; no
  italics marks in headings; a misprint in a prose document corrected with a bracketed
  paragraph "[Correction in this edition: the print has …]". Undecided and left: Jebb's own
  notes disagree on 1195–1197; 502 has no printed number. Not caused by our data (app):
  taps in a contents list sometimes land one section early; the glossary entry of a name is
  never shown when the name has a short definition; "in apposition of ','" on the syntax
  sheet. Counts for the PUBLISHED plays, not regenerated: section labels would change in the
  Ajax at 718 (Third episode) and 961 (Fourth episode), not in Electra or Antigone; the
  ellipsis fix changes nothing in them.
* **Oedipus at Colonus**: first pass back (22 agents, 4.0 M tokens) and committed (8920ee9);
  818 residuals; the residual pass runs (nine at once). Prose leaves set (intro 55–66 and
  99–105, appendix 373–397: to be verified on the drafts; leaf ≠ PDF page), `drama-prose
  oedipuscoloneus intro|appendix fetch|ocr|draft` started (log build/logs/
  oedipuscoloneus-prose.log). Its batch-01 still has the opening word with the OCR's capital
  (Τέκνον): to be written as the check text has it. Next: checker, commit, review (with the
  `extra` text of the Oedipus Tyrannus review), merge, `sophocles-numbering`, prose check +
  second reading (Appendix and argument pages; the introduction pages the first check only,
  unless the author says otherwise), finishing agent, emulator check (which should also
  spot-check the fixed points in the Trachiniae and the Oedipus Tyrannus).

* **2026-11-15, the author: "I have changed my mind. Continue with Philoctetes when it is its
  turn."** The Philoctetes is no longer parked: it follows the Oedipus at Colonus (its first
  pass may overlap the Oedipus at Colonus's finishing steps, as allowed above). To do then:
  first pass on all 19 batches again (13 hold partial work; the agents go on from what is in
  the files), residuals, review with the five-point `extra` text of the Oedipus at Colonus
  review; prose: the whole introduction (leaves 11–49 and 73–75, to verify), the Appendix
  (299–324, to verify), and the WHOLE COMMENTARY, which Perseus lacks: kind `notes`, two
  columns under the rule on both pages of every spread (set `notes_leaves`, `notes_editor`;
  `drama_prose._region` must learn this layout: under the rule found by `page_layout`; test
  on several spreads before any agent; the notes begin with a bold verse number and lemma,
  run on from page to page and from the left page to the right); the merge must then write
  commentary-jebb.md from the notes batches for this play instead of keeping Perseus's
  (there is none), and its introduction comes wholly from the batches, as the Oedipus
  Tyrannus's. Oedipus at Colonus now: review of the 22 text batches and prose (check + second
  reading) running.

* **2026-11-16 (night).** Oedipus at Colonus: residual pass (22 agents, 2.0 M), review with
  the five-point `extra` text (22 agents, 4.1 M, 51 corrections) and prose (12 agents, 1.9 M;
  the second reading found five errors in 42 pages, four in the Appendix's Greek) all back
  and committed; `merge-drama oedipuscoloneus`: 1,795 verses, 917 apparatus notes, 33 log
  remarks (covered verses), 2 words without lemma, review list 95; `sophocles-numbering`:
  9 lemma suspects, 33 numbers in front. (The first merge crashed after the tokens: the
  entries of the two GLAUx plays lacked `translation="kept"`; added.) An Opus agent does the
  finishing (log build/logs/oedipuscoloneus-finish-agent.md); then the emulator check, which
  should also spot-check in the Trachiniae and the Oedipus Tyrannus what was fixed after
  their checks (section headings, O.T. verse 1 and 683, the commentary's ellipses and
  spacing, headings without asterisks, the Appendix correction note).
* **Philoctetes: first pass started** beside the Oedipus at Colonus's finishing (19 batches,
  nine at once; 13 held partial work from the mass run). Its commentary, introduction and
  Appendix by the prose route are NOT set up yet: see the entry above on what that needs;
  test the commentary's layout on several spreads and tell the author how large the job
  looks before any agent reads it.
* **Euripides (the author, 2026-11-15/16)**: all nineteen plays from Murray's Oxford text,
  with an English commentary beside it from the start, to be offered only from 1 January
  2028; the files stay on this computer and must never be pushed (set up a separate local
  folder with its own history before the first file is written; nothing of Murray's in a
  production bundle, no sale mark). Assessment and ranking: pipeline/research/
  euripides-plays.md. Nothing starts before the Sophocles plays are done. Open: which
  printing of Murray's vol. II and III to read (the author offered to look on Google Books
  and HathiTrust: list in the session's messages and in the research file's "Not done or not
  verified").

* **2026-11-16, the author: "Start with Medea next."** The first Euripides play is the
  Medea, after the Philoctetes (its token-free preparation and first pass may overlap the
  Philoctetes's finishing, by the overlap rule). What it is to be: Murray's text and apparatus
  (vol. I, 1902; scan euripidisfabulae01euriuoft, Perseus's own source, so the check text and
  the print are one edition); Earle 1904 as commentary and introduction (scan
  cu31924079583609, OCR of its leaves already on disk; his notes stand under his text in two
  columns and run on: the prose route's region for that layout is still to be written, see
  PLAN-drama.md "Medea, step 3"; his own text and critical appendix are NOT used);
  Coleridge's translation from Perseus; the hand-made Pedalion trees for the whole play
  (CC BY-SA 4.0: check their labels against the treebank's before choosing them over GLAUx).
  Before its first file is written: (1) the private local place for all Euripides files
  (texts, transcription batches, built database, pack), with its own history and ignored by
  the public repository; (2) a way for `catalog` and the release bundle to leave out a text
  that is not yet to be offered (a release date in about.md), so that nothing of Murray's
  reaches a production bundle before 2028-01-01; (3) a plan file of its own for Euripides
  (the drama pipeline's entry for the Medea changes from Earle's text to Murray's).

* **2026-11-16.** Oedipus at Colonus FINISHED but for the emulator check (b01a3d3): finishing
  agent's results in build/logs/oedipuscoloneus-finish-agent.md (48 hand analyses, 25 lemma
  fixes, glossary 20, shortdefs 33; `range_headings` restores the range of a commentary
  heading that Perseus cuts to its first number; `TRANSLATION_NUMBERS`, a per-play table,
  sets the translation's verse numbers right before the re-filing rules; Perseus's commentary
  and translation are the 1889 second edition, the scan's own). **Its emulator check has NOT
  run**: the agent stopped by the rules because (1) I had rerun `sophocles-prose` for the
  Trachiniae and the Oedipus Tyrannus, which rewrote their files a minute before (no change
  in content) so their databases were older than their files: both rebuilt since; (2) only
  2 GB of memory was available. **The session's scratchpad is on a RAM disk (/tmp is tmpfs)**:
  the agents' crops and two emulator bundles had filled 4.3 GB of memory; cleared (finished
  plays' folders deleted), and the workflow prompts now tell every agent to keep its scratch
  small and delete it at the end. Available memory is about 6 GB with the author's own
  programs open: the check needs 8. **To run the check**: `free -g` shows 8 GB or more
  available; then the agent's brief of this session (points A 1-10 for the Oedipus at
  Colonus, B spot-checks for the two sister plays); helper scripts in the scratchpad's
  emulator-oc/bin (patch_aab.py, ui.py; if the scratchpad is gone, PLAN-sophocles.md's
  "Trachiniae emulator check" entry gives the commands and what the scripts do).
* **Philoctetes**: first pass (19 agents, 2.9 M) and residual pass (19 agents, 1.6 M) back and
  committed; the review runs (nine at once; the apparatus crops of this play's draft are
  unreliable on some pages: the draft predates `_rule_hairline`; the reviewers read from their
  own crops). Prose: introduction drafted (intro-01…06, 42 pages, 523 flags), Appendix being
  drafted (leaves 299-324); the commentary (kind `notes`) still to be set up and tested.

* **2026-11-16, the author: deleting scratch files must not lose anything needed to resume;
  store elsewhere than /tmp.** Done: agents' working files go to
  `pipeline/build/agent-scratch/` from now on (on disk, ignored by git; pass it as `scratch`
  to the workflow scripts, whose headers say so); the emulator check's helper scripts are in
  `pipeline/tools/emulator-check/` (committed). What was deleted from the RAM-disk scratchpad
  earlier that day was reproducible or recorded: the agents' page crops (cut from the page
  images in pipeline/build/drama-scans, which stay), two debug bundles (rebuilt by Gradle),
  the Euripides research's sample page images (re-downloadable; the findings are in
  pipeline/research/euripides-plays.md), the crops behind the six settled breathings and the
  adjudication (their verdicts are in research/route-comparison/ and in the batch notes), and
  the Sonnet test's two transcriptions (its result is in this plan; the files themselves are
  gone). Everything needed to resume lives in the repository (batch files, saved after each
  page and committed after each pass), in pipeline/build (scans, OCR, drafts, residual lists,
  logs) and in this plan.

* **2026-11-16, emulator check of the Oedipus at Colonus done** (with spot-checks in the two
  sister plays; 11 GB free after the author closed programs). The app works on every point;
  everything corrected after the earlier checks shows right in the Trachiniae and the Oedipus
  Tyrannus. Three faults in the data, being fixed by the finishing agent: (1) section
  boundaries follow Perseus, not Jebb (O.C. "Third episode" at 1099, Jebb 1096): the merged
  text is to begin each of Jebb's divisions at its verse; (2) 65 "<*>" placeholders in the
  Trachiniae's commentary from Perseus (shown as "α<>νός", breaking italics), also in the
  published Electra (58), Ajax (12), Antigone (11); (3) two "1670— 1750" spacing slips. App
  behaviour noted, not changed: in the Greek-and-English view the English of a lettered part
  of a shared verse sits clipped at the foot of the page before its Greek; a margin number
  moves to the next verse when its own line is full (by design); contents taps land a section
  early; a name's glossary entry never shows when it has a short definition.
* **Philoctetes**: review back (19 agents, 3.1 M, 47 corrections) and committed;
  `merge-drama philoctetes`: 1,469 verses, 814 apparatus notes, 26 log remarks, review list
  82, `sophocles-numbering`: 10 lemma suspects, 26 numbers in front. Running: prose check +
  second reading of intro-01…06 and appendix-01…04 (eight at once; scratch on disk), and an
  Opus agent setting up and measuring the commentary (kind `notes`; log
  build/logs/philoctetes-commentary-setup.md): tell the author its size before any reading.

* **2026-11-16: THE OEDIPUS AT COLONUS IS FINISHED** (built, catalogue, pack,
  `sophocles_oedipuscoloneus_jebb`, no sale mark; emulator-checked). The fix round after its
  check (finishing agent, "Round 2" in its log; shared code, so the Philoctetes gets it too):
  `sophocles.align_part_starts` (merge-drama moves a top-level section that begins within six
  verses of one of Jebb's division starts to that verse: O.C. Third episode now at 1096; the
  Trachiniae and the Oedipus Tyrannus already matched Jebb's structure everywhere);
  Perseus's "<*>" is its keyers' mark for text they could not read (a letter or several
  words): the importer now writes "[?]" so that it cannot break the markdown, and for the
  Trachiniae all 163 places (159 in the commentary, 4 in the introduction) were read from the
  pages into `COMMENTARY_FIXES["trachiniae"]` / `INTRODUCTION_FIXES`; `range_dash` removes the
  space after the dash in a range of numbers. **For the published plays (not regenerated;
  the author decides)**: unread places Antigone 41, Ajax 19, Electra 79 (each would need the
  page, as for the Trachiniae); range dashes Antigone 10, Ajax 9, Electra 8; with the
  commentary spacing (321 / 1,341 / 1,121) and the Ajax's section labels noted before.
  The Philoctetes, when its commentary is read from the scan, has no Perseus placeholders.

* **2026-11-16, Philoctetes commentary.** Set-up agent's report (log
  build/logs/philoctetes-commentary-setup.md; commit c79b80a): kind `notes` for Jebb's page
  (`_region_under_rule`: all under the rule, two columns, read across the spread; a new rule
  detector `_rule_isolated` that measures against the page's own paper; `head_rule`); drafted
  222 pages in 28 batches (notes-01…28), 5,397 flags (median 23.5 a page), 767 note headings;
  about 97 % of the Greek words right in the draft; no page without a rule;
  `write_transcribed_commentary` in sophocles.py writes commentary-jebb.md from the checked
  notes where Perseus has none (tested on made-up batches only: watch its first real run).
  Estimated with a second reading: about 56 agents, 9–12 M tokens. **Running: the first
  check of all 28 batches** (nine at once, no second reading yet). Decision to take when it
  is back: run the second reading on four batches first and count what it finds, then decide
  for the rest (the author's rule on passes). Introduction and Appendix: checked and read a
  second time (20 agents, 2.9 M), committed (de02dab).
* **Medea, stage 1 (preparation, no page agents)**: an Opus agent builds the private place for
  the Euripides files (`private/` with its own repository, links from the usual paths, the
  public .gitignore, a pre-push hook, `check` errors), the `release:` date that keeps a text
  out of the public catalogue, pipeline/PLAN-euripides.md, and the Medea's draft from Murray's
  vol. I (log build/logs/euripides-setup.md). The Medea's page agents start when the
  Philoctetes commentary has been read.

## Decisions

* 2026-11-15: order by least work left (Trachiniae first).
* 2026-11-15: the drama pipeline's OCR route for all four plays (the author's word; see "The
  route"). My first choice that day, to go on with the old by-eye batches, was wrong: it
  ignored that the route had been replaced after the Gorgias and the Agamemnon showed what a
  reader's eye misses (PLAN-drama.md, Decisions, "Agamemnon step 4: a second pass").
