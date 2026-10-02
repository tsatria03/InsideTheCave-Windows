---
name: project_port_plan
description: "PLANNED 2026-10-02, waiting on the dev's answers: the whole port of Inside The Cave to Windows in Python, in five phases (platform, a SpriteKit stand-in, the game scene, the screens, building and releasing), with the decisions it needs from the dev listed at the end. No port code until the dev answers and says go."
metadata:
  type: project
---

**Status: planned (2026-10-02); questions 1 to 3 answered (1 since made unnecessary by the WAVs), question 4 under way.** The dev asked for the whole porting plan to be written now, with the open questions ("Let's write the entire porting plan now, with your open questions"). Nothing is built. Each phase starts only on the dev's go-ahead; the plan is updated first whenever an answer changes it ([[feedback_record_plans_first]]). It is ported from what the disassembly found ([[project_disassembly_plan]], `GAME_STRUCTURE.md`), every port function citing the original's address, every difference recorded in `DIVERGENCES.md` ([[feedback_side_by_side]]).

## What the port is
The original is small: one game scene and five screens, 12 sounds, every number a constant in the code. What makes it work is Apple's **SpriteKit**, the iPhone's built-in game framework: it moves the objects over time, tells the game when two of them touch, and plays sounds placed in space. The dev does not have SpriteKit, and does not need it: it is part of iOS, not something to install. The port reproduces the small part of it the game uses, in Python, in its own module (phase 2), fed with the numbers read from the binary.

The rest follows the reference port in the gitignored `user/` folder ([[feedback_no_other_games]]): pygame for the window and keys, OpenAL Soft for sound, NVDA or Prism for speech, the same save, key-binding and test machinery, adapted ([[project_python_only]]). Windows only.

## Layout
- `InsideTheCave.py`: the entry point and the screen loop, standing in for the storyboard's navigation (Warning, menu, game, result, ranking).
- `insidethecave/paths.py`: `game\sounds` in the repository or beside the executable, `INSIDETHECAVE_GAME`, the save in `%APPDATA%\InsideTheCave` (`INSIDETHECAVE_USER_DIR` for tests). A sound is found by its base name, in `game\sounds\used` first, then `game\sounds\unused`: the binary's `"dash.aiff"` is `used\dash.wav` ([[project_build_scripts]], `DIVERGENCES.md`).
- `insidethecave/platform/`: adapted from the reference port. `openal.py` (OpenAL Soft through ctypes), `runloop.py` (timers and delayed calls, for the NSTimers and `DispatchQueue` the original uses), `defaults.py` (UserDefaults: the save), `speech.py` (NVDA, Prism, a Windows voice; silent in tests), `keymap.py` (rebindable keys), `sound.py` (loading the WAVs with the `wave` module, and mixing a positioned sound down to mono; new), `volume.py` if volume knobs are wanted.
- `insidethecave/scene/`: the SpriteKit stand-in (phase 2).
- `insidethecave/game/`: one module per original class: `app_delegate.py`, `warning_view_controller.py`, `home_screen_view_controller.py`, `game_view_controller.py`, `game_scene.py`, `result_view_controller.py`, `ranking_view_controller.py`, `ranking_cloud.py` only if anything of it survives (question 9).
- `insidethecave/ui/`: the keyboard for the game and for the screens, the F1 key-bindings screen, and pausing on focus loss, adapted.
- `tests/case/`: the tests, silent and off the real save from the first one ([[project_safe_test_run]]).

