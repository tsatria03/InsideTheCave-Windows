---
name: feedback_no_question_pickers
description: "Ask questions as plain text in the reply, never through the multiple-choice picker tool (AskUserQuestion). The dev reads by screen reader."
metadata:
  node_type: memory
  type: feedback
---

**Never ask the dev anything through the question picker** (the `AskUserQuestion` tool, which draws a menu of options the dev has to move through). Ask in the reply instead, in plain sentences.

**Why:** The dev reads by screen reader, and a picker is a separate control to navigate rather than text they can read straight through ([[user_screen_reader]]). It is a standing rule the dev carries across their projects.

**How to apply:**
- Put the question at the end of the reply, in a short numbered list when there is more than one.
- Say which answer is recommended and why, in one line each, so a plain "the first one" is enough to answer.
- **When there are several questions, ask one at a time** (the dev, 2026-10-02: "Ask one question at a time."), each with its recommendation, and the next only once it is answered. A plan note may still list them all; the reply asks one.
- Keep code or layout samples in a fenced block in the reply.
