# Lysias: choosing each word's analysis in the speeches without syntax trees

In the reading app every Greek word can be tapped for its dictionary form (lemma) and its
grammatical form. For most speeches of Lysias these come from syntax trees. Speeches 12, 13 and
19 have no trees we may use, so there a program read each word **by itself, without its
sentence**, and where a spelling allows several readings it took the commonest: τὸ is called
accusative also where it is the subject, δοκεῖ may be called a second person, ἀξιῶ an adjective.
You put that right: for each such word you **choose, among the readings offered, the one that is
right in its sentence**. You translate nothing and you write nothing but your choices.

## Your file

`pipeline/transcriptions/lysias/analyses/job-NN.tsv`. For each section of the speech it gives the
Greek text and then one line for every word to decide:

    12.21:17	… εἰς τοὺς [πολεμίους] ἐξήλασαν …	1 πολέμιος a-p---ma- adjective, plural masculine accusative ‖ 2 πόλεμος …	→ 

* `12.21:17`: the section, and the word's number in it (counted from 0); the word is the one in
  square brackets, shown with the four words either side. Read the whole sentence in the
  section's text above before you choose: the form of a word depends on words that may stand far
  from it.
* Then the readings, numbered, each with its lemma, its tag and the tag in words. **Reading 1 is
  the one the text has now.** It is right more often than not; you are looking for the places
  where it is not.
* After the arrow you write your answer. Nothing else on the line, and nothing else in the file,
  may be changed.

## The answer

* **A number**: the reading that is right here. `1` where the present reading is right.
* **`other: LEMMA TAG reason`** where none of the readings offered is right, e.g.
  `other: ἀξιόω v1spia--- the verb: "I ask that", not the adjective`. This is the only way to
  give a reading that is not on the list, and it needs the reason. The lemma is the dictionary
  form (nominative singular; first person singular present). Use it rarely: the list nearly
  always holds the right reading.
* **`? reason`** where you cannot tell (a neuter that can be subject or object in a sentence that
  can be construed both ways). The word then keeps its present reading.

You may not leave a line empty, and you may not choose a reading because it is commoner: choose
by the sentence.

## The tags

Nine letters: part of speech, person, number, tense, mood, voice, gender, case, degree; `-` where
a place does not apply. The words after the tag say the same. Two readings on a list always
differ in the lemma, or in person, number, tense, mood, voice or case: those are what you decide.
Gender and the finer part of speech (pronoun or adjective, particle or adverb) are not asked for;
middle and passive count as one ("middle or passive").

## How to decide (the commonest cases)

* **Nominative or accusative** of a neuter, of τὸ, τὰ, ταῦτα, τοῦτο, ὅ, ἅ, τι, οὐδέν: is it the
  subject of its verb (nominative; a neuter plural subject takes a singular verb), or its object,
  the subject of an infinitive, or governed by a preposition (accusative)? An article, an
  adjective and a participle take the case of their noun: decide the noun, then give its
  companions the same.
* **Vocative or nominative**: the address after ὦ is a vocative (ὦ ἄνδρες δικασταί, ὦ Ἀγόρατε).
* **Genitive singular or accusative plural** in -ας, **nominative plural or dative singular**
  in -αι/-ᾳ and the like: by the article, the preposition, the verb.
* **A verb form two persons or two moods share**: δοκεῖ (he seems / you seem to yourself), -ετε
  and -εσθε (indicative or imperative: is the court being told to do something?), -σω and -σῃ
  (future indicative or aorist subjunctive: after ἐάν, ἵνα, ὅπως the subjunctive), ἦν (was / if).
* **A participle or a finite verb, a verb or a noun** spelled alike (ἄρχοντος: the archon, or
  "while he held office"; either is right where it is a date by an archon: keep reading 1).
* **Two lemmas**: which word is it? ἄν the particle or ἐάν "if"; ἤ "or, than" and ἦ "truly";
  ταῦτα "these things" and ταὐτά "the same things"; πλεῖν "more" (πλεῖν ἢ τριάκοντα) or "to
  sail".

Where two readings are both defensible and the present one is among them, keep the present one.

## Rules

* Work through the file section by section and **save after each section**.
* You may read `texts/lysias/grc.txt` for more of the context. **Do not open** `texts/lysias/tokens.tsv`
  or `syntax-nodes.tsv`, anything under `pipeline/sources/` (treebanks, parsed texts), any
  translation of Lysias, or another job file. Do not look the speech up elsewhere. The point of
  the pass is your own reading of the Greek.
* Write no other file in the repository and do not run git.

## Checking

From `pipeline/`:

    .venv/bin/python -m anagnosis_pipeline lysias-analyses check transcriptions/lysias/analyses/job-NN.tsv

It must end with `0 remarks`: every line answered, every answer well formed, nothing but the
answers changed.

## Before you finish

Reply (short): how many words you answered; how many answers are not `1`; every `other:` and
every `?` with its place; the checker's last line.
