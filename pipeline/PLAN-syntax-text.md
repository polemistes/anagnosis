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
Theogony the rule had 53 of 62 right (and 53 as to the one thing that shows: marked or not). So every reading is checked by an agent
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

### The Shepherd of Hermas (free) — done 2026-11-17, version `a45c12c26fcfe14d`

**The trees' text: the First1KGreek project's digital text of this same edition (Lake's Loeb).**
Established so: the file (`pipeline/sources/hermas/tlg1419.tlg001.1st1K-grc1.xml`) names Lake's
Apostolic Fathers, vol. 2, as its source; GLAUx's words follow it (27,339 tree words: 147 not in
it at their place, the words written in two), and five of the six words in which the trees
differ from ours are that file's own misprints (ἀσύμποφα, ἀκοκριθεῖσαι, μενανοήσωσι,
μετανήσατε, αὐτῇς; the sixth, παρθένον for παρθένων, is in the trees). So this is not another
edition: the two differ only where the digital copy misprints.

| kind | rows | |
|---|---|---|
| unit | 56 | the words GLAUx writes in two (οὔτε, οὐδέ, μηδέ, εἴτε); the merge had joined them |
| reading | 6 | by rule: spelling 2, form 2, word 2 (the pass will set them: a misprint that is no word is a spelling) |
| absent | 0 | |
| unprinted | 145 | the Greek of the end of the book, which Lake prints in Latin: in 16 sentences none of our words stands in, so never shown |

**4 of 2,086 sentences really differ** by the rule's values. Own analysis: one word (14.1.10
αὐτῆς). Compared with the installed database: `tokens` (that one tag), `meta` (two keys),
`syntax_text_words` (new, 207 rows); everything else the same. The merge (`merge-hermas`) gives
its present files again and now ends with the step.

For the author: whether six misprints deserve the sentence in the description and the credits'
line (`syntax_text`); the record itself is needed either way for the word that had a wrong tag
and so that the tree shows what the parser read.

### The Odyssey (on sale) — done 2026-11-17, version `a6c82a64772c8ecc`

**The trees' text: the Perseus Digital Library's text of the poem (A. T. Murray's Loeb edition,
1919).** Established so: the treebank file (`tlg0012.tlg002.perseus-grc1.tb.xml`, AGDT 2.1)
names that edition in its header; its words, compared book by book with Perseus's Greek and
with Allen's, follow Perseus's (87,625 tree words: 1,311 not in Perseus's text at their place,
nearly all the words the treebank writes in two, οὐ δέ; 2,075 not in ours).

| kind | rows | |
|---|---|---|
| unit | 680 | 648 words that are two tree words (οὐδέ, οὔτε, μηδέ; the merge had joined 643), 32 words of 16 places where ours prints two for the trees' one (ὅ τι, ὥς τε, ἐπεὶ δή) |
| reading | 723 | by rule: nu 137, elision 83, spelling 294, form 85, word 124 (to be checked by the pass) |
| absent | 233 | 56 with their sentence; 177 without: the verses the treebank has no trees for (9.522–535, 21.109–117 and a few single verses) |
| unprinted | 75 | all single words |

**260 of 6,721 sentences really differ** by the rule's values. Own analyses: 9 words (8 by the
analyser, e.g. 3.128 νόῳ a dative where the trees' νόω was tagged a genitive; 5.243 ἤνυτο, from
ἀνύω, which wore the αἴνυμαι of the trees' ᾔνυτο).

Compared with the installed database: `tokens` (168 words: 83 given a sentence only; 60 newly
tied to a node, among them the last verses of books 2, 3, 4, 17 and 20, which the treebank cites
by the book alone and the alignment had lost; 16 second halves; 9 analyses), `sentence_nodes`
(65 nodes fewer: now carried by words), `syntax_text_words` (new, 1,711 rows), `meta` (two
keys). Nothing else; the short definitions are the same.

**What else would have changed, and how it was avoided.** The Odyssey's merge (`merge-odyssey`)
run again would take out the header line `# pronunciation: homeric` of grc.txt and undo two
corrections made by hand in the apparatus (a breve written `^` at two items). So the merge was
not run on the text: the step alone was (`syntax-text odyssey`). The merge now ends with the
step too, and run into a scratch folder it gives the same tokens.tsv, syntax-nodes.tsv and
syntax-text.tsv as the step alone; whoever runs it on the text must keep those three hand-made
things.

### The Gorgias (on sale) — done 2026-11-17, version `20a3f7613229dcbc`

