#!/usr/bin/env python3
"""
Validation test suite for questions.json.
Run after every change. Add new tests as bugs are found.

Usage:
    python3 validate_questions.py site/data/questions.json
    python3 validate_questions.py --strict site/data/questions.json  # fail on warnings too
"""

import json, argparse, re, sys
from collections import Counter

def load(path):
    with open(path) as f:
        return json.load(f)

class ValidationResult:
    def __init__(self):
        self.errors = []    # must fix
        self.warnings = []  # should fix

    def error(self, qid, msg):
        self.errors.append(f"ERROR [{qid}]: {msg}")

    def warn(self, qid, msg):
        self.warnings.append(f"WARN  [{qid}]: {msg}")

    def ok(self):
        return len(self.errors) == 0

    def report(self):
        for e in self.errors: print(e)
        for w in self.warnings: print(w)
        print(f"\n{'PASS' if self.ok() else 'FAIL'}: {len(self.errors)} errors, {len(self.warnings)} warnings")

# ── Test functions ───────────────────────────────────────────────────────

def test_valid_json_structure(questions, r):
    """Every question has required fields."""
    required = ['id', 'quizId', 'question_de', 'question_en', 'options_de', 'options_en', 'correct', 'explanation_de']
    for q in questions:
        for f in required:
            if f not in q:
                r.error(q.get('id', '?'), f"Missing field: {f}")

def test_correct_indices(questions, r):
    """All correct[] indices are within bounds."""
    for q in questions:
        for c in q.get('correct', []):
            if c >= len(q.get('options_de', [])):
                r.error(q['id'], f"correct index {c} >= {len(q['options_de'])} options")
        if len(q.get('correct', [])) == 0:
            r.error(q['id'], "Empty correct[] array")

def test_no_duplicate_ids(questions, r):
    """No duplicate question IDs."""
    ids = [q['id'] for q in questions]
    dupes = [x for x in set(ids) if ids.count(x) > 1]
    for d in dupes:
        r.error(d, "Duplicate ID")

def test_no_composite_options(questions, r):
    """No 'Alle obigen' or 'a) und b)' composite answers."""
    banned = ['Alle obigen', 'Alle oben', 'All of the above', 'Keine der genannten', 'Alle Aspekte']
    composite_re = re.compile(r'\b[a-e]\)\s+und\s+[a-e]\)', re.IGNORECASE)
    for q in questions:
        for opt in q.get('options_de', []) + q.get('options_en', []):
            for b in banned:
                if b.lower() in opt.lower():
                    r.error(q['id'], f"Banned option pattern: '{b}' in '{opt[:60]}'")
            if composite_re.search(opt):
                r.error(q['id'], f"Composite option: '{opt[:60]}'")

def test_matrizen_visual_variety(questions, r):
    """Matrix questions must not have all visually identical cells.
    Bug: 'Quadrat mit 1 Punkt' ... 'Quadrat mit 9 Punkten' all render as
    identical squares if the renderer can't parse the dots."""
    for q in questions:
        if 'matrizen' not in q.get('tags', []):
            continue
        text = q.get('question_de', '')
        # Extract all cell descriptions
        cells = re.findall(r'\[([^\]?]+)\]', text)
        if len(cells) < 4:
            continue
        # Check if all cells have the same shape name with no visual differentiator
        shapes = set()
        has_size = False
        has_color = False
        has_count = False
        has_dots = False
        for cell in cells:
            cl = cell.lower()
            # Extract shape
            for s in ['kreis', 'dreieck', 'quadrat', 'stern', 'herz', 'raute', 'sechseck', 'pfeil']:
                if s in cl:
                    shapes.add(s)
            if any(x in cl for x in ['groß', 'mittel', 'klein']):
                has_size = True
            if any(x in cl for x in ['schwarz', 'weiß', 'grau']):
                has_color = True
            if re.search(r'\d+\s+(kreis|dreieck|quadrat|stern|herz|raute)', cl):
                has_count = True
            if 'punkt' in cl:
                has_dots = True
        # Check for arrow direction variety (arrows differ by ↑↓→←, not shape name)
        has_arrow_dirs = any(d in ' '.join(c.lower() for c in cells) for d in ['↑', '↓', '→', '←', 'oben', 'unten', 'rechts', 'links'])

        # If only one shape and no other visual differentiator → problem
        if len(shapes) == 1 and not has_size and not has_color and not has_count and not has_arrow_dirs:
            if has_dots:
                r.warn(q['id'], f"All cells same shape ({list(shapes)[0]}) differentiated only by dots — verify SVG renders dots correctly")
            else:
                r.error(q['id'], f"All cells visually identical: only shape '{list(shapes)[0]}' with no size/color/count differentiation")

