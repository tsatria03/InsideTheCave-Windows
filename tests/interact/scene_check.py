#!/usr/bin/env python
"""For testing by ear: hear phase 2, the SpriteKit stand-in, placing sounds in the lanes and
timing the roar, before the game scene exists.  Not a test, and not the game: each check
is a short preview built from the stand-in and the binary's own numbers, a monster or a
bat or a coin coming down a lane at the opening speed.  Wear headphones.

    python tests\\interact\\scene_check.py        the menu
    python tests\\interact\\scene_check.py 1      one check straight away, then the menu

The window and its keys are the platform check's: Up and Down choose, Enter or the number
runs, Escape stops a check or leaves the menu, Alt+F4 quits at any moment.

The checks, you standing at the bottom of the cave as the game puts you (0, -0.25 H):

     1  a monster down each lane, you in the centre: its roar at the sensor, then "now" when
        it would reach you
     2  you in each lane, a monster down the left lane: the roar from where it is to you
     3  bats down each lane, you in the centre: 1.0 in your lane, 0.7 in another

No sound is louder than 1.0 (the dev): the game asks for 3.0 in your lane, heard as 1.0,
so a roar is as loud in your lane as in another and tells its lane by where it comes from.
     4  a coin down each lane, jingling as it comes (the port's addition), then "now"
        when it would reach you
     5  eight monsters in a row, lanes at random, as the game's first slots come: roar,
        then "now", every 2.64 seconds

Every timing here is the stand-in's: the roar when the monster's body meets the sensor's,
"now" when it meets yours, from the sizes in Assets.car and the scales in the binary.  The
placing (how far left and right a lane sounds) is a first guess on the constants in
``insidethecave/scene/audio.py``, for you to judge.

**Your save is never touched**: its own save in ``%APPDATA%\\InsideTheCave\\scene_check``.
"""
from __future__ import annotations

import os
import random
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, ROOT)
sys.path.insert(0, HERE)

import platform_check                                            # noqa: E402
from platform_check import Quit, Stop, Window                    # noqa: E402

platform_check.SAVE_NAME = 'scene_check'
Window.TITLE = 'Inside The Cave - scene check'

#: The binary's numbers (GAME_STRUCTURE.md sections 2, 5 and 6).
SPEED = 4.0                     # speedMonster at the start, seconds top to bottom
LANES = (('Left', -0.3), ('Centre', 0.0), ('Right', 0.3))


class Preview:
    """A scene with the player, the roar sensor and the two placed sounds, as the game
    builds them, and things sent down the lanes."""

    def __init__(self, window, speech, al, bank):
        from insidethecave.scene import actions as A
        from insidethecave.scene import physics
        from insidethecave.scene.audio import AudioEngine, AudioNode
        from insidethecave.scene.node import SpriteNode
        from insidethecave.scene.scene import Scene
        self.A, self.physics, self.SpriteNode = A, physics, SpriteNode
        self.window, self.speech = window, speech
        self.engine = AudioEngine(al, bank)
        self.scene = Scene(audio=self.engine)
        self.W, self.H = self.scene.size
        W, H = self.W, self.H
        self.scene.physicsWorld.contactDelegate = self
        # the player, as createPlayer: a circle half its width made before it is scaled by
        # W x 0.0007 (0x10000bec8, then 0x10000c134), category 2, mask 6
        self.player = SpriteNode('player', name='player')
        self.player.position = (0, -0.25 * H)
        self.player.physicsBody = self._body(
            physics.bodyWithCircleOfRadius(self.player.size[0] / 2), 2, 6)
        self.player.setScale(W * 0.0007)
        self.scene.addChild(self.player)
        self.scene.listener = self.player
        # the roar sensor: the missing image, xScale W x 0.007, yScale 0.005, at 0.07 H
        sensor = SpriteNode('', name='sensor')
        sensor.xScale, sensor.yScale = W * 0.007, 0.005
        sensor.position = (0, 0.07 * H)
        sensor.physicsBody = self._body(physics.bodyWithRectangleOfSize(sensor.size), 3, 1)
        self.scene.addChild(sensor)
        self.roar = AudioNode('Rugido.mp3')
        self.bats = AudioNode('BatSound.wav')
        for node in (self.roar, self.bats):
            node.autoplayLooped = False
            self.scene.addChild(node)
        self.AudioNode = AudioNode
        self.reached = []

    @staticmethod
    def _body(body, category, mask):
        body.categoryBitMask, body.contactTestBitMask, body.collisionBitMask = \
            category, mask, 0
        return body

    def lane_x(self, fraction):
        return fraction * self.W

    # ---- what comes down --------------------------------------------------------------
    def monster(self, lane):
        W, H = self.W, self.H
        m = self.SpriteNode('monstroPedra', name='monster')
        m.setScale(W * 0.0013)
        m.position = (self.lane_x(lane), 0.5 * H)
        w, h = m.size
        m.physicsBody = self._body(
            self.physics.bodyWithRectangleOfSize((w * 0.5, h * 0.5), center=(0, -22)), 0, 7)
        self.scene.addChild(m)
        m.runAction(self.A.sequence([self.A.moveToY(-0.5 * H, SPEED),
                                     self.A.removeFromParent()]))

    def bat(self, lane):
        W, H = self.W, self.H
        b = self.SpriteNode('morcego1', name='bat')
        b.setScale(W * 0.0009)
        b.position = (self.lane_x(lane), 0.5 * H)
        w, h = b.size
        b.physicsBody = self._body(
            self.physics.bodyWithRectangleOfSize((w * 0.5, h * 0.5), center=(0, -22)), 1, 7)
        self.scene.addChild(b)
        b.runAction(self.A.sequence([self.A.moveToY(-0.5 * H, SPEED),
                                     self.A.removeFromParent()]))

    def coin(self, lane):
        """A coin, with the jingle the port adds riding down with it, looped."""
        W, H = self.W, self.H
        c = self.SpriteNode('rockCoin', name='coin')
        c.setScale(W * 0.0008)
        c.position = (self.lane_x(lane), 0.5 * H)
        c.physicsBody = self._body(
            self.physics.bodyWithCircleOfRadius(c.size[0] / 2), 7, 3)
        jingle = self.AudioNode('tilintar.aiff')
        c.addChild(jingle)
        self.scene.addChild(c)
        c.runAction(self.A.sequence([self.A.moveToY(-0.5 * H, SPEED),
                                     self.A.removeFromParent()]))

    # ---- contacts, as the game's handlers would treat them ----------------------------
    def didBeginContact(self, contact):
        names = {contact.bodyA.node.name: contact.bodyA.node,
                 contact.bodyB.node.name: contact.bodyB.node}
        if 'sensor' in names and 'monster' in names:
            self.sound_at(self.roar, names['monster'], 3.0, 1.0)
        elif 'sensor' in names and 'bat' in names:
            self.sound_at(self.bats, names['bat'], 3.0, 0.7)
        elif 'player' in names and len(names) == 2:
            other = [n for k, n in names.items() if k != 'player'][0]
            if other.name in ('monster', 'bat', 'coin'):
                self.reached.append(other.name)
                self.window.show('now')
                self.speech.speak('now')
                if other.name == 'coin':
                    other.removeFromParent()

    def sound_at(self, node, thing, here, elsewhere):
        """playMonsterRoarAtPoint: / playBatSoundAtPoint: (0x10000f69c, 0x10000f7c4)."""
        node.position = thing.position
        same = thing.position[0] == self.player.position[0]
        node.runAction(self.A.changeVolumeTo(here if same else elsewhere, 0))
        node.runAction(self.A.play())

    # ---- running ----------------------------------------------------------------------
    def run_for(self, seconds):
        """Run the scene on the real clock, watching the keys."""
        end = time.perf_counter() + seconds
        while True:
            now = time.perf_counter()
            self.scene.frame(now)
            if now >= end:
                return
            self.window.wait(0.01)

    def close(self):
        self.engine.release()


