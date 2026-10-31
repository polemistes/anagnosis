"""Hand corrections of the lemmas and parses the merge gives the edition's words (per play), from
the review of pipeline/build/<play>-review.tsv (pipeline/PLAN-drama.md, step 5).

HAND_ANALYSES: "line form" -> (lemma, nine-position Perseus tag), for a word whose lemma is empty
or plainly wrong (the treebank reads another word there, or the analyser chose wrongly).
LEMMA_FIXES: lemma -> lemma, for a lemma spelled otherwise than the dictionaries' headword or
plainly wrong wherever it stands.
"""
from __future__ import annotations

HAND_ANALYSES: dict[str, dict[str, tuple[str, str]]] = {
    "agamemnon": {},
}

LEMMA_FIXES: dict[str, dict[str, str]] = {
    "agamemnon": {},
}
