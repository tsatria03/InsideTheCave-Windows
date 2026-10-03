"""PORT ADDITION: music on the menus.  The original 2.32 has none.

The dev, 2026-10-02, for the second release: "I added the sound background-music.wav into
the used folder because that should be used as the menu music. When you pause the game,
that music shouldn't play."  It is the early versions' music (1.0 to 1.19,
``background-music-aac.caf``; GAME_STRUCTURE.md section 15), a 16-second stereo loop.

It plays on the main menu, the Score screen and the result screen, carrying on from one to
the next, and stops when a game starts; the warning and the pause menu have none.  It is
not placed: one looped source at the listener, stereo as it is, at full volume, ``GAIN``.
``MENUVOLUME`` sits on top, as ``MUSICVOLUME`` does on the game's music
(``platform/volume.py``), so Page Up and Page Down on the menus turn it down from there.
"""
from __future__ import annotations

import logging

from ..platform import openal as o
from ..platform import volume
from ..scene.audio import heard

log = logging.getLogger('menu.music')

FILE = 'background-music.wav'
#: The file as recorded (the dev: "Put it to 1.0. I can always turn it down from there with
#: page up/down."), after 0.09, matched to the game music's level, was too quiet.
GAIN = 1.0


class MenuMusic:
    def __init__(self, al=None, bank=None):
        self.al = al
        self.bank = bank
        self.source = 0

    @property
    def playing(self):
        return bool(self.source)

    def start(self):
        """Begin looping, unless it already is."""
        if self.source or self.al is None or self.bank is None:
            return
        al = self.al
        try:
            buf = self.bank.buffer(FILE)
        except Exception:
            log.exception('the menu music could not be loaded')
            return
        s = al.gen_source()
        al.alSourcei(s, o.AL_BUFFER, buf)
        al.alSourcei(s, o.AL_SOURCE_RELATIVE, 1)
        al.alSource3f(s, o.AL_POSITION, 0.0, 0.0, 0.0)
        al.alSourcei(s, o.AL_LOOPING, 1)
        al.alSourcef(s, o.AL_GAIN, self.gain())
        al.alSourcePlay(s)
        self.source = s

    def gain(self):
        return heard(volume.menu(GAIN))

    def apply_volume(self):
        """Page Up or Page Down changed ``MENUVOLUME``: heard at once."""
        if self.source:
            self.al.alSourcef(self.source, o.AL_GAIN, self.gain())

    def stop(self):
        if self.source:
            self.al.alSourceStop(self.source)
            self.al.delete_source(self.source)
            self.source = 0
