---
name: project_dev_tasks
description: "The developer-side task list: work on the repository, the tools, the analysis, the tests, the build and the docs that a player never sees. Open tasks first, then finished ones, newest first."
metadata:
  type: project
---

`docks/todo list.txt` holds only what a player notices ([[feedback_todo_list_format]]). Everything else that needs doing, or has been done, lives here, in the same style: one plain sentence per line, newest first.

**How to apply:** a new developer task goes at the top of Open. When it lands and the dev confirms, it moves to the top of Finished. A task that changes what a player hears or sees belongs in `todo list.txt` instead, and in the changelog once done ([[feedback_changelog]]). Debug mode is developer-facing, so its lines live here.

## Open

- Make the first real build and release with compiler.py and releaser.py once the port has an entry script; they were adapted on 2026-10-02 but cannot build yet ([[project_build_scripts]]).
- Add tests/case/release.py for the releaser's version numbering, changelog filing and archive names.
- Write README.md for developers and docks/readme.txt for players once there is a game to describe.

## Finished

- The whole game is disassembled: arm64 tools in tools/, all 575 functions listed with coverage proved, the strings, scenes and storyboards decoded, and GAME_STRUCTURE.md written from the code ([[project_disassembly_plan]]).
- The French, Russian and Chinese tutorial lines are found, in the binary's UTF-16 strings, spoken by GameScene.tutorial.
- The boss the 2016 update described is not in version 2.32: the full disassembly has no boss anywhere.

- Project notes for AI-assisted work are set up in CLAUDE.md and the aidocks folder.
- The original's makers are known: Iago Barbosa, Juliana Barros and Victor Leal at BEPiD Recife, from a 2016 MacMagazine article the dev read and confirmed.
