"""``WarningViewController``: the earphone warning the game opens on.  Ported from
``analysis/disasm/dz_WarningViewController.txt``.

* ``viewDidLoad`` (0x10000e96c): the label in Portuguese when the language is "pt", else in
  English (0x10000ea3c..0x10000eb5c), and a one-shot timer of 3.0 s to ``segue``
  (0x10000e9f0).
* ``touchesBegan:withEvent:`` (0x10000ed18) and the timer both reach 0x10000f2fc, which
  invalidates the timer and goes to the menu (``WarningToMenu``, not animated).

PORT: the label is said by the screen reader, which is what VoiceOver read, and any key is
the touch.
"""
from __future__ import annotations

import logging

from ..platform import language, runloop

log = logging.getLogger('screens')

LABELS = {'en': 'Put the earphone on for a better experience',     # 0x100025550
          'pt': 'Coloque o fone para uma melhor experiência'}      # 0x10002b9c0
WARNING_SECONDS = 3.0                                               # 0x10000e9f0


class WarningViewController:
    title = 'Warning'

    def __init__(self, speech=None, loop=None, language_code=None):
        self.speech = speech
        self.loop = loop or runloop.main_loop()
        self.language_code = language_code or language.code()
        self.text = ''
        self.timer = None
        self.next = None

    # WarningViewController.viewDidLoad 0x10000e96c
    def viewDidLoad(self):
        self.text = LABELS[language.pick(self.language_code, language.WARNING_LANGUAGES)]
        self.timer = self.loop.scheduledTimer(WARNING_SECONDS, self, 'segue')
        if self.speech is not None:
            self.speech.speak(self.text)

    # WarningViewController~shared1 0x10000f2fc: the timer, or a touch
    def segue(self):
        if self.timer is not None:
            self.timer.invalidate()                                     # 0x10000f32c
        if self.next is None:
            self.next = 'menu'                                          # WarningToMenu

    def key(self, name, char=''):
        """Any key, as a touch anywhere (touchesBegan:withEvent: 0x10000ed18)."""
        self.segue()

    def lines(self):
        return ['Inside The Cave - %s' % self.title, '', self.text, '',
                'Any key goes on to the menu.']
