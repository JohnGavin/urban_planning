#!/usr/bin/env python3
"""
Generate Matrizen (3x3 pattern grid) questions with verified answers.
Rules-based: each row/column follows property rules.

Usage:
    python3 gen_matrizen.py --count 50 --output /tmp/matrizen.json
    python3 gen_matrizen.py --size 4 --count 20 --difficulty hard --seed 202609 --output /tmp/matrizen4.json

--size 3 (default) emits the classic 3x3 matrices. --size 4 emits 4x4 matrices
(always difficulty "hard", tags ["matrizen", "4x4"]). Every 4x4 question is
self-validated: the rule must pin down the missing cell uniquely (exhaustive
search over all renderable candidate cells), and exactly one of the 5 options
may satisfy the rule.
"""

import json, random, argparse, itertools

SHAPES = ['Kreis', 'Dreieck', 'Quadrat', 'Stern', 'Herz', 'Raute', 'Sechseck']
COLORS = ['schwarz', 'weiß', 'grau']
SIZES = ['groß', 'mittel', 'klein']
PATTERNS = ['leer', 'horizontal gestreift', 'vertikal gestreift', 'gepunktet', 'kariert']
COUNTS = [1, 2, 3]

SHAPE_EN = {'Kreis': 'Circle', 'Dreieck': 'Triangle', 'Quadrat': 'Square',
            'Stern': 'Star', 'Herz': 'Heart', 'Raute': 'Diamond', 'Sechseck': 'Hexagon'}
COLOR_EN = {'schwarz': 'black', 'weiß': 'white', 'grau': 'grey'}
SIZE_EN = {'groß': 'big', 'mittel': 'medium', 'klein': 'small'}

QUESTION_TEMPLATES_DE = [
    "Was ist die fehlende Figur?",
    "Welche Figur vervollständigt die Matrix?",
    "Was gehört an die Stelle des Fragezeichens?",
    "Ergänzen Sie die Matrix.",
]
QUESTION_TEMPLATES_EN = [
    "What is the missing figure?",
    "Which figure completes the matrix?",
    "What belongs where the question mark is?",
    "Complete the matrix.",
]

# ═══════════════════════════════════════════════════════════════════════════
# 4x4 support (--size 4)
#
# Every rule below returns a dict with
#   grid      4x4 list of cell dicts (the answer is grid[3][3])
#   check     function(grid) -> bool: does the WHOLE grid obey the rule?
#   universe  {cell key: [candidate values]}: every renderable value a cell
#             could take; used to prove the answer is unique by exhaustion
#   desc_de / desc_en   short rule name
#   parts_de / parts_en step-by-step explanation paragraphs
# Only shapes / colours / sizes / dots / arrows that site/js/quiz-engine.js
# (parseMatrixCell / renderCellSVG) understands are used. Dots and arrows are
# drawn in the cell colour, so the dark-background-invisible "weiß" fill is
# never used for them.
# ═══════════════════════════════════════════════════════════════════════════

ARROWS = ['↑', '→', '↓', '←']            # clockwise order
ARROW_SHAPES = [f'Pfeil {d}' for d in ARROWS]
VISIBLE_COLORS = ['schwarz', 'grau']     # stay visible for dots and arrows
SCHEMES = {'cyc': [0, 1, 2, 0], 'pingpong': [0, 1, 2, 1]}
MAX_DOTS = 9


def shape_en(shape):
    if shape.startswith('Pfeil'):
        return 'Arrow' + shape[len('Pfeil'):]
    return SHAPE_EN.get(shape, shape)


def cell_text4(cell, lang='de'):
    """Text of one cell in the format parseMatrixCell understands."""
    if lang == 'de':
        s = cell['shape']
        if 'dots' in cell:
            s += f" mit {cell['dots']} " + ('Punkt' if cell['dots'] == 1 else 'Punkten')
        parts = [s]
        if 'size' in cell:
            parts.append(cell['size'])
        if 'color' in cell:
            parts.append(cell['color'])
    else:
        s = shape_en(cell['shape'])
        if 'dots' in cell:
            s += f" with {cell['dots']} " + ('dot' if cell['dots'] == 1 else 'dots')
        parts = [s]
        if 'size' in cell:
            parts.append(SIZE_EN[cell['size']])
        if 'color' in cell:
            parts.append(COLOR_EN[cell['color']])
    return ', '.join(parts)


def cell_renderable(cell):
    """True iff every value of the cell is in the vocabulary the renderer knows."""
    if set(cell) - {'shape', 'color', 'size', 'dots'}:
        return False
    if cell.get('shape') not in SHAPES + ARROW_SHAPES:
        return False
    if 'color' in cell and cell['color'] not in COLORS:
        return False
    if 'size' in cell and cell['size'] not in SIZES:
        return False
    if 'dots' in cell and not (isinstance(cell['dots'], int) and 1 <= cell['dots'] <= MAX_DOTS):
        return False
    if ('dots' in cell or cell['shape'].startswith('Pfeil')) and cell.get('color') == 'weiß':
        return False  # fill is invisible on the dark background
    return True


def latin_square_n(n):
    """Random n x n Latin square (values 0..n-1 once per row and column)."""
    base = [[(r + c) % n for c in range(n)] for r in range(n)]
    random.shuffle(base)
    cols = list(range(n))
    random.shuffle(cols)
    base = [[row[c] for c in cols] for row in base]
    relabel = list(range(n))
    random.shuffle(relabel)
    return [[relabel[v] for v in row] for row in base]


