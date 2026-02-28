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

