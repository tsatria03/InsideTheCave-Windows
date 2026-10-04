"""``HomeScreenViewController``: the menu.  Ported from
``analysis/disasm/dz_HomeScreenViewController.txt``.

* ``viewDidLoad`` (0x100019fa4): when the save has no ``rank``, it is set to five entries
  of "Player", "0"; ``countTutorial`` is set to 0 when missing (0x10001a00c..0x10001a334).
  It also sets ``rankWorld`` to the same five on every launch, which the port does not save:
  there is no world ranking (aidocks/project_port_plan.md, question 9).
* Two buttons, storyboard segues with no code: **play** to the game and **score** to the
  ranking (``analysis/data/nib_Main.txt``).  Their titles are in a 1-point font: invisible,
  but what VoiceOver read.  No sound or speech of its own.
* ``unwindToHomeScreenSegue:`` (0x100019fa0) is empty: coming back runs nothing.

PORT: the buttons are rows, with a third, "Quit", which an iPhone app never had; Escape
quits too.  Since the fourth release Play and Score first ask for a difficulty
(``ui/difficulty_screen.py``), and each difficulty has its own best five, set like
``rank`` when missing (aidocks/project_difficulty_plan.md).
"""
from __future__ import annotations

from ..platform.defaults import COUNT_TUTORIAL_KEY, RANK_KEYS
from ..ui.rows import RowScreen

#: The local ranking a new save starts with (viewDidLoad, 0x10001a00c..0x10001a334).
DEFAULT_RANK = [{'Name': 'Player', 'Score': '0'} for _ in range(5)]


def default_rank():
    return [dict(e) for e in DEFAULT_RANK]


class HomeScreenViewController(RowScreen):
    title = 'Main menu'
    keys_line = 'Up/Down move   Enter choose   Escape quit   F1 key bindings   Alt+F4 quit'

    def __init__(self, defaults=None, speech=None):
        super().__init__(speech)
        self.defaults = defaults
        # the buttons' titles, play and score; PORT: each asks for a difficulty first, Score
        # is "Scores", and Stats and Quit are added (the dev; project_scores_stats_plan.md)
        self.rows = [('choose_game', 'Play'), ('tutorial', 'Tutorial'),
                     ('choose_ranking', 'Scores'), ('choose_stats', 'Stats'), ('quit', 'Quit')]

    # HomeScreenViewController.viewDidLoad 0x100019fa4
    def viewDidLoad(self, announce=True):
        d = self.defaults
        if d is not None:
            changed = False
            for key in RANK_KEYS.values():                         # PORT: one each
                if d.objectForKey_(key) is None:
                    d.setObject_forKey_(default_rank(), key)
                    changed = True
            if d.objectForKey_(COUNT_TUTORIAL_KEY) is None:
                d.setInteger_forKey_(0, COUNT_TUTORIAL_KEY)
                changed = True
            if changed:
                d.synchronize()
        if announce:
            self.announce(self.title)

    def choose(self, key):
        self.next = key

    def back(self):
        self.next = 'quit'
