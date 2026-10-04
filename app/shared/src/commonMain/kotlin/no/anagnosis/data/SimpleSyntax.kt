package no.anagnosis.data

/**
 * A reader's view of a sentence's syntax as an outline: one phrase per line with a plain role
 * (main verb, subject, object · dat. ...), in the order of the text, each clause named and its
 * lines kept together, a clause inside a clause indented one step where it occurs, the outer
 * clause going on below it.
 *
 * It is drawn from the treebank's dependency tree ([SyntaxTree]) but hides the treebank's
 * conventions: prepositions and conjunctions as heads, coordination nodes, elliptic nodes,
 * the labels of the Prague scheme. A word stays with its article, adjectives and genitives;
 * a preposition with its noun; a conjunction with its clause. The words of a phrase that the
 * text splits are brought together. The treebank's errors remain.
 */
object SimpleSyntax {
    /** The roles a reader is shown. [label] is empty for words shown without one. */
    enum class Role(val label: String) {
        VERB("verb"),
        SUBJECT("subject"),
        OBJECT("object"),
        COMPLEMENT("complement"),
        MODIFIER("adverbial"),
        ADDRESSED("vocative"),
        EXCLAMATION("exclamation"),
        ASIDE("stands apart"),
        CONNECTOR(""),
        PARTICLE(""),
        OTHER(""),
    }

    /** A line of the outline: a phrase, or a clause with the lines inside it. */
    sealed interface Item

    /**
     * Words that belong together, with the role they play in their clause. A clause of one
     * phrase (a bare infinitive, a participle) is shown as a phrase whose label names the clause.
     * [stray] marks the safety net: words the rules placed nowhere.
     */
    class Phrase(
        val role: Role, val words: List<SyntaxNode>, val label: String = role.label, val stray: Boolean = false,
        /** Where the phrase stands in the text, for the order of lines: an omitted word stands by its first dependent. */
        val start: Int = words.first().id,
    ) : Item

    /** A clause: its name (empty for a group of words among clauses) and its lines in the order of the text. */
    class Clause(val label: String, val items: List<Item>) : Item

    /** The outline of a sentence: its clauses in the order of the text, and last any stray words. */
    fun outline(tree: SyntaxTree): List<Item> = Builder(tree).build()

    /** Every word of [items], in the order shown. */
    fun words(items: List<Item>): List<SyntaxNode> = items.flatMap { when (it) { is Phrase -> it.words; is Clause -> words(it.items) } }

    /** The view as plain text, for checking the rules outside the app. */
    fun render(tree: SyntaxTree): String {
        val sb = StringBuilder()
        fun line(item: Item, depth: Int) {
            val indent = "    ".repeat(depth)
            when (item) {
                is Phrase -> {
                    val words = item.words.joinToString(" ") { Syntax.displayForm(it) }
                    sb.append(indent).append(if (item.label.isEmpty()) words else "$words ⟨${item.label}⟩").append('\n')
                }
                is Clause -> {
                    sb.append(indent).append("— ").append(item.label).append('\n')
                    for (i in item.items) line(i, depth + 1)
                }
            }
        }
        for (item in outline(tree)) line(item, 0)
        return sb.toString()
    }

    // ------------------------------------------------------------------ the rules

    private val CLAUSE_ROLES = setOf("SBJ", "OBJ", "ADV", "PNOM", "ATV", "AtvV", "OCOMP", "ExD", "CO")
    private val AUX = setOf("AuxZ", "AuxY", "AuxG", "AuxX", "AuxK", "AuxV", "AuxC", "AuxP", "AuxE", "AuxS")
    private val NEGATIONS = setOf("οὐ", "μή", "οὐκ", "οὐχ", "οὐχί", "οὐχὶ", "μὴ")
    private val MODAL = setOf("ἄν", "κε", "κεν", "κέ", "ἂν")
    private val RELATIVES = setOf(
        "ὅς", "ὅστις", "ὅσος", "οἷος", "ἡλίκος", "ὁπόσος", "ὁποῖος", "ὅσπερ", "ὅθεν", "οὗ", "ἔνθα",
        "ὅπου", "ὅποι", "ὅθι", "ὁπόθεν", "ὁπότερος", "ὁπηλίκος", "ὅπῃ", "ᾗ", "οἷ", "ἔνθεν",
    )
    private val INTERROGATIVES = setOf(
        "τίς", "πῶς", "πότερος", "πότερον", "ποῖος", "πόσος", "ποῦ", "πόθεν", "ποῖ", "πότε", "πῇ", "πηλίκος", "πῆ", "πόσε",
    )
    /** Adverbs that open a clause like a conjunction (ὡς ἔχω "as I am"). */
    private val RELATIVE_ADVERBS = mapOf("ὡς" to "as, how", "ὅπως" to "as, how", "ὥσπερ" to "as")

