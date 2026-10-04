"""MACULA's syntax trees of the New Testament as the dependency trees the app shows.

MACULA (github.com/Clear-Bible/macula-greek, SBLGNT/lowfat/*.xml) analyses every sentence as
nested word groups: clauses whose children carry roles (s, v, o, io, o2, p, vc, adv, aux),
noun phrases built by named rules (DetNP, NPofNP, PrepNp ...), coordinations whose later
members sit in "groups" led by their conjunction. The app, like the Perseus treebanks, wants
a dependency tree in the Prague style: a head word for every group, a relation on every word
(PRED, SBJ, OBJ, ATR, ADV, PNOM, OCOMP, ExD, AuxP for a preposition, AuxC for a subordinating
conjunction, AuxY/AuxZ for particles, COORD with members marked _CO), an artificial node for
an understood verb.

convert() walks the groups, chooses heads, and attaches the rest as the Prague treebanks do:
- a clause's head is its finite verb (or infinitive, or participle); a verbless clause gets an
  artificial head "[0]"; the copula is the head and its predicate PNOM, except that a
  periphrastic "ἦν διδάσκων" makes the participle the head and εἰμί its AuxV; a participle
  beside the verb is circumstantial, ADV;
- a preposition heads its phrase (AuxP) and the noun under it bears the function; a
  subordinating conjunction heads its clause (AuxC) likewise; a coordination is headed by its
  conjunction (COORD) with the members marked _CO and anything shared attached to it; where
  there is no conjunction, the punctuation between the members serves, or an artificial node;
- postpositive and sentence particles (δέ, γάρ, οὖν, ἄν) are AuxY on the verb, negations and
  emphasising particles (οὐ, μή, καί "also", γε) AuxZ, vocatives and interjections ExD;
- inside a noun phrase everything but the head is ATR, an appositive included.

The words of a sentence are numbered in the order of the text, the punctuation marks between
them taking numbers too (only those used as COORD/APOS nodes are written out), and artificial
nodes after them. A sentence is named by the id of its first word (40001001001 = Matthew 1:1:1).
"""
from __future__ import annotations

import collections
import re
from dataclasses import dataclass, field
from pathlib import Path

from lxml import etree

LOWFAT_FILES = [
    "01-matthew", "02-mark", "03-luke", "04-john", "05-acts", "06-romans", "07-1corinthians", "08-2corinthians",
    "09-galatians", "10-ephesians", "11-philippians", "12-colossians", "13-1thessalonians", "14-2thessalonians",
    "15-1timothy", "16-2timothy", "17-titus", "18-philemon", "19-hebrews", "20-james", "21-1peter", "22-2peter",
    "23-1john", "24-2john", "25-3john", "26-jude", "27-revelation",
]
XML_ID = "{http://www.w3.org/XML/1998/namespace}id"
PUNCTUATION = ",.;·!?:\u037e\u0387\u00b7"
FINITE = {"indicative", "subjunctive", "optative", "imperative"}

# conjunctions that coordinate: the COORD node of a coordination
COORDINATORS = {"καί", "δέ", "ἀλλά", "ἤ", "οὐδέ", "μηδέ", "τέ", "τε", "εἴτε", "οὔτε", "μήτε", "πλήν", "ἤτοι"}
# connecting words that stand in a clause without governing it: AuxY on the verb
DISCOURSE = {"γάρ", "οὖν", "μέν", "ἄρα", "διό", "τοίνυν", "μέντοι", "διόπερ", "ἄν", "μενοῦν", "μενοῦνγε", "τοιγαροῦν", "ἆρα",
             "ὄφελον", "πώς", "μήτι", "ἄγε"}
