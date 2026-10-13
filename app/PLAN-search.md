# Search: implementation plan

The reader gets a search: free text in the Greek, the translations, the commentaries and the
reader's own notes, and a lemma search that finds every inflected form of a word. Both work in
the open text or across all installed texts. Decided with the author on 2026-10-13. This file
is the brief: follow it step by step, tick the steps off under Progress, and commit after each
step (the plan file with it). All steps are routine and are done on Opus 5.5. If a step turns
out to need a judgement the brief does not settle, say so rather than guess.

Nothing in the pipeline or the text databases changes: every token already carries an indexed
`lemma_key`, and the Greek lines and the translation paragraphs are plain NFC strings. The
folding of accents and case is done in the app. No version bump: 0.3.0 (version code 5) has
not been uploaded, and search goes into it.

Decisions already taken (do not reopen them):

* The search page keeps its segmented switch and gets four modes: Dictionary, Analysis (today
  "Word analysis"), Text and Lemma. The front page has the same four.
* Text mode is for free text and phrases. Latin letters search the English until a tap turns
  them into Greek by the transliteration scheme; never both at once. Four options, all off by
  default: exact accents, exact case, whole words, regular expression. Four sources, all on by
  default: Greek, translation, commentary (the apparatus counts as commentary), my notes.
* Lemma mode is a search of its own: a headword typed with Latin or Greek letters, accents
  ignored, with suggestions as you type (the lemmas of the texts in scope that begin so, each
  with its gloss and its number of occurrences); a suggestion opens its occurrences. An
  inflected form that is no lemma gets the analyser's lemmas offered instead. The word sheet
  gets an Occurrences button that lands here.
* Scope: this text, or all installed texts. No per-page scope. Results of an epic or the New
  Testament are listed under book headings.
* A hit opens the reader at its line with the match highlighted until the page is turned. A
  translation hit opens the English; a commentary hit opens the Apparatus or Commentary sheet
  of that page; a hit in one of the reader's notes opens the note. Back from there returns to
  the search with its results.
* The search state (query, mode, options, results) lives for the whole session, so that
  leaving the search for a hit and coming back finds everything as it was.

Measured on the Odyssey (the largest text but the New Testament) in a Python prototype of the
folding and scanning, so that no step needs to worry about speed: the Greek is 527 k characters
in 12 111 lines and the translation 696 k characters; folding the whole text once took 123 ms;
one scan for καί found 2 493 hits in under 1 ms. Loading the lines, paragraphs and notes of a
text without its tokens takes about 100 ms. All installed texts together fit in a few tens of
megabytes, which is less than the loaded works already take.

## Folding (`data/TextFold.kt`, object `TextFold`)

`fold(s: String, ignoreAccents: Boolean, ignoreCase: Boolean): String` maps every character to
exactly one character, so that an offset in the folded string is the same offset in the
original and a hit can be highlighted without any bookkeeping. Rules, per character:

* With `ignoreAccents`: a Greek letter with diacritics becomes its base letter, case kept
  (Ἄ → Α, ᾤ → ω, ῥ → ρ, ϊ → ι). Use `GreekNormalizer`'s table: add to it a public
  `baseLetter(c: Char): Char?` that returns the lower-case base for a letter in the table
  (and null otherwise); the fold re-uppercases the base when the original `isUpperCase()`.
  A Latin letter with an accent becomes its plain letter likewise: a table in `TextFold`
  for àáâãäåā èéêëē ìíîïī òóôõöø ùúûüū ýÿ ç ñ and their capitals (ligatures æ œ stay as
  they are; no translation uses them).
* With `ignoreCase`: `lowercaseChar()` (always one character; never `String.lowercase()`).
* Always: final sigma ς → σ; the apostrophes ’ ‘ ʼ ᾽ ᾿ → ' (the texts write elision with
  ʼ U+02BC and the translations use ’); the quotes “ ” „ → "; a newline → space (so that a
  phrase runs over a line end). Everything else unchanged.

The same function folds the query. A pattern (regex mode) is folded by `foldPattern`, which
applies the same mapping to every character except the one after a backslash, so that `\b`
and `\s` survive while literal letters and ranges like `[Α-Ω]` follow the text.

## The engine (`data/TextSearch.kt`)

