# Reader bars: implementation plan

The reader's top and bottom bars are rearranged so that they take less room and never
overflow: one top row whose contents adapt to the width, a bottom bar that cannot wrap and is
thinner on a short screen, and the two-column view from 800 dp. Decided with the author on
2026-10-13 after looking at the Odyssey on his phone (Samsung S22 Ultra, 411 × 882 dp). This
file is the brief: follow it step by step, tick the steps off under Progress, and commit after
each step (the plan file with it). All steps are routine and are done on Opus.

What is wrong today (`ui/ReaderScreen.kt`, the `Scaffold` in `ReaderScreen`):

* The top bar is two rows: a `TopAppBar` (back arrow, title, pencil) and a `Row` of controls
  (Greek/English segmented buttons, the Book menu, the info, dictionary and gear icons). With
  the Odyssey on a phone the row is wider than the screen and the gear falls off the edge. In
  landscape the row also ignores the system bar at the side, so the gear sits under it.
* The bottom bar's span label ("Book 1, lines 1–11") wraps onto two lines once the three
  buttons Apparatus, Commentary and Notes stand beside it.
* In landscape on the phone the bars leave room for three lines of Greek.
* The two-column view (Greek and translation side by side) starts at 840 dp; the phone in
  landscape has about 833 dp after the system bar, so it misses it.

Decisions already taken (do not reopen them):

* One top row in every mode. On narrow screens the rare actions go into an overflow menu
  (three dots) and the view switch is a single "English" chip; on wide screens the three
  actions stay icons and the view switch stays the segmented buttons. The pencil is always
  visible.
* The title is the book chooser for an epic and the New Testament: the Book button goes.
* The bottom label loses its "Book N, " prefix and never wraps. On a short screen both bars
  are thinner.
* The side-by-side limit goes from 840 dp to 800 dp.
* No version bump: 0.3.0 (version code 5) has not been uploaded yet, and this goes into it.

## Breakpoints