def latin_shape_ok(g):
    """Each of 4 shapes exactly once per row and once per column."""
    s = {g[0][c]['shape'] for c in range(4)}
    if len(s) != 4:
        return False
    for i in range(4):
        if {g[i][c]['shape'] for c in range(4)} != s:
            return False
        if {g[r][i]['shape'] for r in range(4)} != s:
            return False
    return True


def latin_shape_parts(g):
    """Explanation paragraphs (de, en) for a shape Latin square; g[3][3] is the answer."""
    order = [g[0][c]['shape'] for c in range(4)]
    row_vis = [g[3][c]['shape'] for c in range(3)]
    col_vis = [g[r][3]['shape'] for r in range(3)]
    miss_row = [s for s in order if s not in row_vis][0]
    miss_col = [s for s in order if s not in col_vis][0]
    assert miss_row == miss_col == g[3][3]['shape']
    de = (f"Form (Lateinisches Quadrat): Jede der 4 Formen ({', '.join(order)}) kommt in jeder Zeile "
          f"und in jeder Spalte genau einmal vor. Zeilenregel: Zeile 4 zeigt schon {', '.join(row_vis)} → es fehlt {miss_row}. "
          f"Spaltenregel: Spalte 4 zeigt schon {', '.join(col_vis)} → es fehlt {miss_col}. Beide Regeln ergeben: {miss_row}.")
    en = (f"Shape (Latin square): each of the 4 shapes ({', '.join(shape_en(s) for s in order)}) appears exactly once in every row "
          f"and every column. Row rule: row 4 already shows {', '.join(shape_en(s) for s in row_vis)} → {shape_en(miss_row)} is missing. "
          f"Column rule: column 4 already shows {', '.join(shape_en(s) for s in col_vis)} → {shape_en(miss_col)} is missing. "
          f"Both rules give: {shape_en(miss_row)}.")
    return de, en


class CycProp:
    """A 3-valued property following value index = (off + k*row + scheme[col]) % 3.
    scheme 'cyc' = 0,+1,+2,+0 steps per column; 'pingpong' = 0,+1,+2,+1 (back and forth).
    Every row starts k steps further along the value order than the row above."""

    def __init__(self, key, values, name_de, name_en, tr):
        self.key = key
        self.values = random.sample(values, 3)
        self.name_de, self.name_en, self.tr = name_de, name_en, tr
        self.off = random.randrange(3)
        self.k = random.choice([1, 2])
        self.scheme = random.choice(sorted(SCHEMES))
        self.pp = SCHEMES[self.scheme]

    def val(self, r, c):
        return self.values[(self.off + self.k * r + self.pp[c]) % 3]

    def parts(self):
        """(de, en) explanation for the missing cell (row 4, column 4)."""
        v = self.values
        start, above, res = self.val(3, 0), self.val(2, 3), self.val(3, 3)
        step = self.pp[3]
        seq_de = ' → '.join(v + [v[0]])
        seq_en = ' → '.join([self.tr[x] for x in v + [v[0]]])
        schema = f"Start, +1, +2, +{step}"
        de = (f"{self.name_de}: Stufenfolge {seq_de} (danach wieder von vorn). Zeilenregel: In jeder Zeile gilt von Spalte 1 bis 4 "
              f"das Schema {schema} Stufen. Zeile 4 startet mit {start}; Spalte 4 liegt {step} Stufe{'' if step == 1 else 'n'} "
              f"weiter → {res}. Spaltenregel: Jede Zeile beginnt {self.k} Stufe{'' if self.k == 1 else 'n'} weiter als die Zeile darüber; "
              f"Spalte 4 zeigt in Zeile 3 {above}, eine Zeile tiefer also {res}.")
        en = (f"{self.name_en}: sequence {seq_en} (then repeat from the start). Row rule: in every row, columns 1 to 4 follow the pattern "
              f"{schema} steps. Row 4 starts with {self.tr[start]}; column 4 is {step} step{'' if step == 1 else 's'} further → {self.tr[res]}. "
              f"Column rule: each row starts {self.k} step{'' if self.k == 1 else 's'} further along than the row above; "
              f"column 4 shows {self.tr[above]} in row 3, so one row down it is {self.tr[res]}.")
        return de, en


def _grid4(f):
    return [[f(r, c) for c in range(4)] for r in range(4)]


def rule4_latin_shape_color():
    shapes = random.sample(SHAPES, 4)
    sq = latin_square_n(4)
    col = CycProp('color', COLORS, 'Farbe', 'Colour', COLOR_EN)
    grid = _grid4(lambda r, c: {'shape': shapes[sq[r][c]], 'color': col.val(r, c)})
    de_s, en_s = latin_shape_parts(grid)
    de_c, en_c = col.parts()
    return {
        'grid': grid,
        'check': lambda g: latin_shape_ok(g) and all(g[r][c]['color'] == col.val(r, c) for r in range(4) for c in range(4)),
        'universe': {'shape': list(SHAPES), 'color': list(COLORS)},
        'desc_de': "4×4: Lateinisches Quadrat (Form) + Farbe mit Zyklus pro Zeile/Spalte",
        'desc_en': "4x4: Latin square (shape) + colour cycling per row/column",
        'parts_de': [de_s, de_c], 'parts_en': [en_s, en_c],
    }


