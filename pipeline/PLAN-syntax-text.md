# The text the syntax trees were made on: the record in the texts on sale and the free texts

Brief for whoever continues this work. Read it with `texts/README.md` ("`syntax-text.tsv`") and
the Theogony's plan (`pipeline/PLAN-theogony.md`, "the trees' text"), where the record was made
first.

## What it is, in plain words

The syntax trees shown in the reader were not drawn on the editions we print. They come from
treebanks, and a treebank was made on the text its makers had: usually the Perseus Digital
Library's text of the work, which is another edition than ours and differs from it here and
there (a word in another form, another word, a word more or less). The principle the author set
on 2026-11-17: **the tree is shown with the words it was made for.** So each text records, word
by word, where our word is not simply the trees' word, and the reader shows a sentence that
really differs with both texts and the differing words marked. A sentence that does not really
differ shows nothing.

The author's order of 2026-11-17: the record goes into **the texts on sale and the free texts,
and only those**: on sale Antigone, Ajax, Electra, the New Testament, the Symposium, the
Gorgias, the Odyssey; free the Theogony (done first), Lysias, the Shepherd of Hermas. Nothing
else in these texts may change.

## How it is made without making the text again

These texts are on sale or about to be offered, and running a text's import or merge again
could change other things (a commentary, a translation). So the record is not made by the
merges. One step, `syntax_text.record_from_files` (command `syntax-text <slug>`, `--dry` to
count only), works from the text's files as they stand and from the trees:

1. A word that already has its tree word keeps it. It is recorded as a **unit** where it joins
   several tree words or carries one of the two words the trees write for it (κἀγὼ: "κ-" and
   "ἀγὼ"), as a **reading** where the tree word has other letters or another iota subscript.
2. A word without a tree word is looked at between its neighbours that have one, against the
   tree words there that no word of ours uses: several of ours that are one tree word, or one
   of ours that is two tree words, become a unit; one word in two forms becomes a reading;
   three or more words that stand elsewhere among the tree words left over are tied there.
3. What is left is **absent** from the trees' text and gets the sentence it stands in, so that
   pressing it opens that sentence's tree (the rule made for the Theogony; a passage cut off by
   stops on both sides, such as a hypothesis the trees' text has not, gets none).
4. The tree words no word of ours uses are **unprinted**.

Only these things change in a text: `syntax-text.tsv` (new), one header line of grc.txt, the
sentence / word id / relation / head of the words concerned in tokens.tsv, the nodes a word of
ours now carries in syntax-nodes.tsv, and the analysis of a word that wore the analysis of a
tree word in another form (below). Each text is built into a scratch folder first
(`build --only X --out pipeline/build/agent-scratch/record/out`) and compared with the installed
database table by table (`pipeline/build/agent-scratch/record/compare.py`, a scratch script).

**A word's own analysis.** An iota subscript is a letter of the form. Where the trees' text
writes ναυμαχία and ours ναυμαχίᾳ, our word had taken over the trees' analysis (a nominative).
Such a word gets the analyser's reading of exactly our spelling under the trees' lemma; where
the analyser has none, the analysis is set by hand in `syntax_text.OWN_ANALYSES`, each with its
reason (also the few readings in other letters that had been left wearing the trees' analysis).
Where this changes a lemma, the text's table of short definitions follows (a lemma no word has
any more goes, the new one comes): that is the one change outside the four tables named by the
author, and it is listed per text below.

