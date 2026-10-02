# CLAUDE.md

This file guides Claude Code when it works in this repository. **It is a lean dispatcher.** It says what the project is and how it is laid out, then points to focused memory files (`[[name]]`) for the detail. When you start work in an area, read its linked memory first.

**Memory location:** all memory files (the `[[name]]` links and the `MEMORY.md` index) live in the repo's **`aidocks/`** folder, as `aidocks/<name>.md`. Read memory from there and write new or updated memory there, never to the `~/.claude` memory store. `aidocks/MEMORY.md` is the index, so add a one-line pointer there for every new memory. Keep this file under 40,000 characters and move detail into memory ([[feedback_memory_in_aidocks]]).

## What this is

A Windows port of **Inside The Cave** (`InsideTheCaveBD` 2.32), an iOS audio game made with Swift 3 and SpriteKit by Iago Barbosa, Juliana Barros and Victor Leal at BEPiD Recife in 2016, and no longer on the App Store. You run through a dark cave in three lanes. When you hear a monster roar, you move to another lane, and you pick up torches and coins along the way. Thrown torches appear to kill bats and monsters, but that is not yet verified from the code ([[feedback_side_by_side]]).

There is no source code for the original. The port is **recovered from the arm64 binary** `game/InsideTheCave` and rewritten **entirely in Python** ([[project_python_only]]), each module mirroring one original class and citing the binary addresses it came from. It is a solo port by tsatria03 ([[project_provenance]]).

**State on 2026-10-02:** nothing is ported yet. The repository holds the original app bundle, the vendored libraries, empty folders for the package, tests, tools and analysis, and these notes.

## Layout

- **`game/`**: the original app bundle, unpacked: the `InsideTheCave` executable, the sounds (12 WAV, MP3 and AIFF files, moved by the dev into `game/sounds/` under their original names), the fonts, the `.sks` scenes, `Assets.car`, the compiled storyboards, `Frameworks/` (the Swift runtime) and `Info.plist`. The port never writes to it. Don't move, rename, convert or delete sound files unless the dev asks.
- **`insidethecave/`**: the Python package, empty so far. It will hold `paths.py`, `game/` (one module per original class), `platform/` and `ui/`.
- **`analysis/`**: empty so far; for the binary and its disassembly.
- **`tools/`**: empty so far; for the arm64 Mach-O and disassembly tools ([[project_binary_analysis_notes]]).
- **`tests/`**: `tests/case/` for the automated tests, `tests/interact/` for the by-ear tools ([[project_tests_layout]]). Both are empty. Every test must keep off the real save and be silent ([[project_safe_test_run]]).
- **`vendor/`**: `soft_oal.dll` (OpenAL Soft) and `nvdaControllerClient64.dll`, with their licenses. The port is Windows only (the dev, 2026-10-02: no Linux build), so `libopenal.so.1` there is unused.
- **`docks/`**: the documents a player reads, which a build ships in a `docks` folder beside the executable: `readme.txt`, `changelog.txt`, `credits.txt` and `todo list.txt`. All are empty so far.
- **`aidocks/`**: the memory notes, plus three developer references: `PORTING_STATUS.md`, `DIVERGENCES.md` and `GAME_STRUCTURE.md`.
- **`compiler.py`** and **`releaser.py`**: the PyInstaller build script and the release script, adapted to this game on 2026-10-02 but not yet run. The compiler builds `dist\InsideTheCave-Windows` around `InsideTheCave.exe`, shipping only `game\sounds\` from the bundle, and refuses to build until `InsideTheCave.py` and the `insidethecave` package exist ([[project_build_scripts]]).
- **`VERSION`**: the date version, `YY.MM.DD-N`.
- **`New File.txt`** at the root is the dev's private scratchpad. It is gitignored; never read, edit, flag or delete it.
- **`user/`** is gitignored private reference material, including the reference port the dev pointed to as an example of how a port is done. Read it, but never edit it, and never name the games in it in this repo's files ([[feedback_no_other_games]]).

## Running and building

**The dev runs and builds, not Claude.** Never build unless told. The tests may be run without asking, always the safe way, but only the scripts that cover the Python files changed; the full suite runs only when the dev asks. Ask before running the game, `compiler.py`, `releaser.py`, or anything else that executes game code or speaks ([[feedback_dont_run_or_build]]).

The game will need 64-bit Python 3.12 or newer, `pygame` (not `pygame-ce`) and `prismatoid`: `pip install -r requirements.txt`.

## Porting rules

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