**The trees' text: the Perseus Digital Library's text of this same edition (Burnet), without
the words Burnet brackets as not Plato's.** Established so: Perseus's file names Burnet's
Platonis Opera III (1903) as its source and marks the bracketed words as deletions (`<del>`);
GLAUx's words (`glaux/0059-023.xml`) are that text word for word without the deleted words
(26,443 tree words; the only tree words not in Perseus's text at their place are the 196 pairs
GLAUx writes in two), and our text is Perseus's word for word with them. No word is read
otherwise.

| kind | rows | |
|---|---|---|
| unit | 196 | the words GLAUx writes in two (οὔτε, οὐδέ, μήτε, εἴτε, ἐάντε); the merge had joined them |
| reading | 0 | |
| absent | 32 | Burnet's bracketed words in 17 places (451b4 [γνῶσις], 470a9 [τὸ μέγα δύνασθαι], …), each with its sentence |
| unprinted | 0 | GLAUx's crasis marks ("τα-" before ταὐτόν) are its device, no words of the text |

**16 of 2,113 sentences really differ** (those with bracketed words; no classification is
needed). Compared with the installed database: `tokens` (the 32 words: a sentence each),
`meta` (two keys), `syntax_text_words` (new, 228 rows). Nothing else.

**What else would have changed, and how it was avoided.** The Gorgias's merge run again (into
a scratch folder) gives the same tokens, but six lines of Lodge's commentary come out otherwise
(`αυ[?]τό` where the text file now has `αυ<*>τό`: later corrections that the merge does not
make). So the merge was not run on the text; the step alone was. The merge now ends with the
step and gives the same tokens.tsv and syntax-text.tsv.

### The Symposium (on sale) — no record; nothing changed, version as it was

**The trees were made on the very text printed.** Established so: Perseus's file names Burnet's
Platonis Opera II as its source and has no deleted words; GLAUx's words (`glaux/0059-011.xml`)
are our text word for word (17,495 tree words against our 17,348: the difference is the 147
words GLAUx writes in two, which the merge had joined). The dry run of the step finds no
reading, no absent word and no unprinted word. So there is no `syntax-text.tsv`, no
`syntax_text` key and no sentence in the description, and the Symposium is not entered in
`FROM_FILES`.

(The Symposium's merge run again into a scratch folder would change other things: the relation
and head of 66 joined words, three lines of Bury's commentary and three of the introduction.
It was not run on the text. Its end calls the step, which does nothing for a text not entered.)

### Ajax and Electra (on sale) — done 2026-11-17, versions `14b31d994d660e82` and `ed9f0c9a4a7e2978`

**The trees' text: the Perseus Digital Library's text of each play (F. Storr's Loeb edition,
1913).** Established so: the AGDT files (`tlg0011.tlg003.perseus-grc1.tb.xml`,
`tlg0011.tlg005.perseus-grc2.tb.xml`) name that edition in their headers; the tree words
follow Perseus's Storr file more closely than Jebb's text (Ajax: 74 tree words not in it at
their place against 117 not in ours; Electra 141 against 191; most of both are the words written
in two); and of fifteen readings looked up, the trees' word is in Storr's file every time
(τίσει, δόρει, εἵνεκα, ἐκόμπεις; αἰεὶ, κλεινὸν, προπίτνω) and ours mostly is not.

