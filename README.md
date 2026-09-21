# Anagnosis

Readers for ancient Greek texts on Android. The first text is Sophocles' *Antigone*.

Tap a word to see its dictionary entry and morphology, switch between the Greek and
translations, and consult commentaries. Everything works offline.

## Repository layout

    texts/       the texts, translations, commentaries and word annotations, as editable plain files
    pipeline/    Python pipeline: fetches upstream sources, imports them into texts/, builds the SQLite bundle
    data/        build output: the SQLite bundle shipped with the app (not committed)
    app/         the Android app (Kotlin Multiplatform, Compose)

## Building the data bundle

    cd pipeline
    python3 -m venv .venv && .venv/bin/pip install -r requirements.txt
    .venv/bin/python -m anagnosis_pipeline fetch    # download upstream sources into pipeline/sources/
    .venv/bin/python -m anagnosis_pipeline import   # (re)generate texts/ from upstream; overwrites hand edits
    .venv/bin/python -m anagnosis_pipeline check    # validate texts/
    .venv/bin/python -m anagnosis_pipeline build    # write data/lexicon.sqlite (shared dictionaries) and data/<text>.sqlite
    .venv/bin/python -m unittest discover -s tests  # run the pipeline tests

See [texts/README.md](texts/README.md) for the file formats.

## Licences

* Code (`pipeline/`, `app/`): GNU General Public License v3.0 or later, see [LICENSE](LICENSE).
* Bundled fonts (Gentium Plus, Cardo, GFS Didot, GFS Neohellenic): SIL Open Font License 1.1, see [app/fonts-licenses/](app/fonts-licenses/).
  Copyright (C) 2026 Robert Emil Berge.
* Data (`texts/`, `data/`): Creative Commons Attribution-ShareAlike 4.0, see [DATA-LICENSE](DATA-LICENSE).
  The data is derived from the Perseus Digital Library (Tufts University), the Ancient Greek
  Dependency Treebank and Logeion; see [texts/README.md](texts/README.md) for the individual sources.

The Anagnosis name and app icon are trademarks of the author and are not covered by these
licences. Builds made by others must not use them.
