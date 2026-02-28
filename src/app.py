from shiny import App, ui, render, reactive
import matplotlib.pyplot as plt
import pandas as pd
import json
import os
import base64
import datetime

# ── Load dataset ───────────────────────────────────────────────────────────────
df_all = pd.read_csv("data/raw/epl_final.csv")
df_all.columns               = df_all.columns.str.strip()
df_all["Season"]             = df_all["Season"].astype(str).str.strip()
df_all["HomeTeam"]           = df_all["HomeTeam"].astype(str).str.strip()
df_all["AwayTeam"]           = df_all["AwayTeam"].astype(str).str.strip()
df_all["FullTimeResult"]     = df_all["FullTimeResult"].astype(str).str.strip()
df_all["MatchDate"]          = pd.to_datetime(df_all["MatchDate"])
df_all["FullTimeHomeGoals"]  = pd.to_numeric(df_all["FullTimeHomeGoals"])
df_all["FullTimeAwayGoals"]  = pd.to_numeric(df_all["FullTimeAwayGoals"])

ALL_TEAMS   = sorted(set(df_all["HomeTeam"].tolist() + df_all["AwayTeam"].tolist()))
ALL_SEASONS = sorted(df_all["Season"].unique().tolist())

# Date defaults for date-range filter
DEFAULT_DATE_START = df_all["MatchDate"].min().date().isoformat()
DEFAULT_DATE_END = df_all["MatchDate"].max().date().isoformat()


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

# last updated date for footer
LAST_UPDATED = datetime.date.today().isoformat()

