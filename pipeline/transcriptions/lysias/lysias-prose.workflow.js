export const meta = {
  name: 'lysias-prose-batches',
  description: "Lysias: the commentaries (Adams, Morgan, Shuckburgh), their introductions and Gillies's translation by the prose route: one Opus agent per batch answers the flags against the crops, then an independent second reading of the batch",
  phases: [
    { title: 'Prose batches', detail: 'flags against the crops, eight pages per agent', model: 'opus' },
    { title: 'Second reading', detail: 'an independent reading of each batch against the page images (REVIEW.md)', model: 'opus' },
  ],
}
// scratch = /home/proteus/koding/anagnosis/pipeline/build/agent-scratch (on disk, git-ignored; NOT the
// session scratchpad, which is a RAM disk)
// args: { scratch, atOnce: 8, review: true,
//         jobs: [{ entry: 'lysias-12', file: 'notes-01' }, { entry: 'lysias-12', file: 'intro-01' }, ...] }
// Each speech's commentary is an entry of the prose route (drama.LYSIAS_NOTES); the batch files are made
// by `drama-prose <entry> notes|intro draft`. The brief is transcriptions/drama/INSTRUCTIONS-prose.md,
// section "Lysias: the three commentaries, their introductions, and Gillies's translation".
// As drama-prose.workflow.js, with the entry given per job. See pipeline/PLAN-lysias.md ("Hand-over").
const ROOT = '/home/proteus/koding/anagnosis/pipeline'
const SECTION = "Lysias: the three commentaries, their introductions, and Gillies's translation"
const { scratch, jobs } = args
const atOnce = args.atOnce || 8
const common = j => `Working directory: ${ROOT} (run commands from there).
Entry: ${j.entry} (your section of the brief: "${SECTION}")
Your batch file (edit it in place, save after each page): transcriptions/drama/${j.entry}/${j.file}.md
Crops and whole pages: build/drama-prose/${j.entry}/ (p-NNNN-flags.png, p-NNNN-col-l.png, -col-r.png, pages/leaf_NNNN.png; FLAG_KINDS.md explains the flags)
Checker: .venv/bin/python -m anagnosis_pipeline check-drama-prose ${j.entry} transcriptions/drama/${j.entry}/${j.file}.md
Write no other file in the repository and do not run git. Keep your scratch folder small (crops only as large as you need, deleted when you are done); never write under /tmp. Do not open texts/lysias/, transcriptions/lysias/ or any other batch file.`
const check = j => `You check one batch of an editor's English prose (with Greek quotations), read by OCR, against the printed pages, for an open-source Ancient Greek reading app. Accuracy of every word, and of every Greek letter, accent and breathing, matters more than speed.

First read transcriptions/drama/INSTRUCTIONS-prose.md: its general parts (to "Each edition's pages"), the section named below, and "Your own files", "Checking", "Before you finish"; follow them exactly.

${common(j)}
Your own folder for crops and scripts: ${scratch}/${j.entry}-${j.file}/

Reply (short): per page the flags answered, what you changed beyond the flags, anything left open, and the checker's last line.`
const review = (j, report) => `You read, independently, a batch of an editor's English prose (with Greek quotations) that was read by OCR and checked by another agent, for an open-source Ancient Greek reading app. Accuracy of every word, and of every Greek letter, accent and breathing, matters more than speed.

First read transcriptions/drama/REVIEW.md (the parts "A prose batch" and "Both") and transcriptions/drama/INSTRUCTIONS-prose.md (its general parts and the section named below), and follow them exactly.

${common(j)}
Your own folder for crops and scripts: ${scratch}/${j.entry}-rev-${j.file}/

The first agent's report, as information only (assume nothing in it is right until you have seen it on the image):
${String(report || '').slice(0, 1500)}

Reply as REVIEW.md says: per page what you changed (or "no change"), the number of unexplained checker remarks, anything left open.`

const out = []
for (let i = 0; i < jobs.length; i += atOnce) {
  const chunk = jobs.slice(i, i + atOnce)
  const res = await pipeline(chunk,
    j => (args.reviewOnly || []).includes(`${j.entry}/${j.file}`)
      ? 'The first agent was stopped before it reported; every flag in the file is answered.'
      : agent(check(j), { label: `${j.entry} ${j.file}`, phase: 'Prose batches', model: 'opus', agentType: 'general-purpose' }),
    (report, j) => args.review
      ? agent(review(j, report), { label: `${j.entry} second reading ${j.file}`, phase: 'Second reading', model: 'opus', agentType: 'general-purpose' })
          .then(r => ({ job: `${j.entry}/${j.file}`, check: String(report || '').slice(0, 400), review: String(r || 'NO REPLY').slice(0, 500) }))
      : { job: `${j.entry}/${j.file}`, check: String(report || 'NO REPLY').slice(0, 700) })
  out.push(...res.map((r, k) => r || { job: `${chunk[k].entry}/${chunk[k].file}`, check: 'AGENT FAILED' }))
}
return out
