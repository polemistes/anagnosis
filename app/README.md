# Anagnosis app

Kotlin Multiplatform + Compose Multiplatform. Two modules:

* `shared/` — KMP library holding the data layer and the whole UI (`commonMain`), plus the
  Android database driver (`androidMain`). iOS targets are added here later.
* `androidApp/` — thin Android application: `MainActivity`, manifest, and the data bundle
  copied into its assets at build time.

## Requirements

* Android SDK with `ANDROID_HOME` set, or a `local.properties` with `sdk.dir=...`.
  Installed: platform android-36, build-tools 36/37, platform-tools.
* JDK 17 or newer to run Gradle. Android Studio's bundled runtime works:
  `export JAVA_HOME=/opt/android-studio/jbr`.
* The data bundle: run the pipeline first so that `../data/lexicon.sqlite` and `../data/catalog.json`
  exist (and `../data/<text>.sqlite` for the text apps).

## Build and run

    export JAVA_HOME=/opt/android-studio/jbr ANDROID_HOME=$HOME/Android/Sdk
    ./gradlew :androidApp:assembleDebug
    ./gradlew :androidApp:installDebug     # to a connected device or running emulator

## Structure

    shared/src/commonMain/sqldelight/                 schema + queries (SQLDelight generates typed Kotlin)
    shared/src/commonMain/sqldelight-notes/           the reader's own notes (notes.sqlite, made on the device, never shipped)
    shared/src/commonMain/kotlin/no/anagnosis/data/   repository, models, morphology decoder, text search and lemma index
    shared/src/commonMain/kotlin/no/anagnosis/ui/     reader screen, search page, word and note sheets, HTML renderer
    shared/src/androidMain/                           Android SQLite driver, copies the bundle out of the assets
    androidApp/src/main/                              MainActivity, manifest

Versions are pinned in `gradle/libs.versions.toml` (Gradle 9.6, AGP 9.1, Kotlin 2.4,
Compose Multiplatform 1.11, SQLDelight 2.4). Compose artifacts come from the Compose plugin's
`compose.*` accessors so they always match the plugin version.

The reader's application id is `no.anagnosis.reader`; each text app (`antigoneApp`, `odysseyApp` ...)
has its own (`no.anagnosis.antigone` ...). Ids cannot be changed after the first Play upload.
