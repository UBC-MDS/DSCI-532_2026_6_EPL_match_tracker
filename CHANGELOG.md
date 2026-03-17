## [0.4.0] - 2026-03-17

### Added

- **Lazy Loading with Parquet + DuckDB**: Migrated data loading from CSV to parquet format stored in `data/processed/`. All filtering now happens at the database level using ibis + DuckDB, ensuring only matching rows are loaded into memory. This enables the app to scale efficiently for large datasets.
- **Enhanced Error Handling**: Improved handling of empty DataFrames across all reactive calculations and output renders. Dashboard, charts, and tables now gracefully display empty states instead of throwing KeyError exceptions.
- **Dependencies**: Added `ibis-framework[duckdb]`, `pyarrow`, and `pyarrow-hotfix` to support lazy loading and parquet operations.
- **Tests**: Added pytest unit tests for `get_team_matches` and `assign_period` helper functions in `tests/test_utils.py`. Added 4 Playwright browser tests covering dashboard load, team filter, result filter chip, and reset button behavior in `tests/test_app.py`.
- **Refactored helpers**: Extracted `get_team_matches` and `assign_period` from `src/app.py` into `src/utils.py` to enable unit testing and improve code organization.
 - **Query interaction log**: Added logging of user AI queries and responses. Logs are written to `logs/querychat_log.csv` as the local fallback and when credentials are provided appended to a Google Sheet (configured via `GSPREAD_SHEET_ID` and `GOOGLE_SERVICE_ACCOUNT_JSON` / `GSPREAD_CREDENTIALS_PATH`). 
 - **`src/app.py` logging improvements**: Implemented `_init_gspread()` to safely parse service-account JSON or credential file, added explicit startup status prints, made Google Sheets optional (graceful CSV fallback), added `log_interaction()` CSV fallback behavior, and improved `read_recent_logs()` to prefer Sheets when available. Added lightweight duplicate-avoidance state and surfaced tracebacks on init failures.
 - **Notebook: Query interaction analysis**: added `notebooks/querychat_log.ipynb` Describing why log is needed and demonstration on how it would be used it for our goals, data pipeline sketch and examples.
 - **Dependencies / environment**: Updated `environment.yml` to include pip-installed packages required for AI and Sheets integration (`querychat`, `anthropic`, `python-dotenv`, `gspread`, and `google-auth`). Ensured `requirements.txt` lists `gspread` and `google-auth` for pip-based installs.
- **Test dependencies**: Added `pytest`, `pytest-playwright`, and `playwright` to `requirements.txt` and `environment.yml`.

### Changed

- **Data Loading**: Replaced `pd.read_csv("data/raw/epl_final.csv")` with `ibis.duckdb.connect().read_parquet("data/processed/epl_final.parquet")` for lazy evaluation.
- **Filtering Logic**: Introduced `filter_matches_ibis()` function to build filter expressions at the database level before execution. All team, season, and result filters now apply via ibis before rows enter pandas DataFrames.
- **`matches_filtered()` Reactive Calc**: Updated to use lazy ibis filtering instead of pandas slicing. Filters are now applied before `.execute()` is called.
- **Helper Functions**: Updated `get_team_matches()`, `summary_home_away()`, `summary_period()`, and `out_matches_table()` to handle empty DataFrames gracefully.
- **Chatbot Appearance**: Updated the AI chatbot interface to use a fixed height container with internal scrolling. This prevents the chat panel from expanding as messages are added and improves overall layout stability and usability.
- **Updated Dependencies**: Modified `requirements.txt` and created `environment.yaml` for both pip and conda users.
- **README**: Updated with instructions to run unit tests and Playwright tests locally.
- **Final UI & Chart polish:** Adjusted AI Explorer sidebar width to 400px, reduced font sizes for the AI chat and table/chart cards, removed two exploratory AI charts from the AI Explorer view, and removed sample-size annotations `(n=...)` from dashboard x-axis labels for cleaner presentation.
- **Match Results chart (AI Explorer):** Reworked layout and plotting so the bar chart fills its card, increased margins and tweaked subplot positioning to avoid clipped axes and labels; bar color standardized to `C_HOME` (`#472A4B`).
- **Win Rate visualization:** Replaced the Home/Away win-rate bar chart with two semicircular gauges that preserve the original `C_HOME`/`C_AWAY` colors, fill from the left, and display percentages with one decimal place.
- **Season normalization:** Normalized season formats (e.g., `2024-25` → `2024/25`) so AI-derived filters match dataset `Season` values and return correct results.

