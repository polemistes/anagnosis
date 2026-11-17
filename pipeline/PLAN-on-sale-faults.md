# Faults in the texts on sale: what was mended, what is open

The author's rule of 2026-11-17: **mistakes in texts that are for sale are more serious and are
fixed first, not deferred.** On sale: Antigone, Ajax, Electra, the New Testament, the Symposium,
the Gorgias, the Odyssey. This file keeps the list for the Gorgias, the Symposium, the Odyssey
and the New Testament (the three plays of Sophocles are mended by their own run; see
`PLAN-sophocles.md`). Every fix is made at its source, so that the text's merge gives the
shipped file: the merges of the Gorgias, the Symposium and the Odyssey, run into a scratch
folder, now give their present files exactly (before 2026-11-17 each would have changed
something).

## Mended 2026-11-17

**The Gorgias** (version `a40493c7382b5acc`)
* Lodge's commentary, six places Perseus's keyers could not read ("<*>") and one mis-keyed name,
  read on the scan `gorgiasss00platuoft` (its OCR text; the page itself for 512 a) and put in
  `gorgias.LODGE_FIXES`: 483 d **αὐτό**; 512 a **ἢ οἳ ἀνέβησαν** (so Lodge's note prints, though
  his text has ἐνέβησαν) and the Apology quoted, ἐνταῦθα; 517 a **ἀλλὰ μέντοι**; 517 e ποριστικὸν;
  518 b ποικιλίαν ὄψου; 523 a Ῥέα (was "*ʽπέα").
* Burnet's apparatus: his asterisks for erased letters are written `\*`, so that two in a note
  no longer turn into italics (476b7 τοι****, 491e3 οὐ τοῦτο **, 519b3–4 ****; as in Lysias).
* 56 joined words (οὐδέ, μηδέ, εἴτε, ἐάντε) that hung on themselves or on a word under them
  carry their topmost part's relation and head (`PLAN-syntax-text.md`, Decisions).

**The Symposium** (version `b0f1889471aa9622`)
* Bury's commentary, three unread places, read on the scan `cu31924073426151` (its OCR text) and
  put in `symposium.BURY_FIXES`: on 188 b ἐρωτικῶν (the page's type is broken there; the same
  word follows in the sentence); on 191 e γαμούμεναί; on 202 a φρονήσεως.
* The introduction (`BURY_INTRODUCTION_FIXES`): § vi οἷον χρὴ εἶναι (was "οἶον χρὴ ε<*>ναι");
  Bekker's siglum of the Bodleianus, a black-letter 𝔄 (seen on the page; was "<*>").
* Burnet's apparatus: asterisks written `\*` (175c4 ***δὲ, 185d6 π**ν, 213d2 οὑτοσὶ ***).
* 49 joined words (οὔτε, μήτε, οὐδέ, μηδέ, εἴτε, ἐάντε) mended as above. These are what a merge
  run again "would have changed" (reported as 66 words): the merge was right about the τε of
  οὔτε and wrong about οὐδέ; both are right now and the merge gives the shipped tokens.
* Kept from the shipped file against the merge: "*Dio*tima" (one word; the merge had come to
  put a space in it; now a fix entry).

**The Odyssey** (version `27ef263073555801`)
* Merry–Riddell–Monro: the digamma. Perseus keys it as Betacode "v" and the import had left a
  Latin v in 176 places of 99 notes (κλέvος for κλέϝος, "does not invariably take the *v").
  `odyssey.digamma`: a v that touches a Greek letter is ϝ, "*v" the capital Ϝ, the digamma named
  by itself by a table of its places ("the v. l." is not touched). Monro's three forms with the
  rough breathing before the digamma at 17.387 (ʽϝὲ αὐτόν, ʽϝʼ αὐτόν, ʽϝεαυτόν) were read on the
  scan `homersodyssey00homeiala` (OCR text). The shipped file was mended by the same function
  (the commentary import itself does not give the shipped file again and was not run).
* Kept against the merge, now made by it: the header line `# pronunciation: homeric`
  (`GREEK_META`) and the two breves in the apparatus (at 3.284 and 6.242: a fix in `odyssey_merge`).
* 11 joined words mended (οὐδέ, τοῦδʼ, ἐϋφρονέων, εὐρυκρείων, πασιμέλουσα).

**The New Testament** (unchanged)
* John 8:5 Μωσῆς: right as it stands. The SBLGNT's own files (text, XML, apparatus) read Μωσῆς
  there, in the passage of the adulteress, and Μωϋσ- everywhere else (78 lines); MACULA spells
  the word Μωϋσῆς like the rest. Our lemma is Μωϋσῆς.

## Open (found, not settled)

* **The Odyssey: fourteen sentences whose trees hold a cycle in the treebank's own data** (an
  omitted-word node that hangs on a word which hangs on it): 2.9, 2.58, 3.102, 3.210, 3.265,
  4.632, 5.265, 5.347, 9.313, 17.283, 17.386, 20.220, 22.302, 24.376. Each needs its sentence
  read. Listed with their nodes by `pipeline/build/agent-scratch/record/treecheck.py`.
* **Words no dictionary has under their lemma** (`check`, "lexicon coverage"): nearly all are
  proper names (the Gorgias 10: Ἀγλαοφῶν, Κλεοπάτρα, Νικήρατος …; the Symposium 2: Ἦλις,
  Διοκλῆς; the Odyssey 58 names). A few are slips of the lemma, not names: the Odyssey πατηρ
  (1 word), ὄψε (1), τειρεσίης (1, lower case), κατερυκάνω, ἰασίων; the Gorgias νύν, πρῴην, οἷον
  (found only loosely). And the Odyssey has 56 lemmas (109 words) without a short definition.
  These want their own pass (lemma fixes; glosses only from printed dictionaries).
* **The shared Betacode converter** still leaves a Latin v for the digamma in every other
  Perseus import (Jebb's commentaries among them); it was not changed, because the plays' fix
  tables match the text as imported and an entry with such a v in it would stop matching.
  `odyssey.digamma` can be applied to those commentaries after their fix tables.
