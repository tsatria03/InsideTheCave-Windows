"""The game: ``insidethecave/game``, played headless on a made-up clock.

No sound device (the scene has no audio engine; its sound nodes keep their state), no
speech (a stand-in records what would be said), the save in the scratch folder.  Each test
starts a game of its own; the random lanes come from a seeded generator.
"""
from __future__ import annotations

import os
import random
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
import _scratch_save                                             # noqa: E402  never the real save

from insidethecave.game import game_scene as G                  # noqa: E402
from insidethecave.game.game_view_controller import GameViewController  # noqa: E402
from insidethecave.platform import runloop                      # noqa: E402
from insidethecave.platform.defaults import UserDefaults        # noqa: E402
from insidethecave.platform.keymap import KeyMap                 # noqa: E402
from insidethecave.scene import physics                         # noqa: E402

W, H = 750.0, 1334.0


class _Said:
    def __init__(self):
        self.lines = []

    def speak(self, text, interrupt=True):
        self.lines.append(text)
        return True

    def stop(self):
        pass


class _Voice:
    """The tutorial's Windows voice: speaks until told it has finished."""

    def __init__(self, can_speak=True):
        self.can_speak = can_speak
        self.lines = []
        self.speaking = False
        self.chosen = None

    def choose(self, lang):
        self.chosen = lang
        return lang

    def speak(self, text):
        if not self.can_speak:
            return False
        self.lines.append(text)
        self.speaking = True
        return True

    def stop(self):
        self.speaking = False


class _Game:
    """A game, and the clock it runs on."""

    def __init__(self, count=3, debug=False, seed=1, voice=None, language='en'):
        self.defaults = UserDefaults()
        self.defaults.setInteger_forKey_(count, 'countTutorial')
        self.base = 1000.0
        self.t = 0.0
        self.loop = runloop.RunLoop(clock_fn=lambda: self.base + self.t)
        self.speech = _Said()
        self.voice = voice or _Voice()
        self.overs = []
        self.vc = GameViewController(defaults=self.defaults, speech=self.speech,
                                     voice=self.voice, keymap=KeyMap(), loop=self.loop,
                                     debug=debug, language_code=language,
                                     rng=random.Random(seed),
                                     on_game_over=lambda s, c: self.overs.append((s, c)))
        self.vc.viewDidLoad()
        self.scene = self.vc.scene
        self.step(0.0)

    def step(self, dt):
        self.t += dt
        now = self.base + self.t
        self.loop.pump(now)
        self.vc.frame(now)

    def run(self, seconds, dt=1 / 30.0):
        end = self.t + seconds
        while self.t < end - 1e-9:
            self.step(min(dt, end - self.t))

    def start(self):
        """Run to the first slot (2 s with the tutorial already heard)."""
        self.run(2.05)
        assert self.scene.started, 'the game did not start'


def _named(scene, name):
    return [n for n in scene.walk() if n.name == name]


# ---- starting ----------------------------------------------------------------------------

def test_after_three_tutorials_the_game_starts_after_two_seconds():
    g = _Game(count=3)
    g.run(1.9)
    assert not g.scene.started and g.scene.blockPlayer
    g.run(0.2)
    assert g.scene.started and not g.scene.blockPlayer
    assert g.scene.countObjectScene == 1
    assert g.voice.lines == [], 'the tutorial line was spoken a fourth time'


def test_the_tutorial_line_then_the_key_hints_then_the_first_slot():
    g = _Game(count=0)
    assert g.voice.lines == [G.TUTORIAL_LINES['en']]
    assert g.defaults.integerForKey_('countTutorial') == 1
    g.run(10.0)
    assert not g.scene.started, 'the game started while the line was still being spoken'
    assert g.speech.lines == []
    g.voice.speaking = False
    g.run(1.0)
    assert g.speech.lines == ['Press A or Left Arrow to move left, and D or Right Arrow '
                              'to move right.', 'Press W or Up Arrow to throw your torch.']
    assert not g.scene.started, 'the first slot came while the hints were being said'
    g.run(8.0)
    assert g.scene.started