Pure Kotlin, no database, no Compose, fully unit-tested.

    enum class SearchSource(val label: String) { GREEK("Greek"), TRANSLATION("Translation"), COMMENTARY("Commentary"), NOTES("My notes") }

    data class SearchOptions(val exactAccents: Boolean = false, val exactCase: Boolean = false, val wholeWords: Boolean = false, val regex: Boolean = false)

    /** One searchable unit: a Greek line, a translation paragraph, a commentary note or a note of the reader's. */
    class SearchUnit(val nInt: Long, val nSub: String, val text: String, val extra: Long = 0)   // extra: note id (NOTES), commentary id (COMMENTARY)

    /** The units of one source of one text, joined by "\n" into one string, with each unit's start offset. */
    class SearchDoc(val slug: String, val source: SearchSource, val label: String, val units: List<SearchUnit>) {
        val text: String; val starts: IntArray
        fun folded(options): String   // cached: the last (accents, case) combination asked for
        fun unitAt(offset: Int): Int  // binary search over starts
    }

    class SearchHit(val slug: String, val source: SearchSource, val label: String, val nInt: Long, val nSub: String,
                    val unitText: String, val start: Int, val end: Int, val extra: Long)   // start/end within unitText

    class SearchResult(val hits: List<SearchHit>, val truncated: Boolean, val error: String?)

    object TextSearch {
        const val MAX_HITS = 2000
        fun search(docs: List<SearchDoc>, query: String, options: SearchOptions, isActive: () -> Boolean): SearchResult
        fun excerpt(hit: SearchHit, whole: Boolean): Excerpt   // Excerpt(text, start, end): the match's place in the excerpt
    }

`label` names the source on a hit: "" for the Greek, "Translation" (every text has one
translation; a surname would give "Committee" for the New Testament), "Apparatus" or
"Commentary" (`NoteKind.label`), "Note".

**Scanning.** The needle is `TextFold.fold(query, …)`, trimmed; empty gives no hits. Plain
mode: `indexOf` in a loop, advancing past each match. Regex mode: `Regex(foldPattern(query))`,
an `IllegalArgumentException` giving `error = "Not a valid pattern"`; matches of length zero
are skipped. The regex runs on a `CancellableText(folded, isActive): CharSequence` whose `get`
calls `isActive()` every 4 096 characters and throws `CancellationException` when it is false,
so that a runaway pattern stops at the next keystroke (java.util.regex never checks
interrupts). `isActive` is checked between documents as well. With `wholeWords`, a match is
kept only when the character before it and the character after it are not letters
(`isLetter()`); the same test in both modes. A match's unit is `unitAt(start)`; a phrase that
runs into the next unit belongs to the unit where it starts, with `end` clamped to that unit's
length. Scanning stops at `MAX_HITS` with `truncated = true`.

**Excerpt.** For a Greek line the whole unit text, with a leading "| " dropped and the offsets
moved by 2 (the braces of a speaker label stay; they are rare). For the other sources a window
of 60 characters before the match and 80 after, widened to whole words, with "…" at a cut end.

## Data (`AnagnosisRepository`, `Anagnosis.sq`, `Notes.sq`)

New queries in `Anagnosis.sq`:

    selectAllNotes: SELECT id, n, from_n_int, to_n_int, html FROM commentary_notes WHERE commentary_id = ? ORDER BY ord;
    selectLemmaCounts: SELECT lemma_key, MIN(lemma) AS lemma, COUNT(*) AS n FROM tokens GROUP BY lemma_key;
    selectAliases: SELECT * FROM lemma_aliases;
    selectOccurrences:
    SELECT tokens.start, tokens.end, lines.n_int, lines.n_sub, lines.text
    FROM tokens JOIN lines ON lines.id = tokens.line_id WHERE tokens.lemma_key = ? ORDER BY lines.ord, tokens.ord;

