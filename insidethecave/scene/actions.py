"""``SKAction``: what the game makes things do over time.

Only the actions the binary uses (its selectors, analysis/disasm): ``moveToX:duration:``,
``moveToY:duration:``, ``waitForDuration:``, ``sequence:``, ``runBlock:``,
``repeatActionForever:``, ``removeFromParent``, ``animateWithTextures:timePerFrame:``,
``changeVolumeTo:duration:``, ``changeVolumeBy:duration:``, ``play`` and
``playSoundFileNamed:waitForCompletion:``.  Movement and volume change linearly, SpriteKit's
default timing; the game never sets another.

Time is the real clock, as SpriteKit's.  **One deliberate refinement:** when an action ends
partway through a frame, the next one in its sequence starts at the moment it ended, not at
the next frame, and so do actions a block starts.  SpriteKit rounds to its frames, 60 a
second on the iPhone; the port's frames are whatever Windows gives, so rounding to them
would make the slot chain (0.165 x speedMonster a slot, ``moveObstacleWithBorn``
0x100013ae8) drift with the frame rate.  Keeping the leftover keeps every chain on the
binary's own durations whatever the frame rate.
"""
from __future__ import annotations

import logging

log = logging.getLogger('actions')

#: How many times a repeat may come round within one frame before it is cut off: a
#: zero-length action repeated forever would otherwise never let the frame end.
MAX_LOOPS = 1000


class Action:
    duration = 0.0

    def state(self, node):
        raise NotImplementedError


# ---- the running of an action on a node --------------------------------------------------
class Running:
    """One action running on one node, from the moment it was started."""

    def __init__(self, action, node):
        self.action = action
        self.node = node
        self.st = action.state(node)
        scene = node.scene
        self.last = scene.action_now if scene is not None else None

    def hold(self, now):
        """Paused: time passes without the action."""
        self.last = now

    def step_to(self, now):
        """Run up to ``now``; True once the action is over."""
        if self.last is None:
            self.last = now
        dt = max(0.0, now - self.last)
        self.last = now
        return self.st.step(dt, now) is not None


class _State:
    """An action under way.  ``step(dt, end)`` moves it on by ``dt`` seconds, the frame
    ending at ``end``; it returns None while the action goes on, or the time left over
    once it ends."""

    def step(self, dt, end):
        raise NotImplementedError


def _scene_clock(node, at):
    """While an instant action runs, actions it starts begin at ``at``."""
    scene = node.scene
    if scene is not None:
        scene.action_now = at
    return scene


# ---- instant actions -------------------------------------------------------------------
class _Instant(Action):
    def run(self, node):
        raise NotImplementedError

    def state(self, node):
        action = self

        class S(_State):
            def step(self, dt, end):
                scene = _scene_clock(node, end - dt)
                try:
                    action.run(node)
                finally:
                    if scene is not None:
                        scene.action_now = end
                return dt
        return S()


class RunBlock(_Instant):
    def __init__(self, fn):
        self.fn = fn

    def run(self, node):
        self.fn()


class RemoveFromParent(_Instant):
    def run(self, node):
        node.removeFromParent()


class Play(_Instant):
    """``SKAction.play()``, for an ``SKAudioNode``."""

    def run(self, node):
        node.play()


class Stop(_Instant):
    def run(self, node):
        node.stop()


# ---- actions that take time ------------------------------------------------------------
class _Timed(Action):
    def __init__(self, duration):
        self.duration = max(0.0, float(duration))

    def begin(self, node):
        """Called once, when the action starts; returns what ``apply`` needs."""
        return None

    def apply(self, node, start, fraction):
        pass

    def state(self, node):
        action = self

        class S(_State):
            def __init__(self):
                self.elapsed = 0.0
                self.start = None
                self.started = False

            def step(self, dt, end):
                if not self.started:
                    self.started = True
                    self.start = action.begin(node)
                self.elapsed += dt
                d = action.duration
                f = 1.0 if d <= 0 else min(1.0, self.elapsed / d)
                action.apply(node, self.start, f)
                if self.elapsed >= d:
                    return self.elapsed - d
                return None
        return S()


class Wait(_Timed):
    pass


class MoveTo(_Timed):
    """``moveToX:``, ``moveToY:``, ``moveTo:``: linear, from wherever the node is when the
    action starts.  ``x`` or ``y`` None leaves that coordinate alone."""

    def __init__(self, x, y, duration):
        super().__init__(duration)
        self.x, self.y = x, y

    def begin(self, node):
        return node.position

    def apply(self, node, start, f):
        sx, sy = start
        x = sx if self.x is None else sx + (self.x - sx) * f
        y = sy if self.y is None else sy + (self.y - sy) * f
        node.position = (x, y)


