# Euripides: all nineteen plays as candidates

Assessed 2026-11-15. The question: which of Euripides' plays can be made into texts for the
app, and in which order from the easiest to the hardest.

**The author's decision, given while this was being written (2026-11-15):** every play is made
from **Gilbert Murray's Oxford text** (Euripidis Fabulae, Oxford Classical Texts, 3 vols,
1902-1913), text and critical apparatus both from that edition, and offered only from
1 January 2028, when Murray (died 1957) is in the public domain in Norway and the UK. So the
text + apparatus question is settled for every play. What remains open per play is the
English commentary and introduction to put beside Murray's text (another editor's, as Paley's
notes stand beside Rzach's text in the Theogony) and the translation. The ranking below is made
on that basis. The older route (one public-domain edition for text + apparatus) is kept in a
column, since the facts were gathered.

"Seen" means I looked at the page image. "OCR" means I only read Tesseract's output of the page
(head and foot), not the image. "Unverified" means what it says.

## Findings in short

* **Murray**: all three volumes are on archive.org with jp2 zips; Perseus digitised vol. I from
  a Toronto printing before 1915, vol. II from a **1962** printing of the 3rd edition (1913),
  vol. III from a **1925-1946** printing of the 2nd edition (1913). The page is large, clear
  type, about 25-30 verses and 5-10 lines of Latin apparatus per page; the Greek hypotheses are
  printed before each play with their own apparatus. See the section on Murray.
* **A good English commentary in a clean scan exists for fourteen plays**; Paley (1857-1880)
  covers all nineteen and is the only one for the Supplices and the Rhesus.
* **W. H. Porter (Rhesus, 1916/1929) died 1961**: protected in Norway until the end of 2031.
  His Rhesus is out, notes and all.
* **GLAUx has all nineteen plays** (github.com/alekkeersmaekers/glaux, `xml/0006-001.xml` …
  `0006-019.xml`, numbered as the TLG works; listing checked 2026-11-15).
* **A hand-made treebank exists for the Medea**: Pedalion trees
  (github.com/perseids-publications/pedalion-trees, `public/xml/euripides_medea.xml`, 9,845
  words, 824 sentences, the whole play; annotated by Toon Van Hal and KU Leuven students on a
  GLAUx pre-parse, "controlled" by Van Hal, Gijbels and Joosten; document_id 0006-003, so
  probably on the GLAUx/Murray text). Licence: the repository's TREEBANK_LICENSE file is
  CC BY-SA 4.0 (the code is MIT). Usable in a sold app. No other play has a hand-made treebank:
  AGDT (PerseusDL/treebank_data), Gorman and Harrington trees have no Euripides; PROIEL has none.
* **Translations**: Perseus (canonical-greekLit, tlg0006) has E. P. Coleridge (George Bell,
  vol. I 1906 printing / vol. II 1891) for eighteen plays, keyed by `card` milestones with line
  numbers as the Medea and Alcestis files the pipeline already reads; the Bacchae's
  `perseus-eng2` is Buckley 1850 (Coleridge's Bacchantes is on Wikisource, as PLAN-drama.md
  says); `tlg019.perseus-eng4` is Murray's Rhesus (not usable). Coleridge (1863-1936)
  translated "from the text of Paley" (title of ahx1899.0001.002.umich.edu), so his English
  follows Paley's Greek, not Murray's, where they differ.

## Ranking, easiest to hardest (Murray's text and apparatus for all)

Verses = the standard last line number (Murray numbers the standard way). "Notes at back" and
"notes under text" are the two layouts of the commentary; both are handled: notes at the back as
Hayley/Tucker (prose route), notes in two columns under the text as Paley's Hesiod (Theogony)
and Earle's Medea. Every commentary below is keyed to the standard verse numbers (seen on its
notes pages), so its notes go under Murray's line numbers directly; small differences in the
lyric division are settled as for Rzach/Paley.

