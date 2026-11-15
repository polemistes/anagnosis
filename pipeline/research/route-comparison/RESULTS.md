# Two ways of reading Jebb's pages: by eye and by OCR with flags

Sophocles, Trachiniae, Jebb 1892, scan pages 80–143 (verses 1–440, about 2,600 words of Greek
text; 258 notes of the critical apparatus), read twice and independently on 2026-11-15:

* **Route E, by eye**: Opus agents read whole page images (1600 px wide), compared the printed
  verses with the Perseus text and typed the apparatus (the route of 2026-10-05, used for Ajax
  and Electra). One pass.
* **Route O, OCR**: Tesseract reads the page, the words are matched to the Perseus text, Opus
  agents decide the flagged places from line crops and write the apparatus from enlarged
  crops; a residual pass settles what Tesseract's reading of each verse still disagrees with
  (the drama pipeline). Measured after the first pass (commit 854a0cb) and after the residual
  pass (37b78c0).

Every place where the two differ was judged from the page image by Opus readers who were not
told which route wrote which reading (two readers on a quarter of the places, agreeing on all;
one reader on the rest, a second where the first was unsure). `compare.py` makes the lists,
`tally.py` the counts; the lists, keys, verdicts and tallies are in `after-flags/`,
`after-residual/` and `adjudication/`.

## Result

No word differs between the routes and neither lacks a note. The differences are stops,
accents and breathings.

| | by eye | OCR, after the flags | OCR, after the residual pass |
|---|---|---|---|
| Greek text: places where this route is wrong and the other right | 10, then 15 (see below) | 24 | 2 |
| of these, a real difference from Perseus it did not see | 9, then 14 | 24 | 2 |
| of these, an error it introduced | 1 | 0 | 0 |
| Critical apparatus: places wrong (the other right) | 22 | 4 | 4 |
| Apparatus: neither right | 1 | 1 | 1 |
| Apparatus: readers could not agree | 1 | 1 | 1 |

"10, then 15": against the OCR route's first pass the by-eye text is wrong in 10 places;
the residual pass then corrected places both routes had wrong until then, which shows five
more by-eye errors.

* **Text.** The by-eye reader overlooks about one stop or accent in 175 words (15 in 2,600).
  The OCR route after its first pass alone is worse than the eye (24: the flags compare
  letters only, so punctuation and accents are not looked at), and after the residual pass
  much better (2). Both of those two (320 σαυτῆς· with a raised stop; 324 προὔφηνεν with the
  coronis) were then found by the review pass, in which an agent reads every verse against
  the page: after it no known error is left in the text of these pages.
* **Apparatus.** By eye 22 errors in 258 notes, nearly all a breathing or accent in the small
  Greek type (rough for smooth and the reverse); from enlarged crops 4. The crops, not the
  OCR, make the difference here: Tesseract's reading of the apparatus is only a help.
* An error both routes make in the same way cannot be seen by this comparison.

## After the review, and the places that stayed in doubt

After the review pass (every verse read against the page, the apparatus item by item) the
comparison was run a third time (`after-review/`). The text had no known error left. In the
apparatus five places still stood against the blind readers or between them, all a breathing
or accent in the small type, and a sixth showed up new. One more agent settled these six from
4x enlargements, each beside certain rough and smooth breathings from the same page: four
corrected in the OCR route's file (122 ἁδεῖα, 166 ἤσφε, 333 ῆ, 162 ἦ: the first three
certain, the last probable), two confirmed as they stood (58 ὤραν; 66 πὄυστιν as one word,
loosely set). Three of the four corrections are readings the by-eye route had right. With
them the final text and apparatus of these pages hold no known error; the by-eye reading of
the same pages holds 15 in the text and about 20 in the apparatus.

## Cost (agent tokens, Opus)

| | tokens | scan pages | per page |
|---|---|---|---|
| by eye, one pass (with two small test agents of another model) | 1.34 M | 64 | about 20,000 |
| OCR route, first pass | 2.47 M | 178 | 13,900 |
| OCR route, residual pass | 1.28 M | 178 | 7,200 |
| OCR route, both | 3.75 M | 178 | 21,100 |
| OCR route, review pass (two runs; the first was stopped half way) | about 2.5 M | 178 | about 14,000 |

The by-eye route would also need its second pass for the lyric verses, which the OCR route
does not (the draft divides the verses as printed).

## Conclusion

At about the same cost per page the OCR route with its residual pass leaves a seventh of the
errors in the text and a fifth in the apparatus. The first pass alone is not enough. The
review pass with verse reading finds the last few. Ajax and Electra, made by eye in one pass,
can be expected to hold errors at the by-eye rate (roughly one stop or accent in 175 words of
text, one breathing or accent in twelve notes of the apparatus).
