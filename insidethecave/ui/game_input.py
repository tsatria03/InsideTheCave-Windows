"""PORT ADDITION: the keys during a game, in place of the original's swipes and tap.

``GameScene.didMoveToView:`` adds four gesture recognisers (GAME_STRUCTURE.md section 4):
swipe right ``movePlayerRight``, swipe left ``movePlayerLeft``, swipe up ``throwTorch``,
and a tap, left or right by where it lands.  Here the player's bindings
(``platform/keymap.py``) call the same methods; a tap's two halves are the two move keys.

The rest is the port's own: T says how much torch is left (``GameScene.sayTorch``), and P
(and Escape, fixed) pause and open the pause menu
(``ui/pause_menu.py``), where the same keys resume.  The menu's Restart and Quit to menu are
left in ``request`` for the screen loop.
"""
from __future__ import annotations

import logging

from ..platform import runloop
from ..platform.keymap import CHORD_WINDOW
from .pause_menu import PauseMenu
from .rows import CHOOSE

log = logging.getLogger('input')

CONTINUE = 'Continue.'
#: The keys the pause menu reads before the bindings do (Up is also a throw key).
MENU_KEYS = ('up', 'down', 'home', 'end') + CHOOSE


class GameInput:
    """The game's keys.  ``press`` and ``release`` take pygame's key names; ``tick`` must
    run every frame, to settle a key that might begin a chord."""

    def __init__(self, keymap, speech=None):
        self.keymap = keymap
        self.speech = speech
        self.scene = None
        self.menu = PauseMenu(speech)
        #: What the pause menu asked the screen loop for: 'restart' or 'menu'.
        self.request = None
        self._settle_at = None

    def attach(self, scene):
        self.scene = scene
        self.request = None
        self.keymap.clear_held()
        self._settle_at = None

    def say(self, text):
        if self.speech is not None:
            self.speech.speak(text)

    @property
    def paused(self):
        return self.scene is not None and self.scene.paused_by_player

    def pause(self, speak=True):
        if self.scene is None or self.scene.paused_by_player:
            return
        self.scene.pause()
        self.keymap.clear_held()
        self._settle_at = None
        self.menu.open(speak)

    def resume(self, speak=True):
        if self.scene is None or not self.scene.paused_by_player:
            return
        self.scene.resume()
        self.keymap.clear_held()
        if speak:
            self.say(CONTINUE)

    def toggle_pause(self):
        if self.paused:
            self.resume()
        else:
            self.pause()

    def act(self, action):
        s = self.scene
        if s is None or action is None:
            return
        if action == 'pause':
            self.toggle_pause()
            return
        if self.paused:
            return
        if action == 'move_left':
            s.movePlayerLeft()
        elif action == 'move_right':
            s.movePlayerRight()
        elif action == 'throw':
            s.throwTorch()
        elif action == 'torch':
            s.sayTorch()                        # PORT ADDITION: T, the torch's state

    # ---- the pause menu ---------------------------------------------------------------
    def menu_key(self, name):
        self.menu.key(name)
        chosen, self.menu.next = self.menu.next, None
        if chosen == 'resume':
            self.resume()
        elif chosen in ('restart', 'menu'):
            self.request = chosen

    def press(self, name):
        """A key went down.  True when it meant something here."""
        if name == 'escape':
            self.toggle_pause()
            return True
        if self.paused and name in MENU_KEYS:
            self.menu_key(name)
            return True
        action, pending = self.keymap.press(name)
        if pending:
            self._settle_at = runloop.clock() + CHORD_WINDOW
            return True
        self._settle_at = None
        if self.paused and action != 'pause':
            self.menu.say_row()                 # any other key says the row again
            return True
        self.act(action)
        return action is not None

    def release(self, name):
        self.keymap.release(name)

    def tick(self):
        if self._settle_at is not None and runloop.clock() >= self._settle_at:
            self._settle_at = None
            self.act(self.keymap.settle())
