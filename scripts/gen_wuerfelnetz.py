#!/usr/bin/env python3
"""
Generate Würfelnetz (cube net) questions with answers verified by folding.
Stdlib only, zero AI tokens.

NOTE: The official Reihungstest cube task is tipping/rotation only (see
gen_wuerfel.py). Net questions are EXTRA spatial practice and labelled so in
the `source` field.

Net text format (inside question_de / question_en), one line:
    Netz: . A . . / B C D E / . F . .      (EN: "Net: ...")
  rows are separated by " / ", cells by single spaces, "." = empty square,
  any other token = a face symbol (single character, all six distinct).
  Rows are equally long. The quiz engine draws this line as an SVG.

Question types (id prefix):
  wnetz-opp   Which face is opposite to X?                     (1 correct)
  wnetz-view  Which view (top/front/right) can be folded?       (1 correct)
  wnetz-adj   Which faces touch X in the cube but are not
              next to X in the net?                             (1-3 correct)

Verification: every answer is recomputed with the algebraic fold used for
generation AND re-checked from the question text with an independent
3D-rotation fold (--verify). See --selftest.

Usage:
    python3 gen_wuerfelnetz.py --count 20 --seed 202609 --output /tmp/wuerfelnetz.json
    python3 gen_wuerfelnetz.py --verify /tmp/wuerfelnetz.json
    python3 gen_wuerfelnetz.py --selftest
"""

import json, random, argparse, sys, re
from collections import Counter, deque

# ── Vector helpers ───────────────────────────────────────────────────────

def neg(v): return (-v[0], -v[1], -v[2])
def dot(a, b): return a[0]*b[0] + a[1]*b[1] + a[2]*b[2]
def cross(a, b):
    return (a[1]*b[2] - a[2]*b[1], a[2]*b[0] - a[0]*b[2], a[0]*b[1] - a[1]*b[0])

DIRS = {'right': (0, 1), 'left': (0, -1), 'up': (-1, 0), 'down': (1, 0)}  # (dr, dc)

def net_neighbours(cell, cells):
    r, c = cell
    return [(r+dr, c+dc) for dr, dc in DIRS.values() if (r+dr, c+dc) in cells]

# ── Fold 1: algebraic (used for generation) ──────────────────────────────

def fold_algebraic(cells, base):
    """cells: iterable of (r,c). Returns {cell: outward normal} for a cube
    folded with the printed side outside and `base` facing the viewer (+z),
    or None if the shape is not a cube net."""
    cells = set(cells)
    state = {base: ((0, 0, 1), (1, 0, 0), (0, 1, 0))}  # n, ex (net right), ey (net up)
    queue = deque([base])
    while queue:
        cell = queue.popleft()
        n, ex, ey = state[cell]
        for name, (dr, dc) in DIRS.items():
            nxt = (cell[0] + dr, cell[1] + dc)
            if nxt not in cells:
                continue
            if name == 'right':  new = (ex, neg(n), ey)
            elif name == 'left': new = (neg(ex), n, ey)
            elif name == 'up':   new = (ey, ex, neg(n))
            else:                new = (neg(ey), ex, n)
            if nxt in state:
                if state[nxt][0] != new[0]:
                    return None
                continue
            state[nxt] = new
            queue.append(nxt)
    if len(state) != len(cells):
        return None
    normals = {c: s[0] for c, s in state.items()}
    if len(set(normals.values())) != 6 or len(cells) != 6:
        return None
    return normals

# ── Fold 2: geometric, independent (used for --verify) ───────────────────

def _matmul(A, B):
    return [[sum(A[i][k]*B[k][j] for k in range(3)) for j in range(3)] for i in range(3)]

def _matvec(A, v):
    return tuple(sum(A[i][k]*v[k] for k in range(3)) for i in range(3))

def _rot(axis, s):
    """Rotation by s*90 degrees (s=+1/-1) about unit axis (Rodrigues, cos=0)."""
    x, y, z = axis
    K = [[0, -z, y], [z, 0, -x], [-y, x, 0]]
    K2 = _matmul(K, K)
    return [[(1 if i == j else 0) + s*K[i][j] + K2[i][j] for j in range(3)] for i in range(3)]

