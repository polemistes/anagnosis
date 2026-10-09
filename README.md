# Anagnosis

An ancient Greek reading app for Android. The app is free and works as a dictionary and
morphological analyser; texts are bought as separate apps.

Tap a word to see its dictionary entry and morphology, switch between the Greek and
translations, and consult commentaries. Everything works offline.

The reader is free on Google Play and the texts are sold there. Everything needed to build it yourself is in this repository,
free of charge: the code under the GPL (see LICENSE), the texts and data under CC BY-SA 4.0
(see DATA-LICENSE). The privacy policy is in PRIVACY.md.

## Repository layout

    texts/       the texts, translations, commentaries and word annotations, as editable plain files
    pipeline/    Python pipeline: fetches upstream sources, imports them into texts/, builds the SQLite bundle
    pipeline/transcriptions/   page-by-page transcriptions of printed editions (Allen's Odyssey, Burnet's Symposium)
                               and of Autenrieth's Homeric Dictionary
    data/        build output: the SQLite bundle shipped with the app (not committed)
    app/         the Android apps (Kotlin Multiplatform, Compose): the free reader (androidApp), which carries no text,
                 and one small paid app per text (antigoneApp, odysseyApp, symposiumApp, newTestamentApp, ajaxApp ...),
                 which hands its text to the reader

## Building the data bundle

    cd pipeline
    python3 -m venv .venv && .venv/bin/pip install -r requirements.txt
    .venv/bin/python -m anagnosis_pipeline fetch    # download upstream sources into pipeline/sources/
    .venv/bin/python -m anagnosis_pipeline import   # (re)generate texts/ from upstream; overwrites hand edits
    .venv/bin/python -m anagnosis_pipeline import-syntax  # regenerate only texts/antigone/syntax-nodes.tsv
    .venv/bin/python -m anagnosis_pipeline check    # validate texts/
    .venv/bin/python -m anagnosis_pipeline build    # write data/lexicon.sqlite (shared dictionaries) and data/<text>.sqlite
    .venv/bin/python -m anagnosis_pipeline build --only odyssey   # rebuild one text, keeping the lexicon

The Odyssey has commands of its own:

    .venv/bin/python -m anagnosis_pipeline import-odyssey         # texts/odyssey/ from Perseus and the treebank (Perseus text as a draft)
    .venv/bin/python -m anagnosis_pipeline prepare-odyssey-pages  # page images and drafts for transcribing Allen's edition
    .venv/bin/python -m anagnosis_pipeline merge-odyssey          # Allen's text and apparatus from the transcription; re-aligns the treebank

So has the Symposium:

    .venv/bin/python -m anagnosis_pipeline prepare-symposium-pages        # page images and drafts for transcribing Burnet's edition
    .venv/bin/python -m anagnosis_pipeline check-symposium-batch FILE...  # check transcription batches against the Perseus text
    .venv/bin/python -m anagnosis_pipeline merge-symposium                # texts/symposium/: Burnet's text and apparatus, GLAUx, Jowett, Bury

Autenrieth's Homeric Dictionary, one of the reader's dictionaries, is transcribed from a scan as well
(the brief is `pipeline/transcriptions/autenrieth/INSTRUCTIONS.md`; `build` reads the batches):

    .venv/bin/python -m anagnosis_pipeline prepare-autenrieth-pages        # page images and OCR drafts for transcribing it
    .venv/bin/python -m anagnosis_pipeline check-autenrieth-batch FILE...  # check transcription batches

The New Testament is imported, not transcribed:

    .venv/bin/python -m anagnosis_pipeline fetch-nt    # the SBLGNT, MACULA Greek, Dodson's lexicon and the Berean Standard Bible into pipeline/sources/nt/
    .venv/bin/python -m anagnosis_pipeline import-nt   # texts/newtestament/ from them

The word analyser's forms come from running Morpheus over the open Perseus corpus:

    .venv/bin/python -m anagnosis_pipeline build-morpheus-forms  # pipeline/build/morpheus-analyses.tsv.gz (needs Morpheus built in pipeline/sources/morpheus)
    .venv/bin/python -m unittest discover -s tests  # run the pipeline tests

See [texts/README.md](texts/README.md) for the file formats.

## Texts sold as separate apps

The reader (`no.anagnosis.reader`) is free and carries no text: without one it is a dictionary
and word analyser. Every text is a paid app of its own (Antigone: `no.anagnosis.antigone`; the
Odyssey: `no.anagnosis.odyssey`; the Symposium: `no.anagnosis.symposium`; the New Testament:
`no.anagnosis.newtestament`; the other Sophocles plays likewise) that carries the text's database.
The reader's list of available texts shows the texts marked `google_play: yes` in their
`about.md`, with the price given there (see texts/README.md). The reader looks for
apps that answer the action `no.anagnosis.action.TEXT` and are signed with its own key, copies
their text in, and removes it again when the app is uninstalled. On Google Play the text apps
must therefore be signed with the same app signing key as the reader: when creating such an
app in Play Console, choose to use the reader's app signing key.

## Licences

* Code (`pipeline/`, `app/`): GNU General Public License v3.0 or later, see [LICENSE](LICENSE).
* Bundled fonts (Gentium Plus, Cardo, GFS Didot, GFS Neohellenic): SIL Open Font License 1.1, see [app/fonts-licenses/](app/fonts-licenses/).
  Copyright (C) 2026 Robert Emil Berge.
* Data (`texts/`, `data/`): Creative Commons Attribution-ShareAlike 4.0, see [DATA-LICENSE](DATA-LICENSE).
  The data is derived from the Perseus Digital Library (Tufts University), the Ancient Greek
  Dependency Treebank, GLAUx, Wikisource and Logeion, and from transcriptions of public-domain
  editions; the New Testament from the SBL Greek New Testament and MACULA Greek (text, apparatus,
  lemmas, morphology and syntax, both CC BY 4.0),
  Dodson's lexicon (CC0) and the Berean Standard Bible (public domain); Abbott-Smith's Manual
  Greek Lexicon of the New Testament from the public-domain TEI edition of
  github.com/translatable-exegetical-tools/Abbott-Smith; Autenrieth's Homeric Dictionary (1891)
  from our transcription of the Internet Archive scan; see
  [texts/README.md](texts/README.md) for the individual sources.

The Anagnosis name and app icon are trademarks of the author and are not covered by these
licences. Builds made by others must not use them.
