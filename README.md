# DSCI-532_2026_6_EPL_match_tracker

The EPL Match Tracker is an interactive dashboard developed by DSCI 532 Group 6 for visualizing and exploring English Premier League football match data. Our analysis segments the season into early, mid, and late periods to uncover performance trends, contrasts home and away metrics to assess venue impact, and evaluates tactical effectiveness using shot conversion rates and goal differences. The dashboard supports visual analytics to help users answer key questions about match dynamics and strategy, evolving through successive course milestones to include AI-powered features and advanced interactivity. 

**Built with:** Python · Shiny · Pandas · Matplotlib

---

## Live Dashboard

| Build | URL |
|-------|-----|
| Stable (main) | https://raymondww-dsci-532-2026-6-epl-match-tracker-stable.share.connect.posit.cloud |
| Preview (dev)   | https://raymondww-dsci-532-2026-6-epl-match-tracker-preview.share.connect.posit.cloud |

---

## Demo
![Demo](img/demo.gif)

---

## What does it solve?

Watching match results week by week makes it hard to see the bigger picture. This dashboard helps coaches and analysts quickly spot performance patterns across a full season — no spreadsheets needed.

Select any **team** and **season** to explore three questions:

1. **Do we play better at home or away?**
   Compares average goals scored and conceded side-by-side for Home and Away matches, so you can see whether the team is more clinical or more vulnerable depending on venue.

2. **Does venue actually affect our win rate?**
   Shows win rate (%) at Home vs Away in a single focused chart — a quick gut-check on whether the home advantage is real for that team and season.

3. **Does our attack improve or fade as the season goes on?**
   Splits the season's matches into Early, Mid, and Late thirds (by date) and plots average goals scored as a line — so you can see at a glance whether the team builds momentum, peaks early, or runs out of steam.

---