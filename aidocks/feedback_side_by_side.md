---
name: feedback_side_by_side
description: "Every gameplay claim is checked side by side against the binary: name the instruction address and the port line, never infer. Say plainly what is verified and what is not."
metadata:
  type: feedback
---

**Check gameplay side by side with the original, and never guess.** The dev plays by ear and relies on the port matching the original exactly, except for divergences they chose.

**Why:** A standing rule the dev carries across their projects ("make sure you are checking things match side by side. no guessing"). Readings of a disassembly are easy to get wrong, and a guess can put in behaviour the original never had. On 2026-10-01 Claude first described Inside The Cave as a game with no killing, from its tutorial line alone, then had to correct it once the torch collision handlers and the monsters' death sprites were noticed.

**How to apply:**
- For each step of a behaviour, find the instruction in the binary ([[project_binary_analysis_notes]]) and the matching line in the port, and compare the constants, the order, the delays and the guards.
- In the report, separate what the bytes verified from what is inferred from names and strings alone. Selector and asset names suggest; only the code proves.
- Don't claim a heard result matches unless the dev heard it.
- Treat a change that alters loudness or position as a divergence, and check it against what the original actually produced.
- Add a test that pins the verified behaviour, timed against the real clock when timing is the point.
