export const meta = {
  name: 'drama-prose-batches',
  description: 'Drama route, steps 6-7: one Opus agent per prose batch (notes, introduction, appendix) checks the flagged words against the crops; then, if asked, an independent review of each batch',
  phases: [
    { title: 'Prose batches', detail: 'flags against the crops, eight pages per agent', model: 'opus' },
    { title: 'Review', detail: 'an independent reading of each batch against the page images (REVIEW.md)', model: 'opus' },
  ],
}
// scratch = /home/proteus/koding/anagnosis/pipeline/build/agent-scratch (on disk, git-ignored; NOT the
// session scratchpad, which is a RAM disk and is emptied at a restart)
// args: { play, scratch, atOnce: 12, review: true,
//         section: "Jebb's Sophocles: the Appendix and the chapters before the text",
//         files: ['intro-01', 'appendix-01', 'appendix-02', 'appendix-03'] }
// The batch files are made by `drama-prose <play> <kind> draft`; the brief is INSTRUCTIONS-prose.md.
const ROOT = '/home/proteus/koding/anagnosis/pipeline'
const { play, scratch, files } = args
const atOnce = args.atOnce || 12
const kindOf = f => f.replace(/-\d+$/, '')
const common = f => `Working directory: ${ROOT} (run commands from there).
Play: ${play}${args.section ? ` (your section of the brief: "${args.section}")` : ''}
Your batch file (edit it in place, save after each page): transcriptions/drama/${play}/${f}.md
Crops and whole pages: build/drama-prose/${play}/ (p-NNNN-flags.png, p-NNNN-col-l.png, -col-r.png, pages/leaf_NNNN.png; FLAG_KINDS.md explains the flags)
Checker: .venv/bin/python -m anagnosis_pipeline check-drama-prose ${play} transcriptions/drama/${play}/${f}.md
Write no other file in the repository and do not run git. Keep your scratch folder small (crops only as large as you need). Do not open anything under transcriptions/sophocles/ or texts/${play}/.`
const check = f => `You check one batch of an editor's English prose (with Greek quotations), read by OCR, against the printed pages, for an open-source Ancient Greek reading app. Accuracy of every word, and of every Greek letter, accent and breathing, matters more than speed.

First read transcriptions/drama/INSTRUCTIONS-prose.md, all of it, and follow it exactly.

${common(f)}
Your own folder for crops and scripts: ${scratch}/${play}-${f}/

Reply (short): per page the flags answered, what you changed beyond the flags, anything left open, and the checker's last line.`
const review = (f, report) => `You review, independently, a batch of an editor's English prose (with Greek quotations) that was read by OCR and checked by another agent, for an open-source Ancient Greek reading app. Accuracy of every word, and of every Greek letter, accent and breathing, matters more than speed.

First read transcriptions/drama/REVIEW.md (the parts "A prose batch" and "Both") and transcriptions/drama/INSTRUCTIONS-prose.md, all of it, and follow them exactly.

${common(f)}
Your own folder for crops and scripts: ${scratch}/${play}-rev-${f}/

The first agent's report, as information only (assume nothing in it is right until you have seen it on the image):
${String(report || '').slice(0, 1500)}

Reply as REVIEW.md says: per page what you changed (or "no change"), the number of unexplained checker remarks, anything left open.`

const out = []
for (let i = 0; i < files.length; i += atOnce) {
  const chunk = files.slice(i, i + atOnce)
  const res = await pipeline(chunk,
    // args.reviewOnly: files whose flags are all answered already (a checking agent was stopped
    // before it reported): they go straight to the review
    f => (args.reviewOnly || []).includes(f)
      ? 'The first agent was stopped before it reported; every flag in the file is answered.'
      : agent(check(f), { label: `${play} ${f}`, phase: 'Prose batches', model: 'opus', agentType: 'general-purpose' }),
    (report, f) => args.review
      ? agent(review(f, report), { label: `${play} review ${f}`, phase: 'Review', model: 'opus', agentType: 'general-purpose' })
          .then(r => ({ file: f, check: String(report || '').slice(0, 400), review: String(r || 'NO REPLY').slice(0, 500) }))
      : { file: f, check: String(report || 'NO REPLY').slice(0, 700) })
  out.push(...res.map((r, k) => r || { file: chunk[k], check: 'AGENT FAILED' }))
}
return out