## Phase 1: the platform
Copy and adapt the platform modules, `paths.py`, the key map and its F1 screen, and the test helper `_scratch_save.py`; rename everything from the reference port. Add `sound.py`, which reads each WAV (16-bit PCM, so the standard library's `wave` reads it) into an OpenAL buffer once, at start, mixed down to mono where the sound is placed in space (question 2). Tests: paths, the save, the run loop, speech kept silent, the key map.

## Phase 2: the SpriteKit stand-in
Only what `GAME_STRUCTURE.md` shows the game using:
- **Nodes** with a position, scale and size, in the scene's own units (750 by 1334, origin at the centre), children (the scenery's two sprites ride on the first), and `removeFromParent`.
- **Actions**, run on a node, advancing with the real clock: `moveToX`/`moveToY` over a duration (linear, as SpriteKit's default), `wait`, `sequence`, `run` (a callback), `repeatForever`, `removeFromParent`, keys (`upScore`) and `removeActionForKey`, pause. Images are not drawn; sprite sizes come from the original's scale factors and image sizes (question 11).
- **Contacts**: each frame, every pair of bodies whose category and contact mask call for it is tested for overlap (rectangles, with their centre offset, and circles), and a pair that starts touching is reported once, to the scene's `didBeginContact`, with the bodies in the order SpriteKit would give them (question 10). No collisions, no gravity: the original has neither.
- **Audio nodes**: an `SKAudioNode` becomes an OpenAL source, looped or not, at its node's position, heard by a listener at the player; `play`, `changeVolumeTo`/`changeVolumeBy` over a duration. How a scene position becomes a position in OpenAL is not in the binary (it is in Apple's code), so it is a tunable mapping chosen by ear (question 2).
- Tests: an action chain finishes at the right time and place against the real clock, contacts fire once and in order, a monster's roar fires at the sensor.

## Phase 3: the game scene
`game_scene.py`, method by method from `analysis/disasm/dz_GameScene.txt`, each with its address: the lanes, the player, the slot chain and every spawn rule, movement and the speed-up, the roar sensor, the torch light and its burning down, picking up and throwing, every contact, death, the score loop, the three scenarios, the tutorial line. `game_view_controller.py`: the score and coin counters and game over. Played first on its own, `--stage`, for the dev to check by ear before the screens exist. Tests: a headless game for the spawn order, the speed-up, the scenario changes at 81 and 161 slots, the score, a coin, a torch thrown and a monster killed, death.