def fold_geometric(cells, base):
    """Fold by rotating squares about their shared edges (rigid transforms in
    3D), each child folded to the back side of its parent. Returns
    {cell: outward normal} or None."""
    cells = set(cells)
    I = [[1, 0, 0], [0, 1, 0], [0, 0, 1]]
    T = {base: (I, (0, 0, 0))}
    queue = deque([base])
    while queue:
        p = queue.popleft()
        Rp, tp = T[p]
        for dr, dc in DIRS.values():
            q = (p[0] + dr, p[1] + dc)
            if q not in cells or q in T:
                continue
            d = (dc, -dr, 0)                                  # flat direction p -> q
            centre_p = (p[1], -p[0], 0)
            e = tuple(centre_p[i] + 0.5*d[i] for i in range(3))   # edge midpoint
            axis = (-d[1], d[0], 0)
            chosen = None
            for s in (1, -1):
                Rot = _rot(axis, s)
                centre_q = (p[1] + dc, -(p[0] + dr), 0)
                moved = _matvec(Rot, tuple(centre_q[i] - e[i] for i in range(3)))
                if moved[2] < -0.4:                           # folds toward -z (back)
                    chosen = Rot
            Re = _matvec(chosen, e)
            shift = tuple(e[i] - Re[i] for i in range(3))
            Rq = _matmul(Rp, chosen)
            tq = tuple(a + b for a, b in zip(_matvec(Rp, shift), tp))
            T[q] = (Rq, tq)
            queue.append(q)
    normals = {c: tuple(int(round(x)) for x in _matvec(T[c][0], (0, 0, 1))) for c in cells}
    if len(T) != len(cells) or len(set(normals.values())) != 6:
        return None
    return normals

# ── The 11 nets ──────────────────────────────────────────────────────────

TRANSFORMS = [
    lambda r, c: (r, c), lambda r, c: (r, -c), lambda r, c: (-r, c), lambda r, c: (-r, -c),
    lambda r, c: (c, r), lambda r, c: (c, -r), lambda r, c: (-c, r), lambda r, c: (-c, -r),
]

def normalise(cells):
    mr = min(r for r, _ in cells); mc = min(c for _, c in cells)
    return frozenset((r - mr, c - mc) for r, c in cells)

def canonical(cells):
    return min(tuple(sorted(normalise([t(r, c) for r, c in cells]))) for t in TRANSFORMS)

def all_hexominoes():
    shapes = {canonical([(0, 0)])}
    for _ in range(5):
        grown = set()
        for shp in shapes:
            cs = set(shp)
            for (r, c) in cs:
                for dr, dc in DIRS.values():
                    n = (r + dr, c + dc)
                    if n not in cs:
                        grown.add(canonical(cs | {n}))
        shapes = grown
    return sorted(shapes)

def cube_nets():
    nets = []
    for shp in all_hexominoes():
        a = fold_algebraic(shp, shp[0])
        if a is not None:
            nets.append(shp)
    return nets

NETS = cube_nets()
assert len(NETS) == 11, f"expected 11 distinct cube nets, found {len(NETS)}"

# ── Geometry queries on a folded net ─────────────────────────────────────

def view_valid(normals_by_sym, top, front, right):
    """True iff faces (top, front, right) meet at a corner in the correct
    handedness: top = front x right (no opposite pair, no mirror image)."""
    nt, nf, nr = normals_by_sym[top], normals_by_sym[front], normals_by_sym[right]
    return cross(nf, nr) == nt

def cyc_canon(triple):
    t = list(triple)
    return min(tuple(t[i:] + t[:i]) for i in range(3))

def opposite_pairs(nsym):
    pairs = set()
    for s, n in nsym.items():
        o = next(k for k, v in nsym.items() if v == neg(n))
        pairs.add(tuple(sorted((s, o))))
    return sorted(pairs)

# ── Text helpers ─────────────────────────────────────────────────────────

SYMBOL_SETS = [
    ['A', 'B', 'C', 'D', 'E', 'F'],
    ['1', '2', '3', '4', '5', '6'],
    ['●', '★', '+', '△', '□', '◆'],
    ['♥', '◆', '↑', '↓', '☽', '☀'],
    ['X', 'O', '△', '□', '♥', '★'],
    ['R', 'G', 'B', 'Y', 'P', 'W'],
    ['α', 'β', 'γ', 'δ', 'ε', 'ζ'],
    ['♠', '♣', '♦', '♥', '★', '●'],
]

def jn(items, word):
    items = list(items)
    if len(items) <= 1:
        return ''.join(items)
    return ', '.join(items[:-1]) + f' {word} ' + items[-1]

def net_line(cells_sym):
    rs = [r for r, _ in cells_sym]; cs = [c for _, c in cells_sym]
    rows = []
    for r in range(min(rs), max(rs) + 1):
        rows.append(' '.join(cells_sym.get((r, c), '.') for c in range(min(cs), max(cs) + 1)))
    return ' / '.join(rows)

