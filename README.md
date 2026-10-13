# Anagnosis

An ancient Greek reading app for Android. The app is free and works as a dictionary and
morphological analyser; texts are bought inside it.

Tap a word to see its dictionary entry and morphology, switch between the Greek and
translations, consult commentaries, and write your own notes on passages. Search the Greek, the
translations, the commentaries and your notes, in one text or all of them, or list every
occurrence of a lemma. Everything works offline.

The reader is free on Google Play and the texts are sold there. Everything needed to build it yourself is in this repository,
free of charge: the code under the GPL (see LICENSE), the texts and data under CC BY-SA 4.0
(see DATA-LICENSE). The privacy policy is in PRIVACY.md.

## Repository layout

    texts/       the texts, translations, commentaries and word annotations, as editable plain files
    pipeline/    Python pipeline: fetches upstream sources, imports them into texts/, builds the SQLite bundle
    pipeline/transcriptions/   page-by-page transcriptions of printed editions (Allen's Odyssey, Burnet's Symposium)
                               and of Autenrieth's Homeric Dictionary; corrections to the OCR of Woodhouse's
                               English-Greek Dictionary
    data/        build output: the SQLite bundle shipped with the app (not committed)
    app/         the Android apps (Kotlin Multiplatform, Compose): the free reader (androidApp), which carries no text;
                 one asset pack per text sold inside it (packs/); and one small app per text (antigoneApp, odysseyApp,
                 symposiumApp, newTestamentApp, ajaxApp ...), which hands its text to the reader, for a text that may
                 also be sold as an app of its own

## Building the data bundle

    cd pipeline
    python3 -m venv .venv && .venv/bin/pip install -r requirements.txt
    .venv/bin/python -m anagnosis_pipeline fetch    # download upstream sources into pipeline/sources/
    .venv/bin/python -m anagnosis_pipeline import   # (re)generate texts/ from upstream; overwrites hand edits
    .venv/bin/python -m anagnosis_pipeline import-syntax  # regenerate only texts/antigone/syntax-nodes.tsv
    .venv/bin/python -m anagnosis_pipeline check    # validate texts/
    .venv/bin/python -m anagnosis_pipeline build    # write data/lexicon.sqlite (shared dictionaries) and data/<text>.sqlite
    .venv/bin/python -m anagnosis_pipeline build --only odyssey   # rebuild one text, keeping the lexicon
    .venv/bin/python -m anagnosis_pipeline catalog  # rewrite data/catalog.json alone (after editing an about.md)

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

Woodhouse's English-Greek Dictionary, the reader's English → Greek dictionary, is the OCR by Akemdwr
(Internet Archive), kept as downloaded, with our corrections against the 1910 scan in
`pipeline/transcriptions/woodhouse/` (the brief is its README.md; `build` applies them):

    .venv/bin/python -m anagnosis_pipeline.woodhouse_qa             # flag suspect words (pipeline/build/woodhouse-flags.tsv)
    .venv/bin/python -m anagnosis_pipeline.woodhouse_pages batches  # the flags in batches, with page images of the scan
    .venv/bin/python -m anagnosis_pipeline.woodhouse                # check that every correction applies

The New Testament is imported, not transcribed:

    .venv/bin/python -m anagnosis_pipeline fetch-nt    # the SBLGNT, MACULA Greek, Dodson's lexicon and the Berean Standard Bible into pipeline/sources/nt/
    .venv/bin/python -m anagnosis_pipeline import-nt   # texts/newtestament/ from them

The word analyser's forms come from running Morpheus over the open Perseus corpus:

    .venv/bin/python -m anagnosis_pipeline build-morpheus-forms  # pipeline/build/morpheus-analyses.tsv.gz (needs Morpheus built in pipeline/sources/morpheus)
    .venv/bin/python -m unittest discover -s tests  # run the pipeline tests

See [texts/README.md](texts/README.md) for the file formats.

## Texts bought in the reader

The reader (`no.anagnosis.reader`) is free and carries no text: without one it is a dictionary
and word analyser. Every text is sold inside it as a one-time in-app product through Google Play
Billing, with the product id `text_<slug>` (`text_antigone`, `text_newtestament`). The text itself
travels with the reader's bundle as an on-demand asset pack (`app/packs/<slug>`), which Google
Play hosts and downloads once the text is bought; the reader copies it in and removes the pack.
The reader's shop (Available texts) lists the texts marked `google_play: yes` in their
`about.md` (see texts/README.md) whose product Google Play offers, with Play's price in the
buyer's currency. What the account owns is asked of Google Play whenever the app comes to the
front, so a new device or a reinstall gets the texts back, and a refunded text is hidden again.
The plan and its reasons are in [app/PLAN-in-app-purchases.md](app/PLAN-in-app-purchases.md).

The reader has no internet permission: payments and downloads are done by the Google Play app.
Google's billing library brings the permission along to send its own diagnostic reports; the
reader's manifest removes it.

A text can also be sold as an app of its own (Antigone: `no.anagnosis.antigone`; the other texts
likewise), which carries the text's database. The reader looks for apps that answer the action
`no.anagnosis.action.TEXT` and are signed with its own key, copies their text in, and removes it
again when the app is uninstalled (unless the text was also bought in the reader). On Google Play
such an app must therefore be signed with the same app signing key as the reader: when creating
it in Play Console, choose to use the reader's app signing key.

To try the shop on the emulator, which has no Play Store, install a debug bundle with
bundletool's local testing (`build-apks --local-testing`, then `install-apks`): debug builds on
an emulator buy with a fake billing that charges nothing, and the packs are served locally.

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
  from our transcription of the Internet Archive scan; Woodhouse's English-Greek Dictionary (1910)
  from the OCR by Akemdwr (Internet Archive), corrected by us against the 1910 scan; see
  [texts/README.md](texts/README.md) for the individual sources.

The Anagnosis name and app icon are trademarks of the author and are not covered by these
licences. Builds made by others must not use them.
