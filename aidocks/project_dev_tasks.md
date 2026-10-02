---
name: project_dev_tasks
description: "The developer-side task list: work on the repository, the tools, the analysis, the tests, the build and the docs that a player never sees. Open tasks first, then finished ones, newest first."
metadata:
  type: project
---

`docks/todo list.txt` holds only what a player notices ([[feedback_todo_list_format]]). Everything else that needs doing, or has been done, lives here, in the same style: one plain sentence per line, newest first.

**How to apply:** a new developer task goes at the top of Open. When it lands and the dev confirms, it moves to the top of Finished. A task that changes what a player hears or sees belongs in `todo list.txt` instead, and in the changelog once done ([[feedback_changelog]]). Debug mode is developer-facing, so its lines live here.

## Open

- Adapt compiler.py and releaser.py to Inside The Cave, once the dev gives the go-ahead ([[project_build_scripts]]).
- Fill in GAME_STRUCTURE.md from the code, with addresses, starting with GameScene: the lanes, the spawning, the speeds, the torch and light, the coins, the scenarios and the collisions.
- Build arm64 versions of the Mach-O and disassembly tools in tools/, and write their output to analysis/ ([[project_binary_analysis_notes]]).
- Put the game's arm64 binary in analysis/bin, so the analysis can be redone from the repository alone.
- Find the boss the 2016 update added: no string names it, so look for it in GameScene's spawning code ([[project_provenance]], GAME_STRUCTURE.md section 0).
- Find the French, Russian and Chinese narrations: only English, Spanish and Portuguese tutorial text has been found. Look in the UTF-16 __ustring section, the storyboards and Assets.car.
- Write README.md for developers and docks/readme.txt for players once there is a game to describe.

## Finished

- Project notes for AI-assisted work are set up in CLAUDE.md and the aidocks folder.
- The original's makers are known: Iago Barbosa, Juliana Barros and Victor Leal at BEPiD Recife, from a 2016 MacMagazine article the dev read and confirmed.
