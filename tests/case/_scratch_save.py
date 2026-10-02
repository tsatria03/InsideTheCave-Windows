"""Keep the tests off the real save, and silent.

Every test file imports this first, before any of the game.  It:

* points ``INSIDETHECAVE_USER_DIR`` at a fresh folder of its own, so ``save.json``,
  ``settings.json`` and ``keys.json`` are written there and never to
  ``%APPDATA%\\InsideTheCave``, and deletes that folder when the run ends;
* sets ``INSIDETHECAVE_SILENT``, so ``platform/speech.py`` never loads NVDA's client or
  Prism and never speaks or cuts off the player's screen reader;
* sends the sound to OpenAL Soft's null driver and SDL's dummy audio, and gives pygame
  a dummy display, so nothing is heard and no window opens for a screen reader to
  announce.

Each is set outright, whatever the shell running the tests has set, so a test is silent
and off the real save wherever it is run from.  ``paths.py``'s tests fail if a test file
does not import this.  It is not a test itself; the leading underscore keeps it apart.
"""
from __future__ import annotations

import atexit
import os
import shutil
import tempfile

FOLDER = tempfile.mkdtemp(prefix='insidethecave_test_save_')
QUIET = {
    'INSIDETHECAVE_USER_DIR': FOLDER,
    'INSIDETHECAVE_SILENT': '1',
    'ALSOFT_DRIVERS': 'null',
    'SDL_AUDIODRIVER': 'dummy',
    'SDL_VIDEODRIVER': 'dummy',
}
os.environ.update(QUIET)
atexit.register(shutil.rmtree, FOLDER, True)


def run(namespace):
    """Run every ``test_*`` function in a test file's globals, printing ``ok`` or ``FAIL``
    for each and a total; exit 1 if any failed."""
    import sys
    fns = [v for k, v in sorted(namespace.items()) if k.startswith('test_')]
    bad = 0
    for fn in fns:
        try:
            fn()
            print('ok    %s' % fn.__name__)
        except AssertionError as e:
            bad += 1
            print('FAIL  %s: %s' % (fn.__name__, e))
        except Exception as e:
            bad += 1
            print('ERROR %s: %r' % (fn.__name__, e))
    print('%d/%d passed' % (len(fns) - bad, len(fns)))
    sys.exit(1 if bad else 0)
