# Reading aloud and screen readers: implementation plan

The reader learns to read the Greek aloud in a reconstructed pronunciation (Homeric, Attic or
Koine), with the spoken word highlighted, and becomes usable with Android's screen reader
(TalkBack). Decided with the author on 2026-10-20. This file is the brief: follow it step by
step, tick the steps off under Progress, and commit after each step (the plan file with it).
The steps are written for Opus 5.5. The phonology was settled by the author with Fable 5.1 and
is not to be re-decided: if a word or a spelling turns up that the rules below do not cover,
say so and ask rather than guess. The same goes for anything else the brief does not settle.

When a step is done, stop the Gradle daemons (`./gradlew --stop`) and close any emulator: the
machine's memory is shared with other work.

## Why this design

* Android's own voices speak Modern Greek, which is unintelligible for a learner of the ancient
  language. No open-source neural voice for Ancient Greek exists, and no recordings with a
  licence that allows a sold app were found (assessed 2026-10-20). eSpeak NG is the only
  open-source synthesizer with any Ancient Greek, it is formant synthesis (robotic but every
  sound distinct), a few megabytes, offline, and GPL-3 like Anagnosis, so it can be built into
  the app. Its own Ancient Greek rules are crude (all accents as stress, no long α ι υ, θ φ χ as
  fricatives), so the app does the letters-to-sounds itself and hands eSpeak phoneme strings;
  eSpeak is only the mouth. If a recorded voice (Piper) ever becomes possible, it takes the same
  phoneme strings.
* Vowel length of α ι υ is not in the spelling. Morpheus knows it for most forms (it marks long
  vowels in its output; the pipeline has been throwing the marks away) and the reader ships the
  Morpheus analyses in `lexicon.sqlite`, so the length can be looked up at speech time.
* For blind readers: the reader's own voice reads the Greek; TalkBack does everything else.
  Word look-up has to work without lag, so the per-word accessibility nodes exist only while a
  screen reader is running. Looking up Greek words inside a dictionary entry stays as it is
  (a tap on the entry text), which TalkBack cannot do: the author decided it is a gimmick not
  worth any cost. Braille displays handle polytonic Greek in current versions, so the Greek is
  left as text, never replaced by a stripped copy.

## Decisions already taken (do not reopen them)

* Three pronunciations, called in the app **Homeric**, **Attic** and **Koine**. Each option
  shows one line under its name: "Ionic Greek of the epics, about 700 BC"; "Athens, about
  400 BC"; "Hellenistic Greek of the New Testament, about AD 100". (The author prefers the
  term Hellenistic; Koine is used as the label because more people know it, and the
  description says Hellenistic.)
* Every text has its own default: the Odyssey Homeric, the New Testament Koine, everything
  else Attic. The reader may override it in Options, for all texts at once ("The text's own"
  is the default choice there).
* Homeric and Attic have a pitch accent, done with eSpeak's tone phonemes (as its Vietnamese
  and Chinese voices do). Koine has a stress accent. If the tone phonemes cannot be made to
  work within step 3, Homeric and Attic fall back to stress, the plan file says so under Known
  limitations, and the author is told.
* The app's letters-to-sounds code lives in common Kotlin (`greek/Phonology.kt`) with unit
  tests; eSpeak's own dictionary rules are not used. The phoneme table (the sounds) and the
  voice file are ours, compiled by the pipeline from eSpeak's sources; the compiled data files
  are committed.
* Native code: a new Android library module `app/espeak` builds eSpeak NG from an unpacked
  copy of its sources (tag 1.52.0, fetched by a script, ignored by git, like `pipeline/sources`
  and `pipeline/tessdata`) with the NDK, plus a small JNI wrapper. The shared module talks to it
  through an `expect`/`actual` interface so that the common code stays free of Android.
* Reading controls: a play bar above the progress bar (previous sentence, play/pause, next
  sentence, speed, close); the spoken word is highlighted like a search hit; pages turn by
  themselves; the word sheet gets a speaker button and shows the word in IPA; a "Read from
  here" button on the word sheet starts reading at that sentence.
* The speed is a setting in words per minute, 100–220, default 150 (eSpeak's own default of
  175 is too fast for tone-marked Greek); shown to the reader as a slider labelled Slower/Faster.
* The screen-reader mode has two shapes, chosen in Options under "Screen reader": words one by
  one (default; each word a button that opens its sheet) or whole lines with look-up actions
  (for braille readers; the line is one node whose accessibility actions name each word).
* The Greek text carries the language mark `el` (Modern Greek) for TalkBack, so that a Greek
  voice reads it when the reader has one installed: Android has no Ancient Greek voice to ask
  for. This only affects what TalkBack says while moving around; the proper pronunciation is
  the app's own.
* No version bump in this plan: the author decides when the release goes out. (Reader 0.3.0 is
  on the store; this will be 0.4.0.)

