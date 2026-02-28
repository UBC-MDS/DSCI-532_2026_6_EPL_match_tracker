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

