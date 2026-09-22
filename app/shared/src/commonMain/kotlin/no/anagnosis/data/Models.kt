package no.anagnosis.data

import no.anagnosis.db.Commentaries
import no.anagnosis.db.Commentary_notes
import no.anagnosis.db.Lines
import no.anagnosis.db.Sections
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
)

/** Everything needed to display one work, loaded once. */
class WorkData(
    val slug: String,
    val work: Works,
    val lines: List<Lines>,
    val tokensByLine: Map<Long, List<Tokens>>,
    val sectionsByFirstLine: Map<Long, List<Sections>>,
    val translations: List<TranslationData>,
    val commentaries: List<Commentaries>,
    /** ids of the lines that open commentary notes (shown with a dot). */
    val linesWithNotes: Set<Long>,
)

class TranslationData(val translation: Translations, val segments: List<Translation_segments>)

/** A dictionary entry together with the name of the lexicon it comes from. */
class Entry(
    val lexiconSlug: String,
    val lexiconTitle: String,
    val headword: String,
    val homograph: Long,
    val html: String,
)

/** What the word sheet shows: a headword (or a token's form), its parse if any, gloss and entries. */
class WordInfo(val form: String, val lemma: String, val morphology: String, val shortDefinition: String?, val entries: List<Entry>)


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
