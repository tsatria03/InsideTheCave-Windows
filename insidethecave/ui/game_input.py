"""PORT ADDITION: the keys during a game, in place of the original's swipes and tap.

``GameScene.didMoveToView:`` adds four gesture recognisers (GAME_STRUCTURE.md section 4):
swipe right ``movePlayerRight``, swipe left ``movePlayerLeft``, swipe up ``throwTorch``,
and a tap, left or right by where it lands.  Here the player's bindings
(``platform/keymap.py``) call the same methods; a tap's two halves are the two move keys.

The rest is the port's own: P (and Escape, fixed) pause and continue; Enter continues too.
"""
from __future__ import annotations

import logging

from ..platform import runloop
from ..platform.keymap import CHORD_WINDOW

log = logging.getLogger('input')

PAUSED = 'Paused. Press P, Escape or Enter to continue.'
CONTINUE = 'Continue.'


class GameInput:
    """The game's keys.  ``press`` and ``release`` take pygame's key names; ``tick`` must
    run every frame, to settle a key that might begin a chord."""

    def __init__(self, keymap, speech=None):
        self.keymap = keymap
        self.speech = speech
        self.scene = None
        self._settle_at = None

    def attach(self, scene):
        self.scene = scene
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
        if speak:
            self.say(PAUSED)

    def resume(self, speak=True):
        if self.scene is None or not self.scene.paused_by_player:
            return
        self.scene.resume()
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

    def press(self, name):
        """A key went down.  True when it meant something here."""
        if name == 'escape':
            self.toggle_pause()
            return True
        if self.paused and name in ('return', 'enter'):
            self.resume()
            return True
        action, pending = self.keymap.press(name)
        if pending:
            self._settle_at = runloop.clock() + CHORD_WINDOW
            return True
        self._settle_at = None
        self.act(action)
        return action is not None

    def release(self, name):
        self.keymap.release(name)

    def tick(self):
        if self._settle_at is not None and runloop.clock() >= self._settle_at:
            self._settle_at = None
            self.act(self.keymap.settle())
