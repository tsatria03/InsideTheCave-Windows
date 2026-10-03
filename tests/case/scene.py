"""The SpriteKit stand-in: ``insidethecave/scene``.

Actions are run against made-up clocks with frames of different lengths, to show they end
on the binary's own durations whatever the frame rate; contacts follow SpriteKit's mask
rule and begin once; sounds are placed on OpenAL Soft's null driver, so nothing is heard.
"""
from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
import _scratch_save                                             # noqa: E402  never the real save

from insidethecave import paths                                  # noqa: E402
from insidethecave.platform import openal, sound                 # noqa: E402
from insidethecave.scene import actions as A                     # noqa: E402
from insidethecave.scene import physics                          # noqa: E402
from insidethecave.scene.audio import AudioEngine, AudioNode     # noqa: E402
from insidethecave.scene.node import Node, SpriteNode, image_size  # noqa: E402
from insidethecave.scene.scene import HEIGHT, WIDTH, Scene       # noqa: E402

W, H = WIDTH, HEIGHT


def _run(scene, until, step, start=0.0):
    """Frames of ``step`` seconds (a list of steps cycles), up to ``until``."""
    steps = step if isinstance(step, (list, tuple)) else [step]
    t, i = start, 0
    scene.frame(t)
    while t < until - 1e-12:
        t = min(until, t + steps[i % len(steps)])
        i += 1
        scene.frame(t)
    return t


def _close(a, b, eps=1e-6):
    return abs(a - b) <= eps


# ---- images ----------------------------------------------------------------------------

def test_sizes_come_from_the_asset_catalogue():
    assert image_size('monstroPedra') == (220.0, 153.0)
    assert image_size('morcego1') == (333.0, 233.0)
    assert image_size('player') == (300.0, 375.0)
    assert image_size('torchObstacle') == (100.0, 129.0)


def test_a_missing_image_is_the_placeholder():
    assert image_size('') == (128.0, 128.0)


def test_a_sprites_size_includes_its_scale():
    """createMonster: setScale(W x 0.0013), then size (0x10000cb94..0x10000cbbc)."""
    s = SpriteNode('monstroPedra')
    s.setScale(W * 0.0013)
    assert _close(s.size[0], 220 * 0.975) and _close(s.size[1], 153 * 0.975)
    s.setSize((W, H))
    assert s.size == (W, H) and _close(s.xScale, 0.975)


def test_a_childs_place_follows_its_parent():
    """The scenery: scenario1 at (0, H) on scenario0 (0x100016a90..0x100016cf4)."""
    scene = Scene()
    s0, s1 = SpriteNode('cenarioPedra'), SpriteNode('cenarioPedra')
    s1.position = (0, H)
    s0.addChild(s1)
    scene.addChild(s0)
    s0.position = (0, -500)
    assert s1.scene_position() == (0, H - 500)


# ---- actions ---------------------------------------------------------------------------

def test_a_move_is_linear():
    scene = Scene()
    n = Node()
    scene.addChild(n)
    n.position = (0, 667)
    _run(scene, 0.0, 0.1)
    n.runAction(A.moveToY(-667, 4.0))
    _run(scene, 1.0, 0.1)
    assert _close(n.position[1], 667 - 1334 / 4.0, 1e-6), n.position
    _run(scene, 9.0, 0.1, start=1.0)
    assert n.position[1] == -667 and not n.hasActions()


def test_the_slot_chain_keeps_its_time_whatever_the_frame_rate():
    """A slot moves to 0.33 H in 0.165 x speedMonster and its block makes the next
    (0x100013ae8): ten slots must start 0.66 s apart, at 60 frames a second or 7."""
    for step in (1 / 60.0, 1 / 7.0, [0.003, 0.05, 0.021]):
        scene = Scene()
        starts = []

        def make():
            starts.append(scene.action_now)
            if len(starts) >= 10:
                return
            slot = Node()
            slot.position = (0, 0.5 * H)
            scene.addChild(slot)
            slot.runAction(A.sequence([A.moveToY(0.33 * H, 0.165 * 4.0), A.runBlock(make),
                                       A.moveToY(-0.5 * H, 0.835 * 4.0), A.removeFromParent()]))

        scene.frame(0.0)
        make()
        _run(scene, 12.0, step)
        assert len(starts) == 10, (step, starts)
        for k, t in enumerate(starts):
            assert _close(t, 0.66 * k, 1e-6), (step, k, t)


