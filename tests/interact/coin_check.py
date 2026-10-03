#!/usr/bin/env python
"""For testing by ear: the coins, with nothing else coming.  Not a test, and not part of the
game: the tests are in ``tests\\case``, and this is one of the tools in ``tests\\interact``
that you play.  Wear headphones.

    python tests\\interact\\coin_check.py

A small window asks where to start, then the game itself takes the window:

    Up / Down       choose where to start, each one named
    Enter           start there
    Escape          quit, here; in the game, pause
    Alt+F4          quit, at any moment

The starting points:

     1  coins as usual: the coins the game sends, where it sends them, and nothing else
     2  more coins: a coin also where each monster or bat and each torch would have been,
        so coins come several times as often, sometimes two at once in different lanes

Each coin dings from its lane as it comes down; be in its lane to take it.  Nothing else
comes down the cave: no monsters or bats, so nothing can kill you and no roars talk over the
coins, and no torches.  Your own torch does not burn down, so "Torch low" never comes.  The
window shows the coins you have taken.  The game starts without the tutorial line; the
pause menu's Restart starts again.

**Your save is never touched**: its own save in
``%APPDATA%\\InsideTheCave\\coin_check``, with a copy of your key bindings and volume
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

platform_check.SAVE_NAME = 'coin_check'
Window.TITLE = 'Inside The Cave - coin check'

#: (what it is, whether monsters, bats and torches become coins too)
STARTS = (('coins as usual, and nothing else', False),
          ('more coins, where monsters, bats and torches would be', True))


def choose():
    """The window's menu; returns the start's "more coins" in a tuple, or None to quit."""
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
        say('Coin check. Up and Down to choose, Enter to start, Escape to quit.')
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
                    return (STARTS[index][1],)
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
    more, = picked

    import InsideTheCave
    from insidethecave.scene.node import SpriteNode

    class Args:
        game = None
        stage = True
        debug = False               # nothing comes that could kill you anyway
        verbose = False

    class CoinApp(InsideTheCave.App):
        def start_game(self):
            self.defaults.setInteger_forKey_(3, 'countTutorial')
            self.defaults.synchronize()
            super().start_game()
            s = self.game.scene
            # only coins come down: monsters, bats and torches are empty slots, which keep
            # the slots going, or with "more coins", coins themselves
            for make in ('createMonster', 'createBats', 'createTorchObstacle'):
                setattr(s, make, s.createCoin if more else (lambda: SpriteNode(name='slot')))
            s.changeFalloffSize = lambda: None      # the torch stays lit: no "Torch low"
            self.speech.speak('Only coins are coming%s.'
                              % (', and more of them' if more else ''), interrupt=False)

    CoinApp(Args()).run('game')
    return 0


if __name__ == '__main__':
    sys.exit(main())