| kind | Ajax | Electra | |
|---|---|---|---|
| unit | 35 | 69 | words that are two tree words (οὐδέ, οὔτε, μηδέ); in the Electra two newly joined at 138 (ἀνστάσεις, οὔτε) |
| reading | 45 | 44 | by rule: Ajax elision 5, nu 6, spelling 14, form 3, word 17; Electra elision 3, nu 2, spelling 21, form 5, word 13 |
| absent | 2 | 9 | all with their sentence (Electra 691, a verse the trees' text has not, is 5 of them) |
| unprinted | 3 | 10 | single words |

**Sentences that really differ: Ajax 20 of 785, Electra 25 of 929** by the rule's values. Own
analyses, where the importer had left a word wearing the analysis of the trees' word: Ajax four
(178 ἐλαφαβολίαις a dative plural, 1184 μεληθεὶς a participle, 1230 ἐφώνεις from φωνέω, not
the trees' κομπέω, 1404 ταχύνετε a present), Electra one (1486 τοῦ, the article, not the trees'
οὐ).

Compared with the installed databases: Ajax `tokens` (9 words: 5 given a sentence, 4 analyses),
`meta`, `syntax_text_words` (new, 85 rows); Electra `tokens` (16 words: 13 given a sentence
only, 2 newly joined, 1 analysis), `sentence_nodes` (4 nodes fewer: now carried by the two
words), `meta`, `syntax_text_words` (new, 132 rows). Nothing else: no commentary, translation
or short definition changed.

**What else would have changed, and how it was avoided.** The Perseus importer of these plays
(`import-sophocles`) was not run: its pending fixes would change the commentaries, which is a
decision the author has not taken. The step alone was run. The importer now calls the step
after it writes its tokens, so a later import leaves the record in step.

### Antigone (on sale) — done 2026-11-17, version `2f00f3809d86f0a9`

**The trees' text: the Perseus Digital Library's text of the play as the treebank's annotators
had it.** The treebank's header names Storr's Loeb edition (1912), and that could not be
confirmed: Perseus's file under that name is, in the words where editions part, the same text
as ours (ἀφαγνίσαι 196, κἀς 212, πᾶσαι 1136), and the trees agree with neither in a handful of
words. Compared in order, the tree words differ from our text in seven words and one more:

| verse | ours | the trees |
|---|---|---|
| 196 | ἀφαγνίσαι | ἐφαγνίσαι (L's reading, the lemma of Jebb's apparatus) |
| 212 | κἀς | καὶ |
| 281 | ʼφευρεθῇς | φευρεθῇς |
| 424 | ἐς | ὡς |
| 591 | βρέμουσι δʼ | βρέμουσιν (the δʼ has a node made by hand in the importer: recorded as absent, node kept) |
| 803 | δάκρυ | δάκρυων |
| 1136 | πᾶσαι | πασᾶν (L's reading in Jebb's apparatus) |

unit 65 (words that are two tree words), reading 7 (by rule: nu 1, spelling 1, form 2, word 3),
absent 1, unprinted 4 (verse 116 a second time, as a sentence of its own that none of our
words stands in: never shown). **6 of 686 sentences really differ.** No token changed: compared
with the installed database only `meta` and the new table `syntax_text_words` (77 rows) differ.
The importer (`import`) was not run.

**Stopped on, for the author.** Four of these look like faults of our text (which is Perseus's
file of Jebb), not readings of Jebb: 424 ἐς ὅταν (ὡς ὅταν is the Greek), 803 δάκρυ, 1136 πᾶσαι
(the apparatus quotes L with πασᾶν and reports no change), and perhaps 196. They need a look at
Jebb's page. Until then the words keep the analyses they wear (the trees': 803 δάκρυ a genitive
plural, 1136 πᾶσαι a genitive plural, 424 ἐς as ὡς, 196 under ἐφαγνίζω), which fit the trees'
words; if Jebb does print ours, they want their own in `OWN_ANALYSES`. Nothing of the text was
changed.

### The New Testament (on sale) — no record; nothing changed, version as it was

**The trees were made on the very text printed.** Established so: MACULA Greek's trees are its
`SBLGNT/lowfat` files, the annotation of the SBL edition, and its README names the SBLGNT
(the commit of July 2023) as its text; its words, set beside our tokens one by one, are the
same 137,741 words in the same order, and one differs in letters: John 8:5, ours Μωσῆς, MACULA
Μωϋσῆς, a spelling of the name (the elision mark, which MACULA keeps apart from the word, is no
difference). Every word of ours has its node. So there is no `syntax-text.tsv`, no `syntax_text`
key and no sentence in the description: a single spelling would never be marked, and a credits'
line for it would mislead. `import-nt` was not run and does not call the step.

## The checking pass: what is prepared (2026-11-17)

Nothing is started; the main session runs it.

* **Job files** in `pipeline/transcriptions/syntax-text/`: 1,089 readings in 21 files:
  `lysias-01` … `lysias-05` (264), `hermas-01` (6), `odyssey-01` … `odyssey-12` (723),
  `antigone-01` (7), `ajax-01` (45), `electra-01` (44). The Gorgias has no readings. Each
  reading stands in ten words of our text before it and eight after, with both words, both
  analyses in letters and in words, and the rule's value.
* **The control**: `control-01`, `control-02`: the Theogony's 62 readings (31 each) with the
  values the rule alone gives; in the record ten of them are set by hand and nine of those
  differ from the rule. `syntax-differences measure` gives, for the rule and for the agents, the
  values right out of 62 and how many are right as to whether a sentence is marked. The rule
  alone: 53 and 53. A pass worth running should come near 60.
