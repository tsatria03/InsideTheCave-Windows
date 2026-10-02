---
name: project_disassembly_plan
description: "PLANNED 2026-10-02: disassemble the whole game before any porting - every function in __text named where possible and listed in analysis/, plus the .sks scenes, the storyboards and all strings - with arm64 tools in tools/ (capstone), a coverage check that nothing was skipped, and GAME_STRUCTURE.md filled from the result. No port code until it is done."
metadata:
  type: project
---

**Status: planned (2026-10-02).** The dev agreed the plan and asked for it to be written first ("Write the plan first"). Nothing is built yet. It becomes "built, not yet confirmed" once the tools and listings land, and "finished" only when the dev says so ([[feedback_record_plans_first]]).

## The rule behind it
**The whole game is disassembled before anything is ported** (the dev, 2026-10-02: "We need to fully disesembel the entire game first before we do anything related to porting it."). No code goes into `insidethecave/` or `InsideTheCave.py` until this plan is finished. Every port line will cite an address from these listings ([[feedback_side_by_side]]).

## Scope: what "the entire game" means
**The code: every function in `__text`** (0x100005764, size 0x1E4AC, about 124 KB):
- not only the nine classes' Objective-C methods, but every Swift function, thunk and closure, including the blocks handed to `SKAction.run`, where much of the timing will be
- **coverage is proved**: every address in `LC_FUNCTION_STARTS` appears in a listing, and the listings together cover `__text` with no gap

**The data the code reads:**
- `GameScene.sks`, `Actions.sks` and `Snow.sks`: SpriteKit scenes, keyed archives that may set node names, positions, physics bodies and actions the code never spells out
- the storyboards in `game/Base.lproj` (`Main.storyboardc`, `LaunchScreen.storyboardc`): each screen's controls, labels, accessibility text and segues (`WarningToMenu`, `GameToResult`, `unwindToHomeScreenSegue`, `unwindToGameSegue`)
- every string: `__cstring`, the UTF-16 `__ustring` (where the French, Russian and Chinese narration probably are) and `__objc_methname`
- `Info.plist`, already read

**Out of scope:**
- `game/Frameworks/`: Apple's Swift runtime, not the game; only which of its functions the game calls is recorded, through the stubs
- `Assets.car`: listed by image name only, since the port shows no images
- `_CodeSignature`, the icons, `iTunesArtwork`

## The tools (`tools/`, standard library plus `capstone`)
Modelled on the reference port's tools in the gitignored `user/` folder ([[feedback_no_other_games]]), but rewritten for **arm64 and 64-bit Objective-C**, since those are 32-bit Thumb-2 ([[project_binary_analysis_notes]]). Planned files; names may change as they are built, and this note is updated first if they do:
- **`macho.py`**: the library the rest import. Load commands, segments and sections, the symbol table and the indirect symbols (so each `__stubs` entry has its import name: `objc_msgSend`, `swift_retain`, `objc_msgSendSuper2` and so on), `LC_FUNCTION_STARTS`, the string sections, `__objc_selrefs`, `__objc_classrefs`, `__objc_superrefs`, and the 64-bit Objective-C class, method, ivar and property lists, plus Swift 3's field names (`__swift3_reflstr`, `__swift3_fieldmd`).
- **`classes.py`**: the nine classes, their superclasses, ivars with offsets, properties and method IMPs, to `analysis/data/classes.json` and a readable `analysis/data/classes.txt`.
- **`dz.py`**: arm64 disassembly through capstone, annotated: `adrp`+`add`, `adrp`+`ldr` and `adr` resolved to strings, selectors, classes and data; `bl` to a stub named by its import; `bl` to a game function named by the function map; ivar offsets; float and double literals. Usage by address range or by name.
- **`names.py`**: the function map. Names come from, in order of trust: the Objective-C method IMPs; the `@objc` thunks, each of which calls its Swift body, so the body takes the thunk's name; the Swift class vtables in the class metadata; closures and helpers named by their caller and the order they appear in (`GameScene.init#closure1`); the rest stay `fn_<address>`. Written to `analysis/data/functions.txt` with the reason for each name.
- **`listings.py`**: writes `analysis/disasm/dz_<Class>.txt` per class, and `dz_unowned.txt` for functions no class claims, each function headed `//// <name>  0xSTART..0xEND  (named from: ...)`.
- **`coverage.py`**: proves every function start is in a listing and no byte of `__text` is left out; it is the check that says the disassembly is complete.
- **`archive.py`**: decodes the keyed archives - the `.sks` scenes, which are binary plists `plistlib` can read - into readable trees in `analysis/data/`. The compiled storyboards' `.nib` files are Apple's NIBArchive format, not plists, so this needs its own small decoder.
- **`strings.py`**: every string, C and UTF-16, with its address and the functions that load it, to `analysis/data/strings.txt`. The scratch script used to match the sound files on 2026-10-02 is its first piece.

**`capstone`** is a developer-only package for these tools, never needed to play or build the game, and stays out of `requirements.txt`, as in the reference port's README ("only to redo the reverse engineering").

## The outputs
- `analysis/bin/InsideTheCave_arm64`: a copy of `game/InsideTheCave`, so the analysis can be redone from `analysis/` alone.
- `analysis/data/`: `classes.json`, `classes.txt`, `functions.txt`, `strings.txt`, and the decoded scenes and storyboards.
- `analysis/disasm/`: one listing per class, plus the unowned functions.
- `aidocks/GAME_STRUCTURE.md`: rewritten from the listings, each fact verified at an address, replacing what is now inferred from names. It answers at least: the lane positions and how sounds are placed in them; monster speed and how it grows; spawning and its patterns; the torch light, its dimming, picking up and throwing; what a torch kills and what each thing scores; coins; the scenarios; the boss; dying and the game over (including the crash a 2016 reader reported); the menus and screens; the ranking; the speech and its languages.
- `aidocks/PORTING_STATUS.md`: every function, listed as read, ready to be ticked off as it is ported.
- `tools/README.md`: how to rerun everything, and the arm64 address rule.

## Order of work
1. Check capstone is installed; install it only if not (the dev, 2026-10-02).
2. `macho.py` and `classes.py`, checked against what is already known by hand: 9 classes, the section map, 198 selector references.
3. `names.py`, `dz.py`, `listings.py`, then `coverage.py` until it reports nothing missing.
4. `strings.py` and `archive.py`.
5. Read the listings class by class, `GameScene` first, writing `GAME_STRUCTURE.md` as each part is verified.
6. Report to the dev; they confirm, and the plan is marked finished. Only then does porting start.

## Checks
- Tools are checked against facts verified by hand before they are trusted: the section addresses, the class count, the sound-loading addresses in `GAME_STRUCTURE.md`.
- Every claim in `GAME_STRUCTURE.md` names its address; anything still read only from a name is marked inferred.
- Running the tools only reads files and writes into `analysis/`; it executes no game code and makes no sound, so it needs no permission beyond this plan ([[feedback_dont_run_or_build]]).

## Commits
- This note, with its `MEMORY.md` pointer and the rule in `CLAUDE.md`, is committed on its own first, and **not pushed** until the whole plan is built and tested ([[feedback_record_plans_first]]).
- The tools and listings follow as their own commits, one per part, when the dev asks.
