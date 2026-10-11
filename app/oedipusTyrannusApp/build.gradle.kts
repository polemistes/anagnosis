import java.util.Properties
import org.jetbrains.kotlin.gradle.dsl.JvmTarget

// Sophocles' Oedipus Tyrannus, sold as an app of its own. It carries the text's database and hands it to the
// Anagnosis reader, which copies it in when it finds this app installed and signed with the same
// key (see DriverFactory.android.kt). Opened by itself, it opens the reader at the Oedipus Tyrannus.
plugins {
    alias(libs.plugins.androidApplication)
}

android {
    namespace = "no.anagnosis.oedipustyrannus"
    compileSdk = libs.versions.android.compileSdk.get().toInt()

    defaultConfig {
        applicationId = "no.anagnosis.oedipustyrannus"
        minSdk = libs.versions.android.minSdk.get().toInt()
        targetSdk = libs.versions.android.targetSdk.get().toInt()
        versionCode = 1
        versionName = "0.1.0"
    }
    // The same upload key as the reader (keystore/, not committed). In Play Console the app must
    // also use the reader's app signing key, or the reader will not accept its text.
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
            // R8 shrinks and renames the code (Google Play asks for it); the activity, named in the
            // manifest, is kept
            isMinifyEnabled = true
            isShrinkResources = true
            proguardFiles(getDefaultProguardFile("proguard-android-optimize.txt"))
            signingConfigs.findByName("upload")?.let { signingConfig = it }
        }
    }
    androidResources {
        // the database is copied out as it is; compressing it would only slow that down
        noCompress += "sqlite"
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

val textSlug = "oedipustyrannus"
val copyText by tasks.registering(Sync::class) {
    from(rootProject.file("../data")) {
        include("$textSlug.sqlite", "$textSlug.sqlite.version", "$textSlug.catalog.json")
    }
    into(layout.projectDirectory.dir("src/main/assets/data"))
}
tasks.matching { it.name == "preBuild" }.configureEach { dependsOn(copyText) }
