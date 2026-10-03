"""``WarningViewController``: the earphone warning the game opens on.  Ported from
``analysis/disasm/dz_WarningViewController.txt``.

* ``viewDidLoad`` (0x10000e96c): the label in Portuguese when the language is "pt", else in
  English (0x10000ea3c..0x10000eb5c), and a one-shot timer of 3.0 s to ``segue``
  (0x10000e9f0).
* ``touchesBegan:withEvent:`` (0x10000ed18) and the timer both reach 0x10000f2fc, which
  invalidates the timer and goes to the menu (``WarningToMenu``, not animated).

PORT: any key is the touch.  The label was said by the screen reader, which is what
VoiceOver read; for the fourth release it is said in the Windows voice the tutorial line
uses (``TutorialVoice``), at its rate, chosen by the same rule (a voice for the language,
else English), and by the screen reader only when there is no such voice (the dev: "the
headphone warning should speak with a window voice, not my screen reader. I always tend to
miss it.").  The menu then waits for the voice to finish, so the screen reader's "Main
menu" does not talk over it; a key still goes on at once, and cuts the voice off.
"""
from __future__ import annotations

import logging

from ..platform import language, runloop

log = logging.getLogger('screens')

LABELS = {'en': 'Put the earphone on for a better experience',     # 0x100025550
          'pt': 'Coloque o fone para uma melhor experiência'}      # 0x10002b9c0
WARNING_SECONDS = 3.0                                               # 0x10000e9f0
#: PORT: how often, once the 3 s are up, the Windows voice is asked whether it is done.
VOICE_POLL_SECONDS = 0.1


class WarningViewController:
    title = 'Warning'

    def __init__(self, speech=None, loop=None, language_code=None, voice=None):
        self.speech = speech
        self.voice = voice
        self.loop = loop or runloop.main_loop()
        self.language_code = language_code or language.code()
        self.text = ''
        self.timer = None
        self.spoken_by_voice = False
        self.next = None

    # WarningViewController.viewDidLoad 0x10000e96c
    def viewDidLoad(self):
        want = language.pick(self.language_code, language.WARNING_LANGUAGES)
        lang = self.voice.choose(want) if self.voice is not None else want
        self.text = LABELS.get(lang, LABELS['en'])
        self.timer = self.loop.scheduledTimer(WARNING_SECONDS, self, 'timeUp')
        self.spoken_by_voice = self.voice is not None and self.voice.speak(self.text)
        if not self.spoken_by_voice and self.speech is not None:
            self.speech.speak(self.text)

    def timeUp(self, timer=None):
        """The original's 3 s timer.  PORT: if the Windows voice is still saying the label,
        wait for it, asking again every VOICE_POLL_SECONDS."""
        if self.spoken_by_voice and self.voice.speaking:
            self.timer = self.loop.scheduledTimer(VOICE_POLL_SECONDS, self, 'timeUp')
            return
        self.segue()

    # WarningViewController~shared1 0x10000f2fc: the timer, or a touch
    def segue(self):
        if self.timer is not None:
            self.timer.invalidate()                                     # 0x10000f32c
        if self.next is None:
            self.next = 'menu'                                          # WarningToMenu

    def key(self, name, char=''):
        """Any key, as a touch anywhere (touchesBegan:withEvent: 0x10000ed18).  PORT: it
        cuts the Windows voice off."""
        if self.spoken_by_voice:
            self.voice.stop()
        self.segue()

    def lines(self):
        return ['Inside The Cave - %s' % self.title, '', self.text, '',
                'Any key goes on to the menu.']