## Not in this plan (later, maybe)

* Reading the translation aloud (Android's English voices would do; a cheap follow-up).
* A neural voice (Piper) trained on recordings. Needs several hours of a single speaker under a
  usable licence; none exists.
* Offering the engine as a system speech engine for TalkBack.

## 1. The phonology (`greek/Phonology.kt`)

### Input and output

```kotlin
enum class Pronunciation(val label: String, val description: String) { HOMERIC, ATTIC, KOINE }

/** One sound. [tone] is set on vowels only; [length] is true for a long vowel or diphthong. */
class Segment(val ipa: String, val long: Boolean = false, val tone: Tone? = null, val vowel: Boolean = false)
enum class Tone { HIGH, RISING, FALLING, STRESS }

object Phonology {
    /** The sounds of one word. [marked] is the form with vowel-length marks (see §2), or null. */
    fun segments(form: String, marked: String?, variant: Pronunciation): List<Segment>
    /** For the word sheet: IPA with tone marks, e.g. "anɛ̌ːr", "ˈanθropos". */
    fun ipa(segments: List<Segment>): String
    /** eSpeak phoneme mnemonics for one word (without the [[ ]]), see §3. */
    fun espeak(segments: List<Segment>, variant: Pronunciation): String
}
```

The IPA rendering used in the tests: long vowels with `ː`; HIGH as an acute on the vowel
(á), RISING as a caron (ǎ, and on a long vowel ǎː), FALLING as a circumflex (â); on a
diphthong the mark goes on its first letter and the second is written plain (zděus, not
zděu̯s); STRESS as `ˈ` before the stressed syllable: before the consonants that precede the
vowel when they could begin a Greek word (one consonant; σ + stop; stop + λ ρ μ ν; σ + stop +
λ ρ), otherwise before the last consonant of the cluster (xriˈstos, evaŋˈgɛlion); geminates
written twice (pollá). Use combining marks (U+0301, U+030C, U+0302) after the vowel letter so that any IPA
letter can carry them; normalise the expected strings in the tests with NFD on both sides.

### Normalisation (all variants)

1. NFD; lower-case. Remember whether the word ends in an elision mark (ʼ U+02BC, ’, ᾽ U+1FBD,
   ' ) and strip it; strip U+0345 (iota subscript) after noting on which vowel it stood.
2. Final sigma ς and lunate ϲ → σ. Ignore characters that are not Greek letters or combining
   marks (digits, Latin, punctuation); a token without any Greek letter yields no segments.
3. Split into letters with their marks: breathing (U+0313 smooth, U+0314 rough), accent
   (U+0301 acute, U+0300 grave, U+0342 circumflex), diaeresis (U+0308), length (U+0304 macron,
   U+0306 breve), subscript.
4. Vowels: α ε η ι ο υ ω. Diphthongs: a vowel followed by ι or υ is one nucleus when the
   second letter has no diaeresis and the first letter carries no breathing and no accent (in a
   true diphthong the marks stand on the second letter). Pairs: αι ει οι υι αυ ευ ηυ ου ωυ.
   A vowel with the subscript (ᾳ ῃ ῳ) is a long diphthong of its own kind. Anything else is a
   separate nucleus (ἀί → a.i; ἄυπνος → a.y…).
5. Length of a nucleus: η ω and every diphthong long; ε ο short; α ι υ long when they carry a
   macron, a circumflex or the subscript, else short. A breve means short. (ει and ου are long
   single vowels in Attic and Homeric; see the tables.)
6. Accent of a nucleus: acute, grave, circumflex or none; the breathing of the word is the
   breathing of the first nucleus (or of ῥ).

### The sounds

Attic (Athens, c. 400 BC; after W. S. Allen, Vox Graeca, 3rd ed. 1987, and P. Probert in A
Companion to the Ancient Greek Language, 2010):

| Spelling | Sound | Spelling | Sound |
|---|---|---|---|
| α / ᾱ | a / aː | αι | ai |
| ε | e | ει | eː |
| η | ɛː | οι | oi |
| ι / ῑ | i / iː | υι | yi |
| ο | o | αυ | au |
| ω | ɔː | ευ | eu |
| υ / ῡ | y / yː | ηυ | ɛːu |
| ᾳ ῃ ῳ | aːi ɛːi ɔːi | ου | uː |
| | | ωυ | ɔːu |

| Letter | Sound | Letter | Sound |
|---|---|---|---|
| β δ γ | b d g; γ before γ κ χ ξ = ŋ | θ φ χ | tʰ pʰ kʰ |
| π τ κ | p t k | ζ | zd |
| ξ ψ | ks ps | σ | s; z before β γ δ μ |
| λ μ ν ρ | l m n r | ῥ | hr (voiceless r, rendered h + r) |
| rough breathing | h before the first vowel | double letters | both sounds (geminate) |

Accent (Attic and Homeric): acute on a short vowel = HIGH; acute on a long vowel or diphthong
= RISING; circumflex = FALLING; grave = no tone; no accent = no tone.

Homeric (the Ionic of the epics as conventionally read, c. 700 BC): as Attic except υ / ῡ =
u / uː (so υι = ui, and this u is also the second element of αυ ευ ηυ), ου = oː. No digamma
(the text does not write it). Rough breathing is pronounced as written.

Koine (Hellenistic Greek, c. AD 100; after G. Horrocks, Greek: A History of the Language and
its Speakers, 2nd ed. 2010, ch. 6, and the papyri as reported there). No vowel length at all
(every nucleus short) and no pitch; the accented syllable gets STRESS, whichever accent it
carries (acute, grave or circumflex).

| Spelling | Sound | Spelling | Sound |
|---|---|---|---|
| α, ᾳ | a | ει | i |
| ε, αι | ɛ | οι, υι, υ | y |
| η, ῃ | e | ου | u |
| ι | i | αυ | av, or af before a voiceless consonant (π τ κ φ θ χ ξ ψ σ) or at the end of the word |
| ο, ω, ῳ | o | ευ, ηυ | ev / ef likewise |

| Letter | Sound | Letter | Sound |
|---|---|---|---|
| β δ γ | v ð ɣ; γ before γ κ χ ξ = ŋ (γγ = ŋg) | θ φ χ | θ f x |
| π τ κ | p t k | ζ | z |
| ξ ψ | ks ps | σ | s; z before β γ δ μ |
| λ μ ν ρ | l m n r | ῥ | r |
| rough breathing | nothing (lost) | double letters | one sound |

### Seed tests (`commonTest/.../PhonologyTest.kt`)

Every row below is a test; add more as the rules get exercised, but do not change these
without asking. `marked` is the length-marked form where it matters (§2); the test passes it
directly.

Attic:

| form | marked | expected |
|---|---|---|
| ἄνδρα | | ándra |
| ἀνήρ | | anɛ̌ːr |
| Μοῦσα | | mûːsa |
| πολύτροπον | | polýtropon |
| ὅς | | hós |
| πολλά | | pollá |
| θάλασσα | | tʰálassa |
| ψυχή | ψῡχή | psyːkʰɛ̌ː |
| ἀγγέλλω | | aŋgéllɔː |
| Ζεύς | | zděus |
| οὐδείς | | uːděːs |
| ᾠδή | | ɔːidɛ̌ː |
| εἰμί | | eːmí |
| ῥήτωρ | | hrɛ̌ːtɔːr |
| ἄνθρωπος | | ántʰrɔːpos |
| γιγνώσκω | | gignɔ̌ːskɔː |
| ἐσβάλλω | | ezbállɔː |
| τιμή | τῑμή | tiːmɛ̌ː |
| νεανίας | νεᾱνίᾱς | neaːníaːs |
| ἀΐσσω | | aíssɔː |
| Ἀθηναῖος | | atʰɛːnâios |
| δέ | | dé |
| δὲ | | de |
| λῦσαι | | lŷːsai |
| ἀλλ᾽ | | all |

Koine:

| form | expected |
|---|---|
| ἀνήρ | aˈner |
| φωνή | foˈne |
| εἰρήνη | iˈrene |
| Χριστός | xriˈstos |
| αὐτός | afˈtos |
| εὐαγγέλιον | evaŋˈgɛlion |
| υἱός | yˈos |
| βασιλεία | vasiˈlia |
| οἶκος | ˈykos |
| ἡμέρα | eˈmɛra |
| καί | ˈkɛ |
| ἐγώ | ɛˈɣo |
| θεός | θɛˈos |
| ἄνθρωπος | ˈanθropos |
| Ἰησοῦς | ieˈsus |
| δόξα | ˈðoksa |
| Ζεύς | ˈzefs |
| πνεῦμα | ˈpnevma |
| ἄλλος | ˈalos |

Homeric:

| form | marked | expected |
|---|---|---|
| Μοῦσα | | môːsa |
| πολύτροπον | | polútropon |
| θυμός | θῡμός | tʰuːmós |
| Ζεύς | | zděus |
| οὐ | | oː |
| Ὀδυσσεύς | | odussěus |
| ἠώς | | ɛːɔ̌ːs |

Also test: `ipa()` and `espeak()` on a few of these; a token of digits gives nothing; a
capital initial (Ἄνδρα) gives the same as the lower-case word.

### Sentences and pauses (`greek/Utterance.kt`)

```kotlin
/** One sentence (or line) ready for the engine: the phoneme text and where each word starts in it. */
class Utterance(val text: String, val words: List<WordSpan>)   // WordSpan(tokenId, lineId, start, end, textOffset)
object Utterances {
    fun build(tokens: List<Tokens>, lineText: (Long) -> String, marked: (Tokens) -> String?, variant: Pronunciation): Utterance
}
```

* Each word becomes `[[` + `Phonology.espeak(...)` + `]]`, words separated by a space. Keep a
  map from the offset of each `[[` in the text to its token, for the engine's word events.
* An elided word (ἀλλ᾽, δ᾽) is joined to the next word without a space and without a pause.
* Punctuation after a word (in the line text between this token's end and the next token's
  start): `,` gives a short pause, `.` `·` `;` `!` `:` a long one, the end of a verse line a short
  one. Use eSpeak's pause phonemes inside the brackets (`_:` short, `_::` long; check with
  `espeak-ng -x` what the installed engine prints for commas and full stops, and use the same).
* A sentence is the tokens with the same `sentence` id, in order; where a text has no sentence
  ids (none of ours), a line.

## 2. Vowel length (pipeline and lexicon)

Morpheus marks length in its output. Example lines from `cruncher -S`:

```
polla/      <NL>N polla_/,polu/s  fem nom/voc sg  doric aeolic  os_h_on</NL>   (fem. sg.: long α)
            <NL>N polu/s  neut nom/voc/acc pl  os_h_on</NL>                     (neut. pl.: short)
yuxa/s      <NL>N yu_xa_/s,yuxh/  fem acc pl  h_hs</NL>
lu=sai      <NL>V lu/w  aor inf act  aor1,reg_conj</NL>                        (circumflex ⇒ long; no mark needed)
```

The rule: when the form has a long α ι υ that the spelling does not show, the first field is
`form-with-marks,lemma`; `_` after a vowel is long, `^` short; without the comma the form has
no hidden long vowel. (Verified on 20 words on 2026-10-20.)

Changes:

* `pipeline/anagnosis_pipeline/morpheus_forms.py`: keep the marked form. `_to_unicode` strips
  `_` and `^`; add `_marked_form(head)` that takes the part before the comma, converts it with
  `beta_code` after turning `_` into a combining macron U+0304 and dropping `^`, and returns
  it in NFD; write it as a fifth column of `morpheus-analyses.tsv.gz` (empty when there is
  none). Re-running `build-morpheus-forms` runs Morpheus over the whole corpus again; it takes a
  long time (see `pipeline/build/build-forms.log` for the last run). Do it once, in the
  background, and do not run it on a machine that is short of memory.
* `pipeline/anagnosis_pipeline/forms.py`: a new table in `lexicon.sqlite`:

  ```sql
  CREATE TABLE vowel_length (form_key TEXT NOT NULL, lemma_key TEXT NOT NULL, postag TEXT NOT NULL, marked TEXT NOT NULL);
  CREATE INDEX vowel_length_form ON vowel_length(form_key);
  ```

  one row per (form key, lemma key, postag) that has a marked form, from the fifth column.
  Bump `data/lexicon.sqlite.version` as the other lexicon changes do. Add the table to
  `sqldelight-lexicon` with a query `selectVowelLength(form_key)`.
* App side, `AnagnosisRepository.markedForm(token: Tokens): String?`: the rows for the token's
  form key (the same key function the analyser uses); pick the row with the token's lemma key
  and postag; else the rows with its lemma key if they all give the same marked form; else
  null. Then transfer the macrons onto the token's own form: walk the base letters of both
  strings (NFD, marks removed) in parallel, and where the marked form has a macron on a letter,
  put a combining macron on the same letter of the token's form (the two have the same letters
  in the same order, since the keys matched; if they do not, return null). This is what
  `Phonology.segments` gets as `marked`.