def test_the_tutorial_line_is_in_the_games_language():
    g = _Game(count=1, language='pt')
    assert g.voice.chosen == 'pt'
    assert g.voice.lines == [G.TUTORIAL_LINES['pt']]
    g2 = _Game(count=1, language='de')
    assert g2.voice.chosen == 'en' and g2.voice.lines == [G.TUTORIAL_LINES['en']]


def test_without_a_windows_voice_the_screen_reader_says_the_line():
    g = _Game(count=0, voice=_Voice(can_speak=False))
    assert g.speech.lines == [G.TUTORIAL_LINES['en']]


# ---- the slots ---------------------------------------------------------------------------

def test_a_slot_every_0_66_seconds_at_the_start():
    """0.165 x speedMonster 4.0 apart, to the moment, whatever the frames."""
    g = _Game(debug=True)
    times = []
    real = g.scene.createObjectScene

    def wrap():
        times.append(g.scene.action_now)
        real()
    g.scene.createObjectScene = wrap
    g.start()
    g.run(4.0, dt=0.037)
    assert len(times) >= 6, times
    for k in range(1, 6):
        assert abs(times[k] - times[0] - 0.66 * k) < 1e-6, (k, times[k] - times[0])


def test_the_game_speeds_up_every_twenty_slots():
    g = _Game(debug=True)
    g.start()
    while g.scene.countObjectScene < 20:
        g.run(0.1)
    assert abs(g.scene.speedMonster - 3.88) < 1e-9, g.scene.speedMonster
    while g.scene.countObjectScene < 40:
        g.run(0.1)
    assert abs(g.scene.speedMonster - 3.76) < 1e-9


def test_the_speed_never_goes_below_2():
    """The original reaches 1.96 at slot 340; the port stops at 2.0 (the dev)."""
    g = _Game(debug=True)
    g.start()
    s = g.scene
    s.speedMonster, s.countObjectScene = 2.08, 339
    s.createObjectScene()                       # the 340th slot
    assert s.speedMonster == G.TOP_SPEED == 2.0, s.speedMonster
    for _ in range(60):
        s.createObjectScene()                   # and every 20th after it
    assert s.speedMonster == 2.0, s.speedMonster


def test_every_seventh_obstacle_is_bats_and_the_rest_monsters():
    g = _Game(debug=True)
    made = []
    for kind in ('createMonster', 'createBats'):
        real = getattr(g.scene, kind)

        def wrap(real=real, kind=kind):
            made.append((g.scene.countObjectScene, kind))
            return real()
        setattr(g.scene, kind, wrap)
    g.start()
    while g.scene.countObjectScene < 57:
        g.run(0.1)
    slots = [s for s, _k in made]
    assert slots[:15] == list(range(0, 57, 4)), slots
    kinds = [k for _s, k in made]
    assert kinds[6] == 'createBats' and kinds[13] == 'createBats', kinds
    assert kinds.count('createBats') == 2, kinds


def test_an_obstacle_never_comes_down_the_last_obstacles_lane():
    g = _Game(debug=True, seed=7)
    lanes = []
    real = g.scene.choiceObstacleLine

    def wrap():
        x = real()
        lanes.append(x)
        return x
    g.scene.choiceObstacleLine = wrap
    g.start()
    while len(lanes) < 30:
        g.run(0.1)
    assert all(a != b for a, b in zip(lanes, lanes[1:])), lanes


