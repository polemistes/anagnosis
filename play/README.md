# Google Play

Everything needed for the store listing of the reader, which sells the texts inside it, and for
the text apps, should a text later also be sold as an app of its own.

| App | Package | Bundle (after `./gradlew :<module>:bundleRelease` in app/) | Icon | Feature graphic | Screenshots | Listing |
|---|---|---|---|---|---|---|
| Anagnosis (free, texts bought inside it) | no.anagnosis.reader | app/androidApp/build/outputs/bundle/release/androidApp-release.aab | icon-512.png | feature-graphic.png | screenshots/reader/{phone,tablet-7,tablet-10} | listings/reader.md |

The reader's bundle carries every text on sale as an asset pack (app/packs/), so it is larger
than the app people download (about 100 MB uploaded; the texts are fetched only once bought).

## In Play Console

The reader is free; each text is a one-time in-app product at €3. The product id is author,
work and edition, as given in the text's `about.md` (`product_id`); it can never be changed:

| Text | Product id |
|---|---|
| Antigone | sophocles_antigone_jebb |
| Ajax | sophocles_ajax_jebb |
| Electra | sophocles_electra_jebb |
| Odyssey | homer_odyssey_allen |
| Symposium | plato_symposium_burnet |
| New Testament | newtestament_sbl |

1. Payments profile (needed before anything can be sold).
2. The reader exists already (no.anagnosis.reader, with Play App Signing). Upload the 0.3.0
   bundle to **Test and release › Testing › Internal testing**, with yourself on the testers'
   list, and roll it out. Products can only be created once a bundle with the billing library
   has been uploaded.
3. **Settings › License testing**: add your own Google account. A licence tester buys with
   test cards and is never charged.
4. **Monetize with Play › Products › One-time products**: create the six products above, each
   with a name (the text's English title), a short description, the price €3 (Play converts it to
   local prices), and activate them. The shop lists a text only once its product is active.
5. Install the reader on your phone from the internal testing link (not from Android Studio:
   purchases only work in a copy installed by Google Play). Open Available texts, buy a text with
   a test card, and check that it downloads, appears on the front page and opens. This is the
   check that buying works although the reader has no internet permission.
6. **Policy and programmes › App content**: privacy policy URL
   (https://github.com/polemistes/anagnosis/blob/main/PRIVACY.md); data safety ("no data
   collected or shared": the reader itself sends nothing, and Google's billing library cannot
   send its reports without the internet permission; read the form's help on purchases made
   through Google Play billing before answering); content rating; target audience (not aimed at
   children); ads: none. Play may also ask about the foreground service: it is the download
   service of Play Asset Delivery (type "data sync"), which brings a bought text onto the device.
7. Store listing: title, short and full description from listings/reader.md, the icon, the
   feature graphic and the screenshots.
8. When the test purchase works, promote the release from internal testing to production. The
   products stay as they are.

A new text later: build it, add its pack (app/packs/<slug>, app/settings.gradle.kts and the
reader's `assetPacks`), mark it `google_play: yes` with its `product_id`, release a reader update, then create and
activate its product.

## Text apps (optional)

A text can also be sold as an app of its own, for a store page that people searching for it
can find; the reader takes in its text as before. The modules (app/antigoneApp, …) and their
graphics and listings are kept here:

| App | Package | Icon | Feature graphic | Screenshots | Listing |
|---|---|---|---|---|---|
| Antigone | no.anagnosis.antigone | antigone-icon-512.png | antigone-feature-graphic.png | screenshots/antigone/phone | listings/antigone.md |
| Ajax | no.anagnosis.ajax | ajax-icon-512.png | ajax-feature-graphic.png | screenshots/ajax/phone | listings/ajax.md |
| Electra | no.anagnosis.electra | electra-icon-512.png | electra-feature-graphic.png | screenshots/electra/phone | listings/electra.md |
| Odyssey | no.anagnosis.odyssey | odyssey-icon-512.png | odyssey-feature-graphic.png | screenshots/odyssey/phone | listings/odyssey.md |
| Symposium | no.anagnosis.symposium | symposium-icon-512.png | symposium-feature-graphic.png | screenshots/symposium/phone | listings/symposium.md |
| New Testament | no.anagnosis.newtestament | newtestament-icon-512.png | newtestament-feature-graphic.png | screenshots/newtestament/phone | listings/newtestament.md |

* Release one only once the reader is live: a text app opened without the reader sends the user
  to the reader's page on Google Play, and review counts a link to a page that is not public yet
  as broken (Antigone was rejected for this, 2026-10-13). In the review notes, say that the app
  adds its text to the free reader and give the reader's Play link.
* Before any release of it rolls out in open testing or production, open **Protected with
  Play › Play Store Protection › Manage Play App Signing**, click **Change the app signing key**,
  choose **Use the same key as another app in this developer account** and pick Anagnosis. Check
  that the SHA-256 of the app signing key is the reader's. The reader accepts a text only from an
  app signed with its own key, and the key cannot be changed once a release has rolled out.
* Say in its listing that the text can also be bought inside the free reader, at the same price,
  so that nobody buys it twice.

## Making the graphics again

* Icons: white GFS Didot capitals on the app's launcher colour (app/<module>/src/main/res/values/colors.xml),
  font size 335 px at 512 px, smaller if the letters would be wider than 420 px, centred.
* Feature graphics: `python3 play/make-feature-graphics.py` from the repository root (Noto Serif Medium).
* Screenshots: phone at 1080x1920 (`adb shell wm size 1080x1920`; Play rejects screens longer than
  twice their width), tablets at 2560x1600 and 1600x2560, with the status bar in demo mode.
