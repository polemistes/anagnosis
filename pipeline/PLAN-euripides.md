# Euripides: the nineteen plays in Gilbert Murray's Oxford text (private until 2028-01-01)

The author decided on 2026-11-15/16 (do not reopen): **all nineteen plays of Euripides are made
from Gilbert Murray's Oxford text** (Euripidis Fabulae, Oxford Classical Texts, 3 vols,
1902-1913): the Greek text **and** the critical apparatus from that edition, with an English
commentary and introduction by another editor beside it from the start, E. P. Coleridge's
translation, and the syntax trees. **The first play is the Medea** (the author: "Start with Medea
next"). Murray died in 1957: his edition is protected in Norway and the UK until the end of
2027. The plays are therefore **offered only from 1 January 2028**; until then the author uses
them privately, and **nothing of Murray's text or apparatus may become public before that day**:
not in the public GitHub repository, not in a release bundle of the app, not marked for sale.
The files stay on this computer.

A session that picks this up: read **Progress** below, then `private/` (`git -C private log -5`;
git may be run inside `private/` only for init, add and commit; never give it a remote), then
the play's row in the table. The pipeline is the drama route of PLAN-drama.md as refined by
PLAN-sophocles.md: read both (their Decisions, and every Progress entry of PLAN-sophocles.md:
they hold the pitfalls) before the first agent of a play.

## The decisions and their reasons

* **Murray's text and apparatus, for all nineteen.** One editor for all the plays: one set of
  sigla (A B V L P and the rest of his Sigla page), one style of apparatus, one way of
  dividing the lyrics, and the text the scholarship of the last century cites. The older plan
  (PLAN-drama.md: a different nineteenth-century edition per play, Earle's Medea, Sandys's
  Bacchae, Hayley's Alcestis) is superseded; those editors now serve as commentaries.
* **Why private and why the date.** US public domain (the volumes were published before 1931)
  does not carry over: the app is made in Norway and sold in the EU and the UK, where a work is
  protected for 70 years after the author's death. Murray died in 1957, so his edition is free
  there from 1 January 2028. Until then nothing of his may be published or sold.
* **The check text is the same edition.** Perseus's Greek Euripides (canonical-greekLit,
  tlg0006.tlgNNN.perseus-grc2, CC BY-SA 4.0) is Murray's own text, digitised by OCR from the
  same scans (vol. I from euripidisfabulae01euriuoft, the copy read here). So the check text and
  the print are one edition: differences between them are OCR slips of Perseus's or of ours, not
  readings, and flags should be few (as for the Lysistrata, whose check text is Hall-Geldart's
  own). Perseus's file is itself Murray's text and is equally private: it is downloaded into
  pipeline/sources/ (ignored) and never shipped or copied into a public file.
* **The automatic syntax is built on it.** GLAUx (0006-001 … 0006-019, CC BY-SA 4.0) annotated
  the Perseus files, that is Murray's text, so its tokens align almost word for word. For the
  Medea there are also hand-made trees (Pedalion, CC BY-SA 4.0, the whole play): compare their
  labels with the treebank's before choosing them over GLAUx (research file).
* **Commentary beside the text from the start**, as Paley's notes stand beside Rzach's text in
  the Theogony (PLAN-theogony.md): the commentary's own text and critical notes are not used;
  its notes go under Murray's line numbers (all the commentaries are keyed to the standard
  numbers; where a lemma differs from Murray's word the note still stands under its line).
* **Translation**: Coleridge from Perseus (eng2; eng3 for the Rhesus, whose eng4 is Murray's
  own verse translation and is never used). Coleridge translated from Paley's text, so his
  English differs from Murray's Greek in places: it is shipped as it is, as for every play.
* Building a play is not putting it on sale: never write `google_play: yes` for these texts
  (`check` refuses it); each gets its `product_id` (`euripides_<slug>_murray`) and a
  `# release: 2028-01-01` line in about.md.

## What is private and how it is kept so

**The private folder.** `private/` at the repository root is ignored by the public repository
(`.gitignore`) and holds its own git repository (no remote, never pushed). In it:
`private/texts/<slug>/` (grc.txt, apparatus, commentary, about.md …),
`private/transcriptions/drama/<slug>/` (batch files), and later the built database and pack of
each play. The pipeline finds them at its usual paths through symbolic links, made by
`python -m anagnosis_pipeline private-setup <slug>`:

    texts/<slug>                          -> ../private/texts/<slug>
    pipeline/transcriptions/drama/<slug>  -> ../../../private/transcriptions/drama/<slug>

What the pipeline writes under `pipeline/build/` (OCR, check sheets, crops, drafts, merge logs)
and `pipeline/sources/` (scans, the Perseus files) is ignored by the public repository as a
whole and stays on this computer. `data/<slug>.sqlite` and the other `data/<slug>.*` files are
ignored by name. **Commit the private files in `private/`** after every verified stage
(`git -C private add -A && git -C private commit -m …`), as PLAN-drama.md says for the public
ones; the public commits carry only code, plans and the research.

**The one list.** `PRIVATE_SLUGS` in `pipeline/anagnosis_pipeline/private.py` names the nineteen
slugs (alcestis, medea, heraclidae, helen, bacchae, hecuba, troades, cyclops, heracles,
iphigeniataurica, orestes, phoenissae, iphigeniaaulidensis, ion, hippolytus, andromache,
euripideselectra, rhesus, supplices; texts/electra is Sophocles'). Everything below reads it.

**The safeguards.**
1. `.gitignore` lists `/private/`, `/data/catalog-author.json` and, per slug, `/texts/<slug>`,
   `/pipeline/transcriptions/drama/<slug>`, `/data/<slug>.*`, `/app/packs/<slug>`
   (`private.gitignore_lines()` gives the block; `check` reports a missing line).
2. **pre-push hook** (`pipeline/tools/pre-push`, installed as `.git/hooks/pre-push`; install line
   in pipeline/tools/README.md): refuses a push when any pushed commit, or the tree of a pushed
   tip, holds a file under a private slug's paths or under `private/`; it refuses too when the
   check cannot run. A file added and removed again is still caught (it is in the history).
3. **`check`** ends with "private texts and release dates": an ERROR for every private slug's
   file that git tracks in the public repository, a private slug in the public pack lists
   (app/settings.gradle.kts, app/androidApp/build.gradle.kts), a private text marked
   `google_play: yes`, a private text without `# release:` or with a date before 2028-01-01, a
   private slug in the public catalogue, a private slug's folder in texts/ that is not a link
   into private/, a missing .gitignore line; and it lists the texts held back and until when.

**Release dates (`# release: YYYY-MM-DD` in about.md).** While the date lies in the future,
`catalog` (and `build`, which writes the catalogue too) leaves the text out of
`data/catalog.json`, the public catalogue that the reader bundles, and writes it with all the
public texts to **`data/catalog-author.json`**, the catalogue for the author's own builds
(ignored by the public repository). A private slug is held back until 2028-01-01 even if its
about.md lacks the key or gives an earlier date. `build --only <slug>` builds the text's
database as for any text (data/<slug>.sqlite, ignored).

**The author's build** (made 2026-11-17 by the Medea's finishing agent; Gradle not yet run).
* **The private packs.** `private-setup <slug> --pack` writes private/app/packs/<slug>/
  build.gradle.kts (the public packs' template) and links app/packs/<slug> to it (the public
  path is ignored by name). The Medea's is there.
* **The list.** `app/author-packs.txt` (ignored by the public repository; the line is in
  `private.gitignore_lines()`, so `check` reports it missing, and the pre-push hook refuses the
  file) names the held-back texts to bundle, one slug a line (`#` starts a comment). It holds
  `medea`. When it names any text, app/settings.gradle.kts includes `:packs:<slug>` for each,
  app/androidApp/build.gradle.kts adds them to `assetPacks` and copies
  `data/catalog-author.json` into the bundle as its catalog.json, and **Gradle refuses every task
  whose name contains "release"** (the build stops at configuration with a message). Without the
  file both Gradle files do exactly what they did (same includes, packs and copied files).
  Chosen over a Gradle property: the author's builds stay the usual command, and the guard
  covers the one dangerous case, a release built while the file is there.
* **The author's build** (from app/, JAVA_HOME=/opt/android-studio/jbr; first `build --only
  <slug>` and `catalog` in pipeline/): with app/author-packs.txt in place,
  `./gradlew :androidApp:bundleDebug`, then `./gradlew --stop`; install as in PLAN-sophocles.md
  "Trachiniae emulator check" (bundletool 1.18.1 `build-apks --local-testing`, `install-apks`).
  **The public build** as before, after moving the file away (`mv app/author-packs.txt
  ../author-packs.txt.off` or delete it): `./gradlew :androidApp:bundleRelease` (or
  bundleDebug); with the file present a release task is refused.
* **Open: the shop.** The reader offers only texts marked `google_play: yes` and bought. On the
  emulator the debug build's fake billing sells a text once the sale mark is in a scratch copy
  of the bundle's catalogue (pipeline/tools/emulator-check/patch_aab.py, slugs edited); on the
  author's phone a debug build uses Play Billing, which cannot sell a product that is not
  active in Play Console. So on a phone the private texts cannot yet be opened: to be decided
  (e.g. the author's build marks its packs for sale and uses the fake billing on any device, or
  the text installed by hand). Not done.
* The **public** pack lists (settings.gradle.kts, androidApp's `assetPacks`) must not name a
  held-back text; `check` reports it if they do.
* On 2028-01-01: move the plays' folders from `private/` into the public repository (replace
  the links by the folders, packs included), remove the slugs from `PRIVATE_SLUGS` and the
  .gitignore block, add the packs to the public lists, empty app/author-packs.txt, run `catalog`
  (the release date has passed), build and publish a reader release that day; activate the
  products in Play Console that day.

## The route per play

As PLAN-sophocles.md "The route" and its "order of the last steps", with what was found to
matter there (a pass stays only if it catches real errors):

1. `private-setup <slug>`; the `Play` entry in drama.py (`edition` Murray's volume, `scan`,
   `app_editor="murray"`, `product_id`, `glaux`, the translation, the commentary as
   `notes_editor` with `notes_scan`, `speaker_trust=True`); the leaves from the scan's
   scandata (`leaf_of`) and the page images: the play's text (first and last page), the pages
   before it (the hypotheses with their own apparatus, the persons page with Murray's note on
   the date and the codices), the volume's Sigla page; the commentary's notes and introduction
   leaves.
2. `drama-pages <slug> fetch | ocr | draft` (background; log `pipeline/build/logs/<slug>-pages.log`).
   Judge the draft before any agent: verses, flagged verses and their kinds (the check text being
   the same edition, more than a tenth of the verses flagged means the layout or matching is
   wrong: find out why), the apparatus found on every page, three pages against their images
   (a dialogue page, a lyric page, the last page: verse division and numbers, the apparatus
   crop holding the whole apparatus and nothing else). Commit the batch files in `private/`.
3. Text batches (six pages, Opus, at most ten agents at once, INSTRUCTIONS-text.md, the
   workflow `transcriptions/drama/drama-text.workflow.js`, scratch in
   `pipeline/build/agent-scratch/`): the text from flags, the apparatus copied from the crops;
   checker; commit in `private/`.
4. `drama-residuals <slug>` and its pass (RESIDUALS.md); then **one review per batch** with the
   five-point `extra` reading task of the Oedipus at Colonus review (every verse against the
   page for punctuation, accents, breathings, iota subscripts, brackets and daggers; the
   apparatus's breathings enlarged and compared with certain ones on the same page). How
   Murray's sigla are written (superscript hands L¹ L², the later correcting hands as the small
   letters l p v b of his Sigla page, Σ) is in INSTRUCTIONS-text.md, "Murray's Euripides".
5. `merge-drama <slug>` (never chained with `&&`: it exits with the number of its remarks); the
   numbering suspects (the Sophocles plays needed `sophocles-numbering`; a like report for
   Murray's lyric division to be written if the merge log shows covered verses); the review
   list once (`HAND_ANALYSES`, `LEMMA_FIXES`).
6. The commentary and introduction by the prose route (`drama-prose <slug> notes|intro
   fetch|ocr|draft`, eight pages per agent, INSTRUCTIONS-prose.md with a section per editor's
   layout; a first check, and a second reading where the Greek is dense, i.e. the notes; for an
   English introduction the first check alone, as proposed to the author for the Sophocles
   plays). Murray's hypotheses (Greek prose with their Latin apparatus) and the persons page:
   read with the text route's apparatus crops or the prose route, to be settled on the Medea.
7. Translation from Perseus (merge only; the translation's segments re-filed where our verse
   numbers differ, as `sophocles-prose` does); sigla.md from Murray's Sigla page (the volume's,
   one per volume, shared by its plays) with the play's own note from the persons page;
   glossary.md, shortdefs.tsv, aliases.tsv; about.md with `product_id` and
   `# release: 2028-01-01`, no sale mark; the texts/README.md section waits for the release
   (it would describe a text the public cannot have); a play/README.md row likewise.
8. `build --only <slug>`, `check`, `catalog` (the play goes to catalog-author.json only), the
   pack only in the private build; the emulator check with the private build (PLAN-sophocles.md
   "Trachiniae emulator check" for the commands; memory: 8 GB free first).

## Order

The ranking of pipeline/research/euripides-plays.md (easiest first), with the Medea first by
the author's word: **Medea**, then **Alcestis** (the author, 2026-11-16: "After Medea, take
Alcestis also"); after those two the author decides the next play, the default being the
ranking's order: Heraclidae, Helen, Bacchae, Hecuba, Troades, Cyclops, Heracles, Iphigenia in
Tauris, Orestes, Phoenissae, Iphigenia in Aulis, Ion, Hippolytus, Andromache, Electra, Rhesus,
Supplices. One play at a time; the next play's token-free steps
(fetch, OCR, draft) and its first pass may overlap the previous play's finishing steps, within
ten agents (PLAN-sophocles.md, the overlap rule). Nothing of Euripides runs before the Sophocles
plays (the Philoctetes) are finished, except this set-up.

## The plays

Murray's volumes: **I** = euripidisfabulae01euriuoft (Toronto, 400 ppi, jp2, a Horace Hart
printing of 1902-1910, Perseus's source); **II** and **III**: which printing to read is open
(For the author): Perseus read vol. II from euripidisfabu02euri (a 1962 printing of the 3rd
edition, 1913) and vol. III from euripidisfabulae03euri_0 (a 1925-1946 printing of the 2nd
edition, 1913); the alternatives are euripidisfabulae02euri_0 (a Horace Hart printing, edition
not pinned) and euripidisfabulae03euriuoft (the 1909 first edition, which differs from Perseus
where Murray revised). "Perseus page n" is the page image Perseus's file names (the research
file lists them per volume; here given to the plays in the volume's order: verify in each
file's sourceDesc): for vol. I it is the persons page, leaf n + 1, and the text begins on the
next leaf. TLG numbers other than
002, 003 and 017 (on disk) are from memory: verify at each play's fetch. Translation =
`pipeline/sources/drama/tlg0006.<tlg>.perseus-eng2.xml` (Coleridge) unless the row says
otherwise; treebank = GLAUx `0006-<nnn>.xml`.

| # | slug | play | tlg | Murray | Perseus page | commentary and introduction (scan) | translation | treebank | product id |
|---|---|---|---|---|---|---|---|---|---|
| 1 | medea | Medea (built 2026-11-17, author's catalogue only; emulator check to do) | tlg003 | I | n103: text leaves 105-161 | M. L. Earle, American Book Co. 1904 (d. 1905), cu31924079583609, notes under the text in two columns (leaves 80-254), introduction leaves 14-71 | eng2 | GLAUx 0006-003; Pedalion hand-made trees (compare first) | euripides_medea_murray |
| 2 | alcestis | Alcestis | tlg002 | I (euripidisfabulae01euriuoft) | n55: half-title and ΥΠΟΘΕΣΙΣ ΑΛΚΗΣΤΙΔΟΣ [ΔΙΚΑΙΑΡΧΟΥ] and [ΑΛΛΩΣ] with apparatus leaf 54, their end leaf 55, persons with Murray's note leaf 56, text leaves 57-101 (seen 2026-11-16) | H. W. Hayley, Ginn 1898 (d. 1899), alcestisofeuripi00euriuoft (284 leaves, jp2, clean), "critical and exegetical notes" at the back, introduction about 90 pp. (leaves to find) | eng2 (sources/drama/tlg0006.tlg002.perseus-eng2.xml, on disk) | GLAUx 0006-002 (on disk) | euripides_alcestis_murray |
| 3 | heraclidae | Heraclidae | tlg004 | I | n163 (persons leaf 164) | A. C. Pearson, Cambridge 1907 (d. 1935), heraclidae00euri, notes at the back | eng2 | GLAUx 0006-004 | euripides_heraclidae_murray |
| 4 | helen | Helen | tlg014 | III | n13 | A. C. Pearson, Cambridge 1903, helena__00euriuoft, notes at the back | eng2 | GLAUx 0006-014 | euripides_helen_murray |
| 5 | bacchae | Bacchae | tlg017 | III | n229 | J. E. Sandys, Cambridge, 3rd ed. 1892 (d. 1922), BacchaeOfEuripides_680, notes at the back | Coleridge's Bacchantes, Wikisource (speeches); Perseus eng2 is Buckley | GLAUx 0006-017 | euripides_bacchae_murray |
| 6 | hecuba | Hecuba | tlg007 | I | n321 | W. S. Hadley, Cambridge 1894 (d. 1927), hekabhecubaofeur00euriuoft, notes at the back | eng2 | GLAUx 0006-007 | euripides_hecuba_murray |
| 7 | troades | Troades | tlg011 | II | n189 | R. Y. Tyrrell, Macmillan 1897 (d. 1914), troadeswithrevte00euriuoft, notes at the back | eng2 | GLAUx 0006-011 | euripides_troades_murray |
| 8 | cyclops | Cyclops | tlg001 | I | n25 (text from leaf 27) | F. A. Paley vol. III, 2nd ed. 1880 (d. 1888), ldpd_8039020_002, notes under the text; W. E. Long 1891 (cyclops00euriuoft) if his death year is found | eng2 | GLAUx 0006-001 | euripides_cyclops_murray |
| 9 | heracles | Heracles | tlg010 | II | n67 | A. Gray and J. T. Hutchinson, Cambridge 1897 (d. 1940, 1924), heraklesmainomen00euriuoft, notes at the back | eng2 | GLAUx 0006-010 | euripides_heracles_murray |
| 10 | iphigeniataurica | Iphigenia in Tauris | tlg012 | II | n297 | E. B. England, Macmillan 1899 (d. 1936), iphigeneiaheenta00euriuoft, notes under the text | eng2 | GLAUx 0006-012 | euripides_iphigeniataurica_murray |
| 11 | orestes | Orestes | tlg016 | III | n155 | N. Wedd, Cambridge 1895 (d. 1940), orestesofeuripid00euriuoft, notes at the back | eng2 | GLAUx 0006-016 | euripides_orestes_murray |
| 12 | phoenissae | Phoenissae | tlg015 | III | n83 | A. C. Pearson, Cambridge 1909, phoenissaeedited00euriuoft, notes at the back | eng2 | GLAUx 0006-015 | euripides_phoenissae_murray |
| 13 | iphigeniaaulidensis | Iphigenia in Aulis | tlg018 | III | n287 | E. B. England, Macmillan 1891, iphigeniaataulis00euri, notes under the text | eng2 | GLAUx 0006-018 | euripides_iphigeniaaulidensis_murray |
| 14 | ion | Ion | tlg013 | II | n123 | A. W. Verrall, Cambridge 1890 (d. 1912), ionofeuripides00euririch (facing verse translation not used), or Paley vol. II | eng2 | GLAUx 0006-013 | euripides_ion_murray |
| 15 | hippolytus | Hippolytus | tlg005 | I | n207 | Mahaffy and Bury, Macmillan 1889 (d. 1919, 1927), hippolytuseurip00eurigoog (Google, no jp2), or Paley vol. I (india.history.resource.14928) | eng2 | GLAUx 0006-005 | euripides_hippolytus_murray |
| 16 | andromache | Andromache | tlg006 | I | n269 | G. Norwood, John Murray 1906 (d. 1954), andromacheeurip00norwgoog (Google, no jp2), or Paley vol. II | eng2 | GLAUx 0006-006 | euripides_andromache_murray |
| 17 | euripideselectra | Electra | tlg009 | II | n243 | Paley vol. II, 2nd ed. 1874, ldpd_8039020_001, notes under the text (Keene 1893 only on HathiTrust) | eng2 | GLAUx 0006-009 | euripides_euripideselectra_murray (see For the author) |
| 18 | rhesus | Rhesus | tlg019 | III | n357 | Paley vol. I, 1857, india.history.resource.14928, notes under the text (Porter is protected: d. 1961) | eng3 (Coleridge; never eng4, Murray's) | GLAUx 0006-019 | euripides_rhesus_murray |
| 19 | supplices | Supplices | tlg008 | II | n17 | Paley vol. I, 1857, india.history.resource.14928, notes under the text | eng2 | GLAUx 0006-008 | euripides_supplices_murray |

drama.py's `bacchae` and `alcestis` entries still describe the older plan (Sandys's and Hayley's
own text): rewrite each at its turn as the Medea's was.

## Progress

* **2026-11-17, Medea finished but for the emulator check** (finishing agent; log
  build/logs/medea-finish-agent.md; private commits fe80aeb … a94f6ca). Numbering: no verse
  renumbered (`sophocles-numbering medea` now reads Murray's apparatus, items without "]" taking
  their first Greek words; every margin of the lyric and anapaestic passages seen on the pages);
  one misprint of Murray's corrected with a note in the item (apparatus 1384 for 1383, τοῦδε).
  Sections: Earle's divisions (introduction § 32) as `Play.parts`: Prologue 1, Parodos 131 (Perseus
  96), episodes and five stasima, Exodos 1293. Trees: 25 hand analyses, 18 lemma fixes, one alias.
  Translation: aligned throughout (no number table needed); stage directions set apart
  (`Play.trans_stages_apart`); Coleridge gives 945 to Jason and 1004a to Medea where Murray does
  not (left). sigla.md (Murray's Latin Sigla page and his note on the Medea's codices), glossary 14,
  shortdefs 18, about.md (product id, release 2028-01-01, no sale mark), true licence lines
  (`Play.edition_license`) and syntax line (`Play.syntax_note`, not "automatic"). Built
  (data/medea.sqlite), in catalog-author.json only; `check` 0 errors. The pack and the author's
  build: see "The author's build" above. **Next**: the emulator check with the author's build
  (8 GB free; patch_aab.py with SLUGS = ['medea']); the shop on a phone (open, above).

* **2026-11-17, Medea: prose done and merged; finishing.** Second reading of the other 18
  commentary batches and the 7 of Earle's introduction: 25 agents, 3.2 M tokens; 38 `rev:`
  corrections in the whole prose, a dozen of them accents or breathings in the Greek (ἄν for
  ἂν three times, ἢ καὶ, ὤν for ὧν, οὓς): the sample had understated what the pass finds, and
  it stays for the Alcestis. `merge-drama medea`: commentary-earle.md 1,098 notes,
  introduction.md 40 headings, 11 log remarks. An Opus agent does the finishing (log
  build/logs/medea-finish-agent.md): numbering by Murray's apparatus, the review list (194
  words against the Pedalion trees), translation, sigla from Murray's leaf 24, glossary,
  shortdefs, about.md with the release date, the build into the author's catalogue, and the
  app's optional list of author packs. Then the emulator check with an author's build.
  Agent tokens for the Medea's prose: set-up 0.42 M, first check 4.3 M, second reading 0.8 +
  3.2 M.
