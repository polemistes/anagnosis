# Checking Lodge's introduction to the Gorgias

Gonzalez Lodge's edition of the Gorgias (Boston: Ginn, 1890; here the 1896 printing) has a
preface (pp. iii-iv) and an introduction (pp. 1-32) that Perseus lacks; his commentary, which
Perseus has, cites it ("See Introd. § 4", "Introd. N. 12"). The pages were read by Tesseract.
Your work is to turn each page's OCR into a clean Markdown page, checked against the image.
`merge-gorgias` joins the pages into `texts/gorgias/introduction.md`. The book is in the public
domain; the transcription is published under CC BY-SA 4.0.

## Files

For each leaf (`0010` … `0041`; `0008`-`0009` are the preface), in `pipeline/build/lodge-intro/`:

* `leaf_0010.md`: Tesseract's text of the page and a list of suspect words;
* `pages/leaf_0010.png`: the page (about 2090 × 2900 pixels).

Write `pipeline/transcriptions/gorgias-lodge-intro/page-0010.md` for each leaf, **one file per
page, saved as soon as the page is done**.

## The page file

```
…continues the paragraph from the page before, with a footnote[^33] here.

## 5. Plan of the Dialogue

A new paragraph, with *italic* titles such as the *Apology*, and Greek as printed: νεωστί.

--- footnotes
[^33]: *Apol.* 32 b.
[^34]: This play was brought out in 420, while the time of the …
+ the rest of a footnote that began on the page before
```

* Leave out the running head ("INTRODUCTION.", "PREFACE.") and the page number.
* **A page that begins in the middle of a paragraph** begins with `…` (U+2026) and a space;
  otherwise it begins with its first heading or paragraph.
* Paragraphs are separated by a blank line and written as one line each; join words divided at
  a line end (`indefi-` / `niteness` → `indefiniteness`; keep a hyphen that belongs to the word:
  `note-worthy` is printed `note-` / `worthy` — decide from the sense and from other places in
  the book).
* **Headings**: Lodge's numbered sections ("1. THE BEGINNINGS OF RHETORIC.") as `## 1. The
  Beginnings of Rhetoric`, in ordinary capitals and lower case; the preface as `## Preface`;
  "INTRODUCTION." at the top of page 1 as `# Introduction`. Smaller headings inside the outline
  of the dialogue (pp. 25-31) are kept as paragraphs, as printed (with their numbers and letters:
  "I. 447 a-481 b. Dialogue between …"; "a. 470 c-472 d. …").
* Italics as `*…*` (book titles, Latin words, emphasis). Small capitals as ordinary text.
* Greek exactly as printed, with all accents and breathings (Tesseract is weak on these: check
  every Greek word against the image).
* References to the Gorgias stay as printed ("472 a", "473 e").
* **Footnotes**: the number in the text becomes `[^33]` right after the word (or punctuation) it
  stands on; the note itself goes under `--- footnotes` as `[^33]: text`. The notes are printed
  at the foot of the page, often in two columns: read the left column, then the right. A note
  that continues from the page before (its text begins without a number) is written as a line
  beginning with `+ `, first under `--- footnotes`.
* Quotation marks as printed (“ ” ‘ ’); dashes as — .

## The suspect words

`leaf_NNNN.md` lists words that are not in the English word lists, Greek with unusual accents,
and digits among letters. Look at each, but read the whole page against the image: Tesseract
also misreads footnote numbers (® for 33), drops stray specks into the text (a "." or "-" at a
line's end), and loses italics.

## When done

For each page you did, say in one line what you corrected beyond the joining of divided words.
