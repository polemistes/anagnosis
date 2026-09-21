# Texts

Everything under `texts/` is the source of truth for the reading data. Edit these files by
hand; then run the pipeline to rebuild the SQLite bundle:

    cd pipeline
    .venv/bin/python -m anagnosis_pipeline check     # validate
    .venv/bin/python -m anagnosis_pipeline build     # write data/antigone.sqlite

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
    <n><TAB>text            a line of text; n = line number, digits plus optional letter (161b)

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
