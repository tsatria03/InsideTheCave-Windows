#!/usr/bin/env python
"""For testing by ear: hear what phase 1 of the port built, before there is a game.  Not a
test, and not part of the game: the tests are in ``tests\\case``, and this is one of the
tools in ``tests\\interact`` that you play.  Wear headphones.

    python tests\\interact\\platform_check.py        the menu
    python tests\\interact\\platform_check.py 1      one check straight away, then the menu

It opens a small window of its own, and the keys go to it:

    Up / Down       move through the checks, each one named
    Enter           run the one you are on
    1 to 8          run that check at once
    Escape          stop the check that is playing; in the menu, quit
    Alt+F4          quit, at any moment, even in the middle of a sound

The checks:

     1  the roar, placed left, centre and right
     2  the bats, placed left, centre and right
     3  the roar at the original's volumes: 3.0 in your lane, 1.0 in another
     4  the roar as the original's stereo file, then the port's mono one, both centred
     5  every sound version 2.32 plays, one after another, each named first
     6  the tutorial line in a Windows voice in your display language, then the key hints
        through your screen reader once the voice is done
     7  the master volume: the roar at 100, 70 and 40 percent
     8  the Windows voices installed, and which one the tutorial would use

Each place and each sound is named through your screen reader before it plays, and
printed, so the console holds what was heard; the window shows the last few lines.

The placing here is a plain stand-in: a sound straight to your left, ahead, or straight
to your right, all at the same distance.  How the game maps its lanes onto OpenAL is phase
2's work, to be tuned by ear (aidocks/project_port_plan.md, question 2); this only checks
that a mono sound can be placed and a stereo one cannot.

**Your save is never touched.**  The tool runs on its own save in
``%APPDATA%\\InsideTheCave\\platform_check``, taking a copy of your key bindings and your
volume settings each time it starts.
"""
from __future__ import annotations

import os
import shutil
import sys
import time

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, ROOT)

SAVE_NAME = 'platform_check'

#: Where each lane is heard, as a direction: straight left, ahead, straight right.
PLACES = (('Left', (-1.0, 0.0, 0.0)), ('Centre', (0.0, 0.0, -1.0)),
          ('Right', (1.0, 0.0, 0.0)))

#: The 12 sounds version 2.32 plays, by the names the binary asks for, and what each is
#: (GAME_STRUCTURE.md section 13).
SOUNDS = (
    ('Rugido.mp3', 'the roar'),
    ('BatSound.wav', 'the bats'),
    ('tilintar.aiff', 'the coin jingle, which the port adds'),
    ('plim_moeda.wav', 'a coin picked up'),
    ('pegou_tocha.wav', 'a torch picked up'),
    ('lancar_tocha.wav', 'a torch thrown'),
    ('tocha.wav', 'the torch burning, the first 4 seconds'),
    ('SC.wav', 'the music, the first 6 seconds'),
    ('dash.aiff', 'a lane change'),
    ('MonsterDead.mp3', 'a monster killed'),
    ('MovimentoProibido.wav', 'a move into the wall'),
    ('screamingMan.wav', 'death'),
)
#: How much of the long ones to play.
CUT = {'tocha.wav': 4.0, 'SC.wav': 6.0}

