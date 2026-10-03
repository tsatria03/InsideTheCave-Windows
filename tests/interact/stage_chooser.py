#!/usr/bin/env python
"""For testing by ear: start the real game at a chosen point.  Not a test, and not part of
the game: the tests are in ``tests\\case``, and this is one of the tools in
``tests\\interact`` that you play.  Wear headphones.

    python tests\\interact\\stage_chooser.py

A small window asks where to start, then the game itself takes the window:

    Up / Down       choose where to start, each one named
    Enter           start there
    T               the tutorial line on or off (on: as on a first game)
    D               debug mode on or off (nothing can kill you)
    Escape          quit, here; in the game, pause
    Alt+F4          quit, at any moment

The starting points:

     1  the beginning, as a new game
     2  slot 75, a little before the cave turns to water at 81
     3  slot 155, a little before the ice at 161
     4  slot 340, at the top speed (speedMonster about 1.96)

Starting later sets the slot count and the speed the game would have reached there, and
the cave it would be in; everything else starts as a new game does.  After a game over,
Enter starts again from the same point.

**Your save is never touched**: its own save in
``%APPDATA%\\InsideTheCave\\stage_chooser``, with a copy of your key bindings and volume
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

platform_check.SAVE_NAME = 'stage_chooser'
Window.TITLE = 'Inside The Cave - stage chooser'

STARTS = (('the beginning, as a new game', 0),
          ('slot 75, a little before the water', 75),
          ('slot 155, a little before the ice', 155),
          ('slot 340, at the top speed', 340))


def speed_at(slot):
    """speedMonster after ``slot`` slots: -0.12 every 20th while 2.0 or more
    (createObjectScene, 0x10000c958..0x10000c9a0)."""
    s = 4.0
    for k in range(1, slot + 1):
        if k % 20 == 0 and s >= 2.0:
            s += -0.12
    return s


def choose():
    """The window's menu; returns (slot, tutorial, debug), or None to quit."""
    from insidethecave.platform.speech import Speech
    speech = Speech.shared()
    window = Window()
    index, tutorial, debug = 0, False, False

    def say(text):
        print(text)
        window.show(text)
        speech.speak(text)

    def item():
        return '%d of %d: %s.' % (index + 1, len(STARTS), STARTS[index][0])

    try:
        say('Stage chooser. Up and Down to choose, Enter to start, T for the tutorial, '
            'D for debug mode, Escape to quit.')
        speech.speak(item(), interrupt=False)
        window.show(item())
        while True:
            for name in window.keys():
                if name == 'escape':
                    return None
                if name in ('up', 'down'):
                    index = (index + (1 if name == 'down' else -1)) % len(STARTS)
                    say(item())
                elif name == 't':
                    tutorial = not tutorial
                    say('Tutorial %s.' % ('on' if tutorial else 'off'))
                elif name == 'd':
                    debug = not debug
                    say('Debug mode %s.' % ('on' if debug else 'off'))
                elif name in ('return', 'enter'):
                    return STARTS[index][1], tutorial, debug
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
    slot, tutorial, debug = picked

    import InsideTheCave
    from insidethecave.game import game_scene as G

    class Args:
        game = None
        stage = True
        verbose = False

    Args.debug = debug

    class ChooserApp(InsideTheCave.App):
        def start_game(self):
            self.defaults.setInteger_forKey_(0 if tutorial else 3, 'countTutorial')
            self.defaults.synchronize()
            super().start_game()
            s = self.game.scene
            s.countObjectScene = slot
            s.speedMonster = speed_at(slot)
            if slot >= G.ICE_AT:
                s.currentScenario = G.ICE
            elif slot >= G.WATER_AT:
                s.currentScenario = G.WATER
            self.game.changeCoinCounterWithScenario(s.currentScenario)
            self.speech.speak('Starting at slot %d, speed %.2f.' % (slot, s.speedMonster),
                              interrupt=False)

    ChooserApp(Args()).run()
    return 0


if __name__ == '__main__':
    sys.exit(main())
