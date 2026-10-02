---
name: feedback_questions_are_checks
description: "A question about the original or the port is a check - answer it in chat, don't edit code, comments or docs off the back of it."
metadata:
  node_type: memory
  type: feedback
---

When the dev asks a question about the original or the port, or states a fact in reply, answer it in chat and change nothing. Findings from the check, even a correction to the docs, are reported and offered, not written.

**Why:** A standing rule the dev carries across their projects: a question was once taken as a request, docstrings and notes were rewritten off the back of it, and the dev had it all reverted ("it was just a check, not something to be modified in terms of docs").

**How to apply:** Only edit files when the dev asks for a change. If a check turns up something wrong in the docs, mention it in one line and let the dev decide.