### Fixed

- **KeyError on Empty Data**: Fixed crashes when no matches are found for selected filters (e.g., team/season combo with no data). All dashboard components now render safely with empty states.
- **Column Missing Error**: Ensured derived columns (`venue`, `goals_for`, `goals_against`, `win`) are present even in empty DataFrames.
- **Season Dropdown Filtered by Team**: The season selector now only shows seasons where the selected team has data, preventing users from selecting a season with no matches for that team. A `TEAM_SEASONS` lookup is computed at startup, and a reactive observer (`_update_seasons_for_team`) updates the dropdown whenever the team changes. The default and reset state correctly show Arsenal with its latest available season.
- **AI Explorer empty state (#74)**: Charts now display a descriptive "No matches found" message instead of a blank "No data" label. A yellow warning banner is shown above the charts when an AI query returns no results, guiding users to refine their query.
- **Feedback prioritization issue link:** #69

### Known Issues

- **Matplotlib charts are static**: Charts are rendered as static PNG images. Interactive exploration (hover tooltips, zoom, pan) is not yet available. Consider migrating to Plotly or Altair for future milestones.
- **Fixed card heights**: Some dashboard components use fixed pixel heights (320px) which may require responsive adjustments for very small viewports (< 600px width).
- **Google Sheets is optional**: If Google Sheets credentials are misconfigured, logs silently fall back to CSV. Users should verify `logs/querychat_log.csv` exists to confirm logging is working.

### Release Highlight: Persistent AI Query Logging with Google Sheets Integration

This release implements **Option B: Persistent LLM Logging**, enabling teams to capture and analyze AI-powered query patterns from the dashboard. Each query and response is logged with a timestamp, stored both locally (as CSV fallback) and remotely (Google Sheets when credentials are provided). This creates a data trail for understanding user behavior, improving the AI prompts, and auditing AI decisions.

- **Option chosen:** B (Persistent LLM Logging)
- **PR:** #90
- **Why this option over the others:** 
  - Logging provides immediate operational insights: which queries work well, which fail, and how users interact with the AI feature. This data helps us iterate on the AI system (Option A would only customize behavior, not provide feedback). RAG (Option C) and component click events (Option D) are longer-term features that benefit from logging data first. We prioritized logging as a foundation for future AI improvements.
- **Feature prioritization issue link:** #88

### Collaboration

- **CONTRIBUTING.md:** Updated with M3 retrospective (communication gaps, last-minute changes led to poor review practices) and M4 norms (early planning, distributed work, clear PR scoping). See PR #XX for full details.
- **M3 retrospective:** In M3, collaboration suffered from unclear task ownership and last-minute bursts. Some PRs were large and hard to review, and feedback integration was rushed. M4 focuses on spreading work evenly across team members and reviewing design docs before implementation.
- **M4:** This milestone emphasized design-before-code (specs updated before implementation), distributed work (each team member tackled feedback items), and smaller, focused PRs. We introduced structured logging from the start rather than bolting it on last-minute.

### Reflection

**What the dashboard does well:**
- The dashboard provides a clear, intuitive interface for exploring EPL performance across multiple dimensions (team, season, venue, period).
- Lazy loading with Ibis/DuckDB scales gracefully; filters apply at the database level before rows enter memory.
- The AI Explorer tab (using QueryChat) makes complex queries conversational and accessible.
- Comprehensive logging (both local and cloud-based) creates an audit trail for AI interactions.

**Current limitations:**
- Matplotlib charts are static; no interactive brushing, zoom, or hover tooltips. For a data-heavy dashboard, interactive charts (Plotly, Altair) would significantly improve exploratory analysis.
- The dashboard is team-sport focused and EPL-specific; generalizing to other sports or leagues would require data schema changes.
- The AI feature uses a fixed prompt; customization per team or per query type is not yet supported.

**Intentional deviations from DSCI 531 best practices:**
- We use fixed card heights (320px) for consistent layout, sacrificing responsive perfection for visual stability. Given the target audience (analysts on fixed workstations), this is acceptable.
- Matplotlib was retained over Plotly/Altair to keep dependencies minimal and deployment fast. The trade-off is static visualizations; in a future sprint, moving to Plotly would unlock interactivity without major refactoring.

**Trade-offs in feedback prioritization:**
- We categorized feedback into critical (broken functionality, major UX issues) and non-critical (polish, nice-to-haves). The critical items (import errors, logging side effects in UI) were fixed across PRs #89-#90. Non-critical items (interactive charts, responsive sizing) were deferred to M5 to avoid scope creep. Each team member resolved at least one feedback item, distributing the work fairly.

**Most useful materials this milestone:**
- The Shiny reactive model (especially separating `@output` from `@reactive.effect`) was crucial for fixing the logging architecture. Lab discussions about side effects in UI functions clarified the pattern.
- The feedback prioritization workflow (creating a single issue to triage all feedback) made it easy to discuss trade-offs as a team and explain decisions in release notes.
- The specification documents (`reports/m2_spec.md`, design decisions in m4_spec.md) helped us think through changes before implementing them, reducing rework and review cycles.


---
## [0.3.0] - 2026-03-07

### Added
- Added a dynamic description box above the dashboard graphs that displays the selected team and season context.
  - This description updates automatically whenever the user changes team or season filters, clearly indicating what data is being shown (e.g., "Currently viewing: Arsenal results for the 2024/25 season").
  - If no matching data exists for the user's selection, the description box informs the user: "Current: no data for Arsenal in the 2024/25 season," maintaining context even when filters result in empty results.
  - Added two additional lines to the **Story 3 chart** to display the **average goals scored at Home and Away separately across season periods (Early / Mid / Late)**.  
    - This allows users to compare how team scoring performance changes depending on    match venue across different parts of the season.
- Integrated AI-powered chat feature using `querychat` and the Anthropic API (`claude` model), allowing users to query and explore EPL match data conversationally directly within the dashboard.
- Added `python-dotenv` support for managing secrets locally via a `.env` file — the app now loads `ANTHROPIC_API_KEY` from the environment at startup.
- Updated `requirements.txt` to include `querychat`, `anthropic`, and `python-dotenv` for Posit Cloud deployment compatibility.
- Updated `environment.yml` to include `querychat`, `anthropic`, and `python-dotenv` for local conda environment setup.

### Changed
- The dashboard now defaults to showing the most recent season available (e.g., "2024/25") when first loaded or when filters are reset, rather than starting from the oldest available season.
- **Justification:** Showing the current season first makes the dashboard immediately relevant for users interested in recent EPL results, and enables clear season-to-season KPI comparisons at a glance.
- The default team selection remains as the first in alphabetical order, which is "Arsenal". We intentionally kept this order because Arsenal is a well-known club that has participated in almost every Premier League season, ensuring ample performance data. This helps provide users with a rich demo experience and reduces the chance of starting with a team that may have little or no data for some seasons.

### Fixed


### Known Issues


### Reflection
- Considered changing the x-axis of the "Average Goals by Season Period" chart from Early/Mid/Late to a categorical "Half time / Full time" split; this was not implemented because a line chart is not appropriate for that categorical division and the available data do not provide meaningful insights for that view.


## [0.2.0] - 2026-02-28

### Added
- Fully implemented dashboard in `src/app.py` (replaced v0.1 skeleton): filters, KPIs, charts, matches table, active-filters, footer, and JS reset behavior.
- New/modified UI components matching M2 job stories:
  - `input_team` and `input_season` selectors (Team / Season).
  - `input_result` selector (Match result: All / Win / Draw / Loss) replacing the earlier date-range control in the spec.
  - KPI cards: Total Matches, Win Rate, Average Goals Scored, Average Goals Conceded with previous-season comparisons (percent + absolute delta).
  - Charts: grouped bar chart (Goals Scored vs Goals Conceded by Home/Away), Home/Away Win Rate chart, and Average Goals by Season Period (Early / Mid / Late).
  - Matches table (`out_matches_table`) with deterministic period assignment logic (`assign_period`).
  - Active-filters UI chips (`out_active_filters`) and a `Reset filters` button with client-side JS.
- New files and assets:
  - `CHANGELOG.md` (this file) — new release notes.
  - `reports/m2_spec.md` — milestone 2 specification (added).
  - `img/stadium.jpg` — header artwork (added/optimized).
  - `src/www/stadium.jpg` and `src/www/stadium.svg` plus top-level `www/` copies — static asset fallbacks for deployments that serve `/www/`.

### Changed
- `src/app.py` reworked from a placeholder layout (v0.1) to a working Shiny app with data-driven reactives and renderers. Major behavioral changes include:
  - Replaced placeholder plots and many static placeholders with real data-driven plots and tables.
  - Replaced the originally-proposed date-range input (removed) with a `Match result` filter to align with the M2 decision and keep the UI robust for small-season subsamples.
  - KPI wording unified ("Average" used instead of "Avg").
  - Layout updated: KPIs placed above charts in a responsive card row; top charts are two side-by-side cards and the bottom row pairs the period line chart with the matches table.
  - Footer rewritten to show repository link, authors and `Last updated` date.
  - Color palette and chart styling updated for accessibility (colorblind-friendly choices).

### Fixed
- Restored and corrected helper implementations that were incomplete or corrupted during iterative development: `hero_header()` (header rendering and fallback logic) and `assign_period()` (period assignment by sorted match date).
- Addressed multiple CSS/JS syntax issues preventing render in earlier interim edits.

### Files added vs v0.1.0
- Added: `CHANGELOG.md`, `reports/m2_spec.md`, `img/stadium.jpg`, `src/www/stadium.jpg`, `src/www/stadium.svg`, `www/stadium.jpg`, `www/stadium.svg`, `img/demo.mp4`.
- Modified: `src/app.py` (major rewrite from v0.1 placeholder); `img/sketch.png` and `img/conversion_rate.png` remain unchanged, `README.md` updated to include the embedded demo and contributor instructions.

### Known Issues
- Charts are rendered using Matplotlib (static PNGs). Interactive exploration (hover/zoom) is not yet available.
- Some card/table heights use fixed pixel heights (320px) and may require responsive improvements for small viewports.


---

## Reflection (M2 job stories)

Mapped to M2 job stories from `reports/m2_spec.md`:

- Story 1 (Home vs Away goals): Implemented — a grouped bar chart compares average goals scored vs conceded for Home and Away, driven by `input_team` and `input_season`.
- Story 2 (Home vs Away win rate): Implemented — a focused bar chart shows win rate (%) at Home and Away for the selected team/season.
- Story 3 (Early/Mid/Late period trend): Implemented — matches for the selected team+season are sorted by date and split evenly into Early, Mid, Late groups; a single-axis line chart shows average goals scored across those periods.

- Partially implemented / next steps for M3:
  - Convert Matplotlib charts to an interactive plotting library (Plotly or Altair) to enable tooltips, brushing and zoom.
  - Improve responsive sizing to remove fixed heights and ensure equal-height columns across viewports.
  - Finalize static asset strategy (serve from `www/` at project root) and clean up duplicate asset copies once deployment approach is confirmed.


### How this compares to v0.1.0

v0.1.0 contained a lightweight UI skeleton in `src/app.py` with placeholder plots and static KPI placeholders. The 0.2.0 release transforms that scaffold into a functional, data-driven dashboard implementing the M2 job stories, adds the milestone specification document, and includes robust header-image fallbacks and small asset optimizations.

