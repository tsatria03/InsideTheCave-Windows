---
name: feedback_changelog
description: "Whenever a change players will notice lands (a bug fix or an enhancement), add a plain sentence at the top of the unrelease: block in docks/changelog.txt, in the same commit; entries read newest first. LF, no BOM, one sentence per line, no markdown; the releaser files the block under the version."
metadata:
  node_type: memory
  type: feedback
---

**Keep `docks/changelog.txt` up to date as game changes land.** Every commit that fixes a bug or adds an enhancement a player will notice also adds a line under `unrelease:` at the top of the changelog. It ships beside the game in the build's `docks` folder.

**Why:** A standing rule the dev carries across their projects; a changelog left for later is missed. On 2026-10-02 the file is still empty, since nothing has been ported yet.

**How to apply:**
- **Format.** This is what the build scripts' changelog parser reads:
  - A heading is one word ending in a colon, on a line of its own: `unrelease:` or a version like `26.10.02-1:`.
  - Every other line is an entry: one plain sentence or two, with no bullets, numbers or markdown.
  - A blank line separates one heading's block from the next.
- **LF, no BOM.** Match the endings the file has when you edit it, and check afterwards with a byte check.
- **New lines go at the top of the `unrelease:` block**, straight under the heading, so the block reads newest first. If there is no `unrelease:` heading, add it at the very top, followed by a blank line before the newest version.
- **Only what a player notices:** fixes, enhancements, removed features, new sounds or files they will see. Debug mode, notes, docs, tests, refactors and build-script internals never go here, unless they change what ships. Bugs that are only found or planned stay in `todo list.txt`.
- **Wording.** Write for a player, in the style of the todo list's finished section: say what is now true, and avoid contractions.
- **Headings stay bare:** date versions like `26.10.02-1:` (year, month, day, that day's build) and `unrelease:` for changes not yet released. Don't propose "Version ..." or "Unreleased:" headings unless asked.
- **How big a release is.** A release aims for 50 to 100 entries. **100 is a hard ceiling, and 5 a hard floor**; the releaser enforces both, and asks "Release anyway?" for 1 to 4, the dev's override. Headings are never counted; count the lines under `unrelease:` from the file each time, never from a running tally. Say so when the block nears 100, and when it is still under 5.
- **Never file the block under a version or run a build yourself** ([[feedback_dont_run_or_build]]). Never edit an entry that already has a version heading.
- **No credit lines.** Entries say what changed, not who changed it.
- The first release of a port the size of this one may well be the port itself; when the game first becomes playable, ask the dev how they want that first block worded rather than listing every ported method.
