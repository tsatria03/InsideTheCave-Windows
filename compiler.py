"""Build Inside The Cave into an executable with PyInstaller.

It builds the game into dist\\InsideTheCave-Windows, and nothing else: it never zips and never changes the
repository.  Setting the version, filing the changelog, zipping, tagging and uploading a release are
releaser.py's work, and the releaser calls this to do the building.  It builds for Windows only, on
Windows; there is no Linux build.

Double-click this file, or run py compiler.py with nothing after it, and it offers a numbered menu of
builds, then waits for Enter at the end so you can hear how it went.  Each choice is one of these flags,
which still work typed out:

    py compiler.py                the folder build: the game's data beside the executable
    py compiler.py --embed        one executable with the sounds and the game's data inside it
    py compiler.py --clean        empty PyInstaller's cache first
    py compiler.py --console      keep a console window, to see why the game will not start
    py compiler.py --onefile      one executable with the game's data still beside it
    py compiler.py --no-game      leave the game's data out
    py compiler.py --dry-run      say what a build would do, build nothing

Every build lands in dist\\InsideTheCave-Windows, around InsideTheCave.exe, with the text a player reads
beside the executable - the readme, the changelog, the credits and the todo list in a docks\\ folder, as
in the repository, and VERSION and the license at the top.  Those are never put inside it.  The
third-party licenses go inside the executable, as licenses\\, whichever kind of build.  That folder is
what releaser.py zips into dist\\InsideTheCave-Win-<VERSION>.zip.

The port and the vendored DLLs always go inside the build.  In the folder build the game's own files do
not: the sounds are copied next to the executable, into game\\sounds, which is where
insidethecave/paths.py is to look for them when frozen, with anything named in GAME_FILES into game\\.
With --embed the same files go inside the executable instead, and are found in the folder it unpacks
itself to; that costs a few seconds at every launch.  Nothing else in the original app bundle is copied -
not the iOS executable, the Swift runtime, the images, the fonts or the storyboards - since the port
reads none of it.

The game's data is the repository's game\\ folder, or the folder named by INSIDETHECAVE_GAME.  The
compiler finds it on its own rather than through insidethecave/paths.py, so a build never depends on
the port's code being importable.

There is no --test yet.  A test build would start the game and read its log; the port does not write a
log, or a crash.txt, so there is nothing for a test run to read.  A windowed build that fails says
why aloud, in one line; build with --console to see the whole traceback.

Until insidethecave\\ and InsideTheCave.py are written there is nothing to build, and the compiler says
so rather than starting PyInstaller (problems_now).
"""
from __future__ import annotations

import argparse
import fnmatch
import importlib.machinery
import importlib.metadata
import importlib.util
import os
import re
import shutil
import subprocess
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
#: The executable's name, without its .exe.
NAME = 'InsideTheCave'
EXE = NAME + '.exe'
ENTRY = 'InsideTheCave.py'
#: The port's own package, which has to exist before there is anything to build.
PACKAGE = 'insidethecave'
#: The folder a build lands in, and the one a release's zip extracts to.
FOLDER = NAME + '-Windows'

#: The vendored DLLs that go inside the build, and the folder each goes to there.
BINARIES = (('vendor/openal/soft_oal.dll', 'vendor/openal'),            # the audio engine itself
            ('vendor/nvda/nvdaControllerClient64.dll', 'vendor/nvda'))
#: Their licenses, which sit beside them in vendor/: the folder each goes to under licenses/ inside the
#: executable, and the files.  Prism's and pygame's are not kept here - they come out of the installed
#: packages when the build runs (license_files()), so they always match what was bundled.
VENDOR_LICENSES = (('openal-soft', ('vendor/openal/license.txt', 'vendor/openal/license-pffft.txt')),
                   ('nvda-controller-client', ('vendor/nvda/license.txt',)))

#: what the game cannot run without: the module, and what pip calls it.  pygame, not pygame-ce - the two
#: cannot be installed side by side, and the port is written against pygame.  prismatoid is Prism, which
#: the port speaks through for every screen reader but NVDA, and for a Windows voice.  The game is to
#: start without it, but then only an NVDA player would hear what it says, so no build leaves it out.
PLAY_PACKAGES = (('pygame', 'pygame'), ('prism', 'prismatoid'))

