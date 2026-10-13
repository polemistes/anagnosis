# Personal notes: implementation plan

A reader marks a passage of the Greek and writes a note on it. The passage is underlined
while reading; the note is read and edited from the bottom bar; notes can be exported to a
file. Decided with the author on 2026-10-13. This file is the brief for the work: follow it
step by step, tick the steps off under Progress, and commit after each step (the plan file
with it).

Who does what: steps 1, 2, 4, 5 and 6 are routine and are done on Opus. **Step 3 (the
selection of the passage) is done on Fable 5.1 only**: when step 3 is next, stop and tell the
user to switch models before starting it. The order of work is 1, 2, 4, 5, 3, 6: everything
Opus does comes first, so that step 3 finds the editor and the sheets in place and can test
the whole flow on the device.

Decisions already taken (do not reopen them):

* Notes go on the Greek text only, never on the translation.
* The mark is a thin underline under the passage's words; nothing is added to the line, so
  pages are cut exactly as before.
* The note-making starts from a pencil icon in the title row of the top bar.
* Changed on 2026-10-13 after trying it: a word that lies in a noted passage gets a "Note"
  button in the word sheet, after Syntax, which opens the note in the editor. Where several
  notes take in the word, each has a button named by its passage ("Note, lines 1–2").
* Existing notes are read from a "Notes" button in the bottom bar, next to Apparatus and
  Commentary; from there, the list of all notes in the text, and export.
* Two switches in the options: hide the underlines; hide the tick marks on the progress bar.
* Export to a Markdown file, through the system file dialog. No import.
* Notes are kept in a database of the reader's own, never deleted when a text app is
  uninstalled, and anchored by citation so that they survive a rebuilt text.

## How it behaves

**Making a note.** The pencil in the title row (top right, the `actions` slot of the
`TopAppBar`, where nothing stands now) starts the selection. The line above the progress bar,
which otherwise shows the page's span and the Apparatus/Commentary/Notes buttons, now reads
"Tap the first word of the passage" with a Cancel button beside it. A tap on a word marks it
(a short haptic tick; the word gets a full-strength underline) and the prompt changes to "Tap
the last word of the passage". The second tap closes the range: a tap before the first word
makes that the first word instead; the same word gives a one-word note. Pages may be turned
between the two taps, so a passage can run over a page. Then the editor opens. Cancel, the
back button, or the pencil again leave the mode with nothing marked. While selecting, a tap on
a word does not open the word sheet, and a press-and-hold does nothing. If the narrow screen
is showing the translation only, the pencil switches the view to the Greek first.

**The editor.** A bottom sheet like the others: the citation as heading ("Line 12",
"Lines 12–14", "Lines 591–591a", "Matthew 5:3–7", "Lines 172a1–172b3"), the Greek passage
quoted in grey under it, a multi-line text field, then Delete (existing notes only, with a
confirmation), Cancel and Save. Save is enabled when the field is not blank. The field has
focus when a new note opens, and the keyboard must not cover it. The quote is a reminder of
the passage, not the passage: it is cut short after four lines. Swiping the sheet away, a
tap beside it or back keeps what was written (a blank new note is dropped); only Cancel
throws a change away.

**The marks.** Each word of a passage is underlined: a line 1.5 dp thick, 3 dp below the
baseline, in the primary colour at 45 % opacity (one constant). It runs from the first word
to the last on each line the passage touches, in verse and in prose alike; on a line in the
middle of a passage, from its first word to its last. Overlapping notes simply overlap. The
option "Underline passages that have a note" turns the marks off.

