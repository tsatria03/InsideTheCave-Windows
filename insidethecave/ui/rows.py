"""PORT ADDITION: a screen of rows, read one at a time, in place of VoiceOver on the
original's buttons.

The original's screens are a few buttons each, and a blind player heard them through
VoiceOver, swiping from one to the next and double-tapping (GAME_STRUCTURE.md sections 9
to 12).  Here a screen is a list of rows: Up and Down move and say each, Home and End go to
the first and the last, Enter or Space chooses, and Escape goes back.  Any other key says
the row again, as the reference port's menus do.  The rows wrap around at both ends.  The
screen loop in ``InsideTheCave.py`` reads ``next`` to know where to go.
"""
from __future__ import annotations

import logging

log = logging.getLogger('screens')

#: The keys every screen of rows reads.
CHOOSE = ('return', 'enter', 'space')
#: Keys that do nothing on their own, so Shift for a capital letter says nothing.
MODIFIERS = ('left shift', 'right shift', 'left ctrl', 'right ctrl', 'left alt',
             'right alt', 'left meta', 'right meta', 'left gui', 'right gui', 'caps lock',
             'num lock', 'mode', 'alt gr')
KEYS_LINE = 'Up/Down move   Enter choose   Escape back   F1 key bindings   Alt+F4 quit'


class RowScreen:
    """A screen of ``(key, label)`` rows.  Subclasses fill ``rows``, and handle a choice in
    ``choose`` and Escape in ``back``."""

    title = ''
    keys_line = KEYS_LINE

    def __init__(self, speech=None):
        self.speech = speech
        self.rows = []
        self.index = 0
        #: Where the screen loop goes next: 'menu', 'game', 'ranking', 'result', 'quit'.
        self.next = None

    # ---- speaking ---------------------------------------------------------------------
    def say(self, text, interrupt=True):
        log.info('say: %s', text)
        if self.speech is not None:
            self.speech.speak(text, interrupt=interrupt)

    def label(self, i=None):
        i = self.index if i is None else i
        return self.rows[i][1] if 0 <= i < len(self.rows) else ''

    def current(self):
        return self.rows[self.index][0] if self.rows else None

    def say_row(self):
        self.say(self.label())

    def announce(self, intro):
        """Arriving: the screen's name, then the row the player is on."""
        self.say('%s. %s' % (intro, self.label()) if self.rows else intro)

    # ---- moving -----------------------------------------------------------------------
    def move(self, step):
        """Up or Down.  The list wraps around: Down on the last row goes to the first, and
        Up on the first to the last (the dev, for the second release)."""
        if self.rows:
            self.index = (self.index + step) % len(self.rows)
        self.say_row()

    def jump(self, last):
        if self.rows:
            self.index = len(self.rows) - 1 if last else 0
        self.say_row()

    # ---- what subclasses do -----------------------------------------------------------
    def choose(self, key):
        """Enter on the row ``key``."""

    def back(self):
        """Escape."""

    # ---- keys ---------------------------------------------------------------------------
    def key(self, name, char=''):
        """A key went down: pygame's name for it, and the character it types, if any."""
        if name in MODIFIERS:
            return
        if name == 'up':
            self.move(-1)
        elif name == 'down':
            self.move(1)
        elif name in ('home', 'end'):
            self.jump(last=(name == 'end'))
        elif name in CHOOSE:
            self.choose(self.current())
        elif name == 'escape':
            self.back()
        else:
            self.say_row()

    # ---- what a sighted helper sees -----------------------------------------------------
    def row_lines(self):
        return ['%s %s' % ('>' if i == self.index else ' ', self.label(i))
                for i in range(len(self.rows))]

    def lines(self):
        return ['Inside The Cave - %s' % self.title, ''] + self.row_lines() \
            + ['', self.keys_line]
