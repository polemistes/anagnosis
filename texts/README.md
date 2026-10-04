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

* Greek text: Perseus Digital Library, `urn:cts:greekLit:tlg0011.tlg002.perseus-grc2`
  (Storr's Loeb text, 1912). CC BY-SA 4.0.
* Lemmas and morphology: Ancient Greek Dependency Treebank 2.1 (Perseus). CC BY-SA 3.0 US.
* Translation: R. C. Jebb (1891), Perseus `perseus-eng2`, modernized by Perseus. CC BY-SA 4.0.
* Commentary: R. C. Jebb, *Sophocles: The Plays and Fragments, part III* (1900), Perseus. CC BY-SA 3.0 US.
* Lexica: LSJ (1940) and Middle Liddell (1889), Perseus. CC BY-SA 4.0 / 3.0 US.
* Short definitions: Logeion (Helma Dik, University of Chicago), based on Perseus. Credit requested; no formal licence stated.

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
  (ἀποκρίνομαι to ἀποκρίνω, γινώσκω to γιγνώσκω); `glossary.md` holds J. J. Dodson's entries
  (*A Lexicon of the Greek New Testament*, CC0, by Strong's number) for the names and words LSJ
  and Middle Liddell lack, and `shortdefs.tsv` his short glosses where Logeion has none.
* Translation (`eng-bsb.txt`): the Berean Standard Bible (public domain since 2023), a paragraph
  wherever the Greek begins one. Its verse numbers are mapped to the SBL text's where they differ
  (Acts 19:41, 2 Corinthians 13:13-14); the doxology of Romans 16:25-27, which the SBL text
  leaves out, is in brackets.

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