**Finding notes.** When the text has at least one note, a "Notes" button stands in the
bottom bar after Apparatus and Commentary. It opens a sheet listing the notes of the current
page (heading, quote, note), each opening the editor, or "No notes on this page", and at the
bottom "All notes in this text". That sheet lists every note in text order with heading,
quote (one line) and note (up to three lines); a tap goes to the note's page and closes the
sheet. Notes whose passage is not found in the current text (after an edition was renumbered)
come last under "Passages not found in the current text", with their quote; a tap opens them
in the editor so they can be read and deleted. An Export button stands in the sheet's title
row. On the progress bar a short tick marks each page that holds a note; the option "Mark
pages with notes on the progress bar" turns the ticks off.

## Data

**Database.** A third SQLDelight database, `NotesDatabase`, package `no.anagnosis.notesdb`,
sources in `shared/src/commonMain/sqldelight-notes/no/anagnosis/notesdb/Notes.sq`, file
`notes.sqlite` in the reader's database directory. Unlike the bundles, this one is created by
SQLDelight's schema on first open (the Android driver does that when the file is new). Later
schema changes go through `.sqm` migrations in the same source directory.

    CREATE TABLE notes (
        id INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
        text_slug TEXT NOT NULL,
        from_n_int INTEGER NOT NULL, from_n_sub TEXT NOT NULL, from_word INTEGER NOT NULL,
        to_n_int INTEGER NOT NULL, to_n_sub TEXT NOT NULL, to_word INTEGER NOT NULL,
        quote TEXT NOT NULL,
        body TEXT NOT NULL,
        created INTEGER NOT NULL, modified INTEGER NOT NULL
    );
    CREATE INDEX notes_text ON notes(text_slug, from_n_int, from_n_sub, from_word);

    selectForText: SELECT * FROM notes WHERE text_slug = ? ORDER BY from_n_int, from_n_sub, from_word, id;
    insert, updateBody (body, modified by id), delete (by id).

`from_word`/`to_word` are the word's `ord` in its line (0-based, as `tokens.ord`). The
anchor is the citation, never a database id: the pipeline numbers lines and tokens in
insertion order, so ids change at every rebuild of a text. `created` and `modified` are epoch
milliseconds from an `expect fun nowMillis(): Long` (Android: `System.currentTimeMillis()`).

**Models** (in `data/Notes.kt`):

    data class WordAnchor(val nInt: Long, val nSub: String, val word: Long)
    class Note(id, textSlug, from: WordAnchor, to: WordAnchor, quote, body, created, modified)
    class Placement(firstLine: Lines, firstToken: Tokens, lastLine: Lines, lastToken: Tokens)
    class PlacedNote(val note: Note, val placement: Placement?)   // placement null = not found
    class NoteSpan(val start: Int, val end: Int, val noteId: Long) // offsets in a line's text
    class NoteDraft(val from: WordAnchor, val to: WordAnchor, val quote: String, val heading: String)

**Placing** (`Notes.place(notes, data)`): the line is looked up by (n_int, n_sub) in a lazy
`WorkData.linesByCitation`, the token by `ord` among `tokensByLine[line.id]`. A note is placed
when both ends are found, the first is not after the last (compare `Lines.ord`, then
`Tokens.ord`), and either the quote built from the current text equals the stored quote or
the first and last words match the stored ones ignoring diacritics (`AnagnosisRepository.looseKey`
on the forms; store nothing extra: the forms are the first and last words of the quote).
Otherwise the note is unplaced and listed as such.

**The quote** (`Notes.quote(data, placement)`): one line: `text.substring(first.start, last.end)`;
several lines: the first from the first word's start, the middle lines whole, the last up to
the last word's end; each piece through `displayText` (drops the "| " verse prefix and the
speaker braces) and trimmed; joined by single spaces, whitespace collapsed.

**The heading** (`Notes.rangeLabel(data, from, to)`): in the New Testament
`data.range(from.nInt, to.nInt)`; otherwise "Line " + `data.citation(nInt, nSub)` when both
ends are the same line, else "Lines " + citation(from) + "–" + citation(to), so 591 and 591a
give "Lines 591–591a" and Plato "Lines 172a1–172b3".