    /** What the commonest conjunctions mean, for the clause label. */
    private val CONJUNCTIONS = mapOf(
        "ὅτι" to "that, because", "ὡς" to "that, as, so that", "εἰ" to "if, whether", "ἐάν" to "if", "ἄν" to "if",
        "ἤν" to "if", "ἵνα" to "so that", "ὅπως" to "so that, how", "ὅτε" to "when", "ὁπότε" to "when",
        "ὅταν" to "whenever", "ἐπεί" to "when, since", "ἐπειδή" to "when, since", "ἐπειδάν" to "when",
        "ἕως" to "while, until", "ἔστε" to "until", "πρίν" to "before", "ὥστε" to "so that", "μή" to "lest",
        "ὅπου" to "where", "ὅθεν" to "whence", "ἡνίκα" to "when", "διότι" to "because", "καίπερ" to "although",
        "εἴτε" to "whether", "ἄτε" to "as", "ὥσπερ" to "as", "ἤ" to "than, or", "ἠέ" to "than, or", "ὄφρα" to "so that, while",
        "εὖτε" to "when", "ἦμος" to "when", "τόφρα" to "meanwhile", "ἐπήν" to "when", "ὁπηνίκα" to "when",
        "ἐπείτε" to "since", "ὁσάκις" to "as often as", "μέχρι" to "until", "ἄχρι" to "until", "ἠμέν" to "both",
        "ἠδέ" to "and", "καί" to "and", "τε" to "and", "δέ" to "and, but", "ἀλλά" to "but", "οὐδέ" to "nor", "μηδέ" to "nor",
        // the New Testament's
        "καθώς" to "as, just as", "καθάπερ" to "just as", "ἐπειδήπερ" to "inasmuch as", "μήποτε" to "lest, whether perhaps",
        "εἴπερ" to "if indeed", "ἐάνπερ" to "if indeed", "ὡσεί" to "as, as if", "ἐπάν" to "when", "καθότι" to "because, as",
        "ὁπόταν" to "whenever", "κἄν" to "even if, and if", "ἄχρι" to "until", "μέχρι" to "until", "ὁσάκις" to "as often as",
        "ἵνα" to "so that, that",
    )

    private class Builder(val tree: SyntaxTree) {
        /** A clause as built: its label, its own phrases, the clauses inside it, its depth, and the span of its own words. */
        class Clause(val label: String, val phrases: List<Phrase>, val subs: List<Clause>, val depth: Int, val range: IntRange) {
            /** Where the clause begins in the text: its first own word, else its first inner clause. */
            val start: Int get() = phrases.minOfOrNull { it.start } ?: subs.minOfOrNull { it.start } ?: range.first
            fun with(more: List<Phrase>) = Clause(label, (phrases + more).sortedBy { it.start }, subs, depth, range)
            fun at(d: Int): Clause = Clause(label, phrases, subs.map { it.at(d + 1) }, d, range)
        }

        /** Where a node stands for the order of lines: an omitted word by its first dependent, as the diagram places it. */
        fun startOf(n: SyntaxNode): Int = if (n.artificial) tree.children(n).filter { it.isWord || it.artificial }.minOfOrNull { startOf(it) } ?: n.id else n.id

        fun ph(role: Role, words: List<SyntaxNode>, label: String = role.label) = Phrase(role, words, label, start = words.minOf { startOf(it) })

