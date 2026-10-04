"""PORT ADDITION: "Choose a difficulty", before a game and before the best five (the dev, for
the fourth release; aidocks/project_difficulty_plan.md).

The original has one game and one ranking.  Here Play and Score on the main menu each open
this screen first: Easy, Medium and Hard, as rows.  Enter goes on, to a game at that
difficulty or to that difficulty's best five; Escape goes back to the main menu.  It opens
on the difficulty last played since the game was opened, Easy before any (the dev: "When
you open the game, and then choose a difficulty, it should not remember your choice. It
should only remember it if you died, and or if you whent back to the main menu, then
pressed play again."): the screen loop keeps it, not the save.
"""
from __future__ import annotations

from ..game.game_scene import DEFAULT_DIFFICULTY, DIFFICULTY_ORDER
from .rows import RowScreen

NAMES = {'easy': 'Easy', 'medium': 'Medium', 'hard': 'Hard'}


class DifficultyScreen(RowScreen):
    title = 'Choose a difficulty'
    keys_line = 'Up/Down move   Enter choose   Escape menu   F1 key bindings   Alt+F4 quit'

    def __init__(self, speech=None, then='game', last=None):
        """``then``: 'game' for Play, 'ranking' for Score; ``last``: the difficulty last
        played since the game was opened, or None."""
        super().__init__(speech)
        self.then = then
        self.rows = [(d, NAMES[d]) for d in DIFFICULTY_ORDER]
        start = last if last in DIFFICULTY_ORDER else DEFAULT_DIFFICULTY
        self.index = DIFFICULTY_ORDER.index(start)
        #: The difficulty chosen, once Enter is pressed.
        self.chosen = None

    def viewDidLoad(self):
        self.announce(self.title)

    def choose(self, key):
        self.chosen = key
        self.next = self.then

    def back(self):
        self.next = 'menu'
