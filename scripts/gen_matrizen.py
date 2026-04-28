#!/usr/bin/env python3
"""
Generate Matrizen (3x3 pattern grid) questions with verified answers.
Rules-based: each row/column follows property rules.

Usage:
    python3 gen_matrizen.py --count 50 --output /tmp/matrizen.json
"""

import json, random, argparse

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

class MatrixGenerator:
    def __init__(self):
        self.rule_types = [
            self.rule_latin_2prop,
            self.rule_latin_3prop,
            self.rule_row_constant_col_changes,
            self.rule_col_constant_row_changes,
            self.rule_arithmetic_count,
            self.rule_rotation_shift,
        ]

    def rule_latin_2prop(self):
        """Latin square: each shape and colour once per row/column."""
        shapes = random.sample(SHAPES, 3)
        colors = random.sample(COLORS, 3)
        # Create a valid Latin square for shapes
        perms = [[0,1,2], [1,2,0], [2,0,1]]
        random.shuffle(perms)
        grid = []
        for row in range(3):
            grid_row = []
            for col in range(3):
                s = shapes[perms[row][col]]
                c = colors[(perms[row][col] + row) % 3]
                grid_row.append({'shape': s, 'color': c})
            grid.append(grid_row)
        return grid, 'medium', "Lateinisches Quadrat: jede Form und Farbe einmal pro Zeile/Spalte"

    def rule_latin_3prop(self):
        """Latin square with 3 properties: shape + color + size."""
        shapes = random.sample(SHAPES, 3)
        colors = random.sample(COLORS, 3)
        sizes = list(SIZES)
        perms = [[0,1,2], [1,2,0], [2,0,1]]
        random.shuffle(perms)
        grid = []
        for row in range(3):
            grid_row = []
            for col in range(3):
                s = shapes[perms[row][col]]
                c = colors[(perms[row][col] + row) % 3]
                sz = sizes[(col + row) % 3]
                grid_row.append({'shape': s, 'color': c, 'size': sz})
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

    def generate_one(self, idx, target_difficulty=None):
        for attempt in range(20):
            rule_func = random.choice(self.rule_types)
            grid, difficulty, rule_desc = rule_func()

            if target_difficulty and difficulty != target_difficulty:
                continue

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

def generate(count, difficulty=None, seed=None):
    if seed is not None:
        random.seed(seed)
    gen = MatrixGenerator()
    questions = []
    attempts = 0
    while len(questions) < count and attempts < count * 10:
        q = gen.generate_one(len(questions) + 1, difficulty)
        if q:
            questions.append(q)
        attempts += 1
    return questions

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--count', type=int, default=50)
    parser.add_argument('--difficulty', choices=['medium', 'hard'], default=None)
    parser.add_argument('--seed', type=int, default=None)
    parser.add_argument('--output', type=str, default='/tmp/matrizen_generated.json')
    args = parser.parse_args()
    qs = generate(args.count, args.difficulty, args.seed)
    with open(args.output, 'w') as f:
        json.dump(qs, f, indent=2, ensure_ascii=False)
    from collections import Counter
    dc = Counter(q['difficulty'] for q in qs)
    print(f"Generated {len(qs)} Matrizen questions → {args.output}")
    print(f"Difficulty: {dict(dc)}")
    print(f"Rule variety: {len(set(q['source'] for q in qs))} unique rules")