Three constants next to `WIDE` in `ReaderScreen.kt`, all measured on the `BoxWithConstraints`
that already wraps the `Scaffold` (`maxWidth`, `maxHeight`; these are the window less the
system bars, since `Scaffold`'s content insets are applied inside):

* `COMPACT = 600.dp`: below this width the rare actions collapse into the overflow menu and
  the view switch is the chip. The phone is compact in portrait (411 dp) and not in landscape
  (about 833 dp); the tablet is never compact.
* `WIDE = 800.dp` (was 840): from this width the view "Both" exists and is the default.
* `SHORT = 480.dp`: below this height both bars use their thin metrics. The phone is short in
  landscape only.

`val compact = maxWidth < COMPACT`, `val short = maxHeight < SHORT`, next to the existing
`val wide = translation != null && maxWidth >= WIDE`.

## The top bar

One `TopAppBar`, the second `Row` removed, `windowInsets = TopAppBarDefaults.windowInsets` as
now (that pads the status bar and the side system bar, which fixes the landscape overlap).
`expandedHeight = if (short) 48.dp else TopAppBarDefaults.TopAppBarExpandedHeight`.

**navigationIcon**: the back arrow, as now.

**title**: a `Row` with `verticalAlignment = CenterVertically`.

* A play: the work's title (`data.work.title`), `titleLarge`, one line, ellipsis. No click
  (the arrow goes back; the title's current `clickable { onBack() }` is dropped).
* An epic or the New Testament (`currentBook != null`): the title is the book chooser. It
  shows the work's title, then " · " and the book (the epic's number, `currentBook.name`;
  the New Testament's name, also `currentBook.name`, e.g. "John"), then a small
  `Icons.Filled.ArrowDropDown`. The work's title is the part that gives way: it is a `Text`
  with `Modifier.weight(1f, fill = false)`, one line, ellipsis; the book and the arrow never
  shrink, so "Ἡ Καινὴ Δ… · John ▾" is what a narrow screen shows. The whole row is
  `clickable { showBooks = true }` and anchors the existing `DropdownMenu` of books (move
  that `Box` with its `DropdownMenu` here; the items stay as they are).
  Style: `titleLarge` when not compact, `titleMedium` when compact, so that
  "Ὀδύσσεια · 24 ▾" fits beside the chip, the pencil and the menu on a 360 dp phone.

**actions**, in this order:

1. The view switch, when `translation != null`:
   * compact: a `FilterChip` labelled "English", `selected = mode == ViewMode.TRANSLATION`,
     `onClick = { chosenMode = if (mode == ViewMode.TRANSLATION) ViewMode.GREEK else ViewMode.TRANSLATION }`.
     No leading icon. 4 dp end padding.
   * not compact: the `SingleChoiceSegmentedButtonRow` as today (`modes` has "Both" only
     when `wide`), with the 13 sp labels, in the actions slot.
2. The pencil, exactly as now (tint primary while selecting, cancel on a second tap, switch
   from the translation view to the Greek first).
3. The rare actions:
   * compact: one `IconButton` with `Icons.Filled.MoreVert` (content description "More")
     anchoring a `DropdownMenu` with `DropdownMenuItem`s "Dictionary" (`onSearch`),
     "About this edition" (only when `documents.isNotEmpty()`; `showDocuments = true`) and
     "Options" (`showOptions = true`). Each item closes the menu first.
   * not compact: the three icons as today: info (when documents exist), dictionary
     (`Res.drawable.dictionary`), gear.

`MoreVert` and `ArrowDropDown` are in the core icon set already used; `FilterChip` is in
Material 3. Remove the imports the old row no longer needs.

## The bottom bar (`ProgressScrubber`)

* The span label: no "Book N, " prefix. `span` in the `ProgressScrubber` call becomes:
  verses → `data.range(first, last)` as now; one line → "Line " + `data.lineLabel(first)`;
  else "Lines " + `lineLabel(first)` + "–" + `lineLabel(last)`. The `Text` gets
  `maxLines = 1, overflow = TextOverflow.Ellipsis`. The selection prompt `Text` likewise.
* A `short: Boolean` parameter. Metrics:

  | | label row height | track height | bottom padding |
  |---|---|---|---|
  | normal | 40 dp (as now) | 28 dp (as now) | 8 dp (as now) |
  | short | 32 dp | 20 dp | 0 dp |

  The track's drawing is unchanged (the thumb, ticks and stroke are sized in dp already;
  the thumb's 9 dp scrubbing radius is fine in a 20 dp track).

## Help text (`IntroDialog` in `ui/OptionsDialog.kt`)

Rewrite the items that name the bars, keeping their order:

* "Greek / English": at the top switches between the text and the translation; on a wide
  screen a third choice, Both, puts them side by side.
* "Book": the title of an epic such as the Odyssey, or of the New Testament, shows the book
  being read; tap it to choose another. Swiping past the last page of a book goes on to the
  next. (Keep the rest of the current item about chapter and verse numbers.)
* "The pencil": unchanged.
* "The i button" becomes "About this edition": opens the edition's introduction, appendix or
  preface where the text has them; on a phone it is under the three-dot menu at the top
  right, on a wider screen an i icon. The manuscripts and sigla sentence stays.
* "The gear" becomes "Options": font, text size, line numbers, colours and notes; on a phone
  under the three-dot menu, on a wider screen the gear. You can reopen this help there.
* Add, after "Tap a word": "Dictionary" — the dictionary search, under the three-dot menu on a
  phone and a book icon on a wider screen; the front page has it too.

## Steps

Build and test as in `PLAN-personal-notes.md`: `./gradlew :androidApp:assembleDebug`,
`./gradlew :shared:testAndroidHostTest`, `./gradlew :androidApp:installDebug` on the phone
when it is connected (its screen must be unlocked for screenshots; it does not obey rotation
forced over adb, so ask the user to turn it). The emulator `anagnosis` (phone) and `tablet`
AVDs exist; the emulator's apps are signed with the release key, so install a release build
there with `adb install -r` after `./gradlew :androidApp:assembleRelease`, and rotate it with
`adb emu rotate`. Each step ends with a commit and a tick under Progress.

### Step 1: the top bar

The breakpoints, the single `TopAppBar` with the title as book chooser, the chip or the
segmented buttons, the pencil, the overflow menu or the icons. Verify on the emulator phone:
Antigone and Odyssey in portrait (nothing cut off; the title shows the book; the menu opens
all three; the chip switches the view), Odyssey in landscape (segmented buttons and icons
inline, the gear not under the system bar), and on the tablet AVD (all inline, Both present).

Commit: "Reader: one adaptive top row; the title chooses the book; rare actions in a menu on phones".

### Step 2: the bottom bar, the two-column limit and the help

The label without prefix and without wrapping, the thin metrics when short, `WIDE = 800.dp`,
the help items. Verify on the emulator phone in landscape: the Odyssey shows the two columns
by default and about nine lines of Greek with Greek chosen; in portrait with a text that has
notes, "Lines 1–11", Apparatus, Commentary and Notes stand on one line (make a note first,
with the pencil, if none exists). Check the New Testament label ("John 1:1–8") and Plato's if
the Symposium is installed ("Lines 172a1–172b6").

Commit: "Reader: bottom bar that cannot wrap and is thinner on a short screen; two columns from 800 dp; help text".

### Step 3: on the phone

Install the debug build on the user's phone and look at Antigone, Odyssey and the New
Testament in portrait; ask the user to turn the phone for landscape. Fix what the phone shows
differently from the emulator (its navigation bar is at the side in landscape). Commit if
anything changed.

## Progress

- [x] Step 1 top bar (with the breakpoints and WIDE = 800 dp)
- [x] Step 2 bottom bar, two-column limit, help
- [ ] Step 3 on the phone

## Where things are now

* `ui/ReaderScreen.kt`: `ViewMode`, the constants `MAX_COLUMN`, `COLUMN_GAP`, `WIDE`; in
  `ReaderScreen` the `BoxWithConstraints` with `wide`, `modes`, `mode`, then the `Scaffold`
  whose `topBar` holds the `TopAppBar` and the controls `Row` (the Book menu's `showBooks`
  state and `DropdownMenu` are there), whose `bottomBar` calls `ProgressScrubber` with the
  `span` lambda; `ProgressScrubber` itself near the end of the file (label row, then the
  `Canvas` track).
* `ui/OptionsDialog.kt`: `IntroDialog` with the `HelpItem`s.
* `ui/Sheets.kt`: `DocumentsSheet` ("About this edition") opened by `showDocuments`.