def parse_net(text):
    m = re.search(r'(?:Netz|Net):\s*([^\n]+)', text)
    if not m:
        return None
    rows = [row.split() for row in m.group(1).strip().split(' / ')]
    if len({len(r) for r in rows}) != 1:
        return None
    cells = {(ri, ci): tok for ri, row in enumerate(rows) for ci, tok in enumerate(row) if tok != '.'}
    return cells

def fold_steps(cells_sym, X):
    """Shared step-by-step folding narrative with X as the bottom face.
    Returns (de_lines, en_lines, side_syms, top_sym, net_nb_syms)."""
    sym_cell = {s: c for c, s in cells_sym.items()}
    base = sym_cell[X]
    nrm = fold_algebraic(set(cells_sym), base)
    parent = {base: None}; dist = {base: 0}; queue = deque([base])
    while queue:
        cur = queue.popleft()
        for nb in net_neighbours(cur, cells_sym):
            if nb not in parent:
                parent[nb] = cur; dist[nb] = dist[cur] + 1; queue.append(nb)
    n0 = (0, 0, 1)
    nb_syms = sorted(cells_sym[c] for c in net_neighbours(base, cells_sym))
    side = {c for c in cells_sym if c != base and dot(nrm[c], n0) == 0}
    top = next(cells_sym[c] for c in cells_sym if nrm[c] == neg(n0))
    de = [f"Fläche {X} liegt unten (bedruckte Seite außen)."]
    en = [f"Face {X} is the bottom (printed side outside)."]
    if len(nb_syms) == 1:
        de.append(f"Ihr Nachbar im Netz ({nb_syms[0]}) klappt hoch und wird Seitenwand.")
        en.append(f"Its neighbour in the net ({nb_syms[0]}) folds up and becomes a side wall.")
    else:
        de.append(f"Die Nachbarn im Netz ({jn(nb_syms, 'und')}) klappen hoch und werden Seitenwände.")
        en.append(f"The neighbours in the net ({jn(nb_syms, 'and')}) fold up and become side walls.")
    for c in sorted((c for c in cells_sym if dist[c] >= 2), key=lambda c: (dist[c], cells_sym[c])):
        s, p = cells_sym[c], cells_sym[parent[c]]
        if c in side:
            de.append(f"{s} hängt an {p} und wird ebenfalls Seitenwand.")
            en.append(f"{s} is attached to {p} and also becomes a side wall.")
        else:
            de.append(f"{s} hängt an {p} und klappt nach oben zum Deckel.")
            en.append(f"{s} is attached to {p} and folds over to become the lid (top).")
    sides = sorted(cells_sym[c] for c in side)
    return de, en, sides, top, nb_syms

def numbered(lines):
    return '<br>'.join(f"{i+1}. {l}" for i, l in enumerate(lines))

def alt(title_de, title_en, text_de, text_en):
    return {"title_de": title_de, "title_en": title_en, "text_de": text_de, "text_en": text_en}

MISTAKES = {
    'opp': ("Typische Fehler: (1) Gegenflächen mit Nachbarn im Netz verwechselt – Felder, die im Netz direkt nebeneinander liegen, sind nie gegenüber. (2) Nur bis zur ersten Faltkante gedacht.",
            "Common mistakes: (1) Confusing opposite faces with neighbours in the net – squares that touch in the net are never opposite. (2) Only folding in your head up to the first edge."),
    'view': ("Typische Fehler: (1) Nur geprüft, ob die drei Flächen benachbart sind, nicht die Drehrichtung. (2) Spiegelbild gewählt. (3) Zwei Gegenflächen in einer Ansicht zugelassen.",
             "Common mistakes: (1) Checking only that the three faces are neighbours, not their turning direction. (2) Choosing the mirror image. (3) Allowing two opposite faces in one view."),
    'adj': ("Typische Fehler: (1) Nur die Nachbarn im Netz gezählt. (2) Die Gegenfläche als Nachbar angekreuzt. (3) Nicht alle richtigen Antworten angekreuzt.",
            "Common mistakes: (1) Counting only the neighbours in the net. (2) Ticking the opposite face as a neighbour. (3) Not ticking all correct answers."),
}

# ── Question builders ────────────────────────────────────────────────────

def make_net(rng):
    base_shape = rng.choice(NETS)
    t = rng.choice(TRANSFORMS)
    shape = normalise([t(r, c) for r, c in base_shape])
    symbols = list(rng.choice(SYMBOL_SETS))
    rng.shuffle(symbols)
    cells = sorted(shape)
    cells_sym = dict(zip(cells, symbols))
    base = cells[0]
    nrm = fold_algebraic(set(cells_sym), base)
    assert nrm is not None
    nsym = {cells_sym[c]: n for c, n in nrm.items()}
    return cells_sym, nsym

