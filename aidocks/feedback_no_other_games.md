---
name: feedback_no_other_games
description: "Never name or refer to the dev's other games in this repo's own files (todo list, changelog, README, aidocks, CLAUDE.md, Python code and comments); write about Inside The Cave alone. Reference material in user/ is described by where it lives."
metadata:
  node_type: memory
  type: feedback
---

Don't mention the dev's other games anywhere in this repo's own files:
- `docks/` (the player readme, the changelog, the todo list)
- `README.md`
- any `aidocks/` memory file, and `CLAUDE.md`
- the Python code, including its comments and docstrings
- commit messages

That rules out their names, their folder names and their paths, and phrases like "the same as in their other game". Write about Inside The Cave alone.

**Why:** The dev confirmed on 2026-10-02 that this repo follows the same rule as their earlier port, which they keep in the gitignored `user/` folder as a reference for how a port is done.

**How to apply:**
- When a fact matters but its source is another project, state the fact on its own. For example, "the dev reviews through a screen reader", not where that was learned.
- When something in this repo came from elsewhere, describe it by where it lives here: "the reference port in the gitignored `user/` folder".
- Reading material in `user/` for reference is fine; just don't name it in writing. Never edit anything in `user/`.
- Before saving a memory, a todo line, a commit message or a code comment, check it for other games' names.
