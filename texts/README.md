# Texts

Everything under `texts/` is the source of truth for the reading data. Edit these files by
hand; then run the pipeline to rebuild the SQLite bundle:

    cd pipeline
    .venv/bin/python -m anagnosis_pipeline check     # validate
    .venv/bin/python -m anagnosis_pipeline build     # write data/lexicon.sqlite and data/antigone.sqlite

The pipeline's `import` command regenerates these files from the upstream Perseus sources
and **overwrites hand edits**. Run it only when you want to resync with upstream, and diff the
result with git before committing.

## Layout

    texts/<work>/
        grc.txt               the Greek text
        tokens.tsv            one row per word of grc.txt: lemma and morphology
        <lang>-<name>.txt     a translation, e.g. eng-jebb.txt
        commentary-<name>.md  a commentary

## Text files (`grc.txt`, translations)

    # key: value            header (title, author, translator, lang, source, edition, license)
    // comment              ignored
    == kind [label]         section; more '=' for deeper nesting (== choral / === strophe 1)
    @ Speaker               speaker change
    !<TAB>text              stage direction
    <n><TAB>text            a line of text; n = line number, digits plus optional letter (161b),
                            book.line for an epic (1.12, 1.93a), Stephanus page, section
                            and line for Plato (172a1), or book.chapter.verse for the New
                            Testament (1.5.3; books 1-27 in the canonical order; a verse that
                            a paragraph divides goes on as 1.5.3b)

The line number and the text are separated by a single TAB. Line numbers must be unique
and increasing. In translations, `<n>` is the first Greek line the paragraph corresponds to,
and the paragraph runs until the next paragraph begins.

Editorial marks in the Greek: `⟨…⟩` for editorial additions, `[…]` for deletions.
Elision is written with U+02BC MODIFIER LETTER APOSTROPHE (ʼ), never a straight quote.

Prose (a header `# layout: prose`) is shown as running paragraphs: `@ ` with no name begins a
paragraph, a speaker's name printed in the text is written in braces where it stands
(`{ΑΠΟΛ.} Δοκῶ μοι`), and a line of verse quoted in the prose begins with `| `. With
`# syntax: automatic` the syntax view says that the analysis is a parser's, not checked by hand.

## `tokens.tsv`

Tab-separated with a header row: `line ord form lemma postag relation head sentence word_id`.

* `line`, `ord`: the line number and the 0-based index of the word within that line.
* `form`: the word exactly as it stands in `grc.txt` (punctuation is not a token).
* `lemma`: the dictionary headword. Must match a Liddell-Scott headword (accents included)
  to give the reader a definition. `check` reports lemmas that do not match.
* `postag`: the nine-position Perseus treebank tag
  (part of speech, person, number, tense, mood, voice, gender, case, degree), e.g.
  `v3spia---` = verb, 3rd, singular, present, indicative, active.
* `relation`, `head`, `sentence`, `word_id`: syntactic annotation from the treebank; optional.

If you change the words of a line in `grc.txt`, update the matching rows here. `check`
fails when the words of a line and its token rows disagree.

## `syntax-nodes.tsv`

The treebank's tokens that are not words of the text but take part in the syntax: the
punctuation (a comma often heads a coordination) and the artificial nodes that stand for an
omitted word (an elided verb, written `[0]`). Together with the `relation`, `head`, `sentence`
and `word_id` columns of `tokens.tsv` they make up the dependency tree of each sentence,
which the app shows when a word is pressed and held.

Tab-separated with a header row: `sentence word_id form lemma postag relation head artificial`.
`head` refers to a `word_id` within the sentence, `0` being the root; `artificial` is `1` for
an omitted word. The file is written by `import` and, on its own, by `import-syntax`, which
touches no other file. `check` warns about heads that point at no word of their sentence.

## Commentary files

    # key: value          header (title, author, lang, source, license)

    ## 12                 a note on line 12 (or `## 12-14` for a range)
    **lemma** note text in Markdown. Blank line = new paragraph.

Markdown subset: `**bold**`, `*italic*`, `[503](#503)` for a cross-reference to the note on
line 503. Everything else is plain text.

## Sources and licences

* Greek text: R. C. Jebb's text (*The Antigone of Sophocles*, 1891), Perseus Digital Library,
  `soph.ant_gk.xml`. CC BY-SA 3.0 US.
