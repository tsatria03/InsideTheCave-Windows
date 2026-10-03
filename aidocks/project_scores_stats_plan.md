---
name: project_scores_stats_plan
description: "PLANNED 2026-10-03, waiting for the go-ahead: the result screen as rows (Score, Coins, Time survived, Speed reached, name, Replay, Menu); the main menu Play, Tutorial, Scores, Stats, Quit; Scores per difficulty, each entry one line with coins and time; Stats per difficulty and All-time, ten rows in the dev's order."
metadata:
  type: project
---

**Status: planned, agreed with the dev on 2026-10-03, not built.** Settled one question at a time. Built only on the dev's go-ahead ([[feedback_record_plans_first]]). Builds on [[project_difficulty_plan]] (a best five for each difficulty) and [[project_status_keys_plan]] (the speed count).

**Why:** the dev's picks: "Make the result screen also say how long you survived and the top speed you reached." and "Add lifetime stats to the Score screen: games played, total coins and your longest run.", grown in planning.

## The main menu
- **Play, Tutorial, Scores, Stats, Quit** (the dev: "What about a menu option called stats?"; "Also score should be scores in the main menu."). The original's button title is "score"; "Scores" is a port change for `DIVERGENCES.md`.

## The result screen
- **Separate rows** (the dev: "I think I want seprat rows so everything is not crammed into one line."), the facts first, the screen starting on Score (the dev chose it):
  1. "Score, 412."
  2. "Coins, 7."
  3. "Time survived, 3 minutes 12 seconds."
  4. "Speed reached, 18."
  5. the name field, "Insert name"
  6. Replay
  7. Menu
- Arriving says "Game over. Score, 412.". The fact rows do nothing on Enter; typing goes only into the name field, as now.
- **The time in words** (the dev: "I want it spoken in words, like 3 minutes 12 seconds."): "45 seconds" under a minute, "1 minute", "1 second" in the singular, whole seconds. Counted from the first slot to being caught; the instructions before it and any time paused do not count.
- **The speed** is the status keys' count, 0 to 40 (the times the cave has sped up); the speed only rises in a game, so the last is the top reached.

## Scores
- Scores asks for Easy, Medium or Hard ([[project_difficulty_plan]]), then reads that best five.
- **Each entry is one line** (the dev: "for each player, the stats should read out in one line. Example. 1, unnamed player. Score, 447. Coins, 15. Time, 3 minutes 12 seconds."): each saved entry gains its coins and time.
- **Older entries leave out what was never saved** (the dev: "Leave out the missing info."): "2, Ana. Score, 300.". The default entries read "4, Player. Score, 0.".
- Then a Menu row; Escape or Menu goes back to the difficulty choice, Escape again to the main menu.

## Stats
- Stats asks for **Easy, Medium, Hard or All-time** (the dev: "Per difficulty, and an opion for all time stats."), then reads that set as rows, **in the dev's order**:
  1. "Games played, 24."
  2. "Longest run, 3 minutes 12 seconds."
  3. "Fastest speed reached, 28."
  4. "Total coins, 183."
  5. "Total time played, 1 hour 14 minutes." (hours from an hour on; "45 minutes 10 seconds" under it)
  6. "Torches picked up, 30."
  7. "Bats frightened, 12." (bats a thrown torch hit, which dodged)
  8. "Monsters killed, 41." (by a thrown torch)
  9. "Bats dodged, 87."
  10. "Monsters dodged, 140."
  11. Menu
- **Dodged** (the dev: "I like Bats frightened, Bats dodged, and monsters dodged"): a monster or bats in the player's lane when its roar or sound played (the sensor), which then passed without catching the player. One in another lane all along does not count; a bat a torch frightened counts as frightened, not dodged.
- **All-time** adds the three difficulties up; its longest run and fastest speed are the best of the three.
- **Counting starts with the update:** past games were never counted, so every stat starts at 0 (the old best five still becomes Easy's). **Tutorial games never count** ([[project_tutorial_plan]]).
- A game is counted only when it ends by being caught, as a score is saved only then; Restart and Quit to menu count nothing (the dev: "restarts and quits do not count in a game.").

## Where it goes
- `game/result_view_controller.py` (the rows, the time and speed, saving coins and time with the entry), `game/ranking_view_controller.py` (the one-line entries, per difficulty), a new stats screen and the difficulty choice before each, `game/home_screen_view_controller.py` (the five rows), `game/game_scene.py` and `game/game_view_controller.py` (the run's time without pauses, the speed reached, the counts of kills, frights, dodges and pickups), `platform/defaults.py` (the stats in the save).
- Tests: the result rows and their words, the time's wording, a pause not counted, entries with and without coins and time, every stat counted and kept per difficulty, All-time's sums and bests, tutorial games and quits not counted, dodges only in your lane.
- Docs: `docks/readme.txt` (the menu, the result screen, Scores, Stats), the changelog, `DIVERGENCES.md`, the todo list moved to Finished once the dev has heard it.
