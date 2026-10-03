---
name: project_status_keys_plan
description: "FINISHED 2026-10-03, confirmed by the dev, except the tutorial's answers, which come with the tutorial: three rebindable keys in a game, S \"Score, 412.\", C \"Coins, 7.\", E \"Speed, 0.\" to \"Speed, 40.\" (speed-ups so far); in the tutorial C as usual, S \"No score to report.\", E \"No speed to report.\"."
metadata:
  type: project
---

**Status: FINISHED 2026-10-03, confirmed by the dev by ear ("Everything works.", trying them in the speed check too), built on the dev's go-ahead ("Yes.").** Agreed the same day ("Yes please."), settled one question at a time ([[feedback_record_plans_first]]). **The tutorial's part (S and E saying there is nothing to report) is built with the tutorial**, since the tutorial does not exist yet.

**As built:** `keymap.py` (`score` S, `coins` C, `speed` E, "Say the score", "Say the coins", "Say the speed"; an older `keys.json` gains them), `game_input.py`, `game_scene.py` (`SAY_SCORE`, `SAY_COINS`, `SAY_SPEED`, `SPEED_COUNT_FROM` 5.0, `speedCount`, `sayScore`, `sayCoins`, `saySpeed`; the score and coins read from `GameViewController`). Tests: `gameplay.py` (the words, the count at each whole speed and after 140 slots, nothing after death), `keymap.py`, `screens.py` (the keys reach the game, not the pause menu). Goes with [[project_torch_key_plan]] (T) and [[project_tutorial_plan]].

**Why:** a player cannot hear the score, the coins or the speed mid-run; the original showed them on screen, and the port's window shows them only to a sighted helper.

## The keys
- Three new actions in `platform/keymap.py`'s `ACTIONS`, **rebindable in F1** (the dev: "Yes for bindable."), defaults chosen by the dev ("For S, it should say score, x. C should say coins, x. For speed, we could use E"):
  - **S**, the score: "Score, 412."
  - **C**, the coins: "Coins, 7."
  - **E**, the speed: "Speed, 0." up to "Speed, 40."
- S, C and E are free in a game: the game's keys are A, D, W, P, the arrows, T (planned), F1, Escape, Page Up, Page Down, Home and End. Typing a name happens only on the result screen, and F1's own letters (A, R) only on the F1 screen. A `keys.json` saved before them must gain them.

## The speed's number
- **The number of times the cave has sped up** (the dev chose a count over the raw number, then: "I thought it would be 0 since 5.0 is the first speed"): `round((START_SPEED - speedMonster) / SPEED_STEP)`, 0 at 5.0, 10 at 4.0 (the original's start), 20 at 3.0, 30 at 2.0, 40 at the top, 1.0. Higher is faster, unlike `speedMonster`. Each step of the cave, every 20 slots, adds one.
- Computed from 5.0 whatever the game started at, so a game started at 4.0 by the planned difficulty choice says "Speed, 10." from its first slot. **The difficulty is never read out** (the dev).

## When they work
- Whenever a game is running, the instructions included; not on the pause menu (its keys are the menu's) and not after death. Said through the screen reader, interrupting, as the game's other messages (`GameScene.say`).

## In the tutorial
- **The score is off entirely** (the dev: "I want the score system to be switched off entirely in the tutorial."): no ticks, and coins add nothing to it (recorded in [[project_tutorial_plan]]).
- **C works as usual** (the dev: "C should work, but not S and E because nothing goes up for that in the tutorial."): coins are still counted.
- **S says "No score to report." and E says "No speed to report."** (the dev's wording), rather than nothing, as the throw key's "No torch to throw.": a key always answers.

## Where it goes
- `platform/keymap.py`, `ui/game_input.py` (the three actions), `game/game_scene.py` or `game/game_view_controller.py` (the score and coins live in the view controller; the speed in the scene).
- Tests: each key's words, the speed count at 5.0, 4.0 and 1.0 and after each step, the keys in F1 and rebindable, an old `keys.json` gaining them, silence on the pause menu and after death, the tutorial's answers.
- By ear: `stage_chooser.py` covers every speed; the dev presses S, C and E in play.
- Docs: `docks/readme.txt` (controls, the F1 list), the changelog, the todo list moved to Finished once the dev has heard it.
