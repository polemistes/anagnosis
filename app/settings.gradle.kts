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
for (slug in listOf("antigone", "ajax", "electra", "odyssey", "symposium", "gorgias", "agamemnon", "choephoroi", "eumenides", "clouds", "theogony", "truestory", "hermas", "newtestament", "trachiniae", "oedipustyrannus", "oedipuscoloneus", "philoctetes", "lysias")) {
    include(":packs:$slug")
}

// A local list, author-packs.txt beside this file (ignored by git; absent from a fresh checkout),
// may name further texts to bundle as asset packs, one slug a line; with it the reader also bundles
// the local catalogue, data/catalog-author.json (androidApp/build.gradle.kts). Without the file
// nothing here changes.
val authorPacks = file("author-packs.txt").takeIf { it.isFile }?.readLines()
    ?.map { it.substringBefore('#').trim() }?.filter { it.isNotEmpty() }.orEmpty()
if (authorPacks.isNotEmpty()) {
    for (slug in authorPacks) {
        include(":packs:$slug")
    }
}