* The word sheet shows the IPA under the form, after the morphology line, in the text's
  pronunciation (or the override): "anɛ̌ːr" — with a small label "Attic" etc. So step 2 is
  visible before the engine exists.

## 3. The engine (`app/espeak`)

### Fetching eSpeak's sources

`app/espeak/fetch-espeak.sh`: clones `https://github.com/espeak-ng/espeak-ng.git` at tag
`1.52.0` into `app/espeak/espeak-ng/` (ignored by git) and applies the patches in
`app/espeak/patches/`. `app/espeak/README.md` says so, with the licence (GPL-3.0-or-later, the
same as the app) and the origin.

Patch 1 (`tone-language.patch`): in `src/libespeak-ng/tr_languages.c`, the entry for our
language code makes it a tone language: find how Vietnamese does it (`tr->langopts.tone_language
= 1` in the `L('v','i')` case) and add the same for `L3('g','r','c')` (the 3-letter macro; see
how `L3` is used in that file). Without this eSpeak ignores the `Tone()` phonemes.

### The phoneme table and the voice (`app/espeak/phsource/`)

* `ph_grc`: our table, `phonemetable grc base1`, replacing the upstream entry (the pipeline
  script edits the upstream `phsource/phonemes` master file: the lines `phonemetable grc base2`
  and `include ph_greek_ancient` become `phonemetable grc base1` and `include ph_grc`).
  Mnemonics are at most 4 characters and eSpeak matches the longest; these are ours:

  | IPA | mnemonic | IPA | mnemonic |
  |---|---|---|---|
  | a aː | a a: | ai au | aI aU |
  | e eː | e e: | ei̯ (not used) | |
  | ɛ ɛː | E E: | oi ou (Homeric ωυ: ɔːu) | oI oU |
  | i iː | i i: | yi ui | yI uI |
  | o oː | o o: | eu ɛːu | eU EU |
  | ɔː | O: | aːi ɛːi ɔːi | aaI EEI OOI |
  | u uː | u u: | p b t d k g | p b t d k g |
  | y yː | y y: | pʰ tʰ kʰ | pH tH kH |
  | f v θ ð x ɣ | f v T D x Q | s z | s z |
  | m n ŋ | m n N | l r h | l r h |

  Vowels: copy the formant definitions from `ph_greek` / `ph_greek_ancient` / `ph_english`
  (`FMT(vowel/...)`) with lengths of about 110 ms short and 200 ms long; diphthongs from
  `vdiph/...` files that exist in `phsource/` (list them; `ph_greek_ancient` already uses
  `vdiph/eeu`, `vdiph/0i`, `vdiph/oou`, `vdiph/yi`). Aspirated stops: copy `p#`, `t#`, `k#`
  from `ph_hindi` and name them `pH tH kH`. Fricatives and the rest come from `base1` already
  (check each mnemonic exists with `espeak-ng --compile-phonemes` output and a test utterance).
  Tones: four `stress`-type phonemes with `Tone(...)` as in `ph_vietnam`: `0` neutral (level,
  low-mid), `1` high level, `2` rising, `3` falling. Every syllable of Attic/Homeric gets
  exactly one tone phoneme after its vowel (unaccented syllables get `0`): learn the exact
  placement from `espeak-ng -v vi -x "mà má mả"` on the installed engine and mirror it.
  Koine uses no tones: `'` before the stressed syllable, as eSpeak's stress mark.