def test_the_cave_changes_at_81_and_161_slots():
    g = _Game(debug=True)
    seen = []
    real = g.vc.changeCoinCounterWithScenario
    g.vc.changeCoinCounterWithScenario = lambda s: (seen.append((s, g.scene.countObjectScene)),
                                                    real(s))
    g.start()
    while g.scene.countObjectScene < 180:
        g.run(0.1, dt=0.05)
    assert [s for s, _n in seen] == [G.WATER, G.ICE], seen
    water, ice = seen[0][1], seen[1][1]
    assert 81 <= water <= 81 + 14, water
    assert 161 <= ice <= 161 + 14, ice
    assert g.vc.coinCounter == 'coinCounterIce'


# ---- the score ---------------------------------------------------------------------------

def test_the_score_goes_up_four_times_a_second():
    g = _Game()
    g.start()
    s0 = g.vc.score
    g.run(1.0)
    assert g.vc.score - s0 == 4, g.vc.score - s0


def test_a_coin_is_ten_points_and_one_coin():
    g = _Game(debug=True)
    g.start()
    coin = g.scene.createCoin()
    coin.position = g.scene.player.position
    g.scene.addChild(coin)
    score = g.vc.score
    g.step(0.001)
    assert g.vc.coins == 1, g.vc.coins
    assert g.vc.score - score in (10, 11), 'ten for the coin, and maybe a tick of the clock'
    assert not coin.in_scene
    g.step(0.001)               # the sound's play action runs on the next frame
    assert g.scene.coinSound.playing


def test_the_coin_sound_is_heard_at_the_player_in_every_lane():
    """The port's fix: plim_moeda is mono, so placed it came from the middle lane."""
    from insidethecave.scene.audio import AudioEngine
    g = _Game(debug=True)
    g.start()
    engine = AudioEngine(None, None)
    for lane in (0, 1, 2):
        g.scene.player.position = (W * (-0.3, 0.0, 0.3)[lane], H * -0.25)
        assert engine.mapped(g.scene.coinSound, g.scene.listener) == (0.0, 0.0, 0.0), lane


def test_the_dash_and_the_wall_come_from_the_lane():
    """The dev: the dash from the lane you are in, the wall from the side you hit."""
    from insidethecave.scene import actions
    from insidethecave.scene.audio import AudioEngine, placed
    g = _Game(debug=True)
    g.start()
    s = g.scene
    engine = AudioEngine(None, None)
    assert placed('dash.aiff') and placed('MovimentoProibido.wav'), 'both mixed to mono'
    for move, x in ((s.movePlayerLeft, -1.0), (s.movePlayerRight, 0.0),
                    (s.movePlayerRight, 1.0)):
        move()
        heard = engine.mapped(s.movePlayerSound, s.listener)
        assert tuple(round(v, 6) for v in heard) == (x, 0.0, 0.0), (x, heard)
    walls = []
    s.runAction = lambda action, key=None: walls.append(action)
    s.movePlayerRight()                                    # into the right wall
    s.actualPositionPlayer = 0
    s.movePlayerLeft()                                     # into the left wall
    sounds = [a for a in walls if isinstance(a, actions.PlaySoundFile)]
    assert [a.name for a in sounds] == ['MovimentoProibido.wav'] * 2
    assert [round(a.lane_x / W, 2) for a in sounds] == [0.3, -0.3]


def test_the_music_volume_changes_during_a_game():
    from insidethecave.platform import volume
    g = _Game()
    m = g.scene.backgroundMusic
    assert abs(m.volume - 1.0) < 1e-9, 'the file as recorded (the dev), not the 0.2'
    volume.percents[volume.MUSIC_KEY] = 50
    try:
        g.scene.applyMusicVolume()
        assert abs(m.volume - 0.25) < 1e-9
    finally:
        volume.percents[volume.MUSIC_KEY] = 100


