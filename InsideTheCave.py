#!/usr/bin/env python
"""Inside The Cave, for Windows: the entry point and the frame loop.

    python InsideTheCave.py              play
    python InsideTheCave.py --debug      play where nothing can kill you, to check sounds
    python InsideTheCave.py --game PATH  with the game's data from another folder
    python InsideTheCave.py -v           with the log on the console

For now the game starts straight away: the original's earphone warning, menu, result and
ranking screens come with phase 4 (aidocks/project_port_plan.md).  At a game over the score
and the coins are said, and Enter plays again.

The keys: your bindings to move and throw (F1 lists and changes them), P or Escape to
pause, Page Up and Page Down for the volume, Alt+F4 to quit.  Leaving the window pauses.
"""
from __future__ import annotations

import argparse
import logging
import os
import sys

ROOT = os.path.dirname(os.path.abspath(__file__))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)
os.environ.setdefault('PYGAME_HIDE_SUPPORT_PROMPT', '1')       # no banner on the console

from insidethecave import paths                                  # noqa: E402

log = logging.getLogger('app')

WINDOW_SIZE = (720, 440)
TITLE = 'Inside The Cave'
FPS = 120
LINES, LINE_HEIGHT = 19, 22
KEY_LINES = ['Keys: your move and throw keys, F1 key bindings,',
             'P or Escape pause, Page Up / Page Down volume, Alt+F4 quit.']


class App:
    def __init__(self, args):
        import pygame
        from insidethecave.game.game_view_controller import GameViewController
        from insidethecave.platform import openal, runloop, sound, volume
        from insidethecave.platform.defaults import UserDefaults
        from insidethecave.platform.keymap import KeyMap
        from insidethecave.platform.speech import Speech, TutorialVoice
        from insidethecave.ui.game_input import GameInput
        from insidethecave.ui.keybind_screen import KeyBindScreen

        self.pygame = pygame
        self.openal, self.runloop, self.volume = openal, runloop, volume
        pygame.display.init()           # never pygame.init(): it would open SDL's mixer
        pygame.font.init()
        self.screen = pygame.display.set_mode(WINDOW_SIZE)
        pygame.display.set_caption(TITLE)
        self.font = pygame.font.SysFont(None, 24)
        self.al = openal.AL()
        self.al.open()
        self.bank = sound.SoundBank(self.al)
        self.defaults = UserDefaults.standardUserDefaults()
        if volume.load(self.defaults):
            self.defaults.synchronize()
        self.set_master()
        self.speech = Speech.shared()
        self.voice = TutorialVoice()
        self.keymap = KeyMap.shared()
        self.loop = runloop.main_loop()
        self.input = GameInput(self.keymap, self.speech)
        self.keys_screen = KeyBindScreen(self.keymap, self.speech)
        self.keys_open = False
        self.game = GameViewController(self.al, self.bank, self.defaults, self.speech,
                                       self.voice, self.keymap, self.loop, debug=args.debug,
                                       on_game_over=self.game_over)
        self.over_said = False
        self.next_device_check = 0.0
        self.running = True

    # ---- the game ---------------------------------------------------------------------
    def set_master(self):
        self.al.alListenerf(self.openal.AL_GAIN, self.volume.master_gain())

    def start_game(self):
        self.loop.reset()
        self.game.viewDidLoad()
        self.input.attach(self.game.scene)
        if self.game.debug:
            self.speech.speak('Debug mode: nothing can kill you.', interrupt=False)

    def game_over(self, score, coins):
        self.speech.speak('Game over. Score %d. Coins %d. Press Enter to play again, '
                          'or Escape to quit.' % (score, coins))

    # ---- keys -------------------------------------------------------------------------
    def change_volume(self, step):
        now = self.volume.change_master(self.defaults, step)
        self.set_master()
        self.speech.speak('Volume %d percent.' % now)

    def open_keys(self):
        """F1: the key bindings, over a game held still (a finished one needs no holding)."""
        self.was_paused = self.input.paused or self.game.over
        if not self.game.over:
            self.input.pause(speak=False)
        self.keys_open = True
        self.keys_screen.open()

    def close_keys(self):
        self.keys_open = False
        self.keymap.clear_held()
        if not self.was_paused:
            self.input.resume(speak=False)

    def keydown(self, event):
        pg = self.pygame
        name = pg.key.name(event.key)
        if name == 'f4' and event.mod & pg.KMOD_ALT:
            self.running = False
            return
        if name == 'f1':
            self.open_keys()
            return
        if name in ('page up', 'page down'):
            self.change_volume(+1 if name == 'page up' else -1)
            return
        if self.game.over:
            if name in ('return', 'enter'):
                self.start_game()
            elif name == 'escape':
                self.running = False
            return
        self.input.press(name)

    def handle(self, event):
        pg = self.pygame
        if event.type == pg.QUIT:
            self.running = False
            return
        if self.keys_open:
            self.keys_screen.handle(event, pg)
            if self.keys_screen.done:
                self.close_keys()
            return
        if event.type == getattr(pg, 'WINDOWFOCUSLOST', None):
            if not self.game.over:
                self.input.pause()
            return
        if event.type == getattr(pg, 'WINDOWFOCUSGAINED', None):
            self.next_device_check = 0.0
            return
        if event.type == pg.KEYDOWN:
            self.keydown(event)
        elif event.type == pg.KEYUP:
            self.input.release(pg.key.name(event.key))

    # ---- the window -------------------------------------------------------------------
    def draw(self):
        lines = (self.keys_screen.render_lines() if self.keys_open
                 else self.game.lines() + [''] + KEY_LINES)
        self.screen.fill((0, 0, 0))
        for i, line in enumerate(lines[:LINES]):
            self.screen.blit(self.font.render(line, True, (230, 230, 230)),
                             (12, 8 + i * LINE_HEIGHT))
        self.pygame.display.flip()

    # ---- the loop ---------------------------------------------------------------------
    def run(self):
        pg = self.pygame
        clock = pg.time.Clock()
        self.start_game()
        try:
            while self.running:
                for event in pg.event.get():
                    self.handle(event)
                    if not self.running:
                        break
                now = self.runloop.clock()
                self.input.tick()
                self.loop.pump(now)
                self.game.frame(now)
                if now >= self.next_device_check:
                    self.next_device_check = now + 1.0
                    self.al.check_device()
                self.draw()
                clock.tick(FPS)
        finally:
            self.close()

    def close(self):
        try:
            self.voice.stop()
            self.speech.stop()
        except Exception:
            pass
        if self.game.engine is not None:
            self.game.engine.release()
        self.bank.release()
        self.al.close()
        self.pygame.display.quit()


def main(argv=None):
    ap = argparse.ArgumentParser(description='Inside The Cave')
    ap.add_argument('--debug', action='store_true', help='nothing can kill you')
    ap.add_argument('--game', help="a folder holding the game's sounds")
    ap.add_argument('--stage', action='store_true',
                    help='start straight on the game (the only way, until the menus)')
    ap.add_argument('-v', '--verbose', action='store_true')
    args = ap.parse_args(argv)
    logging.basicConfig(level=logging.INFO if args.verbose else logging.WARNING,
                        format='%(asctime)s %(name)s: %(message)s')
    if args.game:
        paths.set_game(args.game)
    App(args).run()
    return 0


if __name__ == '__main__':
    sys.exit(main())
