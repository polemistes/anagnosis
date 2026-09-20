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
        applicationId = "no.anagnosis.antigone"
        minSdk = libs.versions.android.minSdk.get().toInt()
        targetSdk = libs.versions.android.targetSdk.get().toInt()
        versionCode = 1
        versionName = "0.1.0"
    }
    packaging {
        resources {
            excludes += "/META-INF/{AL2.0,LGPL2.1}"
        }
    }
    buildTypes {
        getByName("release") {
            isMinifyEnabled = false
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

// The data bundle is built by the Python pipeline into ../data and copied into the APK assets.
val copyBundle by tasks.registering(Copy::class) {
    from(rootProject.file("../data/antigone.sqlite"), rootProject.file("../data/antigone.sqlite.version"))
    into(layout.projectDirectory.dir("src/main/assets"))
}
tasks.matching { it.name == "preBuild" }.configureEach { dependsOn(copyBundle) }