| # | play | verses | commentary + introduction (recommended) | layout of notes | scan | translation | older route (one edition for text + apparatus) | why this rank |
|---|---|---|---|---|---|---|---|---|
| 1 | Alcestis | 1163 | H. W. Hayley, Ginn 1898 (d. 1899) | at back, bold line number + lemma; ~90 pp. intro | alcestisofeuripi00euriuoft, 284, jp2, clean | Coleridge, Perseus eng2 | Hayley (apparatus at foot) | short, mostly dialogue, select play, commentary already planned |
| 2 | Medea | 1419 | M. L. Earle, American Book Co. 1904 (d. 1905) | under text, two columns, run-on notes | cu31924079583609, 316, jp2 | Coleridge, Perseus eng2 | Earle (critical notes in an appendix) | work begun (PLAN-drama.md); the only hand-made treebank |
| 3 | Heraclidae | 1055 | A. C. Pearson, Cambridge 1907 (d. 1935) | at back ("Explanatory notes") | heraclidae00euri, 230, jp2, clean | Coleridge, Perseus eng2 | Pearson (apparatus at foot) | short, little lyric; fine modern commentary; lacuna/lost scenes add apparatus |
| 4 | Helen | 1692 | A. C. Pearson, Cambridge 1903 | at back | helena__00euriuoft, 292, jp2, clean | Coleridge, Perseus eng2 | Pearson (apparatus at foot) | long and lyric, but the best scan and commentary of the set |
| 5 | Bacchae | 1392 | J. E. Sandys, Cambridge, 3rd ed. 1892 (d. 1922) | at back (running heads "BACCHAE [line]") after text with critical notes at the foot | BacchaeOfEuripides_680, jp2 | Coleridge, Wikisource (speeches) / Buckley, Perseus | Sandys | very long introduction; lacuna after 1329; translation by speeches |
| 6 | Hecuba | 1295 | W. S. Hadley, Cambridge 1894 (d. 1927) | at back | hekabhecubaofeur00euriuoft, 164, jp2 | Coleridge, Perseus eng2 | Prinz-Wecklein I (Hadley follows Prinz's text) | modest size, clean short book; triad play: apparatus with many sigla |
| 7 | Troades | 1332 | R. Y. Tyrrell, Macmillan 1897 (d. 1914) | at back | troadeswithrevte00euriuoft, 164, jp2 | Coleridge, Perseus eng2 | Prinz-Wecklein III | short book; much lyric |
| 8 | Cyclops | 709 | Paley vol. III (2nd ed. 1880); W. E. Long, Clarendon 1891 if his death year is found | Paley: under text, two columns; Long: at back | ldpd_8039020_002 (Paley), 690, jp2, clean; cyclops00euriuoft (Long), 112, jp2 | Coleridge, Perseus eng2 | Prinz-Wecklein I | shortest play; satyr vocabulary (glossary work); no safe single-play commentary |
| 9 | Heracles | 1428 | A. Gray (d. 1940) and J. T. Hutchinson (d. 1924), Cambridge 1897 | at back | heraklesmainomen00euriuoft, 146, jp2 | Coleridge, Perseus eng2 | Wilamowitz 1895 (German) or Prinz-Wecklein II | alphabetic play (L P), corrupt; short commentary |
| 10 | Iphigenia in Tauris | 1499 | E. B. England, Macmillan 1899 (2nd ed.; 1st 1883; d. 1936) | under text, two columns | iphigeneiaheenta00euriuoft, 194, jp2, clean | Coleridge, Perseus eng2 | Prinz-Wecklein II (or Jerram 1885, short critical notes at foot) | long, alphabetic; good commentary with critical discussion |
| 11 | Orestes | 1693 | N. Wedd, Cambridge 1895 (d. 1940) | at back | orestesofeuripid00euriuoft, 276, jp2 | Coleridge, Perseus eng2 | Prinz-Wecklein III | long; triad play: heavy apparatus and interpolations |
| 12 | Phoenissae | 1766 | A. C. Pearson, Cambridge 1909 | at back | phoenissaeedited00euriuoft, 324, jp2 | Coleridge, Perseus eng2 | Pearson? (no apparatus seen on two text pages: unverified) | longest play; triad; disputed ending |
| 13 | Iphigenia in Aulis | 1629 | E. B. England, Macmillan 1891 | under text, two columns | iphigeniaataulis00euri, 210, jp2 (500 ppi) | Coleridge, Perseus eng2 | Prinz-Wecklein II | interpolated prologue and ending; many bracketed lines |
| 14 | Ion | 1622 | A. W. Verrall, Cambridge 1890 (d. 1912), or Paley vol. II | Verrall: Greek left, his verse translation right, notes at the foot of both pages | ionofeuripides00euririch, 210, jp2 | Coleridge, Perseus eng2 | Prinz-Wecklein I | long; Verrall's layout is Starkie-like (facing translation) and his notes idiosyncratic |
| 15 | Hippolytus | 1466 | J. P. Mahaffy (d. 1919) and J. B. Bury (d. 1927), Macmillan 1889; or Paley vol. I (1857) | Mahaffy-Bury: at back; Paley: under text | hippolytuseurip00eurigoog (Google, 227, PDF only); Paley india.history.resource.14928 (jp2) | Coleridge, Perseus eng2 | Prinz-Wecklein III (or Wilamowitz 1891, German) | only a Google scan for the one-play commentary |
| 16 | Andromache | 1288 | G. Norwood, John Murray 1906 (d. 1954) | at back, with section headings | andromacheeurip00norwgoog / 01norwgoog (Google, PDF only) | Coleridge, Perseus eng2 | Prinz-Wecklein III | Norwood only as a Google scan; Hyslop (Macmillan 1900, clean jp2) has no death year |
| 17 | Electra | 1359 | Paley vol. II (2nd ed. 1874); C. H. Keene, Bell 1893, only on HathiTrust | Paley: under text | ldpd_8039020_001, 670, jp2, clean | Coleridge, Perseus eng2 | Prinz-Wecklein I | single manuscript (L), corrupt; Keene's pages not seen |
| 18 | Rhesus | 996 | Paley vol. I (1857) only | under text, two columns | india.history.resource.14928, jp2 | Coleridge, Perseus eng3 | Prinz-Wecklein III | short, but Paley only and an Indian library scan; authenticity disputed |
| 19 | Supplices | 1234 | Paley vol. I (1857) only | under text, two columns | india.history.resource.14928, jp2 (page seen, clean) | Coleridge, Perseus eng2 | Prinz-Wecklein II | L only, lacunae and corruptions; Paley only |

Plain reading of the table: plays 1-7 each have a clean one-volume English commentary with
notes at the back or a layout already built, and could be made like the Alcestis. Plays 8-14
have a good commentary but cost more (length, lyric, heavy apparatus, or notes under the text).
Plays 15-19 depend on Paley or on a Google/HathiTrust scan.

## Murray's Oxford text on archive.org

### Edition history

* **Vol. I** (Cyclops, Alcestis, Medea, Heraclidae, Hippolytus, Andromache, Hecuba): first
  published 1902; reprinted 1906, 1910, 1917, 1927, 1934, 1940, 1947, 1951(?), 1955, 1958, 1963,
  1966, 1974 (the verso of the title page in euripidisfabulae01euri_0, OCR). Reprints, no
  revised edition listed.
* **Vol. II** (Supplices, Hercules, Ion, Troades, Electra, Iphigenia in Tauris): first
  published 1904, second edition 1908, third edition 1913, reprinted 1921, 1925 (OCR read
  "1935" between 1921 and 1930), 1930, 1937, 1950 (verso in euripidisfabu02euri, OCR).
* **Vol. III** (Helena, Phoenissae, Orestes, Bacchae, Iphigenia Aulidensis, Rhesus): 1909;
  second edition 1913 (preface "Scribebam Oxonii Kal. Oct. MCMIX" and a note "Cum hunc libellum
  iterum anno MCMXIII edendum …", euripidisfabulae03euri_0, OCR).
* Printers named on the title-page versos: "Excudebat Horatius Hart, Typographus academicus"
  (Horace Hart was Printer to the University until 1915, from memory) and "Excudebat Ioannes
  Johnson, Architypographus academicus" (John Johnson, 1925-1946, from memory). This dates
  printings that carry no year.

### What Perseus digitised (sourceDesc of each canonical-greekLit tlg0006 perseus-grc2 file)

| play (tlg) | Perseus says | scan named |
|---|---|---|
| Cyclops 001 … Hecuba 007 | vol. 1, Clarendon 1902, Greek by Lace OCR | euripidisfabulae01euriuoft (page n25, n55, n103, n163, n207, n269, n321) |
| Supplices 008 … Iphigenia in Tauris 013 | vol. 2, 1913 | euripidisfabu02euri (n17, n67, n123, n189, n243, n297) |
| Helen 014 … Rhesus 019 | vol. 3, 1913 | euripidisfabulae03euri_0 (n13, n83, n155, n229, n287, n357) |

All perseus-grc2 files are CC BY-SA 4.0 (release 2021).

### The scans

| vol. | identifier | images | jp2 zip | printing (from the title page) | notes |
|---|---|---|---|---|---|
| I | **euripidisfabulae01euriuoft** (Toronto, Robarts) | 384 | yes, 400 ppi | Horace Hart, so 1902, 1906 or 1910; library call number "1902" | Perseus's source. Clean (four pages seen). **Recommended.** |
| I | euripidisfabulae01euri_0 (Boston College) | 374 | yes, 300 ppi | 1974 or later (the reprint list ends 1974) | after 1931: not for use |
| I | euripidisfabu01euri (PIMS Toronto) | 380 | yes | not pinned; the catalogue gives 1960s printings for vols II-III of this set | |
| II | **euripidisfabulae02euri_0** (Boston College) | 358 | yes, 300 ppi | Horace Hart, so printed by 1915; whether 1904, 1908 or 1913 edition not pinned | the only pre-1931 printing found; **check its edition before use** |
| II | euripidisfabu02euri (PIMS) | 362 | yes | 1962 printing of the 3rd ed. (1913) | Perseus's source |
| II | euripidisfabul02euri (PIMS) | 362 | yes | same set (1962) | |
| III | euripidisfabulae03euriuoft (Toronto, Robarts) | 422 | yes, 400 ppi | Horace Hart; accession stamp "5/10/11", so the 1st ed. 1909 | pencil underlining on some pages (Bacchae p. 249 seen), page numbers pencilled in the top corner |
| III | **euripidisfabulae03euri_0** (Boston College) | 410 | yes, 300 ppi | John Johnson, "Printed in Great Britain": a 1925-1946 printing of the 2nd ed. (1913) | Perseus's source |
| III | euripidisfabul03euri (PIMS) | 418 | yes | 1960 printing of the 2nd ed. (catalogue note) | |
| ? | euripidisfabula01eurigoog, …02eurigoog, …00eurigoog (Google, Michigan) | 573, 483, 530 | no | not pinned (OCR of a title page read "MCM…") | may hold early printings; not looked at |

Which printing to use: vol. I, the Toronto scan (pre-1915, and what Perseus used). Vol. II and
vol. III: the 1913 editions are what Perseus digitised, and their text was published in 1913,
so it is in the US public domain whatever the date of the printing scanned, provided the later
printing changed nothing (unverified; the reprints are called reprints). A pre-1931 printing of
the 1913 vol. II may be the Boston College scan (check its verso); for vol. III none was found
(the Toronto copy is the 1909 first edition, which differs from Perseus where Murray revised).
Trap: `euripidis-fabulae-i-ii-iii` on archive.org is **Diggle's** OCT (1981-1994), an
unauthorised upload: not usable for anything.

### The page (seen: vol. I Medea persons page, hypothesis pages, pp. on Medea 185-210; vol. III
Sigla, Helen 575-597, Bacchae 419-445)

* Large, clear Greek type; 25-30 verses a page; verse numbers every fifth line at the **right**;
  speakers abbreviated in the left margin (Με., Ελ., Χο.), a new character's full name centred
  above the first speech (ΘΕΡΑΠΩΝ, ΑΓΓΕΛΟΣ); metrical labels at the right in brackets
  (`[ἀντ.`); lyric verses indented by colon.
* **Apparatus**: Latin, at the foot of every page under the text, small type, 5-10 lines a page
  on the pages seen (Helen, an alphabetic play: 7 lines; Medea, a select play with five codices:
  9 lines). Sigla in roman and italic (A B V L P; italic *l p* for later hands), superscripts
  (L², B¹, A¹), Σ for the scholia, ⟨ ⟩ for additions in the text, [ ] for deletions, † for
  cruces: all will trouble OCR and need the agents' crops, as Sidgwick's did.
* **Before each play**: the Greek hypotheses (ΥΠΟΘΕΣΙΣ ΜΗΔΕΙΑΣ, ΑΡΙΣΤΟΦΑΝΟΥΣ ΓΡΑΜΜΑΤΙΚΟΥ
  ΥΠΟΘΕΣΙΣ), printed in full with their own Latin apparatus and line numbers every fifth line at
  the **left**; then ΤΑ ΤΟΥ ΔΡΑΜΑΤΟΣ ΠΡΟΣΩΠΑ (letter-spaced small capitals) with a Latin note on
  the order of the persons in the codices, and at the foot a note on the play: date and codices
  ("Acta anno A. C. 431. Codices A B V L P: etiam Π vv. 5-12 … Accedunt Σ.").
* **Each volume** opens with a Latin Praefatio (vol. I: on the codices and the scholia; vol. II
  on the "alphabetic" plays in L and P; vol. III on Helen and the chronology) and a **Sigla**
  page (vol. III seen: M A B V, L P, Π K H Ambr., Σ, the codices "raro citantur", the hands).
  Whether vol. I prints the ancient Lives was not checked.

## Each play

For each: Murray's volume, the commentary found, other editions, what I saw, what is open.
Death years: from archive.org/Library of Congress name headings unless another source is named.

### Alcestis (1163 verses; Murray vol. I)
Select play (A B V L P). Commentary: H. W. Hayley, *The Alcestis of Euripides, with an
introduction and critical and exegetical notes*, Boston, Ginn 1898; Hayley died 1899 (Library
of Congress heading 1867-1899; HathiTrust gives 1864-1899). Scan alcestisofeuripi00euriuoft
(284 images, jp2; also alcestisofeuripi0000unse_r4u3, alcestisofeuripi0000herm). Notes page
seen by OCR (p. 107, "Critical and exegetical notes": "846. ἐξαίροιμι …"), at the back, keyed
to verse numbers, critical and explanatory remarks mixed (the critical ones would go or stay:
decide at the play). Layout of the text pages as PLAN-drama.md describes (not re-seen). Spares:
Earle 1894 (earlealcestis00euri), Bayfield 1894 (alcestiseuripid00bayfgoog). GLAUx 0006-002.

### Medea (1419; vol. I)
Earle 1904 as in PLAN-drama.md (notes under the text, critical notes in an appendix that would
no longer be shipped). Other commentaries: Verrall 1881 (euripidoumedeiam00euriuoft 1888,
aps0945.0001.001.umich.edu), Heberden (Clarendon). C. E. S. Headlam's Medea (1897-1919, scans
medeaofeuripides00euri_0 and others): Headlam born 1864, death year still not found: avoid.
Treebank: Pedalion hand-made trees (above), CC BY-SA 4.0, besides GLAUx 0006-003. Papyrus
fragments and the D O codices are cited by Murray.

