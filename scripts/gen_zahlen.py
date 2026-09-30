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

# ── Triplet family ───────────────────────────────────────────────────────
# Exam example 1 (Info Reihungstest 2026): 1 4 8 3 6 12 7 ?  -> 10
# Three operations (+3, ×2, −5) repeat, i.e. the sequence splits into triplets.
# Two sub-families:
#   cycle3 : one cycle of THREE operations applied to a running value
#   block  : each triplet follows an internal rule; triplet start values follow their own rule
# Every term is a positive integer <= TRIPLET_MAX, ÷ must divide exactly.

import os, functools

TRIPLET_MAX = 999
TRIPLET_LEN = 8  # 7 shown numbers + the answer

class SelfCheckError(AssertionError):
    pass

def _check(cond, msg):
    if not cond:
        raise SelfCheckError(msg)

def apply_op(x, op, v):
    """Apply one operation; return None if the result is not a positive integer <= TRIPLET_MAX."""
    if x is None: return None
    if op == '+': r = x + v
    elif op == '−': r = x - v
    elif op == '×': r = x * v
    elif op == '÷':
        if x % v != 0: return None
        r = x // v
    else:
        raise ValueError(op)
    if r < 1 or r > TRIPLET_MAX: return None
    return r

def _fmt_op(op, v): return f"({op}{v})"

def _rand_op():
    op = random.choice(['+', '+', '−', '−', '×', '×', '÷'])
    v = random.randint(2, 4) if op in ('×', '÷') else random.randint(1, 9)
    return (op, v)

def rule_term(rule, i):
    """Term i (0-based) computed from the declared rule alone (independent of the builders)."""
    if rule['kind'] == 'cycle3':
        steps = [rule['ops'][s % 3] for s in range(i)]
        return functools.reduce(lambda acc, o: apply_op(acc, o[0], o[1]), steps, rule['start'])
    k, j = divmod(i, 3)
    if rule['start_op'] == '+': x = rule['x0'] + k * rule['start_val']
    else: x = rule['x0'] * rule['start_val'] ** k
    return functools.reduce(lambda acc, o: apply_op(acc, o[0], o[1]), rule['inner'][:j], x)

def _build_cycle3():
    ops = [_rand_op() for _ in range(3)]
    if len(set(ops)) == 1: return None
    start = random.randint(1, 20)
    seq = [start]
    for i in range(TRIPLET_LEN - 1):
        nxt = apply_op(seq[-1], *ops[i % 3])
        if nxt is None: return None
        seq.append(nxt)
    if seq[0:3] == seq[3:6]: return None
    rule = {'kind': 'cycle3', 'ops': ops, 'start': start}
    additive = all(o[0] in '+−' for o in ops)
    return seq, rule, ('medium' if additive else 'hard')

def _build_block():
    inner = [_rand_op(), _rand_op()]
    start_op = random.choice(['+', '+', '×'])
    start_val = random.randint(1, 5) if start_op == '+' else 2
    x0 = random.randint(1, 9)
    seq = []
    for k in range(3):
        x = x0 + k * start_val if start_op == '+' else x0 * start_val ** k
        trip = [x]
        for op, v in inner:
            nxt = apply_op(trip[-1], op, v)
            if nxt is None: return None
            trip.append(nxt)
        seq.extend(trip)
    seq = seq[:TRIPLET_LEN]
    if seq[0:3] == seq[3:6]: return None
    rule = {'kind': 'block', 'inner': inner, 'start_op': start_op,
            'start_val': start_val, 'x0': x0}
    additive = all(o[0] in '+−' for o in inner) and start_op == '+'
    return seq, rule, ('medium' if additive else 'hard')

def _valid_seq(seq):
    if len(seq) != TRIPLET_LEN: return False
    if any((not isinstance(x, int)) or x < 1 or x > TRIPLET_MAX for x in seq): return False
    if len(set(seq)) < 5: return False                      # near-constant
    if any(seq[i] == seq[i + 1] for i in range(len(seq) - 1)): return False
    return True

