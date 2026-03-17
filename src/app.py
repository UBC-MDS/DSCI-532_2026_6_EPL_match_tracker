from shiny import App, ui, render, reactive
import matplotlib.pyplot as plt
from matplotlib.patches import Wedge
import pandas as pd
import json
import sys
import os
import base64
import datetime
import pathlib

import ibis

from dotenv import load_dotenv
from querychat import QueryChat


# SETUP: Ensure sys.path includes src directory for local imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    from utils import get_team_matches, assign_period
except ImportError:
    # Fallback implementations if utils.py is not available
    def get_team_matches(df: pd.DataFrame, team: str) -> pd.DataFrame:
        home = df[df["HomeTeam"] == team].copy()
        away = df[df["AwayTeam"] == team].copy()
        home["venue"] = "Home"
        home["goals_for"] = home["FullTimeHomeGoals"]
        home["goals_against"] = home["FullTimeAwayGoals"]
        home["win"] = (home["FullTimeResult"] == "H").astype(int)
        away["venue"] = "Away"
        away["goals_for"] = away["FullTimeAwayGoals"]
        away["goals_against"] = away["FullTimeHomeGoals"]
        away["win"] = (away["FullTimeResult"] == "A").astype(int)
        return pd.concat([home, away]).sort_values("MatchDate").reset_index(drop=True)

    def assign_period(df: pd.DataFrame) -> pd.DataFrame:
        df = df.copy()
        n = len(df)
        if n == 0:
            df["period"] = pd.Series(dtype=str)
            return df
        third = n / 3
        df["period"] = [
            "Early" if i < third else ("Mid" if i < 2 * third else "Late")
            for i in range(n)
        ]
        return df


# ENVIRONMENT SETUP
load_dotenv()


# GOOGLE SHEETS LOGGING SETUP
try:
    import gspread
    from google.oauth2.service_account import Credentials
    _GSPREAD_AVAILABLE = True
except ImportError:
    _GSPREAD_AVAILABLE = False

_LOG_DIR = pathlib.Path("logs")
_LOG_DIR.mkdir(exist_ok=True)
_LOG_CSV = _LOG_DIR / "querychat_log.csv"

_GSPREAD_ENABLED = False
_GSPREAD_WS = None


def _init_gspread():
    """Initialize Google Sheets client for logging."""
    global _GSPREAD_ENABLED, _GSPREAD_WS
    if not _GSPREAD_AVAILABLE:
        return

    sheet_id = os.getenv("GSPREAD_SHEET_ID")
    sa_json = os.getenv("GOOGLE_SERVICE_ACCOUNT_JSON")
    sa_path = os.getenv("GSPREAD_CREDENTIALS_PATH")

    try:
        if sa_json:
            # Safer parsing: strip surrounding single/double quotes and normalize newlines
            try:
                creds_dict = json.loads(sa_json)
            except Exception as e:
                print(f"ERROR parsing GOOGLE_SERVICE_ACCOUNT_JSON: {e}")
                return
            creds = Credentials.from_service_account_info(
                creds_dict,
                scopes=["https://www.googleapis.com/auth/spreadsheets"]
            )
            gc = gspread.authorize(creds)
            if sheet_id:
                _GSPREAD_WS = gc.open_by_key(sheet_id).sheet1
                _GSPREAD_ENABLED = True
                print(f"✓ Google Sheets logging enabled. Sheet: {_GSPREAD_WS.title}")
            return

        if sa_path and os.path.exists(sa_path):
            if hasattr(gspread, "service_account"):
                gc = gspread.service_account(filename=sa_path)
            else:
                creds = Credentials.from_service_account_file(
                    sa_path,
                    scopes=["https://www.googleapis.com/auth/spreadsheets"]
                )
                gc = gspread.authorize(creds)
            if sheet_id:
                _GSPREAD_WS = gc.open_by_key(sheet_id).sheet1
                _GSPREAD_ENABLED = True
                print(f"✓ Google Sheets logging enabled. Sheet: {_GSPREAD_WS.title}")
            return

    except Exception as e:
        print(f"⚠ Google Sheets logging disabled: {e}")
        _GSPREAD_ENABLED = False
        _GSPREAD_WS = None


_init_gspread()

if not _GSPREAD_ENABLED:
    print("ℹ Logs will be written to logs/querychat_log.csv")


def log_interaction(query: str, response: str, timestamp: str):
    """Log AI interaction to Google Sheets or local CSV."""
    row = [timestamp, query or "", response or ""]

    if _GSPREAD_ENABLED and _GSPREAD_WS is not None:
        try:
            _GSPREAD_WS.append_row(row, value_input_option="USER_ENTERED")
            return
        except Exception as e:
            print(f"ERROR appending to Google Sheet: {e}")

    # Fallback: write to CSV
    try:
        import csv
        exists = _LOG_CSV.exists()
        with open(_LOG_CSV, "a", newline="", encoding="utf-8") as fh:
            writer = csv.writer(fh)
            if not exists:
                writer.writerow(["timestamp", "query", "response"])
            writer.writerow(row)
    except Exception as e:
        print(f"ERROR writing to CSV log: {e}")


