---
name: feedback_dont_run_or_build
description: "Never build unless the dev says so. Tests may be run without asking, always the safe way, but only the scripts covering the Python files changed; the full suite only when the dev asks. Ask before running the game, compiler.py, or scripts that execute game code or speak. Read-only inspection is fine."
metadata:
  node_type: memory
  type: feedback
---

**Never build anything unless the dev says to.** That covers `compiler.py`, PyInstaller, and any packaging or zip step.

**The tests may be run without asking, always the safe way** ([[project_safe_test_run]]): silent, off the real save, headless. Once tests exist:
- **Only the tests that match what changed.** When a Python file changes and a test script covers it, run only that script.
- **During a batch of fixes, run no tests between the commits.** Run the full suite once at the end, and only when the dev gives the go-ahead.

**Still ask first before running:**
- the game itself, including headless runs
- `compiler.py` or `releaser.py` in any mode, including a dry run
- scratch scripts that import and execute game code to check behaviour
- anything that could speak through NVDA or Prism for real, or play sound

Make the edits, report them, and hand verification by ear back to the dev.

**Read-only inspection is always fine:** reading and grepping files; `git status`, `git diff` and `git log`; listing installed packages; and parsing the binary's bytes for analysis, as was done on 2026-10-02 to read its load commands. When unsure which side of the line something falls on, ask.

**Why:** A standing rule the dev carries across their projects. They run and verify builds themselves, and they work with NVDA running, so an unexpected run can make noise, touch their save, or leave stray processes and artifacts ([[user_screen_reader]]).

**How to apply:** After a code change, run only the test scripts that cover the changed files, the safe way, and report the result. When a change needs checking by ear, end with a clear "relaunch to test" note instead of running the game.