* Lemmas and morphology: Ancient Greek Dependency Treebank 2.1 (Perseus). CC BY-SA 3.0 US.
* Translation: R. C. Jebb (1891), Perseus `perseus-eng2`, modernized by Perseus. CC BY-SA 4.0.
* Commentary: R. C. Jebb, *Sophocles: The Plays and Fragments, part III* (1900), Perseus. CC BY-SA 3.0 US.
* Lexica: LSJ (1940) and Middle Liddell (1889), Perseus. CC BY-SA 4.0 / 3.0 US.
* The reader's other dictionaries, shared by all texts (data/lexicon.sqlite), each with a
  switch in Options: Abbott-Smith's *Manual Greek Lexicon of the New Testament* (1922; see the
  New Testament below), and G. Autenrieth's *Homeric Dictionary* (tr. R. P. Keep, rev. I. Flagg,
  1891), transcribed page by page from the Internet Archive scan `homericdictiona00aute`
  (public domain; the transcription CC BY-SA 4.0). The transcription and its brief are in
  `pipeline/transcriptions/autenrieth/`; `build` reads it. Where a text that names Autenrieth in
  its `# dictionaries:` header spells a lemma otherwise than Autenrieth (accents, breathing, a
  movable nu, a people in the plural, Attic for Homeric spelling: θύρα θύρη, ξένος ξεῖνος), `build`
  files the entry under the text's spelling too; a short list checked by hand (`BY_HAND` in
  `autenrieth.py`) adds the rest (τις τὶς, Ποσειδῶν Ποσειδάων). 94.5% of the Odyssey's lemmas,
  99.4% of its words, find an Autenrieth entry; the rest are words this printing of 1891 lacks.
* Short definitions: Logeion (Helma Dik, University of Chicago), based on Perseus. Credit requested; no formal licence stated.

## `dictionary-<slug>.md` (optional)

