# Anagnosis

Readers for ancient Greek texts on Android. The first text is Sophocles' *Antigone*.

Tap a word to see its dictionary entry and morphology, switch between the Greek and
translations, and consult commentaries. Everything works offline.

The app is sold on Google Play. Everything needed to build it yourself is in this repository,
free of charge: the code under the GPL (see LICENSE), the texts and data under CC BY-SA 4.0
(see DATA-LICENSE). The privacy policy is in PRIVACY.md.

## Repository layout

    texts/       the texts, translations, commentaries and word annotations, as editable plain files
    pipeline/    Python pipeline: fetches upstream sources, imports them into texts/, builds the SQLite bundle
    pipeline/transcriptions/   page-by-page transcriptions of printed editions (Allen's Odyssey)
    data/        build output: the SQLite bundle shipped with the app (not committed)
    app/         the Android apps (Kotlin Multiplatform, Compose): the reader (androidApp) with Antigone,
                 and one small app per text sold separately (odysseyApp), which hands its text to the reader

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
    .venv/bin/python -m unittest discover -s tests  # run the pipeline tests

See [texts/README.md](texts/README.md) for the file formats.

## Texts sold as separate apps

The reader (`no.anagnosis.reader`) comes with Antigone. Every further text is a paid app of its
own (the Odyssey: `no.anagnosis.odyssey`) that carries the text's database. The reader looks for
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
  Dependency Treebank and Logeion; see [texts/README.md](texts/README.md) for the individual sources.

The Anagnosis name and app icon are trademarks of the author and are not covered by these
licences. Builds made by others must not use them.
