"""The sounds: ``platform/sound.py`` and ``platform/openal.py``.

The WAVs are read from the repository's ``game/sounds``; the OpenAL tests open OpenAL
Soft on its null driver, which ``_scratch_save`` sets, so nothing is ever heard.
"""
from __future__ import annotations

import array
import os
import struct
import sys
import tempfile
import wave

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
import _scratch_save                                             # noqa: E402  never the real save

from insidethecave import paths                                  # noqa: E402
from insidethecave.platform import openal, sound                 # noqa: E402

#: The sounds placed in a lane, mixed down to mono (aidocks/project_port_plan.md, question 2).
PLACED = ('Rugido.mp3', 'BatSound.wav', 'tilintar.aiff')


def _wav(channels, width, frames):
    """A throwaway WAV holding ``frames``, a list of per-channel sample tuples."""
    fd, path = tempfile.mkstemp(suffix='.wav')
    os.close(fd)
    with wave.open(path, 'wb') as w:
        w.setnchannels(channels)
        w.setsampwidth(width)
        w.setframerate(8000)
        fmt = '<%d%s' % (channels, 'h' if width == 2 else 'B')
        w.writeframes(b''.join(struct.pack(fmt, *f) for f in frames))
    return path


def test_every_sound_the_binary_names_reads():
    paths.set_game(None)
    from paths import BINARY_NAMES                                # tests/case/paths.py
    for name in BINARY_NAMES:
        pcm = sound.load(name)
        assert pcm.width == 2 and pcm.channels in (1, 2) and pcm.frames > 0, name


def test_the_placed_sounds_are_stereo_and_load_as_mono():
    """The roar, the bats and the coin's jingle are stereo files (GAME_STRUCTURE.md
    section 13); placed, each is one channel of the same length."""
    paths.set_game(None)
    for name in PLACED:
        stereo = sound.load(name)
        mono = sound.load(name, mono=True)
        assert stereo.channels == 2, name
        assert mono.channels == 1 and mono.frames == stereo.frames, name
        assert mono.al_format == openal.AL_FORMAT_MONO16


def test_mixing_down_averages_left_and_right():
    path = _wav(2, 2, [(1000, 3000), (-32768, -32768), (32767, -32768), (5, 6)])
    try:
        mono = sound.to_mono(sound.read_wav(path))
        samples = array.array('h')
        samples.frombytes(mono.data)
        assert list(samples) == [2000, -32768, -1, 5], list(samples)
    finally:
        os.remove(path)


def test_mixing_down_eight_bit_keeps_silence_at_128():
    path = _wav(2, 1, [(128, 128), (0, 255), (200, 100)])
    try:
        mono = sound.to_mono(sound.read_wav(path))
        assert list(mono.data) == [128, 127, 150] and mono.width == 1
    finally:
        os.remove(path)


def test_a_mono_file_is_used_as_it_is():
    path = _wav(1, 2, [(7,), (8,)])
    try:
        pcm = sound.read_wav(path)
        assert sound.to_mono(pcm) is pcm
    finally:
        os.remove(path)


def test_a_missing_sound_says_which():
    paths.set_game(None)
    try:
        sound.load('nothing_like_it.wav')
    except sound.SoundError as exc:
        assert 'nothing_like_it' in str(exc)
    else:
        raise AssertionError('no error for a missing sound')


def test_the_sounds_load_into_openal_on_the_null_driver():
    assert os.environ.get('ALSOFT_DRIVERS') == 'null'
    paths.set_game(None)
    al = openal.AL()
    al.open()
    try:
        assert not al.hrtf, 'HRTF is on'
        bank = sound.SoundBank(al)
        roar = bank.buffer('Rugido.mp3', mono=True)
        assert roar and bank.buffer('Rugido.wav', mono=True) == roar, 'loaded twice'
        assert bank.buffer('Rugido.mp3') != roar, 'stereo and mono share a buffer'
        assert abs(bank.seconds('Rugido.mp3', mono=True) - 0.8) < 0.05
        bank.release()
        al.check('releasing')
    finally:
        al.close()


if __name__ == '__main__':
    _scratch_save.run(globals())
