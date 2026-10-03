"""``NSTimer`` on one cooperative run loop.

The original's own timing is almost all SpriteKit actions (the SpriteKit stand-in runs
those), and the rest is four one-shot ``NSTimer``s, every one made with
``scheduledTimerWithTimeInterval:target:selector:userInfo:repeats:``:

    0x10000e0f4   GameScene.tutorial      startGame after 2.0 s, when the line is not spoken
    0x10000e648   GameScene.tutorial      startGame after 4.0 s, when it is
    0x1000236ec   GameScene, at death     clear after 1.0 s, then the result screen
    0x10000ea04   WarningViewController   the menu after 3.0 s

Nothing in the binary uses ``DispatchQueue`` or ``performSelector:afterDelay:``
(``analysis/disasm``), so this loop has timers only.

Delays are wall-clock, like the original's, read from ``clock`` (``time.perf_counter``,
not ``time.monotonic``, whose 15.6 ms steps on Windows would round short delays).  The
loop never advances a timer faster than real time, so a slow frame makes timers late
rather than bunched, as ``NSTimer`` does.  Timers due together run in fire-time order,
the one scheduled first first.

Whether a callback is handed its timer is decided from its signature before it is called,
never by calling it again when it raises ``TypeError``: an error inside a callback is
logged once, and the callback never runs twice.
"""
from __future__ import annotations

import inspect
import itertools
import logging
import time

log = logging.getLogger('runloop')

#: The loop's clock, in seconds.  Anything comparing against a fire date uses this.
clock = time.perf_counter


def _takes(fn, *args) -> bool:
    """Whether ``fn`` can be called with ``args``, judged from its signature without
    calling it.  A callable Python cannot see into is taken to accept them."""
    try:
        inspect.signature(fn).bind(*args)
    except TypeError:
        return False
    except ValueError:
        return True
    return True


class Timer:
    """``NSTimer``."""

    __slots__ = ('interval', 'target', 'selector', 'userInfo', 'repeats',
                 'fireDate', '_valid', '_seq')

    def __init__(self, interval, target, selector, userInfo, repeats, seq, now):
        self.interval = float(interval)
        self.target = target
        self.selector = selector
        self.userInfo = userInfo
        self.repeats = bool(repeats)
        self.fireDate = now + self.interval
        self._valid = True
        self._seq = seq

    def isValid(self):
        return self._valid

    def invalidate(self):
        """``-[NSTimer invalidate]``"""
        self._valid = False

    def fire(self):
        fn = getattr(self.target, self.selector, None)
        if fn is None:
            log.error('timer selector missing: %s.%s', type(self.target).__name__, self.selector)
            self._valid = False
            return
        # NSTimer hands the timer to its selector; a callback that takes nothing gets nothing
        if _takes(fn, self):
            fn(self)
        else:
            fn()


class RunLoop:
    _instance = None

    @classmethod
    def main(cls):
        if cls._instance is None:
            cls._instance = RunLoop()
        return cls._instance

    def __init__(self, clock_fn=None):
        self._timers = []                 # list[Timer]
        self._seq = itertools.count()
        self._held_at = None              # when hold() stopped the clock
        #: What this loop's time is: the real clock, or a made-up one the tests drive.
        self.now = clock_fn or clock

    def scheduledTimer(self, interval, target, selector, userInfo=None, repeats=False):
        """``+[NSTimer scheduledTimerWithTimeInterval:target:selector:userInfo:repeats:]``"""
        t = Timer(interval, target, selector, userInfo, repeats, next(self._seq), self.now())
        self._timers.append(t)
        return t

    def pump(self, now=None):
        """Run every timer due, earliest first.  Called once per frame by the main loop."""
        if self._held_at is not None:
            return
        now = self.now() if now is None else now
        while True:
            timer = min((t for t in self._timers if t._valid and t.fireDate <= now),
                        key=lambda t: (t.fireDate, t._seq), default=None)
            if timer is None:
                break
            self._run(timer, now)
        self._timers = [t for t in self._timers if t._valid]

    def _run(self, t, now):
        try:
            t.fire()
        except Exception:
            log.exception('timer %s.%s', type(t.target).__name__, t.selector)
        if t.repeats and t._valid:
            # NSTimer schedules the next fire from the previous fire date and
            # skips missed ones rather than catching up.
            t.fireDate += t.interval
            if t.fireDate <= now:
                t.fireDate = now + t.interval
        else:
            t._valid = False

    def hold(self):
        """PORT ADDITION: stop the clock, for the pause (P, Escape, or leaving the window)
        and the F1 binding screen; the original has no pause at all.  Nothing fires until
        ``resume``, which moves every fire date on by the time that was held, so the game
        picks up where it left off."""
        if self._held_at is None:
            self._held_at = self.now()

    def resume(self):
        if self._held_at is None:
            return
        gap = self.now() - self._held_at
        self._held_at = None
        for t in self._timers:
            t.fireDate += gap

    @property
    def held(self):
        return self._held_at is not None

    def reset(self):
        self._held_at = None
        self._timers.clear()


def main_loop() -> RunLoop:
    return RunLoop.main()
