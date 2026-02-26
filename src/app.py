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

