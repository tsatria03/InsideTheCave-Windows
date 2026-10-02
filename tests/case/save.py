"""The save: ``platform/defaults.py`` and the volume settings in ``platform/volume.py``.

Everything here is written to the throwaway folder ``_scratch_save`` sets, never to
``%APPDATA%\\InsideTheCave``.
"""
from __future__ import annotations

import json
import os
import shutil
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
import _scratch_save                                             # noqa: E402  never the real save

from insidethecave import paths                                  # noqa: E402
from insidethecave.platform import defaults, volume              # noqa: E402
from insidethecave.platform.defaults import UserDefaults         # noqa: E402


def _fresh():
    """An empty save folder, and defaults read from it."""
    folder = paths.user_dir()
    for name in os.listdir(folder):
        p = os.path.join(folder, name)
        if os.path.isdir(p):
            shutil.rmtree(p)
        else:
            os.remove(p)
    return UserDefaults()


def _file(name):
    with open(os.path.join(paths.user_dir(), name), encoding='utf-8') as f:
        return json.load(f)


def test_the_save_is_in_the_scratch_folder():
    d = _fresh()
    assert os.path.dirname(d.path) == _scratch_save.FOLDER


def test_a_missing_key_is_none_and_zero():
    """UserDefaults gives nil for a missing key, and integerForKey: 0 (countTutorial on the
    first game, 0x10000e000)."""
    d = _fresh()
    assert d.objectForKey_(defaults.COUNT_TUTORIAL_KEY) is None
    assert d.integerForKey_(defaults.COUNT_TUTORIAL_KEY) == 0


def test_progress_and_settings_go_in_their_own_files():
    d = _fresh()
    rank = [{'Name': 'Player', 'Score': '0'}] * 5
    d.setObject_forKey_(rank, defaults.RANK_KEY)
    d.setInteger_forKey_(1, defaults.COUNT_TUTORIAL_KEY)
    d.setInteger_forKey_(70, volume.MASTER_KEY)
    d.synchronize()
    save, settings = _file('save.json'), _file('settings.json')
    assert save == {'countTutorial': 1, 'rank': rank}, save
    assert settings == {'MASTERVOLUME': 70}, settings


def test_what_is_saved_is_read_back():
    d = _fresh()
    d.setObject_forKey_([{'Name': 'tsatria03', 'Score': '120'}], defaults.RANK_KEY)
    d.synchronize()
    again = UserDefaults()
    assert again.objectForKey_(defaults.RANK_KEY) == [{'Name': 'tsatria03', 'Score': '120'}]


def test_a_damaged_save_is_kept_aside_and_the_backup_used():
    d = _fresh()
    d.setInteger_forKey_(1, defaults.COUNT_TUTORIAL_KEY)
    d.synchronize()
    d.setInteger_forKey_(2, defaults.COUNT_TUTORIAL_KEY)
    d.synchronize()                                   # save.json.bak now holds 1
    with open(d.path, 'w', encoding='utf-8') as f:
        f.write('{not json')
    again = UserDefaults()
    assert again.integerForKey_(defaults.COUNT_TUTORIAL_KEY) == 1
    assert os.path.exists(d.path + '.damaged')
    assert _file('save.json') == {'countTutorial': 1}, 'the backup was not written back'


def test_settings_are_written_in_their_order():
    d = _fresh()
    d.setInteger_forKey_(50, volume.MUSIC_KEY)
    d.setInteger_forKey_(80, volume.MASTER_KEY)
    d.synchronize()
    with open(os.path.join(paths.user_dir(), 'settings.json'), encoding='utf-8') as f:
        text = f.read()
    assert text.index('MASTERVOLUME') < text.index('MUSICVOLUME')


def test_loading_the_volumes_writes_the_missing_ones_at_100():
    d = _fresh()
    assert volume.load(d) is True
    assert d.objectForKey_(volume.MASTER_KEY) == 100
    assert d.objectForKey_(volume.MUSIC_KEY) == 100
    assert volume.load(d) is False


def test_a_bad_volume_counts_as_100():
    d = _fresh()
    d.setObject_forKey_('loud', volume.MASTER_KEY)
    d.setObject_forKey_('30', volume.MUSIC_KEY)
    volume.load(d)
    assert volume.percents[volume.MASTER_KEY] == 100
    assert volume.percents[volume.MUSIC_KEY] == 30


def test_the_percentage_is_squared_into_the_gain():
    assert volume.percent_gain(100) == 1.0
    assert volume.percent_gain(50) == 0.25
    assert volume.percent_gain(0) == 0.0


def test_page_up_and_down_step_by_ten_and_hold_at_the_ends():
    assert volume.step_percent(100, +1) == 100
    assert volume.step_percent(100, -1) == 90
    assert volume.step_percent(0, -1) == 0
    assert volume.step_percent(55, +1) == 60
    assert volume.step_percent(55, -1) == 50


def test_changing_the_master_volume_saves_it():
    d = _fresh()
    volume.load(d)
    assert volume.change_master(d, -1) == 90
    assert _file('settings.json')['MASTERVOLUME'] == 90
    assert volume.master_gain() == 0.81
    volume.change_master(d, +1)


def test_the_music_keeps_the_originals_gain_at_100():
    """changeVolumeTo:0.2 at 0x100010a6c."""
    d = _fresh()
    volume.load(d)
    assert volume.music(0.2) == 0.2


if __name__ == '__main__':
    _scratch_save.run(globals())