* Voice file `app/espeak/voices/grc` (goes to `espeak-ng-data/lang/grk/grc`):

  ```
  name Ancient Greek
  language grc
  words 2
  ```

  (`words` is the pause between words; tune it by ear later. The upstream file's
  `stressLength` line is not needed with phoneme input.)
* Dictionary: eSpeak will not load a voice without `grc_dict`. `app/espeak/dictsource/grc_rules`
  holds the minimum (`.group` with nothing, or copy the upstream file: it is never used because
  the app always sends phonemes).

### Compiling the data (`pipeline/anagnosis_pipeline/speech_data.py`, command `build-speech-data`)

The installed `espeak-ng` (Arch, 1.52.0, same tag as the clone) can compile from a directory of
our own: it looks for `phsource/` and `dictsource/` next to the data directory given by
`ESPEAK_DATA_PATH` (check `--help` and try; if it insists on its own paths, build the
clone's host binary with CMake, `cmake -Bbuild && cmake --build build`, and use
`build/src/espeak-ng`). Steps:

1. Make `pipeline/build/espeak/` with `phsource/` (copy of the clone's, plus `ph_grc`, with the
   master `phonemes` file edited as above), `dictsource/` (`grc_rules`, and `grc_list` if any),
   and `espeak-ng-data/` with `lang/grk/grc`.
