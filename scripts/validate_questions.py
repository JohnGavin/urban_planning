#!/usr/bin/env python3
"""
Validation test suite for questions.json.
Run after every change. Add new tests as bugs are found.

Usage:
    python3 validate_questions.py site/data/questions.json
    python3 validate_questions.py --strict site/data/questions.json  # fail on warnings too

Reading-comprehension passages live in passages.json next to questions.json
(override with --passages). Their "evidence" quotes are checked against the
page text extracted by scripts/extract_pdf_text.py (raw/text/<doc>/pNNN.txt).

Exit codes: 0 PASS, 1 FAIL, 3 INDETERMINATE (no errors, but something could
not be checked, e.g. extracted page text missing).
"""

import json, argparse, os, re, sys
from collections import Counter, defaultdict

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TEXT_DIR = os.path.join(ROOT, 'raw', 'text')

def load(path):
    with open(path, encoding='utf-8') as f:
        return json.load(f)

class ValidationResult:
    def __init__(self):
        self.errors = []    # must fix
        self.warnings = []  # should fix
        self.unknown = []   # could not be checked (indeterminate)

    def error(self, qid, msg):
        self.errors.append(f"ERROR [{qid}]: {msg}")

    def warn(self, qid, msg):
        self.warnings.append(f"WARN  [{qid}]: {msg}")

    def indeterminate(self, qid, msg):
        self.unknown.append(f"UNKNOWN [{qid}]: {msg}")

    def ok(self):
        return len(self.errors) == 0

    def report(self):
        for e in self.errors: print(e)
        for w in self.warnings: print(w)
        for u in self.unknown: print(u)
        status = 'FAIL' if not self.ok() else ('INDETERMINATE' if self.unknown else 'PASS')
        print(f"\n{status}: {len(self.errors)} errors, {len(self.warnings)} warnings, {len(self.unknown)} unchecked")

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

def test_matrizen_4x4_structure(questions, r):
    """4x4 matrices: 4 rows x 4 cells, missing cell bottom-right, hard/cognitive,
    5 pairwise-distinct options with exactly one correct, bilingual grids of equal shape."""
    for q in questions:
        tags = q.get('tags', [])
        if 'matrizen' not in tags or '4x4' not in tags:
            continue
        if q.get('difficulty') != 'hard':
            r.error(q['id'], f"4x4 matrix must be 'hard', got '{q.get('difficulty')}'")
        if q.get('quizId') != 'cognitive':
            r.error(q['id'], f"4x4 matrix must have quizId 'cognitive', got '{q.get('quizId')}'")
        for lang, row_word in (('de', 'Zeile'), ('en', 'Row')):
            text = q.get(f'question_{lang}', '')
            rows = re.findall(rf'^{row_word}\s*(\d+):\s*(.*)$', text, re.MULTILINE)
            if [n for n, _ in rows] != ['1', '2', '3', '4']:
                r.error(q['id'], f"4x4 matrix ({lang}) needs rows 1..4, found {[n for n, _ in rows]}")
                continue
            for n, body in rows:
                cells = re.findall(r'\[([^\]]*)\]', body)
                if len(cells) != 4:
                    r.error(q['id'], f"4x4 matrix ({lang}) row {n} has {len(cells)} cells, need 4")
                elif n == '4':
                    if cells[3] != '?' or '?' in cells[:3]:
                        r.error(q['id'], f"4x4 matrix ({lang}): only the bottom-right cell may be [?]")
                elif '?' in cells:
                    r.error(q['id'], f"4x4 matrix ({lang}) row {n} contains [?]")
        opts = [re.sub(r'^[a-e]\)\s*', '', o) for o in q.get('options_de', [])]
        if len(opts) != 5 or len(set(opts)) != 5:
            r.error(q['id'], f"4x4 matrix needs 5 distinct options, got {len(opts)} ({len(set(opts))} distinct)")
        if len(q.get('correct', [])) != 1:
            r.error(q['id'], "4x4 matrix must have exactly one correct option")
        if len(q.get('options_en', [])) != len(q.get('options_de', [])):
            r.error(q['id'], "4x4 matrix: options_de / options_en length mismatch")
        if 'Schritt' not in q.get('explanation_de', ''):
            r.warn(q['id'], "4x4 matrix explanation is not step-by-step")

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

