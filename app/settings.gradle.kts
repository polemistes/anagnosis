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
for (slug in listOf("antigone", "ajax", "electra", "odyssey", "symposium", "newtestament")) {
    include(":packs:$slug")
}
