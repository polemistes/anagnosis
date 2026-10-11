import java.util.Properties
import org.jetbrains.kotlin.gradle.dsl.JvmTarget

plugins {
    alias(libs.plugins.androidApplication)
    alias(libs.plugins.composeCompiler)
}

dependencies {
    implementation(projects.shared)
    implementation(libs.androidx.activity.compose)
}

android {
    namespace = "no.anagnosis"
    compileSdk = libs.versions.android.compileSdk.get().toInt()

    defaultConfig {
        applicationId = "no.anagnosis.reader"
        minSdk = libs.versions.android.minSdk.get().toInt()
        targetSdk = libs.versions.android.targetSdk.get().toInt()
        versionCode = 3
        versionName = "0.1.0"
    }
    packaging {
        resources {
            excludes += "/META-INF/{AL2.0,LGPL2.1}"
        }
    }
    // The upload key for Google Play lives in keystore/, which is not committed. Without it the
    // release build is unsigned, which is fine for local checks.
    val keystoreProps = rootProject.file("keystore/keystore.properties")
    if (keystoreProps.exists()) {
        val props = Properties().apply { keystoreProps.inputStream().use { load(it) } }
        signingConfigs {
            create("upload") {
                storeFile = rootProject.file(props.getProperty("storeFile"))
                storePassword = props.getProperty("storePassword")
                keyAlias = props.getProperty("keyAlias")
                keyPassword = props.getProperty("keyPassword")
            }
        }
    }
    buildTypes {
        getByName("release") {
            isMinifyEnabled = true
            isShrinkResources = true
            proguardFiles(getDefaultProguardFile("proguard-android-optimize.txt"))
            signingConfigs.findByName("upload")?.let { signingConfig = it }
        }
    }
    compileOptions {
        sourceCompatibility = JavaVersion.VERSION_17
        targetCompatibility = JavaVersion.VERSION_17
    }
}

kotlin {
    compilerOptions {
        jvmTarget = JvmTarget.JVM_17
    }
}

// The data bundles are built by the Python pipeline into ../data and copied into the APK assets:
// lexicon.sqlite (shared dictionaries) and catalog.json. The reader is free and carries no text;
// every text is sold as an app of its own (see antigoneApp).
val copyBundle by tasks.registering(Sync::class) {
    from(rootProject.file("../data")) {
        include("lexicon.sqlite", "lexicon.sqlite.version", "catalog.json")
    }
    into(layout.projectDirectory.dir("src/main/assets/data"))
}
tasks.matching { it.name == "preBuild" }.configureEach { dependsOn(copyBundle) }
