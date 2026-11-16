export const meta = {
  name: 'lysias-gillies-align',
  description: "Lysias: Gillies's translation (1778) of six speeches laid beside the Greek: one Opus agent per speech writes the section marks at his paragraphs, a second checks the places",
  phases: [
    { title: 'Placing', detail: 'one speech per agent: the section mark at each paragraph (GILLIES-ALIGN.md)', model: 'opus' },
    { title: 'Second look', detail: 'an independent check of the places against the Greek', model: 'opus' },
  ],
}
// args: { atOnce: 6, review: true, speeches: [1, 3, 4, 21, 26, 34] }
// Before this run: the speech's transcription (transcriptions/drama/lysias-gillies-NN/intro-*.md) has had
// its check and second reading by lysias-prose.workflow.js, has no flag left, and is COMMITTED: the
// checker compares the marked file with HEAD and reports any change that is not a mark.
// The brief is transcriptions/lysias/GILLIES-ALIGN.md. See pipeline/PLAN-lysias.md ("Gillies", "Hand-over").
const ROOT = '/home/proteus/koding/anagnosis/pipeline'
const speeches = args.speeches
const atOnce = args.atOnce || 6
const nn = n => String(n).padStart(2, '0')
const common = n => `Working directory: ${ROOT} (run commands from there).
Your speech: ${n}. Its file(s), edited in place (save after each page): transcriptions/drama/lysias-gillies-${nn(n)}/intro-*.md
The Greek (read only): ../texts/lysias/grc.txt, the lines numbered ${n}.1, ${n}.2 …
Checker: .venv/bin/python -m anagnosis_pipeline check-gillies-marks ${n}
You write section marks and remarks under "--- notes", nothing else: not one word of the translation is changed, and nothing is translated by you. Write no other file in the repository, do not run git, never write under /tmp. Do not open any other translation of Lysias (texts/lysias/eng-1898.txt included) or any other batch file.`
const place = n => `You lay an eighteenth-century English translation of a speech of Lysias beside its Greek text, for an open-source Ancient Greek reading app: you find where each paragraph of the translation begins in the Greek and write the section's number there. You need to read Attic Greek prose. Care matters more than speed.

First read transcriptions/lysias/GILLIES-ALIGN.md and follow it exactly.

${common(n)}

Reply as the brief says.`
const second = (n, report) => `You check, independently, the places at which another agent has laid an eighteenth-century English translation of a speech of Lysias beside its Greek text, for an open-source Ancient Greek reading app. You need to read Attic Greek prose. Care matters more than speed.

First read transcriptions/lysias/GILLIES-ALIGN.md and follow it exactly. The marks (§N) are already in the file: for each one read the Greek section and the English after the mark, and move, remove or add a mark where the brief's rules ask for it. The same single rule binds you: marks and remarks only.

${common(n)}

The first agent's report, as information only:
${String(report || '').slice(0, 1200)}

Reply (short): the marks you moved, removed or added, with the reason in a few words each; what is still doubtful; the checker's last line.`

const out = []
for (let i = 0; i < speeches.length; i += atOnce) {
  const chunk = speeches.slice(i, i + atOnce)
  const res = await pipeline(chunk,
    n => agent(place(n), { label: `Gillies ${n}: placing`, phase: 'Placing', model: 'opus', agentType: 'general-purpose' }),
    (report, n) => args.review
      ? agent(second(n, report), { label: `Gillies ${n}: second look`, phase: 'Second look', model: 'opus', agentType: 'general-purpose' })
          .then(r => ({ speech: n, placing: String(report || '').slice(0, 500), second: String(r || 'NO REPLY').slice(0, 600) }))
      : { speech: n, placing: String(report || 'NO REPLY').slice(0, 800) })
  out.push(...res.map((r, k) => r || { speech: chunk[k], placing: 'AGENT FAILED' }))
}
return out
