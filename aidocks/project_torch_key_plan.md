---
name: project_torch_key_plan
description: "FINISHED 2026-10-03, confirmed by the dev: a rebindable T key that says the torch's state in five slot-based levels, and the throw key saying \"No torch to throw.\" when there is none. For the fourth release."
metadata:
  type: project
---

**Status: FINISHED 2026-10-03, confirmed by the dev by ear ("Everything past.").** Built on the dev's go-ahead ("Let's start with the first 1."), planned and agreed the same day (the dev had said "Do not modify any code yet." until then). Its two todo items are in Finished ([[feedback_record_plans_first]]).

**As built:** `keymap.py` (`torch`, "Say the torch", T; an older `keys.json` gains it, less any key the player already uses elsewhere), `game_input.py` (`sayTorch`), `game_scene.py` (`TORCH_STATES`, `torchState`, `sayTorch`, and `NO_TORCH_TO_THROW` in `throwTorch`, its checks reordered so death and the instructions refuse silently first). The levels fall one slot behind the round numbers below, as the falloff adds up in doubles: full 0 to 20, half 21 to 40, low 41 to 61 (with the game's own "Torch low"), almost out 62 to 69 (the last 8), none from 70. Tests: `gameplay.py` (the levels against the game's own moments, after a throw and death, the throw key's words and silences), `keymap.py` (T by default, an older file gaining it, a key the player uses kept), `screens.py` (T reaches the game, not the pause menu). `torch_check.py` describes T and the no-torch throw.

**Why:** the torch's state was a picture in the original (the light's `falloff` shrinking round the player), which the port does not draw. By ear there is the burning loop, which loses only about a quarter of its volume over a torch, "Torch low" once, about 29 slots before it dies, and the burnout sound. Between "Torch low" and burnout nothing says how close it is, after burnout only the loop's absence says there is no torch, and a throw with no torch does nothing at all. The dev asked whether the game says when it is about to go out: it does, once, with "Torch low"; there is no closer warning, and none was asked for.

## 1. The T key: the torch's state

- **A new action**, `torch`, in `platform/keymap.py`'s `ACTIONS`, default **T**, **rebindable in F1** like the others (the dev: "I want it to be rebindable."). Its F1 label along the lines of "Say the torch". A `keys.json` saved before it exists must get T added, not lose it.
- **Option A, levels by slot** (the dev: "I like the slot method for option A. Agreed."). Read from `falloffSize`, so it is exact at any speed and agrees with the game's own "Torch low":

| Says | When, in slots after a pickup | falloffSize |
|---|---|---|
| "Torch full." | 0 to 19 | 2.0 up to 2.5 |
| "Torch half." | 20 to 39 | 2.5 up to 3.0 (`FALLOFF_DIM`) |
| "Torch low." | 40 to 60, from the game's "Torch low" | 3.0 up to 4.44 |
| "Torch almost out." | the last 8 slots | 4.44 up to 5.0 (`FALLOFF_LAST`) |
| "No torch." | burnt out, or thrown | 5.0 or more (`FALLOFF_OUT` after either) |

  A torch rises 0.025 a slot from 2.0 to 3.0 (40 slots), then 0.07 a slot to 5.0 (about 29), so about 69 slots in all (`changeFalloffSize`, 0x100023a0c). The almost-out boundary is 5.0 - 8 x 0.07 = 4.44. At speed 5.0 a level lasts about 16 s; at 1.0 about 3 s (accepted: the dev chose slots over time).
  **With the difficulties** ([[project_difficulty_plan]]) the torch burns at a different rate on Easy and Hard, so the levels are the falloff points in the table, not fixed slot counts: the slot counts above are Medium's; "Torch half." comes from slot 31 on Easy and 16 on Hard, "Torch low." from 62 and 32, "Torch almost out." from 92 (the last 13) and 47 (the last 7).
- **When it works:** whenever a game is running, the instructions included; not on the pause menu (its keys are the menu's), and not after death. Said through the screen reader, interrupting, as the game's other messages (`GameScene.say`).

## 2. The throw key with no torch

- When the throw key (W or Up Arrow by default) is pressed with no torch, `falloffSize` at `FALLOFF_LAST` or more, the screen reader says **"No torch to throw."** (the dev's choice of the wordings offered).
- The game's other refusals stay silent, as now: during the instructions (`blockPlayer`, 0x100011164) and in the second after death (the port's own fix).
- The throw itself is unchanged when there is a torch.

## Where it goes

- `insidethecave/game/game_scene.py`: a `torchState()` returning the wording, and the "No torch to throw." branch in `throwTorch`, both port additions citing `changeFalloffSize` and `throwTorch` (0x10001111c).
- `insidethecave/platform/keymap.py` and `insidethecave/ui/game_input.py`: the `torch` action and its key.
- Tests: each level at its boundary slots, "No torch." after burnout and after a throw, "No torch to throw." only with no torch, silence during the instructions and after death, T in F1 and rebindable, an old `keys.json` gaining T.
- By ear: `tests/interact/torch_check.py` gains T and the no-torch throw, since its three starts already cover full, low, burning out and thrown ([[feedback_interactive_tests]]).
- Docs: `docks/readme.txt` (controls, the torch section, the F1 list), the changelog's `unrelease:` block, `DIVERGENCES.md` (with "Torch low"), the todo list moved to Finished only once the dev has heard it.