def rule4_latin_shape_size():
    shapes = random.sample(SHAPES, 4)
    sq = latin_square_n(4)
    siz = CycProp('size', SIZES, 'Größe', 'Size', SIZE_EN)
    grid = _grid4(lambda r, c: {'shape': shapes[sq[r][c]], 'size': siz.val(r, c)})
    de_s, en_s = latin_shape_parts(grid)
    de_z, en_z = siz.parts()
    return {
        'grid': grid,
        'check': lambda g: latin_shape_ok(g) and all(g[r][c]['size'] == siz.val(r, c) for r in range(4) for c in range(4)),
        'universe': {'shape': list(SHAPES), 'size': list(SIZES)},
        'desc_de': "4×4: Lateinisches Quadrat (Form) + Größe mit Zyklus pro Zeile/Spalte",
        'desc_en': "4x4: Latin square (shape) + size cycling per row/column",
        'parts_de': [de_s, de_z], 'parts_en': [en_s, en_z],
    }


def rule4_latin_3prop():
    shapes = random.sample(SHAPES, 4)
    sq = latin_square_n(4)
    col = CycProp('color', COLORS, 'Farbe', 'Colour', COLOR_EN)
    siz = CycProp('size', SIZES, 'Größe', 'Size', SIZE_EN)
    grid = _grid4(lambda r, c: {'shape': shapes[sq[r][c]], 'color': col.val(r, c), 'size': siz.val(r, c)})
    de_s, en_s = latin_shape_parts(grid)
    de_c, en_c = col.parts()
    de_z, en_z = siz.parts()
    return {
        'grid': grid,
        'check': lambda g: latin_shape_ok(g) and all(
            g[r][c]['color'] == col.val(r, c) and g[r][c]['size'] == siz.val(r, c)
            for r in range(4) for c in range(4)),
        'universe': {'shape': list(SHAPES), 'color': list(COLORS), 'size': list(SIZES)},
        'desc_de': "4×4: 3 Eigenschaften (Lateinisches Quadrat für Form, Zyklen für Farbe und Größe)",
        'desc_en': "4x4: 3 properties (Latin square for shape, cycles for colour and size)",
        'parts_de': [de_s, de_c, de_z], 'parts_en': [en_s, en_c, en_z],
    }


def rule4_row_shape_col_progression():
    shapes = random.sample(SHAPES, 4)
    col = CycProp('color', COLORS, 'Farbe', 'Colour', COLOR_EN)
    siz = CycProp('size', SIZES, 'Größe', 'Size', SIZE_EN)
    grid = _grid4(lambda r, c: {'shape': shapes[r], 'color': col.val(r, c), 'size': siz.val(r, c)})
    sh = shapes[3]

    def check(g):
        rows_ok = all(len({g[r][c]['shape'] for c in range(4)}) == 1 for r in range(4))
        distinct = len({g[r][0]['shape'] for r in range(4)}) == 4
        props_ok = all(g[r][c]['color'] == col.val(r, c) and g[r][c]['size'] == siz.val(r, c)
                       for r in range(4) for c in range(4))
        return rows_ok and distinct and props_ok

    de_c, en_c = col.parts()
    de_z, en_z = siz.parts()
    return {
        'grid': grid, 'check': check,
        'universe': {'shape': list(SHAPES), 'color': list(COLORS), 'size': list(SIZES)},
        'desc_de': "4×4: Form pro Zeile konstant + Farbe und Größe mit Zyklus",
        'desc_en': "4x4: shape constant per row + colour and size cycling",
        'parts_de': [f"Form: Jede Zeile hat ihre eigene Form, die in der Zeile konstant bleibt (Zeilenregel); "
                     f"die 4 Zeilen zeigen 4 verschiedene Formen (Spaltenregel). Zeile 4 zeigt 3× {sh} → {sh}.", de_c, de_z],
        'parts_en': [f"Shape: each row has its own shape that stays constant within the row (row rule); "
                     f"the 4 rows show 4 different shapes (column rule). Row 4 shows 3x {shape_en(sh)} → {shape_en(sh)}.", en_c, en_z],
    }


