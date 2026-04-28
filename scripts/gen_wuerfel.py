#!/usr/bin/env python3
"""
Generate Würfel (cube spatial reasoning) questions with verified answers.
Zero AI tokens — pure simulation.

Usage:
    python3 gen_wuerfel.py --count 50 --output /tmp/wuerfel.json
    python3 gen_wuerfel.py --count 50 --difficulty hard --output /tmp/wuerfel_hard.json
"""

import json, random, argparse, sys

# ── Cube simulation ──────────────────────────────────────────────────────

OPERATIONS = {
    'in Ihre Richtung gekippt': {'V':'U','U':'H','H':'O','O':'V','L':'L','R':'R'},
    'von Ihnen weg gekippt':    {'V':'O','O':'H','H':'U','U':'V','L':'L','R':'R'},
    'nach rechts gekippt':      {'V':'R','R':'H','H':'L','L':'V','O':'O','U':'U'},
    'nach links gekippt':       {'V':'L','L':'H','H':'R','R':'V','O':'O','U':'U'},
    'um 180° gedreht':          {'V':'H','H':'V','L':'R','R':'L','O':'O','U':'U'},
    'um 90° im Uhrzeigersinn gedreht': {'V':'R','R':'H','H':'L','L':'V','O':'O','U':'U'},
    'um 90° gegen den Uhrzeigersinn gedreht': {'V':'L','L':'H','H':'R','R':'V','O':'O','U':'U'},
}

FACE_NAMES_DE = {'V': 'Vorne', 'H': 'Hinten', 'O': 'Oben', 'U': 'Unten', 'L': 'Links', 'R': 'Rechts'}
FACE_NAMES_EN = {'V': 'Front', 'H': 'Back', 'O': 'Top', 'U': 'Bottom', 'L': 'Left', 'R': 'Right'}

SYMBOL_SETS = [
    ['●', '★', '+', '△', '□', '◆'],
    ['A', 'B', 'C', 'D', 'E', 'F'],
    ['1', '2', '3', '4', '5', '6'],
    ['♥', '◆', '↑', '↓', '☽', '☀'],
    ['X', 'O', '△', '□', '♥', '★'],
    ['R', 'G', 'B', 'Y', 'P', 'W'],
    ['α', 'β', 'γ', 'δ', 'ε', 'ζ'],
    ['♠', '♣', '♦', '♥', '★', '●'],
]

QUESTION_TEMPLATES_DE = [
    "Was sehen Sie auf der {face} Fläche?",
    "Welches Symbol ist auf der {face} Seite?",
    "Was befindet sich auf der {face} Fläche?",
    "Welches Zeichen zeigt die {face} Fläche?",
    "Was ist auf der {face} Seite zu sehen?",
]

QUESTION_TEMPLATES_EN = [
    "What is on the {face} face?",
    "Which symbol is on the {face} side?",
    "What do you see on the {face} face?",
    "What symbol shows on the {face} side?",
    "Which symbol is visible on the {face} face?",
]

def simulate(state, op_name):
    mapping = OPERATIONS[op_name]
    new = {}
    for face, symbol in state.items():
        new[mapping[face]] = symbol
    return new

def simulate_sequence(start, ops):
    state = dict(start)
    for op in ops:
        state = simulate(state, op)
    return state

def has_cancellation(ops):
    """Check if the sequence contains cancelling pairs."""
    cancels = [
        ('in Ihre Richtung gekippt', 'von Ihnen weg gekippt'),
        ('nach rechts gekippt', 'nach links gekippt'),
    ]
    for i in range(len(ops) - 1):
        for a, b in cancels:
            if (ops[i] == a and ops[i+1] == b) or (ops[i] == b and ops[i+1] == a):
                return True
    # Check 4x same = identity
    if len(ops) >= 4:
        for i in range(len(ops) - 3):
            if ops[i] == ops[i+1] == ops[i+2] == ops[i+3]:
                return True
    return False

def classify_difficulty(n_steps, ops, ask_face, is_compound):
    score = n_steps * 12
    if is_compound: score += 20
    if ask_face != 'V': score += 18
    if has_cancellation(ops): score += 25
    unique_ops = len(set(ops))
    score += unique_ops * 5
    if 'um 90° im Uhrzeigersinn gedreht' in ops or 'um 90° gegen den Uhrzeigersinn gedreht' in ops:
        score += 10

    if score <= 35: return 'easy'
    if score <= 55: return 'medium'
    if score <= 80: return 'hard'
    return 'very_hard'