# emphasising and negative particles: AuxZ on what they go with
EMPHASIS = {"οὐ", "οὐκ", "οὐχ", "οὐχί", "μή", "γέ", "γε", "περ", "μόνον", "δή", "καί", "ὡς", "ὡσεί", "οὐδέ", "μηδέ", "ναί"}
NEGATIONS = {"οὐ", "οὐκ", "οὐχ", "οὐχί", "μή"}
INTERJECTIONS = {"ἰδού", "ἴδε", "ἀμήν", "οὐαί", "ναί", "ὦ", "ἔα", "οὐά", "ἁλληλουϊά", "ὡσαννά"}
# subordinating conjunctions, and the adverbs MACULA sets at the head of a clause like one
SUBORDINATORS = {
    "ὅτι", "ἵνα", "ὅπως", "ὡς", "ὥστε", "εἰ", "ἐάν", "ὅτε", "ὅταν", "ἐπεί", "ἐπειδή", "ἕως", "πρίν", "μήποτε", "ἄχρι", "μέχρι",
    "καθώς", "ὥσπερ", "καθάπερ", "διότι", "ἐπάν", "ἡνίκα", "ὁσάκις", "εἴπερ", "ἐάνπερ", "ὅπου", "ὅθεν", "καθότι", "καίπερ",
    "ὡσεί", "ὁπότε", "ἐπειδήπερ", "κἄν", "ὁπόταν", "ὡσπερεί", "καθό", "εἴγε", "ἄχρις", "μέχρις", "ἔστε", "ὅπη", "εἴτε", "ὅπου",
}
# verbs with which a second accusative is a complement of the first ("make X Y", "call X Y")
OCOMP_VERBS = {"ποιέω", "ἔχω", "καλέω", "ἡγέομαι", "λέγω", "τίθημι", "παρίστημι", "καθίστημι", "ἐπικαλέω", "ὀνομάζω", "ἀποδείκνυμι",
               "εὑρίσκω", "νομίζω", "κρίνω", "ὁμολογέω", "ἀποκαθίστημι", "λογίζομαι", "ἀναδείκνυμι", "συνίστημι"}
ROLE_RELATION = {"s": "SBJ", "o": "OBJ", "io": "OBJ", "o2": "OBJ", "p": "PNOM", "adv": "ADV", "aux": "ExD", "v": "PRED", "vc": "PRED"}

NOMINAL_HEAD_LAST = {"DetNP", "DetAdj", "DetCL", "DetNump", "All-NP", "QuanNP", "Demo-NP", "NumpNP", "AdjpNp", "AdvpNp", "PronNP",
                     "ofNPNP", "PpNp2Np", "AdvpAdjp", "AdvNp"}
NOMINAL_HEAD_FIRST = {"NPofNP", "NpAdjp", "NpPp", "NP-CL", "NP-Demo", "NP-all", "NpNump", "NpAdvp", "NPDetAdj", "2Advp_h1", "AdjpAdvp",
                      "QuanPp", "AdvPp", "Np-Appos", "AdjpPp", "NpCL"}
CLAUSE_RULES = re.compile(r"^(ClCl|Conj-CL|sub-CL|that-VP|PtclCL|AdvpCL|CLaCL|aCLaCL|Conj\d+CL|EitherOr\d*CL|2CLaCL|CLandCL2|notCLbutCL2CL)")
COORDINATION_RULES = re.compile(r"^(\d|Conj\d|a[A-Z]|NumpNump|ADVaADV|AdvpaAdvp|NpaNp|AdjpaAdjp|EitherOr|not[A-Z]+but|(Np){2,}$|(Pp){2,}$|(Adjp){2,}$|(Cl){2,}$)")


@dataclass
class Node:
    """A node of the dependency tree: a word, a punctuation mark or an artificial node."""
    id: int
    form: str
    lemma: str = ""
    cls: str = ""      # MACULA's word class
    mood: str = ""
    is_word: bool = False
    artificial: bool = False
    xmlid: str = ""
    rel: str = ""
    head: int | None = None
    pos: int = 0        # position in the text, for "what comes first"


@dataclass
class H:
    """What an element reduces to: the node that attaches to the parent and, for a preposition,
    conjunction or coordination, what it governs (which takes the function in its stead)."""
    node: Node
    kind: str = "plain"        # plain | prep | conj | coord | apos | multi (juxtaposed phrases, each hung on the parent)
    content: "H | None" = None
    members: list["H"] = field(default_factory=list)
    start: int = 10 ** 6       # position of the element's first word

    @property
    def anchor(self) -> Node:
        """The node a dependent of this element hangs on: past a preposition or conjunction;
        the COORD node itself, so that a shared dependent is shared."""
        if self.kind in ("prep", "conj") and self.content is not None:
            return self.content.anchor
        if self.kind == "multi" and self.members:
            return self.members[0].anchor
        return self.node

    @property
    def is_participle(self) -> bool:
        return self.kind == "plain" and self.node.cls == "verb" and self.node.mood == "participle"

    @property
    def is_clausal(self) -> bool:
        """Whether a verb (or an understood one) heads the element, through conjunctions and coordinations."""
        if self.kind in ("coord", "apos", "multi"):
            return any(m.is_clausal for m in self.members)
        if self.kind == "conj" and self.content is not None:
            return self.content.is_clausal
        if self.kind == "prep":
            return False
        return self.node.cls == "verb" or self.node.artificial


