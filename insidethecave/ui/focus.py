"""PORT ADDITION: leaving the window pauses the game, as P and Escape do.

The original has no pause at all, and its app delegate's background handlers are empty
(``applicationWillResignActive:`` to ``applicationWillTerminate:``,
0x10001921c..0x10001922c); SpriteKit itself most likely froze the scene while the app was
in the background (**inferred**).  The dev chose to pause on leaving the window (2026-10-02:
"going out of the window will pause the game as well"; aidocks/project_port_plan.md,
question 5).  Coming back does not resume anything; the game waits for the player, as
after P.

What the original's iOS did for its audio on the way back is ``AL.check_device`` here,
which the frame loop runs once a second and as soon as the window has focus again.
"""
from __future__ import annotations

import logging

log = logging.getLogger('focus')


def focus_lost(event, pygame):
    return event.type == getattr(pygame, 'WINDOWFOCUSLOST', None)


def focus_gained(event, pygame):
    return event.type == getattr(pygame, 'WINDOWFOCUSGAINED', None)


def pause_on_focus_loss(screen):
    """Pause whichever screen is up, if it can be paused.  Returns True if it was."""
    pause = getattr(screen, 'pause', None)
    if pause is None:
        return False
    log.info('window lost focus: pause, as P')
    pause()
    return True