2. `ESPEAK_DATA_PATH=pipeline/build/espeak/espeak-ng-data espeak-ng --compile-phonemes`,
   `--compile-intonations`, `--compile=grc`.
3. Copy `phontab phonindex phondata intonations grc_dict` and `lang/grk/grc` to
   `app/espeak/src/main/assets/espeak-ng-data/`, and write `version` there (a hash of the
   inputs) so that the app knows when to re-copy. These compiled files are committed (about
   1.5 MB).

Try it by hand first: `ESPEAK_DATA_PATH=... espeak-ng -v grc "[[a1ndRa]]"` and listen (the
installed `espeak-ng` plays through the speakers; `-w out.wav` writes a file instead).

### The Android module

`app/espeak/build.gradle.kts`: plugin `com.android.library` (AGP from `libs.versions.toml`),
namespace `no.anagnosis.espeak`, `minSdk`/`compileSdk` as the others,
`externalNativeBuild { cmake { path = file("src/main/cpp/CMakeLists.txt") } }`,
`ndk { abiFilters += listOf("arm64-v8a", "armeabi-v7a", "x86_64") }` (x86_64 for the
emulator). Add `include(":espeak")` to `settings.gradle.kts` and
`implementation(project(":espeak"))` to the shared module's `androidMain`.

