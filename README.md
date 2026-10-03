# InsideTheCave-Windows

A Python port of **Inside The Cave** (`InsideTheCaveBD` 2.32), an iPhone, iPad and
Apple TV audio game made in 2016 by Iago Barbosa, Juliana Barros and Victor Leal at
BEPiD Recife. You are in a dark cave and your torch is slowly going out. Monsters are
coming, and you cannot see them: when you hear one roar, you move to another lane to get
out of its way. Torches you find along the way keep your light up, and can be thrown at
the monsters.

The game was built so that blind and sighted players have the same experience, with
VoiceOver support and sound as the whole of the gameplay. It is no longer on the App
Store. This port brings it to Windows, from the original's own binary and recordings.

**Wear headphones.** The original says so itself ("Put the earphone on for a better
experience"): you find a monster's lane by where its roar comes from, which speakers
cannot show you.

## Status

**The game itself is playable from source**, with no releases yet:

    python InsideTheCave.py

It starts straight on a game: the original's earphone warning, menu, result and ranking
screens are still to come, and until then a game over says your score and coins, and
Enter plays again. The whole original game has been disassembled: every function of its
code is listed in `analysis/disasm/`, and `aidocks/GAME_STRUCTURE.md` describes how the
game works, read from that code. `aidocks/PORTING_STATUS.md` keeps track of what is done,
and `aidocks/DIVERGENCES.md` of every place the port differs on purpose.

---

## Requirements

To run it from source, once there is something to run: 64-bit Python 3.12 or newer on
Windows 10 or later, and two packages:

    pip install -r requirements.txt

- **`pygame`**: the window, the keyboard and the frame loop. It must be `pygame`, not
  `pygame-ce`: the two cannot be installed side by side.
- **`prismatoid`** (Prism): speech through any screen reader other than NVDA, or through
  a Windows voice when none is running. Without it, only NVDA would speak.

Everything else will be the standard library. The audio is OpenAL Soft through `ctypes`:
`vendor/openal/soft_oal.dll` ships with the repository, so there is nothing to install for
it. `vendor/nvda/nvdaControllerClient64.dll` ships too, so NVDA can speak directly. The
port is for Windows only.

## How the game plays

As the original's code has it (`aidocks/GAME_STRUCTURE.md`), with the port's few changes.

- The cave has **three lanes**, and you stand at the bottom of the middle one. Monsters
  come down the lanes toward you; as one comes within reach it **roars**, from its lane,
  left, ahead or right. Move out of its lane before it reaches you, about a second later.
- **Bats** come down the same way, with their own sound; every seventh obstacle is bats.
- Your **torch** burns down as you go; "Torch low" is said when it starts to dim. Torches
  lie on the path: run into one to pick it up and relight.
- **Throw** your torch up your lane to kill a monster in it. It uses the torch up, and
  scores nothing; a bat it hits only dodges into another lane.
- **Coins** come down too, each jingling from its lane: ten points each. The score also
  goes up four times a second while you live.
- The cave **speeds up** every twenty things that come down, and turns from rock to water
  and then ice as you go deeper.
- The game will remember your best five scores on your computer, with the result screen
  still to come. The original also sent them to an online leaderboard, which this port
  leaves out.

**Keys**: A or Left Arrow and D or Right Arrow move, W or Up Arrow throws, P or Escape
pauses, Page Up and Page Down set the volume, F1 lists and changes the keys, Alt+F4 quits.
Leaving the window pauses. On your first three games a Windows voice says the original's
line in your language, and your screen reader then says the keys.

## Layout

```
game/                    the original app bundle, unpacked
  sounds/used/           the 12 sounds version 2.32 plays, as WAV, under their own names
  sounds/unused/         14 sounds from the game's older versions
InsideTheCave.py         the entry point: python InsideTheCave.py
insidethecave/           the Python package: the game, the SpriteKit stand-in, the
                         platform layer and the keyboard
analysis/                the binary, and its complete disassembly and decoded data
tools/                   the arm64 Mach-O and disassembly tools that made analysis/
tests/case/              the automated tests
tests/interact/          tools to play by ear
vendor/                  OpenAL Soft and NVDA's controller client, with their licenses
docks/                   readme.txt, changelog.txt, credits.txt and todo list.txt,
                         which ship in a docks folder beside the game
aidocks/                 GAME_STRUCTURE.md, DIVERGENCES.md, PORTING_STATUS.md, and
                         the notes for AI-assisted work (see CLAUDE.md)
compiler.py              builds the game with PyInstaller
releaser.py              sets the version, files the changelog, builds, zips, tags and uploads a release
requirements.txt         the two packages it needs
VERSION                  the date version, such as 26.10.02-1
```

The game is in `insidethecave/game/`, one module per original class (so far `GameScene`
and `GameViewController`); `insidethecave/scene/` is the part of Apple's SpriteKit it
needs (things moving over time, contacts, sounds placed in the lanes); the platform layer
is in `insidethecave/platform/`: OpenAL, the timers, the save, the volume settings, speech
and the tutorial's Windows voice, the display language, the key bindings and the sounds.
The keyboard and the F1 key-binding screen are in `insidethecave/ui/`, and
`InsideTheCave.py` is the entry point and the window.

The save lives in `%APPDATA%\InsideTheCave`: `save.json` (the local top five and the
tutorial count), `settings.json` (the master and music volumes) and `keys.json` (the key
bindings).

### `game/`: the original's data

`game/` holds the contents of the original `InsideTheCave.app` as it shipped: the
`InsideTheCave` executable, `Info.plist`, the SpriteKit scenes (`GameScene.sks`,
`Actions.sks`, `Snow.sks`), the compiled asset catalogue `Assets.car`, the storyboards,
the four fonts, the app icons, the Swift runtime in `Frameworks/`, and `_CodeSignature/`.
The port never writes to it; the save will live in `%APPDATA%`.

The one thing that is not where the original kept it is the sounds. The original keeps its
12 sounds loose in the bundle's top folder, as WAV, MP3 and AIFF; here they sit in
`game/sounds/used/`, all converted to 16-bit WAV under their original names, from the roar
(`Rugido.wav`) and the bats to the torch, the coins and the music (`SC.wav`). The
original asks for some by another extension, such as `dash.aiff`, so the port finds a sound
by its name without the extension. `game/sounds/unused/` keeps 14 sounds from the game's
older versions, which version 2.32 never plays.

## Where this came from

There is no source code for the original. `game/InsideTheCave` is a thin **arm64**
Mach-O, built with Xcode 8.2 against the iOS 10.2 SDK, and it ships **unencrypted**
(`LC_ENCRYPTION_INFO_64 cryptid = 0`), so the whole thing can be read directly. The game
is written in Swift 3 with SpriteKit, in about 124 KB of code across nine classes, from
the earphone warning and the menu to `GameScene`, which is the game itself.

The Swift symbols are stripped, so the port is recovered from what the binary still
names: its Objective-C selectors and properties (`playMonsterRoarAtPoint:`, `throwTorch`,
`speedMonster`), its strings, and its calls into SpriteKit, AVFoundation and UIKit. Every
ported method will carry the address it came from, and every place the port differs from
the original will be written down in `aidocks/DIVERGENCES.md`.

## Tests

`tests/case/` holds the tests: plain scripts, each checking one part of the game
against the original and printing `ok` or `FAIL` for every check, then a total. So far
they cover the platform layer (`paths`, `runloop`, `save`, `speech`, `keymap`, `sound`,
`language`), the SpriteKit stand-in (`scene`), the game (`gameplay`) and the program
(`app`). Run any of them on its own:

    python tests/case/<name>.py

**The tests will never touch your save, and make no sound.** Each one imports
`tests/case/_scratch_save.py` first, which points the save at a throwaway folder, keeps
everything away from your screen reader, and sends the audio to OpenAL Soft's null driver
with no window. Files starting with `_` are helpers, not tests.

`tests/interact/` holds tools you play rather than tests, each on a save of its own.
`platform_check.py` plays what the port has so far, before there is a game: the roar and
the bats placed left, centre and right, every sound the game plays, the tutorial line in a
Windows voice followed by the key hints, and the volume. It opens a small window: Up and
Down choose a check, Enter runs it, Escape stops it, and Alt+F4 quits at any moment. Wear
headphones:

    python tests/interact/platform_check.py

`scene_check.py`, in the same kind of window, previews the game's sounds in their lanes:
a monster, bats or a jingling coin coming down each lane, the roar when it reaches the
sensor, and "now" when it would reach you.

    python tests/interact/scene_check.py

`stage_chooser.py` starts the real game from the beginning, a little before the water, a
little before the ice, or at the top speed, with the tutorial and debug mode (where
nothing can kill you) on or off:

    python tests/interact/stage_chooser.py

## Building and releasing

Both scripts open a numbered menu when double-clicked, and wait for Enter at the end.
Building needs PyInstaller (`pip install pyinstaller`); releasing also needs the GitHub
CLI, signed in with `gh auth login`. Both are set up for this game, but **there is no game
to build yet**: until the port's entry script exists, the compiler says so and stops.

- **`compiler.py`** only builds. It never zips and never changes the repository. Everything
  lands in `dist\InsideTheCave-Windows`, around `InsideTheCave.exe`. It makes a folder build, with the
  sounds beside the executable in `game\sounds`, or with `--embed` a single exe holding
  them, and puts the documents from `docks/` in a `docks` folder beside the executable,
  with `VERSION` and the license. Of the original app bundle, only the sounds ship.
- **`releaser.py`** does the rest, asking Y or N before each step: it checks that
  everything is committed and pushed, sets `VERSION` to today's date and that day's
  release number, files the changelog's unreleased lines under it, builds with the
  compiler, zips the build into `InsideTheCave-Win-<version>.zip`, commits, tags
  `V<version>`, and uploads the zip to GitHub as the release "InsideTheCave V<version>".

A version is the date of the release and that day's number: `26.10.02-1` would be the first
release of the 2nd of October 2026.

## Credits

**Inside The Cave** was made by Iago Barbosa, Juliana Barros and Victor Leal at BEPiD
Recife, in 2016.

**[tsatria03](https://github.com/tsatria03)** is making the Windows port.

## Licence

The port's code is in `LICENSE`. Everything under `game/`, and the binary and disassembly
under `analysis/`, belong to the original game's makers and are not covered by it.

The third-party pieces keep their own licenses, which sit beside them in `vendor/` and
can also be read online:

- OpenAL Soft, LGPL 2: <https://github.com/kcat/openal-soft/blob/master/COPYING>
- the NVDA controller client, LGPL 2.1: <https://github.com/nvaccess/nvda/blob/master/extras/controllerClient/license.txt>
- Prism, MPL 2.0: <https://github.com/ethindp/prism>
- pygame, LGPL 2.1: <https://github.com/pygame/pygame/blob/main/docs/LGPL.txt>
