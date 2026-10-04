"""PORT ADDITION: the Stats screen (the dev, for the fourth release;
aidocks/project_scores_stats_plan.md).

Stats on the main menu asks for Easy, Medium, Hard or All-time (``difficulty_screen.py``),
then this screen reads that set as rows, in the dev's order, "Games played, 24." to
"Monsters dodged, 140.", then Menu.  Menu and Escape go back to the choice.
"""
from __future__ import annotations

from ..game import stats
from .difficulty_screen import NAMES
from .rows import RowScreen


class StatsScreen(RowScreen):
    keys_line = ('Up/Down move   Enter choose   Escape difficulties   F1 key bindings   '
                 'Alt+F4 quit')

    def __init__(self, defaults=None, speech=None, which='easy'):
        """``which``: a difficulty, or 'all'."""
        super().__init__(speech)
        self.defaults = defaults
        self.which = which
        self.title = 'Stats, %s' % NAMES[which]

    def viewDidLoad(self):
        self.rows = [('stat', line) for line in stats.lines(stats.totals(self.defaults,
                                                                         self.which))]
        self.rows.append(('menu', 'Menu'))
        self.index = 0
        self.announce('%s stats' % NAMES[self.which])

    def choose(self, key):
        if key == 'menu':
            self.back()
        else:
            self.say_row()

    def back(self):
        self.next = 'choose_stats'
