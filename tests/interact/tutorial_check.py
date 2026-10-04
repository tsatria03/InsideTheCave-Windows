#!/usr/bin/env python
"""For testing by ear: the Tutorial.  Not a test, and not part of the game: the tests are in
``tests\\case``, and this is one of the tools in ``tests\\interact`` that you play.  Wear
headphones.

    python tests\\interact\\tutorial_check.py

A small window asks where to start, then the game itself takes the window:

    Up / Down       choose where to start, each one named
    D               debug mode on or off (off at first; on: nothing can catch you)
    Enter           start there
    Escape          quit, here; in the game, pause
    Alt+F4          quit, at any moment

The starting points:

     1  the tutorial as chosen from the main menu: the welcome in the Windows voice, then
        your keys, then the cave
     2  the tutorial as after Replay or Restart: no welcome, the cave after two seconds
     3  just after the closing line: the real game at speed 5.0, with nothing said

Things to listen for (aidocks/project_tutorial_plan.md,
aidocks/project_tutorial_teaching_plan.md and aidocks/project_tutorial_steered_plan.md):

* the teaching part (starts 1 and 2): exactly 12 things, a coin, a torch, a monster and
  bats in each cave lane, in a new order each time, none twice;
* only one in the cave at a time, the next coming 3 seconds after the last has passed you,
  been killed, or been caught; bats your torch frightened still have to pass you;
* each announced as it appears, wherever you stand: "A coin appeared in the left lane. Go
  there to grab it.", "A torch appeared in the middle lane. Go there to pick it up.", "A
  monster appeared in the right lane. Stay out of it, or throw your torch at it.", "Bats
  appeared in the left lane. Stay out of that lane, or throw your torch to scare them
  off."; without a torch, no throw;
* "Coin passed, in the left lane." and so on, and nothing for a coin or torch you took or
  a monster you killed; "Coin caught." and "Torch caught.";
* cutting in at once: each arrival, passed and caught line, "The monster was hit! It's
  gone.", "The bats were hit, and dodged to your left.", "Your torch flew off without
  hitting anything.", and on the first throw "You're out of light now. Find another torch
  soon.";
* after the 12th, the closing line, waiting for the one before to finish: "Well done!
  You've met everything in the cave! Now practice what you've learned, just like the real
  game, but at a steady pace. I'll stay quiet from here, so trust your ears.";
* once it is said (and from the start in start 3): your screen reader saying "Tutorial
  finished. Practice as long as you like, or press Enter to skip it and go to the main
  menu.", then the real game, a monster or bats with a coin or torch beside it at times,
  the cave at 5.0, and no tutorial line at all;
* Enter in the practice: "Practice skipped. Main menu. Play"; Enter in the lessons, nothing;
* throughout: your footsteps walking, S "No score to report.", E "No speed to report.", C
  your coins, Control stopping the voice;
* caught: "You were caught.", Replay (no welcome, a new 12) and Menu; nothing saved.

**Your save is never touched**: its own save in
``%APPDATA%\\InsideTheCave\\tutorial_check``, with a copy of your key bindings and volume
settings each time it starts.
"""
from __future__ import annotations

import os
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, ROOT)
sys.path.insert(0, HERE)

import platform_check                                            # noqa: E402
from platform_check import Quit, Window                          # noqa: E402

platform_check.SAVE_NAME = 'tutorial_check'
Window.TITLE = 'Inside The Cave - tutorial check'

#: (what it is, with the welcome, straight to the real game after the closing line)
STARTS = (('the tutorial as chosen from the main menu, with its welcome', True, False),
          ('the tutorial as after Replay, without the welcome', False, False),
          ('just after the closing line: the real game at speed 5.0, nothing said', False,
           True))


def choose():
    """The window's menu; returns (welcome, practice, debug), or None to quit."""
    from insidethecave.platform.speech import Speech
    speech = Speech.shared()
    window = Window()
    index, debug = 0, False

    def say(text):
        print(text)
        window.show(text)
        speech.speak(text)

    def item():
        return '%d of %d: %s.' % (index + 1, len(STARTS), STARTS[index][0])

    try:
        say('Tutorial check. Up and Down to choose, D for debug mode, Enter to start, '
            'Escape to quit.')
        speech.speak(item(), interrupt=False)
        window.show(item())
        while True:
            for name in window.keys():
                if name == 'escape':
                    return None
                if name in ('up', 'down'):
                    index = (index + (1 if name == 'down' else -1)) % len(STARTS)
                    say(item())
                elif name == 'd':
                    debug = not debug
                    say('Debug mode %s.' % ('on' if debug else 'off'))
                elif name in ('return', 'enter'):
                    _label, welcome, practice = STARTS[index]
                    return welcome, practice, debug
                else:
                    say(item())
            time.sleep(0.02)
    except Quit:
        return None
    finally:
        window.close()


def main():
    platform_check._own_save()
    picked = choose()
    if picked is None:
        return 0
    welcome, practice, debug = picked

    import InsideTheCave

    class Args:
        game = None
        stage = False
        verbose = False

    Args.debug = debug

    class TutorialApp(InsideTheCave.App):
        def start_game(self):
            super().start_game()
            s = self.game.scene
            if practice:                    # the teaching part over before it began
                s.lessons.clear()
                s.teaching = False
                s.sayPracticeHint()

    app = TutorialApp(Args())
    if welcome:
        app.kind = 'menu'                  # as if chosen there, so with its welcome
    app.run('tutorial')
    return 0


if __name__ == '__main__':
    sys.exit(main())
