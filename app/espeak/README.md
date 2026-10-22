# The reader's voice (eSpeak NG)

The reader reads the Greek aloud with [eSpeak NG](https://github.com/espeak-ng/espeak-ng)
1.52.0, built into the app. eSpeak NG is licensed GPL-3.0-or-later, the same licence as
Anagnosis. The app does the letters-to-sounds itself (`shared/.../greek/Phonology.kt`, with the
pronunciation tables of `app/PLAN-speech.md`) and sends eSpeak phonemes; eSpeak only makes the
sound.

What is here:

* `fetch-espeak.sh` clones eSpeak NG 1.52.0 into `espeak-ng/` (ignored by git) and applies
  `patches/`. Two patches: `grc-tone-language.patch` makes Ancient Greek a tone language, so that
  the pitch accent of Homeric and Attic Greek is spoken with tone phonemes, as Vietnamese is;
  `klatt-frame-loudness.patch` makes eSpeak's Klatt synthesiser follow the loudness of the
  sound frames (as the formant synthesiser does through the formant heights), loop a mixed-in
  recording for the length of its sound, and mix it at the formant synthesiser's level. Without
  it the rolled r was one tap and the closures of b d g were spoken at full voice.
* `phsource/ph_grc`: the Ancient Greek phoneme table (replaces eSpeak's own
  `ph_greek_ancient`): short and long vowels, diphthongs, aspirated stops, and four tones
  (0 low, 1 high, 2 rising, 3 falling), with the same four at three more levels (10-13, 20-23,
  30-33) and two sentence ends (40 a final fall, 41 a final rise) for the reader's sentence
  melody option (`greek/Melody.kt`).
* `voices/grc` (Homeric and Attic: tonal, spoken by eSpeak's Klatt synthesiser with its fourth
  voice source, `klatt 4`, chosen by ear) and `voices/grc-koine` (Koine: the Modern Greek
  translator, so stress and stress intonation, with our phonemes, and the formant synthesiser,
  which the author preferred for this voice).
* `dictsource/`: an empty Ancient Greek dictionary; eSpeak needs one to exist.
* `src/main/cpp`: the native build (the library only, no audio output) and a small JNI layer
  that synthesises one utterance into memory with its word events.
* `src/main/assets/espeak-ng-data`: the compiled data, committed. Made by
  `pipeline/.venv/bin/python -m anagnosis_pipeline build-speech-data`, which compiles with
  the checkout built for this computer (`espeak-ng/build-host`, built when missing).

Building the app needs the checkout and the Android NDK (29.0.14206865) and CMake (3.31.6)
from the SDK manager:

    app/espeak/fetch-espeak.sh
    sdkmanager "ndk;29.0.14206865" "cmake;3.31.6"

After changing `ph_grc`, the voices or a patch: run `fetch-espeak.sh` again (for a patch),
then `build-speech-data`, and commit the new assets.

To listen to the voice on the computer:

    pipeline/.venv/bin/python -m anagnosis_pipeline speech-samples prepare
    (cd app && ./gradlew :shared:testAndroidHostTest --tests '*SpeechSampleDump*')
    pipeline/.venv/bin/python -m anagnosis_pipeline speech-samples render

which writes one WAV per text to `pipeline/build/speech-samples/` (the Odyssey in all three
pronunciations).
