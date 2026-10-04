#!/usr/bin/env python
"""Inside The Cave, for Windows: the entry point, the screens and the frame loop.

    python InsideTheCave.py              play, from the earphone warning and the menu
    python InsideTheCave.py --stage      start straight on a game
    python InsideTheCave.py --debug      play where nothing can kill you, to check sounds
    python InsideTheCave.py --game PATH  with the game's data from another folder
    python InsideTheCave.py -v           with the log on the console

The screen loop stands in for the original's storyboard and navigation controller
(GAME_STRUCTURE.md section 1): the earphone warning, then the menu (``WarningToMenu``); the
menu's Play to the game and Score to the ranking; a game over to the result screen
(``GameToResult``), whose Replay starts a new game (``unwindToGameSegue``) and Menu goes back
to the menu (``unwindToHomeScreenSegue``).  The pause menu's Restart and Quit to menu are
the port's own, and so, since the fourth release, is "Choose a difficulty" between Play or
Score and what they open ('choose_game', 'choose_ranking'); Replay and Restart keep the
difficulty.

The keys: on a screen, Up and Down, Enter, Escape to go back; in a game, your bindings to
move and throw, P or Escape to pause, Home and End for the master volume.  Everywhere, F1
lists and changes the keys, Page Up and Page Down set the music volume, and Alt+F4 quits.
Leaving the window pauses a game.
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
#: PORT ADDITION: the screens the menu music plays on (ui/menu_music.py); not the warning,
#: and not a game, paused or not.
MENU_MUSIC_SCREENS = ('menu', 'choose_game', 'choose_ranking', 'ranking', 'choose_stats',
                      'stats', 'result', 'caught')
KEY_LINES = ['Keys: your move and throw keys, P or Escape pause, F1 key bindings,',
             'Page Up / Page Down track volume, Home / End master volume, Alt+F4 quit.']


class App:
    def __init__(self, args):
        import pygame
        from insidethecave.game.game_view_controller import GameViewController
        from insidethecave.platform import language, openal, runloop, sound, volume
        from insidethecave.platform.defaults import UserDefaults
        from insidethecave.platform.keymap import KeyMap
        from insidethecave.platform.speech import Speech, TutorialVoice
        from insidethecave.ui.game_input import GameInput
        from insidethecave.ui.keybind_screen import KeyBindScreen
        from insidethecave.ui.menu_music import MenuMusic

        self.pygame = pygame
        self.openal, self.runloop, self.volume = openal, runloop, volume
        pygame.display.init()           # never pygame.init(): it would open SDL's mixer
        pygame.font.init()
        self.screen = pygame.display.set_mode(WINDOW_SIZE)
        pygame.display.set_caption(TITLE + (' (debug)' if args.debug else ''))
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
        self.language_code = language.code()
        self.input = GameInput(self.keymap, self.speech)
        self.keys_screen = KeyBindScreen(self.keymap, self.speech)
        self.keys_open = False
        self.menu_music = MenuMusic(self.al, self.bank)
        self.game = GameViewController(self.al, self.bank, self.defaults, self.speech,
                                       self.voice, self.keymap, self.loop, debug=args.debug,
                                       language_code=self.language_code,
                                       on_game_over=self.game_over)
        #: The screen showing: 'warning', 'menu', 'choose_game', 'choose_ranking',
        #: 'ranking', 'result' or 'game'.
        self.kind = None
        #: PORT ADDITION: the best five the Score screen shows (the difficulty chosen for it).
        self.ranking_difficulty = None
        #: PORT ADDITION: the difficulty last played since the game was opened, where the
        #: difficulty screens open; None, so Easy, at first (the dev: not kept in the save).
        self.played_difficulty = None
        #: PORT ADDITION: the stats the Stats screen shows: a difficulty, or 'all'.
        self.stats_choice = None
        #: Its object; None during a game, which is ``self.game``.
        self.page = None
        self.over = None                # (score, coins) once a game is over
        self.next_device_check = 0.0
        self.running = True

    # ---- the screens ------------------------------------------------------------------
    def go(self, kind):
        """Show the screen ``kind``; 'quit' ends the program."""
        from insidethecave.game.home_screen_view_controller import HomeScreenViewController
        from insidethecave.game.ranking_view_controller import RankingViewController
        from insidethecave.game.result_view_controller import ResultViewController
        from insidethecave.game.warning_view_controller import WarningViewController
        from insidethecave.ui.difficulty_screen import DifficultyScreen
        from insidethecave.ui.stats_screen import StatsScreen

        from insidethecave.ui.caught_screen import CaughtScreen

        log.info('-> %s', kind)
        chosen = getattr(self.page, 'chosen', None)     # a difficulty, from its screen
        if kind == 'tutorial':
            # PORT ADDITION: the tutorial, a game of its own; its welcome only from the menu
            self.game.tutorial = True
            self.game.welcome = self.kind == 'menu'
            kind = 'game'
        elif kind == 'game':
            self.game.tutorial = False
        if kind == 'game' and chosen is not None:
            self.game.difficulty = chosen               # Replay and Restart keep it
            self.played_difficulty = chosen
        elif kind == 'ranking' and chosen is not None:
            self.ranking_difficulty = chosen
        elif kind == 'stats' and chosen is not None:
            self.stats_choice = chosen
        if self.kind == 'game' and kind != 'game':
            self.leave_game()
        if kind in MENU_MUSIC_SCREENS:
            self.menu_music.start()             # carries on from one menu to the next
        else:
            self.menu_music.stop()              # a game, the warning, or quitting
        if kind == 'quit':
            self.running = False
            return
        self.kind = kind
        if kind == 'game':
            self.page = None
            self.start_game()
            return
        if kind == 'warning':
            self.page = WarningViewController(self.speech, self.loop, self.language_code,
                                              voice=self.voice)
        elif kind == 'menu':
            self.page = HomeScreenViewController(self.defaults, self.speech)
        elif kind in ('choose_game', 'choose_ranking', 'choose_stats'):
            self.page = DifficultyScreen(self.speech, then=kind[len('choose_'):],
                                         last=self.played_difficulty)
        elif kind == 'stats':
            self.page = StatsScreen(self.defaults, self.speech,
                                    self.stats_choice or self.game.difficulty)
        elif kind == 'ranking':
            self.page = RankingViewController(self.defaults, self.speech,
                                              self.ranking_difficulty or self.game.difficulty)
        elif kind == 'caught':
            self.page = CaughtScreen(self.speech)
        elif kind == 'result':
            score, coins = self.over or (0, 0)
            run = self.game.last_run or {}
            self.page = ResultViewController(score, coins, self.defaults, self.speech,
                                             difficulty=self.game.difficulty,
                                             seconds=run.get('seconds', 0),
                                             speed=run.get('speed', 0))
        self.page.viewDidLoad()

    def follow(self):
        """After keys and timers: go where the screen, or the pause menu, asked to."""
        if self.kind == 'game':
            if self.over is not None:
                self.go('caught' if self.game.tutorial else 'result')
            elif self.input.request == 'restart':
                self.restart_game()
            elif self.input.request == 'menu':
                self.go('menu')
        elif self.page is not None and self.page.next:
            self.go(self.page.next)

    # ---- the game ---------------------------------------------------------------------
    def set_master(self):
        self.al.alListenerf(self.openal.AL_GAIN, self.volume.master_gain())

    def start_game(self):
        self.over = None
        self.loop.reset()
        self.game.viewDidLoad()
        self.input.attach(self.game.scene)
        if self.game.debug:
            self.speech.speak('Debug mode: nothing can kill you.', interrupt=False)

    def leave_game(self):
        """PORT: a game left from the pause menu, or over, lets go of its sounds and timers."""
        try:
            self.voice.stop()
        except Exception:
            pass
        self.game.clearScene()
        self.loop.reset()
        self.input.attach(None)

    def restart_game(self):
        self.leave_game()
        self.start_game()

    def game_over(self, score, coins):
        """``gameOverDelegateFunc``'s segue to the result screen, taken once the frame is
        done (``follow``).  PORT ADDITION: a game caught counts in the stats; Restart and
        Quit to menu never reach here (the dev: "restarts and quits do not count")."""
        from insidethecave.game import stats
        self.over = (score, coins)
        if self.game.last_run is not None and not self.game.tutorial:  # never the tutorial
            stats.record(self.defaults, self.game.difficulty, self.game.last_run)

    # ---- keys -------------------------------------------------------------------------
    def change_music(self, step):
        """Page Up or Page Down: in a game, paused or not, the game's music, the track; on
        the menus, the menu music.  Heard at once."""
        if self.kind == 'game':
            now = self.volume.change_music(self.defaults, step)
            if self.game.scene is not None:
                self.game.scene.applyMusicVolume()
            self.speech.speak('Track volume %d percent.' % now)
        else:
            now = self.volume.change_menu(self.defaults, step)
            self.menu_music.apply_volume()
            self.speech.speak('Menu volume %d percent.' % now)

    def change_master(self, step):
        """Home or End, while a game is running: everything's volume."""
        now = self.volume.change_master(self.defaults, step)
        self.set_master()
        self.speech.speak('Master volume %d percent.' % now)

    def game_running(self):
        """A game being played: not paused, and not over.  Home and End are the master
        volume then, and the first and last row everywhere else (the dev)."""
        return self.kind == 'game' and not self.input.paused and not self.game.over

    def open_keys(self):
        """F1: the key bindings, over a game held still, or over a screen."""
        self.was_paused = self.kind != 'game' or self.input.paused or self.game.over
        if not self.was_paused:
            self.input.pause(speak=False)
        self.keys_open = True
        self.keys_screen.open()

    def close_keys(self):
        self.keys_open = False
        self.keymap.clear_held()
        if not self.was_paused:
            self.input.resume(speak=False)
        elif self.kind == 'game' and self.input.paused:
            self.input.menu.say_row()
        elif self.page is not None and hasattr(self.page, 'say_row'):
            self.page.say_row()

    def hush(self):
        """PORT ADDITION: Ctrl stops the Windows voice, as it stops a screen reader; in the
        tutorial the next line waiting follows (the dev, for the fourth release)."""
        try:
            self.voice.stop()
        except Exception:
            pass
        if self.kind == 'game' and self.game.scene is not None:
            self.game.scene.hushTutorial()

    def keydown(self, event):
        pg = self.pygame
        name = pg.key.name(event.key)
        if name == 'f4' and event.mod & pg.KMOD_ALT:
            self.running = False
            return
        if name in ('left ctrl', 'right ctrl'):
            self.hush()                 # and on, in case it starts a chord
        if name == 'f1':
            self.open_keys()
            return
        if name in ('page up', 'page down'):
            self.change_music(+1 if name == 'page up' else -1)
            return
        if name in ('home', 'end') and self.game_running():
            self.change_master(+1 if name == 'home' else -1)
            return
        if self.kind == 'game':
            self.input.press(name)
        elif self.page is not None:
            self.page.key(name, getattr(event, 'unicode', '') or '')

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
            if self.kind == 'game' and not self.game.over:
                self.input.pause()
            return
        if event.type == getattr(pg, 'WINDOWFOCUSGAINED', None):
            self.next_device_check = 0.0
            return
        if event.type == pg.KEYDOWN:
            self.keydown(event)
        elif event.type == pg.KEYUP and self.kind == 'game':
            self.input.release(pg.key.name(event.key))

    # ---- the window -------------------------------------------------------------------
    def lines(self):
        if self.keys_open:
            return self.keys_screen.render_lines()
        if self.kind != 'game':
            return self.page.lines() if self.page is not None else [TITLE]
        if self.input.paused:
            menu = self.input.menu
            return self.game.lines() + [''] + menu.row_lines() + ['', menu.keys_line]
        return self.game.lines() + [''] + KEY_LINES

    def draw(self):
        self.screen.fill((0, 0, 0))
        for i, line in enumerate(self.lines()[:LINES]):
            self.screen.blit(self.font.render(line, True, (230, 230, 230)),
                             (12, 8 + i * LINE_HEIGHT))
        self.pygame.display.flip()

    # ---- the loop ---------------------------------------------------------------------
    def step(self, now):
        """One frame, after the events."""
        if self.kind == 'game':
            self.input.tick()
        self.loop.pump(now)
        if self.kind == 'game':
            self.game.frame(now)
        if not self.keys_open:
            self.follow()

    def run(self, first='warning'):
        pg = self.pygame
        clock = pg.time.Clock()
        self.go(first)
        try:
            while self.running:
                for event in pg.event.get():
                    self.handle(event)
                    if not self.running:
                        break
                if not self.running:
                    break
                now = self.runloop.clock()
                self.step(now)
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
        self.menu_music.stop()
        self.bank.release()
        self.al.close()
        self.pygame.display.quit()


def main(argv=None):
    ap = argparse.ArgumentParser(description='Inside The Cave')
    ap.add_argument('--debug', action='store_true', help='nothing can kill you')
    ap.add_argument('--game', help="a folder holding the game's sounds")
    ap.add_argument('--stage', action='store_true',
                    help='start straight on a game, skipping the warning and the menu')
    ap.add_argument('-v', '--verbose', action='store_true')
    args = ap.parse_args(argv)
    logging.basicConfig(level=logging.INFO if args.verbose else logging.WARNING,
                        format='%(asctime)s %(name)s: %(message)s')
    if args.game:
        paths.set_game(args.game)
    App(args).run('game' if args.stage else 'warning')
    return 0


if __name__ == '__main__':
    sys.exit(main())