def _strip(rel: str) -> str:
    return re.sub(r"(_CO|_AP)+$", "", rel)


def kids(el) -> list:
    return [c for c in el if c.tag in ("w", "wg")]


def rule_of(el) -> str:
    return el.get("rule") or el.get("Rule") or ""


def is_group(el) -> bool:
    """A coordination member with its conjunction: <wg type="group"> with no rule, led by a conjunction."""
    if el.tag != "wg" or el.get("type") != "group" or rule_of(el):
        return False
    k = kids(el)
    return bool(k) and k[0].tag == "w" and k[0].get("class") == "conj"


def finite_clause(el) -> bool:
    """A clause (not an articular participle) whose verb is finite: a relative clause after πᾶς."""
    if el.tag != "wg" or el.get("class") != "cl" or rule_of(el) == "DetCL":
        return False
    vs = [c for c in kids(el) if c.tag == "w" and c.get("role") in ("v", "vc")]
    return any(c.get("mood") in FINITE for c in vs)


def is_clause_el(el) -> bool:
    """An element that is a clause or a sequence of clauses (not a phrase): it never becomes a fragment."""
    if el.tag == "w":
        return el.get("class") == "verb"
    return el.get("class") == "cl" or bool(CLAUSE_RULES.match(rule_of(el))) or is_group(el)


def is_particle_word(el) -> bool:
    """A word that connects or colours rather than fills a role: a conjunction, particle, or an adverb used so."""
    if el.tag != "w" or el.get("role"):
        return False
    cls, lemma = el.get("class"), el.get("lemma", "")
    return cls in ("conj", "ptcl", "intj") or (cls == "adv" and (lemma in EMPHASIS or lemma in NEGATIONS or lemma in DISCOURSE
                                                                  or lemma in SUBORDINATORS or lemma in INTERJECTIONS))


