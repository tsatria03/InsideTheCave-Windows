---
name: project_build_scripts
description: "compiler.py and releaser.py at the root are copies of the reference port's scripts, still naming that game (33 lines). Do not edit either until the dev gives the go-ahead (2026-10-02). What they will need when that comes."
metadata:
  type: project
---

**Status: waiting for the dev's go-ahead. Do not modify `compiler.py` or `releaser.py` yet** (the dev, 2026-10-02: "do not modify the compiler/releaser scripts yet. Wait till I give you the goahead."). Both are untracked in git as of that day.

They are copies of the reference port's build and release scripts, from the gitignored `user/` folder ([[feedback_no_other_games]]), and still name that game on 33 lines between them: its executable and package names, its environment variable, its sound folder layout, and its release title.

**What the compiler does, in short:** a numbered menu (or flags) around PyInstaller. It builds a folder build, or with `--embed` one exe holding the sounds and data, into `dist\<Name>-Windows` (or `dist/<Name>-Linux` on Linux). It copies only the game files the port reads, ships `docks/` as a `docks` folder beside the executable with `VERSION` and `license.txt`, and puts the third-party licenses inside the executable. It never zips and never changes the repository.

**What the releaser does, in short:** check, then set the date version `YY.MM.DD-N` in `VERSION`, file `unrelease:` in `docks/changelog.txt` under it, build through the compiler, zip, commit "Release <version>", tag `V<version>` and upload to GitHub through `gh`. It enforces the 5 to 100 entry limits ([[feedback_changelog]]).

**What the adaptation will need, once allowed** (listed now so nothing is missed; nothing done yet):
- The names: executable, entry script, the `insidethecave` package import, the environment variables, the build folder, the zip names and the release title.
- The game files to copy. This bundle is flat: the WAV, MP3 and AIFF sounds sit in `game/` with the fonts, the `.sks` scenes, the asset catalogue `Assets.car` and the nibs. Which of them the port reads is not known until the port exists; the iOS executable, `_CodeSignature`, `Frameworks/` and the app icons should stay out.
- Whether the sounds are sorted into `game/sounds/used` and `unused` as in the reference port. That is the dev's decision; don't move sound files unless asked.
- `VERSION` already holds `26.10.01-1`.

**How to apply:** Leave both files alone until the go-ahead. When it comes, record the adaptation plan in its own note first ([[feedback_record_plans_first]]), and never run either script ([[feedback_dont_run_or_build]]).