## Phase 4: the screens
- **Warning**: the earphone line in Portuguese or English as the original, 3 seconds or a key, then the menu.
- **Menu**: Play and Score (the original's two buttons), plus Quit; F1 for the keys.
- **Result**: the score and coins, the name (typed; question 8), Replay and Menu, each saving first, as the original; the local top five.
- **Ranking**: the local top five.
- Every screen speaks through the screen reader or a Windows voice: the original has no recordings for its screens, and VoiceOver read them (question 6). Tests: each screen's rows and keys, the save's format.

## Phase 5: building and releasing
`compiler.py` builds once `InsideTheCave.py` and the package exist ([[project_build_scripts]]); the dev's first build. The player's documents in `docks/`: the readme, credits, the changelog's first block and the todo list ([[feedback_changelog]], [[feedback_todo_list_format]]). Then the first release with `releaser.py`, by the dev.

Each phase is committed as it lands and pushed only once it works; each changes `PORTING_STATUS.md` as functions are ported.

## Decisions the dev needs to make
Each with a recommendation; none blocks phase 1 except question 1.

1. **Decoding the MP3s. NO LONGER NEEDED (2026-10-02).** It was decided that pygame would decode them (the dev: "Let's use pygame for the decoder."), but the dev then converted every sound to 16-bit PCM WAV, which OpenAL plays as it is once the standard library's `wave` module has read it. No decoder, nothing to install.
2. **Placing the sounds. DECIDED 2026-10-02: option 2, mono and placed in the lanes.** The original's roar and bats are stereo files (`GAME_STRUCTURE.md` section 13), and Apple's 3D audio, which SpriteKit uses, places only mono sounds in space and plays stereo ones straight through (**inferred**: Apple's behaviour, not in the binary). So in the original the roar most likely did not come from the monster's side: only its volume, 3.0 in your lane against 1.0, said it was yours. The dev chose to improve on that ("I prefer option 2 because the volume of the sound wasn't enough to tell me witch direction the monster was coming from."): every sound the original positions (the roar, the bats, the coin jingle if it is ever used) is mixed down to mono when decoded and placed in its lane, left, centre or right, growing louder as it comes, on constants the dev tunes by ear. The original's 3.0 and 1.0 volumes stay on top. A deliberate difference, written into `DIVERGENCES.md` when it is built.
3. **The torch light for a blind player. DECIDED 2026-10-02: a spoken warning, on top of the original's sounds** (the dev: "I want to add a speech warning if possible. Along with the current sounds."). The original shows the light shrinking; its only sounds for it are the burning loop, which loses only about a quarter of its volume over a whole torch (1.0 to about 0.75, by 0.003 and then 0.0045 a step), and that loop stopping when the torch dies. All of that stays. The port adds "Torch low", spoken through the screen reader or a Windows voice, once, when the falloff passes 3.0, the start of the dim stage (`changeFalloffSize`, 0x100023a0c): about 29 slots before it dies, some 19 seconds at the start of a game. The wording and the point are constants, to be adjusted after the dev has played; spoken in the chosen language (question 7). A port addition, written into `DIVERGENCES.md` when built. Also noted for the dev: the torches lying on the path make no sound, like the coins, so they are found only by touching them.
4. **The original's bugs.** Recommended, keep as the original unless noted: bats cannot be killed (keep); a thrown torch ignores bats' contact order (keep); contacts tested in one order only (reproduce SpriteKit's order so it behaves as the original did); the coin jingle never plays (keep, but ask again after playing, since coins are silent until taken); the spawn chain can stop after a kill between two heights (fix: the game would go quiet for good); the tap's split being device-dependent (gone with keys); moves allowed before the game starts and a throw after death (keep the first, fix the second); an empty name throwing a score away (fix: save as "unnamed player"); the result screen's crash on short device names (gone: the port has no device name); `rankWorld` reset every launch (gone with the world ranking). The snow that never shows has no sound, so nothing to do.
   Asked one bug at a time (2026-10-02). Decided:
   - **The spawn chain stopping: FIX** (the dev: "I want to fix this bug."). A monster killed by a torch before its own action has made the next slot makes it at once, wherever it is, so spawning never stops; the original made it only when the monster was at or above 0.4175 H (0x1000134d8), against the 0.33 H where the slot makes it itself (0x100013aec). A fix, written into `DIVERGENCES.md`.
5. **Keys**, rebindable with F1 as in the reference port: move left A or Left Arrow, move right D or Right Arrow, throw W or Up Arrow, pause P (an addition: the original has none), Escape back or pause, F1 the keys. Switching away from the window pauses. Recommended as listed.
6. **Speech on the screens.** Recommended: the screen reader speaks every screen's text and buttons, and the tutorial line, the way VoiceOver did; a Windows voice when no screen reader runs.
7. **Language.** The original picks the tutorial line (six languages) and the warning (two) by the device's language. Recommended: Windows's display language, falling back to English, with a setting in `settings.json` to choose.
8. **The player's name.** The original guesses it from the device's name. Recommended: start the field empty, with "Insert name" spoken, and save an empty one as "unnamed player".
9. **The world ranking.** CloudKit cannot work. Recommended: drop the World tab and keep the local top five; nothing of `RankingCloud` is ported.
10. **Contact order.** SpriteKit decides which body is A and which is B; the original tests most pairs one way only. Recommended: work out SpriteKit's order from the original's behaviour as far as it shows, so every contact the original handled still fires, and note it in `DIVERGENCES.md`.
11. **Sizes the binary does not hold.** The images' sizes (inside `Assets.car`) and the roar sensor's, which comes from SpriteKit's placeholder for a missing image, decide when contacts happen, the roar's above all. Recommended: read the image sizes out of `Assets.car` in phase 2, take the placeholder as 128 by 128 points (SpriteKit's, inferred), and confirm the roar's timing by ear.
12. **Volume knobs and a debug mode.** Recommended: Page Up and Page Down for a master volume, and the music's in `settings.json`; a `--debug` mode where you cannot die, for checking by ear. Both small, both additions.
13. **The window.** Recommended: a plain window of text lines for a sighted helper, as the reference port has, and no drawing of the original's pictures.
14. **The spider boss. DECIDED 2026-10-02: no** (the dev: "we do not need spiders or bosses."). Version 2.02 had a spider boss with webs, which the 2.3 rewrite dropped, so 2.32 has none (`GAME_STRUCTURE.md` section 15). The port is 2.32 as it is: no spider, no boss. The spider's sounds stay in `game/sounds/unused/` as the dev sorted them; don't propose a boss again unless the dev asks.

Questions are asked one at a time ([[feedback_no_question_pickers]]); question 4 is being asked bug by bug.
