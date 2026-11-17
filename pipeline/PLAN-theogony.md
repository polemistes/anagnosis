# Hesiod's Theogony

Started 2026-11-04 on the author's word ("start on the Theogony only for now"), after the
assessment of the Hesiod sources (Works and Days and the Shield may follow later as their own
texts). The Theogony is built as a tenth entry of the drama pipeline: `drama.PLAYS["theogony"]`,
the same modules, checkers, agents' briefs and steps as `pipeline/PLAN-drama.md`, whose rules
hold here unless this file says otherwise. Tick the steps off under **Progress**, write every
choice under **Decisions**, commit after each step. The work may be cut off at any moment: every
step saves to disk as it goes and can be run again.

## Decisions already taken

| what | source |
|---|---|
| Greek text and critical apparatus (one edition) | A. Rzach, Hesiodi carmina, Leipzig, Teubner, 1908 (the editio minor, revised; Rzach d. 1935). Scan hesiodicarminare00hesi (Toronto, 500 ppi, jp2): sigla ("Notae librorum") leaf 12, text pp. 3-50 = leaves 13-60 (leaf = page + 10); preface pp. III-V leaves 7-9 |
| check text (never shipped) | Perseus tlg0020.tlg001.perseus-grc2 = Evelyn-White's Loeb text (1914), itself based on Rzach |
| syntax | AGDT tlg0020.tlg001.perseus-grc1.tb.xml, hand-made and fully second-annotated (8,234 words), aligned to Rzach's words |
| translation | H. G. Evelyn-White (Loeb 1914), Perseus tlg0020.tlg001.perseus-eng2, by line; his footnotes are left out as for every Perseus translation |
| commentary | F. A. Paley, The Epics of Hesiod, 2nd ed., London, Whittaker, 1883 (d. 1888). Scan epicsofhesiodwit00hesiuoft (Toronto, 400 ppi, jp2; hidden leaves 118-119 and 272-273): the Theogony pp. 171-276 = leaves 223-328, each page Paley's text, a digamma band, his critical notes, then his commentary in two columns. Only the commentary is used |
| introduction | Paley's preface in full (pp. v-xliv = leaves 11-50: Hesiod and Homer, the authenticity of the poems, his manuscripts, the digamma) and his "Epitome of the Theogony" (pp. 167-170 = leaves 219-222: a summary by line ranges and a page on the poem's date and growth) |
| slug, product | `theogony`, Θεογονία, product id `hesiod_theogony_rzach`, €3, google_play: yes |

