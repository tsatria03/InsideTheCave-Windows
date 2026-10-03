"""The screens: the earphone warning, the menu, the result screen and its saving, the
ranking, and the pause menu.  No window and no sound: the screens are driven key by key,
and what they would say is collected.
"""
from __future__ import annotations

import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, ROOT)
import _scratch_save                                             # noqa: E402  never the real save

from insidethecave.game import result_view_controller as R      # noqa: E402
from insidethecave.game.home_screen_view_controller import (     # noqa: E402
    HomeScreenViewController, default_rank)
from insidethecave.game.ranking_view_controller import RankingViewController  # noqa: E402
from insidethecave.game.warning_view_controller import WarningViewController  # noqa: E402
from insidethecave.platform import runloop                      # noqa: E402
from insidethecave.platform.defaults import UserDefaults        # noqa: E402
from insidethecave.platform.keymap import KeyMap                 # noqa: E402
from insidethecave.ui.game_input import GameInput               # noqa: E402


class _Said:
    def __init__(self):
        self.lines = []

    def speak(self, text, interrupt=True):
        self.lines.append(text)
        return True

    def stop(self):
        pass

    @property
    def last(self):
        return self.lines[-1] if self.lines else None


def _defaults(rank=None, count=None):
    d = UserDefaults()
    for key in ('rank', 'countTutorial'):
        d.removeObjectForKey_(key)
    if rank is not None:
        d.setObject_forKey_(rank, 'rank')
    if count is not None:
        d.setInteger_forKey_(count, 'countTutorial')
    return d


def _rank(*scores):
    return [{'Name': 'P%d' % i, 'Score': str(s)} for i, s in enumerate(scores)]


def _keys(screen, *names):
    for name in names:
        screen.key(name, name if len(name) == 1 else '')


# ---- the warning ---------------------------------------------------------------------------

def test_the_warning_is_english_or_portuguese():
    for code, start in (('en', 'Put the earphone'), ('pt', 'Coloque o fone'),
                        ('fr', 'Put the earphone')):
        said = _Said()
        w = WarningViewController(said, runloop.RunLoop(clock_fn=lambda: 0.0), code)
        w.viewDidLoad()
        assert said.last.startswith(start), (code, said.last)


def test_the_warning_goes_to_the_menu_after_three_seconds():
    t = [0.0]
    loop = runloop.RunLoop(clock_fn=lambda: t[0])
    w = WarningViewController(_Said(), loop, 'en')
    w.viewDidLoad()
    t[0] = 2.9
    loop.pump()
    assert w.next is None
    t[0] = 3.0
    loop.pump()
    assert w.next == 'menu'


def test_any_key_skips_the_warning_and_stops_its_timer():
    loop = runloop.RunLoop(clock_fn=lambda: 0.0)
    w = WarningViewController(_Said(), loop, 'en')
    w.viewDidLoad()
    w.key('x', 'x')
    assert w.next == 'menu' and not w.timer.isValid()


# ---- the menu ------------------------------------------------------------------------------

def test_the_menu_makes_a_new_save_s_ranking_and_tutorial_count():
    d = _defaults()
    HomeScreenViewController(d, _Said()).viewDidLoad()
    assert d.objectForKey_('rank') == default_rank()
    assert len(default_rank()) == 5 and default_rank()[0] == {'Name': 'Player', 'Score': '0'}
    assert d.integerForKey_('countTutorial') == 0


def test_the_menu_keeps_an_existing_ranking_and_count():
    d = _defaults(rank=_rank(50, 40, 30, 20, 10), count=2)
    HomeScreenViewController(d, _Said()).viewDidLoad()
    assert d.objectForKey_('rank') == _rank(50, 40, 30, 20, 10)
    assert d.integerForKey_('countTutorial') == 2


