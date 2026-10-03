"""The keys: ``platform/keymap.py``, ``ui/keybind_screen.py`` and ``ui/focus.py``.

The key map is written to the throwaway save folder, and the binding screen speaks to a
stand-in that only records, so nothing is said and no key file of the player's is touched.
pygame is stood in for by the few names the screen reads.
"""
from __future__ import annotations

import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
import _scratch_save                                             # noqa: E402  never the real save

from insidethecave import paths                                  # noqa: E402
from insidethecave.platform import keymap                        # noqa: E402
from insidethecave.platform.keymap import KeyMap                 # noqa: E402
from insidethecave.ui import focus                               # noqa: E402
from insidethecave.ui.keybind_screen import KeyBindScreen        # noqa: E402


def _fresh():
    path = os.path.join(paths.user_dir(), 'keys.json')
    if os.path.exists(path):
        os.remove(path)
    return KeyMap()


class _Said:
    def __init__(self):
        self.lines = []

    def speak(self, text, interrupt=True):
        self.lines.append(text)
        return True


class _Event:
    def __init__(self, type, key=None):
        self.type = type
        self.key = key


class _Key:
    @staticmethod
    def name(key):
        return key


class _Pygame:
    """The names KeyBindScreen and focus read; keys are their own names."""
    QUIT, KEYDOWN, KEYUP = 'quit', 'keydown', 'keyup'
    WINDOWFOCUSLOST, WINDOWFOCUSGAINED = 'focuslost', 'focusgained'
    key = _Key


def _tap(screen, *names):
    for n in names:
        screen.handle(_Event(_Pygame.KEYDOWN, n), _Pygame)
        screen.handle(_Event(_Pygame.KEYUP, n), _Pygame)


def test_the_defaults_are_the_agreed_keys():
    """The dev, 2026-10-02: A or Left, D or Right, W or Up, and P."""
    km = _fresh()
    assert km.bindings['move_left'] == [('a',), ('left',)]
    assert km.bindings['move_right'] == [('d',), ('right',)]
    assert km.bindings['throw'] == [('w',), ('up',)]
    assert km.bindings['pause'] == [('p',)]
    assert km.bindings['torch'] == [('t',)], 'the torch key (the dev, fourth release)'
    assert (km.bindings['score'], km.bindings['coins'], km.bindings['speed']) == \
        ([('s',)], [('c',)], [('e',)]), 'the status keys (the dev, fourth release)'


def test_every_default_key_acts_at_once():
    """No default is a chord, so no key waits for one."""
    km = _fresh()
    for name, action in (('a', 'move_left'), ('left', 'move_left'), ('d', 'move_right'),
                         ('right', 'move_right'), ('w', 'throw'), ('up', 'throw'),
                         ('p', 'pause'), ('t', 'torch'), ('s', 'score'), ('c', 'coins'),
                         ('e', 'speed')):
        assert km.press(name) == (action, False), name
        km.release(name)


def test_an_unbound_key_does_nothing():
    km = _fresh()
    assert km.press('x') == (None, False)


def test_rolling_from_one_key_to_the_next_takes_the_new_one():
    km = _fresh()
    km.press('a')
    assert km.press('d') == ('move_right', False)


def test_the_key_file_is_written_on_the_first_start():
    km = _fresh()
    with open(km.path, encoding='utf-8') as f:
        saved = json.load(f)
    assert saved['throw'] == [['w'], ['up']]


def _old_file(bindings):
    """A keys.json written before the torch key existed."""
    path = os.path.join(paths.user_dir(), 'keys.json')
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(bindings, f)
    return path


def test_an_older_key_file_gains_the_new_keys():
    path = _old_file({'move_left': [['a'], ['left']], 'move_right': [['d'], ['right']],
                      'throw': [['w'], ['up']], 'pause': [['p']]})
    km = KeyMap()
    assert km.bindings['torch'] == [('t',)] and km.bindings['speed'] == [('e',)]
    with open(path, encoding='utf-8') as f:
        saved = json.load(f)
    assert saved['torch'] == [['t']] and saved['score'] == [['s']], 'not written back'


