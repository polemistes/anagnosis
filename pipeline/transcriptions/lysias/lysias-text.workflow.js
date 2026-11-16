export const meta = {
  name: 'lysias-text-batches',
  description: "Lysias (Hude's Oxford text), step 4: one Opus agent per text batch checks the flagged lines and writes the critical apparatus from the crops; checker on every file",
  phases: [
    { title: 'Text batches', detail: 'flags and apparatus, six text pages per agent', model: 'opus' },
  ],
}
// args: { scratch: '/home/proteus/koding/anagnosis/pipeline/build/agent-scratch' (on disk, git-ignored; NOT the session
//         scratchpad, which is a RAM disk), atOnce: 8,
//         batches: [{ id: '01', first: 'p-0019', last: 'p-0024' }, ...] }
// See pipeline/PLAN-lysias.md ("Agents", "Hand-over"). The agents' brief is INSTRUCTIONS.md in this folder;
// this script only hands each agent its batch.
const ROOT = '/home/proteus/koding/anagnosis/pipeline'
const SLUG = 'lysias'
const SCAN = 'orationesrecogno00lysi'
const { scratch, batches } = args
const atOnce = args.atOnce || 8
const prompt = b => `You check one batch of the Greek text of Lysias's speeches against the printed edition (Hude's Oxford text, 1912) and write its critical apparatus, for an open-source Ancient Greek reading app. Accuracy of every Greek letter, accent, breathing and siglum matters more than speed.

Working directory: ${ROOT} (run commands from there).
First read transcriptions/${SLUG}/INSTRUCTIONS.md, all of it, and follow it exactly.

Your batch file (edit it in place, save after each page): transcriptions/${SLUG}/batch-${b.id}.md (pages ${b.first} to ${b.last})
Check sheets and crops: build/hude-pages/${SLUG}/ (p-NNNN.md, p-NNNN-lines.png, p-NNNN-app-l.png, p-NNNN-app-r.png)
Whole pages, only when a flag needs one: build/drama-scans/${SCAN}/pages/leaf_NNNN.png
Your own folder for crops and scripts: ${scratch}/${SLUG}-batch-${b.id}/
Checker: .venv/bin/python -m anagnosis_pipeline check-lysias-batch transcriptions/${SLUG}/batch-${b.id}.md

Write no other file in the repository and do not run git. Keep your scratch folder small (crops only as large as you need, deleted when you are done with them); never write under /tmp. Do not open texts/${SLUG}/ or any other batch file.

Reply as "Before you finish" in the brief says: for each page the flags checked, what you changed, the number of apparatus items, and the checker's last line.`

const out = []
for (let i = 0; i < batches.length; i += atOnce) {
  const chunk = batches.slice(i, i + atOnce)
  const res = await parallel(chunk.map(b => () =>
    agent(prompt(b), { label: `${SLUG} batch-${b.id} ${b.first}–${b.last}`, phase: 'Text batches', model: 'opus', agentType: 'general-purpose' })
      .then(r => ({ batch: b.id, reply: String(r || 'NO REPLY').slice(0, 700) }))))
  out.push(...res.map((r, k) => r || { batch: chunk[k].id, reply: 'AGENT FAILED' }))
  log(`${SLUG}: batches ${chunk[0].id}–${chunk[chunk.length - 1].id} back`)
}
return out
