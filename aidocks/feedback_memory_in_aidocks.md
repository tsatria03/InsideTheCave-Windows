---
name: feedback_memory_in_aidocks
description: "All memory lives in the repo's aidocks/ folder with a MEMORY.md index; CLAUDE.md is a lean dispatcher pointing at it. Never write to the ~/.claude memory store."
metadata:
  node_type: memory
  type: feedback
---

Write every memory for this project into `aidocks/` at the repo root, never into the `~/.claude` memory store. `aidocks/MEMORY.md` is the index: add a one-line pointer there for every new memory, grouped by section. `CLAUDE.md` at the repo root is a lean dispatcher (under 40,000 characters) that orients and then points at memories with `[[name]]` links, which resolve to `aidocks/<name>.md`.

**Why:** The dev asked for this on 2026-10-01, when the repo was set up: "please use the aidocks folder as your memory storage for this repo." Memory travels with the repo that way.

**How to apply:**
- Name files `feedback_<slug>.md`, `project_<slug>.md` or `user_<slug>.md`, and make the `name` in the frontmatter the same as the file name, so a `[[name]]` link always finds its file.
- Use frontmatter with `name`, a quoted `description`, and `metadata: {node_type: memory, type: ...}`. For feedback and project memories, follow the fact with **Why:** and **How to apply:** lines.
- When a `CLAUDE.md` section grows past a few lines of real detail, move it into a memory and leave a `[[name]]` pointer.
- `CLAUDE.md` and `aidocks/` are committed, not gitignored.
- **"The docks" can mean either folder.** `aidocks/` holds these notes; `docks/` holds the player-facing files. On 2026-10-02 the dev said "you can update the docks" and meant `aidocks/`. When it is unclear, take it as `aidocks/`, say so, and leave `docks/` alone. The player-facing files are not to be written until the dev says it is time ("We do not need to update the player facing docks yet").
- A note first written to the `~/.claude` store on 2026-10-01 was moved here on 2026-10-02 and deleted there.