def test_the_menu_rows_and_keys():
    said = _Said()
    m = HomeScreenViewController(_defaults(), said)
    m.viewDidLoad()
    assert said.last == 'Main menu. Play'
    _keys(m, 'up')
    assert said.last == 'Play', 'the list stops at the top'
    _keys(m, 'down')
    assert said.last == 'Score'
    _keys(m, 'end')
    assert said.last == 'Quit'
    _keys(m, 'down')
    assert said.last == 'Quit', 'and at the bottom'
    _keys(m, 'home', 'x')
    assert said.last == 'Play', 'another key says the row again'
    n = len(said.lines)
    _keys(m, 'left shift')
    assert len(said.lines) == n, 'Shift alone says nothing'
    _keys(m, 'return')
    assert m.next == 'game'


def test_score_goes_to_the_ranking_and_escape_quits():
    m = HomeScreenViewController(_defaults(), _Said())
    m.viewDidLoad()
    _keys(m, 'down', 'space')
    assert m.next == 'ranking'
    m.next = None
    _keys(m, 'escape')
    assert m.next == 'quit'


# ---- the result screen ---------------------------------------------------------------------

def test_the_result_screen_says_the_score_and_asks_for_a_name():
    said = _Said()
    r = R.ResultViewController(120, 4, _defaults(rank=default_rank()), said)
    r.viewDidLoad()
    assert said.last == 'Game over. Score 120. Coins 4. Insert name', said.last


def test_typing_a_name_says_each_character():
    said = _Said()
    r = R.ResultViewController(1, 0, _defaults(), said)
    r.viewDidLoad()
    r.key('left shift')
    r.key('a', 'A')
    r.key('n', 'n')
    r.key('space', ' ')
    r.key('b', 'b')
    assert r.name == 'An b'
    assert said.lines[-4:] == ['A', 'n', 'space', 'b']
    r.key('backspace')
    assert r.name == 'An ' and said.last == 'b'
    _keys(r, 'down', 'up')
    assert said.last == 'Name: An '


def test_backspace_on_an_empty_name_says_blank():
    said = _Said()
    r = R.ResultViewController(1, 0, _defaults(), said)
    r.key('backspace')
    assert said.last == 'Blank' and r.name == ''


def test_a_name_holds_at_most_fifteen_characters():
    said = _Said()
    r = R.ResultViewController(1, 0, _defaults(), said)
    for ch in 'abcdefghijklmnopq':
        r.key(ch, ch)
    assert r.name == 'abcdefghijklmno' and len(r.name) == R.NAME_LIMIT == 15
    assert said.last.startswith('Name full')


def test_enter_in_the_name_field_goes_on_to_replay():
    said = _Said()
    r = R.ResultViewController(1, 0, _defaults(), said)
    r.key('return')
    assert r.current() == 'replay' and said.last == 'Replay' and r.next is None


def test_replay_and_menu_save_first():
    d = _defaults(rank=default_rank())
    r = R.ResultViewController(30, 1, d, _Said())
    _keys(r, 'z', 'o', 'e', 'return', 'return')
    assert r.next == 'game'
    assert d.objectForKey_('rank')[0] == {'Name': 'zoe', 'Score': '30'}

    d = _defaults(rank=default_rank())
    r = R.ResultViewController(30, 1, d, _Said())
    _keys(r, 'escape')
    assert r.next == 'menu'
    assert d.objectForKey_('rank')[0] == {'Name': 'unnamed player', 'Score': '30'}


def test_check_rank_saves_once():
    d = _defaults(rank=default_rank())
    r = R.ResultViewController(30, 1, d, _Said())
    assert r.checkRank() is True
    assert r.checkRank() is False
    assert [e['Score'] for e in d.objectForKey_('rank')] == ['30', '0', '0', '0', '0']


def test_a_blank_name_or_insert_name_is_saved_as_unnamed_player():
    for typed in ('', '   ', 'Insert name'):
        r = R.ResultViewController(5, 0, _defaults(), _Said())
        r.name = typed
        assert r.saved_name() == 'unnamed player', typed
    r = R.ResultViewController(5, 0, _defaults(), _Said())
    r.name = ' Ana '
    assert r.saved_name() == 'Ana'


def test_the_ranking_takes_only_a_score_above_the_fifth():
    rank = _rank(50, 40, 30, 20, 10)
    assert R.ranked(rank, 'new', 10) is None, 'equal to the fifth: not in'
    assert R.ranked(rank, 'new', 3) is None
    new = R.ranked(rank, 'new', 11)
    assert [e['Score'] for e in new] == ['50', '40', '30', '20', '11']
    new = R.ranked(rank, 'new', 99)
    assert new[0] == {'Name': 'new', 'Score': '99'} and len(new) == 5
    assert new[-1]['Score'] == '20', 'the sixth is dropped'


