"""Filesystem locations used by the port.

``game/`` holds the contents of the original ``InsideTheCave.app`` as it shipped.  The port
reads only its sounds, which the dev moved out of the bundle's top folder into
``game/sounds/used`` (the 12 that version 2.32 plays) and ``game/sounds/unused`` (14 from
the game's older versions), all converted to 16-bit PCM WAV under their original base names
(aidocks/DIVERGENCES.md).

The binary asks for its sounds by full file name, with whatever extension each had in 2016:
``"Rugido.mp3"``, ``"dash.aiff"``, ``"BatSound.wav"`` (GAME_STRUCTURE.md section 13).  So
``sound`` finds one by its base name alone, whatever extension it is asked for:
``"dash.aiff"`` is ``used/dash.wav``.  It looks in ``used`` first, then ``unused``, so a name
in ``used`` always wins.

The game folder is the one ``--game`` (``set_game``) or ``INSIDETHECAVE_GAME`` names, else
``game`` beside the executable, else the repository's ``game``: the first that holds a
``sounds`` folder.  ``compiler.py``'s ``game_source`` looks in the same places, so a build
and the game agree on what the game's data is.

The port never writes to ``game/``.  The save lives in ``%APPDATA%\\InsideTheCave``, or
wherever ``INSIDETHECAVE_USER_DIR`` points, which the tests use.  Windows only
(aidocks/project_python_only.md).
"""
from __future__ import annotations

import os
import sys

FROZEN = getattr(sys, 'frozen', False)
if FROZEN:
    ROOT = getattr(sys, '_MEIPASS', os.path.dirname(sys.executable))
    EXE_DIR = os.path.dirname(os.path.abspath(sys.executable))
else:
    ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    EXE_DIR = ROOT

VENDOR = os.path.join(ROOT, 'vendor')
OPENAL_DLL = os.path.join(VENDOR, 'openal', 'soft_oal.dll')
NVDA_DLL = os.path.join(VENDOR, 'nvda', 'nvdaControllerClient64.dll')

# A copy of the arm64 binary, for tools/.  Not needed to play.
BINARY = os.path.join(ROOT, 'analysis', 'bin', 'InsideTheCave_arm64')

GAME_ENV = 'INSIDETHECAVE_GAME'
# The save's folder in place of %APPDATA%\InsideTheCave - set by the tests, never by the game.
USER_DIR_ENV = 'INSIDETHECAVE_USER_DIR'
SAVE_FOLDER = 'InsideTheCave'

SOUNDS = 'sounds'
# Searched in this order; the first file of a name wins.
SOUND_FOLDERS = (os.path.join(SOUNDS, 'used'), os.path.join(SOUNDS, 'unused'))

_override: str | None = None
_game: str | None = None
_sound_index: dict[str, str] | None = None


def set_game(path: str | None) -> None:
    """Point the lookup at another game folder (``--game``); None goes back to the default
    places."""
    global _override, _game, _sound_index
    _override = path
    _game = None
    _sound_index = None


def _candidates():
    if _override:
        yield 'the --game option', _override
    env = os.environ.get(GAME_ENV)
    if env:
        yield 'the %s environment variable' % GAME_ENV, env
    yield 'the port', os.path.join(EXE_DIR, 'game')
    yield 'the port', os.path.join(ROOT, 'game')


def _is_game(path: str) -> bool:
    """A folder is the game's if it holds a sounds folder, as compiler.py's _is_game."""
    return os.path.isdir(os.path.join(path, SOUNDS))


def game() -> str:
    """The folder holding the game's data."""
    global _game
    if _game is None:
        tried = []
        for why, path in _candidates():
            if path and _is_game(path):
                _game = path
                break
            tried.append('%s: %s' % (why, path))
        else:
            raise SystemExit("Inside The Cave's game data was not found. Tried:\n  "
                             + '\n  '.join(tried)
                             + '\nPass --game with the path to a folder holding sounds.')
    return _game


#: Sounds the dev renamed in ``game/sounds``: the name the binary asks for, by base name,
#: and the file's name now.  "SC.wav", the game's music, is ``used/game-music.wav``, and
#: "dash.aiff", the move, is ``used/lane.wav`` (2026-10-02).
RENAMED = {'sc': 'game-music', 'dash': 'lane'}


def base_name(name: str) -> str:
    """A file name without its folder or extension, in lower case: the key a sound is
    found by.  ``"dash.aiff"`` and ``"Dash.wav"`` are both ``"dash"``."""
    return os.path.splitext(os.path.basename(name))[0].lower()


def _sounds_by_name() -> dict[str, str]:
    """Every file under ``sounds/used``, then ``sounds/unused``, by its base name.

    Built once, the first time a sound is asked for.  Within a folder the first file in
    sorted order wins, so a name always gives the same file, and a name in ``used`` is never
    taken from ``unused``.
    """
    global _sound_index
    if _sound_index is None:
        index = {}
        for folder in SOUND_FOLDERS:
            for dirpath, dirs, files in os.walk(os.path.join(game(), folder)):
                dirs.sort()
                for name in sorted(files):
                    index.setdefault(base_name(name), os.path.join(dirpath, name))
        _sound_index = index
    return _sound_index


def sound(name: str) -> str | None:
    """The file for a sound the binary names, such as ``"Rugido.mp3"``, by its base name,
    or None when there is none.  Case does not matter, as it does not on Windows.  A name
    the dev has renamed (``RENAMED``) finds the file under its new name."""
    key = base_name(name)
    index = _sounds_by_name()
    return index.get(key) or index.get(RENAMED.get(key, key))


def user_dir() -> str:
    """Where the save lives: ``%APPDATA%\\InsideTheCave``, or the folder
    ``INSIDETHECAVE_USER_DIR`` names.  The tests set that to a throwaway folder, so they
    never read or write the real save."""
    p = os.environ.get(USER_DIR_ENV)
    if not p:
        base = os.environ.get('APPDATA') or os.path.expanduser('~')
        p = os.path.join(base, SAVE_FOLDER)
    os.makedirs(p, exist_ok=True)
    return p
