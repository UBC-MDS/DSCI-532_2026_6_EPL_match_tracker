import pandas as pd


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
df_all["Result"] = df_all["FullTimeResult"].map({
    "H": "Home team win",
    "A": "Away team win",
    "D": "Draw"
})

df_all["Result"] = df_all["FullTimeResult"].map({
    "H": "Home team win",
    "A": "Away team win",
    "D": "Draw"
})

df_all.to_parquet("data/processed/epl_final.parquet")
