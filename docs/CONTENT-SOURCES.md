# Content Sources

All content in this project is derived from the following sources.

## Source Documents (in [`raw/`](../raw/) folder)

| File | Description | Pages | Used for |
|------|-------------|-------|----------|
| [`Info_Raumplanung_Info_AV_RPL_TU_2026.pdf`](../raw/Info_Raumplanung_Info_AV_RPL_TU_2026.pdf) | Official info sheet for the 2026 Reihungstest | 9 | Exam format, example questions, tips |
| [`Stoff_Studienplan_Bachelorstudium_Raumplanung_und_Raumordnung_2022.pdf`](../raw/Stoff_Studienplan_Bachelorstudium_Raumplanung_und_Raumordnung_2022.pdf) | Bachelor curriculum (Studienplan) | 66 | Part A exam material: programme structure, modules, qualifications |
| [`Stoff_OEREK-2030 (1).pdf`](<../raw/Stoff_OEREK-2030 (1).pdf>) | Austrian Spatial Development Concept ([OEREK 2030](https://www.oerek2030.at)) | 178 | Part A exam material: spatial planning principles, megatrends, challenges, action program; Part B reading texts |
| [`2026-04-27 17.33.31.pdf`](<../raw/2026-04-27 17.33.31.pdf>) | Scanned handwritten study notes on the OEREK 2030 | 14 | Not used for questions: no text layer, and the printed sources above are authoritative |

Page numbers in question sources ("PDF-S.") are the page a PDF viewer shows, not the number printed on the page.

### Extracted page text

[`scripts/extract_pdf_text.py`](../scripts/extract_pdf_text.py) writes the text of every page of the Info PDF, the ÖREK and the Studienplan to [`raw/text/<doc>/pNNN.txt`](../raw/text/) (`oerek`, `studienplan`, `info`). It is committed so checks run without PDF tools; `python3 scripts/extract_pdf_text.py --check` shows whether it still matches the PDFs (use the same backend, pypdf or pdftotext, that wrote it).

### Reading texts (Teil B)

Reading texts are in [`site/data/passages.json`](../site/data/passages.json). Each one is a short article written from the ÖREK or the Studienplan, in German first, with an English translation. Every text lists `evidence` quotes (document, page, verbatim words); [`scripts/validate_questions.py`](../scripts/validate_questions.py) checks that each quote is on that page of the extracted text. Statements follow the exam format from the Info PDF (page 3): richtig, falsch, or nicht beurteilbar on the basis of the text alone.

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

## Question Sources

The current total is printed by `python3 scripts/validate_questions.py site/data/questions.json` (Stats line).

| Source | Count | How generated |
|--------|------:|---------------|
| AI-written (Claude) | ~250 | Hand-crafted by Claude Opus/Haiku from source documents |
| `gen_wuerfel.py` | ~30 | Programmatic cube simulation, mathematically verified |
| `gen_zahlen.py` | ~40 | 30+ arithmetic pattern templates; `--family triplet` = 3-step cycles like the Info PDF example `1 4 8 3 6 12 7 ?` |
| `gen_rechen.py` | ~25 | Brute-force operator search |
| `gen_logik.py` | ~25 | Model-checking syllogism verifier |
| `gen_matrizen.py` | ~35 | 3×3 and `--size 4` (4×4) rule types, self-validating (unique answer checked by exhaustive search) |
| `gen_wuerfelnetz.py` | ~20 | Cube nets (Zusatzübung, not an exam format); answers verified by folding, with alternative explanations |
| Reading texts (Claude) | ~46 | Teil B: 13 texts in `site/data/passages.json` written from the ÖREK and Studienplan, statements in the exam's richtig / falsch / nicht beurteilbar format; evidence quotes checked against the extracted PDF text |

All questions are validated by [`scripts/validate_questions.py`](../scripts/validate_questions.py).

Questions are tagged with their source document and section for traceability.

English translations are full translations by Claude of the German source material.

## Related Documentation

- [Architectural Decisions](DECISIONS.md) &mdash; why the project is built this way
- [Replication Guide](REPLICATION.md) &mdash; how to set up your own copy
- [Supabase Guide](SUPABASE-GUIDE.md) &mdash; cloud database setup and access
- [Supabase Setup SQL](supabase-setup.sql) &mdash; database table creation script
- [Live Site](https://johngavin.github.io/urban_planning/) &mdash; deployed dashboard
- [GitHub Repo](https://github.com/JohnGavin/urban_planning) &mdash; source code