(SQLite takes `tokens.end` unquoted; should SQLDelight's parser not, write `tokens."end"`.)

In `Notes.sq`: `selectAll: SELECT * FROM notes ORDER BY text_slug, from_n_int, from_n_sub, from_word, id;`

`loadWork(slug, light: Boolean = false)`: with `light`, no tokens, nodes, translations,
commentaries or note starts are read (empty maps and lists); lines and sections are. The light
`WorkData` gives the search its citations (`citation`, `lineLabel`, `range`), its `books` and
its numbering flags without the seconds the tokens take.

`plainText(html: String): String` in `ui/HtmlText.kt`, next to `htmlToAnnotated`: every tag
removed (`TAG`), with `</p>`, `<br>` and `</li>` replaced by a space first, entities unescaped
(`unescape`), whitespace collapsed.

**Corpora.** `class TextCorpus(val slug: String, val work: WorkData, val docs: List<SearchDoc>)`,
one per text, built once and kept in `private val corpora = HashMap<String, TextCorpus>()`:

* `corpus(slug)`: the light work; one `SearchDoc` for the Greek (`lines` in order, unit text
  `Lines.text`); one per translation (its segments, unit text `text`, nInt/nSub the segment's
  `from_n_int`/`from_n_sub`); one per commentary (`selectAllNotes`, unit text
  `plainText(html)`, nInt `from_n_int`, extra the commentary id, label by `kind()`).
* `notesDoc(slug)`: built fresh at every search from `notes(slug)` (the body is searched; the
  quote is Greek the Greek source finds), nInt/nSub from the note's `from`, extra the note id.
  Not cached: notes change.
* `searchTexts(slugs: List<String>, query, options, sources: Set<SearchSource>, isActive): SearchResult`:
  the docs of each slug in the order given, filtered by source, and `TextSearch.search`.

**The lemma index.** `data/LemmaIndex.kt`:

    class LemmaEntry(val slug: String, val key: String, val lemma: String, val count: Int)
    class LemmaRow(val spellings: List<String>, val keysBySlug: Map<String, List<String>>, val countsBySlug: Map<String, Int>) {
        val total: Int; val looseKey: String   // of the first spelling
        var gloss: String?                      // filled for the rows shown
    }
    object LemmaIndex {
        fun merge(entries: List<LemmaEntry>, aliases: Map<String, Map<String, String>>): List<LemmaRow>   // aliases by slug: lemma_key -> target_key
        fun suggest(rows: List<LemmaRow>, typed: String, limit: Int = 80): List<LemmaRow>
    }

`merge` joins keys with a union-find: every key to itself; a key to its alias target when the
target is a lemma of some text (Homeric ἠέλιος with ἥλιος); a key ending in -ομαι to the key
with -ω in its place when that exists (ἀποκρίνομαι with ἀποκρίνω; the New Testament has 353
such middles, the Odyssey 249, and the conventions differ). Keys that differ only in accent
are not joined (βίος, βιός). A row's spellings are its keys' lemmas, distinct, the most
frequent first; the row's `looseKey` is `GreekNormalizer.looseKey` of the first. `suggest`
converts the typed text with `Transliteration.toGreek` (the search's scheme) and takes its
`looseKey` and `prefixKey`; a row matches when any spelling's loose key starts with either;
rows whose loose key equals the typed key come first, then alphabetical by loose key.

In the repository: `lemmaEntries(slug)` from `selectLemmaCounts` and `selectAliases`, cached
per slug; `lemmaRows(slugs)` merged across the given texts (cached by the set of slugs);
`glossFor(row)`: the first short definition found for any of its keys, in the text's own
`short_definitions` then the lexicon's; `occurrences(row, slugs): List<SearchHit>` through
`selectOccurrences` for each of the row's keys in each text, source GREEK, in the order of
`slugs` then of the text, with `unitText` the line and `start`/`end` the token's.

## The search page (`ui/SearchScreen.kt`, `ui/App.kt`, `ui/HomeScreen.kt`)

**State.** `SearchState` is made once in `App` (`val search = remember { SearchState() }`) and
handed to `SearchScreen` and `HomeScreen`; `rememberSearchState` becomes
`SearchEffects(state, repository, settings, textSlug: String?, catalog)` (a composable that
only runs the `LaunchedEffect`). New fields:

    var mode: SearchMode                 // DICTIONARY("Dictionary"), ANALYSER("Analysis"), TEXT("Text"), LEMMA("Lemma")
    var thisText: Boolean = true         // scope: the text the search was opened from, when there is one
    var asGreek: Boolean = false         // Text mode: Latin letters are transliterated
    var options: SearchOptions
    var sources: Set<SearchSource>       // all four at first
    var textResult: SearchResult?        // Text mode
    var lemmaRows: List<LemmaRow>        // Lemma mode: suggestions
    var analysedLemmas: List<FormAnalysis>  // when the typed form is no lemma but the analyser knows it
    var chosen: LemmaRow?                // the row whose occurrences are listed
    var occurrences: List<SearchHit>
    var busy: Boolean                    // while corpora load (the first search across all texts)
    fun openLemma(lemmaKey: String, lemma: String)   // mode = LEMMA, query = lemma, chosen = the row holding the key (built from the key alone when none does)

Scope: `slugs = if (textSlug != null && thisText) listOf(textSlug) else installed texts in catalog
order`. The front page passes `textSlug = null`.

**The effect.** Keyed on everything that changes the result (mode, the folded query, options,
sources, scope, `chosen`, the scheme). `delay(60)`, then on `Dispatchers.Default`:

* TEXT: the query is the field's text as typed, or `Transliteration.toGreek` of it when
  `asGreek`. `busy = true` while corpora are built; `ensureActive()` between texts (the
  `isActive` passed to the engine is `{ coroutineContext.isActive }`).
* LEMMA with no `chosen`: `lemmaRows = suggest(lemmaRows(slugs), query)`, glosses filled for
  them; when the list is empty, `analysedLemmas = analyse(greekQuery)` distinct by lemma key.
  With `chosen`: `occurrences(chosen, slugs)`.
* The two old modes as now. A change of the field's text clears `chosen`.

**Controls (`SearchControls`).** The back button, when there is one, goes in a row of its own
above the mode switch, which is then full width in every case (four segments and the back
button do not share 411 dp). Under the field:

* All modes: the Greek-keyboard button as now. With a `textSlug`, in Text and Lemma modes, a
  two-segment switch "This text" | "All texts" (`thisText`).
* Text mode: the supporting text shows, when the field holds Latin letters and no Greek,
  "Search the Greek for λογοσ" as a small `TextButton` that sets `asGreek`; with `asGreek`,
  the Greek form and "Search the English instead". The scheme switch shows only with
  `asGreek`. Then a `FlowRow` of `FilterChip`s, 6 dp apart: "Exact accents", "Exact case",
  "Whole words", "Regex" (selected = on), and a second `FlowRow` of the four sources
  (selected = searched). The field's label is "Word or phrase"; its `imeAction` is Done.
* Lemma mode: the scheme switch as in Dictionary mode; field label "Lemma"; `imeAction`
  Search, which picks the first suggestion.
* Dictionary and Analysis: as now.

**Results (`searchResults`).** Items added to the `LazyListScope`, so the front page shows
them in its column as it shows the headword hits:

* Text mode: for each text with hits, a header (`labelLarge`, primary colour): the text's
  English title from the catalog (`titleEn.ifEmpty { title }`) when the scope is all texts,
  and the counts by source ("214 Greek, 12 translation, 3 commentary"); then the hits in text
  order (by `nInt`, `nSub`, source), under book sub-headers (`titleSmall`, muted,
  `Book.title`) when the text is `byBook`. A hit is a `Row`: the citation in the number style
  (`lineLabel` under a book header, else `citation`, at least 56 dp wide, muted) and a `Column`
  with the excerpt (`bodyMedium`, the match in bold) and, for the other sources, the label
  (`labelSmall`, muted). A tap calls `onOpen(hit)`. Before the first header: "Not a valid
  pattern" in the error colour when `error` is set; after the last: "More than 2000 matches;
  showing the first 2000" when truncated; "No matches." as now. A small
  `LinearProgressIndicator` under the controls while `busy`.
* Lemma mode without `chosen`: each row a `Row`: the spellings joined by " / "
  (`titleMedium`) with the gloss under it (`bodyMedium`, muted, one line, ellipsis), and the
  total at the right (`bodyMedium`, muted). A tap sets `chosen`. When `analysedLemmas` is
  shown instead, a line "No lemma begins so; the form can be:" and the analyses as in
  Analysis mode, each tap setting `chosen` to the row holding that lemma key (or a row built
  from the key). With `chosen`: a header with the spellings and the total and a "Suggestions"
  text button that clears `chosen`; then the occurrences exactly as Text-mode Greek hits,
  under text headers (title and count) and book sub-headers.

**Navigation (`App`).**

    data class Reader(val slug: String, val backTo: Screen = Home) : Screen
    var target by remember { mutableStateOf<SearchTarget?>(null) }

`SearchTarget(slug, source, nInt, nSub, start, end, noteKind: NoteKind?, noteId: Long?)` in
`data/TextSearch.kt`, built from a hit (`noteKind` for COMMENTARY from the commentary id
through the corpus, `noteId` for NOTES from `extra`). `onOpen(hit)`: `target = …`,
`expanded = hit.slug`, `screen = Reader(hit.slug, backTo = screen)`. The reader's `onBack`
and its back handler go to `s.backTo`. `startLine = target?.nInt ?: lastLine ?: 1L`;
`ReaderScreen` gets `target` and `onTargetShown = { target = null }`, which it calls from a
`LaunchedEffect(Unit)` after keeping its own copy (`val hit = remember { target }`): the
parameter goes back to null at once and the reader uses its copy only. `onSearchLemma =
{ key, lemma -> search.openLemma(key, lemma); screen = Screen.Search(from = Screen.Reader(slug)) }`.
`wantedSlug` is unchanged. The reader's menu entry and icon say "Search" (`Icons.Filled.Search`
on wide screens, in place of the dictionary drawable).

## The reader at a hit (`ui/ReaderScreen.kt`)

* `var highlight by remember { mutableStateOf(hit) }`, cleared in the settled-page effect when
  the settled page holds no Greek line with the highlighted line's id (so it stays while the
  reader looks and goes when the page is turned).
