# Claude Cowork Instructions for This Project

You are helping a student create their **own personal copy** of a study dashboard for the TU Wien Raumplanung Reihungstest (entrance exam) on **10 July 2026**.

The student is NOT a developer. They need you to handle all technical steps. Explain everything simply, never use jargon.

## What This Project Is

A template study dashboard built as plain HTML/CSS/JavaScript. No build tools, no frameworks, no server needed. The student opens `site/index.html` in any browser and everything works.

**Template repo:** https://github.com/JohnGavin/urban_planning
**Live demo:** https://johngavin.github.io/urban_planning/

## Setup Steps (help the student through these)

1. **Download** the repo to their computer (git clone or ZIP download)
2. **Open** `site/index.html` in a browser — verify it works
3. **Supabase** — help them create a free account, run the SQL from `docs/supabase-setup.sql`, update `site/js/supabase-sync.js` with THEIR project URL and anon key
4. **Publish** — simplest: drag `site/` folder onto [Netlify](https://app.netlify.com) (free). Alternative: GitHub Pages if they want a GitHub account.
5. **Customise** — they ask you to add questions, change theme, add notes, etc.

Full guide: `docs/STUDENT-QUICKSTART.md`

## Project Structure

```
site/                          ← The website (open index.html in browser)
  index.html                   ← Home page with study path and progress
  css/style.css                ← Dark theme, TU Wien colours
  js/
    quiz-engine.js             ← MC quiz with exam-style scoring
    student-db.js              ← IndexedDB local storage
    supabase-sync.js           ← Cloud sync (Supabase)
    countdown.js               ← Exam countdown timer
    tabs.js                    ← Tab switcher
    sidebar.js                 ← Sidebar toggle
  knowledge/                   ← Study material (DE + EN)
    oerek2030-de.html          ← OEREK 2030 (biggest exam topic)
    studienplan-de.html        ← Curriculum structure
    reihungstest-de.html       ← Exam format and tips
    *-en.html                  ← English translations
  quizzes/                     ← Interactive quizzes
    quiz-oerek-principles.html
    quiz-oerek-megatrends.html
    quiz-studienplan.html
    quiz-cognitive.html        ← Includes Würfel (cube) questions
    quiz-full-mock.html        ← Full mock exam (all questions)
  exam/countdown.html          ← Countdown + study plan + exam day details
  dashboard/progress.html      ← Progress tracking
  data/questions.json          ← All quiz questions (443 questions, bilingual)
docs/                          ← Documentation and decisions
  DECISIONS.md                 ← Why the project is built this way
  REPLICATION.md               ← How to set up your own copy
  SUPABASE-GUIDE.md            ← Cloud database setup
  CONTENT-SOURCES.md           ← Where all content comes from
  STUDENT-QUICKSTART.md        ← 7-step guide for non-developers
  supabase-setup.sql           ← Database creation SQL
scripts/                       ← Question generators + validation
  gen_wuerfel.py               ← Cube questions (verified by simulation)
  gen_zahlen.py                ← Number sequences (30+ pattern families)
  gen_rechen.py                ← Fill-in operators (brute-force solver)
  gen_logik.py                 ← Syllogisms (model-checking verifier)
  gen_matrizen.py              ← 3×3 grids (self-validating Latin squares)
  merge_questions.py           ← Merge, deduplicate, validate
  validate_questions.py        ← 15-test quality suite
raw/                           ← Source PDFs (exam material)
CHANGELOG.md                   ← Full change history
```

## How to Help the Student

### If they ask to study or take a quiz
Point them to `site/index.html` — open it in a browser. The home page has a "Start Here" section that recommends what to do next based on their progress.

### If they ask to add or modify quiz questions

**Option 1: Use generators** (preferred for cognitive questions — zero AI tokens):
```bash
python3 scripts/gen_wuerfel.py --count 20 --difficulty hard --output /tmp/new.json
python3 scripts/gen_zahlen.py --count 20 --difficulty medium --output /tmp/new2.json
python3 scripts/merge_questions.py --main site/data/questions.json --add /tmp/new.json /tmp/new2.json
python3 scripts/validate_questions.py site/data/questions.json
```

**Option 2: Edit JSON directly** (for subject knowledge / text comprehension):
Edit `site/data/questions.json`. Each question has this format:
```json
{
  "id": "unique-id",
  "quizId": "oerek-principles",
  "difficulty": "medium|hard",
  "tags": ["oerek-grundsaetze"],
  "question_de": "German question text",
  "question_en": "English question text",
  "options_de": ["a) ...", "b) ...", "c) ...", "d) ...", "e) ..."],
  "options_en": ["a) ...", "b) ...", "c) ...", "d) ...", "e) ..."],
  "correct": [0, 2],
  "explanation_de": "German explanation",
  "explanation_en": "English explanation",
  "mistakes_de": "Common mistakes",
  "mistakes_en": "Common mistakes",
  "links": [{"url": "../knowledge/oerek2030-de.html", "label": "OEREK 2030"}],
  "source": "Document reference"
}
```
Valid quizIds: `oerek-principles`, `oerek-megatrends`, `studienplan`, `oerek-actions`, `text-comprehension`, `cognitive`

**ALWAYS validate after changes:** `python3 scripts/validate_questions.py site/data/questions.json`

**NEVER use:** "Alle obigen", "a) und b)", or other composite answer options.

### If they ask to add new study material
Create or edit HTML files in `site/knowledge/`. Follow the pattern of existing pages: same sidebar nav, same CSS link (`../css/style.css`), use tab-container for sections, include `../js/tabs.js` and `../js/sidebar.js` before `</body>`.

### If they ask to change the theme or styling
Edit `site/css/style.css`. TU Wien colours are defined as CSS variables at the top.

### If they ask about the exam
Key facts: 10 July 2026, 2 hours, paper MC, German only, Parts A(40%)+B(20%)+C(40%), 200 places, ~82-91% acceptance rate recently. Full details in `site/exam/countdown.html`.

### If they ask to set up cloud sync
See `docs/SUPABASE-GUIDE.md` for step-by-step Supabase setup.

## Important Rules

- **No build step.** Never suggest npm, pip, quarto, or any tool that needs installation. Everything is plain HTML/CSS/JS.
- **German first.** The exam is in German. Always create German content first, English as a translation.
- **Exam accuracy.** Quiz questions must be factually correct based on the source PDFs in `raw/`. Do not invent facts about Austrian spatial planning.
- **Keep it simple.** The student is not a developer. Never use technical jargon in the UI. Everything should work by opening HTML files in a browser.
