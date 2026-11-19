import java.util.Properties
import org.jetbrains.kotlin.gradle.dsl.JvmTarget

plugins {
    alias(libs.plugins.androidApplication)
    alias(libs.plugins.composeCompiler)
}

// The local list app/author-packs.txt (see settings.gradle.kts): its texts as asset packs, and
// data/catalog-author.json as the catalogue. Without the file the build is the public one, unchanged.
val authorPacks = rootProject.file("author-packs.txt").takeIf { it.isFile }?.readLines()
    ?.map { it.substringBefore('#').trim() }?.filter { it.isNotEmpty() }.orEmpty()
// The texts of that list given without a purchase and shown whatever their release date: only
// when asked for on purpose, -PauthorRelease=true (a release for the internal testing track) or
// -PauthorGrant=true (a debug build). Otherwise the build is the normal one.
val authorGrant = authorPacks.isNotEmpty() &&
    (providers.gradleProperty("authorRelease").orNull == "true" || providers.gradleProperty("authorGrant").orNull == "true")
/** The public release's version; a granting build sits one above it (see versionCode below). */
val productionVersionCode = 20
val productionVersionName = "0.8.0"

dependencies {
    implementation(projects.shared)
    implementation(libs.androidx.activity.compose)
    implementation(libs.kotlinx.coroutines.core)
    // texts bought in the app (Google Play Billing) and delivered as asset packs (Play Asset Delivery)
    implementation(libs.play.billing)
    implementation(libs.play.asset.delivery)
}

android {
    namespace = "no.anagnosis"
    compileSdk = libs.versions.android.compileSdk.get().toInt()

    defaultConfig {
        applicationId = "no.anagnosis.reader"
        minSdk = libs.versions.android.minSdk.get().toInt()
        targetSdk = libs.versions.android.targetSdk.get().toInt()
        // Version rule: productionVersionCode is the public release's. A granting
        // build (authorGrant above; released with -PauthorRelease=true to the internal testing
        // track only) takes productionVersionCode + 1 and the versionName suffix "-author": a
        // tester's phone installs the highest code it may have, so that bundle must stand above
        // the production one; the next production release then takes the code after it.
        versionCode = if (authorGrant) productionVersionCode + 1 else productionVersionCode
        versionName = if (authorGrant) "$productionVersionName-author" else productionVersionName
        // The texts this build gives without a purchase (comma-separated slugs): empty unless granting
        buildConfigField("String", "GRANTED_TEXTS", "\"${if (authorGrant) authorPacks.joinToString(",") else ""}\"")
    }
    buildFeatures {
        buildConfig = true
    }
    // the texts sold in the app, delivered by Google Play once bought (see packs/antigone)
    assetPacks += listOf("antigone", "ajax", "electra", "odyssey", "symposium", "gorgias", "agamemnon", "choephoroi", "eumenides", "clouds", "theogony", "truestory", "hermas", "newtestament", "trachiniae", "oedipustyrannus", "oedipuscoloneus", "philoctetes", "lysias").map { ":packs:$it" }
    assetPacks += authorPacks.map { ":packs:$it" }
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
            proguardFiles(getDefaultProguardFile("proguard-android-optimize.txt"), "proguard-rules.pro")
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
// every text is bought in the app and arrives as an asset pack (packs/), or comes from a text app
// of its own (see antigoneApp).
val copyBundle by tasks.registering(Sync::class) {
    from(rootProject.file("../data")) {
        include("lexicon.sqlite", "lexicon.sqlite.version", if (authorPacks.isEmpty()) "catalog.json" else "catalog-author.json")
        // with the local list: the local catalogue, under the name the app reads
        rename("catalog-author\\.json", "catalog.json")
    }
    into(layout.projectDirectory.dir("src/main/assets/data"))
}
tasks.matching { it.name == "preBuild" }.configureEach { dependsOn(copyBundle) }
