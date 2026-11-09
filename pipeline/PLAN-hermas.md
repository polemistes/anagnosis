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
| introduction 1 | Lake's (leaves 11–14), first in `introduction.md`; Taylor's after it; then **Taylor's appendix "Hermas and the Gospels"** (vol. II pp. 137 ff.: the author asked for it on 2026-11-08), three `#` parts |
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
7. **Introductions.** Lake's (leaves 11–14, `intro-01.md`), Taylor's (vol. I) and Taylor's
   appendix on Hermas and the Gospels (vol. II, from p. 137 to its end), the same route with
   `intro`; `introduction.md` with three `#` headings ("Lake's introduction (1913)", "Taylor's
   introduction (1903)", "Taylor: Hermas and the Gospels (1906)").
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

* **Taylor's appendix** (vol. II pp. 137 ff., Hermas and the Gospels): decided 2026-11-08, the
  author asked for it: it follows the introductions in `introduction.md` (step 7).
* **The Michigan papyrus** (Bonner 1934, Sim. 2–9): not in Lake; public domain in Norway since
  2025, US status unchecked; a later note in sigla.md at most.
* **Similitude 1's label**: Lake prints no title of its own over Similitude 1, only the heading of
  all the Similitudes in capitals, ΠΑΡΑΒΟΛΑΙ ΑΣ ΕΛΑΛΗΣΕ ΜΕΤʼ ΕΜΟΥ, and that is its label in the
  book chooser ("Similitude 1 · ΠΑΡΑΒΟΛΑΙ ΑΣ …"), as printed. Tauber's "Παραβολὴ αʹ" would read
  more evenly beside the others, but is not on the page. Decided 2026-11-09, the author: "We keep
  to the text we are printing": Lake's heading stays.
* **Misprints in the apparatus**: Lake's misprints in his Greek text are corrected with a note
  (29). Decided 2026-11-09, the author: "But correct misprints, with a note": the five inside his
  apparatus items are corrected too, each with a note after the item (`APPARATUS_MISPRINTS`); the
  siglum F stays (a clear F on both pages, its meaning unknown, so not an evident misprint).
* **Release**: the text is built and in the catalogue after step 10; a reader release with it is
  yours to decide (play/README.md: build the bundle, upload, create and activate the product
  `hermas_shepherd_lake`, name "The Shepherd of Hermas", €3).

## Progress

- [x] Step 1: modules, tests, CLI, app's dotted citation, INSTRUCTIONS (2026-11-08): `hermas_text.py`, `lake_pages.py`, `lake_merge.py`, `tests/test_hermas.py`; `drama_prose` reads a kind from several scans; CLI `lake-pages`, `check-hermas-batch`, `hermas-residuals`, `merge-hermas`; the app's `citation: dotted` (tested); `transcriptions/hermas/INSTRUCTIONS.md`, `REVIEW.md`, `RESIDUALS.md` (the Taylor section of INSTRUCTIONS-prose.md at step 2, when his pages are seen)
- [x] Step 2: leaves (2026-11-08): Lake Greek 18-302 even, Latin 302-316 even, introduction 14-17, sigla 15-17; Taylor I introduction 13-58, notes 61-168; Taylor II notes 13-135, appendix 139-143
- [x] Step 3: draft (Greek and Latin) (2026-11-08): 143 Greek pages, 815 verse blocks, 24 batches; 25 % of the verses flagged before the footnote-mark flags (44 % with them); all 207 First1K notes placed; Latin 8 pages, 40 verse blocks, 25 % (`batch-latin.md`)
- [x] Step 4: text and apparatus batches, residuals (2026-11-08): 24 Greek batches and `batch-latin.md` checked and independently reviewed (five workflows of ten agents), the residual pass (628 items, one change); 207 apparatus items (209 marks), 111 margin references, as First1K; 25 checker remarks, all Lake's misprints noted
- [x] Step 5: merge, Tauber and First1K checks, misprints, review (2026-11-08): `texts/hermas/` written (693 verses, 207 apparatus items + 29 notes of corrected misprints, 27,138 tokens, none without a lemma); the First1K differences and Tauber's comparison notes settled on the page; 28 misprints and one title corrected (`MISPRINTS`, `TITLE_MISPRINTS`); `check` 0 errors; ten verses compared with the page
- [x] Step 6: Lake's and Taylor's notes (2026-11-08): Lake's from Perseus (234 verses: side-headings, footnotes, the margin references), one Greek slip of the Perseus file corrected as printed; Taylor's 231 pages in 29 batches checked and reviewed (six workflows), 174 notes under 173 verses and 6 on the Latin end (in the appendix)
- [x] Step 7: introductions (2026-11-08): 7 batches checked and reviewed (Lake 4 pages, Taylor I 46, Taylor II 5); `introduction.md`: Lake's introduction (1913), Taylor's introduction (1903) in five chapters with his lettered parts, Taylor: Hermas and the Gospels (1906), signed
- [x] Step 8: appendix (the Latin end) (2026-11-08): `appendix.md` from `batch-latin.md` (checked and reviewed at step 4), 34 sections 9.30.3-10.4.5 in order with Lake's translation and his 5 apparatus items, Taylor's 6 notes on the Latin end at its foot; one slip of the Perseus translation corrected; p. 304 read against the file
- [x] Step 9: translation, sigla, glossary, aliases, short definitions, homographs, about, READMEs (2026-11-08): 47 lemma corrections, 5 tokens by hand, one more misprint (26.23.5); glossary 43 names and shortdefs.tsv 72 entries (written and reviewed by agents, the rest by hand): every lemma has a short definition; 24 aliases; 2 homograph groups; sigla.md, about.md, texts/README.md, play/README.md
- [x] Step 10: build, pack, catalogue, emulator check (2026-11-08): data/hermas.sqlite (4.4 MB), app/packs/hermas, catalogue 18 texts; emulator check done, one fix (the short definition of πορεύω)

## Decisions

(append dated entries: what was open, what was chosen, why, which pages were looked at)

* **2026-11-08, step 1: what the pages showed, against the brief.** Looked at leaves 11-23
  (page images n8-n20), 15, 17, 18, 20, 22, 298-316 (every other), and the OCR of leaves 18-40
  (even), 100, 200, 302, 304. The brief's account of Lake's page was written without the images
  and is wrong in four places, all corrected here:
  * **The Greek is on the even (left-hand) pages**, leaves 18-302 = pp. 6-290 (143 pages); the
    English faces it on the odd pages. Leaf = page + 12 holds; the scan hides leaves 0-2, so the
    Archive's page image n = leaf − 3 (not n = leaf). p. 1 (leaf 13) is the half-title, Lake's
    introduction is pp. 2-5 (leaves 14-17, four pages: the Shepherd, the manuscripts and versions,
    the papyri); p. 6 (leaf 18) opens the text with ΠΟΙΜΗΝ and the numeral I, **without** the
    heading Ὅρασις αʹ that Tauber gives (Vision 2 has Ὅρασις βʹ, Vision 3 Ὅρασις γʹ, centred).
    Manuscript A ends inside p. 290 (leaf 302) after Sim. 9.30.2; **the Latin end is pp. 290-304,
    leaves 302-316** (8 pages, the English facing on 303-317); the Martyrdom of Polycarp begins on
    p. 307. PLAYS["hermas"]: `text_leaves=[(18, 302)]`, `latin_leaves=[(302, 316)]`, `leaf_step=2`.
  * **The apparatus is keyed by footnote marks, not by verse numbers**: a raised numeral after a
    word in the Greek, numbered afresh on each page (1, 2, 3), answered by the item at the foot that
    begins with the same numeral ("¹ τόπῳ ℵ* L₁, τρόπῳ ℵᶜAL₂(E). ² θυγατέρα A, dominam E.", running
    on). First1K's `<note n>` is that footnote number (two notes at Vis. 1.1.7 are n=1 and n=2), and
    its notes stand where Lake's marks stand. Of First1K's 326 notes, 111 are the margin's Bible
    references (`<bibl>`), 207 the apparatus to 26.30.2, and 7 more in the Latin part (garbled); so
    the apparatus has about 214 items, not 326.
  * The verse numbers are printed in the text ("2."), each chapter as a centred Roman numeral; the
    Bible references stand in the left margin of the even pages.
  * Lake's notes to the translation (Perseus) are **58 footnotes and 133 side-headings**
    (`type="marginal"`: "Hermas and Rhoda"), not 171 footnotes.
* **2026-11-08, step 1: how the route answers it.**
  * Batches (`transcriptions/hermas/batch-NN.md`) are per page and **keyed by verse** (`1.1.4`),
    a verse divided by a page break continuing as `1.1.3+` on the next page (so that each footnote
    mark stays on its page and is numbered there); `[title]` and `[chapter]` lines as printed; `¶`
    before an indented verse; marks as raised digits after the word (`τόπῳ¹`); the apparatus by
    footnote number; a `--- margin` section of `verse<TAB>reference`.
  * The draft places each mark where First1K has its note (aligned to Tauber's words verse by
    verse) and numbers them by page; every mark is flagged for the agent to confirm on the page.
    The apparatus items themselves are written by the agents from the image (Tesseract's
    grc+eng and eng+grc readings as help), so that the step-5 comparison with First1K's notes is a
    real second check.
  * **The margin references are kept** (the brief dropped them): they are Lake's, cost the agents
    little (pre-filled from First1K, checked against a crop of the margin), and go into
    `commentary-lake.md` under their verse with Lake's footnotes and side-headings.
  * The draft checks the verse number read before each verse's first word, a number read where
    Tauber begins no verse, and a chapter numeral above each chapter's first verse. Tesseract's
    Greek model reads II as "ἐδ", III as "ΠῚ": numerals and titles are found by their shape (a short
    centred line between the text lines; drama_pages drops them as specks), the numeral written from
    the chapter that begins below it and flagged when the OCR disagrees; a title that resembles
    Tauber's heading is written as Tauber has it, else as read, flagged either way.
  * `skel_fold="ξζ"` (Tesseract reads Lake's ζ as ξ throughout: ὀργίξεταί, δοξάξειν), the risk of
    a real ξ/ζ difference passing unflagged accepted as for the True Story. The apparatus crops are
    read with grc+eng / eng+grc (Lake's remarks are English).
  * Trial draft of leaves 18-40: 72 entries (verses, titles, numerals), 45 flagged, 29 without
    counting the mark checks; the misprint μενανοίας (2.2.5) is flagged ("the OCR reads").
  * Taylor's notes are headed by the traditional reference as he prints it (`## Mandate 4.1.2`,
    `## Mandate 1.3` for a book of one chapter); the merge converts it (`lake_merge.taylor_ref`).
    His notes on the Latin end go into the appendix. A prose kind may now come from several scans
    (`Play.notes_sources`); the page stems carry the scan's place in the list (`p-10057`,
    `p-20057`), the crops go to `build/drama-prose/hermas/<scan>/`. The introduction kind will draw
    on three scans: Lake (leaves 14-17), Taylor I, Taylor II (the appendix).
  * `Play.route = "lake"`: the prose batches go to `transcriptions/hermas/`, and the prose checker
    reads Taylor's headings.
* **2026-11-08, step 2: leaves.** Lake: confirmed from `page_numbers.json` and the images (leaf 15
  = p. 3, leaf 302 = p. 290, leaf 316 = p. 304): leaf = page + 12 throughout. Six Greek pages looked
  at (leaves 18, 20, 22, 24, 26, 298-302) and Latin ones (304-316): the layout as recorded under step
  1; the apparatus runs on in one or two lines at the foot, small type, no rule; pages without
  apparatus occur (p. 10). The sigla are on pp. 3-5 (leaves 15-17: ℵ on p. 3, A H and the papyri on
  p. 4, Pᵇᵉʳ, L₁ L₂ L E C and the Fathers on p. 5): `sigla_leaves=[15, 16, 17]`.
  * **Taylor I** (shepherdofhermas0000herm: 192 leaves, leaf 0 hidden, page image n = leaf − 1,
    leaf = page + 4; contents page leaf 9 read): Preface pp. 7-8, **Introduction pp. 9-54 = leaves
    13-58** (1 Authorship and date, 2 The text and the versions, 3 Structure and contents, 4 Sources
    of the Shepherd, 5 The doctrine of Hermas), half-title "Visions I-IV" p. 55, **the translation
    with his footnotes pp. 57-164 = leaves 61-168** (Visions I-IV pp. 57-104, Vision V and the
    Mandates pp. 105-164), Index pp. 165-166, then the publisher's lists.
  * **Taylor II** (shepherdofhermas02hermuoft: jp2 from _0001, hidden 170-173 at the end, page image
    n = leaf − 1, leaf = page + 4; contents page leaf 8 read): "The Similitudes" half-title, **First
    Similitude p. 9 to the end of the Tenth p. 131 = leaves 13-135**, "APPENDIX" half-title p. 133,
    **the Appendix pp. 135-139 = leaves 139-143** (five pages, not the "137 ff." of the brief; signed
    "C. Taylor, Cambridge, August 1906"), Index p. 141.
  * Taylor's page (looked at vol. I leaves 54-66, 160-170; vol. II 9-24, 128-145): running head (THE
    SHEPHERD left, the book right), his translation with the book's title, CHAPTER headings and the
    verse numbers in the text, and under it his footnotes in small type, marked * † …, some running
    over to the next page. His notes are footnotes to his translation, so the agents keep only the
    footnotes, each headed by the traditional reference of its mark (`## Vision 1.1.2`), with the
    English words before the mark as lemma: the Taylor section of
    `transcriptions/drama/INSTRUCTIONS-prose.md` says how.
  * `PLAYS["hermas"].notes_sources`: notes = Taylor I 61-168 and Taylor II 13-135 (231 pages, 29
    batches of eight); intro = Lake 14-17, Taylor I 13-58, Taylor II 139-143 (55 pages, 7 batches).
    Leaf 13 of each Taylor volume fetched from its jp2 zip: p. 9 in both, as computed.