* Greek: `PageContent` and `ProsePage` get `highlight: Pair<Long, IntRange>?` (line id and
  offsets); `GreekLineRow` draws it in the same `drawBehind` as the note marks, before them:
  `drawHighlight(layout, start, end, color)` loops over the visual lines like `drawNoteMark`
  and fills a rectangle from `getLineTop(i)` to `getLineBottom(i)` between the left and right
  bounding-box edges, colour `primary.copy(alpha = 0.2f)`. `ProseParagraph` moves the offsets
  by `prose.start[line.id]` as it does for the note spans. The pinch preview passes null.
* Translation: the mode is `chosenMode?.takeIf { it in modes } ?: if (wide) BOTH else if
  (hit?.source == TRANSLATION) TRANSLATION else GREEK`. `TranslationPage` gets
  `highlight: SearchTarget?` and, while building the paragraph, wraps the matched range of the
  segment whose `from_n_int`/`from_n_sub` are the target's in
  `SpanStyle(background = primary.copy(alpha = 0.2f))`.
* Commentary: once `positioned`, `pageNotesKind = hit.noteKind`. Notes: once `notes` are
  loaded, `editing = notes.firstOrNull { it.note.id == hit.noteId }`; each once only.
* The word sheet gets `onOccurrences: (() -> Unit)?`, a button "Occurrences" after Syntax;
  in the reader it calls `onSearchLemma(token.lemma_key, token.lemma)` and closes the sheet.
  The sheets of the Dictionary and Analysis modes pass it too (`HeadwordHit.lemmaKey`,
  `FormAnalysis.lemmaKey`) when at least one text is installed, else null.

