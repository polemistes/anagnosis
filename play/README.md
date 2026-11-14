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
| Gorgias | plato_gorgias_burnet |
| Agamemnon | aeschylus_agamemnon_sidgwick |
| Choephoroi | aeschylus_choephoroi_sidgwick |
| Eumenides | aeschylus_eumenides_sidgwick |
| Clouds | aristophanes_clouds_starkie |
| Theogony | hesiod_theogony_rzach |
| A True Story | lucian_truestory_nilen |
| The Shepherd | hermas_shepherd_lake |
| New Testament | newtestament_sbl |

On sale (2026-11-14): Antigone, Ajax, Electra, Odyssey, Symposium, Gorgias and the New Testament.
The other ids are reserved for texts that are built but not yet made available; a product is
created in the Console only when the author puts its text on sale.

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

## Reading aloud and screen readers (reader 0.4.0)

Reader 0.4.0 (version code 12) reads the Greek aloud in a reconstructed pronunciation (Homeric,
Attic or Koine), with the spoken word marked, and works with TalkBack and braille displays (see
app/PLAN-speech.md). The listing (listings/reader.md) says so, and has the release notes. Upload
the bundle to internal testing first and try it on a phone: the voice and TalkBack have only
been tested on the emulator, without sound. New screenshots of the play bar and of the word
sheet with its phonetic line would show the feature; the old ones are still correct.

## Gorgias and bookmarks (reader 0.5.0)

Reader 0.5.0 (version code 13) puts Plato's Gorgias on sale (product plato_gorgias_burnet, pack
gorgias) and adds bookmarks (app/PLAN-bookmarks.md), which the listing does not mention. The
listing's text list names the Gorgias with the Symposium, and the release notes for 0.5.0 are in
listings/reader.md. The product must be active before the update reaches people, or the shop
shows the Gorgias as not offered. The screenshots of the reading page lack the new bookmark icon
in the top bar; they are otherwise correct.

Version code 14 (still 0.5.0, 2026-10-22) adds to reading aloud: the speaker's name said before
each speech, Read aloud asking for the word to begin at, the pause fix, option changes heard at
once, and two new options, Sentence melody and Klatt voice (see app/PLAN-speech.md). The release
notes for 0.5.0 in listings/reader.md now name them too. The bundle was checked
on the tablet emulator, installed from the bundle with bundletool's local testing: a text opens
from its pack and is read aloud from a tapped word.

Version code 15 (still 0.5.0, 2026-10-22): the Klatt man two semitones higher, the speakers'
names in the man's voice raised above it rather than below, and a switch for saying the names
(on by default). The release notes say the names can be turned off.

## The forms sections of the dictionaries (reader 0.7.0)

Reader 0.7.0 (version code 17) shows the forms section that opens a long LSJ entry as lines, one
for each tense or case, with the tense and voice labels in colour; a long section is folded
after ten lines ("Show all forms"). The file's section letter "A.", which stood in the middle of
the forms in some 4,800 entries, is put where the meanings start, and shown only where the entry
goes on to a "B.". Middle Liddell's notes on forms and derivation stand one to a line. The
release notes for 0.7.0 are in listings/reader.md. The screenshots show no long dictionary entry
and are still correct.

Which texts are on sale is the author's decision alone: a text that is built and has its pack is
not thereby for sale. `google_play: yes` goes into a text's about.md only when the author says
that this text is to be made available (2026-11-14: the mark was taken off the Oresteia, the
Clouds, the Theogony, A True Story and the Shepherd of Hermas, which had been marked when they
were built; their product ids stay in their about.md, ready for that day).
