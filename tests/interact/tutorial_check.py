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
     3  only coins and torches, one at a time, to hear each taught in each cave lane
     4  only monsters and bats, to hear each taught, and to throw at them: your torch is
        lit again a second after each throw, so you can hear every throw line

Things to listen for (aidocks/project_tutorial_plan.md and
aidocks/project_tutorial_teaching_plan.md):

* each kind said only the first time it comes down each cave lane, wherever you stand: "A
  coin appeared in the left lane. Go there to grab it.", "A torch appeared in the middle
  lane. Go there to pick it up.", "A monster appeared in the right lane. Stay out of it, or
  throw your torch at it.", "Bats appeared in the left lane. Stay out of that lane, or throw
  your torch to scare them off."; without a torch, no throw; the same kind in the same lane
  again, nothing;
* once all 12 (start 1 or 2; 3 and 4 have only 6 each): "You've met everything in the cave.
  From now on, listen for them yourself.";
* "Coin passed, in the left lane." and so on, only for one that was announced, and nothing
  for a coin or torch you took or a monster you killed;
* "Coin caught." and "Torch caught." every time you pick one up (not for start 4's relit
  torch);
* the closing line waiting for the one before to finish;
* cutting in at once: each arrival, each passed and caught line, "The monster was hit! It's gone.", "The bats were hit, and dodged to
  your left.", "Your torch flew off without hitting anything.", and on the first throw
  "You're out of light now. Find another torch soon."; the lines waiting then carry on;
* the cave never speeding up, your footsteps walking, S "No score to report.", E "No speed
  to report.", C your coins;
* Control cutting off one line, the next waiting one following;
* caught: "You were caught.", Replay (no welcome) and Menu; nothing saved.

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

#: (what it is, with the welcome, what comes down: None for everything)
STARTS = (('the tutorial as chosen from the main menu, with its welcome', True, None),
          ('the tutorial as after Replay, without the welcome', False, None),
          ('only coins and torches', False, 'pickups'),
          ('only monsters and bats, and your torch lit again after each throw', False,
           'threats'))


def choose():
    """The window's menu; returns (welcome, only, debug), or None to quit."""
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
                    _label, welcome, only = STARTS[index]
                    return welcome, only, debug
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
    welcome, only, debug = picked

    import InsideTheCave
    from insidethecave.game import game_scene as G
    from insidethecave.scene import actions as A
    from insidethecave.scene.node import SpriteNode

    class Args:
        game = None
        stage = False
        verbose = False

    Args.debug = debug

    def empty():
        return SpriteNode(name='slot')

    class TutorialApp(InsideTheCave.App):
        def start_game(self):
            super().start_game()
            s = self.game.scene
            if only == 'pickups':
                s.createMonster = s.createBats = empty
            elif only == 'threats':
                s.createCoin = s.createTorchObstacle = empty
                real_throw = s.throwTorch

                def relight():
                    if not s.playerDead:
                        s.playerDidCollideWithTorch(SpriteNode(name='torch'))

                def throw():
                    """A throw, then the torch lit again about a second later."""
                    lit = s.falloffSize < G.FALLOFF_LAST
                    real_throw()
                    if lit and s.falloffSize == G.FALLOFF_OUT:
                        s.runAction(A.sequence([A.waitForDuration(1.0),
                                                A.runBlock(relight)]))
                s.throwTorch = throw

    app = TutorialApp(Args())
    if welcome:
        app.kind = 'menu'                  # as if chosen there, so with its welcome
    app.run('tutorial')
    return 0


if __name__ == '__main__':
    sys.exit(main())