class Sentence:
    """One sentence's nodes, numbered in text order, and the tree built over them."""

    def __init__(self, sent):
        self.words: dict[str, Node] = {}              # xml:id -> node
        self.nodes: list[Node] = []                   # the words in text order
        self.punct_after: dict[str, list[Node]] = {}  # xml:id -> punctuation after the word
        self.used_punct: set[int] = set()
        self.extra: list[Node] = []                   # artificial nodes
        ws = sorted(sent.iter("w"), key=lambda w: w.get(XML_ID))
        k = 0
        for w in ws:
            k += 1
            n = Node(k, w.text or "", w.get("lemma", ""), w.get("class", ""), w.get("mood", ""), True, False, w.get(XML_ID), pos=k)
            self.words[n.xmlid] = n
            self.nodes.append(n)
            self.punct_after[n.xmlid] = []
            for c in (w.get("after") or ""):
                if c in PUNCTUATION:
                    k += 1
                    self.punct_after[n.xmlid].append(Node(k, c, pos=k))
        self.next_id = k + 1
        self.id = ws[0].get(XML_ID)[1:]

    def word(self, el) -> Node:
        return self.words[el.get(XML_ID)]

    def artificial(self) -> Node:
        n = Node(self.next_id, "[0]", artificial=True, pos=10 ** 6 + self.next_id)
        self.next_id += 1
        self.extra.append(n)
        return n

    def start_of(self, el) -> int:
        """Where an element (or a list of elements) begins in the text."""
        if isinstance(el, list):
            return min((self.start_of(e) for e in el), default=10 ** 6)
        ids = [el.get(XML_ID)] if el.tag == "w" else [w.get(XML_ID) for w in el.iter("w")]
        return self.words[min(ids)].pos if ids else 10 ** 6

    def punct_before(self, pos: int) -> Node | None:
        """The punctuation mark right before the word at a position, marked as used."""
        prev = [n for n in self.nodes if n.pos < pos]
        marks = self.punct_after.get(prev[-1].xmlid) if prev else None
        if not marks:
            return None
        self.used_punct.add(marks[0].id)
        return marks[0]

    # ---- attaching

    def attach(self, h: H, head: int, rel: str) -> None:
        """Hang an element on a head with a relation: the function goes to what a preposition,
        conjunction or coordination governs."""
        n = h.node
        if h.kind == "prep" and h.content is not None:
            n.head, n.rel = head, "AuxP"
            self.attach(h.content, n.id, rel)
        elif h.kind == "conj" and h.content is not None:
            n.head, n.rel = head, "AuxC"
            self.attach(h.content, n.id, rel)
        elif h.kind == "multi":
            for m in h.members:
                self.attach(m, head, rel)
        elif h.kind in ("coord", "apos"):
            suffix = "_CO" if rel.endswith("_CO") else "_AP" if rel.endswith("_AP") else ""
            n.head = head
            n.rel = ("COORD" if h.kind == "coord" else "APOS") + suffix
            for m in h.members:
                self.attach(m, n.id, _strip(rel) + ("_CO" if h.kind == "coord" else "_AP"))
        else:
            n.head, n.rel = head, rel

    def particle(self, w: Node, head: int) -> None:
        """A connecting or emphasising word on the head it goes with."""
        if w.rel:
            return
        if w.lemma in INTERJECTIONS or w.cls == "intj":
            w.head, w.rel = head, "ExD"
        elif w.lemma in EMPHASIS or w.lemma in NEGATIONS:
            w.head, w.rel = head, "AuxZ"
        else:
            w.head, w.rel = head, "AuxY"