def test_matrizen_answer_color_in_grid(questions, r):
    """Correct answer's colour must appear in the grid cells."""
    colors = ['schwarz', 'weiß', 'grau']
    for q in questions:
        if 'matrizen' not in q.get('tags', []):
            continue
        text = q.get('question_de', '').lower()
        cells = re.findall(r'\[([^\]?]+)\]', text)
        grid_colors = set()
        for cell in cells:
            for c in colors:
                if c in cell.lower():
                    grid_colors.add(c)
        if not grid_colors:
            continue  # no colours in grid at all — OK (colour not a property)
        correct_opt = q['options_de'][q['correct'][0]].lower()
        correct_opt = re.sub(r'^[a-e]\)\s*', '', correct_opt)
        for c in colors:
            if c in correct_opt and c not in grid_colors:
                r.error(q['id'], f"Answer mentions '{c}' but grid only has colours: {grid_colors}")

def test_matrizen_answer_size_in_grid(questions, r):
    """Correct answer's size must appear in the grid cells."""
    sizes = ['groß', 'mittel', 'klein']
    for q in questions:
        if 'matrizen' not in q.get('tags', []):
            continue
        text = q.get('question_de', '').lower()
        cells = re.findall(r'\[([^\]?]+)\]', text)
        grid_sizes = set()
        for cell in cells:
            for sz in sizes:
                if sz in cell.lower():
                    grid_sizes.add(sz)
        if not grid_sizes:
            continue
        correct_opt = q['options_de'][q['correct'][0]].lower()
        correct_opt = re.sub(r'^[a-e]\)\s*', '', correct_opt)
        for sz in sizes:
            if sz in correct_opt and sz not in grid_sizes:
                r.error(q['id'], f"Answer mentions '{sz}' but grid only has sizes: {grid_sizes}")

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

def test_explanations_alt_schema(questions, r):
    """Optional explanations_alt: list of 2-4 objects, all four keys non-empty strings."""
    keys = ['title_de', 'title_en', 'text_de', 'text_en']
    for q in questions:
        if 'explanations_alt' not in q:
            continue
        alts = q['explanations_alt']
        if not isinstance(alts, list) or not (2 <= len(alts) <= 4):
            r.error(q['id'], "explanations_alt must be a list of 2-4 objects")
            continue
        for i, a in enumerate(alts):
            if not isinstance(a, dict):
                r.error(q['id'], f"explanations_alt[{i}] is not an object")
                continue
            for k in keys:
                if not isinstance(a.get(k), str) or not a[k].strip():
                    r.error(q['id'], f"explanations_alt[{i}].{k} missing or empty")
        titles = [a.get('title_de') for a in alts if isinstance(a, dict)]
        if len(set(titles)) != len(titles):
            r.warn(q['id'], "explanations_alt has duplicate title_de")

def test_wuerfelnetz_questions(questions, r):
    """Every wuerfelnetz question has alternative explanations and a parseable net
    (one 'Netz:' line, equal-length rows, 6 distinct symbols). Answers themselves
    are verified by folding: gen_wuerfelnetz.py --verify."""
    for q in questions:
        if 'wuerfelnetz' not in q.get('tags', []):
            continue
        if 'explanations_alt' not in q:
            r.error(q['id'], "wuerfelnetz question without explanations_alt")
        for field in ('question_de', 'question_en'):
            m = re.search(r'(?:Netz|Net):\s*([^\n]+)', q.get(field, ''))
            if not m:
                r.error(q['id'], f"{field}: no 'Netz:' line")
                continue
            rows = [row.split() for row in m.group(1).strip().split(' / ')]
            if len({len(x) for x in rows}) != 1:
                r.error(q['id'], f"{field}: net rows differ in length")
            syms = [t for row in rows for t in row if t != '.']
            if len(syms) != 6 or len(set(syms)) != 6:
                r.error(q['id'], f"{field}: net needs 6 distinct symbols, found {syms}")
        if len(set(q.get('options_de', []))) != len(q.get('options_de', [])):
            r.error(q['id'], "duplicate options")

# ── Reading comprehension: passages (issue #3) ──────────────────────────
# passages.json: [{id, variant: 'artikel'|'lang', title_de/en, paragraphs_de/en,
#                  source, evidence: [{doc, page, quote}]}]
# A question refers to its passage with "passageId". Article sets have 3-4
# paragraphs and 3-4 questions; long sets ('lesen-lang') have 2-3 paragraphs and
# exactly 3 hard questions. Answers use the exam's richtig / falsch / nicht beurteilbar.