def generate_one(idx, target_difficulty=None):
    symbols = random.choice(SYMBOL_SETS)
    random.shuffle(symbols)
    faces = ['V', 'H', 'O', 'U', 'L', 'R']
    start = dict(zip(faces, symbols))

    # Choose complexity based on target difficulty
    if target_difficulty == 'easy':
        n_steps = random.choice([2, 3])
        op_pool = list(OPERATIONS.keys())[:5]  # no 90° rotations
        ask_face = 'V'
    elif target_difficulty == 'medium':
        n_steps = random.choice([3, 4])
        op_pool = list(OPERATIONS.keys())[:5]
        ask_face = random.choice(['V', 'V', 'V', 'O', 'U'])
    elif target_difficulty == 'hard':
        n_steps = random.choice([4, 5])
        op_pool = list(OPERATIONS.keys())
        ask_face = random.choice(['V', 'O', 'U', 'L', 'R'])
    elif target_difficulty == 'very_hard':
        n_steps = random.choice([5, 6, 7])
        op_pool = list(OPERATIONS.keys())
        ask_face = random.choice(['O', 'U', 'L', 'R', 'H'])
    else:
        n_steps = random.choice([2, 3, 4, 5, 6])
        op_pool = list(OPERATIONS.keys())
        ask_face = random.choice(faces)

    ops = [random.choice(op_pool) for _ in range(n_steps)]

    # Sometimes create compound steps (two ops described as one step)
    is_compound = target_difficulty in ('hard', 'very_hard') and random.random() < 0.3

    final = simulate_sequence(start, ops)
    correct_symbol = final[ask_face]
    difficulty = classify_difficulty(n_steps, ops, ask_face, is_compound)

    # If target specified and we missed, retry (max 10 times)
    if target_difficulty and difficulty != target_difficulty:
        return None  # caller retries

    # Build question text
    state_desc_de = ', '.join(f'{FACE_NAMES_DE[f]}={start[f]}' for f in faces)
    state_desc_en = ', '.join(f'{FACE_NAMES_EN[f]}={start[f]}' for f in faces)

    if is_compound:
        # Group ops into compound steps
        steps_de = []
        steps_en = []
        i = 0
        step_num = 1
        while i < len(ops):
            if i + 1 < len(ops) and random.random() < 0.5:
                steps_de.append(f"Schritt {step_num}: {ops[i]}, dann {ops[i+1]}")
                steps_en.append(f"Step {step_num}: {ops[i]}, then {ops[i+1]}")
                i += 2
            else:
                steps_de.append(f"Schritt {step_num}: {ops[i]}")
                steps_en.append(f"Step {step_num}: {ops[i]}")
                i += 1
            step_num += 1
    else:
        steps_de = [f"Schritt {i+1}: {op}" for i, op in enumerate(ops)]
        steps_en = [f"Step {i+1}: {op}" for i, op in enumerate(ops)]

    face_de = FACE_NAMES_DE[ask_face].upper()
    face_en = FACE_NAMES_EN[ask_face].upper()
    q_template_de = random.choice(QUESTION_TEMPLATES_DE)
    q_template_en = random.choice(QUESTION_TEMPLATES_EN)

    question_de = f"WÜRFEL: {state_desc_de}.\n\n" + "\n".join(steps_de) + f"\n\n{q_template_de.format(face=face_de)}"
    question_en = f"CUBE: {state_desc_en}.\n\n" + "\n".join(steps_en) + f"\n\n{q_template_en.format(face=face_en)}"

    # Options: all 6 symbols shuffled
    options = list(symbols)
    random.shuffle(options)
    correct_idx = options.index(correct_symbol)

    options_de = [f"{chr(97+i)}) {s}" for i, s in enumerate(options)]
    options_en = list(options_de)  # same symbols

    # Explanation: trace through steps
    trace_lines = []
    state = dict(start)
    for i, op in enumerate(ops):
        state = simulate(state, op)
        trace_lines.append(f"S{i+1}({op[:15]}...): V={state['V']}")
    trace = "; ".join(trace_lines)

    tags = ['wuerfel']
    if n_steps >= 5: tags.append('multi-schritt')
    if is_compound: tags.append('wuerfel-komplex')
    if ask_face != 'V': tags.append('wuerfel-nicht-vorne')
    if has_cancellation(ops): tags.append('wuerfel-trick')

    return {
        "id": f"wuerfel-gen-{idx:03d}",
        "quizId": "cognitive",
        "difficulty": difficulty,
        "tags": tags,
        "question_de": question_de,
        "question_en": question_en,
        "options_de": options_de,
        "options_en": options_en,
        "correct": [correct_idx],
        "explanation_de": f"Schritt-für-Schritt: {trace}. {FACE_NAMES_DE[ask_face]} = {correct_symbol}.",
        "explanation_en": f"Step-by-step: {trace}. {FACE_NAMES_EN[ask_face]} = {correct_symbol}.",
        "mistakes_de": "Typische Fehler: (1) Kippen und Drehen verwechselt. (2) Nicht alle 6 Seiten nach jedem Schritt aktualisiert. (3) Bei Nicht-Vorne-Fragen die falsche Seite abgelesen.",
        "mistakes_en": "Common mistakes: (1) Confusing tip vs rotate. (2) Not updating all 6 faces per step. (3) Reading the wrong face for non-front questions.",
        "links": [{"url": "../knowledge/reihungstest-de.html", "label": "Würfel-Glossar"}],
        "source": "Generiert (gen_wuerfel.py)"
    }

def generate(count, difficulty=None, seed=None):
    if seed is not None:
        random.seed(seed)
    questions = []
    attempts = 0
    while len(questions) < count and attempts < count * 20:
        q = generate_one(len(questions) + 1, difficulty)
        if q is not None:
            questions.append(q)
        attempts += 1
    return questions

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Generate Würfel questions')
    parser.add_argument('--count', type=int, default=50)
    parser.add_argument('--difficulty', choices=['easy', 'medium', 'hard', 'very_hard'], default=None)
    parser.add_argument('--seed', type=int, default=None)
    parser.add_argument('--output', type=str, default='/tmp/wuerfel_generated.json')
    args = parser.parse_args()

    qs = generate(args.count, args.difficulty, args.seed)
    with open(args.output, 'w') as f:
        json.dump(qs, f, indent=2, ensure_ascii=False)

    from collections import Counter
    dc = Counter(q['difficulty'] for q in qs)
    print(f"Generated {len(qs)} Würfel questions → {args.output}")
    print(f"Difficulty: {dict(dc)}")
