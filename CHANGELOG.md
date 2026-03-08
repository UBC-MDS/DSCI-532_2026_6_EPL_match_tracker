## [0.3.0] - 2026-03-07

### Added
- Added a dynamic description box above the dashboard graphs that displays the selected team and season context.
  - This description updates automatically whenever the user changes team or season filters, clearly indicating what data is being shown (e.g., "Currently viewing: Arsenal results for the 2024/25 season").
  - If no matching data exists for the user's selection, the description box informs the user: "Current: no data for Arsenal in the 2024/25 season," maintaining context even when filters result in empty results.
  - Added two additional lines to the **Story 3 chart** to display the **average goals scored at Home and Away separately across season periods (Early / Mid / Late)**.  
    - This allows users to compare how team scoring performance changes depending on    match venue across different parts of the season.
  
### Changed
- The dashboard now defaults to showing the most recent season available (e.g., "2024/25") when first loaded or when filters are reset, rather than starting from the oldest available season.
- **Justification:** Showing the current season first makes the dashboard immediately relevant for users interested in recent EPL results, and enables clear season-to-season KPI comparisons at a glance.
- The default team selection remains as the first in alphabetical order, which is "Arsenal". We intentionally kept this order because Arsenal is a well-known club that has participated in almost every Premier League season, ensuring ample performance data. This helps provide users with a rich demo experience and reduces the chance of starting with a team that may have little or no data for some seasons.


### Fixed


### Known Issues

### Reflection


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
- Considered changing the x-axis of the "Average Goals by Season Period" chart from Early/Mid/Late to a categorical "Half time / Full time" split; this was not implemented because a line chart is not appropriate for that categorical division and the available data do not provide meaningful insights for that view.

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

