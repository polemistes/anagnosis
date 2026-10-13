# In-app purchases: implementation plan

The reader stays free, and every text is bought inside it as a one-time in-app product through
Google Play. The text then arrives as an on-demand asset pack that Google Play hosts and
delivers. The text apps stay possible: the reader keeps taking in texts from installed text
apps as now, so a text app can still be released later for a text that needs a store listing of
its own. Decided with the author on 2026-10-13. This file is the brief: follow it step by step,
tick the steps off under Progress, and commit after each step (the plan file with it). All
steps are routine and are done on Opus 5.5. If a step turns out to need a judgement the brief
does not settle, say so rather than guess.

The shop goes into reader 0.3.0 (version code 5), which has not been uploaded yet.

Decisions already taken (do not reopen them):

* One product per text, a one-time ("non-consumable") product with the id `text_<slug>`
  (`text_antigone`, `text_newtestament`). The author sets the price (€3) in Play Console.
* The shop shows Play's price in the buyer's own currency on the Buy button.
* A text is owned when Play says the account bought it, or when its text app is installed
  (signed with the reader's key, as now). The shop marks such a text Owned and offers no Buy.
* No server. The reader asks Play (through the Play Store app) for purchases and downloads; its
  own code never connects. But the Billing Library (every version from 7.1.1 to 9.1.0) depends
  on Google's data transport (`transport-backend-cct`), which adds `INTERNET` and sends the
  library's diagnostic logs to Google; Asset Delivery brings WorkManager (`WAKE_LOCK`,
  `ACCESS_NETWORK_STATE`, `RECEIVE_BOOT_COMPLETED`, `FOREGROUND_SERVICE_DATA_SYNC`). Found
  2026-10-13 in the merged manifest; the author decides whether `INTERNET` is removed in the
  reader's manifest (`tools:node="remove"`) or kept and named in the privacy policy.
* The platform's store sits behind a small interface in common code, so that StoreKit can take
  its place on iOS later without touching the shop's screens.

## How it fits together

### Products and packs

* Every text on sale has an asset pack module `app/packs/<slug>` (plugin
  `com.android.asset-pack`, pack name `<slug>`, delivery `on-demand`) whose
  `src/main/assets/data/` holds `<slug>.sqlite` and `<slug>.sqlite.version`, copied from
  `../data` by a Sync task as the text apps do now. The reader's `android { assetPacks += ... }`
  lists them. The packs go up with the reader's bundle; the reader's own download does not
  grow, since on-demand packs are fetched only when asked for.
* Limits (Play Console Help, 2026-10-13): 1.5 GB per pack, 4 GB for all on-demand packs. The
  largest text, the New Testament, is 22 MB.
* `google_play: yes` in `texts/<slug>/about.md` now means "on sale in the reader": the text has
  a pack and the shop lists it. A listed text whose product Play does not return (not created
  or not active in Play Console) is left out of the shop while Play can be reached, so the shop
  never offers what cannot be bought. `app_id` stays for the text apps.
* `catalog.json` gets each text's `version` (the content of `<slug>.sqlite.version`, read
  after the build, so a build of one text still writes every version). The reader compares a
  downloaded text with it to know that a newer one has come with an update.

### Where texts live on the device (`DriverFactory.android.kt`)

* Texts from packs and texts from text apps both go into `filesDir/texts/` as now. Each
  remembers its origin in the reader's preferences: `app_text_pkg_<slug>` (exists) for a text
  app, `pack_text_<slug>` = version for a pack.
* `installedTexts(owned: Set<String>)`: bundled texts, texts from text apps, and texts from
  packs whose slug is in `owned`. A pack text that is no longer owned (a refund, or another
  Google account) is hidden, not deleted: it comes back without a download if the purchase
  does. The reader's notes are never touched.
* When a text app is uninstalled, its text is deleted only if it did not also come from a pack.
* `installPackText(slug, dir)`: copies `<slug>.sqlite` from the pack's assets folder into
  `texts/` (through a `.part` file, as now), records `pack_text_<slug>`, and the caller then
  removes the pack so the text is not stored twice. `packTextVersion(slug)` reads the record.
* The pure decision (which slugs are installed, given files, origins and the owned set) is a
  function in common code with unit tests.

### The store interface (common code, `data/TextShop.kt`)

```kotlin
interface TextShop {
    val state: StateFlow<ShopState>
    fun refresh()              // reconnect, ask for products and purchases again
    fun buy(slug: String)      // opens the store's payment sheet
    fun download(slug: String) // fetch again after a failure, or confirm on mobile data
}
class ShopState(
    val reachable: Boolean,               // the store answered
    val prices: Map<String, String>,      // slug → formatted local price
    val owned: Set<String>,               // bought in the app
    val pending: Set<String>,             // payment not yet completed
    val downloads: Map<String, Download>, // slug → progress / waiting for Wi-Fi / failed
    val revision: Int,                    // bumped when a text arrives or ownership changes
)
```

`App` takes a `TextShop`; the catalog is read again whenever `revision` changes, as it is now
when the app comes to the front.

### Google Play (`androidApp`, `PlayTextShop.kt`)

* Billing Library 9.1.0 (`com.android.billingclient:billing`), Asset Delivery 2.3.0
  (`com.google.android.play:asset-delivery`). One `BillingClient` with
  `enablePendingPurchases(PendingPurchasesParams.newBuilder().enableOneTimeProducts().build())`
  and `enableAutoServiceReconnection()`, started in `MainActivity`.