### Heraclidae (1055; vol. I)
One of the nine "alphabetic" plays without scholia, in L and P only (Murray's vol. I preface,
OCR: "novem fabulae scholiis carent — Hel. El. Herc. Hclid. …"). A lacuna is generally assumed (Macaria's death and other scenes lost; Pearson's
introduction treats it). Commentary: A. C. Pearson, *The Heraclidae of Euripides*, Cambridge
1907 (Pearson 1861-1935). Scan heraclidae00euri (230 images, jp2, Toronto). **Seen** p. 21:
clean; Pearson's own text with margin numbers every fifth verse at the right, speakers in the
left margin, Latin apparatus at the foot (LP, Stephanus, Tyrwhitt, Nauck, Elmsley); "Explanatory
notes" at the back (OCR p. 49: "43. σῴζει …", keyed to verse numbers). Others: Beck & Headlam,
Cambridge 1882/1895 (heracleidae188200euri, heracleidaeofeur00euriuoft; critical notes in an
appendix; Beck 1848-1916, Headlam's death unknown); Jerram, Clarendon 1888 (heracleidae00euri,
164, jp2; short critical notes at the foot of the text pages, OCR; Jerram 1838-1914).

### Helen (1692; vol. III)
L P only (an "alphabetic" play), much lyric. Commentary: A. C. Pearson, *The Helena of
Euripides*, Cambridge 1903. Scans helena__00euriuoft (292, jp2, Toronto), helenaofeuripide0000unse
(290, jp2), helenaeuripides00peargoog (Google). **Seen** p. 46 (verses 1132-1154): clean;
στρ./ἀντ. in the right margin, apparatus at the foot with LG sigla (G = Laurentianus 32.16, his
siglum for Murray's P's family) and "see Comm."; "Explanatory notes" at the back (OCR p. 81,
keyed "128.", "142."); long introduction. Others: Jerram, Clarendon 1882/1892
(euripideshelena00eurigoog, critical appendix), Herwerden 1895 (Latin). GLAUx 0006-014.

