---
name: project_safe_test_run
description: "The rule for tests, to be built in from the first one: they keep off the real save and are silent by themselves (a tests/case/_scratch_save.py helper every test imports first sets the user dir, the silent flag and the null audio and dummy video drivers). Plain scripts, run in PowerShell, skipping _*.py."
metadata:
  node_type: memory
  type: project
---

**No tests exist yet (2026-10-02).** When the first is written, it is built this way from the start.

**The dev's rule: testing speaks nothing whatsoever, makes no sound, opens no window and never touches the real save, wherever it is run from.**

**How the tests do it (the design to build):**
- `insidethecave/paths.py` reads an `INSIDETHECAVE_USER_DIR` environment variable for the save folder when it is set, and `platform/speech.py` speaks nothing when `INSIDETHECAVE_SILENT` is set.
- `tests/case/_scratch_save.py` is imported by every test file right after its `sys.path` line, before any game code. It sets, outright and overriding the shell:
  - `INSIDETHECAVE_USER_DIR` to a fresh temporary folder, deleted at exit
  - `INSIDETHECAVE_SILENT=1`
  - `ALSOFT_DRIVERS=null`, `SDL_AUDIODRIVER=dummy` and `SDL_VIDEODRIVER=dummy`
- A test in `tests/case/paths.py` fails if any test file lacks the import, and a test in `tests/case/speech.py` checks that a silent `Speech` loads neither NVDA's client nor Prism.

**How to run them:**
- In the **PowerShell** tool, never Bash: `python tests\case\<name>.py`.
- Each file is a plain script with `def test_*()` functions, bare `assert`, and its own `__main__` runner printing `ok` or `FAIL` per test and a total. Not pytest.
- When looping over `tests\case\*.py`, skip `_*.py`. Print only the lines that are not `ok` to keep the output short.

**Why:** The dev works with NVDA running, and a test that opened a real audio device, spoke, or wrote their save would interrupt them or lose their progress ([[user_screen_reader]]).

**How to apply:** Run only the tests covering what changed, without asking; the full suite only when the dev asks ([[feedback_dont_run_or_build]]). Don't keep a history of every run here; the latest full run, with its count and commit, is enough.
