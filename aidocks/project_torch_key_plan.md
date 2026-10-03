---
name: project_torch_key_plan
description: "PLANNED 2026-10-03, waiting for the go-ahead: a rebindable T key that says the torch's state in five slot-based levels, and the throw key saying \"No torch to throw.\" when there is none. For the fourth release."
metadata:
  type: project
---

**Status: planned, agreed with the dev on 2026-10-03, not built.** The dev: "Do not modify any code yet." Two items in `docks/todo list.txt` under Unfinished. Built only on the dev's go-ahead ([[feedback_record_plans_first]]).

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