def common_fields(qid, difficulty, tags, qde, qen, options, correct, exp_de, exp_en, alts, kind):
    opts = [f"{chr(97+i)}) {o}" for i, o in enumerate(options)]
    return {
        "id": qid, "quizId": "cognitive", "difficulty": difficulty, "tags": tags,
        "question_de": qde, "question_en": qen,
        "options_de": opts, "options_en": list(opts) if kind != 'view' else None,
        "correct": correct,
        "explanation_de": exp_de, "explanation_en": exp_en,
        "explanations_alt": alts,
        "mistakes_de": MISTAKES[kind][0], "mistakes_en": MISTAKES[kind][1],
        "links": [{"url": "../knowledge/reihungstest-de.html", "label": "Würfel-Glossar"}],
        "source": "Zusatzübung Würfelnetz (generiert, gen_wuerfelnetz.py) – kein offizielles Prüfungsformat",
    }

def row_rule_partner(cells_sym, X):
    """(mid_sym, other_end_sym) if X is an end of a straight line of 3 squares."""
    sym_cell = {s: c for c, s in cells_sym.items()}
    r, c = sym_cell[X]
    for dr, dc in DIRS.values():
        mid, end = (r + dr, c + dc), (r + 2*dr, c + 2*dc)
        if mid in cells_sym and end in cells_sym:
            return cells_sym[mid], cells_sym[end]
    return None

def gen_opposite(rng, idx):
    cells_sym, nsym = make_net(rng)
    X = rng.choice(sorted(nsym))
    Y = next(s for s, n in nsym.items() if n == neg(nsym[X]))
    others = [s for s in nsym if s != X]
    rng.shuffle(others)
    correct = [others.index(Y)]
    nl = net_line(cells_sym)
    qde = f"WÜRFELNETZ: Das Netz wird zu einem Würfel gefaltet (bedruckte Seite außen).\nNetz: {nl}\nWelche Fläche liegt im gefalteten Würfel gegenüber von {X}?"
    qen = f"CUBE NET: The net is folded into a cube (printed side outside).\nNet: {nl}\nWhich face is opposite to {X} in the folded cube?"
    de, en, sides, top, nb = fold_steps(cells_sym, X)
    de.append(f"Übrig bleibt genau eine Fläche für den Deckel: {top}. Sie liegt {X} gegenüber.")
    en.append(f"Exactly one face is left for the lid: {top}. It is opposite {X}.")
    assert top == Y
    sym_cell = {s: c for c, s in cells_sym.items()}
    extra = sorted(s for s in nsym if s != X and s != Y and s not in nb)
    ex_de = f" Durch das Falten stoßen außerdem {jn(extra, 'und')} an {X}." if extra else ""
    ex_en = f" Folding additionally brings {jn(extra, 'and')} next to {X}." if extra else ""
    alts = [alt(
        "Ausschlussverfahren (Nachbarn streichen)", "Elimination (cross out the neighbours)",
        f"Ein Würfel hat 4 Nachbarflächen und 1 Gegenfläche. Direkt neben {X} im Netz: {jn(nb, 'und')} – diese grenzen an {X}.{ex_de} "
        f"Alle vier Nachbarn sind gestrichen, übrig bleibt {Y}.",
        f"A cube has 4 neighbouring faces and 1 opposite face. Directly next to {X} in the net: {jn(nb, 'and')} – these touch {X}.{ex_en} "
        f"All four neighbours are crossed out, leaving {Y}.")]
    rp = row_rule_partner(cells_sym, X)
    if rp and rp[1] == Y:
        alts.append(alt(
            "Reihenregel: ein Feld dazwischen", "Row rule: one square in between",
            f"Liegen drei Felder in einer geraden Reihe, sind das erste und das dritte Feld Gegenflächen. "
            f"Hier liegt {X} – {rp[0]} – {Y} in einer Reihe. Also ist {Y} gegenüber von {X}.",
            f"If three squares lie in a straight row, the first and the third are opposite faces. "
            f"Here {X} – {rp[0]} – {Y} are in a row. So {Y} is opposite {X}."))
    else:
        pairs = opposite_pairs(nsym)
        ptxt = jn([f"({a}, {b})" for a, b in pairs], 'und')
        ptxt_en = jn([f"({a}, {b})" for a, b in pairs], 'and')
        alts.append(alt(
            "Alle Gegenüber-Paare bestimmen", "Find all opposite pairs",
            f"Ein Würfel hat 3 Paare gegenüberliegender Flächen, jede Fläche steht in genau einem Paar. "
            f"Bei diesem Netz sind es {ptxt}. {X} steht im Paar ({' , '.join(sorted((X, Y)))}), also ist {Y} die Antwort. "
            f"Kontrolle: Felder, die im Netz direkt nebeneinander liegen, sind nie in einem Paar.",
            f"A cube has 3 pairs of opposite faces and every face is in exactly one pair. "
            f"For this net they are {ptxt_en}. {X} is in the pair ({' , '.join(sorted((X, Y)))}), so the answer is {Y}. "
            f"Check: squares that touch in the net are never in one pair."))
    difficulty = 'medium' if (rp and rp[1] == Y) else 'hard'
    q = common_fields(f"wnetz-opp-{idx:03d}", difficulty, ['wuerfel', 'wuerfelnetz'], qde, qen,
                      others, correct, numbered(de), numbered(en), alts, 'opp')
    return q