* **The brief**: `DIFFERENCES.md` (the five kinds with examples from these texts; the line
  between spelling and form; the iota subscript; misprints of the trees' text; crasis).
  **The checker**: `syntax-differences check FILE...` (every line answered with one of the five
  words or `?` and a reason; a changed value needs a reason; nothing else changed, against the
  committed file). **The workflow**: `syntax-differences.workflow.js`, args
  `{ atOnce: 8, model: 'sonnet', jobs: ['control-01', 'control-02'] }` first, then the 21 jobs.
* **How the answers enter**: commit the checked files; for each text `syntax-text <slug>` (for
  Lysias and the Shepherd the merge does the same); build into scratch and compare (only
  `syntax_text_words.difference` may differ); `build --only <slug>`, `check`, commit. The
  versions of the six texts with readings will change once more then.


## Progress

- [x] The step, its command, tests (`tests/test_syntax_text_files.py`), the checking pass's module
- [x] Lysias
- [x] The Shepherd of Hermas
- [x] The Odyssey
- [x] The Gorgias
- [x] The Symposium (no record: the trees were made on the text printed)
- [x] Antigone, Ajax, Electra
- [x] The New Testament (no record: the trees were made on the text printed)
- [x] The checking pass prepared (job files, control, brief, workflow)
- [ ] The checking pass run by the main session, its answers entered

## Decisions

(append dated entries)

* **2026-11-17, from the files, not from the merges.** Running an import or merge again would
  change other things in six of the nine texts (found by running each into a scratch folder:
  the Odyssey a header line and two apparatus items, the Gorgias six commentary lines, the
  Symposium 66 joined words and six lines of commentary and introduction; the Sophocles
  importers have pending fixes). So one step works on the files as they stand. Lysias's and the
  Shepherd's merges give their files again exactly and end with the step.
* **2026-11-17, what counts as a word of the trees' text.** Not GLAUx's crasis marks ("τα-"
  before ταὐτόν, "κα-" before κἄν) nor its gap marks ("G?"): they are devices. Not the half of a
  word the treebank writes in two ("κ-" of κἀγώ): our word is a unit of both, and the half
  stays a node of the tree as it was. So none of these is an unprinted word.
* **2026-11-17, a run of words tied elsewhere** (three or more words that stand word for word
  among the tree words left over) must lie within 400 tree words of its neighbours' place or in
  a sentence numbered between theirs: a verse that recurs in Homer is not tied to its twin in
  another book. This tied the last verses of Odyssey 2, 3, 4, 17 and 20 to their own trees
  (the treebank cites them by the book alone, and the alignment had lost them).
* **2026-11-17, sentences counted.** "Really differ" counts only sentences in which a word of
  ours stands: a tree sentence none of our words is in (the Shepherd's Greek end, a verse the
  treebank has twice) is never shown.
* **2026-11-17, found on the way, not changed (for the author).** (1) In the joined words the
  merges made earlier (εἴτε, οὐδέ where GLAUx hangs one half on the other), the word sometimes
  carries the relation and head of the half that hangs on the other half, so its head is one of
  its own tree words: Lysias 83 words, the Gorgias 45, the Shepherd 8, the Odyssey 5, the
  Symposium 4, the Electra 2, Ajax 1. The step's own joins take the half that hangs outside
  (`_main`); the old ones are as they were, since changing them is a change to trees on sale.
  (2) The Antigone's text at 424, 803, 1136 and perhaps 196 (above).

* **2026-11-17, the kinds of difference as checked** (the pass: 21 jobs, 1,089 readings, commit
  67c17f7; the answers entered by `syntax-text <slug>` / the merges). Sentences that really
  differ after it: **Lysias 269 of 2,056** (readings: elision 9, nu 1, spelling 105, form 80,
  word 69), **the Shepherd 2 of 2,086** (spelling 4, form 2), **the Odyssey 258 of 6,721**
  (elision 64, nu 133, spelling 321, form 86, word 119). Antigone, Ajax and Electra wait for the
  agent that is mending those plays.
* **2026-11-17, the Shepherd is not told of another text** (the author): the sentence in the
  description, the `syntax_text` key and the header line are out again (about.md and grc.txt
  are as they were before); the record stays (`FROM_FILES["hermas"]` has no name).
* **2026-11-17, joined words that hung on themselves** (the author: mistakes in texts on sale
  first). A word of ours that is several tree words (οὐδέ = οὐ δέ) carries one part's relation
  and head. The older rule took the part that is no mere particle, else the first; that gave
  two kinds of fault, found by building every tree as the reader does
  (`pipeline/build/agent-scratch/record/treecheck.py`):
  (1) the part carried hangs on the other part, so the word hung on itself: οὐδέ, μηδέ (GLAUx
  ties the δέ to the οὐ as "MWE"), εἴτε, ἐάντε (the εἰ tied to the τε), and in the Odyssey
  ἐϋφρονέων, εὐρυκρείων, πασιμέλουσα (the treebank ties the first half to the second);
  (2) the part carried hangs on a word that hangs on the other part, so the two hung on each
  other: οὔτε, μήτε where the οὔ is an AuxZ on a member of the coordination the τε heads.
  **The rule now: the word carries the relation and head of its topmost part**, the one that
  does not hang, directly or through other words, on another of its parts
  (`import_perseus.joined_main`, used by both aligners and by `syntax_text.mend_joined`, which
  mends the files as they stand). So οὐδέ hangs where its οὐ hangs (an AuxZ on the word
  negated: 3.31 οὐδὲ διελέγετο, Gorgias 455b1 οὐδʼ … δύναμαι); εἴτε, οὔτε, μήτε take the τε's
  place (the coordinator, or AuxY on the next εἴτε); ἐϋφρονέων takes φρονέων's. Mended: Lysias
  87 words, the Gorgias 56, the Symposium 49, the Shepherd 10, the Odyssey 11. After it no word
  hangs on itself and no joined word is in a cycle in these five texts (before: 83+4, 45+4,
  4+93, 8+2, 5+14 words). The merges now give these very tokens (the Symposium's "66 joined
  words" that a merge would have changed are this). **To pass on for Ajax and Electra:** the
  same is in the shared code, so an import after this commit mends Ajax 1073 οὔτʼ and Electra
  1061 εὕρωσι, 1073 διαίτᾳ by itself; otherwise `syntax-text ajax` / `electra` does.
* **2026-11-17, not settled: fourteen sentences of the Odyssey whose trees hold a cycle in the
  treebank itself** (an omitted-word node "[0]" that hangs on a word which hangs on it): 2.9
  (sentence 2185777), 2.58, 3.102, 3.210, 3.265, 4.632, 5.265, 5.347, 9.313, 17.283, 17.386,
  20.220, 22.302, 24.376. Each needs its sentence read to say where the omitted word belongs;
  nothing was changed. What the reader does with such a tree was not checked.

* **2026-11-17, misprints of the trees' text** (the author: "a misprint in the trees' text is
  mentioned where that text is shown, and nowhere else"). `syntax-text.tsv` and
  `syntax_text_words` have a column `misprint` (1 or empty) on reading rows: 1 where the trees'
  word is an evident misprint of the text the trees were made on. The reader treats such a
  reading as a real difference whatever its `difference` and says that the trees' text has a
  misprint there. The hand list, with the reason for each, is `syntax_text.MISPRINTS`; an entry
  that is no reading of the record any more is reported. Marked: the Shepherd 6 (11.2.6
  ἀσύμποφα, 14.1.10 αὐτῇς, 25.6.3 μενανοήσωσι, 26.11.2 ἀκοκριθεῖσαι, 26.11.7 παρθένον, 26.23.5
  μετανήσατε); Lysias 6 (6.20 τούτω, 7.20 ἔραττες, 8.3 χειρεῖτε, 8.15 ἐβάδιξε, 14.7 ἐξῆθε, 23.13
  ἔραξε); the Odyssey 4 (3.74 πέροντες, 3.435 εἰργάξετο, 4.270 οἷν, 4.332 προσέθη). The Odyssey's
  four are those seen while the readings were gone through for other ends, not a reading of all
  723: a pass over the readings for misprints is still to be made. The Theogony: none found (no
  tree form in other letters that the analyser cannot read); the Gorgias has no readings. For
  Antigone, Ajax and Electra, whose records are remade after the other run: one candidate,
  Antigone 803 δάκρυ against the trees' mis-accented δάκρυων, if that reading still stands.
* **2026-11-17, a printed word is filed under its own lemma** (the author, on Theogony 754: "if
  we print εἰς we file it under εἰς"). 754 ἔς (of ἔς τʼ, the trees' ἔστʼ) is under εἰς, a
  preposition, no longer under ἔστε. Every other word of a place where the print divides what
  the trees join was looked at (the Theogony's 13 places, Lysias's 8, the Odyssey's 16): each
  is under its own lemma already (αἵ under ὅς, τʼ under τε, ὅ τι under ὅς and τις). Two places
  of Lysias are one word cut by the line (25.35 ὑπο|ψίαν, 33.9 ἀγανακτήσει|εν): both halves
  stay under the whole word.

