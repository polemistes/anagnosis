// The text sold inside the reader as an in-app product (text_antigone): an on-demand asset pack
// that Google Play hosts and delivers once the text is bought. It holds the text's database and its
// version, copied from ../data; the reader copies them in (see PlayTextShop).
plugins {
    alias(libs.plugins.assetPack)
}

assetPack {
    packName.set("antigone")
    dynamicDelivery {
        deliveryType.set("on-demand")
    }
}

val copyText by tasks.registering(Sync::class) {
    from(rootProject.file("../data")) {
        include("antigone.sqlite", "antigone.sqlite.version")
    }
    into(layout.projectDirectory.dir("src/main/assets/data"))
}
tasks.matching { it.name != copyText.name }.configureEach { dependsOn(copyText) }
