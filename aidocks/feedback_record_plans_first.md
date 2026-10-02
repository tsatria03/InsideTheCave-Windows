---
name: feedback_record_plans_first
description: "Write an agreed plan into its own aidocks note before building it; commit the plan alone first and never push it until the whole thing is built and tested; mark it finished only once the dev says it works."
metadata:
  type: feedback
---

**Record a plan in aidocks before starting on it.** Once the dev and Claude have agreed a plan, it goes into its own note, `aidocks/project_<name>_plan.md`, with a pointer in `MEMORY.md`, before any code is written. The note keeps every decision, the dev's own words where they settle something, and what is left out and why.

**Mark it finished only when the dev says it works.** Its status stays "planned" while waiting for the go-ahead, then "built, not yet confirmed" once the code lands, and becomes "finished" only when the dev confirms it works, in that same note and its `MEMORY.md` line. Code landing, or tests passing, is not enough.

**Why:** A standing rule the dev carries across their projects: a plan agreed in conversation is lost when the context is compacted, and a big change built from memory drifts from what was agreed.

**How to apply:**
- A plan big enough to need questions answered gets a note before its first edit. A one-line fix does not need one.
- If the plan changes while it is being built, update the note first, then the code.
- Update the note as each part lands, and say which parts are built and which are waiting.
- A finished plan stays as a record. Don't delete it.
- **Commit the plan first, on its own, and never push it until the whole thing is built and tested.** The code follows as a separate commit once the dev has tested it and it is marked finished; then both are pushed together.