        fun build(): List<Item> {
            // the sentence's top nodes: the roots, a punctuation root standing for its dependents
            val tops = tree.roots.flatMap { if (it.isPunctuation) tree.children(it) else listOf(it) }
                .filter { !isBarePunct(it) }
            // what stands outside every clause (a particle, a fragment the treebank left hanging) goes
            // with the clause it stands in, else the next one, else the last; with no clause it stands alone
            val (strays, rest) = tops.partition { !leadsToClause(it) }
            val clauses = rest.flatMap { clausesOf(it, 0) }.sortedBy { it.start }.toMutableList()
            if (clauses.isEmpty()) {
                for (s in strays) clauses += wordClause(s, 0, emptyList())
            } else {
                for (st in strays) {
                    val phrases = mutableListOf<Phrase>(); val subs = mutableListOf<Clause>()
                    collect(st, 1, phrases, subs)
                    val target = clauses.firstOrNull { st.id in it.range } ?: clauses.firstOrNull { it.start > st.id } ?: clauses.last()
                    val k = clauses.indexOf(target)
                    clauses[k] = Clause(target.label, (target.phrases + phrases).sortedBy { it.start }, (target.subs + subs).sortedBy { it.start }, target.depth, target.range)
                }
            }
            val out = mutableListOf<Item>()
            for (c in clauses.sortedBy { it.start }) out += view(c, nested = false)
            // nothing may be lost: a word the rules left out is shown at the end, so the reader sees it
            val shown = words(out).map { it.id }.toHashSet()
            val lost = tree.nodes.filter { it.isWord && it.id !in shown }
            if (lost.isNotEmpty()) out += Phrase(Role.OTHER, lost, "not placed", stray = true)
            return out
        }

        // ---- what is what

        fun base(rel: String?): String {
            var s = rel ?: ""
            while (true) {
                s = when {
                    s.endsWith("_CO") -> s.removeSuffix("_CO")
                    s.endsWith("_AP") -> s.removeSuffix("_AP")
                    s.endsWith("_PA") -> s.removeSuffix("_PA")
                    else -> return s
                }
            }
        }

        fun lemma(n: SyntaxNode): String = n.token?.lemma ?: ""
        fun mood(n: SyntaxNode): Char = n.postag.getOrElse(4) { '-' }
        fun pos(n: SyntaxNode): Char = n.postag.getOrElse(0) { '-' }
        fun case(n: SyntaxNode): Char = n.postag.getOrElse(7) { '-' }
        fun person(n: SyntaxNode): Char = n.postag.getOrElse(1) { '-' }
        fun isArticle(n: SyntaxNode) = pos(n) == 'l'
        fun isVerbal(n: SyntaxNode) = n.isWord && mood(n) in "np"
        fun isFinite(n: SyntaxNode) = n.isWord && mood(n) in "isom"
        fun bare(n: SyntaxNode) = tree.children(n).isEmpty()
        fun isBarePunct(n: SyntaxNode) = n.isPunctuation && bare(n)
        /** A connecting word on its own: a particle, or a coordinator the treebank gave no members (a stray δέ). */
        fun isParticle(n: SyntaxNode) = n.isWord && bare(n) && base(n.relation) in setOf("AuxY", "AuxZ", "COORD", "APOS")
        fun hasMemberSuffix(n: SyntaxNode) = (n.relation ?: "").let { it.endsWith("_CO") || it.endsWith("_AP") }
        fun isConnector(n: SyntaxNode) = base(n.relation) in setOf("AuxC", "AuxP")

        /** A member of a coordination: marked _CO/_AP, a preposition or conjunction over one, or a nested coordination. */
        fun isMember(n: SyntaxNode): Boolean = hasMemberSuffix(n) || base(n.relation) in setOf("COORD", "APOS") && !bare(n) ||
            isConnector(n) && contentOf(n).first?.let { hasMemberSuffix(it) } == true
        fun isCoordinator(n: SyntaxNode) = base(n.relation) in setOf("COORD", "APOS") ||
            (!n.isWord || pos(n) in "cg" || base(n.relation) in AUX) && base(n.relation) != "PRED" && tree.children(n).any { hasMemberSuffix(it) }

        /** The members of a coordination; where none is marked, every dependent that is not a particle. */
        fun members(c: SyntaxNode): List<SyntaxNode> = tree.children(c).filter { isMember(it) }
            .ifEmpty { tree.children(c).filter { !isParticle(it) && !isBarePunct(it) } }
        fun shared(c: SyntaxNode): List<SyntaxNode> = tree.children(c) - members(c).toSet()

        /** The dependent of a preposition or conjunction that carries the content, and the rest. */
        fun contentOf(connector: SyntaxNode): Pair<SyntaxNode?, List<SyntaxNode>> {
            val kids = tree.children(connector)
            val main = kids.firstOrNull { base(it.relation) !in AUX && !isBarePunct(it) && !(it.isPunctuation && members(it).isEmpty()) }
                ?: kids.firstOrNull { base(it.relation) !in AUX } ?: kids.firstOrNull()
            return main to kids.filter { it !== main }
        }