def read_recent_logs(n: int = 50) -> pd.DataFrame:
    """Read recent logs from Google Sheets or CSV."""
    if _GSPREAD_ENABLED and _GSPREAD_WS is not None:
        try:
            records = _GSPREAD_WS.get_all_records()
            df = pd.DataFrame(records)
            if "timestamp" in df.columns:
                df = df.rename(columns={
                    "timestamp": "Timestamp",
                    "query": "Query",
                    "response": "Response"
                })
            return df.sort_values("Timestamp", ascending=False).head(n)
        except Exception:
            pass

    if _LOG_CSV.exists():
        try:
            df = pd.read_csv(_LOG_CSV)
            if "timestamp" in df.columns:
                df = df.rename(columns={
                    "timestamp": "Timestamp",
                    "query": "Query",
                    "response": "Response"
                })
            return df.sort_values("Timestamp", ascending=False).head(n)
        except Exception:
            return pd.DataFrame()

    return pd.DataFrame()


# DATA LOADING
con = ibis.duckdb.connect()
try:
    tbl_all = con.read_parquet("data/processed/epl_final.parquet")
    df_meta = tbl_all.execute()
except Exception as e:
    print(f"⚠ Could not load parquet: {e}")
    try:
        df_meta = pd.read_csv("data/raw/epl_final.csv")
        tbl_all = con.from_pandas(df_meta)
    except Exception as e2:
        print(f"ERROR: Could not load data: {e2}")
        df_meta = pd.DataFrame()
        tbl_all = con.from_pandas(df_meta)


# UI METADATA
ALL_TEAMS = sorted(set(df_meta["HomeTeam"].tolist() + df_meta["AwayTeam"].tolist())) if not df_meta.empty else []
ALL_SEASONS = sorted(df_meta["Season"].unique().tolist()) if not df_meta.empty else []

TEAM_SEASONS = {}
for team in ALL_TEAMS:
    seasons = sorted(df_meta[
        (df_meta["HomeTeam"] == team) | (df_meta["AwayTeam"] == team)
    ]["Season"].unique().tolist())
    TEAM_SEASONS[team] = seasons

# Default season = Arsenal's latest season if available
DEFAULT_SEASON = TEAM_SEASONS.get("Arsenal", ALL_SEASONS)[-1] if ALL_SEASONS else None

DEFAULT_DATE_START = df_meta["MatchDate"].min() if not df_meta.empty else None
DEFAULT_DATE_END = df_meta["MatchDate"].max() if not df_meta.empty else None


# AI INTEGRATION
qc = QueryChat(
    df_meta,
    "epl_matches",
    client="anthropic/claude-haiku-4-5"
)


# UI STYLING & ASSETS

LAST_UPDATED = datetime.date.today().isoformat()


def _load_header_datauri():
    """Load header image as base64 data URI for inline embedding."""
    candidates = [
        os.path.join("img", "stadium.jpg"),
        os.path.join("src", "www", "stadium.jpg"),
        os.path.join("www", "stadium.jpg"),
    ]
    for path in candidates:
        try:
            with open(path, "rb") as fh:
                b = fh.read()
            b64 = base64.b64encode(b).decode("ascii")
            return f"data:image/jpeg;base64,{b64}"
        except Exception:
            continue
    return None


INLINE_HEADER_DATAURI = _load_header_datauri()

page_style = ui.tags.style("""
html, body, .container-fluid {
    height: 100%;
    margin: 0;
    padding: 0;
    background: #f4f6f9;
}

.dashboard-wrap {
    display: flex;
    flex-direction: column;
    padding: 16px;
    gap: 14px;
    box-sizing: border-box;
    overflow-y: auto;
}

/* KPI row */
.kpi-row {
    display: flex;
    gap: 12px;
    flex-shrink: 0;
}
.kpi-card {
    flex: 1 1 0;
    background: #fff;
    border-radius: 10px;
    border: 1px solid rgba(0,0,0,0.06);
    box-shadow: 0 4px 20px rgba(16,24,40,0.06);
    padding: 16px;
}
.kpi-label { font-size: 10px; font-weight:700; text-transform:uppercase; color:#6b7280; margin-bottom:6px; }
.kpi-value { font-size: 22px; font-weight:700; color:#111827; }
.kpi-compare { font-size:12px; color:#6b7280; margin-top:6px; display:block; }

/* Body and sidebar */
.body-row { display:flex; gap:14px; align-items:stretch; }
.sidebar { width:260px; flex-shrink:0; background:#fff; border-radius:10px; border:1px solid #e0e4ea; box-shadow:0 1px 4px rgba(0,0,0,0.06); padding:16px; display:flex; flex-direction:column; gap:12px; align-self:stretch; }
.sidebar.ai-sidebar { width:400px; }
.sidebar-title{ font-size:14px; font-weight:700; color:#111827; }
.sidebar label{ font-size:12px; font-weight:600; color:#374151; }
.sidebar .form-select{ font-size:12px; border-radius:6px; border:1px solid #d1d5db; }
.btn-reset{ padding:6px 10px; font-size:12px; border-radius:6px; background:#f3f4f6; color:#111827; }

/* AI chat fixed container */
.ai-sidebar {
    height: 720px;
    overflow: hidden;
}

.ai-chat-shell {
    flex: 1 1 auto;
    min-height: 0;
    display: flex;
    flex-direction: column;
    overflow: hidden;
}

.ai-chat-shell > * {
    flex: 1 1 auto;
    min-height: 0;
}

.ai-chat-shell .messages,
.ai-chat-shell .chat-messages,
.ai-chat-shell .message-list,
.ai-chat-shell [class*="messages"],
.ai-chat-shell [class*="message-list"] {
    overflow-y: auto !important;
    min-height: 0 !important;
    max-height: 100% !important;
}

/* Header banner image */
.header-banner-img{
    width:100%;
    height:160px;
    object-fit:cover;
    border-radius:12px;
    display:block;
}

/* Reduce font sizes for AI chat and filtered-match tables */
.ai-chat-shell, .ai-chat-shell * {
    font-size:13px;
    line-height:1.25;
}
.table-card, .chart-card {
    font-size:13px;
}

/* Charts */
.charts-panel{ flex:1 1 0; display:flex; flex-direction:column; gap:12px; min-width:0; }
.kpi-row { margin-bottom:12px; }
.chart-row-top{ display:flex; gap:12px; }
.chart-card{ flex:1 1 0; background:#fff; border-radius:10px; border:1px solid #e0e4ea; box-shadow:0 1px 4px rgba(0,0,0,0.06); padding:12px 14px 8px; display:flex; flex-direction:column; min-width:0; overflow:hidden; }
.chart-row-bottom{ display:flex; gap:12px; }
.chart-row-bottom > * { flex: 0 0 50%; min-width:0; height:320px; }
.chart-title{ font-size:12px; font-weight:700; color:#374151; margin-bottom:4px; }
.chart-subtitle{ font-size:10px; color:#9ca3af; margin-bottom:8px; }

.table-card{ background:#fff; border-radius:10px; border:1px solid #e0e4ea; box-shadow:0 1px 4px rgba(0,0,0,0.06); padding:10px 14px; height:320px; overflow-y:auto; display:flex; flex-direction:column; }

.active-filters { display:flex; gap:8px; flex-wrap:wrap; margin-bottom:8px; }
.active-filters .chip { background: #eef2ff; color:#3730a3; padding:6px 10px; border-radius:999px; font-size:12px; font-weight:600; }

.app-footer{ margin-top:8px; padding:10px 16px; text-align:left; color:#6b7280; font-size:13px; display:flex; gap:18px; align-items:center; justify-content:space-between; flex-wrap:wrap; }
.app-footer p{ margin:0; }
""")