* **2026-11-17, Alcestis started** (the overlap rule: the next play's first pass beside the
  previous play's finishing). `drama.py`'s `alcestis` entry is Murray's now (text leaves
  57–101, the Medea's page options; Hayley as notes editor, his leaves still to be found);
  `private-setup alcestis`; `drama-pages alcestis fetch|ocr|draft` running (log
  build/logs/alcestis-pages.log). Then: judge the draft (flags, apparatus on every page, three
  pages against the images), first pass (edition section "Murray's Euripides (Oxford text)"),
  NO residual pass, the review with the Medea's five points, merge; Hayley's notes (at the
  back of his book) and introduction by the prose route.


* **2026-11-17, Medea prose: first check back, second reading running.** First check of the
  31 batches: 31 agents, 4.3 M tokens, every flag answered (private cdc2c1c). Second reading
  of a sample (notes-03, 09, 15, 20) and of the two batches with Murray's hypotheses and
  persons (intro-08, 09): 0.8 M. In the 32 commentary pages it found four small errors: two
  phrases bolded that are plain in print, twice a Latin A for the Greek book letter of Homer;
  no wrong accent or breathing; two batches needed nothing. In Murray's persons page the
  names had been taken across the columns instead of down them (corrected). By the author's
  rule (a pass stays if it catches errors that would otherwise remain; the author does not
  want quality compromised) the other 18 commentary batches and the 7 batches of Earle's
  introduction get the second reading too: running, nine at once. **For the next plays**:
  the look-alike letter can be caught by the checker (a Latin capital as a book letter after
  "Hom."); the bolding cannot; consider after the Alcestis whether the second reading of an
  English commentary keeps earning its cost (yield here: one small error per eight pages).


* **2026-11-17, Medea prose.** Set-up agent's report (log build/logs/medea-prose-setup.md;
  public commit a631275, private d7cee8c): Earle's notes 175 pages, 22 batches, 2,623 flags,
  1,039 note headings; introduction 67 pages, 9 batches, 1,021 flags (Earle's introduction 58
  pages; Murray's hypotheses 2; Earle's notes on the hypothesis 6; Murray's persons 1). The
  trees are the Pedalion hand-made ones (all 824 sentences), made on a later text than
  Murray's. **Running: the first check of all 31 batches** (nine at once). Then: a second
  reading of four notes batches as a sample, and by its yield the rest; `merge-drama medea`;
  the finishing steps.


* **2026-11-17, Medea: Earle's commentary and introduction set up and drafted** (agent; log
  build/logs/medea-prose-setup.md; no reading agents yet). Commentary (`notes_layout="earle"`:
  everything under the verses, found by the first run of three two-column rows, drama_prose.
  `earle_top`; the notes that run on inside paragraphs cut before every bold number and settled
  over the whole commentary, `earle_markdown` + `_resolve_note_headings`): **175 pages, 22
  batches (notes-01…22), 2,623 flags (median 15 a page; worst p-0191 and p-0145 33), 1,039 note
  headings**, none falling; about 97 % of the Greek right in the draft. Introduction (kind
  `intro` from two scans, `notes_sources`; Earle's margin notes and quoted verses handled):
  see "Medea: the introduction" under Decisions and the log for its numbers. Merge:
  `write_prose_documents` (out of merge_play) writes commentary-earle.md and introduction.md only
  when their batches are all checked; `notes_refile_mark` puts the printed number in front of a
  note filed under the nearest earlier verse. Brief: INSTRUCTIONS-prose.md, "Earle's Medea: the
  commentary and the introduction". The trees: see "Medea: the syntax trees" under Decisions.
  **Next**: the first check of notes-01…22 (eight pages per agent, Opus, at most ten at once)
  and of intro-01…09, then a second reading of the notes as for the Philoctetes (four batches
  first, then the rest if it finds errors), then `merge-drama medea`.

* **2026-11-17, Medea: text reviewed and merged.** Review back (ten agents, 1.57 M tokens):
  13 `rev:` notes, about six of substance (an iota subscript and a breathing in the
  apparatus, one apparatus item split off, the exclamation at 1055a/1056 numbered as
  Murray's apparatus files it, a paragraphos dash at 1275, an evident misprint αλλʼ at 523
  noted); most pages needed nothing. With the residual pass's one change this confirms the
  decision above: **no residual pass for the next plays from Murray**. `merge-drama medea`:
  1,407 verses, 642 apparatus notes (799 items), Coleridge's translation (504 segments),
  1 word without lemma, review list 194 words, 4 merge remarks (the transposed 1271–1274).
  Committed in private/ (6e6ea90). The trees: pipeline/sources/glaux/0006-003.xml marks its
  sentences `analysis="manual"` and reads otherwise than Murray in some 118 words
  (ἀριστέων for his ἀρίστων at 5): made on a later text; an agent is finding out whose they
  are and how about.md may describe them. **Running: the set-up of Earle's commentary and
  introduction for the prose route** (log build/logs/medea-prose-setup.md), no reading agents
  yet. To do after it: the notes and introduction batches (check, and a second reading where
  the Greek is dense), Murray's hypotheses and persons (his leaves 102–104) and Sigla
  (leaf 24), lemma fixes from the review list, glossary, shortdefs, about.md with
  `# release: 2028-01-01` and `product_id: euripides_medea_murray`, `build --only medea`
  (author's catalogue), and the app's private build for the author's own use and the
  emulator check.
* Agent tokens for the Medea's text: first pass 1.27 M, residual pass 0.87 M, review 1.57 M.


* **2026-11-17, Medea, residual pass and review.** Residual pass back (ten agents, 0.87 M
  tokens, four minutes): of the 235 listed items ONE needed a change (a comma at 1178); the
  rest were Tesseract's own slips, since print and check text are one edition. The three
  other changes it made were Murray's daggers (910, 1256, 1359), seen by looking at the whole
  page, not from the list. **So for the next plays from Murray the residual pass is left out**
  (the author's rule: a pass stays only if it catches errors that would otherwise remain; the
  review reads every verse against the page and covers what the lists held), unless the
  Medea's review shows the two together did more than the review alone would. The review
  runs (ten jobs, nine at once), with the five points adapted to Murray: verse reading;
  daggers, brackets and lacuna marks on every page; the apparatus's breathings and sigla;
  numbering by his apparatus; shared lines and capitals.


* **2026-11-17, Medea, text.** Batch 01 ran alone as the trial (clean: 74 apparatus items on
  six pages, checker silent); batches 02–10 followed. First pass of all ten: 1.27 M agent
  tokens for 57 pages (the Sophocles plays took two to three times that per page: the check
  text being the same edition, there is little to decide). Committed in private/ (9b1a745).
  What the agents found that the flags cannot see: **Perseus's OCR lost Murray's daggers**
  (three verses in batch 08, more in 02, 06, 09: the opening dagger turned into a capital or
  dropped) and some accents (19 αἰσυμνᾷ). Lyric verses renumbered by Murray's apparatus on
  pp. 122, 130, 143. `drama-residuals medea`: 235 residuals (punctuation 80, accent 76,
  ocr-only 48, word 18, bracket 13). **Running: the residual pass** (ten jobs, nine at once;
  `drama-pass.workflow.js` now takes `edition`). Then the review, whose `extra` text must add
  to the five Sophocles points: look on every page for Murray's daggers †, brackets and
  marks of lacunae that the check text lacks; the transposed verses 1271–1274 stay in his
  printed order with his numbers.


* **2026-11-16, set-up** (agent; log `pipeline/build/logs/euripides-setup.md`): private folder,
  safeguards, release dates and this plan; the Medea's entry, leaves and draft (see below).
* **2026-11-16, Medea route step 1-2 done.** `private-setup medea` (private/ has its own git;
  first commits there: README, then the draft's batch files). drama.py's `medea` entry is
  Murray's (leaves in its comment: Sigla leaf 24; hypotheses 102-103; persons 104; text 105-161).
  Murray's page, seen on six pages and three judged in full (123 dialogue, 130 lyric, 161 last):
  running head ΕΥΡΙΠΙΔΟΥ / ΜΗΔΕΙΑ; 25-29 verses; margin numbers every fifth verse at the right
  on both pages; speakers abbreviated in the left margin (Τρ., Πα., Μη., Ια., Χο.), a new
  character's name in capitals on a line of its own above the speech (ΙΑΣΩΝ, ΑΓΓΕΛΟΣ), stage
  directions in brackets as lines of their own ((ΠΑΙΔΕΣ ἔνδοθεν.)); metrical labels "[στρ."
  "[ἀντ." at the right of a strophe's first verse; a long verse's end turned over, indented, with
  its margin number beside the turnover (640); no rule above the apparatus, which is Latin in
  small type at the foot, its item numbers without a stop (a verse number, then the lemma); the printer's
  signature under it on some pages ("EUR. I. 6", "6*"). New `Play` options for this page (all
  off for the other plays, whose pages give what they gave; tests in
  tests/test_murray_layout.py): `app_bare_numbers`, `verse_size_q=0.75`, `foot_signature`,
  `app_pitch_cut` (the apparatus is the run of lines from the foot at the small type's pitch:
  without it a page's last verse was taken into the apparatus on 12 pages), `head_frac=0.065`,
  `metre_labels`. **Draft: 57 pages, 1,405 verses, 72 flagged (5 %), apparatus found on every
  page, 10 batches** (`private/transcriptions/drama/medea/batch-01…10.md`, as the draft made
  them). Flags: 24 words the OCR reads otherwise, 12 words not found (mostly δʼ read as ὃ), 11
  speaker changes not seen in the margin, 13 lettered verses (Murray's shared lyric lines: 96a,
  111a, 144a, 183a, 292a, 1005a, 1008a, 1009a, 1104a, 1270a, 1274a/b, 1397a, 1398a, 1402a), 1271
  and 1272 printed after 1274 (Murray's order; the margin numbers say so), stage directions.
  **Found for the agents' brief (INSTRUCTIONS-text.md needs a "Murray's Euripides" section
  before batch 01 runs):** (1) the check text's numbering of lyric verses is at times one behind
  Murray's where the standard numbering skips a number (Perseus 633 ἱμέρῳ = Murray 634, Perseus
  641 ὀξύφρων = Murray 642, as his apparatus shows); the margin check sees only every fifth
  number, so the agents must number lyric verses by the apparatus's item numbers and the margin,
  and after the first merge a numbering report like `sophocles-numbering` (which reads only
  commentary-jebb-apparatus.md) must be run on commentary-murray-apparatus.md; (2) the metrical
  labels, the character headings and the signatures are not text; (3) how to write Murray's
  sigla: superscript hands (L², B¹ as in Jebb's batches), the later correcting hands as small
  letters (l, p, v, b: Murray's Sigla page says "litteris minusculis"; sigla.md must say so),
  Σ, "codd.", "rell.". **Next**: batch 01 alone as a trial
  (Opus), look at it, then the rest (at most ten at once); the Philoctetes's finishing comes
  first by the author's order.
* **2026-11-16: the agents' brief has its section** "Murray's Euripides (Oxford text)" in
  pipeline/transcriptions/drama/INSTRUCTIONS-text.md (the page, speakers, what is not text, the
  check text being Murray's own, signs, numbering by his apparatus and margin, the apparatus and
  its sigla, the review pass to follow). Batch 01 can run as the trial.

## Decisions

* 2026-11-15/16 (the author): Murray's text and apparatus for all nineteen plays; offered from
  2028-01-01; files private until then; the Medea first.
* 2026-11-16 (the author): "After Medea, take Alcestis also." The Alcestis is the second play;
  after it the author decides the next (default: the research file's ranking).
* 2026-11-16: the private texts' slugs (above); a private slug is held back until 2028-01-01
  whatever its about.md says, so that a forgotten or mistyped release line cannot publish it.
* 2026-11-16: `speaker_trust=True` for Murray's plays (the check text is his own, as Jebb's was
  for the Sophocles plays).
* 2026-11-16: the Medea's draft keeps the drama route's six pages per batch (57 pages, 10
  batches). Earle's `layout="earle"`, `app_leaves` (his critical notes) and his Greek hypothesis
  pages are dropped from the entry: Murray's apparatus is the apparatus. Earle's notes (leaves
  80-254, two columns under his text) are read later by the prose route: `notes_layout="paley"`
  (everything under the last line crossing the page's middle) may already fit his page: try it
  on two spreads before writing a new region.
* 2026-11-16: the texts/README.md section and the play/README.md row of a Murray play wait for
  the release (they would describe in public a text the public cannot have).

* **2026-11-17, Medea: the introduction document** (set-up agent). Order in the app's
  introduction.md, as merged from the intro batches in the order of their page names: (1)
  Earle's Introduction (`p-1…`, his pp. 7-64 = leaves 14-71, all of it but his bracketed
  bibliographies, which the agents replace by `[Bibliography omitted]` by PLAN-drama.md's rule;
  his numbered paragraphs as `## § N`, his margin notes after a dash in the section heading);
  (2) **the ancient hypotheses from Murray's edition** (`p-2…`, vol. I leaves 102-103), the
  Greek with Murray's own Latin apparatus under each page as a `*Critical apparatus.*`
  paragraph, in the form of the Philoctetes's "ancient argument"; (3) **Earle's notes on the
  hypothesis** (`p-3…`, leaves 73-78, pp. 66-71, the two columns under his Greek: kept, because
  they explain the hypothesis's matter (Pherecydes, Simonides, the Nostoi, the didascalia and
  the lost plays); his own Greek of the hypothesis is not used; his notes keep his line numbers,
  said in their heading to be those of his printing); (4) **Murray's persons page** (`p-4…`,
  leaf 104: the names, and his Latin note on the performance and the codices, which sigla.md
  will also quote at step 7). How: **the prose route's `intro` kind from two scans**
  (`Play.notes_sources["intro"]`, four entries; `page_stem` now numbers a page by the entry
  that holds it, so a scan may stand in the list twice; Taylor's Shepherd keeps its stems),
  not a separate batch: the hypotheses are short (two pages and the persons page) and the
  agents of the introduction can write the apparatus by INSTRUCTIONS-text.md's Murray section.
  Earle's leaves 73-78 take his notes pages' region (`Play.notes_region_leaves`); his persons
  page (leaf 79) has no notes and is not used. Earle's leaf 72 is a half-title.
* **2026-11-17, Medea: the syntax trees** (set-up agent; alignment code not changed).
  pipeline/sources/glaux/0006-003.xml has 824 sentences, **all 824 marked `analysis="manual"`**
  (9,916 word nodes with punctuation; in the GLAUx files on disk only this one is wholly manual:
  the Alcestis, Bacchae and the others are all `auto`, A True Story is half and half). They are
  the **Pedalion trees** of the Medea (research file: github.com/perseids-publications/
  pedalion-trees, `euripides_medea.xml`, 824 sentences, about 9,845 words; annotated by Toon
  Van Hal and KU Leuven students on a GLAUx pre-parse and checked by Van Hal, Gijbels and
  Joosten), taken into GLAUx under its document id; the file itself carries no header (no
  licence or editor statement), and the GLAUx documentation is not on disk; the licence is
  **CC BY-SA 4.0** (Pedalion's TREEBANK_LICENSE, and GLAUx's), usable in a sold app with
  attribution. Labels: AGDT style (PRED, SBJ, OBJ, ATR, ADV, AuxP/AuxY/AuxZ, COORD) with GLAUx's
  PRED_CO and its animacy/sense attributes. **Their text is not Murray's**: the merge found 118
  words where Murray reads otherwise and 76 of Murray's words the trees lack (review list 194).
  The trees' readings at those places (ἀριστέων at 5, καλλίνικος ᾁσεται at 45, φυγὰς πολίταις
  at 12, ὅπως ἄριστα at 240) are a later critical text's, most likely J. Diggle's Oxford text
  (1984), which the TLG's Euripides follows; not checked against the edition (no network for
  it). **So about.md must say** (wording for step 7): "Syntax: hand-made trees of the Pedalion
  project (KU Leuven; T. Van Hal and others), distributed with GLAUx, CC BY-SA 4.0. They were
  made on a later edition of the Greek text than Murray's; where Murray reads otherwise (some
  120 words) the tree of the later reading is shown at Murray's word, and some 75 of Murray's
  words have no tree." The keys: `syntax_source:` as above, `syntax_license: CC BY-SA 4.0`,
  and `syntax:` must **not** say machine-made. Open (for the main session): grc.txt gets
  `syntax: automatic` because the entry has no `treebank` (`Play.syntax_automatic`); for this
  play that label is untrue, so before the build either give the Play a way to say the trees
  are hand-made but of another text (a new field, as the review list's HAND_ANALYSES and
  LEMMA_FIXES mend the worst of the 194 words), or accept "automatic" knowingly. Not decided
  here. **Settled 2026-11-17** (finishing agent): `Play.syntax_note`; grc.txt says "hand-made
  (Pedalion trees, with GLAUx), made on a later edition of the text than Murray's", and the
  app's automatic-analysis notice (shown only for the value "automatic") is not shown.

* 2026-11-17 (finishing agent): the Medea's sections are Earle's divisions (§ 32), the parodos
  from 131 (his proöde) though Perseus begins the choral section with the anapaests at 96; the
  notes of Earle's commentary stay in his printed order (out of numeric order in nine places: a
  range note before its single notes, "131 ff." after 131-133); the apparatus item without a
  number after 143 (on his supplement in 144) stays under 143 as printed; an exclamation printed on its
  own line (292, 386, 1009, 1056) carries the number Murray's apparatus gives it and the rest of
  the verse the letter; words Murray divides across two lyric lines (ὀρ-|γὰς, μό-|χθων) stand
  whole in the line where they begin; Coleridge's speaker attributions are kept where Paley's
  text differs from Murray's (945, 1004a); a middle stage direction of the translation stands
  after its segment (895).
