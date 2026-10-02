---
name: feedback_todo_list_format
description: "docks/todo list.txt: ##Unfinished. then ##Finished. headings, one plain sentence per line stating the bug itself (never \"Fix a bug where\"), new items at the top after the heading's blank line, each as short as the rest, LF endings, no markdown. Players only; developer tasks go in project_dev_tasks."
metadata:
  node_type: memory
  type: feedback
---

`docks/todo list.txt`, with a space in the name, is the dev's task list. **It holds only what a player notices**, the same bar as the changelog ([[feedback_changelog]]), because it ships beside the game. Work on the repository, the tools, the tests, the build, the docs and debug mode goes in [[project_dev_tasks]] instead. When a line mixes the two, split it.

Its format:
- `##Unfinished.` on the first line, a blank line, then one item per line.
- A blank line, then `##Finished.`, a blank line, and its items below.
- **Every heading is followed by one blank line, and a new item goes after that blank line**, at the top of the items. Never put an item straight under the heading. With the Edit tool, match the heading and the blank line together (`##Finished.\n\n`) and insert after both. Both headings are capitalized.
- Each item is a plain sentence or two. **A bug is stated as what happens, with no "Fix a bug where" in front**: "The torch is thrown into the wrong lane.", not "Fix a bug where the torch is thrown into the wrong lane."
- An enhancement or task starts with what to do: "Add ...", "Make ...", "Remove ...", "Decide whether ...".
- A finished item says what is now true, starting with its subject.
- No numbering, no bullets, no markdown, no file:line references. Avoid contractions.
- **LF** line endings with no BOM. Keep every line well under 1024 characters.

**Why:** A standing rule the dev carries across their projects. They read the file by screen reader, so plain sentences read cleanly and markdown symbols would be spoken aloud.

**How to apply:**
- **A player-facing finding that is reported to the dev, and not fixed in the same change, goes into `##Unfinished.` as soon as it is reported.**
- **A bug found and fixed in the same change goes straight into `##Finished.`**, worded as what is now true; never add it to unfinished first.
- **Keep each item as short as the others**, one or two short sentences. The how and why go in the changelog, `DIVERGENCES.md` or memory.
- After editing, check the line endings with a byte check.
- Move an item to `##Finished.` only when the dev confirms it is done, not when code lands ([[feedback_dont_run_or_build]]).
- On 2026-10-02 the file is empty. When the first item goes in, write both headings.
