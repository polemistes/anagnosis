package no.anagnosis.data

import no.anagnosis.db.Commentaries
import no.anagnosis.db.Commentary_notes
import no.anagnosis.db.Lines
import no.anagnosis.db.Sections
import no.anagnosis.db.Sentence_nodes
import no.anagnosis.db.Tokens
import no.anagnosis.db.Translation_segments
import no.anagnosis.db.Translations
import no.anagnosis.db.Works

/** One text in the catalog, installed or not. */
class CatalogEntry(
    val slug: String,
    val title: String,
    val author: String,
    val titleEn: String,
    val authorEn: String,
    val description: String,
    val edition: String,
    val installed: Boolean,
    /** The Google Play id of the separate app that adds this text. */
    val appId: String = "",
    /** What the text comes with, for the list of texts on sale: each a short phrase, or empty. */
    val editor: String = "",
    val apparatus: String = "",
    val translation: String = "",
    val commentary: String = "",
    val syntax: String = "",
    /** Dictionaries the text adds to the reader's own. */
    val dictionaries: String = "",
    /** The price as shown on Google Play, when known. */
    val price: String = "",
    /** Whether the text's app is on Google Play, so that the reader offers it. */
    val onGooglePlay: Boolean = false,
) {
    /** The page of the text's app on Google Play. */
    val storeUrl: String get() = "https://play.google.com/store/apps/details?id=$appId"
}

/** Everything needed to display one work, loaded once. */
class WorkData(
    val slug: String,
    val work: Works,
    val lines: List<Lines>,
    val tokensByLine: Map<Long, List<Tokens>>,
    /** The treebank's punctuation and omitted-word nodes, by sentence id (see [Syntax]). */
    val nodesBySentence: Map<String, List<Sentence_nodes>>,
    val sectionsByFirstLine: Map<Long, List<Sections>>,
    val translations: List<TranslationData>,
    val commentaries: List<Commentaries>,
    /** ids of the lines that open commentary notes (shown with a dot). */
    val linesWithNotes: Set<Long>,
    /** An epic cited by book and line (1.12): n_int is book * 1000 + line. */
    val bookNumbered: Boolean = false,
    /** Prose cited by Stephanus page, section and line (172a1): n_int is page * 1000 + section * 100 + line. */
    val stephanus: Boolean = false,
    /** The New Testament, cited by book, chapter and verse (1.5.3): n_int is book * 1000000 + chapter * 1000 + verse. */
    val verses: Boolean = false,
    /** Prose: the lines are shown as flowing paragraphs, not one under the other. */
    val prose: Boolean = false,
    /** The syntax was made by a parser and not checked by hand (shown on the syntax page). */
    val automaticSyntax: Boolean = false,
    /** The dictionaries the word sheet offers first, most fitting first (abbott-smith dodson ml lsj). */
    val dictionaryOrder: List<String> = emptyList(),
) {
    /** Whether the text is read one book at a time: an epic, the New Testament. */
    val byBook: Boolean get() = bookNumbered || verses

    /** The books in order (empty for a play): number, label and first and last line. */
    val books: List<Book> by lazy {
        if (!byBook) emptyList() else lines.groupBy { bookOf(it.n_int) }.map { (b, ls) ->
            val label = sectionsByFirstLine[ls.first().id]?.firstOrNull()?.label ?: b.toString()
            Book(b, label, ls.first().n_int, ls.last().n_int, named = verses)
        }
    }

    /** The number of a line as printed in the margin: within its book for an epic; chapter and verse (5:3) in the New Testament. */
    fun lineLabel(nInt: Long, sub: String = ""): String = when {
        verses -> "${chapterOf(nInt)}:${verseOf(nInt)}"
        bookNumbered -> "${nInt % BOOK}$sub"
        stephanus -> stephanusLabel(nInt)
        else -> "$nInt$sub"
    }

    /** The full reference of a line: 1.12 for an epic, 12 for a play, 172a1 for Plato, Matthew 5:3 in the New Testament. */
    fun citation(nInt: Long, sub: String = ""): String = when {
        verses -> "${books.firstOrNull { it.number == bookOf(nInt) }?.name ?: bookOf(nInt)} ${lineLabel(nInt)}"
        bookNumbered -> "${nInt / BOOK}.${nInt % BOOK}$sub"
        stephanus -> stephanusLabel(nInt)
        else -> "$nInt$sub"
    }

    /** A range of lines as a reader writes it: Matthew 5:3–7, Matthew 5:3–6:2, lines 12–14. */
    fun range(from: Long, to: Long): String = when {
        verses && to <= from -> citation(from)
        verses && chapterOf(to) == chapterOf(from) -> "${citation(from)}–${verseOf(to)}"
        verses -> "${citation(from)}–${lineLabel(to)}"
        to <= from -> "Line ${citation(from)}"
        else -> "Lines ${citation(from)}–${citation(to)}"
    }

    /** The chapter of a verse. */
    fun chapterOf(nInt: Long): Long = (nInt % VERSE_BOOK) / BOOK

    /** The verse number within its chapter. */
    fun verseOf(nInt: Long): Long = nInt % BOOK

    /** The Stephanus section a line belongs to (172a), or null for other numbering. */
    fun stephanusSection(nInt: Long): String? =
        if (!stephanus) null else "${nInt / BOOK}${SECTIONS.getOrElse(((nInt % BOOK) / 100).toInt()) { '?' }}"

    fun bookOf(nInt: Long): Int = (nInt / (if (verses) VERSE_BOOK else BOOK)).toInt()

    companion object {
        const val BOOK = 1000L
        const val VERSE_BOOK = 1000000L
        const val SECTIONS = "abcde"

        /** 172001 -> "172a1" */
        fun stephanusLabel(nInt: Long): String =
            "${nInt / BOOK}${SECTIONS.getOrElse(((nInt % BOOK) / 100).toInt()) { '?' }}${nInt % 100}"
    }
}

