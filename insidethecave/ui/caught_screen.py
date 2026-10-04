"""PORT ADDITION: the tutorial's game over (the dev, for the fourth release;
aidocks/project_tutorial_plan.md).

A tutorial game saves nothing and counts nothing (the dev: "Scores should not count what so
ever. It's purely for practice."), so it has no result screen: "You were caught.", then
Replay, which starts the tutorial again without its welcome, and Menu.  Escape is Menu.
"""
from __future__ import annotations

from .rows import RowScreen

CAUGHT = 'You were caught.'


class CaughtScreen(RowScreen):
    title = 'Tutorial'
    keys_line = 'Up/Down move   Enter choose   Escape menu   F1 key bindings   Alt+F4 quit'

    def __init__(self, speech=None):
        super().__init__(speech)
        self.rows = [('tutorial', 'Replay'), ('menu', 'Menu')]

    def viewDidLoad(self):
        self.announce(CAUGHT[:-1])

    def choose(self, key):
        self.next = key

    def back(self):
        self.next = 'menu'