        /** The node whose relation names a phrase's role: through a preposition or coordination. */
        fun contentNode(n: SyntaxNode): SyntaxNode = when {
            isConnector(n) -> contentOf(n).first?.let { contentNode(it) } ?: n
            isCoordinator(n) -> members(n).firstOrNull()?.let { contentNode(it) } ?: n
            else -> n
        }

        /** Whether a node governs a clause: dependents beyond articles, particles and bare adverbs. */
        fun governs(n: SyntaxNode): Boolean = tree.children(n).any {
            !(isArticle(it) && base(it.relation) !in CLAUSE_ROLES) && !(pos(it) == 'd' && bare(it) && base(it.relation) == "ADV") &&
                (base(it.relation) in CLAUSE_ROLES || isConnector(it) || isCoordinator(it) && members(it).any { m -> base(contentNode(m).relation) in CLAUSE_ROLES })
        }

        fun isClauseHead(n: SyntaxNode): Boolean {
            if (n.artificial) {
                if (isCoordinator(n)) return false
                if (base(n.relation) == "PRED" || n in tree.roots) return true
                if (pos(n) == 'v') return true  // an omitted verb tagged as one (the New Testament's)
                val kids = tree.children(n).filter { !isBarePunct(it) && !isParticle(it) }
                // an omitted noun with one dependent is a phrase; an omitted verb with a subject or several parts a clause
                return kids.any { base(it.relation) == "SBJ" } || kids.size > 1 && kids.any { base(it.relation) in setOf("OBJ", "PNOM", "ADV") }
            }
            if (!n.isWord) return false
            if (base(n.relation) == "AuxV") return false  // an auxiliary joins its verb
            if (base(n.relation) == "PRED") return true
            return when (mood(n)) {
                'i', 's', 'o', 'm' -> true
                'n' -> governs(n) || base(n.relation) == "ATR"
                'p' -> governs(n)
                else -> false
            }
        }

        /** A connector leading to a clause: the clause head or coordination under it, or null. */
        fun clauseUnder(connector: SyntaxNode): SyntaxNode? {
            val (main, _) = contentOf(connector)
            return main?.takeIf { isClauseHead(it) || isCoordinator(it) && members(it).any { m -> leadsToClause(m) } }
        }

        fun leadsToClause(n: SyntaxNode): Boolean = isClauseHead(n) || isConnector(n) && clauseUnder(n) != null ||
            isCoordinator(n) && members(n).any { leadsToClause(it) }

        /** The ids of the words under a node, itself included. */
        fun rangeOf(n: SyntaxNode): IntRange {
            var lo = n.id; var hi = n.id
            fun walk(x: SyntaxNode) {
                if (x.isWord) { if (x.id < lo) lo = x.id; if (x.id > hi) hi = x.id }
                for (c in tree.children(x)) walk(c)
            }
            walk(n)
            return lo..hi
        }

        // ---- roles

        fun roleOf(n: SyntaxNode): Role {
            val rel = base(n.relation)
            return when {
                isConnector(n) -> contentOf(n).first?.let { roleOf(it) }?.let {
                    // a prepositional phrase is never an "object" to a reader, whatever the treebank's convention
                    if (base(n.relation) == "AuxP" && it == Role.OBJECT) Role.MODIFIER else it
                } ?: Role.CONNECTOR
                isCoordinator(n) -> members(n).firstOrNull()?.let { roleOf(it) } ?: Role.PARTICLE
                rel == "SBJ" -> Role.SUBJECT
                rel == "OBJ" -> if (pos(n) == 'd') Role.MODIFIER else Role.OBJECT
                rel in setOf("PNOM", "ATV", "AtvV", "OCOMP") -> Role.COMPLEMENT
                rel == "ADV" -> Role.MODIFIER
                rel == "ExD" -> exdRole(n)
                rel == "PRED" -> Role.VERB
                rel in setOf("AuxY", "AuxZ") && pos(n) == 'v' -> Role.ASIDE  // an interjected φάναι, ἔφη
                rel in AUX -> Role.PARTICLE
                else -> Role.OTHER
            }
        }

        /** An "independent" word: someone addressed, an exclamation, a subject thrown in, or something standing apart. */
        fun exdRole(n: SyntaxNode): Role {
            if (pos(n) == 'i') return if (lemma(n) == "ὦ") Role.ADDRESSED else Role.EXCLAMATION
            if (case(n) == 'v' || lemma(n) == "ὦ" || tree.children(n).any { lemma(it) == "ὦ" }) return Role.ADDRESSED
            val verb = governor(n)
            if (case(n) == 'n' && verb != null && person(verb) == '2') return if (pos(n) == 'p') Role.SUBJECT else Role.ADDRESSED
            return Role.ASIDE
        }

