# Contributing to EPL Match Tracker

Thank you for your interest in contributing to EPL Match Tracker, a DSCI-532 Group 6 project!

---

## Quick Start

1. **Clone** the repo: `git clone https://github.com/UBC-MDS/DSCI-532_2026_6_EPL_match_tracker.git`
2. **Create a branch** from `dev`: `git checkout -b feature/your-feature-name`
3. **Make your changes** with clear commit messages.
4. **Push and open a PR** against `dev` (not `main`). Request a review from at least one teammate.
5. **Merge after approval.**

---

## Project Workflow

### Branch Strategy
- **`main`:** Production-ready code. Deployed to Posit Cloud (stable URL).
- **`dev`:** Development branch. Where features are integrated and tested before release.
- **Feature branches:** Create from `dev` with descriptive names (e.g., `feature/ai-logging`, `fix/import-errors`, `docs/m4-spec`).

### Pull Request Process
1. **Before you code:** Check for open issues or start a new GitHub Issue describing your work. Link it in your PR.
2. **Branch naming:** Use a prefix: `feature/`, `fix/`, `docs/`, `refactor/`, `test/`.
3. **Commit messages:** Write clear, atomic commits (e.g., "Fix utils import path for Posit Cloud" not "stuff").
4. **PR description:** Include:
   - What problem does this solve? (link the issue)
   - How does it solve it? (design rationale, not just code)
   - Any trade-offs or decisions made.
   - Screenshots/demo for UI changes.
5. **Request review:** Tag 1-2 teammates. Respond to feedback promptly.
6. **Approval:** At least one teammate must approve before merging. Aim for reviews within 24 hours.
7. **Merge:** Use "Squash and merge" for cleaner history, or "Create a merge commit" for detailed history. Delete the branch after merging.

### Code Review Expectations
- **Reviewer:** Check for logic errors, test coverage, documentation, adherence to team norms (see Section 3).
- **Author:** Be responsive to feedback. Ask clarifying questions if feedback is unclear.
- **Tone:** Keep discussions respectful and focused on code, not people.

---

## Collaboration Norms (M4)

### Design Before Code
- **Spec-first approach:** For larger features (e.g., new data pipeline, advanced feature), update the specification document BEFORE writing code.
- **Why:** Prevents rework, aligns team on intent, makes code review faster.
- **How:** Create a GitHub Issue describing the change, discuss it, update `reports/m2_spec.md`, then create a PR with the code.

### Distributed Workload
- **Goal:** No single person should dominate the codebase or review queue.
- **Practice:** In each milestone, assign tasks so every team member implements at least one feature or fixes at least one feedback item.
- **Communication:** Mention team members in issues; use Slack to coordinate who's doing what.

### Scoped Pull Requests
- **One feature per PR:** A PR should address one clear goal (e.g., "Add persistent logging" or "Fix import errors"). If you're tempted to do multiple things, split into multiple PRs.
- **Atomic commits:** Each commit should be a logical unit that compiles and works independently (where possible).
- **Size:** Aim for PRs < 400 lines of code changes (excluding tests). Larger changes should be split or discussed with the team.

### No Deadline-Eve Bursts
- **Why:** Last-minute changes are rushed, poorly reviewed, and prone to bugs.
- **Practice:** Start work early in the milestone. Spread contributions throughout, not concentrated in the final night.
- **Benefit:** Better code quality, less stress, team has time to review and test.

### Legible Release Notes
- **Each PR should be release-note-ready:** Write your commit/PR message as if it will go into the CHANGELOG.
- **Example:** Instead of "fixed stuff", write "Fixed import errors on Posit Cloud by adding sys.path handling (#89)".
- **Why:** Eases CHANGELOG generation; keeps project history readable for future contributors.

---

## M3 Retrospective: What Went Well & What Didn't

### What Worked in M3
- ✅ **Core features delivered:** AI Explorer (QueryChat) was implemented and integrated smoothly.
- ✅ **Good separation of concerns:** Each team member took clear ownership of a feature (AI, logging, data transforms).
- ✅ **Regular Slack communication:** Team stayed coordinated on blockers and progress.

### What Didn't Work in M3
- ❌ **Late-stage panic:** Multiple PRs merged in the final 24 hours. Reviewers were rushed; bugs slipped through.
- ❌ **Unclear ownership:** At times, two people worked on the same thing in parallel, causing merge conflicts and rework.
- ❌ **Large, hard-to-review PRs:** Some PRs bundled multiple unrelated changes, making review difficult and slow.
- ❌ **Logging side effects in @output:** Logging was carelessly placed in an `@output` renderer, blocking UI updates. This was a design mistake caught late.
- ❌ **Spec-after-code:** Code was written first; spec was updated to match. This led to inconsistent architecture (e.g., logging in wrong place).

