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
include(":odysseyApp")
include(":symposiumApp")
include(":newTestamentApp")
include(":ajaxApp")
include(":electraApp")
include(":oedipusTyrannusApp")
include(":oedipusColoneusApp")
include(":philoctetesApp")
include(":trachiniaeApp")