#: Where the game's data is: the repository's game\ folder, unless INSIDETHECAVE_GAME names another copy.
GAME_ENV = 'INSIDETHECAVE_GAME'
GAME_DIR = os.path.join(HERE, 'game')
#: The bundle's sounds folder, copied whole with whatever folders it has: game\sounds in the repository,
#: and game\sounds beside the executable.  The original kept its 12 sounds loose in its top folder; the dev
#: moved them here (2026-10-02).
SOUNDS = 'sounds'
#: What else the game reads from its bundle's top folder, matched without regard to case.  Nothing yet:
#: the port is known to need only the sounds so far.  Name a file here once the port reads it - the
#: SpriteKit scenes (*.sks) or Info.plist, say.  The rest of the app - the iOS executable and its code
#: signature, the Swift runtime in Frameworks\, Assets.car, the fonts, the storyboards and the icons - has
#: no business in a release.
GAME_FILES = ()
#: copied beside the executable rather than bundled inside it, so the player can open them: what it is
#: called here, and what it is called there.  They are never embedded, --embed or not.  LICENSE has no
#: extension, which is the convention on GitHub but means Windows asks what to open it with, so it ships
#: as a .txt.  The todo list holds only what a player notices, which is why it can ship.  The documents a
#: player reads live in docks\ in the repository, and go into a docks\ folder beside the executable, as
#: they are laid out here; VERSION and the license stay at the top.
DOCKS = 'docks'
CHANGELOG = os.path.join(DOCKS, 'changelog.txt')
#: The player's readme is plain text of its own, not README.md, which is for developers and would be
#: read aloud with every # and | in it.
SIDE_FILES = ((os.path.join(DOCKS, 'readme.txt'), os.path.join(DOCKS, 'readme.txt')),
              (CHANGELOG, CHANGELOG),
              (os.path.join(DOCKS, 'credits.txt'), os.path.join(DOCKS, 'credits.txt')),
              (os.path.join(DOCKS, 'todo list.txt'), os.path.join(DOCKS, 'todo list.txt')),
              ('VERSION', 'VERSION'),
              ('LICENSE', 'license.txt'))


def say(text: str = '') -> None:
    print(text, flush=True)


def build_version() -> str:
    """What this build calls itself: the one line in VERSION, or '' when there is no such file."""
    try:
        with open(os.path.join(HERE, 'VERSION'), encoding='utf-8') as fh:
            return fh.read().strip().splitlines()[0].strip()
    except (OSError, IndexError):
        return ''


# --- the changelog -----------------------------------------------------------------------------------
# docks\changelog.txt collects what has changed under one heading, "unrelease:", at the top.
# releaser.py files those lines under the version being released before it calls this to build; the
# compiler only reads the changelog, and takes an empty unrelease: heading out of the copy it ships.  The
# parsing lives here, where both use it.

#: The heading the changelog collects unreleased changes under: the whole line, colon and all.
UNRELEASE = 'unrelease:'
#: A heading is one word ending in a colon - "unrelease:", "26.10.02-1:".  The entries are sentences, so a
#: line with a space in it, colons and all, is never taken for one.
_HEADING = re.compile(r'^[^\s:]+:$')


def changelog_heading(version: str) -> str:
    """'26.10.02-1' -> '26.10.02-1:'.  The heading is VERSION exactly as written, build number and all."""
    return version + ':'


def _parse_changelog(text: str) -> list:
    """[[heading, [lines]], ...] in the order of the file.  Blank lines only separate one version from
    the next, so they are not kept; anything above the first heading is a block with no heading."""
    blocks = []
    for line in text.replace('\r\n', '\n').split('\n'):
        if _HEADING.match(line.strip()):
            blocks.append([line.strip(), []])
        elif line.strip():
            if not blocks:
                blocks.append([None, []])
            blocks[-1][1].append(line)
    return blocks