* **Same edition for text and apparatus**: Rzach's text and Latin apparatus ship. Paley's own
  text, digamma band and critical notes do not (his notes cite his text; where his lemma differs
  from Rzach's word the note still goes under its line).
* Rzach prints θ as ϑ, and ϱ, ϐ in places: written θ, ρ, β. His elision mark and raised stop
  are written ʼ and ·. Lines he brackets as interpolated keep their brackets ([ ]); the Metis
  fragment (Perseus 929a-929t) follows the print, whatever it is.
* Rzach groups the verses in paragraphs with blank lines: the text format has no paragraph mark,
  so they are not recorded; the sections come from Paley's Epitome at step 8 (or none).
* Not usable: West (1966), Solmsen's OCT, Jacoby (1930, d. 1959), Aly (1913, d. 1967), Most's
  Loeb, Lattimore, Wender; Mazon's Budé (d. 1955) is free in Norway since 2026 but has no scan.

## Steps

As PLAN-drama.md "Steps for each play", with the play's slug `theogony`:

2. Leaves: done at the start (see the table; drama.py).
3. `drama-pages theogony fetch|ocr`, then `draft`; read the summary; fix the module if more than
   70 % of the lines are flagged.
4. Text and apparatus batches (six pages each, INSTRUCTIONS-text.md with its Rzach section),
   checker, then the residual pass (RESIDUALS.md).
5. `merge-drama theogony`, merge log, review list (drama_fixes.py), `check`, ten verses by eye.
6. Paley's notes: `drama-prose theogony notes fetch|ocr|draft`, batches of eight pages
   (INSTRUCTIONS-prose.md with its Paley section), checker, merge again.
7. Introduction: the Epitome (and the preface if chosen), `drama-prose theogony intro …`.
8. Translation, sigla.md (from leaf 12, with the preface's classes Ω Ψ Φ), glossary.md (the
   Theogony's catalogues of names: Nereids, Oceanids, rivers, Titans; expect many), shortdefs.tsv,
   about.md, texts/README.md section, play/README.md row.
9. `build --only theogony`, `check`, the asset pack app/packs/theogony/, `catalog`; then the
   emulator check of PLAN-drama.md step 10 for this one text. A reader release is the author's
   call (none is planned for the Theogony alone).

## Progress

- [x] Step 2: leaves (2026-11-04)
- [x] Step 3: draft (2026-11-04): 48 pages, 1014 verses, 190 flagged (19 %), eight batches
- [x] Step 4: text and apparatus (2026-11-04): eight batches, then the residual pass
- [x] Step 5: merge (2026-11-04): 1022 verses, 642 apparatus items under 468 lines, 6922 words, all with lemmas
- [x] Step 6: Paley's notes (2026-11-04): 13 batches checked, 500 notes, all placed
- [x] Step 7: introduction (2026-11-04): Paley's preface and Epitome, six batches checked
- [x] Step 8: translation, sigla, glossary (120), short definitions, aliases, about.md, READMEs (2026-11-04)
- [x] Step 9 (build): `build --only theogony` (data/theogony.sqlite 1.9 MB, version ff75082c99c755c0), catalog (16 texts), asset pack app/packs/theogony registered; `bundleDebug` builds (2026-11-04)
- [x] Step 9 (emulator check, 2026-11-04): bought in the debug shop, downloaded, opened; text, apparatus,
  manuscripts page, Paley's commentary, introduction, word sheet, syntax and reading aloud work; a changed
  bundle is fetched again. Found and fixed: the voice read the Theogony as Attic (`Play.pronunciation =
  "homeric"`, grc.txt's `pronunciation` key). The Theogony is done; a reader release is the author's call.

## Decisions already taken

| what | source |
|---|---|
| Greek text and critical apparatus (one edition) | A. Rzach, Hesiodi carmina, Leipzig, Teubner, 1908 (the editio minor, revised; Rzach d. 1935). Scan hesiodicarminare00hesi (Toronto, 500 ppi, jp2): sigla ("Notae librorum") leaf 12, text pp. 3-50 = leaves 13-60 (leaf = page + 10); preface pp. III-V leaves 7-9 |
| check text (never shipped) | Perseus tlg0020.tlg001.perseus-grc2 = Evelyn-White's Loeb text (1914), itself based on Rzach |
| syntax | AGDT tlg0020.tlg001.perseus-grc1.tb.xml, hand-made and fully second-annotated (8,234 words), aligned to Rzach's words |
| translation | H. G. Evelyn-White (Loeb 1914), Perseus tlg0020.tlg001.perseus-eng2, by line; his footnotes are left out as for every Perseus translation |
| commentary | F. A. Paley, The Epics of Hesiod, 2nd ed., London, Whittaker, 1883 (d. 1888). Scan epicsofhesiodwit00hesiuoft (Toronto, 400 ppi, jp2; hidden leaves 118-119 and 272-273): the Theogony pp. 171-276 = leaves 223-328, each page Paley's text, a digamma band, his critical notes, then his commentary in two columns. Only the commentary is used |
| introduction | Paley's preface in full (pp. v-xliv = leaves 11-50: Hesiod and Homer, the authenticity of the poems, his manuscripts, the digamma) and his "Epitome of the Theogony" (pp. 167-170 = leaves 219-222: a summary by line ranges and a page on the poem's date and growth) |
| slug, product | `theogony`, Θεογονία, product id `hesiod_theogony_rzach`, €3, google_play: yes |

* **Same edition for text and apparatus**: Rzach's text and Latin apparatus ship. Paley's own
  text, digamma band and critical notes do not (his notes cite his text; where his lemma differs
  from Rzach's word the note still goes under its line).
* Rzach prints θ as ϑ, and ϱ, ϐ in places: written θ, ρ, β. His elision mark and raised stop
  are written ʼ and ·. Lines he brackets as interpolated keep their brackets ([ ]); the Metis
  fragment (Perseus 929a-929t) follows the print, whatever it is.
* Rzach groups the verses in paragraphs with blank lines: the text format has no paragraph mark,
  so they are not recorded; the sections come from Paley's Epitome at step 8 (or none).
* Not usable: West (1966), Solmsen's OCT, Jacoby (1930, d. 1959), Aly (1913, d. 1967), Most's
  Loeb, Lattimore, Wender; Mazon's Budé (d. 1955) is free in Norway since 2026 but has no scan.

## Steps

As PLAN-drama.md "Steps for each play", with the play's slug `theogony`:

2. Leaves: done at the start (see the table; drama.py).
3. `drama-pages theogony fetch|ocr`, then `draft`; read the summary; fix the module if more than
   70 % of the lines are flagged.
4. Text and apparatus batches (six pages each, INSTRUCTIONS-text.md with its Rzach section),
   checker, then the residual pass (RESIDUALS.md).
5. `merge-drama theogony`, merge log, review list (drama_fixes.py), `check`, ten verses by eye.
6. Paley's notes: `drama-prose theogony notes fetch|ocr|draft`, batches of eight pages
   (INSTRUCTIONS-prose.md with its Paley section), checker, merge again.
7. Introduction: the Epitome (and the preface if chosen), `drama-prose theogony intro …`.
8. Translation, sigla.md (from leaf 12, with the preface's classes Ω Ψ Φ), glossary.md (the
   Theogony's catalogues of names: Nereids, Oceanids, rivers, Titans; expect many), shortdefs.tsv,
   about.md, texts/README.md section, play/README.md row.
9. `build --only theogony`, `check`, the asset pack app/packs/theogony/, `catalog`; then the
   emulator check of PLAN-drama.md step 10 for this one text. A reader release is the author's
   call (none is planned for the Theogony alone).

## Progress

- [x] Step 2: leaves (2026-11-04)
- [x] Step 3: draft (2026-11-04): 48 pages, 1014 verses, 190 flagged (19 %), eight batches
- [x] Step 4: text and apparatus (2026-11-04): eight batches, then the residual pass
- [x] Step 5: merge (2026-11-04): 1022 verses, 642 apparatus items under 468 lines, 6922 words, all with lemmas
- [x] Step 6: Paley's notes (2026-11-04): 13 batches checked, 500 notes, all placed
- [x] Step 7: introduction (2026-11-04): Paley's preface and Epitome, six batches checked
- [x] Step 8: translation, sigla, glossary (120), short definitions, aliases, about.md, READMEs (2026-11-04)
- [x] Step 9 (build): `build --only theogony` (data/theogony.sqlite 1.9 MB, version ff75082c99c755c0), catalog (16 texts), asset pack app/packs/theogony registered; `bundleDebug` builds (2026-11-04)
- [ ] Step 9 (emulator check): **resume here.** Interrupted on 2026-11-04 because the author shut the
  computer down; nothing else is open. Do: emulator `anagnosis` headless, `./gradlew
  :androidApp:bundleDebug`, bundletool `build-apks --local-testing` and `install-apks` (app/README.md),
  buy the Theogony in the debug shop, open it, read a page, open the apparatus, a Paley note, the
  introduction, the sigla, one sentence's syntax, play a line aloud; fix what is wrong; then
  `adb emu kill` and `./gradlew --stop`. A reader release with the Theogony is the author's call.

## Decisions

(append dated entries)

* **2026-11-04, modules.** `Play.app_bare_numbers`: Rzach's apparatus items begin with the bare
  line number ("215 ἧς scripsi"); a bare number counts as an item number unless it stands in the
  right margin (a verse number). `Play.notes_layout = "paley"`: on Paley's pages the commentary
  is what stands under the last line that crosses the page's middle above the first run of
  column lines (his rules are too short for the rule finder). The Perseus translation's footnotes
  left two words glued (quick-glancing<note/>Aphrodite): `perseus_translation` now keeps a space.
* **2026-11-04, step 3: draft.** The first draft flagged 56 % of the verses: Tesseract reads
  Rzach's Teubner θ as ϑ and κ as χ throughout, and Evelyn-White's transpositions in the check
  text (214 before 213, 427 before 426, 434 before 430-433) pulled words onto wrong verses.
  New Play fields: `ocr_fold` (ϑ ϱ ϐ ϰ put right in the OCR), `skel_fold` ("χκ": χ and κ count
  as one letter in the matching, the draft, and the residuals; a real κ/χ difference between
  Rzach and Perseus would go unflagged, a risk accepted), `perseus_order="numeric"` (the check
  text in the order of its numbers, which is Rzach's), `perseus_drop` (Perseus 929a-929t, the
  Metis fragment from Galen: Rzach's p. 46 (leaf 56) goes from 929 straight to 930, so it is
  left out of the check text, and of the text). Result: 1014 verses, 190 flagged (19 %), the
  apparatus found on all 48 pages. Eight verses are missing from the draft (37, 38, 407, 426,
  434, 553, 631, 745): Tesseract read only their accents (Rzach's accents stand high), so their
  words hang on the verse above, flagged "not found … guess"; the agents split them off.
* **2026-11-04, the introduction.** Paley's preface (pp. v-xliv) is the edition's introduction to
  all three poems; the brief's rule is the editor's introduction in full, so it goes in whole
  (about Hesiod and Homer, the Theogony's authenticity, Paley's fourteen manuscripts, a long
  essay on the digamma), followed by the Epitome of the Theogony. Seen on page images n10 (p. v,
  leaf 11) and n49 (p. xliv, leaf 50); leaf 51 is the half-title of the Works and Days.
* **2026-11-04, step 4.** Rzach himself transposes four verses, with his margin numbers beside
  them: 408 before 407, 427 before 426, 434 before 430-433 (Evelyn-White follows him there), 631
  before 630; the text keeps his order and `check` warns of it. The check text's numeric order
  (step 3) was therefore right except at those places, where the agents followed the page. Crates'
  variant verse 142b, which Rzach prints apart below 146 between rules, is a `!` line after 146.
  On twelve pages the apparatus crop stopped a line short of the page foot (a last line Tesseract
  read too badly to count as print): `Play.app_to_foot` makes the crop run to the foot; the
  residual agents compared every page's apparatus end with the print and found nothing missing
  (the first round had read those lines from the whole page). Papyrus capitals: the lunate
  epsilon written Ε, the lunate sigma C, as the brief says.
* **2026-11-04, step 5.** The Hesiod treebank cites its lines as book.line ("1.120"):
  `read_agdt(…, book_cites=True)` for tlg0020. Evelyn-White's translation of the Metis fragment
  (Perseus 929a-929t) is left out with the verses (`perseus_drop`). Review list 128 words: 16
  hand analyses and 2 lemma fixes (Βριάρεως capitalised, Χείρων), plus two treebank errors the
  reviewer saw outside the list (116 γένετʼ was γενέτης, 282 ὅτʼ was ὅτι). Ten random verses
  compared with the page by eye: 109, 262, 273, 309, 328, 340, 854, 965, 976, 1000, all as printed.
* **2026-11-04, step 8: no sections.** The Perseus TEI has only unlabelled "card" milestones, and
  Paley's Epitome gives ranges with long descriptions ("1-35. The Muses after dancing on Mount
  Helicon come by night to Hesiod and confer on him the gift of poetry …"), not titles: section
  labels would be our own words. The Theogony ships without sections; the Epitome, in the
  introduction, is its outline. Glossary: 120 names; 19 treebank lemmas that are misspelt or
  garbled (Ι{ππώ, Ἀφροδ́ιτη, Καλλιπόη …) corrected in LEMMA_FIXES rather than aliased, so that the
  reader finds their glossary entries; 426 οὐδʼ (οὐ+??) and 976 Ἀγαυὴν (Agave, not ἀγαυός) by hand.
  `check`: every lemma found, every lemma glossed.
* **2026-11-17, a free text** (the author's decision): the Theogony is added in the reader without
  paying. about.md says `# free: yes`; the catalogue entry carries `"free": true`; no
  `google_play` mark; the product id stays in about.md, unused. The database is not rebuilt for
  it (the catalogue only; version unchanged).
* **2026-11-17, words printed apart that the trees have as one** (the author: the meaning is the
  same; mark them as a unit so the syntax link shows). The review divided verse 2 as Rzach prints
  it, αἵ θʼ, where Perseus and the hand-made tree have αἵθʼ (lemma ὅστε, subject); the two words
  then stood outside the tree. Now (`odyssey.align(units=True)`, switched on by
  `Play.tree_units`, for the Theogony only, since it changes tokens and so a text's version):
  two to four consecutive words of the text that are one treebank word when joined are a unit on
  that word's node. **The form**: the first word carries the node (sentence, word id, relation,
  head); each further word has the same sentence and the word id `=N`, no relation or head. Why:
  the reader makes one node per word id; two words with the same id would both be shown as
  nodes under the same head, each called the subject, and what depends on them twice. With `=N`
  the present reader gives the second word no node (the id is no number) but knows its sentence,
  so a long press on either word opens the tree, and the word sheet of the first names its role.
  Each word keeps its own lemma and form (αἵ: ὅς; θʼ: τε); the tree's lemma ὅστε is not shown
  anywhere. **Twelve places**: 2 αἵ θʼ, 126 ἑʼ αὐτῇ, 218 αἵ τε, 220 αἵ τʼ, 395 ὅς τις, 754 ἔς τʼ,
  783 ὅς τις, 786 ὅ τʼ, 831 ὥς τε, 905 αἵ τε, 931 ὅς τε, 935 οἵ τʼ. At 754 (ἔς τʼ ἂν ἵκηται, the
  tree's ἔστʼ "until") ἔς is no preposition: its lemma is ἔστε by hand (`HAND_ANALYSES`). The
  tree words are no longer among the extra nodes. A dry count for the other texts with trees
  (from their files as they are; nothing changed): Odyssey 16, Lysias 8, Eumenides 4,
  Agamemnon, Choephoroi and Clouds 3 each, Oedipus Tyrannus and Philoctetes 2, Trachiniae 1,
  the rest none; a few of them are other readings spelled with the same letters (Choephoroi 492
  ᾧ σʼ for ὡς, Odyssey 12.61 δʼ ἦ for δή), so they want a look before the rule is switched on
  there. **For the reader, to make it a true unit** (not needed for the link): in `Syntax.build`
  a token whose word id begins with `=` joins the node of that number: the node's form is the
  words joined (αἵ θʼ), and `nodeFor` answers with that node for either word, so both are
  highlighted and the second's word sheet names the role too. Version 715628c66e892934.
* **2026-11-17, the trees' text** (the author: "The most important thing is that the reader is
  made aware that the syntax tree is based on a (slightly) different text. Then provide the
  pertinent specific information."). The trees are the treebank's, made on the Perseus text of
  the poem (Evelyn-White's Loeb, 1914), not on Rzach's. Module `syntax_text.py`; switched on by
  `Play.syntax_text`, for the Theogony only.
  * **The text-level fact**: grc.txt's header `# syntax-text: the Perseus Digital Library's text
    of the poem (H. G. Evelyn-White's Loeb edition, 1914)` becomes the database's meta key
    `syntax_text`; about.md's `# syntax_text:` puts it into the catalogue.
  * **The word-level facts**: the file `syntax-text.tsv` (texts/README.md) and, in the
    database, the table `syntax_text_words (id, kind, token_id, sentence, word_id, tree_form,
    tree_lemma, extent)` with the meta key `syntax_text_words` (the number of rows). **Why a
    table of its own and meta keys**: the reader's queries name their tables and columns; a new
    column in `tokens` or `sentence_nodes` would be missing from the databases already on the
    phones and from the seven texts on sale, and the reader's generated code would fail on them.
    A table the present reader never asks for is invisible to it; a later reader asks for it
    only where the meta key is there (a missing meta key reads as null, as `syntax_by_book`
    does). The table exists only in a text that has the record, so no other text's content or
    version changes. The schema number is not raised.
  * **The Theogony's numbers** (6,923 words): 6,794 are the trees' own words (the same letters);
    **unit 48** (24 words in the twelve places where our text divides a tree word; 24 words the
    treebank divides and we print as one: οὐδέ, μηδέ, οὔτε, a matter of the treebank's habit, not
    of the text); **reading 46**; **absent 35** (18 in passages: verses 576–577, which Rzach
    brackets and the trees' text has not, with the opening of 578, and two places where the two
    texts word a phrase in another number of words, 48 θεαὶ † λήγουσαί τʼ / καὶ ἐκλήγουσαι, 532
    ταῦτά γʼ ἄρʼ / ταῦτʼ ἄρα; 17 single words, 6 of them readings not kept); **unprinted 152**
    (135 in passages: above all the 129 words of the verses on Hera and Hephaestus after 929 that
    Rzach does not print; 17 single words).
  * **The readings looked at** (`TREE_READINGS["theogony"]`, 52, each with its reason): **46
    kept**, where the inherited role fits our word: the same form spelled otherwise or without
    the movable ν or elided (30: τέκε/τέκεν, μειχθεὶς/μιχθεὶς, Χίρων/Χείρων), the same name (6), and ten
    where another word or form stands in the same construction (31 ἀοιδὴν for αὐδὴν, object of
    ἐνέπνευσαν; 56 νύκτας for νυκτὸς, an adverbial either way; 240 μεγήριτα for μεγήρατα; 282
    τᾷ for τῷ; 304 χθόνα for χθονὶ; 399 ἔδωκεν for δέδωκεν; 401 ἕο for ἑοῦ; 639 παρέσχεθον for
    παρέσχεθεν; 659 αὖτις for ἐξαῦτις; 904 ἧς for ᾗ). **6 dropped**, where it does not: 295
    οὐδὲ (the trees' οὐδὲν is an adverbial accusative), 485 τᾷ (the trees' τῷ is an adverb), 497
    καταπίνων (the trees' κατέπινεν is the verb of a relative clause), 659 δεῦρʼ (the trees' δʼ
    is the connective), 860 Ἀίτνης (the trees' ἀιδνῇς is an adjective with another noun), 961 δή
    (the trees' δέ is the connective). A dropped word has no link; the trees' word stays in the
    tree as not printed. Eight more pairs were no readings at all (the trees' form carries an
    editor's bracket: [οἵ, [ἀθανάτων): they are the trees' own words.
  * **Found on the way: three verses the editions place differently** (214, 407, 631: among the
    four "printed verse order" remarks) stood outside the trees, and their tree words as not
    printed. A run of three or more words of ours that stands word for word among the tree
    words left over is now found there (`odyssey.align`, with `units`): 16 words linked.
  * **The other texts** (not set; each to be confirmed from its sources before it is switched
    on): the Odyssey (Allen's Oxford text; trees on Perseus's text, Murray's Loeb 1919), the
    seven plays of Sophocles (Jebb; trees on Perseus's text of Sophocles), the Oresteia
    (Sidgwick; Perseus's text, Smyth's Loeb), Lysias (Hude; Perseus's text, Lamb's Loeb, for the
    hand-made and the automatic trees alike), the Clouds (Starkie's text; GLAUx on Perseus's
    text, Hall and Geldart) and A True Story (Nilén; GLAUx on Perseus's text, Harmon's Loeb)
    have trees made on another edition. The Symposium and the Gorgias (Burnet in both), the
    Shepherd (Lake in both) and the New Testament (the SBL text in both) have trees made on the
    same edition's digital text: they would need at most the word-level record. Review lists'
    "reads X where the trees have Y": Odyssey 654, Lysias 209: those are the pairs that would
    want decisions.
  * Version d2f7cbb023efbec9; no other text's database changed (checksums).