# COLOR SCHEME
C_HOME = "#472A4B"
C_AWAY = "#e15759"
C_GOALS_FOR = "#472A4B"
C_GOALS_AGAINST = "#e15759"
C_EARLY = "#472A4B"
C_MID = "#e15759"
C_LATE = "#4e79a7"


# HELPER FUNCTIONS
def hero_header():
    """Render the hero header with stadium image and title."""
    img_src = INLINE_HEADER_DATAURI if INLINE_HEADER_DATAURI else "/www/stadium.jpg"
    return ui.div(
        ui.img(src=img_src, class_="header-banner-img", alt="Stadium"),
        ui.div(
            ui.img(
                src="https://upload.wikimedia.org/wikipedia/en/f/f2/Premier_League_Logo.svg",
                style="height:65px; margin-right:20px;",
            ),
            ui.h2(
                "EPL Performance Dashboard",
                style="margin:0; font-weight:800; color:white; font-size:42px; line-height:1;"
            ),
            style="""
                position:absolute;
                left:30px;
                top:50%;
                transform:translateY(-50%);
                display:flex;
                align-items:center;
                gap:20px;
                z-index:2;
            """,
        ),
        style="position:relative; margin-bottom:20px;",
    )


def filter_matches_ibis(team: str, season: str, result: str):
    """Build an ibis filter expression for team, season, and result."""
    expr = tbl_all

    # Filter by team (home OR away)
    if team:
        expr = expr.filter((expr.HomeTeam == team) | (expr.AwayTeam == team))

    # Filter by season
    if season:
        expr = expr.filter(expr.Season == season)

    # Filter by result
    if result and result != "All":
        if result == "Win":
            expr = expr.filter(
                ((expr.HomeTeam == team) & (expr.FullTimeResult == "H")) |
                ((expr.AwayTeam == team) & (expr.FullTimeResult == "A"))
            )
        elif result == "Draw":
            expr = expr.filter(expr.FullTimeResult == "D")
        elif result == "Loss":
            expr = expr.filter(
                ((expr.HomeTeam == team) & (expr.FullTimeResult == "A")) |
                ((expr.AwayTeam == team) & (expr.FullTimeResult == "H"))
            )

    return expr



# UI DEFINITION

