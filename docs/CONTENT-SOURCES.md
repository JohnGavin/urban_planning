# Content Sources

All content in this project is derived from the following sources.

## Source Documents (in [`raw/`](../raw/) folder)

| File | Description | Pages | Used for |
|------|-------------|-------|----------|
| [`Info_Raumplanung_Info_AV_RPL_TU_2026.pdf`](../raw/Info_Raumplanung_Info_AV_RPL_TU_2026.pdf) | Official info sheet for the 2026 Reihungstest | 9 | Exam format, example questions, tips |
| [`Stoff_Studienplan_Bachelorstudium_Raumplanung_und_Raumordnung_2022.pdf`](../raw/Stoff_Studienplan_Bachelorstudium_Raumplanung_und_Raumordnung_2022.pdf) | Bachelor curriculum (Studienplan) | 66 | Part A exam material: programme structure, modules, qualifications |
| [`Stoff_OEREK-2030 (1).pdf`](<../raw/Stoff_OEREK-2030 (1).pdf>) | Austrian Spatial Development Concept ([OEREK 2030](https://www.oerek2030.at)) | 178 | Part A exam material: spatial planning principles, megatrends, challenges, action program |

## Web Sources

| URL | What we extracted | Date accessed |
|-----|-------------------|---------------|
| [Admission Procedure](https://www.tuwien.at/en/studies/studies/bachelor-programmes/urban-and-regional-planning/admission-procedure) | Admission process overview | 2026-04-27 |
| [Ranking Test](https://www.tuwien.at/en/studies/studies/bachelor-programmes/urban-and-regional-planning/admission-procedure/ranking-test) | Test format details | 2026-04-27 |
| [FAQ](https://www.tuwien.at/en/studies/studies/bachelor-programmes/urban-and-regional-planning/admission-procedure/faq) | Statistics (applicants, places), timeline | 2026-04-27 |
| [Fachschaft Raumplanung](https://www.fsraum.at/studium/inskription/) | Student association info on admission | 2026-04-27 |
| [TISS Registration](https://tiss.tuwien.ac.at/aufnahme/aufnahmeverfahren) | Online registration portal | 2026-04-27 |
| [OEREK 2030 Digital](https://www.oerek2030.at) | Official digital version of the OEREK 2030 | 2026-04-27 |

## Key Statistics (from [FAQ page](https://www.tuwien.at/en/studies/studies/bachelor-programmes/urban-and-regional-planning/admission-procedure/faq), accessed 2026-04-27)

- 2024: 233 registered &rarr; 231 invited &rarr; 189 places awarded (200 available)
- 2025: 225 registered &rarr; 223 invited &rarr; 182 participated (200 available)
- 2026: [Registration](https://tiss.tuwien.ac.at/aufnahme/aufnahmeverfahren) 1 April &ndash; 4 May; Exam 10 July 2026

## Content Not Available

- **Past exam papers**: Not publicly released by [TU Wien](https://www.tuwien.at/en/studies/studies/bachelor-programmes/urban-and-regional-planning). Only the sample questions in the [Info PDF](../raw/Info_Raumplanung_Info_AV_RPL_TU_2026.pdf) are available.
- **Detailed scoring rubric**: Not published. We know the weighting (40/20/40) but not the exact number of questions per section.
- **Pass threshold**: No minimum score &mdash; it's a ranking test. Top N candidates (up to 200) get places.

## Question Sources (443 questions)

| Source | Count | How generated |
|--------|------:|---------------|
| AI-written (Claude) | ~250 | Hand-crafted by Claude Opus/Haiku from source documents |
| `gen_wuerfel.py` | ~30 | Programmatic cube simulation, mathematically verified |
| `gen_zahlen.py` | ~20 | 30+ arithmetic pattern templates |
| `gen_rechen.py` | ~25 | Brute-force operator search |
| `gen_logik.py` | ~25 | Model-checking syllogism verifier |
| `gen_matrizen.py` | ~15 | 6 rule types, self-validating Latin squares |

All questions are validated by [`scripts/validate_questions.py`](../scripts/validate_questions.py) (15 tests).

Questions are tagged with their source document and section for traceability.

English translations are full translations by Claude of the German source material.

## Related Documentation

- [Architectural Decisions](DECISIONS.md) &mdash; why the project is built this way
- [Replication Guide](REPLICATION.md) &mdash; how to set up your own copy
- [Supabase Guide](SUPABASE-GUIDE.md) &mdash; cloud database setup and access
- [Supabase Setup SQL](supabase-setup.sql) &mdash; database table creation script
- [Live Site](https://johngavin.github.io/urban_planning/) &mdash; deployed dashboard
- [GitHub Repo](https://github.com/JohnGavin/urban_planning) &mdash; source code