def test_matrizen_answer_consistency(questions, r):
    """Matrix answer should be plausible given the grid pattern."""
    for q in questions:
        if 'matrizen' not in q.get('tags', []):
            continue
        # Check that correct answer option contains at least one property from the grid
        text = q.get('question_de', '')
        cells = re.findall(r'\[([^\]?]+)\]', text)
        if not cells:
            continue
        correct_opt = q['options_de'][q['correct'][0]] if q.get('correct') else ''
        # Collect all shapes mentioned in grid
        grid_shapes = set()
        for cell in cells:
            for s in ['Kreis', 'Dreieck', 'Quadrat', 'Stern', 'Herz', 'Raute', 'Sechseck', 'Pfeil']:
                if s.lower() in cell.lower():
                    grid_shapes.add(s)
        # Answer should contain at least one shape from the grid
        answer_has_grid_shape = any(s.lower() in correct_opt.lower() for s in grid_shapes)
        if grid_shapes and not answer_has_grid_shape:
            r.warn(q['id'], f"Answer '{correct_opt[:40]}' doesn't contain any grid shape: {grid_shapes}")

def test_option_count(questions, r):
    """Each question should have 4-6 options (3 is OK for text comprehension)."""
    for q in questions:
        n = len(q.get('options_de', []))
        is_text_comp = q.get('quizId') == 'text-comprehension'
        if n < 3:
            r.error(q['id'], f"Only {n} options (need at least 3)")
        elif n < 4 and not is_text_comp:
            r.warn(q['id'], f"Only {n} options (prefer 5)")
        elif n > 6:
            r.warn(q['id'], f"{n} options (prefer 5)")

def test_difficulty_present(questions, r):
    """Every question should have a difficulty field."""
    for q in questions:
        if 'difficulty' not in q:
            r.warn(q['id'], "Missing difficulty field")

def test_tags_present(questions, r):
    """Every question should have at least one tag."""
    for q in questions:
        if not q.get('tags') or len(q['tags']) == 0:
            r.warn(q['id'], "No tags")

def test_explanation_length(questions, r):
    """Explanations should be substantive (>20 chars)."""
    for q in questions:
        exp = q.get('explanation_de', '')
        if len(exp) < 20:
            r.warn(q['id'], f"Explanation too short ({len(exp)} chars)")

def test_question_length(questions, r):
    """Questions should be substantive."""
    for q in questions:
        qtext = q.get('question_de', '')
        if len(qtext) < 15:
            r.error(q['id'], f"Question too short ({len(qtext)} chars)")

def test_bilingual_completeness(questions, r):
    """EN fields should exist and not be empty."""
    for q in questions:
        if not q.get('question_en') or len(q['question_en']) < 10:
            r.warn(q['id'], "Missing or empty question_en")
        if not q.get('options_en') or len(q['options_en']) == 0:
            r.warn(q['id'], "Missing options_en")

def test_wuerfel_operations_valid(questions, r):
    """Würfel questions should only use known operations."""
    valid_ops = ['in ihre richtung', 'von ihnen weg', 'nach rechts', 'nach links',
                 'um 180', 'um 90', 'uhrzeigersinn', 'gegen den uhrzeigersinn',
                 'gedreht', 'gekippt']
    for q in questions:
        if 'wuerfel' not in q.get('tags', []):
            continue
        text = q.get('question_de', '').lower()
        if 'schritt' in text or 'gekippt' in text or 'gedreht' in text:
            # Has operations — check they're valid
            for line in text.split('\n'):
                if 'schritt' in line.lower():
                    has_valid = any(op in line.lower() for op in valid_ops)
                    if not has_valid and ('gekippt' in line or 'gedreht' in line):
                        r.warn(q['id'], f"Unknown operation in: {line.strip()[:80]}")

# ── Run all tests ────────────────────────────────────────────────────────

ALL_TESTS = [
    test_valid_json_structure,
    test_correct_indices,
    test_no_duplicate_ids,
    test_no_composite_options,
    test_matrizen_visual_variety,
    test_matrizen_answer_consistency,
    test_option_count,
    test_difficulty_present,
    test_tags_present,
    test_explanation_length,
    test_question_length,
    test_bilingual_completeness,
    test_wuerfel_operations_valid,
]

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Validate questions.json')
    parser.add_argument('path', help='Path to questions.json')
    parser.add_argument('--strict', action='store_true', help='Fail on warnings too')
    args = parser.parse_args()

    questions = load(args.path)
    r = ValidationResult()

    for test in ALL_TESTS:
        test(questions, r)

    r.report()

    # Stats
    c = Counter(q['quizId'] for q in questions)
    dc = Counter(q.get('difficulty', '?') for q in questions)
    print(f"\nStats: {len(questions)} questions")
    print(f"By quiz: {dict(c.most_common())}")
    print(f"Difficulty: {dict(dc)}")

    sys.exit(0 if (r.ok() if not args.strict else r.ok() and len(r.warnings) == 0) else 1)