**Spans** (`Notes.spansByLine(placed, data): Map<Long, List<NoteSpan>>`, keyed by line id):
for each placed note, the lines from the first to the last by their position in `data.lines`;
on the first line from the first token's start, on the last line to the last token's end, on
the lines between from their first token's start to their last token's end; a line without
tokens gets no span. Offsets are into `Lines.text` (`Tokens.start`/`end`, Long to Int).

**Export** (`Notes.markdown(data, title, author, edition, placed)`), file `anagnosis-notes-<slug>.md`,
MIME `text/markdown`:

    # Notes on Antigone

    Sophocles, Antigone. Edition: <CatalogEntry.refEdition, when not empty>.
    Exported from Anagnosis.

    ## Lines 1–2

    > ὦ κοινὸν αὐτάδελφον Ἰσμήνης κάρα, ἆρ᾽ οἶσθ᾽ ὅ τι Ζεὺς τῶν ἀπ᾽ Οἰδίπου κακῶν

    The note as written.

Unplaced notes follow under `## Passages not found in the current text`, each as above with
`### <heading>`.

## Steps

Build and test with `export JAVA_HOME=/opt/android-studio/jbr ANDROID_HOME=$HOME/Android/Sdk`
in `app/`: `./gradlew :androidApp:assembleDebug`, the shared unit tests with
`./gradlew :shared:testAndroidHostTest`, and `./gradlew :androidApp:installDebug` to try it on
the emulator or device when one is connected. Each step ends with a commit (message suggested below, with the Co-Authored-By
trailer) and a tick under Progress.

### Step 1 (Opus): data layer

* `shared/build.gradle.kts`: add the `NotesDatabase` to the `sqldelight` block, with
  `srcDirs("src/commonMain/sqldelight-notes")`, as the lexicon database is declared.
* `Notes.sq` as above.
* `DriverFactory` (expect, in `DriverFactory.kt`): add `fun createNotesDriver(): SqlDriver`.
  Android actual: `AndroidSqliteDriver(NotesDatabase.Schema, context, "notes.sqlite")`, no
  bundle install. Nothing in `importTextApps` or the uninstall clean-up may touch this file.
* `expect fun nowMillis(): Long` next to `inflate` in `DriverFactory.kt`, Android actual in
  `DriverFactory.android.kt`.
* `data/Notes.kt`: the models and the pure functions above (`place`, `quote`, `rangeLabel`,
  `spansByLine`, `markdown`, plus `anchorOf(data, token): WordAnchor` and
  `isBefore(data, a, b)` for ordering two anchors).
* `WorkData`: lazy `linesByCitation: Map<Pair<Long, String>, Lines>` and lazy
  `tokenById: Map<Long, Tokens>` and `lineById: Map<Long, Lines>` (the reader now finds a
  token by scanning every line; these replace that where convenient).
* `AnagnosisRepository`: `private val notesDb by lazy { NotesDatabase(driverFactory.createNotesDriver()) }`
  and `notes(slug): List<Note>`, `addNote(slug, from, to, quote, body): Long`,
  `updateNote(id, body)`, `deleteNote(id)`.
* Tests in `shared/src/commonTest/kotlin/no/anagnosis/data/NotesTest.kt`, built on a
  hand-made `WorkData` of three or four lines with tokens (see `SyntaxTest` for how the
  generated row classes are constructed): placing a one-line and a two-line note; an anchor
  whose line is missing is unplaced; a changed quote with matching end words is placed; a
  changed quote with different end words is unplaced; the quote across lines; the heading for
  a play, a shared verse (591–591a), Plato and the New Testament; spans across three lines;
  the Markdown of one placed and one unplaced note.

Commit: "Notes database and placing logic for personal notes".

### Step 2 (Opus): settings, marks and ticks

* `ReaderSettings`: `noteMarks: Boolean = true`, `noteTicks: Boolean = true`; stored as
  `note_marks`, `note_ticks` in `SettingsStore.android.kt`.
