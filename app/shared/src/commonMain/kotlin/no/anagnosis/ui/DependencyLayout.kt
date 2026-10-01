package no.anagnosis.ui

/**
 * Pure layout helper of the dependency diagram, kept apart from the drawing so that it can be tested.
 */

/**
 * The height level of each arc (1 nearest the words): one more than the highest arc whose span
 * lies within its own, so that an arc never passes through the arcs it bridges.
 */
internal fun arcLevels(spans: List<Pair<Float, Float>>): List<Int> {
    val order = spans.indices.sortedBy { spans[it].second - spans[it].first }
    val levels = IntArray(spans.size)
    for (i in order) {
        var level = 1
        for (j in order) {
            if (j == i || levels[j] == 0) continue
            if (spans[j].first >= spans[i].first && spans[j].second <= spans[i].second) level = maxOf(level, levels[j] + 1)
        }
        levels[i] = level
    }
    return levels.toList()
}