def test_a_sequence_stops_once_its_node_is_removed():
    scene = Scene()
    n, ran = Node(), []
    scene.addChild(n)
    n.runAction(A.sequence([A.waitForDuration(0.1), A.removeFromParent(),
                            A.runBlock(lambda: ran.append(1))]))
    _run(scene, 1.0, 0.05)
    assert not n.in_scene and ran == []


def test_animation_frames_and_repeat_forever():
    """changeSpritePlayer: frames [1, 2, 3, 2] at 0.1 s, forever (0x10000c0c0)."""
    scene = Scene()
    s = SpriteNode('player')
    scene.addChild(s)
    s.runAction(A.repeatActionForever(
        A.animateWithTextures(['player', 'player2', 'player3', 'player2'], 0.1)))
    seen = []
    t = 0.0
    scene.frame(t)
    for _ in range(9):
        t += 0.1
        scene.frame(t + 0.01)
        seen.append(s.texture)
    assert seen[:5] == ['player2', 'player3', 'player2', 'player', 'player2'], seen
    assert s.hasActions()


def test_a_keyed_action_is_replaced_and_removed_by_its_key():
    """The score loop runs keyed "upScore" (0x1000154a4) and stops by that key."""
    scene = Scene()
    n, count = Node(), []
    scene.addChild(n)
    tick = A.repeatActionForever(A.sequence([A.waitForDuration(0.25),
                                             A.runBlock(lambda: count.append(1))]))
    n.runAction(tick, key='upScore')
    n.runAction(tick, key='upScore')                  # replaces, does not double
    _run(scene, 1.0, 0.01)
    assert len(count) == 4, count
    n.removeActionForKey('upScore')
    _run(scene, 2.0, 0.01, start=1.0)
    assert len(count) == 4


def test_a_paused_node_keeps_its_place():
    scene = Scene()
    n = Node()
    scene.addChild(n)
    scene.frame(0.0)
    n.runAction(A.moveToX(100, 1.0))
    scene.frame(0.5)
    n.paused = True
    scene.frame(5.0)
    assert _close(n.position[0], 50.0)
    n.paused = False
    scene.frame(5.25)
    assert _close(n.position[0], 75.0), n.position


def test_pausing_the_scene_holds_everything():
    scene = Scene()
    n = Node()
    scene.addChild(n)
    scene.frame(0.0)
    n.runAction(A.moveToX(100, 1.0))
    scene.frame(0.5)
    scene.pause_all()
    scene.frame(3.0)
    scene.resume_all()
    scene.frame(3.5)
    assert _close(n.position[0], 100.0), n.position


# ---- contacts --------------------------------------------------------------------------

class _Delegate:
    def __init__(self):
        self.contacts = []

    def didBeginContact(self, contact):
        self.contacts.append((contact.bodyA.node.name, contact.bodyB.node.name))


def _body_node(scene, name, shape, cat, mask, pos):
    n = Node(name)
    n.position = pos
    n.physicsBody = shape
    n.physicsBody.categoryBitMask = cat
    n.physicsBody.contactTestBitMask = mask
    n.physicsBody.collisionBitMask = 0
    scene.addChild(n)
    return n


def test_the_mask_rule_is_spritekits():
    """The game's categories are numbers, not bits: category & other's mask, either way."""
    cats = {'monster': (0, 7), 'bat': (1, 7), 'player': (2, 6), 'sensor': (3, 1),
            'pickup': (6, 2), 'coin': (7, 3)}

    def body(name):
        b = physics.bodyWithCircleOfRadius(1)
        b.categoryBitMask, b.contactTestBitMask = cats[name]
        return b

    pairs = {(a, b) for a in cats for b in cats if a < b
             and physics.tests_contact(body(a), body(b))}
    for must in (('monster', 'player'), ('monster', 'sensor'), ('bat', 'player'),
                 ('bat', 'sensor'), ('pickup', 'player'), ('coin', 'player')):
        assert tuple(sorted(must)) in pairs, must
    assert ('player', 'sensor') in pairs, 'player 2 & sensor mask 1 is 0, but 3 & 6 is 2'


