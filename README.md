# TU Wien Raumplanung Reihungstest 2026 — Study Dashboard

Interactive exam preparation for the [Bachelor Raumplanung und Raumordnung](https://www.tuwien.at/en/studies/studies/bachelor-programmes/urban-and-regional-planning) entrance exam at [TU Wien](https://www.tuwien.at).

**Live site:** [johngavin.github.io/urban_planning](https://johngavin.github.io/urban_planning/)

## What is this?

A self-contained study dashboard built as plain HTML/CSS/JavaScript — no installation needed. Open [`site/index.html`](site/index.html) in any browser.

Features:
- Bilingual knowledge base (German + English) covering all exam material
- Interactive multiple-choice quizzes with [exam-style scoring](site/js/quiz-engine.js)
- [Countdown timer](site/exam/countdown.html) to exam day (10 July 2026)
- [10-week study plan](site/exam/countdown.html) with milestones
- [Progress dashboard](site/dashboard/progress.html) synced to cloud ([Supabase](docs/SUPABASE-GUIDE.md))
- Exam day details and preparation checklist

## Exam Details

| Detail | Value |
|--------|-------|
| Exam date | **[10 July 2026](https://www.tuwien.at/en/studies/studies/bachelor-programmes/urban-and-regional-planning/admission-procedure)** |
| Registration | [TISS Portal](https://tiss.tuwien.ac.at/aufnahme/aufnahmeverfahren) (1 Apr – 4 May 2026) |
| Duration | 2 hours |
| Format | Written on paper (MC answer sheets) |
| Language | German only |
| Parts | A: Subject Knowledge (40%) | B: Text Comprehension (20%) | C: Cognitive Abilities (40%) |
| Places | 200 per year |
| Info | [Ranking Test Details](https://www.tuwien.at/en/studies/studies/bachelor-programmes/urban-and-regional-planning/admission-procedure/ranking-test) | [FAQ](https://www.tuwien.at/en/studies/studies/bachelor-programmes/urban-and-regional-planning/admission-procedure/faq) |

## Source Material

- [OEREK 2030](https://www.oerek2030.at) (Austrian Spatial Development Concept) — [knowledge base](site/knowledge/oerek2030-de.html) | [PDF](raw/Stoff_OEREK-2030%20(1).pdf)
- [Studienplan Bachelor Raumplanung 2022](raw/Stoff_Studienplan_Bachelorstudium_Raumplanung_und_Raumordnung_2022.pdf) — [knowledge base](site/knowledge/studienplan-de.html)
- [Reihungstest Info Sheet 2026](raw/Info_Raumplanung_Info_AV_RPL_TU_2026.pdf) — [knowledge base](site/knowledge/reihungstest-de.html)

## Documentation

| Document | Description |
|----------|-------------|
| [Replication Guide](docs/REPLICATION.md) | How to set up your own copy with [Claude Cowork](https://claude.ai/code) |
| [Supabase Guide](docs/SUPABASE-GUIDE.md) | Cloud database setup, login details, management |
| [Architectural Decisions](docs/DECISIONS.md) | Why the project is built this way |
| [Content Sources](docs/CONTENT-SOURCES.md) | Where all content comes from |
| [Supabase SQL](docs/supabase-setup.sql) | Database table creation script |

## For Another Student (Claude Cowork)

See [`docs/REPLICATION.md`](docs/REPLICATION.md) for how to use this with Claude Cowork. No R, Python, Node.js, or any other tools needed. For cloud progress sync, see [`docs/SUPABASE-GUIDE.md`](docs/SUPABASE-GUIDE.md).

## Built With

Plain HTML + CSS + JavaScript + [Supabase](https://supabase.com) free tier. Built with [Claude](https://claude.ai) for exam preparation.