The NDK and CMake are not installed on this machine (`~/Android/Sdk` has no `ndk/` or
`cmake/`). Install them with the SDK manager before building (`sdkmanager "ndk;27.2.12479018"
"cmake;3.22.1"`, or the versions AGP 9 asks for in its error message); say so to the author
when you do, it is a download of about a gigabyte.

`src/main/cpp/CMakeLists.txt`: follow the clone's `android/jni/CMakeLists.txt`, which does
`add_subdirectory(<clone> espeakng)`, but without libsonic: set `USE_LIBSONIC OFF`,
`USE_ASYNC OFF`, `USE_MBROLA OFF`, `USE_KLATT OFF`, `USE_SPEECHPLAYER OFF`, `BUILD_TESTING
OFF` before the `add_subdirectory`. Our library `anagnosisspeech` (`speech_jni.c`) links
`espeak-ng` and `log`. If the upstream CMake fights the NDK (it builds a command-line tool and
data targets we do not need), list the files of `src/libespeak-ng/*.c` directly in our
CMakeLists instead, as the old Android.mk of the eSpeak app did, with the same defines.

`speech_jni.c` (JNI, class `no.anagnosis.espeak.ESpeakNative`):

* `init(dataPath: String): Int` — `espeak_Initialize(AUDIO_OUTPUT_SYNCHRONOUS, 0, dataPath, 0)`
  returns the sample rate; `espeak_SetVoiceByName("grc")`; `espeak_SetSynthCallback(cb)`.
* `synth(phonemeText: String, rateWpm: Int): ShortArray` — `espeak_SetParameter(espeakRATE,
  rate, 0)`; `espeak_Synth(text, bytes + 1, 0, POS_CHARACTER, 0, espeakCHARS_UTF8 |
  espeakPHONEMES, NULL, NULL)`; the callback appends the samples to a growing buffer and records
  every `espeakEVENT_WORD` as (text_position, sample position: `audio_position` is in ms, see
  `speak_lib.h`); returns the samples.
* `lastWordEvents(): IntArray` — pairs (character offset in the text, sample offset) of the
  last synthesis. Check in a first test whether the word events arrive for `[[ ]]` input and
  whether their character offsets point at our `[[`; if they do not, synthesise one word per
  `espeak_Synth` call instead (each call returns its samples, so the boundaries are known
  exactly) and join the samples with our own silences for the pauses — for Attic and Homeric
  this loses nothing, since the pitch is in the tones; for Koine eSpeak's clause tune would then
  fall on every word, so set the voice's tunes to a flat tune (see `docs/intonation.md`,
  `tunes` in the voice file) in that case. Record which way it went under Known limitations.
* `stop()` — `espeak_Cancel()`.

Kotlin, `no.anagnosis.espeak.ESpeak(context)`: on first use copies the assets to
`filesDir/espeak-ng-data` when the `version` file differs (eSpeak needs real files), then
`init`. `synthesize(text, rate): Synthesized(pcm: ShortArray, sampleRate: Int, words:
List<Pair<Int, Int>>)`. All on a background thread; the native object is a singleton with a
lock (eSpeak is not re-entrant).

Shared side, `commonMain/.../speech/SpeechEngine.kt`: `expect class SpeechEngine` with
`synthesize(utterance: Utterance, rate: Int): Synthesized` and `actual` in `androidMain` over
`ESpeak`. Playback: `commonMain/.../speech/Speaker.kt` is the player state machine
(what is being read, where, playing/paused), and `expect class PcmPlayer` with `actual` over
`AudioTrack` (22050 Hz mono 16-bit, streaming mode) exposing the playback position in samples,
so that the Speaker can map it to the current word (poll every 50 ms with a coroutine while
playing). Request audio focus (`AUDIOFOCUS_GAIN_TRANSIENT_MAY_DUCK`) while playing and give it
up after; TalkBack keeps talking through it, which is right.

## 4. Reading aloud in the reader (`ui/ReaderScreen.kt`, `ui/Sheets.kt`, `ui/OptionsDialog.kt`)