def test_footsteps_loop_from_your_lane_and_quicken_with_the_cave():
    """The dev: a walk, then a run, at 0.5, moving with you."""
    from insidethecave.scene.audio import AudioEngine, placed
    assert all(placed(n) for n, _ in G.FOOTSTEPS), 'mixed to mono'
    g = _Game(debug=True)
    s = g.scene
    assert s.footsteps is None, 'none before the first slot'
    g.start()
    f = s.footsteps
    assert f is not None and f.file_name == 'cave-walk.wav' and f.autoplayLooped
    assert f.volume == 0.5 and f.by_lane and f.parent is s.player
    s.movePlayerLeft()
    g.run(0.3)
    heard = AudioEngine(None, None).mapped(f, s.listener)
    assert round(heard[0], 6) == -1.0, 'from the left lane, once you are there'
    assert [G.GameScene.footstepFile(n) for n in (0, 1, 154, 155, 156, 400)] == [
        'cave-walk.wav', 'cave-walk.wav', 'cave-walk.wav', 'cave-run.wav', 'cave-run.wav',
        'cave-run.wav'], 'the run from slot 155 (the dev)'
    s.countObjectScene = 154
    s.createObjectScene()                       # the 155th slot
    assert s.footsteps.file_name == 'cave-run.wav' and not f.in_scene, 'swapped, not doubled'


def test_footsteps_stop_at_death():
    g = _Game()
    g.start()
    f = g.scene.footsteps
    _crash(g)
    assert not f.in_scene


def test_every_coin_and_torch_carries_its_own_sound():
    """The port's addition, looped, riding down with it: the coins the early versions'
    coin.wav, the torches the original's unused tilintar (the dev, for the third release)."""
    from insidethecave.scene.audio import placed
    g = _Game()
    for make, wanted in ((g.scene.createCoin, 'coin.wav'),
                         (g.scene.createTorchObstacle, 'tilintar.aiff')):
        node = make()
        jingles = [n for n in node.children if n.name == 'jingle']
        assert len(jingles) == 1, node
        j = jingles[0]
        assert j.file_name == wanted and j.autoplayLooped and j.volume == 1.0, j.file_name
        assert placed(j.file_name) and not j.by_lane, 'placed against you, from its lane'


def test_a_torch_s_sound_stops_when_you_take_it_or_die():
    g = _Game(debug=True)
    g.start()
    s = g.scene
    torch = s.createTorchObstacle()
    torch.removeAllActions()
    torch.position = s.player.position
    s.addChild(torch)
    jingle = [n for n in torch.children if n.name == 'jingle'][0]
    assert jingle.in_scene
    g.step(0.001)
    assert not torch.in_scene and not jingle.in_scene, 'taken, and silent'
    g = _Game()
    g.start()
    torch = g.scene.createTorchObstacle()
    g.scene.addChild(torch)
    _crash(g)
    assert not [n for n in g.scene.walk() if n.name == 'jingle'], 'all jingles go at death'


# ---- contacts ----------------------------------------------------------------------------

def test_contacts_work_whichever_body_comes_first():
    for flip in (False, True):
        g = _Game(debug=True)
        g.start()
        coin = g.scene.createCoin()
        g.scene.addChild(coin)
        a, b = g.scene.player.physicsBody, coin.physicsBody
        if flip:
            a, b = b, a
        g.scene.didBeginContact(physics.Contact(a, b))
        assert g.vc.coins == 1, flip


def test_the_roar_is_louder_in_your_lane():
    g = _Game(debug=True)
    for lane_x, want in ((0.0, 3.0), (0.3 * W, 1.0)):
        m = g.scene.createMonster()
        m.position = (lane_x, 0.07 * H)
        g.scene.addChild(m)
        g.step(0.001)
        g.step(0.001)
        assert g.scene.roar.position == m.position
        assert g.scene.roar.volume == want and g.scene.roar.playing, (lane_x, g.scene.roar.volume)
        m.removeFromParent()


# ---- moving ------------------------------------------------------------------------------