A dictionary only this text carries, in the format of `glossary.md`: each entry under its
lemma, offered on the word sheet as a button of its own (the New Testament's Dodson).

## `glossary.md` (optional)

Hand-written dictionary entries for words the lexica lack, typically proper names:

    ## Ἀντιγόνη
    **Ἀντιγόνη, ἡ** Antigone, daughter of Oedipus ...

The heading is the lemma exactly as it appears in `tokens.tsv`; the body is Markdown.

## `shortdefs.tsv` (optional)

One-line glosses shown first in the word popup. The bundle takes them from Logeion's short
definitions (Helma Dik, University of Chicago; based on the Perseus short definitions,
https://github.com/helmadik/shortdefs); this file adds glosses for lemmas Logeion lacks or
overrides Logeion's. Format: `lemma<TAB>definition`, `#` starts a comment. `check` lists the
lemmas still without a gloss.

**Homographs.** Where Logeion lists words spelled alike (μήν "now verily", μήν2 "month"; its
placeholders "[lexical cite]" left out), the word sheet shows all of them, numbered, and marks
the one a word is when the annotation tells: the build gives such a token's lemma the homograph's
number in that list (μήν2; the app shows the lemma without it). What tells: a Logeion number on
the lemma in `tokens.tsv` (the New Testament's, set by `import-nt` from MACULA's Strong's numbers),
or the word's part-of-speech tag where it fits exactly one homograph. Each homograph's tag letters
and Strong's numbers are in `pipeline/homographs.tsv` (the 296 groups that occur in the texts;
written and reviewed 2026-11-08); where two homographs share a part of speech, nothing is marked.
A capitalised name keeps its own definition apart from the common word (Ὅμηρος "Homer", ὅμηρος
"hostage").

## `commentary-jebb-apparatus.md`

Jebb's critical notes (textual apparatus), transcribed from the Internet Archive scan of the
1891 second edition (`sophocles03soph`, PDF pages 76–308). It uses the commentary format
above; the lemma and any manuscript readings Jebb prints in bold are `**bold**`, and the
line number in the heading is the first number of Jebb's label ("4 ff." becomes `## 4`).
The transcription was made page by page from the images and can contain reading errors;
corrections are welcome. To check that quoted words sit near their line:

    .venv/bin/python -m anagnosis_pipeline verify-apparatus

Entries it lists are usually lists of conjectures (words that by design are not in the text);
a `NOLINE` or `ORDER` line points to a wrong line number.

### "f." and "ff." marks

Jebb labels many notes "4 ff." or "5 f.". Perseus dropped these, so the pipeline restores them
from the OCR text of the 1891 scan (`pipeline/sources/scans/sophocles03soph_djvu.txt`): a
heading `## 4` becomes `## 4 ff.` when an OCR paragraph starts with that label and the same
Greek word. Headings may carry a range, a mark, or neither: `## 4`, `## 4-6`, `## 4 ff.`.
Marks the OCR missed can be added by hand.

## `aliases.tsv` (optional)

Lemmas the dictionaries list under another headword, mostly Homeric forms:
`lemma<TAB>headword`, e.g. `ἠέλιος	ἥλιος`. The word popup then shows the headword's entries and
short definition. `check` counts aliased lemmas as covered.

## Sophocles' other plays (`texts/ajax/`, `electra/`, `oedipustyrannus/`, `oedipuscoloneus/`, `philoctetes/`, `trachiniae/`)

Like the Antigone, each play is R. C. Jebb's (*Sophocles: The Plays and Fragments*, Cambridge),
made by `import-sophocles` from Perseus (`pipeline/anagnosis_pipeline/sophocles.py`, where
`PLAYS` gives each play's volume and sources); edit the importer and the transcriptions, not the
files here.

* Greek text: Jebb's text from Perseus (`soph.<play>_gk.xml`), CC BY-SA 3.0 US, checked page by
  page against the Internet Archive scans of Jebb's volumes (`SCANS` in `sophocles_pages.py`):
  the transcription batches in `pipeline/transcriptions/sophocles/<play>/` record Jebb's printed
  line numbers and every difference between the print and the Perseus text, and
  `import-sophocles` applies them. For the Oedipus Tyrannus Perseus has the 1887 text, but the
  only scan is of the third edition (1893); the text follows the scan. A verse that two or more
  speakers share has its later parts lettered (591, 591a); the reader sets them staggered, as
  printed.
* Lemmas, morphology and syntax: the Ancient Greek Dependency Treebank (Ajax, Electra, Oedipus
  Tyrannus, Trachiniae), CC BY-SA 3.0 US; GLAUx (Oedipus at Colonus, Philoctetes), automatic
  and marked `# syntax: automatic`. Where Jebb's words differ from the treebank's, the lemma and
  parse come from the analyser, listed in `pipeline/build/<play>-review.tsv` for checking.
* Translation (`eng-jebb.txt`): Jebb's, Perseus `perseus-eng2` (Trachiniae `perseus-eng3`),
  modernized by Perseus. CC BY-SA 4.0.
* Commentary and introduction: Jebb's, from Perseus, CC BY-SA 3.0 US. Perseus lacks the
  introduction to the Oedipus Tyrannus and both the introduction and the commentary of the
  Philoctetes: these are transcribed whole from the scans (Jebb's Introduction, the manuscripts
  chapter, the arguments, persons and structure; for the Philoctetes also his whole commentary,
  read by the prose OCR route from the two columns under the rule of every page,
  `notes-NN.md`, and written as `commentary-jebb.md` by `sophocles-prose`), CC BY-SA 4.0.
  Perseus's Oedipus Tyrannus commentary is of the second edition (1887): `sophocles-prose`
  files a note whose number the third edition's verses lack at
  the verse that holds its lemma. Perseus's Oedipus at Colonus (commentary, introduction and
  translation) is of the second edition (1889), the edition of the scan; where its commentary
  differs from the page (a lost range in a heading, a garbled letter) `sophocles.py` puts it right
  (`range_headings`, `COMMENTARY_FIXES`), and where its English counts verses otherwise than the
  print, `TRANSLATION_NUMBERS` files the segments by Jebb's verses.
* Critical apparatus (`commentary-jebb-apparatus.md`): transcribed from the scans with the text
  check, brief in `pipeline/transcriptions/sophocles/INSTRUCTIONS.md`, checked with
  `check-sophocles-batch` and merged with `merge-sophocles-apparatus`. The differences are
  keyed to the play's frozen `reference-grc.txt` and placed by the words they quote.
* Lyric verses: a second pass (`LYRICS.md`, `lines-NN.md`, checked with
  `check-sophocles-lines`) divides the lyric passages as Jebb prints them and gives fixed
  points from his note headings, so that each verse carries Jebb's number; a long verse that
  covers several of the traditional numbers carries the first, and the reader shows a fifth
  number such a verse covers beside it, as Jebb does. A word Jebb divides between two verses
  (εὐδαί- | μων) is written whole at the end of the first, so that it can be looked up.
* Introduction chapters that Perseus lacks (Jebb's "Manuscripts, editions, etc." and the
  ancient argument, the persons and the structure of the play) are transcribed
  (`INTRODUCTION.md`, `introduction-NN.md`) and added after Perseus's chapters by
  `import-sophocles`; the Appendix (`APPENDIX.md`, `appendix-NN.md`) is merged into
  `appendix.md` by `merge-sophocles-appendix`.
* `glossary.md` (names the dictionaries lack) and `shortdefs.tsv` are written by hand; `sigla.md`
  gives Jebb's note on his symbols.
* Done so far: all six plays (Ajax, Electra, the Trachiniae, the Oedipus Tyrannus, the Oedipus
  at Colonus and the Philoctetes). The last four were made by the drama pipeline's route (`pipeline/PLAN-sophocles.md`: Tesseract
  OCR of the scan matched to Jebb's Perseus text, agents deciding the flagged places from the page,
  a residual pass and a review per batch; text and critical apparatus by `merge-drama <play>` from
  `pipeline/transcriptions/drama/<play>/`, the transcribed introduction and the Appendix by
  `sophocles-prose <play>`, which also makes the commentary and the translation again from Perseus
  and re-files them by the verses) rather than by the by-eye batches described above; the lyric
  numbering was settled against Jebb's margin and note numbers (`sophocles-numbering <play>` lists
  the suspects). The Oedipus at Colonus and the Philoctetes have GLAUx's automatic lemmas and
  syntax, not checked by hand (their `about.md` says so); the lemmas and parses the review list,
  a reading of the lemmas against their forms and `check` showed wrong are corrected in
  `drama_fixes.py` (`HAND_ANALYSES`, `LEMMA_FIXES`). Perseus's Philoctetes translation is of the
  second edition (1898), the scan's; `TRANSLATION_NUMBERS` files its segments by Jebb's verses.