def _distractors(seq, rule, answer):
    """Wrong-cycle traps first, then small offsets as filler."""
    t = seq
    traps = []
    if rule['kind'] == 'cycle3':
        ops = rule['ops']
        traps.append(apply_op(t[6], *ops[1]))   # 2-op alternation: next op taken as op 2
        traps.append(apply_op(t[6], *ops[2]))   # repeat the last op of the cycle
        traps.append(t[6] + (t[6] - t[5]))      # repeat last difference (linear)
        traps.append(t[6] + (t[6] - t[3]))      # continue the block starts
        traps.append(t[5] + (t[4] - t[3]))      # step applied from the wrong anchor
    else:
        inner = rule['inner']
        third = apply_op(t[6], *inner[0])
        traps.append(apply_op(third, *inner[1]))  # third element of the block instead of second
        traps.append(t[6])                        # block start repeated
        traps.append(t[6] + (t[6] - t[5]))        # linear continuation
        traps.append(t[6] + (t[4] - t[3]))        # reuse previous block's step
        traps.append(t[4] + (t[4] - t[1]))        # second elements continued with wrong step
    uniq = []
    for c in traps:
        if c is not None and 1 <= c <= 9999 and c != answer and c not in uniq:
            uniq.append(c)
    random.shuffle(uniq)
    out = uniq[:4]
    for off in random.sample([1, -1, 2, -2, 3, -3, 4, 5, -5], 9):
        if len(out) >= 4: break
        c = answer + off
        if c >= 1 and c != answer and c not in out: out.append(c)
    return out

def _explain(seq, rule, answer, lang):
    de = lang == 'de'
    s = seq[:7]
    groups = f"({s[0]}, {s[1]}, {s[2]}) ({s[3]}, {s[4]}, {s[5]}) ({s[6]}, ?)"
    if rule['kind'] == 'cycle3':
        ops = rule['ops']
        chain = []
        for i in range(7):
            chain.append(str(seq[i]))
            chain.append(_fmt_op(*ops[i % 3]))
        chain.append('?')
        chain_s = " ".join(chain)
        cyc = ", ".join(f"{o}{v}" for o, v in ops)
        first = f"{ops[0][0]}{ops[0][1]}"
        calc = f"{s[6]} {ops[0][0]} {ops[0][1]} = {answer}"
        if de:
            return (f"Schritt für Schritt: {chain_s}. Gruppierung in Dreierblöcke: {groups}. "
                    f"In jedem Block wiederholen sich dieselben drei Rechenschritte: {cyc}. "
                    f"Die {s[6]} beginnt einen neuen Block, also folgt wieder der erste Schritt ({first}): {calc}. Antwort: {answer}.")
        return (f"Step by step: {chain_s}. Grouped into blocks of three: {groups}. "
                f"The same three steps repeat in every block: {cyc}. "
                f"The {s[6]} starts a new block, so the first step ({first}) comes again: {calc}. Answer: {answer}.")
    inner = rule['inner']
    inner_s = " ".join([str(seq[0]), _fmt_op(*inner[0]), str(seq[1]), _fmt_op(*inner[1]), str(seq[2])])
    srule = f"{rule['start_op']}{rule['start_val']}"
    calc = f"{s[6]} {inner[0][0]} {inner[0][1]} = {answer}"
    starts = f"{s[0]}, {s[3]}, {s[6]}"
    if de:
        return (f"Dreierblöcke: {groups}. Regel innerhalb jedes Blocks (Schritt für Schritt): {inner_s}. "
                f"Die Startwerte der Blöcke ({starts}) folgen ihrer eigenen Regel ({srule}). "
                f"Der dritte Block beginnt mit {s[6]}; die gesuchte Zahl ist die zweite im Block: {calc}. Antwort: {answer}.")
    return (f"Blocks of three: {groups}. Rule inside every block (step by step): {inner_s}. "
            f"The block start values ({starts}) follow their own rule ({srule}). "
            f"The third block starts with {s[6]}; the missing number is the second one in the block: {calc}. Answer: {answer}.")

TRIPLET_Q_DE = [
    "Zahlenfolge: {seq}\n\nWelche Zahl steht an Stelle des Fragezeichens?",
    "Setzen Sie die Folge fort: {seq}\n\nWelche Zahl ersetzt das Fragezeichen?",
    "Ergänzen Sie die Zahlenfolge: {seq}\n\nDie gesuchte Zahl ist:",
]
TRIPLET_Q_EN = [
    "Number sequence: {seq}\n\nWhich number replaces the question mark?",
    "Continue the sequence: {seq}\n\nWhich number replaces the question mark?",
    "Complete the number sequence: {seq}\n\nThe missing number is:",
]

def _existing_ids():
    """Read-only: ids already present in the main question bank."""
    path = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'site', 'data', 'questions.json')
    try:
        with open(path) as f:
            return {q['id'] for q in json.load(f)}
    except (OSError, ValueError, KeyError):
        return set()

