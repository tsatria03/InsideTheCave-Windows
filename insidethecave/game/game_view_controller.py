"""``GameViewController``: hosts the game scene, keeps the score and the coins, and ends the
game.  Ported from ``analysis/disasm/dz_GameViewController.txt``.

* Loading (``viewDidLoad``'s body 0x1000179c4, which Replay's ``unwindToGameSegue:`` runs
  again): the score and coin labels start at "0", and a ``GameScene`` is made, given this
  controller as its delegate, and presented.
* ``scoreUpWithValue:`` and ``coinUpWithValue:`` add to the numbers in the labels (helper
  0x100018390); ``changeCoinCounterWithScenario:`` changes the counter's icon (0x100018e08).
* ``clearScene`` (0x1000181cc) stops the scene's actions and empties it;
  ``gameOverDelegateFunc`` (0x100017fdc) goes to the result screen with the score and the
  coins (``prepareForSegue:sender:``, 0x100018b0c).

``on_game_over`` is the segue: the screen loop (``InsideTheCave.py``) takes it to the result
screen with the score and the coins.
"""
from __future__ import annotations

import logging

from ..platform import language
from ..scene.audio import AudioEngine
from .game_scene import COUNTERS, DEFAULT_DIFFICULTY, ROCK, GameScene

log = logging.getLogger('game')


class GameViewController:
    def __init__(self, al=None, bank=None, defaults=None, speech=None, voice=None,
                 keymap=None, loop=None, debug=False, language_code=None, rng=None,
                 on_game_over=None):
        self.al = al
        self.bank = bank
        self.defaults = defaults
        self.speech = speech
        self.voice = voice
        self.keymap = keymap
        self.loop = loop
        self.debug = debug
        self.language_code = language_code or language.code()
        self.rng = rng
        self.on_game_over = on_game_over
        #: PORT ADDITION: the difficulty the next game is played at, set by the screen loop
        #: (aidocks/project_difficulty_plan.md); Replay and Restart keep it.
        self.difficulty = DEFAULT_DIFFICULTY
        self.last_run = None
        self.scene = None
        self.engine = None
        self.score = 0
        self.coins = 0
        self.coinCounter = COUNTERS[ROCK]
        self.over = False

    # ---- GameViewController~shared1 0x1000179c4: viewDidLoad and Replay ------------------
    def viewDidLoad(self):
        self.score = 0                                                 # '0' at 0x100017aec
        self.coins = 0                                                 # '0' at 0x100017ba4
        self.over = False
        if self.al is not None and self.bank is not None:
            self.engine = AudioEngine(self.al, self.bank)
        self.scene = GameScene(audio=self.engine, delegate=self, speech=self.speech,
                               voice=self.voice, keymap=self.keymap, defaults=self.defaults,
                               loop=self.loop, language_code=self.language_code,
                               rng=self.rng, debug=self.debug, difficulty=self.difficulty)
        self.scene.didMoveToView()                                     # presentScene:

    unwindToGameSegue = viewDidLoad

    # ---- the scene's delegate -----------------------------------------------------------
    def scoreUpWithValue(self, value):
        self.score += int(value)

    def coinUpWithValue(self, value):
        self.coins += int(value)

    def changeCoinCounterWithScenario(self, scenario):
        self.coinCounter = COUNTERS.get(scenario, self.coinCounter)

    # GameViewController.clearScene 0x1000181cc
    def clearScene(self):
        scene = self.scene
        if scene is None:
            return
        scene.removeAllActions()
        scene.removeAllChildren()
        if self.engine is not None:
            self.engine.release()

    # -[GameViewController gameOverDelegateFunc] 0x100017fdc
    def gameOverDelegateFunc(self):
        self.over = True
        s = self.scene
        #: PORT ADDITION: the run, for the result screen and the stats
        self.last_run = dict(score=self.score, coins=self.coins,
                             seconds=int(s.runSeconds) if s is not None else 0,
                             speed=s.speedCount() if s is not None else 0,
                             difficulty=self.difficulty,
                             **(dict(s.run) if s is not None else {}))
        log.info('game over: score %d, coins %d', self.score, self.coins)
        if self.on_game_over is not None:
            self.on_game_over(self.score, self.coins)

    # ---- the frame ----------------------------------------------------------------------
    def frame(self, now):
        if self.scene is not None and not self.over:
            self.scene.frame(now)

    # ---- what a sighted helper sees -----------------------------------------------------
    def lines(self):
        s = self.scene
        if s is None:
            return ['Inside The Cave']
        lane = ('left', 'centre', 'right')[s.actualPositionPlayer] \
            if 0 <= s.actualPositionPlayer <= 2 else '?'
        if s.falloffSize >= 1000.0:
            torch = 'no torch'
        elif s.falloffSize >= 3.0:
            torch = 'torch low (%.2f)' % s.falloffSize
        else:
            torch = 'torch (%.2f)' % s.falloffSize
        state = ('game over' if self.over else 'paused' if s.paused_by_player
                 else 'playing' if s.started else 'starting')
        return ['Inside The Cave - %s%s' % (state, ' (debug)' if self.debug else ''),
                'Score %d   Coins %d' % (self.score, self.coins),
                'Lane: %s   %s' % (lane, torch),
                'Cave: %s   speed %.2f   slot %d' % (s.currentScenario, s.speedMonster,
                                                     s.countObjectScene)]
