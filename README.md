# DSCI-532_2026_6_EPL_match_tracker

The EPL Match Tracker is an interactive dashboard developed by DSCI 532 Group 6 for visualizing and exploring English Premier League football match data. Our analysis segments the season into early, mid, and late periods to uncover performance trends, contrasts home and away metrics to assess venue impact, and evaluates tactical effectiveness using shot conversion rates and goal differences. The dashboard supports visual analytics to help users answer key questions about match dynamics and strategy, evolving through successive course milestones to include AI-powered features and advanced interactivity. 

**Built with:** Python · Shiny · Pandas · Matplotlib · Ibis · DuckDB

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

This app uses the Anthropic API for AI-powered features and optional Google Sheets for query logging. Create a `.env` file in the root of the repository:

```bash
touch .env
```

#### 4a. Required: Anthropic API Key

Open `.env` and add your Anthropic API key:

```
ANTHROPIC_API_KEY='your-anthropic-api-key-here'
```

You can get a key from [Anthropic Console](https://console.anthropic.com/).

#### 4b. Optional: Google Sheets Logging Credentials

If your team has set up Google Sheets for query logging, add these variables to `.env`:

```
GSPREAD_SHEET_ID=1N4RjO6syr_vkRd64lBjPMOoq7A8HH0sTmmNOqXlMRDg
GOOGLE_SERVICE_ACCOUNT_JSON='{"type": "service_account", "project_id": "epl-match-tracker", "private_key_id": "...", "private_key": "-----BEGIN PRIVATE KEY-----\n...\n-----END PRIVATE KEY-----\n", "client_email": "shiny-logging@epl-match-tracker.iam.gserviceaccount.com", ...}'
```

**Where to get these:**
- **GSPREAD_SHEET_ID:** Ask your team lead. This is the unique ID of the Google Sheet (visible in the URL).
- **GOOGLE_SERVICE_ACCOUNT_JSON:** Ask your team lead. This is the full service account JSON credentials file content as a single-line string.

**Testing Google Sheets Setup:**

After adding credentials to `.env`, run:

```bash
python -c "from dotenv import load_dotenv; import os; load_dotenv(); print('GSPREAD_SHEET_ID:', os.getenv('GSPREAD_SHEET_ID', 'NOT SET')); print('GOOGLE_SERVICE_ACCOUNT_JSON:', 'SET' if os.getenv('GOOGLE_SERVICE_ACCOUNT_JSON') else 'NOT SET')"
```

Expected output:
```
GSPREAD_SHEET_ID: 1N4RjO6syr_vkRd64lBjPMOoq7A8HH0sTmmNOqXlMRDg
GOOGLE_SERVICE_ACCOUNT_JSON: SET
```

**If you don't have Google Sheets credentials:**
- ✅ The app will still work perfectly.
- ✅ AI queries will be logged locally to `logs/querychat_log.csv` instead.
- ℹ️ On startup, you'll see: `ℹ Logs will be written to logs/querychat_log.csv`.

> **Note:** The `.env` file is listed in `.gitignore` and should **never** be committed to the repository.

#### 4c. Verify Startup Messages

When you run the app, check the console for startup messages:

**✓ Google Sheets enabled:**
```
✓ Google Sheets logging enabled. Sheet: QueryChat Log
```

**ℹ Falling back to CSV (Google Sheets not configured):**
```
ℹ Logs will be written to logs/querychat_log.csv
```

**⚠ Google Sheets credentials invalid (graceful fallback):**
```
⚠ Google Sheets logging disabled: [error details]
ℹ Logs will be written to logs/querychat_log.csv
```

### 5. Run the app locally

```bash
shiny run src/app.py
```

Then open [http://127.0.0.1:8000](http://127.0.0.1:8000) in your browser.

### 6. Run the tests

#### Unit Tests (Pytest)

Test core functions in isolation:

```bash
pytest tests/test_utils.py -v
```

Each test verifies one behavior (e.g., "test_get_team_matches_returns_correct_venue_labels").

#### Browser Tests (Playwright)

Test the dashboard UI end-to-end (requires app running):

```bash
# Terminal 1 - start the app
shiny run src/app.py

# Terminal 2 - run the tests
pytest tests/test_app.py -v
```

Tests cover dashboard load, filter interactions, and reset button behavior.

#### Run All Tests

```bash
pytest tests/ -v
```

---

## Project Structure

```
DSCI-532_2026_6_EPL_match_tracker/
├── src/
│   ├── app.py              # Main Shiny application
│   ├── utils.py            # Helper functions (get_team_matches, assign_period)
│   └── www/                # Static assets (CSS, images)
├── data/
│   ├── raw/                # Original data (epl_final.csv)
│   └── processed/          # Processed data (epl_final.parquet)
├── notebooks/              # Jupyter notebooks (EDA, experiments)
├── reports/                # Specification documents (m2_spec.md, etc.)
├── tests/                  # Unit and browser tests
├── logs/                   # Query logs (querychat_log.csv)
├── environment.yml         # Conda environment
├── requirements.txt        # Pip dependencies
├── README.md               # This file
├── CONTRIBUTING.md         # Contribution guidelines
├── CHANGELOG.md            # Release notes
└── .env                    # Environment variables (local, NOT committed)
```

---

## Contributing

Please read [CONTRIBUTING.md](CONTRIBUTING.md) for our branch workflow, PR process, code style guidelines, and M3-M4 collaboration norms.

---

**Course:** DSCI 532 (Data Visualization II), University of British Columbia  
**Milestone:** M4 (2026-03-17)