app_ui = ui.page_fluid(
    page_style,
    hero_header(),
    ui.navset_tab(
        # ───────── DASHBOARD TAB ─────────
        ui.nav_panel(
            "Dashboard",
            ui.div(
                ui.div(
                    ui.div(
                        ui.output_ui("data_context_description"),
                        class_="charts-panel-section",
                    ),
                ),
                ui.div(
                    # Sidebar
                    ui.div(
                        ui.div("⚽ Filters", class_="sidebar-title"),
                        ui.input_select("input_team", "Team", choices=ALL_TEAMS, selected="Arsenal"),
                        ui.input_select("input_season", "Season", choices=ALL_SEASONS, selected=DEFAULT_SEASON),
                        ui.input_select("input_result", "Match result", choices=["All", "Win", "Draw", "Loss"], selected="All"),
                        ui.output_ui("out_active_filters"),
                        ui.input_action_button("btn_reset", "Reset filters", class_="btn-reset"),
                        class_="sidebar",
                    ),

                    # Main content
                    ui.div(
                        # KPI cards
                        ui.div(
                            ui.div(
                                ui.div("Total Matches", class_="kpi-label"),
                                ui.div(ui.output_ui("out_kpi_total"), class_="kpi-value"),
                                class_="kpi-card",
                            ),
                            ui.div(
                                ui.div("Win Rate", class_="kpi-label"),
                                ui.div(ui.output_ui("out_kpi_winrate"), class_="kpi-value"),
                                class_="kpi-card",
                            ),
                            ui.div(
                                ui.div("Average Goals Scored", class_="kpi-label"),
                                ui.div(ui.output_ui("out_kpi_goals_scored"), class_="kpi-value"),
                                class_="kpi-card",
                            ),
                            ui.div(
                                ui.div("Average Goals Conceded", class_="kpi-label"),
                                ui.div(ui.output_ui("out_kpi_goals_conceded"), class_="kpi-value"),
                                class_="kpi-card",
                            ),
                            class_="kpi-row",
                        ),

                        # Top charts
                        ui.div(
                            ui.div(
                                ui.div("Goals Scored vs Goals Conceded", class_="chart-title"),
                                ui.div("Home vs Away · Story 1", class_="chart-subtitle"),
                                ui.output_plot("out_goals_home_away", height="280px"),
                                class_="chart-card",
                            ),
                            ui.div(
                                ui.div("Win Rate", class_="chart-title"),
                                ui.div("Home vs Away · Story 2", class_="chart-subtitle"),
                                ui.output_plot("out_winrate_home_away", height="280px"),
                                class_="chart-card",
                            ),
                            class_="chart-row-top",
                        ),

                        # Bottom charts
                        ui.div(
                            ui.div(
                                ui.div("Average Goals Scored by Season Period", class_="chart-title"),
                                ui.div("Early / Mid / Late · Story 3", class_="chart-subtitle"),
                                ui.output_plot("out_goals_by_period", height="320px"),
                                class_="chart-card",
                            ),
                            ui.div(
                                ui.div("Match Details", class_="chart-title"),
                                ui.div("Filtered match list", class_="chart-subtitle"),
                                ui.output_data_frame("out_matches_table"),
                                class_="table-card",
                            ),
                            
                            class_="chart-row-bottom",
                        ),

                        class_="charts-panel",
                    ),

                    class_="body-row",
                ),

                class_="dashboard-wrap",
            ),
        ),

        # ───────── AI EXPLORER TAB ─────────
        ui.nav_panel(
            "AI Explorer",
            ui.div(
                # AI Sidebar
                ui.div(
                    ui.div("🤖 AI Filter", class_="sidebar-title"),
                    ui.p(
                        "Try asking: show only Arsenal matches, only draws, Liverpool away wins, or matches where the home team scored at least 4 goals.",
                        style="font-size:12px; color:#6b7280;"
                    ),
                    ui.div(
                        qc.ui(),
                        class_="ai-chat-shell",
                    ),
                    
                    ui.hr(),
                    ui.input_action_button("ai_reset", "Reset AI filters", class_="btn-reset"),
                    ui.download_button("download_ai_data", "Download filtered data"),
                    class_="sidebar ai-sidebar",
                ),

                # AI Results
                ui.div(
                    ui.div(
                        ui.output_ui("ai_title"),
                        style="font-size:18px; font-weight:700; margin-bottom:12px;"
                    ),

                    ui.div(
                        ui.div(
                            ui.div("Filtered Matches", class_="chart-title"),
                            ui.div("Data returned by the AI filter", class_="chart-subtitle"),
                            ui.output_data_frame("ai_table"),
                            class_="chart-card",
                        ),
                        ui.div(
                            ui.div("Match Results", class_="chart-title"),
                            ui.div("Counts by result label", class_="chart-subtitle"),
                            ui.output_plot("ai_plot_result", height="280px"),
                            class_="chart-card",
                        ),
                        class_="chart-row-top",
                    ),

                    

                    ui.div(
                        ui.div("Recent AI Queries", class_="chart-title"),
                        ui.div("Latest AI queries and responses", class_="chart-subtitle"),
                        ui.output_data_frame("out_logs"),
                        class_="table-card",
                    ),

                    class_="charts-panel",
                ),

                class_="body-row",
            ),
        ),
    ),

    # Footer
    ui.div(
        ui.div(
            ui.p("EPL Performance Dashboard : Interactive exploration of team results."),
            ui.p([
                "Authors: Omowunmi, Wenrui, Gurleen, Ashifa. ",
                ui.a(
                    "Repo",
                    href="https://github.com/UBC-MDS/DSCI-532_2026_6_EPL_match_tracker",
                    target="_blank",
                ),
            ]),
            ui.p(f"Last updated: {LAST_UPDATED}"),
            class_="app-footer",
        ),
    ),

    # Reset filters JS
    ui.tags.script("""
document.addEventListener('DOMContentLoaded', function(){
    const btn = document.getElementById('btn_reset');
    if (!btn) return;

    btn.addEventListener('click', function() {
        btn.disabled = true;
        setTimeout(function(){ btn.disabled = false; }, 300);
    });
});
"""),
)


# SERVER LOGIC

# Track last logged interaction to avoid duplicate logging
_last_logged_interaction = None