def _render_changelog(blocks: list) -> str:
    """A heading, its lines, then one blank line before the next heading, all the way down - so where
    one version's changes end is something you hear, not something you have to work out."""
    return '\n\n'.join('\n'.join(([heading] if heading else []) + lines) for heading, lines in blocks) + '\n'


def unreleased_lines(text: str) -> list:
    """The lines under unrelease:, the changes no release has carried yet."""
    return next((lines for heading, lines in _parse_changelog(text) if heading == UNRELEASE), [])


def without_unrelease(text: str) -> str:
    """The changelog a player reads: the same, less the empty unrelease: heading, so it opens on the
    newest version.  A heading that still has lines under it is left alone rather than lose them."""
    return _render_changelog([b for b in _parse_changelog(text) if not (b[0] == UNRELEASE and not b[1])])


def strip_shipped_changelog(dest_root: str) -> None:
    """Take the empty unrelease: heading out of the copy in the build's docks\\ - the copy only.  A build
    made straight after the releaser has filed the changelog opens on the new version."""
    path = os.path.join(dest_root, CHANGELOG)
    if os.path.isfile(path):
        text = open(path, encoding='utf-8').read()
        with open(path, 'w', encoding='utf-8', newline='\n') as fh:
            fh.write(without_unrelease(text))


def release_warnings(changelog: str) -> list:
    """What would make this a bad thing to publish, judged on the changelog the build actually carries."""
    found = []
    if not build_version():
        found.append('there is no VERSION file, so the release has no version to be tagged with, and '
                     'the zip has none in its name')
    try:
        with open(changelog, encoding='utf-8') as fh:
            first = fh.readline().strip()
        if first == UNRELEASE:
            found.append('the changelog in this build still opens with "%s", because only releaser.py '
                         'files the changelog; release with it to put those lines under the version'
                         % UNRELEASE)
    except OSError:
        found.append('there is no changelog.txt, so the release notes would be empty')
    return found


def problems_now() -> list[str]:
    """Everything that would stop the build, in plain words."""
    found = []
    if sys.platform != 'win32':
        found.append('this builds on Windows only, and this is %s' % sys.platform)
    if sys.maxsize <= 2 ** 32:
        found.append('use 64-bit Python: the vendored libraries are 64-bit')
    if importlib.util.find_spec('PyInstaller') is None:
        found.append('PyInstaller is not installed in this Python: pip install pyinstaller')
    absent = [pip for mod, pip in PLAY_PACKAGES if importlib.util.find_spec(mod) is None]
    if absent:
        found.append("the game's own packages have to be installed here too, to be bundled: "
                     'pip install ' + ' '.join(absent))
    for src, _ in BINARIES:
        if not os.path.isfile(os.path.join(HERE, src.replace('/', os.sep))):
            found.append('%s is missing - it ships with the repository' % src)
    if not os.path.isfile(os.path.join(HERE, ENTRY)):
        found.append('%s is not here, so there is no game to build yet - the port has not been written'
                     % ENTRY)
    if not os.path.isfile(os.path.join(HERE, PACKAGE, '__init__.py')):
        found.append('the %s package is not here yet, so the game has no code to build' % PACKAGE)
    return found


def prism_native_modules() -> list[str]:
    """Prism's compiled Python module in its prism\\_native folder, which --collect-all leaves behind: the
    .pyd, whatever this Python names its compiled modules."""
    spec = importlib.util.find_spec('prism')
    if spec is None or not spec.submodule_search_locations:
        return []
    folder = os.path.join(list(spec.submodule_search_locations)[0], '_native')
    if not os.path.isdir(folder):
        return []
    suffixes = tuple(importlib.machinery.EXTENSION_SUFFIXES)
    return sorted(os.path.join(folder, name) for name in os.listdir(folder) if name.endswith(suffixes))


#: Where --embed gathers the game's top-folder files (GAME_FILES) so PyInstaller can take them as one
#: folder.  Adding them one by one would run past Windows' limit on a command line.
EMBED_STAGE = os.path.join(HERE, 'build', 'embed', 'game')
#: Where every build gathers the third-party licenses, which go inside the executable as licenses\; only
#: the port's own license.txt stays beside it.
LICENSES_STAGE = os.path.join(HERE, 'build', 'embed', 'licenses')


