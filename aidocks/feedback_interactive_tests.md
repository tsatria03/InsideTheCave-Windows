---
name: feedback_interactive_tests
description: "Write a by-ear tool in tests/interact whenever something can be heard or spoken, beside the silent tests; the dev runs them, never Claude."
metadata:
  type: feedback
---

**Write interactive tests whenever possible** (the dev, 2026-10-02: "Write interactive tests when possible", as in their earlier port). The silent tests in `tests/case` prove the logic; they cannot prove what is heard, since they run on OpenAL's null driver and stand-in voices ([[project_safe_test_run]]). So whenever a change makes something that can be heard or spoken, add or extend a tool in `tests/interact` that lets the dev hear it ([[project_tests_layout]]).

**Why:** A passing test is not "it works": the dev confirms by ear ([[feedback_record_plans_first]]), and a tool that plays exactly the thing to check makes that quick, even before the game exists to reach it. The dev asked for one after phase 1, when the silent tests passed but nothing had yet been heard.

**How to apply:**
- One tool per area, in a small pygame window of its own, each item named through the screen reader and printed before it plays, as `tests/interact/platform_check.py` does: Up and Down to choose, Enter or the number to run, Escape to stop a check or leave the menu. Add a check to an existing tool before starting a new one.
- **Alt+F4 must quit any interactive tool at any moment** (the dev, 2026-10-02: "alt f4 should be able to tirmenate an interactive test."), even in the middle of a sound or a spoken line. So a tool runs in a window, never on console `input()`, and never waits with a bare `time.sleep`: every wait watches the window's events every 20 ms, and the window's close (`pygame.QUIT`, or Alt+F4 itself) leaves at once, stopping the sound and the voice.
- **The dev's save is never touched**: each tool sets `INSIDETHECAVE_USER_DIR` to its own folder under `%APPDATA%\InsideTheCave` before importing the game, copying in the dev's `keys.json` and `settings.json`.
- **Claude never runs them** ([[feedback_dont_run_or_build]]): they make sound and speak. Check they compile with `python -m py_compile`, then hand them over with the command to run.
- When a phase or fix is reported done, say which tool and which check to hear it with.