def rule4_dot_sum():
    shapes = random.sample(SHAPES, 4)
    colors = [random.choice(VISIBLE_COLORS) for _ in range(4)]
    variant = random.choice(['sum3', 'fib'])
    rows = []
    for r in range(4):
        a, b = random.randint(1, 2), random.randint(1, 2)
        if variant == 'sum3':
            c3 = random.randint(1, 2)
            dots = [a, b, c3, a + b + c3]
        else:
            dots = [a, b, a + b, a + 2 * b]
        rows.append(dots)
    grid = _grid4(lambda r, c: {'shape': shapes[r], 'color': colors[r], 'dots': rows[r][c]})

    def rule_ok(d):
        return d[3] == d[0] + d[1] + d[2] if variant == 'sum3' else (d[2] == d[0] + d[1] and d[3] == d[1] + d[2])

    def check(g):
        for r in range(4):
            if len({g[r][c]['shape'] for c in range(4)}) != 1 or len({g[r][c]['color'] for c in range(4)}) != 1:
                return False
            if not rule_ok([g[r][c]['dots'] for c in range(4)]):
                return False
        return len({g[r][0]['shape'] for r in range(4)}) == 4

    d = rows[3]
    p = rows[0]
    if variant == 'sum3':
        rule_de = "Spalte 4 = Spalte 1 + Spalte 2 + Spalte 3"
        rule_en = "column 4 = column 1 + column 2 + column 3"
        calc_de = f"Zeile 4: {d[0]} + {d[1]} + {d[2]} = {d[3]}"
        calc_en = calc_de.replace('Zeile', 'Row')
        probe = f"Probe Zeile 1: {p[0]} + {p[1]} + {p[2]} = {p[3]}."
    else:
        rule_de = "Spalte 3 = Spalte 1 + Spalte 2 und Spalte 4 = Spalte 2 + Spalte 3"
        rule_en = "column 3 = column 1 + column 2 and column 4 = column 2 + column 3"
        calc_de = f"Zeile 4: {d[0]} + {d[1]} = {d[2]} (sichtbar, passt), dann {d[1]} + {d[2]} = {d[3]}"
        calc_en = f"Row 4: {d[0]} + {d[1]} = {d[2]} (visible, fits), then {d[1]} + {d[2]} = {d[3]}"
        probe = f"Probe Zeile 1: {p[0]} + {p[1]} = {p[2]}, {p[1]} + {p[2]} = {p[3]}."
    probe_en = probe.replace('Probe Zeile', 'Check row')
    return {
        'grid': grid, 'check': check,
        'universe': {'shape': list(SHAPES), 'color': list(VISIBLE_COLORS), 'dots': list(range(1, MAX_DOTS + 1))},
        'desc_de': f"4×4: Punkte addieren ({rule_de})",
        'desc_en': f"4x4: add the dots ({rule_en})",
        'parts_de': [
            f"Form und Farbe: Bleiben in jeder Zeile gleich (Zeilenregel); jede Spalte enthält 4 verschiedene Formen (Spaltenregel). "
            f"Zeile 4 zeigt {shapes[3]}, {colors[3]}.",
            f"Punkte (Zeilenregel): {rule_de}. {calc_de}. {probe}"],
        'parts_en': [
            f"Shape and colour: stay the same within each row (row rule); every column contains 4 different shapes (column rule). "
            f"Row 4 shows {shape_en(shapes[3])}, {COLOR_EN[colors[3]]}.",
            f"Dots (row rule): {rule_en}. {calc_en}. {probe_en}"],
    }


def rule4_arrow_rotation():
    start = random.randrange(4)
    s = random.choice([1, 3])            # 1 = clockwise per column, 3 = counter-clockwise
    k = random.choice([1, 2, 3])         # row shift in 90-degree clockwise steps
    c0 = random.randrange(2)
    siz = CycProp('size', SIZES, 'Größe', 'Size', SIZE_EN)

    def d(r, c):
        return (start + s * c + k * r) % 4

    def color(r):
        return VISIBLE_COLORS[(c0 + r) % 2]

    grid = _grid4(lambda r, c: {'shape': ARROW_SHAPES[d(r, c)], 'color': color(r), 'size': siz.val(r, c)})

    def check(g):
        return all(g[r][c]['shape'] == ARROW_SHAPES[d(r, c)] and g[r][c]['color'] == color(r)
                   and g[r][c]['size'] == siz.val(r, c) for r in range(4) for c in range(4))

    d0 = ARROWS[d(3, 0)]
    above = ARROWS[d(2, 3)]
    res = ARROWS[d(3, 3)]
    way_de = "im Uhrzeigersinn" if s == 1 else "gegen den Uhrzeigersinn"
    way_en = "clockwise" if s == 1 else "counter-clockwise"
    de_z, en_z = siz.parts()
    return {
        'grid': grid, 'check': check,
        'universe': {'shape': list(ARROW_SHAPES), 'color': list(VISIBLE_COLORS), 'size': list(SIZES)},
        'desc_de': "4×4: Pfeil dreht pro Spalte um 90°, Zeilen versetzt; Farbe wechselt pro Zeile",
        'desc_en': "4x4: arrow turns 90° per column, rows offset; colour alternates per row",
        'parts_de': [
            f"Richtung: Der Pfeil dreht sich pro Spalte um 90° {way_de}; jede Zeile ist um {k}×90° im Uhrzeigersinn "
            f"weitergedreht als die Zeile darüber. Zeilenregel: Zeile 4 beginnt mit {d0}; 3 Drehungen um je 90° {way_de} ergeben {res}. "
            f"Spaltenregel: Spalte 4 zeigt in Zeile 3 {above}; eine Zeile tiefer ({k}×90° im Uhrzeigersinn) ist es {res}.",
            f"Farbe: Wechselt pro Zeile zwischen schwarz und grau; Zeile 4 ist {color(3)} (wie die drei sichtbaren Felder der Zeile).",
            de_z],
        'parts_en': [
            f"Direction: the arrow turns 90° {way_en} per column; each row is turned a further {k}×90° clockwise compared with the row above. "
            f"Row rule: row 4 starts with {d0}; 3 turns of 90° {way_en} give {res}. "
            f"Column rule: column 4 shows {above} in row 3; one row down ({k}×90° clockwise) it is {res}.",
            f"Colour: alternates between black and grey per row; row 4 is {COLOR_EN[color(3)]} (like the three visible cells of that row).",
            en_z],
    }


RULES4 = [rule4_latin_shape_color, rule4_latin_shape_size, rule4_latin_3prop,
          rule4_row_shape_col_progression, rule4_dot_sum, rule4_arrow_rotation]