### Lessons for M4
1. **Plan early:** Create detailed issues and update specs BEFORE coding.
2. **Split work early:** Assign tasks by M4.1, not M4.6.
3. **Smaller PRs:** Aim for < 400 lines and one feature per PR. Easier to review, faster merge.
4. **Design principles:** Learn Shiny patterns (e.g., @output is pure, @reactive.effect has side effects) and apply them from the start.
5. **Review promptly:** Aim for 24-hour turnaround. Blocking PRs slow down the team.

---

## M4 Collaboration Commitments

The team commits to the following practices in M4 to address M3 issues:

1. **Specs Before Code (Design-First)**
   - Before starting work on a feature, create a GitHub Issue describing the goal.
   - Update relevant spec document (e.g., `reports/m2_spec.md`).
   - Get team buy-in in the issue comments before opening the PR.

2. **Task Distribution**
   - Each team member resolves at least one M4 feedback item (critical or non-critical).
   - Clearly assign tasks in GitHub Issues to avoid duplication.
   - Use the "Assignee" field to show who's working on what.

3. **Scoped, Reviewable PRs**
   - Each PR = one feature or fix. No bundling unrelated changes.
   - Max ~400 lines of code changes per PR (not counting tests).
   - If a task is larger, split it: "PR #1: Refactor app.py structure" → "PR #2: Add logging" → "PR #3: Add tests".

4. **Continuous Work (No Deadline Surges)**
   - Start early in the milestone.
   - Aim to have most work done by M4.5 (not M4.7).
   - Final days reserved for testing, polish, and release.

5. **Fast Reviews (< 24 hours)**
   - Reviewers respond to PRs within 24 hours (business days).
   - If you're blocked, ping the reviewer in Slack.
   - Implement feedback promptly (same day if possible).

6. **Clear Commit & PR Messages**
   - Write messages as if they'll appear in CHANGELOG.
   - Example: "Fix: Correct sys.path handling for Posit Cloud import errors (#89)" (not "fix bug").
   - Link issues in PR description: "Resolves #88".

---

## Code Style & Best Practices

### Python
- **Format:** Use [Black](https://github.com/psf/black) for consistent formatting (line length: 88).
- **Linting:** Run `flake8` to catch errors. Config in `.flake8` (if present).
- **Type hints:** Encouraged for new code, especially in helper functions.
- **Docstrings:** All public functions should have docstrings (one-line summary + details).

### Shiny (R/Python)
- **@output functions:** Pure rendering only. No side effects (logging, API calls, mutations).
- **@reactive.effect:** Use for side effects (logging, input changes, external calls).
- **Naming:** Use `out_` prefix for outputs, `_` prefix for internal functions (e.g., `_log_ai_interactions`).

### Markdown (Docs)
- **Consistent headings:** Use `#`, `##`, `###` (no skipping levels).
- **Code blocks:** Always include language tag (e.g., ````python`, ````bash`).
- **Links:** Use relative paths for internal docs (`docs/foo.md`), full URLs for external.

### Tests
- **Unit tests:** `tests/test_*.py` using pytest.
- **Browser tests:** `tests/test_app.py` using Playwright.
- **Naming:** Test functions start with `test_` (e.g., `test_get_team_matches_empty_df`).
- **Coverage:** Aim for at least 1 test per public function. Document what each test checks (one-sentence comment).

---

## How to Run Tests Locally

```bash
# Install test dependencies
pip install pytest pytest-playwright playwright

# Run unit tests
pytest tests/test_utils.py -v

# Run browser tests (requires app running)
# Terminal 1:
shiny run src/app.py

# Terminal 2:
pytest tests/test_app.py -v

# Run all tests
pytest tests/ -v
```

---

## Example Contributions

You can contribute in the following ways:

- **Report bugs or issues** via GitHub Issues (include reproduction steps).
- **Fix bugs or implement features** from open Issues (assign yourself).
- **Write or improve documentation** (README.md, specs, CONTRIBUTING.md).
- **Add or improve tests** (unit or browser tests).
- **Code cleanup and refactoring** (improve clarity, reduce duplication, improve performance).
- **Submit feedback** on design or UX via Issues or Slack.

---

## Questions or Suggestions?

- **For technical questions:** Open a GitHub Issue (tag relevant team members).
- **For quick coordination:** Use Slack (esp. for asking who's doing what to avoid duplication).
- **For process questions:** Bring up in team standup or ask in Slack.

---

## Attribution

This contributing guide is adapted from the [Contributor Covenant Contributing Guidelines](https://www.contributor-covenant.org/contributing/) and the team's collaborative experience across Milestones 1-4 of DSCI-532.

**Team:** Omowunmi, Wenrui (Raymond), Gurleen  
**Last updated:** M4 (2026-03-17)