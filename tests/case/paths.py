"""Where the game finds its files: ``paths.sound`` and ``paths.user_dir``.

The binary asks for its sounds by full name with the extension each had in 2016
(``"Rugido.mp3"``, ``"dash.aiff"``); the port's are WAV in ``game/sounds/used`` and
``game/sounds/unused``, found by base name, ``used`` first (aidocks/DIVERGENCES.md).  Most
tests build a small game folder of their own in a temporary folder, so they check the lookup
itself; the last ones check the repository's own sounds.
"""
from __future__ import annotations

import os
import shutil
import sys
import tempfile

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
import _scratch_save                                             # noqa: E402  never the real save

from insidethecave import paths                                  # noqa: E402

#: Every name the 2.32 binary loads a sound by (GAME_STRUCTURE.md section 13).
BINARY_NAMES = ('Rugido.mp3', 'BatSound.wav', 'tilintar.aiff', 'plim_moeda.wav',
                'pegou_tocha.wav', 'lancar_tocha.wav', 'tocha.wav', 'SC.wav', 'dash.aiff',
                'MonsterDead.mp3', 'MovimentoProibido.wav', 'screamingMan.wav')


def _game(files):
    """A throwaway game folder holding ``files`` (paths inside it, with '/' between
    folders), and the lookup pointed at it."""
    top = tempfile.mkdtemp()
    os.makedirs(os.path.join(top, 'sounds'))
    for rel in files:
        p = os.path.join(top, *rel.split('/'))
        os.makedirs(os.path.dirname(p), exist_ok=True)
        with open(p, 'w', encoding='utf-8') as f:
            f.write(rel)
    paths.set_game(top)
    return top


def _done(top):
    paths.set_game(None)
    shutil.rmtree(top, ignore_errors=True)


def _found(top, name):
    p = paths.sound(name)
    return None if p is None else os.path.relpath(p, top).replace(os.sep, '/')


def test_a_sound_is_found_by_its_base_name_whatever_extension_is_asked_for():
    top = _game(['sounds/used/dash.wav', 'sounds/used/Rugido.wav'])
    try:
        assert _found(top, 'dash.aiff') == 'sounds/used/dash.wav'
        assert _found(top, 'Rugido.mp3') == 'sounds/used/Rugido.wav'
        assert _found(top, 'dash') == 'sounds/used/dash.wav'
    finally:
        _done(top)


def test_case_does_not_matter():
    top = _game(['sounds/used/MovimentoProibido.wav'])
    try:
        assert _found(top, 'movimentoproibido.WAV') == 'sounds/used/MovimentoProibido.wav'
    finally:
        _done(top)


def test_the_used_folder_wins_over_the_unused_one():
    top = _game(['sounds/unused/coin.wav', 'sounds/used/coin.wav'])
    try:
        assert _found(top, 'coin.mp3') == 'sounds/used/coin.wav'
    finally:
        _done(top)


def test_a_name_only_in_unused_is_still_found():
    top = _game(['sounds/unused/spider.wav'])
    try:
        assert _found(top, 'spider.mp3') == 'sounds/unused/spider.wav'
    finally:
        _done(top)


def test_a_missing_sound_is_none():
    top = _game(['sounds/used/dash.wav'])
    try:
        assert _found(top, 'Rugido.mp3') is None
    finally:
        _done(top)


def test_pointing_somewhere_else_forgets_the_old_sounds():
    first = _game(['sounds/used/dash.wav'])
    try:
        assert _found(first, 'dash.aiff') is not None
        second = _game([])
        try:
            assert _found(second, 'dash.aiff') is None, \
                'a sound from the previous folder was still found'
        finally:
            _done(second)
    finally:
        _done(first)


def test_a_folder_without_sounds_is_not_the_game():
    top = tempfile.mkdtemp()
    try:
        paths.set_game(top)
        old = os.environ.pop(paths.GAME_ENV, None)
        try:
            # it falls through to the repository's game folder, which has sounds
            assert os.path.normcase(paths.game()) != os.path.normcase(top)
        finally:
            if old is not None:
                os.environ[paths.GAME_ENV] = old
    finally:
        paths.set_game(None)
        shutil.rmtree(top, ignore_errors=True)


