export const meta = {
  name: 'lysias-analyses',
  description: 'Lysias: the word analyses of the speeches without trees (12, 13, 19): one agent per job chooses, for each word whose spelling allows several readings, the reading that is right in its sentence',
  phases: [
    { title: 'Choosing', detail: 'one job file per agent, about 160 words to decide (ANALYSES.md)' },
  ],
}
// args: { atOnce: 8, model: 'sonnet', jobs: ['91', '92'] }
// First the two control jobs (91, 92: stretches of speeches 1 and 24, which have hand-made trees, set as
// if they had none; the agents are not told). Then, from pipeline/:
//   .venv/bin/python -m anagnosis_pipeline lysias-analyses check transcriptions/lysias/analyses/job-9*.tsv
//   .venv/bin/python -m anagnosis_pipeline lysias-analyses measure
// The measurement decides whether the pass goes on to jobs 01-28 and with which model (PLAN-lysias.md,
// "The words without trees"). The brief is transcriptions/lysias/ANALYSES.md.
const ROOT = '/home/proteus/koding/anagnosis/pipeline'
const jobs = args.jobs
const atOnce = args.atOnce || 8
const model = args.model || 'sonnet'
const prompt = n => `You decide the grammatical analysis of Greek words in their sentences, in a speech of the Attic orator Lysias, for an open-source Ancient Greek reading app. You need to read Attic Greek prose with attention to its syntax. Care matters more than speed.

First read transcriptions/lysias/ANALYSES.md and follow it exactly.

Working directory: ${ROOT} (run commands from there).
Your file (edit it in place, save after each section): transcriptions/lysias/analyses/job-${n}.tsv
Checker: .venv/bin/python -m anagnosis_pipeline lysias-analyses check transcriptions/lysias/analyses/job-${n}.tsv
You write your answers after the arrows and nothing else; you translate nothing. Write no other file in the repository, do not run git, never write under /tmp. Do not open texts/lysias/tokens.tsv, texts/lysias/syntax-nodes.tsv, anything under sources/, any translation of Lysias, or another job file.

Reply as the brief says.`

const out = []
for (let i = 0; i < jobs.length; i += atOnce) {
  const chunk = jobs.slice(i, i + atOnce)
  const res = await pipeline(chunk,
    n => agent(prompt(n), { label: `analyses job ${n}`, phase: 'Choosing', model, agentType: 'general-purpose' })
      .then(r => ({ job: n, reply: String(r || 'NO REPLY').slice(0, 900) })))
  out.push(...res.map((r, k) => r || { job: chunk[k], reply: 'AGENT FAILED' }))
}
return out
