"""``UserDefaults`` - JSON files in ``%APPDATA%\\InsideTheCave``.

The keys the original saves (GAME_STRUCTURE.md section 12):

    rank            array  five entries of {"Name": str, "Score": str}, best first; set to
                           five of "Player", "0" when missing (HomeScreenViewController,
                           0x10001a00c..0x10001a334), written by ResultViewController.checkRank
    countTutorial   int    how many games have spoken the tutorial line (GameScene.tutorial,
                           0x10000e000, 0x10000e5bc..0x10000e5f0)

``rankWorld``, the world ranking's copy, is not saved: the port has no online scores
(aidocks/project_port_plan.md, question 9).

and the port's own settings, PORT ADDITIONS (``volume.py``):

    MASTERVOLUME    everything the game plays, which Home and End set during a game
    MUSICVOLUME     the game's music, on top of the original's 0.2 (Page Up and Page Down)

The original keeps everything in one plist.  The port keeps two files, routed by key name,
beside ``keys.json`` (``keymap.py``):

    save.json       progress: every key not named in SETTINGS_KEYS
    settings.json   the player's preferences, SETTINGS_KEYS, written in that order

``synchronize`` writes the files; the original's does the same thing.

PORT ADDITION: a file that cannot be read is never written over.  It is kept as
``<file>.damaged``, and the game carries on from ``<file>.bak``, the copy before the last
write, which every ``synchronize`` keeps.
"""
from __future__ import annotations

import json
import logging
import os
import shutil

from .. import paths

log = logging.getLogger('defaults')

SAVE_FILE = 'save.json'
SETTINGS_FILE = 'settings.json'

RANK_KEY = 'rank'                     # 0x100026d32
COUNT_TUTORIAL_KEY = 'countTutorial'  # 0x100025237

#: The keys that are settings rather than progress, in the order settings.json lists them.
SETTINGS_KEYS = ('MASTERVOLUME', 'MUSICVOLUME')


def _read(path):
    """The JSON object at ``path``, or None when it is missing or is not one."""
    try:
        with open(path, 'r', encoding='utf-8') as f:
            d = json.load(f)
    except FileNotFoundError:
        return None
    except Exception:
        log.exception('could not read %s', path)
        return None
    if not isinstance(d, dict):
        log.error('%s is not a save: %s', path, type(d).__name__)
        return None
    return d


class _File:
    """One JSON file of keys, with its backup, kept aside when it is damaged."""

    def __init__(self, path, order=None):
        self.path = path
        self.backup = path + '.bak'
        self.order = order          # the key order to write in; sorted by name when None
        self.d = {}
        self.recovered = False      # read from the backup, so it wants writing back
        if not os.path.exists(path):
            return                  # a new save, or one deleted to start over
        d = _read(path)
        if d is None:
            damaged = path + '.damaged'
            try:
                os.replace(path, damaged)
                log.error('%s could not be read; kept as %s', path, damaged)
            except OSError:
                log.exception('could not set the damaged %s aside', path)
            d = _read(self.backup)
            if d is not None:
                log.warning('carrying on from %s', self.backup)
                self.recovered = True
        self.d = d or {}

    def ordered(self):
        if self.order is None:
            return dict(sorted(self.d.items()))
        first = [(k, self.d[k]) for k in self.order if k in self.d]
        rest = sorted((k, v) for k, v in self.d.items() if k not in self.order)
        return dict(first + rest)

    def write(self):
        try:
            tmp = self.path + '.tmp'
            with open(tmp, 'w', encoding='utf-8') as f:
                json.dump(self.ordered(), f, indent=1)
                f.flush()
                os.fsync(f.fileno())
            if os.path.exists(self.path):
                shutil.copyfile(self.path, self.backup)
            os.replace(tmp, self.path)
        except Exception:
            log.exception('could not write %s', self.path)


class UserDefaults:
    _instance = None

    @classmethod
    def standardUserDefaults(cls):
        if cls._instance is None:
            cls._instance = UserDefaults()
        return cls._instance

    def __init__(self):
        folder = paths.user_dir()
        self.path = os.path.join(folder, SAVE_FILE)
        self.save = _File(self.path)
        self.settings = _File(os.path.join(folder, SETTINGS_FILE), order=SETTINGS_KEYS)
        if self.save.recovered or self.settings.recovered:
            self.synchronize()      # or the next launch finds no save at all

    def _file_for(self, key):
        return self.settings if key in SETTINGS_KEYS else self.save

    # UserDefaults returns nil for a missing key; integerForKey: gives 0 for it.
    def objectForKey_(self, key):
        return self._file_for(key).d.get(key)

    def integerForKey_(self, key):
        v = self.objectForKey_(key)
        if v is None:
            return 0
        try:
            return int(v)
        except (TypeError, ValueError):
            return 0

    def stringForKey_(self, key):
        v = self.objectForKey_(key)
        return None if v is None else str(v)

    def setObject_forKey_(self, value, key):
        self._file_for(key).d[key] = value

    def setInteger_forKey_(self, value, key):
        self._file_for(key).d[key] = int(value)

    def removeObjectForKey_(self, key):
        self._file_for(key).d.pop(key, None)

    def synchronize(self):
        self.save.write()
        self.settings.write()
        return True


def standard() -> UserDefaults:
    return UserDefaults.standardUserDefaults()
