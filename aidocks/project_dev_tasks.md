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
- Disassemble the whole game before any porting: the arm64 tools, every function listed, coverage proved, the scenes, storyboards and strings decoded, and GAME_STRUCTURE.md verified from it ([[project_disassembly_plan]]).
- Find the boss the 2016 update added: no string names it, so look for it in GameScene's spawning code ([[project_provenance]], GAME_STRUCTURE.md section 0).
- Find the French, Russian and Chinese narrations: only English, Spanish and Portuguese tutorial text has been found. Look in the UTF-16 __ustring section, the storyboards and Assets.car.
- Write README.md for developers and docks/readme.txt for players once there is a game to describe.

## Finished

- Project notes for AI-assisted work are set up in CLAUDE.md and the aidocks folder.
- The original's makers are known: Iago Barbosa, Juliana Barros and Victor Leal at BEPiD Recife, from a 2016 MacMagazine article the dev read and confirmed.