/**
 * A book of an epic or of the New Testament; `label` is e.g. "1 · Α" or "Matthew · ΚΑΤΑ ΜΑΘΘΑΙΟΝ".
 * A [named] book (the New Testament's) is called by its name, an epic's by "Book" and its number.
 */
class Book(val number: Int, val label: String, val firstN: Long, val lastN: Long, val named: Boolean = false) {
    /** "Matthew" for a named book, else its number. */
    val name: String get() = if (named) label.substringBefore(" · ") else number.toString()

    /** How the book is offered in the book menu: "Book 1 · Α", "Matthew · ΚΑΤΑ ΜΑΘΘΑΙΟΝ". */
    val title: String get() = if (named) label else "Book $label"
}

class TranslationData(val translation: Translations, val segments: List<Translation_segments>)

/** A dictionary entry together with the name of the lexicon it comes from. */
class Entry(
    val lexiconSlug: String,
    val lexiconTitle: String,
    val headword: String,
    val homograph: Long,
    val html: String,
)

/**
 * What the word sheet shows: a headword (or a token's form), its parse if any, gloss and entries.
 * [syntax] is the word's role in its sentence ("subject of φέρει"), when the treebank gives one.
 */
class WordInfo(
    val form: String,
    val lemma: String,
    val morphology: String,
    val shortDefinition: String?,
    val entries: List<Entry>,
    val syntax: String? = null,
)


/** One heading of the page-wide Apparatus / Commentary views: a line or range with its notes. */
class NoteGroup(val heading: String, val lineText: String?, val notes: List<Commentary_notes>)

/** Which kind of notes a commentary holds; decided from its slug. */
enum class NoteKind(val label: String) { APPARATUS("Apparatus"), COMMENTARY("Commentary") }

fun Commentaries.kind(): NoteKind = if ("apparatus" in slug) NoteKind.APPARATUS else NoteKind.COMMENTARY

/** One line of the About screen's credits, read from the bundle's licence columns. */
class Credit(val kind: String, val title: String, val detail: String?, val license: String?)

/** A headword match in the dictionary search (one per lemma, across both dictionaries). */
class HeadwordHit(val lemmaKey: String, val headword: String)

/** One analysis of an inflected form. */
class FormAnalysis(val form: String, val lemma: String, val lemmaKey: String, val postag: String, val source: String)