def test_a_contact_begins_once_and_again_only_after_parting():
    scene = Scene()
    d = _Delegate()
    scene.physicsWorld.contactDelegate = d
    a = _body_node(scene, 'a', physics.bodyWithRectangleOfSize((10, 10)), 2, 6, (0, 0))
    _body_node(scene, 'b', physics.bodyWithCircleOfRadius(5), 0, 7, (0, 100))
    scene.frame(0.0)
    assert d.contacts == []
    a.runAction(A.moveToY(100, 1.0))
    _run(scene, 1.0, 0.05)
    assert d.contacts == [('a', 'b')]
    a.runAction(A.sequence([A.moveToY(0, 0.5), A.moveToY(100, 0.5)]))
    _run(scene, 2.0, 0.05, start=1.0)
    assert d.contacts == [('a', 'b'), ('a', 'b')]


def test_bodies_that_do_not_test_never_report():
    scene = Scene()
    d = _Delegate()
    scene.physicsWorld.contactDelegate = d
    _body_node(scene, 'a', physics.bodyWithCircleOfRadius(5), 2, 0, (0, 0))
    _body_node(scene, 'b', physics.bodyWithCircleOfRadius(5), 4, 0, (0, 0))
    scene.frame(0.0)
    assert d.contacts == []


def test_a_body_removed_in_a_contact_is_not_reported_again():
    scene = Scene()

    class D(_Delegate):
        def didBeginContact(self, contact):
            super().didBeginContact(contact)
            contact.bodyB.node.removeFromParent()

    d = D()
    scene.physicsWorld.contactDelegate = d
    _body_node(scene, 'player', physics.bodyWithCircleOfRadius(10), 2, 6, (0, 0))
    _body_node(scene, 'coin', physics.bodyWithCircleOfRadius(10), 7, 3, (0, 0))
    _body_node(scene, 'coin2', physics.bodyWithCircleOfRadius(10), 7, 3, (5, 0))
    scene.frame(0.0)
    scene.frame(0.1)
    assert d.contacts == [('player', 'coin'), ('player', 'coin2')], d.contacts


def test_a_monster_reaches_the_roar_sensor_where_its_bodies_meet():
    """The sensor: the missing image, xScale W x 0.007, yScale 0.005, at 0.07 H, its whole
    size as its body (0x10000c3d8..0x10000c494).  A monster: scale W x 0.0013, half its
    size as a body, centred 22 below (0x10000cc64), from 0.5 H down in 4 s.  The roar
    begins when the monster's body bottom meets the sensor's top."""
    scene = Scene()
    d = _Delegate()
    scene.physicsWorld.contactDelegate = d
    sensor = SpriteNode('', name='sensor')
    sensor.xScale, sensor.yScale = W * 0.007, 0.005
    sensor.position = (0, H * 0.07)
    sensor.physicsBody = physics.bodyWithRectangleOfSize(sensor.size)
    sensor.physicsBody.categoryBitMask, sensor.physicsBody.contactTestBitMask = 3, 1
    scene.addChild(sensor)
    m = SpriteNode('monstroPedra', name='monster')
    m.setScale(W * 0.0013)
    m.position = (0.3 * W, 0.5 * H)
    w, h = m.size
    m.physicsBody = physics.bodyWithRectangleOfSize((w * 0.5, h * 0.5), center=(0, -22))
    m.physicsBody.categoryBitMask, m.physicsBody.contactTestBitMask = 0, 7
    scene.addChild(m)
    hit = []

    class D(_Delegate):
        def didBeginContact(self, contact):
            hit.append(scene.time)

    scene.physicsWorld.contactDelegate = D()
    scene.frame(0.0)
    m.runAction(A.moveToY(-0.5 * H, 4.0))
    _run(scene, 4.0, 1 / 120.0)
    assert len(hit) == 1, hit
    sensor_top = H * 0.07 + 128 * 0.005 / 2
    y_meet = sensor_top + 22 + h * 0.25
    expected = (0.5 * H - y_meet) / (H / 4.0)
    assert abs(hit[0] - expected) <= 1 / 120.0 + 1e-9, (hit[0], expected)