**Run again, it gives the same.** A merge that is run again (Lysias's) calls the step at its
end, so the files come out as they are now. For the texts whose import cannot be run again
without changing other things, the step is the only thing that is run.

## Confirming the trees' text

For each text the trees' text is established from the sources, not assumed: (a) what the
treebank file says of itself (the AGDT header names the edition), (b) the tree words compared in
order with the Perseus Greek of the work (`pipeline/sources/corpora/canonical-greekLit.tar.gz`)
and with our text: the trees were made on the text they follow more closely, (c) a sample of
the readings looked up in the Perseus file. The scratch scripts are
`pipeline/build/agent-scratch/record/confirm*.py`.

## The kinds of difference, and the checking pass

`difference` of a reading: `elision`, `nu`, `spelling` (the same word in the same form written
otherwise), `form` (the same word in another form), `word` (another word). Only `form` and `word`
make the reader mark a sentence. The value is set by rule (`syntax_text.differences`; in this
step helped by the analyser: what it knows of our spelling under the trees' lemma). In the
Theogony the rule had 52 of 62 right. So every reading is checked by an agent
(`syntax_differences.py`, the brief `pipeline/transcriptions/syntax-text/DIFFERENCES.md`, the
workflow `pipeline/transcriptions/syntax-text/syntax-differences.workflow.js`):

* `syntax-differences jobs <slug> ...` writes `pipeline/transcriptions/syntax-text/<slug>-NN.tsv`,
  sixty readings to a file, each with its sentence, both words with their analyses and the
  rule's value; `syntax-differences jobs theogony` writes the control, `control-01.tsv` and
  `control-02.tsv`: the Theogony's 62 readings with the rule's values, as if nothing were known
  of them (ten of them were set by hand; the agents are not told which, nor that it is a control);
* `syntax-differences check FILE...` is the agent's checker; `syntax-differences measure` sets
  the control's answers against the Theogony's record: how many values the rule had right, how
  many the agents have, and how many as to the one thing that shows (marked or not);
* the answers enter through `syntax_differences.answers(slug)`: a job file counts when every
  reading is answered, the checker finds nothing ill formed and the file is committed; the
  value is applied where both words are still the ones it was given for. Run `syntax-text <slug>`
  (or the text's merge), build into scratch, compare, build, catalog, check, commit.

`same_construction` is not judged any more (the author, 2026-11-17: a reading is real by its
`difference`); the column stays and is empty in these texts.

## The texts

(one section per text: the trees' text as established, the counts, what else would have
changed, the version)

### Lysias (free) — done 2026-11-17, version `896cbeb066d4c9b8`

**The trees' text: the Perseus Digital Library's text of the speeches (W. R. M. Lamb's Loeb
edition, 1930).** Established so: the AGDT files of speeches 1, 14, 15, 23 name that edition in
their headers. GLAUx's files (26 automatic speeches, and 24 by hand from the Pedalion trees)
name no edition; their words, compared in order with Perseus's Greek and with Hude's, follow
Perseus's (43,547 tree words: 732 not in Perseus's text at their place, mostly the words the
trees write in two, against 1,001 not in ours), ten readings looked up all have the trees' word
in Perseus's file, and the trees share Perseus's own misprints (6.20 τούτω for τούτῳ). Speeches
12, 13, 19 have no trees and no rows.

| kind | rows | |
|---|---|---|
| unit | 367 | 324 words the merge had joined already (οὔτε = οὔ τε), 26 joined or recognised by this step (μήτε, κἀγώ, τἀληθῆ), 17 words of 8 places where ours prints two for the trees' one (καίτοι γε, ὅ τι) |
| reading | 264 | by rule: elision 12, nu 9, spelling 67, form 91, word 85 (to be checked by the pass) |
| absent | 493 | 195 with their sentence; 298 without: the hypotheses of 32, 33, 34 (283 words) and 6.2, which the trees' text has not |
| unprinted | 75 | 69 single words, 6 in passages; among them the headings Νόμος, Μάρτυρες that the hand-made trees count as words |

**295 of 2,056 sentences really differ** (by the rule's values; the pass will move this).
Own analyses: 39 words (33 by the analyser, where the trees' word lacks or has an iota
subscript: βίᾳ a dative, not the trees' nominative βία; the rest in `OWN_ANALYSES`, among them
24.13 ἐλεήσαντας, which wore the analysis of the trees' πάντας, and 33.7 καινομένην, Hude's own
conjecture, which wore the καίω of the trees' καομένην).

Compared with the installed database: `tokens` (211 words given a sentence only; 34 newly tied
to a node; 9 second halves; 39 analyses), `sentence_nodes` (60 nodes fewer: now carried by
words), `syntax_text_words` (new, 1,199 rows), `meta` (two keys), and `short_definitions`: four
lemmas no word has any more (ἀχεύω, ἐμπελάζω, ἐσθέω, ἦδος: the trees' misreadings) go and καίνω
comes. Nothing else. Lysias's merge can be run again and now ends with this step; run again it
gave the very same files.

## Progress

- [x] The step, its command, tests (`tests/test_syntax_text_files.py`), the checking pass's module
- [x] Lysias
- [ ] The Shepherd of Hermas
- [ ] The Odyssey
- [ ] The Gorgias
- [ ] The Symposium
- [ ] Antigone, Ajax, Electra
- [ ] The New Testament
- [ ] The checking pass prepared (job files, control, brief, workflow); run by the main session

## Decisions

(append dated entries)
