"""PORT ADDITION: the keyboard the touch input is mapped to, and the player's changes.

The original has no keys: four gesture recognisers on the view (``GameScene.didMoveToView:``,
GAME_STRUCTURE.md section 4) send a swipe right to ``movePlayerRight``, a swipe left to
``movePlayerLeft``, a swipe up to ``throwTorch``, and a tap to whichever side it lands on.
The port binds those to keys (the dev, 2026-10-02; aidocks/project_port_plan.md,
question 5), keeps them in ``%APPDATA%\\InsideTheCave\\keys.json``, and lets the player
rebind them from the screen F1 opens:

    move_left    A or Left Arrow      the swipe left, and a tap on the left
    move_right   D or Right Arrow     the swipe right, and a tap on the right
    throw        W or Up Arrow        the swipe up
    pause        P                    the port's own: the original has no pause

Keys are stored by pygame's name for them ("left", "a"), not by keycode, so a saved keymap
survives a pygame update.

**A binding can be a chord**, a set of keys held together, should a player want one; none
of the defaults is.  ``KeyMap.press`` returns an action at once when the held keys match a
binding nothing longer extends; otherwise it asks the caller to wait ``CHORD_WINDOW``
seconds and call ``settle``.  With the default bindings nothing waits.  Of several matches,
the one using the key just pressed wins, then the longest, so a player rolling from one key
to the next gets the new one.
"""
from __future__ import annotations

import json
import logging
import os

from .. import paths

log = logging.getLogger('keymap')

CHORD_WINDOW = 0.06        # seconds to wait before deciding a possibly-chorded key

# action, what the binding screen calls it, default bindings.
# A binding is a tuple of pygame key names; more than one name means a chord.
ACTIONS = (
    ('move_left', 'Move left', (('a',), ('left',))),
    ('move_right', 'Move right', (('d',), ('right',))),
    ('throw', 'Throw the torch', (('w',), ('up',))),
    ('pause', 'Pause', (('p',),)),
)

ACTION_IDS = [a[0] for a in ACTIONS]
LABELS = {a[0]: a[1] for a in ACTIONS}
DEFAULTS = {a[0]: [tuple(b) for b in a[2]] for a in ACTIONS}

# Not rebindable, on purpose: bind over these and there is no way back into the game or
# into the binding screen without deleting the save.
#: Escape pauses a game and goes back everywhere else; Page Up and Page Down set the music
#: volume, and Home and End the master volume during a game (volume.py).
FIXED = {'f1': 'Key bindings', 'escape': 'Pause, or back',
         'page up': 'Music louder', 'page down': 'Music quieter',
         'home': 'Master louder, in a game', 'end': 'Master quieter, in a game'}

# pygame's names are terse and some of them read badly; these are for speech.
SPOKEN = {
    'left': 'Left Arrow', 'right': 'Right Arrow', 'up': 'Up Arrow', 'down': 'Down Arrow',
    'space': 'Space', 'tab': 'Tab', 'escape': 'Escape', 'return': 'Enter',
    'left shift': 'Left Shift', 'right shift': 'Right Shift',
    'left ctrl': 'Left Control', 'right ctrl': 'Right Control',
    'left alt': 'Left Alt', 'right alt': 'Right Alt',
    ',': 'Comma', '.': 'Full stop', '/': 'Slash', ';': 'Semicolon', "'": 'Apostrophe',
    '[': 'Left bracket', ']': 'Right bracket', '\\': 'Backslash', '-': 'Minus',
    '=': 'Equals', '`': 'Backtick', 'backspace': 'Backspace', 'delete': 'Delete',
    'home': 'Home', 'end': 'End', 'page up': 'Page Up', 'page down': 'Page Down',
    'insert': 'Insert', 'caps lock': 'Caps Lock', 'enter': 'Enter',
}


def key_text(name):
    """A key name as it should be spoken."""
    if name in SPOKEN:
        return SPOKEN[name]
    if len(name) == 1:
        return name.upper()
    return name.title()


def binding_text(binding):
    """A chord as it should be spoken: 'Left Arrow plus Up Arrow'."""
    return ' plus '.join(key_text(k) for k in binding)


def bindings_text(bindings):
    if not bindings:
        return 'nothing'
    return ', or '.join(binding_text(b) for b in bindings)


def or_list(items):
    """Words joined for a hint: 'A', 'A or Left Arrow', 'A, Q, or Left Arrow'."""
    items = list(items)
    if len(items) > 2:
        items = [', '.join(items[:-1]) + ',', items[-1]]
    return ' or '.join(items)