### Bacchae (1392; vol. III)
L P, P alone from 755 on; the lacuna after 1329. Commentary: J. E. Sandys, 3rd ed., Cambridge
1892 (d. 1922), scan BacchaeOfEuripides_680 (jp2 `BacchaeEurip_jp2.zip`, 600 ppi). OCR of pp. 16
and later: Latin critical notes at the foot of the text pages ("263. εὐσεβείας PC …"), the
commentary at the back with running heads "BACCHAE." and the verse range ([25-], [1067]). Only
the commentary and introduction would be used. Others: Tyrrell 1892/1910, Cruickshank 1893
(PLAN-drama.md). Translation: Coleridge's Bacchantes on Wikisource (by speeches) or Buckley on
Perseus (by line).

### Hecuba (1295; vol. I)
Select "triad" play, many codices: Murray's apparatus is fuller here. Commentary: W. S. Hadley,
Cambridge 1894 (1859-1927); his preface: the text "is in the main that of Prinz (Leipsic 1883)".
Scan hekabhecubaofeur00euriuoft (164, jp2, Toronto); also hecubaofeuripide00euriiala (jp2).
**Seen** notes p. 87: at the back, verse numbers in bold ("828.", "838. Δαιδάλου τέχναισιν"),
a "See crit. n." pointer shows a few critical notes. Text pages (OCR pp. 17, 32): no
apparatus at the foot. Others: Bond & Walpole, Macmillan 1882 (hecubaofeuripide00euririch,
600 ppi; text only on the pages read; John Bond's death not found), Russell, Clarendon 1889
(Russell born 1862, death not found), Heberden, Clarendon 1901 (1849-1921), Upcott, Bell 1901
(death not found), Sidgwick's Rugby edition.

### Troades (1332; vol. II)
Select play (V P Q and others). Commentary: R. Y. Tyrrell, *The Troades of Euripides, with
revision of text and notes*, Macmillan 1897 (1844-1914); scan troadeswithrevte00euriuoft (164,
jp2); later printing troadesofeuripid00euri (1907, 162, jp2). **Seen** notes p. 95: at the
back, keyed "825.", "829.", critical discussion inside the notes. Introduction short (not
measured). Older: Tyrrell 1882 (troadeseuripide00tyrrgoog).

### Cyclops (709; vol. I)
The satyr play; L P only. Commentaries: Paley vol. III (1860 / 2nd ed. 1880) and W. E. Long,
Clarendon 1891 (cyclops00euriuoft, 112, jp2; cyclops00longgoog). Long: born 1862, **death year
not found**; notes at the back keyed "l. 358" (seen p. 25 of the notes). Paley 2nd ed. **seen**
p. 565 (vv. 41-54): clean, text above, notes in two columns keyed "48.", "49.", "51.". Use
Long if his death year can be shown to be 1955 or earlier; otherwise Paley. Sidgwick's Rugby
edition (cyclopsrugbyedb00eurigoog) has notes for schools.

### Heracles (1428; vol. II)
L P only, corrupt in places. Commentary: A. Gray (1852-1940) and Sir J. T. Hutchinson (1850-1924,
Wikipedia), *Herakles Mainomenos*, Cambridge 1897; scan heraklesmainomen00euriuoft (146, jp2).
**Seen** notes p. 79: at the back, keyed "758.", "764.", "775-6.". Gray reissued it in 1921 (*The
Hercules furens*, Online Books). O. R. A. Byrde, Clarendon 1914 (euripidesheracle00euri, 148,
jp2): its apparatus at the foot is in Murray's words (OCR: "924 ἐξέβαλε inter textum et marginem
… fortasse recte"), so it is probably Murray's text reprinted with notes; Byrde's death year not
found: avoid. Wilamowitz, *Herakles*, 1889 / 2nd ed. 1895 (heraklescerklr00euri, 604, jp2): text
with apparatus at the foot (OCR), German translation and commentary: German only. Paley vol. III
as fallback.

### Iphigenia in Tauris (1499; vol. II)
L P. Commentary: E. B. England, *The Iphigeneia among the Tauri*, Macmillan 1883, 2nd ed. 1899
(England 1847-1936: Online Books Page, HathiTrust). Scan of 1899: iphigeneiaheenta00euriuoft
(194, jp2, Toronto). **Seen** p. 53: clean; text above, notes in two columns under it (lemma in
bold, translation in italics, "Cp. n. on l. 203."). No 1883 scan found. Others: Jerram,
Clarendon 1885 (iphigeniainta00euri, 204, jp2; short critical notes at the foot of text pages,
notes at the back, OCR); Flagg, Ginn 1889 (cu31924059113815, 216, jp2; notes under text; Flagg
1843-1931); Bates, American Book Co. 1904 (iphigeniaintaur05eurigoog, Google; notes under text;
W. N. Bates d. 1947, from memory); Paley vol. III.

### Orestes (1693; vol. III)
Triad play, many codices, heavy apparatus and much suspected interpolation. Commentary: N. Wedd,
Cambridge 1895 (1864-1940, Wikipedia/Wikidata); scan orestesofeuripid00euriuoft (276, jp2);
reissued 1907. **Seen** notes p. 67: at the back, keyed "19 f.", "21.", "24.". Text pages
(OCR): no apparatus at the foot. "Metrical appendix" in the volume.

### Phoenissae (1766; vol. III)
Triad play, the longest; the ending and other passages much suspected. Commentary: A. C.
Pearson, Cambridge 1909; scan phoenissaeedited00euriuoft (324, jp2). **Seen** notes p. 175:
"Explanatory notes" at the back, keyed "1314.", "1315 f.", references to "cr. n." (so the volume
has critical notes: where they stand was not found on the two text pages read by OCR). Also
J. U. Powell, Constable 1911 (euripidouphoini00euriuoft, 256, jp2; Powell born 1865; death year
1932 from memory, unverified); Paley's school edition 1879.

### Iphigenia in Aulis (1629; vol. III)
L P; the prologue's order and the end (from about 1578) are generally held to be later work;
Murray brackets much. Commentary: E. B. England, *The Iphigeneia at Aulis*, Macmillan 1891,
"with introduction and critical and explanatory notes"; scans iphigeniaataulis00euri (210, jp2,
500 ppi), euripidouiphigen00euri (210, jp2, 300 ppi), iphigeniaatauli00englgoog (Google).
**Seen** p. 55: text above, notes in two columns under it, long critical discussions in the
notes (keyed "516.", "517.", "520 and 521."). C. E. S. Headlam's IA (Cambridge 1889/1896): death
year unknown, avoid.

### Ion (1622; vol. II)
L P. Commentary: A. W. Verrall, *The Ion of Euripides, with a translation into English verse and
an introduction and notes*, Cambridge 1890 (1851-1912); scans ionofeuripides00euririch (210,
jp2), euripidouionionw00euriuoft (204, jp2). **Seen** p. 19: the Greek on the left page, his
verse translation on the right, notes at the foot of the pages under a rule, keyed "172.",
"175.", "183." with "B." for Bayfield. A Starkie-like spread; Verrall's readings are often his
own. Others: Jerram, Clarendon 1896 (ioneditedwithint00euriuoft, 212, jp2; critical appendix at
the back); Paley vol. II.

### Hippolytus (1466; vol. I)
Select play. Commentary: J. P. Mahaffy (1839-1919) and J. B. Bury (1861-1927), Macmillan 1881,
new ed. 1889 (title page of hippolytuseurip00eurigoog read by OCR: "edited, J. P. Mahaffy,
J. B. Bury, Macmillan and Co. 1889"); Google scan, 227 images, **no jp2**; notes at the back
(seen p. 63, keyed "161.", "167.", "170."). The 1881 printing is geripdoupplutos00eurigoog
(Google, no jp2). **Trap**: hippolytusofeuri0000unse (catalogued "Macmillan 1881", 100 images,
jp2) is an English verse translation, not Mahaffy-Bury (OCR pp. 21, 33). Hadley's Hippolytus
(1889): no scan. Paley vol. I is the fallback with a jp2 scan. Wilamowitz 1891
(hippolytos00euriuoft): German.

### Andromache (1288; vol. I)
Select play. Commentary: G. Norwood, John Murray 1906 (1880-1954, Wikipedia: free in Norway
since 2025); scans andromacheeurip00norwgoog (221) and andromacheeurip01norwgoog (226; catalogued
"Macmillan 1909", but its title page reads Norwood, John Murray): Google, **no jp2**. **Seen**
p. 182: notes at the back keyed "591.", "592.", with section headings ("545-765. Third
ΕΠΕΙΣΟΔΙΟΝ"). A. R. F. Hyslop, Macmillan 1900 (andromacheofeuri00euri, 176, jp2, clean; notes at
the back seen p. 97): death year **not found**. Paley vol. II as fallback (seen p. 269, 2nd ed.).

### Electra (1359; vol. II)
L only (P copied from L here, as Murray's preface to vol. II explains: unverified in detail);
corrupt. Commentary: C. H. Keene, *The Electra of Euripides, with notes and appendix*, Bell 1893:
**only on HathiTrust** (hvd.hxjvmv and osu.32435055629182, full view; not on archive.org); Keene
born 1847, professor of Greek at Cork, obituary in the Classical Review (year not seen): surely
dead before 1955, but the year is unverified; **pages not seen**. Paley vol. II (2nd ed. 1874,
ldpd_8039020_001, jp2; 1st ed. 1858 page seen: Electra p. 313, clean) is the safe choice.

### Rhesus (996; vol. III)
Select play (V L P and others); its authorship disputed since antiquity (Porter's and Paley's
introductions discuss it). Porter is out (died 1961). Commentary: Paley vol. I only (1857,
india.history.resource.14928, jp2 `14928_jp2.zip`, 300 ppi; Rhesus at the start of the volume,
OCR). Anthon's *English commentary on the Rhesus, Medea, …* (1877; Anthon d. 1867) exists
(englishcommentar00anthrich) but is a school crib built on Paley: not looked at.

### Supplices (1234; vol. II)
L (with P) only; lacunae (one at 263, which Paley marks with asterisks) and corruptions.
Commentary: Paley vol. I only; **seen** p. 389 (vv. 258-273): clean, two-column notes keyed
"260.", "263.", "265.". No English school edition exists (searched archive.org).

## Uniform alternatives

### Paley, *Euripides with an English commentary* (Bibliotheca Classica, Whittaker/Bell)

F. A. Paley, 1815-1888. Each page: Paley's Greek text above, his notes under it in two columns,
critical remarks inside the notes, keyed to verse numbers (pages seen: Supplices p. 389 and
Electra p. 313 of the 1st ed., Andromache p. 269 and Cyclops p. 565 of the 2nd). The same page
type as his Hesiod, which the Theogony already uses. Introductions to each play.

| vol. | plays (in order) | scans |
|---|---|---|
| I | Rhesus, Medea, Hippolytus, Alcestis, Heraclidae, Supplices, Troades | 1st ed. 1857: india.history.resource.14928 (jp2, 300 ppi; Digital Library of India scan; the pages seen are clean). No 2nd ed. (1872) scan found |
| II | Ion, Helena, Andromache, Electra, Bacchae, Hecuba | 2nd ed. 1874: ldpd_8039020_001 (Columbia, 670, jp2); 1st ed. 1858: india.history.resource.53572 (jp2); a Cambridge Library Collection reprint (euripideswitheng0002pale) refuses page downloads (403) |
| III | Hercules Furens, Phoenissae, Orestes, Iphigenia in Tauris, Iphigenia in Aulis, Cyclops | 2nd ed. 1880: ldpd_8039020_002 (Columbia, 690, jp2); 1st ed. 1860: bibliothecaclass0003fapa (694, jp2, 360 ppi), euripides05eurigoog (Google, 684, jp2), 10232889bsb (BSB), india.history.resource.53573 |

Paley's text is not Murray's; his notes discuss his own readings, so a note's lemma will at times
differ from Murray's word (as with Rzach and Paley in the Theogony: the note stays under its
line).

### Prinz-Wecklein, *Euripidis Fabulae* (Teubner) — relevant only to the older route

R. Prinz (1847-1890) and N. Wecklein (1843-1926). One fascicle per play, each with a Latin
preface, the text with margin numbers every fifth verse at the right, a Latin apparatus at the
foot (sigla L P l p), and after the play an **Appendix** of conjectures keyed by verse. Seen:
vol. II, Supplices p. 31 (clean, 400 ppi). Plays and scans (running heads read by OCR every
twelfth image):

| vol. | plays (in order) | scans |
|---|---|---|
| I | Medea (2nd ed. in the Toronto copy), Alcestis, Hecuba, Electra, Ion, Helena, Cyclops | euripidisfabula01euriuoft (546, jp2); bub_gb_XaUNAAAAIAAJ (Google, 526, jp2; Medea with the first preface); euripidisfabulae113euri (v.1 parts 1-3: Medea, Alcestis, Hecuba; 208, jp2, 500 ppi); euripidisfabulae147euri (parts 4-7: Electra, Ion, Helena, Cyclops; 318, jp2) |
| II | Iphigenia in Tauris, Supplices, Bacchae, Heraclidae, Hercules, Iphigenia in Aulis | euripidisfabulae02euriuoft (486, jp2; title pages: IT 1898, Supplices 1898, Bacchae 1897 or 1898, IA 1899); euripidisfabulae02euri (488, jp2) |
| III | Andromache, Hippolytus, Orestes, Phoenissae, Troades, Rhesus (then addenda to vols I-II and the Γένος καὶ βίος) | euripidisfabulae00euri (570, jp2); euripidisfabulae03euri (574, jp2) |

Other uniform texts looked at only in passing: Nauck's Teubner (Hercules 1913 reprint,
herculesediditan00euriuoft), Kirchhoff 1867, Weil's *Sept tragédies* (1868; French notes; Weil
d. 1909; Hippolytus, Medea, Hecuba, IA, IT, Electra, Orestes), Paley's Latin text 1878
(euripidesexrecen01-03euri). None changes the picture now that Murray is the text.

