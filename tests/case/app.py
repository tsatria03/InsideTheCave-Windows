"""The program: ``InsideTheCave.py``, its window, keys and frame loop.

Run on pygame's dummy display and OpenAL Soft's null driver, which ``_scratch_save`` sets,
so no window opens and nothing is heard; speech is silent.  The frames are driven one by
one rather than through ``App.run``, which would not return.
"""
from __future__ import annotations

import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, ROOT)
import _scratch_save                                             # noqa: E402  never the real save

import InsideTheCave                                             # noqa: E402
from insidethecave.platform import runloop                      # noqa: E402


class _Args:
    debug = True
    game = None
    stage = True
    verbose = False


class _Key:
    def __init__(self, pygame, key, down=True, mod=0, unicode=''):
        self.type = pygame.KEYDOWN if down else pygame.KEYUP
        self.key = key
        self.mod = mod
        self.unicode = unicode


def _app(first='game'):
    assert os.environ.get('SDL_VIDEODRIVER') == 'dummy'
    app = InsideTheCave.App(_Args())
    app.defaults.setInteger_forKey_(3, 'countTutorial')
    app.go(first)
    return app


def _frames(app, seconds):
    end = runloop.clock() + seconds
    while runloop.clock() < end:
        app.step(runloop.clock())
        app.draw()


def _press(app, key, mod=0, unicode=''):
    pg = app.pygame
    app.handle(_Key(pg, key, True, mod, unicode))
    app.handle(_Key(pg, key, False, mod))
    app.step(runloop.clock())


def test_the_program_starts_draws_and_closes():
    app = _app()
    try:
        _frames(app, 0.3)
        assert app.game.scene is not None and not app.game.over
        assert app.game.lines()[0].startswith('Inside The Cave')
    finally:
        app.close()


def test_the_keys_move_pause_and_change_the_volume():
    app = _app()
    pg = app.pygame
    try:
        _frames(app, 0.1)
        _press(app, pg.K_LEFT)
        assert app.game.scene.actualPositionPlayer == 0
        _press(app, pg.K_ESCAPE)
        assert app.game.scene.paused_by_player
        _press(app, pg.K_ESCAPE)
        assert not app.game.scene.paused_by_player
        before = app.volume.percents['MASTERVOLUME']
        _press(app, pg.K_PAGEDOWN)
        assert app.volume.percents['MASTERVOLUME'] == max(0, before - 10)
        _press(app, pg.K_PAGEUP)
    finally:
        app.close()


def test_home_and_end_set_the_master_volume_only_while_a_game_runs():
    app = _app()
    pg = app.pygame
    try:
        _frames(app, 0.1)
        p = app.volume.percents
        master = p['MASTERVOLUME']
        _press(app, pg.K_END)
        assert p['MASTERVOLUME'] == max(0, master - 10)
        _press(app, pg.K_HOME)
        assert p['MASTERVOLUME'] == master
        _press(app, pg.K_ESCAPE)                # paused: Home and End are the pause menu's
        _press(app, pg.K_END)
        assert p['MASTERVOLUME'] == master
        assert app.input.menu.current() == 'menu'
        _press(app, pg.K_ESCAPE)
        app.go('menu')                          # and the menu's
        _press(app, pg.K_END)
        assert p['MASTERVOLUME'] == master and app.page.current() == 'quit'
    finally:
        app.close()


def test_f1_holds_the_game_and_escape_brings_it_back():
    app = _app()
    pg = app.pygame
    try:
        _frames(app, 0.1)
        _press(app, pg.K_F1)
        assert app.keys_open and app.game.scene.paused_by_player
        _frames(app, 0.1)
        _press(app, pg.K_ESCAPE)
        assert not app.keys_open and not app.game.scene.paused_by_player
    finally:
        app.close()


def test_leaving_the_window_pauses():
    app = _app()
    pg = app.pygame
    try:
        class Lost:
            type = pg.WINDOWFOCUSLOST
        app.handle(Lost())
        assert app.game.scene.paused_by_player
    finally:
        app.close()


def test_alt_f4_quits():
    app = _app()
    pg = app.pygame
    try:
        app.handle(_Key(pg, pg.K_F4, True, pg.KMOD_LALT))
        assert not app.running
    finally:
        app.close()


# ---- the screens ---------------------------------------------------------------------------

def test_the_warning_then_the_menu_then_a_game():
    app = _app('warning')
    pg = app.pygame
    try:
        assert app.kind == 'warning'
        _frames(app, 0.1)
        assert app.kind == 'warning'
        _press(app, pg.K_x, unicode='x')
        assert app.kind == 'menu'
        assert app.lines()[0] == 'Inside The Cave - Main menu'
        _press(app, pg.K_RETURN)
        assert app.kind == 'game' and app.game.scene is not None
    finally:
        app.close()


def test_score_shows_the_ranking_and_escape_goes_back():
    app = _app('menu')
    pg = app.pygame
    try:
        _press(app, pg.K_DOWN)
        _press(app, pg.K_RETURN)
        assert app.kind == 'ranking'
        _press(app, pg.K_ESCAPE)
        assert app.kind == 'menu'
        _press(app, pg.K_ESCAPE)
        assert not app.running, 'Escape on the menu quits'
    finally:
        app.close()


def test_the_pause_menu_restarts_and_quits_to_the_menu():
    app = _app()
    pg = app.pygame
    try:
        _frames(app, 0.1)
        first = app.game.scene
        _press(app, pg.K_ESCAPE)
        _press(app, pg.K_DOWN)
        _press(app, pg.K_RETURN)
        assert app.kind == 'game' and app.game.scene is not first, 'restarted'
        assert not app.input.paused and not app.loop.held
        _press(app, pg.K_ESCAPE)
        _press(app, pg.K_END)
        _press(app, pg.K_RETURN)
        assert app.kind == 'menu' and not app.loop.held
    finally:
        app.close()


def test_a_game_over_goes_to_the_result_screen_and_replay_saves():
    app = _app()
    pg = app.pygame
    try:
        _frames(app, 0.1)
        app.game.score, app.game.coins = 25, 2
        app.game.scene.clear()                  # what the death timer ends with
        _frames(app, 0.05)
        assert app.kind == 'result'
        assert app.lines()[1] == 'Score 25   Coins 2'
        for key, ch in ((pg.K_a, 'A'), (pg.K_l, 'l')):
            _press(app, key, unicode=ch)
        _press(app, pg.K_RETURN)
        _press(app, pg.K_RETURN)
        assert app.kind == 'game' and not app.game.over
        assert app.defaults.objectForKey_('rank')[0] == {'Name': 'Al', 'Score': '25'}
    finally:
        app.close()


if __name__ == '__main__':
    _scratch_save.run(globals())