def gen_adjacent(rng, idx):
    cells_sym, nsym = make_net(rng)
    sym_cell = {s: c for c, s in cells_sym.items()}
    X = rng.choice(sorted(nsym))
    nb = sorted(cells_sym[c] for c in net_neighbours(sym_cell[X], cells_sym))
    Y = next(s for s, n in nsym.items() if n == neg(nsym[X]))
    folded_only = sorted(s for s in nsym if s not in (X, Y) and s not in nb)
    assert folded_only, "impossible for cube nets"
    others = [s for s in nsym if s != X]
    rng.shuffle(others)
    correct = sorted(others.index(s) for s in folded_only)
    nl = net_line(cells_sym)
    qde = (f"WÜRFELNETZ: Das Netz wird zu einem Würfel gefaltet (bedruckte Seite außen).\nNetz: {nl}\n"
           f"Welche Flächen grenzen im gefalteten Würfel an {X}, liegen im Netz aber nicht direkt neben {X}? (Alle richtigen ankreuzen.)")
    qen = (f"CUBE NET: The net is folded into a cube (printed side outside).\nNet: {nl}\n"
           f"Which faces touch {X} in the folded cube but are not directly next to {X} in the net? (Tick all correct answers.)")
    de, en, sides, top, nbs = fold_steps(cells_sym, X)
    de.append(f"Die Seitenwände rund um {X} sind {jn(sides, 'und')}. Davon liegen {jn(nb, 'und')} im Netz direkt neben {X}; "
              f"erst durch das Falten kommen {jn(folded_only, 'und')} dazu. Der Deckel {top} grenzt nicht an {X}.")
    en.append(f"The side walls around {X} are {jn(sides, 'and')}. Of these, {jn(nb, 'and')} touch {X} in the net; "
              f"only folding brings {jn(folded_only, 'and')} next to it. The lid {top} does not touch {X}.")
    assert top == Y and sorted(sides) == sorted(nb + folded_only)
    alts = [
        alt("Gegenfläche ausschließen", "Rule out the opposite face",
            f"Jede Fläche grenzt an vier andere und liegt nur einer gegenüber. Die Gegenfläche von {X} ist {Y}; sie grenzt nie an {X}. "
            f"Die vier übrigen Flächen {jn(sorted(nb + folded_only), 'und')} grenzen alle an {X}. "
            f"Streichen Sie davon die im Netz direkt benachbarten ({jn(nb, 'und')}): übrig bleibt {jn(folded_only, 'und')}.",
            f"Every face touches four others and is opposite just one. The opposite face of {X} is {Y}; it never touches {X}. "
            f"The other four faces {jn(sorted(nb + folded_only), 'and')} all touch {X}. "
            f"Cross out those directly next to {X} in the net ({jn(nb, 'and')}): that leaves {jn(folded_only, 'and')}."),
        alt("Kanten zählen", "Count the edges",
            f"Ein Quadrat hat 4 Kanten, und jede Kante grenzt im Würfel an eine andere Fläche. {X} hat im Netz {len(nb)} "
            f"{'Kante' if len(nb) == 1 else 'Kanten'} mit Nachbarn ({jn(nb, 'und')}). Die restlichen {4 - len(nb)} "
            f"{'Kante wird' if 4 - len(nb) == 1 else 'Kanten werden'} erst beim Falten verklebt, und zwar mit {jn(folded_only, 'und')}.",
            f"A square has 4 edges and each edge meets a different face in the cube. {X} has {len(nb)} "
            f"{'edge' if len(nb) == 1 else 'edges'} with neighbours in the net ({jn(nb, 'and')}). The remaining {4 - len(nb)} "
            f"{'edge is' if 4 - len(nb) == 1 else 'edges are'} only joined when folding, namely with {jn(folded_only, 'and')}."),
    ]
    difficulty = 'hard' if len(folded_only) >= 2 else 'medium'
    return common_fields(f"wnetz-adj-{idx:03d}", difficulty, ['wuerfel', 'wuerfelnetz'], qde, qen,
                         others, correct, numbered(de), numbered(en), alts, 'adj')