* 2026-11-17: the author's build: an ignored list app/author-packs.txt (not a Gradle property),
  release tasks refused while it names a text; the private packs live in private/app/packs/
  through links made by `private-setup <slug> --pack`.

## For the author

* **Which printing of Murray's vols II and III to read.** Perseus's scans (vol. II 1962, vol.
  III 1925-1946 printings of the 1913 editions) keep the print and the check text one edition;
  from 2028 any printing of Murray's text is free in Norway, so the printing matters only for
  agreement with Perseus and for scan quality. You offered to look on Google Books and
  HathiTrust (the research file's "Not done or not verified").
* **Death years not found** (these editors are avoided until found): W. E. Long (Cyclops,
  b. 1862), A. R. F. Hyslop (Andromache), John Bond (Hecuba), C. H. St. L. Russell (Hecuba,
  b. 1862), A. W. Upcott (Hecuba), C. H. Keene (Electra, b. 1847; surely dead before 1955, year
  unseen), C. E. S. Headlam (b. 1864), O. R. A. Byrde (Heracles).
* **The release on 2028-01-01**: a reader release with the plays built, held ready and published
  that day; the products (`euripides_<slug>_murray`) created in Play Console beforehand and
  activated that day; until then the plays only in your private build.
* **Product id of the Electra**: the rule gives `euripides_euripideselectra_murray` (the slug
  avoids texts/electra, Sophocles'); `euripides_electra_murray` would read better, and a product
  id can never be changed: say which before the Electra is built.