## Aeschylus' Oresteia (`texts/agamemnon/`, `choephoroi/`, `eumenides/`)

Each play is Arthur Sidgwick's edition (*Aeschylus*, with introduction and notes, Oxford,
Clarendon Press: Agamemnon, third edition, revised, 1887; Choephoroi 1884; Eumenides 1887), read
from the Internet Archive scans of students' copies (`drama.PLAYS` gives each scan and its
leaves) and made by `merge-drama <play>` from the checked transcription in
`pipeline/transcriptions/drama/<play>/` (brief `pipeline/PLAN-drama.md`; the agents' briefs
`INSTRUCTIONS-text.md`, `RESIDUALS.md`, `INSTRUCTIONS-prose.md` in `pipeline/transcriptions/drama/`).
Edit the transcription and rerun the merge, not the files here. The editions are in the public
domain; the transcription is published under CC BY-SA 4.0.

* Greek text and critical apparatus (`grc.txt`, `commentary-sidgwick-apparatus.md`): Sidgwick's,
  read by OCR (Tesseract) and matched word by word to the Perseus text of H. W. Smyth (Loeb 1926),
  which is the check text only and does not ship; every line where the two disagreed, and then
  every word, stop and accent where Sidgwick's print and the checked text still differed, was
  settled against the page image. One file line per printed verse, as Sidgwick divides the lyrics;
  a verse takes the number of the Perseus line its first word stands in (a second verse in the same
  line a letter: 1426a), and the numbers printed in Sidgwick's margin win where they differ.
  Transposed verses keep their own numbers in the print's order (Agamemnon 1204 before 1203,
  1304 before 1303). Sidgwick's asterisk before a conjecture is left out (`sigla.md` explains it);
  his daggers stand. An apparatus item Sidgwick numbers by a verse our numbering lacks stands at
  the nearest earlier line with his number in brackets.
* Sections (episode, choral, strophe …) and speakers' names: from the Perseus TEI, placed by the
  words; the speakers are checked against the abbreviations Sidgwick prints.
* Lemmas, morphology and syntax (`tokens.tsv`, `syntax-nodes.tsv`): the Ancient Greek Dependency
  Treebank 2.1 (hand-made), CC BY-SA 3.0 US, aligned to Sidgwick's words; where he reads otherwise,
  the analyser, listed in `pipeline/build/<play>-review.tsv` and corrected by hand in
  `pipeline/anagnosis_pipeline/drama_fixes.py`. The treebank's Choephoroi stops at line 945: the
  last scene's words have the analyser's lemma and form and no syntax. In the Eumenides, Sidgwick's colometry
  and readings leave about 60 words without a treebank node (no syntax for those words).
* Translation (`eng-smyth.txt`): H. W. Smyth, Perseus `perseus-eng2`/`eng3`, modernized by
  Perseus, CC BY-SA 4.0, its line numbers mapped to Sidgwick's verses by the words of the Greek.
* Commentary (`commentary-sidgwick.md`) and introduction (`introduction.md`): Sidgwick's, read by
  OCR (English and Greek) and checked against the page images; a note Sidgwick numbers inside one
  of our longer lyric verses stands at the verse that holds its lemma. His lists of editions and
  translations and his appendices are left out. The Eumenides has no commentary: Sidgwick's notes are in a second
  volume (1887) of which the Internet Archive holds no scan; its introduction is volume I's.
* `sigla.md` (his manuscripts, signs and the editors he cites), `glossary.md` and `shortdefs.tsv`
  are written by hand.

## Aristophanes' Clouds (`texts/clouds/`)

