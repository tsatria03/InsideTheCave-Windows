---
name: project_tests_layout
description: "tests/case/ holds the automated tests (plain scripts, no test_ prefix on the files), tests/interact/ the tools played by ear, which open the real game and are never run by Claude. Both folders exist and are empty on 2026-10-02."
metadata:
  type: project
---

The `tests/` folder was set up with two empty folders before the first session:

- **`tests/case/`**: the automated tests. One plain script per area, named for what it covers (`paths.py`, `runloop.py`, `gameplay.py`), with no `test_` prefix on the file; the functions inside start with `test_`. Each finds the repository by going two folders up from itself, then imports `_scratch_save` ([[project_safe_test_run]]).
- **`tests/interact/`**: tools the dev plays by ear, such as a chooser that opens the real game at a chosen point on its own save. They are not tests, and Claude never runs them, since they open the real game with sound.

**Why:** The dev's layout for their ports.

**How to apply:** Put a new automated test in `tests/case/`, and match a change to the test file that covers it ([[feedback_dont_run_or_build]]).