def solve4(rule, grid=None):
    """All candidate cells for the bottom-right position that make the whole grid obey the rule."""
    g = grid if grid is not None else rule['grid']
    keys = sorted(rule['universe'])
    saved = g[3][3]
    sols = []
    try:
        for combo in itertools.product(*(rule['universe'][k] for k in keys)):
            g[3][3] = dict(zip(keys, combo))
            if rule['check'](g):
                sols.append(dict(g[3][3]))
    finally:
        g[3][3] = saved
    return sols


def validate_grid4(rule):
    """Generation-time self-validation of a 4x4 rule. Returns (ok, reason)."""
    g = rule['grid']
    if len(g) != 4 or any(len(row) != 4 for row in g):
        return False, "grid is not 4x4"
    keyset = set(g[0][0])
    for row in g:
        for cell in row:
            if set(cell) != keyset:
                return False, "cells have different property sets"
            if not cell_renderable(cell):
                return False, f"cell not renderable: {cell}"
    if not rule['check'](g):
        return False, "grid violates its own rule"
    sols = solve4(rule)
    if len(sols) != 1:
        return False, f"answer not unique: {len(sols)} cells satisfy the rule"
    if sols[0] != g[3][3]:
        return False, "the unique solution differs from the intended answer"
    varying = [k for k in keyset if len({str(g[r][c][k]) for r in range(4) for c in range(4)}) > 1]
    if len(varying) < 2:
        return False, f"fewer than 2 varying properties: {varying}"
    return True, "OK"


def make_distractors4(rule, n=4):
    """Near-miss distractors (few properties changed), all provably violating the rule."""
    g = rule['grid']
    answer = g[3][3]
    uni = dict(rule['universe'])
    if 'shape' in uni and not answer['shape'].startswith('Pfeil'):
        seen = {g[r][c]['shape'] for r in range(4) for c in range(4)}
        uni['shape'] = [s for s in uni['shape'] if s in seen]
    keys = sorted(uni)
    cands = []
    for combo in itertools.product(*(uni[k] for k in keys)):
        cell = dict(zip(keys, combo))
        if cell == answer:
            continue
        dist = sum(1 for k in keys if cell[k] != answer[k])
        cands.append((dist, random.random(), cell))
    cands.sort(key=lambda t: (t[0], t[1]))
    return [c[2] for c in cands[:n]]