* **2026-11-08, step 3: the draft.** Lake's 143 Greek pages and 8 Latin pages read by Tesseract
  (`build/logs/hermas-fetch-ocr.log`) and drafted (`build/logs/hermas-draft.log`):
  `transcriptions/hermas/batch-01.md` to `batch-24.md` (six pages each) and `batch-latin.md`, the
  check sheets in `build/lake-pages/hermas/`.
  * **The rate.** The first draft flagged 55 % of the verse blocks, 41 % without the footnote-mark
    flags (every mark is flagged by design, so the agents look at each on the page). That is over
    the brief's 30 %, so the module was mended before any agent saw it. The layout and the verse
    matching were right: every verse of Tauber was placed on a page, all 207 apparatus notes of
    First1K were placed as marks, and every page with a mark has its apparatus found (108 pages
    with an apparatus; leaf 80 has one with no First1K mark, because its note 1 stands on the
    title "Ἀποκάλυψις εʹ¹", which First1K's text lacks: the agent writes the mark on the [title]).
    What raised the rate was Tesseract's Greek model on Lake's figures and a few letters. Mended:
    * **Verse numbers.** The model reads 2 as "3", 3 as "8", "5" or "9", 6 as "0", and turns many
      numbers into a letter or splits them ("Ἰ.", "Ἷ:", "Π." for 7, "δ." for 6, "9" ":"). The
      misreadings counted on the whole draft are accepted (`_NUM_MISREAD`); a short token of no
      Greek word that stands just before a verse of Tauber counts as its number (`_weak_number`);
      a "1." lost under a chapter numeral is not flagged (Lake prints it under every numeral: p. 16).
    * **Pieces of a word** (three letters or more of its beginning or end: "ρόνον" for χρόνον) and
      **λ read as χ, ζ as ἕ, Latin c as e** ("ἱχαρὸς", "ἕωή", "tune") are not flagged as readings
      (`_ocr_noise`). ὅτι read "ὅτε" (13 times; p. 10 looked at: Lake prints ὅτι) stays flagged,
      since ὅτε for ὅτι is a reading an edition can have.
    * **Books of one chapter have no numeral** (Mandates 1 and 2 on p. 70; by Tauber's chapters Vision 5,
      Mandates 1, 2, 3, 7, 8, 9, 11 and Similitudes 1, 2, 3, 4, 7): the draft and
      `check-hermas-batch` ask for a `[chapter]` line only in books of more than one chapter
      (`chapters_in`). Where Lake prints a numeral the OCR missed (Mandate 6 "I", p. 94), the flag
      stays.
  * **After the mending**: 25 % of the 815 verse blocks flagged before the mark flags (44 % with
    them); Latin 25 % of 40 (27 % of 47 entries with headings). Above the brief's expected 10 %,
    under its 30 %: what remains is real reading work for the agents (57 verse numbers the OCR
    cannot confirm, 17 OCR words Tauber lacks, 6 chapter numerals missed, titles read badly, and
    the word readings), not a fault in the layout.
  * Batch 1 read against pages 6-14: the titles (ΠΟΙΜΗΝ, then Tauber's chapters as Roman numerals),
    ¶ at each chapter, `1.1.3+` continuations, marks at First1K's places, the margin references
    pre-filled by verse (Ps. 2, 4; 123, 1 on p. 8). The apparatus sections are empty by design: the
    agents write them from the enlarged halves (INSTRUCTIONS step 3), and step 5 compares them with
    First1K's.

* **2026-11-08, step 4: the batches.** Each batch was checked by one agent (INSTRUCTIONS.md) and
  reviewed by a second that had not seen its reasoning (REVIEW.md), in five workflows of five
  batches; the checker was run on every file after each workflow and the work committed. Then the
  residual pass (RESIDUALS.md, eight agents over three batch files each).
  * **Totals**: 143 Greek pages with 207 apparatus items and 209 footnote marks (Lake prints ²
    twice on p. 30, at both ἓξ of Vis. 3.2.5, and ¹ twice on p. 90, Mand. 5.2.1: one item answers
    each pair), 111 margin references; the Latin pages 5 items, 3 references. The same counts as
    First1K's notes (207) and `<bibl>` references (111).
  * **Rules settled on the way** (written into INSTRUCTIONS.md for the later batches, and the
    earlier batches brought into line):
    * A title is written as printed, with Lake's full stop, the numeral sign as ʹ (never ΄ or ');
      the merge's section label drops the stop (`title_label`). A footnote mark on a title (p. 68
      Ἀποκάλυψις εʹ.¹; p. 138 ΠΑΡΑΒΟΛΑΙ¹ ΑΣ ΕΛΑΛΗΣΕ ΜΕΤʼ ΕΜΟΥ, the general heading of the
      Similitudes) is counted by the checker and belongs to the book's first verse at the merge.
    * Margin ranges with an en dash ("I Cor. 7, 38–40"); references as printed ("Philipp 2, 2").
    * Sigla as printed: Pᵒˣʸ (Lake's "Poxy"; the Latin end once prints Pᵒˣ, kept), Pᴮᵉʳˡ ("Berl",
      capital B), numerals with a stroke over them with U+0305 (ε̅).
    * An apparatus item can run on to the foot of the facing English page (p. 130 → p. 131): read
      there, written whole on the Greek page. Two candidates in batches 1-10 looked at: complete.
    * Where the scan cuts off the right edge or blurs the foot, Google's scan of the same plates
      (`TheApostolicFathersV2`, n = page + 14) was used and cited in notes (pp. 194-198, 248, 254).
  * **The checker** now also reports accent differences from Tauber (`_accented`): Lake's
    accent misprints are visible as remarks, "(noted)". It compares a verse divided between two
    files only in part, the Latin word by word, leaves the keraia of numerals and Lake's dots of
    omission alone. 25 remarks remain over the 25 files, every one a misprint of Lake's noted on
    the page (μενανοίας 2.2.5, βασανισθωσιν 3.7.6, αλλὰ 3.12.2, φυχῇ 13.1.10, και 16.1.8, θίψεσι
    24.1.4, ῥάβδοὺς 25.2.2, πράξέις 25.9.3, σφαγῖδα 26.16.5, κακια 26.29.1, καί 22.5.4 …) or the
    doubled marks of p. 30.
  * **The residual pass** (`hermas-residuals`; the ξ/ζ fold had to be applied to the OCR side as
    well, which took the items from 1084 to 628): every item but one agreed with the print
    (raised stops read as ":" or "ʼ", specks, divided words, accents misread); the change is the
    acute καί at Sim. 5.5.4 (22.5.4), noted as a misprint.
  * **For step 5** (noted on the pages, not decided): the misprints above and the notes of the
    other words printed without an accent (δυναται, δε, ἀπο, ἡμερα, ἁμαρτιας, κυκλῳ, αὐτων …),
    which may be worn type rather than misprints; "AFL₁" (p. 288) and "L₂F" (p. 24) where Lake's
    list of sigla has no F; "Acts 2, 1" on p. 304 (Acts 2, 11 on p. 300 for the same words);
    Εντολὴ γʹ. without a breathing (p. 74); παῆναι 1.3.3, ἀκοκριθεῖσαι 26.11.2, τῆν 26.12.5,
    παρθένον 26.11.7 printed so and in Tauber; the stop after Διατί οὖν 20.1.2 (comma or ;?).