PASSAGE_RULES = {
    'artikel': {'paragraphs': (3, 4), 'questions': (3, 4), 'tag': 'lesen-artikel', 'difficulty': None},
    'lang':    {'paragraphs': (2, 3), 'questions': (3, 3), 'tag': 'lesen-lang',    'difficulty': 'hard'},
}
QUOTED_TEXT_RE = re.compile(r'["„“]([^"“”]{150,})["“”]')


def norm_text(s):
    """Same normalisation for page text and quotes: drop line-break hyphens, collapse whitespace."""
    s = s.replace('­', '')
    s = re.sub(r'(\w)- +(?=[a-zäöüß])', r'\1', re.sub(r'\s+', ' ', s))
    return s.strip()


def test_text_comprehension_has_text(questions, passages, r):
    """Every text-comprehension question shows a text: a known passageId, or (older
    questions) the text quoted inside question_de."""
    for q in questions:
        if q.get('quizId') != 'text-comprehension':
            continue
        pid = q.get('passageId')
        if pid is not None:
            if pid not in passages:
                r.error(q['id'], f"passageId '{pid}' not found in passages.json")
        elif not QUOTED_TEXT_RE.search(q.get('question_de', '')):
            r.error(q['id'], "text-comprehension question without passageId and without a quoted text")


def test_passages_schema(questions, passages, r):
    """Passage fields complete, bilingual paragraph counts equal, paragraph count fits the variant,
    every passage is used by at least one question."""
    used = {q.get('passageId') for q in questions}
    for pid, p in passages.items():
        rule = PASSAGE_RULES.get(p.get('variant'))
        if rule is None:
            r.error(pid, f"passage variant must be one of {sorted(PASSAGE_RULES)}, got {p.get('variant')!r}")
            continue
        for k in ('title_de', 'title_en', 'source'):
            if not isinstance(p.get(k), str) or not p[k].strip():
                r.error(pid, f"passage field {k} missing or empty")
        de, en = p.get('paragraphs_de') or [], p.get('paragraphs_en') or []
        if len(de) != len(en):
            r.error(pid, f"paragraphs_de ({len(de)}) and paragraphs_en ({len(en)}) differ in length")
        lo, hi = rule['paragraphs']
        if not lo <= len(de) <= hi:
            r.error(pid, f"'{p['variant']}' passage needs {lo}-{hi} paragraphs, has {len(de)}")
        if any(not isinstance(x, str) or len(x.strip()) < 80 for x in de + en):
            r.error(pid, "every paragraph must be a non-trivial string (>= 80 chars)")
        if not p.get('evidence'):
            r.error(pid, "passage has no evidence quotes from the source documents")
        if pid not in used:
            r.error(pid, "passage is not used by any question")


def test_passage_question_sets(questions, passages, r):
    """Questions of one passage form a set: right size, tag, difficulty, 3 options
    (richtig/falsch/nicht beurteilbar) with one correct, explanation names a paragraph that exists."""
    sets = defaultdict(list)
    for q in questions:
        if q.get('passageId') in passages:
            sets[q['passageId']].append(q)
    for pid, qs in sets.items():
        p = passages[pid]
        rule = PASSAGE_RULES.get(p.get('variant'))
        if rule is None:
            continue
        lo, hi = rule['questions']
        if not lo <= len(qs) <= hi:
            r.error(pid, f"'{p['variant']}' passage needs {lo}-{hi} questions, has {len(qs)}")
        n_par = len(p.get('paragraphs_de') or [])
        for q in qs:
            if q.get('quizId') != 'text-comprehension':
                r.error(q['id'], "passage question must have quizId 'text-comprehension'")
            if rule['tag'] not in q.get('tags', []):
                r.error(q['id'], f"passage question needs tag '{rule['tag']}'")
            if rule['difficulty'] and q.get('difficulty') != rule['difficulty']:
                r.error(q['id'], f"'{p['variant']}' question must be '{rule['difficulty']}'")
            if len(q.get('options_de', [])) != 3 or len(q.get('options_en', [])) != 3:
                r.error(q['id'], "passage question needs 3 options (richtig / falsch / nicht beurteilbar)")
            if len(q.get('correct', [])) != 1:
                r.error(q['id'], "passage question must have exactly one correct option")
            for lang, word in (('de', 'Absatz'), ('en', 'aragraph')):
                refs = [int(n) for n in re.findall(rf'{word}\s+(\d+)', q.get(f'explanation_{lang}', ''))]
                if not refs:
                    r.error(q['id'], f"explanation_{lang} must say which paragraph ('{word} N') answers it")
                elif max(refs) > n_par:
                    r.error(q['id'], f"explanation_{lang} cites paragraph {max(refs)}, passage has {n_par}")
            for k in ('mistakes_de', 'mistakes_en', 'source'):
                if not q.get(k):
                    r.error(q['id'], f"passage question missing {k}")
        answers = {tuple(q.get('correct', [])) for q in qs}
        if len(qs) > 1 and len(answers) == 1:
            r.warn(pid, "all questions of this passage have the same answer")


