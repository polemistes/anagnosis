export const meta = {
  name: 'jebb-authors',
  description: "Jebb's commentaries from Perseus: one agent per job file reads on the page whether an author's name stands before a title where the file has none (about forty places each)",
  phases: [
    { title: 'Reading', detail: 'one job file per agent (AUTHORS.md)' },
  ],
}
// args: { atOnce: 9, model: 'opus', scratch: '/home/proteus/koding/anagnosis/pipeline/build/agent-scratch',
//         jobs: [{ play: 'antigone', scan: 'sophocles03soph', name: 'authors-01' }, ...] }
// Before: .venv/bin/python -m anagnosis_pipeline jebb-authors jobs antigone ajax electra   (and commit the job files)
// After:  .venv/bin/python -m anagnosis_pipeline jebb-authors check transcriptions/sophocles/<play>/authors-*.tsv
//         commit; `jebb-authors pairs <play>` shows what will be applied; sophocles-prose <play> applies it.
// The brief is transcriptions/sophocles/AUTHORS.md (pipeline/anagnosis_pipeline/jebb_authors.py).
const ROOT = '/home/proteus/koding/anagnosis/pipeline'
const jobs = args.jobs
const atOnce = args.atOnce || 9
const model = args.model || 'opus'
const scratch = args.scratch || `${ROOT}/build/agent-scratch`
const prompt = j => `You read places in a printed commentary (R. C. Jebb's edition of Sophocles, 1890s) on page images, for an open-source Ancient Greek reading app whose text of that commentary is on sale: at each place you say whether an author's name stands before a title. Accuracy matters more than speed; an answer must be something you have seen on the page.

First read transcriptions/sophocles/AUTHORS.md, all of it, and follow it exactly.

Working directory: ${ROOT} (run commands from there).
Play: ${j.play}
Your file (edit it in place, save after every ten answers): transcriptions/sophocles/${j.play}/${j.name}.tsv
Whole pages: build/drama-scans/${j.scan}/pages/leaf_NNNN.png
Your own folder for crops and scripts: ${scratch}/${j.play}-${j.name}/ (on disk; nothing under /tmp)
Checker: .venv/bin/python -m anagnosis_pipeline jebb-authors check transcriptions/sophocles/${j.play}/${j.name}.tsv

Write no other file in the repository and do not run git. Delete your crops when you finish.

Reply as AUTHORS.md says: how many names restored, how many "-", how many "?", the checker's last line, and any other differences between our text and the page that you happened to see (note number, our words, the page's words).`

const out = []
for (let i = 0; i < jobs.length; i += atOnce) {
  const chunk = jobs.slice(i, i + atOnce)
  const res = await parallel(chunk.map(j => () =>
    agent(prompt(j), { label: `${j.play} ${j.name}`, phase: 'Reading', model, agentType: 'general-purpose' })
      .then(r => ({ job: `${j.play}/${j.name}`, reply: String(r || 'NO REPLY').slice(0, 1500) }))))
  out.push(...res.map((r, k) => r || { job: `${chunk[k].play}/${chunk[k].name}`, reply: 'AGENT FAILED' }))
  log(`jobs ${chunk[0].play}/${chunk[0].name} – ${chunk[chunk.length - 1].play}/${chunk[chunk.length - 1].name} back`)
}
return out
