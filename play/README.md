# Google Play

Everything needed for the store listings of the reader and the text apps.

| App | Package | Bundle (after `./gradlew :<module>:bundleRelease` in app/) | Icon | Feature graphic | Screenshots | Listing |
|---|---|---|---|---|---|---|
| Anagnosis (free) | no.anagnosis.reader | app/androidApp/build/outputs/bundle/release/androidApp-release.aab | icon-512.png | feature-graphic.png | screenshots/reader/{phone,tablet-7,tablet-10} | listings/reader.md |
| Antigone | no.anagnosis.antigone | app/antigoneApp/…/antigoneApp-release.aab | antigone-icon-512.png | antigone-feature-graphic.png | screenshots/antigone/phone | listings/antigone.md |
| Ajax | no.anagnosis.ajax | app/ajaxApp/…/ajaxApp-release.aab | ajax-icon-512.png | ajax-feature-graphic.png | screenshots/ajax/phone | listings/ajax.md |
| Electra | no.anagnosis.electra | app/electraApp/…/electraApp-release.aab | electra-icon-512.png | electra-feature-graphic.png | screenshots/electra/phone | listings/electra.md |
| Odyssey | no.anagnosis.odyssey | app/odysseyApp/…/odysseyApp-release.aab | odyssey-icon-512.png | odyssey-feature-graphic.png | screenshots/odyssey/phone | listings/odyssey.md |
| Symposium | no.anagnosis.symposium | app/symposiumApp/…/symposiumApp-release.aab | symposium-icon-512.png | symposium-feature-graphic.png | screenshots/symposium/phone | listings/symposium.md |
| New Testament | no.anagnosis.newtestament | app/newTestamentApp/…/newTestamentApp-release.aab | newtestament-icon-512.png | newtestament-feature-graphic.png | screenshots/newtestament/phone | listings/newtestament.md |

The text apps are priced at €3; the reader is free.

## In Play Console

1. Payments profile (needed before any app can be priced).
2. Create the reader first. Let Google manage its app signing key (Play App Signing) and upload
   the reader's bundle.
3. Create each text app. Before any release of it rolls out in open testing or production, open
   **Protected with Play › Play Store Protection › Manage Play App Signing**, click **Change the
   app signing key**, choose **Use the same key as another app in this developer account** and pick
   Anagnosis. Check that the SHA-256 of the app signing key is the reader's. The reader accepts a
   text only from an app signed with its own key, and the key cannot be changed once a release has
   rolled out in open testing or production. ("Upgrade key" is not the same: it applies only to
   Android 17 and later.)
4. For every app: privacy policy URL
   (https://github.com/polemistes/anagnosis/blob/main/PRIVACY.md), data safety ("no data
   collected or shared"), content rating questionnaire, target audience (not aimed at children),
   ads: none, category (Education, or Books & Reference).
5. Store listing: title, short and full description from listings/, the icon, the feature
   graphic and the screenshots.
6. Price the text apps at €3 (Play converts to local prices) and choose the countries.

Release the reader before (or together with) the text apps: a text app opened without the reader
installed sends the user to the reader's page on Google Play.

## Making the graphics again

* Icons: white GFS Didot capitals on the app's launcher colour (app/<module>/src/main/res/values/colors.xml),
  font size 335 px at 512 px, smaller if the letters would be wider than 420 px, centred.
* Feature graphics: `python3 play/make-feature-graphics.py` from the repository root (Noto Serif Medium).
* Screenshots: phone at 1080x1920 (`adb shell wm size 1080x1920`; Play rejects screens longer than
  twice their width), tablets at 2560x1600 and 1600x2560, with the status bar in demo mode.
