---
name: project_tests_layout
description: "tests/case/ holds the automated tests (plain scripts, no test_ prefix on the files), tests/interact/ the tools played by ear, never run by Claude. Since 2026-10-02: seven test files for phase 1, and platform_check.py to hear it."
metadata:
  type: project
---

The `tests/` folder was set up with two empty folders before the first session:

- **`tests/case/`**: the automated tests. One plain script per area, named for what it covers (`paths.py`, `runloop.py`, `gameplay.py`), with no `test_` prefix on the file; the functions inside start with `test_`. Each finds the repository by going two folders up from itself, then imports `_scratch_save` ([[project_safe_test_run]]), and ends with `_scratch_save.run(globals())`. Since 2026-10-02: `paths`, `runloop`, `save`, `speech`, `keymap`, `sound`, `language` (phase 1) and `scene` (phase 2).
- **`tests/interact/`**: tools the dev plays by ear, each on its own save. They are not tests, and Claude never runs them, since they make sound and speak ([[feedback_interactive_tests]]). Since 2026-10-02:
  - `platform_check.py`: phase 1 by ear, before there is a game; all its checks passed by ear on 2026-10-02 (the dev). A menu in its own window (Up, Down, Enter or the number; Escape stops a check; Alt+F4 quits at any moment): the roar and the bats placed left, centre and right; the roar at 3.0 and 1.0; stereo against mono; every sound 2.32 plays; the tutorial line in the SAPI voice followed by the key hints; the master volume; the installed voices. Its own save in `%APPDATA%\InsideTheCave\platform_check`.
  - `scene_check.py`: phase 2 by ear, built on `platform_check.py`'s window and keys (it imports them): short previews built from the SpriteKit stand-in, a monster, bats or a jingling coin down each lane with the roar at the sensor and "now" when it would reach you, you in each lane, eight monsters in a row. Its own save in `%APPDATA%\InsideTheCave\scene_check`.
  - Later, as in the reference port: a chooser that opens the real game at a chosen point, once there is a game.

**Why:** The dev's layout for their ports.

**How to apply:** Put a new automated test in `tests/case/`, and match a change to the test file that covers it ([[feedback_dont_run_or_build]]). Whenever something can be heard, add a check to a tool in `tests/interact/` too ([[feedback_interactive_tests]]).
