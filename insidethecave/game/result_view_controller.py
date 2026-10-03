"""``ResultViewController``: the game over screen, the name and saving.  Ported from
``analysis/disasm/dz_ResultViewController.txt``.

* ``viewDidLoad`` (0x10001bf40): the score and coin labels from the game
  (``prepareForSegue:sender:`` 0x100018b0c), and the name field filled by ``checkName``.
* The name field takes at most 15 characters (``textField:shouldChangeCharactersInRange:
  replacementString:``, the new length below 16 at 0x1000204a0); Return only closes the
  keyboard (``textFieldShouldReturn:`` 0x10001e63c).
* **Replay** (``replay:`` 0x10001e300) and **Menu** (``backMenu:`` 0x10001e46c) both run
  ``checkRank`` first, then unwind to the game or to the menu.
* ``checkRank`` (0x10001d65c), checked instruction by instruction:
  - the score, read back from its label, goes in only when it is above the fifth entry's,
    strictly (``cmp``/``b.le`` at 0x10001dac4);
  - the name "Insert name" is saved as "unnamed player" (0x10001db48..0x10001dbf4), and an
    empty name saves nothing (0x10001dc04..0x10001dc14);
  - the new entry, ``{"Name", "Score"}`` as strings, is appended, the list sorted by score,
    best first (the comparison is a strict "less than" with its arguments swapped,
    0x10001fb60), and the sixth removed (0x10001de04, 0x10001de20); then ``rank`` is stored.
    A score equal to one already in the list went in beside it.
  - It also sends the score to the world ranking (0x10001de80), which the port leaves out
    (question 9).

PORT, each in aidocks/DIVERGENCES.md:
* the name field starts empty, and "Insert name" is said, where the original guessed the
  name from the device's name in ``checkName`` (and crashed on a short one; question 8);
* a blank name is saved as "unnamed player" too, so a score is never thrown away (question 4);
* a score equal to one already in the top five is not saved again, so no two are tied (the
  dev, 2026-10-02: "There should not be any tied scores."); the one already there stays;
* the screen is rows: the name field, Replay and Menu.  On the field, typed characters go
  in and are said, Backspace deletes and says what it took, and Enter goes on to Replay.
"""
from __future__ import annotations

import logging

from ..platform.defaults import RANK_KEY
from ..ui.rows import MODIFIERS, RowScreen
from .home_screen_view_controller import default_rank

log = logging.getLogger('screens')

NAME_LIMIT = 15                    # the new length must be below 16 (0x1000204a0)
RANK_SIZE = 5
INSERT_NAME = 'Insert name'        # 0x100026e15
UNNAMED = 'unnamed player'         # 0x100026e26
#: The keys that move or choose even on the name field.
NAVIGATION = ('up', 'down', 'home', 'end', 'return', 'enter', 'escape', 'tab')


def score_of(entry):
    """An entry's score as a number.  The original's ``Int(String)`` traps on anything
    else; the port counts it as 0."""
    try:
        return int(str(entry.get('Score', '0')).strip())
    except (AttributeError, ValueError):
        return 0


def ranked(rank, name, score):
    """``checkRank``'s list: ``rank`` with the new entry in it, best first, five long; or
    None when the score does not get in.  ``name`` is already what is saved."""
    rank = [dict(e) for e in rank if isinstance(e, dict)]
    if len(rank) < RANK_SIZE:            # the original traps here (0x10001d884)
        rank += default_rank()[len(rank):]
    if score <= score_of(rank[RANK_SIZE - 1]):                         # 0x10001dac4
        return None
    if any(score_of(e) == score for e in rank):     # PORT: no two equal scores (the dev)
        return None
    rank.append({'Name': name, 'Score': str(score)})
    rank.sort(key=lambda e: -score_of(e))           # best first
    return rank[:RANK_SIZE]


def spoken_char(ch):
    return 'space' if ch == ' ' else ch


class ResultViewController(RowScreen):
    title = 'Game over'
    keys_line = ('Type your name   Up/Down move   Enter choose   Escape menu   '
                 'F1 key bindings')

    def __init__(self, score=0, coins=0, defaults=None, speech=None):
        super().__init__(speech)
        self.score = int(score)
        self.coins = int(coins)
        self.defaults = defaults
        self.name = ''
        self.saved = False
        self.rows = [('name', ''), ('replay', 'Replay'), ('menu', 'Menu')]

    def label(self, i=None):
        i = self.index if i is None else i
        if 0 <= i < len(self.rows) and self.rows[i][0] == 'name':
            return 'Name: %s' % self.name if self.name else INSERT_NAME
        return super().label(i)

    # ResultViewController.viewDidLoad 0x10001bf40
    def viewDidLoad(self):
        self.announce('Game over. Score %d. Coins %d' % (self.score, self.coins))

    # ---- the name field ---------------------------------------------------------------
    def key(self, name, char=''):
        if name in MODIFIERS:
            return
        if self.current() == 'name' and name not in NAVIGATION:
            if name == 'backspace':
                self.backspace()
            elif char and char.isprintable():
                self.type(char)
            else:
                self.say_row()
            return
        if self.current() == 'name' and name in ('return', 'enter'):
            self.index = 1                      # textFieldShouldReturn: only lets go
            self.say_row()
            return
        super().key(name, char)

    def type(self, ch):
        if len(self.name) + len(ch) > NAME_LIMIT:
            self.say('Name full, %d characters.' % NAME_LIMIT)
            return
        self.name += ch
        self.say(spoken_char(ch))

    def backspace(self):
        if not self.name:
            self.say('Blank')
            return
        gone, self.name = self.name[-1], self.name[:-1]
        self.say(spoken_char(gone))

    # ---- saving -----------------------------------------------------------------------
    def saved_name(self):
        """The name as ``checkRank`` saves it.  PORT: a blank one is "unnamed player" too."""
        name = self.name.strip()
        return UNNAMED if name in ('', INSERT_NAME) else name

    # ResultViewController.checkRank 0x10001d65c
    def checkRank(self):
        """Save the score in the local top five if it gets in.  True when it did.  Runs once,
        whichever button goes first."""
        if self.saved or self.defaults is None:
            return False
        self.saved = True
        rank = self.defaults.objectForKey_(RANK_KEY)
        new = ranked(rank if isinstance(rank, list) else [], self.saved_name(), self.score)
        if new is None:
            return False
        self.defaults.setObject_forKey_(new, RANK_KEY)
        self.defaults.synchronize()
        log.info('saved %s, %d', self.saved_name(), self.score)
        return True

    def choose(self, key):
        if key == 'replay':                                             # replay: 0x10001e300
            self.checkRank()
            self.next = 'game'                                          # unwindToGameSegue
        elif key == 'menu':                                             # backMenu: 0x10001e46c
            self.checkRank()
            self.next = 'menu'                                          # unwindToHomeScreenSegue
        else:
            self.say_row()

    def back(self):
        self.choose('menu')

    def lines(self):
        return ['Inside The Cave - %s' % self.title,
                'Score %d   Coins %d' % (self.score, self.coins), ''] \
            + self.row_lines() + ['', self.keys_line]
