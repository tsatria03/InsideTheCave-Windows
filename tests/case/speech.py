"""Who speaks: ``platform/speech.py``.

``Speech``: NVDA first, through its own client; then the other screen readers through
Prism, with Narrator only while narrator.exe runs; then a plain voice through Prism.
``TutorialVoice``: the tutorial line in a SAPI 5 voice of the game's language, at rate 0.5.

Every piece here is a stand-in - a fake NVDA, a fake Prism registry, a fake clock - so
these tests never load NVDA's client or Prism and never make a sound.
"""
from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
import _scratch_save                                             # noqa: E402  never the real save

from insidethecave.platform.speech import (Speech, TutorialVoice, _Prism,  # noqa: E402
                                           voice_language)


class _Nvda:
    def __init__(self, running=False):
        self.is_running = running
        self.said = []
        self.stopped = 0

    def running(self):
        return self.is_running

    def speak(self, text, interrupt):
        if not self.is_running:
            return False
        self.said.append(text)
        return True

    def stop(self):
        self.stopped += 1


class _Features:
    def __init__(self, backend):
        self._backend = backend

    @property
    def is_supported_at_runtime(self):
        return self._backend.is_running

    @property
    def supports_output(self):
        return self._backend.braille


class _Backend:
    """One Prism backend: a screen reader or a voice."""

    def __init__(self, name, running=True, braille=True, fails=False, voices=()):
        self.name = name
        self.is_running = running
        self.braille = braille
        self.fails = fails
        self.spoken = []            # (how, text, interrupt)
        self.stopped = 0
        self._voices = list(voices)  # (name, language)
        self.voice = 0
        self.rate = 0.5
        self.rate_when_spoken = None
        self.speaking = False

    @property
    def features(self):
        return _Features(self)

    @property
    def voices_count(self):
        return len(self._voices)

    def get_voice_name(self, i):
        return self._voices[i][0]

    def get_voice_language(self, i):
        return self._voices[i][1]

    def _say(self, how, text, interrupt):
        if self.fails:
            raise RuntimeError('%s failed' % self.name)
        self.spoken.append((how, text, interrupt))
        self.rate_when_spoken = self.rate
        self.speaking = True

    def speak(self, text, interrupt=False):
        self._say('speak', text, interrupt)

    def output(self, text, interrupt=False):
        self._say('output', text, interrupt)

    def stop(self):
        self.stopped += 1
        self.speaking = False


class _Ids:
    """Stands in for ``prism.BackendId``: the names are the ids."""
    NVDA, JAWS, ZDSR, ZOOM_TEXT, SYSTEM_ACCESS = 'NVDA', 'JAWS', 'ZDSR', 'ZOOM_TEXT', 'SYSTEM_ACCESS'
    PC_TALKER, BOY_PC_READER, SENSE_READER = 'PC_TALKER', 'BOY_PC_READER', 'SENSE_READER'
    WINDOW_EYES, UIA, SAPI, ONE_CORE = 'WINDOW_EYES', 'UIA', 'SAPI', 'ONE_CORE'


class _Context:
    """Stands in for ``prism.Context``, holding the backends by id."""

    def __init__(self, backends, broken=()):
        self.backends = backends          # id -> _Backend
        self.broken = set(broken)         # ids whose create() raises
        self.created = []

    @property
    def backends_count(self):
        return len(self.backends) + len(self.broken)

    def id_of(self, index):
        return (list(self.backends) + sorted(self.broken))[index]

    def create(self, bid):
        self.created.append(bid)
        if bid in self.broken or bid not in self.backends:
            raise ValueError('Invalid or unsupported backend')
        return self.backends[bid]


class _Clock:
    def __init__(self):
        self.now = 100.0

    def __call__(self):
        return self.now


def _speech(backends, nvda=False, narrator=False, broken=()):
    ctx = _Context(backends, broken)
    clock = _Clock()
    prism = _Prism(loader=lambda: (ctx, _Ids), narrator_running=lambda: narrator,
                   clock=clock)
    return Speech(nvda=_Nvda(nvda), prism=prism), ctx, clock


