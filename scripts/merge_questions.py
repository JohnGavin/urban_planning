#!/usr/bin/env python3
"""
Merge generated question files into the main questions.json.
Validates, deduplicates by ID, and reports stats.

Usage:
    python3 merge_questions.py --main site/data/questions.json --add /tmp/wuerfel.json /tmp/zahlen.json
"""

import json, argparse, sys
from collections import Counter

def validate(questions):
    errors = []
    ids = [q['id'] for q in questions]
    dupes = [x for x in set(ids) if ids.count(x) > 1]
    if dupes:
        errors.append(f"Duplicate IDs: {dupes}")
    for q in questions:
        for c in q.get('correct', []):
            if c >= len(q.get('options_de', [])):
                errors.append(f"Bad correct index {c} in {q['id']} (only {len(q['options_de'])} options)")
        for field in ['question_de', 'question_en', 'options_de', 'options_en', 'correct', 'explanation_de']:
            if field not in q:
                errors.append(f"Missing field '{field}' in {q['id']}")
    return errors

def merge(main_path, add_paths, dry_run=False):
    main = json.load(open(main_path))
    existing_ids = set(q['id'] for q in main)
    added = 0
    skipped = 0

    for path in add_paths:
        new = json.load(open(path))
        for q in new:
            if q['id'] in existing_ids:
                skipped += 1
            else:
                main.append(q)
                existing_ids.add(q['id'])
                added += 1

    errors = validate(main)
    if errors:
        print(f"VALIDATION ERRORS ({len(errors)}):")
        for e in errors[:10]:
            print(f"  {e}")
        if not dry_run:
            print("Not saving due to errors.")
            return False

    # Stats
    c = Counter(q['quizId'] for q in main)
    dc = Counter(q.get('difficulty', '?') for q in main)
    print(f"Total: {len(main)} questions (added {added}, skipped {skipped} dupes)")
    print(f"By quiz: {dict(c.most_common())}")
    print(f"Difficulty: {dict(dc)}")

    if not dry_run:
        with open(main_path, 'w') as f:
            json.dump(main, f, indent=2, ensure_ascii=False)
        print(f"Saved to {main_path}")
    else:
        print("(dry run — not saved)")

    return True

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Merge questions into main bank')
    parser.add_argument('--main', required=True, help='Path to main questions.json')
    parser.add_argument('--add', nargs='+', required=True, help='Paths to generated question files')
    parser.add_argument('--dry-run', action='store_true', help='Validate only, do not save')
    args = parser.parse_args()
    success = merge(args.main, args.add, args.dry_run)
    sys.exit(0 if success else 1)
