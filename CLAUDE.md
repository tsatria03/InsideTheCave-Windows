# CLAUDE.md

This file guides Claude Code when it works in this repository. **It is a lean dispatcher.** It says what the project is and how it is laid out, then points to focused memory files (`[[name]]`) for the detail. When you start work in an area, read its linked memory first.

**Memory location:** all memory files (the `[[name]]` links and the `MEMORY.md` index) live in the repo's **`aidocks/`** folder, as `aidocks/<name>.md`. Read memory from there and write new or updated memory there, never to the `~/.claude` memory store. `aidocks/MEMORY.md` is the index, so add a one-line pointer there for every new memory. Keep this file under 40,000 characters and move detail into memory ([[feedback_memory_in_aidocks]]).

## What this is

A Windows port of **Inside The Cave** (`InsideTheCaveBD` 2.32), an iOS audio game made with Swift 3 and SpriteKit by Iago Barbosa, Juliana Barros and Victor Leal at BEPiD Recife in 2016, and no longer on the App Store. You run through a dark cave in three lanes. When you hear a monster roar, you move to another lane, and you pick up torches and coins along the way. A thrown torch kills a monster in your lane; a bat it hits only dodges, as in the original (0x10001356c, `DIVERGENCES.md`).

There is no source code for the original. The port is **recovered from the arm64 binary** `game/InsideTheCave` and rewritten **entirely in Python** ([[project_python_only]]), each module mirroring one original class and citing the binary addresses it came from. It is a solo port by tsatria03 ([[project_provenance]]).

**State on 2026-10-02:** the whole game is disassembled ([[project_disassembly_plan]], finished): the tools are in `tools/`, every function is listed in `analysis/disasm/`, and `aidocks/GAME_STRUCTURE.md` describes the game from the code, with addresses. The port is in phases ([[project_port_plan]]): 1, the platform layer, 2, the SpriteKit stand-in, 3, the game itself (`GameScene` and `GameViewController`), 4, the screens (warning, menu, pause menu, result, ranking), and 5, building and releasing (a test build compiled and released by the dev, and working), are finished and confirmed by the dev.

## Layout

