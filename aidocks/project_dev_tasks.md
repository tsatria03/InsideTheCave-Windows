---
name: project_dev_tasks
description: "The developer-side task list: work on the repository, the tools, the analysis, the tests, the build and the docs that a player never sees. Open tasks first, then finished ones, newest first."
metadata:
  type: project
---

`docks/todo list.txt` holds only what a player notices ([[feedback_todo_list_format]]). Everything else that needs doing, or has been done, lives here, in the same style: one plain sentence per line, newest first.

**How to apply:** a new developer task goes at the top of Open. When it lands and the dev confirms, it moves to the top of Finished. A task that changes what a player hears or sees belongs in `todo list.txt` instead, and in the changelog once done ([[feedback_changelog]]). Debug mode is developer-facing, so its lines live here.

## Open

- Add tests/case/release.py for the releaser's version numbering, changelog filing and archive names.

## Finished

- By-ear tools for the third release: tests/interact/torch_check.py, coin_check.py and speed_check.py ([[project_tests_layout]]).
- README.md for developers and docks/readme.txt and credits.txt for players are written, and kept in step with the game ([[project_player_readme]]).
- compiler.py and releaser.py build and release the game: the dev compiled and released a test build, which worked ([[project_build_scripts]]).
- The game is ported, in the five phases of [[project_port_plan]], every question answered and every phase confirmed by the dev.
- The whole game is disassembled: arm64 tools in tools/, all 575 functions listed with coverage proved, the strings, scenes and storyboards decoded, and GAME_STRUCTURE.md written from the code ([[project_disassembly_plan]]).
- The French, Russian and Chinese tutorial lines are found, in the binary's UTF-16 strings, spoken by GameScene.tutorial.
- The boss the 2016 update described is not in version 2.32: the full disassembly has no boss anywhere.

- Project notes for AI-assisted work are set up in CLAUDE.md and the aidocks folder.
- The original's makers are known: Iago Barbosa, Juliana Barros and Victor Leal at BEPiD Recife, from a 2016 MacMagazine article the dev read and confirmed.
