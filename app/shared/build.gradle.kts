import org.jetbrains.kotlin.gradle.dsl.JvmTarget

plugins {
    alias(libs.plugins.kotlinMultiplatform)
    alias(libs.plugins.androidMultiplatformLibrary)
    alias(libs.plugins.composeMultiplatform)
    alias(libs.plugins.composeCompiler)
    alias(libs.plugins.sqldelight)
}

kotlin {
    compilerOptions {
        freeCompilerArgs.add("-Xexpect-actual-classes")
    }

    // iOS targets go here later:
    // listOf(iosArm64(), iosSimulatorArm64()).forEach { it.binaries.framework { baseName = "Shared"; isStatic = true } }

    androidLibrary {
        namespace = "no.anagnosis.shared"
        compileSdk = libs.versions.android.compileSdk.get().toInt()
        minSdk = libs.versions.android.minSdk.get().toInt()
        compilerOptions {
            jvmTarget = JvmTarget.JVM_17
        }
        androidResources {
            enable = true
        }
        withHostTestBuilder {}
    }

    sourceSets {
        commonMain.dependencies {
            implementation(compose.runtime)
            implementation(compose.foundation)
            implementation(compose.material3)
            implementation(compose.ui)
            implementation(compose.components.resources)
            implementation("org.jetbrains.compose.material:material-icons-core:1.7.3")
            implementation(libs.kotlinx.coroutines.core)
            implementation(libs.sqldelight.runtime)
        }
        commonTest.dependencies {
            implementation(kotlin("test"))
        }
        androidMain.dependencies {
            implementation(libs.sqldelight.android.driver)
            implementation(libs.androidx.activity.compose)
        }
    }
}

compose.resources {
    packageOfResClass = "no.anagnosis.resources"
    publicResClass = true
}

sqldelight {
    databases {
        create("AnagnosisDatabase") {
            packageName.set("no.anagnosis.db")
        }
        create("LexiconDatabase") {
            packageName.set("no.anagnosis.lexdb")
            srcDirs("src/commonMain/sqldelight-lexicon")
        }
    }
}
