"""PORT ADDITION: the player's volume settings (aidocks/project_port_plan.md, question 12).

Every gain in the game comes out of the binary and is written where it is used, with the
address it was read from: the roar at 3.0 or 1.0 (0x10000f738), a coin at 0.2, the music at
0.2 (``changeVolumeTo:0.2 duration:0`` at 0x100010a6c).  Those numbers stay exactly as they
are, so the mix is still the original's.  On top of them sit two settings, percentages kept
in settings.json:

    MASTERVOLUME    everything the game plays; Home and End set it during a game, in steps
                    of ten
    MUSICVOLUME     the game's music, the track, on top of its 0.2; Page Up and Page Down
                    set it in a game, saying "Track volume"
    MENUVOLUME      the menu music (a port addition), on top of its own gain; Page Up and
                    Page Down set it on the menus, saying "Menu volume"

(the dev, 2026-10-02, for the second release).

Each is a whole number from 0 to 100; 100, the default, is the original's mix, and anything
else counts as 100.  The percentage is squared into the gain (``percent_gain``), so each
step sounds about as big as the last.  ``load`` reads them when the game starts and writes
any that are missing, so settings.json shows every one.
"""
from __future__ import annotations

import math

MASTER_KEY = 'MASTERVOLUME'
MUSIC_KEY = 'MUSICVOLUME'
MENU_KEY = 'MENUVOLUME'
#: The settings.json keys, in the order that file lists them (defaults.SETTINGS_KEYS).
VOLUME_KEYS = (MASTER_KEY, MUSIC_KEY, MENU_KEY)

DEFAULT_PERCENT = 100
#: How far one press of a volume key moves its volume.
STEP = 10

#: What ``load`` last read, by key; every one is 100 until then.
percents = {key: DEFAULT_PERCENT for key in VOLUME_KEYS}


def gain(db: float) -> float:
    """Decibels as the amplitude multiplier OpenAL's ``AL_GAIN`` wants: 0 dB is 1.0,
    -6 dB is about a half, -20 dB is a tenth."""
    return 10.0 ** (db / 20.0)


def decibels(g: float) -> float:
    """The other way round.  Silence has no decibel value, so it comes back as negative
    infinity."""
    return 20.0 * math.log10(g) if g > 0 else float('-inf')


def valid_percent(value):
    """``value`` as a whole percentage from 0 to 100, or None when it is not one: a word, a
    fraction, anything out of range.  A hand-edited file may hold "30"."""
    if isinstance(value, bool):
        return None
    if isinstance(value, float):
        value = int(value) if value.is_integer() else None
    elif isinstance(value, str):
        text = value.strip()
        value = int(text) if text.isdigit() else None
    if not isinstance(value, int) or not 0 <= value <= 100:
        return None
    return value


def percent(value):
    """``valid_percent``, with anything invalid counting as 100."""
    p = valid_percent(value)
    return DEFAULT_PERCENT if p is None else p


def percent_gain(p) -> float:
    """A percentage as a gain: squared, so 100 is 1.0, 50 a quarter (about -12 dB), 0
    silent, and each step sounds about as big as the last."""
    return (max(0, min(p, 100)) / 100.0) ** 2


def step_percent(now, step):
    """Page Up (+1) or Page Down (-1) from ``now``: the next step of ten, holding at 0 and
    100.  From a value set by hand between two steps it goes to the nearer step that way:
    55 goes up to 60 and down to 50."""
    if step > 0:
        return min(100, (now // STEP + 1) * STEP)
    return max(0, (-(-now // STEP) - 1) * STEP)


def load(defaults):
    """Read the settings when the game starts, and write any that are missing at their
    default, so settings.json lists both.  True when anything was written."""
    wrote = False
    for key in VOLUME_KEYS:
        value = defaults.objectForKey_(key)
        if value is None:
            defaults.setInteger_forKey_(DEFAULT_PERCENT, key)
            wrote = True
        percents[key] = percent(value)
    return wrote


def change(defaults, key, step):
    """Up (+1) or down (-1): the next step of the volume ``key``, saved at once.  Returns
    the new percentage."""
    now = step_percent(percents[key], step)
    percents[key] = now
    defaults.setInteger_forKey_(now, key)
    defaults.synchronize()
    return now


def change_master(defaults, step):
    """Home (+1) or End (-1) during a game: the master volume."""
    return change(defaults, MASTER_KEY, step)


def change_music(defaults, step):
    """Page Up (+1) or Page Down (-1) in a game: the track's volume."""
    return change(defaults, MUSIC_KEY, step)


def change_menu(defaults, step):
    """Page Up (+1) or Page Down (-1) on the menus: the menu music's volume."""
    return change(defaults, MENU_KEY, step)


def menu(g: float) -> float:
    """The menu music's gain, with ``MENUVOLUME``."""
    return g * percent_gain(percents[MENU_KEY])

def master_gain() -> float:
    """What every sound's gain is multiplied by: OpenAL's listener gain."""
    return percent_gain(percents[MASTER_KEY])


def music(g: float) -> float:
    """The music's gain from the binary, with ``MUSICVOLUME``."""
    return g * percent_gain(percents[MUSIC_KEY])