class Converter:
    def __init__(self, s: Sentence):
        self.s = s

    # ---- dispatch

    def build(self, el) -> H:
        if el.tag == "w":
            w = self.s.word(el)
            return H(w, start=w.pos)
        h = self.build_group(el)
        h.start = min(h.start, self.s.start_of(el))
        return h

    def build_group(self, el) -> H:
        rule = rule_of(el)
        k = kids(el)
        if not k:
            return H(self.s.artificial())
        if len(k) == 1:
            return self.build(k[0])
        if is_group(el):
            # a coordination member standing by itself: its conjunction is a particle of it
            h = self.build_sequence(k[1:], el)
            self.s.particle(self.s.word(k[0]), h.anchor.id)
            return h
        if rule == "PrepNp" or el.get("class") == "pp":
            h = self.build_pp(el)
            if h is not None:
                return h
        if rule == "BeVerb" or (el.get("class") == "vp" and not any(c.get("role") for c in k)):
            h = self.build_vp(el)
            if h is not None:
                return h
        if rule in NOMINAL_HEAD_FIRST or rule in NOMINAL_HEAD_LAST:
            return self.build_np(el)
        if el.get("class") == "cl" or CLAUSE_RULES.match(rule) or any(c.get("role") for c in k) or el.get("predication"):
            return self.build_clause(el)
        return self.build_np(el)

    # ---- phrases

    def build_pp(self, el) -> H | None:
        k = kids(el)
        i = next((i for i, c in enumerate(k) if c.tag == "w" and c.get("class") == "prep" and not c.get("role")), None)
        if i is None:
            return None
        prep = self.s.word(k[i])
        rest = [c for j, c in enumerate(k) if j != i and not is_particle_word(c)]
        if not rest:
            return None
        content = self.build_sequence(rest, el)
        for c in k:
            if is_particle_word(c):
                self.s.particle(self.s.word(c), content.anchor.id)
        v = content.anchor
        kind = "conj" if (v.cls == "verb" and v.mood in FINITE and content.kind != "coord") or content.kind == "conj" else "prep"
        return H(prep, kind, content, start=prep.pos)

    def build_vp(self, el) -> H | None:
        """A periphrastic verb: ἦν διδάσκων, the participle heading and εἰμί its auxiliary."""
        k = kids(el)
        ws = [self.s.word(c) for c in k if c.tag == "w"]
        ptcp = [w for w in ws if w.mood == "participle"]
        fin = [w for w in ws if w.mood != "participle"]
        if not (ptcp and fin):
            return None
        for w in fin:
            w.head, w.rel = ptcp[0].id, "AuxV"
        for w in ptcp[1:]:
            w.head, w.rel = ptcp[0].id, "ATR"
        h = H(ptcp[0], start=min(w.pos for w in ws))
        for c in k:
            if c.tag != "w":
                self.s.attach(self.build(c), h.anchor.id, "ADV")
        return h

    def apposition(self, el, k: list) -> H:
        """An appositive is an attribute of what it explains (the Prague APOS node, a comma or an
        artificial node, would only get between the reader and the words)."""
        content = [c for c in k if not is_particle_word(c)]
        h = self.build(content[0])
        for c in content[1:]:
            self.s.attach(self.build(c), h.anchor.id, "ATR")
        for p in k:
            if is_particle_word(p):
                self.s.particle(self.s.word(p), h.anchor.id)
        return h

    def build_np(self, el) -> H:
        rule = rule_of(el)
        k = kids(el)
        if rule == "Np-Appos" or (el.get("type") == "apposition" and any(c.get("junction") == "apposition" for c in k)):
            return self.apposition(el, k)
        particles = [c for c in k if is_particle_word(c)]
        content = [c for c in k if not is_particle_word(c)]
        if not content:
            content, particles = [k[0]], k[1:]
        # phrases merely juxtaposed (ἀπὸ Ἀβραὰμ ἕως Δαυίδ, 2Pp): each hangs on the parent by itself
        if re.match(r"^(2Np|2Pp|NumpNump|2Advp)$", rule) and not any(is_group(c) for c in content) and len(content) > 1:
            hs = [self.build(c) for c in content]
            for p in particles:
                self.s.particle(self.s.word(p), hs[0].anchor.id)
            return H(hs[0].node, "multi", members=hs, start=min(h.start for h in hs))
        # a coordination: members with their conjunctions in groups, or juxtaposed with punctuation
        if any(is_group(c) for c in content) or COORDINATION_RULES.match(rule):
            members = [(kids(c)[1:], self.s.word(kids(c)[0])) if is_group(c) else (c, None) for c in content]
            return self.coordinate(members, [self.s.word(p) for p in particles], el)
        if rule in NOMINAL_HEAD_LAST and len(content) > 1 and finite_clause(content[-1]):
            head_el = content[0]
        elif rule in NOMINAL_HEAD_LAST:
            head_el = content[-1]
        elif rule in NOMINAL_HEAD_FIRST:
            head_el = content[0]
        else:
            nominal = [c for c in content if (c.tag == "w" and c.get("class") in ("noun", "pron", "adj", "num", "verb", "det"))
                       or (c.tag == "wg" and c.get("class") in ("np", "cl", "adjp", "nump"))]
            head_el = nominal[0] if nominal else content[0]
        h = self.build(head_el)
        if rule == "NP-CL" and h.is_clausal and all(c is head_el or (c.tag == "wg" and c.get("class") == "cl") for c in content):
            # clauses standing for a noun, one after another (ὃ ἦν ἀπʼ ἀρχῆς, ὃ ἀκηκόαμεν ...): coordinated
            return self.coordinate([(h, None)] + [(c, None) for c in content if c is not head_el], [self.s.word(p) for p in particles], el)
        for c in content:
            if c is head_el:
                continue
            rel = "AuxZ" if c.tag == "w" and c.get("class") == "adv" and c.get("lemma") in EMPHASIS else "ATR"
            self.s.attach(self.build(c), h.anchor.id, rel)
        for p in particles:
            self.s.particle(self.s.word(p), h.anchor.id)
        return h

    # ---- clauses

    def build_sequence(self, elements: list, parent) -> H:
        """Elements standing together (what follows a conjunction, the parts of a clause)."""
        if len(elements) == 1:
            return self.build(elements[0])
        return self.build_clause(parent, elements)

    def is_subordinator(self, w, rule: str) -> bool:
        lemma, cls = w.get("lemma", ""), w.get("class")
        if rule == "Conj-CL":
            return False  # a connector to the sentence before: a particle
        if lemma in SUBORDINATORS:
            return True
        return rule in ("sub-CL", "that-VP") and cls in ("conj", "adv") and lemma not in COORDINATORS and lemma not in DISCOURSE

    def build_clause(self, el, elements: list | None = None) -> H:
        k = elements if elements is not None else kids(el)
        rule = rule_of(el)
        if k and is_particle_word(k[0]) and self.is_subordinator(k[0], rule) and len(k) > 1:
            conj = self.s.word(k[0])
            return H(conj, "conj", self.build_sequence(k[1:], el), start=conj.pos)

        # a preposition standing bare among the parts of a clause governs what follows it
        prebuilt: list[tuple] = []   # (element, H): a preposition with the phrase after it
        prebuilt_roles: dict = {}
        rest = []
        i = 0
        while i < len(k):
            c = k[i]
            if c.tag == "w" and c.get("class") == "prep" and not c.get("role") and i + 1 < len(k) and not is_particle_word(k[i + 1]) \
                    and not (k[i + 1].tag == "w" and k[i + 1].get("class") == "verb"):
                prep = self.s.word(c)
                prebuilt.append((k[i + 1], H(prep, "prep", self.build(k[i + 1]), start=prep.pos)))
                i += 2
            else:
                rest.append(c)
                i += 1
        k = rest
        verbs = [c for c in k if c.get("role") in ("v", "vc")]
        roles = [c for c in k if c.get("role") and c.get("role") not in ("v", "vc")]
        particles = [self.s.word(c) for c in k if is_particle_word(c)]
        others = [c for c in k if not c.get("role") and not is_particle_word(c)]

        # the verb: the finite one (or the copula, or an infinitive); a participle beside it is circumstantial
        head: H | None = None
        members: list[tuple] = []      # (H or [elements], leading conjunction node or None)
        circumstantial: list[H] = []
        if verbs:
            built = [(c, self.build(c)) for c in verbs]
            mains = [(c, h) for c, h in built if c.get("role") == "vc" or h.kind != "plain"
                     or (h.node.cls == "verb" and h.node.mood in FINITE | {"infinitive"})]
            if not mains:
                mains = built[:1]
            head = mains[0][1]
            complements: list[H] = []
            for c, h in built:
                if h is head:
                    continue
                if h.is_participle:
                    circumstantial.append(h)
                elif h.kind == "plain" and h.node.cls == "verb" and h.node.mood == "infinitive" and head.anchor.mood in FINITE:
                    complements.append(h)  # δύναται ... κρυβῆναι
                else:
                    members.append((h, None))
            for h in complements:
                self.s.attach(h, head.anchor.id, "OBJ")
            # periphrasis: a copula with a bare participle as its predicate
            p_children = [c for c in roles if c.get("role") == "p"]
            if mains[0][0].get("role") == "vc" and p_children:
                pc = p_children[0]
                hp = self.build(pc)
                periphrastic = (hp.is_participle or (hp.kind == "coord" and all(m.is_participle or m.node.artificial for m in hp.members))) and rule_of(pc) != "DetCL"
                if periphrastic:
                    cop = head.anchor
                    cop.head, cop.rel = hp.anchor.id, "AuxV"
                    head = hp
                else:
                    self.s.attach(hp, head.anchor.id, self.role_relation(pc, head))
                roles = [c for c in roles if c is not pc]

        # the clauses standing beside: members of a sequence, or circumstantial participles
        plain_others = [(c, h) for c, h in prebuilt if not c.get("role")]
        for c, h in prebuilt:
            if c.get("role"):
                roles.append(c)
                prebuilt_roles[c] = h
        for c in others:
            if is_group(c):
                members.append((kids(c)[1:], self.s.word(kids(c)[0])))
            else:
                plain_others.append((c, self.build(c)))
        # a participle clause, or a clause led by a subordinating conjunction, modifies the clause
        # beside it; where there is nothing else, the last one heads and the others go with it;
        # where a coordination follows, it is the first member
        modifiers = [(c, h) for c, h in plain_others if (h.is_participle and rule_of(c) != "DetCL") or h.kind == "conj"]
        if not verbs and len(modifiers) == len(plain_others) and modifiers:
            modifiers = [] if members else modifiers[:-1]
        for c, h in plain_others:
            if (c, h) in modifiers:
                circumstantial.append(h)
            else:
                members.append((h, None))

        # a role-bearing phrase among clauses, with no verb of its own: the rest of a clause
        # whose verb is understood (an answer, an elliptic member of a coordination)
        if head is None and members:
            for c in list(roles):
                if is_clause_el(c) or c.get("role") == "aux":
                    continue
                art = self.s.artificial()
                self.s.attach(self.build(c), art.id, self.role_relation(c, None))
                members.append((H(art, start=self.s.start_of(c)), None))
                roles.remove(c)

        if head is None and members and all(not isinstance(m, list) and not m.is_clausal for m, _l in members):
            # phrases standing as a clause (μήτε ἐν τῷ οὐρανῷ): the predicate of an understood verb
            art = self.s.artificial()
            for m, lead in members:
                self.s.attach(m, art.id, "ADV" if m.kind == "prep" else "PNOM")
                if lead is not None:
                    self.s.particle(lead, art.id)
            members = [(H(art, start=min(m.start for m, _l in members)), None)]
        all_members = ([(head, None)] if head is not None else []) + members
        if not all_members:
            result = H(self.s.artificial())
        elif len(all_members) == 1:
            m, lead = all_members[0]
            result = self.build_sequence(m, el) if isinstance(m, list) else m
            if lead is not None:
                self.s.particle(lead, result.anchor.id)
        else:
            result = self.coordinate(all_members, particles, el)
        anchor = result.anchor
        for h in circumstantial:
            self.s.attach(h, anchor.id, "ADV")
        for c in roles:
            self.s.attach(prebuilt_roles.get(c) or self.build(c), anchor.id, self.role_relation(c, head))
        for p in particles:
            self.s.particle(p, anchor.id)
        return result

    def coordinate(self, members: list, loose: list[Node], el) -> H:
        """members: (H, or an element, or a list of elements; the conjunction leading it or None).
        The COORD node is the first coordinating conjunction leading a member after the first,
        else one standing loose among the members, else the first member's, else the punctuation
        before the second member, else an artificial node. Other conjunctions are AuxY on it,
        sentence particles AuxY on their member, a negation AuxZ on the member it precedes."""
        built: list[tuple[int, H, Node | None]] = []
        for m, lead in members:
            if isinstance(m, H):
                h = m
            elif isinstance(m, list):
                h = self.build_sequence(m, el)
                h.start = min(h.start, self.s.start_of(m))
            else:
                h = self.build(m)
                h.start = min(h.start, self.s.start_of(m))
            if lead is not None:
                h.start = min(h.start, lead.pos)
            built.append((h.start, h, lead))
        built.sort(key=lambda t: t[0])
        hs = [h for _, h, _ in built]
        leads = [l for _, _, l in built]
        if len(hs) == 1:
            if leads[0] is not None:
                self.s.particle(leads[0], hs[0].anchor.id)
            for p in loose:
                self.s.particle(p, hs[0].anchor.id)
            return hs[0]
        candidates = [l for l in leads[1:] if l is not None and l.lemma in COORDINATORS] \
            + [p for p in loose if p.lemma in COORDINATORS] \
            + ([leads[0]] if leads[0] is not None and leads[0].lemma in COORDINATORS else [])
        if candidates:
            coord = candidates[0]
        else:
            coord = self.s.punct_before(built[1][0]) or self.s.artificial()
        h = H(coord, "coord", members=hs, start=built[0][0])
        for l, m in zip(leads, hs):
            if l is not None and l is not coord:
                self.s.particle(l, coord.id if l.lemma in COORDINATORS else m.anchor.id)
        for p in loose:
            if p is coord:
                continue
            if p.lemma in NEGATIONS:
                after = [m for m in hs if m.start > p.pos]
                self.s.particle(p, (after[0] if after else hs[0]).anchor.id)
            else:
                self.s.particle(p, coord.id)
        return h

    def role_relation(self, c, head: H | None) -> str:
        role = c.get("role")
        if c.tag == "w":
            lemma = c.get("lemma", "")
            if lemma in NEGATIONS or lemma in EMPHASIS:
                return "AuxZ"
            if lemma in DISCOURSE:
                return "AuxY"
        nominal = (c.tag == "w" and c.get("class") in ("noun", "adj", "pron", "num", "det")) or (c.tag == "wg" and c.get("class") in ("np", "adjp", "nump"))
        if role == "o2":
            return "OCOMP" if nominal and head is not None and head.anchor.lemma in OCOMP_VERBS else "OBJ"
        if role == "p" and c.tag == "w" and c.get("class") == "adv":
            return "ADV"
        if role in ("s", "o", "io") and (rule_of(c) in ("PrepNp", "2Pp") or (c.tag == "wg" and c.get("class") == "pp")):
            return "ADV"  # a prepositional phrase where the subject or object is understood ("from Abraham to David [generations]")
        return ROLE_RELATION.get(role, "ATR")