def _is_game(folder: str) -> bool:
    """What has to be in a folder for it to be the game's data: the bundle's sounds folder."""
    return os.path.isdir(os.path.join(folder, SOUNDS))


def game_source() -> str | None:
    """The game's data: the folder INSIDETHECAVE_GAME names, or the repository's game\\, whichever is
    found first holding a sounds folder; None when neither does."""
    for folder in (os.environ.get(GAME_ENV, ''), GAME_DIR):
        if folder and _is_game(folder):
            return os.path.abspath(folder)
    return None


def where_the_game_was_looked_for() -> str:
    """The folders game_source() tried, in words, for when it finds none."""
    tried = [os.environ[GAME_ENV] + ' (from %s)' % GAME_ENV] if os.environ.get(GAME_ENV) else []
    return 'looked in %s, for a %s folder' % (' and '.join(tried + [GAME_DIR]), SOUNDS)


def embedded_data(src: str) -> list[tuple[str, str]]:
    """What --embed puts inside the executable, as PyInstaller's (source, folder inside) pairs: the staged
    top-folder files as game\\, and the sounds folder as game\\sounds, whole.  The game finds them in the
    folder the executable unpacks itself to, as it would find them beside a folder build."""
    return [(EMBED_STAGE, 'game'), (os.path.join(src, SOUNDS), 'game/' + SOUNDS)]


def stage_embedded(src: str) -> list[str]:
    """Copy the top-folder files --embed carries into EMBED_STAGE, fresh, and return their names."""
    if os.path.isdir(EMBED_STAGE):
        shutil.rmtree(EMBED_STAGE)
    os.makedirs(EMBED_STAGE)
    names = game_files(src)
    for name in names:
        shutil.copy2(os.path.join(src, name), os.path.join(EMBED_STAGE, name))
    return names


def command(args, data=()) -> list[str]:
    """The PyInstaller command line.  ``data`` is what --embed adds inside the executable."""
    cmd = [sys.executable, '-m', 'PyInstaller', '--noconfirm', '--noupx', '--name', NAME]
    for src, dest in BINARIES:
        cmd += ['--add-binary', src + os.pathsep + dest]
    # Prism is imported only once NVDA is found not to be running, so it is named outright rather than left
    # for the analysis to find.  It loads its compiled half from a folder of its own, prism\_native:
    # --collect-all brings the DLL there but not the Python module beside it, because the folder is not a
    # package, so that is added by name - and it needs cffi's own compiled module, which nothing names either
    cmd += ['--collect-all', 'prism', '--hidden-import', '_cffi_backend']
    for src in prism_native_modules():
        cmd += ['--add-binary', src + os.pathsep + 'prism/_native']
    if not args.console:
        # no console window beside the game's own.  A failure is said aloud in one line;
        # --console shows the whole traceback
        cmd += ['--windowed']
    if args.onefile or args.embed:
        # one file lands in dist\InsideTheCave-Windows too, so every build is one folder to zip and nothing
        # else in dist\ - an older zip, say - is swept into it
        cmd += ['--onefile', '--distpath', output_dir(args)]
    for src, inside in data:
        cmd += ['--add-data', src + os.pathsep + inside]
    # the third-party licenses go inside, whichever kind of build (stage_licenses fills the folder)
    cmd += ['--add-data', LICENSES_STAGE + os.pathsep + 'licenses']
    if args.clean:
        cmd += ['--clean']
    return cmd + [ENTRY]


def output_dir(args=None) -> str:
    """Where the executable lands, and so where everything beside it goes: dist\\InsideTheCave-Windows,
    whichever kind of build."""
    return os.path.join(HERE, 'dist', FOLDER)


def pyinstaller_dir() -> str:
    """Where a folder build's PyInstaller puts it, named after the executable: dist\\InsideTheCave.  It is
    moved to output_dir() once built, since PyInstaller names that folder and the executable alike."""
    return os.path.join(HERE, 'dist', NAME)