#: The dev's voices on 2026-10-02, plus one of another language to choose.
VOICES = (('Microsoft David Desktop', 'en-US'), ('Nvda Sapi', 'en-us'),
          ('Microsoft Zira Desktop', 'en-US'), ('Microsoft Maria Desktop', 'pt-BR'))


def _tutorial(voices=VOICES, default=0):
    sapi = _Backend('SAPI', braille=False, voices=voices)
    sapi.voice = default
    return TutorialVoice(loader=lambda: (_Context({'SAPI': sapi}), _Ids)), sapi


# ---- Speech ------------------------------------------------------------------------------

def test_nvda_speaks_first_and_prism_is_never_loaded():
    nvda = _Nvda(running=True)
    s = Speech(nvda=nvda)
    assert s.speak('Key bindings.') is True
    assert nvda.said == ['Key bindings.']
    assert s._prism is None, 'Prism was loaded for an NVDA player'


def test_jaws_speaks_when_nvda_is_not_running():
    jaws = _Backend('JAWS')
    s, _ctx, _clock = _speech({'JAWS': jaws, 'SAPI': _Backend('SAPI')})
    assert s.speak('Torch low') is True
    assert jaws.spoken == [('output', 'Torch low', True)]
    assert s.which == 'JAWS'


def test_the_first_running_screen_reader_in_order_wins():
    jaws = _Backend('JAWS', running=False)
    zoomtext = _Backend('ZoomText')
    pctalker = _Backend('PC-Talker')
    s, _ctx, _clock = _speech({'JAWS': jaws, 'PC_TALKER': pctalker, 'ZOOM_TEXT': zoomtext})
    s.speak('hello')
    assert zoomtext.spoken and not pctalker.spoken and not jaws.spoken


def test_narrator_is_used_only_while_narrator_is_running():
    uia = _Backend('UIA')              # says it is ready either way, as Prism's does
    sapi = _Backend('SAPI')
    s, ctx, _clock = _speech({'UIA': uia, 'SAPI': sapi}, narrator=False)
    s.speak('one')
    assert not uia.spoken, 'a line went to Narrator while it was off'
    assert sapi.spoken
    assert 'UIA' not in ctx.created, 'the Narrator backend was made while Narrator was off'

    uia2 = _Backend('UIA')
    s2, _ctx2, _clock2 = _speech({'UIA': uia2, 'SAPI': _Backend('SAPI')}, narrator=True)
    s2.speak('two')
    assert uia2.spoken == [('output', 'two', True)]


def test_a_voice_speaks_when_no_screen_reader_runs():
    sapi = _Backend('SAPI', braille=False)
    s, _ctx, _clock = _speech({'JAWS': _Backend('JAWS', running=False), 'SAPI': sapi})
    assert s.speak('Nothing pressed.') is True
    assert sapi.spoken == [('speak', 'Nothing pressed.', True)], 'no braille call on a voice'
    assert s.which == 'SAPI'


def test_onecore_steps_in_when_sapi_will_not_start():
    onecore = _Backend('OneCore')
    s, _ctx, _clock = _speech({'ONE_CORE': onecore}, broken=('SAPI',))
    assert s.speak('hello') is True
    assert onecore.spoken


def test_no_prism_means_nvda_alone_and_no_crash():
    def missing():
        raise ImportError('No module named prism')
    s = Speech(nvda=_Nvda(running=False), prism=_Prism(loader=missing))
    assert s.speak('hello') is False
    assert s.which == 'none' and s.available is False
    s.stop()


def test_a_screen_reader_that_stops_is_let_go():
    jaws = _Backend('JAWS')
    sapi = _Backend('SAPI')
    s, _ctx, clock = _speech({'JAWS': jaws, 'SAPI': sapi})
    s.speak('one')
    assert jaws.spoken
    jaws.is_running = False
    clock.now += _Prism.CHECK_EVERY + 0.1
    s.speak('two')
    assert [t for _h, t, _i in sapi.spoken] == ['two'], 'the line did not move to the voice'


def test_a_screen_reader_started_later_is_found():
    jaws = _Backend('JAWS', running=False)
    sapi = _Backend('SAPI')
    s, _ctx, clock = _speech({'JAWS': jaws, 'SAPI': sapi})
    s.speak('one')
    assert sapi.spoken and not jaws.spoken
    jaws.is_running = True
    s.speak('two')
    assert not jaws.spoken, 'it looked again sooner than every few seconds'
    clock.now += _Prism.PROBE_EVERY + 0.1
    s.speak('three')
    assert [t for _h, t, _i in jaws.spoken] == ['three']


