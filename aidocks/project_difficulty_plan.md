---
name: project_difficulty_plan
description: "FINISHED 2026-10-03, confirmed by the dev: Play asks \"Choose a difficulty\": Easy 5.0 to 3.0 with a torch 1.5 times as long, Medium 4.0 to 2.0 as now, Hard 3.0 to 1.0 with a torch three quarters as long; all else the same; a best five for each, the old one becoming Easy's; the menu opens on Easy, then on the one last played until the game is closed."
metadata:
  type: project
---

**Status: FINISHED 2026-10-03, confirmed by the dev by ear ("All good to commit. It works."), built on the dev's go-ahead ("Now I'm ready for the next feature build.").** Agreed the same day, settled one question at a time ([[feedback_record_plans_first]]).

**As built:**
- `game/game_scene.py`: `DIFFICULTIES` (start, top, torch length), `DIFFICULTY_ORDER`, `DEFAULT_DIFFICULTY` 'easy'; the scene's `difficulty`, `startSpeed`, `topSpeed`, `torchLength`; `changeFalloffSize` divides both burn rates and the burning loop's fade by the length. `START_SPEED` (5.0) and `TOP_SPEED` (1.0) stay as the slowest and fastest of any difficulty, for the speed check and the E key.
- `game/game_view_controller.py`: `difficulty`, handed to each new scene, so Replay and Restart keep it.
- `ui/difficulty_screen.py` (new): "Choose a difficulty", rows Easy, Medium, Hard, opening on `last`, the difficulty last played (Easy when none); Escape to the main menu.
- `InsideTheCave.py`: the screens 'choose_game' and 'choose_ranking' between the menu and the game or the best five, with the menu music; `played_difficulty`, the difficulty last played since the game was opened, where both screens open, **never saved** (changed while building, below); `--stage` plays Easy.
- **The scores, more simply than planned:** Easy's best five is the original's own `rank`, so the old best five became Easy's without moving it; Medium and Hard are `rankMedium` and `rankHard` (`platform/defaults.py`, `RANK_KEYS`), made by the menu when missing. The best five's screen is titled and announced by difficulty ("Hard, your best five."), and Menu or Escape goes back to the difficulties.
- The torch as built: Easy out after 105 slots ("Torch half." from 31, "Torch low." 61, "Torch almost out." 92), Medium 71 (21, 41, 62), Hard 54 (16, 31, 47).
- **The footsteps by difficulty**, added while building (the dev: "The footstep sound should match the difficulty as well. RIght now the cave walk sound plays in all of the difficulties."; option B, recommended and agreed: "Yes please."): Easy walks, then runs from slot 155 as before; Medium and Hard run from the first slot (`FOOTSTEPS` by difficulty, `footstepFile(slot, difficulty)`).
- `tests/interact/stage_chooser.py`: Left and Right choose the difficulty; its fourth start is slot 400, each difficulty's top. The other by-ear tools play Easy, the default of their own saves.
- Tests: `gameplay.py` (each difficulty's start, top at slot 400, torch length, "Torch low" at the same point), `screens.py` (the difficulty screen opening on Easy or the one last played, three best fives, the old one Easy's), `app.py` (Play to Hard at 3.0, Restart and Replay keeping it, saving into Hard's, Play then opening on Hard, a newly opened game on Easy, nothing in the save; Score through the difficulties and back). Goes with [[project_tutorial_plan]], [[project_status_keys_plan]] and [[project_torch_key_plan]].

**Why:** the dev: "For the play option. It should say choose a difficulty, then have some options, like easy/medium/hard." and "I don't only want the speed thing."

## Choosing
- **Play opens "Choose a difficulty"**, rows Easy, Medium and Hard; Enter starts the game, Escape goes back to the main menu.
- **It opens on the last choice** (the dev: "Last diff choice."). **Changed while building**: only while the game is open, never saved (the dev: "When you open the game, and then choose a difficulty, it should not remember your choice. It should only remember it if you died, and or if you whent back to the main menu, then pressed play again."): Easy each time the game is opened, then the difficulty last played.
- Replay and the pause menu's Restart start the same difficulty again.

## What each controls

| | Easy | Medium | Hard |
|---|---|---|---|
| Starting speed (`speedMonster`) | 5.0 | 4.0, the original's (0x1000157bc) | 3.0 |
| Top speed | 3.0 | 2.0 | 1.0 |
| Top reached | slot 400, about 4:27 | slot 400, about 3:21 | slot 400, about 2:15 |
| The E key says | 0 to 20 | 10 to 30 | 20 to 40 |
| Torch length | 1.5 times, about 105 slots | as now, about 71 | three quarters, about 54 |
| "Torch low" at | slot 62, 43 before out | slot 42, 29 before | slot 32, 22 before |

- **Speeds** (the dev: "I want the starting speed for 5, 4, and 3."; "for easy, it will top out at 3.0 if possible. For medium, it will top off at 2.0. For hard, 1.0."). Each spans the same 2.0, 20 steps of 0.1, so each reaches its top at slot 400. They overlap by half: Easy's end, 4.0 to 3.0, is Medium's start, and Medium's end, 3.0 to 2.0, is Hard's start, so each leads to the next (agreed after the dev asked about Medium and Hard).
- **The torch** (the dev chose "Easy longer, Hard shorter" with these numbers): its two burn rates (0.025 and 0.07 a slot, `changeFalloffSize` 0x100023a0c) divided by 1.5 on Easy and by 0.75 on Hard, so it passes the same falloff points on every difficulty: "Torch low", the burnout, and the T key's levels stay in step, each lasting more slots on Easy and fewer on Hard. At each top speed a torch lasts about 52 s on Easy, 23 s on Medium, 9 s on Hard.
- **The same everywhere** (the dev): the 0.1 step every 20 slots (`SPEED_STEP`), torches 1 in 4 pickups ("I want the same everywhere."), an obstacle every 4th slot and bats every 7th obstacle ("I want it the same everywhere. Same for bats."), the water at 81, the ice at 161, the run at 155.
- The difficulty is never read out during a game (the dev, with the status keys); E's count is from 5.0, so Medium opens on "Speed, 10." and Hard on "Speed, 20.".

## Scores
- **A best five for each difficulty** (the dev: "For the scores, it will ask you to choose a difficulty."): Score opens a choice of Easy, Medium and Hard, then reads that list. A game saves into its own difficulty's list, with the same rules as now (strictly above the fifth, no ties).
- **The existing best five becomes Easy's** (the dev: "I'll do easy."): the save's `rank` is moved to Easy's list on first load; Medium and Hard start as five "Player", "0". The first release's games started at 4.0 and the current release's at 5.0; the save does not say which, so they cannot be sorted.

## The tutorial
- Not a difficulty: its own menu row, no choice asked. Its speed is held at 5.0, and **its torch is Easy's**, 1.5 times as long (the dev: "I want the easy longer one."). Recorded in [[project_tutorial_plan]].

## The tools
- `speed_check.py` keeps the whole range, 5.0 to 1.0, so every difficulty's speeds can be heard. `stage_chooser.py` gains the difficulty as a choice, its start points by slot.

## Where it goes
- `game/game_scene.py`: START_SPEED and TOP_SPEED become the difficulty's, with a torch-rate factor; `InsideTheCave.py` and a new difficulty screen of rows; `game/home_screen_view_controller.py`, `game/result_view_controller.py` and `game/ranking_view_controller.py` for the three lists and the move of the old one; `platform/defaults.py` for the new keys.
- Tests: each difficulty's start, top and torch slots; the menu's rows, its last choice and Escape; Replay keeping the difficulty; three lists, each game saving into its own; the old `rank` becoming Easy's once and never again.
- Docs: `docks/readme.txt` (Play, the difficulties, Score), the changelog, `DIVERGENCES.md`, the todo list moved to Finished once the dev has heard it.
