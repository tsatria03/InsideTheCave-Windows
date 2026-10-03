"""``SKPhysicsBody`` and contacts: which things touch, and when they start to.

The game uses physics only to be told when two things touch (``didBeginContact:``): gravity
is (0, 0) (0x1000169c4) and every collision mask is 0, so nothing pushes anything and no
body ever moves by physics (GAME_STRUCTURE.md section 5).  So this is overlap testing, once
a frame after the actions have run, as SpriteKit orders its frame.

**Which pairs are tested** is SpriteKit's rule, with bit masks: two bodies report contacts
when ``(A.categoryBitMask & B.contactTestBitMask) | (B.categoryBitMask &
A.contactTestBitMask)`` is not zero.  The game's categories are plain numbers, 0 to 7, not
single bits (monster 0, bat 1, player 2, roar sensor 3, thrown torch 4, torch pickup 6,
coin 7), so which pairs touch follows from the bits of those numbers exactly as it did on
the iPhone; a monster's category 0 matches nothing, and it is found by its own mask, 7.

**A contact begins** in the frame two bodies first overlap, and is reported once; it can
begin again only after they have parted.  Bodies are given to the delegate in a fixed
order (the order they joined the scene); the port's game scene accepts either order
(aidocks/project_port_plan.md, question 4).

**Shapes**: rectangles (with a centre offset) and circles, never rotated (the game
creates no rotation).  A body's shape is taken in the scene's units, as the game computed
it from the sprite's ``size``, and then scaled by the node's own scale, as SpriteKit
scales a body with its node (**inferred**: Apple's code, not the binary).  The binary
points that way: ``createPlayer`` builds the player's circle from its size *before*
``changeSpritePlayer`` scales it by W x 0.0007 (0x10000bec8, then 0x10000c134), a radius
of 150 points, which only scaled with the node comes out as half the drawn player's
width, 78.75; unscaled it would be twice the sprite.  For a body built after the scale
the difference is small (a monster's scale is 0.975).  The switch
``BODY_SCALES_WITH_NODE`` keeps the other reading at hand (aidocks/project_port_plan.md,
question 11).
"""
from __future__ import annotations

import math

#: Whether a body's shape grows and shrinks with its node's scale (**inferred** yes, from
#: createPlayer; turned on 2026-10-02 with phase 3).
BODY_SCALES_WITH_NODE = True

DEFAULT_CATEGORY = 0xFFFFFFFF
DEFAULT_CONTACT = 0
DEFAULT_COLLISION = 0xFFFFFFFF


class PhysicsBody:
    """``SKPhysicsBody``."""

    def __init__(self, kind, size=None, radius=None, center=(0.0, 0.0)):
        self.kind = kind                    # 'rect' or 'circle'
        self.size = size
        self.radius = radius
        self.center = center
        self.categoryBitMask = DEFAULT_CATEGORY
        self.contactTestBitMask = DEFAULT_CONTACT
        self.collisionBitMask = DEFAULT_COLLISION
        self.allowsRotation = True
        self.node = None

    def bounds(self):
        """The body in the scene: ('rect', left, bottom, right, top) or
        ('circle', x, y, r)."""
        x, y = self.node.scene_position()
        sx, sy = self.node.scene_scale() if BODY_SCALES_WITH_NODE else (1.0, 1.0)
        cx, cy = x + self.center[0] * sx, y + self.center[1] * sy
        if self.kind == 'circle':
            return ('circle', cx, cy, self.radius * max(abs(sx), abs(sy)))
        w, h = self.size[0] * abs(sx), self.size[1] * abs(sy)
        return ('rect', cx - w / 2, cy - h / 2, cx + w / 2, cy + h / 2)


def bodyWithRectangleOfSize(size, center=(0.0, 0.0)):
    return PhysicsBody('rect', size=(float(size[0]), float(size[1])), center=center)


def bodyWithCircleOfRadius(radius, center=(0.0, 0.0)):
    return PhysicsBody('circle', radius=float(radius), center=center)


def tests_contact(a, b):
    """SpriteKit's rule for whether a pair reports contacts."""
    return bool((a.categoryBitMask & b.contactTestBitMask)
                | (b.categoryBitMask & a.contactTestBitMask))


def overlap(p, q):
    """Whether two shapes from ``bounds`` touch or overlap."""
    if p[0] == 'rect' and q[0] == 'rect':
        return p[1] <= q[3] and q[1] <= p[3] and p[2] <= q[4] and q[2] <= p[4]
    if p[0] == 'circle' and q[0] == 'circle':
        return math.hypot(p[1] - q[1], p[2] - q[2]) <= p[3] + q[3]
    c, r = (p, q) if p[0] == 'circle' else (q, p)
    nx = min(max(c[1], r[1]), r[3])
    ny = min(max(c[2], r[2]), r[4])
    return math.hypot(c[1] - nx, c[2] - ny) <= c[3]


class Contact:
    """``SKPhysicsContact``."""

    def __init__(self, a, b):
        self.bodyA = a
        self.bodyB = b

    def __repr__(self):
        return '<Contact %r / %r>' % (self.bodyA.node, self.bodyB.node)


class PhysicsWorld:
    """``SKPhysicsWorld``: the bodies in the scene, and the contacts between them."""

    def __init__(self):
        self.gravity = (0.0, 0.0)
        self.contactDelegate = None
        self.bodies = []            # in the order they joined the scene
        self._touching = set()      # pairs of id() touching at the last check

    def add(self, body):
        if body not in self.bodies:
            self.bodies.append(body)

    def remove(self, body):
        if body in self.bodies:
            self.bodies.remove(body)
        self._touching = {pair for pair in self._touching if id(body) not in pair}

    def simulate(self):
        """Find the contacts that began since the last frame and tell the delegate, in
        order.  Contacts reported to the delegate may remove bodies; a body removed
        before its turn is skipped."""
        bodies = list(self.bodies)
        shapes = [b.bounds() for b in bodies]
        now = set()
        began = []
        for i in range(len(bodies)):
            for j in range(i + 1, len(bodies)):
                a, b = bodies[i], bodies[j]
                if not tests_contact(a, b):
                    continue
                if overlap(shapes[i], shapes[j]):
                    pair = frozenset((id(a), id(b)))
                    now.add(pair)
                    if pair not in self._touching:
                        began.append((a, b))
        self._touching = now
        delegate = self.contactDelegate
        for a, b in began:
            if a not in self.bodies or b not in self.bodies:
                continue
            if delegate is not None:
                delegate.didBeginContact(Contact(a, b))
        return len(began)
