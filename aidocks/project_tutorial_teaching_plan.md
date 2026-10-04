---
name: project_tutorial_teaching_plan
description: "FINISHED 2026-10-03, confirmed by the dev: the tutorial teaches each kind of thing once per cave lane (12 arrivals at most), the cave's lanes named, every line cutting in but the closing line, which waits its turn, a closing line once all 12 are taught; Ctrl skips one line."
metadata:
  type: project
---

**Status: FINISHED 2026-10-03, confirmed by the dev by ear with `tutorial_check.py` ("Okay you can commit."), the dev already planning a different tutorial next.** Built on the dev's go-ahead ("Yes. This will be the first change for the 4th release."); agreed the same day one question at a time.

**As built:** `game/game_scene.py`: `LANE_NAMES`, `ARRIVAL`, `TUTORIAL_CLOSING`, `PASSED` with the lane; `_taught`, (kind, cave lane) pairs; `announcement(node, lane)`; `announce` says an untaught arrival at once, marks it taught, watches it, and queues the closing line after the 12th; `_nextLine` says the next line waiting; `tutorialSay` queues, `urgent` speaks at once without clearing the queue; `hushTutorial` only frees the voice; the throw lines and `OUT_OF_LIGHT` urgent; `_speakingUrgent` and `where` gone. "You're out of light now." stays on the first throw only, as before. `InsideTheCave.py`: `App.hush`'s docstring. Tests: `gameplay.py` (the cave lanes' words from every lane, once per kind and lane then the closing line, arrivals and throw lines cutting in while the rest wait, Ctrl skipping one, passed lines with the lane, caught every time, the throw lines), `app.py` (Ctrl frees the voice and keeps the next line). `tests/interact/tutorial_check.py`'s notes. It changes the finished [[project_tutorial_plan]]'s announcements; the rest of the tutorial (speed held at 5.0, one thing a slot, no score, the welcome, "You were caught.") stays as it is.

**Why:** the dev: "Instead of speaking every single time an entity appears, I was thinking that when an entity of any type appears in any of the lanes, it will speak based on where it came from for each entity. It will do that for each lane. ... It will do this non interuptively, unless control is pressed of course, witch in that case will just interupt one line and go onto the next one." Then: "It gives people the feel for what's going to be in a level without bombarding them with so much info over and over."

## Arrivals: taught once per kind, per cave lane
- An arrival line is said only the **first time each kind** (coin, torch, monster, bats) **appears in each cave lane** (left, middle, right): 12 at most. After that, that kind in that lane is silent.
- **The cave's lanes, not the player's** (the dev: "Name the cave lanes."): the words stay true however long a line waits. The 12 "taught" marks use the same lanes (`laneOf`).
- **They interrupt** (changed after the dev heard them wait: "Please make all 12 lines interupt. It whent back to speaking them all at once."): each is said the moment its thing appears, cutting off the line being said, as the torch lines do; the lines waiting carry on after it. First built waiting their turn, with stale arrivals skipped (the dev, on Claude's recommendation: "Yes please."); said at once, an arrival can no longer go stale, so that part is gone.
- The words (the dev: "I like these lines."):
  - "A coin appeared in the left lane. Go there to grab it."
  - "A torch appeared in the middle lane. Go there to pick it up."
  - "A monster appeared in the right lane. Stay out of it, or throw your torch at it." Without light: "A monster appeared in the right lane. Stay out of it."
  - "Bats appeared in the left lane. Stay out of that lane, or throw your torch to scare them off." Without light: "Bats appeared in the left lane. Stay out of that lane."
- The "coming right at you" lines and "Move left", "two lanes to your right" go: the cave lane is the same wherever the player stands.

## Passed lines
- Like the arrivals (the dev: "It should be like the arriveals."): said **only for a thing whose arrival was announced**, naming its cave lane (the dev: "Yes something like, coin past, on your left, on your right, in the middle."):
  - "Coin passed, in the left lane." / "Torch passed, in the middle lane." / "Monster passed, in the right lane." / "Bats passed, in the left lane."
- **They interrupt**, as the arrivals (the dev, after hearing them wait: "It still does not interupt. Example. When the monster past, it did not cut off the previous speech."). First built waiting their turn.

## Caught lines
- "Coin caught." and "Torch caught." are said **every time** (the dev: "For coin and torch caught, those can continue to speak. Those aren't as spammy."), and **interrupt** (the dev: "These should interupt as well."). First built waiting their turn. Only the closing line now waits.

## Torch lines
- "The monster was hit! It's gone.", "The bats were hit, and dodged to your left.", "Your torch flew off without hitting anything." and "You're out of light now. Find another torch soon." are said **every time** and **interrupt** (the dev: "it should interupt, not wait."): each cuts off the line being said and is said at once; the lines waiting carry on after it.

## The closing line
- Once all 12 arrivals have been said (the dev: "Do a closing line."): "You've met everything in the cave. From now on, listen for them yourself.", waiting its turn, said once a tutorial. Replay starts the teaching over, as a new tutorial.

## Ctrl
- **Skips one line**: cuts off the line being said, and the next waiting line follows (it now drops every waiting line).

## Where it goes
- `game/game_scene.py`: `announcement`, `announce`, `watchPassing`, `_caught`, `tutorialSay` (waiting by default, `urgent` interrupting without clearing the queue), `hushTutorial`, `PASSED`, a closing-line constant, the 12 taught marks.
- Tests (`gameplay.py`): once per kind and lane, the cave lanes' words, the arrivals and torch lines cutting in and the queue carrying on, passed only for an announced thing, caught every time, the closing line after the 12th, Ctrl skipping one line.
- By ear: `tests/interact/tutorial_check.py` ([[feedback_interactive_tests]]).
- Docs: `docks/readme.txt` (the Tutorial section), the changelog, `DIVERGENCES.md` if it names the tutorial's lines, the todo list (Finished only once the dev has heard it), [[project_tutorial_plan]] pointing here.
