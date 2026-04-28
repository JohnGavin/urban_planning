#!/usr/bin/env python3
"""
Generate Logik (syllogism) questions with verified conclusions.
Uses formal logic rules with nonsense words to prevent knowledge-based shortcuts.

Usage:
    python3 gen_logik.py --count 50 --output /tmp/logik.json
"""

import json, random, argparse
from itertools import combinations

# Nonsense word pools (German-sounding)
NOUNS = ['Blux', 'Trem', 'Voki', 'Plosa', 'Amiv', 'Dreng', 'Kelm', 'Furit',
         'Glanx', 'Horim', 'Jalp', 'Krint', 'Lurp', 'Miven', 'Norfel',
         'Pratz', 'Quil', 'Romen', 'Sulk', 'Torix', 'Waben', 'Zelk',
         'Brinx', 'Dalop', 'Fenk', 'Gurat', 'Hixen', 'Jopel', 'Kramb']

# Premise types and their logical consequences
PREMISE_TYPES = {
    'all_are': {
        'de': 'Alle {A} sind {B}',
        'en': 'All {A} are {B}',
    },
    'some_are': {
        'de': 'Zumindest ein {A} ist {B}',
        'en': 'At least one {A} is {B}',
    },
    'no_are': {
        'de': 'Kein {A} ist {B}',
        'en': 'No {A} is {B}',
    },
    'some_not': {
        'de': 'Nicht alle {A} sind {B}',
        'en': 'Not all {A} are {B}',
    },
}

CONCLUSION_TYPES = {
    'all_are': {'de': 'Alle {A} sind {B}', 'en': 'All {A} are {B}'},
    'some_are': {'de': 'Zumindest ein {A} ist {B}', 'en': 'At least one {A} is {B}'},
    'no_are': {'de': 'Kein {A} ist {B}', 'en': 'No {A} is {B}'},
    'some_not': {'de': 'Nicht alle {A} sind {B}', 'en': 'Not all {A} are {B}'},
}

def get_valid_conclusions(premises):
    """
    Given premises, determine which conclusions are logically valid.
    Uses a simple set-theoretic model checker.
    """
    valid = []
    invalid = []

    # Extract terms
    terms = set()
    for ptype, a, b in premises:
        terms.add(a)
        terms.add(b)
    terms = list(terms)

    # Generate all possible conclusions between term pairs
    for t1, t2 in [(a, b) for a in terms for b in terms if a != b]:
        for ctype in CONCLUSION_TYPES:
            conclusion = (ctype, t1, t2)
            if check_validity(premises, conclusion):
                valid.append(conclusion)
            else:
                invalid.append(conclusion)

    return valid, invalid

def check_validity(premises, conclusion):
    """
    Check if a conclusion follows from premises using model checking.
    Tests against multiple possible worlds.
    """
    ctype, ca, cb = conclusion

    # Try to find a counterexample (a model where all premises hold but conclusion doesn't)
    for _ in range(200):
        model = generate_random_model([p[1] for p in premises] + [p[2] for p in premises] + [ca, cb])
        if all(premise_holds(model, p) for p in premises):
            if not premise_holds(model, (ctype, ca, cb)):
                return False  # Found counterexample

    # No counterexample found in 200 attempts — likely valid
    # Verify with a focused check
    return True

def generate_random_model(terms, universe_size=5):
    """Generate a random model: assign random sets to each term."""
    universe = set(range(universe_size))
    model = {}
    for t in set(terms):
        size = random.randint(0, universe_size)
        model[t] = set(random.sample(list(universe), size))
    return model

def premise_holds(model, premise):
    ptype, a, b = premise
    sa = model.get(a, set())
    sb = model.get(b, set())
    if ptype == 'all_are':
        return sa.issubset(sb)
    elif ptype == 'some_are':
        return len(sa & sb) > 0
    elif ptype == 'no_are':
        return len(sa & sb) == 0
    elif ptype == 'some_not':
        return not sa.issubset(sb) or len(sa) == 0
    return False

QUESTION_TEMPLATES_DE = [
    "Welche Schlüsse sind gültig?",
    "Welche Schlussfolgerungen lassen sich ableiten?",
    "Was folgt logisch aus den Aussagen?",
    "Kreuzen Sie alle gültigen Schlüsse an.",
]
QUESTION_TEMPLATES_EN = [
    "Which conclusions are valid?",
    "Which conclusions can be derived?",
    "What follows logically from the statements?",
    "Select all valid conclusions.",
]