class KeyMap:
    _shared = None

    @classmethod
    def shared(cls):
        if cls._shared is None:
            cls._shared = KeyMap()
        return cls._shared

    def __init__(self, path=None):
        self.path = path or os.path.join(paths.user_dir(), 'keys.json')
        self.bindings = {a: [tuple(b) for b in DEFAULTS[a]] for a in ACTION_IDS}
        self.load()
        self._held = set()
        self._newest = None        # the key pressed last, which decides a rollover

    @property
    def actions(self):
        return ACTION_IDS

    # ---- storage ---------------------------------------------------------
    def load(self):
        """Read the bindings, and write the file when it is missing or lacks an action, so
        ``keys.json`` is there from the first start.  A file that cannot be read is left
        alone, so a player's bindings are never overwritten by the defaults."""
        saved = {}
        try:
            if os.path.exists(self.path):
                with open(self.path, 'r', encoding='utf-8') as f:
                    saved = json.load(f)
                for action in ACTION_IDS:
                    if action in saved:
                        self.bindings[action] = [tuple(b) for b in saved[action] if b]
        except Exception:
            log.exception('could not read %s; using the defaults', self.path)
            return
        if not all(action in saved for action in ACTION_IDS):
            self.save()

    def save(self):
        try:
            tmp = self.path + '.tmp'
            with open(tmp, 'w', encoding='utf-8') as f:
                json.dump({a: [list(b) for b in self.bindings[a]] for a in ACTION_IDS},
                          f, indent=1, sort_keys=True)
            os.replace(tmp, self.path)
        except Exception:
            log.exception('could not write %s', self.path)

    def reset(self):
        self.bindings = {a: [tuple(b) for b in DEFAULTS[a]] for a in ACTION_IDS}
        self.save()

    # ---- editing ---------------------------------------------------------
    def label(self, action):
        return LABELS[action]

    def keys_text(self, action):
        return bindings_text(self.bindings.get(action, []))

    def hint_keys(self, action):
        """The keys for an action as a hint says them, 'A or Left Arrow', or None when it
        has none.  For the key hints after the tutorial line."""
        keys = []
        for b in self.bindings.get(action, []):
            text = binding_text(b)
            if text not in keys:
                keys.append(text)
        return or_list(keys) if keys else None

    def conflicts(self, binding, ignore=None):
        """Actions already using exactly this chord."""
        b = tuple(sorted(binding))
        return [a for a in self.actions if a != ignore
                and any(tuple(sorted(x)) == b for x in self.bindings[a])]

    def set_binding(self, action, binding, replace=True):
        """Give ``action`` this chord, taking it off whatever else had it."""
        b = tuple(binding)
        key = tuple(sorted(b))
        for other in ACTION_IDS:
            self.bindings[other] = [x for x in self.bindings[other]
                                    if tuple(sorted(x)) != key]
        self.bindings[action] = [b] if replace else self.bindings[action] + [b]
        self.save()

    def clear(self, action):
        self.bindings[action] = []
        self.save()

    # ---- resolving -------------------------------------------------------
    def _matches(self, held):
        """(action, binding) for every binding satisfied by ``held``."""
        out = []
        for action in self.actions:
            for b in self.bindings[action]:
                if set(b) <= held:
                    out.append((action, b))
        return out

    def _extendable(self, held):
        """True when some binding is a strict superset of ``held`` - so holding one
        more key could still mean something else."""
        for action in self.actions:
            for b in self.bindings[action]:
                if held < set(b):
                    return True
        return False

    def _best(self, matches, newest):
        """Which match to take: one that uses the key just pressed, and the longest of
        those, so a chord still beats one of its own keys."""
        fresh = [m for m in matches if newest in m[1]] or matches
        return max(fresh, key=lambda m: len(m[1]))

    def press(self, name):
        """A key went down.

        Returns ``(action, pending)``. ``action`` is what to do now, or None.
        ``pending`` is True when the caller should wait ``CHORD_WINDOW`` and then call
        ``settle`` - the key might be the start of a chord.
        """
        self._held.add(name)
        self._newest = name
        held = set(self._held)
        matches = self._matches(held)
        if not matches:
            return None, self._extendable(held)
        action, _binding = self._best(matches, name)
        if self._extendable(held):
            return None, True
        return action, False

    def settle(self):
        """The chord window closed; decide on whatever is still held."""
        held = set(self._held)
        matches = self._matches(held)
        if not matches:
            return None
        action, _b = self._best(matches, self._newest)
        return action

    def release(self, name):
        self._held.discard(name)

    def clear_held(self):
        self._held.clear()
        self._newest = None

    @property
    def held(self):
        return set(self._held)