# ---- sound -----------------------------------------------------------------------------

def _audio_scene():
    paths.set_game(None)
    al = openal.AL()
    al.open()
    engine = AudioEngine(al, sound.SoundBank(al))
    scene = Scene(audio=engine)
    player = Node('player')
    player.position = (0, -0.25 * H)
    scene.addChild(player)
    scene.listener = player
    return scene, al, engine


def test_the_roar_is_placed_in_its_lane():
    scene, al, engine = _audio_scene()
    try:
        roar = AudioNode('Rugido.mp3')
        roar.autoplayLooped = False
        scene.addChild(roar)
        roar.position = (-0.3 * W, 0.07 * H)
        roar.runAction(A.changeVolumeTo(3.0, 0))
        roar.runAction(A.play())
        scene.frame(0.0)
        x, y, z = al.source_position(roar.source)
        assert _close(x, -1.0, 1e-5) and z < 0 and y == 0, (x, y, z)
        assert _close(al.source_float(roar.source, openal.AL_GAIN), 3.0, 1e-6)
        assert al.source_float(roar.source, openal.AL_MAX_GAIN) >= 3.0
        assert al.source_state(roar.source) == openal.AL_PLAYING
        scene.listener.position = (-0.3 * W, -0.25 * H)        # the player moves left
        scene.frame(0.1)
        x, _y, _z = al.source_position(roar.source)
        assert _close(x, 0.0, 1e-5), x
    finally:
        engine.release()
        al.close()


def test_only_the_placed_sounds_are_mixed_to_mono():
    scene, al, engine = _audio_scene()
    try:
        for name, want in (('Rugido.mp3', 1), ('BatSound.wav', 1), ('tilintar.aiff', 1),
                           ('tocha.wav', 2), ('lancar_tocha.wav', 2)):
            node = AudioNode(name)
            node.autoplayLooped = False
            scene.addChild(node)
            got = engine.bank._buffers[(paths.base_name(name), want == 1)][1].channels
            assert got == want, (name, got)
    finally:
        engine.release()
        al.close()


def test_a_looped_node_plays_as_soon_as_it_joins():
    """SKAudioNode's autoplayLooped is on unless the game turns it off."""
    scene, al, engine = _audio_scene()
    try:
        music = AudioNode('SC.wav')
        scene.addChild(music)
        assert music.playing and al.source_state(music.source) == openal.AL_PLAYING
        music.removeFromParent()
        assert music.source == 0 and not engine.nodes
    finally:
        engine.release()
        al.close()


def test_a_one_shot_plays_unplaced_and_waits_when_asked():
    scene, al, engine = _audio_scene()
    try:
        n = Node()
        scene.addChild(n)
        done = []
        n.runAction(A.sequence([A.playSoundFileNamed('MovimentoProibido.wav', True),
                                A.runBlock(lambda: done.append(scene.action_now))]))
        scene.frame(0.0)
        assert len(engine._one_shots) == 1
        _run(scene, 1.0, 0.05)
        assert done and _close(done[0], 0.62, 0.01), done
    finally:
        engine.release()
        al.close()


def test_pausing_stops_every_sound_and_resuming_starts_them():
    scene, al, engine = _audio_scene()
    try:
        music = AudioNode('SC.wav')
        scene.addChild(music)
        scene.pause_all()
        assert al.source_state(music.source) == openal.AL_PAUSED
        scene.resume_all()
        assert al.source_state(music.source) == openal.AL_PLAYING
    finally:
        engine.release()
        al.close()


if __name__ == '__main__':
    _scratch_save.run(globals())
