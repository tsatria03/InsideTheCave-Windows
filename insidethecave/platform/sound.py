"""PORT ADDITION: the game's sounds, read into OpenAL buffers.

The original hands SpriteKit a file name (``SKAudioNode(fileNamed: "Rugido.mp3")``,
``playSoundFileNamed("MovimentoProibido.wav")``) and Apple decodes it.  The port's sounds
are all 16-bit PCM WAV since the dev converted them (2026-10-02, aidocks/DIVERGENCES.md),
so the standard library's ``wave`` reads them and OpenAL plays them as they are; nothing
needs a decoder.  ``paths.sound`` finds each by its base name, whatever extension the
binary asks for.

**Mono for the sounds placed in a lane.**  OpenAL places only mono buffers in space and
plays a stereo one straight through, as Apple's 3D audio does (**inferred** for Apple).
The roar and the bats are stereo files, so in the original they most likely came from no
side at all (GAME_STRUCTURE.md section 13).  The dev chose to place them
(aidocks/project_port_plan.md, question 2): a sound loaded with ``mono=True`` is mixed down
to one channel, each frame the average of its channels, so the SpriteKit stand-in can put
it in its lane.  A file that is mono already is used as it is.

Each file is read once, the first time it is asked for, and kept.
"""
from __future__ import annotations

import array
import logging
import sys
import wave
from dataclasses import dataclass

from .. import paths
from . import openal

log = logging.getLogger('sound')


class SoundError(RuntimeError):
    pass


@dataclass(frozen=True)
class Pcm:
    """A sound's samples, as OpenAL wants them."""
    data: bytes
    channels: int
    width: int          # bytes a sample: 1 (unsigned 8-bit) or 2 (signed 16-bit)
    rate: int

    @property
    def frames(self) -> int:
        return len(self.data) // (self.channels * self.width)

    @property
    def seconds(self) -> float:
        return self.frames / float(self.rate)

    @property
    def al_format(self) -> int:
        return {(1, 1): openal.AL_FORMAT_MONO8, (1, 2): openal.AL_FORMAT_MONO16,
                (2, 1): openal.AL_FORMAT_STEREO8, (2, 2): openal.AL_FORMAT_STEREO16}[
                    (self.channels, self.width)]


def read_wav(path: str) -> Pcm:
    """A WAV file's samples: 8 or 16-bit PCM, mono or stereo, the forms OpenAL takes."""
    try:
        with wave.open(path, 'rb') as w:
            channels, width, rate = w.getnchannels(), w.getsampwidth(), w.getframerate()
            data = w.readframes(w.getnframes())
    except (OSError, EOFError, wave.Error) as exc:
        raise SoundError('%s: %s' % (path, exc)) from exc
    if channels not in (1, 2) or width not in (1, 2):
        raise SoundError('%s: %d channels of %d-bit samples; OpenAL takes 1 or 2 channels '
                         'of 8 or 16 bits' % (path, channels, width * 8))
    return Pcm(data, channels, width, rate)


def to_mono(pcm: Pcm) -> Pcm:
    """Two channels mixed down to one, each frame the average of its left and right."""
    if pcm.channels == 1:
        return pcm
    if pcm.width == 2:
        samples = array.array('h')
        samples.frombytes(pcm.data)
        if sys.byteorder != 'little':
            samples.byteswap()      # WAV is little-endian
        mixed = array.array('h', [(l + r) >> 1 for l, r in zip(samples[0::2], samples[1::2])])
        if sys.byteorder != 'little':
            mixed.byteswap()
        return Pcm(mixed.tobytes(), 1, 2, pcm.rate)
    # unsigned 8-bit, silence at 128
    data = pcm.data
    return Pcm(bytes((l + r) >> 1 for l, r in zip(data[0::2], data[1::2])), 1, 1, pcm.rate)


def load(name: str, mono: bool = False) -> Pcm:
    """A sound the binary names, such as ``"Rugido.mp3"``, read from its WAV; mixed down to
    mono when ``mono`` is set."""
    path = paths.sound(name)
    if path is None:
        raise SoundError('no sound named %s in %s' % (paths.base_name(name),
                                                      ' or '.join(paths.SOUND_FOLDERS)))
    pcm = read_wav(path)
    return to_mono(pcm) if mono else pcm


class SoundBank:
    """Every sound loaded into an OpenAL buffer once, by base name and whether it is mono."""

    def __init__(self, al):
        self.al = al
        self._buffers = {}          # (base name, mono) -> (buffer id, Pcm)

    def buffer(self, name: str, mono: bool = False) -> int:
        """The OpenAL buffer for a sound, loaded the first time it is asked for."""
        key = (paths.base_name(name), bool(mono))
        if key not in self._buffers:
            pcm = load(name, mono)
            bid = self.al.gen_buffer()
            self.al.buffer_data(bid, pcm.al_format, pcm.data, pcm.rate)
            self.al.check('loading %s' % name)
            self._buffers[key] = (bid, pcm)
            log.info('loaded %s: %d channel(s), %d Hz, %.2f s',
                     key[0], pcm.channels, pcm.rate, pcm.seconds)
        return self._buffers[key][0]

    def seconds(self, name: str, mono: bool = False) -> float:
        """How long a sound lasts."""
        self.buffer(name, mono)
        return self._buffers[(paths.base_name(name), bool(mono))][1].seconds

    def release(self):
        for bid, _pcm in self._buffers.values():
            self.al.delete_buffer(bid)
        self._buffers.clear()