W. J. M. Starkie's edition (*The Clouds of Aristophanes*, London, Macmillan, 1911), read from the
Internet Archive scan cloudsofaristoph00aris_0 and made by `merge-drama clouds` from the checked
transcription in `pipeline/transcriptions/drama/clouds/` (brief `pipeline/PLAN-drama.md`). The
edition is in the public domain; the transcription is published under CC BY-SA 4.0.

* Greek text and critical apparatus (`grc.txt`, `commentary-starkie-apparatus.md`): Starkie's,
  from the left-hand pages, read by OCR and matched word by word to the Perseus text (Hall and
  Geldart's Oxford text, the check text only); every disagreement, then every word, stop and
  accent where print and text still differed, settled against the page image, and each batch
  reviewed by a second agent. Starkie's numbering is followed where his margin numbers depart
  from the traditional ones; a verse too long for his line (a turnover) is one verse; a verse
  divided between speakers on two stepped lines has a letter for its second part (35a). His
  apparatus runs on to the facing page on 30 spreads; those items stand with their text page.
* Translation (`eng-starkie.txt`): Starkie's prose translation, from the right-hand pages,
  each speech placed at the Greek verse where it begins.
* Commentary (`commentary-starkie.md`) and introduction (`introduction.md`, with the Greek
  hypotheses): Starkie's, read by OCR and checked against the page images.
* Lemmas, morphology and syntax (`tokens.tsv`, `syntax-nodes.tsv`): GLAUx (automatic, CC BY-SA
  4.0) aligned to Starkie's words; where he reads otherwise, the analyser, listed in
  `pipeline/build/clouds-review.tsv` and corrected by hand in `drama_fixes.py`.
* `sigla.md`, `glossary.md` (names and comic words), `shortdefs.tsv` and `aliases.tsv` are
  written by hand.

## Hesiod's Theogony (`texts/theogony/`)

Alois Rzach's edition (*Hesiodi carmina*, Leipzig, Teubner, 1908), read from the Internet
Archive scan hesiodicarminare00hesi and made by `merge-drama theogony` from the checked
transcription in `pipeline/transcriptions/drama/theogony/` (brief `pipeline/PLAN-theogony.md`).
The editions are in the public domain; the transcription is published under CC BY-SA 4.0.

* Greek text and critical apparatus (`grc.txt`, `commentary-rzach-apparatus.md`): Rzach's, read
  by OCR and matched word by word to the Perseus text (Evelyn-White's Loeb text of 1914, the
  check text only); every disagreement, then every word, stop and accent where print and text
  still differed, settled against the page image. Rzach's own order is kept where he transposes
  verses (427 before 426, 434 before 430, 408 before 407, 631 before 630); the lines he brackets
  as interpolated keep their brackets. The Metis fragment that Perseus prints after 929
  (929a-929t, from Galen) is not in Rzach's text and is left out, with its translation.
* Translation (`eng-evelyn-white.txt`): H. G. Evelyn-White's (Loeb 1914, Perseus Digital
  Library, CC BY-SA 4.0), by line; his footnotes are left out.
* Commentary (`commentary-paley.md`) and introduction (`introduction.md`): F. A. Paley's (*The
  Epics of Hesiod*, 2nd ed., London, Whittaker, 1883; scan epicsofhesiodwit00hesiuoft): his
  notes on the Theogony, his preface to the volume and his "Epitome of the Theogony", read by
  OCR and checked against the page images. His own Greek text, his digamma readings and his
  manuscript readings printed above the notes are not used; his lemmas follow his text and may
  differ from Rzach's.
* Lemmas, morphology and syntax (`tokens.tsv`, `syntax-nodes.tsv`): the Ancient Greek Dependency
  Treebank 2.1 (annotated by hand, CC BY-SA 3.0 US) aligned to Rzach's words; where he reads
  otherwise, the analyser, listed in `pipeline/build/theogony-review.tsv` and corrected by hand
  in `drama_fixes.py`.
* `sigla.md`, `glossary.md` (the names of the catalogues), `shortdefs.tsv` and `aliases.tsv` are
  written by hand.

## Lucian's A True Story (`texts/truestory/`)

Nils Nilén's edition (*Lucianus*, vol. I fasc. I, libelli I–XIV, Leipzig, Teubner, 1906), read
from the Internet Archive scan bub_gb_RYepnZKT1OwC and made by `merge-lucian truestory` from the
checked transcription in `pipeline/transcriptions/lucian/truestory/` (brief
`pipeline/PLAN-true-story.md`, modules `lucian_pages.py`, `lucian_merge.py`). The editions are in
the public domain; the transcription is published under CC BY-SA 4.0.

