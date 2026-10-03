"""``GameScene``: the game.  Ported method by method from ``analysis/disasm/dz_GameScene.txt``;
each method names the address of its body (the Swift function its ``@objc`` thunk calls).

The scene is 750 by 1334 with (0, 0) at the centre; W and H below are its width and
height.  Three lanes at -0.3 W, 0 and 0.3 W; the player at (0, -0.25 H); things come down
from 0.5 H, one slot every 0.165 x ``speedMonster`` seconds (GAME_STRUCTURE.md sections
2 to 7).  Nothing runs per frame (``update:`` is empty, 0x10001561c): everything is actions,
contacts and four NSTimers.

What is not ported, because nothing of it can be heard: the light's colours and shadows
(``setLightTorch``), the snow that is never shown, the gesture recognisers (keys instead,
``ui/game_input.py``), and the scenery's textures changing with the scenario (the scenario's
name, which picks the monsters' and coins' looks, is kept).

The port's own changes, each in aidocks/DIVERGENCES.md:

* contacts are matched whichever body comes first (``didBeginContact``);
* a monster killed before its slot made the next one makes it then, so spawning never
  stops (``torchDidCollideWithObstacle``);
* no throw once the player is dead (``throwTorch``);
* every coin jingles as it comes (``createCoin``), the original's unused ``tilintar``;
* the coin's collect sound is heard at the player, not from the middle lane
  (``createNodesSounds``);
* the dash and the wall come from the lane, left, middle or right (``soundMovePlayer``,
  ``soundWall``), and the music's volume can change during a game (``applyMusicVolume``);
* "Torch low" is spoken as the torch starts to dim (``changeFalloffSize``);
* the tutorial line in a Windows voice, then the key hints, then the first slot
  (``tutorial``);
* the pause, and ``--debug``, where nothing can kill the player.
"""
from __future__ import annotations

import logging
import random

from ..platform import language, runloop, volume
from ..platform.defaults import COUNT_TUTORIAL_KEY
from ..scene import actions as A
from ..scene import physics
from ..scene.audio import AudioNode
from ..scene.node import Node, SpriteNode
from ..scene.scene import Scene

log = logging.getLogger('game')

# ---- the physics categories: plain numbers, compared with == (GAME_STRUCTURE.md 5) ------
MONSTER, BAT, PLAYER, SENSOR, THROWN_TORCH, TORCH_PICKUP, COIN = 0, 1, 2, 3, 4, 6, 7

# ---- the scenarios (currentScenario, 0x100015cdc; changeScenario 0x100011c20) -----------
ROCK, WATER, ICE = 'cenarioPedra', 'cenarioAgua', 'cenarioGelo'
WATER_AT, ICE_AT = 0x51, 0xa1          # countObjectScene: 81 (0x100011c50), 161 (0x100012180)

MONSTER_FRAMES = {ROCK: ('monstroPedra', 'monstroPedra2-1', 'monstroPedra2'),
                  WATER: ('monstroCristal', 'monstroCristal2-1', 'monstroCristal2'),
                  ICE: ('monstroGelo', 'monstroGelo2-1', 'monstroGelo2')}
COIN_LOOKS = {ROCK: 'rockCoin', WATER: 'waterCoin', ICE: 'iceCoin'}
DEAD_LOOKS = {ROCK: 'deadPedra.png', WATER: 'deadCristal.png', ICE: 'deadGelo.png'}
COUNTERS = {ROCK: 'coinCounterRock', WATER: 'coinCounterWater', ICE: 'coinCounterIce'}

# ---- the light (createLight 0x100023740, changeFalloffSize 0x100023a0c) -----------------
FALLOFF_START = 2.0                    # 0x100015ba0
FALLOFF_DIM = 3.0                      # 0x100023a2c
FALLOFF_LAST = 5.0                     # 0x100023aac, and throwTorch's guard 0x100011150
FALLOFF_OUT = 1000.0                   # 0x100023b64

# ---- the tutorial line (GameScene.tutorial 0x10000dea8; analysis/data/strings.txt) -------
TUTORIAL_LINES = {
    'en': 'You need to scape from a cave full of monsters on the way! When you hear the '
          'roar, swipe or tap to the other side!',                           # 0x100025260
    'pt': 'Voce precisa fugir da caverna desviando dos monstros de pedra no caminho! '
          'Quando ouvir o rugido, deslize ou toque para um dos lados!',      # 0x100025390
    'es': 'Usted necesita escapar de la cueva esquivando de los monstruos de piedra en el '
          'camino! Cuando se oye un ruido, deslice o toque hacia un lado',   # 0x1000252f0
    'zh': '你需要从洞穴跑出来， 小心路上有很多怪物！听到怪声，向左右滑动或是按另一边避免它',  # 0x10002b960
    'ru': 'Вам нужно выбраться из пещеры, заполненной монстрами! Когда услышите рык, '
          'проведите пальцем по экрану или нажмите на другой стороне!',     # 0x10002b850
    'fr': "Tu dois t'échaper d'une grote pleine de monstres. Quand tu entendras la bête "
          "rugir, glisse ou appuyes vers l'autre côté!",                      # 0x10002b750
}
#: PORT ADDITION: the key hints after the line, from the player's own bindings
#: (aidocks/project_port_plan.md, question 6).
KEY_HINTS = (('Press {move_left} to move left, and {move_right} to move right.',
              ('move_left', 'move_right')),
             ('Press {throw} to throw your torch.', ('throw',)))
