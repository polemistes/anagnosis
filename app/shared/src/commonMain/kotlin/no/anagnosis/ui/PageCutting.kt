package no.anagnosis.ui

/**
 * Cutting a text's rows into pages, by their measured heights alone (see paginate in ReaderScreen).
 */
internal object PageCutting {
    /**
     * Cuts the rows [from, to) into pages from the front: the page indices, each a range of
     * rows. A row goes on the page while the Greek ([heights]) fits [pageHeight] and the
     * translation beside it ([enHeights]) fits [enPageHeight]. A heading ([headings]: a section
     * heading or a speaker's name) is never left at a page's foot: it goes on the page only
     * with every heading after it and the first row that is not one (a strophe's heading, its
     * speaker and its first verse: Ajax 220–221, where "Strophe 1" stood alone at the foot).
     */
    fun forward(heights: IntArray, enHeights: IntArray, headings: BooleanArray, from: Int, to: Int, pageHeight: Int, enPageHeight: Int): List<IntRange> {
        val pages = mutableListOf<IntRange>()
        var start = from
        var used = 0
        var usedEn = 0
        var i = from
        while (i < to) {
            // the row with the headings and the first other row that follow it
            var needed = heights[i]
            var neededEn = enHeights[i]
            if (headings[i]) {
                var j = i + 1
                while (j < to) {
                    needed += heights[j]; neededEn += enHeights[j]
                    if (!headings[j]) break
                    j++
                }
            }
            if (i > start && (used + needed > pageHeight || usedEn + neededEn > enPageHeight)) {
                pages += start until i
                start = i; used = 0; usedEn = 0
                continue
            }
            used += heights[i]; usedEn += enHeights[i]; i++
        }
        if (i > start) pages += start until i
        return pages
    }
}