def test_a_screen_reader_that_fails_hands_the_line_to_the_voice():
    jaws = _Backend('JAWS', fails=True)
    sapi = _Backend('SAPI')
    s, _ctx, _clock = _speech({'JAWS': jaws, 'SAPI': sapi})
    assert s.speak('hello') is True
    assert [t for _h, t, _i in sapi.spoken] == ['hello']


def test_stopping_a_voice_discards_it_so_stuck_audio_is_torn_down():
    sapi = _Backend('SAPI', braille=False)
    s, ctx, _clock = _speech({'SAPI': sapi})
    s.speak('one')
    s.stop()
    assert sapi.stopped == 1
    sapi2 = _Backend('SAPI', braille=False)
    ctx.backends['SAPI'] = sapi2
    s.speak('two')
    assert sapi2.spoken == [('speak', 'two', True)], 'a fresh backend was not built'


def test_an_empty_line_says_nothing():
    jaws = _Backend('JAWS')
    s, _ctx, _clock = _speech({'JAWS': jaws})
    assert s.speak('') is False
    assert not jaws.spoken


def test_the_tests_never_reach_the_players_screen_reader():
    """_scratch_save sets INSIDETHECAVE_SILENT, so a Speech built with no stand-ins - as
    Speech.shared() builds one - loads neither NVDA's client nor Prism."""
    assert os.environ.get('INSIDETHECAVE_SILENT') == '1'
    s = Speech()
    assert s.silent and s.nvda is None and s._prism is None
    assert s.speak('Torch low') is False
    s.stop()
    assert s.which == 'none' and not s.available
    assert s._prism is None, 'Prism was loaded'


# ---- TutorialVoice -----------------------------------------------------------------------

def test_a_voice_languages_two_letters():
    assert voice_language('en-US') == 'en'
    assert voice_language('pt_br') == 'pt'
    assert voice_language('FR') == 'fr'
    assert voice_language(None) == ''


def test_the_tutorial_voice_speaks_the_games_language_when_one_is_installed():
    tv, sapi = _tutorial()
    assert tv.choose('pt') == 'pt'
    assert sapi.voice == 3, 'the Portuguese voice was not chosen'


def test_with_no_voice_for_the_language_it_is_english_in_the_default_voice():
    """No line is ever read in a voice for another language."""
    tv, sapi = _tutorial(default=2)
    assert tv.choose('ru') == 'en'
    assert sapi.voice == 2, 'the default voice was not kept'


def test_choosing_english_after_another_language_goes_back_to_an_english_voice():
    tv, sapi = _tutorial()
    tv.choose('pt')
    assert tv.choose('en') == 'en'
    assert voice_language(sapi.get_voice_language(sapi.voice)) == 'en'


def test_the_tutorial_line_is_spoken_at_rate_one_half():
    """Prism's 0.5 is a voice's normal speed; never higher (the dev, 2026-10-02)."""
    tv, sapi = _tutorial()
    sapi.rate = 0.9
    assert tv.speak('You need to scape from a cave full of monsters on the way!') is True
    assert sapi.rate_when_spoken == 0.5
    assert sapi.spoken[0][0] == 'speak' and sapi.spoken[0][2] is True


def test_speaking_says_when_the_line_is_done():
    tv, sapi = _tutorial()
    assert tv.speaking is False
    tv.speak('line')
    assert tv.speaking is True
    sapi.speaking = False
    assert tv.speaking is False


def test_without_sapi_the_tutorial_voice_says_it_cannot_speak():
    def missing():
        raise ImportError('No module named prism')
    tv = TutorialVoice(loader=missing)
    assert tv.choose('pt') == 'pt'
    assert tv.speak('line') is False
    assert tv.speaking is False
    tv.stop()


def test_the_tests_never_reach_sapi():
    tv = TutorialVoice()
    assert tv.silent and tv.backend() is None
    assert tv.speak('line') is False and tv.voices() == []


if __name__ == '__main__':
    _scratch_save.run(globals())
