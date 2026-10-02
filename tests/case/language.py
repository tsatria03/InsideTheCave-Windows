"""The game's language: ``platform/language.py``, Windows' display language in two letters,
English when there is nothing the game has words in."""
from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
import _scratch_save                                             # noqa: E402  never the real save

from insidethecave.platform import language                      # noqa: E402


def test_two_letters_from_a_locale_name():
    assert language.two_letters('pt-BR') == 'pt'
    assert language.two_letters('zh_CN') == 'zh'
    assert language.two_letters('EN-us') == 'en'


def test_nothing_usable_is_english():
    """The original crashes with no device language (0x10000e830); the port says English."""
    assert language.two_letters(None) == 'en'
    assert language.two_letters('') == 'en'
    assert language.two_letters('1-2') == 'en'


def test_windows_gives_a_two_letter_code():
    code = language.code()
    assert len(code) >= 2 and code.isalpha() and code == code.lower(), code


def test_the_tutorial_has_six_languages_and_the_warning_two():
    """GameScene.tutorial compares with pt, es, zh, ru, fr; the warning with pt alone."""
    for lang in ('en', 'pt', 'es', 'zh', 'ru', 'fr'):
        assert language.pick(lang, language.TUTORIAL_LANGUAGES) == lang
    assert language.pick('de', language.TUTORIAL_LANGUAGES) == 'en'
    assert language.pick('pt', language.WARNING_LANGUAGES) == 'pt'
    assert language.pick('fr', language.WARNING_LANGUAGES) == 'en'


if __name__ == '__main__':
    _scratch_save.run(globals())
