"""``SKAudioNode`` and the scene's listener, on OpenAL.

Every sound the game keeps is an ``SKAudioNode`` made in the scene's initialisers
(0x1000157d8..0x100015b0c, GAME_STRUCTURE.md section 13), heard from the scene's
``listener``, which the game sets to the player (0x100016a78).  Here each node is one
OpenAL source, and the listener stays at OpenAL's origin: a node's place is worked out
from where it is against the listener, every frame.

**Placing a sound** (aidocks/project_port_plan.md, question 2).  How SpriteKit turned a
scene position into a direction is Apple's code, not the binary's, so this is the port's
own mapping, on constants to tune by ear:

    across   the distance from the listener in lanes (``LANE_WIDTH``, 0.3 W = 225: the
             lanes' spacing, 0x10000fa10), times ``PAN_PER_LANE``: one lane over is one
             unit to that side
    ahead    the height above the listener as a fraction of the scene's height, times
             ``DEPTH``, in front

with OpenAL's inverse distance, clamped, from ``REFERENCE_DISTANCE``.  HRTF is off
(``openal.AL.open``), so a sound is panned, not filtered.

**Mono for the placed sounds.**  OpenAL places only mono buffers, and plays stereo ones
straight through, as Apple's 3D audio did with the original's stereo roar (**inferred**).
The dev chose to place the roar, the bats and the coin jingle: those three (``PLACED``)
load mixed down to mono.  Every other positional node keeps its file as it is, so a
stereo one plays unplaced, as it most likely did on the iPhone; the music is mono already
and sits at the player.

**No sound louder than 1.0** (the dev, 2026-10-02: "All sound volumes should not exceed
1.0 to avoid peaking.").  The game asks for 3.0 for a roar in the player's lane
(0x10000f740) and for the bats in it (0x10000f85c).  Every volume is capped at ``MAX_GAIN``,
1.0, as it is set, which is most likely what the iPhone did too: the volume
``changeVolumeTo:`` sets runs from 0 to 1 in Apple's audio (**inferred**: Apple's code).  So
a roar is as loud in the player's lane as in another, and its lane is told by where it
comes from; the bats keep 1.0 against 0.7.  A node keeps the volume the game asked for;
only what is heard is capped.
"""
from __future__ import annotations

import logging

from .. import paths
from ..platform import openal as o
from .node import Node

log = logging.getLogger('audio')

#: The lanes' spacing in the scene, 0.3 W (the lanes at -0.3 W, 0 and 0.3 W).
LANE_WIDTH = 225.0
#: OpenAL units across per lane, and in front per scene height: tuned by ear, and kept as
#: they are by the dev (2026-10-02: "I liked the panning amounts.").
PAN_PER_LANE = 1.0
DEPTH = 2.0
#: OpenAL's inverse distance: full volume within this distance, quieter beyond it.
REFERENCE_DISTANCE = 1.0
ROLLOFF = 1.0
#: The highest gain a source may have (the dev); the game asks for 3.0, heard as 1.0.
MAX_GAIN = 1.0


def heard(volume):
    """A volume the game sets, as it is played: 0 to ``MAX_GAIN``."""
    return min(max(0.0, float(volume)), MAX_GAIN)
#: The sounds placed in their lanes, loaded mixed down to mono (base names).
PLACED = frozenset(('rugido', 'batsound', 'tilintar'))


def placed(file_name):
    return paths.base_name(file_name) in PLACED


class AudioNode(Node):
    """``SKAudioNode(fileNamed:)``.  As SpriteKit's, it is positional and plays looped as
    soon as it joins a scene, unless told otherwise (``setAutoplayLooped:``,
    ``setPositional:``)."""

    def __init__(self, file_name, name=None):
        super().__init__(name or paths.base_name(file_name))
        self.file_name = file_name
        self.autoplayLooped = True
        self.positional = True
        self.volume = 1.0
        self.playing = False
        self.engine = None          # the AudioEngine, while the node is in a scene with one
        self.source = 0

    def set_volume(self, volume):
        self.volume = float(volume)
        if self.engine is not None:
            self.engine.volume_changed(self)

    def play(self):
        """``SKAction.play()``: from the start; looped if the node loops."""
        self.playing = True
        if self.engine is not None:
            self.engine.start(self)

    def stop(self):
        self.playing = False
        if self.engine is not None:
            self.engine.halt(self)


