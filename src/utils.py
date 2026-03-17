import pandas as pd


def get_team_matches(df: pd.DataFrame, team: str) -> pd.DataFrame:
    """
    Return all matches for a given team with venue, goals_for, goals_against, and win columns.
    """
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
    """
    Assign Early/Mid/Late period labels to matches based on their position in the DataFrame.
    """
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