        /** The case of a noun phrase, where it tells the reader something: an object or adverbial not in the accusative or any case. */
        private val CASES = mapOf('g' to "gen.", 'd' to "dat.", 'a' to "acc.")

        fun labelOf(n: SyntaxNode, role: Role): String {
            val c = contentNode(n)
            val ptcp = if (c.isWord && mood(c) == 'p' && c === n) "participle · " else ""
            val label = when (role) {
                Role.COMPLEMENT -> when (base(c.relation)) { "OCOMP" -> "object complement"; "PNOM" -> "predicate"; else -> "complement" }
                Role.OTHER -> when (base(c.relation)) {
                    "ATR" -> governorLabel(c)?.let { "describes $it" } ?: "attributive"
                    "MWE" -> "expression"; "CO" -> "joined on"; else -> ""
                }
                Role.ASIDE -> if (pos(n) == 'v' && base(n.relation) in setOf("AuxY", "AuxZ")) "says" else role.label
                else -> role.label
            }
            // a noun's case names its construction: object · dat., adverbial · gen.; not through a preposition
            val nominal = !throughPreposition(n) && c.isWord && pos(c) in "nalpm" && mood(c) != 'p'
            val case = if (nominal && (role == Role.MODIFIER || role == Role.OBJECT && case(c) != 'a')) CASES[case(c)] else null
            val full = if (case != null) "$label · $case" else label
            return if (full.isEmpty()) ptcp.removeSuffix(" · ") else ptcp + full
        }

        /** Whether the phrase's content stands under a preposition (or its coordinated members do). */
        fun throughPreposition(n: SyntaxNode): Boolean = isConnector(n) || isCoordinator(n) && members(n).any { throughPreposition(it) }

        /** The verb's line: "main verb", "verb · optative", "infinitive", "verb understood"; a noun standing as predicate "predicate". */
        fun verbLabel(head: SyntaxNode, main: Boolean, auxiliary: Boolean): String {
            if (head.artificial) return "verb understood"
            if (!head.isWord) return Role.VERB.label
            val m = mood(head)
            if (m !in "isomnp") return if (base(head.relation) == "PRED") "predicate" else Role.VERB.label
            val kind = when {
                auxiliary -> if (main) "main verb" else Role.VERB.label
                m == 'n' -> "infinitive"
                m == 'p' -> "participle"
                main -> "main verb"
                else -> Role.VERB.label
            }
            val note = when (m) { 's' -> "subjunctive"; 'o' -> "optative"; 'm' -> "imperative"; else -> null }
            return if (note != null) "$kind · $note" else kind
        }

        // ---- building

        /**
         * The phrases and clauses under a dependent [c] of a clause head, added to [phrases] and
         * [subs]: a clause of its own, the clauses under a conjunction or coordinator, a particle
         * with things hung on it (seen through), or one phrase with the clauses found inside it.
         */
        fun collect(c: SyntaxNode, depth: Int, phrases: MutableList<Phrase>, subs: MutableList<Clause>) {
            when {
                isBarePunct(c) -> {}
                leadsToClause(c) -> subs += clausesOf(c, depth)
                c.isWord && base(c.relation) in setOf("AuxY", "AuxZ") && !bare(c) && pos(c) != 'v' -> {
                    // the treebank hung words on a particle: the particle alone, its dependents on their own
                    phrases += ph(Role.PARTICLE, listOf(c))
                    for (k in tree.children(c)) collect(k, depth, phrases, subs)
                }
                else -> {
                    val words = mutableListOf<SyntaxNode>()
                    gather(c, depth, words, subs)
                    if (words.isNotEmpty()) {
                        val role = roleOf(c)
                        phrases += ph(role, words.sortedBy { it.id }, labelOf(c, role))
                    }
                }
            }
        }

        /** The words of a phrase headed by [n], with the clauses found inside it made clauses of their own. */
        fun gather(n: SyntaxNode, depth: Int, words: MutableList<SyntaxNode>, subs: MutableList<Clause>) {
            if (isBarePunct(n)) return
            if (!n.artificial && !n.isPunctuation) words += n  // an omitted noun inside a phrase, or a comma, is not shown
            for (c in tree.children(n)) {
                if (leadsToClause(c)) subs += clausesOf(c, depth) else gather(c, depth, words, subs)
            }
        }

