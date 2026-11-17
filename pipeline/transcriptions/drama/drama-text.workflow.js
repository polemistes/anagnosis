export const meta = {
  name: 'drama-text-batches',
  description: 'Drama route, step 4: one Opus agent per text batch checks the flagged verses and writes the critical apparatus from the crops; checker on every file',
  phases: [
    { title: 'Text batches', detail: 'flags and apparatus, six text pages per agent', model: 'opus' },
  ],
}
// args: { play: 'trachiniae', scan: 'sophocles05soph', scratch: '/home/proteus/koding/anagnosis/pipeline/build/agent-scratch' (on disk, git-ignored; NOT the session scratchpad, which is a RAM disk), atOnce: 8,
//         edition: "Jebb's Sophocles", batches: [{ id: '01', first: 'p-0080', last: 'p-0090' }, ...] }
// See pipeline/PLAN-drama.md ("Agents") and pipeline/PLAN-sophocles.md. The agents' brief is
// INSTRUCTIONS-text.md in this folder; this script only hands each agent its batch.
const ROOT = '/home/proteus/koding/anagnosis/pipeline'
const { play, scan, scratch, edition, batches } = args
const atOnce = args.atOnce || 8
const prompt = b => `You check one batch of the Greek text of a play against the printed edition and write its critical apparatus, for an open-source Ancient Greek reading app. Accuracy of every Greek letter, accent, breathing and siglum matters more than speed.

Working directory: ${ROOT} (run commands from there).
First read transcriptions/drama/INSTRUCTIONS-text.md, all of it, and follow it exactly. Your edition's section there is "${edition}".

Play: ${play}
Your batch file (edit it in place, save after each page): transcriptions/drama/${play}/batch-${b.id}.md (pages ${b.first} to ${b.last})
Check sheets and crops: build/drama-pages/${play}/ (p-NNNN.md, p-NNNN-lines.png, p-NNNN-app-l.png, -app-r.png, -app2-l.png, -app2-r.png)
Whole pages, only when a flag needs one: build/drama-scans/${scan}/pages/leaf_NNNN.png
Your own folder for crops and scripts: ${scratch}/${play}-batch-${b.id}/
Checker: .venv/bin/python -m anagnosis_pipeline check-drama-batch ${play} transcriptions/drama/${play}/batch-${b.id}.md

Write no other file in the repository and do not run git. Keep your scratch folder small (crops only as large as you need). Do not open anything under transcriptions/sophocles/ (an independent reading of these pages is kept there for comparison and must stay independent), nor texts/${play}/.
${args.extra ? '\n' + args.extra + '\n' : ''}
Reply as "Before you finish" in the brief says: for each page the flags checked, what you changed, the number of apparatus items, and the checker's last line.`

const out = []
for (let i = 0; i < batches.length; i += atOnce) {
  const chunk = batches.slice(i, i + atOnce)
  const res = await parallel(chunk.map(b => () =>
    agent(prompt(b), { label: `${play} batch-${b.id} ${b.first}–${b.last}`, phase: 'Text batches', model: 'opus', agentType: 'general-purpose' })
      .then(r => ({ batch: b.id, reply: String(r || 'NO REPLY').slice(0, 700) }))))
  out.push(...res.map((r, k) => r || { batch: chunk[k].id, reply: 'AGENT FAILED' }))
  log(`${play}: batches ${chunk[0].id}–${chunk[chunk.length - 1].id} back`)
}
return out
