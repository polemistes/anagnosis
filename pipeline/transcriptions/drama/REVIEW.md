# The plays: the independent review of a checked batch

Used for the Clouds (2026-11-01/02): after the agent that checked a batch has finished, a second
agent, which has not seen the first one's reasoning, reviews the batch against the page images.
It caught wrong breathings, missed apparatus items, misplaced notes and sentences out of order
that the checker cannot see. Give the reviewer this file, the batch file, its pages, and the
first agent's report (as information only).

**Your own files.** Scripts and crops only in a folder of your own under the session's scratchpad
(`<scratchpad>/<play>-rev-<batch>/`). Edit only the batch file you are given. Do not commit. Save
the batch file after each page.

## A text batch (`batch-NN.md`)

Read `INSTRUCTIONS-text.md` (all of it, with the section on the edition): the batch must meet it.
Images: `pipeline/build/drama-pages/<play>/` (`p-NNNN-lines.png`, `p-NNNN-app-l.png`,
`p-NNNN-app-r.png`, `-app2-` for an apparatus run on to the facing page, the check sheets
`p-NNNN.md`) and the whole pages `pipeline/build/drama-pages/<play>/pages/leaf_NNNN.png`. Assume
nothing the first agent wrote is right until you have seen it on the image. For each page:

1. **The apparatus**, item by item against the print: every item present (items divided by `||`
   are separate lines), each with its printed line number, readings, sigla and the editor's words
   as printed, the Greek accents right; nothing from the commentary. Where the apparatus runs on
   to the facing page, that part too. Add what is missing, correct what is wrong.
2. **The verses**: every turnover the draft joined, every lettered verse, every speaker line and
   the printed margin numbers against the page (the printed numbering wins; INSTRUCTIONS-text.md
   gives the rule).
3. Any flagged line whose resolution looks doubtful.

## A prose batch (`notes-NN.md`, `intro-NN.md`, `trans-NN.md`, `app-NN.md`)

Read `INSTRUCTIONS-prose.md`. Images: `pipeline/build/drama-prose/<play>/` (`p-NNNN-col-l.png`,
`-col-r.png`; for a translation batch `trans-p-NNNN-…`) and
`pipeline/build/drama-prose/<play>/pages/leaf_NNNN.png`. Read every page's block against the page
image, word by word: wrong words; lost, doubled or misordered text (above all at the column break
and the page break); paragraphs, headings and footnotes; italics and quotation marks; the Greek
with every accent and breathing; references and sigla. In notes: every note present with its
printed line number as heading and its bold lemma, no false headings, nothing taken in from the
verses, the apparatus or the translation. In a translation: every speech's speaker and line
number against the facing Greek page (its checked batch file), stage directions in parentheses.

## Both

Correct what is wrong in place, with one line for each change under `--- notes` beginning
`rev:` (`273	rev: apparatus item 273 added`). Then run the checker
(`check-drama-batch <play> <file>` or `check-drama-prose <play> <file>`, from `pipeline/`) and fix
or explain every remark. Reply per page with what you changed (or "no change"), the number of
unexplained remarks, and anything left open.
