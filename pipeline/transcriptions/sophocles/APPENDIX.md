# Jebb's Sophocles: the Appendix

Each of Jebb's volumes ends with an Appendix: notes, longer than those of the commentary, on
particular lines of the play (readings, conjectures, constructions, antiquities). It is
transcribed page by page into `appendix-NN.md` files in the play's folder, and
`merge-sophocles-appendix` joins them into `texts/<play>/appendix.md`, a document of the app,
in the format of `texts/antigone/appendix.md` (look at that file before you start). The edition
is in the public domain; the transcription is published under CC BY-SA 4.0.

Page images: `pipeline/build/sophocles-pages/<play>/p-NNNN.png`, the PDF page number zero padded
to four digits. Read them with the Read tool, one at a time, in order.

## Output format

One block per page, in page order, each beginning with a line `=== p-NNNN`:

    === p-0297
    ## Line 15

    **κἂν ἄποπτος ᾖς ὅμως.** In his *Lehrbuch der griechischen Bühnenalterthümer*, p. 151,
    note 1, Dr Albert Müller holds that this clause is to be understood as merely a general
    remark (‘als allgemeine Bemerkung zu fassen ist’). …

    ## Line 75

    **οὐ σῖγ’ ἀνέξει μηδὲ δειλίαν ἀρεῖ;**

    ### I. Note on the Construction.

    Prof. W. W. Goodwin, in his *Syntax of Greek Moods and Tenses* (new ed. 1889), § 299,
    gives a view of this passage which requires
    === p-0298
    + careful consideration. …

* Leave out the running head (the page number and "APPENDIX." or the play's name) and the large
  title "APPENDIX." on the first page.
* Each note of the Appendix begins with a line number and Jebb's lemma. Write the number as a
  heading `## Line 15`, as printed with "f." or "ff." (`## Line 2 f.`, `## Line 23 ff.`), or a
  range with an en dash (`## Lines 836–838`). The lemma, the Greek words that follow the number,
  goes in bold at the start of the first paragraph: `**κἂν ἄποπτος ᾖς ὅμως.** In his …`; when
  the lemma stands alone on its line, it is a paragraph of its own.
* A heading inside a note ("I. NOTE ON THE CONSTRUCTION.") is `### ` plus the words as printed,
  small capitals written as ordinary capitals and small letters: `### I. Note on the Construction.`
* Paragraphs are separated by a blank line, and so are headings. Write each paragraph as running
  text: join its lines, and write a word divided at the end of a line whole (keep a hyphen only
  in a word that has one, as *tobacco-pipe*). Lines may be wrapped in the file as you like.
* Greek verses quoted on lines of their own: in their paragraph, separated by ` | `.
* A numbered list ("4. Bothe: κἂν οὐδενί …") is a paragraph per item, beginning with its number.
* A paragraph that runs on to the next page simply stops at the foot of the page; the next page's
  block begins with `+ ` followed by the rest of it. A word divided between two pages is written
  whole at the end of the first page, and its second half is left out on the next.
* A footnote (small type at the foot of the page, marked ¹ ² …): keep the mark in the text where
  it stands (`30 B.C.¹`), and write the note as a paragraph `[Note: ¹ …]` directly after the
  paragraph in which its mark stands (on that page).
* Keep Jebb's wording, spelling, punctuation and quotation marks (‘ ’ “ ”) exactly; the dash is —.
  Italics go in `*...*`. Greek in Unicode polytonic, precomposed characters, with every breathing
  and accent; ’ (U+2019) for elision. Small capitals (B.C., MSS.) as ordinary capitals.
* Where something is genuinely illegible, write `[illegible]` and say so in your reply; never
  guess silently. Nothing of your own.

## Checking

Read your file through once against the images, above all the Greek accents and breathings
(in the small Greek type a rough breathing is easily misread as smooth) and the names of scholars.
