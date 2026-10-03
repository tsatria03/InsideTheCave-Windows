---
name: project_build_scripts
description: "compiler.py and releaser.py were adapted to Inside The Cave on 2026-10-02 at the dev's go-ahead, and FINISHED the same day: the dev built and released a test build with them and it worked. The compiler finds game\\ and game\\sounds itself, ships every sound (used and unused, the dev's choice), and refuses to build while InsideTheCave.py or the insidethecave package is missing."
metadata:
  type: project
---

**Status: FINISHED, confirmed by the dev (2026-10-02).** The dev gave the go-ahead that day ("Modify the build scripts."), after first asking for them to be left alone until then. Once the port had its entry script and phase 4 was in, the dev built and released a test build with them, and it worked: "You can mark the compiler/releaser thing as finished because I compiled and released a test build of the game, and it worked. The release has been deleted from github releases." The test release left nothing in the repository (no release commit, no tag, `VERSION` and the changelog's `unrelease:` block as they were). Never run either script yourself ([[feedback_dont_run_or_build]]).

Both came from the reference port's scripts in the gitignored `user/` folder ([[feedback_no_other_games]]).

## What the compiler does
A numbered menu, or flags, around PyInstaller: a folder build, or with `--embed` one exe holding the sounds and data; also `--clean`, `--console`, `--onefile`, `--no-game` and `--dry-run`. Every build lands in `dist\InsideTheCave-Windows` around `InsideTheCave.exe`. It ships `docks\` (readme, changelog, credits, todo list) as a `docks` folder beside the executable with `VERSION` and `license.txt`, and puts the third-party licenses (OpenAL Soft, the NVDA client, Prism, pygame) inside the executable as `licenses\`. It never zips and never changes the repository.

## What the releaser does
Check, then set the date version `YY.MM.DD-N` in `VERSION`, file `unrelease:` in `docks/changelog.txt` under it, build through the compiler, zip (`InsideTheCave-Win-<version>.zip`, extracting to `InsideTheCave-Windows`), commit "Release <version>", tag `V<version>`, and upload as the release "InsideTheCave V<version>" through `gh`. It enforces the 5 to 100 entry limits ([[feedback_changelog]]), and never moves a tag or replaces a release asset.

## What changed from the reference scripts (2026-10-02)
- **Names:** `NAME = 'InsideTheCave'`, `ENTRY = 'InsideTheCave.py'`, a new `PACKAGE = 'insidethecave'`, the build folders, zip names, release title, menu titles and examples (`26.10.02-1`).
- **Finding the game's data:** the reference compiler asked its port's `paths.py`. This one finds it itself (`game_source()`): the folder named by `INSIDETHECAVE_GAME`, else the repository's `game\`, whichever holds a `sounds` folder. So a build never depends on the port's code importing, and works before the port exists. `insidethecave/paths.py` should look in the same places, and in `game\sounds` beside the executable when frozen.
- **What ships from the bundle:** only `game\sounds\`, whole (`SOUNDS`, `sound_files()`), as `game\sounds` beside the executable, or inside it with `--embed`. `GAME_FILES` (top-folder files) is empty: add a pattern once the port reads one, such as the `.sks` scenes or `Info.plist`. Never shipped: the iOS executable, `_CodeSignature`, `Frameworks\`, `Assets.car`, the fonts, the storyboards and the icons.
- **Sounds counted** as `.wav`, `.mp3`, `.aiff`, `.aif` and `.ogg`. Since the dev's sort of 2026-10-02 the repository's are all WAV, in `game\sounds\used` (12 at first; 17 by the third release's work: the menu music, `Running_On_Rocks` made into two footstep loops, `tocha_acende` for the torch burning out, and `coin` for the coins, with `SC.wav` renamed `game-music.wav` and `dash.wav` `lane.wav`) and `game\sounds\unused` (14 at first, now 10); `sound_files()` walks the whole `sounds` folder with its subfolders, so a build ships both and `data_summary()` reads "26 files - 26 sounds". Both folders together are about 90 MB, most of it three files (`unused\SuperBonk.wav` 28 MB, `unused\perdeu.wav` 24 MB, `used\SC.wav` 16 MB); **both ship, decided 2026-10-02** (the dev: "I want all of the sounds to be packed, including the unused ones. So you can leave that as is."). Don't propose leaving `unused` out.
- **`docks\credits.txt`** ships too, since this repository has one.
- **A new check in `problems_now()`:** the build refuses while `InsideTheCave.py` or `insidethecave\__init__.py` is missing, saying the port has not been written yet. A dry run still reports everything else.
- **The closing line** credits the game's files to Iago Barbosa, Juliana Barros and Victor Leal ([[project_provenance]]).
- **Removed:** the other project's contributor credits, dates and plan-note links in the comments; they now point here.
- `TOOLS_INI` (`~/.game_tools/tools.ini`, the dev's shared tools file naming `gh`) and the `gh` fallback path stay as they were.
- **Windows only (the dev, 2026-10-02: "Can you please remove the linux thing? I do not have WSL.").** The reference scripts built and released for Linux too, from a per-system table. That is gone: the compiler has plain `EXE`, `FOLDER`, `BINARIES` and `VENDOR_LICENSES` constants and refuses to build anywhere but Windows; the releaser packs a zip only (no `.tar.gz`, no `tarfile`), and its "Add this system's build to the release" step and menu choice are removed. `add_to_release()` stays, so uploading to a release that is already on GitHub without its zip adds the zip rather than failing. `vendor/openal/libopenal.so.1`, the Linux build's OpenAL, was removed from the repository the same day at the dev's word.

## Still to do
- A `tests/case/release.py` for the releaser's version numbering, changelog filing and archive names, which builds nothing and touches no network ([[project_dev_tasks]]).
- Bring back a `--test` build once the game writes a log and a `crash.txt`.
