# TU Wien Raumplanung Reihungstest 2026 — Study Dashboard

Exam preparation template for the [Bachelor Raumplanung und Raumordnung](https://www.tuwien.at/en/studies/studies/bachelor-programmes/urban-and-regional-planning) entrance exam at [TU Wien](https://www.tuwien.at).

**Live demo:** [johngavin.github.io/urban_planning](https://johngavin.github.io/urban_planning/)

---

## For Students: Create Your Own Personal Copy

This repo is a **template**. Use [Claude Cowork](https://claude.ai/code) to download it, set up your own cloud database, publish your own version, and customise it however you want. No programming skills needed.

### Quick Start (paste into Claude Cowork)

```
I want to create my own personal study dashboard for the TU Wien
Raumplanung entrance exam (Reihungstest, 10 July 2026).

There is a template at https://github.com/JohnGavin/urban_planning

Please:
1. Download/clone that repository to a folder on my computer
2. Read the CLAUDE.md file — it explains how the project works
3. Open site/index.html in my browser so I can see it
4. Tell me what the next setup steps are (Supabase + publishing)

I am not a developer. Please explain everything simply.
```

### What Happens Next

| Step | What | How |
|------|------|-----|
| **1. Download** | Get your own local copy | Claude downloads from this repo |
| **2. Browse locally** | Open `site/index.html` in any browser | Works immediately, no install needed |
| **3. Set up Supabase** | Your own cloud database (free) for quiz scores | Claude walks you through [supabase.com](https://supabase.com) signup. See [`docs/SUPABASE-GUIDE.md`](docs/SUPABASE-GUIDE.md) |
| **4. Publish online** | Your own URL accessible from phone/tablet | Drag `site/` folder onto [Netlify](https://app.netlify.com) (free, no terminal) |
| **5. Customise** | Add questions, change theme, add notes | Ask Claude: "Add 10 new questions about megatrends" |
| **6. Study** | Take quizzes, track progress, review weak areas | Scores sync to your Supabase across devices |

**Full step-by-step guide:** [`docs/STUDENT-QUICKSTART.md`](docs/STUDENT-QUICKSTART.md)

---

## What's In the Template

| Feature | Description | Link |
|---------|-------------|------|
| Study material | Knowledge base of all exam topics (German + English) | [OEREK 2030](site/knowledge/oerek2030-de.html) &#124; [Studienplan](site/knowledge/studienplan-de.html) &#124; [Exam Info](site/knowledge/reihungstest-de.html) |
| 195 quiz questions | MC with exam-style scoring, choose 5/10/all, easy/medium/hard | [Quizzes](site/quizzes/) |
| Progress tracking | Dashboard with scores, weak areas, lessons learned | [Dashboard](site/dashboard/progress.html) |
| Exam countdown | Days until exam, study plan, exam day checklist | [Countdown](site/exam/countdown.html) |
| Cube (Würfel) practice | 28 spatial reasoning questions with visual glossary | [Cognitive Quiz](site/quizzes/quiz-cognitive.html) |
| Visual Matrizen | CSS grid rendering of 3x3 pattern matching | [Cognitive Quiz](site/quizzes/quiz-cognitive.html) |
| Timed mock exam | 1 min/question countdown with auto-submit | [Mock Exam](site/quizzes/quiz-full-mock.html) |
| Mistake tracking | Lessons learned, weak tags, retrain button | [Dashboard](site/dashboard/progress.html) |
| Combined synthesis | Cross-document glossary, numbers, strategy | [Gesamtübersicht](site/knowledge/combined-de.html) |

## Exam Key Facts

| Detail | Value |
|--------|-------|
| Exam date | **[10 July 2026](https://www.tuwien.at/en/studies/studies/bachelor-programmes/urban-and-regional-planning/admission-procedure)** |
| Registration | [TISS Portal](https://tiss.tuwien.ac.at/aufnahme/aufnahmeverfahren) (1 Apr – 4 May 2026) |
| Duration | 2 hours, paper MC, German only |
| Scoring | A: Subject Knowledge (40%) + B: Text Comprehension (20%) + C: Cognitive Abilities (40%) |
| Places | 200 per year &#124; Recent acceptance: ~82-91% |
| More info | [Ranking Test](https://www.tuwien.at/en/studies/studies/bachelor-programmes/urban-and-regional-planning/admission-procedure/ranking-test) &#124; [FAQ](https://www.tuwien.at/en/studies/studies/bachelor-programmes/urban-and-regional-planning/admission-procedure/faq) |

## How to Customise (via Claude Cowork)

| What you want | What to tell Claude |
|---------------|---------------------|
| Add quiz questions | "Add 10 new questions about [topic] to `site/data/questions.json`" |
| Change difficulty | "Add more hard questions about Würfel" |
| Add study notes | "Create a new page in `site/knowledge/` about [topic]" |
| Change the look | "Change the accent colour" — edit `site/css/style.css` |
| Set up cloud sync | "Follow `docs/SUPABASE-GUIDE.md` to set up my own Supabase" |
| Publish updates | Drag `site/` folder onto Netlify again (or ask Claude) |

## Documentation

| Document | For whom | Description |
|----------|----------|-------------|
| [`docs/STUDENT-QUICKSTART.md`](docs/STUDENT-QUICKSTART.md) | Students | 7-step setup, customisation guide, troubleshooting |
| [`CLAUDE.md`](CLAUDE.md) | Claude Cowork | Auto-read instructions for helping students |
| [`docs/SUPABASE-GUIDE.md`](docs/SUPABASE-GUIDE.md) | Anyone | Cloud database setup and management |
| [`docs/DECISIONS.md`](docs/DECISIONS.md) | Curious | Why the project is built this way |
| [`docs/CONTENT-SOURCES.md`](docs/CONTENT-SOURCES.md) | Anyone | Where all content comes from |

## Source Material

| Document | Knowledge Base | Original |
|----------|---------------|----------|
| OEREK 2030 | [Read (DE)](site/knowledge/oerek2030-de.html) | [PDF](raw/Stoff_OEREK-2030%20(1).pdf) &#124; [Web](https://www.oerek2030.at) (same content) |
| Studienplan 2022 | [Read (DE)](site/knowledge/studienplan-de.html) | [PDF](raw/Stoff_Studienplan_Bachelorstudium_Raumplanung_und_Raumordnung_2022.pdf) |
| Reihungstest Info 2026 | [Read (DE)](site/knowledge/reihungstest-de.html) | [PDF](raw/Info_Raumplanung_Info_AV_RPL_TU_2026.pdf) |

## Built With

Plain HTML + CSS + JavaScript + [Supabase](https://supabase.com) free tier. No build tools, no frameworks, no server. Built with [Claude](https://claude.ai).
