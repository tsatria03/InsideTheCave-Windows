#!/usr/bin/env python
"""For testing by ear: the bats, and a torch thrown at them.  Not a test, and not part of
the game: the tests are in ``tests\\case``, and this is one of the tools in
``tests\\interact`` that you play.  Wear headphones.

    python tests\\interact\\bat_check.py

A small window asks where to start, then the game itself takes the window:

    Up / Down       choose where to start, each one named
    Enter           start there
    Escape          quit, here; in the game, pause
    Alt+F4          quit, at any moment

The starting points:

     1  bats that can kill you: miss one in your lane, and the game is over
     2  bats in debug mode: a bat that reaches you only says "Hit"

Every obstacle is bats: no monsters, and no coins or torches on the path.  The bats' sound
comes from their lane as they reach the roar sensor, as in the game.  Throw your torch (W
or Up Arrow) up the lane of a bat you hear: when it hits, the bat dodges, from a side lane
to the middle, or from the middle to a side, its sound going with it, and your screen
reader says where it went, "The bat dodges to the left lane.", to check by.  A bat
that dodged out of your lane never reaches you.  About a second after each throw your torch
is lit again, with the torch pickup sound, so you can throw at the next one; it never burns
down.  The game starts without the tutorial line; the pause menu's Restart starts again.

**Your save is never touched**: its own save in
``%APPDATA%\\InsideTheCave\\bat_check``, with a copy of your key bindings and volume
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

platform_check.SAVE_NAME = 'bat_check'
Window.TITLE = 'Inside The Cave - bat check'

#: (what it is, debug mode)
STARTS = (('bats that can kill you', False),
          ('bats in debug mode, a bat that reaches you says hit', True))

#: a lane's x, as a fraction of W, to its name
LANES = ((-0.3, 'the left lane'), (0.0, 'the middle lane'), (0.3, 'the right lane'))


def choose():
    """The window's menu; returns the start's debug mode in a tuple, or None to quit."""
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
        say('Bat check. Up and Down to choose, Enter to start, Escape to quit.')
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


def lane_name(x, W):
    """The name of the lane nearest ``x``."""
    return min(LANES, key=lambda lane: abs(lane[0] * W - x))[1]


def main():
    platform_check._own_save()
    picked = choose()
    if picked is None:
        return 0
    debug, = picked

    import InsideTheCave

    class Args:
        game = None
        stage = True
        verbose = False

    Args.debug = debug

    from insidethecave.game import game_scene as G
    from insidethecave.scene import actions as A
    from insidethecave.scene.node import SpriteNode

    class BatApp(InsideTheCave.App):
        def start_game(self):
            self.defaults.setInteger_forKey_(3, 'countTutorial')
            self.defaults.synchronize()
            super().start_game()
            s = self.game.scene
            say = self.speech.speak
            # every obstacle is bats, and nothing else comes: coins and torches on the path
            # are empty slots, which keep the slots going
            s.createMonster = s.createBats
            for make in ('createCoin', 'createTorchObstacle'):
                setattr(s, make, lambda: SpriteNode(name='slot'))
            s.changeFalloffSize = lambda: None      # the torch never burns down

            real_dodge, real_throw = s.torchDidCollideWithBat, s.throwTorch

            def dodge(torch, bat):
                """The game's own dodge, then where the bat went, once it is there."""
                real_dodge(torch, bat)
                s.runAction(A.sequence([
                    A.waitForDuration(0.35),
                    A.runBlock(lambda: say('The bat dodges to %s.'
                                           % lane_name(bat.position[0], s.W),
                                           interrupt=False))]))
            s.torchDidCollideWithBat = dodge

            def relight():
                if not s.playerDead:
                    s.playerDidCollideWithTorch(SpriteNode(name='torch'))

            def throw():
                """A throw, then the torch lit again about a second later."""
                lit = s.falloffSize < G.FALLOFF_LAST
                real_throw()
                if lit and s.falloffSize == G.FALLOFF_OUT:      # it was thrown
                    s.runAction(A.sequence([A.waitForDuration(1.0), A.runBlock(relight)]))
            s.throwTorch = throw
            say('Only bats are coming%s.' % (', in debug mode' if debug else ''),
                interrupt=False)

    BatApp(Args()).run('game')
    return 0


if __name__ == '__main__':
    sys.exit(main())
