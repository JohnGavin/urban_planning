# Replication Guide for Another Student (Claude Cowork)

This guide explains how to use this project if you only have Claude Cowork
(the Claude desktop/web app with file access) and a web browser.

## Quick Start

1. **Download this repo** from GitHub: https://github.com/JohnGavin/urban_planning
   - Click the green "Code" button → "Download ZIP"
   - Or ask Claude Cowork: "Clone https://github.com/JohnGavin/urban_planning"
2. **Open the website**: navigate to `site/index.html` and open it in your browser
3. **Everything works offline** — no internet needed after download

## What You Get

- **Knowledge base** in German and English covering all exam material
- **Interactive quizzes** with instant scoring
- **Countdown timer** to exam day (10 July 2026)
- **Study schedule** showing what to learn by when
- **Progress dashboard** tracking your quiz scores and weak areas
- **Full mock exams** simulating the real 2-hour test

## How to Study

1. Start with the **Countdown** page to see your timeline
2. Read the **Knowledge Base** pages (start with OEREK 2030 — it's the biggest topic)
3. Take **quizzes** after each section
4. Check your **Dashboard** to see weak areas
5. Take **mock exams** weekly as the exam approaches

## How to Modify with Claude Cowork

Ask Claude Cowork to:
- "Generate 20 new Würfel questions: `python3 scripts/gen_wuerfel.py --count 20 --output /tmp/new.json`"
- "Merge them in: `python3 scripts/merge_questions.py --main site/data/questions.json --add /tmp/new.json`"
- "Validate: `python3 scripts/validate_questions.py site/data/questions.json`"
- "Add 5 new Part A questions about megatrends to data/questions.json"
- "Translate this section to English in site/knowledge/oerek2030-en.html"

Claude Cowork can read and edit all files directly. No build step needed.

## Question Generators (zero AI cost)

```bash
python3 scripts/gen_wuerfel.py --count 50 --difficulty hard --output /tmp/w.json
python3 scripts/gen_zahlen.py --count 50 --output /tmp/z.json
python3 scripts/gen_rechen.py --count 30 --output /tmp/r.json
python3 scripts/gen_logik.py --count 30 --output /tmp/l.json
python3 scripts/gen_matrizen.py --count 20 --output /tmp/m.json
python3 scripts/merge_questions.py --main site/data/questions.json --add /tmp/w.json /tmp/z.json /tmp/r.json /tmp/l.json /tmp/m.json
python3 scripts/validate_questions.py site/data/questions.json
```

## Student Progress

Quiz results are saved in two places:
1. **Cloud (Supabase)** — syncs across devices, persists even if you clear browser data
2. **Local (IndexedDB)** — instant, works offline as backup

Each student gets a random ID stored in their browser. This links their results.

To set up your OWN Supabase database (instead of sharing the existing one),
see `docs/SUPABASE-GUIDE.md` for step-by-step instructions.

## File Structure

```
urban_planning/
├── raw/          → Source PDFs (exam material)
├── docs/         → Decisions, rationale, this guide
├── site/         → The website (open index.html in browser)
│   ├── css/      → Styling (dark theme, TU Wien colors)
│   ├── js/       → Quiz engine, database, charts
│   ├── knowledge/→ Full knowledge base (DE + EN)
│   ├── exam/     → Countdown, exam day info, study plan
│   ├── quizzes/  → Interactive quizzes by topic
│   ├── dashboard/→ Progress tracking
│   └── data/     → Question bank (questions.json)
```

## Requirements

- A web browser (Chrome, Firefox, Safari, Edge — any modern browser)
- That's it. No R, no Python, no Node.js, no Nix, no terminal commands needed.
