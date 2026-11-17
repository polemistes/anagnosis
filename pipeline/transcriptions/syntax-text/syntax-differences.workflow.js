export const meta = {
  name: 'syntax-differences',
  description: "The trees' text: one agent per job file checks, for each word of ours that the trees' text reads otherwise, the kind of difference (elision, nu, spelling, form, word) the rule has set, and corrects it where it is wrong",
  phases: [
    { title: 'Checking', detail: 'one job file per agent, about sixty readings (DIFFERENCES.md)' },
  ],
}
// args: { atOnce: 8, model: 'sonnet', jobs: ['control-01', 'control-02'] }
//
// First the control (control-01, control-02: the Theogony's 62 readings, whose values are set by hand
// in the record; the agents see the rule's values and are not told it is a control). Then, from pipeline/:
//   .venv/bin/python -m anagnosis_pipeline syntax-differences check transcriptions/syntax-text/control-0*.tsv
//   .venv/bin/python -m anagnosis_pipeline syntax-differences measure
// The measurement (values right, and right as to whether a sentence is marked: the rule alone has 53 and
// 53 of 62) decides whether the pass goes on and with which model. Then the 21 job files of the texts:
//   lysias-01 … lysias-05, hermas-01, odyssey-01 … odyssey-12, antigone-01, ajax-01, electra-01
// After each wave: check every file, commit the files, and for each text run
//   .venv/bin/python -m anagnosis_pipeline syntax-text <slug>      (the answers enter here)
// then build into scratch, compare, build, catalog, check (pipeline/PLAN-syntax-text.md).
// The brief is transcriptions/syntax-text/DIFFERENCES.md.
const ROOT = '/home/proteus/koding/anagnosis/pipeline'
const jobs = args.jobs
const atOnce = args.atOnce || 8
const model = args.model || 'sonnet'
const prompt = n => `You check how pairs of Ancient Greek words differ, for an open-source Ancient Greek reading app: for each pair you say whether the two are the same word in the same form (and differ only by an elision, a movable ν or a spelling), the same word in another form, or another word. You need to know Greek accidence well: Attic prose, Homer and tragedy. Care matters more than speed.

First read transcriptions/syntax-text/DIFFERENCES.md and follow it exactly.

Working directory: ${ROOT} (run commands from there).
Your file (edit it in place, save after every ten answers): transcriptions/syntax-text/${n}.tsv
Checker: .venv/bin/python -m anagnosis_pipeline syntax-differences check transcriptions/syntax-text/${n}.tsv
You write your answers after the arrows and nothing else; you translate nothing. Write no other file in the repository, do not run git, never write under /tmp. Do not open anything under texts/, sources/ or anagnosis_pipeline/, any translation, or another job file.

Reply as the brief says.`

const out = []
for (let i = 0; i < jobs.length; i += atOnce) {
  const chunk = jobs.slice(i, i + atOnce)
  const res = await pipeline(chunk,
    n => agent(prompt(n), { label: `differences ${n}`, phase: 'Checking', model, agentType: 'general-purpose' })
      .then(r => ({ job: n, reply: String(r || 'NO REPLY').slice(0, 900) })))
  out.push(...res.map((r, k) => r || { job: chunk[k], reply: 'AGENT FAILED' }))
}
return out