* On connect and on every `refresh()` (the app coming to the front):
  `queryProductDetailsAsync` for the `text_<slug>` of every text marked on sale (prices from
  `oneTimePurchaseOfferDetails.formattedPrice`), and `queryPurchasesAsync(INAPP)`.
* A purchase in state PURCHASED: owned; acknowledged (`acknowledgePurchase`) if it is not yet.
  PENDING: shown as "Payment pending", not owned. The owned set is saved in the preferences
  after every successful query; when Play cannot be reached, the saved set stands, so the
  texts stay readable offline and without Play.
* Every owned text that is missing from `texts/`, or whose `pack_text_<slug>` differs from the
  catalog's `version`, is fetched (`AssetPackManager.fetch`), so a new phone or a reinstall
  gets the texts back and an update of the reader brings updated texts. A listener follows the
  progress; on COMPLETED the text is copied in (`installPackText`), the pack removed
  (`removePack`) and `revision` bumped. WAITING_FOR_WIFI and REQUIRES_USER_CONFIRMATION show a
  Download button that calls `showConfirmationDialog`; FAILED shows Try again.
* `buy(slug)`: `launchBillingFlow` with the product's details; the result comes through the
  purchases listener and is handled as above, so the download starts by itself.
* Billing and delivery are separate parts of `PlayTextShop`. Debug builds
  (`androidApp/src/debug`) can swap the billing part for a fake that "buys" at once and keeps
  its purchases in the preferences, for the emulator, which has no Play Store; the delivery
  part stays real and works there through bundletool's local testing. The fake never goes into
  a release build.

### The shop (`AvailableTextsScreen.kt`)

The page keeps its cards by author with what each text comes with. Under the heading: "Each
text is bought once, here in Anagnosis, through Google Play. It is then downloaded and appears
on the front page, and it comes back on a new phone with the same Google account." The button
row of a card, by state:

* not owned: `Buy · 35 kr` (the formatted price);
* payment pending: "Payment pending";
* owned, downloading: a progress bar with "Downloading";
* owned, waiting for Wi-Fi or confirmation: "Download";
* owned, failed: "Download failed" and "Try again";
* owned and installed: "Owned" and "Open".

When Play cannot be reached the cards show no buttons and a line under the heading says that
buying needs Google Play and a connection. The front page's button reads "Available texts"
whenever a text is marked on sale; the "No text is installed yet" lines in the search say the
texts are bought under Available texts on the front page.

## Steps

1. **Packs and catalog.** `version` in catalog.json (pipeline), the asset-pack plugin in the
   version catalog, `app/packs/<slug>` for the six texts that are built (antigone, ajax,
   electra, odyssey, symposium, newtestament), the reader's `assetPacks`. Check that
   `bundleRelease` holds the six packs and that the reader's base is no larger.
2. **Ownership in the reader.** `TextShop`/`ShopState` in common code, the installed-texts rule
   with unit tests, `DriverFactory` changes (origins, `installPackText`, the uninstall fix),
   `App` reading the catalog again on `revision`.
3. **Google Play.** `PlayTextShop`: billing (products, purchases, acknowledge, pending, saved
   owned set) and asset delivery (fetch, listener, copy in, remove pack, updates). The fake
   billing in debug.
4. **The shop page.** `AvailableTextsScreen` by the states above; front page button; the
   texts in the search, Options/About and the text cards that speak of texts as apps.
5. **Test on the emulator.** Debug build with the fake billing and the packs installed by
   bundletool's local testing (`build-apks --local-testing`, `install-apks`): buy, download,
   read, refund (owned set emptied), reinstall (texts come back), update (changed version
   fetched again). Release build: R8 keeps billing and asset delivery working (both libraries
   ship their own keep rules; check the release build starts and the shop says Play cannot be
   reached rather than crashing).
6. **Documents.** PRIVACY.md (purchases and downloads through the Google Play app; the reader
   learns which texts the account has bought, keeps that on the device, and asks for the
   Billing permission), play/README.md (the reader's release with products, licence testers
   and internal testing; text apps as an option for later), play/listings/reader.md (facts
   only: the texts are bought in the app; the author will rewrite the listing), README.md,
   texts/README.md (`google_play`), the six texts marked `google_play: yes`, the reader's
   "Available texts" screenshot retaken. Rebuild the release AAB.
7. **Purchase signature (after the author has created the app in Play Console).** Play
   Console › Monetize › Monetization setup › Licensing gives the app's public key (not a
   secret). The reader checks each purchase's signature (`originalJson`, `signature`) with it
   and ignores purchases that fail. Until the key is in the build, purchases are taken as Play
   reports them.

## Left to the author in Play Console

Payments profile; upload the 0.3.0 bundle to internal testing (products can only be created
once a bundle with the Billing permission is uploaded); create the six products `text_<slug>`
at €3 and activate them; add yourself as a licence tester and buy each text on your own phone
(licence testers are not charged); Data safety form looked at again; then production.

## Progress

- [x] 1. Packs and catalog (2026-10-13: the bundle holds six on-demand packs; the base is unchanged)
- [x] 2. Ownership in the reader (2026-10-13)
- [x] 3. Google Play (2026-10-13; builds, tested in step 5)
- [x] 4. The shop page (2026-10-13)
- [x] 5. Test on the emulator (2026-10-13: buy, download, read, refund hides, rebuy without download, lost and outdated texts fetched again, text app beside the shop both ways; release build starts and says Play cannot be reached. Fixed: fake billing chosen on the emulator by hardware, since its image has a stub Play Store; a text app just uninstalled no longer stops the fetch; R8 keep rule for WorkManager's database. A real purchase can only be tested from Play's internal testing track.)
- [ ] 6. Documents
- [ ] 7. Purchase signature
