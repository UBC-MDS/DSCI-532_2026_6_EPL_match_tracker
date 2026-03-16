from shiny import App, ui, render, reactive
import matplotlib.pyplot as plt
import pandas as pd
import json
import sys
import os
import base64
import datetime
import ibis

from dotenv import load_dotenv
from querychat import QueryChat
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from utils import get_team_matches, assign_period

load_dotenv()

# ── Load dataset with DuckDB (Lazy Loading) ────────────────────────────────────
con = ibis.duckdb.connect()
tbl_all = con.read_parquet("data/processed/epl_final.parquet")

# Execute once to get metadata for UI choice lists
df_meta = tbl_all.execute()

ALL_TEAMS = sorted(set(df_meta["HomeTeam"].tolist() + df_meta["AwayTeam"].tolist()))
ALL_SEASONS = sorted(df_meta["Season"].unique().tolist())
# DEFAULT_SEASON = ALL_SEASONS[-1] if ALL_SEASONS else "2024"
# Build a mapping: team -> sorted list of seasons where that team has data
TEAM_SEASONS = {}
for team in ALL_TEAMS:
    seasons = sorted(df_meta[
        (df_meta["HomeTeam"] == team) | (df_meta["AwayTeam"] == team)
    ]["Season"].unique().tolist())
    TEAM_SEASONS[team] = seasons

# Default season = Arsenal's latest season
DEFAULT_SEASON = TEAM_SEASONS["Arsenal"][-1] if TEAM_SEASONS.get("Arsenal") else ALL_SEASONS[-1]

DEFAULT_DATE_START = df_meta["MatchDate"].min() if not df_meta.empty else None
DEFAULT_DATE_END = df_meta["MatchDate"].max() if not df_meta.empty else None

# Anthropic QueryChat (pass the full metadata df for now)
qc = QueryChat(
    df_meta,
    "epl_matches",
    client="anthropic/claude-haiku-4-5"
)

# Load a local JPEG as a data-URI so the header doesn't rely on static file serving.
def _load_header_datauri():
    candidates = [
        os.path.join("img", "stadium.jpg"),
        os.path.join("src", "www", "stadium.jpg"),
        os.path.join("www", "stadium.jpg"),
    ]
    for p in candidates:
        try:
            with open(p, "rb") as fh:
                b = fh.read()
            b64 = base64.b64encode(b).decode("ascii")
            return f"data:image/jpeg;base64,{b64}"
        except Exception:
            continue
    return None

INLINE_HEADER_DATAURI = _load_header_datauri()

LAST_UPDATED = datetime.date.today().isoformat()

# ── Helpers ────────────────────────────────────────────────────────────────────
def filter_matches_ibis(team: str, season: str, result: str):
    """
    Build an ibis filter expression for team, season, and result.
    Returns an ibis table expression (not yet executed).
    """
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
            # Home win OR Away win
            expr = expr.filter(
                ((expr.HomeTeam == team) & (expr.FullTimeResult == "H")) |
                ((expr.AwayTeam == team) & (expr.FullTimeResult == "A"))
            )
        elif result == "Draw":
            expr = expr.filter(expr.FullTimeResult == "D")
        elif result == "Loss":
            # Loss = (home team AND away result) OR (away team AND home result)
            expr = expr.filter(
                ((expr.HomeTeam == team) & (expr.FullTimeResult == "A")) |
                ((expr.AwayTeam == team) & (expr.FullTimeResult == "H"))
            )
    
    return expr


# ── Colours ────────────────────────────────────────────────────────────────────
C_HOME          = "#472A4B"
C_AWAY          = "#e15759"
C_GOALS_FOR     = "#472A4B"
C_GOALS_AGAINST = "#e15759"
C_EARLY         = "#472A4B"
C_MID           = "#e15759"
C_LATE          = "#4e79a7"

