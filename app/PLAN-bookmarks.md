# Bookmarks: implementation plan

A reader bookmarks a sentence of the Greek so as to come back to it: a place in the text,
with a name if wanted, nothing drawn in the text. Decided with the author on 2026-10-21. This
file is the brief: follow it step by step, tick the steps off under Progress, and commit after
each step (the plan file with it). All steps are routine and are done on Opus.

Decisions already taken (do not reopen them):

* A bookmark is a sentence, anchored by its first word (citation of the line and the word's
  place in it, as a note's `WordAnchor`), never by sentence id or database id, which change
  when a text is rebuilt. It has an optional name. It never underlines or marks the text.
* Making one works like making a note, from an icon beside the pencil: a tap on the icon, a
  prompt in the title row, a tap on any word, and that word's sentence is bookmarked. The
  bookmark is not offered anywhere else (not on the word sheet): one function, one place.
* The list is reached from a "Bookmarks" button in the bottom bar beside "Notes", shown once
  the text has a bookmark. It always lists every bookmark of the text; those on the present
  page are highlighted. No list of the page's bookmarks, no explanatory texts.
* The quote shown for a bookmark is the first eight words from the sentence's start, running
  on into the next sentence when the sentence is shorter, and stopping only at the end of the
  text. So a one-word sentence still gets a telling quote.
* Opening a bookmark goes to the page where its sentence starts.
* A tick on the progress bar for each bookmarked page, drawn differently from the note ticks,
  with a switch in the options like the one for notes.
* A "Bookmarks" section at the end of the notes export. No list across texts on the front page.
* Bookmarks are kept in the reader's own notes database (never deleted when a text app is
  uninstalled).
* Icons come from the full material set (`material-icons-extended`, same publisher and version
  as the core set already used); release builds shrink it to the icons used. No icons are
  drawn by hand.

## How it behaves

**The icon.** `Icons.Outlined.BookmarkBorder` in the `actions` slot of the `TopAppBar`,
before the pencil, on compact and wide screens alike; `Icons.Filled.Bookmark` in the primary
colour when a placed bookmark's sentence starts on the current page. Content description
"Add a bookmark". While a passage is being chosen for a note the bar shows only Cancel, as now,
and the same while a sentence is being chosen for a bookmark.

**Choosing the sentence.** A tap on the icon sets `bookmarking = true`; the title row reads
"Tap a word of the sentence to bookmark" (the same place and style as the note prompt) with
Cancel in the actions; if only the English is shown the view switches to the Greek, as the
pencil does. A tap on a word (`onWord` while bookmarking, as `pickWord` is called while
selecting) takes the word's sentence from `sentences[sentenceOfToken[id]]` (the reading
voice's split of the book by treebank sentence id, already in `ReaderScreen`), its first token
`t`, and the anchor `Notes.anchorOf(data, t)`. When a placed bookmark already has that anchor,
the editor opens on it; otherwise on a new bookmark with that anchor and
`Bookmarks.quote(data, t)`. Bookmarking ends with the tap. Cancel, back, or the icon again
leave the mode. While bookmarking a tap on a word does not open the word sheet and a press-and-
hold does nothing (as while selecting). With a screen reader, the word actions get
`WordAction.BOOKMARK` ("Bookmark this sentence") after NOTE, which does the same.