## Steps

Build and test as in `PLAN-personal-notes.md`: `export JAVA_HOME=/opt/android-studio/jbr
ANDROID_HOME=$HOME/Android/Sdk` in `app/`, then `./gradlew :androidApp:assembleDebug`, the
shared unit tests with `./gradlew :shared:testAndroidHostTest`, and
`./gradlew :androidApp:installDebug` on the phone or the emulator when one is connected. Each
step ends with a commit (message below, with the Co-Authored-By trailer) and a tick under
Progress.

### Step 1 (Opus): folding and the engine

* `GreekNormalizer.baseLetter`; `data/TextFold.kt`; `data/TextSearch.kt` with the classes
  above, `CancellableText`, the scanning, `excerpt`, and `SearchTarget`.
* Tests in `shared/src/commonTest/kotlin/no/anagnosis/data/TextFoldTest.kt` and
  `TextSearchTest.kt`: the fold keeps the length on a polytonic line and on an English one;
  Ἄνδρα folds to ανδρα with both ignored, to Ανδρα with case kept, stays Ἄνδρα with accents
  kept except ς → σ; ʼ and ’ fold to '; é to e; a newline to a space; `foldPattern` leaves
  `\b` alone and folds `[Ἀ-Ὠ]`. The engine on three hand-made docs (Greek lines, an English
  paragraph, a note): hits with the right unit, offsets and excerpt; a phrase over two lines
  belongs to the first; whole words; exact case; regex alternation; an invalid pattern gives
  the error and no hits; zero-length matches are skipped; `MAX_HITS` truncates; a
  `CancellableText` whose flag is false throws `CancellationException` from a regex; the
  excerpt window with "…".

