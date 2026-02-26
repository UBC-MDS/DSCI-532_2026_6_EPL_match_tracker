from shiny import App, ui, render, reactive
import matplotlib.pyplot as plt
import pandas as pd

# ── Load dataset ───────────────────────────────────────────────────────────────
df_all = pd.read_csv("data/raw/EPL_final.csv")
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
C_HOME          = "#4e79a7"
C_AWAY          = "#e15759"
C_GOALS_FOR     = "#59a14f"
C_GOALS_AGAINST = "#e15759"
C_EARLY         = "#4e79a7"
C_MID           = "#f28e2b"
C_LATE          = "#59a14f"

# ── CSS ────────────────────────────────────────────────────────────────────────
page_style = ui.tags.style("""
html, body, .container-fluid {
    height: 100%; margin: 0; padding: 0; background: #f4f6f9;
}

.dashboard-wrap {
    display: flex;
    flex-direction: column;
    padding: 16px;
    gap: 14px;
    box-sizing: border-box;
    overflow-y: auto;
}

/* ── KPI row ── */
.kpi-row {
    display: flex;
    gap: 12px;
    flex-shrink: 0;
}
.kpi-card {
    flex: 1 1 0;
    background: #fff;
    border-radius: 10px;
    border: 1px solid #e0e4ea;
    box-shadow: 0 1px 4px rgba(0,0,0,.06);
    padding: 12px 16px;
}
.kpi-label {
    font-size: 10px;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: .05em;
    color: #6b7280;
    margin-bottom: 6px;
}
.kpi-value {
    font-size: 22px;
    font-weight: 700;
    color: #111827;
    line-height: 1;
}

/* ── Body row ── */
.body-row {
    display: flex;
    gap: 14px;
}

/* ── Sidebar ── */
.sidebar {
    width: 200px;
    flex-shrink: 0;
    background: #fff;
    border-radius: 10px;
    border: 1px solid #e0e4ea;
    box-shadow: 0 1px 4px rgba(0,0,0,.06);
    padding: 16px 14px;
    display: flex;
    flex-direction: column;
    gap: 14px;
    box-sizing: border-box;
}
.sidebar-title {
    font-size: 14px;
    font-weight: 700;
    color: #111827;
    margin-bottom: 2px;
}
.sidebar label {
    font-size: 12px;
    font-weight: 600;
    color: #374151;
}
.sidebar .form-select {
    font-size: 12px;
    border-radius: 6px;
    border: 1px solid #d1d5db;
}

/* ── Charts panel ── */
.charts-panel {
    flex: 1 1 0;
    display: flex;
    flex-direction: column;
    gap: 12px;
    min-width: 0;
}

.chart-row-top {
    display: flex;
    gap: 12px;
}

.chart-row-bottom {
    display: flex;
}

.chart-card {
    flex: 1 1 0;
    background: #fff;
    border-radius: 10px;
    border: 1px solid #e0e4ea;
    box-shadow: 0 1px 4px rgba(0,0,0,.06);
    padding: 12px 14px 8px;
    display: flex;
    flex-direction: column;
    min-width: 0;
    overflow: hidden;
}
.chart-title {
    font-size: 12px;
    font-weight: 700;
    color: #374151;
    margin-bottom: 2px;
    flex-shrink: 0;
}
.chart-subtitle {
    font-size: 10px;
    color: #9ca3af;
    margin-bottom: 6px;
    flex-shrink: 0;
}

/* ── Table card ── */
.table-card {
    background: #fff;
    border-radius: 10px;
    border: 1px solid #e0e4ea;
    box-shadow: 0 1px 4px rgba(0,0,0,.06);
    padding: 10px 14px;
    max-height: 200px;
    overflow-y: auto;
}
""")

# ── UI ─────────────────────────────────────────────────────────────────────────
app_ui = ui.page_fluid(
    page_style,
    ui.div(

        # ── KPI row ───────────────────────────────────────────────────────────
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
                ui.div("Avg Goals Scored",   class_="kpi-label"),
                ui.div(ui.output_ui("out_kpi_goals_scored"),   class_="kpi-value"),
                class_="kpi-card",
            ),
            ui.div(
                ui.div("Avg Goals Conceded", class_="kpi-label"),
                ui.div(ui.output_ui("out_kpi_goals_conceded"), class_="kpi-value"),
                class_="kpi-card",
            ),
            class_="kpi-row",
        ),

        # ── Body row ──────────────────────────────────────────────────────────
        ui.div(

            # Sidebar
            ui.div(
                ui.div("⚽ Filters", class_="sidebar-title"),
                ui.input_select("input_team",   "Team",   choices=ALL_TEAMS),
                ui.input_select("input_season", "Season", choices=ALL_SEASONS),
                class_="sidebar",
            ),

            # Charts panel
            ui.div(

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

                # Row 2: Story 3 full width
                ui.div(
                    ui.div(
                        ui.div("Avg Goals Scored by Season Period", class_="chart-title"),
                        ui.div("Early / Mid / Late · Story 3",      class_="chart-subtitle"),
                        ui.output_plot("out_goals_by_period", height="220px"),
                        class_="chart-card",
                    ),
                    class_="chart-row-bottom",
                ),

                # Row 3: Match table
                ui.div(
                    ui.output_data_frame("out_matches_table"),
                    class_="table-card",
                ),

                class_="charts-panel",
            ),

            class_="body-row",
        ),

        class_="dashboard-wrap",
    ),
)


# ── Server ─────────────────────────────────────────────────────────────────────
def server(input, output, session):

    # ── matches_filtered ──────────────────────────────────────────────────────
    @reactive.calc
    def matches_filtered():
        df = df_all[df_all["Season"] == input.input_season()]
        return get_team_matches(df, input.input_team())

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
        return str(len(matches_filtered()))

    @output
    @render.ui
    def out_kpi_winrate():
        mf = matches_filtered()
        return "—" if mf.empty else f"{mf['win'].mean()*100:.1f}%"

    @output
    @render.ui
    def out_kpi_goals_scored():
        mf = matches_filtered()
        return "—" if mf.empty else f"{mf['goals_for'].mean():.2f}"

    @output
    @render.ui
    def out_kpi_goals_conceded():
        mf = matches_filtered()
        return "—" if mf.empty else f"{mf['goals_against'].mean():.2f}"

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


# ── App instance ───────────────────────────────────────────────────────────────
app = App(app_ui, server)