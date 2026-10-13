# Corrections to the Woodhouse OCR

The reader's English → Greek dictionary is S. C. Woodhouse, *English-Greek Dictionary: A
Vocabulary of the Attic Language* (Routledge, 1910). Its text is the OCR by Akemdwr
(archive.org/details/Woodhouse, `pipeline/sources/woodhouse/Woodhouse.dsl`), which is kept as
downloaded. The files here correct it against the 1910 scan; `woodhouse.py` applies them.

## Files

- `corrections-NN.tsv`: one correction per line, tab-separated:
  `<line>	<old>	<new>	<page>	<note>`
  - `<line>`: the line of `Woodhouse.dsl` (1-based; the same numbers as the Read tool shows).
  - `<old>`: an exact piece of that line **as it stands, markup included**, that occurs in it
    exactly once. Keep it short, but long enough to be unique (a whole word, or the word with its
    neighbour).
  - `<new>`: what the print has, in the same markup. Write `\t` for a tab and `\n` for a line
    break.
  - `<page>`: the PDF page of the scan you read it on.
  - `<note>`: empty, or `print: <reading>` when you corrected a misprint of the book itself (see
    below), or `unsure: <why>`.
  - Corrections apply in file order: when two touch the same line, the second's `<old>` must match
    the line as the first left it. One correction that covers both is simpler.
- `checked-NN.tsv`: the flagged words that the print has exactly as the OCR does:
  `<line>	<word>` (the word exactly as the flag gives it), and an optional third column for a note.
  A rerun of the flagger leaves them out.

- `global.tsv`: rules for the whole text, applied after the corrections:
  `<regular expression>	<replacement>	<note>` (a misreading the OCR makes throughout, a misprint
  the book repeats, such as οὐδένος for οὐδενός).
- `lsj-forms.tsv`: where Woodhouse accents a word otherwise than LSJ (λαβρός, βλαβή, ἀλάζων), LSJ's
  form is used throughout: `<printed>	<LSJ>	<occurrences>`, applied last.

## Reading the scan

Page images are in `pipeline/build/woodhouse-pages/`: `p0421-l1.png`, `-l2`, `-l3` (left
column, top to bottom), `-r1`, `-r2`, `-r3` (right column), and `p0421.png`, the whole page,
small. An entry may run on into the next part, the other column, or the next page (after `r3`
comes the next page's `l1`). If a page you need is missing, render it:
`cd pipeline && .venv/bin/python -m anagnosis_pipeline.woodhouse_pages 422`.

## What the DSL markup means

- `[b]adj.[/b]`, `[b]subs.[/b]`, `[b]v. trans.[/b]`: the part of speech after the headword.
- `[i]…[/i]`: the English in italics.
- `[c brown]P.[/c]`, `[c brown]V.[/c]`, `[c brown]Ar.[/c]`, `[c brown]Thuc.[/c]`: the marks of
  usage and the authors (roman type in the print).
- `[c darkviolet]gen.[/c]`, `[c darkviolet]mid.[/c]`: grammatical words.
- Woodhouse's marks of vowel length are colours on the vowel: `[c red]ι[/c]` long (macron),
  `[c blue]α[/c]` short (breve), `[c purple]…[/c]` both. An accent or breathing stays on the
  letter: `π[c blue]ά[/c]ρ`, `[c blue]ἀ[/c]φ[c red]ι[/c]έναι`.
- `[sup]A[/sup]`: a superscript (Stephanus letters).
- Elision is `ʼ` (U+02BC).

## Rules

1. Follow the 1910 print: its letters, accents, breathings, iota subscripts, length marks,
   punctuation and English spelling (British: *colour*, *honour*).
2. For each flag: if the OCR differs from the print, write a correction; if the print reads the
   same, add the word to `checked-NN.tsv`. While you have the line before you, compare the
   **whole line** with the print and correct anything else in it that is wrong, including the
   markup (a word italic in the print should be in `[i]`; a stray or unclosed tag is removed or
   closed).
3. A misprint of the book itself (a wrong accent on a common word, *adj.* for *adv.*, a letter
   upside down) is corrected only when you are certain, with the note `print: <what the print
   has>`. When in doubt, follow the print.
4. The kinds of flag:
   - `greek`: the letters are found in no dictionary or corpus; often a misread letter
     (φ for ψ, ν for υ, ο for σ), sometimes a rare word that is right.
   - `accent`: the letters are right but not with those accents or breathings.
   - `english`: a likely misspelling.
   - `mixed`: Greek and Latin letters mixed in one word (`Αr.` with a Greek Alpha, `oὐδαμοῦ` with a
     Latin o); write each in its own alphabet.
   - `markup`: the line's tags do not pair up. The line may go on in the next line of the file
     (the DSL breaks lines after some abbreviations); read the file around it.
   - `headword`: a headword line that is suspect. Archaic English (*churl*, *gyves*) is right
     and goes to `checked`. A line that is really part of the entry before (it has Greek,
     markup or a colon) becomes an indented line: replace it with `\t` and the line in proper
     markup. A headword with part of its entry on the same line is split with `\n\t`.
5. Do not change line numbers' meaning: never add or remove lines in `Woodhouse.dsl` itself;
   do not edit that file at all.
6. Save as you go: after each page, append that page's rows to your files, so that the work
   survives an interruption.
7. When done, check that your corrections apply:
   `cd pipeline && .venv/bin/python -m anagnosis_pipeline.woodhouse corrections-NN.tsv`