* Settings (`prefs/Settings.kt`, `SettingsStore`): `pronunciation: Pronunciation?` (null = the
  text's own), `speechRate: Int = 150`, `screenReaderLines: Boolean = false` (whole lines).
* `WorkData.pronunciation`: from the bundle's `meta` key `pronunciation` when present
  (`homeric` / `attic` / `koine`); else Homeric when `work.author` is Ὅμηρος, Koine when the
  slug is `newtestament`, else Attic. Pipeline: `build.py` writes the key from an about.md
  header `# pronunciation: homeric` (add the header to `texts/odyssey/about.md` and
  `texts/newtestament/about.md`; the others default to Attic); no bundle is rebuilt for this
  plan, the fallback carries them.
* Options gets a section "Reading aloud": the pronunciation radio (The text's own / Homeric /
  Attic / Koine, each with its description line), the speed slider, and under "Screen reader"
  the two shapes (only shown when a screen reader is running, see §5, with one line saying
  what it is for).
* The top bar: a "Read aloud" entry — an icon button (`Icons.Filled.PlayArrow`) on wide
  screens, a menu item in the overflow menu on compact ones. It opens the play bar and starts
  reading at the first sentence that begins on the current page (or the first token on the
  page when a sentence runs over from the previous page).
* The play bar sits between the pages and the progress scrubber (a `Column` in `bottomBar`):
  previous sentence · play/pause · next sentence · the pronunciation's name as plain text ·
  close. Material's core icons have PlayArrow but no Pause or Stop: draw the pause (two bars)
  and the skip arrows with a small `Canvas`, as `SearchScreen.kt` draws its sliders icon.
  Every control has a `contentDescription`.
* While reading, the current word is highlighted with the search-hit mechanism
  (`PageContent(highlight = ...)`, `ProsePage`'s paragraph highlight): the Speaker exposes
  `current: (lineId, IntRange)?`; it takes precedence over a search highlight. When the next
  sentence's first token lies on another page, scroll the pager there (`animateScrollToPage`)
  before it is spoken. Reading stops at the end of the book (and says nothing; the bar shows
  play again).
* The word sheet: a speaker icon button next to the form (speaks the word alone, at the
  current rate), the IPA line from §2, and a "Read from here" button among the sheet's buttons
  that closes the sheet, opens the play bar and starts at the word's sentence.
* A tap on a word while reading opens the sheet as always; reading goes on. Leaving the reader
  (back, search, syntax) pauses it; coming back shows the bar paused where it was.
* Synthesis runs one sentence ahead on `Dispatchers.Default`, so that the next sentence is
  ready when the current one ends.

## 5. Screen readers (`ui/ReaderScreen.kt`, `ui/GreekKeyboard.kt`, `ui/SyntaxScreen.kt`)

* `expect fun screenReaderActive(): State<Boolean>` (`commonMain/ui/Accessibility.kt`);
  `actual` on Android reads `AccessibilityManager.isTouchExplorationEnabled` and follows it
  with `addTouchExplorationStateChangeListener` in a `DisposableEffect`. Everything below
  happens only while it is true; the sighted path is not touched (no extra nodes, no extra
  work per word).
* Words one by one (default): in `GreekLineRow` and `ProseParagraph`, after the text has laid
  out, every token gets an invisible `Box` placed over its bounds (`TextLayoutResult.
  getBoundingBox` for the token's characters, merged per visual line; a token wrapped over two
  lines gets two boxes, the second `invisibleToUser`) with
  `Modifier.semantics { text = AnnotatedString(form); role = Role.Button; onClick { onWord(id); true };
  customActions = listOf("Read the sentence aloud", "Read from here", "Syntax of the sentence", "Add a note") }`.
  The line's `Text` gets `clearAndSetSemantics { }` so that it is not read twice; the line
  number keeps its node with `contentDescription = "Line 12"` and `traversalIndex = -1f` so it
  is read before the words. Section headers and speaker names are already text nodes.
* Whole lines (option): the line's `Text` keeps its semantics (TalkBack reads the whole line;
  a braille display shows it) and gets `customActions` of "Look up ἄνδρα", "Look up μοι", … one
  per token, plus the four actions above; no per-word boxes.
* The Greek styles (`styles.greek`, `styles.prose`, the word sheet's form, the search results'
  Greek) carry `localeList = LocaleList("el")` in their `TextStyle`/`SpanStyle`; Compose turns
  this into the language mark TalkBack uses to pick a voice (verified in Compose 1.11.2's
  accessibility code).
* `GreekKeyboard`: each key gets a `contentDescription`: the letters themselves; the marks
  "Smooth breathing", "Rough breathing", "Acute", "Grave", "Circumflex", "Iota subscript",
  "Diaeresis"; "Apostrophe", "Space", "Backspace", "Done".
* `SyntaxScreen`: the drawn diagram's `Canvas` gets `contentDescription = "Diagram of the
  sentence; the list shows the same in words"` and the switch to the list view is a labelled
  button (check it already is).
* The play bar, the options and the sheets are standard Material parts and need nothing.

## Steps

Commit after each step with the plan's Progress ticked; the message names the step. Run the
unit tests (`./gradlew :shared:testDebugUnitTest` or whatever runs `commonTest` here; see how
the earlier plans' tests were run) before each commit. Where a step needs the emulator, use the
same one as before (see `app/README.md`), and close it afterwards.

1. **Phonology.** `greek/Phonology.kt`, `greek/Utterance.kt` and `PhonologyTest.kt` with every
   seed row, plus the sentence builder's tests (pauses, elision joining, offsets). No UI.
2. **Vowel length.** The pipeline changes, the lexicon table and its version bump, the
   repository look-up, the IPA line on the word sheet (with the text's pronunciation). Start
   `build-morpheus-forms` early in the step, in the background, since it is slow; rebuild the
   lexicon with `build` afterwards. Check ten words of the Odyssey on the emulator or in a host
   test against the lexicon file (there is a host test set-up in `androidHostTest`).
3. **The engine.** `fetch-espeak.sh` and the patch; `ph_grc`, the voice, `build-speech-data`;
   listening test on the desktop with `espeak-ng` and the compiled data for all three variants
   (write a tiny script that prints an utterance for a line of each text and plays it); the
   `app/espeak` module, JNI, `SpeechEngine`/`PcmPlayer`; a hidden check: the word sheet's
   speaker button, which speaks the word on the emulator. This is the step with the open
   questions (tones; word events): resolve them as the brief says and write the outcome under
   Known limitations.
4. **Reading in the reader.** Settings and options, the per-text default, the top-bar entry,
   the play bar, the highlight, the page turns, "Read from here", pause on leaving.
5. **Screen readers.** `screenReaderActive`, both shapes, the language marks, the keyboard and
   syntax labels. Test with TalkBack on the emulator (it can be installed from the Play Store
   on a Play-enabled image, or sideloaded) — move through a page, open a word, read a sentence
   aloud, type in the search with the Greek keyboard.
6. **Words.** The help text (reading aloud, the three pronunciations in one sentence each, the
   screen-reader modes), About → Software (eSpeak NG, GPL-3.0-or-later, its site), `README.md`
   (licences section: eSpeak NG), `app/README.md` (how to fetch and build eSpeak and the
   speech data), and `play/README.md` gets a note that the listing should say the reader reads
   the Greek aloud in reconstructed pronunciation and works with TalkBack — the listing itself
   is the author's.

## Known limitations (accepted)

* Formant synthesis sounds robotic. Clear, not pleasant; a recorded voice is a later project.
* Vowel length is only as good as Morpheus: a form it does not know, or where its analyses
  disagree and the token's parse does not settle it, is read with short α ι υ.
* Homeric reads ει and ου as long single vowels throughout; the genuine diphthongs of early
  epic cannot be told from the spurious ones by spelling.
* Koine is one moment (c. AD 100) of a changing language; some sounds (η, αυ/ευ, the
  fricatives) were still in motion then, and the choices above are one defensible point.
* TalkBack's own voice, while moving about the page, speaks the Greek as Modern Greek (or not
  at all without a Greek voice installed); the proper reading is one action away.
* (Fill in during step 3: tones or stress for Attic/Homeric; word events or per-word synthesis.)

## Decisions made during the work

The author asked (2026-10-20) for the whole plan to be done overnight without questions. Where
the brief says to ask, the decision taken is recorded here instead, for review.

* Koine ευ and ηυ are read [ev]/[ef] (the plan's table), not [ɛv]: the seed tests agree.
* A Koine word without an accent (ὁ, ἐν, enclitics) is marked unstressed (`%`) for eSpeak.
* Where a word has two accents (an enclitic's accent thrown back, ἄνθρωπός τις), Attic and
  Homeric give both a tone; Koine stresses only the first.
* A rough breathing on a vowel inside a word (a koronis in crasis) is not pronounced.
* Step 2: the marked form is a fifth field of the analyses already packed per form key in
  `lexicon.sqlite`, not a table of its own: no new index, and older readers, which read four
  fields, are not affected. Where a treebank analysis and a Morpheus one coincide (same form key,
  lemma and parse), the treebank line carries Morpheus's marked form. The lexicon's version
  changes by itself (it is a hash of the file).
* Step 2: Morpheus was run again over the current corpus, which now takes in the texts added
  since 2 October: the forms table grew from 333 349 to 406 757 form keys. About 150 000
  analyses carry a marked form. A sample of 3000 words per text gave a marked long vowel for
  9–11 % of the words that have an α ι υ (θῡμόν, ἡμέρᾱς, the Doric τᾱ́ν of the choral odes).
* Step 2: the per-text pronunciation is a header of `grc.txt` (`# pronunciation: homeric`), where
  the other bundle keys (`layout`, `dictionaries`) live, not of `about.md`.
* Step 2: the search page's word sheet shows the IPA in the reader's chosen pronunciation, or
  Attic when the choice is "the text's own" (a dictionary word belongs to no text).

## Progress

- [x] Step 1: phonology
- [x] Step 2: vowel length
- [ ] Step 3: the engine
- [ ] Step 4: reading in the reader
- [ ] Step 5: screen readers
- [ ] Step 6: words