def clear_output(dest_root: str) -> None:
    """Empty dist\\InsideTheCave-Windows before a build, and dist\\InsideTheCave, where a folder build
    first lands.  A one-file build only writes its executable, and would leave an older build's files
    around it."""
    for folder in (dest_root, pyinstaller_dir()):
        if os.path.isdir(folder):
            shutil.rmtree(folder)


def move_folder_build(dest_root: str) -> None:
    """A folder build is made in dist\\InsideTheCave; move it to dist\\InsideTheCave-Windows."""
    built = pyinstaller_dir()
    if os.path.normcase(built) != os.path.normcase(dest_root) and os.path.isdir(built):
        os.replace(built, dest_root)


def game_files(src: str) -> list[str]:
    """The names in the bundle's top folder that the game reads - GAME_FILES, matched without regard to
    case, as Windows matches file names."""
    return sorted(name for name in os.listdir(src)
                  if os.path.isfile(os.path.join(src, name))
                  and any(fnmatch.fnmatch(name.lower(), pattern.lower()) for pattern in GAME_FILES))


def sound_files(src: str) -> list[str]:
    """Every file under the bundle's sounds folder, as a path inside the bundle, so each one keeps
    whatever folder it is in."""
    found = []
    for dirpath, dirs, files in os.walk(os.path.join(src, SOUNDS)):
        dirs.sort()
        found += [os.path.relpath(os.path.join(dirpath, name), src) for name in sorted(files)]
    return found


#: What data_summary() counts as a sound.  The repository's are all WAV, in sounds\used and sounds\unused
#: (the dev converted and sorted them on 2026-10-02); the original's MP3 and AIFF still count, for a copy
#: of the untouched bundle.
SOUND_EXTENSIONS = ('.wav', '.mp3', '.aiff', '.aif', '.ogg')


def data_summary(names: list[str]) -> str:
    """What a list of the game's files holds, in words: '12 files - 12 sounds', or '14 files - 12 sounds,
    and 2 other files'."""
    sounds = sum(1 for name in names if name.lower().endswith(SOUND_EXTENSIONS))
    others = len(names) - sounds
    return '%d files - %d sounds%s' % (len(names), sounds,
                                         ', and %d other files' % others if others else '')


def copy_game(dest_root: str) -> bool:
    src = game_source()
    if src is None:
        say("  the game's data was not found, so nothing was copied: %s." % where_the_game_was_looked_for())
        say('  set %s to a copy of the game folder, or put one beside the executable.' % GAME_ENV)
        return False
    dest = os.path.join(dest_root, 'game')
    say("copying the game's data from %s into %s ..." % (src, dest))
    started = time.perf_counter()
    names = game_files(src) + sound_files(src)
    for name in names:
        target = os.path.join(dest, name)
        os.makedirs(os.path.dirname(target), exist_ok=True)
        shutil.copy2(os.path.join(src, name), target)
    say('  %s, in %.0f seconds.' % (data_summary(names), time.perf_counter() - started))
    return True


def copy_side_files(dest_root: str) -> None:
    """The text the player reads, next to the game rather than inside it: docks\\ as a folder, and
    VERSION and the license at the top."""
    for name, shipped_as in SIDE_FILES:
        src = os.path.join(HERE, name)
        if not os.path.isfile(src):
            say('  %s is not here, so it was not copied.' % name)
            continue
        target = os.path.join(dest_root, shipped_as)
        os.makedirs(os.path.dirname(target), exist_ok=True)
        shutil.copy2(src, target)
        say('%s is in the build%s.'
            % (shipped_as, '' if shipped_as == name else ', from %s' % name))


