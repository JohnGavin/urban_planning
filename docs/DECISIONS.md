# Architectural Decisions Log

All decisions for this project, with rationale, so another student using [Claude Cowork](https://claude.ai/code)
can understand why things are built this way and replicate/extend them.

**Related:** [Content Sources](CONTENT-SOURCES.md) | [Replication Guide](REPLICATION.md) | [Supabase Guide](SUPABASE-GUIDE.md) | [Live Site](https://johngavin.github.io/urban_planning/) | [GitHub Repo](https://github.com/JohnGavin/urban_planning)

## D001: Plain HTML/CSS/JS over Quarto/Shiny/React

**Date:** 2026-04-27
**Decision:** Build the entire site as plain HTML + CSS + JavaScript with no build step.
**Alternatives considered:**
- **Quarto website** — beautiful rendering, bilingual tabs, Markdown authoring. Rejected because it requires installing Quarto CLI + R/Python. A non-technical student with only Claude Cowork cannot do this.
- **Shiny app** — full interactivity, SQLite database. Rejected because it requires R running locally.
- **Shinylive (WASM)** — no server needed but 50MB initial download, limited packages, slow load.
- **React/Vue SPA** — modern UI but requires Node.js, npm, build toolchain.

**Rationale:** The primary constraint is that another student with only Claude Cowork (no R, no Nix, no Node.js) must be able to replicate and maintain this. Plain HTML files work in any browser with zero installation. Claude Cowork can edit any file directly. The student double-clicks `index.html` and everything works.

## D002: IndexedDB for student progress (not localStorage)

**Date:** 2026-04-27
**Decision:** Use IndexedDB (via a thin JS wrapper) for storing quiz scores, progress, and study history.
**Alternatives:** localStorage (5MB limit, synchronous, no structured queries), SQLite via WASM (complex), JSON files (no browser persistence).
**Rationale:** IndexedDB is built into every modern browser, has no size limits in practice, supports structured data, and persists across sessions. The thin wrapper keeps it simple.

## D003: Dark theme with TU Wien brand colors

**Date:** 2026-04-27
**Decision:** Dark background (#1a1a2e) with TU Wien blue (#006699) as primary accent.
**Rationale:** User preference. TU Wien's brand blue provides institutional recognition. Dark theme reduces eye strain during long study sessions.

## D004: Bilingual DE/EN as separate pages (not tabs on same page)

**Date:** 2026-04-27
**Decision:** Each knowledge base topic has a `-de.html` and `-en.html` variant, with a language toggle in the navigation.
**Alternatives:** Single page with JS tab switching (more complex HTML, harder to maintain), side-by-side columns (too cramped).
**Rationale:** Separate pages are simpler to author, easier for Claude Cowork to edit (each file is self-contained), and the student can focus on one language at a time. A nav toggle switches between them.

## D005: GitHub Pages for sharing

**Date:** 2026-04-27
**Decision:** Deploy [`site/`](../site/) folder to gh-pages branch so the dashboard is publicly accessible at [johngavin.github.io/urban_planning](https://johngavin.github.io/urban_planning/).
**Rationale:** Another student can view the [live site](https://johngavin.github.io/urban_planning/), see progress, and download/clone the [repo](https://github.com/JohnGavin/urban_planning) to get their own local copy. GitHub Pages serves static HTML with zero configuration.

## D006: Exam-focused structure (Reihungstest first, curriculum second)

**Date:** 2026-04-27
**Decision:** The entire site is structured around passing the Reihungstest on 10 July 2026. The Studienplan content is included for Part A of the exam but is secondary to OEREK 2030 content.
**Rationale:** The student must pass the entrance exam before studying the full curriculum. The exam weighs Part A (subject knowledge from OEREK + Studienplan) at 40%, Part C (cognitive abilities) at 40%, and Part B (text comprehension) at 20%. Study time should be allocated proportionally.

## D007: Question bank in JSON (not embedded in HTML)

**Date:** 2026-04-27
**Decision:** All MC questions are stored in [`data/questions.json`](../site/data/questions.json) and loaded by the [quiz engine](../site/js/quiz-engine.js).
**Rationale:** Single source of truth for questions. Easy to add new questions (edit JSON). The quiz engine randomly selects and presents them. Separation of content and presentation.

## D008: Git with regular commits

**Date:** 2026-04-27
**Decision:** Commit after every meaningful unit of work. Push to GitHub. Deploy to gh-pages.
**Rationale:** Enables revert if something breaks. Provides history for the other student to follow. gh-pages deployment makes results immediately visible.
