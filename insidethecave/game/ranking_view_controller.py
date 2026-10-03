"""``RankingViewController``: the rankings.  Ported from
``analysis/disasm/dz_RankingViewController.txt``.

* ``viewDidLoad`` (0x100020e60) makes the table its own data source and delegate.
* The table (``tableView:cellForRowAtIndexPath:`` 0x100021a9c) shows, for each entry of
  ``rank`` (Local) or ``rankWorld`` (World), its position, its "Name" and its "Score", with
  three ``setText:`` calls (0x100021d08, 0x100021fc8, 0x100022274).
* ``changeValue:`` (0x100022428) is the Local / World switch; ``menuBack:`` (0x100021018), the
  MENU button, unwinds to the menu.

PORT: no World tab, as there are no online scores (aidocks/project_port_plan.md, question
9).  The five entries and MENU are rows, read as "1, Ana, 120"; Escape is MENU.
"""
from __future__ import annotations

from ..platform.defaults import RANK_KEY
from ..ui.rows import RowScreen
from .home_screen_view_controller import default_rank


class RankingViewController(RowScreen):
    title = 'Score'
    keys_line = 'Up/Down move   Enter choose   Escape menu   F1 key bindings   Alt+F4 quit'

    def __init__(self, defaults=None, speech=None):
        super().__init__(speech)
        self.defaults = defaults

    def entries(self):
        rank = self.defaults.objectForKey_(RANK_KEY) if self.defaults is not None else None
        if not isinstance(rank, list) or not rank:
            rank = default_rank()
        return [e for e in rank if isinstance(e, dict)]

    # RankingViewController.viewDidLoad 0x100020e60, and the table 0x100021a9c
    def viewDidLoad(self):
        self.rows = [('entry', '%d, %s, %s' % (i + 1, e.get('Name', ''), e.get('Score', '')))
                     for i, e in enumerate(self.entries())]
        self.rows.append(('menu', 'Menu'))                              # the MENU button
        self.index = 0
        self.announce('Score, your best five')

    def choose(self, key):
        if key == 'menu':
            self.back()
        else:
            self.say_row()

    # -[RankingViewController menuBack:] 0x100021018
    def back(self):
        self.next = 'menu'                                              # unwindToHomeScreenSegue
