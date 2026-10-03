---
name: project_tutorial_plan
description: "PLANNED 2026-10-03, waiting for the go-ahead: a Tutorial row after Play: speed held at 5.0, one thing at a time, every coin, torch, monster and bats announced in an English Windows voice as it appears, throws explained, \"You were caught.\" with Replay or Menu and nothing saved. Play gives the key hints on the first 2 games only; the original's 3-game instructions line goes."
metadata:
  type: project
---

**Status: planned, agreed with the dev on 2026-10-03 ("Yes, all good here."), not built.** Settled one question at a time. Built only on the dev's go-ahead ([[feedback_record_plans_first]]). It replaces the todo item "a row to the main menu that says the instructions at any time". Waiting with it: [[project_torch_key_plan]].

**Why:** the original's tutorial is one sentence on the first three games, speaking of swipes and taps, then never again. The dev: "Please add a tutorial option in the main menu after play. In this mode, the speed will not go below 5.0. You can still die ... Also, for special items, like coins and torches, it will announce what it is, and where you need to go to get it. This will also use your windows voice. ... This ilimenates the origenal quick tutorial you'll here for the first 3 games."

## The Tutorial row
- On the main menu right after Play: Play, Tutorial, Score, Quit.

## Starting it
- From the main menu: the welcome, in the Windows voice (`TutorialVoice`), then the key hints from the player's own bindings, as now, then the first slot once both are done. The welcome (the dev chose a new line over the original's, which speaks of swipes and taps):
  "Welcome to the tutorial. You're in a dark cave with three lanes, and things will come down them toward you. I'll tell you what each one is, and what to do. The cave won't speed up here, so take your time."
- **English only for now** (the dev: "Let's do english only for now."): every tutorial line is English, said in an English voice (`voice.choose('en')`); translation would be a later project covering the whole port.
- **Replay, and the pause menu's Restart, skip the welcome** (the dev: "Skip it if you restart the tutorial."): the first slot after the usual 2 s.

## The game in the tutorial
- **Speed held at 5.0** (the dev: "held at 5.0"): the speed-up every 20 slots never applies. You can still die; the water at 81 and ice at 161 still come.
- **Easy's torch**, 1.5 times as long, about 105 slots (the dev, while planning the difficulties: "I want the easy longer one."). The tutorial is not a difficulty and asks for none ([[project_difficulty_plan]]).
- **No score at all** (the dev, while planning the status keys: "I want the score system to be switched off entirely in the tutorial."): the score loop does not run and coins add nothing to it; coins are still counted. The status keys there: C "Coins, 3.", S "No score to report.", E "No speed to report." ([[project_status_keys_plan]]).
- **One thing at a time** (the dev: "a coin and a bat cannot appear in the same lane. Only in the tutorial."): a coin or torch that would come with a monster or bats (`coinTogether`, `torchTogether`, objectHeight 4) waits for the next empty slot and comes there on its own (the dev: "Move it to the next empty slot if possible."). That is nearly always the very next slot, since objectHeight is then 0 and no lone pickup comes that round. Normal games are unchanged.

## Announcements, in the Windows voice
- **When each thing appears** at the top of the cave, about 3 to 4 s before it reaches the player at 5.0; its own sound still plays at its moment (the dev agreed, after asking for a recommendation).
- **Danger first:** a monster or bats line cuts off a coin or torch line; a coin or torch line waits for the one before it, never cutting off anything.
- **Conversational** (the dev: "It should be more conversational. Example, A coin appeared on your left... Not too long though."; "I love it!"). Directions are from the player's lane when said; from a side lane the far lane is "two lanes to your left" and "move left twice".
  - Coin: "A coin appeared on your left. Move left to grab it." / "A coin is coming right at you. Stay where you are." / "... on your right. Move right to grab it."
  - Torch: "A torch appeared on your right. Move right to pick it up." / "A torch is coming right at you. Stay where you are."
  - Monster in your lane: "A monster is coming right at you! Move left or right." (from a side lane the one way out: "Move right!"), adding ", or throw your torch at it." when there is a torch to throw. In another lane: "A monster appeared on your left. Stay out of its way."
  - Bats (the dev: "it should give announcements for monsters and bats too."): "Bats are coming right at you! Move left or right." with ", or throw your torch to scare them off." when there is a torch; "Bats appeared on your right. Stay out of their way."
- **After a throw** (the dev: "It should say a monster/bat was hit"):
  - a monster: "The monster was hit! It's gone."
  - bats: "The bats were hit, and dodged to your left." (the side from the player)
  - neither, the torch leaving the top: "Your torch flew off without hitting anything."
  - the first throw of each tutorial adds: "You're out of light now. Find another torch soon."

## Dying in the tutorial
- **Nothing counts** (the dev: "Scores should not count what so ever. It's purely for practice."): no best five, no lifetime stats, no name, nothing saved.
- A short screen (the dev chose it): "You were caught.", then rows Replay and Menu; Escape is Menu. Replay starts the tutorial again without the welcome.

## Play
- **The key hints only on the first 2 games** (the dev: "if you click play, your screen reader key hints should speak. So for the first 2 games, and on the third game, it's silent."): through the screen reader, as now, then the first slot; from the third game, the first slot after the original's 2 s with nothing said.
- **The original's instructions line is never said** (`GameScene.tutorial`'s six-language line, 0x10000dea8, and the SAPI voice for it): a divergence for `DIVERGENCES.md`. `countTutorial` (the save's key) keeps counting Play games, as the original did (0x10000e5bc), so a save with 2 or more already starts silent; tutorial games do not count.

## Where it goes
- `game/home_screen_view_controller.py` (the row), `InsideTheCave.py` (the screen loop: 'tutorial', and its game-over screen), `game/game_scene.py` and `game/game_view_controller.py` (a tutorial flag: the held speed, the moved companion, the announcements and throw lines, the start), a small screen for "You were caught.".
- Tests: the row and its place; the speed held; no two things in one slot and the companion's move; each announcement by lane, and danger cutting off a pickup; the throw lines; nothing saved; Replay without the welcome; Play's hints on the first 2 games only and never the original's line.
- By ear: the dev plays it from the menu; `screens_check.py` gains a start straight into the tutorial ([[feedback_interactive_tests]]).
- Docs: `docks/readme.txt` (the menu, a Tutorial section, the first games), the changelog, `DIVERGENCES.md`, the todo list moved to Finished only once the dev has heard it.