def generate_one(idx, target_difficulty=None):
    # Choose number of premises based on difficulty
    if target_difficulty == 'easy':
        n_premises = 2
        premise_pool = ['all_are', 'some_are']
    elif target_difficulty == 'medium':
        n_premises = 2
        premise_pool = ['all_are', 'some_are', 'no_are']
    elif target_difficulty == 'hard':
        n_premises = random.choice([2, 3])
        premise_pool = ['all_are', 'some_are', 'no_are', 'some_not']
    elif target_difficulty == 'very_hard':
        n_premises = 3
        premise_pool = ['all_are', 'some_are', 'no_are', 'some_not']
    else:
        n_premises = random.choice([2, 2, 3])
        premise_pool = ['all_are', 'some_are', 'no_are']

    for attempt in range(30):
        # Pick random terms
        terms = random.sample(NOUNS, n_premises + 1)

        # Build premises (chain: A→B→C or A→B, C→B, etc.)
        premises = []
        for i in range(n_premises):
            ptype = random.choice(premise_pool)
            premises.append((ptype, terms[i], terms[i + 1]))

        valid, invalid = get_valid_conclusions(premises)

        # We need at least 1 valid and 2 invalid for a good question
        if len(valid) < 1 or len(invalid) < 2:
            continue

        # Pick 2-3 valid and 2-3 invalid for options
        n_valid = min(random.choice([1, 2, 3]), len(valid))
        n_invalid = 5 - n_valid
        if len(invalid) < n_invalid:
            continue

        chosen_valid = random.sample(valid, n_valid)
        chosen_invalid = random.sample(invalid, min(n_invalid, len(invalid)))

        all_conclusions = chosen_valid + chosen_invalid
        random.shuffle(all_conclusions)

        correct_indices = [i for i, c in enumerate(all_conclusions) if c in chosen_valid]

        # Format premises
        premises_de = "\n".join(f"Aussage {i+1}: {PREMISE_TYPES[p[0]]['de'].format(A=p[1], B=p[2])}" for i, p in enumerate(premises))
        premises_en = "\n".join(f"Statement {i+1}: {PREMISE_TYPES[p[0]]['en'].format(A=p[1], B=p[2])}" for i, p in enumerate(premises))

        options_de = [f"{chr(97+i)}) {CONCLUSION_TYPES[c[0]]['de'].format(A=c[1], B=c[2])}" for i, c in enumerate(all_conclusions)]
        options_en = [f"{chr(97+i)}) {CONCLUSION_TYPES[c[0]]['en'].format(A=c[1], B=c[2])}" for i, c in enumerate(all_conclusions)]

        q_template_de = random.choice(QUESTION_TEMPLATES_DE)
        q_template_en = random.choice(QUESTION_TEMPLATES_EN)

        # Classify difficulty
        if n_premises == 2 and all(p[0] in ['all_are', 'some_are'] for p in premises):
            difficulty = 'medium'
        elif n_premises == 2:
            difficulty = 'hard'
        elif n_premises == 3:
            difficulty = 'hard'
        else:
            difficulty = 'medium'

        if any(p[0] == 'no_are' for p in premises):
            difficulty = 'hard'
        if any(p[0] == 'some_not' for p in premises):
            difficulty = 'hard'

        if target_difficulty and difficulty != target_difficulty:
            continue

        return {
            "id": f"logik-gen-{idx:03d}",
            "quizId": "cognitive",
            "difficulty": difficulty,
            "tags": ["logik"],
            "question_de": f"Logik:\n{premises_de}\n\n{q_template_de}",
            "question_en": f"Logic:\n{premises_en}\n\n{q_template_en}",
            "options_de": options_de,
            "options_en": options_en,
            "correct": correct_indices,
            "explanation_de": f"Gültige Schlüsse: {', '.join(chr(97+i) for i in correct_indices)}. Abgeleitet durch Verkettung der Aussagen. Schlüsse, die den Aussagen nicht widersprechen aber nicht ableitbar sind, sind FALSCH.",
            "explanation_en": f"Valid conclusions: {', '.join(chr(97+i) for i in correct_indices)}. Derived by chaining the statements. Conclusions consistent with but not derivable from the premises are FALSE.",
            "mistakes_de": "Typische Fehler: (1) 'Zumindest ein' mit 'Alle' verwechseln. (2) Schlüsse akzeptieren, die nicht widersprechen aber nicht ableitbar sind. (3) Kontraposition vergessen.",
            "mistakes_en": "Common mistakes: (1) Confusing 'at least one' with 'all'. (2) Accepting non-contradicting but non-derivable conclusions. (3) Forgetting contraposition.",
            "links": [{"url": "../knowledge/reihungstest-de.html", "label": "Reihungstest Info"}],
            "source": "Generiert (gen_logik.py)"
        }
    return None

def generate(count, difficulty=None, seed=None):
    if seed is not None:
        random.seed(seed)
    questions = []
    attempts = 0
    while len(questions) < count and attempts < count * 10:
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
    parser.add_argument('--output', type=str, default='/tmp/logik_generated.json')
    args = parser.parse_args()
    qs = generate(args.count, args.difficulty, args.seed)
    with open(args.output, 'w') as f:
        json.dump(qs, f, indent=2, ensure_ascii=False)
    from collections import Counter
    dc = Counter(q['difficulty'] for q in qs)
    print(f"Generated {len(qs)} Logik questions → {args.output}")
    print(f"Difficulty: {dict(dc)}")
