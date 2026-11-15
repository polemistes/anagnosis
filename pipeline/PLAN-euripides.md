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

**What the app side will need (not done; Kotlin and Gradle were not touched).**
* A **private build** of the reader for the author's own phone: it bundles
  `data/catalog-author.json` instead of `data/catalog.json` (androidApp's `copyBundle` takes
  catalog.json today) and includes the private asset packs. Its pack list must live outside the
  public files, e.g. a Gradle file under `private/app/` read by app/settings.gradle.kts and
  androidApp/build.gradle.kts only when it exists, or the private texts installed by hand as
  downloaded texts (data/<slug>.sqlite into the app's download folder with its catalog entry,
  as the text apps do). The private packs themselves (`app/packs/<slug>/build.gradle.kts`) are
  ignored by name, or live under `private/` with a link.
* The **public** pack lists (settings.gradle.kts, androidApp's `assetPacks`) must not name a
  held-back text; `check` reports it if they do.
* On 2028-01-01: move the plays' folders from `private/` into the public repository (replace
  the links by the folders), remove the slugs from `PRIVATE_SLUGS` and the .gitignore block,
  add the packs to the public lists, run `catalog` (the release date has passed), build and
  publish a reader release that day; activate the products in Play Console that day.

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
| 1 | medea | Medea | tlg003 | I | n103: text leaves 105-161 | M. L. Earle, American Book Co. 1904 (d. 1905), cu31924079583609, notes under the text in two columns (leaves 80-254), introduction leaves 14-71 | eng2 | GLAUx 0006-003; Pedalion hand-made trees (compare first) | euripides_medea_murray |
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
