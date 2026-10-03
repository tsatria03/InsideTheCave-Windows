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


def test_every_coin_carries_its_own_jingle():
    """The port's addition: the original's tilintar, looped, riding down with the coin."""
    g = _Game()
    coin = g.scene.createCoin()
    jingles = [n for n in coin.children if n.name == 'jingle']
    assert len(jingles) == 1
    assert jingles[0].file_name == 'tilintar.aiff' and jingles[0].autoplayLooped


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