        /** The clauses a node leads to: itself, the clause under its connector, its coordinated members; else a word clause. */
        fun clausesOf(n: SyntaxNode, depth: Int, extra: List<SyntaxNode> = emptyList()): List<Clause> = when {
            isClauseHead(n) -> listOf(clause(n, null, emptyList(), depth, extra))
            isConnector(n) && clauseUnder(n) != null -> clausesUnder(n, depth, extra)
            isCoordinator(n) && members(n).any { leadsToClause(it) } -> coordinated(n, depth, emptyList(), null, extra)
            else -> wordClause(n, depth, extra)
        }

        /** A word among clauses (a noun coordinated with a clause): a clause of its own, with no label. */
        fun wordClause(n: SyntaxNode, depth: Int, extra: List<SyntaxNode>): List<Clause> {
            val phrases = mutableListOf<Phrase>(); val subs = mutableListOf<Clause>()
            collect(n, depth + 1, phrases, subs)
            for (e in extra) collect(e, depth + 1, phrases, subs)
            if (phrases.isEmpty()) return subs.map { it.at(depth) }
            return listOf(Clause("", phrases.sortedBy { it.start }, subs.sortedBy { it.start }, depth, rangeOf(n)))
        }

        /** The clause(s) under a conjunction or preposition, the connector word leading the first. */
        fun clausesUnder(connector: SyntaxNode, depth: Int, extra: List<SyntaxNode> = emptyList()): List<Clause> {
            val (main, rest) = contentOf(connector)
            val lead = listOf(connector) + rest.filter { !leadsToClause(it) && !isBarePunct(it) }
            val more = rest.filter { leadsToClause(it) }
            return when {
                main == null -> wordClause(connector, depth, extra)
                isClauseHead(main) -> listOf(clause(main, connector, lead, depth, extra + more))
                isCoordinator(main) -> coordinated(main, depth, lead, connector, extra + more)
                else -> wordClause(connector, depth, extra)
            }
        }

        /**
         * Coordinated clauses: each member a clause (a bare infinitive or participle beside a
         * clause becomes one too). What the coordinator shares out (a subject, a participle, a
         * clause hung on it) goes with the first member. A connecting word (καί, δέ, τε, the
         * conjunction before the whole) goes with the member whose words surround it, else with
         * the first member after it, else the last: "A καὶ B" shows καί with B, "A τε B" keeps
         * τε with A.
         */
        fun coordinated(c: SyntaxNode, depth: Int, lead: List<SyntaxNode> = emptyList(), connector: SyntaxNode? = null, extra: List<SyntaxNode> = emptyList()): List<Clause> {
            val ms = members(c).sortedBy { rangeOf(it).first }
            val sharedAll = shared(c).filter { !isParticle(it) && !isBarePunct(it) } + extra
            val clauses = mutableListOf<Clause>()
            for ((i, m) in ms.withIndex()) {
                val here = if (i == 0) sharedAll else emptyList()
                clauses += when {
                    isClauseHead(m) || isVerbal(m) -> listOf(clause(m, connector ?: c, emptyList(), depth, here))
                    isConnector(m) && clauseUnder(m) != null -> clausesUnder(m, depth, here)
                    isCoordinator(m) && members(m).any { leadsToClause(it) } -> coordinated(m, depth, emptyList(), connector, here)
                    else -> wordClause(m, depth, here)
                }
            }
            if (clauses.isEmpty()) return wordClause(c, depth, extra)
            val words = (lead + (if (c.isWord) listOf(c) else emptyList()) + shared(c).filter { isParticle(it) }).sortedBy { it.id }
            for (w in words) {
                val target = clauses.firstOrNull { w.id in it.range } ?: clauses.firstOrNull { it.start > w.id } ?: clauses.last()
                val k = clauses.indexOf(target)
                clauses[k] = target.with(listOf(ph(Role.CONNECTOR, listOf(w))))
            }
            return clauses
        }

