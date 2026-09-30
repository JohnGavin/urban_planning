# Changelog

All notable changes to this project, ordered by date (newest first).

## 2026-09-30

### Cognitive question group ([#1](https://github.com/JohnGavin/urban_planning/issues/1), [#2](https://github.com/JohnGavin/urban_planning/issues/2)): 443 → 503 questions
- **Triplet number sequences (#2):** `gen_zahlen.py --family triplet`, 20 questions in the style of the Info PDF example `1 4 8 3 6 12 7 ?` (3-step cycle +3, ×2, −5). Explanations show the operation under each gap and the triplet grouping. Seed 202609.
- **4×4 matrices (#1):** `gen_matrizen.py --size 4`, 20 hard questions. Exhaustive search checks each answer is unique. The grid now renders 4 columns, and English matrix text now draws the right shapes (it was all circles). Seed 202609, `PYTHONHASHSEED=0`.
- **Cube nets (#1):** new `gen_wuerfelnetz.py`, 20 questions (extra practice, not an exam format). Answers are verified by folding (`--verify`). The net is drawn as SVG, and there is a new "Würfelnetz" filter. Seed 202609.
- **Alternative explanations:** new optional `explanations_alt` field (documented in CLAUDE.md). Students switch between reasoning paths with "Andere Erklärung". Checked by `validate_questions.py`.
- **Cache:** script and stylesheet links now carry `?v=20260930`, so returning browsers load the new engine.
- **Not done:** the 20 × 3×3 matrices in #1 already existed (30), so none were added.

## 2026-04-29

### SVG Matrix Rendering Overhaul
- Replaced Unicode characters with inline SVG shapes (cross-browser)
- 9 shapes: circle, triangle, square, star, heart, diamond, hexagon, arrow, dot
- Colour system: schwarz=filled, weiß=outline, grau=medium grey
- Size differentiation: groß=44px, mittel=30px, klein=18px
- Dot rendering: wraps into rows of 5, fits inside 80px cells
- "Shape mit N Punkt(en)" parser fix for dot-count questions
- Fixed Latin square generator bug (colour formula didn't guarantee valid squares)
- Removed 4 broken hand-written matrizen, replaced with validated ones

### Validation Test Suite
- `scripts/validate_questions.py` with 15 tests
- Catches: duplicate IDs, bad indices, "Alle obigen" patterns, visually identical cells, colour/size mismatches, missing fields
- Self-validating generator: `gen_matrizen.py` validates grid before AND after text conversion
- Run: `python3 scripts/validate_questions.py site/data/questions.json`

### Question Bank: 443 questions (was 195 on Apr 27)
- cognitive: 195 (Würfel 58, Zahlenfolgen 38, Matrizen 30, Logik 26, Rechenoperationen 25, Analogien 13)
- text-comprehension: 78
- studienplan: 47
- oerek-megatrends: 45
- oerek-principles: 39
- oerek-actions: 39
- Difficulty: medium=212, hard=220, easy=11

### Programmatic Generators (zero AI tokens per question)
- `gen_wuerfel.py` — cube spatial reasoning (7 ops × 8 symbol sets)
- `gen_zahlen.py` — number sequences (30+ pattern families)
- `gen_rechen.py` — fill-in operators (brute-force solver)
- `gen_logik.py` — syllogisms (model-checking verifier, 29 nonsense nouns)
- `gen_matrizen.py` — 3×3 grids (6 rule types, self-validating)
- `merge_questions.py` — validates, deduplicates, bans bad patterns

## 2026-04-28

### Question Doubling: 195 → 429
- 63 text comprehension questions (Part B complete at target 78)
- 76 Part A questions via 4 parallel haiku batches
- 50 generated cognitive questions (Würfel + Zahlenfolgen)
- Part balance: A=38%, B=18%, C=44% (target 40/20/40)

### Timed Mock Exam
- 1-minute-per-question countdown (was flat 2 hours)
- Timer toggle button (was tiny checkbox)
- Auto-submit when time runs out
- Available on ALL quizzes (was mock-only)

### Cognitive Sub-Type Filter
- "Thema" row on start screen: Würfel | Matrizen | Zahlenfolgen | Logik | Rechenop. | Analogien
- Students can practice one cognitive type at a time

### Collapsible Sidebar
- Section headings clickable to expand/collapse
- Arrow indicator, state persisted in localStorage
- Section with active page auto-opens

### Combined Synthesis Page (DE)
- 7 tabs: Prüfungslandkarte, Querschnittsthemen, Glossar A-Z, Zahlen & Fakten, Prüfungsstrategie, Lernmaterial, Externe Links
- Cross-document glossary (30+ terms with links)
- OEREK→Studienplan connection map (10 topic pairs)

### Stale Topic Reminders
- Home page warns "not practiced in 3+ days" with quiz links

### Review Wrong Only
- "Nur falsche wiederholen" button on quiz results

## 2026-04-27

### Initial Build (Single Session)
- 3 source PDFs digested (OEREK 2030, Studienplan, Reihungstest Info)
- Bilingual knowledge base (DE complete, EN partial)
- Dark theme with TU Wien colours (#006699)
- 195 quiz questions with exam-style scoring
- Progress dashboard with Supabase cloud sync
- Exam countdown timer (10 July 2026)
- 10-week study plan with milestones
- Mistake tracking with lessons learned tab
- Würfel glossary (7 operations, solving strategy)
- GitHub Pages deployment
- CLAUDE.md for Claude Cowork auto-instructions
- Student quickstart guide (7-step setup for non-developers)
- Netlify drag-and-drop deployment option