Commit: "Search engine: folding, scanning and excerpts".

### Step 2 (Opus): data layer

* The queries, `plainText`, `loadWork(light)`, the corpora, `notesDoc`, `searchTexts`,
  `data/LemmaIndex.kt`, `lemmaEntries`, `lemmaRows`, `glossFor`, `occurrences`.
* Tests in `LemmaIndexTest.kt`: merging two texts' entries, one with an alias and one with an
  -ομαι twin; βίος and βιός stay apart; counts per text and total; `suggest` with a Latin
  prefix, with a final ς, exact row first; `plainText` on a commentary note with `<p>`, `<b>`
  and `&amp;`.

Commit: "Repository: search corpora, lemma index and occurrences".

### Step 3 (Opus): the search page in Text mode

* The hoisted state and `SearchEffects`; the four-mode switch ("Analysis"); the controls and
  results of Text mode; the front page and the search page both showing them; `Screen.Reader.backTo`,
  `target`, `onOpen`, and the reader opening at the hit's line (no highlight yet); the menu
  entry and icon renamed. The Lemma segment can exist but show nothing yet.
* Verify on the device: Odyssey, "Ὀδυσ" and "odysseus"; "wine-dark" with the Greek letters
  tap; a phrase across two lines; the four options; the four source chips; all texts from the
  front page; a translation hit opens the English, a commentary hit the sheet; back returns
  to the results.

Commit: "Search page: free-text search of the Greek, translations, commentaries and notes".

### Step 4 (Opus): Lemma mode and Occurrences

* The suggestions, the analyser's fallback, the occurrences, `openLemma`, the Occurrences
  button on the three word sheets, `onSearchLemma`.
* Verify: "logos" on the front page with two texts installed; "φέρει" (no lemma, analyses
  offered); Occurrences from a word in the Odyssey and from a dictionary headword; a text
  whose lemmas are automatic (the Symposium) in the all-texts list.

Commit: "Lemma search with suggestions and occurrences; Occurrences on the word sheet".

### Step 5 (Opus): the highlight

* The Greek highlight in verse and prose, the translation highlight, the clearing on a page
  turn, the commentary sheet and the note editor on arrival.
* Verify in Antigone (verse), the Symposium (prose), the New Testament (verse marks on) and
  the Odyssey, in all five colour themes.

Commit: "Reader: the match found by a search is highlighted until the page is turned".

### Step 6 (Opus): help and documentation

* `IntroDialog`: the "Dictionary" item becomes "Search", saying what the four modes do, that
  Latin letters search the English until the tap, that Occurrences on a word lists every
  place the word occurs, and where the options are.
* `README.md` (the second paragraph) and `play/listings/reader.md` (the feature paragraphs):
  one sentence each on search; `app/README.md`'s structure list names the search.
* The reader's store screenshots are retaken with the 0.3.0 build in any case (see
  `play/README.md`); one of the search results page would be good.

Commit: "Help and READMEs for the search".

## Known limitations (accepted)

* An editor's addition inside a word (Ἀγάθων⟨ος⟩) is not found by the whole word.
* A lemma spelt with different accents in two texts stands as two rows side by side.
* Regex patterns run on the folded text, so a pattern written with accents matches only
  with "Exact accents" on; that is what the fold means.

## Progress

- [x] Step 1: folding and the engine
- [x] Step 2: data layer
- [ ] Step 3: the search page in Text mode
- [ ] Step 4: Lemma mode and Occurrences
- [ ] Step 5: the highlight
- [ ] Step 6: help and documentation
