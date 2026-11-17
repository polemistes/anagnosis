# Authors' names before titles in Jebb's commentaries: reading the places on the page

Jebb's commentaries on the Antigone, the Ajax and the Electra come from the Perseus Digital
Library's files. In those files an author's abbreviation has dropped out before many titles:
Jebb prints "Then in Plat. *Phaedr.* 272 B", the file has "Then in *Phaedr.* 272 B". Whether a
name is missing cannot be told from the file ("Aesch. *Ag.* 1148 …: *Th.* 683 …" is right as it
stands: Jebb does not repeat "Aesch."). So every place where it may have happened is read on
his page. That is your work: one job file, about forty places.

## Your file

`pipeline/transcriptions/sophocles/<play>/authors-NN.tsv`. Each place has three lines:

    == 12 · note 583 · leaves 180, 181
    … for there μὴ ἐλλείπεσθαι εὖ ποιῶν=‘not to be outdone in generosity.’ Then in ⟦A⟧ *Phaedr.* 272 B ὅ τι ἂν αὐτῶν τις
    → 

* "note 583": the commentary note in which the place stands (Jebb heads his notes with the
  verse number in bold: **583 ff.**).
* "leaves 180, 181": the pages of the scan on which that note should stand. The commentary is
  printed in two columns under the text and the critical apparatus, and runs across both pages
  of an opening; a long note may begin on the opening before or run on to the next: look there
  if you do not find the words.
* The second line is our text round the place; ⟦A⟧ marks where a name may be missing. The
  asterisks are our italics.

Write your answer after the arrow, on the same line:

* the author's name or abbreviation exactly as the page prints it at that place, with its
  stop: `Plat.`, `Eur.`, `Aesch.`, `Ar.`, `Xen.`, `Arist.`, `Hor.`, `Lucian`;
* `-` if the page prints nothing there (the title follows the words before it directly);
* `? ` and a few words, if you cannot find the place or cannot read it (say which leaves you
  looked at). Do not guess: an answer must be something you have seen on the page.

Only that. Do not correct anything else in the line, even if you see that our text differs
from the page in another way; if you do see such a difference, add it to your reply (note
number, our words, the page's words), not to the file.

## The pages

Whole pages: `pipeline/build/drama-scans/<scan>/pages/leaf_NNNN.png` (about 2300 × 3900
pixels). The commentary is the lower part of the page, in two columns of small type. Cut the
part you need and enlarge it; do not judge small type from a reduced whole page. A citation's
author stands in upright type before the italic title: "Plat. *Phaedr.*".

Your scratch folder for crops is given in your task; keep it small and delete the crops when
you finish. Do not put files under /tmp.

## Checking and finishing

Save the file after every ten answers. Run the checker from `pipeline/`:

    .venv/bin/python -m anagnosis_pipeline jebb-authors check transcriptions/sophocles/<play>/authors-NN.tsv

It must print no remark (an unanswered place, or an answer that is neither a name, `-` nor
`? …`). Write no other file in the repository and do not run git.

Reply with: the number of places with a name restored, with `-`, and with `?`; the checker's
last line; and any other differences between our text and the page that you happened to see.