def test_a_new_key_never_takes_one_the_player_already_uses():
    """A player who put the pause on T keeps it; the torch key starts with none."""
    _old_file({'move_left': [['a'], ['left']], 'move_right': [['d'], ['right']],
               'throw': [['w'], ['up']], 'pause': [['t']]})
    km = KeyMap()
    assert km.bindings['pause'] == [('t',)] and km.bindings['torch'] == []
    assert km.press('t') == ('pause', False)


def test_a_rebound_key_is_kept_and_taken_off_the_other_action():
    km = _fresh()
    km.set_binding('throw', ('a',))
    assert km.bindings['throw'] == [('a',)]
    assert km.bindings['move_left'] == [('left',)]
    assert KeyMap().bindings['throw'] == [('a',)], 'the change was not saved'


def test_a_chord_waits_for_its_window():
    km = _fresh()
    km.set_binding('pause', ('left ctrl', 'p'))
    assert km.press('left ctrl') == (None, True)
    assert km.press('p') == ('pause', False)


def test_a_hint_says_the_players_own_keys():
    km = _fresh()
    assert km.hint_keys('move_left') == 'A or Left Arrow'
    assert km.hint_keys('throw') == 'W or Up Arrow'
    km.set_binding('throw', ('space',), replace=False)
    assert km.hint_keys('throw') == 'W, Up Arrow, or Space'
    km.clear('pause')
    assert km.hint_keys('pause') is None


def test_the_fixed_keys_cannot_be_rebound():
    km = _fresh()
    said = _Said()
    screen = KeyBindScreen(keymap=km, speech=said)
    screen.open()
    screen.handle(_Event(_Pygame.KEYDOWN, 'return'), _Pygame)
    _tap(screen, 'escape')
    assert 'cannot be rebound' in said.lines[-1], said.lines[-1]
    assert km.bindings['move_left'] == [('a',), ('left',)]


def test_the_binding_screen_rebinds_what_is_held():
    km = _fresh()
    said = _Said()
    screen = KeyBindScreen(keymap=km, speech=said)
    screen.open()
    assert said.lines[0].startswith('Key bindings.')
    assert said.lines[1] == 'Move left: A, or Left Arrow'
    _tap(screen, 'down', 'down')
    assert said.lines[-1] == 'Throw the torch: W, or Up Arrow'
    screen.handle(_Event(_Pygame.KEYDOWN, 'return'), _Pygame)
    screen.handle(_Event(_Pygame.KEYUP, 'return'), _Pygame)    # Enter's own key-up
    assert screen.capturing
    _tap(screen, 'space')
    assert not screen.capturing
    assert said.lines[-1] == 'Throw the torch is now Space.'
    assert km.bindings['throw'] == [('space',)]


def test_reset_asks_first():
    km = _fresh()
    km.set_binding('throw', ('space',))
    said = _Said()
    screen = KeyBindScreen(keymap=km, speech=said)
    screen.open()
    _tap(screen, 'r', 'x')
    assert km.bindings['throw'] == [('space',)], 'reset without being asked twice'
    _tap(screen, 'r', 'r')
    assert km.bindings['throw'] == [('w',), ('up',)]


def test_escape_leaves_the_binding_screen():
    said = _Said()
    screen = KeyBindScreen(keymap=_fresh(), speech=said)
    screen.open()
    _tap(screen, 'escape')
    assert screen.done and said.lines[-1] == 'Back.'


def test_leaving_the_window_pauses_what_can_be_paused():
    class Game:
        paused = False

        def pause(self):
            self.paused = True

    game = Game()
    assert focus.focus_lost(_Event(_Pygame.WINDOWFOCUSLOST), _Pygame)
    assert not focus.focus_lost(_Event(_Pygame.KEYDOWN, 'p'), _Pygame)
    assert focus.pause_on_focus_loss(game) is True and game.paused
    assert focus.pause_on_focus_loss(object()) is False


def test_the_fixed_keys_are_the_way_out_and_the_volume():
    assert set(keymap.FIXED) == {'f1', 'escape', 'page up', 'page down', 'home', 'end'}


if __name__ == '__main__':
    _scratch_save.run(globals())
