#!/usr/bin/env python
"""For testing by ear: the full game at a speed you set yourself.  Not a test, and not part
of the game: a developer tool, one of the tools in ``tests\\interact`` that you play.  Wear
headphones.

    python tests\\interact\\speed_check.py

A small window asks how to start, then the game itself takes the window:

    Enter           start, at speed 0, the game's own start
    D               debug mode on or off (off at first; on: nothing can kill you)
    Escape          quit, here; in the game, pause
    Alt+F4          quit, at any moment

In the game, besides the game's own keys:

    Equals (=)      faster: the speed up by one, as 0, 1, 2 ...
    Minus (-)       slower: the speed down by one

The speed is said as the E key says it (aidocks/project_status_keys_plan.md): how many
times the cave has sped up, "Speed, 0." at the game's start up to "Speed, 40.", the
fastest (the dev: "What if minus and equals increased and decreased the speed, like speed
0, speed 1."; "Equals faster and Minus slower").  Behind it is the game's ``speedMonster``,
the seconds a thing takes to fall the whole cave: 5.0 at 0, 0.1 less for each one up, 1.0
at 40.  Left to itself the game goes up one every 20 slots, reaching 40 at slot 800; here
it never changes by itself, and stays where you put it, from 0 to 40, the game's own limits
(the dev: "the speed checker script should cap to those speeds as well.").  A slot comes
every 0.165 x speedMonster seconds, and a roar about 0.26 x speedMonster seconds before its
monster reaches you: about 1.3 s at 0, a quarter of a second at 40.  E says the same
number as these keys.

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

FASTER, SLOWER = ('=', '[+]'), ('-', '[-]')     # pygame's names, the keypad's too


def limits():
    """The game's own range as the E key counts it: (the fastest count, a count's
    speedMonster), read only once the save is our own."""
    from insidethecave.game.game_scene import SPEED_COUNT_FROM, SPEED_STEP, TOP_SPEED

    def speed_of(count):
        return round(SPEED_COUNT_FROM - count * SPEED_STEP, 2)
    return int(round((SPEED_COUNT_FROM - TOP_SPEED) / SPEED_STEP)), speed_of


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
        say('Speed check. Enter to start at speed 0, D for debug mode, Escape to quit. '
            'In the game, equals is faster and minus is slower. Debug mode is off.')
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
    FASTEST, speed_of = limits()    # counts 0 (the slowest, the start) to FASTEST

    class SpeedApp(InsideTheCave.App):
        count = 0

        def start_game(self):
            self.defaults.setInteger_forKey_(3, 'countTutorial')
            self.defaults.synchronize()
            super().start_game()
            s = self.game.scene
            s.speedMonster = speed_of(self.count)
            real = s.createObjectScene

            def slot():
                """A slot as the game makes it, with the speed put back after: the game's
                own speed-up every 20 slots (0x10000c998) never sticks."""
                real()
                s.speedMonster = speed_of(self.count)
            s.createObjectScene = slot
            self.speech.speak('Speed, %d.' % self.count, interrupt=False)

        def keydown(self, event):
            name = self.pygame.key.name(event.key)
            if self.kind == 'game' and name in FASTER + SLOWER:
                step = 1 if name in FASTER else -1
                self.count = min(FASTEST, max(0, self.count + step))
                if self.game.scene is not None:
                    self.game.scene.speedMonster = speed_of(self.count)
                edge = (', the fastest' if self.count == FASTEST else
                        ', the slowest' if self.count == 0 else '')
                self.speech.speak('Speed, %d%s.' % (self.count, edge))
                return
            super().keydown(event)

    SpeedApp(Args()).run('game')
    return 0


if __name__ == '__main__':
    sys.exit(main())
