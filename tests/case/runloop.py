"""The run loop: ``platform/runloop.py``, the original's NSTimers.

Each test drives a loop of its own with ``pump(now=...)``, so nothing waits on the real
clock and nothing of the game is loaded.
"""
from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
import _scratch_save                                             # noqa: E402  never the real save

from insidethecave.platform import runloop                       # noqa: E402
from insidethecave.platform.runloop import RunLoop               # noqa: E402


class _Target:
    def __init__(self):
        self.calls = []

    def bare(self):
        self.calls.append('bare')

    def takes(self, arg):
        self.calls.append(('takes', arg))

    def breaks(self, *_):
        self.calls.append('breaks')
        raise TypeError('a mistake inside the callback')


def test_a_one_shot_timer_fires_once_when_due_and_not_before():
    """startGame 4.0 s after the tutorial line (0x10000e648): not at 3.9, once at 4.0."""
    loop, t = RunLoop(), _Target()
    timer = loop.scheduledTimer(4.0, t, 'bare')
    start = timer.fireDate - 4.0
    loop.pump(now=start + 3.9)
    assert t.calls == []
    loop.pump(now=start + 4.0)
    loop.pump(now=start + 9.0)
    assert t.calls == ['bare'], t.calls
    assert not timer.isValid() and not loop._timers


def test_a_callback_that_raises_type_error_runs_once():
    loop, t = RunLoop(), _Target()
    loop.scheduledTimer(0.0, t, 'breaks')
    loop.pump(now=runloop.clock() + 1.0)
    assert t.calls == ['breaks'], t.calls


def test_a_timer_is_handed_to_a_callback_that_takes_it():
    loop, t = RunLoop(), _Target()
    timer = loop.scheduledTimer(0.0, t, 'takes')
    loop.scheduledTimer(0.0, t, 'bare')
    loop.pump(now=runloop.clock() + 1.0)
    assert t.calls == [('takes', timer), 'bare'], t.calls


def test_timers_run_in_fire_time_order():
    loop, order = RunLoop(), []

    class T:
        def late(self):
            order.append('3.0 s')

        def early(self):
            order.append('1.0 s')

    t = T()
    loop.scheduledTimer(3.0, t, 'late')
    loop.scheduledTimer(1.0, t, 'early')
    loop.pump(now=runloop.clock() + 5.0)
    assert order == ['1.0 s', '3.0 s'], order


def test_an_invalidated_timer_never_fires():
    loop, t = RunLoop(), _Target()
    loop.scheduledTimer(0.0, t, 'bare').invalidate()
    loop.pump(now=runloop.clock() + 1.0)
    assert t.calls == []


def test_a_repeating_timer_fires_once_a_pump_and_skips_what_it_missed():
    loop, t = RunLoop(), _Target()
    timer = loop.scheduledTimer(0.1, t, 'bare', repeats=True)
    now = runloop.clock() + 5.0                       # fifty intervals late
    loop.pump(now=now)
    assert t.calls == ['bare']
    assert abs(timer.fireDate - (now + 0.1)) < 1e-9
    assert timer.isValid() and timer in loop._timers


def test_the_clock_is_fine_grained():
    """time.monotonic moves in 15.6 ms steps on Windows; delays of a few ms were rounded."""
    assert runloop.clock is __import__('time').perf_counter
    a = runloop.clock()
    b = runloop.clock()
    while b == a:
        b = runloop.clock()
    assert b - a < 0.001, 'the clock steps by %.4f s' % (b - a)


def test_holding_stops_the_clock_and_resuming_moves_everything_on():
    """The pause: a timer held for a while still has its whole delay to go after."""
    loop, t = RunLoop(), _Target()
    timer = loop.scheduledTimer(1.0, t, 'bare')
    due = timer.fireDate
    loop.hold()
    assert loop.held
    loop.pump(now=runloop.clock() + 10.0)
    assert t.calls == [], 'a timer fired while the loop was held'
    loop.resume()
    assert not loop.held and timer.fireDate > due
    loop.pump(now=timer.fireDate)
    assert t.calls == ['bare']


def test_reset_drops_every_timer():
    loop, t = RunLoop(), _Target()
    loop.scheduledTimer(0.0, t, 'bare')
    loop.hold()
    loop.reset()
    assert not loop.held
    loop.pump(now=runloop.clock() + 1.0)
    assert t.calls == []


if __name__ == '__main__':
    _scratch_save.run(globals())
