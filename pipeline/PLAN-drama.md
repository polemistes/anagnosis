# Nine plays: Aeschylus' Oresteia, Aristophanes' Clouds, Frogs and Lysistrata, Euripides' Medea, Bacchae and Alcestis

Decided with the author on 2026-11-01. This file is the brief: follow it step by step in the
order given, tick the steps off under **Progress**, write every choice the brief does not settle
under **Decisions**, and commit after each step (this file with it). All steps are done on
Opus 5.5; no step needs another model. The author is travelling and will not answer questions
while the work runs: **never stop to ask**. Where the brief leaves something open, take the
choice that keeps the data closest to the printed page, write it under Decisions, and go on.
The work may be cut off at any moment (connection, battery): every step below saves its result
to disk as it goes and can be run again from where it stopped.

The texts are sold inside the reader as before (app/PLAN-in-app-purchases.md): one asset pack and
one in-app product per play. What the author must do in Play Console is collected under
**For the author** at the end of each release step; it never blocks the next play.

## How to work from this brief

* **Order**: Agamemnon, Choephoroi, Eumenides, Clouds, Medea, Frogs, Bacchae, Alcestis,
  Lysistrata. (Alcestis took the Hippolytus's place on 2026-11-01, the author's decision: no
  scan of Hadley's Hippolytus exists, and the alternative needed two scans.) Finish a play's steps before the next play's, except that the long OCR jobs
  (fetch, ocr) of the next play may run in the background meanwhile.
* **Resuming after an interruption**: `git status`, `git log -5`, read Progress and Decisions
  here, run the checker on the batch files that were being written (they are appended page by
  page, so a file may end in the middle of a batch: continue from the first missing page, which
  `grep '^=== p-' file` shows), then continue with the first unticked step. The fetch, OCR and
  draft commands skip what is already on disk. Never re-run a play's `merge-drama` while agents
  are still writing its batches.
* **Commits**: after every step, and after every three or four batch files come back checked:
  `git add -A pipeline/transcriptions/drama texts pipeline/anagnosis_pipeline pipeline/PLAN-drama.md`
  and commit with a message that names the play and the step. Never leave more than an hour of
  agent work uncommitted. Do not push unless the author asks.
* **Agents** (general-purpose, Opus 5.5): at most 6 pages each for text batches, 8 for prose
  batches, at most 10 running at once. Every agent appends to its batch file after each page
  ("save after each page" stands in the briefs). Give each agent only its page range, the brief
  to read, the files to look at and the checker to run; nothing else. Run the checker yourself
  when an agent reports, and send a page back to a fresh agent when a remark is not explained.
* **Long commands** (fetch, ocr, draft, build-morpheus-forms, Gradle) run in the background with
  their output in `pipeline/build/logs/<play>-<step>.log`, one at a time per play. They are
  idempotent: run again after a crash.
* **Housekeeping**: stop Gradle daemons and close the emulator after every use (the author's RAM
  is shared with other work); never search outside the repository and the scratchpad; keep
  downloads under `pipeline/sources/scans/<scan>/` and `pipeline/sources/`, nothing in the
  repository root. In every text written for the app say "critical apparatus", not "critical
  notes". Keep requests to the model light: line crops, not whole pages, wherever a crop does.
* **Tools already in the repository**: the Gorgias route (`gorgias_pages.py`: Tesseract +
  matching to the Perseus text, flags, crops, check sheets; `gorgias_merge.py`: GLAUx alignment,
  analyser fallback, review list), the Sophocles route (`sophocles.py`: AGDT alignment,
  `apply_text_check`, verse numbering; `sophocles_pages.py`: Jebb-layout crops), the prose OCR
  routes (`egt_ocr.py`: eng+grc hOCR, columns, word flags, proof pages; `lodge_intro.py`: Greek
  words re-read with the Greek model, § headings), the translation aligners (`gorgias.py`:
  speeches matched to the Greek by speaker and length, `symposium.py: jowett_segments`), and the
  briefs in `pipeline/transcriptions/{gorgias,sophocles,gorgias-lodge-intro}/`. Read them before
  step 1; reuse their functions rather than writing new ones.

## Decisions already taken (do not reopen)

### The nine texts

| slug | play | Greek text and critical apparatus (one edition) | scan (Internet Archive) | commentary | translation | syntax | product_id |
|---|---|---|---|---|---|---|---|
| agamemnon | Ἀγαμέμνων, Agamemnon | A. Sidgwick, Aeschylus: Agamemnon, Oxford, Clarendon Press (the printing of the scan; the title page gives the edition) | agamemnonwithint00aescuoft (1887 printing, 204 leaves, jp2); spare: aeschylusagamemn00aescrich (1881) | Sidgwick's notes and introduction, same volume | H. W. Smyth (Loeb 1926), Perseus tlg0085.tlg005.perseus-eng3 | AGDT tlg0085.tlg005.perseus-grc1.tb.xml (hand-made) | aeschylus_agamemnon_sidgwick |
| choephoroi | Χοηφόροι, Choephoroi | A. Sidgwick, Aeschylus: Choephoroi, Oxford 1884 | choephoroiwithin00aescuoft (180 leaves, jp2); spare: choephoroiwitned00aescuoft (1900 printing) | Sidgwick, same volume | Smyth, perseus-eng2 (tlg006) | AGDT tlg0085.tlg006.perseus-grc2.tb.xml | aeschylus_choephoroi_sidgwick |
| eumenides | Εὐμενίδες, Eumenides | A. Sidgwick, Aeschylus: Eumenides, Oxford 1887 | eumenideswithint01aescuoft (102 leaves, jp2) — a student has written notes on the text pages; see below | Sidgwick, same volume | Smyth, perseus-eng2 (tlg007) | AGDT tlg0085.tlg007.perseus-grc1.tb.xml | aeschylus_eumenides_sidgwick |
| clouds | Νεφέλαι, Clouds | W. J. M. Starkie, The Clouds of Aristophanes, London, Macmillan 1911 | cloudsofaristoph00aris_0 (474 leaves, jp2) | Starkie, same volume | Starkie's prose translation, same volume (facing pages) | GLAUx 0019-003.xml (automatic) | aristophanes_clouds_starkie |
| medea | Μήδεια, Medea | M. L. Earle, The Medea of Euripides, New York, American Book Co. 1904 — if his volume prints a critical apparatus (see the Medea rule below); otherwise Prinz-Wecklein, Euripidis Fabulae I (Teubner), Medea | cu31924079583609 (316 leaves, jp2); Teubner: euripidisfabula01euriuoft | Earle, same volume | E. P. Coleridge (1891), Perseus tlg0006.tlg003.perseus-eng2 | GLAUx 0006-003.xml | euripides_medea_earle (euripides_medea_wecklein if the Teubner text is used) |
| frogs | Βάτραχοι, Frogs | T. G. Tucker, The Frogs of Aristophanes, London, Macmillan 1906 | frogsofaristopha00arisrich (354 leaves, jp2) | Tucker, same volume | The Athenian Society (1912, anonymous), Gutenberg #8689 | GLAUx 0019-009.xml | aristophanes_frogs_tucker |
| bacchae | Βάκχαι, Bacchae | J. E. Sandys, The Bacchae of Euripides, Cambridge, 3rd ed. 1892 | BacchaeOfEuripides_680 (jp2 `BacchaeEurip_jp2.zip`); spare: bacchaeeuripide01eurigoog (2nd ed. 1885) | Sandys, same volume | Coleridge, "The Bacchantes", Wikisource (The Plays of Euripides (Coleridge)/The Bacchantes); fallback T. A. Buckley (1850), Perseus tlg0006.tlg017.perseus-eng2 | GLAUx 0006-017.xml | euripides_bacchae_sandys |
| alcestis | Ἄλκηστις, Alcestis | H. W. Hayley, The Alcestis of Euripides, edited with an introduction and critical and exegetical notes, Boston, Ginn 1898 | alcestisofeuripi00euriuoft (284 leaves, jp2, clean); spare: earlealcestis00euri (M. L. Earle, Macmillan 1894, jp2) | Hayley, same volume | Coleridge, Perseus tlg0006.tlg002.perseus-eng2 | GLAUx 0006-002.xml | euripides_alcestis_hayley |
| lysistrata | Λυσιστράτη, Lysistrata | F. W. Hall and W. M. Geldart, Aristophanis Comoediae II, Oxford 1907 (the Perseus text is this edition) | aristophaniscomo02arisuoft (jp2) | B. B. Rogers, The Lysistrata of Aristophanes, London 1911: notes and introduction | The Athenian Society (1912), Gutenberg #8688 | GLAUx 0019-007.xml | aristophanes_lysistrata_hall_geldart |

Every chosen scan has a jp2 zip. A scan without one (some spares have only a PDF) can be
fetched page by page from `https://archive.org/download/<id>/page/n<N>_w2000.jpg` (the Archive
renders the page; `n<N>` is the leaf number from 0; try a larger width first and keep the largest
the server gives). The same address at `_w700` is the quick way to look at any leaf of any scan
when finding page ranges.

### Rules for every play

* **Same edition for text and apparatus.** The Greek text that ships is the edition's text,
  transcribed from the scan, with its critical apparatus. The Perseus text (Smyth for Aeschylus,
  Hall-Geldart for Aristophanes, Murray for Euripides) is the **check text** that the OCR is
  matched against, as Perseus was for the Gorgias; it never ships. Murray's Euripides is
  protected in Norway until 2028 and must not appear in texts/ in any form; the Smyth and
  Hall-Geldart texts may differ from the edition and so do not ship either, except that for the
  Lysistrata the edition *is* Hall-Geldart's.
* **Not usable, ever**: Murray's Greek text and his verse translations; Jack Lindsay's
  Lysistrata (Perseus's English Lysistrata and Gutenberg #7700 are his); the Perseus English
  Aristophanes of 1938 (O'Neill); Headlam-Thomson, Fraenkel, Denniston-Page (Agamemnon); Dodds
  (Bacchae); Dale (Alcestis); Page (Medea); Coulon; Stanford (Frogs); Dover; Sommerstein;
  Henderson; C. E. S. Headlam's Medea (death year unknown). Every other source in the table
  above is checked: editors dead before 1956, texts published before 1931.
* **Text**: one file line per printed verse, exactly as the edition divides the lyrics; the
  Perseus check text is re-divided to the print (the first word of a printed verse gives its
  line number; a second printed verse that begins in the same Perseus line gets a letter, 401a;
  a printed verse that covers two or more Perseus lines carries the first number, and the
  numbers it covers are skipped, as Jebb's Sophocles). The margin numbers of the print are
  checked against this and flagged where they disagree; a disagreement is decided by the agent
  from the page, printed numbers winning. Speakers are the Perseus names in full (`@ Χορός`), put
  where the print changes speaker; the print's abbreviations (ΚΛ., ΧΟ.) are the check. A stage
  direction the edition prints in the text ((Μυγμός.), (ὠγμός.)) is a `!` line. Words, accents
  and punctuation come from the print; where the OCR agrees with Perseus the Perseus spelling is
  taken as confirmed, where it differs the agent decides from the crop. Elision is ʼ (U+02BC);
  the raised stop ·; editorial brackets as printed (`[ ]` deletions, `⟨ ⟩` additions; an
  obelus † stays). Sidgwick's asterisks before conjectural readings are left out of the text and
  explained in sigla.md. An edition that prints the iota adscript (τῶι, χώραι)
  ships with the subscript (τῷ, χώρᾳ): a word that differs from Perseus only so takes Perseus's
  spelling and is not flagged; sigla.md says so.
* **Sections** (`== episode`, `== choral`, `=== strophe 1`, the Aristophanic Prologue, Parodos,
  Agon, Parabasis) come from the Perseus TEI, re-attached by line number after the re-division;
  the edition's own headings (ΧΟΡΟΣ., Starkie's AGON II) are not sections.
* **Critical apparatus**: every item under its line number, copied as printed (sigla, Latin,
  English), in `commentary-<editor>-apparatus.md` with `## N` headings, as
  the Gorgias. Tesseract's two readings are a help, not a draft.
* **Commentary**: the editor's notes, OCR'd with the English and Greek models, split into notes
  by the line number that begins each note (`## 779`, `## 214-218`; "215 f." becomes `## 215`),
  the lemma in bold, checked by agents against crops of the flagged words only (the
  Expositor's-Greek-Testament route). Notes on lines our numbering skips go to the nearest
  earlier line.
* **Introduction**: the editor's, in full, by the same route, as `introduction.md` with the
  heading rules of `pipeline/transcriptions/sophocles/INTRODUCTION.md`; lists of editions and
  bibliographies are left out; chapters on the manuscripts, the metres, the play and the
  legend are kept.
* **Translation**: by Greek line where the source has line numbers (Smyth, Coleridge on
  Perseus: `tei_to_document`, as Jebb's); by speeches where it has none (the Athenian Society,
  Coleridge's Bacchantes): each speech keyed to the Greek line where it begins, matched to the
  Greek speeches by speaker and length (`gorgias.py: _speech_places`), long speeches cut at
  sentence ends in proportion to the Greek about every ten lines (`jowett_segments`). Starkie's
  translation faces his text page by page: its speeches are keyed from the facing page.
* **Sigla**: `sigla.md` from the editor's list of manuscripts and signs (introduction or the
  first apparatus page), written by hand from the page, short, as `texts/ajax/sigla.md`.
* **Lemmas and syntax**: AGDT or GLAUx aligned to the edition's words (`align`), the analyser
  for the words the treebank lacks or reads otherwise, the review list
  `pipeline/build/<slug>-review.tsv` as for the Gorgias; an agent goes through the review list
  once and fixes the entries whose lemma is empty or plainly wrong by `HAND_ANALYSES` /
  `LEMMA_FIXES` tables in drama.py (per play); nothing more. `glossary.md` for names the
  dictionaries lack, `shortdefs.tsv` for lemmas `check` reports without a gloss, `aliases.tsv`
  where a lemma stands under another headword — as for Ajax and the Gorgias.
* **about.md** as `texts/gorgias/about.md`, with `ref_edition`, `ref_translation`,
  `ref_commentary`, `editor`, `apparatus` ("Sidgwick's critical apparatus"), `translation`,
  `commentary`, `syntax` ("annotated by hand (Ancient Greek Dependency Treebank)" for Aeschylus,
  "machine-made (GLAUx), not checked by hand" for the rest), `syntax_source`, `syntax_license`
  (CC BY-SA 3.0 US for AGDT, CC BY-SA 4.0 for GLAUx), `google_play: yes`, `product_id` from the
  table. Licence lines in the files: the editions and translations are in the public domain; the
  transcriptions CC BY-SA 4.0; Perseus translations CC BY-SA 4.0 (modernized by Perseus) — copy
  the wording of texts/ajax and texts/gorgias.
* **texts/README.md** gets a section per author like "Sophocles' other plays", naming the
  edition, the scan, the sources and licences, and `play/README.md`'s product table a row per
  play.

### Play-specific decisions

* **Eumenides**: the only scan of Sidgwick's edition has a reader's handwriting between and
  beside the lines. Tesseract reads the print under it mostly; the Perseus matching flags the
  rest; the agents read the crops. Where a line crop is unreadable because of the writing, the
  agent looks at the whole page and, if still unreadable, keeps the Perseus words and says so
  under notes. Do not look for another edition.
* **Choephoroi**: the most corrupt text of the nine; Sidgwick's apparatus is long (some 400
  items). Expect many flags; they are real differences, not OCR noise.
* **Clouds**: Starkie prints the Greek on the left-hand page with the apparatus under it, his
  translation on the right-hand page with the apparatus continued and the commentary in two
  columns under a rule, as Jebb (`sophocles_pages.py` has the crops for this layout). His
  translation is the one that ships (`eng-starkie.txt`); Hickie's (Perseus, hopper
  aristoph.cl.hickie_eng.xml) is the fallback only if Starkie's pages prove unusable, and then
  the Decisions log says why.
* **Medea**: Earle's volume sets the text at the top of each page with his commentary under it
  in two columns (Jebb's layout without the translation). Before the draft, look at six text
  pages and at the end matter: if Earle prints a critical apparatus (under the text, or as
  critical notes in an appendix), text and apparatus are his; if he prints none, the text and
  apparatus are Prinz-Wecklein's Teubner Medea (scan euripidisfabula01euriuoft; find the Medea's
  leaves by its title page), Earle's notes go on top, the product id becomes
  euripides_medea_wecklein, and the Decisions log records the choice with the pages looked at.
* **Frogs**: Tucker prints the text with the apparatus at the foot and the notes at the back
  (running heads give the line range). The Athenian Society translation is the one that
  ships; Rogers's and Tucker's are not used.
* **Bacchae**: Sandys prints the apparatus under the text, Latin with English remarks. After
  line 1329 the manuscripts have a gap and the end is partly restored from the Christus
  Patiens: the text follows what Sandys prints in his text, line for line; restored lines he
  prints get the numbers he gives them, or letters after 1329 where he gives none; what he
  keeps in the notes stays in the notes. The translation and the GLAUx tokens are aligned by
  words and speeches as everywhere else; that stretch is simply checked by hand in the merge log.
  Sandys's 3rd edition (1892) is the text; his introduction is long (over a hundred pages) and is
  transcribed in full except the lists of editions.
* **Alcestis**: Hayley prints the text with the speakers' abbreviations in the margin, the
  numbers every fifth line at the right and the critical apparatus at the foot of each page
  (English, with the sigla of his introduction); the "critical and exegetical notes" at the back,
  each under a bold line number and lemma; an introduction of about ninety pages. One volume for
  everything, as Tucker's Frogs; the scan is clean. Earle's Alcestis (1894) is the spare only
  if pages of Hayley's scan prove unusable, and then the Decisions log says which.
* **Lysistrata**: the text and apparatus are Hall-Geldart's Oxford text (vol. II of the scan;
  the Perseus text is the same edition, so the check is light, as for the Gorgias). The notes
  are Rogers's, printed at the foot of his pages under the text and his verse translation
  (scan aristophaniscomo04aris, the Lysistrata and Thesmophoriazusae volume): crop the
  full-width small-type block at the foot of each page; his introduction too. His verse
  translation is not used (softened); the Athenian Society's prose is. Laconian forms the
  analyser cannot parse stay without lemma and are listed in the review file; the glossary gets
  the commonest (σιώ, ναί, τώ, ποττάν, ὑμές …) with their Attic equivalents.

### Releases

Three reader releases, each after a group of plays is built and checked: **0.6.0 (version
code 16)** with the Oresteia; **0.7.0 (17)** with Clouds, Medea and Frogs; **0.8.0 (18)** with
Bacchae, Alcestis and Lysistrata. If the author has not uploaded a release when the next
group is ready, the next release carries everything (version codes only go up). Each release
step bumps `versionCode`/`versionName` in app/androidApp/build.gradle.kts, writes the release
notes in play/listings/reader.md (a bullet per new text in the description, a "What's new"
paragraph under 500 characters), builds the bundle (`cd app && ./gradlew :androidApp:bundleRelease`,
then `./gradlew --stop`), and lists what the author must do.

## Step 0: set-up (once)

1. Read: texts/README.md; the briefs under pipeline/transcriptions/{gorgias,sophocles,gorgias-lodge-intro};
   gorgias_pages.py, gorgias_merge.py, gorgias.py, sophocles.py, sophocles_pages.py, egt_ocr.py,
   lodge_intro.py, odyssey.py (`align`, `syntax_nodes`), odyssey_merge.py (`Analyser`,
   `choose_analysis`), import_perseus.py (`tei_to_document`, `write_tokens`), textfmt.py.
2. Check the tools: `pipeline/.venv/bin/python -m pytest pipeline/tests` passes; `tesseract
   --list-langs --tessdata-dir pipeline/tessdata` lists eng, grc, lat (fetch the models from
   tessdata_best if not, see pipeline/tessdata/README.md); `opj_decompress`, `magick`, `pdftoppm`
   exist; Morpheus is built (`pipeline/sources/morpheus/bin/cruncher`).
3. Add to `fetch.py` and run `fetch`: the nine Perseus Greek files (canonical-greekLit
   perseus-grc2 of tlg0085.tlg005/006/007, tlg0019.tlg003/007/009, tlg0006.tlg002/003/017), the
   Perseus translations (tlg0085.tlg005.perseus-eng3, tlg006 and tlg007 perseus-eng2;
   tlg0006.tlg002 and tlg003 perseus-eng2; tlg0006.tlg017.perseus-eng2 as the Bacchae fallback),
   the three AGDT files (treebank_data v2.1 Greek texts, names in the table), the six GLAUx
   files (alekkeersmaekers/glaux main/xml), Gutenberg #8688 and #8689 as plain text
   (`https://www.gutenberg.org/cache/epub/<n>/pg<n>.txt`; if Gutenberg refuses, the mirror
   `https://gutenberg.pglaf.org/8/6/8/<n>/<n>.txt`), and Coleridge's Bacchantes: the Wikisource
   page transcludes pages 99-141 of the index "The Plays of Euripides Vol. 2- Edward P.
   Coleridge (1913).djvu", so fetch each `Page:` wikitext
   (`https://en.wikisource.org/w/index.php?title=Page:The_Plays_of_Euripides_Vol._2-_Edward_P._Coleridge_(1913).djvu/<n>&action=raw`,
   n = 99 … 141) into `pipeline/sources/coleridge/bacchantes-<n>.wiki`. Scans are fetched leaf
   by leaf by the page tools, not here.
4. Create `pipeline/transcriptions/drama/<slug>/` for the nine plays (empty), and
   `pipeline/build/logs/`.

## Step 1: the pipeline modules

Write, with tests in pipeline/tests (numbering rule, note splitting, speech alignment on
small made-up inputs), and register in `__main__.py`:

* **`drama.py`**: `PLAYS`, a table of `Play` records with everything from the tables above
  (slug, Greek and English titles and authors, tlg, Perseus files, treebank or GLAUx file,
  translation source and kind, scans with their leaf ranges — text pages, apparatus pages if
  separate, notes pages, introduction pages, translation pages — filled in at step 2 of each
  play, edition and licence strings, product id, per-play `HAND_ANALYSES`, `LEMMA_FIXES`,
  `SPEAKERS` map from the translation's names to the Greek ones). `merge_play(slug)` writes
  texts/<slug>/ from the batches: grc.txt, commentary-<editor>-apparatus.md, tokens.tsv and
  syntax-nodes.tsv (AGDT or GLAUx through `align`, then the analyser, review list in
  pipeline/build/<slug>-review.tsv), eng-<name>.txt, commentary-<editor>.md, introduction.md,
  and a merge log pipeline/build/<slug>-merge.log of every line it could not place. It must be
  safe to run again at any time.
* **`drama_pages.py`**: the Gorgias route for verse, parameterised by play: `fetch` (leaves as
  grey PNG; jp2 from the zip, or the page-image service for PDF-only scans), `ocr` (Tesseract
  grc, hOCR; the apparatus block read twice more, Greek-first and Latin-first, enlarged), `draft`
  (the text block of each page found by type size and position, the apparatus block under it,
  the margin numbers; the OCR lines matched word by word to the Perseus text; the numbering and
  speaker rules above; flags; the crops `p-NNNN-lines.png`, `p-NNNN-app-l.png`, `-app-r.png`; a
  check sheet `p-NNNN.md`; the batch files `batch-NN.md` of six pages each, pre-filled with
  the draft text and empty apparatus and notes sections; `pages.json` and `draft.json`).
  Outputs under pipeline/build/drama-pages/<slug>/. For Jebb-layout volumes (Starkie, Earle)
  the text block is the top of the left-hand page and the apparatus may continue on the facing
  page under the translation: both halves go into the same page's apparatus crops, in order.
  The flags and their wording are the Gorgias ones plus: "the margin reads N at a line numbered
  M", "this printed line matched no Perseus words", "a speaker change in the print that Perseus
  does not have here" (and the reverse), "a bracketed line: a stage direction?", "lettered: a
  second verse in Perseus line N".
* **`drama_prose.py`**: the prose route for notes, introductions and Starkie's translation:
  `fetch`, `ocr` (eng+grc hOCR; Greek words re-read with grc as lodge_intro does), `draft` per
  page: columns found (two-column pages split as egt_ocr; a full-width block under a rule as
  sophocles_pages `_crop_commentary`; Rogers's foot block by its small type), the running head
  dropped, paragraphs joined, a note begun at every paragraph that starts with a line number
  (bold digits, optionally a range or "f."/"ff."/"sqq."), its lemma (the bold Greek up to the
  colon, bracket or stop) wrapped in `**…**`; flagged words as egt_ocr's FLAG_KINDS, each with
  a numbered crop in `p-NNNN-flags.png`; the draft written into the batch file
  (`notes-NN.md`, `intro-NN.md`, `trans-NN.md`: eight pages each) as `=== p-NNNN` blocks with
  the markdown and a `--- flags` list the agent ticks off. For an introduction the draft keeps
  the printed headings as `# ` / `## § n`. For Starkie's translation the draft writes each speech
  as `@ Speaker` and `N<TAB>text`, N from the facing Greek page's draft.
* **Checkers**: `check-drama-batch <slug> files…` (as check-gorgias-batch: numbering runs on,
  apparatus numbers name lines on the page, elision, every wording change against Perseus
  listed, pages missing from a batch) and `check-drama-prose <slug> files…` (block order and
  completeness, headings well formed and increasing, run-on markers, every flag answered,
  Greek in precomposed Unicode with breathings on initial vowels).
* **`merge-drama <slug>`** calls `merge_play`; `drama-pages <slug> fetch|ocr|draft`;
  `drama-prose <slug> notes|intro|trans fetch|ocr|draft`.

Commit the modules with their tests before any play's step 2.

## Steps for each play (in the order of the table)

2. **Leaves.** Find in the scan the leaves of: the Greek text (first and last), the notes, the
   introduction, the sigla or manuscripts page, the translation pages (Starkie), using the page
   images at `_w700` (binary search by leaf number; the scan's `_djvu.txt` helps to find a
   chapter). Write them into `PLAYS` in drama.py and commit. Look at six text pages: note the
   layout (apparatus at the foot? speaker abbreviations in the margin? margin numbers every
   fifth line, left or right?) under Decisions, and apply the Medea rule. For a Jebb-layout
   volume record which pages are text and which translation.
3. **Text OCR and draft.** `drama-pages <slug> fetch`, `ocr`, `draft` in the background; read
   the summary (pages, lines, flagged). If more than 70 % of the lines are flagged on a scan
   with clean print, the matching or the layout detection is wrong: fix the module, do not
   send it to agents.
4. **Text and apparatus batches.** Agents on `batch-NN.md` with
   `pipeline/transcriptions/drama/INSTRUCTIONS-text.md`, six pages each. Checker on every
   returned file; unresolved remarks back to a fresh agent. Commit every few batches.
5. **Merge the text.** `merge-drama <slug>`; read the merge log and the review list; have one
   agent check the review list (lemma empty or wrong → HAND_ANALYSES / LEMMA_FIXES); run
   `check`; look at ten random lines of grc.txt against the page images yourself. Commit.
6. **Notes.** `drama-prose <slug> notes fetch|ocr|draft`; agents on `notes-NN.md` with
   `INSTRUCTIONS-prose.md`, eight pages each; checker; commit every few batches;
   `merge-drama <slug>` again and read the merge log (notes it could not place).
7. **Introduction** (and the translation pages for the Clouds): the same with `intro` (`trans`).
8. **Translation, sigla, glossary, short definitions, about.md, README.** `merge-drama` writes
   the translation; read its log (speeches it could not match: fix the SPEAKERS map, or the
   Greek speech list where the translation merges two speeches). Write sigla.md from the
   editor's page, glossary.md (names; Laconian for the Lysistrata), shortdefs.tsv for what
   `check` lists, about.md, the texts/README.md section and the play/README.md row. Commit.
9. **Build.** `build --only <slug>`; `check`; the pack: copy app/packs/gorgias/build.gradle.kts
   to app/packs/<slug>/ with the slug changed, add the slug to the list in app/settings.gradle.kts
   and to `assetPacks` in app/androidApp/build.gradle.kts; `catalog`. Commit. Do not start the
   emulator here.
10. **Group check** (after Eumenides, Frogs, Lysistrata only): `build-morpheus-forms` (long;
    background), full `build`, `check`; install the debug reader on the emulator, buy each new
    text in the debug shop, open it, read a lyric passage, open the apparatus, a note, the
    introduction, the syntax of one sentence, play one line aloud; fix what is wrong; close the
    emulator, `./gradlew --stop`. Then the release step.

## Release steps

**R1** after Eumenides (0.6.0, code 16), **R2** after Frogs (0.7.0, 17), **R3** after Lysistrata
(0.8.0, 18): version bump, listing and release notes, bundle, commit; then write under
**For the author** below what is left: upload the bundle to internal testing, create and
activate the one-time products with the ids above (name = the English title, €3), test one
purchase, promote. Then go on with the next play.

## For the author

(filled in by the release steps)

**R1, reader 0.6.0 (version code 16), built 2026-11-01:**
`app/androidApp/build/outputs/bundle/release/androidApp-release.aab` (rebuild with
`./gradlew :androidApp:bundleRelease` if it is gone). Release notes in
`play/listings/reader.md` ("Release notes, 0.6.0"), and the Oresteia line in the full description.
1. Upload the bundle to internal testing.
2. Create and activate three one-time products, €3 each: `aeschylus_agamemnon_sidgwick`
   (name "Agamemnon"), `aeschylus_choephoroi_sidgwick` ("Choephoroi"),
   `aeschylus_eumenides_sidgwick` ("Eumenides").
3. Test one purchase on your phone; then promote the release.
Tested on the emulator (debug shop): all three bought, downloaded and opened; apparatus,
manuscripts page, introduction, commentary (Agamemnon, Choephoroi), syntax and reading aloud work.

## Progress

**Paused by the author on 2026-11-02 (Clouds nearly done, Medea at step 3). Resume here.** Every
result so far is committed; nothing depends on the session that did it.

*Clouds, to finish (about half an hour):*
1. Review the four commentary batches whose review the usage limit stopped: one agent each,
   given `pipeline/transcriptions/drama/REVIEW.md` (the prose part), the batch file and its
   pages: notes-14 (p-0212 to p-0219), notes-25 (p-0302 to p-0309), notes-33 (p-0366 to
   p-0373), notes-35 (p-0382 to p-0389). Commit each. The checker's remaining remarks on the
   Clouds notes batches are explained ones: no breathing on a word ending in Starkie's brackets
   ([-ων R], ⟨ει⟩), a page beginning with a further lemma of the note before, and "note 1366
   comes after 1368" (Starkie's transposition, as in the text).
2. `merge-drama clouds`; read `pipeline/build/clouds-merge.log`. Expected: "line 1366 follows
   1368" (Starkie's order), apparatus items 569, 1164, 1511 placed on the verse before. A notes
   problem there (a heading with an impossible line number) is a fault in a batch: fix it there.
3. `check` (the clouds section must stay clean: 0 lemmas not found, every short definition);
   `build --only clouds`; `catalog`; commit; tick the Clouds line below.
The Clouds was done with an extra review agent per batch (REVIEW.md) because the author had
turned "ultracode" (workflows) on; for the later plays use it if the author asks for the
Clouds-level checking, otherwise the brief's route (one agent per batch, checker, residual pass).

*Medea, step 3 onwards:* step 2 is done (see Decisions, "Medea step 2"); the OCR of the text,
introduction and notes leaves is on disk (`pipeline/build/drama-scans/cu31924079583609/`). Step 3
needs module work for Earle's layout before the draft (tests with each change):
* `drama_pages.page_layout`, layout "earle": no rule; the verses are the lines above the start of
  the block in smaller type (his commentary); no apparatus on the text pages (`app_y` None, no
  apparatus crops in `write_draft`; the first page's notes say "no apparatus on the text pages").
* `drama_prose._region`, kind notes, layout "earle": the commentary begins where that small-type
  block begins (take it from `page_layout`), two columns.
* Earle's notes run on inside paragraphs: a new note begins after a dash with its number and bold
  lemma ("— 20. **ἡ δύστηνος**: …", "— 21 f. …"). Either the draft splits paragraphs there into
  `## 20` notes, or INSTRUCTIONS-prose.md gets an Earle section telling the agents to; look at
  two drafted pages before choosing.
* A new prose kind `app` for `play.app_leaves` (his "Notes on the text of this edition",
  pp. 267-294 = leaves 274-301, fetch and OCR not yet run): `KINDS` in drama_prose.py, the
  `drama-prose` choices in `__main__.py`, headings `## 107` as in the notes; `merge_play` takes
  the apparatus from the `app-NN.md` batches when `app_leaves` is set (one item per note, the
  note's text as the item).
* INSTRUCTIONS-text.md and INSTRUCTIONS-prose.md: an Earle section each (the page, the run-on
  notes, the critical notes).
Then the usual steps 3-9; the translation is Coleridge's from Perseus (merge only).


- [x] Step 0: set-up (2026-11-01)
- [x] Step 1: modules, tests, CLI (2026-11-01; tried on Agamemnon leaves 31-36, notes 150-151, introduction 11-12)
- [x] Agamemnon: 2 ✓ leaves · 3 ✓ draft · 4 ✓ text batches (two passes) · 5 ✓ merge · 6 ✓ notes · 7 ✓ introduction · 8 ✓ translation, sigla, glossary, about · 9 ✓ build and pack
- [x] Choephoroi: 2 ✓ · 3 ✓ · 4 ✓ (two passes) · 5 ✓ · 6 ✓ · 7 ✓ · 8 ✓ · 9 ✓
- [x] Eumenides: 2 ✓ · 3 ✓ · 4 ✓ (two passes) · 5 ✓ · 6 skipped (no notes) · 7 ✓ · 8 ✓ · 9 ✓ · 10 ✓ group check (2026-11-01)
- [x] R1: reader 0.6.0 (bundle built 2026-11-01; upload and products: see For the author)
- [ ] Clouds: 2 ✓ · 3 ✓ · 4 ✓ (transcribed, reviewed, residuals, facing-page apparatus) · 5 ✓ · 6 (35 of 39 notes batches reviewed; see "Resume here") · 7 ✓ · 8 ✓ · 9 (about, sigla, READMEs, pack done; final merge, build, catalog still to do)
- [ ] Medea: 2 ✓ (apparatus rule: Earle's appendix) · 3 · 4 · 5 · 6 · 7 · 8 · 9
- [ ] Frogs: 2 · 3 · 4 · 5 · 6 · 7 · 8 · 9 · 10 group check
- [ ] R2: reader 0.7.0
- [ ] Bacchae: 2 · 3 · 4 · 5 · 6 · 7 · 8 · 9
- [ ] Alcestis: 2 · 3 · 4 · 5 · 6 · 7 · 8 · 9
- [ ] Lysistrata: 2 (two scans) · 3 · 4 · 5 · 6 (Rogers) · 7 · 8 · 9 · 10 group check
- [ ] R3: reader 0.8.0

Tick a play's sub-steps in place (e.g. "2 ✓ 3 ✓ 4 (batches 1-7 of 12)") so that a resumed
session sees where it stopped.

## Decisions

(append dated entries: what was open, what was chosen, why, which pages were looked at)

* **2026-11-01, step 0, tests.** pytest is not installed in pipeline/.venv; the tests are
  `unittest` tests and run, as the repository README says, with
  `cd pipeline && .venv/bin/python -m unittest discover -s tests` (44 passed). Use that command
  wherever this brief says pytest.
* **2026-11-01, step 0, where the sources are.** The Perseus Greek texts and translations are
  fetched to `pipeline/sources/drama/<urn>.xml` under their Perseus names
  (`tlg0085.tlg005.perseus-grc2.xml`, `tlg0085.tlg005.perseus-eng3.xml` …), the GLAUx files to
  `pipeline/sources/glaux/`, the Athenian Society to `pipeline/sources/gutenberg/pg8688.txt` (vol. 1:
  Knights, Acharnians, Peace, **Lysistrata**, Clouds) and `pg8689.txt` (vol. 2: Wasps, Birds,
  **Frogs**, Thesmophoriazusae, Ecclesiazusae, Plutus; each play is cut out of its volume by
  drama.py), Coleridge's Bacchantes to `pipeline/sources/coleridge/bacchantes-99.wiki` …
  `-141.wiki` (99 is the title page, 141 ends with the chorus's last lines). The AGDT files were
  already in `pipeline/sources/treebanks/`. Translators checked in the files: Smyth (Agamemnon
  eng3, Choephoroi and Eumenides eng2), Coleridge (Alcestis, Medea eng2), Buckley (Bacchae eng2).
* **2026-11-01, step 1, leaves.** A leaf is the number of the scan's JPEG 2000 file
  (`<scan>_0042.jp2`), as in gorgias_pages.py. The Archive's page images (`/page/n<N>_w700.jpg`)
  count only the pages shown: for agamemnonwithint00aescuoft n = leaf − 1. The scan's
  `<scan>_page_numbers.json` (archive.org/download/<scan>/) maps leaves to printed page numbers
  and is the quickest way to find the text, notes and introduction at step 2.
* **2026-11-01, step 1, page images.** Grey PNGs and hOCR are kept per scan in
  `pipeline/build/drama-scans/<scan>/` (pages/, hocr/: `.grc.hocr` for the text route,
  `.eng.hocr` for the prose route), shared by the text and prose routes; each route's folder
  (`pipeline/build/drama-pages/<play>/`, `drama-prose/<play>/`) has `pages` as a link to them, so
  the agents' paths `pages/leaf_0042.png` hold.
* **2026-11-01, step 1, how the text route reads a Sidgwick page** (tried on Agamemnon leaves
  31-36, whose copy has a student's pencil notes between and beside the lines). The apparatus is
  found from the foot of the page upwards by its smaller type (Tesseract's `x_size`, verse about
  50, apparatus about 42) and its item numbers ("103.": two or more digits read with confidence
  70 or more), passing over handwriting (lines with no word read with confidence 75); a blank
  band above it is not required, as the pencil notes often fill it. Lines without a confident
  word are dropped as handwriting before the lines are put together; two OCR lines whose heights
  overlap but whose words differ are kept as two verses; a line Tesseract skipped is read again
  from the strip between its neighbours. The margin numbers are read per verse from the ink right
  of its last confident word (English model, digits only) and only multiples of 5 within 8 of
  the verse's number count. Perseus's `<q>` gets no quotation marks (the editions print none in
  the verse); its `<del>`/`<add>` give [ ] and ⟨ ⟩, which the agents check against the print (a
  flag says where the OCR shows brackets and the draft has none, or the reverse). Words Smyth
  divides between verses (νε- | ῶν) are joined on the first verse in the check text as in ours.
  Result on the six pages: 158 verses, 37 flagged (23 %), the apparatus found on every page.
* **2026-11-01, step 1, numbering.** A verse whose first word stands in an earlier Perseus line
  than the verse before keeps the numbers increasing (it takes the verse before's number with a
  letter) and is flagged; Perseus's own lettered parts (15b) count as their line (15), so the
  parts of a shared verse are numbered 15, 15a, 15b as for Sophocles. Where the print numbers a
  verse otherwise (Agamemnon 49a, which Sidgwick prints as 50 because he divides 49-50 otherwise
  than Smyth), the margin flag shows it and the agent renumbers to the print.
* **2026-11-01, step 1, translations.** Perseus translations (Smyth, Coleridge): a stage
  direction between verses becomes a `!` line, one inside a verse stays in parentheses; a
  Perseus line number our text lacks goes with the nearest earlier line, and segments that fall
  on the same line of ours are joined. The Athenian Society (Gutenberg) and Coleridge's Bacchantes
  (Wikisource) are matched to the Greek speeches by speaker and length (drama.speech_segments)
  and long speeches are cut about every ten Greek lines at sentence ends; their names are mapped
  by `Play.speakers` (to be filled at the play's step 8).
* **2026-11-01, step 1, the prose route** (tried on notes leaves 150-151 and introduction 11-12).
  Tesseract's English model reads Sidgwick's "l. 1178." as "1. 1178.": the note pattern accepts
  l, 1, I or |. Headings set in capitals become `# Title` in ordinary capitals and small letters
  ("The Story and the Plot of the Agamemnon"); footnotes are found by their smaller type or by a
  wider gap and a note's mark at the foot, and written `[Note: …]`; a line Tesseract lost (the
  pencil underlining stretched its neighbour's box) is read again from the strip. The EGT word
  checks were moved into `egt_ocr.check_words` (no change to the EGT's output: compared on leaf
  150) so that the prose route uses them.
* **2026-11-01, Agamemnon step 2.** Scan agamemnonwithint00aescuoft is the third edition,
  revised (Oxford 1887), Part I (introduction and text) and Part II (notes) in one scan; leaf = n + 1.
  Text pp. 1-61 = leaves 31-91 (line 1 on leaf 31, 1664-1673 on leaf 91); notes pp. 3-79 = leaves
  93-169 (Part II begins at p. 3; leaf 92 blank); introduction pp. vii-xxiii = leaves 11-27, and
  the list of persons (ΤΑ ΤΟΥ ΔΡΑΜΑΤΟΣ ΠΡΟΣΩΠΑ) on leaf 30, which goes into introduction.md as
  "## The persons of the drama" (the Sophocles rule); leaves 28 blank, 29 half-title. The
  chapters "The Editions" (with the abbreviations of the editors the apparatus cites) and
  "Translations" are lists: left out of introduction.md as the brief says, but the abbreviations
  go into sigla.md with the manuscripts (pp. xix-xx) and the signs of the text (p. xxii: * before
  a conjecture, † where no reading satisfies): sigla leaves 23-26. The Appendices (pp. 80-85,
  leaves 170-175: "The remote deliberative", Verrall on τόπος/τοπάζω) are neither notes on lines
  nor the introduction: left out. Layout seen on leaves 31-36, 60-61, 90-91: running head with
  the page number; the speakers' abbreviations (ΚΛ., ΧΟ., ΑΙ.) in the left margin, a new
  speaker's name centred above the first speech (ΦΥΛΑΞ.); the margin numbers every fifth line at
  the right; metrical labels (στρ. α΄., ἀντ. β΄., μεσῳδ.) in the right margin; the apparatus at
  the foot of the page, full measure, items "850. … MSS. corr. Pors."; the copy has a student's
  pencil notes in English between and beside the lines on many pages, and underlinings.
* **2026-11-01, Agamemnon step 3.** Leaves 47-48 are the title page of Part II (Notes) and its
  verso, bound in after p. 16: left out of the text leaves. The refrain 1489-1496 = 1513-1520
  made difflib pair the print's first copy with Perseus's second and leave 1489-1512 unmatched;
  drama_pages.realign now aligns again, by a full monotone alignment, the neighbourhood of every
  stretch of 15 or more unmatched Perseus words, and takes it where it pairs clearly more words.
  Draft: 59 pages, 1607 verses, 417 flagged (26 %), ten batches. Page 22 (leaf 52) prints no
  apparatus. The agents' brief has a section for Sidgwick's pages (margin labels, handwriting,
  apparatus format).
* **2026-11-01, Agamemnon step 4: a second pass.** The first pass showed that Sidgwick differs
  from Smyth far more than Burnet's Gorgias from its Perseus text, and in ways the flags do not
  see: punctuation (not compared at all), daggers and brackets, and words Tesseract read rightly
  but with confidence under 80. `drama-residuals <play>` (drama_residuals.py) compares every
  checked verse with the OCR of its printed line, word by word with its punctuation, and lists
  each difference Tesseract read with some confidence (477 on 59 pages: punctuation 214, words
  only the OCR has 120, accents 91, words 44, brackets 8), with a crop per page; a second round
  of agents (brief RESIDUALS.md, two batches each) settles them against the print and makes the
  numbering follow the print's margin numbers, which the first round had left open in several
  places. Rules given in RESIDUALS.md: a lettered verse the print counts as its own takes the
  print's number; a stretch counted otherwise is renumbered between margin numbers (where two
  cannot both be met, the later wins); transposed verses keep each its own number in the print's
  order (Agamemnon 1204 before 1203, 1304 before 1303), which `check` reports as a warning only;
  a diaeresis is written as printed (Ἀχαιϊκοῦ, ἀΐστοις). This pass is part of the route for every
  play from now on: step 4 = flags, then residuals.
* **2026-11-01, Agamemnon step 4, agents' scratch files.** Two agents' helper scripts of the
  same name in the shared scratchpad overwrote each other (one agent noticed and redid its
  edits); every "res:" note naming a mark was then checked against the text (89, all present).
  The briefs now require each agent to keep its files in a folder of its own.
* **2026-11-01, Agamemnon step 5.** The merge files an apparatus item that Sidgwick numbers by a
  verse our numbering lacks under the nearest earlier line, with his number in brackets in front
  (`[135] οἴκῳ MSS. corr. Scal.` under 133); a word the treebank has as two halves (Smyth divides
  it between verses) takes the second half's lemma where it continues the first's letters. The
  review's corrections go in drama_fixes.py (one table per play), not in drama.py. Ten random
  verses of grc.txt compared with the page by eye: all ten as printed (89, 104, 128, 201, 258,
  487, 855, 1388, 1478, 1565).
* **2026-11-01, Choephoroi step 2 (done early, during the Agamemnon's step 6, so that its OCR
  can run meanwhile).** Scan choephoroiwithin00aescuoft, first edition (Oxford 1884); the copy has
  a student's notes in pencil and ink. The scan hides 15 leaves (scandata.xml: 28-29, 52-53,
  62-63, 70-71, 92-93 and the end), so the Archive's page images are not leaf − 1 here and its
  page-number file is wrong after the first gap; drama.py now reads each scan's scandata.xml
  (`hidden_leaves`, `leaf_of(scan, n)`) and `Play.visible()` skips hidden leaves. Text pp. 3-43
  = leaves 37-83 (41 pages); notes pp. 45-121 = leaves 85-163; introduction pp. vii-xxvii =
  leaves 11-33 and the persons on leaf 36; sigla (manuscripts, scholia, editions, text of this
  edition) leaves 26-33. Appendices (from p. 122) left out as for the Agamemnon. Layout as the
  Agamemnon's.
* **2026-11-01, Agamemnon steps 6-8.** The English OCR of this pencil-marked copy is weaker than
  its flags show (quotation marks, "l." read as "1.", Greek read as Latin letters, lines garbled
  under underlining): the agents read each page's column through against the image, not only the
  flags; the prose brief's run-on rule stands (a page that begins with a new paragraph of the note
  before is left without `+ `, and the merge files it under that note). Sidgwick's bracketed scene
  summaries ("[Prologue. … (ll. 1-39.) …]") are notes headed by the range they name, kept in
  plain type and in their brackets; a note Sidgwick numbers inside one of our longer lyric verses
  goes to the verse near it that holds its lemma (11 of 21), else to the nearest earlier line. The
  merge writes elision ʼ for the OCR's ᾽ in the notes. 786 notes; introduction with Sidgwick's
  chapters, the list of persons, the lists of editions and translations left out. sigla.md
  written from pp. xix-xxii; glossary.md (19 names and rare words), shortdefs.tsv (72 glosses):
  every lemma finds a dictionary entry and a gloss.
* **2026-11-01, Eumenides step 2: no notes.** The only scan of Sidgwick's Eumenides,
  eumenideswithint01aescuoft, is "Vol. I.—Introduction and Text" (Oxford 1887); the Archive has
  no scan of vol. II (the notes) under any identifier (searched by title and author; the brief
  says not to look for another edition). The Eumenides therefore ships with Sidgwick's text,
  apparatus and introduction, Smyth's translation and the treebank, and without a commentary;
  step 6 is skipped and about.md says so. Leaves (this scan's jp2 files begin at _0001, so
  leaf = page image n + 1; its scandata is in scandata.zip, which drama._scandata now reads):
  text pp. 35-74 = leaves 37-76; introduction pp. 7-31 = leaves 9-33, the persons on 36; sigla
  (manuscripts, scholia, editions, the text) leaves 27-32. A first draft on leaves 36-75 (one
  leaf early) was thrown away before any agent saw it. The text pages carry a student's ink notes, as the
  brief warns.
* **2026-11-01, Choephoroi step 4, a renumbered transposition.** Sidgwick moves Perseus 997-1004
  (τί νιν προσείπω … θερμαίνοι φρενί) to follow 982, with Hermann, and numbers the verses in his
  new order (983-990 for the moved verses, 991-1004 for Perseus 983-996), giving the traditional
  numbers only in brackets. Unlike the Agamemnon's transpositions (where his margin keeps each
  verse's own number), the printed numbers here are the new ones, and his notes and apparatus cite
  them: the text follows the print. Translation, sections and treebank are fitted by the words, not
  the numbers, so they are not affected.
* **2026-11-01, Clouds step 2: leaves and layout.** Scan cloudsofaristoph00aris_0 (jp2 from
  _0000; hidden leaves 0, 42-43 and 298-299, so leaf = page image n + 3 from n 42 on). Each
  spread: the left-hand (even) page has the Greek with the speakers abbreviated in the left
  margin and the margin numbers on the right every fifth line, then a rule, the apparatus
  (numbered items, full measure), a second rule and Starkie's commentary in two columns; the
  right-hand (odd) page has his translation at the top and the commentary continued in two
  columns under a rule. Text pp. 10-314 = leaves 108-414, every other shown leaf (153 pages; the
  hidden pair 298-299 keeps the alternation), translation on the facing leaves 109-415,
  commentary on all of them (under the last rule on a text page, under the first on a
  translation page); the facing page is the next shown leaf, not leaf + 1 (Play.facing).
  Introduction leaves 19-98 (pp. vii-xc), the Greek hypotheses 101-106 and the persons 107;
  sigla: the chapter "The Manuscripts", pp. lvii-lx = leaves 67-70. The apparatus sits between
  the two rules (drama_pages.page_layout takes it from there when a second rule is found).
  Starkie's translation is used (not Hickie's): the pages are clean print. The jp2 download
  failed for 25 leaves, and the page-image fallback took page image n = leaf, which is the wrong
  page in a scan with hidden leaves; fixed (n counted over the shown leaves), the 25 refetched.
* **2026-11-01, Eumenides step 4, numbering.** Sidgwick's apparatus numbers sometimes count one
  above his margins (788, 796, 798, 879, 944) or one below (347, 507, 521-522); they are copied as
  printed and the merge places them on the nearest earlier verse with the [N] prefix. Two margin
  numbers stand one verse low against both the neighbouring margins and the apparatus (270 on
  p. 45, 535 on p. 55): there the apparatus and the other margins were followed, not the brief's
  "later margin wins" tie-break. The stage cries (Μυγμός., Ὠγμός., 117-129) are `!` lines; the
  print counts them as verses, so their numbers are skipped.
* **2026-11-02, Choephoroi steps 5-9.** The AGDT Choephoroi ends at line 945: the last 687
  words (946-1076) have the analyser's lemma and form, corrected in the review (116 corrections,
  most of them there), and no syntax tree. GLAUx could fill the trees automatically, but a text
  has one syntax label (hand or machine) for all its lines; left without, and said in about.md
  and texts/README.md. Ten random verses checked by eye against the page (93, 136, 252, 330, 422,
  786, 844, 864, 972, 1071): all as printed. 1062 verses, 350 apparatus notes, 616 commentary
  notes; every lemma found and glossed.

* **2026-11-01, Eumenides steps 5-9.** 1019 verses, 318 apparatus notes (three numbered by
  Sidgwick for verses our numbering lacks: [347], [879], [944], placed on the verse before);
  introduction in 17 sections, persons included. The AGDT covers the play; 62 words where
  Sidgwick reads otherwise have no node. Review list 176 words: 45 hand analyses, 13 lemma fixes
  (spellings to the dictionaries' headwords: συνοικήτωρ, σύμβουλος, ὑπισχνέομαι …). Ten random
  verses checked by eye against the page (480, 481, 494, 539, 593, 820, 899, 901, 910, 973): all
  as printed. sigla.md from pp. 25-30 (manuscripts in two groups, editors' table, emendators).
  No commentary (vol. II has no scan), said in about.md and texts/README.md.

* **2026-11-01, Clouds step 3: draft.** Three faults found before any agent saw a page: (1) the
  Clouds is tlg0019.tlg003, not tlg004 (the Wasps), so the first draft matched the Wasps; Perseus
  text and GLAUx file corrected (the other eight plays' ids checked by their Perseus titles);
  (2) the leaf 130 OCR was of the wrong page (a test before the refetch), redone; (3) Starkie's
  facing page holds the translation and the commentary, and on 30 of the 153 spreads the
  apparatus run on between two rules under the translation; the draft first made no facing crops
  for Starkie (wrong), now it makes them where the facing page has a second rule; the 30 blocks
  were checked against the batches afterwards by a workflow (fix, independent verify, commit). Starkie prints the end of a verse too long for the line
  indented on the next line (a turnover); the draft now joins such a line to the verse above
  when the line above reaches the right edge, the line is indented by 1.5 x-heights or more and
  its first word is in the same Perseus line (63 joins, each flagged for the agents); a verse
  divided between speakers that Starkie prints on two stepped lines keeps its letter (35a).
  Result: 153 pages, 1697 verses, 722 flagged (43 %). INSTRUCTIONS-text.md has a Starkie section.
  From here the bulk agent stages run as workflows (the author turned ultracode on): per batch a
  transcription agent, then an independent review agent (checker, apparatus completeness against
  the crops, every turnover and lettered verse against the page), each batch committed when
  reviewed; then the residual pass. The brief's limits hold (at most 10 agents at once).

* **2026-11-01, Medea step 2: leaves, layout, the Medea rule.** Scan cu31924079583609 (316
  leaves, jp2 from _0000, no hidden leaves; leaf = page + 7 throughout). Earle prints a critical
  apparatus as an appendix, "c. Notes on the text of this edition" (pp. 267-294 = leaves
  274-301, a note per line he discusses, "107. οἰμωγαῖς Plüss …: … "), after his account of the
  codices and their sigla (pp. 255-259, the table pp. 257-259 = leaves 264-266, after
  Prinz-Wecklein): so by the Medea rule text and apparatus are Earle's, and the product id stays
  euripides_medea_earle. The layout is new ("earle"): the Greek at the top of every page
  (pp. 73-247 = leaves 80-254; no facing translation, so no alternation), the margin numbers at
  the right every fifth verse, the commentary under it in two columns in smaller type, with no
  rule between; the notes run on inside paragraphs, a new line number and its lemma in bold after
  a dash ("— 20. **ἡ δύστηνος**: …"). Introduction pp. 7-64, the Greek hypothesis and the persons
  pp. 65-72 (leaves 14-79). The critical notes go through the prose route as their own kind
  (app_leaves) and are merged as the apparatus file. Module work for this layout (verses above
  the small-type block, the commentary's region, the app kind) is part of Medea step 3.

## Sizes, for planning

| play | lines | text leaves (about) | notes leaves (about) | introduction |
|---|---|---|---|---|
| Agamemnon | 1673 | 75 | 90 | short |
| Choephoroi | 1076 | 50 | 80 | short |
| Eumenides | 1047 | 45 | 30 | short |
| Clouds | 1510 | 110 text + 110 facing translation/commentary | in the facing pages | long |
| Medea | 1419 | 150 (text and notes share the page) | — | long |
| Frogs | 1533 | 110 | 170 | medium |
| Bacchae | 1392 | 90 | 150 | very long |
| Alcestis | 1163 | 55 | 115 | long (about 90 pages) |
| Lysistrata | 1321 | 45 (Hall-Geldart) | 110 (Rogers, foot of page) | medium |

The Gorgias cost about 90k tokens per six text pages checked; prose pages, where only flagged
words are looked at, cost less than half of that. Expect 1-2 million tokens per play.
