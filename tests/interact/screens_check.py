#!/usr/bin/env python
"""For testing by ear: the screens of phase 4.  Not a test, and not part of the game: the
tests are in ``tests\\case``, and this is one of the tools in ``tests\\interact`` that you
play.  Wear headphones.

    python tests\\interact\\screens_check.py

A small window asks where to start, then the game itself takes the window:

    Up / Down       choose where to start, each one named
    Enter           start there
    Escape          quit, here
    Alt+F4          quit, at any moment

The starting points:

     1  the whole program, from the earphone warning
     2  the result screen at once, with a made-up score of 150 and 4 coins,
        which gets into the ranking at third place
     3  the result screen at once, with a made-up score of 5, too low to get in
     4  straight into a game, to try the pause menu (P or Escape) and a real game over

Each start writes a made-up top five first, so you know what to expect on the Score screen:

     1, Ana, 300   2, Ben, 200   3, Cleo, 100   4, Dev, 50   5, Eli, 10

Things to listen for:

* the warning, then the menu after 3 seconds, or at once on a key;
* the menu: Play, Score, Quit; Up, Down, Home, End, Enter; Escape quits;
* the result screen: "Game over. Score 150. Coins 4. Insert name"; each letter said as you
  type it, Backspace saying what it took, at most 15 characters; Enter in the name goes on
  to Replay; Replay and Menu (and Escape) save first, a blank name as "unnamed player";
* the Score screen afterwards, with your name in the right place;
* the pause menu: "Paused. Resume", then Restart and Quit to menu; Escape or P resumes.

**Your save is never touched**: its own save in
``%APPDATA%\\InsideTheCave\\screens_check``, with a copy of your key bindings and volume
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

platform_check.SAVE_NAME = 'screens_check'
Window.TITLE = 'Inside The Cave - screens check'

STARTS = (('the whole program, from the earphone warning', 'warning', None),
          ('the result screen, score 150 and 4 coins, third place', 'result', (150, 4)),
          ('the result screen, score 5, too low to get in', 'result', (5, 0)),
          ('straight into a game, for the pause menu and a game over', 'game', None))
SAMPLE_RANK = [{'Name': n, 'Score': s} for n, s in
               (('Ana', '300'), ('Ben', '200'), ('Cleo', '100'), ('Dev', '50'),
                ('Eli', '10'))]


def choose():
    """The window's menu; returns the chosen start, or None to quit."""
    from insidethecave.platform.speech import Speech
    speech = Speech.shared()
    window = Window()
    index = 0

    def say(text):
        print(text)
        window.show(text)
        speech.speak(text)

    def item():
        return '%d of %d: %s.' % (index + 1, len(STARTS), STARTS[index][0])

    try:
        say('Screens check. Up and Down to choose, Enter to start, Escape to quit.')
        speech.speak(item(), interrupt=False)
        window.show(item())
        while True:
            for name in window.keys():
                if name == 'escape':
                    return None
                if name in ('up', 'down'):
                    index = (index + (1 if name == 'down' else -1)) % len(STARTS)
                    say(item())
                elif name in ('return', 'enter'):
                    return STARTS[index]
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
    _label, first, made_up = picked

    import InsideTheCave

    class Args:
        game = None
        stage = False
        debug = False
        verbose = False

    app = InsideTheCave.App(Args())
    app.defaults.setObject_forKey_([dict(e) for e in SAMPLE_RANK], 'rank')
    app.defaults.setInteger_forKey_(3, 'countTutorial')
    app.defaults.synchronize()
    if made_up is not None:
        app.over = made_up                 # as if a game had just ended
    app.run(first)
    return 0


if __name__ == '__main__':
    sys.exit(main())
