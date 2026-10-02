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
                            or book.line for an epic (1.12, 1.93a)

The line number and the text are separated by a single TAB. Line numbers must be unique
and increasing. In translations, `<n>` is the first Greek line the paragraph corresponds to,
and the paragraph runs until the next paragraph begins.

Editorial marks in the Greek: `⟨…⟩` for editorial additions, `[…]` for deletions.
Elision is written with U+02BC MODIFIER LETTER APOSTROPHE (ʼ), never a straight quote.

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