def license_files() -> list[tuple[str, str]]:
    """Every third-party license a release carries: (where it goes under licenses\\, where it comes from).

    The two vendored DLLs' licenses sit beside them in vendor\\.  Prism's come out of its installed
    package's dist-info - its own license, its NOTICE, and the LICENSES folder that NOTICE points to, for
    the libraries Prism itself is built from - and pygame's LGPL out of pygame's installed package, so a
    build always carries the licenses of exactly what it bundled.  A file with no extension gets .txt, so
    Windows opens it rather than asking what to open it with."""
    found = []
    for folder, sources in VENDOR_LICENSES:
        for src in sources:
            found.append((os.path.join(folder, os.path.basename(src)),
                          os.path.join(HERE, src.replace('/', os.sep))))
    try:
        dist = importlib.metadata.distribution('prismatoid')
        for entry in dist.files or ():
            parts = entry.parts
            if len(parts) > 2 and parts[0].endswith('.dist-info') and parts[1] == 'licenses':
                rel = os.path.join('prism', *parts[2:])
                if not os.path.splitext(rel)[1]:
                    rel += '.txt'
                found.append((rel, str(dist.locate_file(entry))))
    except importlib.metadata.PackageNotFoundError:
        found.append((os.path.join('prism', 'LICENSE.txt'), ''))      # reported as missing
    spec = importlib.util.find_spec('pygame')
    folder = list(spec.submodule_search_locations)[0] if spec and spec.submodule_search_locations else ''
    found.append((os.path.join('pygame', 'LGPL.txt'),
                  os.path.join(folder, 'docs', 'generated', 'LGPL.txt') if folder else ''))
    return found


def licensed_names() -> str:
    """Whose licenses the build carries, in words."""
    vendored = [{'openal-soft': 'OpenAL Soft', 'nvda-controller-client': 'the NVDA controller client'}
                .get(folder, folder) for folder, _files in VENDOR_LICENSES]
    return ', '.join(vendored + ['Prism']) + ' and pygame'


def stage_licenses(dest: str = None) -> int:
    """The third-party licenses, gathered fresh into LICENSES_STAGE for PyInstaller to put inside the
    executable as licenses\\.  Returns how many."""
    dest = dest or LICENSES_STAGE
    if os.path.isdir(dest):
        shutil.rmtree(dest)
    os.makedirs(dest)
    copied = 0
    for rel, src in license_files():
        if not src or not os.path.isfile(src):
            say('  the license %s was not found, so it was not copied.' % rel)
            continue
        target = os.path.join(dest, rel)
        os.makedirs(os.path.dirname(target), exist_ok=True)
        shutil.copy2(src, target)
        copied += 1
    say('%d license files - %s - go inside the executable, as licenses%s.'
        % (copied, licensed_names(), os.sep))
    return copied


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(prog='compiler.py', description='build Inside The Cave with PyInstaller')
    parser.add_argument('--embed', action='store_true',
                        help="one executable with the sounds and the game's data inside it; the text a "
                             'player reads stays beside it')
    parser.add_argument('--onefile', action='store_true',
                        help="one executable, with the game's data still beside it")
    parser.add_argument('--no-game', action='store_true',
                        help="leave the game's data out")
    parser.add_argument('--console', action='store_true',
                        help='keep a console window, where a failed start-up prints its traceback')
    parser.add_argument('--clean', action='store_true', help="throw away PyInstaller's cache first")
    parser.add_argument('--dry-run', action='store_true', help='print what would be done, build nothing')
    args = parser.parse_args(argv)
    os.chdir(HERE)                                      # the paths above are relative to the project

    found = problems_now()
    if found:
        say('this would stop the build:' if args.dry_run else 'the build cannot start:')
        for problem in found:
            say('  ' + problem)
        if not args.dry_run:
            return 2
        say()

    dest_root = output_dir(args)
    src = None if args.no_game else game_source()      # INSIDETHECAVE_GAME, then game\
    if args.embed and src is None:
        say("--embed puts the game's data inside the executable, and the game's data was not found.")
        if not args.dry_run:
            return 2

    data = embedded_data(src) if args.embed and src else []
    cmd = command(args, data)
    say('running: python ' + ' '.join(cmd[1:]))
    if args.dry_run:
        if args.no_game:
            say("the game's data would be left out.")
        elif src is None:
            say("the game's data was not found, so none would be copied: %s."
                % where_the_game_was_looked_for())
        elif args.embed:
            say("the game's data would go inside the executable, from %s: %s, and nothing else from the "
                'app bundle' % (src, data_summary(game_files(src) + sound_files(src))))
        else:
            say("the game's data would then be copied from %s into %s: %s, and nothing else from the "
                'app bundle'
                % (src, os.path.join(dest_root, 'game'), data_summary(game_files(src) + sound_files(src))))
        for name, shipped_as in SIDE_FILES:
            say('%s would be copied into the build%s%s'
                % (name, '' if shipped_as == name else ', as %s' % shipped_as,
                   '' if os.path.isfile(os.path.join(HERE, name)) else ' - but it is not here'))
        licenses = license_files()
        absent = [rel for rel, lic in licenses if not lic or not os.path.isfile(lic)]
        say('%d license files - %s - would go inside the executable, as licenses%s'
            % (len(licenses) - len(absent), licensed_names(), os.sep))
        for rel in absent:
            say('  but the license %s is not here' % rel)
        for warning in release_warnings(os.path.join(HERE, CHANGELOG)):
            say('before releasing: ' + warning)
        return 0

    if args.embed:
        names = stage_embedded(src)
        say("the game's data goes inside the executable: %s."
            % data_summary(names + sound_files(src)))
    stage_licenses()
    clear_output(dest_root)
    started = time.perf_counter()
    if subprocess.run(cmd).returncode != 0:
        say("PyInstaller failed - its own output above says why.")
        return 1
    say('built in %.0f seconds.' % (time.perf_counter() - started))
    if not (args.onefile or args.embed):
        move_folder_build(dest_root)

    if src is not None and not args.embed:
        copy_game(dest_root)
    copy_side_files(dest_root)
    strip_shipped_changelog(dest_root)

    for warning in release_warnings(os.path.join(dest_root, CHANGELOG)):
        say('before releasing: ' + warning)

    exe = os.path.join(dest_root, EXE)
    say()
    say('the game is %s' % exe)
    say("the folder around it is what releaser.py zips, and the game's own files in it belong to the "
        "original's makers, Iago Barbosa, Juliana Barros and Victor Leal.")
    return 0


