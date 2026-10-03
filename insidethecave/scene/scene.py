"""``SKScene``: the tree of nodes, the frame, the physics world and the listener.

``GameScene.sks`` makes the scene 750 by 1334 with its anchor at (0.5, 0.5), so (0, 0)
is the centre (GAME_STRUCTURE.md section 2).  Each frame runs in SpriteKit's order:

    1. ``update(now)``, which the original leaves empty (``ret`` at 0x10001561c)
    2. every node's actions, the scene's own first, then down the tree
    3. the physics: the contacts that began, to the contact delegate
    4. the sounds kept where their nodes are

A paused node, or a paused scene, keeps its actions where they are while the time goes
by (``setPaused:``, used at death for the scenery and for the whole scene).

The scene's clock is whatever the caller gives ``frame``, in seconds: the real clock in
the game, made-up times in the tests.
"""
from __future__ import annotations

from .audio import AudioNode
from .node import Node
from .physics import PhysicsWorld

WIDTH = 750.0
HEIGHT = 1334.0


class Scene(Node):
    is_scene = True

    def __init__(self, size=(WIDTH, HEIGHT), audio=None):
        super().__init__('scene')
        self.size = (float(size[0]), float(size[1]))
        self.anchorPoint = (0.5, 0.5)
        self.physicsWorld = PhysicsWorld()
        self.listener = None
        self.audio = audio          # an AudioEngine, or None for silence
        self.time = None            # the clock at the current frame
        self.action_now = None      # when actions started now begin (actions.py)
        self.frames = 0

    @property
    def scene(self):
        return self

    # ---- nodes joining and leaving ------------------------------------------------------
    def _node_added(self, node):
        if node.physicsBody is not None:
            self.physicsWorld.add(node.physicsBody)
        if isinstance(node, AudioNode) and self.audio is not None:
            self.audio.attach(node)

    def _node_removed(self, node):
        if node.physicsBody is not None:
            self.physicsWorld.remove(node.physicsBody)
        if isinstance(node, AudioNode) and node.engine is not None:
            node.engine.detach(node)

    # ---- the frame ----------------------------------------------------------------------
    def update(self, now):
        """``update:``: empty in the original (0x10001561c)."""

    def frame(self, now):
        """Run one frame at time ``now``."""
        self.time = now
        self.action_now = now
        self.frames += 1
        self.update(now)
        for node in list(self.walk()):
            if node is not self and node.scene is not self:
                continue            # removed by an action earlier this frame
            if node.effectively_paused():
                node.hold(now)
            else:
                node.advance(now)
        self.action_now = now
        if not self.paused:
            self.physicsWorld.simulate()
        if self.audio is not None:
            self.audio.sync(self)

    # ---- pausing everything (PORT ADDITION) ---------------------------------------------
    def pause_all(self):
        """The port's pause: the scene's actions and every sound stop where they are."""
        self.paused = True
        if self.audio is not None:
            self.audio.pause_all()

    def resume_all(self):
        self.paused = False
        if self.audio is not None:
            self.audio.resume_all()