        /** A clause headed by [head] (a verb, or an omitted one), led by [lead] (a conjunction and its particles). */
        fun clause(head: SyntaxNode, connector: SyntaxNode?, lead: List<SyntaxNode>, depth: Int, extra: List<SyntaxNode> = emptyList()): Clause {
            val phrases = mutableListOf<Phrase>()
            val subs = mutableListOf<Clause>()
            val verb = mutableListOf(head)
            val leadWords = lead.toMutableList()
            var auxiliary = false
            val kids = tree.children(head) + extra
            // a relative adverb opening the clause (ὡς ἔχω) leads it like a conjunction
            var opener: SyntaxNode? = null
            if (connector == null && lead.isEmpty()) {
                val first = kids.filter { !isBarePunct(it) }.minByOrNull { rangeOf(it).first }
                if (first != null && first.id < head.id && pos(first) == 'd' && bare(first) && lemma(first) in RELATIVE_ADVERBS && base(first.relation) == "ADV") {
                    opener = first
                    leadWords += first
                }
            }
            for (c in kids) {
                if (isBarePunct(c) || c === opener) continue
                val rel = base(c.relation)
                val negation = rel in setOf("AuxZ", "AuxY", "AuxV") && lemma(c) in NEGATIONS && bare(c)
                when {
                    negation && leadWords.isNotEmpty() && c.id < leadWords.minOf { it.id } -> leadWords += c  // οὐχ ὅπως
                    negation || rel in setOf("AuxZ", "AuxY", "AuxV") && lemma(c) in MODAL && bare(c) -> verb += c
                    rel == "AuxV" && c.isWord -> { auxiliary = true; verb += c; for (k in tree.children(c)) collect(k, depth + 1, phrases, subs) }
                    isArticle(c) && bare(c) && rel !in CLAUSE_ROLES && mood(head) in "np" -> verb += c  // τὸ λέγειν
                    rel == "AuxZ" && pos(c) == 'r' && bare(c) && pos(head) == 'v' -> verb += c  // a preverb in tmesis
                    else -> collect(c, depth + 1, phrases, subs)
                }
            }
            val main = head in tree.roots || tree.headOf(head)?.isPunctuation == true || base(head.relation) == "PRED"
            phrases += ph(Role.VERB, verb.sortedBy { it.id }, verbLabel(head, main, auxiliary))
            if (leadWords.isNotEmpty()) phrases += ph(Role.CONNECTOR, leadWords.sortedBy { it.id })
            phrases.sortBy { it.start }
            val ownWords = phrases.flatMap { it.words }
            val label = clauseLabel(head, connector, opener, ownWords, auxiliary)
            val ids = ownWords.filter { it.isWord }.map { it.id }
            return Clause(label, phrases, subs.sortedBy { it.start }, depth, if (ids.isEmpty()) rangeOf(head) else ids.min()..ids.max())
        }

        // ---- naming a clause

        fun clauseLabel(head: SyntaxNode, connector: SyntaxNode?, opener: SyntaxNode?, ownWords: List<SyntaxNode>, auxiliary: Boolean): String {
            val rel = base(head.relation)
            val root = head in tree.roots || tree.headOf(head)?.let { it.isPunctuation && it in tree.roots } == true
            val isRelative = { n: SyntaxNode -> lemma(n) in RELATIVES && pos(n) in "pd" }
            // a relative pronoun among the clause's own words, as an attribute too (ἐν ᾧ κρίματι κρίνετε)
            val relative = ownWords.any { it !== head && isRelative(it) } || isRelative(head)
            val firstWord = ownWords.filter { it.isWord }.minByOrNull { it.id }
            val continuing = root && firstWord != null && firstWord.id == tree.nodes.firstOrNull { it.isWord }?.id && isRelative(firstWord)
            val kind = when {
                continuing -> "relative clause, continuing the previous sentence"
                head.artificial && (root || rel == "PRED") -> "main clause, verb understood"
                root || rel == "PRED" -> if ((head.relation ?: "").endsWith("_PA")) "parenthesis" else "main clause"
                connector != null && base(connector.relation) == "AuxC" && connector.isWord -> {
                    val gloss = CONJUNCTIONS[lemma(connector)]
                    if (gloss != null) "${connector.form} clause ($gloss)" else "${connector.form} clause"
                }
                opener != null -> "${opener.form} clause (${RELATIVE_ADVERBS[lemma(opener)]})"
                head.artificial -> "clause, verb understood"
                mood(head) == 'n' && !auxiliary -> "infinitive"
                mood(head) == 'p' && !auxiliary -> "participle"
                relative || rel == "ATR" && isFinite(head) -> "relative clause"
                connector != null && base(connector.relation) == "AuxP" -> "${connector.form} clause"
                // the SBL New Testament capitalises the first word of direct speech
                ownWords.any { lemma(it) in INTERROGATIVES } && rel in setOf("OBJ", "SBJ") ->
                    if (firstWord != null && firstWord.form.first().isUpperCase() && firstWord.id != tree.nodes.firstOrNull { it.isWord }?.id && pos(firstWord) != 'n') "quoted question" else "indirect question"
                rel in setOf("OBJ", "SBJ") && (connector == null || isCoordinator(connector)) -> "quoted or reported clause"
                else -> "clause"
            }
            if (root || rel == "PRED") return kind
            val x = governorLabel(head)
            val function = when (rel) {
                "SBJ" -> "subject of $x"
                "OBJ" -> "object of $x"
                "ADV" -> "modifies $x"
                "ATR" -> "describes $x"
                "PNOM" -> "predicate of $x"
                "ATV", "AtvV" -> "complement of $x"
                "OCOMP" -> "object complement of $x"
                "CO" -> "joined on to $x"
                "ExD" -> "stands apart"
                "APOS" -> "explains $x"
                "" -> ""
                else -> rel.lowercase()
            }
            return if (function.isEmpty() || x == null && rel != "ExD") kind else "$kind · $function"
        }

