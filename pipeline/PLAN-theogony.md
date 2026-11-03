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
| introduction | Paley's "Epitome of the Theogony" (pp. 167-170 = leaves 219-222: a summary by line ranges and a page on the poem's date and growth); whether his general preface (pp. iii-xliv, mostly on the Works and Days and the digamma) is added is settled at step 7 |
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
- [ ] 3 · 4 · 5 · 6 · 7 · 8 · 9

## Decisions

(append dated entries)

* **2026-11-04, modules.** `Play.app_bare_numbers`: Rzach's apparatus items begin with the bare
  line number ("215 ἧς scripsi"); a bare number counts as an item number unless it stands in the
  right margin (a verse number). `Play.notes_layout = "paley"`: on Paley's pages the commentary
  is what stands under the last line that crosses the page's middle above the first run of
  column lines (his rules are too short for the rule finder). The Perseus translation's footnotes
  left two words glued (quick-glancing<note/>Aphrodite): `perseus_translation` now keeps a space.