def convert_sentence(sent) -> Sentence:
    s = Sentence(sent)
    top = kids(sent)
    conv = Converter(s)
    h = conv.build(top[0]) if len(top) == 1 else conv.build_clause(sent, top)
    role = top[0].get("role")
    if role and role not in ("v", "vc") and h.anchor.cls != "verb" and not h.anchor.artificial:
        # a phrase standing as the sentence: the predicate of an understood verb
        art = s.artificial()
        art.head, art.rel = 0, "PRED"
        s.attach(h, art.id, conv.role_relation(top[0], None))
    else:
        s.attach(h, 0, "PRED")
    # every word must hang somewhere: what the rules left out hangs on the root as ExD
    roots = [n for n in s.nodes + s.extra if n.head == 0]
    root = roots[0].id if roots else 0
    for n in s.nodes + s.extra:
        if n.head is None and (n.is_word or n.artificial):
            n.head, n.rel = root, "ExD"
            s.unplaced = getattr(s, "unplaced", 0) + 1
            print(f"  left over: {n.form} in {s.id}")
    return s


def convert(sources: Path) -> tuple[dict[str, tuple[str, int, str, int]], list[dict], collections.Counter]:
    """(by xml:id: (sentence, word_id, relation, head); the nodes beyond the words; statistics)."""
    lowfat = sources / "nt" / "macula" / "SBLGNT" / "lowfat"
    by_word: dict[str, tuple[str, int, str, int]] = {}
    nodes: list[dict] = []
    stats: collections.Counter = collections.Counter()
    for name in LOWFAT_FILES:
        root = etree.parse(str(lowfat / f"{name}.xml")).getroot()
        for sent in root.iter("sentence"):
            s = convert_sentence(sent)
            stats["sentences"] += 1
            stats["words left over, hung on the root"] += getattr(s, "unplaced", 0)
            for n in s.nodes:
                by_word[n.xmlid] = (s.id, n.id, n.rel, n.head or 0)
                stats["rel " + _strip(n.rel)] += 1
            for marks in s.punct_after.values():
                for p in marks:
                    if p.id in s.used_punct:
                        nodes.append({"sentence": s.id, "word_id": str(p.id), "form": p.form, "lemma": "", "postag": "u--------",
                                      "relation": p.rel, "head": str(p.head or 0), "artificial": ""})
                        stats["punctuation nodes"] += 1
            for a in s.extra:
                # an understood verb is tagged as a verb; an understood coordinator has no tag
                nodes.append({"sentence": s.id, "word_id": str(a.id), "form": a.form, "lemma": "",
                              "postag": "" if _strip(a.rel) == "COORD" else "v--------",
                              "relation": a.rel, "head": str(a.head or 0), "artificial": "1"})
                stats["artificial nodes"] += 1
                stats["artificial " + _strip(a.rel)] += 1
            # a tree: every head is a node of the sentence and no path loops back
            ids = {n.id for n in s.nodes} | s.used_punct | {a.id for a in s.extra}
            heads = {n.id: n.head for n in s.nodes + s.extra if n.id in ids}
            for marks in s.punct_after.values():
                for p in marks:
                    if p.id in s.used_punct:
                        heads[p.id] = p.head
            for i in ids:
                seen = set()
                cur = i
                while cur and cur in heads and cur not in seen:
                    seen.add(cur)
                    cur = heads[cur]
                if cur and cur not in heads:
                    stats["dangling heads"] += 1
                elif cur in seen:
                    stats["cycles"] += 1
    return by_word, nodes, stats