#: The tutorial line in the original's six languages (analysis/data/strings.txt).
TUTORIAL = {
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
#: The proposed key hints (aidocks/project_port_plan.md, question 6), filled with your keys.
HINTS = (('Press {left} or {right} to change lanes.', ('move_left', 'move_right')),
         ('Press {throw} to throw your torch.', ('throw',)))


def _own_save():
    """Point the save at the tool's own folder, before anything reads it, with a copy of
    your key bindings and settings."""
    real = os.path.join(os.environ.get('APPDATA') or os.path.expanduser('~'), 'InsideTheCave')
    mine = os.path.join(real, SAVE_NAME)
    os.makedirs(mine, exist_ok=True)
    for name in ('keys.json', 'settings.json'):
        yours = os.path.join(real, name)
        if os.path.exists(yours):
            shutil.copyfile(yours, os.path.join(mine, name))
    os.environ['INSIDETHECAVE_USER_DIR'] = mine
    return mine


class Quit(Exception):
    """Alt+F4, or the window closed: leave at once."""


class Stop(Exception):
    """Escape during a check: back to the menu."""


class Window:
    """The tool's own window: the keys come to it, and it shows the last lines said."""

    TITLE = 'Inside The Cave - platform check'

    def __init__(self):
        import pygame
        self.pygame = pygame
        pygame.display.init()           # never pygame.init(), which would open SDL's mixer
        pygame.font.init()
        self.screen = pygame.display.set_mode((640, 360))
        pygame.display.set_caption(self.TITLE)
        self.font = pygame.font.SysFont(None, 26)
        self.lines = []

    def show(self, text):
        self.lines.append(text)
        del self.lines[:-12]
        self.draw()

    def draw(self):
        self.screen.fill((0, 0, 0))
        for i, line in enumerate(self.lines):
            self.screen.blit(self.font.render(line, True, (230, 230, 230)), (12, 10 + i * 28))
        self.pygame.display.flip()

    def keys(self):
        """The keys pressed since last asked, by pygame's name; Quit on Alt+F4."""
        pg = self.pygame
        out = []
        for event in pg.event.get():
            if event.type == pg.QUIT:
                raise Quit()
            if event.type == pg.KEYDOWN:
                if event.key == pg.K_F4 and event.mod & pg.KMOD_ALT:
                    raise Quit()
                out.append(pg.key.name(event.key))
        return out

    def wait(self, seconds):
        """Wait, watching the keys every 20 ms: Alt+F4 quits, Escape stops the check."""
        end = time.monotonic() + seconds
        while True:
            if 'escape' in self.keys():
                raise Stop()
            left = end - time.monotonic()
            if left <= 0:
                return
            time.sleep(min(0.02, left))

    def close(self):
        self.pygame.display.quit()


class Check:
    def __init__(self, window):
        from insidethecave.platform import openal, sound, volume
        from insidethecave.platform.defaults import UserDefaults
        from insidethecave.platform.speech import Speech
        self.window = window
        self.openal = openal
        self.speech = Speech.shared()
        volume.load(UserDefaults.standardUserDefaults())
        self.volume = volume
        self.al = openal.AL()
        self.al.open()
        self.bank = sound.SoundBank(self.al)
        self.set_master(volume.percents[volume.MASTER_KEY])

    # ---- saying and playing -----------------------------------------------------------
    def say(self, text, pause=0.9):
        """Print it, show it, say it through the screen reader, and give it time to be
        heard."""
        print(text)
        self.window.show(text)
        self.speech.speak(text)
        if pause:               # with none, the keys are left for the menu to read
            self.window.wait(pause)

    def set_master(self, percent):
        self.al.alListenerf(self.openal.AL_GAIN, self.volume.percent_gain(percent))

    def play(self, name, mono=True, where=(0.0, 0.0, -1.0), gain=1.0, seconds=None):
        """Play a sound from a direction, at one distance from you, and wait for it."""
        al, o = self.al, self.openal
        s = al.gen_source()
        try:
            al.alSourcei(s, o.AL_BUFFER, self.bank.buffer(name, mono))
            al.alSourcei(s, o.AL_SOURCE_RELATIVE, 1)
            al.alSource3f(s, o.AL_POSITION, *where)
            al.alSourcef(s, o.AL_MAX_GAIN, 4.0)     # OpenAL caps a source at 1.0 otherwise
            al.alSourcef(s, o.AL_GAIN, gain)
            al.alSourcePlay(s)
            length = self.bank.seconds(name, mono)
            self.window.wait(min(length, seconds or length) + 0.3)
        finally:
            al.alSourceStop(s)
            al.delete_source(s)

    # ---- the checks -------------------------------------------------------------------
    def placed(self, name, what):
        self.say('%s, placed left, centre and right.' % what)
        for place, where in PLACES:
            self.say(place, 0.7)
            self.play(name, mono=True, where=where)

    def roar(self):
        self.placed('Rugido.mp3', 'The roar')

    def bats(self):
        self.placed('BatSound.wav', 'The bats')

    def roar_volumes(self):
        self.say('The roar at the original volumes.')
        self.say('In your lane, 3.0, ahead of you.', 0.7)
        self.play('Rugido.mp3', gain=3.0)
        self.say('In another lane, 1.0, to your left.', 0.7)
        self.play('Rugido.mp3', gain=1.0, where=PLACES[0][1])

    def stereo_and_mono(self):
        self.say('The roar as the original stereo file. It cannot be placed.', 0.7)
        self.play('Rugido.mp3', mono=False)
        self.say('The same roar mixed to mono, ahead of you.', 0.7)
        self.play('Rugido.mp3', mono=True)

    def every_sound(self):
        self.say('Every sound the game plays, centred.')
        for name, what in SOUNDS:
            self.say(what.capitalize() + '.', 0.7)
            self.play(name, mono=True, seconds=CUT.get(name))

    def tutorial(self):
        from insidethecave.platform import language
        from insidethecave.platform.keymap import KeyMap
        from insidethecave.platform.speech import TutorialVoice
        code = language.code()
        want = language.pick(code, language.TUTORIAL_LANGUAGES)
        tv = TutorialVoice()
        lang = tv.choose(want)
        self.say('Windows says %s; the tutorial line is in %s.' % (code, lang), 1.5)
        line = TUTORIAL[lang]
        print(line)
        self.window.show(line[:70] + '...')
        try:
            if tv.speak(line):
                self.window.wait(0.5)
                started = time.monotonic()
                while tv.speaking and time.monotonic() - started < 30:
                    self.window.wait(0.1)
            else:
                self.say('The Windows voice could not speak, so the screen reader reads it.',
                         1.0)
                self.speech.speak(line)
                self.window.wait(8)
        finally:
            tv.stop()           # Escape or Alt+F4 cuts the voice off too
        km = KeyMap.shared()
        for text, actions in HINTS:
            keys = {a.split('_')[-1]: km.hint_keys(a) or 'nothing' for a in actions}
            self.say(text.format(**keys), 2.5)

    def master_volume(self):
        was = self.volume.percents[self.volume.MASTER_KEY]
        try:
            for percent in (100, 70, 40):
                self.say('The roar at %d percent.' % percent, 0.7)
                self.set_master(percent)
                self.play('Rugido.mp3')
        finally:
            self.set_master(was)

    def voices(self):
        from insidethecave.platform import language
        from insidethecave.platform.speech import TutorialVoice
        tv = TutorialVoice()
        found = tv.voices()
        if not found:
            self.say('No Windows voice could be listed.')
            return
        self.say('%d Windows voices.' % len(found), 0.5)
        for i, name, lang in found:
            self.say('%d: %s, %s.' % (i + 1, name, lang or 'no language'), 0.5)
        want = language.pick(language.code(), language.TUTORIAL_LANGUAGES)
        lang = tv.choose(want)
        self.say('The tutorial would use voice %d, in %s.' % (tv.backend().voice + 1, lang))

    def close(self):
        self.bank.release()
        self.al.close()


CHECKS = (
    ('The roar, placed left, centre and right', 'roar'),
    ('The bats, placed left, centre and right', 'bats'),
    ("The roar at the original's volumes", 'roar_volumes'),
    ('The roar in stereo, then in mono', 'stereo_and_mono'),
    ('Every sound the game plays', 'every_sound'),
    ('The tutorial line, then the key hints', 'tutorial'),
    ('The master volume', 'master_volume'),
    ('The Windows voices', 'voices'),
)


MENU_HELP = ('Platform check. Up and Down to choose, Enter to run, or the number. Escape '
             'stops a check, or quits from here. Alt+F4 quits at any time.')


def item_text(i):
    return '%d of %d: %s.' % (i + 1, len(CHECKS), CHECKS[i][0])


def run(check, n):
    """Run check ``n`` (1 to 8); Escape during it comes back here."""
    try:
        getattr(check, CHECKS[n - 1][1])()
        check.say('Done. %s' % item_text(n - 1), 0)
    except Stop:
        check.say('Stopped. %s' % item_text(n - 1), 0)


def menu(check, window, index):
    """The menu, until Escape or Alt+F4."""
    while True:
        for name in window.keys():
            if name == 'escape':
                return
            if name in ('down', 'up'):
                index = (index + (1 if name == 'down' else -1)) % len(CHECKS)
                check.say(item_text(index), 0)
            elif name in ('return', 'enter'):
                run(check, index + 1)
            elif name.isdigit() and 1 <= int(name) <= len(CHECKS):
                index = int(name) - 1
                run(check, index + 1)
            else:
                check.say(item_text(index), 0)
        time.sleep(0.02)


def main(argv):
    # the tutorial's Chinese and Russian lines, in a console that cannot show them
    sys.stdout.reconfigure(errors='replace')
    mine = _own_save()
    print('Playing on its own save, in %s.' % mine)
    window = Window()
    check = None
    try:
        check = Check(window)
        index = 0
        first = argv[1] if len(argv) > 1 else ''
        if first.isdigit() and 1 <= int(first) <= len(CHECKS):
            index = int(first) - 1
            run(check, index + 1)
        else:
            check.say(MENU_HELP, 0)
            check.speech.speak(item_text(index), interrupt=False)
            window.show(item_text(index))
        menu(check, window, index)
    except Quit:
        print('Quit.')
    finally:
        if check is not None:
            check.speech.stop()
            check.close()
        window.close()
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv))