def test_passage_evidence(questions, passages, r):
    """Each evidence quote occurs on the stated page of the extracted source text
    (raw/text/<doc>/pNNN.txt from scripts/extract_pdf_text.py)."""
    for pid, p in passages.items():
        for ev in p.get('evidence') or []:
            doc, page, quote = ev.get('doc'), ev.get('page'), ev.get('quote', '')
            if not doc or not isinstance(page, int) or len(quote.strip()) < 10:
                r.error(pid, f"evidence entry incomplete: {ev}")
                continue
            path = os.path.join(TEXT_DIR, doc, f'p{page:03d}.txt')
            if not os.path.exists(path):
                r.indeterminate(pid, f"cannot check evidence: {os.path.relpath(path, ROOT)} missing "
                                     f"(run scripts/extract_pdf_text.py)")
                continue
            with open(path, encoding='utf-8') as f:
                page_text = norm_text(f.read())
            if norm_text(quote) not in page_text:
                r.error(pid, f"evidence quote not found on {doc} p.{page}: '{quote[:60]}'")


PASSAGE_TESTS = [
    test_text_comprehension_has_text,
    test_passages_schema,
    test_passage_question_sets,
    test_passage_evidence,
]

# ── Run all tests ────────────────────────────────────────────────────────

ALL_TESTS = [
    test_valid_json_structure,
    test_correct_indices,
    test_no_duplicate_ids,
    test_no_composite_options,
    test_matrizen_visual_variety,
    test_matrizen_answer_consistency,
    test_matrizen_answer_color_in_grid,
    test_matrizen_answer_size_in_grid,
    test_matrizen_4x4_structure,
    test_option_count,
    test_difficulty_present,
    test_tags_present,
    test_explanation_length,
    test_question_length,
    test_bilingual_completeness,
    test_wuerfel_operations_valid,
    test_explanations_alt_schema,
    test_wuerfelnetz_questions,
]

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Validate questions.json')
    parser.add_argument('path', help='Path to questions.json')
    parser.add_argument('--strict', action='store_true', help='Fail on warnings too')
    parser.add_argument('--passages', help='Path to passages.json (default: next to questions.json)')
    args = parser.parse_args()

    questions = load(args.path)
    r = ValidationResult()

    passages_path = args.passages or os.path.join(os.path.dirname(os.path.abspath(args.path)), 'passages.json')
    passages = {}
    if os.path.exists(passages_path):
        plist = load(passages_path)
        for p in plist:
            if p.get('id') in passages:
                r.error(p.get('id'), "duplicate passage id")
            passages[p.get('id')] = p
    elif any(q.get('passageId') for q in questions):
        r.error('passages', f"questions use passageId but {passages_path} does not exist")

    for test in ALL_TESTS:
        test(questions, r)
    for test in PASSAGE_TESTS:
        test(questions, passages, r)

    r.report()

    # Stats
    c = Counter(q['quizId'] for q in questions)
    dc = Counter(q.get('difficulty', '?') for q in questions)
    print(f"\nStats: {len(questions)} questions")
    print(f"By quiz: {dict(c.most_common())}")
    print(f"Difficulty: {dict(dc)}")
    if passages:
        pv = Counter(p.get('variant') for p in passages.values())
        npq = sum(1 for q in questions if q.get('passageId'))
        print(f"Passages: {len(passages)} ({dict(pv)}), {npq} passage questions")

    if not (r.ok() if not args.strict else r.ok() and len(r.warnings) == 0):
        sys.exit(1)
    sys.exit(3 if r.unknown else 0)