* Greek text (`grc.txt`): Nilén's, read by OCR and matched word by word to the Perseus text
  (Harmon's Loeb of 1913, the check text only, never shipped); every disagreement, then every
  word, stop and accent where print and text still differed, settled against the page image.
  Prose, one line per section (`1.7`: book and section, Nilén's chapter numbers); a paragraph
  that Nilén begins inside a section continues the section on a lettered line (`2.47b`).
  Three misprints in Nilén's text are corrected (σκοκῶν, μεγέθος, ἐξώγρησαν at 1.18: `MISPRINTS`
  in `lucian_merge.py`; the batches keep the print), each with a note in the apparatus; his lacuna
  `***` (1.2) and his brackets ⟨ ⟩ and [ ] are kept. Read aloud in the Attic pronunciation.
* Critical apparatus (`commentary-nilen-apparatus.md`): Nilén's, in Latin, each item under the
  section that holds its lemma; the printed page-line number in front of each item is left out
  (it refers to Nilén's page). Checked: every positive item's lemma found in its section, and
  Harmon's 26 footnotes looked up on Nilén's page.
* Translation (`eng-harmon.txt`): A. M. Harmon's (Loeb 1913, Perseus Digital Library, CC BY-SA
  4.0), by section; his footnotes are left out.
* Commentary and introduction (`commentary-jerram.md`, `introduction.md`): C. S. Jerram's
  (*Luciani Vera Historia*, Oxford, Clarendon Press, 1879; scan lucianiverahisto00luci), read by
  OCR and checked against the page images. Jerram keys his notes by the lines of his own text
  (Weise's Tauchnitz text); his text pages were read and matched to the Greek to give each line
  its section, and each note goes under the section of the word its lemma names.
* Commentary (`commentary-dcc.md`): the notes of the Dickinson College Commentaries (Eric Casey,
  Evan Hayes, Stephen Nimis, 2023, CC BY-SA), from the site's pages (saved in
  `pipeline/sources/dcc/lucian-true/`); their vocabulary lists are left out. Their text is
  Harmon's.
* Lemmas, morphology and syntax (`tokens.tsv`, `syntax-nodes.tsv`): GLAUx 0062-012 (automatic,
  CC BY-SA 4.0) aligned to Nilén's words; where he reads otherwise, the analyser, listed in
  `pipeline/build/truestory-review.tsv` and corrected by hand in `drama_fixes.py`.
* `sigla.md` (from Nilén's praefatio), `glossary.md` (the names and Lucian's invented words),
  `shortdefs.tsv` and `aliases.tsv` are written by hand.

## The Shepherd of Hermas (`texts/hermas/`)

Kirsopp Lake's Loeb edition (*The Apostolic Fathers*, vol. II, London, Heinemann, 1913, the 1917
reprint), read from the Internet Archive scan apostolicfathers02lakeuoft and made by
`merge-hermas` from the checked transcription in `pipeline/transcriptions/hermas/` (brief
`pipeline/PLAN-hermas.md`, modules `hermas_text.py`, `lake_pages.py`, `lake_merge.py`). The
editions are in the public domain; the transcription is published under CC BY-SA 4.0.

* Greek text (`grc.txt`): Lake's, read by OCR and matched word by word to J. Tauber and S.
  Macdonald's digital text of this edition (the check text only); the flags, then every word,
  stop and accent where print and text still differed, settled against the page image and
  reviewed. Prose, one line per verse in the traditional numbering of 27 books (`9.1.2`; the app
  cites it "Mandate 4.1.2": `# citation: dotted`), each chapter headed by its number and the
  continuous chapter number (1-114); Lake's titles of the books as printed. 29 misprints in his
  text and one in a title are corrected (`MISPRINTS`, `TITLE_MISPRINTS` in `lake_merge.py`; the
  batches keep the print), each with a note in the apparatus; so are five inside his apparatus items
  (`APPARATUS_MISPRINTS`). The Greek ends at Similitude 9.30.2,
  where manuscript A breaks off. Read aloud in the Koine pronunciation.
* Critical apparatus (`commentary-lake-apparatus.md`): Lake's 207 items, each under the verse of
  its footnote mark (the marks are numbered by the page in the print and left out of the text);
  compared item by item with First1KGreek's digital apparatus of the same edition.
* Translation (`eng-lake.txt`): Lake's (Perseus Digital Library, CC BY-SA 4.0), by verse.
* Commentary (`commentary-lake.md`): Lake's side-headings and footnotes from the Perseus
  translation, and the Bible references in the margin of his Greek pages (transcribed).
