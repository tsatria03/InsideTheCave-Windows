# InsideTheCave-Windows memory index

The `[[name]]` links in `CLAUDE.md` and across these memories resolve to `aidocks/<name>.md`. Add a one-line pointer here for every new memory. "Memory" or "memories" always means this folder, never the `~/.claude` store.

## Reference documents (not memory notes)
- [Porting status](PORTING_STATUS.md), [Divergences](DIVERGENCES.md) and [Game structure](GAME_STRUCTURE.md): the three developer references. What is ported, where the port differs from the original, and the game's mechanism as read from the binary. On 2026-10-02 nothing is ported; the game structure is read from the full disassembly, with addresses.
- The player documents, `readme.txt`, `changelog.txt` and `todo list.txt`, live in the repo's `docks/` folder; all three are empty on 2026-10-02.

## Project: what the port is and how to work on it
- [Provenance](project_provenance.md): the original was made by Iago Barbosa, Juliana Barros and Victor Leal at BEPiD Recife (MacMagazine, 2016-09-06, confirmed by the dev); it is no longer on the App Store. The port is solo, by tsatria03, with no contributors now or planned.
- [Python only](project_python_only.md): pygame, OpenAL Soft through ctypes, NVDA or Prism; the insidethecave/ package with game, platform and ui. Windows only: no Linux build (the dev has no WSL).
- [Binary analysis notes](project_binary_analysis_notes.md): a thin arm64 Mach-O, unencrypted, Swift 3 with stripped symbols. File offset = address - 0x100000000. The section map, and why 32-bit Thumb tooling will not work unchanged.
- [Disassembly plan](project_disassembly_plan.md): FINISHED 2026-10-02, confirmed by the dev. The whole game is disassembled before any porting: arm64 tools in tools/ (capstone), all 575 functions listed in analysis/disasm with coverage proved, the scenes, storyboards and strings decoded, GAME_STRUCTURE.md rewritten from the code with addresses, PORTING_STATUS.md listing every function. Porting may now start.
- [Port plan](project_port_plan.md): phase 1 (the platform) FINISHED 2026-10-02, 80 tests passing and confirmed by ear with tests/interact/platform_check.py; phase 2 (the SpriteKit stand-in, insidethecave/scene, image sizes from Assets.car) BUILT 2026-10-02, 22 tests passing, no sound above 1.0 (the dev), waiting for the dev's ear with tests/interact/scene_check.py; phases 3 to 5 planned, each waiting for the dev's go. All 14 questions answered (asked one at a time). Decided: 1 (no decoder needed, the sounds are WAV), 2 (sounds mono and placed in their lanes), 3 (a spoken "Torch low" added to the torch's sounds), 4 (the spawn chain fixed, a blank name saved as "unnamed player", bats stay unkillable, coins jingle from their lane, torches on the path stay silent, contacts work in either order, moving before the start kept, no throw after death), 5 (the proposed keys; Escape, P and leaving the window pause), 6 (the tutorial sentence in a SAPI 5 voice at rate 0.5, then key hints through the screen reader), 7 (Windows's display language, English fallback), 8 (the name field starts empty, "Insert name" spoken), 9 (no online scores, local top five only), 10 (settled with 4), 11 (sizes read from Assets.car, the roar sensor 128 by 128, timing by ear), 12 (volume keys and a --debug mode), 13 (a plain window of text lines), 14 (no spider or boss: the port is 2.32 as it is). Five phases: the platform, a SpriteKit stand-in (nodes, actions, contacts, positioned sound), the game scene, the screens, building and releasing.
- [Build scripts](project_build_scripts.md): compiler.py and releaser.py adapted 2026-10-02 at the dev's go-ahead; built, not yet confirmed. The compiler finds game\ and game\sounds itself, ships only the sounds, and refuses to build until InsideTheCave.py and the package exist.
- [Safe test run](project_safe_test_run.md): the design every test follows from the first one: a _scratch_save helper, silent, off the real save, headless. Plain scripts, run in PowerShell, skipping _*.py.
- [Tests layout](project_tests_layout.md): tests/case for the automated tests, tests/interact for the by-ear tools Claude never runs; platform_check.py hears phase 1.
- [Developer tasks](project_dev_tasks.md): repository, tool, analysis, test, build and docs tasks, open and finished.

## Feedback: how the dev wants you to work
- [Memory in aidocks](feedback_memory_in_aidocks.md): all memory goes in aidocks/ with this index, and CLAUDE.md is a lean dispatcher under 40,000 characters.
- [No other games](feedback_no_other_games.md): never name the dev's other games in this repo's files; the reference port is "the reference port in the gitignored user/ folder".
- [Don't run or build](feedback_dont_run_or_build.md): never build unless told. Tests may be run without asking, the safe way, only those covering what changed; ask before running the game or any script that executes game code or speaks.
- [Git commits and pushes](feedback_git_commits.md): one commit per fix; commit only when asked, and push only when told; commits pile up locally until then. Every 10 to 20 commits, run the whole tests/case suite without asking. Nothing comes in from elsewhere, so no routine fetch before a push. Never pull, merge or rebase without a go-ahead; history rewrites need one too. Use git commit -F, never hide git's errors.
- [GitHub usernames](feedback_use_github_usernames.md): the dev is tsatria03; no co-author lines for people.
- [Changelog](feedback_changelog.md): every player-facing change adds a plain sentence at the top of unrelease: in docks/changelog.txt, in the same commit. 5 to 100 entries a release; never file it or build yourself.
- [Todo list format](feedback_todo_list_format.md): ##Unfinished. and ##Finished., one plain sentence per line, new items after the heading's blank line, players only, LF, no markdown.
- [No release records](feedback_no_release_records.md): never record individual releases in aidocks or README.md.
- [Record plans first](feedback_record_plans_first.md): an agreed plan gets its own note before any code, committed alone and pushed only with the finished work; finished only when the dev says it works.
- [Side by side, no guessing](feedback_side_by_side.md): every gameplay claim checked against the binary by address and the port by line; say what is verified and what is inferred.
- [Questions are checks](feedback_questions_are_checks.md): a question from the dev gets an answer in chat, not edits.
- [Interactive tests](feedback_interactive_tests.md): whenever something can be heard or spoken, add a by-ear tool in tests/interact (its own window and save; Alt+F4 quits at any moment); the dev runs it, never Claude.
- [No question pickers](feedback_no_question_pickers.md): ask in plain text at the end of the reply, never through the picker tool.

## User
- [Screen reader](user_screen_reader.md): the dev works with NVDA running. Prefer lists and short lines to wide tables, and never make noise or speak through NVDA from tools or tests.
