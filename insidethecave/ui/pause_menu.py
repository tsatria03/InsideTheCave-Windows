"""PORT ADDITION: the pause menu.  The original has no pause at all (aidocks/DIVERGENCES.md).

The dev, 2026-10-02: "I want a propper pause menu with resume, restart, and quit to menu
if possible. Pressing escape will still resume the game."  Pausing holds the game
(``ui/game_input.py``) and opens these rows; Escape and the pause key resume.  Restart and
Quit to menu leave the game without saving a score: only a game over reaches the result
screen, the original's only way to save.
"""
from __future__ import annotations

from .rows import RowScreen

PAUSED = 'Paused'


class PauseMenu(RowScreen):
    title = 'Paused'
    keys_line = ('Up/Down move   Enter choose   Escape or P resume   F1 key bindings   '
                 'Alt+F4 quit')

    def __init__(self, speech=None):
        super().__init__(speech)
        self.rows = [('resume', 'Resume'), ('restart', 'Restart'), ('menu', 'Quit to menu')]

    def open(self, speak=True):
        self.index = 0
        self.next = None
        if speak:
            self.announce(PAUSED)

    def choose(self, key):
        self.next = key

    def back(self):
        self.next = 'resume'
