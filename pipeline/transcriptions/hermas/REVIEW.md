# Lake's Shepherd: the independent review of a checked batch

After the agent that checked a batch has finished, a second agent, which has not seen the first
one's reasoning, reviews the batch against the page images (as for the True Story,
`pipeline/transcriptions/lucian/REVIEW.md`). Give the reviewer this file, the batch file, and the
first agent's report (as information only).

**Your own files.** Scripts and crops only in a folder of your own under the session's scratchpad
(`<scratchpad>/hermas-rev-<batch>/`). Edit only the batch file you are given. Do not commit. Save
the batch file after each page.

Read `INSTRUCTIONS.md` in this folder, all of it: the batch must meet it. Images:
`pipeline/build/lake-pages/hermas/` (`p-NNNN-lines.png`, `p-NNNN-app-l.png`, `p-NNNN-app-r.png`,
`p-NNNN-margin.png`, the check sheets `p-NNNN.md`) and the whole pages
`pipeline/build/lake-pages/hermas/pages/leaf_NNNN.png`. Assume nothing the first agent wrote is
right until you have seen it on the image. For each page:

1. **The apparatus**, item by item against the print: every item present (each raised numeral at
   the foot begins one), its number as printed, the lemma, readings, sigla with their raised and
   lowered letters (ℵ* ℵᶜ ℵᵃ L₁ L₂ Pᵃᵐ Pᵒˣ), Lake's Latin and English as printed, the Greek accents
   and breathings right. Add what is missing, correct what is wrong. This is where most errors are.
2. **The footnote marks**: every raised numeral in the Greek text of the page found and written
   after the right word (and after its stop), numbered as printed; none written that the page does
   not print. Look at the whole page image line by line for them: they are small.
3. **The structure**: the verses of the page with the first one keyed `+` when it continues from
   the page before; the page break at the right word (a word divided across it whole on the first
   page); `[chapter]` and `[title]` lines as printed; `¶` where Lake begins an indented line.
4. **The margin references** against `p-NNNN-margin.png`: all present, copied as printed, keyed to
   the verse beside them.
5. **The text**: every change the first agent made (its notes, and the checker's remarks), and any
   flag whose resolution looks doubtful; Lake's reading must stand, misprints included.

Correct what is wrong in place, with one line for each change under `--- notes` beginning `rev:`
(`1.1.7	rev: apparatus item 2 θυγατέρα A, dominam E. corrected`). Then run the checker (from
`pipeline/`: `.venv/bin/python -m anagnosis_pipeline check-hermas-batch transcriptions/hermas/batch-NN.md`)
and fix or explain every remark. Reply per page with what you changed (or "no change"), the number
of unexplained remarks, and anything left open.