* **2026-11-08, step 5: the merge and the checks.** `merge-hermas` wrote `texts/hermas/` (grc.txt
  693 verses 1.1.1-26.30.2 in order, 107 paragraphs; commentary-lake-apparatus.md; tokens.tsv;
  aliases.tsv; eng-lake.txt; commentary-lake.md; appendix.md, read at step 8). Its import of the
  lexica had the wrong module (`build.load_lexica`, not `nt`): mended.
  * **(a) Against Tauber**: every verse once and in order; four verses still differ in wording,
    all misprints that Tauber keeps as printed and this edition corrects (ἀσύμποφα 11.2.6,
    μενανοήσωσι 25.6.3, ἀκοκριθεῖσαι 26.11.2, παρθένον 26.11.7).
  * **(b) The apparatus against First1K's**: 19 differences before the misprint notes, each settled
    (I read the doubtful ones on the page myself rather than sending them to an agent; they were
    few): First1K's own slips ("nos" for Lake's "now" at Mand. 11.1.18, read on p. 124; "sith",
    "#3" for q, a truncated item at Mand. 12.4.1, sigla written flat, PBerl, Poxy, PAmh); First1K
    repeats a note at Lake's doubled marks (Vis. 3.2.5, Mand. 5.2.1); the notes on titles, which
    First1K's text lacks (Vis. 5, the Similitudes' heading); Lake's misprinted mark ² for ¹ at
    Sim. 5.6.1, which First1K followed and the agents placed by content; Funk's "καὶ [παθεῖν οὐ]
    φοβοῦνται" at Sim. 8.10.4, brackets printed (p. 214, the last line, left half). Lake prints
    the Amherst papyrus "Pam" (p. 12) and "PAmh" (p. 220): both kept as printed.
  * **(c) Tauber's comparison notes**: 2.2.5, 3.7.6 corrected as misprints; 3.6.1 πονηρίας, 3.8.5
    εἰσίν., 9.3.7 αὐτῷ· (Google's scan), 25.3.2-3, 26.11.9 ὅλως (Google's scan), 26.29.4 τὸ were
    settled on the page at step 4; 27.3.5 Lake's dots as printed. The titles of Mandate 6,
    Similitudes 6 and 9 (11.0.0, 23.0.0, 26.0.0), where Tauber's scan shows a stop: neither our
    scan nor Google's of the same plates prints one (looked at enlarged): written without.
  * **Misprints** (`MISPRINTS`, whole words, several per verse; `TITLE_MISPRINTS`): the 28 the
    agents found and noted on the page are corrected in grc.txt with a note in the apparatus ("καὶ:
    Lake prints κα, a misprint; corrected in this edition."), and the title Εντολὴ γʹ. (Mand. 3)
    has its breathing back (note on 8.1.1). Lake's misprints inside his own apparatus notes
    (μετανοήσοὐσιν, θεῖαν, πρυφητικοῦ, ἐθελυδιδάσκαλοι, ἀμαρτίας with a smooth breathing, the
    siglum F in "AFL₁" and "L₂F") stay as printed: they are his commentary. παῆναι 1.3.3 is the
    late aorist of παύω, not a misprint.
  * **Misprints in the apparatus** (2026-11-09, the author's answer): μετανοήσοὐσιν (1.3.2),
    ἀμαρτίας (3.1.5), θεῖαν (16.1.8), πρυφητικοῦ (16.1.9), ἐθελυδιδάσκαλοι (26.22.2) are corrected
    in the items, each followed by "X (in the note above): Lake prints Y, a misprint; corrected in
    this edition." (`APPARATUS_MISPRINTS`, `correct_apparatus_misprints`). The First1K comparison
    still runs on the items as printed (the merge log unchanged). F in "L₂F" (p. 24) and "AFL₁"
    (p. 288) is a clear, unworn F on both pages: kept, sigla.md says so. τοῦ προφητοῦ A (16.1.9)
    is A's reading as reported, not touched.
  * **(d) The review list**: the numerals with a keraia (ρʹ, λʹ, κεʹ, λεʹ, μʹ: 27 in the text) were
    split by the tokenizer into a letter (μ analysed as ἐγώ) and a lone ʹ. `greek._TOKEN` now
    keeps U+02B9 at the end of a word (no other text has one), so they align with GLAUx, which
    has them whole: 0 tokens without a lemma (14 before). The list is left with the four corrected
    misprints, whose analyses fit the corrected words (παρθένων n-p---fg-).
  * `check`: 0 errors; for hermas 77 lemmas no dictionary has (134 tokens): step 9.
  * **Ten verses compared with the page by eye** (1.1.4, 2.3.4, 6.1.2, 9.2.1, 16.1.8, 20.1.2,
    22.1.1, 25.6.4, 26.11.2, 26.16.5): all as printed, the corrected misprints apart; the comma
    after Διατί οὖν (20.1.2) looked at again: a comma with a speck above, kept.

* **2026-11-08, step 6: the notes.**
  * **Lake's notes** (`commentary-lake.md`, written by the merge from the Perseus translation):
    234 verses with his side-headings (italic), his 58 footnotes and the margin references of the
    Greek pages. The Greek in his notes looked over for impossible accents: one slip of the Perseus
    file, ἀνεγνωρισἀμην, read on his p. 7 (leaf 19) as ἀνεγνωρισάμην and corrected
    (`PERSEUS_FIXES`).
  * **Taylor's notes**: `drama-prose hermas notes` drafted 231 pages (Taylor I leaves 61-168,
    Taylor II 13-135) into 29 batches of eight; each checked by one agent (INSTRUCTIONS-prose.md,
    the Taylor section) and reviewed by a second (drama REVIEW.md, the prose section), five batches
    to a workflow; the prose checker run on every file (0 remarks on all 29); committed after each
    workflow. The merge (`taylor_notes_and_introduction`, tried first on batches 1-5) placed every
    note: `commentary-taylor.md`, 174 notes under 173 verses; the 6 on the Latin end (after
    26.30.2) go to the appendix with the Latin.
  * **Rules settled on the way** (in the Taylor section of INSTRUCTIONS-prose.md): Taylor's
    printing slips, a wrong or dropped letter that makes no word ("Gosbels", "he Gospel", *Mana.*)
    or a footnote ending in a printed comma with nothing after it (worn type), are corrected with a
    line under notes; anything that could be his own spelling or wording stays as printed (the
    reference "Gen. xxviii. 1" for verse 11, "vi. i. 4", "conj", "*Mand*" without its stop). Where
    Taylor prints no verse number before a mark, the heading is the traditional verse the mark
    stands in (Mandate 10.1.2). Both forms of a heading for a book of one chapter (`Mandate 7.1.4`,
    `Mandate 7.4`) are read alike by the merge.

* **2026-11-08, step 8: the appendix.** The merge writes `appendix.md` from `batch-latin.md` (the
  Latin pages, checked and reviewed with the Greek at step 4): a short preface (A breaks off after
  Sim. 9.30.2; Lake's L₁ with the Greek of the papyri), then Similitude 9.30.3 to 10.4.5, 34
  sections in order, each with Lake's translation beneath it (Perseus), Lake's five apparatus items
  ("Apparatus: …") where their marks stand, and at the foot "Taylor's notes on the Latin end" (6,
  from step 6). Read through: the Perseus translation has a garbled quotation mark at Sim. 9.31.2
  ("needs must€ enter"); his p. 293 (leaf 305) prints "needs must ‘enter into the kingdom of
  God’;": corrected (`PERSEUS_FIXES`, now applied to the translation as well as the notes; no
  other stray character in the Perseus text). Sim. 10.4.3-5 compared with p. 304 by eye: word for
  word.

* **2026-11-08, step 7: the introductions.** `intro-01.md` (Lake, pp. 2-5) ran with the last notes
  batches; `intro-02` to `intro-06` (Taylor I, pp. 9-52) in one workflow; `intro-07` (the end of
  Taylor's introduction and his appendix, Taylor II pp. 135-139) alone; each checked and reviewed,
  the prose checker 0 remarks on all. Settled on the way: Taylor's chapters `##`, his lettered parts
  `###` in every batch; verse he quotes (Shakespeare) kept in its paragraph with ` | ` between the
  lines, the source last; a line the draft lost under a library stamp (p. 53) restored from the
  page; his slips as in step 6 ("he may chose" stays: a real word). The merge writes
  `introduction.md`: "Lake's introduction (1913)", "Taylor's introduction (1903)" (1. Authorship
  and Date … 5. The Doctrine of Hermas, with A.-C. parts), "Taylor: Hermas and the Gospels
  (1906)" ending with his signature.
* **2026-11-08, step 9: the reference files.**
  * **Lemmas.** The merge log listed 73 lemmas no dictionary has. Most were GLAUx's garbled
    lemmas (γιρρήσγω for ἀπερρηγὼς, πίλσκω for ἔλθη, λογίσανταμαι, πηρωτωᾴ …) or names given to the
    wrong word (Ἑρμῆς the god for Ἑρμᾶ, Κώμη for Κώμας, Γραπτεύς, Κάλος for Κάλει): corrected in
    `LEMMA_FIXES["hermas"]`, 47 entries with ἰάζω → ἰάομαι (ἰάσεται), ἀείρω → αἴρω (ἦραν, ἆρον: the Koine
    headword), πυρίνη → πύρινος. Five tokens by hand (`HAND_ANALYSES["hermas"]`): κʹ at Sim. 9.5.4
    (GLAUx: ἄν), the names Γραπτὴ and Ἁπλότης (Sim. 9.15.2, a maiden's name), and two tags
    (συμφυρμοὺς, διχοστάταις are nouns). Found on the way: Lake prints "μετα-|νήσατε" at Sim. 9.23.5,
    the ο lost at the line's end (looked at on p. 276): a 29th misprint, in `MISPRINTS` (Tauber
    keeps it).
  * **Glossary and short definitions**: `glossary.md`, 43 names (persons, places, angels, and the
    virtues and vices the text uses as names: the seven women of Vis. 3.8, the maidens and the women
    in black of Sim. 9.15), and `shortdefs.tsv`, the 31 words no dictionary has (διψυχέω, ὀξυχολία,
    συμψέλιον, πολυσπλαγχνία …) and the numerals: each written by one agent from the words' use in
    the text, Lake's English and Taylor's and Lake's notes (no copyrighted lexicon), and reviewed by
    a second, who corrected seven glossary entries and four definitions. Then by hand the 35 lemmas
    that Logeion's list lacks (διατί, διψυχία, ἱστάνω, ποτέ …, and short glosses of the names):
    `check` now finds a short definition for every lemma (1792/1792).
  * **Aliases** (`aliases.tsv`, 24): the other spellings found by `resolve_lemmas`, and the Koine
    headwords of Abbott-Smith (`KOINE` extended: σῴζω → σώζω, θλῖψις → θλίψις, ἀμφότερος →
    ἀμφότεροι, ἐλαχύς → ἐλάχιστος). Abbott-Smith lacks some common words (ἄν, δεύτερος, ἁπλότης
    as transcribed): LSJ and Middle Liddell have them.
  * **Homographs**: the text's lemmas in Logeion's homograph groups not yet classified were three:
    ἀκακία (both nouns: n, n; the word sheet lists both, marks none, as ὥρα), εὐθαλής (a; "[Dor.]"
    -), and ἰάζω, which was GLAUx's wrong lemma for ἰάσεται (now ἰάομαι). Two groups added to
    `homographs.tsv`.
  * **Perseus**: "Hennas the temperate" (Vis. 1.2.4) corrected to "Hermas" (`PERSEUS_FIXES`).
  * `sigla.md` from Lake's list of witnesses (pp. 3-5, `intro-01`) and what his apparatus uses
    (the hands of ℵ, Pᵃᵐ/Pᴬᵐʰ, Pᵒˣʸ/Pᵒˣ, Pᴮᵉʳˡ, E₁ and the unexplained F, the Fathers, the signs),
    each place it cites looked up; `about.md` (product hermas_shepherd_lake, google_play yes);
    the section in texts/README.md and the row in play/README.md.

* **2026-11-08, step 10: build and the emulator check.** `build --only hermas` (693 lines, 27,138
  tokens, 1770 lemmas, every one with a short definition; 43 glossary entries; the introduction,
  the appendix and the sigla as documents), `check` 0 errors; the asset pack `app/packs/hermas`
  (from truestory's) in settings.gradle.kts and androidApp/build.gradle.kts; `catalog`, 18 texts.
  The longest verse is 622 characters (the True Story's lines run to 723 after its split and fit a
  phone page), so no verse is divided. RAM looked at first (13 GB free, no emulator running); the
  bundle built with no emulator up, Gradle stopped, then one emulator (`anagnosis`), bundletool
  local testing. Checked on the phone: bought in the debug shop ("Owned", downloaded), opened;
  the book chooser lists 26 books (the Greek ends in Similitude 9; Similitude 10 is in the
  appendix, so 26, not the brief's 27), each with Lake's title; a chapter read (verse numbers
  inline, "Chapter 1 · 29" in Mandate 4 with the continuous number); the citation "Vision
  1.1.1–3", "Mandate 4.1.1–4" at the bottom, "Vision 1.1.3" over notes and syntax; the apparatus
  and its Manuscripts page; Lake's side-heading and Taylor's note under Vision 1.1.3, each headed
  with its commentator; the introduction (Lake, Taylor's five chapters, his 1906 appendix) and the
  appendix (Similitude 9.30.3-10.4.5) under "About this edition"; the word sheet of πορευομένου
  (GLAUx lemma πορεύω; Abbott-Smith's πορεύομαι reached through the alias; Koine pronunciation);
  the syntax of Vision 1.1.3 (marked automatic); reading aloud from a tapped word (Koine voice,
  the word lit; the sound itself not heard on the emulator). One fix: Logeion's short definition
  of πορεύω is the active's ("to make to go, carry"); the Shepherd has only the middle:
  `shortdefs.tsv` now gives "(mid.) go, journey, proceed …". The emulator closed (`adb emu kill`),
  `./gradlew --stop`.

## Sizes, for planning

The Shepherd: 27,340 Greek words in 695 verses (Tauber; GLAUx 27,570 word tokens), on about 150
Greek pages of the Loeb (leaves 15–303 odd), with about 326 apparatus items (First1K's count);
the Latin end 1,250 words on 5 pages. Lake's introduction 4 pages, his notes 171 (digital).
Taylor: about 230 pages of translation with footnotes (one to three a page: perhaps 400 notes)
and about 50 pages of introduction. Against the True Story (80 pages, 1,660 items, one day of
agent batches): twice the pages but a fifth of the apparatus and a check text of the same
edition; expect two days, the second mostly Taylor.
