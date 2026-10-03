#!/usr/bin/env python
"""For testing by ear: the full game at a speed you set yourself.  Not a test, and not part
of the game: a developer tool, one of the tools in ``tests\\interact`` that you play.  Wear
headphones.

    python tests\\interact\\speed_check.py

A small window asks how to start, then the game itself takes the window:

    Enter           start, at speed 4.0, the game's own start
    D               debug mode on or off (off at first; on: nothing can kill you)
    Escape          quit, here; in the game, pause
    Alt+F4          quit, at any moment

In the game, besides the game's own keys:

    Minus (-)       faster: the speed down by 0.1, as 4.0, 3.9, 3.8 ...
    Equals (=)      slower: the speed up by 0.1

The speed is the game's ``speedMonster``: the seconds a thing takes to fall the whole
height of the cave.  The game starts at 4.0 and, left to itself, steps down by 0.12 every
20 slots until 2.0, at slot 340, and stays there.  Here it never changes by itself: it
stays where you put it, anywhere from 0.1 to 10.0, above 4.0 and below 2.0 included.  A
slot comes every 0.165 x the speed seconds, and a roar comes about 0.26 x the speed seconds
before its monster reaches you: about 1 s at 4.0, half a second at 2.0.

A change applies to the next slot and what it brings; things already coming keep the
speed they set off at.  The speed carries over a Restart, a Replay or a new game.  The
game starts without the tutorial line, and everything else is the full game.

**Your save is never touched**: its own save in
``%APPDATA%\\InsideTheCave\\speed_check``, with a copy of your key bindings and volume
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

platform_check.SAVE_NAME = 'speed_check'
Window.TITLE = 'Inside The Cave - speed check'

START_SPEED = 4.0               # the game's own start (0x1000157bc)
STEP = 0.1
SLOWEST, FASTEST = 10.0, 0.1
FASTER, SLOWER = ('-', '[-]'), ('=', '[+]')     # pygame's names, the keypad's too


def choose():
    """The window's menu; returns (debug,), or None to quit."""
    from insidethecave.platform.speech import Speech
    speech = Speech.shared()
    window = Window()
    debug = False

    def say(text):
        print(text)
        window.show(text)
        speech.speak(text)

    try:
        say('Speed check. Enter to start at speed 4.0, D for debug mode, Escape to quit. '
            'In the game, minus is faster and equals is slower. Debug mode is off.')
        while True:
            for name in window.keys():
                if name == 'escape':
                    return None
                if name == 'd':
                    debug = not debug
                    say('Debug mode %s.' % ('on' if debug else 'off'))
                elif name in ('return', 'enter'):
                    return (debug,)
                else:
                    say('Enter to start, D for debug mode, Escape to quit.')
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
    debug, = picked

    import InsideTheCave

    class Args:
        game = None
        stage = True
        verbose = False

    Args.debug = debug

    class SpeedApp(InsideTheCave.App):
        speed = START_SPEED

        def start_game(self):
            self.defaults.setInteger_forKey_(3, 'countTutorial')
            self.defaults.synchronize()
            super().start_game()
            s = self.game.scene
            s.speedMonster = self.speed
            real = s.createObjectScene

            def slot():
                """A slot as the game makes it, with the speed put back after: the game's
                own speed-up every 20 slots (0x10000c998) never sticks."""
                real()
                s.speedMonster = self.speed
            s.createObjectScene = slot
            self.speech.speak('Speed %.1f.' % self.speed, interrupt=False)

        def keydown(self, event):
            name = self.pygame.key.name(event.key)
            if self.kind == 'game' and name in FASTER + SLOWER:
                step = -STEP if name in FASTER else STEP
                self.speed = round(min(SLOWEST, max(FASTEST, self.speed + step)), 1)
                if self.game.scene is not None:
                    self.game.scene.speedMonster = self.speed
                edge = (', the fastest' if self.speed == FASTEST else
                        ', the slowest' if self.speed == SLOWEST else '')
                self.speech.speak('Speed %.1f%s.' % (self.speed, edge))
                return
            super().keydown(event)

    SpeedApp(Args()).run('game')
    return 0


if __name__ == '__main__':
    sys.exit(main())