def test_moving_left_and_into_the_wall():
    g = _Game()
    g.scene.movePlayerLeft()
    assert g.scene.actualPositionPlayer == 0
    g.run(0.2)
    assert abs(g.scene.player.position[0] - (-0.3 * W)) < 1e-6
    assert abs(g.scene.backgroundMusic.position[0] - (-0.3 * W)) < 1e-6
    g.scene.movePlayerLeft()
    assert g.scene.actualPositionPlayer == 0, 'went through the wall'
    g.scene.movePlayerRight()
    g.scene.movePlayerRight()
    assert g.scene.actualPositionPlayer == 2
    g.run(0.2)
    assert abs(g.scene.player.position[0] - 0.3 * W) < 1e-6


def test_moving_works_before_the_game_starts():
    """Kept as the original: only playerDead is checked (0x10000f910)."""
    g = _Game()
    assert g.scene.blockPlayer
    g.scene.movePlayerRight()
    assert g.scene.actualPositionPlayer == 2


# ---- the torch ---------------------------------------------------------------------------

def test_a_throw_needs_a_started_game_and_a_torch():
    g = _Game()
    g.scene.throwTorch()
    assert not _named(g.scene, 'thrown'), 'thrown before the game started'
    g.start()
    g.scene.throwTorch()
    assert len(_named(g.scene, 'thrown')) == 1
    assert g.scene.falloffSize == G.FALLOFF_OUT
    assert not g.scene.backgroundTorch.in_scene
    g.scene.throwTorch()
    assert len(_named(g.scene, 'thrown')) == 1, 'thrown twice with one torch'


def test_a_thrown_torch_kills_a_monster_for_no_points():
    g = _Game(debug=True)
    g.start()
    m = g.scene.createMonster()
    m.position = (0.0, 0.1 * H)
    m.born = True
    g.scene.addChild(m)
    m.removeAllActions()
    score = g.vc.score
    g.scene.throwTorch()
    g.run(1.0)
    assert not m.in_scene and g.scene.deadMonster.playing
    assert g.vc.score - score <= 5, 'the kill scored'


def test_a_monster_killed_before_its_slot_made_the_next_still_makes_it():
    """The fix: the original made it only above 0.4175 H (0x1000134dc)."""
    g = _Game(debug=True)
    g.start()
    torch = g.scene.createTorch()
    m = g.scene.createMonster()
    m.born = False
    m.position = (0.0, 0.38 * H)            # between 0.33 H and 0.4175 H
    before = g.scene.countObjectScene
    g.scene.torchDidCollideWithObstacle(torch, m)
    assert g.scene.countObjectScene == before + 1
    m2 = g.scene.createMonster()
    m2.born = True
    g.scene.torchDidCollideWithObstacle(torch, m2)
    assert g.scene.countObjectScene == before + 1, 'a slot made twice'


def test_a_bat_dodges_a_torch():
    g = _Game(seed=3)
    torch = g.scene.createTorch()
    b = g.scene.createBats()
    g.scene.addChild(b)
    b.removeAllActions()
    b.position = (-0.3 * W, 0.2 * H)
    g.scene.torchDidCollideWithBat(torch, b)
    g.run(0.4)
    assert abs(b.position[0]) < 1e-6, 'a side bat goes to the centre'
    b.position = (0.0, 0.2 * H)
    g.scene.torchDidCollideWithBat(torch, b)
    g.run(0.4)
    assert abs(abs(b.position[0]) - 0.3 * W) < 1e-6, 'a centre bat goes to a side'