def gen_view(rng, idx):
    cells_sym, nsym = make_net(rng)
    syms = sorted(nsym)
    F = rng.choice(syms)
    sides = [s for s in syms if dot(nsym[s], nsym[F]) == 0]
    R = rng.choice(sides)
    T = next(s for s in syms if nsym[s] == cross(nsym[F], nsym[R]))
    assert view_valid(nsym, T, F, R)
    correct_triple = (T, F, R)
    # distractors
    opp = {s: next(k for k, v in nsym.items() if v == neg(nsym[s])) for s in syms}
    pool_mirror, pool_opp = [], []
    for a in syms:
        for b in syms:
            for c in syms:
                if len({a, b, c}) < 3:
                    continue
                if view_valid(nsym, a, b, c):
                    pool_mirror.append((a, c, b))          # mirror image of a valid view
                elif opp[a] in (b, c) or opp[b] == c:
                    pool_opp.append((a, b, c))
    mirror_of_correct = (T, R, F)
    chosen = [mirror_of_correct]
    seen = {cyc_canon(correct_triple), cyc_canon(mirror_of_correct)}
    rng.shuffle(pool_mirror); rng.shuffle(pool_opp)
    want_opp = rng.choice([1, 2, 2])
    for pool, n in ((pool_opp, want_opp), (pool_mirror, 4 - 1 - want_opp)):
        k = 0
        for trip in pool:
            if k >= n:
                break
            cc = cyc_canon(trip)
            if cc in seen:
                continue
            seen.add(cc); chosen.append(trip); k += 1
    while len(chosen) < 4:                                  # top up if a pool ran dry
        for trip in pool_mirror + pool_opp:
            cc = cyc_canon(trip)
            if cc not in seen:
                seen.add(cc); chosen.append(trip); break
    triples = [correct_triple] + chosen
    rng.shuffle(triples)
    for t in triples:
        assert (t == correct_triple) == view_valid(nsym, *t)
    correct = [triples.index(correct_triple)]
    opts_de = [f"oben {a}, vorne {b}, rechts {c}" for a, b, c in triples]
    opts_en = [f"top {a}, front {b}, right {c}" for a, b, c in triples]
    nl = net_line(cells_sym)
    qde = (f"WÜRFELNETZ: Das Netz wird zu einem Würfel gefaltet (bedruckte Seite außen).\nNetz: {nl}\n"
           f"Welche Ansicht (oben, vorne, rechts) kann man von diesem Würfel sehen?")
    qen = (f"CUBE NET: The net is folded into a cube (printed side outside).\nNet: {nl}\n"
           f"Which view (top, front, right) can be seen on this cube?")
    # primary: frame with F in front, net as drawn (x right, y up, z towards viewer)
    # nsym uses base = first cell; re-fold with F in front to describe the frame
    sym_cell = {s: c for c, s in cells_sym.items()}
    nF = fold_algebraic(set(cells_sym), sym_cell[F])
    frame = {cells_sym[c]: n for c, n in nF.items()}
    names = {(0, 0, 1): ('vorne', 'front'), (0, 0, -1): ('hinten', 'back'), (0, 1, 0): ('oben', 'top'),
             (0, -1, 0): ('unten', 'bottom'), (1, 0, 0): ('rechts', 'right'), (-1, 0, 0): ('links', 'left')}
    at = {names[n][0]: s for s, n in frame.items()}
    at_en = {names[n][1]: s for s, n in frame.items()}
    right_now = at['rechts']
    turn_de = (f"{R} liegt bereits rechts, also liegt {T} oben." if right_now == R else
               f"Drehen Sie den Würfel um die Blickachse, bis {R} rechts liegt. Dann liegt {T} oben.")
    turn_en = (f"{R} is already on the right, so {T} is on top." if right_now == R else
               f"Turn the cube about your line of sight until {R} is on the right. Then {T} is on top.")
    de = [f"Halten Sie das Netz so, wie es gezeichnet ist: {F} schaut Sie an.",
          f"Falten Sie alle anderen Felder nach hinten. Dann liegt oben {at['oben']}, unten {at['unten']}, links {at['links']}, "
          f"rechts {at['rechts']} und hinten {at['hinten']}.",
          turn_de,
          f"Die Ansicht ist also: oben {T}, vorne {F}, rechts {R}."]
    en = [f"Hold the net as drawn: {F} faces you.",
          f"Fold all other squares backwards. Then the top is {at_en['top']}, bottom {at_en['bottom']}, left {at_en['left']}, "
          f"right {at_en['right']} and back {at_en['back']}.",
          turn_en,
          f"So the view is: top {T}, front {F}, right {R}."]
    letters = [chr(97 + i) for i in range(5)]
    pairs = opposite_pairs(nsym)
    bad_opp = [letters[i] for i, t in enumerate(triples) if any(opp[a] == b for a in t for b in t)]
    mirror_letter = [letters[i] for i, t in enumerate(triples)
                     if i not in correct and not any(opp[a] == b for a in t for b in t)]
    alts = [
        alt("Ecke und Drehsinn", "Corner and turning direction",
            f"Die drei Flächen {T}, {F}, {R} treffen sich an einer Würfelecke. Schaut man von außen auf diese Ecke, "
            f"folgen oben ({T}) → vorne ({F}) → rechts ({R}) gegen den Uhrzeigersinn aufeinander. "
            f"Die Reihenfolge {T} → {R} → {F} liefe im Uhrzeigersinn – das wäre das Spiegelbild und ist bei diesem Netz nicht möglich.",
            f"The three faces {T}, {F}, {R} meet at one corner of the cube. Looking at this corner from outside, "
            f"top ({T}) → front ({F}) → right ({R}) follow each other counter-clockwise. "
            f"The order {T} → {R} → {F} would run clockwise – that is the mirror image and is impossible for this net."),
        alt("Gegenüber-Paare streichen", "Cross out opposite pairs",
            f"Eine Ansicht zeigt nie zwei Gegenflächen. Die Gegenüber-Paare dieses Netzes sind {jn([f'({a}, {b})' for a, b in pairs], 'und')}. "
            f"Optionen mit so einem Paar ({jn(bad_opp, 'und') if bad_opp else 'keine'}) fallen weg. "
            f"Bei den übrigen ({jn(mirror_letter, 'und')}) sind die Flächen zwar benachbart, aber nur eine hat die richtige Drehrichtung: "
            f"{letters[correct[0]]}).",
            f"A view never shows two opposite faces. The opposite pairs of this net are {jn([f'({a}, {b})' for a, b in pairs], 'and')}. "
            f"Options containing such a pair ({jn(bad_opp, 'and') if bad_opp else 'none'}) are out. "
            f"In the others ({jn(mirror_letter, 'and')}) the faces are neighbours, but only one has the right turning direction: "
            f"{letters[correct[0]]})."),
    ]
    q = common_fields(f"wnetz-view-{idx:03d}", 'hard', ['wuerfel', 'wuerfelnetz'], qde, qen,
                      opts_de, correct, numbered(de), numbered(en), alts, 'view')
    q["options_en"] = [f"{chr(97+i)}) {o}" for i, o in enumerate(opts_en)]
    return q