# ── Helpers ────────────────────────────────────────────────────────────────────
def get_team_matches(df: pd.DataFrame, team: str) -> pd.DataFrame:
    home = df[df["HomeTeam"] == team].copy()
    away = df[df["AwayTeam"] == team].copy()

    home["venue"]         = "Home"
    home["goals_for"]     = home["FullTimeHomeGoals"]
    home["goals_against"] = home["FullTimeAwayGoals"]
    home["win"]           = (home["FullTimeResult"] == "H").astype(int)

    away["venue"]         = "Away"
    away["goals_for"]     = away["FullTimeAwayGoals"]
    away["goals_against"] = away["FullTimeHomeGoals"]
    away["win"]           = (away["FullTimeResult"] == "A").astype(int)

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
.sidebar { width:220px; flex-shrink:0; background:#fff; border-radius:10px; border:1px solid #e0e4ea; box-shadow:0 1px 4px rgba(0,0,0,0.06); padding:16px; display:flex; flex-direction:column; gap:12px; align-self:stretch; }
.sidebar-title{ font-size:14px; font-weight:700; color:#111827; }
.sidebar label{ font-size:12px; font-weight:600; color:#374151; }
.sidebar .form-select{ font-size:12px; border-radius:6px; border:1px solid #d1d5db; }
.btn-reset{ padding:6px 10px; font-size:12px; border-radius:6px; background:#f3f4f6; color:#111827; }

/* Header banner image (explicit <img>) */
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

/* Table card */
.table-card{ background:#fff; border-radius:10px; border:1px solid #e0e4ea; box-shadow:0 1px 4px rgba(0,0,0,0.06); padding:10px 14px; height:320px; overflow-y:auto; display:flex; flex-direction:column; }

/* Active filters chips */
.active-filters { display:flex; gap:8px; flex-wrap:wrap; margin-bottom:8px; }
.active-filters .chip { background: #eef2ff; color:#3730a3; padding:6px 10px; border-radius:999px; font-size:12px; font-weight:600; }

/* Footer */
.app-footer{ margin-top:8px; padding:10px 16px; text-align:left; color:#6b7280; font-size:13px; display:flex; gap:18px; align-items:center; justify-content:space-between; flex-wrap:wrap; }
.app-footer p{ margin:0; }

""")

# ── Hero Header with Local Stadium Background ─────────────────────
def hero_header():
    # prefer inline data-uri when available, otherwise fall back to static path
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
    ui.div(

        

        # ── Body row ──────────────────────────────────────────────────────────
        ui.div(

            # Sidebar
            ui.div(
                ui.div("⚽ Filters", class_="sidebar-title"),
                ui.input_select("input_team",   "Team",   choices=ALL_TEAMS, selected="Arsenal"),
                ui.input_select("input_season", "Season", choices=ALL_SEASONS, selected="2000/01"),
                ui.input_select("input_result", "Match result", choices=["All","Win","Draw","Loss"], selected="All"),
                    ui.output_ui("out_active_filters"),
                    ui.input_action_button("btn_reset", "Reset filters", class_="btn-reset"),
                class_="sidebar",
            ),

            # Charts panel
            ui.div(
                # main content: KPI row + charts
                ui.div(
                    ui.div(
                        ui.div("Total Matches",      class_="kpi-label"),
                        ui.div(ui.output_ui("out_kpi_total"),          class_="kpi-value"),
                        class_="kpi-card",
                    ),
                    ui.div(
                        ui.div("Win Rate",           class_="kpi-label"),
                        ui.div(ui.output_ui("out_kpi_winrate"),        class_="kpi-value"),
                        class_="kpi-card",
                    ),
                    ui.div(
                        ui.div("Average Goals Scored",   class_="kpi-label"),
                        ui.div(ui.output_ui("out_kpi_goals_scored"),   class_="kpi-value"),
                        class_="kpi-card",
                    ),
                    ui.div(
                        ui.div("Average Goals Conceded", class_="kpi-label"),
                        ui.div(ui.output_ui("out_kpi_goals_conceded"), class_="kpi-value"),
                        class_="kpi-card",
                    ),
                    class_="kpi-row",
                ),

                # Row 1: Story 1 + Story 2 side by side
                ui.div(
                    ui.div(
                        ui.div("Goals Scored vs Goals Conceded", class_="chart-title"),
                        ui.div("Home vs Away · Story 1",         class_="chart-subtitle"),
                        ui.output_plot("out_goals_home_away", height="280px"),
                        class_="chart-card",
                    ),
                    ui.div(
                        ui.div("Win Rate",               class_="chart-title"),
                        ui.div("Home vs Away · Story 2", class_="chart-subtitle"),
                        ui.output_plot("out_winrate_home_away", height="280px"),
                        class_="chart-card",
                    ),
                    class_="chart-row-top",
                ),

                # Row 2: small line chart + match table side-by-side
                ui.div(
                    ui.div(
                        ui.div("Average Goals Scored by Season Period", class_="chart-title"),
                        ui.div("Early / Mid / Late · Story 3",      class_="chart-subtitle"),
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
    # Footer
    ui.div(
        ui.div(
            ui.p("EPL Performance Dashboard : Interactive exploration of team results."),
            ui.p(["Authors: Omowunmi, Wenrui, Gurleen. ", ui.a("Repo", href="https://github.com/UBC-MDS/DSCI-532_2026_6_EPL_match_tracker", target="_blank")]),
            ui.p(f"Last updated: {LAST_UPDATED}"),
            class_="app-footer",
        ),
    ),
    ui.tags.script(f"""
document.addEventListener('DOMContentLoaded', function(){{
    const btn = document.getElementById('btn_reset');
    if (!btn) return;

    btn.addEventListener('click', function() {{
        // prevent double-clicks while resetting
        btn.disabled = true;

        // set primary inputs first (team, season) as event-priority updates
        Shiny.setInputValue('input_team', 'Arsenal', {{priority: 'event'}});
        Shiny.setInputValue('input_season', '2000/01', {{priority: 'event'}});

        // also update visible select elements immediately if present
        const selTeam = document.getElementById('input_team');
        if (selTeam) {{ selTeam.value = 'Arsenal'; selTeam.dispatchEvent(new Event('input')); selTeam.dispatchEvent(new Event('change')); }}
        const selSeason = document.getElementById('input_season');
        if (selSeason) {{ selSeason.value = '2000/01'; selSeason.dispatchEvent(new Event('input')); selSeason.dispatchEvent(new Event('change')); }}

        // set match-result after a short delay so the server sees team/season first
        setTimeout(function() {{
            Shiny.setInputValue('input_result', 'All', {{priority: 'event'}});
            // also update the visible select element value if present
            const sel = document.getElementById('input_result');
            if (sel) {{ sel.value = 'All'; sel.dispatchEvent(new Event('input')); sel.dispatchEvent(new Event('change')); }}
            // re-enable the button after another short delay
            setTimeout(function(){{ btn.disabled = false; }}, 200);
        }}, 250);
    }});
}});
"""),
)


# ── Server ─────────────────────────────────────────────────────────────────────
def server(input, output, session):

    # ── matches_filtered ──────────────────────────────────────────────────────
    @reactive.calc
    def matches_filtered():
        df = df_all[df_all["Season"] == input.input_season()].copy()
        mf = get_team_matches(df, input.input_team())
        # apply match-result filter if provided
        try:
            res = input.input_result()
        except Exception:
            res = None
        if res and res != "All":
            if res == "Win":
                mf = mf[mf["win"] == 1]
            elif res == "Draw":
                mf = mf[mf["FullTimeResult"] == "D"]
            elif res == "Loss":
                mf = mf[(mf["win"] == 0) & (mf["FullTimeResult"] != "D")]
        return mf

    # ── summary_home_away ─────────────────────────────────────────────────────
    @reactive.calc
    def summary_home_away():
        mf = matches_filtered()
        out = {}
        for venue in ("Home", "Away"):
            sub = mf[mf["venue"] == venue]
            if sub.empty:
                out[venue] = dict(win_rate=0, avg_goals_for=0, avg_goals_against=0, n=0)
            else:
                out[venue] = dict(
                    win_rate          = sub["win"].mean() * 100,
                    avg_goals_for     = sub["goals_for"].mean(),
                    avg_goals_against = sub["goals_against"].mean(),
                    n                 = len(sub),
                )
        return out

    def _metrics_for_season(season: str):
        df = df_all[df_all["Season"] == season]
        mf = get_team_matches(df, input.input_team())
        if mf.empty:
            return dict(n=0, win_rate=0.0, avg_goals_for=0.0, avg_goals_against=0.0)
        return dict(
            n = len(mf),
            win_rate = mf["win"].mean() * 100,
            avg_goals_for = mf["goals_for"].mean(),
            avg_goals_against = mf["goals_against"].mean(),
        )

    def _pct_change(curr, prev, abs_unit: str = ""):
        # returns a small UI span showing ▲/▼ percent change and absolute difference
        if prev == 0 or prev is None:
            return None
        try:
            change = (curr - prev) / prev * 100
        except Exception:
            return None
        arrow = "▲" if change > 0 else ("▼" if change < 0 else "—")
        sign = f"{abs(change):.1f}%"
        abs_diff = curr - prev
        # format absolute diff: integer for matches, one decimal otherwise
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

    # ── summary_period ────────────────────────────────────────────────────────
    @reactive.calc
    def summary_period():
        mf = assign_period(matches_filtered())
        out = {}
        for period in ("Early", "Mid", "Late"):
            sub = mf[mf["period"] == period]
            if sub.empty:
                out[period] = dict(avg_goals=0, n=0)
            else:
                out[period] = dict(
                    avg_goals = sub["goals_for"].mean(),
                    n         = len(sub),
                )
        return out

    # ── KPIs ────��─────────────────────────────────────────────────────────────
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

    # ── Shared helpers ────────────────────────────────────────────────────────
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

    # ── Story 1: Goals scored vs conceded, Home vs Away ───────────────────────
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
            [s[v]["avg_goals_for"]     for v in venues],
            width=w, color=C_GOALS_FOR,     zorder=3, label="Goals Scored",
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
            [s[v]["avg_goals_for"]     for v in venues] +
            [s[v]["avg_goals_against"] for v in venues] + [1]
        ) * 1.35)
        _style_ax(ax)
        _bar_labels(ax, list(bars_for) + list(bars_against))
        ax.legend(fontsize=8, frameon=False, loc="upper right")
        fig.tight_layout(pad=0.8)
        return fig

    # ── Story 2: Win rate, Home vs Away ───────────────────────────────────────
    @output
    @render.plot
    def out_winrate_home_away():
        s = summary_home_away()
        venues = ["Home", "Away"]
        vals   = [s[v]["win_rate"] for v in venues]

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

    # ── Story 3: Avg goals scored by period (line chart) ──────────────────────
    @output
    @render.plot
    def out_goals_by_period():
        s = summary_period()
        periods   = ["Early", "Mid", "Late"]
        avg_goals = [s[p]["avg_goals"] for p in periods]
        ns        = [s[p]["n"]         for p in periods]
        x_labels  = [f"{p}\n(n={ns[i]})" for i, p in enumerate(periods)]
        x         = list(range(len(periods)))

        fig, ax = plt.subplots(figsize=(9, 3))
        fig.patch.set_facecolor("#fff")
        ax.set_facecolor("#fff")

        # Base line in light grey
        ax.plot(x, avg_goals, color="#d1d5db", linewidth=2.2, zorder=2)

        # Coloured point + label per period
        for i, (val, col) in enumerate(zip(avg_goals, [C_EARLY, C_MID, C_LATE])):
            ax.plot(i, val, marker="o", markersize=10, color=col, zorder=4)
            ax.annotate(
                f"{val:.2f}",
                xy=(i, val), xytext=(0, 12),
                textcoords="offset points",
                ha="center", fontsize=9, fontweight="700", color=col,
            )

        ax.set_xticks(x)
        ax.set_xticklabels(x_labels, fontsize=9)
        ax.set_ylabel("Avg Goals Scored", fontsize=9)
        ax.set_ylim(0, max(avg_goals + [1]) * 1.4)
        _style_ax(ax)
        fig.tight_layout(pad=0.8)
        return fig

    # ── Match table ───────────────────────────────────────────────────────────
    @output
    @render.data_frame
    def out_matches_table():
        mf = assign_period(matches_filtered()).copy()
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
            "FullTimeResult":    "Result",
            "venue":             "Venue",
            "goals_for":         "Goals For",
            "goals_against":     "Goals Against",
            "win":               "Win",
            "period":            "Period",
        })
        return render.DataGrid(display, width="100%")


    # ── Active filters display ─────────────────────────────────────────────
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



# ── App instance ───────────────────────────────────────────────────────────────
app = App(app_ui, server)