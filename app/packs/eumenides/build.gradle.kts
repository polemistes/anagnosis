// The eumenides text as an on-demand asset pack; see packs/antigone.
plugins {
    alias(libs.plugins.assetPack)
}

assetPack {
    packName.set("eumenides")
    dynamicDelivery {
        deliveryType.set("on-demand")
    }
}

val copyText by tasks.registering(Sync::class) {
    from(rootProject.file("../data")) {
        include("eumenides.sqlite", "eumenides.sqlite.version")
    }
    into(layout.projectDirectory.dir("src/main/assets/data"))
}
tasks.matching { it.name != copyText.name }.configureEach { dependsOn(copyText) }