class SceneCheck(platform_check.Check):
    def preview(self):
        return Preview(self.window, self.speech, self.al, self.bank)

    def _each_lane(self, send, what):
        for place, lane in LANES:
            p = self.preview()
            try:
                self.say('%s, %s lane.' % (what, place.lower()), 0.8)
                p.run_for(0.05)
                send(p, lane)
                p.run_for(SPEED * 0.8)
            finally:
                p.close()

    def monsters(self):
        self.say('A monster down each lane. You are in the centre.')
        self._each_lane(lambda p, lane: p.monster(lane), 'A monster')

    def you_in_each_lane(self):
        self.say('A monster down the left lane, with you in each lane.')
        for place, lane in LANES:
            p = self.preview()
            try:
                p.player.position = (p.lane_x(lane), p.player.position[1])
                self.say('You are %s.' % place.lower(), 0.8)
                p.run_for(0.05)
                p.monster(-0.3)
                p.run_for(SPEED * 0.8)
            finally:
                p.close()

    def bats(self):
        self.say('Bats down each lane. You are in the centre.')
        self._each_lane(lambda p, lane: p.bat(lane), 'Bats')

    def coins(self):
        self.say('A coin down each lane, jingling as it comes. You are in the centre.')
        self._each_lane(lambda p, lane: p.coin(lane), 'A coin')

    def a_run(self):
        """Every 4th slot an obstacle, a slot every 0.165 x speed: 2.64 s apart."""
        self.say('Eight monsters, lanes at random, 2.64 seconds apart. You are in the centre.')
        p = self.preview()
        try:
            p.run_for(0.5)
            last = None
            for _ in range(8):
                lane = random.choice([l for _n, l in LANES if l != last])
                last = lane
                p.monster(lane)
                p.run_for(4 * 0.165 * SPEED)
            p.run_for(SPEED * 0.8)
        finally:
            p.close()


platform_check.CHECKS = (
    ('A monster down each lane, you in the centre', 'monsters'),
    ('You in each lane, a monster down the left', 'you_in_each_lane'),
    ('Bats down each lane', 'bats'),
    ('A coin down each lane, jingling', 'coins'),
    ('Eight monsters in a row', 'a_run'),
)
platform_check.MENU_HELP = platform_check.MENU_HELP.replace('Platform check', 'Scene check')
platform_check.Check = SceneCheck


if __name__ == '__main__':
    sys.exit(platform_check.main(sys.argv))