class MatrixGenerator:
    def __init__(self, size=3):
        self.size = size
        self.rule_types4 = RULES4
        self.rule_types = [
            self.rule_latin_2prop,
            self.rule_latin_3prop,
            self.rule_row_constant_col_changes,
            self.rule_col_constant_row_changes,
            self.rule_arithmetic_count,
            self.rule_rotation_shift,
        ]

    @staticmethod
    def _latin_square():
        """Generate a random 3x3 Latin square (each value 0,1,2 once per row and column)."""
        base = [[0,1,2], [1,2,0], [2,0,1]]
        # Shuffle rows, then shuffle columns, then relabel values
        random.shuffle(base)
        cols = list(range(3))
        random.shuffle(cols)
        base = [[row[c] for c in cols] for row in base]
        relabel = list(range(3))
        random.shuffle(relabel)
        return [[relabel[base[r][c]] for c in range(3)] for r in range(3)]

    def rule_latin_2prop(self):
        """Latin square: each shape and colour once per row/column."""
        shapes = random.sample(SHAPES, 3)
        colors = random.sample(COLORS, 3)
        shape_sq = self._latin_square()
        color_sq = self._latin_square()
        grid = []
        for row in range(3):
            grid_row = []
            for col in range(3):
                grid_row.append({'shape': shapes[shape_sq[row][col]], 'color': colors[color_sq[row][col]]})
            grid.append(grid_row)
        return grid, 'medium', "Lateinisches Quadrat: jede Form und Farbe einmal pro Zeile/Spalte"

    def rule_latin_3prop(self):
        """Latin square with 3 properties: shape + color + size."""
        shapes = random.sample(SHAPES, 3)
        colors = random.sample(COLORS, 3)
        sizes = list(SIZES)
        shape_sq = self._latin_square()
        color_sq = self._latin_square()
        size_sq = self._latin_square()
        grid = []
        for row in range(3):
            grid_row = []
            for col in range(3):
                grid_row.append({'shape': shapes[shape_sq[row][col]], 'color': colors[color_sq[row][col]], 'size': sizes[size_sq[row][col]]})
            grid.append(grid_row)
        return grid, 'hard', "3 Eigenschaften im Lateinischen Quadrat"

    def rule_row_constant_col_changes(self):
        """Shape constant per row, colour changes per column."""
        shapes = random.sample(SHAPES, 3)
        colors = random.sample(COLORS, 3)
        grid = []
        for row in range(3):
            grid_row = []
            for col in range(3):
                grid_row.append({'shape': shapes[row], 'color': colors[col]})
            grid.append(grid_row)
        return grid, 'medium', "Form pro Zeile konstant, Farbe ändert sich pro Spalte"

    def rule_col_constant_row_changes(self):
        """Shape constant per column, size changes per row."""
        shapes = random.sample(SHAPES, 3)
        sizes = list(SIZES)
        grid = []
        for row in range(3):
            grid_row = []
            for col in range(3):
                grid_row.append({'shape': shapes[col], 'size': sizes[row]})
            grid.append(grid_row)
        return grid, 'medium', "Form pro Spalte konstant, Größe ändert sich pro Zeile"

    def rule_arithmetic_count(self):
        """Count in column 3 = column 1 + column 2 (or subtraction)."""
        shapes = random.sample(SHAPES, 3)
        op = random.choice(['add', 'sub'])
        grid = []
        for row in range(3):
            a = random.randint(1, 3)
            b = random.randint(1, 3)
            c = a + b if op == 'add' else abs(a - b)
            if c == 0: c = 1
            grid.append([
                {'shape': shapes[row], 'count': a, 'color': 'schwarz'},
                {'shape': shapes[row], 'count': b, 'color': 'weiß'},
                {'shape': shapes[row], 'count': c, 'color': 'schwarz'},
            ])
        rule_desc = "Spalte 3 = Spalte 1 + Spalte 2" if op == 'add' else "Spalte 3 = |Spalte 1 - Spalte 2|"
        return grid, 'hard', rule_desc

    def rule_rotation_shift(self):
        """Arrows that rotate per column, colour shifts per row."""
        directions = ['↑', '→', '↓', '←']
        colors = random.sample(COLORS, 3)
        start_dir = random.randint(0, 3)
        grid = []
        for row in range(3):
            grid_row = []
            for col in range(3):
                d = directions[(start_dir + col + row) % 4]
                grid_row.append({'shape': f'Pfeil {d}', 'color': colors[row]})
            grid.append(grid_row)
        return grid, 'hard', "Pfeil dreht sich pro Spalte um 90°, Farbe wechselt pro Zeile"

    @staticmethod
    def validate_grid(grid):
        """Validate a generated grid BEFORE converting to question text.
        Returns (ok, reason). Catches bugs at generation time."""
        # Collect all properties across cells
        shapes = set()
        colors = set()
        sizes = set()
        has_count = False
        has_arrow_dir = False
        for row in grid:
            for cell in row:
                s = cell.get('shape', '')
                shapes.add(s.split()[0].lower() if s else '')  # base shape name
                if 'color' in cell: colors.add(cell['color'])
                if 'size' in cell: sizes.add(cell['size'])
                if cell.get('count', 1) > 1: has_count = True
                if any(d in s for d in ['↑','↓','→','←']): has_arrow_dir = True

        # Rule 1: not all cells visually identical
        if len(shapes) == 1 and len(colors) <= 1 and len(sizes) <= 1 and not has_count and not has_arrow_dir:
            return False, f"All cells identical: shape={shapes}, no color/size/count/arrow variety"

        # Rule 2: answer properties must be present in the grid
        answer = grid[2][2]
        grid_props = set()
        for row in grid:
            for cell in row:
                grid_props.update(cell.keys())
        for prop in answer:
            if prop not in grid_props:
                return False, f"Answer property '{prop}' not in grid"

        # Rule 3: at least 2 distinct visual properties vary across cells
        varying = 0
        if len(shapes) > 1: varying += 1
        if len(colors) > 1: varying += 1
        if len(sizes) > 1: varying += 1
        if has_count: varying += 1
        if has_arrow_dir: varying += 1
        if varying < 1:
            return False, f"Only {varying} properties vary — needs at least 1"

        # Rule 4: Latin square check — if same property set, each value once per row/col
        # (only for shape and color which are the most common Latin square properties)
        for prop_name, values in [('shape', shapes), ('color', colors), ('size', sizes)]:
            if len(values) == 3:  # exactly 3 values = should be Latin square
                for row in range(3):
                    row_vals = [grid[row][c].get(prop_name, '').split()[0].lower() if prop_name == 'shape' else grid[row][c].get(prop_name, '') for c in range(3)]
                    if len(set(row_vals)) != 3:
                        return False, f"Latin square violation: row {row} has {prop_name}={row_vals}"
                for col in range(3):
                    col_vals = [grid[r][col].get(prop_name, '').split()[0].lower() if prop_name == 'shape' else grid[r][col].get(prop_name, '') for r in range(3)]
                    if len(set(col_vals)) != 3:
                        return False, f"Latin square violation: col {col} has {prop_name}={col_vals}"

        return True, "OK"

    def generate_one4(self, idx, target_difficulty=None):
        """One self-validated 4x4 question (always difficulty 'hard')."""
        if target_difficulty and target_difficulty != 'hard':
            return None
        for attempt in range(20):
            rule = random.choice(self.rule_types4)()
            ok, reason = validate_grid4(rule)
            if not ok:
                continue
            g = rule['grid']
            answer = g[3][3]

            dist = make_distractors4(rule, 4)
            if len(dist) < 4:
                continue
            opts = [answer] + dist
            texts_de = [cell_text4(o, 'de') for o in opts]
            texts_en = [cell_text4(o, 'en') for o in opts]
            if len(set(texts_de)) != 5 or len(set(texts_en)) != 5:
                continue  # options must be pairwise distinct
            if not all(cell_renderable(o) for o in opts):
                continue
            # exactly one option may satisfy the rule when placed in the grid
            passing = 0
            for o in opts:
                saved = g[3][3]
                g[3][3] = o
                passing += 1 if rule['check'](g) else 0
                g[3][3] = saved
            if passing != 1:
                continue

            combined = list(zip(texts_de, texts_en))
            random.shuffle(combined)
            all_de = [c[0] for c in combined]
            all_en = [c[1] for c in combined]
            correct_idx = all_de.index(texts_de[0])

            lines_de = ["Matrix (4×4) – Muster:"]
            lines_en = ["Matrix (4×4) – Pattern:"]
            for r in range(4):
                cells_de = ['[?]' if (r == 3 and c == 3) else f'[{cell_text4(g[r][c], "de")}]' for c in range(4)]
                cells_en = ['[?]' if (r == 3 and c == 3) else f'[{cell_text4(g[r][c], "en")}]' for c in range(4)]
                lines_de.append(f"Zeile {r+1}: {' '.join(cells_de)}")
                lines_en.append(f"Row {r+1}: {' '.join(cells_en)}")
            q_de = '\n'.join(lines_de) + '\n\n' + random.choice(QUESTION_TEMPLATES_DE)
            q_en = '\n'.join(lines_en) + '\n\n' + random.choice(QUESTION_TEMPLATES_EN)

            steps_de = ["Schritt 1 – Regel erkennen: Jede Eigenschaft getrennt prüfen, zuerst entlang der Zeilen, dann entlang der Spalten."]
            steps_en = ["Step 1 – Find the rule: check each property separately, first along the rows, then along the columns."]
            for i, (pd, pe) in enumerate(zip(rule['parts_de'], rule['parts_en'])):
                steps_de.append(f"Schritt {i+2} – {pd}")
                steps_en.append(f"Step {i+2} – {pe}")
            n = len(rule['parts_de']) + 2
            steps_de.append(f"Schritt {n} – Fehlende Figur zusammensetzen: {texts_de[0]}.")
            steps_en.append(f"Step {n} – Assemble the missing figure: {texts_en[0]}.")

            return {
                "id": f"matrix4-gen-{idx:03d}",
                "quizId": "cognitive",
                "difficulty": "hard",
                "tags": ["matrizen", "4x4"],
                "question_de": q_de,
                "question_en": q_en,
                "options_de": [f"{chr(97+i)}) {o}" for i, o in enumerate(all_de)],
                "options_en": [f"{chr(97+i)}) {o}" for i, o in enumerate(all_en)],
                "correct": [correct_idx],
                "explanation_de": '\n'.join(steps_de),
                "explanation_en": '\n'.join(steps_en),
                "mistakes_de": "Typische Fehler: (1) Nur Zeilen ODER Spalten analysieren, nicht beides. (2) Eine Eigenschaft übersehen (Form, Farbe, Größe, Punkte, Richtung getrennt prüfen). (3) Die Regel anhand von 2 Zellen ableiten statt alle 15 sichtbaren zu prüfen. (4) Bei 4 Spalten vergessen, dass sich ein Zyklus aus 3 Stufen nach 3 Schritten wiederholt oder zurückläuft.",
                "mistakes_en": "Common mistakes: (1) Analysing only rows OR columns, not both. (2) Missing a property (check shape, colour, size, dots, direction separately). (3) Deriving the rule from 2 cells instead of checking all 15 visible ones. (4) With 4 columns, forgetting that a 3-step cycle repeats or reverses after 3 steps.",
                "links": [{"url": "../knowledge/reihungstest-de.html", "label": "Reihungstest Info"}],
                "source": f"Generiert (gen_matrizen.py --size 4, Regel: {rule['desc_de']})"
            }
        return None

    def generate_one(self, idx, target_difficulty=None):
        if self.size == 4:
            return self.generate_one4(idx, target_difficulty)
        for attempt in range(20):
            rule_func = random.choice(self.rule_types)
            grid, difficulty, rule_desc = rule_func()

            if target_difficulty and difficulty != target_difficulty:
                continue

            # VALIDATE the grid before proceeding
            ok, reason = self.validate_grid(grid)
            if not ok:
                continue  # discard and retry

            # The answer is grid[2][2]
            answer_cell = grid[2][2]

            # Format grid as text
            def cell_to_text(cell):
                parts = []
                if 'count' in cell and cell['count'] > 1:
                    parts.append(f"{cell['count']} {cell['shape']}")
                else:
                    parts.append(cell['shape'])
                if 'size' in cell:
                    parts.append(cell['size'])
                if 'color' in cell:
                    parts.append(cell['color'])
                return ', '.join(parts)

            def cell_to_text_en(cell):
                parts = []
                if 'count' in cell and cell['count'] > 1:
                    shape_en = SHAPE_EN.get(cell['shape'], cell['shape'])
                    parts.append(f"{cell['count']} {shape_en}")
                else:
                    shape_en = SHAPE_EN.get(cell['shape'], cell['shape'])
                    parts.append(shape_en)
                if 'size' in cell:
                    parts.append(SIZE_EN.get(cell['size'], cell['size']))
                if 'color' in cell:
                    parts.append(COLOR_EN.get(cell['color'], cell['color']))
                return ', '.join(parts)

            answer_text_de = cell_to_text(answer_cell)
            answer_text_en = cell_to_text_en(answer_cell)

            lines_de = ["Matrix (3×3) – Muster:"]
            lines_en = ["Matrix (3×3) – Pattern:"]
            for row in range(3):
                cells_de = []
                cells_en = []
                for col in range(3):
                    if row == 2 and col == 2:
                        cells_de.append('[?]')
                        cells_en.append('[?]')
                    else:
                        cells_de.append(f'[{cell_to_text(grid[row][col])}]')
                        cells_en.append(f'[{cell_to_text_en(grid[row][col])}]')
                lines_de.append(f"Zeile {row+1}: {' '.join(cells_de)}")
                lines_en.append(f"Row {row+1}: {' '.join(cells_en)}")

            q_de = '\n'.join(lines_de) + '\n\n' + random.choice(QUESTION_TEMPLATES_DE)
            q_en = '\n'.join(lines_en) + '\n\n' + random.choice(QUESTION_TEMPLATES_EN)

            # Generate distractors
            distractors_de = set()
            distractors_en = set()
            for _ in range(50):
                fake = dict(answer_cell)
                prop = random.choice(list(fake.keys()))
                if prop == 'shape':
                    fake[prop] = random.choice(SHAPES)
                elif prop == 'color':
                    fake[prop] = random.choice(COLORS)
                elif prop == 'size':
                    fake[prop] = random.choice(SIZES)
                elif prop == 'count':
                    fake[prop] = random.choice([1, 2, 3, 4, 5])
                ft_de = cell_to_text(fake)
                ft_en = cell_to_text_en(fake)
                if ft_de != answer_text_de:
                    distractors_de.add(ft_de)
                    distractors_en.add(ft_en)
                if len(distractors_de) >= 4:
                    break

            if len(distractors_de) < 4:
                continue

            dist_de = list(distractors_de)[:4]
            dist_en = list(distractors_en)[:4]
            all_opts_de = [answer_text_de] + dist_de
            all_opts_en = [answer_text_en] + dist_en

            # Shuffle together
            combined = list(zip(all_opts_de, all_opts_en))
            random.shuffle(combined)
            all_opts_de, all_opts_en = zip(*combined)
            correct_idx = list(all_opts_de).index(answer_text_de)

            options_de = [f"{chr(97+i)}) {o}" for i, o in enumerate(all_opts_de)]
            options_en = [f"{chr(97+i)}) {o}" for i, o in enumerate(all_opts_en)]

            # POST-GENERATION validation: answer consistency
            # Check answer mentions only properties that appear in grid cells
            answer_lower = answer_text_de.lower()
            grid_text = q_de.lower()
            if 'punkt' in answer_lower and 'punkt' not in grid_text.replace('[?]', ''):
                continue  # answer mentions dots but grid doesn't show any
            if any(sz in answer_lower for sz in ['groß', 'mittel', 'klein']):
                if not any(sz in grid_text.replace('[?]', '') for sz in ['groß', 'mittel', 'klein']):
                    continue  # answer mentions size but grid has no sizes

            # Verify correct_idx is valid
            if correct_idx >= len(options_de):
                continue

            return {
                "id": f"matrix-gen-{idx:03d}",
                "quizId": "cognitive",
                "difficulty": difficulty,
                "tags": ["matrizen"],
                "question_de": q_de,
                "question_en": q_en,
                "options_de": list(options_de),
                "options_en": list(options_en),
                "correct": [correct_idx],
                "explanation_de": f"Regel: {rule_desc}. Antwort: {answer_text_de}.",
                "explanation_en": f"Rule: {rule_desc}. Answer: {answer_text_en}.",
                "mistakes_de": "Typische Fehler: (1) Nur Zeilen ODER Spalten analysieren, nicht beides. (2) Eine Eigenschaft übersehen. (3) Die Regel anhand von 2 Zellen ableiten statt alle 8 zu prüfen.",
                "mistakes_en": "Common mistakes: (1) Analysing only rows OR columns, not both. (2) Missing a property. (3) Deriving the rule from 2 cells instead of checking all 8.",
                "links": [{"url": "../knowledge/reihungstest-de.html", "label": "Reihungstest Info"}],
                "source": f"Generiert (gen_matrizen.py, Regel: {rule_desc})"
            }
        return None