def _generate_triplet_one(idx):
    built = random.choice([_build_cycle3, _build_block])()
    if built is None: return None
    seq, rule, difficulty = built
    if not _valid_seq(seq): return None
    answer = seq[7]
    dis = _distractors(seq, rule, answer)
    if len(dis) < 4: return None
    options = [answer] + dis
    random.shuffle(options)
    correct_idx = options.index(answer)

    # Self-verification: recompute everything from the declared rule.
    _check([rule_term(rule, i) for i in range(TRIPLET_LEN)] == seq, f"rule does not reproduce sequence {seq}")
    expected = rule_term(rule, 7)
    _check(expected == answer, f"answer {answer} != rule result {expected}")
    _check(len(options) == 5 and len(set(options)) == 5, f"options not 5 distinct: {options}")
    _check(sum(1 for o in options if o == expected) == 1, "not exactly one option satisfies the rule")
    _check(options[correct_idx] == expected, "correct index does not point at rule result")

    seq_str = ", ".join(str(x) for x in seq[:7]) + ", ?"
    opts = [f"{chr(97 + i)}) {x}" for i, x in enumerate(options)]
    return tuple(seq), {
        "id": f"zahlen-triplet-{idx:03d}",
        "quizId": "cognitive",
        "difficulty": difficulty,
        "tags": ["zahlenfolge", "triplet"],
        "question_de": random.choice(TRIPLET_Q_DE).format(seq=seq_str),
        "question_en": random.choice(TRIPLET_Q_EN).format(seq=seq_str),
        "options_de": opts,
        "options_en": list(opts),
        "correct": [correct_idx],
        "explanation_de": _explain(seq, rule, answer, 'de'),
        "explanation_en": _explain(seq, rule, answer, 'en'),
        "mistakes_de": "Typische Fehler: (1) Nur zwei Rechenschritte abwechselnd annehmen, obwohl sich drei wiederholen. (2) Den letzten Rechenschritt einfach wiederholen oder den falschen Schritt des Zyklus anwenden. (3) Nicht in Dreierblöcken gruppieren und die Folge nur Zahl für Zahl betrachten.",
        "mistakes_en": "Common mistakes: (1) Assuming two alternating steps when three steps repeat. (2) Repeating the last step or applying the wrong step of the cycle. (3) Not grouping the numbers into blocks of three and looking at single differences only.",
        "links": [{"url": "../knowledge/reihungstest-de.html", "label": "Reihungstest Info"}],
        "source": "Info Reihungstest 2026 (TU Wien), Zahlenfolgen-Beispiel 1 — generiert"
    }

def generate_triplet(count, difficulty=None, seed=None):
    if seed is not None:
        random.seed(seed)
    taken = _existing_ids()
    questions, seen, attempts, last = [], set(), 0, 0
    while len(questions) < count and attempts < count * 500:
        attempts += 1
        nid = last + 1
        while f"zahlen-triplet-{nid:03d}" in taken:
            nid += 1
        res = _generate_triplet_one(nid)
        if not res: continue
        key, q = res
        if difficulty and q['difficulty'] != difficulty: continue
        if key in seen: continue
        seen.add(key)
        last = nid
        questions.append(q)
    return questions

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Generate Zahlenfolgen questions')
    parser.add_argument('--count', type=int, default=50)
    parser.add_argument('--difficulty', choices=['easy', 'medium', 'hard'], default=None)
    parser.add_argument('--family', choices=['default', 'triplet'], default='default',
                        help="'triplet' = 3-operation cycles / triplet blocks only (default: existing pool)")
    parser.add_argument('--seed', type=int, default=None)
    parser.add_argument('--output', type=str, default='/tmp/zahlen_generated.json')
    args = parser.parse_args()

    if args.family == 'triplet':
        qs = generate_triplet(args.count, args.difficulty, args.seed)
    else:
        qs = generate(args.count, args.difficulty, args.seed)
    with open(args.output, 'w') as f:
        json.dump(qs, f, indent=2, ensure_ascii=False)

    from collections import Counter
    dc = Counter(q['difficulty'] for q in qs)
    print(f"Generated {len(qs)} Zahlenfolgen questions → {args.output}")
    print(f"Difficulty: {dict(dc)}")
    print(f"Pattern variety: {len(set(q['source'] for q in qs))} unique patterns")