class ChangeVolumeTo(_Timed):
    def __init__(self, volume, duration):
        super().__init__(duration)
        self.volume = float(volume)

    def begin(self, node):
        return node.volume

    def apply(self, node, start, f):
        node.set_volume(start + (self.volume - start) * f)


class ChangeVolumeBy(_Timed):
    def __init__(self, delta, duration):
        super().__init__(duration)
        self.delta = float(delta)

    def begin(self, node):
        return node.volume

    def apply(self, node, start, f):
        node.set_volume(start + self.delta * f)


class Animate(_Timed):
    """``animateWithTextures:timePerFrame:``: the sprite's texture name steps through the
    frames.  Nothing is drawn; the name is kept for the window and the tests."""

    def __init__(self, textures, time_per_frame):
        self.textures = list(textures)
        self.time_per_frame = float(time_per_frame)
        super().__init__(len(self.textures) * self.time_per_frame)

    def apply(self, node, start, f):
        if not self.textures:
            return
        i = min(len(self.textures) - 1, int(f * len(self.textures) + 1e-9))
        node.texture = self.textures[i]


class PlaySoundFile(_Timed):
    """``playSoundFileNamed:waitForCompletion:``: a one-shot sound, not placed, at full
    volume; it takes the sound's length only when told to wait."""

    def __init__(self, name, wait):
        super().__init__(0.0)
        self.name = name
        self.wait = bool(wait)

    def begin(self, node):
        scene = node.scene
        if scene is not None and scene.audio is not None:
            length = scene.audio.play_once(self.name)
            if self.wait:
                self.duration = length
        return None


# ---- actions made of actions -----------------------------------------------------------
class Sequence(Action):
    def __init__(self, actions):
        self.actions = list(actions)
        self.duration = sum(a.duration for a in self.actions)

    def state(self, node):
        actions = self.actions

        class S(_State):
            def __init__(self):
                self.i = 0
                self.cur = actions[0].state(node) if actions else None

            def step(self, dt, end):
                while self.cur is not None:
                    left = self.cur.step(dt, end)
                    if left is None:
                        return None
                    self.i += 1
                    if self.i >= len(actions):
                        self.cur = None
                        return left
                    if not node.in_scene:
                        return None         # removed: the rest never runs
                    self.cur = actions[self.i].state(node)
                    dt = left
                return dt
        return S()


class Repeat(Action):
    """``repeatActionForever:``, or ``count`` times."""

    def __init__(self, action, count=None):
        self.action = action
        self.count = count
        self.duration = float('inf') if count is None else action.duration * count

    def state(self, node):
        action, count = self.action, self.count

        class S(_State):
            def __init__(self):
                self.done = 0
                self.cur = action.state(node)

            def step(self, dt, end):
                for _ in range(MAX_LOOPS):
                    left = self.cur.step(dt, end)
                    if left is None:
                        return None
                    self.done += 1
                    if count is not None and self.done >= count:
                        return left
                    if not node.in_scene:
                        return None
                    self.cur = action.state(node)
                    if left <= 0.0 and action.duration <= 0.0:
                        return None         # nothing takes time: wait for the next frame
                    dt = left
                log.warning('a repeated action came round %d times in one frame', MAX_LOOPS)
                return None
        return S()


# ---- SKAction's class methods, under the names the binary calls -------------------------
def moveToX(x, duration):
    return MoveTo(x, None, duration)


def moveToY(y, duration):
    return MoveTo(None, y, duration)


def moveTo(point, duration):
    return MoveTo(point[0], point[1], duration)


def waitForDuration(duration):
    return Wait(duration)


def sequence(actions):
    return Sequence(actions)


def runBlock(fn):
    return RunBlock(fn)


def repeatActionForever(action):
    return Repeat(action)


def repeatAction(action, count):
    return Repeat(action, count)


def removeFromParent():
    return RemoveFromParent()


def animateWithTextures(textures, timePerFrame):
    return Animate(textures, timePerFrame)


def changeVolumeTo(volume, duration):
    return ChangeVolumeTo(volume, duration)


def changeVolumeBy(delta, duration):
    return ChangeVolumeBy(delta, duration)


def play():
    return Play()


def stop():
    return Stop()


def playSoundFileNamed(name, waitForCompletion=False):
    return PlaySoundFile(name, waitForCompletion)