# ── CSS ────────────────────────────────────────────────────────────────────────
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
.sidebar-title{ font-size:14px; font-weight:700; color:#111827; }
.sidebar label{ font-size:12px; font-weight:600; color:#374151; }
.sidebar .form-select{ font-size:12px; border-radius:6px; border:1px solid #d1d5db; }
.btn-reset{ padding:6px 10px; font-size:12px; border-radius:6px; background:#f3f4f6; color:#111827; }

/* Header banner image */
.header-banner-img{
    width:100%;
    height:160px;
    object-fit:cover;
    border-radius:12px;
    display:block;
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

# ── Hero Header ────────────────────────────────────────────────────────────────
def hero_header():
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

# ── UI ─────────────────────────────────────────────────────────────────────────
app_ui = ui.page_fluid(
    page_style,
    hero_header(),
    ui.navset_tab(
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
                    ui.div(
                        ui.div("⚽ Filters", class_="sidebar-title"),
                        ui.input_select("input_team", "Team", choices=ALL_TEAMS, selected="Arsenal"),
                        ui.input_select("input_season", "Season", choices=ALL_SEASONS, selected=DEFAULT_SEASON),
                        ui.input_select("input_result", "Match result", choices=["All", "Win", "Draw", "Loss"], selected="All"),
                        ui.output_ui("out_active_filters"),
                        ui.input_action_button("btn_reset", "Reset filters", class_="btn-reset"),
                        class_="sidebar",
                    ),

                    ui.div(
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

        ui.nav_panel(
            "AI Explorer",
            ui.div(
                ui.div(
                    ui.div("🤖 AI Filter", class_="sidebar-title"),
                    ui.p(
                        "Try asking: show only Arsenal matches, only draws, Liverpool away wins, or matches where the home team scored at least 4 goals.",
                        style="font-size:12px; color:#6b7280;"
                    ),
                    qc.ui(),
                    ui.hr(),
                    ui.input_action_button("ai_reset", "Reset AI filters", class_="btn-reset"),
                    ui.download_button("download_ai_data", "Download filtered data"),
                    class_="sidebar",
                ),

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
                        ui.div(
                            ui.div("Average Home vs Away Goals", class_="chart-title"),
                            ui.div("Computed from filtered matches", class_="chart-subtitle"),
                            ui.output_plot("ai_plot_goals", height="280px"),
                            class_="chart-card",
                        ),
                        ui.div(
                            ui.div("Matches by Season", class_="chart-title"),
                            ui.div("Count of filtered matches per season", class_="chart-subtitle"),
                            ui.output_plot("ai_plot_season", height="280px"),
                            class_="chart-card",
                        ),
                        class_="chart-row-top",
                    ),

                    class_="charts-panel",
                ),

                class_="body-row",
            ),
        ),
    ),

    ui.div(
        ui.div(
            ui.p("EPL Performance Dashboard : Interactive exploration of team results."),
            ui.p([
                "Authors: Omowunmi, Wenrui, Gurleen. ",
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

    ui.tags.script(f"""
document.addEventListener('DOMContentLoaded', function(){{
    const btn = document.getElementById('btn_reset');
    if (!btn) return;

    btn.addEventListener('click', function() {{
        btn.disabled = true;

        Shiny.setInputValue('input_team', 'Arsenal', {{priority: 'event'}});
        Shiny.setInputValue('input_season', '{DEFAULT_SEASON}', {{priority: 'event'}});

        const selTeam = document.getElementById('input_team');
        if (selTeam) {{ selTeam.value = 'Arsenal'; selTeam.dispatchEvent(new Event('input')); selTeam.dispatchEvent(new Event('change')); }}
        const selSeason = document.getElementById('input_season');
        if (selSeason) {{ selSeason.value = '{DEFAULT_SEASON}'; selSeason.dispatchEvent(new Event('input')); selSeason.dispatchEvent(new Event('change')); }}

        setTimeout(function() {{
            Shiny.setInputValue('input_result', 'All', {{priority: 'event'}});
            const sel = document.getElementById('input_result');
            if (sel) {{ sel.value = 'All'; sel.dispatchEvent(new Event('input')); sel.dispatchEvent(new Event('change')); }}
            setTimeout(function(){{ btn.disabled = false; }}, 200);
        }}, 250);
    }});
}});
"""),
)

# ── Server ─────────────────────────────────────────────────────────────────────
def server(input, output, session):
    qc_vals = qc.server()
    
    @reactive.effect
    @reactive.event(input.input_team)
    def _update_seasons_for_team():
        team = input.input_team()
        available = TEAM_SEASONS.get(team, ALL_SEASONS)
        # Keep current season if valid, otherwise pick the latest available
        current_season = input.input_season()
        selected = current_season if current_season in available else available[-1]
        ui.update_select("input_season", choices=available, selected=selected)
        
    @output
    @render.ui
    def ai_title():
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
        return render.DataGrid(qc_vals.df(), width="100%")

    @output
    @render.plot
    def ai_plot_result():
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

    @reactive.effect
    @reactive.event(input.ai_reset)
    def _reset_ai():
        qc_vals.sql.set("")
        qc_vals.title.set(None)

    @render.download(filename="querychat_filtered_epl.csv")
    def download_ai_data():
        yield qc_vals.df().to_csv(index=False)

    # ────── LAZY LOADING: Filter at database level with ibis ──────────────────
    @reactive.calc
    def matches_filtered():
        """
        Build ibis filter expression from inputs, execute only filtered rows.
        This ensures ALL filtering happens before rows enter pandas DataFrame.
        """
        team = input.input_team()
        season = input.input_season()
        result = input.input_result()
        
        # Build filter expression (lazy, not executed yet)
        expr = filter_matches_ibis(team, season, result)
        
        # Execute to get pandas DataFrame (only filtered rows loaded)
        mf = expr.execute()
        
        # Add team-centric derived columns (Home vs Away view)
        if not mf.empty:
            mf = get_team_matches(mf, team)
        
        return mf

    @reactive.calc
    def summary_home_away():
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

    def _metrics_for_season(season: str):
        """Get metrics for a specific season (all teams)."""
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

    @reactive.calc
    def summary_period():
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

    @output
    @render.ui
    def data_context_description():
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
        season = input.input_season()
        curr = _metrics_for_season(season)["n"]
        prev = None
        try:
            idx = ALL_SEASONS.index(season)
            if idx > 0:
                prev = ALL_SEASONS[idx - 1]
        except Exception:
            prev = None
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
        season = input.input_season()
        curr = _metrics_for_season(season)["win_rate"]
        prev = None
        try:
            idx = ALL_SEASONS.index(season)
            if idx > 0:
                prev = ALL_SEASONS[idx - 1]
        except Exception:
            prev = None
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
        season = input.input_season()
        curr = _metrics_for_season(season)["avg_goals_for"]
        prev = None
        try:
            idx = ALL_SEASONS.index(season)
            if idx > 0:
                prev = ALL_SEASONS[idx - 1]
        except Exception:
            prev = None
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
        season = input.input_season()
        curr = _metrics_for_season(season)["avg_goals_against"]
        prev = None
        try:
            idx = ALL_SEASONS.index(season)
            if idx > 0:
                prev = ALL_SEASONS[idx - 1]
        except Exception:
            prev = None
        prev_val = _metrics_for_season(prev)["avg_goals_against"] if prev else 0.0
        comp = _pct_change(curr, prev_val)
        comp_ui = comp if comp is not None else ui.span("— vs previous season", class_="kpi-compare")
        return ui.div(
            ui.div(f"{curr:.2f}", style="font-size:22px; font-weight:700;"),
            comp_ui,
        )

    def _style_ax(ax):
        ax.spines[["top", "right"]].set_visible(False)
        ax.yaxis.grid(True, linestyle="--", linewidth=0.6, alpha=0.45, zorder=0)
        ax.set_axisbelow(True)
        ax.tick_params(axis="both", labelsize=8)

    def _bar_labels(ax, bars):
        ylim = ax.get_ylim()
        for bar in bars:
            h = bar.get_height()
            ax.text(
                bar.get_x() + bar.get_width() / 2,
                h + (ylim[1] - ylim[0]) * 0.02,
                f"{h:.1f}",
                ha="center", va="bottom", fontsize=8, fontweight="600",
            )

    @output
    @render.plot
    def out_goals_home_away():
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
        ax.set_xticklabels([f"{v}\n(n={s[v]['n']})" for v in venues], fontsize=9)
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
        s = summary_home_away()
        venues = ["Home", "Away"]
        vals = [s[v]["win_rate"] for v in venues]

        fig, ax = plt.subplots(figsize=(5, 3.5))
        fig.patch.set_facecolor("#fff")
        ax.set_facecolor("#fff")

        bars = ax.bar(
            [f"{v}\n(n={s[v]['n']})" for v in venues],
            vals,
            color=[C_HOME, C_AWAY],
            width=0.45, zorder=3,
        )
        ax.set_ylabel("Win Rate (%)", fontsize=9)
        ax.set_ylim(0, max(vals + [1]) * 1.35)
        _style_ax(ax)
        _bar_labels(ax, bars)
        fig.tight_layout(pad=0.8)
        return fig

    @output
    @render.plot
    def out_goals_by_period():

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

        x_labels = [f"{p}\n(n={ns[i]})" for i, p in enumerate(periods)]

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
        mf = assign_period(matches_filtered()).copy()
        
        # Handle empty DataFrame
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

    @output
    @render.ui
    def out_active_filters():
        parts = []
        try:
            team = input.input_team()
        except Exception:
            team = None
        try:
            season = input.input_season()
        except Exception:
            season = None
        try:
            res = input.input_result()
        except Exception:
            res = None

        if team:
            parts.append(ui.span(f"Team: {team}", class_="chip"))
        if season:
            parts.append(ui.span(f"Season: {season}", class_="chip"))
        if res and res != "All":
            parts.append(ui.span(f"Result: {res}", class_="chip"))
        if not parts:
            return ui.div(ui.span("No active filters", style="color:#9ca3af; font-size:12px;"))
        return ui.div(*parts, class_="active-filters")


app = App(app_ui, server)