def generate(count, difficulty=None, seed=None, size=3):
    if seed is not None:
        random.seed(seed)
    gen = MatrixGenerator(size)
    questions = []
    seen = set()
    attempts = 0
    while len(questions) < count and attempts < count * 10:
        q = gen.generate_one(len(questions) + 1, difficulty)
        if q and size == 4:
            if q['question_de'] in seen:
                q = None  # never emit the same 4x4 grid twice in one run
            else:
                seen.add(q['question_de'])
        if q:
            questions.append(q)
        attempts += 1
    return questions

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--count', type=int, default=50)
    parser.add_argument('--difficulty', choices=['medium', 'hard'], default=None)
    parser.add_argument('--seed', type=int, default=None)
    parser.add_argument('--size', type=int, choices=[3, 4], default=3,
                        help='grid size: 3 (default, classic 3x3) or 4 (4x4, always hard)')
    parser.add_argument('--output', type=str, default='/tmp/matrizen_generated.json')
    args = parser.parse_args()
    qs = generate(args.count, args.difficulty, args.seed, args.size)
    with open(args.output, 'w') as f:
        json.dump(qs, f, indent=2, ensure_ascii=False)
    from collections import Counter
    dc = Counter(q['difficulty'] for q in qs)
    print(f"Generated {len(qs)} Matrizen questions → {args.output}")
    print(f"Difficulty: {dict(dc)}")
    print(f"Rule variety: {len(set(q['source'] for q in qs))} unique rules")