# ── Generation / verification ────────────────────────────────────────────

def generate(count, seed=None):
    rng = random.Random(seed)
    out, seen_text = [], set()
    attempts = 0
    while len(out) < count and attempts < count * 50:
        attempts += 1
        kind = rng.choices(['opp', 'view', 'adj'], weights=[40, 35, 25])[0]
        idx = len(out) + 1
        q = {'opp': gen_opposite, 'view': gen_view, 'adj': gen_adjacent}[kind](rng, idx)
        if q['question_de'] in seen_text:
            continue
        seen_text.add(q['question_de'])
        if len(set(q['options_de'])) != 5:
            continue
        out.append(q)
    return out

def strip_letter(opt):
    return re.sub(r'^[a-e]\)\s*', '', opt)

def verify_question(q):
    """Re-derive the answer from the question TEXT with the independent
    geometric fold. Returns list of problem strings (empty = verified)."""
    probs = []
    cells = parse_net(q['question_de'])
    if cells is None:
        return ["cannot parse net"]
    if parse_net(q['question_en']) != cells:
        probs.append("EN net differs from DE net")
    if len(cells) != 6 or len(set(cells.values())) != 6:
        return probs + ["net must have 6 distinct symbols"]
    base = min(cells)
    nrm = fold_geometric(set(cells), base)
    if nrm is None:
        return probs + ["shape does not fold into a cube"]
    nsym = {cells[c]: n for c, n in nrm.items()}
    opp = {s: next(k for k, v in nsym.items() if v == neg(n)) for s, n in nsym.items()}
    sym_cell = {s: c for c, s in cells.items()}
    options = [strip_letter(o) for o in q['options_de']]
    got = set(q['correct'])
    kind = q['id'].split('-')[1]
    if kind in ('opp', 'adj'):
        m = re.search(r'(?:gegenüber von|\san) (\S+?)[?,]', q['question_de'].split('\n')[-1])
        if not m or m.group(1) not in nsym:
            return probs + ["cannot parse asked face"]
        X = m.group(1)
        if sorted(options) != sorted(s for s in nsym if s != X):
            probs.append("options are not the 5 other faces")
        if kind == 'opp':
            want = {i for i, o in enumerate(options) if o == opp[X]}
        else:
            netnb = {cells[c] for c in net_neighbours(sym_cell[X], cells)}
            want = {i for i, o in enumerate(options)
                    if o != X and dot(nsym[o], nsym[X]) == 0 and o not in netnb}
    else:
        want = set()
        for i, o in enumerate(options):
            m = re.fullmatch(r'oben (\S+), vorne (\S+), rechts (\S+)', o)
            if not m:
                probs.append(f"cannot parse view option {o!r}")
                continue
            t, f, r = m.groups()
            if all(s in nsym for s in (t, f, r)) and len({t, f, r}) == 3 and view_valid(nsym, t, f, r):
                want.add(i)
        en_syms = [re.findall(r'(?:top|front|right) (\S+?)(?:,|$)', strip_letter(o)) for o in q['options_en']]
        de_syms = [re.findall(r'(?:oben|vorne|rechts) (\S+?)(?:,|$)', o) for o in options]
        if en_syms != de_syms:
            probs.append("EN view options differ from DE")
    if got != want:
        probs.append(f"stored correct={sorted(got)} but folding gives {sorted(want)}")
    return probs