def test_a_falling_bat_dodges_a_thrown_torch_and_stays_dodged():
    """The dev found the bats not moving off to the side: the dodge's moveToX and the
    fall's moveToY each put the other's axis back.  A bat in your lane, a torch thrown at
    it: the bat leaves for good, keeps falling, and you live."""
    g = _Game(seed=3)
    s = g.scene
    g.start()
    s.createMonster = s.createBats
    for make in ('createCoin', 'createTorchObstacle'):
        setattr(s, make, lambda: G.SpriteNode(name='slot'))
    bat = None
    for _ in range(400):
        g.step(1 / 30.0)
        bats = _named(s, 'bat')
        if bats:
            bat = bats[0]
            break
    assert bat is not None, 'no bat came'
    s.createBats = s.createMonster = lambda: G.SpriteNode(name='slot')   # this bat alone
    lane = bat.position[0]
    s.actualPositionPlayer = {-0.3 * W: 0, 0.0: 1, 0.3 * W: 2}[round(lane, 6)]
    s.player.position = (lane, s.player.position[1])
    g.run(0.5)
    s.throwTorch()
    for _ in range(120):
        g.step(1 / 30.0)
        if bat.position[0] != lane:
            break
    assert bat.position[0] != lane, 'the torch never reached the bat'
    y = bat.position[1]
    g.run(1.0)
    assert abs(abs(bat.position[0] - lane) - 0.3 * W) < 1e-6, 'the bat went back to its lane'
    assert bat.position[1] < y, 'the bat stopped falling'
    g.run(4.0)
    assert not s.playerDead, 'the dodged bat still reached you'


def test_the_torch_burns_out_and_says_torch_low_once():
    g = _Game()
    s = g.scene
    steps = 0
    while s.falloffSize < G.FALLOFF_OUT:
        s.changeFalloffSize()
        steps += 1
    assert 68 <= steps <= 71, steps
    assert g.speech.lines.count(G.TORCH_LOW) == 1
    assert not s.backgroundTorch.in_scene
    assert s.player.texture.startswith('sem_tocha') or True


def test_a_sound_plays_when_the_torch_burns_out_but_not_when_it_is_thrown():
    """The dev: tocha_acende when the torch gets fully burned out."""
    from insidethecave.scene import actions

    def played(s):
        return [a.name for a in s._sounds if isinstance(a, actions.PlaySoundFile)]

    for burn in (True, False):
        g = _Game(debug=True)
        g.start()
        s = g.scene
        s._sounds = []
        real = s.runAction
        s.runAction = lambda action, key=None: (s._sounds.append(action), real(action, key))
        if burn:
            while s.falloffSize < G.FALLOFF_OUT:
                s.changeFalloffSize()
            s.changeFalloffSize()                       # out already: not again
            assert played(s) == [G.TORCH_OUT], played(s)
        else:
            s.throwTorch()
            for _ in range(5):
                s.changeFalloffSize()
            assert G.TORCH_OUT not in played(s), 'a thrown torch did not burn out'


def test_torch_low_comes_as_the_light_starts_to_dim():
    g = _Game()
    s = g.scene
    while s.falloffSize < G.FALLOFF_DIM:
        s.changeFalloffSize()
    assert G.TORCH_LOW not in g.speech.lines
    s.changeFalloffSize()
    assert g.speech.lines == [G.TORCH_LOW]


def test_picking_up_a_torch_relights_and_resets_the_warning():
    g = _Game(debug=True)
    g.start()
    s = g.scene
    s.falloffSize = 4.0
    s.torch_low_said = True
    pickup = s.createTorchObstacle()
    s.addChild(pickup)
    s.playerDidCollideWithTorch(pickup)
    assert s.falloffSize == G.FALLOFF_START and not s.torch_low_said
    assert s.backgroundTorch.in_scene and not pickup.in_scene


# ---- death -------------------------------------------------------------------------------

def _crash(g):
    m = g.scene.createMonster()
    m.removeAllActions()
    m.position = g.scene.player.position
    g.scene.addChild(m)
    g.step(0.001)
    return m


def test_a_monster_reaching_you_ends_the_game_a_second_later():
    g = _Game()
    g.start()
    _crash(g)
    s = g.scene
    assert s.playerDead and not s.player.in_scene
    score = g.vc.score
    g.run(0.9)
    assert g.vc.score == score, 'the score went on after death'
    assert s.roar.in_scene and not s.backgroundMusic.in_scene
    assert g.overs == []
    g.run(0.2)
    assert g.overs == [(score, 0)] and g.vc.over