**The editor** (`BookmarkEditorSheet` in `ui/BookmarksSheets.kt`), a `ModalBottomSheet` like
the note editor: the citation as heading (`Bookmarks.label`: "Line 12", "Line 1.12",
"Line 172a1", "Matthew 5:3"), the quote in grey under it, a single-line text field
"Name (optional)", then Delete (existing bookmarks only, with a confirmation like the note's),
Cancel and Save. Save is always enabled. The field has focus when a new bookmark opens and the
keyboard must not cover it. Swiping the sheet away or back saves a new bookmark too (as the
note editor keeps what was written); only Cancel drops it. Save and Delete reload the
bookmarks.

**The list** (`BookmarksSheet`), from the "Bookmarks" button in the bottom bar (after "Notes";
`hasBookmarks`, `onBookmarks` on `ProgressScrubber`). Heading "Bookmarks" in the style of the
other sheets' headings. Then every placed bookmark in text order, as a row: citation in
`titleMedium`, the name after it on the same line in `bodyMedium` when there is one, and under
them the quote in grey, one line, ellipsis. A row whose sentence starts on the present page
has the `primaryContainer` background with rounded corners (`MaterialTheme.shapes.small`) and
a little padding, the rest no background. A tap on a row goes to the bookmark's page
(`goToLine` of its first line) and closes the sheet. A pencil icon at the end of each row
opens the bookmark in the editor, to rename or delete it (added 2026-10-21 while building:
otherwise the only way to an existing bookmark is to find its sentence again). Bookmarks whose sentence is not found in
the current text come last under a heading "Not found in the current text" (in the style of
the all-notes sheet's heading for lost notes), each with its quote; a tap on one opens it in
the editor, which is where it can be deleted. Nothing else is written in the sheet.

**Four buttons in the bottom bar.** On a narrow screen (`compact`, a phone held upright) with
four buttons (Apparatus, Commentary, Notes, Bookmarks) the buttons show abbreviated names:
"App.", "Comm.", "Notes", "Bookm." (`NoteKind.short`), so that the span keeps its full
"Lines 252–269". A screen reader still reads the full names. Decided with the author on
2026-10-21 after seeing the span cut to "Lin…" on the emulator.

**The ticks.** `ProgressScrubber` gets `bookmarkedPages: Set<Int>`. A note's tick is a short
vertical line through the track in the primary colour at half strength; a bookmark's tick is
a small filled triangle above the track (apex down touching the track, 8 dp wide, 6 dp high)
in the primary colour at full strength, so the two are told apart; a page can have both. The
option "Mark bookmarked pages on the progress bar" (`ReaderSettings.bookmarkTicks`, key
`bookmark_ticks`, default on) stands under the two note switches in the group of the options,
which is renamed "Notes and bookmarks".

**The export.** `Notes.markdown` takes the placed bookmarks too and, when there are any, ends
with a `## Bookmarks` section: one list item per bookmark, `- **Line 12** Name: quote` (name
omitted when empty, then `- **Line 12**: quote`), placed ones in text order, then unplaced ones
under `### Not found in the current text`. The Export button stays on the all-notes sheet, so
a text with bookmarks and no notes has no export: accepted.

## Data

**Database.** A second table in `NotesDatabase`, added by the migration
`shared/src/commonMain/sqldelight-notes/no/anagnosis/notesdb/1.sqm` (schema version 1 to 2;
the Android driver runs it on upgrade) and declared as well in `Bookmarks.sq` beside
`Notes.sq`, since the `.sq` files hold the full current schema.

    CREATE TABLE bookmarks (
        id INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
        text_slug TEXT NOT NULL,
        n_int INTEGER NOT NULL, n_sub TEXT NOT NULL, word INTEGER NOT NULL,
        name TEXT NOT NULL,
        quote TEXT NOT NULL,
        created INTEGER NOT NULL
    );
    CREATE INDEX bookmarks_text ON bookmarks(text_slug, n_int, n_sub, word);

    selectForText (ORDER BY n_int, n_sub, word, id), insert, lastInsertId, rename (name by id),
    delete (by id).

`word` is the first word's `ord` in its line, as in `notes`. `quote` is the text's words when
the bookmark was set, to notice a renumbered edition and to show in the list.

**Models** (`data/Bookmarks.kt`):

    class Bookmark(id, textSlug, at: WordAnchor, name, quote, created)
    class PlacedBookmark(val bookmark: Bookmark, val line: Lines?, val token: Tokens?)  // null = not found

**The quote** (`Bookmarks.quote(data, token)`): the eight tokens from `token` on in text order
(the rest of its line, then the following lines of `data.lines`, across books), as
`Notes.quote` of the `Placement` from the first to the last of them, so punctuation between
the words is kept and verse marks and speaker braces are not; "…" is appended when a ninth
token follows. Fewer than eight at the end of the text: what there is, no "…".

**Placing** (`Bookmarks.place(bookmarks, data)`): the line by (n_int, n_sub) in
`linesByCitation`, the token by `ord` in `tokensByLine`; placed when both are found and either
the quote now equals the stored one or the stored quote's first word is the token's form
ignoring diacritics (`AnagnosisRepository.looseKey`).

**The label** (`Bookmarks.label(data, anchor)`): `Notes.rangeLabel(data, anchor, anchor)`.

**Repository**: `bookmarks(slug)`, `addBookmark(slug, at, name, quote): Long`,
`renameBookmark(id, name)`, `deleteBookmark(id)`.

## Steps

Build and test with `export JAVA_HOME=/opt/android-studio/jbr ANDROID_HOME=$HOME/Android/Sdk`
in `app/`: `./gradlew :androidApp:assembleDebug`, the shared unit tests with
`./gradlew :shared:testAndroidHostTest`, and `./gradlew :androidApp:installDebug` to try it on
the emulator or device when one is connected. Stop the Gradle daemon when done.

### Step 1: data layer

The icon dependency in `shared/build.gradle.kts`; `1.sqm`, `Bookmarks.sq`, `data/Bookmarks.kt`,
the repository functions, and `shared/src/commonTest/kotlin/no/anagnosis/data/BookmarksTest.kt`:
the quote of a long sentence, of a short sentence running into the next across a line, and at
the end of the text; placing a bookmark whose quote matches; a changed quote with the same
first word is placed; a different first word, a missing line or a missing word is unplaced;
the label for a play, Plato and the New Testament.

Commit: "Bookmarks table, quote and placing logic".

### Step 2: choosing, editor, list

`ui/BookmarksSheets.kt`, and in `ReaderScreen`: state `bookmarks: List<PlacedBookmark>` loaded
with the text like the notes and reloaded after each change; `bookmarking` and its prompt; the
icon; the editor; the bottom-bar button and the list; the screen-reader action. Checked on
the emulator with four buttons in the bottom bar of a phone.

Commit: "Bookmarks: icon, choosing a sentence, editor and list".

### Step 3: ticks and the option

`ReaderSettings.bookmarkTicks`, the store, the options switch, `bookmarkedPages` in the reader
and the triangles in `ProgressScrubber`.

Commit: "Bookmarks: ticks on the progress bar, with a switch".

### Step 4: export

`Notes.markdown` with the bookmarks section and a test; the call in `ReaderScreen` passes them.

Commit: "Bookmarks in the notes export".

## Progress

- [x] Step 1
- [x] Step 2
- [ ] Step 3
- [ ] Step 4