class AudioEngine:
    """The scene's sound: one OpenAL source per audio node, kept where its node is."""

    def __init__(self, al, bank, scene_height=1334.0):
        self.al = al
        self.bank = bank
        self.scene_height = float(scene_height)
        self.nodes = []
        self._one_shots = []        # sources of playSoundFileNamed, deleted when done
        self._paused = []           # sources pause_all stopped, to start again

    # ---- where a node is heard ------------------------------------------------------
    def mapped(self, node, listener):
        """A node's place, relative to the listener, in OpenAL's units."""
        if not node.positional or listener is None:
            return (0.0, 0.0, 0.0)
        nx, ny = node.scene_position()
        lx, ly = listener.scene_position()
        return ((nx - lx) / LANE_WIDTH * PAN_PER_LANE, 0.0,
                -(ny - ly) / self.scene_height * DEPTH)

    # ---- nodes joining and leaving ----------------------------------------------------
    def attach(self, node):
        node.engine = self
        self.nodes.append(node)
        al = self.al
        s = al.gen_source()
        node.source = s
        al.alSourcei(s, o.AL_BUFFER,
                     self.bank.buffer(node.file_name, mono=placed(node.file_name)))
        al.alSourcei(s, o.AL_SOURCE_RELATIVE, 1)
        al.alSourcef(s, o.AL_MAX_GAIN, MAX_GAIN)
        al.alSourcef(s, o.AL_REFERENCE_DISTANCE, REFERENCE_DISTANCE)
        al.alSourcef(s, o.AL_ROLLOFF_FACTOR, ROLLOFF)
        al.alSourcef(s, o.AL_GAIN, heard(node.volume))
        if node.autoplayLooped or node.playing:
            node.playing = True
            self.start(node)

    def detach(self, node):
        if node in self.nodes:
            self.nodes.remove(node)
        if node.source:
            self.al.alSourceStop(node.source)
            self.al.delete_source(node.source)
        node.source = 0
        node.engine = None

    # ---- playing --------------------------------------------------------------------
    def start(self, node):
        if not node.source:
            return
        al = self.al
        al.alSourceStop(node.source)
        al.alSourcei(node.source, o.AL_LOOPING, 1 if node.autoplayLooped else 0)
        self._place(node, node.scene.listener if node.scene is not None else None)
        al.alSourcePlay(node.source)

    def halt(self, node):
        if node.source:
            self.al.alSourceStop(node.source)

    def volume_changed(self, node):
        if node.source:
            self.al.alSourcef(node.source, o.AL_GAIN, heard(node.volume))

    def play_once(self, name):
        """``playSoundFileNamed:``: not placed, at full volume.  Returns its length."""
        al = self.al
        s = al.gen_source()
        al.alSourcei(s, o.AL_BUFFER, self.bank.buffer(name))
        al.alSourcei(s, o.AL_SOURCE_RELATIVE, 1)
        al.alSource3f(s, o.AL_POSITION, 0.0, 0.0, 0.0)
        al.alSourcePlay(s)
        self._one_shots.append(s)
        return self.bank.seconds(name)

    # ---- every frame ----------------------------------------------------------------
    def _place(self, node, listener):
        self.al.alSource3f(node.source, o.AL_POSITION, *self.mapped(node, listener))

    def sync(self, scene):
        """Keep every node's sound where the node is, and let finished one-shots go."""
        for node in self.nodes:
            if node.source:
                self._place(node, scene.listener)
                if node.playing and not node.autoplayLooped \
                        and self.al.source_state(node.source) == o.AL_STOPPED:
                    node.playing = False
        for s in list(self._one_shots):
            if self.al.source_state(s) == o.AL_STOPPED:
                self._one_shots.remove(s)
                self.al.delete_source(s)

    def pause_all(self):
        """PORT ADDITION, for the pause: every playing sound stops where it is."""
        sources = [n.source for n in self.nodes if n.source] + self._one_shots
        self._paused = [s for s in sources if self.al.source_state(s) == o.AL_PLAYING]
        for s in self._paused:
            self.al.alSourcePause(s)

    def resume_all(self):
        for s in self._paused:
            if self.al.source_state(s) == o.AL_PAUSED:
                self.al.alSourcePlay(s)
        self._paused = []

    def release(self):
        for node in list(self.nodes):
            self.detach(node)
        for s in self._one_shots:
            self.al.alSourceStop(s)
            self.al.delete_source(s)
        self._one_shots = []
