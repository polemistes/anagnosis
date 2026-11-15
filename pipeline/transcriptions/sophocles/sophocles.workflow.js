export const meta = {
  name: 'sophocles-pages',
  description: 'Jebb Sophocles: one agent per group of pages (text check and critical apparatus, lyric pass, appendix or introduction), checker on every file',
  phases: [
    { title: 'Transcribe', detail: 'one agent per job, each saving page by page' },
  ],
}
// args: { play: 'trachiniae', title: 'Trachiniae', scratch: '<session scratchpad>', model: 'opus',
//         kind: 'batch' | 'lines' | 'appendix' | 'introduction',
//         jobs: [{ id: '09', from: 144, to: 151 }  or  { id: '01', pages: [120, 122, 124] }] }
// OLD ROUTE (agents read whole pages by eye), kept for the record: PLAN-sophocles.md now
// prescribes the drama pipeline (OCR, flags, residuals). Do not use for new pages.
const ROOT = '/home/proteus/koding/anagnosis/pipeline'
const { play, title, scratch, kind, jobs } = args
const model = args.model || 'opus'
const pad = n => 'p-' + String(n).padStart(4, '0')
const pagesOf = j => j.pages ? j.pages.map(pad).join(', ') : `${pad(j.from)} to ${pad(j.to)}`
const dir = `transcriptions/sophocles/${play}`
const KIND = {
  batch: { brief: 'INSTRUCTIONS.md', prefix: 'batch', what: 'the critical notes and the text check' },
  lines: { brief: 'LYRICS.md', prefix: 'lines', what: 'the division of the lyric verses' },
  appendix: { brief: 'APPENDIX.md', prefix: 'appendix', what: "Jebb's Appendix" },
  introduction: { brief: 'INTRODUCTION.md (and APPENDIX.md, whose rules it builds on)', prefix: 'introduction', what: 'the pages before the text' },
}[kind]
const extra = {
  batch: `* For the text check use ${dir}/reference-grc.txt; find our lines by the numbers printed in the margin. Compare word by word, with accents, breathings and punctuation.
* When all pages are done run
    .venv/bin/python -m anagnosis_pipeline check-sophocles-batch ${play} ${dir}/batch-ID.md
  and deal with every remark as INSTRUCTIONS.md says (look again at the image).`,
  lines: `* Our text is texts/${play}/grc.txt (../texts/${play}/grc.txt from the working directory), as LYRICS.md says. Pages on which the print's division agrees with ours get no block.
* After each page with changes, and at the end, run
    .venv/bin/python -m anagnosis_pipeline check-sophocles-lines ${play} ${dir}/lines-ID.md
  and compare its output with the print, verse for verse, as LYRICS.md says.`,
  appendix: `* Look at ../texts/antigone/appendix.md for the format before you start. When you have finished, read your file through once against the images.`,
  introduction: `* Look at ../texts/antigone/introduction.md (its last two chapters) and at ../texts/electra/introduction.md for the result wanted. When you have finished, read your file through once against the images.`,
}[kind]
const prompt = j => `You are transcribing pages of R. C. Jebb's edition of Sophocles' ${title} (Sophocles: The Plays and Fragments, Cambridge) for an open-source Ancient Greek reading app: ${KIND.what}. Accuracy of every word, and of every Greek letter, accent and breathing, matters more than speed.

Working directory: ${ROOT} (run commands from there).
First read transcriptions/sophocles/${KIND.brief} and follow it exactly.

Play: ${play}
Pages: ${pagesOf(j)} (images build/sophocles-pages/${play}/p-NNNN.png)
Output file: ${dir}/${KIND.prefix}-${j.id}.md
${j.note ? '\n' + j.note + '\n' : ''}
How to work:
* One page at a time, in order: Read the image, write that page's block, and append it to the output file BEFORE going on to the next page, so nothing is lost if you are interrupted. If the output file already holds blocks, continue after the last page present.
* Small type: whenever a letter, accent, breathing or siglum is not perfectly clear, crop that part of the page with Python (PIL) at full resolution or enlarged 2x into ${scratch}/${play}-${KIND.prefix}-${j.id}/ and Read the crop. One image per request; keep requests light. Never guess: look closer, and if still unsure say so (under --- notes where the format has it, otherwise in your reply).
${extra.replace(/ID/g, j.id)}
* Write no other file in the repository, do not run git, and do not read anything outside /home/proteus/koding/anagnosis and ${scratch}.

Final reply (short): for each page what it holds (numbers of notes and differences, or paragraphs), the checker's last line if there is a checker, and anything left uncertain.`

const out = await parallel(jobs.map(j => () =>
  agent(prompt(j), { label: `${play} ${KIND.prefix}-${j.id} ${pagesOf(j)}`, phase: 'Transcribe', model, agentType: 'general-purpose' })
    .then(r => ({ job: `${KIND.prefix}-${j.id}`, reply: String(r || 'NO REPLY').slice(0, 900) }))))
return out
