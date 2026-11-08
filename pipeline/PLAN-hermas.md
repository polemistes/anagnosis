# The Shepherd of Hermas (Ποιμήν), from Kirsopp Lake's Loeb edition

Decided with the author on 2026-11-08 after an assessment of the sources (memory note
"hermas-sources"; the research notes are summarised under **Decisions already taken**). The
pipeline's rules are those of `pipeline/PLAN-drama.md` and, for a prose text read by OCR against a
check text, `pipeline/PLAN-true-story.md` (read both first: this brief names only what differs).
This file is the brief: follow it step by step in the order given, tick the steps off under
**Progress**, write every choice the brief does not settle under **Decisions** (dated, with the
pages looked at), and commit after each step, this file with it. Where the brief leaves something
open, take the choice that keeps the data closest to the printed page, write it under Decisions
and go on; the questions that only the author can answer are collected under **For the author**
and never block the next step. The work may be cut off at any moment: every step saves to disk as
it goes and can be run again from where it stopped (`git status`, `git log -5`, Progress and
Decisions here, then `grep '^=== '` on the batch file being written shows the first missing page).

## What ships, and the rules behind it

**Lake's text with Lake's apparatus, Lake's translation and Lake's notes, from one edition.**
Kirsopp Lake, *The Apostolic Fathers*, vol. II (Loeb Classical Library, London, Heinemann, and
New York, Macmillan, 1913), pp. 1–305: the Greek on the left-hand pages with his short critical
apparatus at their foot, his English translation facing it with his explanatory footnotes, his
introduction to the Shepherd before it. Lake died on 10 November 1946: the edition is in the
public domain in Norway (70 years) and in the US (1913). Nothing from any other edition's text
or apparatus ships (the same-edition rule of PLAN-drama.md).