* Commentary and introduction (`commentary-taylor.md`, `introduction.md`): Charles Taylor's notes
  to his translation (*The Shepherd of Hermas*, Early Church Classics, SPCK, vol. I 1903, vol. II
  1906; scans shepherdofhermas0000herm, shepherdofhermas02hermuoft), read by OCR and checked
  against the page images: only his footnotes, each under the verse of its mark; his introduction
  (vol. I) and his appendix "Hermas and the Gospels" (vol. II, 1906), after Lake's introduction.
* Appendix (`appendix.md`): the end of the book (Similitude 9.30.3-10.4.5) in the Latin version
  with the Greek of the papyri, as Lake prints it, with his translation, his apparatus and
  Taylor's notes on it.
* Lemmas, morphology and syntax (`tokens.tsv`, `syntax-nodes.tsv`): GLAUx 1419-001 (automatic,
  CC BY-SA 4.0) aligned to Lake's words; garbled lemmas corrected in `drama_fixes.py`
  (`LEMMA_FIXES["hermas"]`). The numerals keep their keraia (μʹ). Koine spellings lead to
  Abbott-Smith through `aliases.tsv`.
* `sigla.md` (from Lake's introduction and his apparatus), `glossary.md` (the names) and
  `shortdefs.tsv` (the words no dictionary has) are written by hand.

## The Odyssey (`texts/odyssey/`)

The Greek text is T. W. Allen's Oxford edition (*Homeri Opera* III–IV, 2nd ed., 1917 and 1919),
with his apparatus criticus in `commentary-allen-apparatus.md`, his preface in `preface.md` and
his list of witnesses in `sigla.md`. Allen's edition exists only in print, so it was transcribed
page by page from the Internet Archive scans; the transcription and its brief are in
`pipeline/transcriptions/odyssey/`, and `merge-odyssey` builds the files here from it. The
translation is A. T. Murray's (Loeb, 1919, from Perseus), the commentary that of Merry and
Riddell (books 1–12) and Monro (books 13–24), also from Perseus.

`tokens.tsv` comes from the Ancient Greek Dependency Treebank, which was made on the Perseus
text (Murray's). Where Allen reads differently the word keeps its place in the treebank's
sentence, and its lemma and parse come from the analyser; `merge-odyssey` lists those words in
`pipeline/build/odyssey-review.tsv` for checking by hand. Lines are numbered book.line.

The header line `# dictionaries: autenrieth ml lsj` of `grc.txt` puts Autenrieth's Homeric
Dictionary first on the word sheet.

## The Symposium (`texts/symposium/`)

The Greek text is John Burnet's Oxford edition (*Platonis Opera* II, 1901, printing of 1910 and
later), with his apparatus criticus in `commentary-burnet-apparatus.md` and his sigla in
`sigla.md`. Burnet's line numbers (172a1: Stephanus page, section, line within the section) and
his apparatus exist only in print, so the pages were transcribed from the Internet Archive scan
`platonisopera02platuoft` (with `operarecognovitb02platuoft`, the 1910 printing, for the
apparatus); the transcription and its brief are in `pipeline/transcriptions/symposium/`, checked
word for word against the Perseus text of Burnet, and `merge-symposium` builds the files here.

* Lemmas, morphology and syntax (`tokens.tsv`, `syntax-nodes.tsv`): GLAUx (Alek Keersmaekers,
  github.com/alekkeersmaekers/glaux), CC BY-SA 4.0. GLAUx is an automatic annotation (lemmas about
  99% right, morphology 97%, syntax about 80%); the app says so on the syntax page.
* Translation (`eng-jowett.txt`): B. Jowett, *The Dialogues of Plato*, 3rd ed. (1892), from the
  proofread Wikisource transcription. Jowett marks only the Stephanus pages; the sections within a
  page are placed at the sentence end nearest to where they fall in proportion to the Greek.
* Commentary (`commentary-bury.md`) and introduction (`introduction.md`): R. G. Bury, *The
  Symposium of Plato* (1909), Perseus, CC BY-SA 3.0 US. Each note stands at the line where its
  lemma is found in Burnet's text, or at its section's first line where Bury's text differs.

## The New Testament (`texts/newtestament/`)

Every file here is made by `import-nt` from the sources `fetch-nt` downloads; edit the importer
(`pipeline/anagnosis_pipeline/nt.py`), not the files.

* Text and apparatus (`grc.txt`, `commentary-sbl-apparatus.md`): *The Greek New Testament: SBL
  Edition*, ed. Michael W. Holmes (2010, github.com/LogosBible/SBLGNT, version 1.2), CC BY 4.0,
  © Society of Biblical Literature and Logos Bible Software. A line is a verse; the SBL
  paragraphs are kept, and a paragraph that begins inside a verse makes the rest of the verse a
  line of its own (1.1.6b). The signs with which the SBL text marks the places its apparatus
  discusses (⸀ ⸂ ⸃) are left out; each note stands at its verse. `sigla.md` explains the editions
  the apparatus cites.
* Lemmas, morphology and syntax (`tokens.tsv`, `syntax-nodes.tsv`): MACULA Greek (Clear Bible /
  Biblica, github.com/Clear-Bible/macula-greek), CC BY 4.0, whose words match the SBL text's one
  for one. MACULA's hand-checked syntax trees are nested word groups with roles; `nt_syntax.py`
  turns them into dependency trees in the style of the Perseus treebanks (a head word for every
  group, the Prague relations, a preposition or conjunction heading its phrase, a coordination
  headed by its conjunction or by the punctuation between its members, an artificial node
  "[0]" for an understood verb); the module's docstring states the rules. The sentence ids are
  MACULA's ids of each sentence's first word.
* Dictionaries: `aliases.tsv` sends New Testament lemmas to the LSJ headword they stand under
  (ἀποκρίνομαι to ἀποκρίνω, γινώσκω to γιγνώσκω); `dictionary-dodson.md` is J. J. Dodson's
  *A Lexicon of the Greek New Testament* (CC0) under the lemmas it is linked to by Strong's
  number, a dictionary that only the New Testament carries; `shortdefs.tsv` has his short
  glosses where Logeion has none or the word is not in LSJ. Abbott-Smith's *Manual Greek
  Lexicon of the New Testament* is one of the reader's shared dictionaries (data/lexicon.sqlite).
  The header line `# dictionaries:` of `grc.txt` gives the order of the word sheet's buttons.
* Translation (`eng-bsb.txt`): the Berean Standard Bible (public domain since 2023), a paragraph
  wherever the Greek begins one. Its verse numbers are mapped to the SBL text's where they differ
  (Acts 19:41, 2 Corinthians 13:13-14); the doxology of Romans 16:25-27, which the SBL text
  leaves out, is in brackets.

## The text's entry in the catalog (`about.md`)

`about.md` describes the text for the reader's catalog (`data/catalog.json`). Its body is a
longer description (not shown in the app at present); its `# key: value` headers give:

* `title_en`, `author_en`: the English title and author ("Antigone by Sophocles").
* `app_id`: the Google Play id of the text's own app (`no.anagnosis.antigone`), for a text
  also sold as an app of its own.
* `ref_edition`, `ref_translation`, `ref_commentary`: the books the edition, translation and
  commentary come from, shown on the text's own page. Equal references share one line ("Edition,
  translation and commentary: R. C. Jebb, ..."); an empty or missing one is left out.
* `editor`, `apparatus`, `translation`, `commentary`, `syntax`, `dictionaries`: short phrases for
  the list of available texts (left out when the text has none, e.g. the New Testament's commentary).
  `syntax` says whether the syntax is annotated by hand or machine-made.
* `syntax_source`, `syntax_license`: where the lemmas, morphology and syntax come from, for the
  text's About and credits.
* `google_play: yes`: the text is on sale in the reader: it has an asset pack (`app/packs/<slug>`,
  listed in app/settings.gradle.kts and the reader's `assetPacks`) and the shop offers it as the
  in-app product named by `product_id`, once that product is active in Play Console. Texts
  without it are not listed.
* `product_id`: the text's product id in Google Play: author, work and edition, in lower case
  with underscores (`sophocles_electra_jebb`, `homer_odyssey_allen`, `newtestament_sbl`). It can
  never be changed or reused once the product is created.

The catalog is bundled with the reader, so a change here reaches users with the reader's next
update. `catalog` rewrites the catalog without rebuilding any database; it also writes each
built text's `version`, by which the reader knows that a downloaded text is out of date.

## Other documents (`sigla.md`, `introduction.md`, `appendix.md`)

Any other `*.md` file in the work's folder (not `commentary-*.md`, `glossary.md` or `about.md`) becomes a
free-standing document in the bundle, with `# key: value` headers for title, source and
license. `sigla.md` lists the manuscripts and symbols of the critical notes; the app shows it
from the Manuscripts button of the Apparatus view.

## Inflected forms (the analyser)

`data/lexicon.sqlite` also holds a `forms` table: the analyses of every word form of the open
Perseus Greek corpus (canonical-greekLit, CC BY-SA 4.0), made by running Morpheus
(perseids-tools/morpheus, Mozilla Public License 2.0, built in `pipeline/sources/morpheus`)
with `build-morpheus-forms`, together with the analyses in the Perseus treebanks
(`pipeline/sources/treebanks/`). Forms are keyed without diacritics; treebank analyses are
listed first. Where a form has an analysis valid in Attic, Epic or Ionic, its analyses valid only
in other dialects are left out. `fetch` downloads the corpus and Morpheus.