def selftest():
    print(f"[selftest] hexominoes: {len(all_hexominoes())} (expect 35); cube nets: {len(NETS)} (expect 11)")
    assert len(all_hexominoes()) == 35 and len(NETS) == 11
    # Known fact 1: standard die, opposite faces sum to 7.
    die = parse_net("Net: . 2 . . / 3 1 4 6 / . 5 . .")
    for fold in (fold_algebraic, fold_geometric):
        nrm = fold(set(die), min(die))
        nsym = {die[c]: n for c, n in nrm.items()}
        sums = {int(a) + int(b) for a, b in opposite_pairs(nsym)}
        print(f"[selftest] {fold.__name__}: opposite pairs {opposite_pairs(nsym)} sums {sums}")
        assert sums == {7}
        # Known fact 2 (hand-derived): C in front of you, A above, D right -> (top A, front C, right D)
        assert view_valid(nsym, '2', '1', '4') and not view_valid(nsym, '2', '4', '1')
    # Algebraic and geometric folds agree on every net from every base cell
    for shp in NETS:
        for base in shp:
            assert fold_algebraic(shp, base) == fold_geometric(shp, base), (shp, base)
    # Result must be independent of the base cell (up to rotation): opposite pairs identical
    syms = dict(zip(sorted(NETS[0]), 'ABCDEF'))
    ref = None
    for base in syms:
        nsym = {syms[c]: n for c, n in fold_algebraic(set(syms), base).items()}
        pairs = opposite_pairs(nsym)
        assert ref is None or pairs == ref
        ref = pairs
        # every valid view stays valid under re-basing -> chirality is base independent
    print("[selftest] algebraic == geometric on all 11 nets x 6 bases; base-independent pairs: OK")
    print("[selftest] PASS")

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Generate Würfelnetz questions')
    parser.add_argument('--count', type=int, default=20)
    parser.add_argument('--seed', type=int, default=None)
    parser.add_argument('--output', type=str, default='/tmp/wuerfelnetz_generated.json')
    parser.add_argument('--verify', type=str, default=None, help='re-verify a questions JSON file by folding')
    parser.add_argument('--selftest', action='store_true')
    args = parser.parse_args()

    if args.selftest:
        selftest(); sys.exit(0)
    if args.verify:
        qs = [q for q in json.load(open(args.verify)) if 'wuerfelnetz' in q.get('tags', [])]
        bad = 0
        for q in qs:
            for p in verify_question(q):
                bad += 1
                print(f"MISMATCH [{q['id']}]: {p}")
        print(f"verified {len(qs)} net questions: {'FAIL' if bad else 'OK'} ({bad} problems)")
        sys.exit(1 if bad else 0)

    qs = generate(args.count, args.seed)
    problems = [(q['id'], p) for q in qs for p in verify_question(q)]
    if problems:
        for qid, p in problems:
            print(f"VERIFY FAIL [{qid}]: {p}")
        sys.exit(1)
    with open(args.output, 'w') as f:
        json.dump(qs, f, indent=2, ensure_ascii=False)
    print(f"Generated {len(qs)} Würfelnetz questions → {args.output} (all answers verified by folding)")
    print(f"Types: {dict(Counter(q['id'].split('-')[1] for q in qs))}")
    print(f"Difficulty: {dict(Counter(q['difficulty'] for q in qs))}")
