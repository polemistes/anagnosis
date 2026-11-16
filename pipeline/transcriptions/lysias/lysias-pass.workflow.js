export const meta = {
  name: 'lysias-second-passes',
  description: "Lysias (Hude's Oxford text): the residual pass (RESIDUALS.md) or the independent review (REVIEW.md) of checked text batches, one Opus agent per job",
  phases: [
    { title: 'Pass', detail: 'one agent per job, checker on every file', model: 'opus' },
  ],
}
// scratch = /home/proteus/koding/anagnosis/pipeline/build/agent-scratch (on disk, git-ignored; NOT the
// session scratchpad, which is a RAM disk and is emptied at a restart)
// args: { scratch, kind: 'residuals' | 'review', atOnce: 10,
//         extra: 'a further instruction for every review agent',
//         jobs: [{ id: '01', batches: ['01', '02'], pages: 'p-0019, p-0022' }] }
// residuals: after `lysias-residuals`; two batch files per job, `pages` = the pages that have residuals.
// review: one batch file per job. See pipeline/PLAN-lysias.md ("Hand-over").
const ROOT = '/home/proteus/koding/anagnosis/pipeline'
const SLUG = 'lysias'
const SCAN = 'orationesrecogno00lysi'
const { scratch, kind, jobs } = args
const atOnce = args.atOnce || 10
const files = j => j.batches.map(b => `transcriptions/${SLUG}/batch-${b}.md`)
const common = j => `Working directory: ${ROOT} (run commands from there).
Batch file${j.batches.length > 1 ? 's' : ''} (edit in place, save after each page): ${files(j).join(', ')}
Whole pages: build/drama-scans/${SCAN}/pages/leaf_NNNN.png
Checker: .venv/bin/python -m anagnosis_pipeline check-lysias-batch <batch file>
Write no other file in the repository and do not run git. Keep your scratch folder small (crops only as large as you need, deleted when you are done with them); never write under /tmp. Do not open texts/${SLUG}/ or any other batch file.`
const prompt = j => kind === 'residuals'
  ? `You do the second pass (residuals, sections, paragraphs) on checked batches of the Greek text of Lysias's speeches (Hude's Oxford text, 1912), for an open-source Ancient Greek reading app. Accuracy of every accent, breathing and stop matters more than speed.

First read transcriptions/${SLUG}/RESIDUALS.md and transcriptions/${SLUG}/INSTRUCTIONS.md (all of both) and follow them exactly.

${common(j)}
Residual lists and crops: build/hude-pages/${SLUG}/residuals/ (r-NNNN.md, r-NNNN.png)${j.pages ? `; your pages with residuals: ${j.pages}` : ''}
Your own folder for crops and scripts: ${scratch}/${SLUG}-res-${j.id}/

Reply as RESIDUALS.md says: per page, items settled, changes made; and the checker's last line for each file.`
  : `You review, independently, a batch of the Greek text and critical apparatus of Lysias's speeches (Hude's Oxford text, 1912) that another agent has checked, for an open-source Ancient Greek reading app. Accuracy of every Greek letter, accent, breathing and siglum matters more than speed.

First read transcriptions/${SLUG}/REVIEW.md and transcriptions/${SLUG}/INSTRUCTIONS.md (all of both) and follow them exactly.

${common(j)}
Check sheets and crops: build/hude-pages/${SLUG}/ (p-NNNN.md, p-NNNN-lines.png, p-NNNN-app-l.png, p-NNNN-app-r.png)
Your own folder for crops and scripts: ${scratch}/${SLUG}-rev-${j.id}/
${args.extra ? '\n' + args.extra + '\n' : ''}
Reply as REVIEW.md says: per page what you changed (or "no change"), the number of unexplained checker remarks, anything left open.`

const out = []
for (let i = 0; i < jobs.length; i += atOnce) {
  const chunk = jobs.slice(i, i + atOnce)
  const res = await parallel(chunk.map(j => () =>
    agent(prompt(j), { label: `${SLUG} ${kind} ${j.id}`, phase: 'Pass', model: 'opus', agentType: 'general-purpose' })
      .then(r => ({ job: j.id, reply: String(r || 'NO REPLY').slice(0, 700) }))))
  out.push(...res.map((r, k) => r || { job: chunk[k].id, reply: 'AGENT FAILED' }))
  log(`${SLUG} ${kind}: jobs ${chunk[0].id}–${chunk[chunk.length - 1].id} back`)
}
return out