* `OptionsDialog`: after the "Name a word's function" switch, a label "Notes" and two rows in
  the same style: "Underline passages that have a note" and "Mark pages with notes on the
  progress bar".
* `ReaderScreen`: state `notes: List<PlacedNote>` loaded with the text (`LaunchedEffect(data)`,
  on `Dispatchers.Default`, through `Notes.place(repository.notes(data.slug), data)`) and a
  `reloadNotes()` for later steps; `spans = remember(notes, settings.noteMarks)`, empty when
  the marks are off. `PageContent` gets `spans: Map<Long, List<NoteSpan>>` and hands each
  line its list (the pinch preview passes the same map).
* `GreekLineRow`: the Text's modifier chain, after its padding, gets a `drawBehind` that
  reads the `layout` state and draws every span: for each visual line from
  `getLineForOffset(start)` to `getLineForOffset(end - 1)`, from `getHorizontalPosition` of
  the span's start (or the line's `getLineStart`) to that of its end (or
  `getLineEnd(i, visibleEnd = true)`), at `getLineBaseline(i) + 3.dp`, 1.5 dp thick, primary
  at `NOTE_MARK_ALPHA = 0.45f`. Put the drawing in one private function used by verse and
  prose. The text itself stays a plain String; nothing changes in pagination or the measure
  cache.
* `ProseParagraph`: the same drawing, with the spans' offsets moved into the paragraph by
  `prose.start[line.id]`, as the `words` list already does for taps.
* `ProgressScrubber`: a `notedPages: Set<Int>` (computed in the reader as
  `remember(pages, notes)`: a page is noted when one of its Greek lines carries a span) and,
  when `settings.noteTicks`, a tick per noted page on the track before the thumb is drawn:
  2 dp wide, 12 dp tall, centred on the track at `width * (i + 0.5) / count`, primary at 50 %.
* Verify: build; on the device nothing is visible yet (no notes exist). A temporary note may
  be inserted through a line in `MainActivity` to look at the underline and the tick, and
  removed again before the commit.

Commit: "Reader underlines noted passages and ticks their pages; options to hide both".

### Step 4 (Opus): editor, Notes button, the sheets, go-to

Done before step 3 so that step 3 only has to produce a `NoteDraft`.

* New file `ui/NotesSheets.kt`; make `sheetModifier()` in `Sheets.kt` internal and reuse it.
  * `NoteEditorSheet(heading, quote, initialBody, isNew, onSave: (String) -> Unit, onDelete: (() -> Unit)?, onDismiss)`:
    `ModalBottomSheet`, `skipPartiallyExpanded = true`; heading `titleMedium`; quote
    `bodyMedium` in `onSurfaceVariant`; an `OutlinedTextField` of at least four lines, filling
    the width, focused on open when `isNew` (a `FocusRequester` in a `LaunchedEffect`); a row
    with Delete (an `AlertDialog` "Delete this note?" with Delete/Cancel), a spacer, Cancel,
    Save (enabled when the text is not blank). Pad for the keyboard (`imePadding`) and check
    on the emulator that the keyboard never hides the field or the buttons.
  * `PageNotesListSheet(notes: List<PlacedNote>, onOpen: (PlacedNote) -> Unit, onAll, onDismiss)`:
    title "Notes" as the commentary sheet shows its kind; each note: heading `titleMedium`,
    quote `bodyMedium` in `onSurfaceVariant`, body `bodyMedium`; dividers between; the whole
    entry clickable; "No notes on this page." when empty; a `TextButton` "All notes in this
    text" at the bottom.
  * `AllNotesSheet(title, notes: List<PlacedNote>, onGo: (PlacedNote) -> Unit, onOpen: (PlacedNote) -> Unit, onExport, onDismiss)`:
    a `LazyColumn`; title row "Notes on <text title>" with an Export `TextButton`; placed
    notes in text order (heading, quote on one line with ellipsis, body up to three lines
    with ellipsis), tap = `onGo`; then, if any, the heading "Passages not found in the
    current text" and the unplaced notes, tap = `onOpen`.
