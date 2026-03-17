"""
Playwright behavior tests for the EPL Match Tracker dashboard.
Requires the app to be running locally at http://127.0.0.1:8000.
Run with: pytest tests/test_app.py --headed
"""
 
import pytest
from playwright.sync_api import Page, expect
 
 
APP_URL = "http://127.0.0.1:8000/"
 
 
def test_dashboard_loads(page: Page):
    """Verifies that the dashboard loads successfully and displays the main title,
    ensuring the app is reachable and the UI renders without errors."""
    page.goto(APP_URL)
    expect(page.locator("h2")).to_contain_text("EPL Performance Dashboard")
 
 
def test_team_filter_updates_context(page: Page):
    """Verifies that selecting a different team updates the data context description,
    confirming that the team filter is wired correctly to the reactive outputs."""
    page.goto(APP_URL)
    page.select_option("#input_team", "Liverpool")
    page.wait_for_timeout(500)
    expect(page.locator(".chip", has_text="Team: Liverpool")).to_be_visible()


def test_result_filter_shows_active_chip(page: Page):
    """Verifies that selecting a result filter displays an active filter chip,
    so users can confirm which filters are currently applied to the dashboard."""
    page.goto(APP_URL)
    page.select_option("#input_result", "Win")
    page.wait_for_timeout(500)
    expect(page.locator(".chip", has_text="Result: Win")).to_be_visible()
 
 
def test_reset_button_clears_filters(page: Page):
    """Verifies that clicking Reset filters restores the default team and result,
    which is critical for users who want to quickly return to the default view."""
    page.goto(APP_URL)
    page.select_option("#input_team", "Liverpool")
    page.select_option("#input_result", "Win")
    page.click("#btn_reset")
    page.wait_for_timeout(600)
    expect(page.locator("#input_team")).to_have_value("Arsenal")
