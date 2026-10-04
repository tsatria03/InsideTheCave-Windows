"""PORT ADDITION: a run's numbers in words, and the lifetime stats in the save (the dev, for the
fourth release; aidocks/project_scores_stats_plan.md).  The original keeps only the best
five; none of this is in the binary.

The stats are kept for each difficulty under the save's ``stats``.  A game counts only when
it ends by being caught (the dev: "restarts and quits do not count in a game."), and
tutorial games never do.  All-time adds the three up, its longest run and fastest speed the
best of them.
"""
from __future__ import annotations

from .game_scene import DIFFICULTY_ORDER, RUN_COUNTS

STATS_KEY = 'stats'

#: The Stats screen's rows, in the dev's order: (key, words, how it is said, best or sum).
ROWS = (('games', 'Games played', 'number', 'sum'),
        ('longest', 'Longest run', 'time', 'best'),
        ('fastest', 'Fastest speed reached', 'number', 'best'),
        ('coins', 'Total coins', 'number', 'sum'),
        ('time', 'Total time played', 'long time', 'sum'),
        ('torchesPicked', 'Torches picked up', 'number', 'sum'),
        ('batsFrightened', 'Bats frightened', 'number', 'sum'),
        ('monstersKilled', 'Monsters killed', 'number', 'sum'),
        ('batsDodged', 'Bats dodged', 'number', 'sum'),
        ('monstersDodged', 'Monsters dodged', 'number', 'sum'))
KEYS = tuple(r[0] for r in ROWS)


def _unit(n, word):
    return '%d %s%s' % (n, word, '' if n == 1 else 's')


def spoken_time(seconds, hours=False):
    """Whole seconds in words (the dev: "like 3 minutes 12 seconds"): "45 seconds",
    "1 minute", "3 minutes 12 seconds"; with ``hours``, from an hour on "1 hour 14
    minutes", for the total time played."""
    s = max(0, int(seconds))
    if hours and s >= 3600:
        h, m = s // 3600, s % 3600 // 60
        return _unit(h, 'hour') + (' ' + _unit(m, 'minute') if m else '')
    m, s = s // 60, s % 60
    if not m:
        return _unit(s, 'second')
    return _unit(m, 'minute') + (' ' + _unit(s, 'second') if s else '')


def blank():
    return {k: 0 for k in KEYS}


def load(defaults):
    """Every difficulty's stats, missing ones as zeros."""
    saved = defaults.objectForKey_(STATS_KEY) if defaults is not None else None
    saved = saved if isinstance(saved, dict) else {}
    out = {}
    for d in DIFFICULTY_ORDER:
        mine = saved.get(d) if isinstance(saved.get(d), dict) else {}
        out[d] = {k: int(mine.get(k, 0) or 0) for k in KEYS}
    return out


def record(defaults, difficulty, run):
    """Add a game that ended by being caught.  ``run``: GameViewController.last_run."""
    if defaults is None or difficulty not in DIFFICULTY_ORDER:
        return
    every = load(defaults)
    mine = every[difficulty]
    mine['games'] += 1
    mine['longest'] = max(mine['longest'], int(run['seconds']))
    mine['fastest'] = max(mine['fastest'], int(run['speed']))
    mine['coins'] += int(run['coins'])
    mine['time'] += int(run['seconds'])
    for k in RUN_COUNTS:
        mine[k] += int(run.get(k, 0))
    defaults.setObject_forKey_(every, STATS_KEY)
    defaults.synchronize()


def totals(defaults, which):
    """One difficulty's stats, or 'all' of them added up."""
    every = load(defaults)
    if which != 'all':
        return every[which]
    out = blank()
    for mine in every.values():
        for key, _words, _say, how in ROWS:
            out[key] = max(out[key], mine[key]) if how == 'best' else out[key] + mine[key]
    return out


def lines(numbers):
    """The Stats screen's rows, in words."""
    out = []
    for key, words, say, _how in ROWS:
        n = numbers[key]
        if say == 'time':
            value = spoken_time(n)
        elif say == 'long time':
            value = spoken_time(n, hours=True)
        else:
            value = '%d' % n
        out.append('%s, %s.' % (words, value))
    return out