* `ReaderScreen`:
  * state `draft: NoteDraft?` (set by step 3), `editing: PlacedNote?`, `showPageNotes`,
    `showAllNotes`. The editor opens for either `draft` or `editing`; Save calls
    `repository.addNote` or `updateNote`, Delete `deleteNote`, each followed by
    `reloadNotes()`; work on `Dispatchers.Default`.
  * `ProgressScrubber` gets `hasNotes: Boolean` (the text has any note, placed or not) and
    `onMyNotes`; it shows the "Notes" `TextButton` after the commentary buttons when
    `hasNotes`.
  * the page's notes: the placed notes whose first line, or any line of the span, lies on the
    current page (compare line ids against the page's Greek rows).
  * `goToNote(note)`: for a text read by book, when the note's book is not the open one,
    do as `goToBook` does but with `anchorN = note.from.nInt`; otherwise scroll the pager to
    `pages.indexOfLast { it.firstN <= nInt } + offset`. An unplaced note goes to its stored
    line number the same way.
* Verify: build and unit tests. Without step 3 no note can be made in the app; a temporary
  insert as in step 2 lets the sheets, the editor, Delete and go-to be tried on the device.
  Remove it before the commit.

Commit: "Notes sheet, list of all notes, editor and go-to for personal notes".

### Step 5 (Opus): export and backup

* `expect @Composable fun rememberFileSaver(mimeType: String): (name: String, content: String) -> Unit`
  in `ui/FileSaver.kt`; Android actual in `shared/src/androidMain/kotlin/no/anagnosis/ui/FileSaver.android.kt`
  with `rememberLauncherForActivityResult(ActivityResultContracts.CreateDocument(mimeType))`
  (activity-compose is already an androidMain dependency); the content waits in a
  `remember`ed state until the Uri comes back, then is written through
  `contentResolver.openOutputStream`. No permission is needed for this.
* The all-notes sheet's Export button calls it with `anagnosis-notes-<slug>.md` and
  `Notes.markdown(...)`, the title from the catalog entry (`titleEn`, else `title`) and the
  edition from `refEdition`.
* Backup rules: the manifest allows backup but has no rules, and the copied bundles are far
  above Auto Backup's per-app limit, so backups most likely never happen today. Add
  `res/xml/backup_rules.xml` (`fullBackupContent`, for Android 8–11) and
  `res/xml/data_extraction_rules.xml` (`dataExtractionRules`, Android 12 and later, both the
  cloud-backup and device-transfer sections) that include only
  `<include domain="database" path="notes.sqlite"/>` and
  `<include domain="sharedpref" path="anagnosis_settings.xml"/>`; with includes present
  nothing else is backed up. Reference both from `androidApp/src/main/AndroidManifest.xml`.
  Optional check on an emulator with a Google account: `adb shell bmgr backupnow no.anagnosis.reader`
  and `adb logcat | grep -i backup`.
* Verify: build; export a note on the device and open the file.

Commit: "Export personal notes to Markdown; backup rules that carry the notes and settings and leave out the bundles".

### Step 3 (Fable 5.1): selecting the passage

Stop here and tell the user to switch to Fable 5.1 before starting. Everything else is in
place by now, so the step ends with the whole feature tried on the device.

* `ReaderScreen`: state `selecting: Boolean` and `selectionStart: WordAnchor?` (with the
  token's line and token for the pending underline).
* The pencil: `TopAppBar(actions = { IconButton(onClick = ...) { Icon(Icons.Filled.Edit, "Add a note") } })`
  (`Edit` is in the core icon set already used). Tinted primary while selecting. Tap: when
  selecting, cancel; otherwise `selecting = true`, and if `mode == TRANSLATION` set
  `chosenMode = GREEK`.
* `ProgressScrubber`: a `prompt: String?` and `onCancel`; when `prompt` is set the label row
  shows the prompt (`labelMedium`, `onSurface`) in place of the span and a Cancel
  `TextButton` in place of the note buttons. Prompts: "Tap the first word of the passage",
  "Tap the last word of the passage".
* Taps: the `onWord` passed to `PageContent` checks `selecting` (through a
  `rememberUpdatedState`); when selecting it sets the start, with
  `HapticFeedbackType.LongPress`, or completes the range. `onSentence` does nothing while
  selecting. Ordering by `Notes.isBefore`; if the second anchor is before the first, it
  becomes the first. Then `draft = NoteDraft(from, to, Notes.quote(...), Notes.rangeLabel(...))`
  and `selecting = false`; the editor of step 4 opens.
* The pending underline: the start word's span, drawn by the same function at full opacity
  and 2 dp thick; it goes into the spans map while the start is set.
* `PlatformBackHandler` while selecting: cancel.
* Verify on the device: one-word note; a passage across a page; a passage across a book
  boundary in the Odyssey; cancel by button, back and pencil; the prose Symposium and the
  New Testament; the marks and ticks with their options; the underline in all five colour
  themes; rotation with a note open.

Commit: "Make a note on a passage: the pencil, the selection prompt and the hand-over to the editor".

### Step 6 (Opus): words and version

* `IntroDialog`: a `HelpItem` "The pencil" after "Apparatus and Commentary": the pencil at
  the top starts a note: tap the first and the last word of the passage, write the note. The
  passage is underlined; Notes at the bottom opens the page's notes and the list of all notes
  in the text, from which they can be exported to a file. Both marks can be hidden in the
  options.
* `PRIVACY.md`: add the notes to what the app stores on the device; say that the notes and
  the display preferences are included in the device's Android backup when that is turned on,
  under Google's terms, and that the texts are not; that notes can be exported to a file by
  the user; update "Last updated".
* `README.md` (root): one phrase in the opening paragraph: notes on passages. `app/README.md`
  structure list: the notes database.
* `androidApp/build.gradle.kts`: `versionCode = 5`, `versionName = "0.3.0"`.

Commit: "Reader 0.3.0: personal notes on passages; help, privacy policy and README".

## Progress

- [x] Step 1 data layer
- [x] Step 2 settings, marks and ticks
- [x] Step 4 editor, sheets, go-to
- [x] Step 5 export and backup rules
- [x] Step 3 selection (Fable 5.1)
- [x] Step 6 words and version

## Where things are now (for orientation)

* `shared/src/commonMain/kotlin/no/anagnosis/ui/ReaderScreen.kt`: the top bar (title row and
  controls row), `ProgressScrubber` (label row with the span and the Apparatus/Commentary
  buttons, then the track), `PageContent`, `GreekLineRow` (one tap handler per line, the
  layout kept in state, `onWord`/`onSentence`), `ProsePage`/`ProseParagraph` (paragraph
  offsets in `prose.start`), `goToBook`, `anchorN` and the pagination effect that positions
  the pager at it.
* `ui/Sheets.kt`: `WordSheet`, `PageNotesSheet` (the model for the new sheets), `DocumentSheet`.
* `ui/OptionsDialog.kt`: the switches; `IntroDialog` with its `HelpItem`s.
* `prefs/Settings.kt`, `prefs/SettingsStore.android.kt`: settings and their keys.
* `data/Models.kt`: `WorkData` with `citation`, `range`, `lineLabel`, `bookOf`;
  `data/AnagnosisRepository.kt`: the databases and `notesForPage` (commentary).
* `shared/src/androidMain/kotlin/no/anagnosis/DriverFactory.android.kt`: `createDriver`,
  the bundle install and the import and removal of text apps' databases.
* `androidApp/src/main/AndroidManifest.xml`: `allowBackup="true"`, no rules yet.
