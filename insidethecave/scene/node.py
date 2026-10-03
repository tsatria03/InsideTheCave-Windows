"""``SKNode`` and ``SKSpriteNode``: things in the scene, where they are, and their actions.

Positions are in the scene's own units, as the original's: 750 by 1334, with (0, 0) at the
centre (``GameScene.sks``, anchor (0.5, 0.5); GAME_STRUCTURE.md section 2).  A child's
position is in its parent's space, so its place in the scene is its parent's place plus its
position times the parent's scale; only the scenery uses children (scenario1 and scenario2
ride on scenario0, 0x100016a90..0x100016cf4).

**A sprite's size** is its image's size in points (``image_sizes.py``, read from
``game/Assets.car``) times its scale, which is how the game reads it: every body is built
from ``size`` after ``setScale`` (``createMonster``: ``setScale:`` at 0x10000cba0, then
``size`` x 0.5 into ``bodyWithRectangleOfSize:center:`` at 0x10000cc64).  That ``size``
includes the scale is SpriteKit's behaviour (**inferred**: Apple's code, not the binary).
A name the catalogue does not hold, such as the roar sensor's ``""``, gets SpriteKit's
placeholder for a missing image, taken as 128 by 128 points (**inferred**;
aidocks/project_port_plan.md, question 11).

Nothing is drawn: the port has no pictures.  A sprite keeps its texture's name, so a
sighted helper's window and the tests can tell which frame it is on.
"""
from __future__ import annotations

from . import image_sizes

#: SpriteKit's placeholder for an image it cannot find (**inferred**).
MISSING_IMAGE = (128.0, 128.0)


def image_size(name):
    """An image's size in points, by the name the code asks for.  ``imageNamed:`` takes
    the name with or without ``.png`` (the dead sprites are asked for with it,
    ``"deadPedra.png"`` at 0x100027931)."""
    if name not in image_sizes.SIZES and name.lower().endswith('.png'):
        name = name[:-4]
    return image_sizes.SIZES.get(name, MISSING_IMAGE)


class Node:
    """``SKNode``."""

    def __init__(self, name=None):
        self.name = name
        self.position = (0.0, 0.0)
        self.xScale = 1.0
        self.yScale = 1.0
        self.zPosition = 0.0
        self.alpha = 1.0
        self.paused = False
        self.parent = None
        self.children = []
        self._body = None
        self._actions = []          # [(key or None, running action)]

    # ---- the body ---------------------------------------------------------------------
    @property
    def physicsBody(self):
        return self._body

    @physicsBody.setter
    def physicsBody(self, body):
        """``setPhysicsBody:``: the body joins the scene's physics with its node."""
        scene = self.scene
        if self._body is not None and scene is not None:
            scene.physicsWorld.remove(self._body)
        self._body = body
        if body is not None:
            body.node = self
            if scene is not None:
                scene.physicsWorld.add(body)

    # ---- the tree ---------------------------------------------------------------------
    def addChild(self, node):
        if node.parent is not None:
            raise ValueError('%r already has a parent' % node)
        node.parent = self
        self.children.append(node)
        scene = self.scene
        if scene is not None:
            for n in node.walk():
                scene._node_added(n)

    def removeFromParent(self):
        parent = self.parent
        if parent is None:
            return
        scene = self.scene
        parent.children.remove(self)
        self.parent = None
        if scene is not None:
            for n in self.walk():
                scene._node_removed(n)

    def removeAllChildren(self):
        for child in list(self.children):
            child.removeFromParent()

    def walk(self):
        """This node and everything under it."""
        yield self
        for child in list(self.children):
            yield from child.walk()

    @property
    def scene(self):
        n = self
        while n.parent is not None:
            n = n.parent
        return n if getattr(n, 'is_scene', False) else None

    @property
    def in_scene(self):
        return self.scene is not None

    # ---- place --------------------------------------------------------------------------
    def setScale(self, scale):
        self.xScale = self.yScale = float(scale)

    def scene_position(self):
        """Where the node is in the scene's units."""
        x, y = self.position
        p = self.parent
        while p is not None and not getattr(p, 'is_scene', False):
            px, py = p.position
            x, y = px + x * p.xScale, py + y * p.yScale
            p = p.parent
        return x, y

    def scene_scale(self):
        sx, sy = self.xScale, self.yScale
        p = self.parent
        while p is not None and not getattr(p, 'is_scene', False):
            sx, sy = sx * p.xScale, sy * p.yScale
            p = p.parent
        return sx, sy

    def effectively_paused(self):
        n = self
        while n is not None:
            if n.paused:
                return True
            n = n.parent
        return False

    # ---- actions ------------------------------------------------------------------------
    def runAction(self, action, key=None):
        """``runAction:`` / ``runAction:withKey:``: a keyed action replaces the one running
        under that key."""
        from .actions import Running
        if key is not None:
            self.removeActionForKey(key)
        self._actions.append((key, Running(action, self)))

    def actionForKey(self, key):
        for k, running in self._actions:
            if k == key:
                return running.action
        return None

    def removeActionForKey(self, key):
        self._actions = [(k, r) for k, r in self._actions if k != key]

    def removeAllActions(self):
        self._actions = []

    def hasActions(self):
        return bool(self._actions)

    def advance(self, now):
        """Run this node's own actions up to ``now``; the scene calls it every frame."""
        for entry in list(self._actions):
            if entry not in self._actions:
                continue            # removed by an earlier action this frame
            _key, running = entry
            if running.step_to(now) and entry in self._actions:
                self._actions.remove(entry)

    def hold(self, now):
        """Paused: the actions keep their place while time goes by."""
        for _key, running in self._actions:
            running.hold(now)

    def __repr__(self):
        return '<%s %s at (%.1f, %.1f)>' % (type(self).__name__, self.name or '',
                                           self.position[0], self.position[1])


class SpriteNode(Node):
    """``SKSpriteNode(imageNamed:)``: a node with an image's size."""

    def __init__(self, image='', name=None):
        super().__init__(name)
        self.texture = image
        self._base = image_size(image)

    @property
    def size(self):
        """The image's size times the scale, as SpriteKit's ``size``."""
        return (self._base[0] * self.xScale, self._base[1] * self.yScale)

    def setSize(self, size):
        """``setSize:``: the sprite's ``size`` becomes this; the scale stays as it is."""
        w, h = size
        self._base = (w / self.xScale if self.xScale else w,
                      h / self.yScale if self.yScale else h)