# --- the menu ----------------------------------------------------------------------------------------
# Double-click compiler.py, or run it with nothing after it, and it asks rather than expects you to know
# the flags.  Each choice is exactly one of the command lines below, so the two can never disagree; the
# flags still work as they always have for anyone typing them.

MENU = (
    ("Folder build: the game in a folder, with its data beside the executable", []),
    ("Single exe: the sounds and the game's data inside one executable", ['--embed']),
    ("Clean build: empty PyInstaller's cache first, for when a build behaves oddly", ['--clean']),
    ("Build with a console window, to see why the game will not start", ['--console']),
    ("One-file build: a single executable, with the game's data still beside it", ['--onefile']),
    ("Build without the game's data", ['--no-game']),
    ('Show what a build would do, without building anything', ['--dry-run']),
)


def menu() -> list | None:
    """Ask which build.  Returns the flags for it, or None to quit."""
    version = build_version()
    say('Inside The Cave compiler.  VERSION is %s.'
        % (version or 'missing - releaser.py sets it as it releases'))
    say()
    for number, (text, _flags) in enumerate(MENU, 1):
        say('  %d. %s' % (number, text))
    say('  0. Quit')
    say()
    while True:
        try:
            choice = input('Type a number and press Enter: ').strip()
        except EOFError:
            return None
        if choice == '0':
            return None
        if choice.isdigit() and 1 <= int(choice) <= len(MENU):
            text, flags = MENU[int(choice) - 1]
            say('%s.' % text.split(':')[0])
            say()
            return list(flags)
        say('There is no choice "%s". Type a number from 0 to %d.' % (choice, len(MENU)))


def run(argv=None) -> int:
    """Flags on the command line build straight away, as they always have.  No flags with a keyboard at
    the other end - a double-click in Explorer, or py compiler.py typed on its own - opens the menu, and
    the window waits at the end so what happened can be heard before it closes.  With no keyboard at
    all, no flags is still the release build it always was."""
    argv = sys.argv[1:] if argv is None else argv
    if argv or not sys.stdin.isatty():
        return main(argv)
    chosen = menu()
    if chosen is None:
        return 0
    try:
        return main(chosen)
    finally:
        say()
        try:
            input('Finished. Press Enter to close this window.')
        except EOFError:
            pass


if __name__ == '__main__':
    sys.exit(run())
