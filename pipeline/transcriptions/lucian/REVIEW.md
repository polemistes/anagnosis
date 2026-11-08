# Nilén's Lucian: the independent review of a checked batch

After the agent that checked a batch has finished, a second agent, which has not seen the first
one's reasoning, reviews the batch against the page images (as for the plays:
`pipeline/transcriptions/drama/REVIEW.md`). Give the reviewer this file, the batch file, and the
first agent's report (as information only).

**Your own files.** Scripts and crops only in a folder of your own under the session's scratchpad
(`<scratchpad>/truestory-rev-<batch>/`). Edit only the batch file you are given. Do not commit.
Save the batch file after each page.

Read `INSTRUCTIONS.md` in this folder, all of it: the batch must meet it. Images:
`pipeline/build/lucian-pages/truestory/` (`p-NNNN-lines.png`, `p-NNNN-app-l.png`,
`p-NNNN-app-r.png`, the check sheets `p-NNNN.md`) and the whole pages
`pipeline/build/lucian-pages/truestory/pages/leaf_NNNN.png`. Assume nothing the first agent wrote
is right until you have seen it on the image. For each page:

1. **The apparatus**, item by item against the print: every item present (each line number
   begins one), its number as printed, the lemma, readings, sigla with their raised letters and
   digits (Γᵃ Γˣ Γ* S²), Nilén's Latin and the editors' names as printed, the Greek accents and
   breathings right, `-` for "Libri: …" and the subscriptions. Add what is missing, correct what
   is wrong. This is where most errors are.
2. **The keys and marks**: the lines of the page counted (the title counts as line 1), every
   `§` mark on the line where Nilén's chapter number stands and before the right word, every `¶`
   where he indents.
3. **The text**: every change the first agent made (its notes, and the checker's remarks), and
   any flagged line whose resolution looks doubtful; Nilén's reading must stand, not Harmon's.

Correct what is wrong in place, with one line for each change under `--- notes` beginning `rev:`
(`133.5	rev: apparatus item 5 αὐτοὺς F added`). Then run the checker (from `pipeline/`:
`.venv/bin/python -m anagnosis_pipeline check-lucian-batch transcriptions/lucian/truestory/batch-NN.md`)
and fix or explain every remark. Reply per page with what you changed (or "no change"), the
number of unexplained remarks, and anything left open.
