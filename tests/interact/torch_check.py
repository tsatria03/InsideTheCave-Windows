#!/usr/bin/env python
"""For testing by ear: the torch, without waiting for it.  Not a test, and not part of the
game: the tests are in ``tests\\case``, and this is one of the tools in ``tests\\interact``
that you play.  Wear headphones.

    python tests\\interact\\torch_check.py

A small window asks where to start, then the game itself takes the window:

    Up / Down       choose where to start, each one named
    Enter           start there
    Escape          quit, here; in the game, pause
    Alt+F4          quit, at any moment

The starting points:

     1  burning out: the torch nearly gone.  "Torch low" at the first slot, and the
        burning-out sound at the second, about 3 seconds in
     2  torch low: the torch just about to dim.  "Torch low" at the second slot, about
        3 seconds in, and the burning-out sound 29 slots later, some 19 seconds on
     3  a full torch, as a new game: for throwing it (W or Up Arrow), which plays the throw
        and never the burning-out sound

Nothing comes down the cave by itself: no torches to pick up, so nothing relights yours,
and no monsters, bats or coins, so nothing can kill you and there are no roars to talk
over.  But each time you throw your torch, one torch comes down a lane the game picks,
and your screen reader says "A torch is coming."; be in its lane to pick it up and throw
again.  Miss it, and you have no torch until you restart.  Each would-be one is an empty slot, so the slots, and
with them the torch burning down, keep their pace.  The game starts without the tutorial
line.  The pause menu's Restart starts again from the same point.

**Your save is never touched**: its own save in
``%APPDATA%\\InsideTheCave\\torch_check``, with a copy of your key bindings and volume
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

platform_check.SAVE_NAME = 'torch_check'
Window.TITLE = 'Inside The Cave - torch check'

#: (what it is, the torch's falloff to start at; None for a full torch)
STARTS = (('burning out, the torch nearly gone', 4.95),
          ('torch low, the torch about to dim', 2.99),
          ('a full torch, for throwing', None))


def choose():
    """The window's menu; returns the start's falloff (None for a full torch) in a tuple, or
    None to quit."""
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
        say('Torch check. Up and Down to choose, Enter to start, Escape to quit.')
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
    falloff, = picked

    import InsideTheCave

    class Args:
        game = None
        stage = True
        debug = False               # nothing comes that could kill you anyway
        verbose = False

    from insidethecave.game import game_scene as G
    from insidethecave.scene.node import SpriteNode

    class TorchApp(InsideTheCave.App):
        def start_game(self):
            self.defaults.setInteger_forKey_(3, 'countTutorial')
            self.defaults.synchronize()
            super().start_game()
            s = self.game.scene
            # nothing comes down the cave but empty slots, which keep the slots and the
            # light going: no torches to pick up, so nothing relights yours (the dev: "Only
            # spawn one torch."), and no monsters, bats or coins (the dev: "Please do not
            # spawn monsters, bats, and coins.")
            real_torch, real_throw = s.createTorchObstacle, s.throwTorch
            for make in ('createTorchObstacle', 'createMonster', 'createBats', 'createCoin'):
                setattr(s, make, lambda: SpriteNode(name='slot'))

            def throw():
                """A throw sends one torch down a lane the game picks, to pick up again
                (the dev: "If you throw a torch in the test, then 1 should get spawned in
                any lane.")."""
                lit = s.falloffSize < G.FALLOFF_LAST
                real_throw()
                if lit and s.falloffSize == G.FALLOFF_OUT:      # it was thrown
                    torch = real_torch()
                    s.addChild(torch)
                    torch.runAction(s.moveObstacle())
                    self.speech.speak('A torch is coming.', interrupt=False)
            s.throwTorch = throw
            if falloff is not None:
                s.falloffSize = falloff
                s.lightTorch.falloff = falloff
                self.speech.speak('The torch starts at %.2f; it dims at 3 and goes out '
                                  'past 5.' % falloff, interrupt=False)

    TorchApp(Args()).run('game')
    return 0


if __name__ == '__main__':
    sys.exit(main())
