# TU Wien Raumplanung Reihungstest 2026 — Study Dashboard

Interactive exam preparation for the [Bachelor Raumplanung und Raumordnung](https://www.tuwien.at/en/studies/studies/bachelor-programmes/urban-and-regional-planning) entrance exam at [TU Wien](https://www.tuwien.at).

**Live site:** [johngavin.github.io/urban_planning](https://johngavin.github.io/urban_planning/)

---

## For Students Using Claude Cowork

**You don't need a GitHub account, programming skills, or any technical tools.**

Open [Claude Cowork](https://claude.ai/code) and paste this:

> I want to prepare for the TU Wien Raumplanung entrance exam (Reihungstest). There is a ready-made study dashboard at https://github.com/JohnGavin/urban_planning — Please download it, open site/index.html in my browser, and tell me what to do first. I am not a developer.

Claude will download everything, open the dashboard, and guide you through studying.

**Full guide:** [`docs/STUDENT-QUICKSTART.md`](docs/STUDENT-QUICKSTART.md) — what you can ask Claude to do, how to add questions, how to customise everything.

---

## What You Get

| Feature | Description | Link |
|---------|-------------|------|
| Study material | Knowledge base of all exam topics (German + English) | [OEREK 2030](site/knowledge/oerek2030-de.html) &#124; [Studienplan](site/knowledge/studienplan-de.html) &#124; [Exam Info](site/knowledge/reihungstest-de.html) |
| Interactive quizzes | 76 MC questions with exam-style scoring, choose 5/10/all, easy/medium/hard | [Quizzes](site/quizzes/) |
| Progress tracking | Dashboard with scores, weak areas, history — synced to cloud | [Dashboard](site/dashboard/progress.html) |
| Exam countdown | Days until exam, 10-week study plan, exam day checklist | [Countdown](site/exam/countdown.html) |
| Cube practice | 16 Würfel (spatial reasoning) questions across 6 sequences | [Cognitive Quiz](site/quizzes/quiz-cognitive.html) |
| Mock exam | Full practice test combining all question types | [Mock Exam](site/quizzes/quiz-full-mock.html) |

## Exam Key Facts

| Detail | Value |
|--------|-------|
| Exam date | **[10 July 2026](https://www.tuwien.at/en/studies/studies/bachelor-programmes/urban-and-regional-planning/admission-procedure)** |
| Registration | [TISS Portal](https://tiss.tuwien.ac.at/aufnahme/aufnahmeverfahren) (1 Apr – 4 May 2026) |
| Duration | 2 hours, paper MC, German only |
| Scoring | A: Subject Knowledge (40%) + B: Text Comprehension (20%) + C: Cognitive Abilities (40%) |
| Places | 200 per year &#124; Recent acceptance: ~82-91% of participants |
| More info | [Ranking Test](https://www.tuwien.at/en/studies/studies/bachelor-programmes/urban-and-regional-planning/admission-procedure/ranking-test) &#124; [FAQ](https://www.tuwien.at/en/studies/studies/bachelor-programmes/urban-and-regional-planning/admission-procedure/faq) |

## Source Material

| Document | Knowledge Base | Original PDF |
|----------|---------------|--------------|
| OEREK 2030 (Austrian Spatial Development Concept) | [Read (DE)](site/knowledge/oerek2030-de.html) | [PDF](raw/Stoff_OEREK-2030%20(1).pdf) &#124; [Official site](https://www.oerek2030.at) |
| Studienplan Bachelor Raumplanung 2022 | [Read (DE)](site/knowledge/studienplan-de.html) | [PDF](raw/Stoff_Studienplan_Bachelorstudium_Raumplanung_und_Raumordnung_2022.pdf) |
| Reihungstest Info Sheet 2026 | [Read (DE)](site/knowledge/reihungstest-de.html) &#124; [Read (EN)](site/knowledge/reihungstest-en.html) | [PDF](raw/Info_Raumplanung_Info_AV_RPL_TU_2026.pdf) |

## How to Customise (via Claude Cowork)

| What you want | What to tell Claude |
|---------------|---------------------|
| Add quiz questions | "Add 10 new questions about [topic] to `site/data/questions.json`" |
| Change difficulty | "Make question [id] easier" or "Add more hard questions about megatrends" |
| Add study material | "Create a new knowledge base page about [topic] in German in `site/knowledge/`" |
| Change the look | "Change the accent colour" or "Make the font bigger" — edit `site/css/style.css` |
| Translate content | "Translate `site/knowledge/oerek2030-de.html` to English" |
| Set up cloud sync | "Follow the steps in `docs/SUPABASE-GUIDE.md` to set up my own Supabase" |
| Add a new quiz type | "Create a new quiz page for [topic] in `site/quizzes/` following the existing pattern" |

Claude Cowork reads the [`CLAUDE.md`](CLAUDE.md) file automatically and knows the project structure, file formats, and rules.

## Documentation

| Document | For whom | Description |
|----------|----------|-------------|
| [`docs/STUDENT-QUICKSTART.md`](docs/STUDENT-QUICKSTART.md) | Students | Step-by-step setup, what to ask Claude, troubleshooting |
| [`CLAUDE.md`](CLAUDE.md) | Claude Cowork | Auto-read instructions: project structure, how to help |
| [`docs/REPLICATION.md`](docs/REPLICATION.md) | Anyone | How the project works, file structure, requirements |
| [`docs/SUPABASE-GUIDE.md`](docs/SUPABASE-GUIDE.md) | Anyone | Cloud database: setup, login, management, troubleshooting |
| [`docs/DECISIONS.md`](docs/DECISIONS.md) | Developers | Architectural decisions with rationale |
| [`docs/CONTENT-SOURCES.md`](docs/CONTENT-SOURCES.md) | Anyone | Where all content comes from |
| [`docs/supabase-setup.sql`](docs/supabase-setup.sql) | Setup | Database table creation SQL |

## Built With

Plain HTML + CSS + JavaScript + [Supabase](https://supabase.com) free tier. No build tools, no frameworks, no server. Built with [Claude](https://claude.ai).