def test_the_environment_variable_points_at_another_game_folder():
    top = _game([])
    paths.set_game(None)
    old = os.environ.get(paths.GAME_ENV)
    try:
        os.environ[paths.GAME_ENV] = top
        paths.set_game(None)
        assert paths.game() == top
    finally:
        if old is None:
            os.environ.pop(paths.GAME_ENV, None)
        else:
            os.environ[paths.GAME_ENV] = old
        _done(top)


def test_every_sound_the_binary_names_is_in_the_used_folder():
    paths.set_game(None)
    missing = []
    for name in BINARY_NAMES:
        p = paths.sound(name)
        if p is None or os.path.basename(os.path.dirname(p)) != 'used':
            missing.append(name)
    assert not missing, 'not in game/sounds/used: %s' % ', '.join(missing)


#: The sounds the port plays that the 2.32 binary never names: the menu music (the dev).
PORT_NAMES = ('background-music.wav',)


def test_the_used_folder_holds_only_what_the_game_plays():
    """What the binary names, under the dev's new names, and the port's own."""
    paths.set_game(None)
    used = os.path.join(paths.game(), 'sounds', 'used')
    names = {paths.base_name(n) for n in os.listdir(used)}
    wanted = {paths.RENAMED.get(paths.base_name(n), paths.base_name(n))
              for n in BINARY_NAMES + PORT_NAMES}
    assert names == wanted, sorted(names ^ wanted)


def test_a_renamed_sound_is_found_by_the_binary_s_name():
    paths.set_game(None)
    assert paths.sound('SC.wav').endswith('game-music.wav')
    assert paths.sound('dash.aiff').endswith('lane.wav')


def test_the_save_goes_where_insidethecave_user_dir_points():
    """The tests' way off the real save; without it, the save is in %APPDATA%\\InsideTheCave."""
    old_dir, old_appdata = os.environ.get(paths.USER_DIR_ENV), os.environ.get('APPDATA')
    top = tempfile.mkdtemp()
    try:
        mine = os.path.join(top, 'mine')
        os.environ[paths.USER_DIR_ENV] = mine
        assert paths.user_dir() == mine and os.path.isdir(mine)
        os.environ.pop(paths.USER_DIR_ENV)
        os.environ['APPDATA'] = top
        assert paths.user_dir() == os.path.join(top, 'InsideTheCave')
    finally:
        for key, old in ((paths.USER_DIR_ENV, old_dir), ('APPDATA', old_appdata)):
            if old is None:
                os.environ.pop(key, None)
            else:
                os.environ[key] = old
        shutil.rmtree(top, ignore_errors=True)


def test_the_libraries_ship_in_vendor():
    assert os.path.isfile(paths.OPENAL_DLL), paths.OPENAL_DLL
    assert os.path.isfile(paths.NVDA_DLL), paths.NVDA_DLL


def test_every_test_file_keeps_off_the_real_save():
    """Each test file imports _scratch_save before the game, so none can write the real
    save, whichever shell runs it."""
    here = os.path.dirname(os.path.abspath(__file__))
    forgot = []
    for name in sorted(os.listdir(here)):
        if name.endswith('.py') and not name.startswith('_'):
            with open(os.path.join(here, name), encoding='utf-8') as fh:
                if '\nimport _scratch_save' not in fh.read():
                    forgot.append(name)
    assert not forgot, 'these do not import _scratch_save: %s' % ', '.join(forgot)
    assert os.environ.get(paths.USER_DIR_ENV) == _scratch_save.FOLDER
    # ...and silent: no speech, no sound, no window for a screen reader to announce
    for key, value in _scratch_save.QUIET.items():
        assert os.environ.get(key) == value, key


if __name__ == '__main__':
    _scratch_save.run(globals())
