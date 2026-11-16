# Gillies's translation: placing his paragraphs beside the Greek

John Gillies's English version of six speeches of Lysias (London 1778: speeches 1, 3, 4, 21, 26,
34) has been transcribed from the scan and checked against the page
(`pipeline/transcriptions/drama/lysias-gillies-NN/intro-NN.md`). It is a free version: no section
numbers, long paragraphs, sentences recast, things left out and added. The reader shows a
translation beside the Greek section by section, so each of his paragraphs must be told where in
the Greek it begins. **That is your whole task: you write marks. You do not translate, correct,
reword, cut or move anything.**

## The one rule

**The only thing you may write into the text is the mark `§N ` (the section sign, the number of
a section of the Greek, one space).** Every word, letter, stop and space of Gillies stays as it
is, also where he is wrong about the Greek, and also where the transcription looks wrong to you
(say so in your reply; do not change it). The checker compares your file with the committed
transcription and reports any difference that is not a mark.

Do not open any other translation of Lysias, and do not put Gillies right from memory of one.
You read the Greek yourself to find the places; nothing you read is written down except numbers.

## What you have

* Your speech's batch file(s): `transcriptions/drama/lysias-gillies-NN/intro-01.md` (and
  `intro-02.md` if the speech has two). A file is a row of page blocks (`=== p-0607`, the text,
  `--- flags`, `--- notes`). In the text: `# ` lines are the oration's heading; `[Note: …]`
  paragraphs are Gillies's footnotes; a block's first paragraph that begins `+ ` is the
  paragraph of the page before running on. None of these three takes a mark.
* The Greek: `texts/lysias/grc.txt` (read only). Your speech is the lines whose number begins
  with the speech's number: `4.7<TAB>…` is speech 4, section 7. A lettered line (`4.7b`) is the
  same section going on after a paragraph break: its mark is `§7`. A line `!<TAB>ΜΑΡΤΥΡΕΣ` is a
  heading inside the speech (witnesses, a law read out). Speech 34 begins with section 0, the
  ancient summary by Dionysius; Gillies does not translate it, so his first mark there is `§1`.

## Where the marks go

1. **At the head of every paragraph of the translation**: the section of the Greek in which the
   Greek of the paragraph's first sentence begins. If that sentence renders the end of a section
   and the paragraph then goes on into the next, it still takes the section where it begins.
2. **Inside a paragraph that covers several sections**: also before a sentence of his that
   begins where a section of the Greek begins, wherever that is plain. A mark inside a paragraph
   stands only before the first word of a sentence. Not every section gets a mark: where Gillies
   has run two sections into one sentence, or you cannot say where the section begins in his
   English, put none; the text simply runs on under the mark before. Never force a place.
3. **The marks rise.** Each mark is a higher number than the one before it. A paragraph or
   sentence that begins in a section already marked takes no mark. Where Gillies brings a passage
   earlier or later than the Greek has it, it takes no mark either and runs on where he put it;
   write a remark (below).
4. Where he leaves a section out, there is no mark for it. Where he adds a sentence of his own,
   it runs on under the mark before.

How to find the places: proper names, numbers and sums of money, the address to the court
("O Senators", "Athenians"; ὦ βουλή, ὦ ἄνδρες δικασταί), the calling of witnesses and the reading
of laws, the order of events. Read the Greek section through before you decide; a name alone can
occur in several sections.

Example (speech 4; the Greek 4.1 begins Θαυμαστόν γε, ὦ βουλή, …, and 4.5 Ἀλλʼ ἦν, εἰ βούλεται,
ἐχθρός· …):

    §1 It is wonderful, O Senators! he should pretend, that we had not settled our differences ; …

    §5 But granting I was his enemy (for I give up this point as less material), does it follow …

## Remarks

Under `--- notes` of the page, one line for each thing the next reader should know: "§12: Gillies
leaves out 13–14"; "the paragraph 'Such, Athenians …' renders 22 before 21: left unmarked";
"§9 doubtful: his sentence joins 8 and 9". The notes are yours to write in; the text is not.

## Checking

From `pipeline/`:

    .venv/bin/python -m anagnosis_pipeline check-gillies-marks N

(N the speech's number). It must end with `speech N: 0 remarks`. It reports any change to the
text that is not a mark, a mark that is no section of the speech, and marks that do not rise; and
it lists every mark with the first words of the English after it and the first words of the
Greek section. **Read that list down, line by line: does the English begin where the Greek
does?** Correct what does not.

## Before you finish

Reply (short): the number of marks and the number of the speech's sections; the sections Gillies
leaves out or moves; places you were unsure of; anything in the transcription that looked wrong
(not changed); the checker's last line.
