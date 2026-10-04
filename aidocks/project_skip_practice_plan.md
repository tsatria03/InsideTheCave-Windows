---
name: project_skip_practice_plan
description: "FINISHED 2026-10-03, confirmed by the dev: once the tutorial's closing line has been said, the screen reader says \"Tutorial finished. Practice as long as you like, or press Enter to skip it and go to the main menu.\"; a new rebindable action, \"Skip the practice\" (Enter), says \"Practice skipped.\" and goes to the main menu. Optional; before the closing line it does nothing."
metadata:
  type: project
---

**Status: FINISHED 2026-10-03, confirmed by the dev by ear ("All good here.").** Built on the dev's go-ahead ("Yes, you can build and run your full tests."); agreed the same day one question at a time.

**As built:** `platform/keymap.py` (`skip_practice`, "Skip the practice", Enter); `game/game_scene.py` (`PRACTICE_HINT`, `TUTORIAL_FINISHED`, `PRACTICE_SKIPPED`; `sayPracticeHint`, said by `watchLesson` as `teaching` turns off; `practicing`); `ui/game_input.py` (the action sets `request` to 'skip' only while `practicing`); `InsideTheCave.py` (`follow` on 'skip' goes to the menu with `menu_before`); `game/home_screen_view_controller.py` (`before`, said in the same breath as "Main menu": "Practice skipped. Main menu. Play"). Tests: `keymap.py` (the default, the label, at once, an old file gaining it), `gameplay.py` (the hint after the closing line and never before, no practice during the lessons or in Play, the hint without a key), `app.py` (Enter in the lessons does nothing; in the practice, the menu with "Practice skipped.", nothing counted). `tests/interact/tutorial_check.py`'s start 3 says the hint. Follows [[project_tutorial_steered_plan]]: the Tutorial row now holds the lessons (the 12) and the practice after them (the real game at 5.0).

**Why:** the dev: "Can you add a new thing where enter can skip the practice, but only after the closing line of the teaching lessons? Also your screen reader should tell you how to do it, just like it does for the key hints in the beginning of the tutorial. If the user presses enter, it will say practice skipped. I say practice because the tutorial option in the main menu does double dooty."

## The key
- A new action in `platform/keymap.py`'s `ACTIONS`, **rebindable in F1** (the dev: "make this bindable."): label **"Skip the practice"**, default **Enter**. Enter is free in a game (typing a name is only on the result screen). An older `keys.json` gains it, as it gained T, S, C and E.
- **Works only in the tutorial's practice**: once the closing line has been said (`GameScene.teaching` off), the player alive and the game not paused. Before that, in Play, on the pause menu or after death, it does nothing.
- **Optional** (the dev: "skipping the practice area is completely optional."): without it, the practice goes on until the player is caught, as now.

## The hint
- Once the closing line has been said, **through the screen reader**, as the key hints at the start (the dev: "your screen reader should tell you how to do it, just like it does for the key hints"), from the player's own binding (`keymap.hint_keys`); the dev's wording, then option 3 of Claude's (the dev: "I like option 3 the best."):
  "Tutorial finished. Practice as long as you like, or press Enter to skip it and go to the main menu."
- Said once a tutorial. If the action has no key bound, the hint says only "Tutorial finished."

## Pressing it
- The screen reader says **"Practice skipped."**, then the **main menu**, on Play (the dev, first "It should start the actual game", then: "Actually on second thought, the main menu because you need to choose a difficulty any way."). "Practice skipped." is said so the menu's own announcement does not cut it off.
- Nothing is saved or counted, as in the rest of the tutorial.

## Where it goes
- `platform/keymap.py` (the action, label, default, an older `keys.json` gaining it), `ui/game_input.py` (the action), `game/game_scene.py` (the hint when `teaching` turns off; `skipPractice` answering only in the practice), `game/game_view_controller.py` and `InsideTheCave.py` (leaving the game for the menu, as Quit to menu does, with nothing saved).
- Tests: `keymap.py` (the action, Enter, rebindable, an old `keys.json`), `gameplay.py` (the hint after the closing line, with the player's key, and not before; nothing before the closing line or in Play), `app.py` (Enter in the practice: "Practice skipped.", the main menu, nothing counted; Enter in the lessons does nothing).
- By ear: `tests/interact/tutorial_check.py` (its start just after the closing line, and starts 1 and 2 through the lessons).
- Docs: `docks/readme.txt` (the Tutorial section, the controls, the F1 list), the changelog, the todo list, `DIVERGENCES.md`.
