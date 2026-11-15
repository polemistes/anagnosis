export const meta = {
  name: 'drama-second-passes',
  description: 'Drama route: the residual pass (RESIDUALS.md) or the independent review (REVIEW.md) of checked text batches, one Opus agent per job',
  phases: [
    { title: 'Pass', detail: 'one agent per job, checker on every file', model: 'opus' },
  ],
}
// scratch = /home/proteus/koding/anagnosis/pipeline/build/agent-scratch (on disk, git-ignored; NOT the
// session scratchpad, which is a RAM disk and is emptied at a restart)
// args: { play, scan, scratch, kind: 'residuals' | 'review', atOnce: 12,
//         extra: 'a further instruction for every review agent',
//         jobs: [{ id: '01', batches: ['01', '02'], pages: 'p-0080, p-0082', open: 'numbering questions left open …' }] }
// residuals: after `drama-residuals <play>`; two batch files per job, `pages` = the pages that have residuals.
// review: one batch file per job. See pipeline/PLAN-drama.md and pipeline/PLAN-sophocles.md.
const ROOT = '/home/proteus/koding/anagnosis/pipeline'
const { play, scan, scratch, kind, jobs } = args
const atOnce = args.atOnce || 12
const files = j => j.batches.map(b => `transcriptions/drama/${play}/batch-${b}.md`)
const common = j => `Working directory: ${ROOT} (run commands from there).
Play: ${play} (edition section in INSTRUCTIONS-text.md: "Jebb's Sophocles" for the Sophocles plays)
Batch file${j.batches.length > 1 ? 's' : ''} (edit in place, save after each page): ${files(j).join(', ')}
Whole pages: build/drama-scans/${scan}/pages/leaf_NNNN.png
Checker: .venv/bin/python -m anagnosis_pipeline check-drama-batch ${play} <batch file>
Write no other file in the repository and do not run git. Keep your scratch folder small (crops only as large as you need). Do not open anything under transcriptions/sophocles/ (an independent reading of these pages is kept there for comparison and must stay independent), nor texts/${play}/.`
const prompt = j => kind === 'residuals'
  ? `You do the second pass (residuals and numbering) on checked batches of the Greek text of a play, for an open-source Ancient Greek reading app. Accuracy of every accent, breathing and stop matters more than speed.

First read transcriptions/drama/RESIDUALS.md and transcriptions/drama/INSTRUCTIONS-text.md (all of both) and follow them exactly.

${common(j)}
Residual lists and crops: build/drama-pages/${play}/residuals/ (r-NNNN.md, r-NNNN.png)${j.pages ? `; your pages with residuals: ${j.pages}` : ''}
${j.open ? `Numbering questions the first pass left open on your pages: ${j.open}\n` : ''}Your own folder for crops and scripts: ${scratch}/${play}-res-${j.id}/

Reply as RESIDUALS.md says: per page, items settled, changes made, verses renumbered; and the checker's last line for each file.`
  : `You review, independently, a batch of the Greek text and critical apparatus of a play that another agent has checked, for an open-source Ancient Greek reading app. Accuracy of every Greek letter, accent, breathing and siglum matters more than speed.

First read transcriptions/drama/REVIEW.md and transcriptions/drama/INSTRUCTIONS-text.md (all of both) and follow them exactly (the part "A text batch").

${common(j)}
Check sheets and crops: build/drama-pages/${play}/ (p-NNNN.md, p-NNNN-lines.png, p-NNNN-app-l.png, -app-r.png, -app2-l.png, -app2-r.png)
Your own folder for crops and scripts: ${scratch}/${play}-rev-${j.id}/
${args.extra ? '\n' + args.extra + '\n' : ''}
Reply as REVIEW.md says: per page what you changed (or "no change"), the number of unexplained checker remarks, anything left open.`

const out = []
for (let i = 0; i < jobs.length; i += atOnce) {
  const chunk = jobs.slice(i, i + atOnce)
  const res = await parallel(chunk.map(j => () =>
    agent(prompt(j), { label: `${play} ${kind} ${j.id}`, phase: 'Pass', model: 'opus', agentType: 'general-purpose' })
      .then(r => ({ job: j.id, reply: String(r || 'NO REPLY').slice(0, 700) }))))
  out.push(...res.map((r, k) => r || { job: chunk[k].id, reply: 'AGENT FAILED' }))
  log(`${play} ${kind}: jobs ${chunk[0].id}–${chunk[chunk.length - 1].id} back`)
}
return out
