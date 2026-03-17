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

## Getting Started (Contributors)

### 1. Clone the repo

```bash
git clone https://github.com/UBC-MDS/DSCI-532_2026_6_EPL_match_tracker.git
cd DSCI-532_2026_6_EPL_match_tracker
```

### 2. Install dependencies

```bash
conda env create -f environment.yml
conda activate dsci532
```

### 3. One-time Setup: Create the Parquet Data File

The app uses a parquet file for efficient data loading. On first setup, convert the raw CSV to parquet:

```bash
python -c "import pandas as pd; df = pd.read_csv('data/raw/epl_final.csv'); df.to_parquet('data/processed/epl_final.parquet')"
```

This creates `data/processed/epl_final.parquet` which the dashboard loads at startup. You only need to run this once, unless the raw CSV is updated.

### 4. Set up environment variables

This app uses the Anthropic API for AI-powered features. Create a `.env` file in the root of the repository:

```bash
touch .env
```

Then open it and add your Anthropic API key:

```
ANTHROPIC_API_KEY='your-api-key-here'
```

> **Note:** The `.env` file is listed in `.gitignore` and should **never** be committed to the repository.

### 5. Run the app locally

```bash
shiny run src/app.py
```

Then open [http://127.0.0.1:8000](http://127.0.0.1:8000) in your browser.

### 6. Run the tests

Unit tests (pytest):
```bash
pytest tests/test_utils.py -v
```

Playwright behavior tests (requires the app to be running in a separate terminal):
```bash
# Terminal 1 - start the app
shiny run src/app.py

# Terminal 2 - run the tests
pytest tests/test_app.py -v
```

Run all tests at once:
```bash
pytest tests/ -v
```

---

## Contributing

Please read [CONTRIBUTING.md](CONTRIBUTING.md) for our branch workflow, PR process, and code style guidelines.