- **`game/`**: the original app bundle, unpacked: the `InsideTheCave` executable, the sounds, sorted by the dev into `game/sounds/used/` (17: the 12 the 2.32 binary names, plus the menu music, two footstep loops, the torch burning out and the coins' ding, from the older versions) and `game/sounds/unused/` (the 10 left from the older versions), all 16-bit PCM WAV under their original base names, except `SC` and `dash`, renamed `game-music` and `lane` (`paths.RENAMED`); the binary also asks for `.aiff` and `.mp3` names, so the port looks a sound up by its base name, in `used/` first, the fonts, the `.sks` scenes, `Assets.car`, the compiled storyboards, `Frameworks/` (the Swift runtime) and `Info.plist`. The port never writes to it. Don't move, rename, convert or delete sound files unless the dev asks.
- **`insidethecave/`**: the Python package. `paths.py` (the game folder, sounds by base name, the save in `%APPDATA%\InsideTheCave`); `platform/` (`openal.py`, `runloop.py` for the NSTimers, `defaults.py` for `save.json` and `settings.json`, `volume.py`, `speech.py` with the SAPI 5 `TutorialVoice`, `language.py`, `keymap.py` for `keys.json`, `sound.py`); `ui/` (the F1 `keybind_screen.py`, `focus.py`, `game_input.py` for the game's keys, `rows.py` for a screen of rows, `pause_menu.py`); `scene/`, the SpriteKit stand-in (phase 2: `node.py`, `actions.py`, `physics.py`, `audio.py`, `scene.py`, and `image_sizes.py`, generated from `game/Assets.car` by `tools/assets.py`); `game/`, one module per original class (phase 3: `game_scene.py`, `game_view_controller.py`; phase 4: `warning_view_controller.py`, `home_screen_view_controller.py`, `result_view_controller.py`, `ranking_view_controller.py`).
- **`InsideTheCave.py`**: the entry point, the window of text lines, the frame loop, and the screen loop standing in for the storyboard: warning, menu, game, result, ranking. `--stage` starts on a game.
- **`analysis/`**: `bin/InsideTheCave_arm64` (a copy of the binary), `data/` (the classes, every function's name, every string, the decoded scenes and storyboards) and `disasm/dz_<Class>.txt` (every function, annotated).
- **`tools/`**: the arm64 Mach-O and disassembly tools that make `analysis/`, standard library plus `capstone` for the disassembly; `tools/README.md` says how to rerun them ([[project_binary_analysis_notes]]).
- **`tests/`**: `tests/case/` for the automated tests, `tests/interact/` for the by-ear tools ([[project_tests_layout]]). `tests/case/` holds the tests; `tests/interact/platform_check.py`, `scene_check.py`, `stage_chooser.py` and `screens_check.py` let the dev hear phases 1, 2, 3 and 4, `torch_check.py`, `coin_check.py` and `bat_check.py` the torch, the coins and the bats, and `speed_check.py` the game at any speed. Write a by-ear tool whenever something can be heard ([[feedback_interactive_tests]]). Every test must keep off the real save and be silent ([[project_safe_test_run]]).
- **`vendor/`**: `soft_oal.dll` (OpenAL Soft) and `nvdaControllerClient64.dll`, with their licenses. The port is Windows only (the dev, 2026-10-02: no Linux build), and the Linux `libopenal.so.1` was removed the same day.
- **`docks/`**: the documents a player reads, which a build ships in a `docks` folder beside the executable: `readme.txt`, `changelog.txt`, `credits.txt` and `todo list.txt`. Since phase 3 the changelog has its first `unrelease:` block and the todo list its items; the readme (how to play) and credits (makers, licenses) were written on 2026-10-02 ([[project_player_readme]]): keep the readme in step with the game.
- **`aidocks/`**: the memory notes, plus three developer references: `PORTING_STATUS.md`, `DIVERGENCES.md` and `GAME_STRUCTURE.md`.
- **`compiler.py`** and **`releaser.py`**: the PyInstaller build script and the release script, adapted to this game on 2026-10-02, and run by the dev, who has built and released the game with them. The compiler builds `dist\InsideTheCave-Windows` around `InsideTheCave.exe`, shipping only `game\sounds\` (both `used` and `unused`) from the bundle ([[project_build_scripts]]).
- **`VERSION`**: the date version, `YY.MM.DD-N`.
- **`New File.txt`** at the root is the dev's private scratchpad. It is gitignored; never read, edit, flag or delete it.
- **`user/`** is gitignored private reference material, including the reference port the dev pointed to as an example of how a port is done. Read it, but never edit it, and never name the games in it in this repo's files ([[feedback_no_other_games]]).

## Running and building

**The dev runs and builds, not Claude.** Never build unless told. The tests may be run without asking, always the safe way, but only the scripts that cover the Python files changed; the full suite runs only when the dev asks, or by itself every 10 to 20 commits ([[feedback_git_commits]]). Ask before running the game, `compiler.py`, `releaser.py`, or anything else that executes game code or speaks ([[feedback_dont_run_or_build]]).

The game needs 64-bit Python 3.12 or newer, `pygame` (not `pygame-ce`) and `prismatoid`: `pip install -r requirements.txt`. `python InsideTheCave.py` plays (`--debug`: nothing can kill you; `--game PATH`; `-v` logs to the console).

## Porting rules

- **Disassemble the whole game before porting anything** (the dev, 2026-10-02). Done: [[project_disassembly_plan]] was finished and confirmed the same day. Port from `GAME_STRUCTURE.md` and the listings in `analysis/disasm/`, and tick each function off in `PORTING_STATUS.md`.
- Port from the binary, and cite the address in the code. Record every deliberate difference in `aidocks/DIVERGENCES.md`.
- Addresses are VM addresses: **file offset = address - 0x100000000** ([[project_binary_analysis_notes]]). Swift symbols are stripped, so the game's own calls are plain branches to addresses; the Objective-C selectors and the strings are the anchors.
- Before "reproducing" anything that hinges on one branch or constant, check the raw instructions. Say what is verified and what is inferred ([[feedback_side_by_side]]).
- Changing tested behaviour means updating its test in the same change.

## Where the detail lives

- **What the game is, as far as it is known**: `aidocks/GAME_STRUCTURE.md`.
- **Reading the binary**: [[project_binary_analysis_notes]].
- **Running the tests safely**: [[project_safe_test_run]].
- **The build scripts**: [[project_build_scripts]].
- **The task list** (`docks/todo list.txt`, players only) and how to write in it: [[feedback_todo_list_format]]. Developer tasks are in [[project_dev_tasks]].
- **The changelog** (`docks/changelog.txt`): every player-facing fix or enhancement adds a line at the top of the `unrelease:` block in the same commit ([[feedback_changelog]]).
- **Plans**: an agreed plan goes into its own aidocks note before any code ([[feedback_record_plans_first]]).
- **Committing and pushing**: [[feedback_git_commits]]. Name people by GitHub username only: [[feedback_use_github_usernames]].
- **Who you're working with**: [[user_screen_reader]]. The dev uses NVDA, so prefer lists and short lines, ask questions in plain text ([[feedback_no_question_pickers]]), and never make noise from tools.
- **A question is a check**, answered in chat, not a request for edits ([[feedback_questions_are_checks]]). Never record individual releases ([[feedback_no_release_records]]).

`CLAUDE.md` and `aidocks/` are committed, not gitignored.
