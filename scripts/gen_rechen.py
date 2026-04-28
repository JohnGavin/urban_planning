#!/usr/bin/env python3
"""
Generate Rechenoperationen (fill-in-operators) questions with verified answers.
Brute-forces all operator combinations to find valid solutions.

Usage:
    python3 gen_rechen.py --count 50 --output /tmp/rechen.json
"""

import json, random, argparse
from itertools import product

OPS = {'+': lambda a, b: a + b, '-': lambda a, b: a - b,
       '×': lambda a, b: a * b, '÷': lambda a, b: a / b if b != 0 else None}
OP_SYMBOLS = ['+', '-', '×', '÷']

QUESTION_TEMPLATES_DE = [
    "Rechenoperationen: {equation}\n\nWelche Operatoren (+, -, ×, ÷) ergeben das richtige Ergebnis?",
    "Setzen Sie die richtigen Rechenzeichen ein: {equation}",
    "Finden Sie die Operatoren: {equation}",
    "Welche Rechenzeichen fehlen? {equation}",
]
QUESTION_TEMPLATES_EN = [
    "Arithmetic operations: {equation}\n\nWhich operators (+, -, ×, ÷) give the correct result?",
    "Insert the correct operators: {equation}",
    "Find the operators: {equation}",
    "Which operators are missing? {equation}",
]

def evaluate_left_to_right(numbers, ops):
    """Evaluate strictly left-to-right (no PEMDAS) as typical in German Einstellungstests."""
    result = numbers[0]
    for i, op in enumerate(ops):
        val = OPS[op](result, numbers[i + 1])
        if val is None:
            return None
        result = val
    return result

def evaluate_pemdas(numbers, ops):
    """Evaluate with standard order of operations."""
    # Build expression and eval safely
    expr_parts = [str(numbers[0])]
    for i, op in enumerate(ops):
        py_op = op.replace('×', '*').replace('÷', '/')
        expr_parts.append(py_op)
        expr_parts.append(str(numbers[i + 1]))
    try:
        result = eval(' '.join(expr_parts))
        return result
    except:
        return None

def find_solutions(numbers, target, n_blanks, use_pemdas=False):
    """Find all operator combinations that produce the target."""
    evaluator = evaluate_pemdas if use_pemdas else evaluate_left_to_right
    solutions = []
    for ops in product(OP_SYMBOLS, repeat=n_blanks):
        result = evaluator(numbers, ops)
        if result is not None and abs(result - target) < 0.001 and result == int(result):
            solutions.append(list(ops))
    return solutions

def generate_one(idx, target_difficulty=None):
    if target_difficulty == 'easy' or target_difficulty == 'medium':
        n_blanks = 2
        max_num = 12
        ops_allowed = ['+', '-'] if target_difficulty == 'easy' else ['+', '-', '×']
    elif target_difficulty == 'hard':
        n_blanks = random.choice([2, 3])
        max_num = 15
        ops_allowed = OP_SYMBOLS
    elif target_difficulty == 'very_hard':
        n_blanks = random.choice([3, 4])
        max_num = 20
        ops_allowed = OP_SYMBOLS
    else:
        n_blanks = random.choice([2, 2, 3, 3, 4])
        max_num = 15
        ops_allowed = OP_SYMBOLS

    # Generate random numbers and find valid operator combos
    for attempt in range(50):
        numbers = [random.randint(1, max_num) for _ in range(n_blanks + 1)]
        # Pick random ops to define the target
        true_ops = [random.choice(ops_allowed) for _ in range(n_blanks)]
        target = evaluate_left_to_right(numbers, true_ops)
        if target is None or target != int(target) or abs(target) > 999:
            continue
        target = int(target)

        # Find ALL solutions
        solutions = find_solutions(numbers, target, n_blanks)
        if not solutions:
            continue

        # We want exactly 1 solution for clean questions (or 2-3 for harder ones)
        if target_difficulty in ('easy', 'medium') and len(solutions) > 2:
            continue
        if len(solutions) > 5:
            continue  # too many valid answers = ambiguous

        # Build equation string
        blanks = ' _ '.join(str(n) for n in numbers)
        equation = f"{blanks} = {target}"

        # Build options: the correct ops + 4 wrong combos
        correct_ops_str = ' '.join(solutions[0])
        wrong_options = set()
        for ops in product(ops_allowed, repeat=n_blanks):
            ops_str = ' '.join(ops)
            if ops_str not in [' '.join(s) for s in solutions]:
                wrong_options.add(ops_str)
            if len(wrong_options) >= 8:
                break

        if len(wrong_options) < 4:
            continue

        wrong_list = random.sample(list(wrong_options), 4)
        all_options = [correct_ops_str] + wrong_list
        random.shuffle(all_options)
        correct_idx = all_options.index(correct_ops_str)

        # Classify difficulty
        if n_blanks <= 2 and all(op in ['+', '-'] for op in solutions[0]):
            difficulty = 'easy'
        elif n_blanks <= 2:
            difficulty = 'medium'
        elif n_blanks == 3:
            difficulty = 'hard'
        else:
            difficulty = 'very_hard'

        if target_difficulty and difficulty != target_difficulty:
            continue

        options_de = [f"{chr(97+i)}) {o}" for i, o in enumerate(all_options)]

        return {
            "id": f"rechen-gen-{idx:03d}",
            "quizId": "cognitive",
            "difficulty": difficulty,
            "tags": ["rechenoperationen"],
            "question_de": random.choice(QUESTION_TEMPLATES_DE).format(equation=equation),
            "question_en": random.choice(QUESTION_TEMPLATES_EN).format(equation=equation),
            "options_de": options_de,
            "options_en": list(options_de),
            "correct": [correct_idx],
            "explanation_de": f"Lösung: {' '.join(str(numbers[0]))} {' '.join(f'{solutions[0][i]} {numbers[i+1]}' for i in range(n_blanks))} = {target}. Berechnung von links nach rechts.",
            "explanation_en": f"Solution: {numbers[0]} {' '.join(f'{solutions[0][i]} {numbers[i+1]}' for i in range(n_blanks))} = {target}. Calculated left to right.",
            "mistakes_de": "Typische Fehler: (1) Punkt-vor-Strich anwenden statt links-nach-rechts. (2) ÷ übersehen. (3) Negative Zwischenergebnisse nicht berücksichtigen.",
            "mistakes_en": "Common mistakes: (1) Applying PEMDAS instead of left-to-right. (2) Overlooking ÷. (3) Not considering negative intermediate results.",
            "links": [{"url": "../knowledge/reihungstest-de.html", "label": "Reihungstest Info"}],
            "source": "Generiert (gen_rechen.py)"
        }
    return None

def generate(count, difficulty=None, seed=None):
    if seed is not None:
        random.seed(seed)
    questions = []
    attempts = 0
    while len(questions) < count and attempts < count * 20:
        q = generate_one(len(questions) + 1, difficulty)
        if q:
            questions.append(q)
        attempts += 1
    return questions

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--count', type=int, default=50)
    parser.add_argument('--difficulty', choices=['easy', 'medium', 'hard', 'very_hard'], default=None)
    parser.add_argument('--seed', type=int, default=None)
    parser.add_argument('--output', type=str, default='/tmp/rechen_generated.json')
    args = parser.parse_args()
    qs = generate(args.count, args.difficulty, args.seed)
    with open(args.output, 'w') as f:
        json.dump(qs, f, indent=2, ensure_ascii=False)
    from collections import Counter
    dc = Counter(q['difficulty'] for q in qs)
    print(f"Generated {len(qs)} Rechenoperationen → {args.output}")
    print(f"Difficulty: {dict(dc)}")