## Traps

* **Murray**: protected in Norway and the UK until the end of 2027 (author's plan: from
  1 January 2028). His English verse translations stay protected (died 1957) and are many on
  archive.org (Electra, Hippolytus, Iphigenia in Tauris, Rhesus, Bacchae, Trojan Women, Medea);
  Perseus tlg019 eng4 is his Rhesus.
* **Perseus vol. II source is a 1962 printing** (euripidisfabu02euri) and vol. III a 1925-1946
  printing; the text is the 1913 editions'. Vol. I's Boston College copy is a 1974 printing.
* **Porter's Rhesus** (1916, 1929): Porter died 1961.
* **Byrde's Heracles** (1914) seems to reprint Murray's text and apparatus; Byrde's death not
  found.
* **C. E. S. Headlam** (Medea, IA, Heraclidae with Beck): born 1864, death year still not found.
* **Death years not found**: W. E. Long (Cyclops, b. 1862), A. R. F. Hyslop (Andromache), John
  Bond (Hecuba, with Walpole 1850-1920), C. H. St. L. Russell (Hecuba, b. 1862), A. W. Upcott
  (Hecuba), C. H. Keene (Electra; b. 1847, so certainly dead before 1955, year unseen).
* **Scans that look right but are not**: hippolytusofeuri0000unse (a verse translation, not
  Mahaffy-Bury); andromacheeurip01norwgoog (catalogued Macmillan 1909, is Norwood 1906);
  `euripidis-fabulae-i-ii-iii` (Diggle's OCT, unauthorised); euripideswitheng0002pale (a 2010
  reprint, pages not downloadable); india.history.resource.* scans show "images None" in the
  metadata but their page images load.
* Death years taken from memory and not checked here: Horace Hart's and John Johnson's terms as
  printers, W. N. Bates (1947), J. U. Powell (1932).

## Not done or not verified

* Pages of Keene's Electra (HathiTrust) and of Pearson's Phoenissae text pages with their
  critical notes.
* Which edition the Boston College vol. II (euripidisfabulae02euri_0) is; whether a pre-1931
  printing of the 1913 vol. III exists on archive.org (the Google Michigan scans were not
  opened).
* Verse counts are the standard last line numbers, not counts of Murray's printed verses (the
  Perseus grc2 files have 747 to 1,812 `<l>` elements per play, lettered parts included).
* Lyric share per play was not measured; the ranking uses the general picture (Helen, Troades,
  Phoenissae, Orestes, IA lyric-heavy; Heraclidae, Medea, Alcestis less so).
