// The reader's voice: eSpeak NG (GPL-3.0-or-later, the app's own licence) built with the NDK from
// the checkout of fetch-espeak.sh, and its Ancient Greek data (src/main/assets, compiled by the
// pipeline's build-speech-data). See README.md and app/PLAN-speech.md.
plugins {
    alias(libs.plugins.androidLibrary)
}

android {
    namespace = "no.anagnosis.espeak"
    compileSdk = libs.versions.android.compileSdk.get().toInt()
    ndkVersion = "29.0.14206865"

    defaultConfig {
        minSdk = libs.versions.android.minSdk.get().toInt()
        ndk {
            // phones and tablets (arm), and the emulator (x86_64)
            abiFilters += listOf("arm64-v8a", "armeabi-v7a", "x86_64")
        }
        externalNativeBuild {
            cmake {
                arguments += listOf("-DANDROID_STL=none")
            }
        }
    }
    externalNativeBuild {
        cmake {
            path = file("src/main/cpp/CMakeLists.txt")
            version = "3.31.6"
        }
    }
    compileOptions {
        sourceCompatibility = JavaVersion.VERSION_17
        targetCompatibility = JavaVersion.VERSION_17
    }
}