**The check text is Lake's own text, proofread by others.** James Tauber and Seumas Macdonald's
*Open Apostolic Fathers* (github.com/jtauber/apostolic-fathers, `texts/013-shepherd.txt`, CC
BY-SA 4.0) is Lake's Greek, compared across three digitisations and "manually checked (twice
independently) against multiple scans of the printed Lake". So, unlike the True Story (Harmon
against Nilén), the check text and the page should agree everywhere but where the print has a
misprint that Tauber silently corrected (Vis. 2.2.5 μενανοίας → μετανοίας is one), or where
Tauber erred. **The page wins**, with one exception, the author's rule from the True Story: an
evident misprint is corrected in the text and an apparatus note says so ("μετανοίας: Lake prints
μενανοίας, a misprint; corrected in this edition"; `MISPRINTS` in the merge module, keyed by
Lake's page and verse). Tauber's own notes on his decisions are in the repository's
`comparison/013-shepherd_COMPARE_JT3vsSM2_notes.txt`: read them at step 5.

**The apparatus has a check of its own.** First1KGreek's edition of the same Loeb text
(`data/tlg1419/tlg001/tlg1419.tlg001.1st1K-grc1.xml`, CC BY-SA 4.0, typed from the 1917
reprint) carries Lake's 326 apparatus notes as inline `<note>` elements, in Beta code ("pro\s
gunai=ka/ tina AL1"). Converted to Unicode, they are compared item by item with ours at step 5:
every difference is either our transcription error or theirs, and an agent settles it from the
page. (Its Greek text is not used as check text: its Latin pages were run through a Beta-code
converter and came out as Greek letters.)

## Decisions already taken (do not reopen)

| what | source |
|---|---|
| Greek text, critical apparatus, translation, explanatory notes, introduction (one edition) | K. Lake, *The Apostolic Fathers* II, Loeb, 1913 (d. 1946). Scan **apostolicfathers02lakeuoft** (Toronto, the 1917 reprint from the same plates, 500 ppi colour, jp2, very clean; 410 leaves, none hidden before the end; **leaf = page + 12**, p. 2 = leaf 14, checked against page_numbers.json over the whole book; page image n = leaf). The Shepherd: introduction leaves 11–14 (4 pages: contents, the manuscripts and versions, date); **Greek on the odd leaves 15–313** (pp. 3–301), English facing on the even leaves 16–314; the Martyrdom of Polycarp begins at leaf 316. Spare: **apostolicfathers0000vari** (the 1913 first printing, 360 ppi colour, jp2) for a doubtful letter |
| check text (never shipped) | Tauber–Macdonald, Open Apostolic Fathers, `texts/013-shepherd.txt` (CC BY-SA 4.0; v1.0 2019, DOI 10.5281/zenodo.2555673): 754 lines, `book.chapter.section text`, 27 "books" (1–5 Visions, 6–17 Mandates, 18–27 Similitudes), headings as `N.0.0` (Ὅρασις αʹ, Ἐντολὴ αʹ, ΠΑΡΑΒΟΛΑΙ …, Similitudo X); 695 Greek sections, 27 Latin-only, 5 mixed (26.30.3, 26.30.4, 27.3.3, 27.3.5 Latin with Greek; 26.31.5–6 Greek within the Latin part) |
| apparatus check | First1KGreek `tlg1419.tlg001.1st1K-grc1.xml`, the 326 `<note n="verse">` elements in Beta code (the `n` is the verse within the chapter it stands in) |
| translation | Lake's own (1913), Perseus `canonical-greekLit/data/tlg1419/tlg001/tlg1419.tlg001.perseus-eng1.xml` (repository licence CC BY-SA 4.0): the same 27-book scheme, `div subtype="book"/"chapter"/"section"`, complete to Sim. 10.4.5, with Lake's 171 footnotes as `<note>` |
| notes 1 | Lake's 171 footnotes to the translation (the same file): a commentary of their own, `commentary-lake.md`, by verse. The brief's usual rule (a Perseus translation's footnotes are left out) is set aside here: they are the editor's explanatory notes, and the only English notes on Hermas that are already digital |
| notes 2 and introduction 2 | Charles Taylor (d. 1908), *The Shepherd of Hermas*, Early Church Classics, SPCK, 2 vols: I (1903: introduction, the Visions and Mandates in translation with footnotes), II (1906: the Similitudes, with an appendix on Hermas and the Gospels). Scans **shepherdofhermas0000herm** (vol. I, 360 ppi, jp2, 192 leaves, 2 hidden; leaf ≈ page + 4 for the arabic pages: introduction from about p. 9, the translation "FIRST VISION" from about p. 57, the Fourth Mandate about p. 118; find the leaves at step 2) and **shepherdofhermas02hermuoft** (vol. II, Toronto, 500 ppi, jp2, 168 leaves; leaf = page + 4: Similitude 1 about p. 10, the Tenth Similitude about p. 127, the Appendix from p. 137). Spares: shepherdhermas00taylgoog, shepherdhermas01taylgoog (Google, 600 ppi) for vol. I. Taylor's text is his own eclectic one; his notes are keyed to his translation by the printed verse numbers, so each note gets the chapter and verse where its mark stands (step 6) |
| introduction 1 | Lake's (leaves 11–14), first in `introduction.md`; Taylor's after it (two `#` parts). Taylor's appendix on the Gospels is left out (For the author) |
| syntax | **GLAUx `xml/1419-001.xml`** (text id 1479; automatic, CC BY-SA 4.0; 2,102 sentences, all `analysis="auto"`; its text is Tauber's, so it aligns word for word; the Latin sections have no tokens). No hand-made treebank of Hermas exists (AGDT, Pedalion, Gorman, Harrington, PTNK checked); PROIEL has none and is NC. `# syntax: automatic` |
| sigla | `sigla.md` written by hand from Lake's introduction (leaves 13–14: ℵ Sinaiticus, A Athous, the papyri P.Amh. 190, P.Oxy. 404, P.Berl. 6789, the Latin versions L1 (Vulgata) and L2 (Palatina), E Ethiopic, C Coptic, the quotations in Clement, Athanasius, Antiochus) and from the sigla as the apparatus uses them (Pam, Pox, Pber, L, Clem., Athan., Ant.) |
| slug, titles, product | `hermas`; Greek title Ποιμήν (Lake's running title ΠΟΙΜΗΝ), English "The Shepherd"; author Ἑρμᾶς / Hermas; product id `hermas_shepherd_lake`, €3, `google_play: yes` |
| pronunciation | `# pronunciation: koine` (Rome, second century; the author chose Attic for Lucian's learned prose, not for this) |

* **The unit of the text is the verse**, as in the New Testament: one line of grc.txt per
  verse, numbered `book.chapter.verse` with the 27 books of the digital texts (`1.1.5` = Vis.
  1.1.5, `6.1.1` = Mand. 1.1, `26.30.2` = Sim. 9.30.2), which is the reader's `book.chapter.verse`
  scheme (linenum.VERSE; the app shows named books one at a time). Each book is a `== book`
  section whose label names it: `== book Vision 1 · Ὅρασις αʹ`, … `== book Vision 5 ·
  Ἀποκάλυψις εʹ`, `== book Mandate 1 · Ἐντολὴ αʹ`, …, `== book Similitude 1 · Παραβολὴ αʹ`
  (Lake's Greek headings as he prints them; Mandates 1–3, 7–9, 11 and Similitudes 1–4, 7 have a
  single chapter). **The author chose the traditional numbering** (Vision, Mandate, Similitude
  with chapter and verse: Lake's own, and the one the literature cites) **and asked that the
  continuous numbering (chapters 1–114, Whittaker–Joly, used by Ehrman's Loeb and Holmes) be shown
  as well**: each chapter is a level-2 section `=== chapter 1 · 9` whose label carries the
  continuous number (the table: Vis. 1 = 1–4, Vis. 2 = 5–8, Vis. 3 = 9–21, Vis. 4 = 22–24, Vis. 5
  = 25, Mand. 1–3 = 26–28, Mand. 4 = 29–32, Mand. 5 = 33–34, Mand. 6 = 35–36, Mand. 7–9 = 37–39,
  Mand. 10 = 40–42, Mand. 11 = 43, Mand. 12 = 44–49, Sim. 1–4 = 50–53, Sim. 5 = 54–60, Sim. 6 =
  61–65, Sim. 7 = 66, Sim. 8 = 67–77, Sim. 9 = 78–110, Sim. 10 = 111–114; checked against the
  chapter counts, 114 in all). Verse numbers are the same in both systems.
* **How the reader cites it** (an app change, step 1): the New Testament's "Matthew 5:3" style
  would give "Vision 1 1:5". A header key `# citation: dotted` makes the reader write the
  traditional form: label `1.5` (chapter.verse) instead of `1:5`, citation `Vision 1.1.5`,
  ranges `Vision 1.1.5–7` and `Vision 1.1.5–2.1`; everything else as for the New Testament
  (`WorkData.verses`). Where the app lists the books (the title's book chooser), the names
  "Vision 1" … "Similitude 10" come from the section labels, as the New Testament's do.
* **The Latin end goes in an appendix (the author's decision).** Lake's Greek manuscript A breaks
  off after Sim. 9.30.2; from 9.30.3 to the end (10.4.5) Lake prints the Latin version L1, with
  the Greek that the papyri give at Sim. 9.30.3–4 and 9.31.5–6 (P.Amh. 190) and 10.3.2–5 (P.Oxy.
  404), about 1,250 Latin words and 150 Greek on leaves 305–313. **grc.txt and eng-lake.txt end at
  26.30.2.** Everything after it goes into `appendix.md` ("The end of the Shepherd in the Latin
  version"): section by section (Sim. 9.30.3, 9.30.4 …), Lake's Latin and Greek exactly as he
  prints them, each section followed by Lake's English of it (from the Perseus file, sections
  26.30.3–27.4.5), and Lake's apparatus items on those pages under their sections; a short
  heading paragraph says why (A's last leaf lost; L1; the papyri), in Lake's words from his
  introduction where he gives them. The Latin and the papyrus Greek are not annotated (no
  tokens, no syntax, no Latin layer); the reader opens the appendix as a document, like an
  introduction. Tauber's lines 26.30.3–27.4.5 (Latin in Latin letters) are the check text for
  the OCR of those pages, read with Tesseract's Latin model.
* **Lake's page** (looked at: leaves 15, 17, 19, 101, 311, 313, images n15–n19 at 700 px): the
  running head "THE APOSTOLIC FATHERS" and the page number; **Bible references in the left
  margin** in small type ("Ps. 2, 4; 123, 1", "Deut. 30, 3 cf. Jer. 3, 22": not text, dropped as
  margin words, recorded in the draft); the Greek with the chapter number as a centred Roman
  numeral line ("I.", "II.") and **the verse numbers printed in the text before each verse** ("2."
  in the type of the text); the apparatus at the foot in small type, each item beginning with the
  verse number ("2 θυγατέρα A, dominam E.", "3 πέρυσιν AL1, πρότερον ℵ, om. EL2"). No short rule
  (check at step 2; the drama layout's small-type rule finds the apparatus as for Sidgwick). The
  facing English page has its own heading ("THE SHEPHERD, vis. i. i. 3–8") and Lake's footnotes;
  it is not read (the translation and the notes come from Perseus).
* **Batches** (`pipeline/transcriptions/hermas/batch-NN.md`, six Greek pages each): the page's
  lines are **verses**, keyed by their reference (`1.1.2<TAB>text`), whole on the page where the
  verse begins (a verse divided by the page break stands with the page where it starts; the next
  page's block begins with the next verse); `=== chapter 2` on a line of its own where Lake prints
  a chapter numeral; `¶` before a verse Lake indents (he indents at chapter starts and at some
  speeches); `[title]` lines for the book headings he prints (ΠΟΙΜΗΝ, ΟΡΑΣΙΣ Αʹ …). The apparatus
  items carry the verse number as printed (`2`, `3`), the chapter being known from the text above;
  the merge files each under its verse (`## 1.1.2`), the printed number not repeated. The draft
  checks three things the page itself gives: every verse's first word follows its printed number,
  every chapter numeral stands where Tauber's chapter begins, and the OCR and Tauber agree word for
  word; what disagrees is flagged for the agents (INSTRUCTIONS.md, step 1).
* **Koine vocabulary (the author left this to the brief).** The lemmas are GLAUx's, which are LSJ's
  headwords (γίγνομαι, γιγνώσκω, ἐθέλω, πορεύω, ἀποκρίνω, οὕτως); the dictionaries offered are
  `# dictionaries: abbott-smith ml lsj` (Abbott-Smith first: a New Testament lexicon that covers
  most of Hermas's words in Koine form; LSJ, which cites Hermas, covers the rest; Dodson is keyed
  to Strong's numbers the Shepherd has not, and is left out). `aliases.tsv` lets Abbott-Smith be
  found under the Attic headword: the merge writes it from (a) `nt.resolve_lemmas` for lemmas no
  lexicon has under the given spelling, as `import-nt` does, and (b) a hand table in the merge
  module of Attic → Koine headwords (γίγνομαι → γίνομαι, γιγνώσκω → γινώσκω, ἐθέλω → θέλω,
  πορεύω → πορεύομαι, ἀποκρίνω → ἀποκρίνομαι, οὕτως → οὕτω(ς) as Abbott-Smith has it, φοβέω →
  φοβέομαι …; extend it from the merge log's list of lemmas Abbott-Smith lacks). About 500 lemmas
  (4–5 % of the words: διψυχία, διψυχέω, ὀξυχολία, σχισμή, πτελέα, ἰτέα, παραφυάς, ἡμίξηρος,
  συμψέλιον, ἀδίστακτος …) are in LSJ only: fine, LSJ is there. `shortdefs.tsv` for the lemmas
  Logeion's list lacks; `glossary.md` for the names (Hermas, Rhoda, Clement, Grapte, Maximus,
  Cumae, Arcadia, the Tiber, the twelve mountains' virgins' and women's names in Sim. 9) and for
  Hermas's own words where a gloss from Lake's English helps; rows in `pipeline/homographs.tsv` for
  every homograph group this text brings in (the homograph rule of 2026-11-08: list all, mark the
  one the tag identifies). GLAUx's gap marker (a lemma written `E`, 199 tokens) is an error of
  its source: those words get the analyser's lemma (the review list).
* **Not usable, ever**: Lightfoot–Harmer (Harmer's text, d. 1944, has no apparatus and is a
  different edition), Gebhardt–Harnack 1877 (before the Athos collation; no jp2 scan), Funk 1901
  (no digital text to check against), Hilgenfeld (Simonides), Anger–Dindorf (Simonides' forgery),
  the Celano Morpheus dump in Tauber's repository (`raw-gcelano-analysis/`, NC), PROIEL (NC),
  Snyder 1968 and Osiek 1999 (copyright), Bonner's Michigan papyrus (1934; US status unchecked;
  not in Lake anyway).
* **Agents**: as PLAN-true-story.md: one agent per batch of six pages, an independent reviewer per
  batch (REVIEW.md), the residual pass (RESIDUALS.md), at most ten agents at once; with ultracode
  on, as workflows. Every agent keeps its helper files in a folder of its own under the session's
  scratchpad. Check free memory (`free -h`) before a build or an emulator; never a Gradle build
  beside two emulators; close the emulator and stop Gradle when done (memory note
  "feedback-memory-use").

## Steps

1. **Module work** (tests with each change; `cd pipeline && .venv/bin/python -m unittest discover -s tests`).
   * `fetch.py`: `hermas/013-shepherd.txt` (raw.githubusercontent.com/jtauber/apostolic-fathers/master/texts/013-shepherd.txt),
     `hermas/tlg1419.tlg001.1st1K-grc1.xml` (First1KGreek), `drama/tlg1419.tlg001.perseus-eng1.xml`
     (canonical-greekLit), `glaux/1419-001.xml`.
   * Readers in a new `hermas_text.py`: `tauber_text()` → tokens with `sec` (`1.1.2`), `newsec`,
     `newchapter`, `heading` lines (`N.0.0`), `latin` (a Latin word), as `lucian_pages.perseus_prose`
     gives them, for the Greek sections 1.1.1–26.30.2 and separately for the Latin part;
     `first1k_apparatus()` → [(sec, text)] with the Beta code converted (`greek.betacode_to_unicode`;
     the `n` of a note is the verse, the chapter is the enclosing div); `lake_translation()` →
     [(sec, text)] and `lake_notes()` → [(sec, text)] from the Perseus file (the three-level
     `translation_sections` of lucian_pages generalised).
   * `lake_pages.py` from `lucian_pages.py` (copy and generalise; do not break the True Story): the
     Greek leaves of `PLAYS["hermas"]` (`text_leaves=[(15, 313)]` with `visible()` keeping the odd
     ones: add a `Play.odd_leaves` flag, or list them), the check text from `tauber_text`, the
     apparatus block by the drama layout (small type from the foot up; `app_bare_numbers=True`),
     the left margin's references dropped as margin words, the chapter numeral lines recognised
     (`^[IVXL]+\.$`), the **verse numbers read inline** and compared with where Tauber's verses
     begin, lines assembled into verses, the batch written per page as above. Commands
     `lake-pages hermas fetch|ocr|draft`, `check-hermas-batch FILE...` (format, verse order
     within the book, chapters, apparatus numbers naming verses of the page, elision ʼ, NFC, and
     every difference in wording from Tauber, "(noted)" where the notes name the verse),
     `merge-hermas`, `hermas-residuals` in `__main__.py`. The Latin pages (leaves 305–313: the
     Latin begins inside leaf 305 at Sim. 9.30.3) are drafted the same way with Tesseract's `lat`
     model and Tauber's Latin lines; their batch is `batch-latin.md`.
   * `lake_merge.py`: grc.txt (one line per verse, `== book` and `=== chapter` sections with the
     labels above, `@ ` paragraphs, header keys incl. `layout: prose`, `syntax: automatic`,
     `dictionaries`, `pronunciation`, `citation: dotted`), `MISPRINTS`, `commentary-lake-apparatus.md`
     (`## 1.1.2`), the apparatus comparison with First1K (a report in `build/hermas-merge.log`:
     items of ours with no First1K note of the same verse and similar words, and theirs with none
     of ours), tokens from GLAUx (`align`; the analyser for the rest; the review list
     `build/hermas-review.tsv`; `HAND_ANALYSES`/`LEMMA_FIXES` in drama_fixes.py), `eng-lake.txt` by
     verse to 26.30.2, `commentary-lake.md` from Lake's notes, `appendix.md` from `batch-latin.md`
     and the Perseus English, `aliases.tsv` (the two sources above), and, from the prose batches,
     `commentary-taylor.md` and `introduction.md`.
   * `drama_prose.py` for Taylor's two scans: `Play.notes_scan` holds one scan; add
     `notes_sources: list[tuple[str, list[tuple[int, int]]]]` (scan, leaf ranges) used for `notes`
     and `intro` when set, the crops under `build/drama-prose/hermas/<scan>/` (or prefixed by the
     volume), without breaking the plays and the True Story (their single `notes_scan` stays).
   * The app: `# citation: dotted` → `WorkData.dottedCitation` (from the `meta` table, as `dashes`
     is read); `lineLabel` "1.5", `citation` "Vision 1.1.5", `range` as above; a unit test in
     `commonTest`. Build with `./gradlew :shared:testAndroid`.
   * `pipeline/transcriptions/hermas/INSTRUCTIONS.md` from the True Story's, with a Lake section
     (the page, the margin references, the verse numbers, the apparatus's shape and sigla, L1/L2/E
     readings in Latin, `[title]`, `=== chapter`); `RESIDUALS.md`, `REVIEW.md` likewise; a Taylor
     section in `pipeline/transcriptions/drama/INSTRUCTIONS-prose.md` (how his footnotes are keyed:
     the running head gives Vision/Mandate/Similitude and chapter, the verse numbers stand in his
     translation, the footnote mark stands in a verse: heading `## 1.1.2`).
2. **Leaves.** Confirm from the page images (`https://archive.org/download/apostolicfathers02lakeuoft/page/n<N>_w700.jpg`,
   N = leaf) that leaf = page + 12 at both ends, that the Greek is on the odd leaves 15–313 and
   where the Latin begins (leaf 305?), that leaves 11–14 are Lake's introduction to the Shepherd;
   Taylor's leaves for his introduction (vol. I), the translation pages with notes (vol. I pp. 57–
   about 165, vol. II pp. 9–about 135) and their hidden leaves (scandata: vol. I has two); write
   them into `PLAYS["hermas"]`. Look at six Greek pages and two Latin ones and note the layout
   under Decisions. Commit.
3. **OCR and draft.** `lake-pages hermas fetch`, `ocr`, `draft` in the background; read the
   summary (pages, verses, flagged). The Loeb type is clean and the check text is the same
   edition: expect under 10 % flagged; over 30 % means the layout or the verse matching is wrong:
   fix the module, do not send it to agents. The Latin draft likewise.
4. **Text and apparatus batches.** About 25 batches of six pages plus `batch-latin.md`; agents
   with INSTRUCTIONS.md, reviewers, checker on every file, commit every few batches, then the
   residual pass.
5. **Merge and the checks.** `merge-hermas`; read the merge log: (a) every verse 1.1.1–26.30.2
   once, in order, against Tauber; (b) the First1K comparison of the apparatus, each difference
   to an agent with the page; (c) Tauber's comparison notes read for the places where he corrected
   the print, each checked on the page and either kept as printed or put in `MISPRINTS` with its
   note; (d) the review list to one agent; `check`; ten verses compared with the page by eye.
   Commit.
6. **Notes.** Lake's: written by the merge (`commentary-lake.md`), read its log. Taylor's:
   `drama-prose hermas notes fetch|ocr|draft` over both volumes, batches of eight pages
   (`notes-NN.md`): the agents keep only the footnotes (headed by chapter and verse as above) and
   leave the translation; checker; merge again; read the log (notes it could not place).
7. **Introductions.** Lake's (leaves 11–14, `intro-01.md`) and Taylor's (vol. I), the same
   route with `intro`; `introduction.md` with two `#` headings ("Lake's introduction (1913)",
   "Taylor's introduction (1903)").
8. **The appendix.** `appendix.md` from `batch-latin.md` and the Perseus English, as described;
   read it against the pages by eye (the Greek islands, the sigla of the apparatus items there).
9. **Translation, sigla, glossary, aliases, short definitions, homographs, about.md, README.**
   The merge writes `eng-lake.txt` and `aliases.tsv`; read their logs (sections of the translation
   with no verse, lemmas no dictionary has under any spelling). `sigla.md` from Lake's introduction
   (step 2's leaves). `glossary.md`, `shortdefs.tsv`, the `homographs.tsv` rows (the homograph
   groups of this text's lemmas, classified as on 2026-11-08: tag letters that fit each homograph;
   an agent, then a reviewer). `about.md` as texts/truestory/about.md with `ref_edition`,
   `ref_translation`, `ref_commentary` (Taylor; Lake's notes), `syntax` "machine-made (GLAUx), not
   checked by hand", `google_play: yes`, `product_id`. A "Hermas" section in texts/README.md, the
   row in play/README.md. Commit.
10. **Build.** `build --only hermas`; `check`; the pack (copy app/packs/truestory/build.gradle.kts
    to app/packs/hermas/ with the slug changed, add `hermas` to the lists in app/settings.gradle.kts
    and app/androidApp/build.gradle.kts); `catalog`. Then the emulator check of PLAN-drama.md step
    10 for this one text: buy it in the debug shop, open it, the book chooser (27 named books),
    read a chapter (verse numbers inline, the chapter heading with its continuous number), the
    citation "Vision 1.1.5" at the bottom and in the notes, the apparatus, a Lake note and a Taylor
    note under one verse (each named), the introduction, the appendix, the sigla, the word sheet
    (a Koine lemma found in Abbott-Smith through an alias), the syntax of one sentence, a verse
    read aloud (Koine); fix what is wrong; `adb emu kill`, `./gradlew --stop`. A reader release is
    the author's call.

## For the author

* **Taylor's appendix** (vol. II pp. 137 ff., Hermas and the Gospels): left out; say if you want it
  after the introductions.
* **The Michigan papyrus** (Bonner 1934, Sim. 2–9): not in Lake; public domain in Norway since
  2025, US status unchecked; a later note in sigla.md at most.
* **Release**: the text is built and in the catalogue after step 10; a reader release with it is
  yours to decide (play/README.md: build the bundle, upload, create and activate the product
  `hermas_shepherd_lake`, name "The Shepherd of Hermas", €3).

## Progress

- [ ] Step 1: modules, tests, CLI, app's dotted citation, INSTRUCTIONS
- [ ] Step 2: leaves
- [ ] Step 3: draft (Greek and Latin)
- [ ] Step 4: text and apparatus batches, residuals
- [ ] Step 5: merge, Tauber and First1K checks, misprints, review
- [ ] Step 6: Lake's and Taylor's notes
- [ ] Step 7: introductions
- [ ] Step 8: appendix (the Latin end)
- [ ] Step 9: translation, sigla, glossary, aliases, short definitions, homographs, about, READMEs
- [ ] Step 10: build, pack, catalogue, emulator check

## Decisions

(append dated entries: what was open, what was chosen, why, which pages were looked at)

## Sizes, for planning

The Shepherd: 27,340 Greek words in 695 verses (Tauber; GLAUx 27,570 word tokens), on about 150
Greek pages of the Loeb (leaves 15–303 odd), with about 326 apparatus items (First1K's count);
the Latin end 1,250 words on 5 pages. Lake's introduction 4 pages, his notes 171 (digital).
Taylor: about 230 pages of translation with footnotes (one to three a page: perhaps 400 notes)
and about 50 pages of introduction. Against the True Story (80 pages, 1,660 items, one day of
agent batches): twice the pages but a fifth of the apparatus and a check text of the same
edition; expect two days, the second mostly Taylor.