        fun isTransparent(p: SyntaxNode) = isConnector(p) || isCoordinator(p) || p.isWord && base(p.relation) in setOf("AuxY", "AuxZ")

        /** The word a node hangs on: past its conjunction, preposition, coordinator or a particle it was hung on. */
        fun governor(n: SyntaxNode): SyntaxNode? {
            var p = tree.headOf(n)
            var steps = 0
            while (p != null && isTransparent(p) && steps++ < 20) p = tree.headOf(p)
            return p
        }

        /** How the governing word is named: coordinated nouns by name, an omitted verb as "the understood verb". */
        fun governorLabel(n: SyntaxNode): String? {
            var below = n
            var p = tree.headOf(n)
            var steps = 0
            while (p != null && steps++ < 20) {
                // a member of a coordination hangs on what the coordination hangs on; a shared dependent on the members
                if (isCoordinator(p) && members(p).isNotEmpty() && below !in members(p)) {
                    // shared by coordinated clauses: named by the first; by coordinated words: all of them
                    val ms = members(p)
                    val named = if (ms.any { leadsToClause(it) }) ms.take(1) else ms
                    return named.joinToString(", ") { m -> contentNode(m).let { if (it.artificial) "the understood verb" else Syntax.headLabel(it) } }
                }
                if (!isTransparent(p)) break
                below = p
                p = tree.headOf(p)
            }
            return p?.let { if (it.artificial) "the understood verb" else Syntax.headLabel(it) }
        }

        // ---- lines

        fun isGlue(p: Phrase) = p.role == Role.CONNECTOR || p.role == Role.PARTICLE

        /**
         * A clause as shown: its phrases and inner clauses in the order of the text, connecting
         * words that follow one another on one line. A nested clause of a single phrase (a bare
         * infinitive, a participle) becomes a phrase named after the clause.
         */
        fun view(c: Clause, nested: Boolean): Item {
            val items = (c.phrases.map { it.start to (it as Item) } + c.subs.map { it.start to view(it, nested = true) })
                .sortedBy { it.first }.map { it.second }
            val merged = mutableListOf<Item>()
            for (item in items) {
                val last = merged.lastOrNull()
                if (item is Phrase && isGlue(item) && last is Phrase && isGlue(last)) {
                    merged[merged.size - 1] = Phrase(Role.CONNECTOR, last.words + item.words, "", start = last.start)
                } else merged += item
            }
            val only = merged.singleOrNull()
            if (only != null && c.label.isEmpty()) return only
            // a short clause (εἰ βούλει, καὶ ἀκοῦσαι) reads as one line, the connecting words in front
            val lead = merged.firstOrNull() as? Phrase
            val core = merged.getOrNull(1) as? Phrase
            val short = if (merged.size == 2 && lead != null && isGlue(lead) && core != null && !isGlue(core)) Phrase(core.role, lead.words + core.words, core.label, start = lead.start) else only as? Phrase
            if (nested && short != null) {
                val label = if (short.role == Role.VERB || short.label.isEmpty()) c.label else "${c.label} · ${short.label}"
                return Phrase(short.role, short.words, label, start = short.start)
            }
            return SimpleSyntax.Clause(c.label, merged)
        }
    }
}
