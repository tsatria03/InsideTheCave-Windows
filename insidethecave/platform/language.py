"""The language the game speaks: Windows' display language, as the original read the
device's.

The original takes ``Locale.current``'s ``NSLocaleLanguageCode``, two letters, and compares
it with the languages it has words for:

    the tutorial line         "pt", "es", "zh", "ru", "fr"; anything else English
                              (GameScene.tutorial, 0x10000e034..0x10000e0ac)
    the earphone warning      "pt"; anything else English
                              (WarningViewController.viewDidLoad, 0x10000ea3c)

The port reads Windows' display language instead, by its two-letter code, falling back to
English when it cannot be read (the dev, 2026-10-02: "Follow the window's language
setting."; aidocks/project_port_plan.md, question 7).  The original crashes when the
device has no language (``brk`` at 0x10000e830); the port says English.
"""
from __future__ import annotations

import ctypes
import logging

log = logging.getLogger('language')

ENGLISH = 'en'
#: What the tutorial line is written in (GAME_STRUCTURE.md section 8).
TUTORIAL_LANGUAGES = ('en', 'pt', 'es', 'zh', 'ru', 'fr')
#: What the earphone warning is written in (GAME_STRUCTURE.md section 9).
WARNING_LANGUAGES = ('en', 'pt')

_LOCALE_NAME_MAX_LENGTH = 85


def locale_name() -> str | None:
    """Windows' display language as a locale name, such as ``"en-US"``, or None."""
    try:
        k32 = ctypes.WinDLL('kernel32')
        langid = k32.GetUserDefaultUILanguage()
        buf = ctypes.create_unicode_buffer(_LOCALE_NAME_MAX_LENGTH)
        if not k32.LCIDToLocaleName(langid, buf, _LOCALE_NAME_MAX_LENGTH, 0):
            return None
        return buf.value or None
    except (OSError, AttributeError):
        return None


def two_letters(name) -> str:
    """A locale name's language, in two lower-case letters: ``"pt-BR"`` is ``"pt"``;
    nothing usable is English."""
    code = str(name or '').replace('_', '-').split('-')[0].strip().lower()
    return code if len(code) >= 2 and code.isalpha() else ENGLISH


def code() -> str:
    """The game's language: Windows' display language in two letters, or ``"en"``."""
    name = locale_name()
    if name is None:
        log.info('display language not readable; English')
    return two_letters(name)


def pick(language, available) -> str:
    """``language`` when the game has words in it, else English, as the original's
    comparisons do."""
    return language if language in available else ENGLISH
