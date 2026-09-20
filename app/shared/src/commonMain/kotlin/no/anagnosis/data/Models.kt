package no.anagnosis.data

import no.anagnosis.db.Commentaries
import no.anagnosis.db.Commentary_notes
import no.anagnosis.db.Lines
import no.anagnosis.db.Sections
import no.anagnosis.db.Tokens
import no.anagnosis.db.Translation_segments
import no.anagnosis.db.Translations
import no.anagnosis.db.Works

/** Everything needed to display one work, loaded once. */
class WorkData(
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

class WordInfo(val token: Tokens, val morphology: String, val shortDefinition: String?, val entries: List<Entry>)

class NoteInfo(val commentary: Commentaries, val notes: List<Commentary_notes>)

/** One line of the About screen's credits, read from the bundle's licence columns. */
class Credit(val kind: String, val title: String, val detail: String?, val license: String?)
