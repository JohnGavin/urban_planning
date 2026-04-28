#!/usr/bin/env python3
"""
Generate Zahlenfolgen (number sequence) questions with verified answers.
Zero AI tokens — pure arithmetic.

Usage:
    python3 gen_zahlen.py --count 50 --output /tmp/zahlen.json
"""

import json, random, argparse, math

# ── Pattern templates ────────────────────────────────────────────────────
# Each template is a function: (n) -> sequence of length n+1 (last is answer)

def make_add_const(start, step):
    def gen(n): return [start + i * step for i in range(n + 1)]
    return gen, f"+{step}", 'easy'

def make_mul_const(start, factor):
    def gen(n): return [start * (factor ** i) for i in range(n + 1)]
    return gen, f"×{factor}", 'easy'

def make_alternating_ops(start, op1_val, op2_val, op1_name, op2_name):
    def gen(n):
        seq = [start]
        for i in range(n):
            if i % 2 == 0:
                if op1_name == '+': seq.append(seq[-1] + op1_val)
                elif op1_name == '×': seq.append(seq[-1] * op1_val)
                elif op1_name == '-': seq.append(seq[-1] - op1_val)
            else:
                if op2_name == '+': seq.append(seq[-1] + op2_val)
                elif op2_name == '×': seq.append(seq[-1] * op2_val)
                elif op2_name == '-': seq.append(seq[-1] - op2_val)
                elif op2_name == '÷': seq.append(seq[-1] // op2_val)
        return seq
    return gen, f"{op1_name}{op1_val}/{op2_name}{op2_val}", 'medium'

def make_interleaved(seq_a, seq_b):
    """Two sequences interleaved: a1, b1, a2, b2, ..."""
    def gen(n):
        result = []
        for i in range((n + 2) // 2):
            if len(result) <= n: result.append(seq_a[i])
            if len(result) <= n: result.append(seq_b[i])
        return result[:n + 1]
    return gen, "interleaved", 'medium'

def make_growing_diff(start, diff_start, diff_step):
    def gen(n):
        seq = [start]
        diff = diff_start
        for _ in range(n):
            seq.append(seq[-1] + diff)
            diff += diff_step
        return seq
    return gen, f"growing diff +{diff_step}", 'medium'

def make_squares():
    def gen(n): return [(i + 1) ** 2 for i in range(n + 1)]
    return gen, "n²", 'medium'

def make_cubes():
    def gen(n): return [(i + 1) ** 3 for i in range(n + 1)]
    return gen, "n³", 'hard'

def make_triangular():
    def gen(n): return [(i + 1) * (i + 2) // 2 for i in range(n + 1)]
    return gen, "n(n+1)/2", 'hard'

def make_fibonacci_like(a, b):
    def gen(n):
        seq = [a, b]
        while len(seq) <= n:
            seq.append(seq[-1] + seq[-2])
        return seq[:n + 1]
    return gen, "Fibonacci-like", 'hard'

def make_powers_of(base):
    def gen(n): return [base ** i for i in range(n + 1)]
    return gen, f"{base}^n", 'medium'

def make_factorial():
    def gen(n): return [math.factorial(i + 1) for i in range(n + 1)]
    return gen, "n!", 'hard'

def make_prime_sequence():
    def is_prime(x):
        if x < 2: return False
        for i in range(2, int(x**0.5) + 1):
            if x % i == 0: return False
        return True
    primes = [x for x in range(2, 200) if is_prime(x)]
    def gen(n): return primes[:n + 1]
    return gen, "primes", 'hard'

def make_cycle_ops(start, ops_cycle):
    """Cycle through operations: e.g., +2, ×3, -1, repeat"""
    def gen(n):
        seq = [start]
        for i in range(n):
            op, val = ops_cycle[i % len(ops_cycle)]
            if op == '+': seq.append(seq[-1] + val)
            elif op == '-': seq.append(seq[-1] - val)
            elif op == '×': seq.append(seq[-1] * val)
            elif op == '÷': seq.append(seq[-1] // val)
        return seq
    desc = "/".join(f"{op}{val}" for op, val in ops_cycle)
    return gen, f"cycle({desc})", 'hard'

def make_n_times_n_plus_k(k):
    def gen(n): return [(i + 1) * (i + 1 + k) for i in range(n + 1)]
    return gen, f"n×(n+{k})", 'hard'

QUESTION_TEMPLATES_DE = [
    "Zahlenfolge: {seq}\n\nWelche Zahl folgt als nächstes?",
    "Setzen Sie die Folge fort: {seq}\n\nWas kommt als nächstes?",
    "Finden Sie die nächste Zahl: {seq}, ?",
    "Ergänzen Sie die Zahlenfolge: {seq}\n\nDie nächste Zahl ist:",
    "Welche Zahl setzt die Reihe fort? {seq}",
]

QUESTION_TEMPLATES_EN = [
    "Number sequence: {seq}\n\nWhat number comes next?",
    "Continue the sequence: {seq}\n\nWhat comes next?",
    "Find the next number: {seq}, ?",
    "Complete the number sequence: {seq}\n\nThe next number is:",
    "Which number continues the series? {seq}",
]

def generate_distractors(correct, n=4):
    """Generate plausible wrong answers near the correct value."""
    distractors = set()
    attempts = 0
    while len(distractors) < n and attempts < 100:
        offset = random.choice([-3, -2, -1, 1, 2, 3, 5, 10, -5, -10])
        d = correct + offset
        if d != correct and d not in distractors:
            # Also try multiplicative distractors
            distractors.add(d)
        # Try common wrong patterns
        for wrong in [correct * 2, correct // 2, correct + correct % 10, correct - correct % 10]:
            if wrong != correct and wrong not in distractors and len(distractors) < n:
                distractors.add(wrong)
        attempts += 1
    return list(distractors)[:n]

def generate_pattern_pool():
    """Create a pool of pattern generators with variety."""
    pool = []

    # Easy: simple arithmetic
    for step in [2, 3, 4, 5, 7, 11]:
        for start in [1, 2, 3, 5, 10]:
            pool.append(make_add_const(start, step))
    for factor in [2, 3]:
        for start in [1, 2, 3, 5]:
            pool.append(make_mul_const(start, factor))

    # Medium: alternating, growing diff, squares, powers
    pool.append(make_alternating_ops(2, 3, 2, '×', '-'))
    pool.append(make_alternating_ops(1, 2, 3, '+', '×'))
    pool.append(make_alternating_ops(100, 10, 2, '-', '÷'))
    pool.append(make_alternating_ops(5, 3, 2, '+', '×'))
    pool.append(make_alternating_ops(3, 2, 1, '×', '+'))
    for start, ds, dd in [(1, 1, 1), (2, 2, 1), (3, 3, 2), (1, 2, 2), (5, 1, 3)]:
        pool.append(make_growing_diff(start, ds, dd))
    pool.append(make_squares())
    for base in [2, 3, 5]:
        pool.append(make_powers_of(base))

    # Hard: fibonacci, triangular, primes, cycles, factorial
    for a, b in [(1, 1), (2, 1), (1, 3), (2, 3), (3, 5)]:
        pool.append(make_fibonacci_like(a, b))
    pool.append(make_triangular())
    pool.append(make_cubes())
    pool.append(make_factorial())
    pool.append(make_prime_sequence())
    for k in [1, 2, 3]:
        pool.append(make_n_times_n_plus_k(k))
    pool.append(make_cycle_ops(2, [('+', 3), ('×', 2), ('-', 5)]))
    pool.append(make_cycle_ops(1, [('×', 3), ('+', 1)]))
    pool.append(make_cycle_ops(100, [('-', 7), ('÷', 2)]))
    pool.append(make_cycle_ops(5, [('+', 2), ('×', 2), ('-', 3)]))

    # Medium: interleaved
    pool.append(make_interleaved([2, 4, 6, 8, 10, 12], [1, 3, 9, 27, 81, 243]))
    pool.append(make_interleaved([1, 4, 9, 16, 25, 36], [100, 90, 80, 70, 60, 50]))
    pool.append(make_interleaved([3, 6, 12, 24, 48, 96], [1, 2, 3, 4, 5, 6]))

    return pool

def generate_one(idx, pool, seq_length=7):
    gen_func, pattern_name, difficulty = random.choice(pool)

    try:
        full_seq = gen_func(seq_length)
    except:
        return None

    # Validate: all integers, reasonable range
    if not all(isinstance(x, (int, float)) for x in full_seq):
        return None
    full_seq = [int(x) for x in full_seq]
    if any(abs(x) > 100000 for x in full_seq):
        return None

    shown = full_seq[:-1]
    answer = full_seq[-1]

    seq_str = ", ".join(str(x) for x in shown)

    distractors = generate_distractors(answer)
    options = [answer] + distractors
    random.shuffle(options)
    correct_idx = options.index(answer)

    q_de = random.choice(QUESTION_TEMPLATES_DE).format(seq=seq_str)
    q_en = random.choice(QUESTION_TEMPLATES_EN).format(seq=seq_str)

    options_de = [f"{chr(97+i)}) {x}" for i, x in enumerate(options)]
    options_en = list(options_de)

    return {
        "id": f"zahlen-gen-{idx:03d}",
        "quizId": "cognitive",
        "difficulty": difficulty,
        "tags": ["zahlenfolge"],
        "question_de": q_de,
        "question_en": q_en,
        "options_de": options_de,
        "options_en": options_en,
        "correct": [correct_idx],
        "explanation_de": f"Muster: {pattern_name}. Die Folge: {', '.join(str(x) for x in full_seq)}. Antwort: {answer}.",
        "explanation_en": f"Pattern: {pattern_name}. Sequence: {', '.join(str(x) for x in full_seq)}. Answer: {answer}.",
        "mistakes_de": "Typische Fehler: (1) Nur eine Operation suchen, wenn die Folge zwei verschränkte Teilfolgen hat. (2) Bei ×/÷-Mustern an +/- denken. (3) Die Folge nicht von verschiedenen Startpunkten testen.",
        "mistakes_en": "Common mistakes: (1) Looking for one operation when there are interleaved sub-sequences. (2) Thinking +/- when pattern is ×/÷. (3) Not testing from different starting points.",
        "links": [{"url": "../knowledge/reihungstest-de.html", "label": "Reihungstest Info"}],
        "source": f"Generiert (gen_zahlen.py, Muster: {pattern_name})"
    }

def generate(count, difficulty=None, seed=None):
    if seed is not None:
        random.seed(seed)
    pool = generate_pattern_pool()
    if difficulty:
        pool = [p for p in pool if p[2] == difficulty]

    questions = []
    seen_seqs = set()
    attempts = 0
    while len(questions) < count and attempts < count * 10:
        q = generate_one(len(questions) + 1, pool)
        if q:
            # Deduplicate by sequence
            seq_key = q['question_de'][:50]
            if seq_key not in seen_seqs:
                seen_seqs.add(seq_key)
                questions.append(q)
        attempts += 1
    return questions

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Generate Zahlenfolgen questions')
    parser.add_argument('--count', type=int, default=50)
    parser.add_argument('--difficulty', choices=['easy', 'medium', 'hard'], default=None)
    parser.add_argument('--seed', type=int, default=None)
    parser.add_argument('--output', type=str, default='/tmp/zahlen_generated.json')
    args = parser.parse_args()

    qs = generate(args.count, args.difficulty, args.seed)
    with open(args.output, 'w') as f:
        json.dump(qs, f, indent=2, ensure_ascii=False)

    from collections import Counter
    dc = Counter(q['difficulty'] for q in qs)
    print(f"Generated {len(qs)} Zahlenfolgen questions → {args.output}")
    print(f"Difficulty: {dict(dc)}")
    print(f"Pattern variety: {len(set(q['source'] for q in qs))} unique patterns")