def server(input, output, session):
    """Main server logic."""
    global _last_logged_interaction

    # Initialize QueryChat server
    qc_vals = qc.server()

    # REACTIVE EFFECTS (Side effects like logging)
    @reactive.effect
    @reactive.event(input.input_team)
    def _update_seasons_for_team():
        """Update available seasons when team changes."""
        team = input.input_team()
        available = TEAM_SEASONS.get(team, ALL_SEASONS)
        current_season = input.input_season()
        selected = current_season if current_season in available else available[-1]
        ui.update_select("input_season", choices=available, selected=selected)
        
    @reactive.effect
    @reactive.event(input.btn_reset)
    def _reset_filters():
        """Reset all filters to defaults when reset button is clicked."""
        ui.update_select("input_team", selected="Arsenal")
        ui.update_select("input_season", selected=DEFAULT_SEASON)
        ui.update_select("input_result", selected="All")
        
    @reactive.effect
    def _log_ai_interactions():
        """Log AI query interactions to Google Sheets or CSV (NO UI RENDERING)."""
        global _last_logged_interaction
        try:
            df = qc_vals.df()
            if df is None or df.empty:
                return

            title = ""
            try:
                title = qc_vals.title() or ""
            except Exception:
                pass

            if not title.strip():
                return

            n = len(df)
            cols = ",".join(list(df.columns)[:6]) if not df.empty else ""
            response_summary = f"returned {n} rows; cols: {cols}"
            ts = datetime.datetime.utcnow().isoformat()

            pair = (title, response_summary)
            if pair != _last_logged_interaction:
                try:
                    log_interaction(title, response_summary, ts)
                    _last_logged_interaction = pair
                except Exception as e:
                    print(f"ERROR logging AI interaction: {e}")
        except Exception:
            pass

    @reactive.effect
    @reactive.event(input.ai_reset)
    def _reset_ai():
        """Reset AI filters."""
        qc_vals.sql.set("")
        qc_vals.title.set(None)

    # REACTIVE CALCULATIONS
    @reactive.calc
    def matches_filtered():
        """Filter matches based on inputs using Ibis lazy evaluation."""
        team = input.input_team()
        season = input.input_season()
        result = input.input_result()

        expr = filter_matches_ibis(team, season, result)
        mf = expr.execute()

        if not mf.empty:
            mf = get_team_matches(mf, team)

        return mf

    @reactive.calc
    def summary_home_away():
        """Calculate Home vs Away statistics."""
        mf = matches_filtered()
        out = {}
        for venue in ("Home", "Away"):
            sub = mf[mf["venue"] == venue] if not mf.empty else pd.DataFrame()
            if sub.empty:
                out[venue] = dict(win_rate=0, avg_goals_for=0, avg_goals_against=0, n=0)
            else:
                out[venue] = dict(
                    win_rate=sub["win"].mean() * 100,
                    avg_goals_for=sub["goals_for"].mean(),
                    avg_goals_against=sub["goals_against"].mean(),
                    n=len(sub),
                )
        return out

    @reactive.calc
    def summary_period():
        """Calculate statistics by season period."""
        mf = assign_period(matches_filtered())
        out = {}
        for period in ("Early", "Mid", "Late"):
            sub = mf[mf["period"] == period] if not mf.empty else pd.DataFrame()
            if sub.empty:
                out[period] = dict(avg_goals=0, n=0)
            else:
                out[period] = dict(
                    avg_goals=sub["goals_for"].mean(),
                    n=len(sub),
                )
        return out

    # HELPER FUNCTIONS (used within server)
    def _metrics_for_season(season: str):
        """Get metrics for a specific season."""
        expr = tbl_all.filter(tbl_all.Season == season)
        df = expr.execute()
        team = input.input_team()
        mf = get_team_matches(df, team)
        if mf.empty:
            return dict(n=0, win_rate=0.0, avg_goals_for=0.0, avg_goals_against=0.0)
        return dict(
            n=len(mf),
            win_rate=mf["win"].mean() * 100,
            avg_goals_for=mf["goals_for"].mean(),
            avg_goals_against=mf["goals_against"].mean(),
        )

    def _pct_change(curr, prev, abs_unit: str = ""):
        """Calculate percentage change with formatting."""
        if prev == 0 or prev is None:
            return None
        try:
            change = (curr - prev) / prev * 100
        except Exception:
            return None
        arrow = "▲" if change > 0 else ("▼" if change < 0 else "—")
        sign = f"{abs(change):.1f}%"
        abs_diff = curr - prev
        if abs_unit.strip().startswith("matches") or abs_unit.strip().lower().startswith("match"):
            abs_fmt = f"{int(abs_diff):+d} {abs_unit.strip()}"
        else:
            abs_fmt = f"{abs_diff:+.1f} {abs_unit.strip()}" if abs_unit else f"{abs_diff:+.1f}"
        col = "#16a34a" if change > 0 else ("#ef4444" if change < 0 else "#6b7280")
        return ui.span(
            ui.span(f"{arrow} {sign}", style=f"color: {col}; font-weight:700; margin-right:6px;"),
            ui.span(f"({abs_fmt})", style="color:#6b7280; margin-right:4px;"),
            ui.span("vs previous season", style="color:#6b7280;"),
            class_="kpi-compare",
            style="margin-left:6px;",
        )

    def _style_ax(ax):
        """Apply consistent styling to matplotlib axes."""
        ax.spines[["top", "right"]].set_visible(False)
        ax.yaxis.grid(True, linestyle="--", linewidth=0.6, alpha=0.45, zorder=0)
        ax.set_axisbelow(True)
        ax.tick_params(axis="both", labelsize=8)

    def _bar_labels(ax, bars):
        """Add labels above bars in matplotlib charts."""
        ylim = ax.get_ylim()
        for bar in bars:
            h = bar.get_height()
            ax.text(
                bar.get_x() + bar.get_width() / 2,
                h + (ylim[1] - ylim[0]) * 0.02,
                f"{h:.1f}",
                ha="center", va="bottom", fontsize=8, fontweight="600",
            )

    # OUTPUTS (UI Rendering - NO SIDE EFFECTS)
    @output
    @render.ui
    def data_context_description():
        """Render the data context description."""
        try:
            team = input.input_team()
        except Exception:
            team = "—"
        try:
            season = input.input_season()
        except Exception:
            season = "—"
        try:
            result = input.input_result()
        except Exception:
            result = None
        try:
            mf = matches_filtered()
            data_empty = mf.empty
        except Exception:
            data_empty = True

        if data_empty:
            text = f"Current: no data for {team} in the {season} season."
            if result and result != "All":
                text += f" (no {result.lower()} matches)"
        else:
            text = f"Currently viewing: {team} results for the {season} season"
            if result and result != "All":
                text += f" — filtered to {result.lower()} matches"
            text += "."

        desc_style = (
            "background:#fff; "
            "border-radius:10px; border:1px solid rgba(0,0,0,0.06); "
            "box-shadow: 0 4px 20px rgba(16,24,40,0.06); "
            "padding: 16px 20px; margin-bottom:12px; "
            "font-size:16px; font-weight:600; color:#232323;"
        )

        return ui.div(text, style=desc_style)

    @output
    @render.ui
    def out_kpi_total():
        """Render total matches KPI."""
        season = input.input_season()
        curr = _metrics_for_season(season)["n"]
        prev = None
        try:
            idx = ALL_SEASONS.index(season)
            if idx > 0:
                prev = ALL_SEASONS[idx - 1]
        except Exception:
            pass
        prev_n = _metrics_for_season(prev)["n"] if prev else 0
        comp = _pct_change(curr, prev_n)
        comp_ui = comp if comp is not None else ui.span("— vs previous season", class_="kpi-compare")
        return ui.div(
            ui.div(f"{curr}", style="font-size:22px; font-weight:700;"),
            comp_ui,
        )

    @output
    @render.ui
    def out_kpi_winrate():
        """Render win rate KPI."""
        season = input.input_season()
        curr = _metrics_for_season(season)["win_rate"]
        prev = None
        try:
            idx = ALL_SEASONS.index(season)
            if idx > 0:
                prev = ALL_SEASONS[idx - 1]
        except Exception:
            pass
        prev_val = _metrics_for_season(prev)["win_rate"] if prev else 0.0
        comp = _pct_change(curr, prev_val)
        comp_ui = comp if comp is not None else ui.span("— vs previous season", class_="kpi-compare")
        return ui.div(
            ui.div(f"{curr:.1f}%", style="font-size:22px; font-weight:700;"),
            comp_ui,
        )

    @output
    @render.ui
    def out_kpi_goals_scored():
        """Render average goals scored KPI."""
        season = input.input_season()
        curr = _metrics_for_season(season)["avg_goals_for"]
        prev = None
        try:
            idx = ALL_SEASONS.index(season)
            if idx > 0:
                prev = ALL_SEASONS[idx - 1]
        except Exception:
            pass
        prev_val = _metrics_for_season(prev)["avg_goals_for"] if prev else 0.0
        comp = _pct_change(curr, prev_val)
        comp_ui = comp if comp is not None else ui.span("— vs previous season", class_="kpi-compare")
        return ui.div(
            ui.div(f"{curr:.2f}", style="font-size:22px; font-weight:700;"),
            comp_ui,
        )

    @output
    @render.ui
    def out_kpi_goals_conceded():
        """Render average goals conceded KPI."""
        season = input.input_season()
        curr = _metrics_for_season(season)["avg_goals_against"]
        prev = None
        try:
            idx = ALL_SEASONS.index(season)
            if idx > 0:
                prev = ALL_SEASONS[idx - 1]
        except Exception:
            pass
        prev_val = _metrics_for_season(prev)["avg_goals_against"] if prev else 0.0
        comp = _pct_change(curr, prev_val)
        comp_ui = comp if comp is not None else ui.span("— vs previous season", class_="kpi-compare")
        return ui.div(
            ui.div(f"{curr:.2f}", style="font-size:22px; font-weight:700;"),
            comp_ui,
        )

    @output
    @render.ui
    def out_active_filters():
        """Render active filter chips (PURE RENDERING ONLY)."""
        parts = []
        try:
            team = input.input_team()
            if team:
                parts.append(ui.span(f"Team: {team}", class_="chip"))
        except Exception:
            pass
        try:
            season = input.input_season()
            if season:
                parts.append(ui.span(f"Season: {season}", class_="chip"))
        except Exception:
            pass
        try:
            result = input.input_result()
            if result and result != "All":
                parts.append(ui.span(f"Result: {result}", class_="chip"))
        except Exception:
            pass

        if not parts:
            return ui.div(ui.span("No active filters", style="color:#9ca3af; font-size:12px;"))
        return ui.div(*parts, class_="active-filters")

    @output
    @render.plot
    def out_goals_home_away():
        """Render Home vs Away goals chart."""
        s = summary_home_away()
        venues = ["Home", "Away"]
        x = range(len(venues))
        w = 0.35

        fig, ax = plt.subplots(figsize=(5, 3.5))
        fig.patch.set_facecolor("#fff")
        ax.set_facecolor("#fff")

        bars_for = ax.bar(
            [i - w/2 for i in x],
            [s[v]["avg_goals_for"] for v in venues],
            width=w, color=C_GOALS_FOR, zorder=3, label="Goals Scored",
        )
        bars_against = ax.bar(
            [i + w/2 for i in x],
            [s[v]["avg_goals_against"] for v in venues],
            width=w, color=C_GOALS_AGAINST, zorder=3, label="Goals Conceded",
        )

        ax.set_xticks(list(x))
        ax.set_xticklabels([v for v in venues], fontsize=9)
        ax.set_ylabel("Avg Goals", fontsize=9)
        ax.set_ylim(0, max(
            [s[v]["avg_goals_for"] for v in venues] +
            [s[v]["avg_goals_against"] for v in venues] + [1]
        ) * 1.35)
        _style_ax(ax)
        _bar_labels(ax, list(bars_for) + list(bars_against))
        ax.legend(fontsize=8, frameon=False, loc="upper right")
        fig.tight_layout(pad=0.8)
        return fig

    @output
    @render.plot
    def out_winrate_home_away():
        """Render Home vs Away win rate chart."""
        s = summary_home_away()
        venues = ["Home", "Away"]
        vals = [s[v]["win_rate"] for v in venues]

        fig, axes = plt.subplots(1, 2, figsize=(8, 3.5))
        fig.patch.set_facecolor("#fff")
        bg_color = "#e0e4ea"

        for ax, val, color, label in zip(axes, vals, [C_HOME, C_AWAY], venues):
            ax.set_aspect("equal")
            ax.axis("off")

            bg = Wedge((0, 0), 1.0, 0, 180, width=0.22, facecolor=bg_color, edgecolor="none", lw=0)
            ax.add_patch(bg)

            frac = max(0.0, min(float(val) / 100.0 if val is not None else 0.0, 1.0))
            if frac > 0:
                start_ang = 180 - 180 * frac
                fg = Wedge((0, 0), 1.0, start_ang, 180, width=0.22, facecolor=color, edgecolor="none", lw=0)
                ax.add_patch(fg)

            ax.text(0, -0.08, f"{(val or 0):.1f}%", ha="center", va="center", fontsize=14, fontweight="700", color=color)
            ax.text(0, -0.32, label, ha="center", va="center", fontsize=10, color="#6b7280")

            ax.set_xlim(-1.15, 1.15)
            ax.set_ylim(-0.6, 1.05)

        fig.tight_layout(pad=0.6)
        return fig

    @output
    @render.plot
    def out_goals_by_period():
        """Render goals by season period chart."""
        mf = assign_period(matches_filtered())

        periods = ["Early", "Mid", "Late"]
        x = list(range(len(periods)))

        avg_goals = []
        home_avg = []
        away_avg = []
        ns = []

        for p in periods:
            sub = mf[mf["period"] == p]
            ns.append(len(sub))

            if sub.empty:
                avg_goals.append(0)
                home_avg.append(0)
                away_avg.append(0)
            else:
                avg_goals.append(sub["goals_for"].mean())
                home_avg.append(sub[sub["venue"] == "Home"]["goals_for"].mean())
                away_avg.append(sub[sub["venue"] == "Away"]["goals_for"].mean())

        x_labels = [p for i, p in enumerate(periods)]

        fig, ax = plt.subplots(figsize=(9, 3))
        fig.patch.set_facecolor("#fff")
        ax.set_facecolor("#fff")

        ax.plot(x, avg_goals, color="#d1d5db", linewidth=2.2, marker="o", label="Overall Avg Goals", zorder=2)
        ax.plot(x, home_avg, color=C_HOME, linewidth=2.2, marker="o", label="Home Avg Goals", zorder=3)
        ax.plot(x, away_avg, color=C_AWAY, linewidth=2.2, marker="o", label="Away Avg Goals", zorder=3)

        ax.set_xticks(x)
        ax.set_xticklabels(x_labels, fontsize=9)
        ax.set_ylabel("Avg Goals Scored", fontsize=9)

        ymax = max(avg_goals + home_avg + away_avg + [1])
        ax.set_ylim(0, ymax * 1.4)

        _style_ax(ax)
        ax.legend(fontsize=8, frameon=False)

        fig.tight_layout(pad=0.8)

        return fig

    @output
    @render.data_frame
    def out_matches_table():
        """Render matches table."""
        mf = assign_period(matches_filtered()).copy()

        if mf.empty:
            return render.DataGrid(pd.DataFrame(), width="100%")

        mf["MatchDate"] = mf["MatchDate"].dt.strftime("%Y-%m-%d")
        display = mf[[
            "MatchDate", "HomeTeam", "AwayTeam",
            "FullTimeHomeGoals", "FullTimeAwayGoals", "FullTimeResult",
            "venue", "goals_for", "goals_against", "win", "period",
        ]].rename(columns={
            "MatchDate":         "Date",
            "HomeTeam":          "Home",
            "AwayTeam":          "Away",
            "FullTimeHomeGoals": "HG",
            "FullTimeAwayGoals": "AG",
            "FullTimeResult":    "Result Code",
            "venue":             "Venue",
            "goals_for":         "Goals For",
            "goals_against":     "Goals Against",
            "win":               "Win",
            "period":            "Period",
        })
        return render.DataGrid(display, width="100%")

    # AI EXPLORER OUTPUTS
    @output
    @render.ui
    def ai_title():
        """Render AI title with error handling."""
        df = qc_vals.df()
        title = qc_vals.title() or "All EPL matches"
        if df.empty and qc_vals.title():
            return ui.div(
                ui.div(title, style="font-size:18px; font-weight:700; margin-bottom:6px;"),
                ui.div(
                    "⚠️ No matches found for this query. The charts below are empty. Try refining your question.",
                    style="background:#fff3cd; border:1px solid #ffc107; border-radius:8px; padding:10px 14px; font-size:13px; color:#856404;"
                )
            )
        return ui.div(title, style="font-size:18px; font-weight:700;")

    @output
    @render.data_frame
    def ai_table():
        """Render AI filtered matches table."""
        return render.DataGrid(qc_vals.df(), width="100%")

    @output
    @render.plot
    def ai_plot_result():
        """Render AI result distribution chart."""
        df = qc_vals.df().copy()

        fig, ax = plt.subplots(figsize=(5, 3.5))
        fig.patch.set_facecolor("#fff")
        ax.set_facecolor("#fff")

        if df.empty:
            ax.text(0.5, 0.5, "No matches found for the current AI filter.\nTry a different query.", ha="center", va="center", fontsize=10, color="#6b7280")
            ax.axis("off")
            return fig

        counts = df["Result"].value_counts()

        bars = ax.bar(counts.index, counts.values, zorder=3)
        ax.set_ylabel("Count", fontsize=9)
        ax.set_xlabel("")
        ax.spines[["top", "right"]].set_visible(False)
        ax.yaxis.grid(True, linestyle="--", linewidth=0.6, alpha=0.45, zorder=0)
        ax.set_axisbelow(True)
        ax.tick_params(axis="x", labelrotation=10, labelsize=8)
        ax.tick_params(axis="y", labelsize=8)

        for bar in bars:
            h = bar.get_height()
            ax.text(
                bar.get_x() + bar.get_width() / 2,
                h + 0.02 * max(counts.values.max(), 1),
                f"{int(h)}",
                ha="center",
                va="bottom",
                fontsize=8,
                fontweight="600",
            )

        fig.tight_layout(pad=0.8)
        return fig

    @output
    @render.plot
    def ai_plot_goals():
        """Render AI average goals chart."""
        df = qc_vals.df().copy()

        fig, ax = plt.subplots(figsize=(5, 3.5))
        fig.patch.set_facecolor("#fff")
        ax.set_facecolor("#fff")

        if df.empty:
            ax.text(0.5, 0.5, "No matches found for the current AI filter.\nTry a different query.", ha="center", va="center", fontsize=10, color="#6b7280")
            ax.axis("off")
            return fig

        labels = ["Home Goals", "Away Goals"]
        vals = [
            df["FullTimeHomeGoals"].mean(),
            df["FullTimeAwayGoals"].mean()
        ]

        bars = ax.bar(labels, vals, zorder=3)
        ax.set_ylabel("Average Goals", fontsize=9)
        ax.set_xlabel("")
        ax.spines[["top", "right"]].set_visible(False)
        ax.yaxis.grid(True, linestyle="--", linewidth=0.6, alpha=0.45, zorder=0)
        ax.set_axisbelow(True)
        ax.tick_params(axis="both", labelsize=8)

        ylim_top = max(vals + [1]) * 1.35
        ax.set_ylim(0, ylim_top)

        for bar in bars:
            h = bar.get_height()
            ax.text(
                bar.get_x() + bar.get_width() / 2,
                h + ylim_top * 0.02,
                f"{h:.2f}",
                ha="center",
                va="bottom",
                fontsize=8,
                fontweight="600",
            )

        fig.tight_layout(pad=0.8)
        return fig

    @output
    @render.plot
    def ai_plot_season():
        """Render AI matches by season chart."""
        df = qc_vals.df().copy()

        fig, ax = plt.subplots(figsize=(5, 3.5))
        fig.patch.set_facecolor("#fff")
        ax.set_facecolor("#fff")

        if df.empty:
            ax.text(0.5, 0.5, "No matches found for the current AI filter.\nTry a different query.", ha="center", va="center", fontsize=10, color="#6b7280")
            ax.axis("off")
            return fig

        counts = df["Season"].value_counts().sort_index()

        bars = ax.bar(counts.index.astype(str), counts.values, zorder=3)
        ax.set_ylabel("Matches", fontsize=9)
        ax.set_xlabel("Season", fontsize=9)
        ax.spines[["top", "right"]].set_visible(False)
        ax.yaxis.grid(True, linestyle="--", linewidth=0.6, alpha=0.45, zorder=0)
        ax.set_axisbelow(True)
        ax.tick_params(axis="x", labelrotation=45, labelsize=8)
        ax.tick_params(axis="y", labelsize=8)

        fig.tight_layout(pad=0.8)
        return fig

    @render.download(filename="querychat_filtered_epl.csv")
    def download_ai_data():
        """Download AI filtered data as CSV."""
        yield qc_vals.df().to_csv(index=False)



# APP INITIALIZATION
app = App(app_ui, server)