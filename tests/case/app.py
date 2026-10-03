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
    def __init__(self, pygame, key, down=True, mod=0):
        self.type = pygame.KEYDOWN if down else pygame.KEYUP
        self.key = key
        self.mod = mod


def _app():
    assert os.environ.get('SDL_VIDEODRIVER') == 'dummy'
    app = InsideTheCave.App(_Args())
    app.defaults.setInteger_forKey_(3, 'countTutorial')
    app.start_game()
    return app


def _frames(app, seconds):
    end = runloop.clock() + seconds
    while runloop.clock() < end:
        now = runloop.clock()
        app.input.tick()
        app.loop.pump(now)
        app.game.frame(now)
        app.draw()


def _press(app, key, mod=0):
    pg = app.pygame
    app.handle(_Key(pg, key, True, mod))
    app.handle(_Key(pg, key, False, mod))


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


if __name__ == '__main__':
    _scratch_save.run(globals())
