rootProject.name = "anagnosis"
enableFeaturePreview("TYPESAFE_PROJECT_ACCESSORS")

pluginManagement {
    repositories {
        google {
            mavenContent {
                includeGroupAndSubgroups("androidx")
                includeGroupAndSubgroups("com.android")
                includeGroupAndSubgroups("com.google")
            }
        }
        mavenCentral()
        gradlePluginPortal()
    }
}

dependencyResolutionManagement {
    repositories {
        google {
            mavenContent {
                includeGroupAndSubgroups("androidx")
                includeGroupAndSubgroups("com.android")
                includeGroupAndSubgroups("com.google")
            }
        }
        mavenCentral()
    }
}

include(":shared")
include(":espeak")
include(":androidApp")
include(":antigoneApp")
include(":odysseyApp")
include(":symposiumApp")
include(":newTestamentApp")
include(":ajaxApp")
include(":electraApp")
include(":oedipusTyrannusApp")
include(":oedipusColoneusApp")
include(":philoctetesApp")
include(":trachiniaeApp")

// The texts sold inside the reader, one on-demand asset pack each (see packs/antigone)
for (slug in listOf("antigone", "ajax", "electra", "odyssey", "symposium", "gorgias", "agamemnon", "choephoroi", "eumenides", "clouds", "theogony", "truestory", "hermas", "newtestament", "trachiniae", "oedipustyrannus", "oedipuscoloneus", "philoctetes")) {
    include(":packs:$slug")
}

// The author's own build (pipeline/PLAN-euripides.md, "The author's build"): author-packs.txt
// beside this file, ignored by git and absent from every public build, may name texts held back
// until their release date, one slug a line; their packs are included too, and the reader
// bundles data/catalog-author.json (androidApp/build.gradle.kts). Without the file nothing here
// changes. Such a build is for the author's own devices only: a release task is refused unless
// it is asked for on purpose with -PauthorRelease=true, and that bundle goes to Google Play's
// internal testing track only (its versionName ends in "-author"; see play/README.md).
val authorPacks = file("author-packs.txt").takeIf { it.isFile }?.readLines()
    ?.map { it.substringBefore('#').trim() }?.filter { it.isNotEmpty() }.orEmpty()
if (authorPacks.isNotEmpty()) {
    val release = gradle.startParameter.taskNames.filter { it.contains("release", ignoreCase = true) }
    val authorRelease = gradle.startParameter.projectProperties["authorRelease"] == "true"
    if (release.isNotEmpty() && !authorRelease) {
        throw GradleException("app/author-packs.txt names held-back texts ($authorPacks): this is the author's " +
            "own build, not a public release (asked for: $release). Move the file away to build the public " +
            "release. A release bundle with these texts is built only with -PauthorRelease=true; it is for " +
            "Google Play's internal testing track only and must never be promoted to another track.")
    }
    for (slug in authorPacks) {
        include(":packs:$slug")
    }
}
