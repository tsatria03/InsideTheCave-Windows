---
name: user_screen_reader
description: "The dev works with NVDA running and reviews output by screen reader; prefer lists and short lines over wide tables, and never make noise or speak through NVDA from tools or tests."
metadata:
  node_type: memory
  type: user
---

The dev, tsatria03, builds audio-only games for blind players and works with NVDA running. They review changes through a screen reader, and lines over 1024 characters get split mid-thought.

**How to apply:**
- In replies and docs, prefer headings and bulleted lists to wide tables, and keep lines reasonably short.
- Don't run anything that plays audio or speaks through NVDA without silencing it first; see [[project_safe_test_run]].
- When recommending game changes, weigh how they sound to a player who can't see the window. The pygame window's text is secondary; the sounds and speech are the real interface.
- Inside The Cave was built for sighted and VoiceOver players alike (it calls `UIAccessibilityIsVoiceOverRunning`), so the port's job is to make everything it shows on screen reachable by ear.
