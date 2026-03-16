"""
Unit tests for helper functions in src/utils.py.
Run with: pytest tests/test_utils.py
"""
 
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))
 
import pandas as pd
import pytest
from utils import get_team_matches, assign_period
 
 
# ── Fixtures ───────────────────────────────────────────────────────────────────
 
@pytest.fixture
def sample_df():
    """Minimal EPL-style DataFrame with two matches."""
    return pd.DataFrame({
        "HomeTeam":          ["Arsenal", "Chelsea"],
        "AwayTeam":          ["Chelsea", "Arsenal"],
        "FullTimeHomeGoals": [2, 1],
        "FullTimeAwayGoals": [1, 3],
        "FullTimeResult":    ["H", "A"],
        "MatchDate":         pd.to_datetime(["2023-01-01", "2023-01-08"]),
        "Season":            ["2022-23", "2022-23"],
    })
 
 
# ── get_team_matches tests ─────────────────────────────────────────────────────
 
def test_get_team_matches_returns_both_venues(sample_df):
    """Verifies that get_team_matches returns both home and away matches for a team,
    which is critical for correct venue-based analysis throughout the dashboard."""
    result = get_team_matches(sample_df, "Arsenal")
    assert set(result["venue"]) == {"Home", "Away"}
 
 
def test_get_team_matches_goals_for_home(sample_df):
    """Verifies that goals_for is correctly assigned as FullTimeHomeGoals when
    Arsenal plays at home, ensuring KPI and chart calculations are accurate."""
    result = get_team_matches(sample_df, "Arsenal")
    home_row = result[result["venue"] == "Home"].iloc[0]
    assert home_row["goals_for"] == 2
 
 
def test_get_team_matches_win_away(sample_df):
    """Verifies that win is correctly set to 1 for an away win,
    which directly affects the win rate KPI displayed on the dashboard."""
    result = get_team_matches(sample_df, "Arsenal")
    away_row = result[result["venue"] == "Away"].iloc[0]
    assert away_row["win"] == 1
 
 
def test_get_team_matches_empty_for_unknown_team(sample_df):
    """Verifies that an unknown team returns an empty DataFrame rather than
    crashing, preventing silent errors when filters produce no results."""
    result = get_team_matches(sample_df, "UnknownFC")
    assert result.empty
 
 
# ── assign_period tests ────────────────────────────────────────────────────────
 
def test_assign_period_labels(sample_df):
    """Verifies that assign_period produces only valid period labels (Early/Mid/Late),
    ensuring the season period chart always has well-defined categories."""
    result = assign_period(sample_df)
    assert set(result["period"]).issubset({"Early", "Mid", "Late"})
 
 
def test_assign_period_empty_df():
    """Verifies that assign_period handles an empty DataFrame without crashing,
    which matters when filters return no matches for a team/season combination."""
    empty = pd.DataFrame(columns=["HomeTeam", "MatchDate"])
    result = assign_period(empty)
    assert "period" in result.columns
    assert len(result) == 0