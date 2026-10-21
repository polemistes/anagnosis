# Anagnosis app

Kotlin Multiplatform + Compose Multiplatform. Two modules:

* `shared/` — KMP library holding the data layer and the whole UI (`commonMain`), plus the
  Android database driver (`androidMain`). iOS targets are added here later.
* `androidApp/` — thin Android application: `MainActivity`, manifest, and the data bundle
  copied into its assets at build time.
* `espeak/` — the reading voice: eSpeak NG built with the NDK, and its compiled Ancient Greek
  data. Needs `espeak/fetch-espeak.sh` run once and the NDK and CMake installed; see
  [espeak/README.md](espeak/README.md). The pronunciation rules are in
  `shared/.../greek/Phonology.kt`; the plan and the decisions behind them in `PLAN-speech.md`.

## Requirements

* Android SDK with `ANDROID_HOME` set, or a `local.properties` with `sdk.dir=...`.
  Installed: platform android-36, build-tools 36/37, platform-tools.
* JDK 17 or newer to run Gradle. Android Studio's bundled runtime works:
  `export JAVA_HOME=/opt/android-studio/jbr`.
* For the reading voice (module `espeak`): `espeak/fetch-espeak.sh`, and the NDK 29.0.14206865
  and CMake 3.31.6 from the SDK manager (`sdkmanager "ndk;29.0.14206865" "cmake;3.31.6"`).
* The data bundle: run the pipeline first so that `../data/lexicon.sqlite` and `../data/catalog.json`
  exist (and `../data/<text>.sqlite` for the text apps).

## Build and run

    export JAVA_HOME=/opt/android-studio/jbr ANDROID_HOME=$HOME/Android/Sdk
    ./gradlew :androidApp:assembleDebug
    ./gradlew :androidApp:installDebug     # to a connected device or running emulator

To try the shop and the texts' download packs as Play delivers them, build the bundle and install
it with bundletool's local testing. `tools/bundletool-1.18.1.jar` is Google's release
(github.com/google/bundletool, Apache 2.0), kept here but not in git; fetch it again with
`curl -L -o tools/bundletool-1.18.1.jar https://github.com/google/bundletool/releases/download/1.18.1/bundletool-all-1.18.1.jar`.

    ./gradlew :androidApp:bundleDebug
    java -jar tools/bundletool-1.18.1.jar build-apks --local-testing \
        --bundle=androidApp/build/outputs/bundle/debug/androidApp-debug.aab --output=/tmp/reader.apks
    java -jar tools/bundletool-1.18.1.jar install-apks --apks=/tmp/reader.apks

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