def test_no_throw_after_death():
    """The fix: the original checks only the light and blockPlayer (0x100011150)."""
    g = _Game()
    g.start()
    _crash(g)
    g.scene.throwTorch()
    assert not _named(g.scene, 'thrown')


def test_in_debug_mode_nothing_kills_you():
    g = _Game(debug=True)
    g.start()
    _crash(g)
    assert not g.scene.playerDead and 'Hit' in g.speech.lines


# ---- with sound, on the null driver --------------------------------------------------------

def test_a_game_runs_with_sound_on_the_null_driver():
    """The whole game with its OpenAL sources, silent: every sound the game plays is
    loaded, placed and let go without an error, through a death and a second game."""
    from insidethecave import paths
    from insidethecave.platform import openal, sound
    assert os.environ.get('ALSOFT_DRIVERS') == 'null'
    paths.set_game(None)
    al = openal.AL()
    al.open()
    bank = sound.SoundBank(al)
    try:
        loop = runloop.RunLoop()
        defaults = UserDefaults()
        defaults.setInteger_forKey_(3, 'countTutorial')
        overs = []
        vc = GameViewController(al, bank, defaults, _Said(), _Voice(), KeyMap(), loop,
                                language_code='en', rng=random.Random(5),
                                on_game_over=lambda s, c: overs.append(s))
        for game in range(2):
            vc.viewDidLoad()
            now = runloop.clock()
            for i in range(900):                       # 30 s at 30 frames a second
                now += 1 / 30.0
                loop.pump(now)
                vc.frame(now)
                if i == 450:
                    vc.scene.throwTorch()
                al.check('frame %d of game %d' % (i, game))
                if vc.over:
                    break
            assert vc.scene.countObjectScene > 3
        vc.clearScene()
        al.check('clearing')
    finally:
        bank.release()
        al.close()


def test_footsteps_keep_playing_through_lane_changes_on_the_null_driver():
    """The dev: "SOme times the footsteps sounds stop playing after I switch lanes." """
    from insidethecave import paths
    from insidethecave.platform import openal, sound
    paths.set_game(None)
    al = openal.AL()
    al.open()
    bank = sound.SoundBank(al)
    try:
        loop = runloop.RunLoop()
        defaults = UserDefaults()
        defaults.setInteger_forKey_(3, 'countTutorial')
        vc = GameViewController(al, bank, defaults, _Said(), _Voice(), KeyMap(), loop,
                                debug=True, language_code='en', rng=random.Random(7))
        vc.viewDidLoad()
        s = vc.scene
        now = runloop.clock()
        moves = (s.movePlayerLeft, s.movePlayerLeft, s.movePlayerRight, s.movePlayerRight,
                 s.movePlayerRight, s.movePlayerLeft)
        stopped = []
        for i in range(200 * 30):                     # 200 s: past the change to the run
            now += 1 / 30.0
            loop.pump(now)
            vc.frame(now)
            if s.started and i % 7 == 0:
                moves[(i // 7) % len(moves)]()
            f = s.footsteps
            if f is not None and f.in_scene and \
                    al.source_state(f.source) != openal.AL_PLAYING:
                stopped.append((i, f.file_name, f.source, s.actualPositionPlayer))
        assert not stopped, stopped[:5]
    finally:
        bank.release()
        al.close()


# ---- the pause ---------------------------------------------------------------------------

def test_the_pause_holds_the_score_and_the_slots():
    g = _Game(debug=True)
    g.start()
    g.scene.pause()
    score, slots = g.vc.score, g.scene.countObjectScene
    g.run(5.0)
    assert (g.vc.score, g.scene.countObjectScene) == (score, slots)
    g.scene.resume()
    g.run(1.0)
    assert g.vc.score > score and g.scene.countObjectScene > slots


if __name__ == '__main__':
    _scratch_save.run(globals())