#: How long a screen reader takes over the hints, which it cannot say: characters a second.
HINT_CHARS_PER_SECOND = 14.0
#: PORT ADDITION: what is said as the torch starts to dim (question 3).
TORCH_LOW = 'Torch low'
#: PORT ADDITION: the jingle each coin carries, at SpriteKit's default volume (question 4).
JINGLE_VOLUME = 1.0
#: The music's gain, before MUSICVOLUME.  The original's is 0.2 (``changeVolumeTo:0.2`` at
#: 0x100010a6c); PORT: 1.0, the file as recorded (the dev: "Please put the game music volume
#: to 1.0 as well. Again, I can turn that down as well."), turned down with Page Down.
MUSIC_GAIN = 1.0


class GameScene(Scene):
    """``GameScene``, an ``SKScene`` and its own ``SKPhysicsContactDelegate``."""

    def __init__(self, audio=None, delegate=None, speech=None, voice=None, keymap=None,
                 defaults=None, loop=None, language_code='en', rng=None, debug=False):
        super().__init__(audio=audio)
        self.gameSceneDelegate = delegate
        self.speech = speech
        self.voice = voice
        self.keymap = keymap
        self.defaults = defaults
        self.loop = loop or runloop.main_loop()
        self.language_code = language_code
        self.random = rng or random.Random()
        self.debug = debug
        self.init_fields()

    # ---- GameScene.initWithCoder: 0x100017154 (initWithSize: and init alike) ---------------
    def init_fields(self):
        W, H = self.size
        self.positionLaneZero, self.positionLaneOne, self.positionLaneTwo = -0.3, 0.0, 0.3
        self.actualPositionPlayer = 1
        self.player = SpriteNode('player', name='player')
        self.lightTorch = Node('lightTorch')                 # an SKLightNode; never drawn
        self.lightTorch.falloff = FALLOFF_START
        self.throwLightTorch = None
        self.positionLastObstacles = 0
        self.countObstacles = 1
        self.countSubObstacles = 1
        self.countObjectScene = 0
        self.objectHeight = 0
        self.playerDead = False
        self.blockPlayer = True
        self.positionX = 0.0
        self.speedMonster = 4.0                              # 0x1000157bc
        self.roar = AudioNode('Rugido.mp3')                  # 0x1000157d8
        self.batSound = AudioNode('BatSound.wav')
        self.coinTinkle = AudioNode('tilintar.aiff')
        self.coinSound = AudioNode('plim_moeda.wav')
        self.getTorchSound = AudioNode('pegou_tocha.wav')
        self.playTorchSound = AudioNode('lancar_tocha.wav')
        self.backgroundTorch = AudioNode('tocha.wav')
        self.backgroundMusic = AudioNode('SC.wav')           # used/game-music.wav (paths.RENAMED)
        self.movePlayerSound = AudioNode('dash.aiff')
        self.deadMonster = AudioNode('MonsterDead.mp3')
        self.falloffSize = FALLOFF_START                     # 0x100015ba0
        self.scenario0 = SpriteNode(ROCK, name='scenario0')
        self.scenario1 = SpriteNode(ROCK, name='scenario1')
        self.scenario2 = SpriteNode(ROCK, name='scenario2')
        self.currentScenario = ROCK                          # 0x100015cdc
        # the port's own state
        self.paused_by_player = False
        self.torch_low_said = False
        self.started = False

    # ---- helpers the binary inlines -----------------------------------------------------
    @property
    def W(self):
        return self.size[0]

    @property
    def H(self):
        return self.size[1]

    def arc4random_uniform(self, n):
        return self.random.randrange(n)

    def say(self, text, interrupt=True):
        if self.speech is not None:
            self.speech.speak(text, interrupt)

    def delegate(self, name, *args):
        d = self.gameSceneDelegate
        if d is not None:
            getattr(d, name)(*args)

    @staticmethod
    def _masked(body, category, collision, contact):
        body.categoryBitMask = category
        body.collisionBitMask = collision
        body.contactTestBitMask = contact
        return body

    # ---- GameScene.didMoveToView: 0x10001696c -------------------------------------------
    def didMoveToView(self):
        W, H = self.size
        self.physicsWorld.gravity = (0.0, 0.0)                         # 0x1000169c4
        self.physicsWorld.contactDelegate = self
        self.roar.positional = True                                    # 0x100016a24
        self.roar.autoplayLooped = False
        self.addChild(self.roar)
        self.listener = self.player                                    # 0x100016a78
        # the scenery: scenario0 the size of the scene, the other two riding on it
        self.scenario0.setSize((W, H))
        self.scenario0.position = (0.0, 0.0)
        self.addChild(self.scenario0)
        self.scenario1.setSize((W, H))
        self.scenario1.position = (0.0, H)
        self.scenario0.addChild(self.scenario1)
        self.scenario2.setSize((W, H))
        self.scenario2.position = (0.0, H + H)
        self.scenario0.addChild(self.scenario2)
        self.putScenario()                                             # 0x100016cfc
        self.createPlayer()
        self.createRoarSensor()
        self.createLight()
        self.createNodesSounds()
        self.tutorial()                                                # 0x100016d4c
        # the swipes and the tap are keys in the port (ui/game_input.py); the snow emitter
        # is made and never added (0x100017058..0x100017110), so it is left out

    # ---- -[GameScene createScene] 0x100015280 (never called by the game) -----------------
    def createScene(self):
        self.createPlayer()
        self.createRoarSensor()
        self.createLight()
        self.createNodesSounds()

    # ---- GameScene.createPlayer 0x10000be10 ---------------------------------------------
    def createPlayer(self):
        W, H = self.size
        p = self.player
        p.position = (W * 0.0, H * -0.25)                              # 0x10000be60..0x10000be90
        # the body from the player's size before changeSpritePlayer scales it
        p.physicsBody = self._masked(physics.bodyWithCircleOfRadius(p.size[0] * 0.5),
                                   PLAYER, 0, 6)                       # 0x10000bec8..0x10000c018
        p.zPosition = 10.0
        p.lightingBitMask = 1
        self.changeSpritePlayer(True)                                  # 0x10000c05c
        self.addChild(p)

    # ---- GameScene.changeSpritePlayer: 0x10000c0c0 -------------------------------------
    def changeSpritePlayer(self, withTorch):
        if self.playerDead:                                            # 0x10000c0e4
            return
        W = self.W
        p = self.player
        p.setScale(W * 0.0007)                                         # 0x10000c134
        p.removeAllActions()
        frames = (('player', 'player2', 'player3') if withTorch
                  else ('sem_tocha_1', 'sem_tocha_2', 'sem_tocha_3'))
        p.runAction(self.spriteThreeFrames(*frames))

    # ---- spriteThreeFramesWithImageOne:imageTwo:imageThree: 0x1000194fc ------------------
    @staticmethod
    def spriteThreeFrames(one, two, three):
        """Frames 1, 2, 3, 2 at 0.1 s, forever (helper 0x100019778, 0.1 at 0x100019998)."""
        return A.repeatActionForever(A.animateWithTextures([one, two, three, two], 0.1))

    # ---- spriteSixFramesWithImageOne:...imageSeven: 0x1000195e4 --------------------------
    @staticmethod
    def spriteSixFrames(*images):
        """Seven frames at 0.04 s, forever (helper 0x100019a24, 0.04 at 0x100019dbc)."""
        return A.repeatActionForever(A.animateWithTextures(list(images), 0.04))

    # ---- GameScene.createRoarSensor 0x10000c344 -----------------------------------------
    def createRoarSensor(self):
        W, H = self.size
        s = SpriteNode('', name='sensor')                              # the missing image
        s.xScale = W * 0.007                                           # 0x10000c3d8
        s.yScale = 0.005                                               # 0x10000c404
        s.position = (s.size[0] * 0.0, H * 0.07)                       # 0x10000c444
        s.physicsBody = self._masked(physics.bodyWithRectangleOfSize(s.size), SENSOR, 0, 1)
        s.physicsBody.allowsRotation = False
        s.alpha = 0.0
        self.addChild(s)

    # ---- GameScene.createObjectScene 0x10000c674 -----------------------------------------
    def createObjectScene(self):
        """One slot.  Every 4th an obstacle (a monster, every 7th obstacle bats), with a
        coin or a torch beside it when objectHeight is 4; otherwise a coin or a torch on
        the slot objectHeight picks, every 3rd obstacle round; otherwise an empty slot that
        only keeps the chain going.  Then the light dims a step, and every 20th slot the
        game speeds up while speedMonster is 2.0 or more."""
        s = self.countObjectScene
        slot = SpriteNode(name='slot')                                 # an empty sprite
        if s & 3 == 0:
            if self.countObstacles % 7 == 0:                           # 0x10000c760..0x10000c778
                node = self.createBats()
            else:
                node = self.createMonster()
            if self.objectHeight == 4:                                 # 0x10000c7c4
                if self.countSubObstacles & 3:
                    self.coinTogether()
                else:
                    self.torchTogether()
                self.countSubObstacles += 1
                self.objectHeight = 0
            else:
                self.objectHeight = self.coinRandom()                  # 0x10000c7f0
            self.addChild(node)
            node.runAction(self.moveObstacleWithBorn(node))
            self.countObstacles += 1                                   # 0x10000c888
        else:
            if (self.countObstacles % 3 == 0 and self.objectHeight <= 3
                    and s % 4 == self.objectHeight):                   # 0x10000c6dc..0x10000c720
                if self.countSubObstacles & 3:                         # 0x10000c730
                    slot = self.createCoin()
                else:
                    slot = self.createTorchObstacle()
                self.countSubObstacles += 1                            # 0x10000c8c0
            self.addChild(slot)                                        # 0x10000c8d4
            slot.runAction(self.moveObstacleWithBorn(slot))
        self.countObjectScene += 1                                     # 0x10000c93c
        self.changeFalloffSize()                                       # 0x10000c94c
        if self.countObjectScene % 20 == 0 and self.speedMonster >= 2.0:
            self.speedMonster += -0.12                                 # 0x10000c998

    # ---- -[GameScene coinTogether] / torchTogether, and their helper 0x10000ca0c ---------
    def coinTogether(self):
        self._together(self.createCoin)

    def torchTogether(self):
        self._together(self.createTorchObstacle)

    def _together(self, make):
        node = make()
        self.addChild(node)
        node.runAction(self.moveObstacle())                            # 0x10000caa0

    # ---- -[GameScene lineRandom] 0x1000116a4, coinRandom 0x1000116e0 ---------------------
    def lineRandom(self):
        return self.arc4random_uniform(3) + 1

    def coinRandom(self):
        return self.arc4random_uniform(4) + 1

    # ---- -[GameScene positionLineWithValue:] 0x10001171c --------------------------------
    @staticmethod
    def positionLineWithValue(value):
        return {1: -0.3, 2: 0.0}.get(value, 0.3)

    # ---- -[GameScene choiceObstacleLine] 0x100011744, choiceObstacleCoin 0x1000117c4 -----
    def choiceObstacleLine(self):
        """A lane other than the last obstacle's, kept as the last obstacle's."""
        while True:
            v = self.lineRandom()
            if v != self.positionLastObstacles:
                break
        self.positionLastObstacles = v
        return self.positionLineWithValue(v)

    def choiceObstacleCoin(self):
        """A lane other than the last obstacle's, not kept."""
        while True:
            v = self.lineRandom()
            if v != self.positionLastObstacles:
                return self.positionLineWithValue(v)

    # ---- -[GameScene positionFloat] 0x100014108 -----------------------------------------
    def positionFloat(self):
        return (-0.3, 0.0, 0.3)[self.actualPositionPlayer] \
            if 0 <= self.actualPositionPlayer <= 2 else 0.0

    # ---- what comes down ----------------------------------------------------------------
    def _obstacle(self, image, scale, choose, category, contact, center=True):
        """The shape the creators share: an image scaled by W, in a chosen lane at the top,
        its body half its size (centred 22 below it for the obstacles), z 10."""
        W, H = self.size
        n = SpriteNode(image)
        n.setScale(W * scale)
        n.position = (W * choose(), H * 0.5)
        n.zPosition = 10.0
        w, h = n.size
        if center:
            body = physics.bodyWithRectangleOfSize((w * 0.5, h * 0.5), center=(0.0, -22.0))
        else:
            body = physics.bodyWithRectangleOfSize((w * 0.5, h * 0.5))
        n.physicsBody = self._masked(body, category, 0, contact)
        return n

    # GameScene.createMonster 0x10000caf8
    def createMonster(self):
        m = self._obstacle('monstroPedra', 0.0013, self.choiceObstacleLine, MONSTER, 7)
        m.name = 'monster'
        m.lightingBitMask = 1
        frames = MONSTER_FRAMES.get(self.currentScenario, MONSTER_FRAMES[ROCK])
        m.runAction(self.spriteThreeFrames(*frames))
        return m

    # GameScene.createBats 0x10000d1b8
    def createBats(self):
        b = self._obstacle('morcego1', 0.0009, self.choiceObstacleLine, BAT, 7)
        b.name = 'bat'
        b.lightingBitMask = 1
        b.runAction(self.spriteThreeFrames('morcego1', 'morcego2', 'morcego3'))
        return b

    # GameScene.createTorchObstacle 0x10000d578
    def createTorchObstacle(self):
        t = self._obstacle('torchObstacle', 0.0009, self.choiceObstacleLine, TORCH_PICKUP, 2)
        t.name = 'torch'
        t.lightingBitMask = 0
        return t

    # GameScene.createCoin 0x10000d86c
    def createCoin(self):
        """A coin, its look by scenario; its size, and so its body, always rockCoin's
        (setTexture: keeps the size, 0x10000dc08).  PORT ADDITION: it carries its own
        jingle, looped, the original's unused tilintar (question 4)."""
        c = self._obstacle('rockCoin', 0.0008, self.choiceObstacleCoin, COIN, 3,
                           center=False)
        c.name = 'coin'
        c.texture = COIN_LOOKS.get(self.currentScenario, 'rockCoin')
        c.lightingBitMask = 1
        jingle = AudioNode('tilintar.aiff', name='jingle')
        jingle.volume = JINGLE_VOLUME
        c.addChild(jingle)
        return c

    # ---- the slots' movement ------------------------------------------------------------
    # GameScene.moveObstacleWithBorn 0x100013a5c
    def moveObstacleWithBorn(self, node=None):
        """Down to 0.33 H, where it makes the next slot, then on down and away; the whole
        height in speedMonster seconds (0.33 at 0x100013aec, 0.165 and 0.835 x speed)."""
        W, H = self.size
        speed = self.speedMonster

        def born():                                                    # closure 0x100014164
            if node is not None:
                node.born = True
            self.createObjectScene()

        if node is not None:
            node.born = False
        return A.sequence([A.moveToY(H * 0.33, speed * 0.165), A.runBlock(born),
                           A.moveToY(H * -0.5, speed * 0.835), A.removeFromParent()])

    # GameScene.moveObstacle 0x100013d5c
    def moveObstacle(self):
        H = self.H
        return A.sequence([A.moveToY(H * -0.5, self.speedMonster), A.removeFromParent()])

    # GameScene.moveCoinSound 0x100013f3c (never called by the original)
    def moveCoinSound(self):
        return A.sequence([A.moveToY(self.H * -0.5, 3.0), A.removeFromParent()])

    # ---- the scenery --------------------------------------------------------------------
    # -[GameScene putScenario] 0x100011b98
    def putScenario(self):
        self.scenario0.runAction(self.moveScenario())

    # GameScene.moveScenario 0x100011840
    def moveScenario(self):
        H = self.H
        return A.sequence([A.moveToY(H * -2.0, self.speedMonster + self.speedMonster),
                           A.moveToY(0.0, 0.0),
                           A.runBlock(self.putScenario),               # closure2 0x1000127bc
                           A.runBlock(self.changeScenario)])           # closure1 0x100012774

    # GameScene.changeScenario 0x100011c20
    def changeScenario(self):
        """Rock to water at 81 slots, water to ice at 161; the scenery's textures follow,
        which are not ported (nothing to hear)."""
        if self.countObjectScene >= WATER_AT and self.currentScenario == ROCK:
            self.currentScenario = WATER
            self.delegate('changeCoinCounterWithScenario', WATER)
        elif self.countObjectScene >= ICE_AT and self.currentScenario == WATER:
            self.currentScenario = ICE
            self.delegate('changeCoinCounterWithScenario', ICE)

    # ---- sounds -------------------------------------------------------------------------
    # GameScene.createNodesSounds 0x1000105b0
    def createNodesSounds(self):
        for node in (self.coinSound, self.getTorchSound, self.playTorchSound,
                     self.movePlayerSound, self.deadMonster):
            node.autoplayLooped = False
            self.addChild(node)
        # PORT: the coin's sound is the only mono one here, so OpenAL would place it at the
        # node's own (0, 0), the middle lane, whatever lane the coin was taken in.  Unplaced,
        # it is heard at the player, like the stereo pickup sounds beside it.
        self.coinSound.positional = False
        # PORT: the dash is placed by its lane, left, middle or right, not against the
        # player, who would always hear it in the middle (soundMovePlayer).
        self.movePlayerSound.by_lane = True
        for node in (self.coinTinkle, self.batSound):
            node.positional = True
            node.autoplayLooped = False
            self.addChild(node)
        self.createBackgroundTorch()
        self.createBackgroundMusic()

    # GameScene.removeNodesSounds 0x100010768
    def removeNodesSounds(self):
        for node in (self.coinSound, self.getTorchSound, self.playTorchSound,
                     self.movePlayerSound, self.deadMonster, self.backgroundTorch,
                     self.coinTinkle, self.batSound, self.backgroundMusic):
            node.removeFromParent()

    # GameScene.createBackgroundTorch 0x100010864
    def createBackgroundTorch(self):
        t = self.backgroundTorch
        t.removeFromParent()
        t.autoplayLooped = True
        self.addChild(t)
        t.runAction(A.play())
        t.runAction(A.changeVolumeTo(1.0, 3.0))                        # 0x100010930

    # GameScene.createBackgroundMusic 0x1000109a8
    def createBackgroundMusic(self):
        m = self.backgroundMusic
        m.autoplayLooped = True
        m.positional = True
        m.position = self.player.position
        target = volume.music(MUSIC_GAIN)
        m.set_volume(target)        # at once, not a frame late: no loud first instant
        m.runAction(A.changeVolumeTo(target, 0.0))
        self.addChild(m)

    def applyMusicVolume(self):
        """PORT ADDITION: Page Up or Page Down changed ``MUSICVOLUME``; heard at once."""
        self.backgroundMusic.set_volume(volume.music(MUSIC_GAIN))

    # GameScene.soundMovePlayer 0x10000fe30
    def soundMovePlayer(self, fraction=0.0):
        """PORT: the dash comes from the lane it ends in, left, middle or right, placed by
        the lane rather than against the player (the dev, for the second release)."""
        s = self.movePlayerSound
        s.position = (self.W * fraction, self.player.position[1])
        s.runAction(A.play())
        s.runAction(A.changeVolumeTo(0.25, 0.0))                       # 0x10000fec4

    def soundWall(self, fraction):
        """The wall: MovimentoProibido, one-shot (0x10000f988, 0x10000fc14).  PORT: placed on
        the side of the wall that was hit, where the original's was not placed."""
        self.runAction(A.playSoundFileNamed('MovimentoProibido.wav', False,
                                            lane_x=self.W * fraction))

    # GameScene.playMonsterRoarAtPoint: 0x10000f69c
    def playMonsterRoarAtPoint(self, point):
        self.roar.position = point
        here = point[0] == self.player.position[0]                     # 0x10000f738
        self.roar.runAction(A.changeVolumeTo(3.0 if here else 1.0, 0.0))
        self.roar.runAction(A.play())

    # GameScene.playBatSoundAtPoint: 0x10000f7c4
    def playBatSoundAtPoint(self, point):
        self.batSound.position = point
        here = point[0] == self.player.position[0]                     # 0x10000f854
        self.batSound.runAction(A.changeVolumeTo(3.0 if here else 0.7, 0.0))
        self.batSound.runAction(A.play())

    # ---- moving -------------------------------------------------------------------------
    # GameScene.movePlayerRight 0x10000f8e4
    def movePlayerRight(self):
        if self.playerDead:                                            # 0x10000f910
            return
        lane = self.actualPositionPlayer
        if lane == 0:
            self.actualPositionPlayer = 1
            x = 0.0
            self.soundMovePlayer(x)
        elif lane == 1:
            self.actualPositionPlayer = 2
            x = 0.3
            self.soundMovePlayer(x)
        elif lane == 2:
            self.actualPositionPlayer = 2
            x = 0.3
            self.soundWall(x)                                          # 0x10000f988
        else:
            x = 0.0
        self._move_to(x)

    # GameScene.movePlayerLeft 0x10000fb90
    def movePlayerLeft(self):
        if self.playerDead:                                            # 0x10000fbbc
            return
        lane = self.actualPositionPlayer
        if lane == 2:
            self.actualPositionPlayer = 1
            x = 0.0
            self.soundMovePlayer(x)
        elif lane == 1:
            self.actualPositionPlayer = 0
            x = -0.3
            self.soundMovePlayer(x)
        elif lane == 0:
            self.actualPositionPlayer = 0
            x = -0.3
            self.soundWall(x)                                          # 0x10000fc14
        else:
            x = 0.0
        self._move_to(x)

    def _move_to(self, fraction):
        """The player, the music and the light to the lane in 0.15 s (0x10000fa60..
        0x10000fb38), the light 0.072 W to the left of the player."""
        W = self.W
        move = A.moveToX(W * fraction, 0.15)
        self.player.runAction(move)
        self.backgroundMusic.runAction(move)
        self.lightTorch.runAction(A.moveToX(W * fraction + W * -0.072, 0.15))

    # -[GameScene movePlayerTap] 0x10000fff0: a tap left of W / 4 goes left, else right
    def movePlayerTap(self):
        if self.W * 0.25 < self.positionX:
            self.movePlayerRight()
        else:
            self.movePlayerLeft()

    # ---- the torch ----------------------------------------------------------------------
    # GameScene.createLight 0x100023740
    def createLight(self):
        W = self.W
        px, py = self.player.position
        self.lightTorch.position = (px + W * -0.072, py + W * 0.09)
        self.lightTorch.zPosition = 10.0
        self.lightTorch.categoryBitMask = 1
        self.lightTorch.falloff = self.falloffSize
        self.addChild(self.lightTorch)

    # GameScene.changeFalloffSize 0x100023a0c
    def changeFalloffSize(self):
        f = self.falloffSize
        if f < FALLOFF_DIM:
            self.falloffSize = f + 0.025
            self.lightTorch.falloff = self.falloffSize
            self.backgroundTorch.runAction(A.changeVolumeBy(-0.003, 0.0))
        elif f < FALLOFF_LAST:
            if not self.torch_low_said:                                # PORT ADDITION
                self.torch_low_said = True
                self.say(TORCH_LOW)
            self.falloffSize = f + 0.07
            self.lightTorch.falloff = self.falloffSize
            self.backgroundTorch.runAction(A.changeVolumeBy(-0.0045, 0.0))
        elif f != FALLOFF_OUT:
            self.falloffSize = FALLOFF_OUT
            self.lightTorch.falloff = FALLOFF_OUT
            self.changeSpritePlayer(False)
            self.backgroundTorch.removeFromParent()

    # GameScene.createTorch 0x100010b00
    def createTorch(self):
        W, H = self.size
        t = SpriteNode('Layer1', name='thrown')
        pw, ph = self.player.size
        t.position = (self.positionFloat() * W + pw * -0.3, H * -0.25 + ph * 0.5)
        t.setScale(W * 0.0007)
        t.physicsBody = self._masked(physics.bodyWithCircleOfRadius(t.size[0] + t.size[0]),
                                   THROWN_TORCH, 0, 0)                 # 0x100010ca8
        t.lightingBitMask = 1
        t.runAction(self.spriteSixFrames('Layer1', 'Layer2', 'Layer3', 'Layer4', 'Layer5',
                                         'Layer4', 'Layer6'))
        return t

    # GameScene.throwTorch 0x10001111c
    def throwTorch(self):
        if self.falloffSize >= FALLOFF_LAST or self.blockPlayer:      # 0x100011150, 0x100011164
            return
        if self.playerDead:
            return                  # PORT FIX: the original checks nothing of the kind
        self.backgroundTorch.removeFromParent()
        self.playTorchSound.runAction(A.play())
        self.playTorchSound.runAction(A.changeVolumeTo(1.3, 0.0))      # 0x100011234
        torch = self.createTorch()
        light = Node('throwLightTorch')
        light.position = self.lightTorch.position
        light.falloff = self.lightTorch.falloff
        self.throwLightTorch = light
        self.addChild(torch)
        self.addChild(light)
        self.falloffSize = FALLOFF_OUT                                 # 0x100011400
        self.lightTorch.falloff = FALLOFF_OUT
        fly = self.speedMonster * 0.5
        torch.runAction(A.sequence([A.moveToY(self.H, fly), A.removeFromParent()]))
        light.runAction(A.sequence([A.moveToY(self.H, fly), A.removeFromParent()]))
        self.changeSpritePlayer(False)

    # ---- contacts -----------------------------------------------------------------------
    # -[GameScene didBeginContact:]~closure1 0x100012984
    def didBeginContact(self, contact):
        """PORT FIX: each pair is matched whichever body comes first.  The original tests
        the roar and the bats both ways, but the coin, the thrown torch and the pickup one
        way only (0x100012d80..0x1000131c4); every handler gets its bodies in the order the
        original passes them, the higher category first."""
        a, b = contact.bodyA, contact.bodyB
        if a.node is None or b.node is None:
            return
        cats = {a.categoryBitMask: a, b.categoryBitMask: b}
        if len(cats) < 2:
            return

        def pair(c1, c2):
            if c1 in cats and c2 in cats:
                return cats[c1].node, cats[c2].node
            return None

        if (p := pair(SENSOR, MONSTER)):
            self.playMonsterRoarAtPoint(p[1].position)
        elif (p := pair(SENSOR, BAT)):
            self.playBatSoundAtPoint(p[1].position)
        elif (p := pair(COIN, PLAYER)):
            self.playerDidCollideWithCoin(p[0], p[1])
        elif (p := pair(THROWN_TORCH, MONSTER)):
            self.torchDidCollideWithObstacle(p[0], p[1])
        elif (p := pair(THROWN_TORCH, BAT)):
            self.torchDidCollideWithBat(p[0], p[1])
        elif (p := pair(TORCH_PICKUP, PLAYER)):
            self.playerDidCollideWithTorch(p[0])
        elif (p := pair(PLAYER, MONSTER)) or (p := pair(PLAYER, BAT)):
            self.obstacleDidCollideWithPlayer(p[0], p[1])

    # GameScene.playerDidCollideWithCoin:playerP: 0x10001390c
    def playerDidCollideWithCoin(self, coin, player):
        self.coinSound.runAction(A.play())
        self.coinSound.runAction(A.changeVolumeTo(0.2, 0.0))           # 0x1000139ac
        coin.removeFromParent()
        self.delegate('scoreUpWithValue', 10)                          # 0x100013a10
        self.delegate('coinUpWithValue', 1)

    # -[GameScene playerDidCollideWithTorch:]~closure1 0x1000137b8
    def playerDidCollideWithTorch(self, torch):
        self.getTorchSound.runAction(A.play())
        self.getTorchSound.runAction(A.changeVolumeTo(1.5, 0.0))       # 0x100013854
        self.createBackgroundTorch()
        torch.removeFromParent()
        self.falloffSize = FALLOFF_START                               # 0x1000138bc
        self.lightTorch.falloff = FALLOFF_START
        self.torch_low_said = False                                    # PORT: a new torch
        self.changeSpritePlayer(True)

    # GameScene.torchDidCollideWithObstacle:obstacleE: 0x1000133b8
    def torchDidCollideWithObstacle(self, torch, monster):
        """The monster dies.  The original makes the next slot here only when the monster
        is still at or above 0.4175 H (0x1000134dc..0x1000134f0), though its own action
        makes it at 0.33 H: one killed in between left the chain with no next slot and the
        cave went quiet for good.  PORT FIX: the next slot is made whenever the monster's
        own action has not made it yet."""
        self.deadMonster.runAction(A.play())
        self.deadMonster.runAction(A.changeVolumeTo(0.7, 0.0))         # 0x100013460
        if not getattr(monster, 'born', True):
            monster.born = True
            self.createObjectScene()
        torch.removeFromParent()
        monster.removeFromParent()
        if self.throwLightTorch is not None:
            self.throwLightTorch.removeFromParent()
        self.lightTorch.falloff = FALLOFF_OUT

    # GameScene.torchDidCollideWithBat:batB: 0x10001356c (it is handed only the bat)
    def torchDidCollideWithBat(self, torch, bat):
        """The bat dodges in 0.3 s: from the centre to a side at random, from a side to the
        centre.  The original prints the bat's x and W / 3 to its console here."""
        W = self.W
        log.debug('bat at %.1f, %.1f', bat.position[0], W / 3.0)
        if bat.position[0] == 0.0:                                     # 0x1000136f4
            fraction = -0.3 if self.arc4random_uniform(2) == 0 else 0.3
        else:
            fraction = 0.0
        bat.runAction(A.moveToX(fraction * W, 0.3))

    # GameScene.obstacleDidCollideWithPlayer:obstacleE: 0x1000230c4
    def obstacleDidCollideWithPlayer(self, player, obstacle):
        if self.debug:
            self.say('Hit')         # --debug: nothing kills the player
            return
        if self.playerDead:
            return
        W, H = self.size
        self.playerDead = True                                         # 0x1000230f4
        self.removeActionForKey('upScore')
        self.runAction(A.playSoundFileNamed('screamingMan.wav', False))
        self.player.removeFromParent()
        dead = SpriteNode(DEAD_LOOKS.get(self.currentScenario, DEAD_LOOKS[ROCK]), name='dead')
        dead.xScale = W * 0.0016                                       # 0x100023524
        dead.yScale = W * 0.0016
        dead.zPosition = 2.0
        dead.position = (obstacle.position[0], H * -0.25)
        self.addChild(dead)
        self.lightTorch.enabled = False
        self.removeNodesSounds()
        for node in self.walk():    # PORT: the coins' jingles go with the other sounds
            if isinstance(node, AudioNode) and node.name == 'jingle':
                node.removeFromParent()
        for s in (self.scenario0, self.scenario1, self.scenario2):
            s.paused = True
        self.loop.scheduledTimer(1.0, self, 'clear')                   # 0x1000236d8

    # -[GameScene clear] 0x100022fc8
    def clear(self):
        self.delegate('clearScene')
        self.delegate('gameOverDelegateFunc')

    # ---- starting -----------------------------------------------------------------------
    # GameScene.tutorial 0x10000dea8
    def tutorial(self):
        """On the first three games, the line in the game's language (en, pt, es, zh, ru,
        fr; else English), then the first slot.  PORT: the line in a Windows voice at rate
        0.5, then the key hints through the screen reader, and the first slot once both are
        done, not 4 s after the line began (0x10000e634)."""
        count = self.defaults.integerForKey_(COUNT_TUTORIAL_KEY) if self.defaults else 3
        if count > 2:                                                  # 0x10000e010
            self.loop.scheduledTimer(2.0, self, 'startGame')           # 0x10000e0e0
            return
        want = language.pick(self.language_code, language.TUTORIAL_LANGUAGES)
        lang = self.voice.choose(want) if self.voice is not None else want
        line = TUTORIAL_LINES.get(lang, TUTORIAL_LINES['en'])
        self.tutorial_line = line
        spoken = self.voice is not None and self.voice.speak(line)
        if not spoken:
            self.say(line)
        self.defaults.setInteger_forKey_(count + 1, COUNT_TUTORIAL_KEY)  # 0x10000e5bc
        self.defaults.synchronize()
        if spoken:
            self._tutorial_polls = 0
            self._tutorial_poll = self.loop.scheduledTimer(0.1, self, 'tutorialPoll',
                                                           repeats=True)
        else:
            self.loop.scheduledTimer(len(line) / HINT_CHARS_PER_SECOND, self, 'keyHints')

    #: Polls, 0.1 s apart, before the voice's silence is believed: it may not have begun.
    POLLS_BEFORE_SILENCE = 5

    def tutorialPoll(self, timer=None):
        """PORT: wait for the Windows voice to finish the line."""
        self._tutorial_polls += 1
        if self._tutorial_polls < self.POLLS_BEFORE_SILENCE:
            return
        if self.voice is not None and self.voice.speaking:
            return
        self._tutorial_poll.invalidate()
        self.keyHints()

    def key_hints(self):
        """The hints, from the player's own keys."""
        out = []
        for text, actions in KEY_HINTS:
            keys = {a: (self.keymap.hint_keys(a) if self.keymap else None) or 'nothing'
                    for a in actions}
            out.append(text.format(**keys))
        return out

    def keyHints(self, timer=None):
        """PORT ADDITION: the key hints, then the first slot once they have been said."""
        hints = self.key_hints()
        for i, hint in enumerate(hints):
            self.say(hint, interrupt=(i == 0))
        wait = sum(len(h) for h in hints) / HINT_CHARS_PER_SECOND
        self.loop.scheduledTimer(wait, self, 'startGame')

    # -[GameScene startGame] 0x1000152e4
    def startGame(self, timer=None):
        self.started = True
        self.startScore()
        self.blockPlayer = False
        self.createObjectScene()

    # GameScene.startScore 0x10001532c
    def startScore(self):
        """A point at once, then one every 0.25 s, under the key "upScore"."""
        self.runAction(A.repeatActionForever(A.sequence([A.runBlock(self.upScore),
                                                         A.waitForDuration(0.25)])),
                       key='upScore')

    # -[GameScene upScore] 0x1000155f4
    def upScore(self):
        self.delegate('scoreUpWithValue', 1)

    # ---- the pause (PORT ADDITION) ------------------------------------------------------
    def pause(self):
        """Everything stops where it is: the slots, the light, the score, the sounds, the
        timers; the tutorial voice is cut off."""
        if self.paused_by_player:
            return
        self.paused_by_player = True
        self.pause_all()
        self.loop.hold()
        if self.voice is not None:
            self.voice.stop()

    def resume(self):
        if not self.paused_by_player:
            return
        self.paused_by_player = False
        self.loop.resume()
        self.resume_all()