def test_a_score_already_in_the_top_five_is_not_saved_again():
    """The dev: "There should not be any tied scores." The one already there stays."""
    for score in (50, 30, 20):
        assert R.ranked(_rank(50, 40, 30, 20, 10), 'new', score) is None, score
    d = _defaults(rank=_rank(63, 40, 30, 20, 10))
    r = R.ResultViewController(63, 0, d, _Said())
    assert r.checkRank() is False
    assert [e['Score'] for e in d.objectForKey_('rank')] == ['63', '40', '30', '20', '10']


def test_a_short_or_damaged_ranking_still_saves():
    new = R.ranked([{'Name': 'A', 'Score': 'x'}], 'new', 1)
    assert new[0] == {'Name': 'new', 'Score': '1'} and len(new) == 5
    assert R.score_of({'Score': 'nonsense'}) == 0


# ---- the ranking ---------------------------------------------------------------------------

def test_the_ranking_reads_the_five_and_menu():
    said = _Said()
    d = _defaults(rank=[{'Name': 'Ana', 'Score': '120'}] + default_rank()[:4])
    s = RankingViewController(d, said)
    s.viewDidLoad()
    assert said.last == 'Score, your best five. 1, Ana, 120'
    _keys(s, 'down')
    assert said.last == '2, Player, 0'
    _keys(s, 'end')
    assert said.last == 'Menu'
    _keys(s, 'return')
    assert s.next == 'menu'
    s.next = None
    _keys(s, 'home', 'escape')
    assert s.next == 'menu'


# ---- the pause menu ------------------------------------------------------------------------

class _Scene:
    def __init__(self):
        self.paused_by_player = False
        self.moves = []

    def pause(self):
        self.paused_by_player = True

    def resume(self):
        self.paused_by_player = False

    def movePlayerLeft(self):
        self.moves.append('left')

    def movePlayerRight(self):
        self.moves.append('right')

    def throwTorch(self):
        self.moves.append('throw')


def _game_input():
    said = _Said()
    gi = GameInput(KeyMap(), said)
    gi.attach(_Scene())
    return gi, said


def test_pausing_opens_the_menu_and_escape_or_p_resumes():
    gi, said = _game_input()
    gi.press('escape')
    assert gi.paused and said.last == 'Paused. Resume'
    gi.press('escape')
    assert not gi.paused
    gi.press('p')
    gi.release('p')
    assert gi.paused
    gi.press('p')
    gi.release('p')
    assert not gi.paused


def test_the_pause_menu_rows():
    gi, said = _game_input()
    gi.press('escape')
    gi.press('down')
    assert said.last == 'Restart'
    gi.press('down')
    assert said.last == 'Quit to menu'
    gi.press('up')
    gi.press('up')
    assert said.last == 'Resume'
    gi.press('return')
    assert not gi.paused and gi.request is None


def test_up_moves_the_pause_menu_and_does_not_throw():
    gi, said = _game_input()
    gi.press('escape')
    gi.press('up')
    gi.release('up')
    gi.press('a')
    gi.release('a')
    assert gi.scene.moves == [] and gi.paused
    assert said.last == 'Resume', 'a game key says the row again'


def test_restart_and_quit_to_menu_are_left_for_the_screen_loop():
    for presses, wanted in ((('down',), 'restart'), (('end',), 'menu')):
        gi, said = _game_input()
        gi.press('escape')
        for name in presses:
            gi.press(name)
        gi.press('return')
        assert gi.request == wanted and gi.paused
        gi.attach(_Scene())
        assert gi.request is None


def test_pausing_again_starts_the_menu_at_resume():
    gi, said = _game_input()
    gi.press('escape')
    gi.press('end')
    gi.press('escape')
    gi.press('escape')
    assert gi.menu.current() == 'resume'


if __name__ == '__main__':
    _scratch_save.run(globals())
